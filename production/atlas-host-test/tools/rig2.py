"""ATLAS rig v2 from the owner's separate-parts pack (pack/src/pNN.png).

Every part is placed into the old 'sheet' coordinate frame (the frame the animation
code already uses) by mapping two anchor points of the part image onto a bone.
PLACE[name] = (RGBA image, 3x3 matrix image px -> sheet rest pose).
PV2 = pivots of the new skeleton (sheet coords).
"""
import math, os
import numpy as np
from PIL import Image, ImageFilter

DS = 0.25   # working downscale of the 1024-1536 px sources (still ~2x screen size)


def T(x, y): return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], float)
def R(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)
def S2(sx, sy): return np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1]], float)
def ang(v): return math.degrees(math.atan2(v[1], v[0]))
def ap(M, p): v = M @ np.array([p[0], p[1], 1.0]); return v[:2]


def load(path, darken=1.0, flip=False):
    im = Image.open(path).convert('RGBA')
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    a = np.asarray(im).astype(np.float32)
    al = a[..., 3]
    # defringe: the packs have red/yellow matte halos; pull the edge in ~4 px and
    # replace edge colours with nearby interior colours
    am = Image.fromarray(al.astype(np.uint8)).filter(ImageFilter.MinFilter(9))
    al2 = np.asarray(am.filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32)
    inner = Image.fromarray(((al > 250) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(13))
    rgb = a[..., :3]
    blur = Image.fromarray(np.dstack([rgb * (np.asarray(inner)[..., None] / 255), np.asarray(inner)]).astype(np.uint8), 'RGBA')
    big = blur.filter(ImageFilter.GaussianBlur(10))
    b = np.asarray(big).astype(np.float32)
    fill = b[..., :3] / np.maximum(b[..., 3:4] / 255, 1e-3)
    edge = (np.asarray(inner) < 128)[..., None]
    rgb = np.where(edge & (b[..., 3:4] > 5), fill, rgb)
    rgb = rgb * darken
    out = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), al2]).astype(np.uint8), 'RGBA')
    w, h = out.size
    return out.resize((int(w * DS), int(h * DS)), Image.LANCZOS)


def place(a0, a1, j0, j1, width_k=1.0):
    """Matrix taking image px (full-res anchors a0->a1) onto sheet bone j0->j1.
    width_k scales across the bone relative to along it."""
    a0 = np.array(a0, float) * DS; a1 = np.array(a1, float) * DS
    j0 = np.array(j0, float); j1 = np.array(j1, float)
    s = np.hypot(*(j1 - j0)) / np.hypot(*(a1 - a0))
    return (T(*j0) @ R(ang(j1 - j0)) @ S2(s, s * width_k) @ R(-ang(a1 - a0)) @ T(-a0[0], -a0[1]))


def place_sim(a0, a1, j0, j1, sx=1.0):
    """Similarity placement with an optional horizontal squash (for the 3/4 pelvis)."""
    M = place(a0, a1, j0, j1)
    return M


