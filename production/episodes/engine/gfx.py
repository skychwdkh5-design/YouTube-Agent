"""Editorial motion graphics in Pillow, matching the owner's motion.js reference.

All coordinates are in the reference's 1280x720 design space and are scaled to
1920x1080 (x1.5). Vector marks are drawn on a 2x supersampled layer for clean edges.
"""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
K = 1.5            # design (1280x720) -> output
SS = 2             # supersampling of the vector layer
PAL = {'ice': (164, 232, 255), 'paper': (247, 241, 229), 'red': (255, 96, 72), 'lime': (198, 255, 105),
       'amber': (255, 179, 100), 'rose': (255, 158, 133), 'coral': (255, 128, 105)}
FONT = {'sans': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        'sans_r': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        'mono': '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
        'mono_r': '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'}


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def rng(t, a, b):
    return smooth((t - a) / (b - a)) if b > a else float(t >= a)


def lerp(a, b, u):
    return a + (b - a) * u


def hexc(s):
    s = s.lstrip('#')
    if len(s) in (3, 4):
        s = ''.join(c * 2 for c in s)
    v = tuple(int(s[i:i + 2], 16) for i in range(0, len(s), 2))
    return v if len(v) == 4 else v + (255,)


def rgba(c, a=1.0):
    if isinstance(c, str):
        c = hexc(c)
    if len(c) == 3:
        c = tuple(c) + (255,)
    return (int(c[0]), int(c[1]), int(c[2]), int(round(c[3] * a)))


@lru_cache(maxsize=None)
def font(kind, px):
    return ImageFont.truetype(FONT[kind], int(round(px)))


def rand(i):
    x = math.sin(i * 117.83 + 23.98) * 43758.54
    return x - math.floor(x)


@lru_cache(maxsize=64)
def _load(path):
    return Image.open(path).convert('RGB')


@lru_cache(maxsize=16)
def _radial(r, col, inner=0.19):
    """Glow sprite like the reference: alpha bb at 0, 55 at 19%, 0 at r."""
    n = int(r * 2 + 2)
    yy, xx = np.mgrid[0:n, 0:n]
    d = np.hypot(xx - n / 2, yy - n / 2) / r
    a = np.where(d < inner, lerp(0xbb, 0x55, d / inner), 0x55 * np.clip(1 - (d - inner) / (1 - inner), 0, 1)) / 255
    a = np.clip(a, 0, 1)
    arr = np.dstack([np.full((n, n), c, np.float32) for c in col[:3]] + [a * 255])
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


