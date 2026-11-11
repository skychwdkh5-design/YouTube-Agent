"""ATLAS test fragment: 2D cutout rig (FK arms, 2-bone IK legs with planted feet,
mouth visemes from the narration envelope) rendered as an RGBA layer.

usage: render_atlas.py PARTS_DIR NARRATION_WAV MINBAR_JSON OUT_RAW [--frames a:b]
Writes raw RGBA 1920x1080 frames at 30 fps to OUT_RAW ('-' = stdout).
"""
import json, math, subprocess, sys
import numpy as np
from PIL import Image

PARTS, WAV, MINBAR, OUT = sys.argv[1:5]
FPS, W, H = 30, 1920, 1080
DUR = 12.0
NAR_OFFSET = 298.89          # narration time = fragment time + this
N = int(DUR * FPS)
rig = json.load(open(f'{PARTS}/rig.json'))
TL = {k: v['tl'] for k, v in rig['parts'].items() if 'tl' in v}
PV = rig['pivots']
# The far (left) arm is mostly hidden in the reference, so it is rebuilt from the
# near sleeve textures at 0.92 scale, hinged at the far shoulder.
FAR_SH = (986.0, 150.0)
FAR_BASE = None  # set after matrix helpers

def load(name):
    return Image.open(f'{PARTS}/{name}.png').convert('RGBA')

IM = {k: load(k) for k in TL}
# rock-in-hand prop: mirrored so the cuff meets a forearm coming from the left
rock = IM['hand_rock'].transpose(Image.FLIP_LEFT_RIGHT)
rock = rock.crop((0, 0, 79, 100))
IM['hand_rock_m'] = rock

# ---------------------------------------------------------------- matrices
def T(x, y): return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], float)
def S(s, sy=None): return np.array([[s, 0, 0], [0, s if sy is None else sy, 0], [0, 0, 1]], float)
def R(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)
def about(p, a): return T(*p) @ R(a) @ T(-p[0], -p[1])
def ap(M, p): v = M @ np.array([p[0], p[1], 1.0]); return v[:2]
def ang(v): return math.degrees(math.atan2(v[1], v[0]))

SC = 1.50
SCREEN = T(300, 1045) @ S(SC) @ T(-930, -492)
SCREEN_INV = np.linalg.inv(SCREEN)
FAR_BASE = T(*FAR_SH) @ R(-6) @ S(0.92) @ T(-PV['near_shoulder'][0], -PV['near_shoulder'][1])
PV['far_shoulder'] = list(FAR_SH)
PV['far_elbow'] = list(ap(FAR_BASE, PV['near_elbow']))
PV['far_wrist'] = list(ap(FAR_BASE, PV['near_wrist']))

# ---------------------------------------------------------------- keyframe channels
def ease(u): return u * u * (3 - 2 * u)

class Ch:
    def __init__(self, keys): self.k = sorted(keys)
    def __call__(self, t):
        k = self.k
        if t <= k[0][0]: return k[0][1]
        for (t0, v0), (t1, v1) in zip(k, k[1:]):
            if t <= t1:
                return v0 + (v1 - v0) * ease((t - t0) / (t1 - t0))
        return k[-1][1]

# fragment time beats (narration words, already shifted into fragment time)
#  0.32 Inside | 1.27 NASA measured | 2.10 121.6 grams | 4.27 of asteroid material
#  5.69 That's about four ounces | 7.30 The mission needed at least 60 grams
#  9.90 It brought back about twice that | 11.63 end of line
WALK0, WALK1 = 0.75, 2.70
X_OFF, X_STAND = -330.0, 0.0           # root x in sheet units (0 = standing mark)
X_STEP2 = 30.0                         # small step toward the minimum bar
_side = Ch([(7.25, 0.0), (8.05, X_STEP2)])
def root_x(t):
    # constant walking speed, then a smooth stop (no slow creep in from off-screen)
    if t <= WALK0:
        return X_OFF
    if t < WALK1:
        u = (t - WALK0) / (WALK1 - WALK0)
        a = 1 / 0.85
        f = a * u if u < 0.7 else a * 0.7 + a * (u - 0.7) - (a / 0.6) * (u - 0.7) ** 2
        return X_OFF + (X_STAND - X_OFF) * f
    return X_STAND + _side(t)

