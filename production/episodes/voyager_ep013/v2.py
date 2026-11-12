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
S['thr'] = c('Once engineers could see') - 0.25
S['trip'] = c("Here's what makes troubleshooting") - 0.25
S['dist'] = c('On November eighteenth, Voyager will') - 0.25
S['power'] = c('In September, the engineers') - 0.25
S['hist'] = c('Voyager left Earth') - 0.2
S['helio'] = c('In twenty twelve') - 0.25
S['fin'] = c('Now look at the timeline') - 0.25
PILOT_END = ce("It didn't detect a signal") + 0.55
ORDER = ['cover', 'away', 'map', 'dsn', 'thr', 'trip', 'dist', 'power', 'hist', 'helio', 'fin']
if PILOT:
    ORDER = ORDER[:4]
DUR = round(PILOT_END, 2) if PILOT else round(C.last_end() + 1.6, 2)


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
PLACE = dict(cover=BIG, away=SMALL, map=MED, dsn=SMALL, thr=MED, trip=MED, dist=MED, power=MED, hist=SMALL,
             helio=SMALL, fin=BIG)

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
D_24 = c('Twenty-four hours later')
D_AGAIN = c('tried again')
D_STILL = c('Still nothing')
D_20 = c('On the twentieth')
D_RE = c('signal reappeared')
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
    fail1 = smooth(rng(t, D_NO + 0.3, D_NO + 1.0)) * (1 - smooth(rng(t, D_AGAIN - 0.3, D_AGAIN + 0.2)))
    fail2 = smooth(rng(t, D_STILL, D_STILL + 0.6)) * (1 - smooth(rng(t, D_20 - 0.2, D_20 + 0.2)))
    found = smooth(rng(t, D_RE - 0.2, D_RE + 0.4))
    dim = 1 - 0.55 * max(fail1, fail2)
    if patch > 0:
        col = (255, 196, 130) if found > 0.5 else CREAM
        f.circle(sx, sy, 70 - 12 * patch, None, col + (int(230 * patch * dim),), 2 + 1.5 * found)
        f.circle(sx, sy, 4 + 3 * found, col + (int(255 * patch * dim),))
        if found > 0:
            f.glow(sx, sy, 110, ORANGE, 0.8 * found)
        f.text("VOYAGER 1'S PATCH OF SKY", sx, sy - 76, 14, CREAM, 'mono', 'center', alpha=patch * dim)
        f.text('IN THE CONSTELLATION OPHIUCHUS', sx, sy + 84, 12, CREAM, 'mono_r', 'center', alpha=patch * dim * 0.85)
    # listening: rings climb the beam (Oct 18, Oct 19) and nothing comes back
    for t_try in (D_NO, D_AGAIN):
        for k in range(3):
            u = rng(t, t_try - 0.5 + k * 0.4, t_try + 0.6 + k * 0.4)
            if 0 < u < 1:
                f.circle(lerp(dcx, sx, u), lerp(dcy, sy, u), 6 + 12 * u, None, (239, 226, 196, int(210 * (1 - u))), 1.8)
    # Oct 20: the answer comes down the beam
    for k in range(4):
        u = rng(t, D_RE + k * 0.3, D_RE + 1.1 + k * 0.3)
        if 0 < u < 1:
            f.circle(lerp(sx, dcx, u), lerp(sy, dcy, u), 14 - 6 * u, None, (255, 196, 130, int(240 * (1 - u * 0.5))), 2.4)
    if found > 0:
        f.glow(dcx, dcy, 90, ORANGE, 0.6 * smooth(rng(t, D_RE + 1.0, D_RE + 1.5)))
    no = smooth(rng(t, c('detect a signal') - 0.05, c('detect a signal') + 0.3)) * (1 - smooth(rng(t, D_24 - 0.2, D_24 + 0.1)))
    stamp(f, 'OCT 18 · NO SIGNAL DETECTED', x + w * 0.5, y + h - 50, no, RED, 24)
    no2 = smooth(rng(t, D_STILL - 0.05, D_STILL + 0.3)) * (1 - smooth(rng(t, D_20 - 0.2, D_20 + 0.1)))
    stamp(f, 'OCT 19 · STILL NOTHING', x + w * 0.5, y + h - 50, no2, RED, 24)
    stamp(f, 'OCT 20 · SIGNAL REAPPEARS', x + w * 0.5, y + h - 50, smooth(rng(t, D_RE + 0.2, D_RE + 0.5)), (255, 196, 130), 24)
    # the date card: Oct 20 (where the map left off) -> back to Oct 18 -> 19 -> 20
    marks = [(D_OCT, 'OCT 18'), (D_24, 'OCT 19'), (D_20, 'OCT 20')]
    cur, prev, tk = 'OCT 20', 'OCT 20', -10.0
    for tm, lab in marks:
        if t >= tm:
            prev, cur, tk = cur, lab, tm
    flip = smooth(rng(t, tk, tk + 0.5))
    f.rect(x + 18, y + 18, 190, 60, (10, 7, 6, 215), (239, 226, 196, 70), 1)
    f.text(prev if flip < 0.5 else cur, x + 113, y + 60, 30, ORANGE, 'mono', 'center', alpha=max(0.05, abs(flip - 0.5) * 2))
    box_frame(f, 1.0, 'DSN ANTENNA (EXAMPLE) · SKY, BEAM & PATCH: ILLUSTRATION',
              'PHOTO: NASA / CANBERRA DEEP SPACE COMMUNICATION COMPLEX')
    return retro(f.done(), 0.35)


# ------------------------------------------------------------------ thrusters: the clue in the data
T0 = S['thr'] if 'thr' in S else 999
T_CLUE = c('they found a clue')
T_OFF = c('One group of thrusters')
T_BACKUP = c('its backup had')
T_AUTO = c('Voyager is programmed')
T_WHY = c('What triggered')
T_INV = c('still under investigation')


@lru_cache(maxsize=1)
def craft_close():
    return Video(os.path.join(MEDIA, 'cuts', 'v_craft_0-7.mp4'))


