"""EP015 v2 pilot (0-33 s): real footage first.

Frame 0 = the owner-approved cover (cover/EP015_cover_APPROVED_*). From frame 1 every shot is
real, rights-cleared footage of earlier Starship flights, clearly labelled ARCHIVE with the flight
and credit (no Flight 15 footage is free for a monetized channel). ATLAS hosts as a separate,
smaller overlay layer on a darkened presenter corner; he never stands "inside" the footage.
Graphics only add information (stamps, the Flight 15 result card).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'engine'))
import numpy as np                                   # noqa: E402
from PIL import Image                                # noqa: E402
from common import *                                 # noqa
from host import Host, Shot, seq                     # noqa: E402
from live import Seg, plate, build_plates            # noqa: E402

DUR = 33.4
OFFSET = 0.0
COVER = '/mnt/project-files/starship/EP015/cover/EP015_cover_APPROVED_1920x1080.png'

H_PLASMA, H_FLIP, H_AIM, H_NORUN, H_NOLEG, H_ARMS = 6.33, 9.49, 11.0, 12.76, 13.78, 15.31
S2, S2_TWIST, S2_BOOST, S2_CONTRAST = 20.4, 27.57, 29.94, 33.07

F5 = 'ARCHIVE · FLIGHT 5 BOOSTER CATCH · OCT 13, 2024'
F5C = 'Video: Anne Toal · CC BY 3.0 · Wikimedia Commons'
F5B = 'Video: TimBunning1 · CC0 · Wikimedia Commons'
F2 = 'ARCHIVE · FLIGHT 2 · NOV 18, 2023 · NASA'
F2C = 'Video: NASA · public domain'

SEGS = [
    Seg('B', 1 / 30, H_PLASMA, 'ift5_catch.webm', 34.3, crop=(300, 150, 1330, 748), push=(1.0, 1.15),
        focus=(0.6, 0.7), label=F5, credit=F5C),
    Seg('C', H_PLASMA, H_FLIP, 'ift5_booster_cc0.webm', 25.0, mode='portrait', push=(1.0, 1.03),
        label='ARCHIVE · FLIGHT 5 BOOSTER RETURN · SOUTH PADRE ISLAND', credit=F5B),
    Seg('D', H_FLIP, H_NORUN, 'ift5_catch.webm', 40.6, crop=(620, 390, 900, 506), push=(1.0, 1.1),
        focus=(0.6, 0.7), label=F5, credit=F5C),
    Seg('E', H_NORUN, H_ARMS, 'ift2_nasa.webm', 0.5, crop=(420, 40, 720, 405), push=(1.0, 1.08),
        focus=(0.5, 0.45), label=F2, credit=F2C, grade=2.2),
    Seg('F', H_ARMS, S2, 'ift5_catch.webm', 43.4, crop=(730, 490, 760, 428), push=(1.0, 1.12),
        focus=(0.55, 0.6), label=F5, credit=F5C),
    Seg('G', S2, S2_TWIST, 'ift2_nasa.webm', 22.0, push=(1.0, 1.12), focus=(0.5, 0.4), label=F2, credit=F2C),
    Seg('H', S2_TWIST, S2_BOOST, 'ift2_nasa.webm', 80.0, push=(1.05, 1.15), focus=(0.4, 0.3), label=F2, credit=F2C),
    Seg('I', S2_BOOST, DUR, 'ift2_nasa.webm', 165.6, crop=(420, 265, 480, 270), push=(1.0, 1.06),
        label='ARCHIVE · FLIGHT 2 BOOSTER, 2023 · NOT FLIGHT 15', credit=F2C),
]


def seg_at(t):
    cur = SEGS[0]
    for s in SEGS:
        if t >= s.t0 - 1e-9:
            cur = s
    return cur


@lru_cache(maxsize=1)
def _cover():
    return np.asarray(Image.open(COVER).convert('RGB').resize((W, H), Image.LANCZOS), np.float32)


@lru_cache(maxsize=1)
def _host_shade():
    """darkened presenter corner (bottom-left) so ATLAS reads as an overlay host, not a witness"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot((xx - 120) / 760, (yy - 1000) / 520)
    return (1 - 0.55 * np.clip(1.15 - d, 0, 1) ** 1.3)[..., None]


def background(t):
    if t < 1 / 30:
        return Image.fromarray(_cover().astype(np.uint8))
    s = seg_at(t)
    cv = Canvas(plate(s, t))
    cv.a *= _host_shade()
    _graphics(cv, s, t)
    # 4-frame flash into the first live shot, then quick fades at cuts
    if t < 0.17:
        cv.a = cv.a * smooth(t / 0.17) + _cover() * (1 - smooth(t / 0.17))
    return cv.image()


def _graphics(cv, s, t):
    v = Vec()
    if s.name == 'E':
        a1 = rng(t, H_NORUN + 0.05, H_NORUN + 0.3)
        a2 = rng(t, H_NOLEG + 0.05, H_NOLEG + 0.3)
        if a1 > 0:
            stamp(v, 'NO RUNWAY', 1360, 330, RED, 64, a1)
        if a2 > 0:
            stamp(v, 'NO LANDING LEGS', 1360, 450, RED, 64, a2)
    if s.name == 'F':
        a = rng(t, H_ARMS + 0.4, H_ARMS + 0.9) * (1 - rng(t, S2 - 0.5, S2 - 0.1))
        if a > 0:
            tag(v, 'THE TOWER ARMS · "CHOPSTICKS"', 1240, 250, YELLOW, 30, a)
    if s.name in ('G', 'H', 'I'):
        _result_card(v, t)
    if s.name == 'I':
        a = rng(t, S2_BOOST + 1.6, S2_BOOST + 1.9)
        if a > 0:
            stamp(v, 'BOOSTER LOST', 1240, 260, RED, 78, a)
    v.onto(cv)