# ---------------------------------------------------------------- footsteps
REST = {
    'near': dict(hip=PV['near_hip'], knee=PV['near_knee'], ankle=PV['near_ankle']),
    'far': dict(hip=PV['far_hip'], knee=PV['far_knee'], ankle=PV['far_ankle']),
}

def plan_steps():
    """Plants for each foot: list of (t_lift, t_land, x_from, x_to)."""
    steps = {'near': [], 'far': []}
    pos = {'near': REST['near']['ankle'][0] + X_OFF, 'far': REST['far']['ankle'][0] + X_OFF}
    P = 0.27
    t = WALK0
    foot = 'far'
    while t < WALK1 - 0.05:
        t1 = min(t + P, WALK1 + 0.05)
        ahead = 0.26 if t1 < WALK1 - 0.2 else 0.0
        target_root = root_x(min(t1 + ahead, WALK1))
        nx = REST[foot]['ankle'][0] + target_root + (10 if ahead else 0)
        steps[foot].append((t, t1, pos[foot], nx))
        pos[foot] = nx
        foot = 'near' if foot == 'far' else 'far'
        t = t1
    # settle: bring the trailing foot to the rest mark
    for f in ('near', 'far'):
        want = REST[f]['ankle'][0] + X_STAND
        if abs(pos[f] - want) > 1:
            steps[f].append((WALK1 + 0.02, WALK1 + 0.32, pos[f], want)); pos[f] = want
    # sidestep toward the minimum bar (far foot leads, near follows)
    for f, a, b in (('far', 7.25, 7.62), ('near', 7.62, 8.02)):
        want = REST[f]['ankle'][0] + X_STEP2
        steps[f].append((a, b, pos[f], want)); pos[f] = want
    return steps

STEPS = plan_steps()

def foot_state(f, t):
    """World-sheet ankle position, foot pitch and swing amount."""
    x = STEPS[f][0][2]
    for (a, b, x0, x1) in STEPS[f]:
        if t < a:
            break
        if t <= b:
            u = (t - a) / (b - a)
            lift = (14 if (x1 - x0) > 40 else 8) * math.sin(math.pi * u)
            pitch = -10 * math.sin(math.pi * u) + 6 * math.sin(math.pi * min(1, u * 1.6)) * (u < 0.6)
            return np.array([x0 + (x1 - x0) * ease(u), REST[f]['ankle'][1] - lift]), pitch, math.sin(math.pi * u)
        x = x1
    return np.array([x, REST[f]['ankle'][1]]), 0.0, 0.0

def walking(t):
    return any(a <= t <= b for f in STEPS for (a, b, _, _) in STEPS[f])

# ---------------------------------------------------------------- poses
# head tilt (+ = clockwise = looking down/forward); looks up at bar label, down at rock
head_rot = Ch([(0, 2), (2.0, 0), (2.4, -9), (3.9, -10), (4.4, 5), (5.5, 6), (6.0, 4), (7.0, 3),
               (7.4, 2), (8.6, -3), (9.9, -2), (10.6, -11), (11.3, -8), (12, -6)])
lean = Ch([(0, 4), (2.5, 4), (2.95, -1.5), (3.3, 0.5), (4.3, 1.5), (5.6, 1), (7.25, 3), (8.1, 1), (10.2, -1), (12, -0.5)])
# near arm holds the rock: shoulder / elbow / wrist-tilt of the prop
near_u = Ch([(0, -22), (2.7, -22), (4.3, -24), (4.9, -38), (5.6, -36), (7.2, -25), (9.9, -24), (10.6, -30), (11.4, -32), (12, -30)])
near_f_dir = Ch([(0, -12), (2.7, -12), (4.3, -14), (4.9, -38), (5.6, -34), (7.2, -14), (9.9, -14), (10.6, -28), (12, -26)])
rock_tilt = Ch([(0, -78), (4.3, -78), (4.9, -90), (5.6, -88), (7.2, -78), (12, -82)])
# far arm: weight of 'aim' vs walking swing, and the aim target on screen
far_aim_w = Ch([(0, 0), (2.55, 0), (3.05, 1), (4.05, 1), (4.55, 0), (7.45, 0), (7.85, 1), (12, 1)])
far_u_aim = Ch([(0, -70), (3.0, -78), (4.0, -80), (7.8, -52), (9.6, -60), (10.3, -118), (11.4, -124), (12, -122)])
HAND_SWITCH_UP = 2.80      # open hand -> pointing hand (hidden in motion blur of the raise)
HAND_SWITCH_DN = 4.40
HAND_SWITCH_UP2 = 7.65