def nozzle_group(f, x, y, on, label, state, col):
    """four thruster nozzles (generic icon) with a state label."""
    for k in range(4):
        nx = x + (k - 1.5) * 34
        f.poly([(nx - 10, y), (nx + 10, y), (nx + 15, y + 30), (nx - 15, y + 30)], (30, 22, 18, 255), CREAM + (180,), 1.4)
        if on > 0:
            for j in range(3):
                L = 22 + 10 * math.sin(time_phase + j * 2.1 + k)
                f.poly([(nx - 9, y + 32), (nx + 9, y + 32), (nx, y + 32 + L)], ORANGE + (int(200 * on),))
    f.text(label, x, y - 18, 13, CREAM, 'mono', 'center')
    f.text(state, x, y + 82, 15, col, 'mono', 'center')


time_phase = 0.0


def bg_thr(t):
    global time_phase
    time_phase = t * 9
    f = Frame()
    f.background('#1c1411', '#080605')
    x, y, w, h = BOX
    # A) close-ups of the spacecraft (NASA animation) while engineers 'see what it had been doing'
    k_diag = smooth(rng(t, T_OFF - 0.6, T_OFF + 0.2))
    if k_diag < 1:
        fr = craft_close().at(min(6.9, (t - T0) * 1.1))
        fr = Image.fromarray(np.clip((np.asarray(fr, np.float32) / 255) ** 0.6 * 255 * 1.1, 0, 255).astype(np.uint8))
        clip_in_box(f, fr, zoom=1.15 + 0.06 * rng(t, T0, T_OFF), fx=0.5, fy=0.5,
                    alpha=1 - k_diag)
        clue = smooth(rng(t, T_CLUE, T_CLUE + 0.4)) * (1 - k_diag)
        if clue > 0:
            f.rect(x + w / 2 - 150, y + h - 92, 300, 52, (12, 8, 7, int(225 * clue)), ORANGE + (int(255 * clue),), 2)
            f.text('A CLUE', x + w / 2, y + h - 56, 26, ORANGE, 'mono', 'center', alpha=clue)
    # B) the clue as a schematic: primary group goes offline, backup switches on automatically
    if k_diag > 0:
        f.rect(x, y, w, h, (16, 11, 9, int(255 * k_diag)))
        f.group(k_diag)
        sp = craft_sprite()
        im = sp.resize((int(sp.size[0] * 0.55), int(sp.size[1] * 0.55)), Image.LANCZOS)
        f.paste(im, x + w * 0.5 - im.size[0] / 3, y + 40)
        off = smooth(rng(t, T_OFF + 0.6, T_OFF + 1.2))
        on = smooth(rng(t, T_BACKUP + 0.2, T_BACKUP + 0.6))
        g1x, g2x, gy = x + w * 0.2, x + w * 0.8, y + 300
        nozzle_group(f, g1x, gy, 1 - off, 'THRUSTER GROUP', 'OFFLINE' if off > 0.5 else 'ACTIVE', RED if off > 0.5 else CREAM)
        nozzle_group(f, g2x, gy, on, 'BACKUP GROUP', 'SWITCHED ON' if on > 0.5 else 'STANDBY', ORANGE if on > 0.5 else (150, 140, 120))
        if off > 0.5:
            f.line([(g1x - 70, gy - 5), (g1x + 70, gy + 45)], RED + (220,), 3)
            f.line([(g1x - 70, gy + 45), (g1x + 70, gy - 5)], RED + (220,), 3)
        auto = smooth(rng(t, T_AUTO, T_AUTO + 0.9))
        if auto > 0:
            ax0, ax1 = g1x + 90, lerp(g1x + 90, g2x - 90, auto)
            f.line([(ax0, gy + 15), (ax1, gy + 15)], ORANGE + (230,), 3)
            if auto > 0.95:
                f.poly([(g2x - 90, gy + 15), (g2x - 104, gy + 6), (g2x - 104, gy + 24)], ORANGE + (230,))
            f.text('AUTOMATIC SWITCH · BUILT INTO VOYAGER', (g1x + g2x) / 2, gy - 8, 13, ORANGE, 'mono', 'center', alpha=auto)
        why = smooth(rng(t, T_WHY, T_WHY + 0.5))
        if why > 0:
            bx, by = x + w / 2 - 230, y + h - 120
            f.rect(bx, by, 460, 84, (12, 8, 7, int(235 * why)), CREAM + (int(120 * why),), 1.4)
            f.text('?', bx + 40, by + 64, 54, ORANGE, 'sans', 'center', alpha=why)
            f.text('WHAT TRIGGERED THE OUTAGE', bx + 80, by + 34, 15, CREAM, 'mono', alpha=why)
            inv = smooth(rng(t, T_INV, T_INV + 0.4))
            f.text('STILL UNDER INVESTIGATION (NASA)', bx + 80, by + 62, 15, ORANGE, 'mono', alpha=why * inv)
        f.end()
    lab = 'NASA ANIMATION · VOYAGER SPACECRAFT' if k_diag < 0.5 else 'SCHEMATIC · SUMMARY OF NASA\'S REPORT'
    box_frame(f, 1.0, lab, 'NASA SVS 20130' if k_diag < 0.5 else 'THRUSTER ICONS: ILLUSTRATION')
    return retro(f.done(), 0.35)


# ------------------------------------------------------------------ round trip: a space-time diagram
TR0 = S['trip'] if 'trip' in S else 999
TR_SEND0 = c('The first day goes by')
TR_HEAR = c('finally hears you')
TR_REPLY0 = c('If it responds immediately')
TR_HOME = ce('still on its way home')
TR_BIG = c("That's forty-eight hours")
TR_TRY = c('try something different')
TR_LOOP = c('the next command starts')
TR_NEAR = c('a spacecraft near Earth')
HPX = 13.0                   # design px per hour


def tr_cam(t):
    return _keys(t, [(TR0, 0.0), (TR_TRY - 0.5, 0.0), (TR_LOOP + 2.5, 330.0)])[0]


def tr_xy(t, hour, lane):
    """lane 0 = Earth (bottom), 1 = Voyager (top)"""
    return 370 + hour * HPX - tr_cam(t), 470 - lane * 290


