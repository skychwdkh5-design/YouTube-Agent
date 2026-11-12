"""EP014 Artemis II - v2 visual direction (v1 was rejected as a slideshow).

The observation is told as it developed: where Orion was, why the Moon cut the radio link,
what the crew could see out of the window, why the dark Moon matters, what an impact flash is
(NASA's own animation), how the three crew colours are read on the annotated view, how images and
notes combine, and how the record reached the ground. NASA material stays in frames with its
labels; ATLAS stays outside and gets small during key shots. Our graphics are labelled
SCHEMATIC / ILLUSTRATION; no flash is drawn as if it were observed."""
import math
import os
import sys
from functools import lru_cache

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine_path import *                     # noqa
from host import Host, Shot, seq
from cues import Cues
from gfx import Frame, Video, rng, smooth, lerp, clamp
import scenes
from scenes import retro, MARKS, NOTE

VOICE_DIR = '/mnt/project-files/artemis/EP014/voice'
VOICE_WAV = os.path.join(VOICE_DIR, 'narration.wav')
VOICE_JSON = os.path.join(VOICE_DIR, 'narration.voice.json')
C = Cues(VOICE_JSON)
OFFSET = 0.0
MEDIA = '/mnt/project-files/media_v2/cuts'

PAPER = (250, 240, 222)
CREAM = (247, 226, 190)
ORANGE = (240, 122, 30)
RED = (232, 70, 40)
BLUE = (110, 170, 255)
GREEN = (120, 220, 120)
PURPLE = (190, 130, 255)


def c(p, after=0.0):
    return C.at(p, after)


def ce(p, after=0.0):
    return C.end(p, after)


S = {}
S['cover'] = 0.0
S['crew'] = c('Three astronauts') - 0.2
S['geo'] = c('Orion was about') - 0.2
S['view'] = c("Here's what the crew") - 0.2
S['blackout'] = c('When Orion moved') - 0.2
S['dark'] = c('This was a rare chance') - 0.2
S['impact'] = c('Picture a small piece') - 0.2
S['notes'] = c('Now look at the') - 0.2
S['two'] = c('An astronaut seeing') - 0.2
S['back'] = c('Once communications came') - 0.2
S['why'] = c('This is why scientists') - 0.2
S['fin'] = c('That makes these') - 0.25
ORDER = ['cover', 'crew', 'geo', 'view', 'blackout', 'dark', 'impact', 'notes', 'two', 'back', 'why', 'fin']
DUR = round(C.last_end() + 1.6, 2)

BIG = (250, 1800, 2.9, 1)
SMALL = (205, 1000, 0.58, 1)
MED = (215, 1000, 0.82, 1)
PLACE = dict(cover=BIG, crew=SMALL, geo=MED, view=SMALL, blackout=MED, dark=SMALL, impact=MED, notes=SMALL,
             two=MED, back=MED, why=SMALL, fin=BIG)
BOX = (282, 34, 958, 539)


def end_of(k):
    i = ORDER.index(k)
    return S[ORDER[i + 1]] if i + 1 < len(ORDER) else DUR


def scene_at(t):
    cur = ORDER[0]
    for k in ORDER:
        if t >= S[k]:
            cur = k
    return cur


def P(x, y):
    return (x * 1.5, y * 1.5)


@lru_cache(maxsize=None)
def V(name):
    return Video(os.path.join(MEDIA, name + '.mp4'))


@lru_cache(maxsize=None)
def still(name):
    return Image.open(scenes.A(name)).convert('RGB')


# ------------------------------------------------------------------ helpers
def bg(f):
    f.background('#2a2119', '#0d0a08')


def box_frame(f, label=None, credit=None, box=BOX, a=1.0):
    x, y, w, h = box
    f.rect(x - 2, y - 2, w + 4, h + 4, None, CREAM + (int(150 * a),), 1.4)
    if label:
        f.text(label, x, y + h + 20, 12.5, ORANGE, 'mono', alpha=a)
    if credit:
        f.text(credit, x + w, y + h + 20, 12.5, CREAM, 'mono_r', 'right', alpha=a * 0.85)


def in_box(f, im, box=BOX, zoom=1.0, fx=0.5, fy=0.5, alpha=1.0):
    x, y, w, h = box
    f.image(None, x, y, w, h, zoom=zoom, fx=fx, fy=fy, alpha=alpha, frame=im)


def img_to_box(p, size, box, z, fx, fy):
    """image pixel -> design px inside a cover-cropped box"""
    x, y, w, h = box
    iw, ih = size
    sw = min(iw, ih * w / h) / z
    sh = sw * h / w
    x0, y0 = (iw - sw) * fx, (ih - sh) * fy
    return x + (p[0] - x0) / sw * w, y + (p[1] - y0) / sh * h


def stamp(f, s, x, y, k, col=ORANGE, n=22):
    if k <= 0:
        return
    a = clamp(k * 3)
    w = f.text_w(s, n, 'mono') + 30
    f.rect(x - w / 2, y - n - 8, w, n + 22, (20, 14, 10, int(225 * a)), col + (int(255 * a),), 2.2)
    f.text(s, x, y + 2, n, col, 'mono', 'center', alpha=a)


def moon_disc(f, x, y, r, lit=0.0, col=(120, 116, 110)):
    """schematic Moon: dark disc with a lit limb share 0..1 (sun from the right)."""
    f.circle(x, y, r, (34, 32, 30), CREAM + (120,), 1.4)
    if lit > 0:
        f.arc(x, y, r * 0.93, -90, 90, col + (200,), max(1.0, r * 0.14 * lit))


def earth_disc(f, x, y, r):
    f.glow(x, y, r * 2.2, (90, 160, 210), 0.35)
    f.circle(x, y, r, (40, 80, 120), (190, 220, 235), 1.6)
    for dx, dy, rr in [(-0.3, -0.25, 0.32), (0.25, 0.1, 0.28), (-0.05, 0.42, 0.2)]:
        f.circle(x + dx * r, y + dy * r, rr * r, (96, 128, 88, 200))