MINTOP = json.load(open(MINBAR))
def min_bar_target(t):
    i = min(len(MINTOP) - 1, int(t * FPS))
    top = MINTOP[i]
    top = 900 if top is None else min(900, max(636, top + 70))
    return np.array([566.0, top + 14])

DELIVERED = np.array([1095.0, 420.0])
DELIVERED_TOP = np.array([1080.0, 300.0])

def far_target(t):
    if t < 6:
        return DELIVERED
    # 7.8-9.6 follows the minimum bar as it rises; 10.0-10.9 sweeps up to the delivered bar
    m = min_bar_target(t)
    u = ease(min(1, max(0, (t - 9.95) / 0.9)))
    return m * (1 - u) + DELIVERED_TOP * u

# ---------------------------------------------------------------- lip sync
def mouth_track():
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(NAR_OFFSET), '-t', str(DUR + 0.2), '-i', WAV,
                          '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(float)
    hop = 16000 // FPS
    rms = np.array([np.sqrt((a[i * hop:(i + 1) * hop] ** 2).mean() + 1e-9) for i in range(N + 3)])
    rms = rms / np.percentile(rms, 92)
    lv = np.where(rms > 0.6, 2, np.where(rms > 0.1, 1, 0))
    # syllable dips: drop one level where the envelope sits below its local peak
    for i in range(2, len(rms) - 2):
        if lv[i] == 2 and rms[i] < 0.8 * rms[i - 2:i + 3].max():
            lv[i] -= 1
    # close the mouth in the gaps between words (provider word timings)
    words = json.load(open(WAV.replace('narration.wav', 'narration.voice.json')))['words']
    for i in range(len(lv)):
        tn = i / FPS + NAR_OFFSET
        inside = any(w['start'] - 0.03 <= tn <= w['end'] for w in words if w['end'] > NAR_OFFSET - 1 and w['start'] < NAR_OFFSET + DUR + 1)
        if not inside:
            lv[i] = 0
    lv = np.roll(lv, -1)                      # mouth leads the sound by one frame
    sm = lv.copy()
    for i in range(1, len(lv) - 1):           # kill single-frame flicker
        if lv[i - 1] == lv[i + 1] != lv[i]:
            sm[i] = lv[i - 1]
    return sm, rms

MOUTH, RMS = mouth_track()
MOUTH_IMG = ['head_mouth_closed', 'head_mouth_mid', 'head_mouth_open']

# ---------------------------------------------------------------- compositing
def draw(canvas, img, M):
    """M maps image-local pixels to screen pixels."""
    w, h = img.size
    pts = np.array([ap(M, p) for p in [(0, 0), (w, 0), (0, h), (w, h)]])
    x0, y0 = np.floor(pts.min(0)).astype(int) - 1
    x1, y1 = np.ceil(pts.max(0)).astype(int) + 1
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, W), min(y1, H)
    if x1 <= x0 or y1 <= y0:
        return
    inv = np.linalg.inv(M) @ T(x0, y0)
    tile = img.transform((x1 - x0, y1 - y0), Image.AFFINE, tuple(inv[:2].reshape(-1)), Image.BICUBIC)
    canvas.alpha_composite(tile, (x0, y0))

def part(canvas, name, Mworld):
    draw(canvas, IM[name], SCREEN @ Mworld @ T(*TL[name]))

