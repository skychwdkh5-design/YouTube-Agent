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
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig2 import build, hand_matrix
PL, HANDS, PV = build(PARTS)      # PARTS = folder with the owner's parts pack (pNN.png)

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
SCREEN = T(300, 1045) @ S(SC) @ T(-940, -PV['ground'])
SCREEN_INV = np.linalg.inv(SCREEN)


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
    pos = {'near': REST['near']['ankle'][0] + X_OFF + 45, 'far': REST['far']['ankle'][0] + X_OFF}
    P = 0.3
    t = WALK0
    foot = 'far'
    while t < WALK1 - 0.05:
        t1 = min(t + P, WALK1 + 0.05)
        ahead = 0.12 if t1 < WALK1 - 0.2 else 0.0
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
near_u = Ch([(0, -6), (2.7, -6), (4.3, -8), (4.9, -30), (5.6, -28), (7.2, -12), (7.8, -6), (12, -6)])
near_f_dir = Ch([(0, -12), (2.7, -12), (4.3, -16), (4.9, -66), (5.6, -64), (7.2, -30), (7.8, -14), (12, -12)])
rock_tilt = Ch([(0, -48), (4.3, -50), (4.9, -88), (5.6, -86), (7.2, -62), (7.8, -50), (12, -48)])
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

# ---------------------------------------------------------------- face controls (continuous)
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from face import Face, HEAD_TL
FACE = Face(os.environ.get('ATLAS_REF', 'ref.png'), glass=False)
HEAD_DY = float(os.environ.get('HEAD_DY', '9'))

def face_tracks():
    words = [w for w in json.load(open(WAV.replace('narration.wav', 'narration.voice.json')))['words']
             if w['end'] > NAR_OFFSET - 1 and w['start'] < NAR_OFFSET + DUR + 1]
    n = N + 3
    tgt = np.clip((RMS[:n] - 0.08) / 0.85, 0, 1) ** 0.8
    wid = np.ones(n)
    for i in range(n):
        tn = i / FPS + NAR_OFFSET + 1 / FPS          # look one frame ahead
        w = next((w for w in words if w['start'] - 0.03 <= tn <= w['end']), None)
        if w is None:
            tgt[i] = 0
            continue
        txt = w['text'].lower()
        if txt[0] in 'mbp' and tn - w['start'] < 0.07:   # lips meet on m/b/p
            tgt[i] = 0
        if any(v in txt for v in ('oo', 'ou', 'ow', 'wo', 'o')) and not txt.startswith('the'):
            wid[i] = 0.82
        elif any(v in txt for v in ('ee', 'ea', 'i')):
            wid[i] = 1.05
    op = np.zeros(n); wd = np.ones(n)
    for i in range(1, n):
        k = 0.7 if tgt[i] > op[i - 1] else 0.45
        op[i] = op[i - 1] + (tgt[i] - op[i - 1]) * k
        wd[i] = wd[i - 1] + (wid[i] - wd[i - 1]) * 0.5
    return op, wd

OPEN, WIDTH = face_tracks()
BLINKS = [1.95, 4.15, 7.15, 9.65, 11.55]
def blink_at(t):
    b = 0.0
    for t0 in BLINKS:
        u = t - t0
        if 0 <= u < 0.07: b = max(b, u / 0.07)
        elif 0.07 <= u < 0.10: b = 1.0
        elif 0.10 <= u < 0.22: b = max(b, 1 - (u - 0.10) / 0.12)
    return b
