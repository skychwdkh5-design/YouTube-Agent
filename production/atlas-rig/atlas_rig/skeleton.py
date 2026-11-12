"""ATLAS rig definition: the ONE place that holds skeleton geometry, part placement,
layer order and skinning (deformation) settings. Every scene uses build_rig().

Coordinate frame: 'rest' = the reference-sheet frame the parts were fitted in
(pixels, y down, character faces +x). World = rest frame shifted by the character's
root; screen = camera @ world.
"""
import os
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageFilter

from .mathx import T, R, S, ap, ang, unit

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, '..', 'assets')
SRC_SCALE = 0.5   # assets/parts are stored at half the owner's original resolution
DS = 0.25         # working resolution relative to the original (~2x screen size at scale 1.5)


# ----------------------------------------------------------------------------- image loading
def load_part(path, darken=1.0):
    """Load a part, pull the matte fringe in, refill edge colour, scale to DS."""
    im = Image.open(path).convert('RGBA')
    k = 0.5 / SRC_SCALE                      # filter sizes were tuned at 0.5x of the original
    a = np.asarray(im).astype(np.float32)
    al = a[..., 3]
    am = Image.fromarray(al.astype(np.uint8)).filter(ImageFilter.MinFilter(max(3, int(5 * k) | 1)))
    al2 = np.asarray(am.filter(ImageFilter.GaussianBlur(0.8 * k))).astype(np.float32)
    inner = np.asarray(Image.fromarray(((al > 250) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(7)))
    rgb = a[..., :3]
    pre = Image.fromarray(np.dstack([rgb * (inner[..., None] / 255), inner]).astype(np.uint8), 'RGBA')
    b = np.asarray(pre.filter(ImageFilter.GaussianBlur(5 * k))).astype(np.float32)
    fill = b[..., :3] / np.maximum(b[..., 3:4] / 255, 1e-3)
    edge = (inner < 128)[..., None]
    rgb = np.where(edge & (b[..., 3:4] > 5), fill, rgb) * darken
    out = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), al2]).astype(np.uint8), 'RGBA')
    f = DS / SRC_SCALE
    out = out.resize((max(1, int(out.width * f)), max(1, int(out.height * f))), Image.LANCZOS)
    return np.asarray(out).astype(np.float32) / 255.0      # straight RGBA 0..1


def place(a0, a1, j0, j1, width_k=1.0):
    """Matrix: working-image px -> rest frame, mapping image anchors a0->a1 (ORIGINAL px)
    onto the bone j0->j1. width_k scales across the bone (part thickness)."""
    a0 = np.array(a0, float) * DS
    a1 = np.array(a1, float) * DS
    j0 = np.array(j0, float)
    j1 = np.array(j1, float)
    s = np.hypot(*(j1 - j0)) / np.hypot(*(a1 - a0))
    return T(*j0) @ R(ang(j1 - j0)) @ S(s, s * width_k) @ R(-ang(a1 - a0)) @ T(-a0[0], -a0[1])


# ----------------------------------------------------------------------------- data types
@dataclass
class Bone:
    name: str
    parent: str            # None for the pelvis (driven by the pose root)
    head: str              # rest joint the bone rotates about
    tail: str = None       # rest joint at the far end (chains only)


@dataclass
class Zone:
    """Skin blend toward a neighbouring bone around a joint.
    axis points from the joint INTO this part; zone = blend length (rest px);
    cap = weight of the other bone exactly at the joint (0.5 = shared joint)."""
    other: str
    joint: str
    axis: np.ndarray
    zone: float
    cap: float = 0.5


@dataclass
class Part:
    name: str
    img: np.ndarray        # straight RGBA float, working resolution
    M: np.ndarray          # image px -> rest frame
    bone: str
    zones: list = field(default_factory=list)
    grid: tuple = (1, 1)   # mesh cells (nx, ny); (1,1) = rigid quad


@dataclass
class Hand:
    img: np.ndarray
    wrist: np.ndarray      # anchor in working px
    tip: np.ndarray        # direction anchor in working px
    length: float          # wrist->tip in rest px


@dataclass
class Rig:
    J: dict                # rest joints
    bones: dict
    parts: dict
    layers: list           # back-to-front draw order (part names, 'hand_far', 'head', 'hand_near')
    hands: dict
    lengths: dict          # segment lengths (rest px)
    bend: dict             # +1 / -1 bend side per limb (fixed, never flips)
    foot: dict             # sole contact points relative to the ankle (rest px)
    ground: float
    head: dict             # head image placement constants