def shadow(canvas, x, y, w, a):
    sh = Image.new('L', (int(w * 2) + 8, 22), 0)
    arr = np.zeros((22, int(w * 2) + 8))
    yy, xx = np.mgrid[0:22, 0:arr.shape[1]]
    arr = np.clip(1 - (((xx - arr.shape[1] / 2) / w) ** 2 + ((yy - 11) / 7) ** 2), 0, 1) ** 1.5 * a * 255
    img = Image.fromarray(np.dstack([np.zeros_like(arr)] * 3 + [arr]).astype(np.uint8), 'RGBA')
    canvas.alpha_composite(img, (int(x - img.width / 2), int(y - 11)))

IKERR = []
WALK_W = Ch([(WALK0 - 0.2, 0.0), (WALK0, 1.0), (WALK1 - 0.05, 1.0), (WALK1 + 0.4, 0.0)])
SIDE_W = Ch([(7.1, 0.0), (7.3, 1.0), (7.95, 1.0), (8.3, 0.0)])
def frame(i):
    t = i / FPS
    can = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    rx = root_x(t)
    # body height: knees bent and a bob while walking, breath otherwise
    fs = {f: foot_state(f, t) for f in ('near', 'far')}
    swing = max(fs['near'][2], fs['far'][2])
    walk_w = WALK_W(t)
    side_w = SIDE_W(t)
    dip = walk_w * (10 - 4 * swing) + side_w * (6 - 3 * swing)
    settle = 3 * math.exp(-((t - WALK1 - 0.25) / 0.18) ** 2)    # small knee give when stopping
    breath = math.sin(2 * math.pi * t / 3.4)
    ry = 3.5 + dip + settle + 0.8 * breath
    pelvis = (935, 276)
    Mroot = T(rx, ry)
    Mt = Mroot @ about(pelvis, lean(t)) @ T(935, 276) @ S(1, 1 + 0.006 * breath) @ T(-935, -276)

    # ---- legs (2-bone IK, foot flat unless swinging)
    legs = {}
    for f in ('near', 'far'):
        r = REST[f]
        hip = ap(Mt, r['hip'])
        L1 = np.hypot(*np.subtract(r['knee'], r['hip']))
        L2 = np.hypot(*np.subtract(r['ankle'], r['knee']))
        tgt, pitch, _ = fs[f]
        d = tgt - hip
        dist = min(np.hypot(*d), L1 + L2 - 0.6)
        base = math.atan2(d[1], d[0])
        A = math.acos(max(-1, min(1, (L1 ** 2 + dist ** 2 - L2 ** 2) / (2 * L1 * dist))))
        cands = [hip + L1 * np.array([math.cos(base + s * A), math.sin(base + s * A)]) for s in (1, -1)]
        knee = max(cands, key=lambda k: k[0])
        ankle = knee + L2 * (tgt - knee) / max(1e-6, np.hypot(*(tgt - knee)))
        IKERR.append((t, f, float(np.hypot(*(ankle - tgt)))))
        a1 = ang(knee - hip) - ang(np.subtract(r['knee'], r['hip']))
        a2 = ang(ankle - knee) - ang(np.subtract(r['ankle'], r['knee']))
        legs[f] = dict(
            thigh=T(*hip) @ R(a1) @ T(-r['hip'][0], -r['hip'][1]),
            shin=T(*knee) @ R(a2) @ T(-r['knee'][0], -r['knee'][1]),
            foot=T(*ankle) @ R(pitch) @ T(-r['ankle'][0], -r['ankle'][1]),
            ground_x=ankle[0], lift=REST[f]['ankle'][1] - tgt[1])

    # ---- far arm: walking swing blended with aiming at the chart
    far_sw = -0.22 * ((fs['far'][0][0] - REST['far']['ankle'][0]) - (fs['near'][0][0] - REST['near']['ankle'][0]))
    w_aim = far_aim_w(t)
    sh = PV['far_shoulder']; el = PV['far_elbow']; wr = PV['far_wrist']
    a_u = far_sw * (1 - w_aim) + far_u_aim(t) * w_aim
    Mu = Mt @ about(sh, a_u)
    elbow_w = ap(Mu, el)
    tgt_w = ap(SCREEN_INV, far_target(t))
    want = ang(tgt_w - elbow_w)
    rest_dir = ang(np.subtract(wr, el)) + a_u + lean(t)
    a_f_aim = want - rest_dir
    a_f = (far_sw * 0.5 - 6) * (1 - w_aim) + a_f_aim * w_aim
    Mf = Mu @ about(el, a_f)
    wrist_w = ap(Mf, wr)
    pointing = (HAND_SWITCH_UP <= t < HAND_SWITCH_DN) or t >= HAND_SWITCH_UP2

    # ---- near arm holding the rock
    nsh, nel, nwr = PV['near_shoulder'], PV['near_elbow'], PV['near_wrist']
    bounce = 0.0
    if 5.75 <= t <= 7.05:   # hefting the specimen twice on "about four ounces"
        bounce = 13 * abs(math.sin(math.pi * (t - 5.75) / 0.65)) * math.exp(-(t - 5.75) * 0.6)
    walk_bob = 2.5 * swing * walk_w
    a_nu = near_u(t) + walk_bob
    Mnu = Mt @ about(nsh, a_nu)
    nelw = ap(Mnu, nel)
    rest_nd = ang(np.subtract(nwr, nel)) + a_nu + lean(t)
    a_nf = near_f_dir(t) - bounce - rest_nd
    Mnf = Mnu @ about(nel, a_nf)
    nwrw = ap(Mnf, nwr)

    # ---- head
    hm = MOUTH_IMG[int(MOUTH[i])]
    nod = 1.5 * math.sin(2 * math.pi * t / 1.9) * (RMS[i] > 0.2)
    Mh = Mt @ about(PV['neck'], head_rot(t) + nod - lean(t) * 0.5) @ T(920, 80) @ S(51 / 86) @ T(-343, -638)

    # ---------------- draw back to front
    for f in ('near', 'far'):
        g = ap(SCREEN, (legs[f]['ground_x'], REST[f]['ankle'][1] + 42))
        shadow(can, g[0], g[1], 44 * SC / 1.4, 0.45 * max(0.35, 1 - legs[f]['lift'] / 20))
    # far arm behind the torso
    if pointing:
        hp = IM['hand_point']
        phi = ang((50 - 7, 6 - 62))
        Mhand = T(*wrist_w) @ R(want + 4 - phi) @ S(0.70) @ T(-7, -62)
        draw(can, hp, SCREEN @ Mhand)
    else:
        part(can, 'far_hand', Mf @ about(wr, -4 * (1 - w_aim)) @ T(wr[0] - 1002, wr[1] - 268))
    part(can, 'near_fore', Mf @ FAR_BASE)
    part(can, 'near_upper', Mu @ FAR_BASE)
    for f in ('far', 'near'):
        part(can, f + '_foot', legs[f]['foot'])
        part(can, f + '_shin', legs[f]['shin'])
        part(can, f + '_thigh', legs[f]['thigh'])
    part(can, 'torso', Mt)
    part(can, hm, Mh)
    part(can, 'near_upper', Mnu)
    part(can, 'near_fore', Mnf)
    rk = IM['hand_rock_m']
    phi_r = ang((45 - 22, 30 - 92))
    Mr = T(*nwrw) @ R(rock_tilt(t) - phi_r) @ S(0.66) @ T(-22, -92)
    draw(can, rk, SCREEN @ Mr)
    return can

if __name__ == '__main__':
    a, b = 0, N
    if '--frames' in sys.argv:
        a, b = map(int, sys.argv[sys.argv.index('--frames') + 1].split(':'))
    out = sys.stdout.buffer if OUT == '-' else open(OUT, 'wb')
    for i in range(a, b):
        out.write(frame(i).tobytes())
    out.flush()


def still(ts, bgvid, out):
    tiles = []
    for t in ts:
        i = int(t * FPS)
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(i / FPS), '-i', bgvid, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], capture_output=True).stdout
        bg = Image.frombytes('RGBA', (W, H), raw)
        bg.alpha_composite(frame(i))
        tiles.append(bg.convert('RGB'))
    return tiles
