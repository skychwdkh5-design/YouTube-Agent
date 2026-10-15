"""Word-level kinetic typography v2 (VISUAL_REF_002): every word is a cached raster TILE (fill or outline) that is transformed per frame -
rise from a mask, travel in depth, slide with tracking, outline draw-on then fill, type-on with a cursor, light glint - and composed into
lines that wrap and never jump. Overlays built on it: KineticLine, ImpactCard (full-frame colour card), NumberCard (kicker + count-up value +
unit in a HUD panel), YearTag (HUD date stamp), plus `push_lines` (line -> line text transition).

Determinism: every frame is a pure function of t. Timing: word start times come from the narration (provider/alignment) or are explicit."""
# effect-reuse-checked: kinetic.py has single-string primitives; this adds per-word tiles, outline typography, depth travel, glint, colour
# cards, number cards and line transitions (VR2-01, VR2-04, VR2-07, VR2-11, VR2-13 of docs/references/library), none of which existed.
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from . import easing as E
from . import textrec as _TR
from . import kinetic as K
from .layers import Overlay

WHITE, INK = (255, 255, 255), (11, 15, 20)
AMBER, CYAN, VIOLET = (255, 194, 71), (92, 225, 230), (124, 77, 255)
_tiles = {}


def tile(word, px, weight="black", mode="fill", color=WHITE, stroke=None):
    """RGBA raster of one word with padding; mode 'fill' | 'outline' (stroke only, inside transparent). Cached."""
    key = (word, int(round(px)), weight, mode, tuple(color), stroke)
    if key in _tiles: return _tiles[key]
    f = K.face(px, weight); w = int(math.ceil(f.getlength(word))) + 1; pad = int(px * 0.35) + 4; h = int(px * 1.32)
    W, H = w + 2 * pad, h + 2 * pad; sw = stroke or max(2, int(round(px * 0.035)))
    if mode == "fill":
        im = Image.new("RGBA", (W, H), tuple(color) + (0,)); ImageDraw.Draw(im).text((pad, pad), word, font=f, fill=tuple(color) + (255,))
    else:
        outer = Image.new("L", (W, H), 0); ImageDraw.Draw(outer).text((pad, pad), word, font=f, fill=255, stroke_width=sw, stroke_fill=255)
        inner = Image.new("L", (W, H), 0); ImageDraw.Draw(inner).text((pad, pad), word, font=f, fill=255)
        a = np.clip(np.asarray(outer, np.int16) - np.asarray(inner, np.int16), 0, 255).astype(np.uint8)
        im = Image.new("RGBA", (W, H), tuple(color) + (0,)); im.putalpha(Image.fromarray(a))
    if len(_tiles) > 4000: _tiles.clear()
    _tiles[key] = (im, pad, w); return _tiles[key]


def _alpha(im, a):
    if a >= 0.999: return im
    out = im.copy(); out.putalpha(out.getchannel("A").point(lambda v: int(v * max(0.0, a)))); return out