def orion_icon(f, x, y, s=1.0, a=1.0):
    f.poly([(x - 9 * s, y + 7 * s), (x + 9 * s, y + 7 * s), (x + 4 * s, y - 8 * s), (x - 4 * s, y - 8 * s)],
           PAPER + (int(255 * a),), ORANGE + (int(255 * a),), 1.2)
    f.rect(x - 7 * s, y + 7 * s, 14 * s, 9 * s, (120, 110, 100, int(255 * a)))
    f.line([(x - 22 * s, y + 12 * s), (x - 8 * s, y + 12 * s)], ORANGE + (int(200 * a),), 2)
    f.line([(x + 8 * s, y + 12 * s), (x + 22 * s, y + 12 * s)], ORANGE + (int(200 * a),), 2)


# ------------------------------------------------------------------ cover (frame 0 == cover)
CV1 = S['crew']


def mark_rings(f, t, cam_s, fxy, t0s, scale=1.0):
    fx, fy = fxy
    for i, (mx, my) in enumerate(MARKS):
        k = smooth(rng(t, t0s[i], t0s[i] + 0.25))
        if k <= 0:
            continue
        x = fx + (mx - fx) * cam_s
        y = fy + (my - fy) * cam_s
        pul = 0.5 + 0.5 * math.sin((t - t0s[i]) * 6.0)
        f.circle(x / 1.5, y / 1.5, (26 + 8 * pul) * cam_s * scale / 1.5 + 4, None, ORANGE, 3, alpha=k * (0.45 + 0.55 * pul))


def bg_cover(t):
    if t <= 1e-6:
        return scenes.cover(0.0)
    push = 0.45 * smooth(rng(t, 0.1, CV1))
    img = scenes.cover(t, push=push, title_out=0.0)
    f = Frame(img)
    s = 1 + 0.9 * smooth(push)
    mark_rings(f, t, s, MARKS[2], [0.25 + 0.45 * i for i in range(5)])
    a = smooth(rng(t, 0.5, 0.9))
    f.pill('CONCEPT ILLUSTRATION  ·  MARKS ARE NOT OBSERVED LOCATIONS', 470, 690, 'paper', 15) if a > 0.5 else None
    return f.done()


# ------------------------------------------------------------------ crew: the three astronauts and their marks
CR_MARK = c('marked where they saw them')


def notes_view(f, t, z, fx=0.51, fy=0.47, box=BOX, alpha=1.0):
    in_box(f, still('moon_notes.jpg'), box, z, fx, fy, alpha)


def nxy(key, z, fx=0.51, fy=0.47, box=BOX):
    return img_to_box(NOTE[key], (2200, 1238), box, z, fx, fy)


def bg_crew(t):
    f = Frame()
    bg(f)
    x, y, w, h = BOX
    sw = smooth(rng(t, CR_MARK - 0.5, CR_MARK + 0.1))
    if sw < 1:
        in_box(f, V('a_crew_cabin').at(1.0 + (t - S['crew']) * 0.55), zoom=1.3, fy=0.12, alpha=1.0)
    if sw > 0:
        z = 1.0 + 0.04 * rng(t, CR_MARK, S['geo'])
        notes_view(f, t, z, alpha=sw)
        for i, (key, col) in enumerate((('reid', BLUE), ('ike', GREEN), ('jeremy', RED))):
            k = smooth(rng(t, CR_MARK + 0.35 + 0.45 * i, CR_MARK + 0.6 + 0.45 * i))
            if k > 0:
                px, py = nxy(key, z)
                f.circle(px, py, 56, None, col, 3, alpha=k)
    lab = 'NASA VIDEO · ARTEMIS II CREW ABOARD ORION' if sw < 0.5 else "NASA · CREW ANNOTATIONS ON A SIMULATED VIEW OF THE MOON"
    box_frame(f, lab, 'NASA SVS 15103' if sw < 0.5 else 'NASA ARTEMIS II PRELIMINARY LUNAR SCIENCE REPORT')
    return retro(f.done(), 0.3)


# ------------------------------------------------------------------ geometry: where Orion was
G_MILES = c('forty-six thousand miles')
G_POINT = c('And at that point')
G_BETWEEN = c('the Moon was between')
G_EARTH = c('spacecraft and Earth')


def geo_layout(t):
    """design px of Earth, Moon, Orion on the schematic line"""
    return (330, 330), (820, 330), (1070, 330)


def bg_geo(t):
    f = Frame()
    bg(f)
    x, y, w, h = BOX
    sch = smooth(rng(t, G_POINT - 0.4, G_POINT + 0.3))
    if sch < 1:
        in_box(f, V('a_missionmap').at(6.0 + (t - S['geo']) * 1.6), alpha=1 - sch)
        m = smooth(rng(t, G_MILES - 0.1, G_MILES + 0.3))
        if m > 0:
            f.rect(x + w - 330, y + 20, 310, 96, (12, 9, 7, int(225 * m * (1 - sch))), CREAM + (int(90 * m),), 1)
            f.text('≈ 46,000 MILES', x + w - 175, y + 66, 30, PAPER, 'sans', 'center', alpha=m * (1 - sch))
            f.text('≈ 74,000 KM AWAY', x + w - 175, y + 94, 14, CREAM, 'mono_r', 'center', alpha=m * (1 - sch))
        box_frame(f, 'NASA ANIMATION · ARTEMIS II FLIGHT PATH', 'NASA / JSC (SVS 20412)', a=1 - sch)
    if sch > 0:
        f.group(sch)
        f.starfield(t, 60)
        (ex, ey), (mx, my), (ox, oy) = geo_layout(t)
        earth_disc(f, ex, ey, 34)
        f.text('EARTH', ex, ey + 62, 13, CREAM, 'mono', 'center')
        moon_disc(f, mx, my, 70, lit=0.3)
        f.text('MOON', mx, my + 98, 13, CREAM, 'mono', 'center')
        come = smooth(rng(t, G_POINT, G_POINT + 1.2))
        orion_icon(f, lerp(1240, ox, come), oy - 6)
        f.text('ORION', lerp(1240, ox, come), oy + 40, 13, ORANGE, 'mono', 'center')
        # line of sight from Orion back toward Earth: stopped by the Moon
        ls = smooth(rng(t, G_BETWEEN, G_EARTH + 0.4))
        if ls > 0:
            end = lerp(ox - 14, mx + 70, ls)
            f.line([(ox - 14, oy), (end, oy)], ORANGE + (230,), 2.5, dash=(9, 6))
            if ls > 0.98:
                f.line([(mx + 62, oy - 14), (mx + 86, oy + 14)], RED + (255,), 3)
                f.line([(mx + 62, oy + 14), (mx + 86, oy - 14)], RED + (255,), 3)
            f.line([(mx - 70, oy), (ex + 40, oy)], CREAM + (int(60 * ls),), 1.2, dash=(4, 8))
        btw = smooth(rng(t, G_EARTH, G_EARTH + 0.4))
        f.text('THE MOON IS BETWEEN ORION AND EARTH', 706, 160, 22, ORANGE, 'mono', 'center', alpha=btw)
        f.text('SCHEMATIC · NOT TO SCALE', 290, 684, 13, ORANGE, 'mono')
        f.end()
    return retro(f.done(), 0.35)


