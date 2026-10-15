"""shorts - vertical (1080x1920) motion-design primitives for OrbitalAtlas Shorts.

Building blocks a Short script composes per frame (every function is a pure function of time):
  * `ImageView`   image-space camera over a large source (centre + visible width, sub-pixel, eased); class A camera, never called a flyover
  * `tilt`        put a rendered frame on a perspective plane (2.5-D): a flat image tilted, honest about being flat
  * `zoom_blur`, `shake_free_punch`   radial zoom blur for fast cinematic pushes (motion cue, not a grade of evidence pixels)
  * type: `word_tile`, `slam`, `extrude`, `stack`, `strike`, `counter` (Inter Black tiles from typeset, 2.5-D extrusion, weight contrast)
  * shapes: `resample`, `morph`, `star_polygon`, `Badge` (circle <-> starburst morph that carries a date or number)
  * `grid_floor`, `dust`, `color_card`, `caption_words` (voice-synced word captions, Shorts-sized)
  * `SAFE` - text-safe box of the Shorts UI (right action column and bottom title area excluded) and `check_safe`.
Evidence pixels are never recoloured: overlays sit on top, graded presentation only applies to illustration layers."""
# effect-reuse-checked: director/typeset/kinetic are 16:9 long-form overlays bound to a Scene camera and narration plans; nothing renders a
# vertical Short, extruded type, a starburst morph, polygon morphs, radial zoom blur or Shorts safe zones (effects.json searched: short, morph, extrude).
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from . import easing as E
from . import typeset as TS
from . import kinetic as K
from . import textrec as TR

W, H = 1080, 1920
SAFE = (80, 250, 940, 1380)                 # x0, y0, x1, y1: keep informational text inside (Shorts UI: right buttons, bottom title, top bar)
INK = (8, 10, 14); WHITE = (246, 248, 250); AMBER = (255, 194, 71); CYAN = (92, 225, 230); SOFT = (170, 182, 196)
Image.MAX_IMAGE_PIXELS = None


# ----------------------------------------------------------------- imagery ---
class ImageView:
    """image-space camera over one source image. cx, cy in source pixels (or 0..1 if norm=True); width = visible source width in pixels."""
    def __init__(self, path_or_image, label=None, credit=None):
        self.im = path_or_image if isinstance(path_or_image, Image.Image) else Image.open(path_or_image).convert("RGB")
        self.label, self.credit = label, credit; self.w, self.h = self.im.size

    def view(self, cx, cy, width, size=(W, H), rot=0.0, norm=True):
        if norm: cx, cy = cx * self.w, cy * self.h
        s = width / size[0]; c, si = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        # output (x, y) -> source: centre + R * (x - W/2, y - H/2) * s
        a, b = c * s, -si * s; d, e = si * s, c * s
        cx0 = cx - a * size[0] / 2 - b * size[1] / 2; cy0 = cy - d * size[0] / 2 - e * size[1] / 2
        return self.im.transform(size, Image.AFFINE, (a, b, cx0, d, e, cy0), resample=Image.BICUBIC, fillcolor=INK)

    def to_screen(self, p, cx, cy, width, size=(W, H), norm=True):
        """source point (normalised if norm) -> screen pixel under the same view (rot 0)."""
        if norm: p = (p[0] * self.w, p[1] * self.h); cx, cy = cx * self.w, cy * self.h
        s = width / size[0]; return ((p[0] - cx) / s + size[0] / 2, (p[1] - cy) / s + size[1] / 2)


def lerp_view(a, b, u):
    """a, b = (cx, cy, width); width interpolated in log space (constant-speed zoom)."""
    return (E.lerp(a[0], b[0], u), E.lerp(a[1], b[1], u), math.exp(E.lerp(math.log(a[2]), math.log(b[2]), u)))