def put(layer, word, x, y, px, weight="black", color=WHITE, mode="fill", alpha=1.0, scale=1.0, blur=0.0, clip=None, reveal=None, glint=None, glow_r=0.0, cut_above=None):
    """draw one word with its top-left at (x, y) (layout position at scale 1). scale is about the word centre; clip = SCREEN y of a mask line:
    only the part of the word above it is visible (a word rising from behind a line); cut_above = screen y above which the word is hidden (leaving
    upward through a line); reveal = fraction visible left->right (draw-on); glint = position 0..1 of a light band. Returns the box."""
    if alpha <= 0.004: return None
    im, pad, w = tile(word, px, weight, mode, color)
    if reveal is not None or glint is not None:
        im = im.copy(); W, H = im.size; a = np.asarray(im.getchannel("A"), np.float32)
        if reveal is not None:
            cols = np.arange(W, dtype=np.float32)[None, :]; edge = pad + (w + 2) * E.clamp(reveal); a = a * np.clip((edge - cols) / 3.0, 0, 1)
        im.putalpha(Image.fromarray(a.astype(np.uint8)))
        if glint is not None and 0 < glint < 1:
            cols = np.arange(W, dtype=np.float32)[None, :]; rows = np.arange(H, dtype=np.float32)[:, None]
            band = np.exp(-(((cols - rows * 0.45) - (-0.3 * W + 1.6 * W * glint)) / (0.07 * W + 2)) ** 2) * (a / 255.0)
            rgb = np.asarray(im, np.float32)[..., :3]; rgb = rgb + (255 - rgb) * band[..., None] * 0.85
            im = Image.fromarray(np.dstack([rgb, a]).clip(0, 255).astype(np.uint8), "RGBA")
    if glow_r > 0: im = K.glow(im, glow_r, 0.9)
    if abs(scale - 1.0) > 1e-3:
        W, H = im.size; nw, nh = max(1, int(W * scale)), max(1, int(H * scale)); cx, cy = x - pad + W / 2, y - pad + H / 2
        im = im.resize((nw, nh), Image.BICUBIC); ox, oy = int(round(cx - nw / 2)), int(round(cy - nh / 2))
    else:
        ox, oy = int(round(x - pad)), int(round(y - pad))
    if blur > 0.3: im = im.filter(ImageFilter.GaussianBlur(blur))
    if clip is not None or cut_above is not None:
        rows = oy + np.arange(im.height, dtype=np.float32)[:, None]; a = np.asarray(im.getchannel("A"), np.float32)
        if clip is not None: a = a * np.clip((clip - rows) / 1.5, 0, 1)
        if cut_above is not None: a = a * np.clip((rows - cut_above) / 1.5, 0, 1)
        im = im.copy(); im.putalpha(Image.fromarray(a.astype(np.uint8)))
    im = _alpha(im, alpha); layer.paste(im, (ox, oy), im)
    box = (x + (1 - scale) * w / 2, y + (1 - scale) * px * 0.6, x + w * (1 + scale) / 2, y + px * 1.25 * scale)
    if scale > 0.95 and blur <= 0.3 and reveal is None and mode == "fill": _TR.note(word, px * scale, box, color, alpha)       # settled words only (MOBILE_READABILITY_QA)
    return box


def layout(words, px, weight, max_w, gap=0.26, line_h=1.12, align="center", x0=0.0, y0=0.0, scales=None):
    """positions (x, y) per word for a block wrapped into balanced lines; x0 is the centre (align center) or the left edge."""
    ws = [K.width(w, px * (scales[i] if scales else 1.0), weight) for i, w in enumerate(words)]; sp = px * gap
    lines, cur, cw = [], [], 0.0
    total = sum(ws) + sp * (len(ws) - 1)
    target = total / max(1, math.ceil(total / max_w)) if total > max_w else max_w
    for i, w in enumerate(ws):
        if cur and cw + sp + w > max(target * 1.08, w) and cw > 0: lines.append(cur); cur, cw = [], 0.0
        cur.append(i); cw += (sp if len(cur) > 1 else 0) + w
    if cur: lines.append(cur)
    pos = {}; n = len(lines); yy = y0 - (n - 1) * px * line_h / 2
    for li, idx in enumerate(lines):
        lw = sum(ws[j] for j in idx) + sp * (len(idx) - 1); x = x0 - lw / 2 if align == "center" else x0
        for j in idx: pos[j] = (x, yy + li * px * line_h); x += ws[j] + sp
    return pos, lines


PRESETS = ("rise", "depth_in", "depth_out", "slide", "outline_fill", "type", "pop")


def animate_word(layer, word, x, y, px, t, t0, preset="rise", weight="black", color=WHITE, emph=False, accent=AMBER, dur=0.32, exit_t=None, exit="up", hold_glint=True):
    """one word through its entrance preset, its emphasis treatment and its exit. Returns the box or None."""
    u = E.seg(t, t0, t0 + dur)
    if u <= 0: return None
    cut_above = None
    col = accent if emph else color; sc = 1.0; a = 1.0; blur = 0.0; clip = None; reveal = None; mode = "fill"; yy = y; xx = x; glint = None; glow_r = 0.0
    if preset == "rise":
        yy = y + (1 - E.out_expo(u)) * px * 1.25; clip = y + px * 1.3
    elif preset == "depth_in":                       # from far behind: small, soft, then lands
        e = E.out_expo(u); sc = 0.45 + 0.55 * e; a = min(1, u * 2.2); blur = (1 - e) * px * 0.06
    elif preset == "depth_out":                      # from in front of the camera: huge, blurred, settles (travel toward the screen plane)
        e = E.out_expo(u); sc = 2.6 - 1.6 * e; a = min(1, u * 2.5); blur = (1 - e) * px * 0.12
    elif preset == "slide":
        e = E.out_expo(u); xx = x - (1 - e) * px * 1.6; a = min(1, u * 2)
    elif preset == "outline_fill":                   # outline draws on, then the fill floods in
        rv = E.out_cubic(E.seg(t, t0, t0 + dur)); f = E.smooth(E.seg(t, t0 + dur * 0.8, t0 + dur * 1.8))
        b1 = put(layer, word, x, y, px, weight, col, "outline", 1.0, 1.0, 0, None, rv)
        b2 = put(layer, word, x, y, px, weight, col, "fill", f) if f > 0 else None
        return b2 or b1
    elif preset == "type":
        n = max(1, len(word)); k = int(math.ceil(E.clamp(u) * n)); part = word[:k]
        if k < n: K.draw_text(layer, (x + K.width(part, px, weight), y + px * 0.15), "|", px * 0.9, accent, "regular", 0.9)
        return put(layer, part, x, y, px, weight, col, "fill", 1.0) if part else None
    elif preset == "pop":
        sc = E.lerp(0.4, 1.0, E.out_back(u, 2.4)) if u < 1 else 1.0; a = min(1, u * 3)
    if emph:
        glow_r = px * 0.08
        if hold_glint: glint = E.seg(t, t0 + dur, t0 + dur + 0.6)
    if exit_t is not None and t > exit_t:
        v = E.in_cubic(E.seg(t, exit_t, exit_t + 0.25))
        if exit == "up": yy -= v * px * 1.25; a *= 1 - 0.3 * v; clip = None; cut_above = y - px * 0.05
        elif exit == "away": sc *= 1 - 0.35 * v; a *= 1 - v; blur += v * px * 0.05
        else: a *= 1 - v
    return put(layer, word, xx, yy, px, weight, col, mode, a, sc, blur, clip, reveal, glint if glint and 0 < glint < 1 else None, glow_r, cut_above)


