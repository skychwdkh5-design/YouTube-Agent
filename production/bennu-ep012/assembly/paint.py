"""EP011 painted 2.5D primitives (Pillow + numpy only).

Procedural painted look for the selected Orbital Atlas style: textured gradients, brush-noise grain,
sculpted conifer sprites with lit/shadow sides, soft glows. Everything here is original, generated in code.
"""
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H, FPS = 1920, 1080, 30
FI = "/usr/share/fonts/opentype/inter/"


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def seg(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def lerp(a, b, u):
    return a + (b - a) * u


def mix(c0, c1, u):
    return tuple(int(round(lerp(a, b, u))) for a, b in zip(c0, c1))


@lru_cache(maxsize=None)
def font(name, size):
    return ImageFont.truetype(FI + name, size)


# ---------------------------------------------------------------- noise / texture
def noise(w, h, cell, seed, aniso=1.0):
    """value noise: random grid upsampled bicubic; aniso>1 stretches horizontally (brush strokes)."""
    rng = np.random.default_rng(seed)
    gw, gh = max(2, int(w / (cell * aniso))), max(2, int(h / cell))
    g = (rng.random((gh, gw)) * 255).astype(np.uint8)
    im = Image.fromarray(g, "L").resize((w, h), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0


def fbm(w, h, seed, cells=(160, 60, 22, 8), weights=(0.45, 0.28, 0.17, 0.10), aniso=1.0):
    out = np.zeros((h, w), np.float32)
    for k, (c, wt) in enumerate(zip(cells, weights)):
        out += wt * noise(w, h, c, seed + 17 * k, aniso)
    return out


def paint_texture(img, seed, amount=0.10, aniso=2.2):
    """modulate an RGB(A) image with brush-like value noise (keeps alpha)."""
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    n = fbm(w, h, seed, cells=(90, 30, 9, 3), weights=(0.35, 0.3, 0.2, 0.15), aniso=aniso) - 0.5
    a[..., :3] *= (1 + amount * 2 * n)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), img.mode)


def vgradient(w, h, stops):
    """vertical gradient; stops = [(pos0..1, (r,g,b)), ...]"""
    y = np.linspace(0, 1, h, dtype=np.float32)
    out = np.zeros((h, 3), np.float32)
    ps = [p for p, _ in stops]
    for ch in range(3):
        out[:, ch] = np.interp(y, ps, [c[ch] for _, c in stops])
    return Image.fromarray(np.repeat(out[:, None, :], w, axis=1).astype(np.uint8), "RGB")


def radial_alpha(size, inner=0.0, power=1.6):
    s = size
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    r = np.hypot(x - s / 2 + 0.5, y - s / 2 + 0.5) / (s / 2)
    a = np.clip(1 - (r - inner) / (1 - inner), 0, 1) ** power
    return a


