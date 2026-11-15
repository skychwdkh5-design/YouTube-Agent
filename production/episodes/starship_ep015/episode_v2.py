"""EP015 v2 (full episode): real footage first, no host.

Frame 0 = the owner-approved cover (cover/EP015_cover_APPROVED_*). From frame 1 every shot is
real, rights-cleared footage of earlier Starship flights, clearly labelled ARCHIVE with the flight
and credit (no Flight 15 footage is free for a monetized channel). No ATLAS (owner decision
2026-11-15). Short v1 explainer graphics (episode.py, labelled SCHEMATIC / ILLUSTRATION / NASA SVS)
fill only the beats no free footage can show: the abort map, orbit, re-entry physics, the ship catch.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'engine'))
import numpy as np                                   # noqa: E402
from PIL import Image                                # noqa: E402
from common import *                                 # noqa
import episode as V1                                 # noqa: E402
from live import Seg, plate, build_plates            # noqa: E402

OFFSET = 0.0
DUR = V1.DUR
NO_HOST = True
COVER = '/mnt/project-files/starship/EP015/cover/EP015_cover_APPROVED_1920x1080.png'

H_PLASMA, H_FLIP, H_AIM, H_NORUN, H_NOLEG, H_ARMS = 6.33, 9.49, 11.0, 12.76, 13.78, 15.31
S2, S2_TWIST, S2_BOOST, S2_CONTRAST = 20.4, 27.57, 29.94, 33.07

F5 = 'ARCHIVE · FLIGHT 5 BOOSTER CATCH · OCT 13, 2024'
F5C = 'Video: Anne Toal · CC BY 3.0 · Wikimedia Commons'
F5B = 'Video: TimBunning1 · CC0 · Wikimedia Commons'
F2 = 'ARCHIVE · FLIGHT 2 · NOV 18, 2023 · NASA'
F2C = 'Video: NASA · public domain'

A, B5, C3, D4 = V1.A, V1.B, V1.Cc, V1.D
F5W = 'ARCHIVE · FLIGHT 5 · EARLIER BOOSTER CATCH · OCT 13, 2024'
F2X = 'ARCHIVE · FLIGHT 2 · NOV 18, 2023 · NASA · NOT FLIGHT 15'
WIDE = (300, 150, 1330, 748)
TIGHT = (620, 390, 900, 506)
PAD = (420, 40, 720, 405)
F2A = 'ARCHIVE · FLIGHT 2 · NOV 18, 2023 · CBP AEROSTAT · NOT FLIGHT 15'
F2AC = 'Video: U.S. Customs and Border Protection · public domain'
V = 'V1'                      # marker: this beat uses the v1 explainer graphic

SEGS = [
    # ---- hook (approved pilot, 0-33 s)
    Seg('B', 1 / 30, H_PLASMA, 'ift5_catch.webm', 34.3, crop=WIDE, push=(1.0, 1.15), focus=(0.6, 0.7), label=F5, credit=F5C),
    Seg('C', H_PLASMA, H_FLIP, 'ift5_booster_cc0.webm', 25.0, mode='portrait', push=(1.0, 1.03),
        label='ARCHIVE · FLIGHT 5 BOOSTER RETURN · SOUTH PADRE ISLAND', credit=F5B),
    Seg('D', H_FLIP, H_NORUN, 'ift5_catch.webm', 40.6, crop=TIGHT, push=(1.0, 1.1), focus=(0.6, 0.7), label=F5, credit=F5C),
    Seg('E', H_NORUN, H_ARMS, 'ift2_nasa.webm', 0.5, crop=PAD, push=(1.0, 1.08), focus=(0.5, 0.45), label=F2, credit=F2C, grade=2.2),
    Seg('F', H_ARMS, S2, 'ift5_catch.webm', 43.4, crop=(730, 490, 760, 428), push=(1.0, 1.12), focus=(0.55, 0.6), label=F5, credit=F5C),
    Seg('G', S2, S2_TWIST, 'ift2_nasa.webm', 22.0, push=(1.0, 1.12), focus=(0.5, 0.4), label=F2, credit=F2C),
    Seg('H', S2_TWIST, S2_BOOST, 'ift2_nasa.webm', 80.0, push=(1.05, 1.15), focus=(0.4, 0.3), label=F2, credit=F2C),
    Seg('I', S2_BOOST, S2_CONTRAST, 'ift2_nasa.webm', 165.6, crop=(420, 265, 480, 270), push=(1.0, 1.06),
        label='ARCHIVE · FLIGHT 2 BOOSTER, 2023 · NOT FLIGHT 15', credit=F2C),
    # ---- the crowd, then the launch
    Seg('J', S2_CONTRAST, A.S3, 'ift5_booster_cc0.webm', 30.0, mode='portrait', push=(1.0, 1.04),
        label='ARCHIVE · FLIGHT 5 · SOUTH PADRE ISLAND CROWD', credit=F5B),
    Seg('L', A.S3, A.S4, 'ift2_aerostat.webm', 9.0, push=(1.0, 1.10), focus=(0.5, 0.35), label=F2A, credit=F2AC, grade=1.4),
    Seg('M', A.S4, 80.6, 'ift2_nasa.webm', 100.0, push=(1.0, 1.12), focus=(0.35, 0.4), label=F2X, credit=F2C),
    Seg('K6', 80.6, B5.S5, 'cira6.webm', 0.0, crop=(960, 180, 960, 540), speed=0.72, push=(1.0, 1.08), focus=(0.5, 0.5),
        label='ARCHIVE · FLIGHT 6 SEEN FROM ORBIT · NOV 19, 2024 · GOES · NOT FLIGHT 15', credit='Imagery: NOAA / CIRA'),
    # ---- booster: earlier catches were real, this one was called off
    Seg('N', B5.S5, B5.S5_RETURN, 'ift5_catch.webm', 30.5, crop=WIDE, push=(1.0, 1.12), focus=(0.6, 0.7), label=F5W, credit=F5C),
    Seg(V, B5.S5_RETURN, B5.S6),
    Seg('O', B5.S6, B5.S7, 'ift2_nasa.webm', 160.0, crop=(420, 265, 480, 270), push=(1.0, 1.06),
        label='ARCHIVE · FLIGHT 2 BOOSTER, 2023 · NOT FLIGHT 15', credit=F2C),
    # ---- orbit (NASA SVS), speed over real ascent footage, then re-entry explainer
    Seg(V, B5.S7, B5.S8_WHETHER),
    Seg('P', B5.S8_WHETHER, B5.S8_KEEP, 'ift2_nasa.webm', 40.0, push=(1.0, 1.12), focus=(0.45, 0.4), label=F2X, credit=F2C),
    Seg(V, B5.S8_KEEP, C3.S10_TARGET),
    # ---- the target: the tower and its arms
    Seg('Q', C3.S10_TARGET, C3.S10_LEGS, 'ift2_nasa.webm', 0.3, crop=PAD, push=(1.0, 1.15), focus=(0.6, 0.35),
        label=F2X, credit=F2C, grade=2.2),
    Seg('AT', C3.S10_LEGS, C3.S11, 'ift2_aerostat.webm', 0.0, crop=(560, 0, 800, 450), speed=0.62, push=(1.0, 1.10),
        focus=(0.5, 0.4), label=F2A, credit=F2AC, grade=1.4),
    Seg('R', C3.S11, C3.S11_END_SEQ, 'ift5_catch.webm', 35.0, crop=WIDE, push=(1.0, 1.18), focus=(0.62, 0.72), label=F5W, credit=F5C),
    Seg(V, C3.S11_END_SEQ, D4.S13),
    # ---- after the catch
    Seg('S', D4.S13, D4.S13_INSPECT, 'ift5_booster_cc0.webm', 34.0, mode='portrait', push=(1.0, 1.04),
        label='ARCHIVE · FLIGHT 5 · SOUTH PADRE ISLAND CROWD', credit=F5B),
    Seg('Y', D4.S13_INSPECT, 326.8, 'ift1_wb57.webm', 228.0, crop=(0, 40, 1936, 1089), push=(1.0, 1.06),
        label='ARCHIVE · FLIGHT 1 · APR 20, 2023 · NASA WB-57 · NOT FLIGHT 15', credit=F2C),
    Seg('Z', 326.8, D4.S14, 'ship25_debris.webm', 0.0, crop=(300, 60, 1320, 742), speed=0.6, push=(1.0, 1.06),
        label='ARCHIVE · FLIGHT 2 SHIP DEBRIS ON WEATHER RADAR · NOV 18, 2023 · NOT FLIGHT 15',
        credit='Radar: NOAA / National Weather Service · public domain', grade=0.5),
    Seg('T', D4.S14, D4.S14_NOTDATA, 'ift2_nasa.webm', 8.0, push=(1.0, 1.12), focus=(0.5, 0.4), label=F2X, credit=F2C, grade=1.6),
    Seg(V, D4.S14_NOTDATA, D4.S15),
    Seg('U', D4.S15, D4.S16, 'ift5_catch.webm', 30.0, crop=WIDE, push=(1.0, 1.15), focus=(0.6, 0.7), label=F5W, credit=F5C),
    Seg('X', D4.S16, DUR + 0.5, 'ift5_catch.webm', 46.0, crop=WIDE, push=(1.0, 1.10), focus=(0.6, 0.75), label=F5W, credit=F5C),
]
LIVE = [s for s in SEGS if s.name != V]


def seg_at(t):
    cur = SEGS[0]
    for s in SEGS:
        if t >= s.t0 - 1e-9:
            cur = s
    return cur


@lru_cache(maxsize=1)
def _cover():
    return np.asarray(Image.open(COVER).convert('RGB').resize((W, H), Image.LANCZOS), np.float32)


def background(t):
    if t < 1 / 30:
        return Image.fromarray(_cover().astype(np.uint8))
    s = seg_at(t)
    if s.name == V:
        img = V1.background(t)
        V1.overlay(t, img)                 # its own SCHEMATIC / ILLUSTRATION / NASA SVS label
        cv = Canvas(np.asarray(img, np.float32))
    else:
        cv = Canvas(plate(s, t))
        _graphics(cv, s, t)
    # short dip at every cut (live <-> graphic), first cut flashes out of the cover
    if t < 0.17:
        cv.a = cv.a * smooth(t / 0.17) + _cover() * (1 - smooth(t / 0.17))
    else:
        k = min(abs(t - s.t0), abs(s.t1 - t)) if s.t0 > 1 else 1.0
        if k < 0.1:
            cv.a *= 0.55 + 0.45 * (k / 0.1)
    if t > DUR - 1.2:
        cv.a *= max(0.0, (DUR - t) / 1.2)
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
    if s.name == 'L':
        a = rng(t, A.S3 + 0.3, A.S3 + 0.8) * (1 - rng(t, A.S3_LIFT + 3, A.S3_LIFT + 3.5))
        if a > 0:
            tag(v, 'FLIGHT 15 · STARBASE, TEXAS · NOV 13, 2026', 120, 200, (255, 255, 255), 34, a)
        a = rng(t, A.S3_BOT, A.S3_BOT + 0.4) * (1 - rng(t, A.S3_TOP - 0.3, A.S3_TOP))
        if a > 0:
            tag(v, 'BOTTOM: SUPER HEAVY BOOSTER', 120, 200, YELLOW, 34, a)
        a = rng(t, A.S3_TOP, A.S3_TOP + 0.4) * (1 - rng(t, A.S3_PLAN - 0.3, A.S3_PLAN))
        if a > 0:
            tag(v, 'TOP: THE SHIP · THE SPACECRAFT', 120, 200, YELLOW, 34, a)
        a = rng(t, A.S3_PLAN + 1.0, A.S3_PLAN + 1.5) * (1 - rng(t, A.S4 - 0.4, A.S4))
        if a > 0:
            tag(v, 'THE PLAN: CATCH BOTH STAGES ON ONE FLIGHT', 120, 200, (255, 255, 255), 34, a)
    if s.name == 'M':
        a = rng(t, A.S4_SEP, A.S4_SEP + 0.4)
        if a > 0:
            tag(v, 'STAGE SEPARATION', 120, 200, YELLOW, 36, a * (1 - rng(t, A.S4_SPLIT - 0.4, A.S4_SPLIT)))
        a = rng(t, A.S4_SPLIT + 1.0, A.S4_SPLIT + 1.4)
        if a > 0:
            tag(v, 'SUPER HEAVY  →  BACK TOWARD THE COAST', 120, 200, (238, 136, 89), 34, a * (1 - rng(t, A.S4_SHIP - 0.3, A.S4_SHIP)))
        a = rng(t, A.S4_SHIP + 0.2, A.S4_SHIP + 0.6)
        if a > 0:
            tag(v, 'THE SHIP  →  HEADING FOR ORBIT', 120, 200, (140, 200, 255), 34, a)
    if s.name in ('N', 'R', 'U'):
        a = rng(t, s.t0 + 0.6, s.t0 + 1.1) * (1 - rng(t, s.t1 - 0.6, s.t1 - 0.2))
        txt = {'N': 'BOOSTER CATCHES HAD WORKED BEFORE', 'R': 'THE TOWER CAN\'T MOVE: THE ROCKET MUST HIT THE GAP',
               'U': 'NEXT: FLY IT AGAIN · CATCH BOTH STAGES'}[s.name]
        if a > 0:
            tag(v, txt, 120, 200, YELLOW, 34, a)
    if s.name == 'O':
        a = rng(t, B5.S6 + 1.0, B5.S6 + 1.4) * (1 - rng(t, B5.S6_YET - 0.3, B5.S6_YET))
        if a > 0:
            tag(v, 'ONE HALF LOST', 120, 200, RED, 40, a)
        a = rng(t, B5.S6_YET + 0.2, B5.S6_YET + 0.6)
        if a > 0:
            tag(v, 'THE OTHER HALF: STILL CLIMBING TO ORBIT', 120, 200, (140, 200, 255), 34, a)
    if s.name == 'P':
        a = rng(t, B5.S8_SPEED, B5.S8_SPEED + 0.5)
        if a > 0:
            tag(v, 'LOW ORBIT ≈ 17,000 MPH · 28,000 KM/H', 120, 200, (255, 255, 255), 38, a)
    if s.name == 'Q':
        a = rng(t, C3.S10_CHOP - 0.2, C3.S10_CHOP + 0.3)
        if a > 0:
            tag(v, 'THE TARGET: THE GAP BETWEEN THE ARMS', 980, 300, YELLOW, 32, a)
    if s.name == 'T':
        a = rng(t, D4.S14_AGAIN, D4.S14_AGAIN + 0.4)
        if a > 0:
            tag(v, 'GOAL: FLY THE SAME ROCKET AGAIN', 120, 200, (255, 255, 255), 36, a)
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
    if t < 1 / 30:                       # frame 0 is exactly the approved cover
        img.paste(Image.fromarray(_cover().astype(np.uint8)))
        return
    s = seg_at(t)
    if s.name == V:
        return
    cv = Canvas(np.asarray(img, np.float32))
    v = Vec()
    a = rng(t, 0.1, 0.4)
    kicker(v, s.label, a)
    if s.credit:
        w = v.tw(s.credit, 15, 'm')
        v.text(s.credit, W - 40 - w, 60, 15, (210, 218, 228), 'm', a=0.85 * a)
    v.onto(cv)
    img.paste(cv.image())


# ------------------------------------------------------------------ sound
# v1 score envelope and designed SFX (same narration timing), plus whooshes at the new live cuts
MUSIC = V1.MUSIC
SFX = [x for x in V1.SFX if x[0] >= S2_CONTRAST] + [
    (0.0, 'hit', -14), (0.05, 'roar', -19), (H_PLASMA - 0.25, 'whoosh', -21), (H_PLASMA + 0.2, 'plasma', -17),
    (H_FLIP - 0.25, 'whoosh', -21), (H_FLIP + 0.4, 'roar', -19), (H_NORUN + 0.1, 'stamp', -16),
    (H_NOLEG + 0.1, 'stamp', -16), (H_ARMS - 0.25, 'whoosh', -21), (H_ARMS + 0.5, 'roar', -17),
    (H_ARMS + 1.6, 'clank', -17), (S2 - 0.3, 'whoosh', -21), (S2 + 0.2, 'rumble', -15), (S2_TWIST - 0.25, 'whoosh', -22),
    (S2_BOOST + 1.55, 'hit', -14), (S2_BOOST + 1.6, 'stamp', -15)]
# real NASA launch audio (public domain) under these live shots: (episode t0, t1, source start)
NASA_AUDIO = [(S2, S2_CONTRAST, 22.0), (A.S3, A.S4, 6.8), (D4.S14, D4.S14_NOTDATA, 8.0)]

if __name__ == '__main__':
    build_plates(LIVE)
