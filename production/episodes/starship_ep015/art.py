"""EP015 original 2.5D art: Starship (Ship + Super Heavy), the catch tower with its two arms,
Starbase night/dusk environment, engine plumes, plasma and painted grain.

Everything is drawn here from geometry (numpy + PIL); nothing is traced from SpaceX media.
Proportions follow public dimensions (Ship ~50 m tall, Super Heavy ~71 m, both ~9 m wide);
this is an ILLUSTRATION, not flight footage, and the episode labels it that way.

All functions work in output pixels (1920x1080)."""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_R = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_M = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'

STEEL = np.array([196, 202, 208], np.float32)
TILE = np.array([30, 32, 38], np.float32)
AMBER = (255, 170, 70)
HOT = (255, 214, 140)
ICE = (150, 210, 255)
CREAM = (246, 232, 206)
YELLOW = (255, 214, 64)
RED = (255, 86, 60)
CYAN = (110, 210, 235)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def mjerk(x):
    """minimum-jerk ease 10t^3 - 15t^4 + 6t^5"""
    x = clamp(x)
    return x * x * x * (10 - 15 * x + 6 * x * x)


def rng(t, a, b):
    return mjerk((t - a) / (b - a)) if b > a else float(t >= a)


def lerp(a, b, u):
    return a + (b - a) * u


@lru_cache(maxsize=None)
def font(kind, px):
    return ImageFont.truetype({'b': FONT_B, 'r': FONT_R, 'm': FONT_M}[kind], int(px))