# ------------------------------------------------------------------ view: the crew's window (NASA simulation)
def bg_view(t):
    f = Frame()
    bg(f)
    lt = t - S['view']
    in_box(f, V('a_crewview').at(20 + lt * 9.0), zoom=1.15 + 0.03 * lt)
    box_frame(f, "NASA SIMULATION · THE CREW'S WINDOW VIEW, APRIL 6, 2026", 'NASA SVS 5633')
    return retro(f.done(), 0.3)


# ------------------------------------------------------------------ blackout: behind the Moon, contact drops
BL_DROP = c('radio contact with Earth')
BL_BLOCK = c('The Moon itself blocked')
BL_SPLIT = c('For a while, the people')
BL_REC = c('watching and recording')
BL_WAIT = c('had to wait')
MOON_C = (760, 340)
ORB_R = 190


def orion_ang(t):
    # Orion moves along its arc from the upper right to behind the Moon (far side, right of the disc)
    return lerp(-70, 0, smooth(rng(t, S['blackout'] + 0.2, BL_BLOCK + 0.6)))


def orion_xy_bl(t):
    a = math.radians(orion_ang(t))
    return MOON_C[0] + ORB_R * math.cos(a) * 1.6, MOON_C[1] + ORB_R * math.sin(a) * 0.9


def bg_blackout(t):
    f = Frame()
    bg(f)
    split = smooth(rng(t, BL_SPLIT - 0.3, BL_SPLIT + 0.4))
    if split < 1:
        f.group(1 - split)
        f.starfield(t, 60)
        mx, my = MOON_C
        moon_disc(f, mx, my, 120, lit=0.25)
        f.text('MOON', mx, my + 148, 13, CREAM, 'mono', 'center')
        # arrow to Earth (far to the left)
        f.line([(330, my), (220, my)], CREAM + (150,), 2)
        f.poly([(212, my), (226, my - 8), (226, my + 8)], CREAM + (150,))
        f.text('TO EARTH', 260, my - 16, 13, CREAM, 'mono', 'center')
        # Orion's path
        pts = []
        for a in range(-80, 30, 4):
            r = math.radians(a)
            pts.append((mx + ORB_R * math.cos(r) * 1.6, my + ORB_R * math.sin(r) * 0.9))
        f.line(pts, ORANGE + (90,), 1.6, dash=(6, 6))
        ox, oy = orion_xy_bl(t)
        orion_icon(f, ox, oy)
        # the link to Earth: clear until the Moon is in the way
        blocked = oy > my - 120 and ox > mx
        drop = smooth(rng(t, BL_DROP + 0.2, BL_DROP + 0.8))
        if not blocked or drop < 1:
            f.line([(ox - 12, oy), (330, my + (oy - my) * 0.0)], ORANGE + (int(220 * (1 - drop)),), 2, dash=(10, 6))
        if drop > 0:
            # the part of the line that still exists ends at the Moon's limb
            f.line([(ox - 12, oy), (mx + 120, lerp(oy, my, 0.3))], ORANGE + (int(220 * drop),), 2, dash=(10, 6))
            stamp(f, 'RADIO CONTACT DROPS · PLANNED', mx, 120, drop, RED, 20)
        blk = smooth(rng(t, BL_BLOCK, BL_BLOCK + 0.6))
        if blk > 0:
            f.line([(mx - 128, my), (340, my)], RED + (int(160 * blk),), 2, dash=(4, 8))
            f.text("THE MOON BLOCKS THE DIRECT PATH", 520, my + 170, 15, ORANGE, 'mono', 'center', alpha=blk)
        f.text('SCHEMATIC · NOT TO SCALE', 290, 684, 13, ORANGE, 'mono')
        f.end()
    if split > 0:
        x, y, w, h = BOX
        L = (x, y + 40, w / 2 - 12, (w / 2 - 12) * 9 / 16)
        R = (x + w / 2 + 12, y + 40, w / 2 - 12, (w / 2 - 12) * 9 / 16)
        f.group(split)
        lt = t - BL_SPLIT
        in_box(f, V('a_window3').at(0.2 + lt * 0.55), L, zoom=1.05)
        in_box(f, V('a_mcc').at(0.9 + lt * 0.35), R, zoom=1.1)
        box_frame(f, 'NASA · CREW AT THE WINDOW', 'SVS 15110', L)
        box_frame(f, 'NASA · MISSION CONTROL, HOUSTON', 'SVS 15103', R)
        f.text('ABOARD ORION', L[0] + L[2] / 2, y + 20, 18, PAPER, 'mono', 'center')
        f.text('ON THE GROUND', R[0] + R[2] / 2, y + 20, 18, PAPER, 'mono', 'center')
        rec = smooth(rng(t, BL_REC, BL_REC + 0.4))
        if rec > 0:
            blink = 0.5 + 0.5 * math.sin(t * 6)
            f.circle(L[0] + 26, L[1] + 26, 8, RED + (int(255 * rec * (0.4 + 0.6 * blink)),))
            f.text('WATCHING · RECORDING', L[0] + 44, L[1] + 32, 15, PAPER, 'mono', alpha=rec)
        wt = smooth(rng(t, BL_WAIT, BL_WAIT + 0.4))
        if wt > 0:
            dots = '.' * (1 + int(t * 2.5) % 3)
            f.text('WAITING FOR CONTACT' + dots, R[0] + 18, R[1] + 32, 15, PAPER, 'mono', alpha=wt)
        # the link strip below: broken
        yy = L[1] + L[3] + 70
        f.line([(L[0] + 40, yy), (L[0] + L[2] - 30, yy)], ORANGE + (200,), 2, dash=(10, 6))
        f.line([(R[0] + 30, yy), (R[0] + R[2] - 40, yy)], ORANGE + (200,), 2, dash=(10, 6))
        f.text('NO RADIO LINK', x + w / 2, yy + 6, 15, RED, 'mono', 'center')
        f.end()
    return retro(f.done(), 0.35)