look_down = Ch([(0, 0), (4.3, 0), (4.6, 0.38), (5.5, 0.38), (5.75, 0.3), (7.0, 0.3), (7.25, 0), (12, 0)])
brow = Ch([(0, 0), (1.9, 0), (2.15, 0.9), (2.9, 0.8), (3.3, 0), (5.9, 0), (6.1, 0.5), (6.7, 0.1), (7.3, -0.35),
           (8.2, -0.3), (9.0, 0.1), (9.25, 0.45), (9.6, 0.1), (10.25, 1.0), (11.0, 0.8), (11.6, 0.3), (12, 0.2)])

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
    img, M = PL[name]
    draw(canvas, img, SCREEN @ Mworld @ M)

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
    dip = walk_w * (1.0 + 7.0 * (1 - swing) ** 2) + side_w * (1.0 + 4.0 * (1 - swing) ** 2)
    settle = 3 * math.exp(-((t - WALK1 - 0.25) / 0.18) ** 2)    # small knee give when stopping
    breath = math.sin(2 * math.pi * t / 3.4)
    ry = 2.0 + dip + settle + 0.8 * breath
    pelvis = PV['pelvis']
    Mroot = T(rx, ry)
    Mt = Mroot @ about(pelvis, lean(t)) @ T(*pelvis) @ S(1, 1 + 0.006 * breath) @ T(-pelvis[0], -pelvis[1])

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
    def _au(tt):
        f2 = {f: foot_state(f, tt) for f in ('near', 'far')}
        sw2 = -0.22 * ((f2['far'][0][0] - REST['far']['ankle'][0]) - (f2['near'][0][0] - REST['near']['ankle'][0]))
        return sw2 * (1 - far_aim_w(tt)) + far_u_aim(tt) * far_aim_w(tt)
    drag = (a_u - _au(t - 0.1))           # deg per 0.1 s of shoulder rotation
    Mu = Mt @ about(sh, a_u)
    elbow_w = ap(Mu, el)
    tgt_w = ap(SCREEN_INV, far_target(t))
    want = ang(tgt_w - elbow_w)
    rest_dir = ang(np.subtract(wr, el)) + a_u + lean(t)
    a_f_aim = want - rest_dir
    a_f = (far_sw * 0.5 - 6 - 0.35 * drag) * (1 - w_aim) + (a_f_aim - 0.25 * drag) * w_aim
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

    # ---- head (painted head from the approved sheet, new helmet over it)
    nod = 1.2 * math.sin(2 * math.pi * t / 1.9) * min(1, OPEN[i] * 2)
    OLD_C = (932.5, 90.0)
    bc = PV['bubble_c']
    Mh = Mt @ about(PV['neck'], head_rot(t) + nod - lean(t) * 0.5) @ T(bc[0], bc[1] + HEAD_DY) @ S(0.9) @ T(-OLD_C[0], -OLD_C[1]) @ T(*HEAD_TL) @ S(1 / 3)
    Mhelm = Mt @ about(PV['neck'], (head_rot(t) + nod - lean(t) * 0.5) * 0.25)
    head_img = FACE.render(open_=float(OPEN[i]), width=float(WIDTH[i]),
                           blink=max(blink_at(t), look_down(t)), brow=brow(t))

    # ---------------- draw back to front
    for f in ('near', 'far'):
        g = ap(SCREEN, (legs[f]['ground_x'], PV['ground'] - 2))
        shadow(can, g[0], g[1], 44 * SC / 1.4, 0.45 * max(0.35, 1 - legs[f]['lift'] / 20))
    # far arm behind the torso
    fore_dir = ang(wrist_w - ap(Mu, el))
    if pointing:
        draw(can, HANDS['point'][0], SCREEN @ hand_matrix(HANDS['point'], wrist_w, want + 4 - 0.3 * drag, 0.95))
    else:
        draw(can, HANDS['relaxed'][0], SCREEN @ hand_matrix(HANDS['relaxed'], wrist_w, fore_dir - 4 - 0.4 * drag, 0.95))
    part(can, 'far_fore', Mf)
    part(can, 'far_upper', Mu)
    for f in ('far', 'near'):
        part(can, f + '_foot', legs[f]['foot'])
        part(can, f + '_shin', legs[f]['shin'])
        part(can, f + '_thigh', legs[f]['thigh'])
    part(can, 'pelvis', Mt)
    draw(can, head_img, SCREEN @ Mh)
    part(can, 'torso', Mt)
    part(can, 'helmet', Mhelm)
    part(can, 'near_upper', Mnu)
    part(can, 'near_fore', Mnf)
    draw(can, HANDS['rock'][0], SCREEN @ hand_matrix(HANDS['rock'], nwrw, rock_tilt(t), 1.15))
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
