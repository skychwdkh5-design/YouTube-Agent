"""EP013 Voyager 1 - v2 visual direction (after the owner rejected v1 as a slideshow).

Every scene is a small sequence with an event -> change -> result, keyed to the narration:
the command pulse leaves the cover, the real NASA spacecraft animation recedes while the
one-way clock runs, the reply crosses the map, the listening attempts fail on the line, the
signal returns before the troubleshooting command is sent, the antenna turns to Voyager's
patch of sky. Real NASA material stays in frames, ATLAS stays outside them and gets small
during key shots. Graphics that are not NASA data carry an ILLUSTRATION / SCHEMATIC label.

PILOT=1 renders only the first scenes (0-31.6 s)."""
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
import opening
import scenes
from scenes import retro

VOICE_DIR = '/mnt/project-files/voyager/EP013/voice'
VOICE_WAV = os.path.join(VOICE_DIR, 'narration.voice.json'.replace('.voice.json', '.wav'))
VOICE_JSON = os.path.join(VOICE_DIR, 'narration.voice.json')
C = Cues(VOICE_JSON)
OFFSET = 0.0
PILOT = os.environ.get('PILOT') == '1'
MEDIA = '/mnt/project-files/media_v2'

CREAM = (239, 226, 196)
ORANGE = (242, 112, 58)
RED = (232, 62, 40)
DIM = (239, 226, 196, 70)


def c(p, after=0.0):
    return C.at(p, after)


def ce(p, after=0.0):
    return C.end(p, after)


# ------------------------------------------------------------------ scene table (pilot part)
S = {}
S['cover'] = 0.0
S['away'] = 3.30
S['map'] = c('If the spacecraft replies') - 0.18
S['dsn'] = c('On October eighteenth') - 0.30
PILOT_END = ce("It didn't detect a signal") + 0.55
ORDER = ['cover', 'away', 'map', 'dsn']
DUR = round(PILOT_END, 2) if PILOT else None


def end_of(k):
    i = ORDER.index(k)
    return S[ORDER[i + 1]] if i + 1 < len(ORDER) else DUR


def scene_at(t):
    cur = ORDER[0]
    for k in ORDER:
        if t >= S[k]:
            cur = k
    return cur


# ATLAS placements (feet x, floor y, scale, facing)
BIG = (263, 1830, 2.9, 1)
SMALL = (205, 1000, 0.58, 1)
MED = (215, 1000, 0.82, 1)
PLACE = dict(cover=BIG, away=SMALL, map=MED, dsn=SMALL)

# real footage frame (design px): right of ATLAS, above the subtitle band
BOX = (282, 34, 958, 539)          # x, y, w, h  -> screen 423..1860, 51..860

# ------------------------------------------------------------------ media
@lru_cache(maxsize=1)
def craft():
    return Video(os.path.join(MEDIA, 'cuts', 'v_craft_7-20.mp4'))


@lru_cache(maxsize=1)
def dish():
    return Image.open(scenes.A('dish.jpg')).convert('RGB')


@lru_cache(maxsize=1)
def craft_sprite():
    """Voyager from the NASA animation, cut out by luminance (bright model on dark sky)."""
    im = craft().at(12.6)
    a = np.asarray(im, np.float32)
    lum = a.mean(-1)
    alpha = np.clip((lum - 95) / 60, 0, 1)
    # keep the main connected body only: the big bright block around the dish
    big = alpha > 0.5
    yy, xx = np.nonzero(big)
    cy, cx = np.median(yy), np.median(xx)            # the dish dominates the bright pixels
    x0, x1 = int(max(0, cx - 240)), int(min(a.shape[1], cx + 240))
    y0, y1 = int(max(0, cy - 330)), int(min(a.shape[0], cy + 360))
    rgba = np.dstack([a, alpha[..., None] * 255])[y0:y1, x0:x1].astype(np.uint8)
    return Image.fromarray(rgba, 'RGBA')