def zoom_blur(img, strength, center=None, n=6):
    """radial zoom blur: average of copies scaled up to (1 + strength). Used only during fast pushes (strength ~0.02-0.12)."""
    if strength <= 0.004: return img
    w, h = img.size; cx, cy = center or (w / 2, h / 2); acc = np.asarray(img, np.float32).copy()
    for i in range(1, n):
        s = 1 + strength * i / (n - 1); im = img.resize((int(w * s), int(h * s)), Image.BILINEAR)
        ox, oy = int(cx * s - cx), int(cy * s - cy); acc += np.asarray(im.crop((ox, oy, ox + w, oy + h)), np.float32)
    return Image.fromarray((acc / n).astype(np.uint8))


def _persp_coeffs(src, dst):
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]; B += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(B, float))


def tilt(img, deg, lift=0.0, bg=INK, size=None):
    """lay `img` on a plane tilted back by `deg` (top edge recedes): a flat picture in perspective, nothing more."""
    w, h = img.size; size = size or (w, h); k = math.sin(math.radians(deg)) * 0.42; top_w = w * (1 - k); dy = h * k * 0.32
    dst = [((w - top_w) / 2, dy - lift), ((w + top_w) / 2, dy - lift), (w, h - lift * 0.2), (0, h - lift * 0.2)]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    return img.transform(size, Image.PERSPECTIVE, tuple(_persp_coeffs(src, dst)), resample=Image.BICUBIC, fillcolor=bg)


def cover_scale(deg):
    """oversize factor so that a frame tilted back by `deg` (as in `tilt`) still covers the whole output after a centre crop."""
    k = math.sin(math.radians(max(deg, 0.0))) * 0.42; return 1.03 * max(1.0 / (1 - k), 0.5 / (0.5 - 0.32 * k))


def big_size(deg, size=(W, H)):
    s = cover_scale(deg); return (int(math.ceil(size[0] * s / 2) * 2), int(math.ceil(size[1] * s / 2) * 2))


def cover_tilt(big_img, deg, size=(W, H), bg=INK):
    """tilt an oversize image (from big_size) back by `deg` and centre-crop to `size`. Returns (image, fwd) with fwd(x, y) mapping a pixel
    of the oversize image to its screen pixel - for labels that must stay on their features."""
    k = math.sin(math.radians(max(deg, 0.0))) * 0.42; w, h = big_img.size; ox, oy = (w - size[0]) // 2, (h - size[1]) // 2
    top_w = w * (1 - k); dy = h * k * 0.32
    dst = [((w - top_w) / 2, dy), ((w + top_w) / 2, dy), (w, h), (0, h)]; src = [(0, 0), (w, 0), (w, h), (0, h)]
    out = big_img.transform((w, h), Image.PERSPECTIVE, tuple(_persp_coeffs(src, dst)), resample=Image.BICUBIC, fillcolor=bg).crop((ox, oy, ox + size[0], oy + size[1]))
    A = _persp_coeffs(dst, src)

    def fwd(x, y):
        a, b, c, d, e, f, g, hh = A; den = g * x + hh * y + 1; return ((a * x + b * y + c) / den - ox, (d * x + e * y + f) / den - oy)
    return out, fwd


def tilted_view(iv, cx, cy, width, deg, norm=True, size=(W, H), bg=INK):
    """`iv` (ImageView) on a plane tilted back by `deg`, rendered oversize so the plane covers the frame. Returns (image, to_screen(p))."""
    big = big_size(deg, size); wb = width * big[0] / size[0]
    out, fwd = cover_tilt(iv.view(cx, cy, wb, size=big, norm=norm), deg, size, bg)
    return out, (lambda p: fwd(*iv.to_screen(p, cx, cy, wb, size=big, norm=norm)))


# -------------------------------------------------------------------- type ---
def word_tile(text, px, weight="black", color=WHITE, mode="fill"):
    im, pad, w = TS.tile(text, px, weight, mode, color); return im, pad, w


def text_width(text, px, weight="black"): return K.width(text, px, weight)