def bg_trip(t):
    f = Frame()
    f.background('#1f1713', '#0a0706')
    f.starfield(t, 60)
    f.kick('ONE CONVERSATION WITH VOYAGER 1  ·  TIME →', 290, 62, ORANGE)
    # lanes
    for lane, name in ((0, 'EARTH'), (1, 'VOYAGER 1')):
        x0, y0 = tr_xy(t, 0, lane)
        x1, _ = tr_xy(t, 120, lane)
        f.line([(x0 - 20, y0), (x1, y0)], CREAM + (110,), 2)
        f.text(name, x0 - 30, y0 + 5, 14, CREAM, 'mono', 'right')
    # hour ticks
    for hr in range(0, 121, 12):
        x, y = tr_xy(t, hr, 0)
        if 250 < x < 1280:
            f.line([(x, y), (x, y + 10)], CREAM + (120,), 1.4)
            f.text(f'{hr} H', x, y + 30, 12, CREAM, 'mono_r', 'center', alpha=0.75)
    # near-Earth contrast at the start
    near = smooth(rng(t, TR_NEAR - 0.3, TR_NEAR + 0.3)) * (1 - smooth(rng(t, TR_SEND0 - 0.4, TR_SEND0 + 0.2)))
    if near > 0:
        x, y = tr_xy(t, 0, 0)
        f.line([(x, y), (x + 4, y - 60), (x + 8, y)], CREAM + (int(220 * near),), 2)
        f.text('NEAR EARTH: THE ANSWER IS BACK IN SECONDS', x + 20, y - 70, 14, CREAM, 'mono', alpha=near)
    def leg(ta, tb, h0, l0, h1, l1, col):
        u = smooth(rng(t, ta, tb))
        if u <= 0:
            return None
        xa, ya = tr_xy(t, h0, l0)
        xb, yb = tr_xy(t, h1, l1)
        xe, ye = lerp(xa, xb, u), lerp(ya, yb, u)
        f.line([(xa, ya), (xe, ye)], col + (230,), 3)
        if u < 1:
            pulse(f, xe, ye, 7, col=col)
        return xe, ye
    leg(TR_SEND0 - 0.1, TR_HEAR + 0.2, 0, 0, 24, 1, ORANGE)
    leg(TR_REPLY0 + 0.2, TR_HOME, 24, 1, 48, 0, (255, 196, 130))
    leg(TR_LOOP, TR_LOOP + 3.0, 48, 0, 72, 1, ORANGE)
    for hr, lane, tt, lab in ((0, 0, TR_SEND0, 'COMMAND SENT'), (24, 1, TR_HEAR + 0.2, 'VOYAGER HEARS IT'),
                              (48, 0, TR_HOME, 'ANSWER ARRIVES'), (48, 0, TR_TRY + 0.2, 'TRY SOMETHING ELSE?')):
        a = smooth(rng(t, tt, tt + 0.4))
        if hr == 48 and lab == 'ANSWER ARRIVES':
            a *= 1 - smooth(rng(t, TR_TRY, TR_TRY + 0.3))
        if a > 0:
            x, y = tr_xy(t, hr, lane)
            f.circle(x, y, 7, CREAM + (int(255 * a),))
            f.text(lab, x, y + (58 if lane == 0 else -22), 14, ORANGE, 'mono', 'center', alpha=a)
    # the 48 h brace
    big = smooth(rng(t, TR_BIG, TR_BIG + 0.5)) * (1 - smooth(rng(t, TR_TRY - 0.6, TR_TRY)))
    if big > 0:
        xa, ya = tr_xy(t, 0, 0)
        xb, _ = tr_xy(t, 48 * big, 0)
        f.line([(xa, ya + 80), (xb, ya + 80)], ORANGE + (255,), 4)
        f.text('48 HOURS OF TRAVEL TIME ALONE', (xa + tr_xy(t, 48, 0)[0]) / 2, ya + 116, 26, ORANGE, 'sans', 'center', alpha=big)
    loop = smooth(rng(t, TR_LOOP + 1.2, TR_LOOP + 1.8))
    if loop > 0:
        x, y = tr_xy(t, 72, 1)
        f.text('…AND THE WHOLE TRIP STARTS AGAIN', x, y - 50, 16, ORANGE, 'mono', 'center', alpha=loop)
    f.text('SCHEMATIC · ROUND TRIP AT ABOUT 24 H EACH WAY (NOV 2026)', 290, 684, 13, ORANGE, 'mono')
    return retro(f.done(), 0.4)


# ------------------------------------------------------------------ distance: zoom out to one light-day
DI0 = S['dist'] if 'dist' in S else 999
DI_MILES = c('sixteen billion miles')
DI_LDAY = c('That distance is one light-day')
DI_MARK = c("There's no marker")
DI_CONV = c('what that distance does')
AU_VOY = 172.0               # about 16 billion miles in AU (Nov 2026)
VOY_ANG = math.radians(-24)
SUN = (760, 360)


def di_scale(t):
    """design px per AU: from Earth's orbit filling the view to Voyager's distance."""
    u = smooth(rng(t, DI0 + 0.2, DI_LDAY + 0.5))
    return math.exp(lerp(math.log(150.0), math.log(470.0 / AU_VOY), u))