def _result_card(v, t):
    """Flight 15 result, built line by line as the narration states it"""
    a0 = rng(t, S2 + 0.2, S2 + 0.6)
    if a0 <= 0:
        return
    x, y = 1180, 600
    v.rect(x, y, 640, 236, (8, 12, 20, 215), (255, 255, 255, 90), 2, a=a0, r=10)
    v.text('FLIGHT 15 · NOV 13-14, 2026', x + 28, y + 52, 30, (255, 255, 255), 'b', a=a0)
    a1 = rng(t, S2 + 1.6, S2 + 2.0)
    if a1 > 0:
        v.text('SHIP 42', x + 28, y + 118, 30, (220, 228, 236), 'm', a=a1)
        v.text('CAUGHT  ✓', x + 300, y + 118, 30, (120, 230, 150), 'b', a=a1)
    a2 = rng(t, S2_BOOST + 1.2, S2_BOOST + 1.6)
    if a2 > 0:
        v.text('SUPER HEAVY', x + 28, y + 184, 30, (220, 228, 236), 'm', a=a2)
        v.text('LOST  ✗', x + 300, y + 184, 30, RED, 'b', a=a2)


def overlay(t, img):
    if t < 1 / 30:                       # frame 0 is exactly the approved cover (no host, no label)
        img.paste(Image.fromarray(_cover().astype(np.uint8)))
        return
    s = seg_at(t)
    cv = Canvas(np.asarray(img, np.float32))
    v = Vec()
    a = rng(t, 0.1, 0.4)
    kicker(v, s.label, a)
    if s.credit:
        w = v.tw(s.credit, 15, 'm')
        v.text(s.credit, W - 40 - w, 60, 15, (210, 218, 228), 'm', a=0.85 * a)
    v.onto(cv)
    img.paste(cv.image())


# ------------------------------------------------------------------ ATLAS (overlay host, bottom-left)
HS = 0.5
HOST_SHOTS = [
    (-3.0, H_PLASMA, 150, FLOOR, HS, 1),
    (H_PLASMA, S2, 170, FLOOR, HS, 1),
    (S2, DUR + 1, 150, FLOOR, HS, 1),
]


def build_host(atlas):
    h = Host(atlas, [Shot(*s) for s in HOST_SHOTS], VOICE_WAV, VOICE_JSON, DUR, offset=0.0)
    # B: tracks the booster coming down toward the tower, then points at it
    h.gaze(0.0, ('s', (900, 300)), look=0.8)
    h.point(0.5, seq([(0.5, (820, 260)), (3.5, (980, 420)), (6.0, (1060, 560))], 1.2), H_PLASMA - 0.4, arm='f',
            gaze_lead=0.0)
    h.walk(1.2, 60)
    # C: the fireball over the crowd: near-hand guard, eyes on it
    h.gaze(H_PLASMA + 0.1, ('s', (1150, 420)), look=0.8)
    h.support(H_PLASMA + 0.4, H_FLIP - 0.3, 'n', offset=(16.0, -24.0))
    # D: points at the tower as the booster swings upright toward it
    h.point(H_FLIP + 0.15, (1120, 560), H_NORUN - 0.25, arm='f')
    # E: counts the two missing things
    h.walk(H_NORUN + 0.1, 70)
    h.point(H_NORUN + 0.2, seq([(H_NORUN + 0.2, (1180, 330)), (H_NOLEG + 0.05, (1180, 450))], 0.5), H_ARMS - 0.3, arm='f')
    # F: both hands frame the arms closing
    h.point(H_ARMS + 0.5, (1160, 540), S2 - 0.6, arm='f')
    h.support(H_ARMS + 1.2, S2 - 0.6, 'n', offset=(14.0, -22.0))
    h.brow(H_ARMS + 2.6, 0.7, 1.2)
    # G-I: presents the result card, then the lost booster
    h.walk(S2 + 0.2, 60)
    h.point(S2 + 1.6, (1240, 718), S2_TWIST - 0.3, arm='f')
    h.gaze(S2_TWIST + 0.1, None, look=-0.8)
    h.support(S2_TWIST + 0.2, S2_BOOST - 0.2, 'n')
    h.point(S2_BOOST + 0.3, (1000, 540), DUR - 0.2, arm='f')
    h.brow(S2_BOOST + 1.7, 0.8, 1.2)
    h.auto(emphasis=('caught', 'twist', 'runway', 'legs', 'arms', 'booster', 'never'))
    return h


# ------------------------------------------------------------------ sound
MUSIC = [(0.0, 0.75), (6.0, 0.8), (15.0, 0.95), (20.0, 0.55), (27.5, 0.7), (DUR - 1.0, 0.6), (DUR, 0.4)]
SFX = [(0.0, 'hit', -14), (0.05, 'roar', -19), (H_PLASMA - 0.25, 'whoosh', -21), (H_PLASMA + 0.2, 'plasma', -17),
       (H_FLIP - 0.25, 'whoosh', -21), (H_FLIP + 0.4, 'roar', -19), (H_NORUN + 0.1, 'stamp', -16),
       (H_NOLEG + 0.1, 'stamp', -16), (H_ARMS - 0.25, 'whoosh', -21), (H_ARMS + 0.5, 'roar', -17),
       (H_ARMS + 1.6, 'clank', -17), (S2 - 0.3, 'whoosh', -21), (S2 + 0.2, 'rumble', -15), (S2_TWIST - 0.25, 'whoosh', -22),
       (S2_BOOST + 1.55, 'hit', -14), (S2_BOOST + 1.6, 'stamp', -15)]

if __name__ == '__main__':
    build_plates(SEGS)
