"""Typography primitives: fonts, theme tokens, kinetic text, plates, rolling digits, collision registry.
Layers are PIL RGBA images the size of the frame; sizes scale with the frame so the same spec works at any resolution."""
import math
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .easing import clamp, seg, smooth, smoother, out_cubic

_FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


@dataclass(frozen=True)
class Theme:
    """brand tokens (defaults: OrbitalAtlas, see productions/dubai/motion/MOTION_DESIGN_SYSTEM.md §3). Override per project."""
    ink: tuple = (11, 15, 20)
    text: tuple = (234, 240, 246)
    amber: tuple = (255, 194, 71)
    cyan: tuple = (92, 225, 230)
    muted: tuple = (138, 148, 163)
    font_regular: str = _FR
    font_bold: str = _FB


THEME = Theme()
_fc = {}


def font(px, bold=False, theme=THEME):
    k = (int(max(8, round(px))), bold, theme.font_bold if bold else theme.font_regular)
    if k not in _fc: _fc[k] = ImageFont.truetype(k[2], k[0])
    return _fc[k]


def text_width(s, fnt, track=0.0):
    return sum(fnt.getlength(c) + track for c in s)


class Registry:
    """records the screen boxes of text/plates drawn in one frame so QA can find collisions and out-of-frame text."""
    def __init__(self): self.items = []
    def reset(self): self.items.clear()
    def add(self, group, box, alpha=1.0):
        if group is not None and alpha > 0.35: self.items.append((group, *map(float, box), float(alpha)))
    def collisions(self):
        out = []
        for i, a in enumerate(self.items):
            for b in self.items[i + 1:]:
                if a[0] == b[0]: continue
                if min(a[3], b[3]) - max(a[1], b[1]) > 2 and min(a[4], b[4]) - max(a[2], b[2]) > 2: out.append((a[0], b[0]))
        return out
    def outside(self, size, margin=0):
        W, H = size
        return [it[0] for it in self.items if it[1] < margin or it[2] < margin or it[3] > W - margin or it[4] > H - margin]


def kinetic(layer, xy, s, px, color, t, t0, per=0.028, dur=0.40, rise=0.3, track=0.0, out_t=None, out_dur=0.25,
            shadow=True, bold=True, group=None, reg=None, anchor="left"):
    """per-glyph reveal (fade + rise, ease-out) at a screen position; optional fade-out from out_t. Returns text width."""
    f = font(px, bold); d = ImageDraw.Draw(layer, "RGBA")
    w = text_width(s, f, track * px)
    x = xy[0] - {"left": 0, "center": w / 2, "right": w}[anchor]; y = xy[1]; xs = 0.0; amax = 0.0
    for i, ch in enumerate(s):
        a = out_cubic(seg(t, t0 + i * per, t0 + i * per + dur))
        if out_t is not None: a *= 1 - smooth(seg(t, out_t + i * 0.01, out_t + i * 0.01 + out_dur))
        amax = max(amax, a)
        dy = rise * px * (1 - a)
        if a > 0.003:
            if shadow: d.text((x + xs + px * 0.06, y + dy + px * 0.06), ch, font=f, fill=(0, 0, 0, int(170 * a)))
            d.text((x + xs, y + dy), ch, font=f, fill=tuple(color) + (int(255 * a),))
        xs += f.getlength(ch) + track * px
    if reg is not None: reg.add(group, (x, y, x + xs, y + px * 1.25), amax)
    return xs


def rotated_label(layer, center, s, px, color, angle=0.0, track=0.0, alpha=1.0, glow=0.0, shadow=True, anchor="center", reg=None, group=None, bold=True):
    """whole-string label rotated by `angle` degrees (counter-clockwise on screen), centred (or left/right anchored) at `center`.
    Clipped, not skipped, when it crosses the frame edge. For per-letter reveal use `reveal_label`."""
    return reveal_label(layer, center, s, px, color, 1e9, -1e9, angle=angle, track=track, glow=glow, shadow=shadow, anchor=anchor, reg=reg, group=group, bold=bold, global_alpha=alpha)