def bg_dist(t):
    f = Frame()
    f.background('#160f0d', '#050404')
    f.starfield(t, 90)
    k = di_scale(t)
    sx, sy = SUN
    f.glow(sx, sy, 40, (255, 200, 120), 0.9)
    f.circle(sx, sy, 5, (255, 236, 200))
    for au, name in ((1.0, 'EARTH'), (5.2, 'JUPITER'), (9.5, 'SATURN'), (30.1, 'NEPTUNE')):
        r = au * k
        if 4 < r < 2400:
            a = clamp((r - 4) / 10) * clamp((2400 - r) / 400)
            f.circle(sx, sy, r, None, CREAM + (int(90 * a),), 1.2)
            if r > 30:
                f.text(name, sx + r * 0.7, sy - r * 0.72 - 6, 11, CREAM, 'mono_r', 'center', alpha=a * 0.8)
    ex, ey = sx + k, sy
    vx, vy = sx + AU_VOY * k * math.cos(VOY_ANG), sy + AU_VOY * k * math.sin(VOY_ANG)
    f.circle(ex, ey, 5, (120, 180, 230))
    # Voyager's path (direction only) and the probe
    f.line([(sx, sy), (vx, vy)], ORANGE + (120,), 1.6, dash=(6, 6))
    sp = craft_sprite()
    im = sp.resize((44, int(44 * sp.size[1] / sp.size[0])), Image.LANCZOS)
    f.paste(im, vx - 14, vy - 20)
    f.text('VOYAGER 1', vx, vy + 48, 13, CREAM, 'mono', 'center')
    # a light pulse leaves Earth and takes a day to reach Voyager
    u = rng(t, DI_MILES - 0.3, DI_LDAY + 0.8)
    if 0 < u <= 1:
        px, py = lerp(ex, vx, u), lerp(ey, vy, u)
        f.line([(ex, ey), (px, py)], (255, 220, 160, 200), 2.2)
        pulse(f, px, py, 6, col=(255, 220, 160))
    if u > 0:
        clock(f, 24 * u, 1080, 560, 'LIGHT TRAVEL TIME', a=1.0, col=ORANGE if u >= 1 else CREAM)
    m = smooth(rng(t, DI_MILES, DI_MILES + 0.4))
    f.text('≈ 16 BILLION MILES', (sx + vx) / 2 - 40, (sy + vy) / 2 - 40, 28, CREAM, 'sans', 'center', alpha=m)
    f.text('≈ 26 BILLION KM · NOV 18, 2026', (sx + vx) / 2 - 40, (sy + vy) / 2 - 12, 13, CREAM, 'mono_r', 'center', alpha=m)
    ld = smooth(rng(t, DI_LDAY + 0.6, DI_LDAY + 1.1))
    f.text('= ONE LIGHT-DAY', (sx + vx) / 2 - 40, (sy + vy) / 2 + 22, 24, ORANGE, 'mono', 'center', alpha=ld)
    # 'no marker': a ring is drawn for scale, then labelled as nothing that exists out there
    mk = smooth(rng(t, DI_MARK - 0.2, DI_MARK + 1.0))
    if mk > 0:
        r = AU_VOY * k
        f.arc(sx, sy, r, -100, -100 + 360 * mk, CREAM + (int(90 * (1 - 0.5 * smooth(rng(t, DI_CONV, DI_CONV + 1)))),), 1.4)
        f.text('NO LINE OUT THERE · DRAWN ONLY FOR SCALE', sx, sy + r + 30 if sy + r + 30 < 600 else 600, 13, CREAM,
               'mono_r', 'center', alpha=mk * (1 - smooth(rng(t, DI_CONV, DI_CONV + 0.5))))
    cv = smooth(rng(t, DI_CONV, DI_CONV + 0.6))
    if cv > 0:
        f.text('EVERY QUESTION: 24 H OUT · EVERY ANSWER: 24 H BACK', 760, 640, 17, ORANGE, 'mono', 'center', alpha=cv)
    f.text('SCHEMATIC · DISTANCES TO SCALE, SIZES NOT', 290, 684, 13, ORANGE, 'mono')
    return retro(f.done(), 0.4)


# ------------------------------------------------------------------ power: three swaps at once
PW0 = S['power'] if 'power' in S else 999
PW_WATT = c('every watt matters')
PW_OFF = c('They switched off')
PW_ON = c('turned on three')
PW_WARM = c('help keep the spacecraft')
PW_TOG = c('all three swaps together')
PW_HEAT = c('keep the heat distributed')
PW_ROOM = c('The change bought')
PW_WITHOUT = c('Without it, NASA says')
PW_2027 = c('summer of twenty twenty-seven')


