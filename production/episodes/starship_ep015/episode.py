"""EP015 Starship Flight 15 - "Starship Returned From Orbit. Then They Caught It."

Original 2.5D illustration (vehicles, tower, diagrams) + NASA SVS Earth visualization, hosted
by ATLAS on the shared rig. Frame 0 is the cover (concept A, THEY CAUGHT IT); motion starts on
frame 1. No SpaceX footage is used (no monetized-use licence); every illustrated shot carries
an ILLUSTRATION / SCHEMATIC label."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'engine'))
from common import *          # noqa
from host import Host, Shot, seq   # noqa
import scenes_a as A
import scenes_b as B
import scenes_c as Cc
import scenes_d as D

DUR = round(C.duration, 2)
OFFSET = 0.0

# (start, function, kicker label)
TIMELINE = [
    (0.0, A.hook_cover, 'ILLUSTRATION · NOT FLIGHT FOOTAGE'),
    (A.H_PLASMA, A.hook_plasma, 'VISUALIZATION · NOT FLIGHT FOOTAGE'),
    (A.H_FLIP, A.hook_flip, 'ILLUSTRATION'),
    (A.H_AIM, A.hook_aim, 'ILLUSTRATION'),
    (A.H_NORUN, A.hook_norun, 'ILLUSTRATION'),
    (A.H_ARMS, A.hook_arms, 'ILLUSTRATION'),
    (A.S2, A.split, 'ILLUSTRATION · SCHEMATIC MAP, NOT TO SCALE'),
    (A.S3, A.rewind, ''),
    (A.S3_LIFT - 4.0, A.launch, 'ILLUSTRATION · NOT FLIGHT FOOTAGE'),
    (A.S4, A.staging, 'ILLUSTRATION'),
    (A.S4_SPLIT, A.two_outcomes, 'SCHEMATIC'),
] + B.TIMELINE + Cc.TIMELINE + D.TIMELINE
TIMELINE.sort(key=lambda r: r[0])


def entry_at(t):
    cur = TIMELINE[0]
    for e in TIMELINE:
        if t >= e[0] - 1e-9:
            cur = e
    return cur


def background(t):
    cv = Canvas()
    e = entry_at(t)
    e[1](cv, t)
    finish_frame(cv)
    vignette(cv)
    return cv.image()


def overlay(t, img):
    e = entry_at(t)
    if t < 1.0 / 30 or not e[2]:
        return
    cv = Canvas(np.asarray(img, np.float32))
    v = Vec()
    kicker(v, e[2])
    v.onto(cv)
    img.paste(cv.image())


# ------------------------------------------------------------------ ATLAS
# Shot = (start, end, pelvis screen x at shot start, floor y, scale, facing)
def build_host(atlas):
    T = [e[0] for e in TIMELINE] + [DUR]
    shots = []
    for sh in HOST_SHOTS:
        shots.append(Shot(*sh))
    h = Host(atlas, shots, VOICE_WAV, VOICE_JSON, DUR, offset=0.0)
    for fn in (host_a, B.host, Cc.host, D.host):
        fn(h)
    h.auto(emphasis=('caught', 'twist', 'lost', 'both', 'orbit', 'fourteen', 'twenty-six', 'plasma', 'runway',
                     'legs', 'chopsticks', 'precise', 'first', 'inspections', 'dream', 'data', 'milestones'))
    return h


HOST_SHOTS = [
    # hook
    (-3.0, A.H_PLASMA, 330, FLOOR, 0.62, 1),
    (A.H_PLASMA, A.H_AIM, 1650, FLOOR, 0.58, -1),
    (A.H_AIM, A.H_ARMS, 170, FLOOR, 0.6, 1),
    (A.H_ARMS, A.S2, 250, FLOOR, 0.78, 1),
    # split
    (A.S2, A.S2_TWIST, 1010, FLOOR, 0.62, -1),
    (A.S2_TWIST, A.S3, 900, FLOOR, 0.62, 1),
    # rewind + launch
    (A.S3, A.S3_LIFT - 4.0, 1500, FLOOR, 0.7, -1),
    (A.S3_LIFT - 4.0, A.S4, 160, FLOOR, 0.82, 1),
    # staging
    (A.S4, A.S4_SPLIT, 1640, FLOOR, 0.66, -1),
    (A.S4_SPLIT, B.S5, 1460, FLOOR, 0.66, -1),
] + B.SHOTS + Cc.SHOTS + D.SHOTS


def host_a(h):
    # cover: points at the ship over the arms (gesture already held at frame 0), gaze on it
    sx, sy = A.cover_ship_y(0)
    cam0 = Cam(*A.COVER_CAM)
    tgt0 = cam0.p(sx - 40, sy - 40)
    h.point(-2.0, tgt0, A.H_PLASMA - 1.4, gaze_lead=0.0)
    h.brow(0.4, 0.5, 1.4)
    h.walk(1.6, 70)
    # plasma: watches the ship, flinches at the heat (near-arm guard)
    h.gaze(A.H_PLASMA + 0.15, ('s', (960, 470)), look=0.8)
    h.support(A.H_PLASMA + 0.6, A.H_PLASMA + 2.4, 'n', offset=(16.0, -26.0))
    h.point(A.H_FLIP + 0.1, seq([(0, (1000, 380)), (A.H_FLIP + 1.2, (980, 300))], 0.8), A.H_AIM - 0.2, gaze_lead=0.2)
    # aim / no runway: walks toward the tower, points at the runway icon then the legs icon
    h.walk(A.H_AIM + 0.1, 110)
    h.point(A.H_NORUN + 0.1, (360, 700), A.H_NOLEG - 0.15, arm='n')
    h.point(A.H_NOLEG + 0.05, (1560, 700), A.H_ARMS - 0.4, arm='f')
    # arms: steps in, both hands frame the arms (near hand palm, far hand points at the gap)
    h.walk(A.H_ARMS + 0.2, 90)
    h.point(A.H_ARMS + 1.6, (1240, 520), A.S2 - 0.5, arm='f')
    h.support(A.H_ARMS + 2.2, A.S2 - 0.6, 'n', offset=(14.0, -22.0))
    # split: points at the caught ship (left), then turns to the lost booster (right)
    h.point(A.S2 + 0.5, (520, 420), A.S2_TWIST - 0.4)
    h.walk(A.S2_TWIST + 0.1, 60)
    h.point(A.S2_BOOST + 0.2, (1400, 360), A.S2_CONTRAST + 0.8)
    h.support(A.S2_CONTRAST + 1.2, A.S3 - 0.5, 'n')
    # rewind: watches the calendar
    h.gaze(A.S3 + 0.3, ('s', (960, 560)), look=0.7)
    # launch: walks in, points at booster then ship as they are named
    h.walk(A.S3_LIFT - 3.6, 120)
    h.brow(A.S3_LIFT + 0.3, 0.7, 1.4)
    h.gaze(A.S3_LIFT + 0.4, ('s', (1130, 400)), look=0.8)
    h.point(A.S3_BOT + 0.2, (900, 700), A.S3_TOP - 0.3, arm='f')
    h.point(A.S3_TOP + 0.2, (900, 330), A.S3_PLAN - 0.2, arm='n')
    h.support(A.S3_PLAN + 1.2, A.S3_PLAN + 3.4, 'n')
    h.walk(A.S3_PLAN + 3.8, 80)
    # staging: follows the stack, reacts to the separation
    h.gaze(A.S4 + 0.2, ('s', (900, 300)), look=0.8)
    h.brow(A.S4_SEP + 0.2, 0.7, 1.2)
    h.point(A.S4_SEP + 0.6, (1000, 260), A.S4_SPLIT - 0.4, arm='f')
    h.point(A.S4_SPLIT + 0.6, (600, 640), A.S4_SHIP - 0.2, arm='f')
    h.point(A.S4_SHIP + 0.3, (1460, 240), B.S5 - 0.5, arm='n')


# ------------------------------------------------------------------ sound (original score + designed SFX, engine/score.py)
_cuts = [e[0] for e in TIMELINE if e[0] > 0.5]
_T12 = Cc.S12_CAUGHT - 0.9                         # contact moment in the catch scene
MUSIC = [(0.0, 0.7), (6.0, 0.8), (15.0, 0.9), (20.0, 0.55), (33.0, 0.7), (41.0, 0.3), (45.0, 0.9), (52.0, 0.6),
         (71.0, 0.75), (88.0, 0.5), (99.0, 0.35), (110.0, 0.3), (122.0, 0.55), (131.0, 0.65), (154.0, 0.45),
         (187.0, 0.6), (200.0, 0.85), (211.0, 0.5), (255.0, 0.55), (270.0, 0.7), (279.0, 0.8), (_T12 - 1.0, 0.95),
         (_T12 + 0.2, 0.12), (Cc.S12_FIRST - 0.5, 0.2), (Cc.S12_FIRST + 1.0, 0.7), (310.0, 0.45), (335.0, 0.55),
         (353.0, 0.75), (363.0, 0.6), (378.0, 0.8), (DUR - 2.0, 0.4), (DUR, 0.0)]
SFX = [(0.0, 'hit', -14), (0.05, 'roar', -19), (2.9, 'roar', -21)]
SFX += [(t - 0.3, 'whoosh', -21) for t in _cuts if not (_T12 - 3 < t < _T12 + 6)]
SFX += [(A.H_PLASMA, 'plasma', -15), (A.H_FLIP + 0.3, 'rumble', -16), (A.H_AIM, 'roar', -20),
        (A.H_NORUN + 0.1, 'stamp', -16), (A.H_NOLEG + 0.1, 'stamp', -16), (A.H_ARMS + 0.2, 'clank', -18),
        (A.S2_BOOST + 2.4, 'lost', -19), (A.S2_CONTRAST, 'stamp', -14), (A.S2_CONTRAST + 0.12, 'stamp', -16),
        (A.S3 + 0.2, 'send', -22), (A.S3_LIFT - 0.6, 'rumble', -11), (A.S3_LIFT + 1.6, 'rumble', -13),
        (A.S3_LIFT + 4.0, 'roar', -16), (A.S3_BOT, 'tick', -20), (A.S3_TOP, 'tick', -20), (A.S3_PLAN + 1.2, 'send', -20),
        (A.S4_SEP, 'hit', -14), (A.S4_SEP + 0.2, 'roar', -18), (A.S4_SEP + 3.6, 'rumble', -19),
        (B.S5_EARLIER + 0.3, 'arrive', -22), (B.S5_CALLED, 'lost', -17), (B.S5_DIV, 'hit', -18), (B.S5_NOT, 'stamp', -17),
        (B.S5_REPORTS, 'tick', -19), (B.S6 + 0.5, 'roar', -22), (B.S7_ALT, 'tick', -20),
        (B.S7_HOURS, 'arrive', -20), (B.S8_SPEED, 'send', -20), (B.S8_DROP + 0.4, 'stamp', -19),
        (Cc.S9_FIRE, 'rumble', -18), (Cc.S9_AIR, 'plasma', -16), (Cc.S9_PLASMA, 'plasma', -14), (Cc.S9_PLASMA + 2.6, 'plasma', -17),
        (Cc.S10_LIT + 0.3, 'rumble', -21), (Cc.S10_CHOP, 'clank', -22), (Cc.S10_IDEA + 0.6, 'tick', -19),
        (Cc.S11_PLACE + 1.8, 'tick', -18), (Cc.S11_SPEED + 1.8, 'tick', -18), (Cc.S11_PIECE, 'arrive', -21)]
# the catch: engines roar while it descends, contact clank, hiss, then quiet
SFX += [(Cc.S12 + 0.4 + 2.6 * k, 'roar', -15) for k in range(int((_T12 - Cc.S12 - 1.0) / 2.6) + 1)]
SFX += [(_T12 - 0.05, 'clank', -11), (_T12 + 0.35, 'hiss', -15), (_T12 + 0.4, 'hit', -17), (Cc.S12_FIRST, 'arrive', -18)]
SFX += [(B.S7_DEPLOY + 0.4 + (B.S7_CAMS - 0.6 - B.S7_DEPLOY) * i / 26, 'tick', -26) for i in range(26)]
SFX += [(B.S7_ORBITS - 0.2 + (B.S7_HOURS + 0.8 - B.S7_ORBITS) * i / 13, 'tick', -22) for i in range(13)]
SFX += [(D.S13_NOTSAME, 'stamp', -16)] + [(tc, 'tick', -19) for tc in D.CHECK_T] + [(D.S13_BOOST, 'lost', -21),
        (D.S14_D1, 'tick', -18), (D.S14_D2, 'tick', -18), (D.S14_D3, 'stamp', -17), (D.S15_WATCH, 'arrive', -20),
        (D.S16 + 0.2, 'arrive', -21), (DUR - 2.4, 'hit', -19)]
SFX += [(tm, 'tick', -19) for tm in D.S15_M]