# ------------------------------------------------------------------ dark Moon
DK_WITHOUT = c('Without the bright face')
DK_FLASH = c('a short flash could')
DK_TEAM = c('The science team had asked')


def bg_dark(t):
    f = Frame()
    bg(f)
    x, y, w, h = BOX
    if t < DK_WITHOUT - 0.2:
        # the lit crescent thins out in NASA's window simulation: the dark surface takes over
        lt = t - S['dark']
        in_box(f, V('a_crewview').at(55 + lt * 18), zoom=1.15)
        box_frame(f, "NASA SIMULATION · THE CREW'S VIEW AS THE LIT CRESCENT THINS", 'NASA SVS 5633')
    elif t < DK_TEAM - 0.2:
        lt = t - DK_WITHOUT
        in_box(f, V('a_darkmoon2').at(1.4 + lt * 0.8), zoom=1.05 + 0.02 * lt)
        # contrast meter (illustration): glare falls, contrast rises
        g = smooth(rng(t, DK_WITHOUT, DK_WITHOUT + 1.6))
        bx, by = x + 24, y + 24
        f.rect(bx, by, 300, 92, (12, 9, 7, 215), CREAM + (80,), 1)
        f.text('GLARE', bx + 14, by + 30, 13, CREAM, 'mono')
        f.rect(bx + 100, by + 18, 180 * (1 - 0.8 * g), 14, CREAM + (220,))
        f.text('CONTRAST', bx + 14, by + 64, 13, ORANGE, 'mono')
        f.rect(bx + 100, by + 52, 180 * (0.2 + 0.8 * g), 14, ORANGE + (230,))
        fl = smooth(rng(t, DK_FLASH, DK_FLASH + 0.4))
        f.text('A SHORT FLASH COULD STAND OUT', x + w / 2, y + h - 30, 18, PAPER, 'mono', 'center', alpha=fl)
        box_frame(f, 'NASA VIDEO · ARTEMIS II · THE DARK MOON · METER: ILLUSTRATION', 'NASA SVS 15103')
    else:
        lt = t - DK_TEAM
        in_box(f, V('a_training').at(0.2 + lt * 0.5), zoom=1.0)
        box_frame(f, 'NASA · CREW TRAINING, 2023: "PERFECTLY POSITIONED TO SPOT IMPACT FLASHES"', 'NASA SVS 15103')
    return retro(f.done(), 0.3)


# ------------------------------------------------------------------ impact: what a flash is
IM_ATM = c('At the Moon')
IM_HIT = c('It can hit the surface')
IM_ENERGY = c('A little of the impact')
IM_PIN = c('From Orion, that flash')


def rock(f, x, y, s=1.0, a=1.0):
    pts = [(x + s * dx, y + s * dy) for dx, dy in [(-10, -4), (-4, -10), (6, -8), (11, -1), (7, 8), (-3, 10), (-9, 5)]]
    f.poly(pts, (150, 132, 112, int(255 * a)), (60, 50, 40, int(255 * a)), 1)


def bg_impact(t):
    f = Frame()
    bg(f)
    x, y, w, h = BOX
    if t < IM_HIT - 0.15:
        f.starfield(t, 70)
        lt = t - S['impact']
        if t < IM_ATM - 0.2:
            # a small rock drifting through space
            rx = lerp(320, 980, rng(t, S['impact'], IM_ATM))
            rock(f, rx, 300 + 30 * math.sin(lt), 2.0)
            f.line([(rx - 120, 300 + 30 * math.sin(lt - 0.5)), (rx - 22, 300 + 30 * math.sin(lt))], CREAM + (60,), 1.4, dash=(4, 6))
            f.text('A SMALL PIECE OF ROCK', 706, 160, 22, PAPER, 'mono', 'center', alpha=smooth(rng(t, S['impact'] + 0.3, S['impact'] + 0.8)))
        else:
            # Earth has an atmosphere to cross, the Moon does not
            u = rng(t, IM_ATM, IM_HIT)
            for cx, title in ((500, 'EARTH: AIR TO CROSS'), (960, 'MOON: NO THICK ATMOSPHERE')):
                f.rect(cx - 200, 170, 400, 400, (18, 13, 10, 200), CREAM + (70,), 1)
                f.text(title, cx, 200, 15, CREAM, 'mono', 'center')
            f.rect(301, 420, 398, 110, (70, 120, 170, 110))
            f.rect(301, 530, 398, 39, (70, 90, 70, 255))
            f.rect(761, 530, 398, 39, (130, 126, 118, 255))
            ey = lerp(240, 470, u)
            burn = clamp((ey - 420) / 50)
            if burn < 1:
                rock(f, 470 + 40 * u, ey, 1.6, 1 - burn)
            f.line([(430 + 40 * u, ey - 60), (468 + 40 * u, ey - 4)], (255, 200, 140, int(230 * clamp((ey - 410) / 15) * (1 - clamp((ey - 480) / 40)))), 3)
            f.text('BURNS UP AS A METEOR', 500, 600, 13, ORANGE, 'mono', 'center', alpha=clamp(u * 2 - 0.6))
            my = lerp(240, 522, u)
            rock(f, 930 + 40 * u, my, 1.6)
            f.text('NOTHING TO SLOW IT', 960, 600, 13, ORANGE, 'mono', 'center', alpha=clamp(u * 2 - 0.6))
            f.text('SCHEMATIC', 290, 684, 13, ORANGE, 'mono')
    elif t < IM_PIN - 0.2:
        lt = t - IM_HIT
        in_box(f, V('a_impact_anim').at(1.3 + lt * 0.82), zoom=1.0)
        box_frame(f, 'NASA ANIMATION · HOW AN IMPACT FLASH FORMS', 'NASA SVS 15103 (LABELLED "ANIMATION")')
    else:
        # pull back from the surface to the whole dark Moon seen from Orion: the flash is a pinprick
        u = smooth(rng(t, IM_PIN - 0.2, IM_PIN + 1.6))
        f.starfield(t, 60)
        r = lerp(900, 150, u)
        moon_disc(f, 760, 330 + (1 - u) * 600, r, lit=0.2)
        k = smooth(rng(t, IM_PIN + 1.0, IM_PIN + 1.4))
        if k > 0:
            f.circle(800, 300, 2.2, (255, 240, 210, int(255 * k)))
            f.circle(800, 300, 16, None, (255, 240, 210, int(150 * k)), 1)
            f.text('A PINPRICK', 840, 290, 20, PAPER, 'mono', alpha=k)
        f.text('SCALE ILLUSTRATION · NOT AN OBSERVED FLASH OR LOCATION', 290, 684, 13, ORANGE, 'mono')
    return retro(f.done(), 0.35)