def paste_center(layer, im, cx, cy, alpha=1.0):
    if alpha < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, alpha))))
    _paste_clip(layer, im, int(round(cx - im.width / 2)), int(round(cy - im.height / 2)))


def _paste_clip(layer, im, x, y):
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(layer.width, x + im.width), min(layer.height, y + im.height)
    if x1 > x0 and y1 > y0: layer.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


def extrude(text, px, depth=14, color=WHITE, side=(150, 120, 60), weight="black", angle=(0.55, 0.85), mode="fill"):
    """2.5-D extruded word: `depth` stacked copies shifted along `angle`, shaded from side colour to dark, front face on top. Returns RGBA tile."""
    front, pad, w = TS.tile(text, px, weight, mode, color); dx, dy = angle
    out = Image.new("RGBA", (front.width + int(depth * dx) + 4, front.height + int(depth * dy) + 4), (0, 0, 0, 0))
    a = front.getchannel("A")
    for i in range(depth, 0, -1):
        f = i / depth; c = tuple(int(sc * (1 - 0.55 * f)) for sc in side)
        layer = Image.new("RGBA", front.size, c + (0,)); layer.putalpha(a); out.alpha_composite(layer, (int(i * dx), int(i * dy)))
    out.alpha_composite(front, (0, 0)); return out


def slam(t, t0, dur=0.32, start_scale=1.7):
    """scale/alpha/blur of a word slamming in at t0 (exp-out). Returns (scale, alpha, blur_px) or None before t0."""
    u = E.seg(t, t0, t0 + dur)
    if t < t0: return None
    e = E.out_expo(u); return (start_scale - (start_scale - 1) * e, min(1.0, u * 3), (1 - e) * 10)


def place(layer, tile_img, cx, cy, scale=1.0, alpha=1.0, blur=0.0, record=None, px=None, color=WHITE, tag=None, shadow=0.55):
    """paste a type tile centred at (cx, cy); `shadow` = opacity of a soft dark drop shadow that keeps type legible over bright imagery."""
    im = tile_img
    if abs(scale - 1) > 1e-3: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if blur > 0.4: im = im.filter(ImageFilter.GaussianBlur(blur))
    if shadow > 0 and alpha > 0.02:
        pad = 18; sh = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0)); sa = Image.new("L", sh.size, 0)
        sa.paste(im.getchannel("A"), (pad, pad)); sa = sa.filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(min(255, v * 1.6)))
        sh.putalpha(sa); paste_center(layer, sh, cx, cy + 6, alpha * shadow)
    paste_center(layer, im, cx, cy, alpha)
    if record and px and scale > 0.95 and blur <= 0.4 and alpha > 0.5:
        prev = TR.STATE["tag"]; TR.STATE["tag"] = tag
        bb = im.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox() or (0, 0, im.width, im.height)    # inked box, not the padded tile
        x0, y0 = cx - im.width / 2, cy - im.height / 2
        try: TR.note(record, px * scale, (x0 + bb[0], y0 + bb[1], x0 + bb[2], y0 + bb[3]), color, alpha)
        finally: TR.STATE["tag"] = prev


def strike(layer, box, u, color=AMBER, width=14):
    if u <= 0: return
    x0, y0, x1, y1 = box; y = (y0 + y1) / 2; ImageDraw.Draw(layer).line([(x0, y), (x0 + (x1 - x0) * E.out_cubic(u), y)], fill=color + (255,), width=width)


# ------------------------------------------------------------------ shapes ---
def resample(poly, n=180):
    p = np.asarray(poly, float); p = np.vstack([p, p[:1]]); seg = np.hypot(*np.diff(p, axis=0).T); cum = np.concatenate([[0], np.cumsum(seg)])
    s = np.linspace(0, cum[-1], n, endpoint=False); return np.stack([np.interp(s, cum, p[:, 0]), np.interp(s, cum, p[:, 1])], 1)


