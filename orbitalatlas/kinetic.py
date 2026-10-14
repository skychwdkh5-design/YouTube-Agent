"""Kinetic typography primitives (VISUAL_REF_002): word-by-word reveals, word replacement, slides, scale pops, glow, masks, tracking,
colour-offset duplicate, motion-blur streak and a controlled 2.5D tilt. All are pure functions of time `t` drawn onto an RGBA frame-size layer,
so they are deterministic and testable. Text is English; nothing here knows what the words mean (see `semantic`).

Every primitive returns the screen box (x0, y0, x1, y1) it drew, or None, and registers it in an optional `reg` (text.Registry) for QA."""
# effect-reuse-checked: text.kinetic is a per-glyph fade/rise only, MaskReveal/GeoFocus are image transitions, label_tag is a yt-render caption label and the Dubai
# engine's caption/trail code is episode-only; none of them does word-timed reveals, replacement, scale pops, colour-offset duplicates, streaks or 2.5D tilt.
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from . import easing as E

INTER_DIR = "/usr/share/fonts/opentype/inter/"
_FONTS = {"regular": "Inter-Medium.otf", "bold": "Inter-Bold.otf", "heavy": "Inter-ExtraBold.otf", "black": "Inter-Black.otf"}
_FALLBACK = {"regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"}
_cache = {}


def face(px, weight="bold"):
    """Inter (OFL, installed here) with a DejaVu fallback so tests run anywhere. Cached per (size, weight)."""
    key = (int(max(8, round(px))), weight)
    if key not in _cache:
        try: _cache[key] = ImageFont.truetype(INTER_DIR + _FONTS[weight], key[0])
        except OSError: _cache[key] = ImageFont.truetype(_FALLBACK["regular" if weight == "regular" else "bold"], key[0])
    return _cache[key]


def width(s, px, weight="bold", track=0.0):
    f = face(px, weight)
    return sum(f.getlength(c) for c in s) + track * px * max(0, len(s) - 1)


def _blank(size): return Image.new("RGBA", size, (0, 0, 0, 0))


def glow(layer, radius, strength=1.0):
    """add a soft halo of the layer's own colours (neon look); returns a new layer."""
    g = layer.filter(ImageFilter.GaussianBlur(radius))
    a = g.getchannel("A").point(lambda v: int(min(255, v * strength * 2.0))); g.putalpha(a)
    return Image.alpha_composite(g, layer)


def draw_text(layer, xy, s, px, color=(255, 255, 255), weight="bold", alpha=1.0, track=0.0, anchor="left", shadow=0.0, stroke=0, stroke_color=(0, 0, 0)):
    """plain text with optional drop shadow and outline. anchor: left | center | right on x, y = top of the line box. Returns the box."""
    if alpha <= 0.004: return None
    f = face(px, weight); w = width(s, px, weight, track)
    x = xy[0] - {"left": 0, "center": w / 2, "right": w}[anchor]; y = xy[1]
    d = ImageDraw.Draw(layer, "RGBA"); a = int(255 * E.clamp(alpha))
    cx = x
    for ch in s:
        if shadow:
            d.text((cx + px * shadow, y + px * shadow), ch, font=f, fill=(0, 0, 0, int(a * 0.65)))
        d.text((cx, y), ch, font=f, fill=tuple(color) + (a,), stroke_width=stroke, stroke_fill=tuple(stroke_color) + (a,))
        cx += f.getlength(ch) + track * px
    return (x, y, x + w, y + px * 1.25)


def word_by_word(layer, xy, words, px, t, t0s, color=(255, 255, 255), weight="bold", dur=0.22, rise=0.35, gap=0.28, anchor="left", reg=None, group=None, shadow=0.05):
    """words appear one by one at their own start times (`t0s`, e.g. provider word starts): fade + rise + tiny overshoot. Line layout is fixed from the
    FULL text, so nothing jumps when the next word arrives. Returns the box."""
    space = px * gap
    w_all = sum(width(w, px, weight) for w in words) + space * (len(words) - 1)
    x = xy[0] - {"left": 0, "center": w_all / 2, "right": w_all}[anchor]; box = None
    for w, t0 in zip(words, t0s):
        ww = width(w, px, weight); u = E.seg(t, t0, t0 + dur); a = E.out_cubic(u)
        pop = 1 + 0.06 * math.sin(u * math.pi) if u < 1 else 1.0
        if a > 0.004:
            b = draw_text(layer, (x, xy[1] + rise * px * (1 - E.out_cubic(u))), w, px * pop, color, weight, a, shadow=shadow)
            if b: box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        x += ww + space
    if reg is not None and box: reg.add(group, box, 1.0)
    return box