# ---------------------------------------------------------------------------- noise / texture
@lru_cache(maxsize=None)
def vnoise(w, h, cell, seed):
    """smooth value noise 0..1 (bicubic upsampled random grid)"""
    r = np.random.default_rng(seed)
    gw, gh = max(2, w // cell + 3), max(2, h // cell + 3)
    g = (r.random((gh, gw)) * 255).astype(np.uint8)
    im = Image.fromarray(g).resize((gw * cell, gh * cell), Image.BICUBIC)
    return np.asarray(im, np.float32)[:h, :w] / 255.0


@lru_cache(maxsize=1)
def grain():
    """painted canvas grain (multiplier around 1.0) - gives the flat gradients a brushed feel"""
    a = vnoise(W, H, 3, 11) - 0.5
    b = vnoise(W, H, 40, 12) - 0.5
    c = vnoise(W, H, 160, 13) - 0.5
    return (1 + 0.045 * a + 0.05 * b + 0.04 * c)[..., None].astype(np.float32)


# ---------------------------------------------------------------------------- canvas
class Canvas:
    """float32 RGB canvas 0..255 with paste / additive light helpers"""

    def __init__(self, arr=None):
        self.a = np.zeros((H, W, 3), np.float32) if arr is None else arr.astype(np.float32).copy()

    def _clip(self, x, y, h, w):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        if x1 <= x0 or y1 <= y0:
            return None
        return x0, y0, x1, y1, x0 - x, y0 - y

    def over(self, rgba, x, y, alpha=1.0):
        """straight-alpha RGBA float (0..255 rgb, 0..1 a) over the canvas at top-left x,y"""
        x, y = int(round(x)), int(round(y))
        h, w = rgba.shape[:2]
        c = self._clip(x, y, h, w)
        if c is None or alpha <= 0.003:
            return
        x0, y0, x1, y1, ox, oy = c
        s = rgba[oy:oy + y1 - y0, ox:ox + x1 - x0]
        a = s[..., 3:4] * alpha
        reg = self.a[y0:y1, x0:x1]
        reg *= (1 - a)
        reg += s[..., :3] * a

    def add(self, rgb, x, y, k=1.0):
        """additive light (rgb float 0..255 array) at top-left x,y"""
        x, y = int(round(x)), int(round(y))
        h, w = rgb.shape[:2]
        c = self._clip(x, y, h, w)
        if c is None or k <= 0.003:
            return
        x0, y0, x1, y1, ox, oy = c
        self.a[y0:y1, x0:x1] += rgb[oy:oy + y1 - y0, ox:ox + x1 - x0, :3] * k

    def glow(self, x, y, r, col, k=1.0, power=2.0):
        g = _glow(int(max(4, round(r / 6) * 6)), tuple(int(v) for v in col), power)
        self.add(g, x - g.shape[1] / 2, y - g.shape[0] / 2, k)

    def pil(self, im, x=0, y=0, alpha=1.0):
        """paste a PIL RGBA image"""
        a = np.asarray(im.convert('RGBA'), np.float32)
        a[..., 3] /= 255.0
        self.over(a, x, y, alpha)

    def fill(self, col, alpha=1.0, box=None):
        x0, y0, x1, y1 = box or (0, 0, W, H)
        reg = self.a[y0:y1, x0:x1]
        reg *= (1 - alpha)
        reg += np.array(col, np.float32) * alpha

    def image(self):
        return Image.fromarray(np.clip(self.a, 0, 255).astype(np.uint8), 'RGB')


@lru_cache(maxsize=512)
def _glow(r, col, power):
    n = 2 * r + 1
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.hypot(xx - r, yy - r) / r
    f = np.clip(1 - d, 0, 1) ** power
    return f[..., None] * np.array(col, np.float32)[None, None]


def to_rgba(im):
    a = np.asarray(im.convert('RGBA'), np.float32)
    a[..., 3] /= 255.0
    return a


# ---------------------------------------------------------------------------- vector overlay (2x supersampled)
class Vec:
    """Anti-aliased vector/text layer: draw at 2x, composite onto a Canvas."""
    SS = 2

    def __init__(self):
        self.im = Image.new('RGBA', (W * self.SS, H * self.SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.used = False

    def _p(self, pts):
        return [(x * self.SS, y * self.SS) for x, y in pts]

    @staticmethod
    def c(col, a=1.0):
        col = tuple(int(v) for v in col)
        base = col[3] if len(col) == 4 else 255
        return col[:3] + (int(base * clamp(a)),)

    def line(self, pts, col, w=3, a=1.0, dash=None):
        if a <= 0.003 or len(pts) < 2:
            return
        self.used = True
        P = self._p(pts)
        ww = max(1, int(round(w * self.SS)))
        if dash:
            on, off = dash[0] * self.SS, dash[1] * self.SS
            carry = 0.0
            for (x0, y0), (x1, y1) in zip(P, P[1:]):
                L = math.hypot(x1 - x0, y1 - y0)
                s = carry
                while s < L:
                    e = min(L, s + on)
                    self.d.line([(x0 + (x1 - x0) * s / L, y0 + (y1 - y0) * s / L),
                                 (x0 + (x1 - x0) * e / L, y0 + (y1 - y0) * e / L)], fill=self.c(col, a), width=ww)
                    s += on + off
                carry = s - L
            return
        self.d.line(P, fill=self.c(col, a), width=ww, joint='curve')
        r = ww / 2
        for p in (P[0], P[-1]):
            self.d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=self.c(col, a))

    def poly(self, pts, fill, a=1.0, outline=None, w=2):
        if a <= 0.003:
            return
        self.used = True
        self.d.polygon(self._p(pts), fill=self.c(fill, a) if fill else None)
        if outline:
            self.line(list(pts) + [pts[0]], outline, w, a)

    def circle(self, x, y, r, fill=None, outline=None, w=2, a=1.0):
        if a <= 0.003:
            return
        self.used = True
        S = self.SS
        self.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=self.c(fill, a) if fill else None,
                       outline=self.c(outline, a) if outline else None, width=max(1, int(w * S)) if outline else 0)

    def rect(self, x, y, w, h, fill=None, outline=None, lw=2, a=1.0, r=0):
        if a <= 0.003:
            return
        self.used = True
        S = self.SS
        box = [x * S, y * S, (x + w) * S, (y + h) * S]
        kw = dict(fill=self.c(fill, a) if fill else None, outline=self.c(outline, a) if outline else None,
                  width=max(1, int(lw * S)) if outline else 0)
        if r:
            self.d.rounded_rectangle(box, r * S, **kw)
        else:
            self.d.rectangle(box, **kw)

    def text(self, s, x, y, size, col, kind='b', anchor='ls', a=1.0, stroke=0, stroke_col=(0, 0, 0)):
        if a <= 0.003:
            return
        self.used = True
        S = self.SS
        self.d.text((x * S, y * S), s, font=font(kind, size * S), fill=self.c(col, a), anchor=anchor,
                    stroke_width=int(stroke * S), stroke_fill=self.c(stroke_col, a))

    def tw(self, s, size, kind='b'):
        return font(kind, size * self.SS).getlength(s) / self.SS

    def arc_pts(self, cx, cy, rx, ry, a0, a1, n=80):
        return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                 cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

    def onto(self, cv, alpha=1.0):
        if not self.used:
            return
        bb = self.im.getbbox()
        if not bb:
            return
        S = self.SS
        x0, y0 = (bb[0] // S) * S, (bb[1] // S) * S
        x1, y1 = min(W * S, -(-bb[2] // S) * S), min(H * S, -(-bb[3] // S) * S)
        im = self.im.crop((x0, y0, x1, y1)).resize(((x1 - x0) // S, (y1 - y0) // S), Image.BOX)
        a = np.asarray(im, np.float32)
        a[..., 3] /= 255.0
        cv.over(a, x0 // S, y0 // S, alpha)


def partial(pts, u):
    """first fraction u (0..1) of a polyline, by length"""
    if u >= 1:
        return pts
    if u <= 0:
        return pts[:1]
    L = [0.0]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L.append(L[-1] + math.hypot(x1 - x0, y1 - y0))
    tgt = L[-1] * u
    out = [pts[0]]
    for i in range(1, len(pts)):
        if L[i] >= tgt:
            k = (tgt - L[i - 1]) / max(1e-9, L[i] - L[i - 1])
            out.append((lerp(pts[i - 1][0], pts[i][0], k), lerp(pts[i - 1][1], pts[i][1], k)))
            break
        out.append(pts[i])
    return out


def bez(p0, p1, p2, n=60):
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
             (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]) for u in np.linspace(0, 1, n)]


# ---------------------------------------------------------------------------- environment
@lru_cache(maxsize=16)
def sky(kind):
    """painted sky gradients (cached). kind: night, dusk, dawn, space, high"""
    y = np.linspace(0, 1, H)[:, None]
    stops = {
        'night': [(0, (8, 14, 30)), (0.55, (18, 32, 58)), (0.78, (44, 52, 70)), (1, (40, 36, 40))],
        'dusk': [(0, (14, 22, 46)), (0.45, (46, 56, 92)), (0.7, (150, 96, 82)), (0.8, (232, 150, 86)), (1, (90, 60, 50))],
        'dawn': [(0, (22, 34, 64)), (0.5, (84, 104, 140)), (0.72, (220, 170, 130)), (0.8, (250, 206, 150)), (1, (120, 100, 90))],
        'high': [(0, (4, 6, 16)), (0.5, (16, 30, 70)), (0.8, (52, 96, 160)), (1, (120, 170, 220))],
        'space': [(0, (3, 5, 12)), (1, (8, 12, 26))],
        'studio': [(0, (12, 18, 32)), (0.7, (22, 30, 48)), (1, (14, 18, 28))],
    }[kind]
    ps = [s[0] for s in stops]
    out = np.zeros((H, W, 3), np.float32)
    for c in range(3):
        out[..., c] = np.interp(y, ps, [s[1][c] for s in stops]).repeat(W, 1)
    # broad painted cloud bands
    n = vnoise(W, H, 220, hash(kind) % 997) - 0.5
    m = vnoise(W, H, 60, hash(kind) % 991 + 1) - 0.5
    out *= (1 + 0.10 * n[..., None] + 0.04 * m[..., None])
    return out


@lru_cache(maxsize=8)
def starfield(seed=3, n=900):
    r = np.random.default_rng(seed)
    arr = np.zeros((H, W, 3), np.float32)
    xs, ys = r.integers(0, W, n), r.integers(0, H, n)
    br = r.random(n) ** 3 * 220 + 20
    for x, y, b in zip(xs, ys, br):
        arr[y, x] += b
        if b > 150:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < W and 0 <= y + dy < H:
                    arr[y + dy, x + dx] += b * 0.35
    return arr


@lru_cache(maxsize=8)
def starbase_ground(kind='night', horizon=820):
    """flat Texas coast: ground, distant tank farm / buildings, sea strip with shimmer (RGBA)"""
    im = Image.new('RGBA', (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    hz = horizon * 2
    gcol = {'night': (20, 22, 28), 'dusk': (36, 30, 34), 'dawn': (60, 52, 54)}[kind]
    scol = {'night': (24, 34, 52), 'dusk': (70, 64, 80), 'dawn': (120, 110, 120)}[kind]
    # sea on the right, beyond the beach
    d.rectangle([0, hz - 8, W * 2, hz + 30], fill=scol + (255,))
    d.rectangle([0, hz + 18, W * 2, H * 2], fill=gcol + (255,))
    r = np.random.default_rng(5)
    # low buildings + tank farm silhouettes along the horizon
    sil = tuple(max(0, c - 8) for c in gcol) + (255,)
    x = 40
    while x < W * 2:
        w = r.integers(40, 180)
        h = r.integers(14, 70) if r.random() < 0.7 else r.integers(70, 130)
        if r.random() < 0.25:                          # tank (rounded top)
            d.rounded_rectangle([x, hz + 18 - h, x + w * 0.6, hz + 22], 14, fill=sil)
        else:
            d.rectangle([x, hz + 18 - h, x + w, hz + 22], fill=sil)
        x += w + r.integers(30, 260)
    a = np.asarray(im.resize((W, H), Image.BOX), np.float32)
    a[..., 3] /= 255.0
    # ground texture
    g = vnoise(W, H, 30, 21)[..., None]
    a[..., :3] *= (0.9 + 0.2 * g)
    return a


def ground_lights(cv, horizon, t, k=1.0, seed=8):
    r = np.random.default_rng(seed)
    for i in range(40):
        x = r.uniform(0, W)
        y = horizon + r.uniform(-6, 26)
        tw = 0.75 + 0.25 * math.sin(t * (1 + r.random() * 2) + i)
        col = (255, 200, 140) if r.random() < 0.7 else (200, 220, 255)
        cv.glow(x, y, r.uniform(4, 10), col, 0.9 * k * tw, 1.6)


# ---------------------------------------------------------------------------- vehicles
def _cyl_shade(nx, light=-0.35):
    """cylinder shading for normalised x (-1..1); light from upper left"""
    nz = np.sqrt(np.clip(1 - nx * nx, 0, 1))
    lx = light
    lz = math.sqrt(1 - lx * lx)
    diff = np.clip(nx * lx + nz * lz, 0, 1)
    spec = np.clip(nx * lx + nz * lz, 0, 1) ** 24
    return diff, spec


@lru_cache(maxsize=None)
def ship_sprite(h, heat=0.0, legs=False):
    """Starship upper stage, nose up. Returns (RGBA float array, meta). Width ~ h * 0.18 body.
    heat: 0..1 glow on the windward tiles (re-entry). meta: pivot/engine/pin rows."""
    S = 2
    Hs = int(h * S)
    bw = int(Hs * 0.17 / 2)                      # body half width
    fin = int(bw * 1.25)                         # flap reach
    Ws = 2 * (bw + fin) + 8
    cx = Ws / 2
    yy, xx = np.mgrid[0:Hs, 0:Ws].astype(np.float32)
    nose_h = Hs * 0.20
    body_bot = Hs * 0.965
    # profile: ogive nose then straight barrel
    yn = np.clip(yy / nose_h, 0, 1)
    half = np.where(yy < nose_h, bw * np.sqrt(np.clip(1 - (1 - yn) ** 2.2, 0, 1)), bw)
    inside = (np.abs(xx - cx) <= half) & (yy <= body_bot) & (yy >= 1)
    nx = np.clip((xx - cx) / np.maximum(half, 1), -1, 1)
    diff, spec = _cyl_shade(nx)
    col = STEEL[None, None] * (0.38 + 0.72 * diff[..., None]) + 255 * 0.5 * spec[..., None]
    # weld rings
    ring = (np.abs(((yy - nose_h) / (Hs * 0.052)) % 1 - 0.5) < 0.012) & (yy > nose_h)
    col = np.where(ring[..., None], col * 0.82, col)
    # heat shield: windward (left) half - black hex tiles
    tile_side = nx < -0.08
    hexv = (np.abs(np.sin(xx * 0.9 / S) * np.sin(yy * 0.52 / S + 0.5 * np.sin(xx * 0.45 / S))) < 0.08)
    tcol = TILE[None, None] * (0.7 + 0.5 * diff[..., None]) * np.where(hexv[..., None], 0.7, 1.0)
    if heat > 0:
        glowc = np.array([255, 120, 40], np.float32)
        edge = np.clip((-nx - 0.1) / 0.9, 0, 1) ** 1.5
        tcol = tcol + glowc * heat * edge[..., None] * 1.1
    col = np.where(tile_side[..., None], tcol, col)
    a = inside.astype(np.float32)
    rgba = np.dstack([col, a])
    im = Image.fromarray(np.dstack([np.clip(col, 0, 255), a * 255]).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(im)
    dark = (34, 36, 44, 255)
    edge = (70, 74, 86, 255)
    # forward flaps (small, near nose) - drawn both sides
    fy0, fy1 = nose_h * 0.92, nose_h * 1.55
    for sgn in (-1, 1):
        x0 = cx + sgn * (bw * 0.86)
        pts = [(x0, fy0), (cx + sgn * (bw + fin * 0.55), fy0 + (fy1 - fy0) * 0.35),
               (cx + sgn * (bw + fin * 0.6), fy1), (x0, fy1)]
        d.polygon(pts, fill=dark, outline=edge)
    # aft flaps (large)
    ay0, ay1 = Hs * 0.72, Hs * 0.93
    for sgn in (-1, 1):
        x0 = cx + sgn * (bw * 0.9)
        pts = [(x0, ay0), (cx + sgn * (bw + fin * 0.95), ay0 + (ay1 - ay0) * 0.38),
               (cx + sgn * (bw + fin * 1.0), ay1), (x0, ay1)]
        d.polygon(pts, fill=dark, outline=edge)
    # catch pins (small nubs below the forward flaps)
    py = nose_h * 1.9
    for sgn in (-1, 1):
        d.rectangle([cx + sgn * bw - (0 if sgn > 0 else bw * 0.16), py, cx + sgn * bw + (bw * 0.16 if sgn > 0 else 0), py + bw * 0.14],
                    fill=(150, 156, 166, 255))
    # engine bells
    for k, ex in enumerate((-0.5, 0.0, 0.5)):
        ew = bw * 0.36
        x = cx + ex * bw
        d.polygon([(x - ew * 0.55, body_bot - 2), (x + ew * 0.55, body_bot - 2), (x + ew * 0.75, Hs - 1), (x - ew * 0.75, Hs - 1)],
                  fill=(58, 58, 64, 255), outline=(30, 30, 34, 255))
    im = im.resize((Ws // S, Hs // S), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    a[..., 3] /= 255.0
    meta = dict(w=Ws // S, h=Hs // S, cx=cx / S, engine_y=Hs / S, pin_y=py / S, nose_h=nose_h / S, bw=bw / S)
    return a, meta


@lru_cache(maxsize=None)
def booster_sprite(h):
    """Super Heavy booster, top up (hot-stage ring, grid fins, engine skirt)."""
    S = 2
    Hs = int(h * S)
    bw = int(Hs * 0.125 / 2)
    gf = int(bw * 0.8)
    Ws = 2 * (bw + gf) + 8
    cx = Ws / 2
    yy, xx = np.mgrid[0:Hs, 0:Ws].astype(np.float32)
    inside = (np.abs(xx - cx) <= bw) & (yy <= Hs * 0.975)
    nx = np.clip((xx - cx) / bw, -1, 1)
    diff, spec = _cyl_shade(nx)
    col = STEEL[None, None] * (0.36 + 0.72 * diff[..., None]) + 255 * 0.45 * spec[..., None]
    ring = (np.abs((yy / (Hs * 0.04)) % 1 - 0.5) < 0.012)
    col = np.where(ring[..., None], col * 0.84, col)
    soot = np.clip((yy / Hs - 0.7) / 0.3, 0, 1) ** 1.5
    col = col * (1 - 0.45 * soot[..., None])
    im = Image.fromarray(np.dstack([np.clip(col, 0, 255), inside * 255.0]).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(im)
    # hot-staging ring (vented, dark) at the top
    d.rectangle([cx - bw, 0, cx + bw, Hs * 0.045], fill=(46, 48, 54, 255))
    for k in range(9):
        x = cx - bw + (2 * bw) * (k + 0.5) / 9
        d.rectangle([x - bw * 0.06, Hs * 0.008, x + bw * 0.06, Hs * 0.037], fill=(18, 18, 22, 255))
    # grid fins
    for sgn in (-1, 1):
        gx0 = cx + sgn * bw
        gx1 = cx + sgn * (bw + gf)
        y0, y1 = Hs * 0.07, Hs * 0.125
        d.rectangle([min(gx0, gx1), y0, max(gx0, gx1), y1], fill=(64, 66, 74, 255), outline=(28, 28, 32, 255))
        for k in range(1, 5):
            x = gx0 + (gx1 - gx0) * k / 5
            d.line([(x, y0), (x, y1)], fill=(30, 30, 36, 255), width=2)
        for k in range(1, 3):
            y = y0 + (y1 - y0) * k / 3
            d.line([(gx0, y), (gx1, y)], fill=(30, 30, 36, 255), width=2)
    # engine cluster
    for ex in np.linspace(-0.8, 0.8, 7):
        ew = bw * 0.2
        x = cx + ex * bw
        d.polygon([(x - ew * 0.6, Hs * 0.972), (x + ew * 0.6, Hs * 0.972), (x + ew * 0.8, Hs - 1), (x - ew * 0.8, Hs - 1)],
                  fill=(56, 56, 62, 255))
    im = im.resize((Ws // S, Hs // S), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    a[..., 3] /= 255.0
    return a, dict(w=Ws // S, h=Hs // S, cx=cx / S, bw=bw / S)


def plume(length, width, t, seed=0, k=1.0, cold=False):
    """engine exhaust as an additive light sprite (rgb float), pointing DOWN from the top centre."""
    L, Wd = max(4, int(length)), max(4, int(width))
    yy, xx = np.mgrid[0:L, 0:Wd * 3].astype(np.float32)
    cx = Wd * 1.5
    v = yy / L
    flick = 1 + 0.12 * math.sin(t * 37 + seed) + 0.08 * math.sin(t * 61 + 2 * seed)
    spread = Wd * (0.45 + 1.1 * v) * flick
    d = np.abs(xx - cx) / np.maximum(spread, 1)
    core = np.clip(1 - d, 0, 1) ** 1.6 * (1 - v) ** 1.25
    # turbulence along the plume
    n = vnoise(Wd * 3, L + 64, 18, seed % 7)
    off = int((t * 900) % 64)
    tur = 0.75 + 0.5 * n[off:off + L]
    inten = core * tur * k
    if cold:
        col = np.stack([inten * 170, inten * 210, inten * 255], -1)
    else:
        hot = np.clip(1 - v * 2.2, 0, 1)[..., None]
        col = inten[..., None] * (np.array([255, 150, 60], np.float32) * (1 - hot) + np.array([255, 245, 210], np.float32) * hot)
    return col


def rot_sprite(rgba, angle, scale=1.0):
    """rotate (deg, counter-clockwise on screen) + scale a straight-alpha float sprite.
    returns (array, (ox, oy)) where o = position of the sprite centre in the output."""
    im = Image.fromarray(np.dstack([np.clip(rgba[..., :3], 0, 255), rgba[..., 3:4] * 255]).astype(np.uint8), 'RGBA')
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if abs(angle) > 0.05:
        im = im.rotate(angle, Image.BICUBIC, expand=True)
    a = np.asarray(im, np.float32)
    a[..., 3] /= 255.0
    return a, (im.width / 2, im.height / 2)


def draw_vehicle(cv, spr, meta, x, y, angle=0.0, scale=1.0, alpha=1.0):
    """place a vehicle sprite so that its CENTRE is at (x, y); angle in deg (+ = tilt left/ccw)."""
    a, (ox, oy) = rot_sprite(spr, angle, scale)
    cv.over(a, x - ox, y - oy, alpha)


def body_point(meta, u, x, y, angle, scale):
    """screen point at fraction u along the vehicle axis (0 = nose/top, 1 = engines) for a
    vehicle centred at x, y."""
    L = meta['h'] * scale
    d = (u - 0.5) * L
    th = math.radians(angle)
    return x + math.sin(th) * d, y + math.cos(th) * d


def exhaust(cv, meta, x, y, angle, scale, t, k=1.0, length=2.2, seed=0, cold=False, ground_y=None):
    """plume from the engine end of a vehicle (angle as in draw_vehicle)."""
    if k <= 0.01:
        return
    ex, ey = body_point(meta, 0.985, x, y, angle, scale)
    bw = meta['bw'] * scale
    L = meta['h'] * scale * 0.42 * length
    p = plume(L, bw * 0.9, t, seed, k, cold)
    im = Image.fromarray(np.clip(p, 0, 255).astype(np.uint8), 'RGB')
    if abs(angle) > 0.05:
        im = im.rotate(angle, Image.BILINEAR, expand=True)
    arr = np.asarray(im, np.float32)
    # rotation about the top centre: place so that the plume origin lands on the nozzle
    th = math.radians(angle)
    w0, h0 = p.shape[1], p.shape[0]
    # origin in the rotated (expanded) image
    cxr, cyr = im.width / 2, im.height / 2
    vx, vy = 0, -h0 / 2                              # origin relative to the original centre
    rx = vx * math.cos(th) + vy * math.sin(th)
    ry = -vx * math.sin(th) + vy * math.cos(th)
    cv.add(arr, ex - (cxr + rx), ey - (cyr + ry), 1.0)
    cv.glow(ex, ey + 10, bw * 3.2, (255, 170, 80), 0.55 * k)
    if ground_y is not None:
        cv.glow(ex, ground_y, bw * 9, (255, 150, 70), 0.35 * k, 1.4)


# ---------------------------------------------------------------------------- the tower
def tower(v, x, ground, top, arm_y, open_=1.0, light=0.0, arm_len=430, w=86, front=True, back=True, scale=1.0):
    """Launch-and-catch tower (side 3/4). x: tower centre, ground y, top y. Arms on a carriage at
    arm_y reaching to the right. open_ 0..1: arms apart (1) or closed (0). Draws back arm when
    back=True and front arm when front=True (so a ship can sit between them)."""
    if back:
        # lattice column
        c_dark = (22, 26, 32)
        c_lit = (90, 74, 62)
        x0, x1 = x - w / 2, x + w / 2
        v.poly([(x0, ground), (x0, top), (x1, top), (x1, ground)], c_dark)
        n = int((ground - top) / (w * 0.9))
        for i in range(n + 1):
            y = top + (ground - top) * i / max(1, n)
            v.line([(x0, y), (x1, y)], (48, 54, 64), 2.2 * scale)
            if i < n:
                y2 = top + (ground - top) * (i + 1) / max(1, n)
                v.line([(x0, y), (x1, y2)], (40, 46, 56), 1.8 * scale)
                v.line([(x1, y), (x0, y2)], (40, 46, 56), 1.8 * scale)
        v.line([(x1, top), (x1, ground)], tuple(int(lerp(a, b, light)) for a, b in zip((60, 66, 78), (230, 160, 90))), 3 * scale)
        v.line([(x0, top), (x0, ground)], (52, 58, 70), 3 * scale)
        # crane / lightning mast on top
        v.line([(x, top), (x, top - 80 * scale)], (40, 46, 56), 4 * scale)
        v.circle(x, top - 82 * scale, 4 * scale, (255, 80, 60))
        # carriage
        v.rect(x0 - 10 * scale, arm_y - 46 * scale, w + 20 * scale, 92 * scale, (36, 40, 48), (70, 76, 88), 2)
        _arm(v, x1, arm_y, open_, arm_len, scale, far=True, light=light)
    if front:
        _arm(v, x + w / 2, arm_y, open_, arm_len, scale, far=False, light=light)


def arm_tips(x_edge, arm_y, open_, arm_len, scale=1.0):
    """(far tip, near tip) screen points - used to seat the ship's catch pins."""
    sep = lerp(34, 120, open_) * scale
    return (x_edge + arm_len * scale, arm_y - sep * 0.42), (x_edge + arm_len * scale * 1.04, arm_y + sep * 0.58)


def _arm(v, x_edge, arm_y, open_, arm_len, scale, far, light):
    tfar, tnear = arm_tips(x_edge, arm_y, open_, arm_len, scale)
    tip = tfar if far else tnear
    th = (14 if far else 22) * scale
    root = (x_edge, arm_y - (14 if far else -10) * scale)
    col = (44, 50, 60) if far else (62, 68, 80)
    edge = tuple(int(lerp(a, b, light)) for a, b in zip((96, 104, 118), (240, 176, 104)))
    pts = [(root[0], root[1] - th), (tip[0], tip[1] - th * 0.6), (tip[0], tip[1] + th * 0.6), (root[0], root[1] + th)]
    v.poly(pts, col)
    # truss pattern
    n = 9
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        a = (lerp(root[0], tip[0], u0), lerp(root[1] - th, tip[1] - th * 0.6, u0))
        b = (lerp(root[0], tip[0], u1), lerp(root[1] + th, tip[1] + th * 0.6, u1))
        v.line([a, b], (30, 34, 42), 1.6 * scale)
    v.line([pts[0], pts[1]], edge, 2.4 * scale)
    # catch rail (landing surface for the pins)
    v.line([(lerp(root[0], tip[0], 0.55), lerp(root[1], tip[1], 0.55) - th * 0.75), (tip[0], tip[1] - th * 0.62)],
           (180, 186, 196) if not far else (110, 116, 126), 3 * scale)


# ---------------------------------------------------------------------------- labels
def tag(v, s, x, y, col=(255, 255, 255), size=20, a=1.0, bg=(8, 12, 20, 200)):
    w = v.tw(s, size, 'm')
    v.rect(x - 10, y - size - 6, w + 20, size + 16, bg, None, a=a, r=4)
    v.text(s, x, y + 2, size, col, 'm', a=a)
    return w + 20


def kicker(v, s, a=1.0):
    """small production label (top-left): ILLUSTRATION / SCHEMATIC / NASA SVS ..."""
    w = v.tw(s, 17, 'm')
    v.rect(40, 34, w + 26, 34, (6, 10, 18, 190), (255, 255, 255, 60), 1, a=a, r=4)
    v.text(s, 53, 58, 17, (220, 228, 236), 'm', a=a)


def stamp(v, s, x, y, col, size=64, a=1.0, rot=0.0, box=True):
    """bold stamp text centred at x,y"""
    w = v.tw(s, size, 'b')
    if box:
        v.rect(x - w / 2 - 18, y - size * 0.82, w + 36, size * 1.12, None, col, 5, a=a, r=6)
    v.text(s, x, y + size * 0.12, size, col, 'b', 'ms', a=a)