# ------------------------------------------------------------------ the annotations, by crew member
NO_REID = c('Reid Wiseman marked')
NO_IKE = c('Victor Glover')
NO_JER = c('Jeremy Hansen')
NO_PURPLE = c('General annotations')
NO_REC = c('The drawing is their record')
NO_CMP = c('It gives scientists')


def notes_cam(t):
    """(zoom, fx, fy) moving between the coloured labels as they are named."""
    def at(key, z):
        px, py = NOTE[key]
        return (z, clamp(px / 2200), clamp(py / 1238))
    keys = [(S['notes'], 1.0, 0.51, 0.47), (NO_REID - 0.2, 1.0, 0.51, 0.47), (NO_REID + 0.4, *at('reid', 1.7)),
            (NO_IKE + 0.4, *at('ike', 1.7)), (NO_JER + 0.4, *at('jeremy', 1.7)), (NO_PURPLE + 0.4, *at('purple', 1.6)),
            (NO_REC + 0.3, 1.0, 0.51, 0.47), (NO_CMP + 0.3, 1.25, 0.47, 0.6), (S['two'], 1.25, 0.47, 0.6)]
    if t <= keys[0][0]:
        return keys[0][1:]
    for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
        if t <= t1:
            u = smooth((t - t0) / max(1e-6, t1 - t0))
            return tuple(lerp(p, q, u) for p, q in zip(a, b))
    return keys[-1][1:]


def bg_notes(t):
    f = Frame()
    bg(f)
    z, fx, fy = notes_cam(t)
    notes_view(f, t, z, fx, fy)
    for key, col, tt in (('reid', BLUE, NO_REID), ('ike', GREEN, NO_IKE), ('jeremy', RED, NO_JER), ('purple', PURPLE, NO_PURPLE)):
        k = smooth(rng(t, tt + 0.2, tt + 0.6)) * (1 - smooth(rng(t, NO_REC - 0.2, NO_REC + 0.2)))
        if k > 0:
            px, py = nxy(key, z, fx, fy)
            f.circle(px, py, 70, None, col, 3, alpha=k)
    for i, m in enumerate(('m1', 'm2', 'm3', 'm4', 'm5')):
        k = smooth(rng(t, NO_REC + 0.3 + 0.3 * i, NO_REC + 0.5 + 0.3 * i)) * (1 - smooth(rng(t, NO_CMP - 0.1, NO_CMP + 0.3)))
        if k > 0:
            px, py = nxy(m, z, fx, fy)
            f.circle(px, py, 30, None, PAPER, 2.5, alpha=k)
    cmp_ = smooth(rng(t, NO_CMP + 0.3, NO_CMP + 0.8))
    if cmp_ > 0:
        px, py = nxy('purple', z, fx, fy)
        f.circle(px, py, 110, None, PURPLE, 3, alpha=cmp_)
        f.rect(BOX[0] + BOX[2] / 2 - 220, BOX[1] + BOX[3] - 64, 440, 40, (12, 9, 7, int(225 * cmp_)), PURPLE + (int(200 * cmp_),), 1.2)
        f.text('SAME EVENT? COMPARE OBSERVERS', BOX[0] + BOX[2] / 2, BOX[1] + BOX[3] - 38, 18, PAPER, 'mono', 'center', alpha=cmp_)
    leg = [('REID WISEMAN', BLUE, NO_REID), ('VICTOR GLOVER', GREEN, NO_IKE), ('JEREMY HANSEN', RED, NO_JER), ('GENERAL', PURPLE, NO_PURPLE)]
    for i, (n, col, tt) in enumerate(leg):
        k = smooth(rng(t, tt, tt + 0.3))
        if k > 0:
            f.rect(BOX[0] + 16, BOX[1] + 16 + 30 * i, 14, 14, col + (int(255 * k),))
            f.text(n, BOX[0] + 38, BOX[1] + 29 + 30 * i, 13, PAPER, 'mono', alpha=k)
    box_frame(f, 'NASA · CREW ANNOTATIONS ON A SIMULATED VIEW · RINGS & LEGEND: OURS', 'NASA ARTEMIS II PRELIMINARY LUNAR SCIENCE REPORT')
    return retro(f.done(), 0.3)


# ------------------------------------------------------------------ two records: eyes vs camera, images + notes
TW_IMG = c('The images give us')
TW_NOTES = c('Their notes tell us')
TW_PUT = c('Put those together')
TW_SAME = c('thought they had seen the same')


def eye_icon(f, x, y, a):
    f.poly([(x - 40, y), (x - 20, y - 18), (x + 20, y - 18), (x + 40, y), (x + 20, y + 18), (x - 20, y + 18)], None, PAPER + (int(255 * a),), 2.5)
    f.circle(x, y, 12, PAPER + (int(255 * a),))