def replace_word(layer, xy, old, new, px, t, t0, color=(255, 255, 255), new_color=None, weight="bold", dur=0.35, anchor="left", reg=None, group=None):
    """animated word replacement: the old word slides up and fades, the new one rises in from below (a one-slot roll)."""
    u = E.in_out_cubic(E.seg(t, t0, t0 + dur)); nc = new_color or color
    b1 = draw_text(layer, (xy[0], xy[1] - u * px * 0.8), old, px, color, weight, 1 - u, anchor=anchor, shadow=0.05)
    b2 = draw_text(layer, (xy[0], xy[1] + (1 - u) * px * 0.8), new, px, nc, weight, u, anchor=anchor, shadow=0.05)
    box = b2 or b1
    if reg is not None and box: reg.add(group, box, 1.0)
    return box


def slide_in(layer, xy, s, px, t, t0, from_dir="left", dist=0.6, dur=0.45, color=(255, 255, 255), weight="bold", anchor="left", track_in=0.0, reg=None, group=None):
    """slides along one axis while letter-spacing tightens (smooth text tracking): track_in is the extra tracking at the start (em)."""
    u = E.out_expo(E.seg(t, t0, t0 + dur)); dx, dy = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}[from_dir]
    off = (1 - u) * dist * px * 3
    b = draw_text(layer, (xy[0] + dx * off, xy[1] + dy * off), s, px, color, weight, E.clamp(u * 1.4), track=track_in * (1 - u), anchor=anchor, shadow=0.05)
    if reg is not None and b: reg.add(group, b, 1.0)
    return b


def scale_pop(layer, center, s, px, t, t0, hold=0.5, overshoot=1.18, dur=0.28, color=(255, 255, 255), weight="black", alpha=1.0, glow_radius=0.0, reg=None, group=None, out=0.2):
    """rapid scale-in with overshoot (emphasis / impact); glow_radius > 0 adds a neon halo. The text is rasterised once at its final size and resampled,
    so the scaling is smooth. Returns the box."""
    u = E.seg(t, t0, t0 + dur)
    if u <= 0: return None
    sc = E.lerp(0.35, 1.0, E.out_back(u, 2.2)) if u < 1 else 1.0
    sc = min(sc, overshoot)
    a = alpha * E.out_cubic(u) * (1 - E.smooth(E.seg(t, t0 + dur + hold, t0 + dur + hold + out)))
    if a <= 0.004: return None
    w = width(s, px, weight); h = px * 1.4; pad = int(px * 0.6)
    tile = _blank((int(w) + 2 * pad, int(h) + 2 * pad)); draw_text(tile, (pad, pad), s, px, color, weight, 1.0, shadow=0.04)
    if glow_radius > 0: tile = glow(tile, glow_radius * px, 1.0)
    tile = tile.resize((max(1, int(tile.width * sc)), max(1, int(tile.height * sc))), Image.BICUBIC)
    tile.putalpha(tile.getchannel("A").point(lambda v: int(v * a)))
    x, y = int(center[0] - tile.width / 2), int(center[1] - tile.height / 2)
    layer.paste(tile, (x, y), tile)
    box = (center[0] - w * sc / 2, center[1] - px * sc * 0.65, center[0] + w * sc / 2, center[1] + px * sc * 0.65)
    if reg is not None: reg.add(group, box, a)
    return box


def duplicate_offset(layer, xy, s, px, t, t0, front=(255, 255, 255), back=(124, 77, 255), offset=0.06, dur=0.3, weight="black", anchor="left", blur_in=True, reg=None, group=None):
    """impact headline: a coloured duplicate sits behind and slightly offset; both slide-blur in horizontally (VE-12)."""
    u = E.out_expo(E.seg(t, t0, t0 + dur))
    if u <= 0: return None
    tile = _blank(layer.size)
    draw_text(tile, (xy[0] + offset * px, xy[1] + offset * px), s, px, back, weight, 1.0, anchor=anchor)
    draw_text(tile, xy, s, px, front, weight, 1.0, anchor=anchor, shadow=0.0)
    if blur_in and u < 1:
        r = (1 - u) * px * 0.25
        if r > 1: tile = tile.filter(ImageFilter.BoxBlur(max(0.1, r * 0.2)))
        tile = tile.transform(tile.size, Image.AFFINE, (1, 0, (1 - u) * px * 1.2, 0, 1, 0))
    tile.putalpha(tile.getchannel("A").point(lambda v: int(v * E.clamp(u * 1.6))))
    layer.alpha_composite(tile)
    w = width(s, px, weight); x = xy[0] - {"left": 0, "center": w / 2, "right": w}[anchor]; box = (x, xy[1], x + w + offset * px, xy[1] + px * 1.3)
    if reg is not None: reg.add(group, box, E.clamp(u))
    return box


