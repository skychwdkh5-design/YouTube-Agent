"""EP015 shared pieces: narration cues, the catch set (tower + ship in one camera), UI helpers."""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'engine'))
from cues import Cues                                   # noqa: E402
from art import *                                       # noqa: E402,F401

VOICE_DIR = '/mnt/project-files/starship/EP015/voice_timed'
VOICE_WAV = os.path.join(VOICE_DIR, 'narration.wav')
VOICE_JSON = os.path.join(VOICE_DIR, 'narration.voice.json')
C = Cues(VOICE_JSON)
MEDIA = '/mnt/project-files/starship/EP015/media'
FLOOR = 915          # ATLAS floor line (subtitles live below it)


def c(p, after=0.0):
    return C.at(p, after)


def ce(p, after=0.0):
    return C.end(p, after)


# ---------------------------------------------------------------------------- camera
class Cam:
    """world -> screen: s = (w - (cx, cy)) * z + (960, 540)"""

    def __init__(self, cx=960.0, cy=540.0, z=1.0, shake=0.0, t=0.0):
        sx = shake * (math.sin(t * 31.0) + 0.6 * math.sin(t * 57.0))
        sy = shake * (math.cos(t * 27.0) + 0.5 * math.sin(t * 49.0))
        self.cx, self.cy, self.z = cx + sx, cy + sy, z

    def p(self, x, y):
        return ((x - self.cx) * self.z + 960, (y - self.cy) * self.z + 540)

    def s(self, v):
        return v * self.z


def cam_lerp(a, b, u):
    return Cam(lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u))


# ---------------------------------------------------------------------------- the catch set
TX, GROUND, TOP, ARMY, ARML, TW = 1000.0, 880.0, 130.0, 470.0, 470.0, 92.0
SHIP_H = 300.0
SHIP_BASE = 640           # sprite build height (scaled per frame)


def ship_catch_xy(open_=1.0):
    """world centre of the ship when its pins sit on the arms"""
    spr, m = ship_sprite(SHIP_BASE)
    k = SHIP_H / m['h']
    x = TX + TW / 2 + ARML * 0.9
    y = ARMY - m['pin_y'] * k + SHIP_H / 2 + 4
    return x, y


def ground_band(cv, horizon_y, kind='night', t=0.0, lights=1.0):
    """distant Starbase horizon placed at screen y (ground below it)."""
    g = starbase_ground(kind, 540)
    dy = horizon_y - 540
    cv.over(g, 0, dy)
    if dy < 0:
        bottom = int(H + dy)
        col = g[-1, W // 2, :3]
        cv.fill(tuple(col), 1.0, (0, max(0, bottom), W, H))
    if lights > 0:
        ground_lights(cv, horizon_y, t, lights)


def catch_set(cv, t, cam, ship=(None, None), ang=0.0, open_=1.0, plume_k=0.0, light=0.0, kind='night',
              heat=0.0, steam=0.0, show_ship=True, stars=0.7, plume_len=2.0):
    """night/dusk Starbase with the tower; ship centre in world coords (None -> caught position)."""
    cv.a[:] = sky(kind)
    if stars > 0:
        cv.a += starfield() * stars * (1 if kind == 'night' else 0.35)
    hy = cam.p(0, GROUND)[1]
    ground_band(cv, hy, kind, t, 1.0)
    z = cam.z
    tx, gy = cam.p(TX, GROUND)
    _, ty = cam.p(TX, TOP)
    _, ay = cam.p(TX, ARMY)
    # flood-light glow at the tower
    cv.glow(tx + TW * z * 0.6, ay, 260 * z, (255, 190, 120), 0.18 + 0.4 * light)
    v = Vec()
    tower(v, tx, gy, ty, ay, open_=open_, light=light, arm_len=ARML * z, w=TW * z, front=False, scale=z)
    v.onto(cv)
    sx, sy = ship
    if sx is None:
        sx, sy = ship_catch_xy(open_)
    px, py = cam.p(sx, sy)
    spr, m = ship_sprite(SHIP_BASE, round(heat, 1))
    k = SHIP_H / m['h'] * z
    if show_ship:
        if plume_k > 0:
            exhaust(cv, m, px, py, ang, k, t, plume_k, plume_len, ground_y=gy)
        dim = 0.55 + 0.45 * (1 if kind != 'night' else 0.6)
        sp = spr.copy()
        sp[..., :3] *= dim
        # warm under-light from the plume / tower floods
        if plume_k > 0 or light > 0:
            h = sp.shape[0]
            ramp = np.linspace(0, 1, h)[:, None, None] ** 2
            sp[..., :3] += ramp * np.array([90, 50, 20], np.float32) * (0.6 * plume_k + 0.3 * light)
        draw_vehicle(cv, sp, m, px, py, ang, k)
    if steam > 0:
        r = np.random.default_rng(4)
        for i in range(14):
            ox = r.uniform(-1, 1) * 160 * z
            rise = (t * (20 + r.random() * 30)) % 200
            cv.glow(px + ox, gy - 60 * z - rise * z * 0.6, (90 + r.random() * 140) * z, (150, 146, 144), 0.045 * steam, 1.3)
    v = Vec()
    tower(v, tx, gy, ty, ay, open_=open_, light=light, arm_len=ARML * z, w=TW * z, back=False, scale=z)
    v.onto(cv)
    return (px, py), k, m


# ---------------------------------------------------------------------------- frames / panels
def panel(cv, v, x, y, w, h, a=1.0, col=(255, 255, 255)):
    v.rect(x, y, w, h, None, col + (110,), 2, a=a, r=10)


def sub_canvas(fn, w, h):
    """render fn(cv) at full size and return the crop centre w x h (for panels)"""
    cv = Canvas()
    fn(cv)
    x0, y0 = (W - w) // 2, (H - h) // 2
    return cv.a[y0:y0 + h, x0:x0 + w]


def place_rgb(cv, rgb, x, y, alpha=1.0):
    h, w = rgb.shape[:2]
    cv.over(np.dstack([rgb, np.full((h, w, 1), 1.0, np.float32)]), x, y, alpha)


def finish_frame(cv):
    cv.a *= grain()
    # gentle vignette
    return cv


@lru_cache(maxsize=1)
def _vig():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
    return (1 - 0.32 * np.clip(d - 0.55, 0, 1) ** 1.4)[..., None]


def vignette(cv):
    cv.a *= _vig()


from functools import lru_cache   # noqa: E402