def cam_icon(f, x, y, a):
    f.rect(x - 38, y - 22, 76, 46, None, PAPER + (int(255 * a),), 2.5)
    f.circle(x, y + 1, 14, None, PAPER + (int(255 * a),), 2.5)
    f.rect(x - 14, y - 32, 26, 10, PAPER + (int(255 * a),))


def bg_two(t):
    f = Frame()
    bg(f)
    f.starfield(t, 40)
    x, y, w, h = BOX
    ic = smooth(rng(t, S['two'] + 0.2, S['two'] + 0.8)) * (1 - smooth(rng(t, TW_IMG - 0.3, TW_IMG + 0.1)))
    if ic > 0:
        eye_icon(f, 560, 280, ic)
        f.text('A PERSON SEES A FLASH', 560, 360, 16, PAPER, 'mono', 'center', alpha=ic)
        neq = smooth(rng(t, c('two different things') - 0.2, c('two different things') + 0.3))
        f.text('≠', 760, 300, 64, ORANGE, 'sans', 'center', alpha=ic * neq)
        cam_icon(f, 960, 280, ic * neq)
        f.text('A CAMERA CAPTURES IT', 960, 360, 16, PAPER, 'mono', 'center', alpha=ic * neq)
    together = smooth(rng(t, TW_PUT, TW_PUT + 1.0))
    pw, ph = 466, 262
    gap = lerp(26, 8, together)
    L = (x + w / 2 - gap / 2 - pw, y + 70, pw, ph)
    R = (x + w / 2 + gap / 2, y + 70, pw, ph)
    a_img = smooth(rng(t, TW_IMG - 0.1, TW_IMG + 0.4))
    if a_img > 0:
        in_box(f, still('eclipse.jpg'), L, zoom=1.0 + 0.04 * rng(t, TW_IMG, S['back']), alpha=a_img)
        box_frame(f, "IMAGES: THE CREW'S VIEW", 'NASA', L, a_img)
        f.text('WHAT IT LOOKED LIKE', L[0] + pw / 2, y + 40, 17, PAPER, 'mono', 'center', alpha=a_img)
    a_n = smooth(rng(t, TW_NOTES - 0.1, TW_NOTES + 0.4))
    if a_n > 0:
        notes_view(f, t, 1.0, box=R, alpha=a_n)
        box_frame(f, 'NOTES: WHERE THEY SAW LIGHT', 'NASA', R, a_n)
        f.text('WHERE THEY SAW LIGHT', R[0] + pw / 2, y + 40, 17, PAPER, 'mono', 'center', alpha=a_n)
        same = smooth(rng(t, TW_SAME, TW_SAME + 0.4))
        if same > 0:
            px, py = nxy('purple', 1.0, box=R)
            f.circle(px, py, 40, None, PURPLE, 3, alpha=same)
            f.text('CREW: LIKELY THE SAME IMPACTS', R[0] + pw / 2, R[1] + ph + 48, 14, PURPLE, 'mono', 'center', alpha=same)
    if together > 0:
        k = smooth(rng(t, TW_PUT + 0.5, TW_PUT + 1.1))
        by = y + 70 + ph + 80
        f.line([(L[0] + 40, by - 18), (L[0] + 40, by), (R[0] + pw - 40, by), (R[0] + pw - 40, by - 18)], ORANGE + (int(220 * k),), 2)
        f.rect(x + w / 2 - 330, by + 14, 660, 44, (40, 26, 16, int(225 * k)), ORANGE + (int(160 * k),), 1.4)
        f.text('TOGETHER: A RECONSTRUCTION OF WHAT THEY REPORTED', x + w / 2, by + 43, 17, ORANGE, 'mono', 'center', alpha=k)
    return retro(f.done(), 0.3)


# ------------------------------------------------------------------ contact restored: the record reaches the ground
BK_REACH = c('could reach the ground')
BK_EVID = c("That's when the view")
BK_ALONG = c('alongside the rest')


def bg_back(t):
    f = Frame()
    bg(f)
    x, y, w, h = BOX
    if t < BK_EVID - 0.2:
        f.starfield(t, 60)
        mx, my = MOON_C
        moon_disc(f, mx, my, 120, lit=0.25)
        f.line([(330, my), (220, my)], CREAM + (150,), 2)
        f.poly([(212, my), (226, my - 8), (226, my + 8)], CREAM + (150,))
        f.text('TO EARTH', 260, my - 16, 13, CREAM, 'mono', 'center')
        # Orion comes out from behind the Moon (upper left), the link re-forms, packets travel home
        a = math.radians(lerp(10, -110, smooth(rng(t, S['back'], BK_REACH))))
        ox, oy = mx + ORB_R * math.cos(a) * 1.6, my + ORB_R * math.sin(a) * 0.9
        orion_icon(f, ox, oy)
        clear = oy < my - 125 or ox < mx - 130
        if clear:
            f.line([(ox - 12, oy), (330, my)], ORANGE + (230,), 2.2, dash=(10, 6))
            for i in range(4):
                u = (t * 0.5 + i / 4) % 1
                px, py = lerp(ox, 330, u), lerp(oy, my, u)
                f.rect(px - 8, py - 6, 16, 12, PAPER + (230,), ORANGE + (255,), 1)
            stamp(f, 'CONTACT RESTORED', mx, 110, 1.0, ORANGE, 20)
        f.text('SCHEMATIC · NOT TO SCALE', 290, 684, 13, ORANGE, 'mono')
    else:
        lt = t - BK_EVID
        in_box(f, V('a_celebrate').at(2.6 + lt * 0.6), zoom=1.05)
        al = smooth(rng(t, BK_ALONG, BK_ALONG + 0.5))
        for i, lab in enumerate(('IMAGES', 'CREW NOTES', 'AUDIO', 'TRAJECTORY')):
            k = smooth(rng(t, BK_ALONG + 0.2 * i, BK_ALONG + 0.2 * i + 0.4))
            if k > 0:
                cx, cy = x + w - 200 + 10 * i, y + 40 + 56 * i
                f.rect(cx, cy, 180, 44, (20, 14, 10, int(230 * k)), CREAM + (int(150 * k),), 1.2)
                f.text(lab, cx + 90, cy + 28, 14, PAPER, 'mono', 'center', alpha=k)
        f.text('THE FLYBY RECORD', x + w - 110, y + 30, 13, ORANGE, 'mono', 'center', alpha=al)
        box_frame(f, 'NASA VIDEO · LUNAR SCIENCE TEAM, HOUSTON · RECORD CARDS: OURS', 'NASA SVS 15103')
    return retro(f.done(), 0.3)