# ------------------------------------------------------------------ small drawing helpers
def box_frame(f, alpha=1.0, label=None, credit=None):
    x, y, w, h = BOX
    f.rect(x - 2, y - 2, w + 4, h + 4, None, (239, 226, 196, int(150 * alpha)), 1.4)
    if label:
        f.text(label, x, y + h + 20, 12.5, ORANGE, 'mono', alpha=alpha)
    if credit:
        f.text(credit, x + w, y + h + 20, 12.5, CREAM, 'mono_r', 'right', alpha=alpha * 0.85)


def clip_in_box(f, im, zoom=1.0, fx=0.5, fy=0.5, alpha=1.0):
    x, y, w, h = BOX
    f.image(None, x, y, w, h, zoom=zoom, fx=fx, fy=fy, alpha=alpha, frame=im)


def stamp(f, s, x, y, k, col=RED, n=30):
    """Rubber-stamp text that lands (scale-in + settle) with k in 0..1."""
    if k <= 0:
        return
    a = clamp(k * 3)
    w = f.text_w(s, n, 'mono') + 30
    f.rect(x - w / 2, y - n - 8, w, n + 22, (12, 8, 7, int(220 * a)), col + (int(255 * a),), 2.2)
    f.text(s, x, y + 2, n, col, 'mono', 'center', alpha=a)


def clock(f, hours, x, y, label='SIGNAL TRAVEL TIME', a=1.0, col=CREAM):
    hh = int(hours)
    mm = int((hours - hh) * 60)
    f.text(label, x, y - 46, 13, ORANGE, 'mono', 'center', alpha=a)
    f.text(f'{hh:02d}:{mm:02d}', x, y, 54, col, 'mono', 'center', alpha=a)
    f.text('HOURS', x, y + 24, 12, CREAM, 'mono_r', 'center', alpha=a * 0.7)


def pulse(f, x, y, r=8, a=1.0, col=ORANGE):
    f.glow(x, y, r * 7, col, 0.7 * a)
    f.circle(x, y, r, CREAM + (int(255 * a),))


def earth_disc(f, x, y, r):
    """Schematic Earth in the poster palette (not an image of Earth)."""
    f.glow(x, y, r * 2.2, (90, 160, 210), 0.35)
    f.circle(x, y, r, (34, 70, 104), (190, 220, 235), 1.6)
    for i, (dx, dy, rr) in enumerate([(-0.3, -0.25, 0.32), (0.25, 0.1, 0.28), (-0.05, 0.42, 0.2), (0.38, -0.38, 0.14)]):
        f.circle(x + dx * r, y + dy * r, rr * r, (96, 128, 88, 200))
    f.arc(x, y, r * 0.98, 300, 120, (12, 16, 24, 160), r * 0.35)


# ------------------------------------------------------------------ cover (frame 0 == cover)
P0, P1 = 0.35, 2.75                 # command pulse runs along the painted waveform


def cover_pulse_x(t):
    return lerp(opening.WAVE_X0 + 30, opening.WAVE_X1 + 140, smooth(rng(t, P0, P1)))


def bg_cover(t):
    push = 1 + 0.055 * smooth(rng(t, 0.15, 3.3)) * 1.0
    to = smooth(rng(t, 1.9, 3.25))
    spec = [
        ('plate', {}),
        ('probe', dict(s=1 + 0.03 * t, cx=1690, cy=730, dx=-10.0 * t, dy=-3.0 * t)),
        ('lost', dict(dy=-90 * to, alpha=1 - to)),
        ('signal', dict(dy=-120 * to, alpha=1 - to)),
        ('wave', dict(mask=None if t <= 1e-6 else _wave_lit(t))),
    ]
    img = opening.STACK.render(spec, cam=(0.0, 0.0, push, 1500, 640))
    if t <= 1e-6:
        return img
    f = Frame(img)
    x = cover_pulse_x(t) / 1.5
    a = smooth(rng(t, P0 - 0.1, P0 + 0.25)) * (1 - smooth(rng(t, P1 - 0.2, P1 + 0.3)))
    if a > 0:
        # zoom-corrected position of the pulse on the waveform
        X = (x * 1.5 - 1500) * push + 1500
        Y = (opening_wave_y() - 640) * push + 640
        pulse(f, X / 1.5, Y / 1.5, 7, a)
    k = smooth(rng(t, 2.0, 2.5))
    if k > 0:
        f.text('COMMAND SENT', 1000, 120, 15, ORANGE, 'mono', alpha=k * (1 - smooth(rng(t, 3.0, 3.3))))
    return f.done()