def morph(a, b, u, n=180):
    """shape morph: both outlines resampled to n points, b rotated to the start that best matches a, then interpolated."""
    A, B = resample(a, n), resample(b, n)
    best = min(range(0, n, 3), key=lambda k: float(((A - np.roll(B, -k, 0)) ** 2).sum())); B = np.roll(B, -best, 0)
    return A + (B - A) * E.clamp(u)


def star_polygon(cx, cy, r, spikes=14, depth=0.0, rot=0.0):
    """circle (depth 0) .. starburst (depth ~0.3): the reference's spiky badge, OrbitalAtlas colours."""
    n = spikes * 2; th = np.linspace(0, 2 * math.pi, n, endpoint=False) + math.radians(rot)
    rr = np.where(np.arange(n) % 2 == 0, r, r * (1 - depth)); return np.stack([cx + rr * np.cos(th), cy + rr * np.sin(th)], 1)


def draw_poly(layer, pts, fill=None, outline=None, width=6, ss=2):
    big = Image.new("RGBA", (layer.width * ss, layer.height * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    q = [(float(x) * ss, float(y) * ss) for x, y in pts]
    if fill: d.polygon(q, fill=fill)
    if outline: d.line(q + [q[0]], fill=outline, width=width * ss, joint="curve")
    layer.alpha_composite(big.resize(layer.size, Image.LANCZOS))


class Badge:
    """round badge that morphs to a starburst on an accent and back, with a short text (a year, a number)."""
    def __init__(self, cx, cy, r=118, color=AMBER, text_color=INK):
        self.cx, self.cy, self.r, self.color, self.tc = cx, cy, r, color, text_color

    def draw(self, layer, text, depth, rot, scale=1.0, alpha=1.0, px=64):
        r = self.r * scale
        if r < 4 or alpha < 0.02: return
        sz = int(r * 2.6); tile = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        draw_poly(tile, star_polygon(sz / 2, sz / 2, r, 16, depth, rot), fill=self.color + (int(255 * alpha),))
        tt, _, _ = TS.tile(text, px * scale, "black", "fill", self.tc); tile.alpha_composite(tt, (int(sz / 2 - tt.width / 2), int(sz / 2 - tt.height / 2)))
        paste_center(layer, tile, self.cx, self.cy)
        if scale > 0.95 and alpha > 0.5: TR.note(text, px * scale, (self.cx - r, self.cy - r, self.cx + r, self.cy + r), self.tc, alpha)


# ------------------------------------------------------------- atmosphere ---
def grid_floor(layer, t, color=CYAN, alpha=0.35, horizon=0.58, speed=0.6, spacing=0.06):
    """perspective grid floor (decor), scrolling toward the viewer."""
    d = ImageDraw.Draw(layer); w, h = layer.size; hy = h * horizon; c = color + (int(255 * alpha),)
    for i in range(-14, 15): d.line([(w / 2 + i * w * 0.02, hy), (w / 2 + i * w * 0.32, h)], fill=c, width=2)
    off = (t * speed) % 1.0
    for j in range(1, 16):
        z = (j - off) * spacing; y = hy + (h - hy) * (z ** 1.6) if z > 0 else None
        if y and y < h: d.line([(0, y), (w, y)], fill=c, width=2)


def dust(layer, t, n=120, seed=3, color=(235, 220, 190), alpha=0.5, drift=(40, -12), area=None, size=3.0):
    rng = np.random.default_rng(seed); x0, y0, x1, y1 = area or (0, 0, layer.width, layer.height); d = ImageDraw.Draw(layer)
    px, py, ph, sp = rng.uniform(x0, x1, n), rng.uniform(y0, y1, n), rng.uniform(0, 1, n), rng.uniform(0.6, 1.4, n)
    for i in range(n):
        u = (t * 0.25 * sp[i] + ph[i]) % 1.0; x = px[i] + drift[0] * u * 6 * sp[i]; y = py[i] + drift[1] * u * 6 * sp[i]
        a = int(255 * alpha * math.sin(math.pi * u)); r = size * sp[i]
        if a > 4: d.ellipse([x - r, y - r, x + r, y + r], fill=color + (a,))


def color_card(layer, color, u, direction="up"):
    """full-frame colour punch entering (u 0->1) - the reference's colour-card beat."""
    if u <= 0: return
    w, h = layer.size; e = E.out_expo(E.clamp(u)); d = ImageDraw.Draw(layer)
    if direction == "up": d.rectangle([0, h * (1 - e), w, h], fill=color + (255,))
    else: d.rectangle([0, 0, w * e, h], fill=color + (255,))


def vignette(img, strength=0.45):
    w, h = img.size; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); r = np.hypot((xx - w / 2) / (w * 0.7), (yy - h / 2) / (h * 0.62))
    v = np.clip(1 - strength * np.clip(r - 0.45, 0, 1) ** 1.3, 0, 1); a = np.asarray(img.convert("RGB"), np.float32) * v[..., None]
    return Image.fromarray(a.astype(np.uint8))


# ---------------------------------------------------------------- captions ---
def caption_words(layer, t, words, y=1240, px=72, emph=(), max_w=820, window=2.4):
    """voice-synced captions: the phrase containing time t, words rise as they are spoken, the spoken word in amber.
    words: [{text, start, end}] in programme time. Phrases are split at sentence ends or every ~4 words."""
    phrases, cur = [], []
    for w in words:
        cur.append(w)
        if w["text"][-1:] in ".,:?!" or len(cur) >= 4: phrases.append(cur); cur = []
    if cur: phrases.append(cur)
    for ph in phrases:
        a, b = ph[0]["start"] - 0.12, ph[-1]["end"] + 0.15
        if not (a <= t <= b): continue
        texts = [w["text"].upper() for w in ph]; pos, _ = TS.layout(texts, px, "black", max_w, align="center", x0=layer.width / 2, y0=y)
        prev = TR.STATE["tag"]; TR.STATE["tag"] = "WordCaptions"
        try:
            for i, w in enumerate(ph):
                active = w["start"] <= t <= w["end"] + 0.05; col = AMBER if (active or w["text"].strip(".,").lower() in emph) else WHITE
                TS.animate_word(layer, texts[i], pos[i][0], pos[i][1], px, t, w["start"] - 0.1, preset="pop", weight="black", color=col, dur=0.22)
        finally: TR.STATE["tag"] = prev
        return texts
    return None


def chip(layer, text, x=80, y=150, px=30, accent=AMBER, alpha=1.0):
    """small source/date chip (kept above the safe box: it is metadata, readable at 30 px)."""
    if alpha < 0.02: return
    f = K.face(px, "bold"); w = f.getlength(text); d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x, y, x + w + px * 1.1, y + px * 1.5], radius=px * 0.25, fill=(0, 0, 0, int(160 * alpha)))
    d.rectangle([x, y, x + px * 0.18, y + px * 1.5], fill=accent + (int(255 * alpha),))
    d.text((x + px * 0.55, y + px * 0.2), text, font=f, fill=WHITE + (int(255 * alpha),)); TR.note(text, px, (x, y, x + w + px * 1.1, y + px * 1.5), WHITE, alpha)


def check_safe(recs, safe=SAFE, allow_top_chips=True):
    """text records outside the Shorts safe box (chips above the box allowed when they stay left of the action column)."""
    bad = []
    for r in recs:
        x0, y0, x1, y1 = r["box"]
        if allow_top_chips and y1 <= safe[1] and x1 <= safe[2] and x0 >= 40 and y0 >= 100: continue
        if x0 < safe[0] - 2 or y0 < safe[1] - 2 or x1 > safe[2] + 2 or y1 > safe[3] + 2: bad.append((r["text"], tuple(round(v) for v in r["box"])))
    return bad