def push_lines(layer, x, y, old, new, px, t, t0, dur=0.35, weight="bold", color=WHITE, align="left"):
    """line -> line transition in one slot: the old line leaves upward through the slot's top edge while the new one rises through its bottom edge
    (VR2 'complex text transitions'). Both are masked by the slot, so nothing overlaps."""
    u = E.in_out_cubic(E.seg(t, t0, t0 + dur)); top, bot = y - px * 0.05, y + px * 1.3; out = None
    for s_, off in ((old, -u), (new, 1 - u)):
        if not s_ or (s_ is old and u >= 1) or (s_ is new and u <= 0): continue
        xx = x - (K.width(s_, px, weight) / 2 if align == "center" else 0)
        b = put(layer, s_, xx, y + off * px * 1.35, px, weight, color, "fill", 1.0, 1.0, 0, bot, None, None, 0.0, top); out = b or out
    return out


# ---------------------------------------------------------------------------------------------------------------------- overlays
class KineticLine(Overlay):
    """a phrase whose words animate on their own times. words: [{'text','start'[,'emph']}]. xy and px are frame fractions."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, words, xy=(0.5, 0.5), px=0.08, preset="rise", weight="black", color=WHITE, align="center", max_w=0.8, out_t=None, exit="up",
                 accent=AMBER, group="kline", upper=False):
        self.words = [dict(w, text=(w["text"].upper() if upper else w["text"])) for w in words]; self.xy, self.px, self.preset, self.weight = xy, px, preset, weight
        self.color, self.align, self.max_w, self.out_t, self.exit, self.accent, self.group = color, align, max_w, out_t, exit, accent, group
    def draw(self, ctx):
        W, H = ctx.size; px = self.px * H; t = ctx.t
        if t < self.words[0]["start"] - 0.05 or (self.out_t is not None and t > self.out_t + 0.3): return
        pos, _ = layout([w["text"] for w in self.words], px, self.weight, self.max_w * W, align=self.align, x0=self.xy[0] * W, y0=self.xy[1] * H)
        box = None
        for i, w in enumerate(self.words):
            b = animate_word(ctx.ui, w["text"], pos[i][0], pos[i][1], px, t, w["start"], self.preset, self.weight, self.color, bool(w.get("emph")), self.accent, exit_t=self.out_t, exit=self.exit)
            if b: box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        if box: ctx.reg.add(self.group, box, 1.0)
    def describe(self): return dict(super().describe(), effect="kinetic_line", preset=self.preset, words=len(self.words))


class ImpactCard(Overlay):
    """full-frame colour card with huge type (VR2-04): the card wipes in on a diagonal, words travel in depth on their own times, an outline
    echo of the text sits behind, and the card cuts out at t1. Use for a revelation, at most ~2 per minute."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, words, t0, t1, bg=AMBER, fg=INK, echo=WHITE, px=0.17, preset="depth_out", grid=True, kicker=None):
        self.words, self.t0, self.t1, self.bg, self.fg, self.echo, self.px, self.preset, self.grid, self.kicker = words, t0, t1, bg, fg, echo, px, preset, grid, kicker
    def draw(self, ctx):
        t = ctx.t
        if t < self.t0 or t >= self.t1: return
        W, H = ctx.size; u = E.out_expo(E.seg(t, self.t0, self.t0 + 0.22)); card = Image.new("RGBA", (W, H), tuple(self.bg) + (255,))
        if self.grid:
            d = ImageDraw.Draw(card, "RGBA"); sp = H * 0.075; c = tuple(int(v * 0.86) for v in self.bg) + (255,)
            for x in np.arange((t * 30) % sp, W, sp): d.line([(x, 0), (x, H)], fill=c, width=1)
            for y in np.arange(0, H, sp): d.line([(0, y), (W, y)], fill=c, width=1)
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon([(0, 0), (W * 1.35 * u, 0), (W * 1.35 * u - H * 0.35, H), (0, H)], fill=255)
        card.putalpha(m); ctx.ui.alpha_composite(card)
        px = self.px * H; txt = [w["text"].upper().strip(".,:;") for w in self.words]
        while K.width(" ".join(txt), px, "black") > W * 0.86 * 2 and px > 20: px *= 0.92
        pos, _ = layout(txt, px, "black", W * 0.86, x0=W / 2, y0=H * 0.42)
        for i, w in enumerate(self.words):
            st = max(self.t0 + 0.08, w["start"])
            put(ctx.ui, txt[i], pos[i][0] + px * 0.05, pos[i][1] + px * 0.05, px, "black", self.echo, "outline", 0.85 * E.smooth(E.seg(t, st + 0.15, st + 0.45)))
            animate_word(ctx.ui, txt[i], pos[i][0], pos[i][1], px, t, st, self.preset, "black", self.fg, False, dur=0.3)
        if self.kicker:
            K.draw_text(ctx.ui, (W / 2, H * 0.18), self.kicker.upper(), H * 0.03, self.fg, "bold", E.smooth(E.seg(t, self.t0 + 0.1, self.t0 + 0.4)), track=0.25, anchor="center")
        x0 = min(p[0] for p in pos.values()); y1 = max(p[1] for p in pos.values()) + px * 1.2
        ctx.reg.add("impact", (x0, min(p[1] for p in pos.values()), W - x0, y1), 1.0)
    def describe(self): return dict(super().describe(), effect="impact_card")