# ------------------------------------------------------------------ why stare into darkness
WY_GONE = c('A flash disappears')
WY_REC = c('An observer who records')
WY_TRACE = c('leave a trace')


def bg_why(t):
    f = Frame()
    bg(f)
    x, y, w, h = BOX
    if t < WY_GONE - 0.2:
        lt = t - S['why']
        in_box(f, V('a_window1').at(0.2 + lt * 0.5), zoom=1.05)
        box_frame(f, 'NASA VIDEO · REID WISEMAN AT THE WINDOW, ARTEMIS II', 'NASA SVS 15103')
    else:
        # a time ribbon: light lasts a blink, the mark stays
        f.starfield(t, 40)
        x0, x1, yy = 330, 1180, 520
        f.line([(x0, yy), (x1, yy)], CREAM + (140,), 2)
        f.text('TIME →', x1, yy + 30, 13, CREAM, 'mono', 'right')
        head = lerp(x0, x1, rng(t, WY_GONE, S['fin']))
        f.line([(x0, yy), (head, yy)], ORANGE + (220,), 3)
        lx = x0 + 60
        la = smooth(rng(t, WY_GONE + 0.2, WY_GONE + 0.3)) * (1 - smooth(rng(t, WY_GONE + 0.45, WY_GONE + 0.9)))
        f.rect(lx - 4, yy - 70, 8, 70, (255, 240, 210, int(255 * la)))
        f.text('LIGHT: GONE ALMOST AT ONCE', lx, yy - 84, 15, PAPER, 'mono', alpha=smooth(rng(t, WY_GONE + 0.4, WY_GONE + 0.8)))
        rk = smooth(rng(t, WY_REC, WY_REC + 0.6))
        if rk > 0:
            f.rect(lx + 10, yy - 22, max(1, (head - lx - 10)), 22, (190, 130, 255, int(140 * rk)))
            f.text("THE OBSERVER'S RECORD: STILL HERE", (lx + head) / 2 + 40, yy - 34, 15, PURPLE, 'mono', 'center', alpha=rk)
        tr = smooth(rng(t, WY_TRACE, WY_TRACE + 0.6))
        if tr > 0:
            R = (760, 70, 440, 248)
            notes_view(f, t, 1.6, *(clamp(NOTE['m2'][0] / 2200), clamp(NOTE['m2'][1] / 1238)), box=R, alpha=tr)
            box_frame(f, 'A MARK ON THE NOTES', 'NASA', R, tr)
        f.text('SCHEMATIC TIMELINE', 290, 684, 13, ORANGE, 'mono')
    return retro(f.done(), 0.3)


# ------------------------------------------------------------------ finale: the notebook cover again
def bg_fin(t):
    lt = t - S['fin']
    push = 0.45 * (1 - smooth(rng(t, S['fin'], S['fin'] + 4.5)))
    img = scenes.cover(2.0 + lt * 0.5, push=push, title_out=0.0)
    f = Frame(img)
    s = 1 + 0.9 * smooth(push)
    mark_rings(f, t, s, MARKS[2], [S['fin'] + 0.4 + 0.35 * i for i in range(5)])
    f.pill('CONCEPT ILLUSTRATION  ·  MARKS ARE NOT OBSERVED LOCATIONS', 470, 690, 'paper', 15)
    return f.done()


def background(t):
    k = scene_at(t)
    return {'cover': bg_cover, 'crew': bg_crew, 'geo': bg_geo, 'view': bg_view, 'blackout': bg_blackout, 'dark': bg_dark,
            'impact': bg_impact, 'notes': bg_notes, 'two': bg_two, 'back': bg_back, 'why': bg_why, 'fin': bg_fin}[k](t)


def overlay(t, img):
    pass