def build(pack):
    P = lambda n: os.path.join(pack, f'p{n:02d}.png')
    PL = {}
    # ---------------- torso: collar ring centre -> neck, belt buckle -> buckle in the old pose
    NECK, BUCKLE = (921.0, 116.0), (950.0, 240.0)
    torso = load(P(15))
    Mt = place((700, 110), (841, 903), NECK, BUCKLE)
    PL['torso'] = (torso, Mt)
    near_sh = ap(Mt, (np.array([395, 505]) * DS))
    far_sh = ap(Mt, (np.array([1000, 450]) * DS))
    # ---------------- pelvis (frontal drawing, squashed for 3/4): buckle under torso buckle
    pel = load(P(21))
    k = 0.0935
    Mp = T(BUCKLE[0] + 2, BUCKLE[1] - 1) @ S2(k * 0.82 / DS, k / DS) @ T(-960 * DS, -362 * DS)
    PL['pelvis'] = (pel, Mp)
    near_hip = ap(Mp, np.array([500, 690]) * DS)
    far_hip = ap(Mp, np.array([1060, 705]) * DS)
    # ---------------- legs
    L1, L2, FOOT = 96.0, 80.0, 44.0
    near_knee = near_hip + np.array([-6.0, L1 - 0.2])
    far_knee = far_hip + np.array([5.0, L1 - 0.1])
    near_ankle = near_knee + np.array([-3.0, L2 - 0.1])
    far_ankle = far_knee + np.array([-5.0, L2 - 0.2])
    thigh = load(P(11)); thigh_f = load(P(11), darken=0.82)
    PL['near_thigh'] = (thigh, place((482, 252), (514, 1334), near_hip, near_knee, 1.4))
    PL['far_thigh'] = (thigh_f, place((482, 252), (514, 1334), far_hip, far_knee, 1.4))
    shin = load(P(7)); shin_f = load(P(14), darken=0.82)
    PL['near_shin'] = (shin, place((538, 259), (484, 1329), near_knee, near_ankle, 1.4))
    PL['far_shin'] = (shin_f, place((524, 276), (461, 1317), far_knee, far_ankle, 1.4))
    boot = load(P(9)); boot_f = load(P(18), darken=0.82)
    # boot: shaft top centre -> a bit above the ankle (hidden under the shin cuff), sole on the ground
    def boot_place(top, sole, ankle):
        j0 = ankle + np.array([0.0, -8.0]); j1 = np.array([ankle[0], ankle[1] + FOOT])
        return place(top, (top[0], sole), j0, j1)
    PL['near_foot'] = (boot, boot_place((605, 105), 915, near_ankle))
    PL['far_foot'] = (boot_f, boot_place((560, 130), 905, far_ankle))
    # ---------------- arms (shoulder = centre of the torso's short sleeve)
    UA, FA = 60.0, 54.0
    near_el = near_sh + np.array([-3.0, UA]); near_wr = near_el + np.array([2.0, FA])
    far_el = far_sh + np.array([4.0, UA * 0.95]); far_wr = far_el + np.array([3.0, FA * 0.95])
    PL['near_upper'] = (load(P(20)), place((521, 245), (443, 1337), near_sh, near_el, 1.45))
    PL['near_fore'] = (load(P(16)), place((450, 219), (552, 1353), near_el, near_wr, 1.45))
    PL['far_upper'] = (load(P(20), darken=0.8), place((521, 245), (443, 1337), far_sh, far_el, 1.35))
    PL['far_fore'] = (load(P(12), darken=0.8), place((406, 226), (614, 1365), far_el, far_wr, 1.35))
    # ---------------- hands: (image, wrist anchor, 'tip' anchor) in full-res px; placed per frame
    HANDS = {
        'point': (load(P(1), darken=0.85), (395, 905), (1380, 140), 50.0),
        'relaxed': (load(P(3), darken=0.85), (350, 1225), (950, 260), 44.0),
        'rock': (load(P(4)), (390, 1240), (640, 80), 46.0),
        'palm': (load(P(2), darken=0.85), (450, 900), (1350, 280), 46.0),
    }
    # ---------------- helmet: ring sits on the torso collar ring
    helm = load(P(19))
    ring_c = ap(Mt, np.array([700, 118]) * DS)
    Mh = T(*ring_c) @ S2(0.108 / DS, 0.108 / DS) @ T(-770 * DS, -840 * DS)
    PL['helmet'] = (helm, Mh)
    bubble_c = ap(Mh, np.array([770, 476]) * DS)
    PV2 = {
        'neck': list(ring_c), 'bubble_c': list(bubble_c),
        'near_shoulder': list(near_sh), 'near_elbow': list(near_el), 'near_wrist': list(near_wr),
        'far_shoulder': list(far_sh), 'far_elbow': list(far_el), 'far_wrist': list(far_wr),
        'near_hip': list(near_hip), 'near_knee': list(near_knee), 'near_ankle': list(near_ankle),
        'far_hip': list(far_hip), 'far_knee': list(far_knee), 'far_ankle': list(far_ankle),
        'ground': float(near_ankle[1] + FOOT), 'pelvis': [float(BUCKLE[0]), float(BUCKLE[1] + 25)],
    }
    return PL, HANDS, PV2


def hand_matrix(hand, wrist_w, direction_deg, scale_k=1.0):
    img, a0, a1, length = hand
    a0 = np.array(a0, float) * DS; a1 = np.array(a1, float) * DS
    s = length * scale_k / np.hypot(*(a1 - a0))
    return T(*wrist_w) @ R(direction_deg) @ S2(s, s) @ R(-ang(a1 - a0)) @ T(-a0[0], -a0[1])