def opening_wave_y():
    return 640.0


def _wave_lit(t):
    """The waveform stays; behind the pulse it is drawn (energised), ahead it is faint."""
    xs = np.arange(opening.W, dtype=np.float32)
    head = cover_pulse_x(t)
    m = 0.55 + 0.45 * np.clip((head - xs) / 60.0, 0, 1)
    return np.broadcast_to(m[None, :], (opening.H, opening.W))


# ------------------------------------------------------------------ away: the craft recedes, clock runs
A_T0 = S['away']
A_ARRIVE = ce('just to get there') - 0.05


def away_hours(t):
    return 24.0 * smooth(rng(t, A_T0 + 0.35, A_ARRIVE))


def bg_away(t):
    f = Frame()
    f.background('#1c1411', '#080605')
    lt = t - A_T0
    # NASA animation: the spacecraft drifting away (source 7-20 s of SVS 20130), 1.45x speed
    im = craft().at(min(12.9, 4.6 + lt * 1.45))
    clip_in_box(f, im, zoom=1.0 + 0.05 * smooth(lt / 4))
    x, y, w, h = BOX
    # outgoing wavefronts from the viewer side towards the dish (illustration)
    for k in range(4):
        u = (lt * 0.55 + k * 0.25) % 1.0
        if lt < 0.2:
            continue
        r = lerp(520, 40, u)
        f.arc(x + w * 0.5, y + h * 0.48, r, 200, 340, (242, 112, 58, int(170 * (1 - u) * smooth(lt / 0.6))), 2.5)
    arrive = smooth(rng(t, A_ARRIVE - 0.1, A_ARRIVE + 0.35))
    if arrive > 0:
        f.glow(x + w * 0.5, y + h * 0.47, 140, ORANGE, 0.55 * arrive * (1 - 0.6 * smooth(rng(t, A_ARRIVE + 0.4, A_ARRIVE + 1.2))))
    # one-way clock
    f.rect(x + w - 236, y + 18, 218, 112, (10, 7, 6, 210), (239, 226, 196, 60), 1)
    clock(f, away_hours(t), x + w - 127, y + 92, 'ONE WAY · EARTH → VOYAGER 1',
          col=ORANGE if arrive > 0.5 else CREAM)
    f.text('BY NOV 18, 2026', x + w - 127, y + 152, 13, CREAM, 'mono_r', 'center', alpha=smooth(rng(t, c('November', A_T0) - 0.1, c('November', A_T0) + 0.4)))
    box_frame(f, 1.0, 'NASA ANIMATION · VOYAGER SPACECRAFT (TWIN DESIGN)', 'NASA SVS 20130 · WAVES & CLOCK: ILLUSTRATION')
    return retro(f.done(), 0.35)


# ------------------------------------------------------------------ map: reply, silence, return
M0 = S['map']
R0 = c('If the spacecraft replies') + 0.15
R1 = ce('another day to get back') - 0.1
L_LISTEN = c('NASA listened twice')
L_TWICE = c('twice', M0)
L_NOTHING = c('heard nothing')
B_ENG = c('before engineers')
B_SENT = c('sent a troubleshooting')
B_SIG = c('the signal came back')
B_BACK = c('came back on its own')
B_OWN = c('on its own')
EX, VX, LY = 0.0, 2600.0, 0.0            # world: Earth, Voyager, line