def reveal_label(layer, center, s, px, color, t, t0, angle=0.0, track=0.0, dur=0.45, per=0.05, rise=0.32, out_t=None, out_dur=0.35,
                 glow=0.0, shadow=True, anchor="center", reg=None, group=None, bold=True, global_alpha=1.0):
    """letters rise and fade in one by one; the text can lie along an angle (e.g. parallel to a coastline).
    Returns the max glyph alpha (0 = nothing drawn)."""
    f = font(px, bold); ts = px * track
    adv = [f.getlength(c) + ts for c in s]; Wt = sum(adv); pad = int(px * 0.6); Ht = int(px * 1.5)
    tile = Image.new("RGBA", (int(Wt) + 2 * pad, Ht + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(tile, "RGBA")
    sh = Image.new("RGBA", tile.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh, "RGBA"); x = pad; amax = 0.0
    for i, c in enumerate(s):
        a = out_cubic(seg(t, t0 + i * per, t0 + i * per + dur))
        if out_t is not None: a *= 1 - smooth(seg(t, out_t + i * 0.015, out_t + i * 0.015 + out_dur))
        a *= global_alpha; amax = max(amax, a)
        if a > 0.004:
            y = pad + rise * px * (1 - a)
            ds.text((x + px * 0.05, y + px * 0.07), c, font=f, fill=(0, 0, 0, int(190 * a)))
            d.text((x, y), c, font=f, fill=tuple(color) + (int(255 * a),))
        x += adv[i]
    if amax <= 0.004: return 0.0
    if shadow: tile = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(px * 0.06)), tile)
    if glow:
        g = tile.filter(ImageFilter.GaussianBlur(px * 0.12)); g.putalpha(g.getchannel("A").point(lambda v: int(min(255, v * glow)))); tile = Image.alpha_composite(g, tile)
    if abs(angle) > 0.01: tile = tile.rotate(angle, resample=Image.BICUBIC, expand=True)
    cx, cy = center
    ox = {"center": tile.width / 2, "left": pad, "right": tile.width - pad}[anchor] if abs(angle) <= 0.01 else tile.width / 2
    _paste(layer, tile, int(cx - ox), int(cy - tile.height / 2))
    if reg is not None:
        import numpy as np
        bb = np.array([[-Wt / 2, -px * 0.6], [Wt / 2, -px * 0.6], [Wt / 2, px * 0.6], [-Wt / 2, px * 0.6]])
        th = math.radians(angle); R = np.array([[math.cos(th), math.sin(th)], [-math.sin(th), math.cos(th)]])
        q = bb @ R.T + [cx, cy]; reg.add(group, (q[:, 0].min(), q[:, 1].min(), q[:, 0].max(), q[:, 1].max()), amax)
    return amax


def _paste(layer, tile, x, y):
    W, H = layer.size
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + tile.width), min(H, y + tile.height)
    if x1 <= x0 or y1 <= y0: return
    layer.alpha_composite(tile.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


def plate(layer, xy, s, px, t, t0, out_t=None, accent=THEME.amber, text_color=THEME.text, pad=None, reg=None, group=None, bold=False):
    """translucent plate with an accent bar: the plate grows, the text fades in, the whole thing fades out (source chips, titles)."""
    pad = pad if pad is not None else px * 0.7
    f = font(px, bold)
    a_in = out_cubic(seg(t, t0, t0 + 0.45)); a = a_in * (1 - (smooth(seg(t, out_t, out_t + 0.3)) if out_t is not None else 0))
    if a <= 0.003: return 0.0
    x, y = xy; w = text_width(s, f) + pad * 2 + 8; h = px + pad * 1.4
    d = ImageDraw.Draw(layer, "RGBA"); ww = w * out_cubic(seg(t, t0, t0 + 0.5))
    reg and reg.add(group, (x, y, x + w, y + h), a)
    d.rectangle([x, y, x + ww, y + h], fill=(0, 0, 0, int(150 * a)))
    d.rectangle([x, y, x + max(2, px * 0.2), y + h], fill=tuple(accent) + (int(255 * a),))
    d.text((x + pad + 8, y + pad * 0.55), s, font=f, fill=tuple(text_color) + (int(255 * a),))
    return w


def roll(layer, xy, old, new, t, t0, px, dur=0.7, stagger=0.09, color=THEME.text, bold=True, reg=None, group=None):
    """rolling characters: positions that differ scroll vertically from `old` to `new` (year / date counters).
    old and new must have the same length."""
    assert len(old) == len(new), "roll() needs equal-length strings"
    f = font(px, bold); cw = f.getlength("0") + px * 0.04; hh = int(px * 1.25)
    tile = Image.new("RGBA", (int(cw * len(new)) + 20, hh + 10), (0, 0, 0, 0))
    for i, (o, n) in enumerate(zip(old, new)):
        e = smoother(seg(t, t0 + i * stagger, t0 + i * stagger + dur)) if o != n else 1.0
        cell = Image.new("RGBA", (int(cw) + 4, hh), (0, 0, 0, 0)); dc = ImageDraw.Draw(cell, "RGBA")
        if o != n:
            dc.text((2, -e * hh * 0.9), o, font=f, fill=tuple(color) + (int(255 * (1 - e)),))
            dc.text((2, (1 - e) * hh * 0.9), n, font=f, fill=tuple(color) + (int(255 * e),))
        else:
            dc.text((2, 0), n, font=f, fill=tuple(color) + (255,))
        tile.alpha_composite(cell, (int(i * cw) + 8, 4))
    sh = Image.new("RGBA", tile.size, (0, 0, 0, 0)); sh.putalpha(tile.getchannel("A").point(lambda v: int(v * 0.63)))
    sh = sh.filter(ImageFilter.GaussianBlur(px * 0.05))
    _paste(layer, sh, int(xy[0] + px * 0.04), int(xy[1] + px * 0.06)); _paste(layer, tile, int(xy[0]), int(xy[1]))
    reg and reg.add(group, (xy[0], xy[1], xy[0] + tile.width, xy[1] + tile.height), 1.0)
    return tile.width