def bg_power(t):
    f = Frame()
    f.background('#1c1411', '#080605')
    x, y, w, h = BOX
    f.rect(x, y, w, h, (14, 10, 9, 255), CREAM + (110,), 1.4)
    # left: the spacecraft (from the NASA animation) with a warmth glow (illustration)
    sp = craft_sprite()
    im = sp.resize((int(sp.size[0] * 0.62), int(sp.size[1] * 0.62)), Image.LANCZOS)
    cx, cy = x + 200, y + 250
    warm = 0.55 + 0.12 * math.sin(t * 1.3)
    f.glow(cx, cy + 30, 190, (232, 92, 40), 0.35 * warm)
    f.paste(im, cx - im.size[0] / 3, cy - im.size[1] / 3)
    # power budget: what's available drifts down; the swap restores the margin
    pa = smooth(rng(t, PW_WATT - 0.6, PW_WATT))
    if pa > 0:
        avail = lerp(0.78, 0.70, rng(t, PW0, PW_ROOM)) + 0.0
        need = lerp(0.74, 0.74, 0) - 0.10 * smooth(rng(t, PW_ON + 0.2, PW_ROOM + 0.4))
        bx, by, bw = x + 30, y + 470, 340
        f.text('POWER AVAILABLE vs NEEDED (ILLUSTRATIVE)', bx, by - 16, 12, CREAM, 'mono_r', alpha=pa)
        f.rect(bx, by, bw * avail, 16, CREAM + (int(200 * pa),))
        f.rect(bx, by + 24, bw * need, 16, ORANGE + (int(220 * pa),))
        room = smooth(rng(t, PW_ROOM, PW_ROOM + 0.5))
        if room > 0:
            f.rect(bx + bw * need, by + 22, bw * (avail - need), 20, None, (255, 220, 160, int(255 * room)), 2)
            f.text('BREATHING ROOM', bx + bw * (need + avail) / 2, by + 62, 14, (255, 220, 160), 'mono', 'center', alpha=room)
    # right: three devices off, three lower-power replacements on - at the same moment
    for i in range(3):
        ry = y + 90 + i * 120
        rx0, rx1 = x + 470, x + 720
        ap_ = smooth(rng(t, PW_OFF - 0.6 + 0.12 * i, PW_OFF - 0.2 + 0.12 * i))
        if ap_ <= 0:
            continue
        off = smooth(rng(t, PW_TOG - 0.1, PW_TOG + 0.25))      # all three flip together
        f.rect(rx0, ry, 190, 64, (20, 14, 12, int(240 * ap_)), (RED if off > 0.5 else CREAM) + (int(160 * ap_),), 1.4)
        f.text(f'DEVICE {i + 1}', rx0 + 14, ry + 26, 14, CREAM, 'mono', alpha=ap_)
        f.text('OFF' if off > 0.5 else 'ON', rx0 + 14, ry + 50, 14, RED if off > 0.5 else CREAM, 'mono', alpha=ap_)
        ar = smooth(rng(t, PW_ON - 0.2, PW_ON + 0.3)) * ap_
        if ar > 0:
            f.line([(rx0 + 196, ry + 32), (rx1 - 8, ry + 32)], ORANGE + (int(200 * ar),), 2, dash=(6, 5))
            f.rect(rx1, ry, 200, 64, (20, 14, 12, int(240 * ar)), (ORANGE if off > 0.5 else (150, 140, 120)) + (int(200 * ar),), 1.4)
            f.text('LOWER-POWER', rx1 + 14, ry + 26, 14, CREAM, 'mono', alpha=ar)
            f.text('ON' if off > 0.5 else 'READY', rx1 + 14, ry + 50, 14, ORANGE if off > 0.5 else (150, 140, 120), 'mono', alpha=ar)
    tog = smooth(rng(t, PW_TOG, PW_TOG + 0.4))
    if tog > 0:
        f.line([(x + 930, y + 90), (x + 942, y + 90), (x + 942, y + 394), (x + 930, y + 394)], ORANGE + (int(230 * tog),), 2.5)
        f.text('ALL 3', x + 935, y + 430, 16, ORANGE, 'mono', 'center', alpha=tog)
        f.text('AT ONCE', x + 935, y + 450, 13, ORANGE, 'mono_r', 'center', alpha=tog)
    heat = smooth(rng(t, PW_HEAT, PW_HEAT + 0.5)) * (1 - smooth(rng(t, PW_ROOM - 0.2, PW_ROOM + 0.2)))
    if heat > 0:
        f.text('HEAT STAYS EVENLY SPREAD', cx, cy - 190, 14, ORANGE, 'mono', 'center', alpha=heat)
    wo = smooth(rng(t, PW_WITHOUT, PW_WITHOUT + 0.5))
    if wo > 0:
        f.rect(x + 450, y + h - 120, 480, 90, (12, 8, 7, int(240 * wo)), RED + (int(200 * wo),), 1.6)
        f.text('WITHOUT THE SWAP (NASA):', x + 470, y + h - 88, 14, CREAM, 'mono', alpha=wo)
        f.text('ANOTHER SCIENCE INSTRUMENT OFF', x + 470, y + h - 62, 15, RED, 'mono', alpha=wo)
        f.text('AS EARLY AS SUMMER 2027', x + 470, y + h - 40, 15, RED, 'mono', alpha=wo * smooth(rng(t, PW_2027, PW_2027 + 0.4)))
    f.text('SEPTEMBER 2026 · KEEPING VOYAGER 1 WARM', x + 18, y + 34, 16, ORANGE, 'mono')
    box_frame(f, 1.0, 'SCHEMATIC · DEVICE BOXES & POWER BARS: ILLUSTRATION', 'SPACECRAFT: NASA SVS 20130')
    return retro(f.done(), 0.35)


# ------------------------------------------------------------------ history: 1977 -> Jupiter/Saturn -> Pale Blue Dot
HI0 = S['hist'] if 'hist' in S else 999
HI_JUP = c('It flew past Jupiter')
HI_SAT = c('and Saturn')
HI_1990 = c('In nineteen ninety')
HI_PIC = c('took this picture')
HI_SPECK = c('That little speck')
HI_HOURS = c('It had already taken hours')
PB_EARTH = (1307, 1131)            # Earth in paleblue.jpg (px)


@lru_cache(maxsize=1)
def traj():
    return Video(os.path.join(MEDIA, 'cuts', 'v_traj_0-50.mp4'))


@lru_cache(maxsize=1)
def jup():
    return Video(os.path.join(MEDIA, 'cuts', 'v_jupiter.mp4'))


@lru_cache(maxsize=1)
def paleblue():
    return Image.open(scenes.A('paleblue.jpg')).convert('RGB')


def bg_hist(t):
    f = Frame()
    f.background('#1c1411', '#080605')
    x, y, w, h = BOX
    if t < HI_1990 - 0.15:
        src = float(np.interp(t, [HI0, HI_JUP, HI_SAT, HI_1990], [2.0, 36.0, 46.0, 49.5]))
        clip_in_box(f, traj().at(src), zoom=1.05)
        j = smooth(rng(t, HI_JUP, HI_JUP + 0.35)) * (1 - smooth(rng(t, HI_SAT + 0.2, HI_SAT + 0.5)))
        if j > 0:
            jx, jy, jw, jh = x + w - 330, y + 24, 300, 169
            f.rect(jx - 3, jy - 3, jw + 6, jh + 6, (10, 7, 6, int(255 * j)), CREAM + (int(160 * j),), 1.4)
            f.image(None, jx, jy, jw, jh, frame=jup().at((t - HI_JUP) * 1.0), alpha=j)
            f.text('JUPITER · FROM VOYAGER IMAGES (NASA SVS)', jx, jy + jh + 18, 11, CREAM, 'mono_r', alpha=j)
        box_frame(f, 1.0, 'NASA DATA VISUALIZATION · VOYAGER 1 TRAJECTORY 1977–1980', 'NASA SVS 4139 (DATES IN THE CLIP)')
    else:
        # the Pale Blue Dot: push in toward the speck, ring it, then light crosses the gap
        z = 1.0 + 1.6 * smooth(rng(t, HI_1990, HI_SPECK + 0.8))
        im = paleblue()
        iw, ih = im.size
        fx = PB_EARTH[0] / iw
        fy = PB_EARTH[1] / ih
        clip_in_box(f, im, zoom=z, fx=fx, fy=fy)
        # where the speck lands in the box (cover-crop math of Frame.image)
        sw = min(iw, ih * w / h) / z
        sh = sw * h / w
        bx0, by0 = (iw - sw) * fx, (ih - sh) * fy
        ex, ey = x + (PB_EARTH[0] - bx0) / sw * w, y + (PB_EARTH[1] - by0) / sh * h
        ring = smooth(rng(t, HI_SPECK - 0.1, HI_SPECK + 0.4))
        if ring > 0:
            f.circle(ex, ey, 34 - 10 * ring, None, (255, 220, 160, int(240 * ring)), 2)
            f.text('EARTH', ex + 40, ey - 30, 16, (255, 220, 160), 'mono', alpha=ring)
        lt = rng(t, HI_HOURS, HI_HOURS + 4.0)
        if lt > 0:
            for kk in range(3):
                u = (lt * 1.2 + kk / 3) % 1
                f.circle(ex, ey, 20 + u * 280, None, (255, 220, 160, int(140 * (1 - u) * min(1, lt * 4))), 1.6)
            f.rect(x + 20, y + h - 96, 400, 70, (10, 7, 6, 220), CREAM + (80,), 1)
            f.text('LIGHT FROM EARTH TO VOYAGER 1', x + 36, y + h - 64, 14, ORANGE, 'mono')
            f.text('≈ 5.5 HOURS · ≈ 40 AU (FEB 1990)', x + 36, y + h - 40, 14, CREAM, 'mono')
        box_frame(f, 1.0, 'VOYAGER 1 PHOTO · PALE BLUE DOT REVISITED · RINGS: ILLUSTRATION', 'NASA / JPL-CALTECH')
    return retro(f.done(), 0.3)