def _keys(t, keys):
    """eased interpolation through (t, a, b) keys"""
    if t <= keys[0][0]:
        return keys[0][1:]
    for (t0, *v0), (t1, *v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = smooth((t - t0) / max(1e-6, t1 - t0))
            return tuple(lerp(p, q, u) for p, q in zip(v0, v1))
    return keys[-1][1:]


def map_cam(t):
    """camera (cx, zoom) over the map world: it follows the reply to Earth, moves to Voyager's
    end while the line goes silent, swings to Earth for the waiting command, holds there while
    the returning signal arrives, then pulls back to the whole restored line."""
    wide = (1164.0, 0.55)
    keys = [(M0, VX - 120, 1.75), (R0 + 0.2, VX - 120, 1.75), (R0 + 2.2, 1900, 0.62), (R1 + 0.4, wide[0], wide[1]),
            (L_LISTEN - 0.2, wide[0], wide[1]), (L_NOTHING + 0.4, 1900, 0.95), (B_ENG - 0.1, 1900, 0.95),
            (B_ENG + 1.1, 420, 1.15), (B_BACK + 0.5, 420, 1.15), (B_OWN + 1.2, wide[0], wide[1]),
            (S['dsn'], wide[0] - 60, wide[1] * 0.96)]
    return _keys(t, keys)


def m2s(t, wx, wy=0.0):
    cx, z = map_cam(t)
    return 706 + (wx - cx) * z / 1.5, 300 + wy * z / 1.5      # design px


def reply_x(t):
    return lerp(VX, EX, smooth(rng(t, R0 + 0.3, R1)))


def bg_map(t):
    f = Frame()
    f.background('#1f1713', '#0a0706')
    f.starfield(t, 70)
    cx, z = map_cam(t)
    ex, ey = m2s(t, EX)
    vx, vy = m2s(t, VX)
    # match-cut in: the spacecraft frame shrinks into Voyager's position on the map
    lt = t - M0
    shrink = smooth(rng(lt, 0.0, 0.7))
    # the line: dashes; state changes: lit by reply, fades in silence, re-forms on return
    fade = smooth(rng(t, L_NOTHING - 0.4, L_NOTHING + 0.8)) * (1 - smooth(rng(t, B_SIG - 0.1, B_BACK + 0.2)))
    gap_from_v = lerp(0, 0.85, fade)            # share of the line (from Voyager) that is gone
    n = 70
    for i in range(n):
        u0, u1 = i / n, (i + 0.55) / n
        wx0, wx1 = lerp(EX, VX, u0), lerp(EX, VX, u1)
        pres = clamp((1 - u0 - gap_from_v) * 12 + 0.0)
        if pres <= 0:
            continue
        lit = 1.0 if (R0 < t < R1 + 1.0 and wx0 >= reply_x(t)) else 0.0
        col = (242, 112, 58, int(230 * pres)) if lit else (239, 226, 196, int(95 * pres))
        f.line([m2s(t, wx0), m2s(t, wx1)], col, 2.2)
    # hour ticks along the line: they light up as the reply passes (24 -> 48 h)
    tick_a = 1 - smooth(rng(t, L_LISTEN - 0.6, L_LISTEN))
    if tick_a > 0:
        for k in range(1, 4):
            wx = lerp(VX, EX, k / 4)
            x, y = m2s(t, wx)
            on = (R0 < t and reply_x(t) <= wx)
            col = ORANGE if on else CREAM
            f.line([(x, y - 9), (x, y + 9)], col + (int(200 * tick_a),), 1.6)
            f.text(f'{24 + 6 * k} H', x, y - 18, 12, col, 'mono', 'center', alpha=tick_a * (1.0 if on else 0.55))
    # Earth + Voyager markers
    earth_disc(f, ex, ey, 30 * z / 0.55 * 0.75)
    f.text('EARTH', ex, ey + 46 * z / 0.55 * 0.6 + 8, 13, CREAM, 'mono', 'center')
    sp = craft_sprite()
    s = max(0.2, 0.15 * z / 0.55)
    if shrink < 1:
        # picture-in-picture of the last animation frame shrinking into the marker
        im = craft().at(min(12.9, 4.6 + (M0 - A_T0) * 1.45))
        x, y, w, h = BOX
        k = shrink
        bx, by = lerp(x, vx - 60, k), lerp(y, vy - 34, k)
        bw, bh = lerp(w, 120, k), lerp(h, 68, k)
        f.image(None, bx, by, bw, bh, frame=im, alpha=1 - k)
    sw, sh = sp.size
    spr = sp.resize((max(2, int(sw * s)), max(2, int(sh * s))), Image.LANCZOS)
    f.paste(spr, vx - spr.size[0] / 3, vy - spr.size[1] / 3, alpha=shrink)
    f.text('VOYAGER 1', vx, vy + 70 * z / 0.55 * 0.6 + 8, 13, CREAM, 'mono', 'center', alpha=shrink)
    # reply pulse
    if R0 + 0.3 < t < R1 + 0.25:
        x, y = m2s(t, reply_x(t))
        pulse(f, x, y, 7)
    hit = smooth(rng(t, R1 - 0.05, R1 + 0.3)) * (1 - smooth(rng(t, R1 + 0.8, R1 + 1.6)))
    if hit > 0:
        f.glow(ex, ey, 120, ORANGE, 0.6 * hit)
    # round-trip clock: 24 -> 48 h with the reply
    hours = 24 + 24 * smooth(rng(t, R0 + 0.3, R1))
    rt = smooth(rng(t, R1, R1 + 0.4))
    clock_a = 1 - smooth(rng(t, c('In October') - 0.3, c('In October') + 0.1))
    if clock_a > 0:
        clock(f, hours, 706, 116, 'ROUND TRIP · 48 H OF TRAVEL TIME' if rt > 0.5 else 'SIGNAL TRAVEL TIME',
              a=clock_a, col=ORANGE if rt > 0.5 else CREAM)
    # October: two listening attempts fail
    oct_a = smooth(rng(t, c('In October') - 0.1, c('In October') + 0.4))
    if oct_a > 0:
        f.text('OCTOBER 2026', 706, 90, 22, ORANGE, 'mono', 'center', alpha=oct_a)
    for k, (tt, lab) in enumerate([(L_LISTEN + 0.2, 'OCT 18 · NOTHING'), (L_TWICE + 0.25, 'OCT 19 · NOTHING')]):
        a = smooth(rng(t, tt, tt + 0.25))
        if a <= 0:
            continue
        # listening cone from Earth toward Voyager, unanswered
        u = rng(t, tt - 0.9, tt + 0.5)
        cxz, zz = map_cam(t)
        if 0 < u < 1:
            f.arc(ex, ey, 30 + u * VX * zz / 1.5, -7, 7, (239, 226, 196, int(190 * (1 - u * 0.6))), 2.4)
        stamp(f, lab, 760 + (k - 0.5) * 300, 470 - 0 * k, a * (1 - smooth(rng(t, B_ENG - 0.4, B_ENG + 0.1))), RED, 20)
    # the troubleshooting command waits at Earth
    cmd_a = smooth(rng(t, B_ENG + 0.2, B_ENG + 0.6))
    if cmd_a > 0:
        prog = rng(t, B_SENT - 0.2, B_SIG + 0.3)
        cancelled = smooth(rng(t, B_OWN, B_OWN + 0.4))
        bx, by = ex + 70, ey - 150
        f.rect(bx, by, 260, 70, (12, 8, 7, int(225 * cmd_a)), (239, 226, 196, int(120 * cmd_a)), 1.4)
        f.text('TROUBLESHOOTING COMMAND', bx + 14, by + 26, 13, CREAM, 'mono', alpha=cmd_a)
        f.rect(bx + 14, by + 40, 232 * min(prog, 0.82) + 0.1, 10, (242, 112, 58, int(200 * cmd_a * (1 - cancelled))))
        f.rect(bx + 14, by + 40, 232, 10, None, (239, 226, 196, int(80 * cmd_a)), 1)
        f.text('NOT SENT · NOT NEEDED' if cancelled > 0.5 else 'PREPARING…', bx + 14, by + 66, 11,
               ORANGE if cancelled > 0.5 else CREAM, 'mono_r', alpha=cmd_a)
    # the signal comes back on its own: a pulse from Voyager along the re-formed line
    if B_SIG - 0.2 < t < B_BACK + 0.6:
        u = smooth(rng(t, B_SIG - 0.1, B_BACK + 0.1))
        x, y = m2s(t, lerp(VX, EX, u))
        pulse(f, x, y, 8, col=(255, 210, 150))
    back = smooth(rng(t, B_BACK + 0.05, B_BACK + 0.4))
    if back > 0:
        f.glow(ex, ey, 160, (255, 190, 120), 0.7 * back * (1 - 0.5 * smooth(rng(t, B_BACK + 0.6, B_BACK + 2))))
        stamp(f, 'OCT 20 · SIGNAL BACK', 706, 470, back, (255, 190, 120), 24)
    f.text('SCHEMATIC · NOT TO SCALE', 54, 684, 13, ORANGE, 'mono', alpha=1)
    f.text('SPACECRAFT: NASA SVS 20130', 1226, 684, 13, CREAM, 'mono_r', 'right', alpha=0.8)
    return retro(f.done(), 0.4)


# ------------------------------------------------------------------ DSN: antenna to Voyager's patch of sky
D0 = S['dsn']
D_OCT = c('On October eighteenth')
D_POINT = c('pointed its antennas')
D_PATCH = c("Voyager's patch of sky")
D_NO = c("It didn't detect")
SKY = (900, 190)                          # design px, Voyager's patch of sky (direction, schematic)


_SKYSTARS = None


def sky_chart(f, x, y, w, h, off):
    """night sky above the antenna (schematic star field, not a real chart)."""
    global _SKYSTARS
    if _SKYSTARS is None:
        r = np.random.default_rng(5)
        _SKYSTARS = [(r.uniform(0, 1), r.uniform(0, 1), r.uniform(0.6, 2.3), r.uniform(0.3, 1)) for _ in range(260)]
    vis0, vis1 = max(y, y + off), min(y + h, y + off + h)
    if vis1 - vis0 < 1:
        return
    hh = int(round((vis1 - vis0) * 1.5))
    v = (np.arange(hh) / 1.5 + vis0 - (y + off)) / h
    top, mid, bot = np.array([4, 6, 11.]), np.array([11, 20, 38.]), np.array([29, 53, 80.])
    col = np.where(v[:, None] < 0.7, top + (mid - top) * (v[:, None] / 0.7), mid + (bot - mid) * ((v[:, None] - 0.7) / 0.3))
    grad = np.repeat(col[:, None, :], int(round(w * 1.5)), 1).astype(np.uint8)
    f.paste(Image.fromarray(grad, 'RGB'), x, vis0)
    for (u, v, rr, a) in _SKYSTARS:
        sy = y + off + v * h
        if y <= sy <= y + h:
            f.circle(x + u * w, sy, rr, (230, 236, 255, int(255 * a)))


def bg_dsn(t):
    f = Frame()
    f.background('#1c1411', '#080605')
    x, y, w, h = BOX
    # 1) the antenna (real photo) slowly pushed in; 2) at 'pointed its antennas' the view tilts up
    # off the photo into the night sky toward Voyager's direction (schematic)
    tilt = smooth(rng(t, D_POINT - 0.2, D_POINT + 1.6))
    photo_off = tilt * h * 0.78
    clip_in_box(f, dish(), zoom=1.08 + 0.05 * rng(t, D0, D_POINT), fx=0.5, fy=0.7)
    if tilt > 0:
        # sky slides down from above the photo, photo slides down out of the frame
        base = f.done()
        f = Frame(base)
        f.rect(x, y, w, photo_off / 1.0, (0, 0, 0, 255))
        sky_chart(f, x, y, w, h, photo_off - h)
        # photo strip that remains (shifted down)
        crop = base.crop((int(x * 1.5), int(y * 1.5), int((x + w) * 1.5), int((y + h - photo_off) * 1.5)))
        if crop.size[1] > 2:
            ramp = np.clip(np.arange(crop.size[1]) / 140.0, 0, 1) if photo_off > 1 else np.ones(crop.size[1])
            al = (np.repeat(ramp[:, None], crop.size[0], 1) * 255).astype(np.uint8)
            crop = crop.convert('RGBA')
            crop.putalpha(Image.fromarray(al))
            f.paste(crop, x, y + photo_off)
    sx, sy = SKY
    # beam from the dish rim (now at the bottom edge) up to the patch
    dcx, dcy = x + w * 0.4, min(y + h - 8, y + h * 0.45 + photo_off)
    beam = smooth(rng(t, D_POINT + 0.5, D_POINT + 1.6))
    if beam > 0:
        for k in range(3):
            off = (k - 1) * 26
            f.line([(dcx, dcy), (lerp(dcx, sx + off, beam), lerp(dcy, sy, beam))], (242, 112, 58, int(130 * beam)), 1.8, dash=(8, 7))
    patch = smooth(rng(t, D_PATCH - 0.2, D_PATCH + 0.4))
    dim = 1 - 0.55 * smooth(rng(t, D_NO + 0.3, D_NO + 1.0))
    if patch > 0:
        f.circle(sx, sy, 70 - 12 * patch, None, (239, 226, 196, int(230 * patch * dim)), 2)
        f.circle(sx, sy, 4, CREAM + (int(255 * patch * dim),))
        f.text("VOYAGER 1'S PATCH OF SKY", sx, sy - 76, 14, CREAM, 'mono', 'center', alpha=patch * dim)
        f.text('IN THE CONSTELLATION OPHIUCHUS', sx, sy + 84, 12, CREAM, 'mono_r', 'center', alpha=patch * dim * 0.85)
    # listening: rings climb the beam, nothing comes back
    for k in range(3):
        u = rng(t, D_NO - 0.5 + k * 0.4, D_NO + 0.6 + k * 0.4)
        if 0 < u < 1:
            f.circle(lerp(dcx, sx, u), lerp(dcy, sy, u), 6 + 12 * u, None, (239, 226, 196, int(210 * (1 - u))), 1.8)
    no = smooth(rng(t, c('detect a signal') - 0.05, c('detect a signal') + 0.3))
    stamp(f, 'OCT 18 · NO SIGNAL DETECTED', x + w * 0.5, y + h - 50, no, RED, 24)
    # date flips back from Oct 20 to Oct 18
    flip = smooth(rng(t, D_OCT, D_OCT + 0.5))
    f.rect(x + 18, y + 18, 190, 60, (10, 7, 6, 215), (239, 226, 196, 70), 1)
    f.text('OCT 20' if flip < 0.5 else 'OCT 18', x + 113, y + 60, 30, ORANGE if flip >= 0.5 else CREAM, 'mono', 'center',
           alpha=abs(flip - 0.5) * 2)
    box_frame(f, 1.0, 'DSN ANTENNA (EXAMPLE) · SKY, BEAM & PATCH: ILLUSTRATION',
              'PHOTO: NASA / CANBERRA DEEP SPACE COMMUNICATION COMPLEX')
    return retro(f.done(), 0.35)


# ------------------------------------------------------------------ dispatch
def background(t):
    k = scene_at(t)
    img = {'cover': bg_cover, 'away': bg_away, 'map': bg_map, 'dsn': bg_dsn}[k](t)
    # short dip between scenes so cuts feel motivated (no long dissolve)
    return img


# ------------------------------------------------------------------ ATLAS
def build_host(atlas):
    shots = []
    for k in ORDER:
        fx, fy, sc, fc = PLACE[k]
        shots.append(Shot(S[k] if k != 'cover' else -5.0, end_of(k), fx, fy, sc, fc))
    h = Host(atlas, shots, VOICE_WAV, VOICE_JSON, DUR, offset=0.0)
    # cover: he fires the command along the waveform - the hand follows the pulse
    h.point(-2.0, lambda t: (min(cover_pulse_x(t) - 30, 980.0), 640.0), S['away'] - 0.5, gaze_lead=0.0)
    h.brow(1.9, 0.5, 1.0)
    # away: small, watches the craft in the frame, points at the clock when it hits 24 h
    s0, e = S['away'], end_of('away')
    x, y, w, hh = BOX
    h.gaze(s0 + 0.2, ('s', ((x + w * 0.5) * 1.5, (y + hh * 0.5) * 1.5)), look=0.7)
    h.point(c('full day') - 0.45, ((x + w - 127) * 1.5, (y + 80) * 1.5), e - 0.4)
    # map: follows the reply to Earth, reacts to the silence, then to the returning signal
    s0, e = S['map'], end_of('map')
    h.gaze(s0 + 0.2, ('s', (1700, 450)), look=0.8)
    h.point(R0 + 0.4, lambda t: tuple(np.array(m2s(t, reply_x(t))) * 1.5), R1 + 0.3, gaze_lead=0.1)
    h.gaze(L_LISTEN - 0.2, ('s', (1500, 450)), look=0.6)
    h.brow(L_NOTHING, -0.6, 1.2)
    h.gaze(L_NOTHING + 0.2, None, look=-0.9)
    h.walk(B_ENG - 0.1, 70)
    h.point(B_SIG - 0.15, lambda t: tuple(np.array(m2s(t, lerp(VX, EX, smooth(rng(t, B_SIG - 0.1, B_BACK + 0.1))))) * 1.5),
            B_OWN + 0.6, gaze_lead=0.0)
    h.brow(B_BACK + 0.1, 0.9, 1.3)
    # dsn: looks up to the sky patch with the antenna, points at it, lowers the arm when nothing comes
    s0, e = S['dsn'], end_of('dsn')
    h.gaze(s0 + 0.3, ('s', ((x + w * 0.47) * 1.5, (y + hh * 0.7) * 1.5)), look=0.7)
    h.point(D_PATCH - 0.3, (SKY[0] * 1.5, SKY[1] * 1.5), D_NO + 0.4)
    h.brow(D_NO + 0.6, -0.5, 1.2)
    h.gaze(D_NO + 0.9, None, look=-0.8)
    h.auto(emphasis=('day', 'nothing', 'twice', 'own', 'sky', 'signal'))
    return h


def overlay(t, img):
    pass


# ------------------------------------------------------------------ sound: score sections + accents
MUSIC = [(0.0, 0.55), (3.0, 0.7), (7.0, 0.75), (12.6, 0.3), (16.5, 0.45), (20.2, 0.85), (22.5, 0.5), (29.3, 0.25),
         (40.0, 0.4)]
SFX = [(P0, 'send', -16), (S['away'] - 0.35, 'whoosh', -20), (A_ARRIVE, 'arrive', -17), (S['map'] - 0.3, 'whoosh', -22),
       (R0 + 0.3, 'send', -19), (R1, 'arrive', -18), (L_LISTEN + 0.2, 'stamp', -15), (L_TWICE + 0.25, 'stamp', -15),
       (L_NOTHING - 0.2, 'lost', -20), (B_SIG - 0.1, 'back', -16), (B_BACK + 0.05, 'hit', -14),
       (S['dsn'] - 0.3, 'whoosh', -21), (D_POINT, 'send', -21), (c('detect a signal') - 0.05, 'stamp', -15)]