def mask_reveal(layer, xy, s, px, t, t0, dur=0.5, direction="right", color=(255, 255, 255), weight="bold", anchor="left", edge_glow=(124, 77, 255), reg=None, group=None):
    """text uncovered by a moving mask edge with a glowing leading edge (light sweep over type)."""
    w = width(s, px, weight); x = xy[0] - {"left": 0, "center": w / 2, "right": w}[anchor]; u = E.in_out_cubic(E.seg(t, t0, t0 + dur))
    if u <= 0: return None
    tile = _blank(layer.size); draw_text(tile, (x, xy[1]), s, px, color, weight, 1.0, shadow=0.04)
    m = Image.new("L", layer.size, 0); md = ImageDraw.Draw(m)
    edge = x + (w + px * 0.3) * u if direction == "right" else x + w - (w + px * 0.3) * u
    md.rectangle([x - 4, xy[1] - 4, edge, xy[1] + px * 1.4] if direction == "right" else [edge, xy[1] - 4, x + w + 4, xy[1] + px * 1.4], fill=255)
    tile.putalpha(Image.fromarray((np.asarray(tile.getchannel("A"), np.float32) * np.asarray(m, np.float32) / 255).astype(np.uint8)))
    layer.alpha_composite(tile)
    if u < 1 and edge_glow:
        d = ImageDraw.Draw(layer, "RGBA"); a = int(220 * (1 - u * 0.5)); d.rectangle([edge - 2, xy[1], edge + 2, xy[1] + px * 1.15], fill=tuple(edge_glow) + (a,))
    box = (x, xy[1], x + w, xy[1] + px * 1.25)
    if reg is not None: reg.add(group, box, E.clamp(u + 0.2))
    return box