# ------------------------------------------------------------------ heliopause: into interstellar space
HE0 = S['helio'] if 'helio' in S else 999
HE_CROSS = c('crossed the heliopause')
HE_EDGE = c('the edge of the bubble')
HE_SAMPLE = c('sampling interstellar space')


@lru_cache(maxsize=1)
def chase():
    return Video(os.path.join(MEDIA, 'cuts', 'v_chase_110-130.mp4'))


def bg_helio(t):
    f = Frame()
    f.background('#1c1411', '#080605')
    x, y, w, h = BOX
    # source clip 110-130 s of SVS 4139 ChaseV1; Aug 2012 is near 124.3 s -> local 14.3 s
    src = clamp(14.3 + (t - HE_CROSS) * 1.5, 0.0, 19.9)
    clip_in_box(f, chase().at(src), zoom=1.04)
    st = smooth(rng(t, HE_CROSS + 0.2, HE_CROSS + 0.6))
    stamp(f, '2012 · CROSSES THE HELIOPAUSE', x + w * 0.5, y + 70, st * (1 - smooth(rng(t, HE_SAMPLE - 0.3, HE_SAMPLE))), ORANGE, 22)
    edge = smooth(rng(t, HE_EDGE, HE_EDGE + 0.5))
    f.text("THE EDGE OF THE SUN'S BUBBLE (SOLAR WIND)", x + w * 0.5, y + 120, 14, CREAM, 'mono', 'center',
           alpha=edge * (1 - smooth(rng(t, HE_SAMPLE - 0.3, HE_SAMPLE))))
    smp = smooth(rng(t, HE_SAMPLE, HE_SAMPLE + 0.5))
    stamp(f, 'INTERSTELLAR SPACE · SINCE 2012', x + w * 0.5, y + 70, smp, (255, 220, 160), 22)
    box_frame(f, 1.0, 'NASA DATA VISUALIZATION · VOYAGER 1 TRAJECTORY TO THE HELIOPAUSE', 'NASA SVS 4139 (DATES IN THE CLIP)')
    return retro(f.done(), 0.3)


# ------------------------------------------------------------------ finale: the cover again, the whole conversation
FI0 = S['fin'] if 'fin' in S else 999
FI_H0 = c('At hour zero')
FI_H24 = c('At hour twenty-four')
FI_H48 = c('At hour forty-eight')
FI_REM = c('that last moment is')
FI_LINE = c('on the other end of the line')


def fin_pulse(t):
    """x on the cover waveform and direction; out: hand -> probe, back: probe -> hand"""
    if t < FI_H24 + 0.3:
        return lerp(opening.WAVE_X0 + 30, opening.WAVE_X1 + 140, smooth(rng(t, FI_H0 + 0.2, FI_H24 + 0.3))), 1
    return lerp(opening.WAVE_X1 + 140, opening.WAVE_X0 + 30, smooth(rng(t, FI_H24 + 0.8, FI_H48 + 0.4))), -1


def bg_fin(t):
    lt = t - FI0
    push = 1 + 0.02 * smooth(rng(t, FI0, FI0 + 6))
    spec = [('plate', {}), ('probe', dict(s=1 + 0.004 * lt, cx=1690, cy=730, dx=-1.0 * lt)),
            ('lost', dict(alpha=smooth(rng(t, FI0, FI0 + 1.0)))), ('signal', dict(alpha=smooth(rng(t, FI0, FI0 + 1.0)))),
            ('wave', {})]
    img = opening.STACK.render(spec, cam=(0.0, 0.0, push, 1500, 640))
    f = Frame(img)
    xs, d = fin_pulse(t)
    if FI_H0 < t < FI_H48 + 0.5:
        X = (xs - 1500) * push + 1500
        pulse(f, X / 1.5, ((640 - 640) * push + 640) / 1.5, 8, col=ORANGE if d > 0 else (255, 220, 160))
    for tt, lab, px in ((FI_H0, 'HOUR 0 · EARTH SENDS', opening.WAVE_X0 + 20), (FI_H24, 'HOUR 24 · VOYAGER HEARS', opening.WAVE_X1 + 120),
                        (FI_H48, 'HOUR 48 · EARTH HEARS BACK', opening.WAVE_X0 + 20)):
        a = smooth(rng(t, tt, tt + 0.4)) * (1 - smooth(rng(t, tt + 3.0, tt + 3.5)))
        if a > 0:
            f.text(lab, px / 1.5, 470 if 'VOYAGER' not in lab else 520, 17, ORANGE, 'mono', 'center' if 'VOYAGER' in lab else 'left', alpha=a)
    hit = smooth(rng(t, FI_H24 + 0.2, FI_H24 + 0.5)) * (1 - smooth(rng(t, FI_H24 + 1.0, FI_H24 + 1.8)))
    if hit > 0:
        f.glow(1150, 300, 160, ORANGE, 0.7 * hit)
    end = smooth(rng(t, FI_LINE - 0.3, FI_LINE + 0.8))
    if end > 0:
        f.glow(1150, 300, 200, (255, 200, 140), 0.45 * end * (0.85 + 0.15 * math.sin(t * 3)))
        f.text('STILL SOMETHING ON THE OTHER END OF THE LINE', 640, 690, 18, CREAM, 'mono', 'center', alpha=end * 0.0)
    return f.done()