class NumberCard(Overlay):
    """the single focus for a number: a HUD panel with a kicker line (the words before the number), the value counting up to its exact string,
    the unit, corner brackets and an accent bar; an optional leader line to an anchor that follows the camera (`anchor_fn(ctx) -> (x, y)`)."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, value, unit, kicker, t0, t1, xy=(0.07, 0.30), px=0.16, accent=CYAN, anchor_fn=None, group="number"):
        self.value, self.unit, self.kicker, self.t0, self.t1, self.xy, self.px, self.accent, self.anchor_fn, self.group = value, unit, kicker, t0, t1, xy, px, accent, anchor_fn, group
    def draw(self, ctx):
        t = ctx.t
        if t < self.t0 - 0.02 or t > self.t1 + 0.35: return
        from .captions import _count_up
        W, H = ctx.size; px = self.px * H; x, y = self.xy[0] * W, self.xy[1] * H
        o = 1 - E.smooth(E.seg(t, self.t1, self.t1 + 0.3)); u = E.out_expo(E.seg(t, self.t0, self.t0 + 0.35))
        val = _count_up(self.value, E.out_cubic(E.seg(t, self.t0 + 0.1, self.t0 + 0.55)))
        vw = K.width(self.value, px, "black"); uw = K.width(self.unit, px * 0.42, "heavy"); kw = K.width(self.kicker.upper(), px * 0.2, "bold", 0.18)
        pw, ph = max(vw + uw + px * 0.5, kw) + px * 0.7, px * 2.05
        panel = Image.new("RGBA", ctx.size, (0, 0, 0, 0)); d = ImageDraw.Draw(panel, "RGBA")
        d.rectangle([x, y, x + pw * u, y + ph], fill=(8, 12, 18, int(185 * o))); d.rectangle([x, y, x + px * 0.06, y + ph * u], fill=tuple(self.accent) + (int(255 * o),))
        b = px * 0.25
        for cx, cy, dx, dy in ((x + pw, y, -1, 1), (x + pw, y + ph, -1, -1)):
            if u > 0.9: d.line([(cx + dx * b, cy), (cx, cy), (cx, cy + dy * b)], fill=tuple(self.accent) + (int(255 * o),), width=max(2, int(px * 0.02)))
        if self.anchor_fn is not None and u > 0.5:
            ax, ay = self.anchor_fn(ctx); sx, sy = x + pw, y + ph * 0.5; f = E.out_cubic(E.seg(t, self.t0 + 0.2, self.t0 + 0.6))
            d.line([(sx, sy), (sx + (ax - sx) * f, sy + (ay - sy) * f)], fill=tuple(self.accent) + (int(220 * o),), width=max(2, int(px * 0.015)))
            if f >= 1: d.ellipse([ax - px * 0.06, ay - px * 0.06, ax + px * 0.06, ay + px * 0.06], outline=tuple(self.accent) + (int(255 * o),), width=max(2, int(px * 0.015)))
        ctx.ui.alpha_composite(panel)
        lx = x + px * 0.35
        K.draw_text(ctx.ui, (lx, y + px * 0.18), self.kicker.upper(), px * 0.2, self.accent, "bold", o * E.smooth(E.seg(t, self.t0 + 0.1, self.t0 + 0.35)), track=0.18)
        gl = E.seg(t, self.t0 + 0.6, self.t0 + 1.2)
        put(ctx.ui, val, lx, y + px * 0.52 + (1 - E.out_expo(u)) * px * 0.6, px, "black", WHITE, "fill", o * min(1, u * 1.5), 1.0, 0, y + ph - px * 0.08, None, gl if 0 < gl < 1 else None)
        K.draw_text(ctx.ui, (lx + vw + px * 0.18, y + px * 1.05), self.unit, px * 0.42, WHITE, "heavy", o * E.smooth(E.seg(t, self.t0 + 0.35, self.t0 + 0.6)))
        ctx.reg.add(self.group, (x, y, x + pw, y + ph), o)
    def describe(self): return dict(super().describe(), effect="number_card", value=self.value, unit=self.unit)


class YearTag(Overlay):
    """HUD date stamp, top-left: a tick line draws, a small label types on, the year draws as an outline and fills."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, year, label, t0, t1, xy=(0.05, 0.08), px=0.085, accent=CYAN, group="yeartag"):
        self.year, self.label, self.t0, self.t1, self.xy, self.px, self.accent, self.group = str(year), label, t0, t1, xy, px, accent, group
    def draw(self, ctx):
        t = ctx.t
        if t < self.t0 or t > self.t1 + 0.3: return
        W, H = ctx.size; px = self.px * H; x, y = self.xy[0] * W, self.xy[1] * H; o = 1 - E.smooth(E.seg(t, self.t1, self.t1 + 0.3))
        f = E.out_expo(E.seg(t, self.t0, self.t0 + 0.4)); d = ImageDraw.Draw(ctx.ui, "RGBA"); lw = px * 2.6
        d.line([(x, y + px * 1.45), (x + lw * f, y + px * 1.45)], fill=tuple(self.accent) + (int(255 * o),), width=max(2, int(px * 0.03)))
        for k in range(6):
            tx = x + lw * f * k / 5; d.line([(tx, y + px * 1.38), (tx, y + px * 1.52)], fill=tuple(self.accent) + (int(200 * o),), width=1)
        lb = self.label.upper(); n = int(len(lb) * E.seg(t, self.t0 + 0.1, self.t0 + 0.5))
        K.draw_text(ctx.ui, (x, y + px * 1.6), lb[:n], max(11.0, px * 0.26), self.accent, "bold", o, track=0.16)
        b = animate_word(ctx.ui, self.year, x, y, px, t, self.t0 + 0.05, "outline_fill", "black", WHITE, dur=0.35)
        if o < 1 and b is not None:
            pass
        ctx.reg.add(self.group, (x, y, x + max(lw, K.width(self.year, px, "black")), y + px * 1.9), o)
    def describe(self): return dict(super().describe(), effect="year_tag")


class Dim(Overlay):
    """focus helper: darkens everything drawn before it (the map, pins) while a focus element is on screen. DECOR, never a recolour."""
    layer = "ui"; cls = "DECOR"
    def __init__(self, t0, t1, amount=0.45, fade=0.25):
        self.t0, self.t1, self.amount, self.fade = t0, t1, amount, fade
    def draw(self, ctx):
        a = self.amount * E.smooth(E.seg(ctx.t, self.t0, self.t0 + self.fade)) * (1 - E.smooth(E.seg(ctx.t, self.t1, self.t1 + self.fade)))
        if a > 0.01: ctx.ui.alpha_composite(Image.new("RGBA", ctx.size, (5, 8, 12, int(255 * a))))
    def describe(self): return dict(super().describe(), effect="focus_dim")