class Frame:
    """One output frame: a 1x RGB base for photos/gradients and a 2x vector layer on top."""

    def __init__(self, base=None):
        self.img = base.copy() if base is not None else Image.new('RGB', (W, H), (0, 0, 0))
        self.v = None
        self.stack = []

    # ------------------------------------------------------------------ raster (1x)
    def background(self, a='#090e1c', b='#03060d'):
        self.img = Image.fromarray(_diag_grad(hexc(a)[:3], hexc(b)[:3]))

    def image(self, path, x=0, y=0, w=1280, h=720, zoom=1.0, fx=0.5, fy=0.5, alpha=1.0, frame=None):
        """Cover-crop like motion.js image(). frame: an already loaded PIL image (video frame)."""
        im = frame if frame is not None else _load(path)
        iw, ih = im.size
        sw = min(iw, ih * w / h) / zoom
        sh = sw * h / w
        box = ((iw - sw) * fx, (ih - sh) * fy, (iw - sw) * fx + sw, (ih - sh) * fy + sh)
        out = im.resize((int(round(w * K)), int(round(h * K))), Image.BICUBIC, box=box)
        self.paste(out, x, y, alpha)

    def paste(self, im, x, y, alpha=1.0):
        self._flush()
        X, Y = int(round(x * K)), int(round(y * K))
        if alpha >= 0.999 and im.mode == 'RGB':
            self.img.paste(im, (X, Y))
        else:
            im = im.convert('RGBA')
            if alpha < 0.999:
                a = np.asarray(im)[..., 3].astype(np.float32) * alpha
                im.putalpha(Image.fromarray(a.astype(np.uint8)))
            base = self.img.convert('RGBA')
            base.alpha_composite(im, (max(0, X), max(0, Y)) if X >= 0 and Y >= 0 else (0, 0),
                                 (0, 0) if X >= 0 and Y >= 0 else (max(0, -X), max(0, -Y)))
            self.img = base.convert('RGB')

    def shade(self, stops, x0=0, y0=0, x1=1280, y1=0):
        """Linear gradient overlay (list of (pos, '#rrggbbaa'))."""
        self._flush()
        arr = _lin_grad(tuple((p, hexc(c)) for p, c in stops), x0 * K, y0 * K, x1 * K, y1 * K)
        base = self.img.convert('RGBA')
        base.alpha_composite(Image.fromarray(arr, 'RGBA'))
        self.img = base.convert('RGB')

    def vignette(self, a=0x99):
        self._flush()
        base = self.img.convert('RGBA')
        base.alpha_composite(_vignette(a))
        self.img = base.convert('RGB')

    def glow(self, x, y, r, col, alpha=1.0):
        sp = _radial(int(r * K), tuple(hexc(col)[:3]) if isinstance(col, str) else tuple(col[:3]))
        if alpha < 0.999:
            sp = sp.copy()
            sp.putalpha(Image.fromarray((np.asarray(sp)[..., 3] * alpha).astype(np.uint8)))
        n = sp.size[0]
        self._flush()
        base = self.img.convert('RGBA')
        X, Y = int(x * K - n / 2), int(y * K - n / 2)
        base.alpha_composite(sp, (max(0, X), max(0, Y)), (max(0, -X), max(0, -Y)))
        self.img = base.convert('RGB')

    # ------------------------------------------------------------------ vector (2x)
    def _d(self):
        if self.v is None:
            self.v = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
        return ImageDraw.Draw(self.v)

    def group(self, alpha):
        """Start a faded group (like ctx.globalAlpha)."""
        self._flush()
        self.stack.append(alpha)

    def end(self):
        a = self.stack.pop()
        self._flush(a)

    def _flush(self, alpha=1.0):
        if self.v is None:
            return
        v = self.v.resize((W, H), Image.BOX)
        if alpha < 0.999:
            v.putalpha(Image.fromarray((np.asarray(v)[..., 3] * alpha).astype(np.uint8)))
        base = self.img.convert('RGBA')
        base.alpha_composite(v)
        self.img = base.convert('RGB')
        self.v = None

    def _p(self, x, y):
        return (x * K * SS, y * K * SS)

    def text(self, s, x, y, n=28, color='paper', kind='sans', align='left', alpha=1.0, spacing=0):
        d = self._d()
        f = font(kind, n * K * SS)
        col = rgba(PAL.get(color, color) if isinstance(color, str) else color, alpha)
        anchor = {'left': 'ls', 'center': 'ms', 'right': 'rs'}[align]
        if spacing:
            # letter-spaced text (manual)
            widths = [d.textlength(ch, font=f) + spacing * K * SS for ch in s]
            total = sum(widths)
            X = x * K * SS - (total / 2 if align == 'center' else total if align == 'right' else 0)
            for ch, w_ in zip(s, widths):
                d.text((X, y * K * SS), ch, font=f, fill=col, anchor='ls')
                X += w_
            return
        d.text(self._p(x, y), s, font=f, fill=col, anchor=anchor)

    def text_w(self, s, n, kind='sans'):
        return font(kind, n * K * SS).getlength(s) / (K * SS)

    def line(self, pts, color, w=2, dash=None, alpha=1.0):
        d = self._d()
        col = rgba(PAL.get(color, color) if isinstance(color, str) else color, alpha)
        P = [self._p(*p) for p in pts]
        ww = max(1, int(round(w * K * SS)))
        if not dash:
            d.line(P, fill=col, width=ww, joint='curve')
            for p in (P[0], P[-1]):
                r = ww / 2
                d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)
            return
        on, off = dash[0] * K * SS, dash[1] * K * SS
        for (x0, y0), (x1, y1) in zip(P, P[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            s = 0.0
            while s < L:
                e = min(L, s + on)
                d.line([(x0 + (x1 - x0) * s / L, y0 + (y1 - y0) * s / L), (x0 + (x1 - x0) * e / L, y0 + (y1 - y0) * e / L)],
                       fill=col, width=ww)
                s += on + off

    def circle(self, x, y, r, fill=None, stroke=None, w=1, alpha=1.0):
        d = self._d()
        X, Y = self._p(x, y)
        R = r * K * SS
        f = rgba(PAL.get(fill, fill) if isinstance(fill, str) else fill, alpha) if fill else None
        o = rgba(PAL.get(stroke, stroke) if isinstance(stroke, str) else stroke, alpha) if stroke else None
        d.ellipse([X - R, Y - R, X + R, Y + R], fill=f, outline=o, width=max(1, int(round(w * K * SS))) if o else 0)

    def arc(self, x, y, r, a0, a1, color, w=2, alpha=1.0):
        d = self._d()
        X, Y = self._p(x, y)
        R = r * K * SS
        d.arc([X - R, Y - R, X + R, Y + R], a0, a1, fill=rgba(PAL.get(color, color) if isinstance(color, str) else color, alpha),
              width=max(1, int(round(w * K * SS))))

    def rect(self, x, y, w, h, fill=None, stroke=None, sw=1, alpha=1.0, radius=0):
        d = self._d()
        X0, Y0 = self._p(x, y)
        X1, Y1 = self._p(x + w, y + h)
        f = rgba(fill if not isinstance(fill, str) else hexc(fill), alpha) if fill else None
        o = rgba(stroke if not isinstance(stroke, str) else hexc(stroke), alpha) if stroke else None
        if radius:
            d.rounded_rectangle([X0, Y0, X1, Y1], radius * K * SS, fill=f, outline=o, width=max(1, int(sw * K * SS)) if o else 0)
        else:
            d.rectangle([X0, Y0, X1, Y1], fill=f, outline=o, width=max(1, int(sw * K * SS)) if o else 0)

    def poly(self, pts, fill=None, stroke=None, w=1, alpha=1.0):
        d = self._d()
        P = [self._p(*p) for p in pts]
        f = rgba(fill if not isinstance(fill, str) else hexc(fill), alpha) if fill else None
        d.polygon(P, fill=f)
        if stroke:
            self.line(P and pts + [pts[0]], stroke, w, alpha=alpha)

    # ------------------------------------------------------------------ editorial pieces
    def grid(self, s=48, col='#a4e8ff13', drift=0.0):
        c = hexc(col)
        x = drift % s
        while x < 1280:
            self.line([(x, 0), (x, 720)], c, 1)
            x += s
        y = 0
        while y < 720:
            self.line([(0, y), (1280, y)], c, 1)
            y += s

    def starfield(self, t=0.0, n=100):
        for i in range(n):
            x = (rand(i) * 1280 + t * (5 + rand(i + 100) * 12)) % 1280
            y = rand(i + 200) * 720
            self.circle(x, y, 0.4 + rand(i + 300) * 1.35, (193, 226, 255, int(255 * (0.17 + rand(i + 400) * 0.6))))

    def footer(self, label, credit='', accent='ice'):
        self.line([(54, 657), (1226, 657)], (217, 239, 255, 50), 1)
        self.text(label, 54, 684, 15, accent, 'mono')
        if credit:
            self.text(credit, 1226, 684, 15, (217, 225, 230), 'mono_r', 'right')

    def kick(self, s, x=55, y=65, color='ice'):
        self.text(s, x, y, 18, color, 'mono')

    def big(self, s, x, y, n=100, color='paper', align='left'):
        self.text(s, x, y, n, color, 'sans', align)

    def pill(self, s, x, y, color='paper', n=16):
        w = self.text_w(s, n, 'mono') + 24
        c = PAL.get(color, color) if isinstance(color, str) else color
        self.rect(x, y - 24, w, 31, (8, 10, 13, 232), tuple(c[:3]) + (85,))
        self.text(s, x + 12, y - 3, n, color, 'mono')
        return w

    def done(self):
        self._flush()
        return self.img


# ---------------------------------------------------------------------- cached rasters
@lru_cache(maxsize=32)
def _diag_grad(a, b):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u = (xx * W + yy * H) / (W * W + H * H)
    u = np.clip(u, 0, 1)[..., None]
    arr = np.array(a, np.float32) * (1 - u) + np.array(b, np.float32) * u
    return arr.astype(np.uint8)


@lru_cache(maxsize=64)
def _lin_grad(stops, x0, y0, x1, y1):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    u = np.clip(((xx - x0) * dx + (yy - y0) * dy) / L2, 0, 1)
    ps = np.array([s[0] for s in stops], np.float32)
    cols = np.array([s[1] for s in stops], np.float32)
    out = np.zeros((H, W, 4), np.float32)
    for c in range(4):
        out[..., c] = np.interp(u, ps, cols[:, c])
    return out.astype(np.uint8)


@lru_cache(maxsize=4)
def _vignette(a):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - 640 * K, yy - 355 * K)
    u = np.clip((d - 245 * K) / ((735 - 245) * K), 0, 1)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., 3] = (u * a).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


class Video:
    """Frame access for a short source clip (decoded once to memory at 1920 width)."""
    _cache = {}

    def __init__(self, path):
        self.path = path
        if path not in Video._cache:
            import subprocess
            probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                    'stream=width,height,r_frame_rate', '-of', 'csv=p=0', path],
                                   capture_output=True, text=True).stdout.strip().split(',')
            w, h = int(probe[0]), int(probe[1])
            num, den = map(int, probe[2].split('/'))
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                 capture_output=True).stdout
            n = len(raw) // (w * h * 3)
            Video._cache[path] = (np.frombuffer(raw, np.uint8)[:n * w * h * 3].reshape(n, h, w, 3), num / den)
        self.frames, self.fps = Video._cache[path]

    def at(self, ts):
        i = int(clamp(ts * self.fps, 0, len(self.frames) - 1))
        return Image.fromarray(self.frames[i])

    @property
    def duration(self):
        return len(self.frames) / self.fps