# ------------------------------------------------------------------ dispatch
def background(t):
    k = scene_at(t)
    return {'cover': bg_cover, 'away': bg_away, 'map': bg_map, 'dsn': bg_dsn, 'thr': bg_thr, 'trip': bg_trip,
            'dist': bg_dist, 'power': bg_power, 'hist': bg_hist, 'helio': bg_helio, 'fin': bg_fin}[k](t)


def overlay(t, img):
    pass


# ------------------------------------------------------------------ ATLAS
def P(x, y):
    """design px -> screen px"""
    return (x * 1.5, y * 1.5)


def build_host(atlas):
    shots = []
    for k in ORDER:
        fx, fy, sc, fc = PLACE[k]
        shots.append(Shot(S[k] if k != 'cover' else -5.0, end_of(k), fx, fy, sc, fc))
    h = Host(atlas, shots, VOICE_WAV, VOICE_JSON, DUR, offset=0.0)
    x, y, w, hh = BOX
    # cover: he fires the command along the waveform - the hand follows the pulse
    h.point(-2.0, lambda t: (min(cover_pulse_x(t) - 30, 980.0), 640.0), S['away'] - 0.5, gaze_lead=0.0)
    h.brow(1.9, 0.5, 1.0)
    # away: small, watches the craft in the frame, points at the clock when it hits 24 h
    s0, e = S['away'], end_of('away')
    h.gaze(s0 + 0.2, ('s', P(x + w * 0.5, y + hh * 0.5)), look=0.7)
    h.point(c('full day') - 0.45, P(x + w - 127, y + 80), e - 0.4)
    # map: follows the reply to Earth, reacts to the silence, then to the returning signal
    s0, e = S['map'], end_of('map')
    h.gaze(s0 + 0.2, ('s', (1700, 450)), look=0.8)
    h.point(R0 + 0.4, lambda t: P(*m2s(t, reply_x(t))), R1 + 0.3, gaze_lead=0.1)
    h.gaze(L_LISTEN - 0.2, ('s', (1500, 450)), look=0.6)
    h.brow(L_NOTHING, -0.6, 1.2)
    h.gaze(L_NOTHING + 0.2, None, look=-0.9)
    h.walk(B_ENG - 0.1, 70)
    h.point(B_SIG - 0.15, lambda t: P(*m2s(t, lerp(VX, EX, smooth(rng(t, B_SIG - 0.1, B_BACK + 0.1))))),
            B_OWN + 0.6, gaze_lead=0.0)
    h.brow(B_BACK + 0.1, 0.9, 1.3)
    if PILOT:
        _dsn_host(h, x, y, w, hh)
        h.auto(emphasis=('day', 'nothing', 'twice', 'own', 'sky', 'signal'))
        return h
    _dsn_host(h, x, y, w, hh)
    # thrusters: watches the close-ups, points at the failed group, then the backup, then the question
    s0, e = S['thr'], end_of('thr')
    g1x, g2x, gy = x + w * 0.2, x + w * 0.8, y + 300
    h.gaze(s0 + 0.2, ('s', P(x + w * 0.5, y + hh * 0.5)), look=0.6)
    h.point(T_OFF + 0.4, seq([(0, P(g1x, gy + 10)), (T_BACKUP + 0.1, P(g2x, gy + 10))]), T_AUTO + 1.2)
    h.point(T_WHY + 0.3, P(x + w / 2 - 190, y + hh - 80), e - 0.4)
    h.brow(T_INV, -0.4, 1.4)
    # trip: walks with the command, follows each leg with the hand
    s0, e = S['trip'], end_of('trip')
    h.point(TR_NEAR, P(390, 400), TR_SEND0 - 0.4)
    h.point(TR_SEND0 + 0.1, lambda t: P(*tr_xy(t, 24 * smooth(rng(t, TR_SEND0 - 0.1, TR_HEAR + 0.2)),
                                           smooth(rng(t, TR_SEND0 - 0.1, TR_HEAR + 0.2)))), TR_HEAR + 0.6, gaze_lead=0.0)
    h.point(TR_REPLY0 + 0.3, lambda t: P(*tr_xy(t, 24 + 24 * smooth(rng(t, TR_REPLY0 + 0.2, TR_HOME)),
                                            1 - smooth(rng(t, TR_REPLY0 + 0.2, TR_HOME)))), TR_HOME + 0.4, gaze_lead=0.0)
    h.point(TR_BIG + 0.2, lambda t: P(tr_xy(t, 24, 0)[0], tr_xy(t, 24, 0)[1] + 90), TR_BIG + 2.4)
    h.walk(TR_LOOP + 0.2, 90)
    h.point(TR_LOOP + 2.0, lambda t: P(*tr_xy(t, 72, 1)), e - 0.4)
    # distance: follows the light pulse, then faces the viewer for the conversation line
    s0, e = S['dist'], end_of('dist')
    h.gaze(s0 + 0.2, ('s', P(*SUN)), look=0.5)
    h.point(DI_MILES - 0.1, lambda t: P(*_di_pulse(t)), DI_LDAY + 1.2, gaze_lead=0.0)
    h.point(DI_MARK + 0.3, P(SUN[0] + AU_VOY * di_scale(DI_MARK + 0.3) * 0.2, SUN[1] + 180), DI_CONV - 0.2)
    h.gaze(DI_CONV + 0.2, None, look=-0.9)
    h.brow(DI_CONV + 0.5, 0.5, 1.2)
    # power: watches the budget, points at the three swaps, then at the warning
    s0, e = S['power'], end_of('power')
    h.gaze(s0 + 0.2, ('s', P(x + 200, y + 250)), look=0.6)
    h.point(PW_OFF - 0.1, seq([(0, P(x + 560, y + 120)), (PW_ON, P(x + 820, y + 240)), (PW_TOG, P(x + 935, y + 420))]),
            PW_HEAT + 1.0)
    h.point(PW_ROOM, P(x + 200, y + 490), PW_WITHOUT - 0.3)
    h.point(PW_WITHOUT + 0.2, P(x + 690, y + hh - 75), e - 0.4)
    # history: small, watches the trajectory; points at the speck
    s0, e = S['hist'], end_of('hist')
    h.gaze(s0 + 0.2, ('s', P(x + w * 0.5, y + hh * 0.5)), look=0.7)
    h.point(HI_SPECK - 0.3, P(x + w * 0.55, y + hh * 0.5), HI_HOURS + 2.0)
    h.brow(HI_SPECK + 0.2, 0.6, 1.2)
    # heliopause
    s0, e = S['helio'], end_of('helio')
    h.gaze(s0 + 0.2, ('s', P(x + w * 0.5, y + hh * 0.4)), look=0.7)
    h.point(HE_CROSS, P(x + w * 0.5, y + 70), HE_SAMPLE + 1.0)
    # finale on the cover framing: the hand follows the pulse out and back
    h.point(FI_H0 - 0.3, lambda t: (min(fin_pulse(t)[0] - 30, 980.0), 640.0), FI_H48 + 1.0, gaze_lead=0.0)
    h.brow(FI_H48 + 0.3, 0.7, 1.4)
    h.gaze(FI_REM, None, look=-0.9)
    h.brow(FI_LINE, 0.5, 1.6)
    h.auto(emphasis=('day', 'nothing', 'twice', 'own', 'sky', 'signal', 'clue', 'offline', 'automatically', 'alone',
                     'light-day', 'watt', 'warm', 'jupiter', 'earth', 'heliopause', 'remarkable', 'line'))
    return h