# ----------------------------------------------------------------------------- build
def build_rig(parts_dir=None):
    pd = parts_dir or os.path.join(ASSETS, 'parts')
    P = lambda n: os.path.join(pd, f'p{n:02d}.png')
    J = {}
    parts = {}

    # torso: collar ring centre -> neck, belt buckle -> waist
    J['neck'] = np.array([921.0, 116.0])
    J['waist'] = np.array([950.0, 240.0])
    torso_img = load_part(P(15))
    Mt = place((700, 110), (841, 903), J['neck'], J['waist'])
    J['shoulder_n'] = ap(Mt, np.array([395, 505]) * DS)
    J['shoulder_f'] = ap(Mt, np.array([1000, 450]) * DS)

    # pelvis: frontal drawing, squashed to read as 3/4
    pel_img = load_part(P(21))
    k = 0.0935
    Mp = T(J['waist'][0] + 2, J['waist'][1] - 1) @ S(k * 0.82 / DS, k / DS) @ T(-960 * DS, -362 * DS)
    J['pelvis'] = J['waist'] + np.array([0.0, 25.0])
    J['hip_n'] = ap(Mp, np.array([500, 690]) * DS)
    J['hip_f'] = ap(Mp, np.array([1060, 705]) * DS)

    # legs (rest: nearly straight, knee slightly forward)
    L1, L2 = 96.0, 80.0
    J['knee_n'] = J['hip_n'] + np.array([-6.0, L1 - 0.2])
    J['knee_f'] = J['hip_f'] + np.array([5.0, L1 - 0.1])
    J['ankle_n'] = J['knee_n'] + np.array([-3.0, L2 - 0.1])
    J['ankle_f'] = J['knee_f'] + np.array([-5.0, L2 - 0.2])
    FOOT = 44.0

    # arms
    UA, FA = 60.0, 54.0
    J['elbow_n'] = J['shoulder_n'] + np.array([-3.0, UA])
    J['wrist_n'] = J['elbow_n'] + np.array([2.0, FA])
    J['elbow_f'] = J['shoulder_f'] + np.array([4.0, UA * 0.95])
    J['wrist_f'] = J['elbow_f'] + np.array([3.0, FA * 0.95])

    bones = {}
    def bone(*a):
        bones[a[0]] = Bone(*a)
    bone('pelvis', None, 'pelvis')
    bone('torso', 'pelvis', 'waist')
    bone('head', 'torso', 'neck')
    for s in 'nf':
        bone(f'upper_{s}', 'torso', f'shoulder_{s}', f'elbow_{s}')
        bone(f'fore_{s}', f'upper_{s}', f'elbow_{s}', f'wrist_{s}')
        bone(f'hand_{s}', f'fore_{s}', f'wrist_{s}')
        bone(f'thigh_{s}', 'pelvis', f'hip_{s}', f'knee_{s}')
        bone(f'shin_{s}', f'thigh_{s}', f'knee_{s}', f'ankle_{s}')
        bone(f'foot_{s}', f'shin_{s}', f'ankle_{s}')

    def ax(a, b):
        return unit(J[b] - J[a])

    # ---- parts + skinning.
    # Rigid pads (shoulder, elbow, knee pads, boots) stay on one bone; the cloth of the
    # NEXT segment bends under them, and its cap above the joint follows the parent bone,
    # so the back of the knee / inside of the elbow closes without holes.
    parts['torso'] = Part('torso', torso_img, Mt, 'torso',
                          [Zone('pelvis', 'waist', ax('waist', 'neck'), 16.0)], (10, 16))
    parts['pelvis'] = Part('pelvis', pel_img, Mp, 'pelvis', [], (1, 1))
    thigh = load_part(P(11))
    thigh_f = load_part(P(11), darken=0.82)
    shin = load_part(P(7))
    shin_f = load_part(P(14), darken=0.82)
    for s, th, sh, sh_a in (('n', thigh, shin, ((538, 259), (484, 1329))),
                            ('f', thigh_f, shin_f, ((524, 276), (461, 1317)))):
        parts[f'thigh_{s}'] = Part(f'thigh_{s}', th, place((482, 252), (514, 1334), J[f'hip_{s}'], J[f'knee_{s}'], 1.4),
                                   f'thigh_{s}', [Zone('pelvis', f'hip_{s}', ax(f'hip_{s}', f'knee_{s}'), 14.0)], (6, 30))
        parts[f'shin_{s}'] = Part(f'shin_{s}', sh, place(sh_a[0], sh_a[1], J[f'knee_{s}'], J[f'ankle_{s}'], 1.4),
                                  f'shin_{s}', [Zone(f'thigh_{s}', f'knee_{s}', ax(f'knee_{s}', f'ankle_{s}'), 16.0),
                                                Zone(f'foot_{s}', f'ankle_{s}', ax(f'ankle_{s}', f'knee_{s}'), 10.0, 0.3)], (6, 30))
    boot = load_part(P(9))
    boot_f = load_part(P(18), darken=0.82)

    def boot_place(top, sole, ankle):
        j0 = ankle + np.array([0.0, -8.0])
        j1 = np.array([ankle[0], ankle[1] + FOOT])
        return place(top, (top[0], sole), j0, j1)
    parts['foot_n'] = Part('foot_n', boot, boot_place((605, 105), 915, J['ankle_n']), 'foot_n')
    parts['foot_f'] = Part('foot_f', boot_f, boot_place((560, 130), 905, J['ankle_f']), 'foot_f')

    up = load_part(P(20))
    up_f = load_part(P(20), darken=0.8)
    fo = load_part(P(16))
    fo_f = load_part(P(12), darken=0.8)
    for s, u_img, f_img, wk, f_anc in (('n', up, fo, 1.45, ((450, 219), (552, 1353))),
                                       ('f', up_f, fo_f, 1.35, ((406, 226), (614, 1365)))):
        parts[f'upper_{s}'] = Part(f'upper_{s}', u_img, place((521, 245), (443, 1337), J[f'shoulder_{s}'], J[f'elbow_{s}'], wk),
                                   f'upper_{s}', [Zone('torso', f'shoulder_{s}', ax(f'shoulder_{s}', f'elbow_{s}'), 8.0, 0.25)], (6, 24))
        parts[f'fore_{s}'] = Part(f'fore_{s}', f_img, place(f_anc[0], f_anc[1], J[f'elbow_{s}'], J[f'wrist_{s}'], wk),
                                  f'fore_{s}', [Zone(f'upper_{s}', f'elbow_{s}', ax(f'elbow_{s}', f'wrist_{s}'), 14.0)], (6, 24))

    helm = load_part(P(19))
    ring_c = ap(Mt, np.array([700, 118]) * DS)
    Mh = T(*ring_c) @ S(0.108 / DS) @ T(-770 * DS, -840 * DS)
    parts['helmet'] = Part('helmet', helm, Mh, 'helmet')     # bone 'helmet' = torso with damped head turn
    J['bubble_c'] = ap(Mh, np.array([770, 476]) * DS)

    def hand(n, wrist, tip, length, darken=0.85):
        return Hand(load_part(P(n), darken), np.array(wrist, float) * DS, np.array(tip, float) * DS, length)
    hands = {
        'point': hand(1, (395, 905), (1380, 140), 50.0),
        'relaxed': hand(3, (350, 1225), (950, 260), 44.0),
        'palm': hand(2, (450, 900), (1350, 280), 46.0),
        'rock': hand(4, (390, 1240), (640, 80), 46.0, 1.0),
        'relaxed_near': hand(3, (350, 1225), (950, 260), 44.0, 1.0),
        'palm_near': hand(2, (450, 900), (1350, 280), 46.0, 1.0),
    }

    # sole contact points from the boot's own alpha (rest frame, relative to the ankle)
    foot = {}
    for s in 'nf':
        p = parts[f'foot_{s}']
        al = p.img[..., 3]
        ys, xs = np.nonzero(al > 0.5)
        yb = ys.max()
        row = xs[ys >= yb - 0.07 * al.shape[0]]
        pts = ap(p.M, (row.min(), yb)), ap(p.M, (row.max(), yb))
        heel, toe = (pts[0], pts[1]) if pts[0][0] < pts[1][0] else (pts[1], pts[0])
        ball = heel + 0.72 * (toe - heel)
        foot[s] = {'heel': heel - J[f'ankle_{s}'], 'ball': ball - J[f'ankle_{s}'], 'toe': toe - J[f'ankle_{s}']}
    ground = float(J['ankle_n'][1] + foot['n']['heel'][1])     # floor = the near boot's sole

    lengths = {}
    for s in 'nf':
        lengths[f'upper_{s}'] = float(np.hypot(*(J[f'elbow_{s}'] - J[f'shoulder_{s}'])))
        lengths[f'fore_{s}'] = float(np.hypot(*(J[f'wrist_{s}'] - J[f'elbow_{s}'])))
        lengths[f'thigh_{s}'] = float(np.hypot(*(J[f'knee_{s}'] - J[f'hip_{s}'])))
        lengths[f'shin_{s}'] = float(np.hypot(*(J[f'ankle_{s}'] - J[f'knee_{s}'])))
    # bend side, in y-down screen terms: legs bend with the knee toward +x (forward),
    # arms with the elbow back/down. Fixed per limb, never chosen per frame.
    bend = {'leg_n': -1, 'leg_f': -1, 'arm_n': +1, 'arm_f': +1}

    layers = ['hand_f', 'fore_f', 'upper_f',
              'foot_f', 'shin_f', 'thigh_f', 'foot_n', 'shin_n', 'thigh_n',
              'pelvis', 'head', 'torso', 'helmet', 'upper_n', 'fore_n', 'hand_n']
    head = {'bubble_c': J['bubble_c'], 'old_c': np.array([932.5, 90.0]), 'dy': 9.0, 'scale': 0.9}
    return Rig(J, bones, parts, layers, hands, lengths, bend, foot, ground, head)