def _perspective(dst, src):
    """PIL PERSPECTIVE coefficients mapping output (dst) points to input (src) points."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return tuple(np.linalg.solve(np.array(A, float), np.array(B, float)))


def tilt_25d(layer, xy, s, px, t, t0, angle=-55.0, color=(255, 255, 255), weight="black", dur=0.7, anchor="center", reg=None, group=None, blur=0.0):
    """controlled 2.5D: the text starts tilted about the vertical axis with perspective and settles flat (the big '2,600 km' swoosh of VISUAL_REF_001).
    A perspective transform of a flat raster: no 3D engine, no depth sorting; angle in degrees about the vertical axis."""
    u = E.out_expo(E.seg(t, t0, t0 + dur))
    if u <= 0: return None
    w = width(s, px, weight); h = px * 1.4; pad = int(px * 0.5)
    tile = _blank((int(w) + 2 * pad, int(h) + 2 * pad)); draw_text(tile, (pad, pad), s, px, color, weight, 1.0, shadow=0.04)
    ang = math.radians(angle * (1 - u)); W, H = tile.size
    k = 0.28 * math.sin(ang); dx = W / 2 * (1 - math.cos(ang))
    src = [(0, 0), (W, 0), (W, H), (0, H)]
    dst = [(dx, k * H), (W - dx, -k * H), (W - dx, H + k * H), (dx, H - k * H)]
    out = tile.transform(tile.size, Image.PERSPECTIVE, _perspective(dst, src), Image.BICUBIC)
    if blur > 0 and u < 1: out = out.filter(ImageFilter.GaussianBlur(blur * px * (1 - u)))
    out.putalpha(out.getchannel("A").point(lambda v: int(v * E.clamp(u * 2.0))))
    x = int(xy[0] - W / 2 if anchor == "center" else xy[0]); y = int(xy[1] - H / 2)
    layer.paste(out, (x, y), out)
    box = (x + pad, y + pad, x + W - pad, y + H - pad)
    if reg is not None: reg.add(group, box, E.clamp(u))
    return box


def motion_streak(layer, xy, s, px, t, t0, dur=0.25, direction=(1, 0), length=0.6, color=(255, 255, 255), weight="black", anchor="center", reg=None, group=None):
    """high-impact entrance: directional motion blur that resolves into sharp text (shutter streak, not a filter on the whole frame)."""
    u = E.out_expo(E.seg(t, t0, t0 + dur))
    if u <= 0: return None
    w = width(s, px, weight); pad = int(px * 0.8) + int(length * px * 2)
    tile = _blank((int(w) + 2 * pad, int(px * 1.5) + 2 * pad)); draw_text(tile, (pad, pad), s, px, color, weight, 1.0, shadow=0.04)
    n = max(1, int((1 - u) * 10)); L = (1 - u) * length * px * 2
    if n > 1:
        acc = np.zeros((tile.height, tile.width, 4), np.float32)
        for i in range(n):
            o = (i / (n - 1) - 0.5) * L; sh = tile.transform(tile.size, Image.AFFINE, (1, 0, -o * direction[0], 0, 1, -o * direction[1]))
            acc += np.asarray(sh, np.float32)
        tile = Image.fromarray((acc / n).astype(np.uint8), "RGBA")
    tile.putalpha(tile.getchannel("A").point(lambda v: int(v * E.clamp(u * 2.5))))
    x = int(xy[0] - tile.width / 2) if anchor == "center" else int(xy[0] - pad); y = int(xy[1] - tile.height / 2)
    layer.paste(tile, (x, y), tile)
    box = (x + pad, y + pad, x + tile.width - pad, y + tile.height - pad)
    if reg is not None: reg.add(group, box, E.clamp(u))
    return box


def text_trail(layer, xy, s, px, t, t0, dur=0.5, n=5, step=0.045, color=(255, 255, 255), trail_color=(124, 77, 255), weight="bold", anchor="left", drift=(-1, 0), reg=None, group=None):
    """echo trail: fading copies of the word behind its movement (VISUAL_REF_002 'text trails')."""
    box = None
    for i in range(n, -1, -1):
        tt = t - i * step; u = E.out_cubic(E.seg(tt, t0, t0 + dur))
        if u <= 0: continue
        off = (1 - u) * px * 2.2; a = (1 - i / (n + 1)) * (1.0 if i == 0 else 0.35)
        c = color if i == 0 else trail_color
        b = draw_text(layer, (xy[0] + drift[0] * off, xy[1] + drift[1] * off), s, px, c, weight, a * E.clamp(u * 2), anchor=anchor)
        if b and i == 0: box = b
    if reg is not None and box: reg.add(group, box, 1.0)
    return box


# ------------------------------------------------------------------------------------------------------------ overlays
from .layers import Overlay  # noqa: E402  (kept at the end: the primitives above have no engine dependency)


class KineticTitle(Overlay):
    """documentary title card: a heavy headline (colour-offset duplicate, slide-blur in) with a light sub-line (mask reveal), fading out at t1.
    Positions are screen fractions; sizes scale with the frame height so the same spec works for 16:9 and 9:16."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, head, sub, t0, t1, xy=(0.06, 0.12), head_px=0.095, sub_px=0.036, back=(124, 77, 255), anchor="left"):
        self.head, self.sub, self.t0, self.t1, self.xy, self.head_px, self.sub_px, self.back, self.anchor = head, sub, t0, t1, xy, head_px, sub_px, back, anchor
    def draw(self, ctx):
        t = ctx.t
        if t < self.t0 or t > self.t1 + 0.4: return
        W, H = ctx.size; lay = _blank(ctx.size); o = 1 - E.smooth(E.seg(t, self.t1, self.t1 + 0.35)); x, y = self.xy[0] * W, self.xy[1] * H; hp = self.head_px * H
        while width(self.head, hp, "black") > W * 0.88 and hp > 20: hp *= 0.94
        duplicate_offset(lay, (x, y), self.head, hp, t, self.t0, back=self.back, anchor=self.anchor, reg=ctx.reg, group="title")
        mask_reveal(lay, (x, y + hp * 1.34), self.sub, self.sub_px * H, t, self.t0 + 0.28, dur=0.55, color=(235, 240, 246), weight="bold", anchor=self.anchor, edge_glow=(92, 225, 230), reg=ctx.reg, group="subtitle")
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * o))); ctx.ui.alpha_composite(lay)
    def describe(self): return dict(super().describe(), effect="kinetic_title")


class StatPop(Overlay):
    """a number / year / short fact that pops in with a glow at its word time and leaves after `hold`. count_up animates a numeric string to its value."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, text, t0, xy=(0.5, 0.40), px=0.12, hold=1.6, color=(255, 255, 255), glow_color=None, count_up=False, group=None, weight="black"):
        self.text, self.t0, self.xy, self.px, self.hold, self.color, self.glow, self.count, self.group, self.weight = text, t0, xy, px, hold, color, glow_color, count_up, group or f"stat_{text}", weight
    def draw(self, ctx):
        W, H = ctx.size; s = self.text
        if self.count:
            from .captions import _count_up
            s = _count_up(self.text, E.out_cubic(E.seg(ctx.t, self.t0, self.t0 + 0.4)))
        scale_pop(ctx.ui, (self.xy[0] * W, self.xy[1] * H), s, self.px * H, ctx.t, self.t0, hold=self.hold, color=self.color, weight=self.weight, glow_radius=0.09 if self.glow else 0.0, reg=ctx.reg, group=self.group)
    def describe(self): return dict(super().describe(), effect="stat_pop", count_up=self.count)