def _di_pulse(t):
    k = di_scale(t)
    sx, sy = SUN
    ex, ey = sx + k, sy
    vx, vy = sx + AU_VOY * k * math.cos(VOY_ANG), sy + AU_VOY * k * math.sin(VOY_ANG)
    u = clamp(rng(t, DI_MILES - 0.3, DI_LDAY + 0.8))
    return lerp(ex, vx, u), lerp(ey, vy, u)


def _dsn_host(h, x, y, w, hh):
    s0, e = S['dsn'], end_of('dsn')
    h.gaze(s0 + 0.3, ('s', P(x + w * 0.47, y + hh * 0.7)), look=0.7)
    h.point(D_PATCH - 0.3, P(*SKY), D_NO + 0.4)
    h.brow(D_NO + 0.6, -0.5, 1.2)
    h.gaze(D_NO + 0.9, None, look=-0.8)
    if not PILOT:
        h.gaze(D_AGAIN - 0.2, ('s', P(*SKY)), look=0.6)
        h.brow(D_STILL + 0.1, -0.6, 1.0)
        h.point(D_RE - 0.2, P(*SKY), e - 0.5)
        h.brow(D_RE + 0.3, 0.9, 1.4)


# ------------------------------------------------------------------ sound: score sections + accents
MUSIC = [(0.0, 0.55), (3.0, 0.7), (7.0, 0.75), (12.6, 0.3), (16.5, 0.45), (20.2, 0.85), (22.5, 0.5), (29.3, 0.25),
         (31.5, 0.3), (35.5, 0.85), (38.4, 0.5), (43.0, 0.6), (51.5, 0.35), (56.0, 0.5), (62.0, 0.65), (77.5, 0.85),
         (87.0, 0.5), (92.5, 0.8), (99.0, 0.4), (103.0, 0.5), (111.0, 0.65), (124.0, 0.8), (126.5, 0.35), (134.0, 0.75),
         (139.5, 0.45), (151.0, 0.7), (158.0, 0.85), (161.0, 0.5), (166.0, 0.7), (174.5, 0.9), (182.0, 0.7), (190.0, 0.3)]
SFX = [(P0, 'send', -16), (S['away'] - 0.35, 'whoosh', -20), (A_ARRIVE, 'arrive', -17), (S['map'] - 0.3, 'whoosh', -22),
       (R0 + 0.3, 'send', -19), (R1, 'arrive', -18), (L_LISTEN + 0.2, 'stamp', -15), (L_TWICE + 0.25, 'stamp', -15),
       (L_NOTHING - 0.2, 'lost', -20), (B_SIG - 0.1, 'back', -16), (B_BACK + 0.05, 'hit', -14),
       (S['dsn'] - 0.3, 'whoosh', -21), (D_POINT, 'send', -21), (c('detect a signal') - 0.05, 'stamp', -15)]
if not PILOT:
    SFX += [(D_AGAIN - 0.3, 'send', -21), (D_STILL - 0.05, 'stamp', -15), (D_RE, 'back', -15), (D_RE + 0.3, 'hit', -15),
            (S['thr'] - 0.3, 'whoosh', -21), (T_CLUE, 'tick', -18), (T_OFF + 0.6, 'stamp', -16), (T_BACKUP + 0.2, 'arrive', -19),
            (T_WHY, 'lost', -24), (S['trip'] - 0.3, 'whoosh', -21), (TR_SEND0, 'send', -19), (TR_HEAR + 0.2, 'arrive', -18),
            (TR_REPLY0 + 0.2, 'send', -19), (TR_HOME, 'arrive', -18), (TR_BIG, 'hit', -14), (TR_LOOP, 'send', -20),
            (S['dist'] - 0.3, 'whoosh', -21), (DI_LDAY + 0.6, 'hit', -15), (S['power'] - 0.3, 'whoosh', -21),
            (PW_TOG, 'stamp', -15), (PW_ROOM, 'arrive', -19), (PW_WITHOUT, 'lost', -23), (S['hist'] - 0.3, 'whoosh', -21),
            (HI_SPECK, 'arrive', -18), (S['helio'] - 0.3, 'whoosh', -21), (HE_CROSS + 0.2, 'hit', -15),
            (S['fin'] - 0.3, 'whoosh', -20), (FI_H0, 'send', -17), (FI_H24 + 0.2, 'arrive', -17), (FI_H48 + 0.3, 'back', -15),
            (FI_LINE, 'hit', -16)]