def glow_sprite(size, color, power=1.6, core=None, seed=0, turb=0.0):
    """soft radial glow RGBA; core=(r,g,b) hot centre; turb adds painted turbulence to the edge."""
    a = radial_alpha(size, 0.0, power)
    if turb:
        a = a * (1 - turb + turb * 2 * fbm(size, size, seed, cells=(size / 6, size / 14, size / 30), weights=(0.5, 0.3, 0.2)))
    rgb = np.zeros((size, size, 3), np.float32)
    rgb[:] = color
    if core is not None:
        k = radial_alpha(size, 0.0, 3.0)[..., None]
        rgb = rgb * (1 - k) + np.array(core, np.float32) * k
    out = np.dstack([rgb, np.clip(a, 0, 1) * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


# ---------------------------------------------------------------- sprites
def tree_sprite(h, seed, base=(22, 54, 44), lit=(196, 140, 82), shade=(10, 26, 26), lit_amt=0.35, stripped=False):
    """painted spruce/larch at 2x then downsampled; base at bottom centre. lit side = right."""
    rng = np.random.default_rng(seed)
    S = 2
    hh = int(h * S); ww = int(h * 0.42 * S) + 8
    im = Image.new("RGBA", (ww, hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = ww / 2
    trunk_w = max(2, int(h * 0.035 * S))
    d.rectangle([cx - trunk_w / 2, hh * 0.12, cx + trunk_w / 2, hh], fill=(60, 40, 30, 255))
    if stripped:
        # bare trunk with a few broken stubs ("telegraph pole" trees)
        for k in range(5):
            y = hh * (0.25 + 0.13 * k)
            L = ww * rng.uniform(0.06, 0.14)
            sgn = -1 if k % 2 else 1
            d.line([(cx, y), (cx + sgn * L, y - L * 0.5)], fill=(70, 48, 34, 255), width=max(1, trunk_w // 2))
    else:
        tiers = rng.integers(7, 10)
        for k in range(tiers):
            u = k / (tiers - 1)
            y_top = hh * (0.02 + 0.70 * u)
            y_bot = y_top + hh * (0.20 + 0.06 * rng.random())
            half = ww * (0.10 + 0.38 * u ** 0.9) * rng.uniform(0.85, 1.1)
            jag = [(cx, y_top)]
            n = 5
            for j in range(n + 1):  # right side jagged
                v = j / n
                jag.append((cx + half * v * rng.uniform(0.8, 1.05), y_top + (y_bot - y_top) * v + rng.uniform(-3, 3) * S))
            for j in range(n, -1, -1):
                v = j / n
                jag.append((cx - half * v * rng.uniform(0.8, 1.05), y_top + (y_bot - y_top) * v + rng.uniform(-3, 3) * S))
            col = mix(base, shade, 0.25 * (1 - u))
            d.polygon(jag, fill=col + (255,))
    # sculpted light: warm rim on the right, cool shadow on the left, darker toward the trunk
    a = np.asarray(im).astype(np.float32)
    xs = np.linspace(-1, 1, ww, dtype=np.float32)[None, :]
    k = np.clip((xs + 0.15) * 1.4, 0, 1) ** 1.5 * lit_amt * 1.6
    rgb = a[..., :3] * (1 - k[..., None]) + np.array(lit, np.float32) * k[..., None] * 0.75 + a[..., :3] * k[..., None] * 0.25
    rgb *= (0.78 + 0.22 * np.clip(xs + 1, 0, 1))[..., None]
    a[..., :3] = rgb
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    im = im.resize((ww // S, hh // S), Image.LANCZOS)
    return paint_texture(im, seed + 5, 0.16, 1.0)


def stamp(canvas, spr, x, y, angle=0.0, scale=1.0, alpha=1.0, pivot="bottom"):
    """alpha-composite sprite with base (bottom-centre) or centre at (x, y), rotated (deg, ccw) around that pivot."""
    if alpha <= 0.003 or scale <= 0.01:
        return
    s = spr
    if abs(scale - 1) > 1e-3:
        s = s.resize((max(1, int(s.width * scale)), max(1, int(s.height * scale))), Image.BILINEAR)
    if pivot == "bottom":
        # pad so the base is the centre, then rotate about centre
        pad = Image.new("RGBA", (s.width, s.height * 2), (0, 0, 0, 0))
        pad.paste(s, (0, 0))
        s = pad
    if abs(angle) > 0.05:
        s = s.rotate(angle, Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = s.getchannel("A").point(lambda v: int(v * alpha))
        s = s.copy(); s.putalpha(a)
    canvas.alpha_composite(s, (int(round(x - s.width / 2)), int(round(y - s.height / 2))), ) if \
        -s.width < x < canvas.width + s.width and -s.height < y < canvas.height + s.height else None


def add_glow(canvas, spr, x, y, size, alpha=1.0, mode="add"):
    if alpha <= 0.003 or size < 2:
        return canvas
    g = spr.resize((int(size), int(size)), Image.BILINEAR)
    if mode == "add":
        layer = Image.new("RGB", canvas.size, (0, 0, 0))
        a = np.asarray(g).astype(np.float32)
        rgb = (a[..., :3] * (a[..., 3:4] / 255.0) * alpha).astype(np.uint8)
        layer.paste(Image.fromarray(rgb, "RGB"), (int(x - size / 2), int(y - size / 2)))
        base = canvas.convert("RGB")
        out = ImageChops.add(base, layer)
        if canvas.mode == "RGBA":
            out = out.convert("RGBA")
        return out
    gg = g.copy()
    gg.putalpha(g.getchannel("A").point(lambda v: int(v * alpha)))
    canvas.alpha_composite(gg, (int(x - size / 2), int(y - size / 2)))
    return canvas


def camera(layer, cx, cy, zoom, out=(W, H)):
    """view of `layer` centred on (cx, cy) in layer pixels at zoom (1 = layer px per output px)."""
    w, h = out
    sx = 1.0 / zoom
    x0 = cx - w * sx / 2; y0 = cy - h * sx / 2
    return layer.transform(out, Image.AFFINE, (sx, 0, x0, 0, sx, y0), resample=Image.BILINEAR)


# ---------------------------------------------------------------- text
def shadow_text(img, xy, text, f, fill, anchor="la", stroke=3, blur=8, shadow=(0, 0, 0, 190)):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0] + 4, xy[1] + 6), text, font=f, fill=shadow, anchor=anchor, stroke_width=stroke, stroke_fill=shadow)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(sh)
    ImageDraw.Draw(img).text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))


def pill(img, xy, text, size=24, bg=(10, 18, 34, 190), fg=(244, 238, 226, 255), anchor="l", alpha=1.0, wt="Inter-SemiBold.otf"):
    if alpha <= 0.01:
        return
    f = font(wt, size)
    d0 = ImageDraw.Draw(img)
    l, t, r, b = d0.textbbox((0, 0), text, font=f)
    w, h = r - l + 32, b - t + 20
    x, y = xy
    if anchor == "r":
        x -= w
    elif anchor == "c":
        x -= w / 2
    layer = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 10, fill=bg)
    d.text((16 - l, 10 - t), text, font=f, fill=fg)
    if alpha < 0.999:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(layer, (int(x), int(y)))


def grade(img, vignette=0.35, grain_seed=None, grain=0.0):
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    h, w = a.shape[:2]
    if vignette:
        a *= _vig(w, h, vignette)[..., None]
    if grain and grain_seed is not None:
        a += (_grain(w, h, grain_seed % 8) * grain)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


@lru_cache(maxsize=4)
def _vig(w, h, k):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot((x - w / 2) / (w / 2), (y - h / 2) / (h / 2)) / math.sqrt(2)
    return (1 - k * r ** 2.2).astype(np.float32)


@lru_cache(maxsize=8)
def _grain(w, h, s):
    return (np.random.default_rng(1000 + s).standard_normal((h, w)) * 1.0).astype(np.float32)