# ------------------------------------------------------------------ ATLAS
def build_host(atlas):
    shots = [Shot(S[k] if k != 'cover' else -5.0, end_of(k), *PLACE[k]) for k in ORDER]
    h = Host(atlas, shots, VOICE_WAV, VOICE_JSON, DUR, offset=0.0)
    x, y, w, hh = BOX
    mark = MARKS[2]
    # cover: points at the sketch marks as they light up, the camera moves in
    h.point(-2.0, seq([(0, mark), (1.4, MARKS[3]), (2.3, MARKS[1])], 0.6), CV1 - 0.4, gaze_lead=0.0)
    h.brow(0.9, 0.6, 1.2)
    # crew: small; watches the crew, then points at the three colours
    s0, e = S['crew'], end_of('crew')
    h.gaze(s0 + 0.2, ('s', P(x + w / 2, y + hh / 2)), look=0.7)
    h.point(CR_MARK + 0.3, seq([(0, P(*nxy('reid', 1.0))), (CR_MARK + 0.8, P(*nxy('ike', 1.0))), (CR_MARK + 1.25, P(*nxy('jeremy', 1.0)))]), e - 0.3)
    # geometry
    s0, e = S['geo'], end_of('geo')
    h.point(G_MILES - 0.2, P(x + w - 175, y + 70), G_POINT - 0.2)
    h.point(G_BETWEEN, P(820, 330), e - 0.4)
    h.brow(G_EARTH + 0.2, 0.5, 1.0)
    # view
    s0, e = S['view'], end_of('view')
    h.gaze(s0 + 0.2, ('s', P(x + w / 2, y + hh / 2)), look=0.8)
    # blackout: follows Orion behind the Moon, reacts to the drop, then looks at both panels
    s0, e = S['blackout'], end_of('blackout')
    h.point(s0 + 0.4, lambda t: P(*orion_xy_bl(t)), BL_DROP + 1.2, gaze_lead=0.0)
    h.brow(BL_DROP + 0.5, -0.5, 1.2)
    h.point(BL_BLOCK + 0.2, P(760, 340), BL_SPLIT - 0.5)
    h.point(BL_REC - 0.1, P(x + w / 4, y + 160), BL_WAIT - 0.3)
    h.point(BL_WAIT, P(x + 3 * w / 4, y + 160), e - 0.4)
    # dark
    s0, e = S['dark'], end_of('dark')
    h.gaze(s0 + 0.2, ('s', P(x + w / 2, y + hh / 2)), look=0.8)
    h.point(DK_WITHOUT + 0.3, P(x + 200, y + 70), DK_FLASH + 1.0)
    h.brow(DK_TEAM + 0.4, 0.6, 1.2)
    # impact
    s0, e = S['impact'], end_of('impact')
    h.point(s0 + 0.5, lambda t: P(lerp(320, 980, rng(t, S['impact'], IM_ATM)), 300), IM_ATM - 0.2, gaze_lead=0.0)
    h.point(IM_ATM + 0.2, seq([(0, P(520, 360)), (IM_ATM + 1.4, P(930, 360))]), IM_HIT - 0.3)
    h.gaze(IM_HIT, ('s', P(x + w / 2, y + hh / 2)), look=0.7)
    h.point(IM_PIN + 1.0, P(800, 300), e - 0.4)
    # notes: small; points at each colour as it is named
    s0, e = S['notes'], end_of('notes')
    h.gaze(s0 + 0.2, ('s', P(x + w / 2, y + hh / 2)), look=0.8)
    h.point(NO_REC + 0.2, lambda t: P(*nxy('m2', *notes_cam(t))), NO_CMP - 0.2)
    h.point(NO_CMP + 0.4, lambda t: P(*nxy('purple', *notes_cam(t))), e - 0.4)
    # two
    s0, e = S['two'], end_of('two')
    h.point(s0 + 0.4, seq([(0, P(560, 280)), (c('two different things'), P(960, 280))]), TW_IMG - 0.4)
    h.point(TW_IMG + 0.1, P(x + 226, y + 177), TW_NOTES - 0.2)
    h.point(TW_NOTES + 0.2, P(x + w - 226, y + 177), TW_PUT - 0.2)
    h.brow(TW_PUT + 0.6, 0.6, 1.2)
    # back
    s0, e = S['back'], end_of('back')
    h.point(s0 + 0.5, P(330, 340), BK_EVID - 0.4)
    h.gaze(BK_EVID, ('s', P(x + w / 2, y + hh / 2)), look=0.7)
    h.brow(BK_EVID + 0.4, 0.7, 1.4)
    h.point(BK_ALONG + 0.3, P(x + w - 110, y + 120), e - 0.4)
    # why: small at the window shot, then the ribbon
    s0, e = S['why'], end_of('why')
    h.gaze(s0 + 0.2, ('s', P(x + w / 2, y + hh / 2)), look=0.8)
    h.point(WY_GONE + 0.3, P(390, 450), WY_REC - 0.2)
    h.point(WY_TRACE + 0.3, P(980, 190), e - 0.4)
    # fin
    s0 = S['fin']
    h.point(s0 + 0.3, seq([(0, MARKS[0]), (s0 + 1.4, MARKS[2]), (s0 + 2.8, MARKS[4])], 0.7), DUR - 2.5, gaze_lead=0.0)
    h.gaze(c('while the rest of us') - 0.2, None, look=-0.9)
    h.brow(c('other side of the Moon'), 0.5, 1.5)
    h.auto(emphasis=('pinpricks', 'three', 'blocked', 'dark', 'flash', 'pinprick', 'blue', 'green', 'red', 'record',
                     'together', 'evidence', 'darkness', 'trace', 'second'))
    return h


# ------------------------------------------------------------------ sound
MUSIC = [(0.0, 0.5), (3.5, 0.6), (13.5, 0.55), (19.0, 0.45), (22.7, 0.35), (28.0, 0.25), (31.4, 0.4), (39.8, 0.55),
         (50.0, 0.6), (54.0, 0.45), (61.5, 0.85), (68.0, 0.4), (71.3, 0.55), (90.7, 0.45), (102.3, 0.8), (110.9, 0.75),
         (115.5, 0.9), (123.9, 0.4), (134.0, 0.6), (140.6, 0.75), (148.0, 0.5), (155.0, 0.2)]
SFX = [(0.25 + 0.45 * i, 'tick', -22) for i in range(5)] + [
    (S['crew'] - 0.3, 'whoosh', -21), (CR_MARK + 0.35, 'tick', -20), (CR_MARK + 0.8, 'tick', -20), (CR_MARK + 1.25, 'tick', -20),
    (S['geo'] - 0.3, 'whoosh', -21), (G_MILES, 'hit', -17), (G_EARTH + 0.3, 'stamp', -17),
    (S['view'] - 0.3, 'whoosh', -21), (S['blackout'] - 0.3, 'whoosh', -21), (BL_DROP + 0.3, 'lost', -20),
    (BL_DROP + 0.5, 'stamp', -16), (BL_SPLIT - 0.3, 'whoosh', -21), (S['dark'] - 0.3, 'whoosh', -21),
    (DK_WITHOUT - 0.2, 'hit', -18), (DK_TEAM - 0.2, 'whoosh', -22), (S['impact'] - 0.3, 'whoosh', -21),
    (IM_ATM - 0.2, 'whoosh', -22), (IM_HIT - 0.15, 'hit', -15), (IM_PIN + 1.0, 'tick', -18),
    (S['notes'] - 0.3, 'whoosh', -21), (NO_REID + 0.2, 'tick', -19), (NO_IKE + 0.2, 'tick', -19), (NO_JER + 0.2, 'tick', -19),
    (NO_PURPLE + 0.2, 'tick', -19), (NO_CMP + 0.3, 'arrive', -19), (S['two'] - 0.3, 'whoosh', -21),
    (TW_PUT + 0.8, 'arrive', -18), (S['back'] - 0.3, 'whoosh', -21), (S['back'] + 1.0, 'back', -16),
    (BK_EVID - 0.2, 'hit', -16), (S['why'] - 0.3, 'whoosh', -21), (WY_GONE + 0.2, 'tick', -16), (WY_TRACE, 'arrive', -18),
    (S['fin'] - 0.3, 'whoosh', -20), (DUR - 3.0, 'hit', -18)]
