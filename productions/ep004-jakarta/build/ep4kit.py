"""EP004 episode kit: small overlays and diagram scenes built ON the shared orbitalatlas engine (no new renderer).
Everything here is composition: class chips, data cards, bar charts, schematic diagrams. Nothing is a measurement unless a chip says so.

Evidence classes shown on screen (every frame carries one chip):
  REAL SATELLITE  Landsat pixels processed by tools/autopilot/landsat_color.py (optical context, NOT subsidence)
  DATA CARD       our typography of a published number, with source and period
  ILLUSTRATION    our own drawing / animation, not a measurement
"""
import math
import numpy as np
from PIL import Image, ImageDraw
from orbitalatlas import easing as E, kinetic as K, text as T, typeset as TS
from orbitalatlas.layers import Overlay
from orbitalatlas.illustrate import Diagram
from orbitalatlas import textrec as TR

AMBER, CYAN, WHITE, INK, MUTED = T.THEME.amber, T.THEME.cyan, (240, 244, 248), T.THEME.ink, T.THEME.muted
RED = (255, 107, 94)
CLS_COLOR = {"REAL SATELLITE": CYAN, "DATA CARD": AMBER, "ILLUSTRATION": (170, 140, 255), "STYLISED MAP": MUTED}


def _a(t, t0, t1=None, fin=0.35, fout=0.3):
    """fade-in at t0, fade-out after t1 -> alpha 0..1"""
    a = E.out_cubic(E.seg(t, t0, t0 + fin))
    if t1 is not None: a *= 1 - E.smooth(E.seg(t, t1, t1 + fout))
    return a


def panel(ctx, box, alpha, accent=None, fill=(8, 12, 18, 190)):
    d = ImageDraw.Draw(ctx.ui, "RGBA"); x0, y0, x1, y1 = box
    d.rectangle(box, fill=fill[:3] + (int(fill[3] * alpha),))
    if accent: d.rectangle([x0, y0, x0 + max(3, (y1 - y0) * 0.012 + 3), y1], fill=tuple(accent) + (int(255 * alpha),))


class ClassChip(Overlay):
    """top-left evidence-class chip: coloured class word + what it is. One per scene, always on screen."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, klass, text, t0=0.0, t1=None, y=0.045, px=0.0235):
        self.klass, self.text, self.t0, self.t1, self.y, self.px = klass, text, t0, t1, y, px
    def draw(self, ctx):
        W, H = ctx.size; a = _a(ctx.t, self.t0, self.t1)
        if a <= 0.01: return
        px = self.px * H; col = CLS_COLOR.get(self.klass, CYAN); x, y = 0.035 * W, self.y * H
        wk = K.width(self.klass, px, "black", 0.12); wt = K.width(self.text, px * 0.86, "bold", 0.04)
        w = wk + wt + px * 2.4; h = px * 1.75
        d = ImageDraw.Draw(ctx.ui, "RGBA"); d.rectangle([x, y, x + w, y + h], fill=(6, 9, 14, int(185 * a))); d.rectangle([x, y, x + px * 0.22, y + h], fill=tuple(col) + (int(255 * a),))
        K.draw_text(ctx.ui, (x + px * 0.65, y + px * 0.34), self.klass, px, col, "black", a, 0.12)
        K.draw_text(ctx.ui, (x + px * 0.65 + wk + px * 0.8, y + px * 0.40), self.text, px * 0.86, WHITE, "bold", a, 0.04)
        ctx.reg.add("class_chip", (x, y, x + w, y + h), a)
    def describe(self): return dict(super().describe(), effect="class_chip", klass=self.klass)


class Tag(Overlay):
    """small amber/cyan caution tag (PREPRINT, ABSTRACT ONLY, LINE OF SIGHT ...) at a screen position"""
    layer = "ui"; cls = "TEXT"
    def __init__(self, text, xy, t0, t1=None, color=AMBER, px=0.026, anchor="left", group=None, solid=False):
        self.text, self.xy, self.t0, self.t1, self.color, self.px, self.anchor, self.group, self.solid = text, xy, t0, t1, color, px, anchor, group, solid
    def draw(self, ctx):
        W, H = ctx.size; a = _a(ctx.t, self.t0, self.t1)
        if a <= 0.01: return
        px = self.px * H; w = K.width(self.text, px, "heavy", 0.10) + px * 1.3; h = px * 1.7
        x = self.xy[0] * W - {"left": 0, "center": w / 2, "right": w}[self.anchor]; y = self.xy[1] * H + (1 - a) * px * 0.6
        d = ImageDraw.Draw(ctx.ui, "RGBA")
        if self.solid: d.rectangle([x, y, x + w, y + h], fill=tuple(self.color) + (int(235 * a),)); fg = INK
        else: d.rectangle([x, y, x + w, y + h], fill=(6, 9, 14, int(200 * a)), outline=tuple(self.color) + (int(255 * a),), width=max(2, int(px * 0.08))); fg = self.color
        K.draw_text(ctx.ui, (x + px * 0.65, y + px * 0.34), self.text, px, fg, "heavy", a, 0.10)
        ctx.reg.add(self.group or "tag:" + self.text, (x, y, x + w, y + h), a)
    def describe(self): return dict(super().describe(), effect="tag")


class Stat(Overlay):
    """big data card: kicker line, huge value counting in, unit, a source line. The single focus for a number (never also a caption number: captions are hidden by the caller)."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, value, unit, kicker, source, t0, t1, xy=(0.06, 0.20), px=0.15, accent=AMBER, sub=None):
        self.value, self.unit, self.kicker, self.source, self.t0, self.t1, self.xy, self.px, self.accent, self.sub = value, unit, kicker, source, t0, t1, xy, px, accent, sub
    def draw(self, ctx):
        from orbitalatlas.captions import _count_up
        t = ctx.t; W, H = ctx.size; o = _a(t, self.t0, self.t1, 0.1, 0.35)
        if o <= 0.01: return
        u = E.out_expo(E.seg(t, self.t0, self.t0 + 0.4)); px = self.px * H; x, y = self.xy[0] * W, self.xy[1] * H
        val = _count_up(self.value, E.out_cubic(E.seg(t, self.t0 + 0.1, self.t0 + 0.7)))
        vw = K.width(self.value, px, "black"); uw = K.width(self.unit, px * 0.40, "heavy"); kw = K.width(self.kicker.upper(), px * 0.19, "bold", 0.16)
        sw = K.width(self.source.upper(), px * 0.16, "bold", 0.10); sbw = K.width(self.sub.upper(), px * 0.19, "bold", 0.12) if self.sub else 0
        pw = max(vw + uw + px * 0.5, kw, sw, sbw) + px * 0.8; ph = px * (2.35 if self.sub else 2.1) + px * 0.5
        panel(ctx, (x, y, x + pw * u, y + ph), o, self.accent)
        lx = x + px * 0.38
        K.draw_text(ctx.ui, (lx, y + px * 0.16), self.kicker.upper(), px * 0.19, self.accent, "bold", o * E.smooth(E.seg(t, self.t0 + 0.1, self.t0 + 0.4)), 0.16)
        K.draw_text(ctx.ui, (lx, y + px * 0.50 + (1 - u) * px * 0.4), val, px, WHITE, "black", o * min(1, u * 1.5))
        K.draw_text(ctx.ui, (lx + vw + px * 0.18, y + px * 1.0), self.unit, px * 0.40, WHITE, "heavy", o * E.smooth(E.seg(t, self.t0 + 0.4, self.t0 + 0.7)))
        yy = y + px * 1.62
        if self.sub: K.draw_text(ctx.ui, (lx, yy), self.sub.upper(), px * 0.19, CYAN, "bold", o * E.smooth(E.seg(t, self.t0 + 0.5, self.t0 + 0.8)), 0.12); yy += px * 0.32
        K.draw_text(ctx.ui, (lx, yy + px * 0.04), self.source.upper(), px * 0.16, MUTED, "bold", o * E.smooth(E.seg(t, self.t0 + 0.6, self.t0 + 0.9)), 0.10)
        ctx.reg.add("stat:" + self.value, (x, y, x + pw, y + ph), o)
    def describe(self): return dict(super().describe(), effect="stat_card", value=self.value, unit=self.unit)


class Bars(Overlay):
    """animated horizontal bar chart: rows = [(label, value, t_start)], one scale, value printed at the bar end. Own graphic of published numbers."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, rows, vmax, unit, title, source, t0, t1, box=(0.06, 0.20, 0.62, 0.74), colors=None, fmt="{:g}", note=None):
        self.rows, self.vmax, self.unit, self.title, self.source, self.t0, self.t1, self.box, self.colors, self.fmt, self.note = rows, vmax, unit, title, source, t0, t1, box, colors or {}, fmt, note
    def draw(self, ctx):
        t = ctx.t; W, H = ctx.size; o = _a(t, self.t0, self.t1, 0.3, 0.4)
        if o <= 0.01: return
        x0, y0, x1, y1 = self.box[0] * W, self.box[1] * H, self.box[2] * W, self.box[3] * H; px = H * 0.032
        panel(ctx, (x0, y0, x1, y1), o, CYAN)
        K.draw_text(ctx.ui, (x0 + px * 0.7, y0 + px * 0.5), self.title.upper(), px * 0.8, CYAN, "heavy", o, 0.10)
        n = len(self.rows); top = y0 + px * 2.3; bottom = y1 - px * 2.0; rh = (bottom - top) / max(1, n); lab_w = px * 7.4; bx0 = x0 + px * 0.7 + lab_w; bw = x1 - px * 0.7 - bx0 - px * 3.6
        for i, (lab, val, ts) in enumerate(self.rows):
            g = E.out_cubic(E.seg(t, ts, ts + 0.8)); yy = top + i * rh
            if g <= 0.01: continue
            K.draw_text(ctx.ui, (x0 + px * 0.7, yy + rh * 0.18), lab.upper(), px * 0.78, WHITE, "bold", o * min(1, g * 2), 0.04)
            col = self.colors.get(lab, AMBER); d = ImageDraw.Draw(ctx.ui, "RGBA"); bl = bw * (val / self.vmax) * g
            d.rectangle([bx0, yy + rh * 0.16, bx0 + bw, yy + rh * 0.16 + rh * 0.52], fill=(255, 255, 255, int(22 * o)))
            d.rectangle([bx0, yy + rh * 0.16, bx0 + bl, yy + rh * 0.16 + rh * 0.52], fill=tuple(col) + (int(240 * o),))
            K.draw_text(ctx.ui, (bx0 + bl + px * 0.35, yy + rh * 0.20), self.fmt.format(val * min(1, g * 1.2) if g < 1 else val), px * 0.9, WHITE, "heavy", o * min(1, g * 2))
        K.draw_text(ctx.ui, (x0 + px * 0.7, y1 - px * 1.55), (self.unit + "  |  " + self.source).upper(), px * 0.52, MUTED, "bold", o, 0.08)
        if self.note: K.draw_text(ctx.ui, (x0 + px * 0.7, y1 - px * 0.85), self.note.upper(), px * 0.52, AMBER, "bold", o, 0.08)
        ctx.reg.add("bars", (x0, y0, x1, y1), o)
    def describe(self): return dict(super().describe(), effect="bar_chart", rows=len(self.rows))


class Lines(Overlay):
    """stacked text lines that appear one at a time (t_start each); the last may be emphasised. lines = [(text, t_start, color)]"""
    layer = "ui"; cls = "TEXT"
    def __init__(self, lines, xy, t1, px=0.042, weight="heavy", track=0.04, gap=1.45, plate=True, anchor="left", head=None):
        self.lines, self.xy, self.t1, self.px, self.weight, self.track, self.gap, self.plate, self.anchor, self.head = lines, xy, t1, px, weight, track, gap, plate, anchor, head
    def draw(self, ctx):
        t = ctx.t; W, H = ctx.size; px = self.px * H; t0 = self.lines[0][1]; o = 1 - E.smooth(E.seg(t, self.t1, self.t1 + 0.35))
        if t < t0 or o <= 0.01: return
        x = self.xy[0] * W; y = self.xy[1] * H
        ws = [K.width(s.upper(), px, self.weight, self.track) for s, _, _ in self.lines]; hh = px * self.gap * len(self.lines) + px * (1.2 if self.head else 0.5)
        pw = max(ws + [K.width(self.head.upper(), px * 0.5, "bold", 0.16) if self.head else 0]) + px * 1.2
        x0 = x - {"left": 0, "center": pw / 2, "right": pw}[self.anchor]
        if self.plate: panel(ctx, (x0, y - px * 0.3, x0 + pw, y - px * 0.3 + hh), o * E.smooth(E.seg(t, t0, t0 + 0.3)), CYAN)
        yy = y
        if self.head: K.draw_text(ctx.ui, (x0 + px * 0.6, yy), self.head.upper(), px * 0.5, CYAN, "bold", o * E.smooth(E.seg(t, t0, t0 + 0.4)), 0.16); yy += px * 0.8
        for (s, ts, col), w in zip(self.lines, ws):
            a = o * E.out_cubic(E.seg(t, ts, ts + 0.35))
            if a > 0.01: K.draw_text(ctx.ui, (x0 + px * 0.6 + (1 - E.out_cubic(E.seg(t, ts, ts + 0.35))) * px * 0.8, yy), s.upper(), px, col, self.weight, a, self.track)
            yy += px * self.gap
        ctx.reg.add("lines:" + self.lines[0][0], (x0, y - px * 0.3, x0 + pw, y - px * 0.3 + hh), o)
    def describe(self): return dict(super().describe(), effect="text_lines", n=len(self.lines))


class Arrow(Overlay):
    """screen-space arrow with an optional label; pointing at a map point (source px) when `to_src` is given (follows the camera)."""
    layer = "ui"; cls = "DECOR"
    def __init__(self, to_src, from_off, t0, t1=None, label=None, color=AMBER, lab_px=0.026, width=0.0042):
        self.to, self.off, self.t0, self.t1, self.label, self.color, self.lab_px, self.width = np.asarray(to_src, float), np.asarray(from_off, float), t0, t1, label, color, lab_px, width
    def draw(self, ctx):
        t = ctx.t; W, H = ctx.size; o = _a(t, self.t0, self.t1)
        if o <= 0.01: return
        tip = np.asarray(ctx.view.pt(self.to), float).ravel()[:2]; tail = tip + self.off * np.array([W, H]); f = E.out_cubic(E.seg(t, self.t0, self.t0 + 0.5))
        p = tail + (tip - tail) * f; v = tip - tail; L = np.hypot(*v) + 1e-9; u = v / L; n = np.array([-u[1], u[0]]); hs = H * 0.028
        s = ctx.stroke(self.color, 0.6); s.line([tail, p], H * self.width, o)
        if f > 0.85: s.line([p - u * hs + n * hs * 0.55, p, p - u * hs - n * hs * 0.55], H * self.width, o)
        if self.label and f > 0.5:
            px = self.lab_px * H; w = K.width(self.label.upper(), px, "heavy", 0.08); lx = tail[0] - (w / 2 if abs(u[0]) < 0.8 else (w if u[0] > 0 else 0)); ly = tail[1] - px * 1.7 if u[1] > -0.5 else tail[1] + px * 0.4
            lx = min(max(lx, 0.03 * W), 0.97 * W - w)
            ImageDraw.Draw(ctx.ui, "RGBA").rectangle([lx - px * 0.4, ly - px * 0.15, lx + w + px * 0.4, ly + px * 1.3], fill=(6, 9, 14, int(190 * o)))
            K.draw_text(ctx.ui, (lx, ly), self.label.upper(), px, self.color, "heavy", o, 0.08); ctx.reg.add("arrow:" + self.label, (lx - px * 0.4, ly - px * 0.15, lx + w + px * 0.4, ly + px * 1.3), o)
    def describe(self): return dict(super().describe(), effect="arrow")


class Ring(Overlay):
    """pulsing ring + optional label at a source-px point (follows the camera)"""
    layer = "ui"; cls = "DECOR"
    def __init__(self, p, t0, t1=None, label=None, color=AMBER, r=22.0, off=(0.045, -0.06), px=0.024, sub=None):
        self.p, self.t0, self.t1, self.label, self.color, self.r, self.off, self.px, self.sub = np.asarray(p, float), t0, t1, label, color, r, off, px, sub
    def draw(self, ctx):
        t = ctx.t; W, H = ctx.size; o = _a(t, self.t0, self.t1)
        if o <= 0.01: return
        k = H / 720; c = np.asarray(ctx.view.pt(self.p), float).ravel()[:2]
        if not (0 <= c[0] <= W and 0 <= c[1] <= H * 0.8): return
        s = ctx.stroke(self.color, 0.8); g = E.out_cubic(E.seg(t, self.t0, self.t0 + 0.4)); s.ring(c, self.r * k * (0.5 + 0.5 * g), 2.4 * k, o)
        ph = ((t - self.t0) % 1.5) / 1.5; s.ring(c, self.r * k * (1 + 1.5 * ph), 1.6 * k, o * (1 - ph) * 0.8)
        if self.label:
            px = self.px * H; e = c + np.array(self.off) * np.array([W, H]); s.line([c, e], 2 * k, o * 0.8)
            w = K.width(self.label.upper(), px, "heavy", 0.08); lx = min(e[0], 0.97 * W - w) if self.off[0] >= 0 else max(e[0] - w, 0.03 * W); ly = e[1] - px * 1.1 if self.off[1] < 0 else e[1]
            hh = px * (1.55 + (0.62 if self.sub else 0)); sw = K.width(self.sub.upper(), px * 0.58, "bold", 0.06) if self.sub else 0
            ImageDraw.Draw(ctx.ui, "RGBA").rectangle([lx - px * 0.4, ly - px * 0.1, lx + max(w, sw) + px * 0.4, ly + hh], fill=(6, 9, 14, int(195 * o)))
            K.draw_text(ctx.ui, (lx, ly), self.label.upper(), px, self.color, "heavy", o, 0.08)
            if self.sub: K.draw_text(ctx.ui, (lx, ly + px * 1.12), self.sub.upper(), px * 0.58, WHITE, "bold", o, 0.06)
            ctx.reg.add("ring:" + self.label, (lx - px * 0.4, ly - px * 0.1, lx + max(w, sw) + px * 0.4, ly + hh), o)
    def describe(self): return dict(super().describe(), effect="ring")


class Wipe:
    """before/after wipe on one co-registered grid: a vertical bar moves left->right revealing scene B over scene A (both are layers.Scene with the same camera)."""
    def __init__(self, a, b, t0, t1, labels=("", ""), name="wipe"):
        self.a, self.b, self.t0, self.t1, self.labels = a, b, t0, t1, labels; self.size, self.name = a.size, name
        self.start, self.end = a.start, a.end; self.camera = a.camera; self.reg = a.reg; self.overlays = a.overlays
    def render(self, t, **kw):
        fa = self.a.render(t); f = E.in_out_cubic(E.seg(t, self.t0, self.t1))
        if f <= 0.001: return fa
        fb = self.b.render(t); W, H = self.size; x = int(W * f); out = fa.copy()
        if x > 0: out.paste(fb.crop((0, 0, x, H)), (0, 0))
        d = ImageDraw.Draw(out, "RGBA"); d.rectangle([x - 2, 0, x + 2, H], fill=(255, 255, 255, 235))
        return out
    def manifest(self): return self.a.manifest()


class Backdrop:
    """a Scene wrapper that dims (and optionally desaturates a little) the picture behind data cards; the pixels stay Landsat, the chip says so."""
    def __init__(self, scene, dim=0.45, name=None):
        self.s, self.dim = scene, dim; self.size, self.name = scene.size, name or scene.name; self.start, self.end, self.camera, self.reg, self.overlays = scene.start, scene.end, scene.camera, scene.reg, scene.overlays
    def render(self, t, **kw):
        f = self.s.render(t, **kw); a = np.asarray(f, np.float32) * (1 - self.dim) + np.array(INK, np.float32) * self.dim
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    def manifest(self): return self.s.manifest()


# ---------------------------------------------------------------------------------------------------- diagram scenes ----
class Panel2D(Diagram):
    """base for 2-D schematic scenes: dark gradient + faint grid, all drawing in pixels of the frame (ILLUSTRATION)."""
    def bg(self, t):
        W, H = self.size; im = Image.new("RGB", (W, H), INK); a = np.asarray(im, np.float32)
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]; a = a + yy * np.array([8, 14, 22], np.float32) + (1 - yy) * np.array([3, 6, 10], np.float32)
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im, "RGBA"); sp = H / 14
        for x in np.arange((t * 6) % sp, W, sp): d.line([(x, 0), (x, H)], fill=(120, 160, 200, 14), width=1)
        for y in np.arange(0, H, sp): d.line([(0, y), (W, y)], fill=(120, 160, 200, 14), width=1)
        return im


class OrbitDiagram(Panel2D):
    """EP004 beat 2: a satellite far above the ground, beams going down on two passes. Not to scale (says so). ILLUSTRATION."""
    def __init__(self, size, duration, name="orbit", t_label=(2.0, None), t_pass2=5.2):
        super().__init__(size, duration, name); self.t_label, self.t_pass2 = t_label, t_pass2
    def render(self, t):
        W, H = self.size; im = self.bg(t); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA"); k = H / 720
        gy = H * 0.70; R = W * 3.2; cx = W * 0.5; cyc = gy + R   # big circle: the curve of the Earth
        pts = [(x, cyc - math.sqrt(max(R * R - (x - cx) ** 2, 0))) for x in np.linspace(-W * 0.1, W * 1.1, 80)]
        d.polygon(pts + [(W * 1.1, H), (-W * 0.1, H)], fill=(18, 40, 70, 255)); d.line(pts, fill=(92, 225, 230, 220), width=int(3 * k))
        jx, jy = W * 0.5, gy                                                                    # the city marker on the surface
        sx0 = W * 0.18; sx = sx0 + (W * 0.64) * E.in_out_cubic(E.seg(t, 0.4, self.duration - 0.6)); sy = H * 0.16 + ((sx - W * 0.5) / W) ** 2 * H * 0.30
        for ti, nm in ((self.t_pass2 - 1.6, "PASS 1"), (self.t_pass2 + 0.4, "PASS 2")):        # two beams towards the same spot
            f = E.seg(t, ti, ti + 0.9)
            if f > 0:
                px_ = W * (0.34 if nm == "PASS 1" else 0.66); py_ = H * 0.16 + ((px_ - W * 0.5) / W) ** 2 * H * 0.30
                for j in range(6):
                    q = (f * 1.2 - j * 0.12) % 1.0 if f < 1 else (t * 0.9 - j * 0.16) % 1.0
                    bx, by = px_ + (jx - px_) * q, py_ + (jy - py_) * q; r = (4 + 9 * q) * k
                    d.ellipse([bx - r, by - r * 0.45, bx + r, by + r * 0.45], outline=(255, 194, 71, int(190 * (1 - 0.5 * q))), width=int(2 * k))
                d.line([(px_, py_), (jx, jy)], fill=(255, 194, 71, 70), width=int(2 * k))
                self._sat(d, px_, py_, k, 1.0)
        if t < self.t_pass2 - 1.7: self._sat(d, sx, sy, k, 1.0)
        # Jakarta marker + altitude dimension
        s = 6 * k; d.polygon([(jx, jy - 3 * k), (jx - s, jy - 3 * k - 2.2 * s), (jx + s, jy - 3 * k - 2.2 * s)], fill=(255, 194, 71, 255))
        ga = E.out_cubic(E.seg(t, self.t_label[0], self.t_label[0] + 0.8))
        if ga > 0:
            lx = W * 0.82; top = H * 0.20 + 6 * k; bot = gy - 4 * k; yb = top + (bot - top) * ga
            d.line([(lx, top), (lx, yb)], fill=(240, 244, 248, 230), width=int(2.5 * k))
            for yy in (top, yb): d.line([(lx - 10 * k, yy), (lx + 10 * k, yy)], fill=(240, 244, 248, 230), width=int(2.5 * k))
        im = im.convert("RGBA"); im.alpha_composite(lay); ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if ga > 0.6:
            a = E.smooth(E.seg(t, self.t_label[0] + 0.5, self.t_label[0] + 1.1)); px = 0.05 * H
            K.draw_text(ui, (W * 0.82 - 16 * k, H * 0.40), "ABOUT 430 MILES", px, WHITE, "black", a, 0.02, "right", 0.04)
            K.draw_text(ui, (W * 0.82 - 16 * k, H * 0.40 + px * 1.15), "693 KM · ESA SENTINEL-1 ALTITUDE", px * 0.42, CYAN, "bold", a, 0.10, "right")
        K.draw_text(ui, (W * 0.5, gy + 14 * k), "JAKARTA", 0.034 * H, AMBER, "heavy", 1.0, 0.16, "center")
        K.draw_text(ui, (W * 0.5, H * 0.76), "NOT TO SCALE", 0.022 * H, MUTED, "bold", 0.9, 0.16, "center")
        im.alpha_composite(ui); return im.convert("RGB")
    def _sat(self, d, x, y, k, a):
        w = 26 * k; d.rectangle([x - w * 0.35, y - w * 0.28, x + w * 0.35, y + w * 0.28], fill=(220, 226, 236, 255))
        for sgn in (-1, 1): d.rectangle([x + sgn * w * 0.45 if sgn > 0 else x - w * 1.55, y - w * 0.2, x + sgn * w * 1.55 if sgn > 0 else x - w * 0.45, y + w * 0.2], fill=(70, 120, 200, 255), outline=(200, 220, 255, 255))


class DykeDiagram(Panel2D):
    """EP004 beat 20: cross-section of a coast. A 3 m dyke holds the sea; the ground under it sinks over the 'model years'; the sea reaches the dyke top. ILLUSTRATION, not data."""
    def __init__(self, size, duration, name="dyke", t_over=(1.5, 5.5), t_sink=(5.6, 15.0), t_model=(8.0, None)):
        super().__init__(size, duration, name); self.t_over, self.t_sink, self.t_model = t_over, t_sink, t_model
    def render(self, t):
        W, H = self.size; im = self.bg(t).convert("RGBA"); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA"); k = H / 720
        sink = 0.115 * H * E.in_out_cubic(E.seg(t, *self.t_sink)); wave = math.sin(t * 2.2) * 2.5 * k
        base = H * 0.60; dyke_w = W * 0.07
        # ground (sinks together with the dyke and the land behind it)
        gl = base + sink; d.rectangle([W * 0.34, gl, W, H], fill=(104, 82, 64, 255)); d.rectangle([W * 0.34, gl, W, gl + 10 * k], fill=(86, 128, 70, 255))
        d.polygon([(W * 0.34 - 0.0, gl), (W * 0.30, H), (W * 0.34, H)], fill=(104, 82, 64, 255))
        top = gl - 0.20 * H                                                                            # dyke 'three metres' tall (schematic)
        d.polygon([(W * 0.43, gl), (W * 0.43 + dyke_w * 0.25, top), (W * 0.43 + dyke_w * 0.75, top), (W * 0.43 + dyke_w, gl)], fill=(160, 160, 168, 255), outline=(220, 224, 232, 255))
        # sea, rising level labelled as 'today' then lapping the top as the land sinks (the sea stays; the ground goes down)
        sea_y = base - 0.20 * H * 0.55 - wave
        if t > self.t_over[0]: sea_y = base - 0.20 * H * (0.55 + 0.28 * E.seg(t, *self.t_over)) - wave
        d.rectangle([0, sea_y, W * 0.43 + dyke_w * 0.1, H], fill=(40, 110, 170, 235)); d.rectangle([0, sea_y, W * 0.43 + dyke_w * 0.1, sea_y + 5 * k], fill=(150, 215, 245, 255))
        # water over the top once the dyke has sunk enough
        over = max(0.0, (sea_y - top) * -1.0)
        if sea_y < top + 2 * k:
            f = E.seg(t, self.t_sink[1] * 0.78, self.t_sink[1]); d.polygon([(W * 0.43 + dyke_w * 0.1, sea_y), (W * 0.43 + dyke_w * (0.1 + 0.9 * f), sea_y + 40 * k * f + (top - sea_y) * 0), (W * 0.43 + dyke_w, gl), (W * 0.43 + dyke_w * 0.1, gl)], fill=(40, 110, 170, int(200 * f)))
        for j in range(6): d.ellipse([W * 0.15 + j * 90 * k, sea_y + 20 * k + (j % 3) * 18 * k, W * 0.15 + j * 90 * k + 6 * k, sea_y + 26 * k + (j % 3) * 18 * k], fill=(255, 255, 255, 90))
        # arrow on the ground showing the sinking
        if E.seg(t, *self.t_sink) > 0.02:
            ax, ay = W * 0.80, H * 0.52; L = 0.11 * H * min(1.0, E.seg(t, *self.t_sink) * 1.5)
            d.line([(ax, ay), (ax, ay + L)], fill=(255, 194, 71, 255), width=int(5 * k)); d.polygon([(ax - 12 * k, ay + L - 8 * k), (ax + 12 * k, ay + L - 8 * k), (ax, ay + L + 14 * k)], fill=(255, 194, 71, 255))
        im.alpha_composite(lay); ui = Image.new("RGBA", (W, H), (0, 0, 0, 0)); px = 0.03 * H
        a1 = E.smooth(E.seg(t, 0.4, 1.0)); K.draw_text(ui, (W * 0.04, H * 0.30), "SEA", px * 1.2, CYAN, "heavy", a1, 0.16)
        K.draw_text(ui, (W * 0.43 + dyke_w / 2, top - px * 2.0), "DYKE: 3 M", px, WHITE, "heavy", a1, 0.10, "center")
        K.draw_text(ui, (W * 0.80, H * 0.45), "LAND SINKS", px, AMBER, "heavy", E.smooth(E.seg(t, self.t_sink[0], self.t_sink[0] + 0.7)), 0.10, "center")
        if t >= self.t_model[0]:
            a = E.smooth(E.seg(t, self.t_model[0], self.t_model[0] + 0.6)); w = K.width("2017 MODEL: BY 2040 THE DYKE COULD FAIL", 0.04 * H, "black", 0.04) + 0.06 * H
            ImageDraw.Draw(ui, "RGBA").rectangle([W * 0.5 - w / 2, H * 0.115, W * 0.5 + w / 2, H * 0.19], fill=(6, 9, 14, int(210 * a)), outline=(255, 194, 71, int(255 * a)), width=3)
            K.draw_text(ui, (W * 0.5, H * 0.128), "2017 MODEL: BY 2040 THE DYKE COULD FAIL", 0.04 * H, AMBER, "black", a, 0.04, "center")
            K.draw_text(ui, (W * 0.5, H * 0.205), "IF THE GROUND KEEPS SINKING QUICKLY · MODEL RESULT, NOT A PREDICTION", 0.024 * H, WHITE, "bold", a, 0.06, "center")
        K.draw_text(ui, (W * 0.5, H * 0.94), "SCHEMATIC · NOT TO SCALE", 0.022 * H, MUTED, "bold", 0.9, 0.16, "center")
        im.alpha_composite(ui); return im.convert("RGB")


class CoherenceDiagram(Panel2D):
    """EP004 beat 15: why a pixel can be dropped. Two panels: a steady echo pass-to-pass (coherent) vs a scrambled one (below the 0.6 threshold, thrown out). ILLUSTRATION."""
    def __init__(self, size, duration, name="coherence", t_good=(0.4, 1.6), t_bad=(5.0, 6.2), t_thr=(9.0, 10.0)):
        super().__init__(size, duration, name); self.t_good, self.t_bad, self.t_thr = t_good, t_bad, t_thr
    def render(self, t):
        W, H = self.size; im = self.bg(t).convert("RGBA"); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA"); k = H / 720
        rng = np.random.RandomState(5)
        def wave(x0, x1, y, amp, phase, noise, col, a, n=220):
            xs = np.linspace(x0, x1, n); ph = phase + np.linspace(0, 9 * math.pi, n); jit = np.cumsum(rng.randn(n)) * noise
            ys = y + amp * np.sin(ph + jit); d.line(list(zip(xs, ys)), fill=tuple(col) + (int(255 * a),), width=int(3.4 * k), joint="curve")
        for (x0, x1, title, ts, noise, col) in ((W * 0.07, W * 0.47, "PASS TO PASS: ECHO STAYS CONSISTENT", self.t_good, 0.0, CYAN), (W * 0.53, W * 0.93, "PASS TO PASS: ECHO SCRAMBLED", self.t_bad, 0.20, RED)):
            a = E.out_cubic(E.seg(t, *ts));
            if a <= 0.01: continue
            d.rectangle([x0, H * 0.22, x1, H * 0.66], fill=(10, 16, 24, int(180 * a)), outline=tuple(col) + (int(160 * a),), width=int(2 * k))
            ph0 = 0.0 if noise == 0 else 1.9
            wave(x0 + 14 * k, x1 - 14 * k, H * 0.36, 34 * k, 0.0, 0.0, (255, 194, 71), a)
            wave(x0 + 14 * k, x1 - 14 * k, H * 0.52, 34 * k, ph0 + 0.5 * math.sin(t * 2.0) * (1 if noise else 0), 0.0 if noise == 0 else 0.35, col, a)
        if E.seg(t, *self.t_bad) > 0.5:                                                                # a scrambled pixel is crossed out
            f = E.out_cubic(E.seg(t, self.t_bad[1], self.t_bad[1] + 0.5)); cx, cy = W * 0.73, H * 0.44; r = H * 0.10 * f
            d.line([(cx - r, cy - r), (cx + r, cy + r)], fill=(255, 107, 94, 220), width=int(7 * k)); d.line([(cx - r, cy + r), (cx + r, cy - r)], fill=(255, 107, 94, 220), width=int(7 * k))
        im.alpha_composite(lay); ui = Image.new("RGBA", (W, H), (0, 0, 0, 0)); px = 0.026 * H
        for (x0, x1, title, ts, col) in ((W * 0.07, W * 0.47, "CONSISTENT ECHO", self.t_good, CYAN), (W * 0.53, W * 0.93, "COHERENCE BELOW 0.6", self.t_bad, RED)):
            a = E.smooth(E.seg(t, ts[0] + 0.3, ts[0] + 0.9))
            if a > 0.01: K.draw_text(ui, ((x0 + x1) / 2, H * 0.24), title, px, col, "heavy", a, 0.12, "center")
        a = E.smooth(E.seg(t, self.t_thr[0], self.t_thr[0] + 0.7))
        if a > 0.01:
            w = K.width("COHERENCE < 0.6  →  PIXEL THROWN OUT", 0.040 * H, "black", 0.05) + 0.07 * H
            ImageDraw.Draw(ui, "RGBA").rectangle([W / 2 - w / 2, H * 0.72, W / 2 + w / 2, H * 0.80], fill=(6, 9, 14, int(215 * a)), outline=(255, 194, 71, int(255 * a)), width=3)
            K.draw_text(ui, (W / 2, H * 0.735), "COHERENCE < 0.6  →  PIXEL THROWN OUT", 0.040 * H, AMBER, "black", a, 0.05, "center")
        K.draw_text(ui, (W / 2, H * 0.94), "SCHEMATIC · NOT A REAL ECHO", 0.022 * H, MUTED, "bold", 0.9, 0.16, "center")
        im.alpha_composite(ui); return im.convert("RGB")


class TrendsDiagram(Panel2D):
    """EP004 beat 17: three schematic trend lines 2016 -> 2024: west = fast start then flattens; northwest and northeast = straight. NO numbers. ILLUSTRATION."""
    def __init__(self, size, duration, name="trends", t_west=(0.6, 4.5), t_others=(7.8, 11.0)):
        super().__init__(size, duration, name); self.t_west, self.t_others = t_west, t_others
    def render(self, t):
        W, H = self.size; im = self.bg(t).convert("RGBA"); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA"); k = H / 720
        x0, x1, y0, y1 = W * 0.12, W * 0.88, H * 0.26, H * 0.74                                          # axes: time left->right, sinking downwards
        d.line([(x0, y0), (x0, y1), (x1, y1)], fill=(180, 190, 205, 200), width=int(2.5 * k))
        def curve(f, col, ts, fn):
            n = max(2, int(120 * E.seg(t, *ts)));
            if E.seg(t, *ts) <= 0: return None
            xs = np.linspace(0, E.seg(t, *ts), n); pts = [(x0 + (x1 - x0) * x, y0 + (y1 - y0) * fn(x)) for x in xs]; d.line(pts, fill=tuple(col) + (255,), width=int(5 * k), joint="curve"); return pts[-1]
        west = curve(None, CYAN, self.t_west, lambda x: 0.78 * (1 - math.exp(-5.0 * x)) / (1 - math.exp(-5.0)) + 0.06 * x)    # fast, then slows
        nw = curve(None, AMBER, self.t_others, lambda x: 0.10 + 0.78 * x)                               # straight
        ne = curve(None, (255, 140, 200), (self.t_others[0] + 0.5, self.t_others[1] + 0.5), lambda x: 0.02 + 0.70 * x)
        im.alpha_composite(lay); ui = Image.new("RGBA", (W, H), (0, 0, 0, 0)); px = 0.027 * H
        K.draw_text(ui, (x0, y0 - px * 1.8), "SINKING (SCHEMATIC)", px * 0.8, MUTED, "bold", 0.9, 0.12); K.draw_text(ui, (x1, y1 + px * 0.5), "2016 → 2024", px * 0.9, MUTED, "bold", 0.9, 0.12, "right")
        if west: K.draw_text(ui, (west[0] + px * 0.5, west[1] - px * 1.9), "WEST: FAST START, THEN SLOWED", px, CYAN, "heavy", E.smooth(E.seg(t, self.t_west[1] - 1.0, self.t_west[1])), 0.06, "right")
        if nw: K.draw_text(ui, (nw[0] - px * 0.5, nw[1] + px * 0.3), "NORTHWEST COAST: STRAIGHT LINE", px, AMBER, "heavy", E.smooth(E.seg(t, self.t_others[1] - 0.9, self.t_others[1] + 0.2)), 0.06, "right")
        if ne: K.draw_text(ui, (ne[0] - px * 0.5, ne[1] - px * 2.2), "NORTHEAST (TANJUNG PRIOK): STRAIGHT LINE", px, (255, 140, 200), "heavy", E.smooth(E.seg(t, self.t_others[1] - 0.2, self.t_others[1] + 0.8)), 0.06, "right")
        K.draw_text(ui, (W / 2, H * 0.94), "SCHEMATIC OF THE SHAPE REPORTED · NO VALUES SHOWN", 0.022 * H, MUTED, "bold", 0.9, 0.16, "center")
        im.alpha_composite(ui); return im.convert("RGB")


class HysteresisSketch(Overlay):
    """beat 9: compaction schematic - load removes water (ground sinks), water returns -> springs back a little, but a permanent part stays. ILLUSTRATION."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, t0, t1, t_load, t_unload, box=(0.60, 0.20, 0.96, 0.62)):
        self.t0, self.t1, self.t_load, self.t_unload, self.box = t0, t1, t_load, t_unload, box
    def draw(self, ctx):
        t = ctx.t; W, H = ctx.size; o = _a(t, self.t0, self.t1, 0.4, 0.4)
        if o <= 0.01: return
        x0, y0, x1, y1 = self.box[0] * W, self.box[1] * H, self.box[2] * W, self.box[3] * H; px = H * 0.026
        panel(ctx, (x0, y0, x1, y1), o, (170, 140, 255)); s = ctx.stroke((240, 244, 248), 0.0)
        ax0, ay0, ax1, ay1 = x0 + px * 1.4, y0 + px * 2.2, x1 - px * 1.0, y1 - px * 2.6
        s.line([(ax0, ay0), (ax0, ay1), (ax1, ay1)], 2.2, o)
        pa, pb, pc = (ax0 + (ax1 - ax0) * 0.1, ay0 + (ay1 - ay0) * 0.08), (ax0 + (ax1 - ax0) * 0.85, ay0 + (ay1 - ay0) * 0.82), (ax0 + (ax1 - ax0) * 0.28, ay0 + (ay1 - ay0) * 0.52)
        sl = ctx.stroke(CYAN, 0.5); su = ctx.stroke(AMBER, 0.5)
        f1 = E.seg(t, self.t_load, self.t_load + 1.6); f2 = E.seg(t, self.t_unload, self.t_unload + 1.8)
        if f1 > 0: sl.line([pa, (pa[0] + (pb[0] - pa[0]) * f1, pa[1] + (pb[1] - pa[1]) * f1)], 5, o)
        if f2 > 0: su.line([pb, (pb[0] + (pc[0] - pb[0]) * f2, pb[1] + (pc[1] - pb[1]) * f2)], 5, o)
        K.draw_text(ctx.ui, (x0 + px * 0.8, y0 + px * 0.5), "SCHEMATIC: PUMPING, THEN WATER RETURNS", px * 0.78, (170, 140, 255), "heavy", o, 0.06)
        K.draw_text(ctx.ui, (ax1, ay1 + px * 0.3), "WATER LEVEL FALLS →", px * 0.62, MUTED, "bold", o, 0.06, "right")
        if f2 > 0.95:
            K.draw_text(ctx.ui, ((pb[0] + pc[0]) / 2 + px * 0.5, (pb[1] + pc[1]) / 2 - px * 1.6), "SPRINGS BACK A LITTLE", px * 0.8, AMBER, "heavy", o, 0.05, "center")
            K.draw_text(ctx.ui, (pc[0] + px * 0.4, pc[1] + px * 0.2), "STAYS SQUEEZED", px * 0.8, CYAN, "heavy", o, 0.05)
            s.line([(pc[0], ay0 + (ay1 - ay0) * 0.08), (pc[0], pc[1])], 1.6, o * 0.7)
        ctx.reg.add("hyst", (x0, y0, x1, y1), o)
    def describe(self): return dict(super().describe(), effect="hysteresis_sketch")


class Suspects(Overlay):
    """beat 7: three suspect cards with simple vector icons; one is highlighted by the ESA caption (index `hi`)."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, items, t0s, t1, hi=None, t_hi=None, box=(0.06, 0.22, 0.94, 0.70)):
        self.items, self.t0s, self.t1, self.hi, self.t_hi, self.box = items, t0s, t1, hi, t_hi, box
    def _icon(self, d, kind, cx, cy, s, col, a):
        c = tuple(col) + (int(255 * a),)
        if kind == "well":
            d.rectangle([cx - s * 0.5, cy + s * 0.1, cx + s * 0.5, cy + s * 0.9], outline=c, width=max(2, int(s * 0.07))); d.line([(cx, cy - s * 0.9), (cx, cy + s * 0.1)], fill=c, width=max(2, int(s * 0.1)))
            d.polygon([(cx - s * 0.28, cy - s * 0.35), (cx + s * 0.28, cy - s * 0.35), (cx, cy + s * 0.15)], fill=c)
            for j in range(3): d.arc([cx - s * (0.2 + 0.2 * j), cy + s * 0.2, cx + s * (0.2 + 0.2 * j), cy + s * 0.9], 200, 340, fill=c, width=max(2, int(s * 0.05)))
        elif kind == "build":
            for dx, h in ((-0.55, 0.9), (0.0, 1.3), (0.55, 0.7)):
                d.rectangle([cx + s * dx - s * 0.22, cy + s * 0.8 - s * h, cx + s * dx + s * 0.22, cy + s * 0.8], outline=c, width=max(2, int(s * 0.07)))
            d.line([(cx - s * 0.95, cy + s * 0.8), (cx + s * 0.95, cy + s * 0.8)], fill=c, width=max(2, int(s * 0.1)))
            d.polygon([(cx - s * 0.1, cy - s * 1.0), (cx + s * 0.1, cy - s * 1.0), (cx, cy - s * 0.7)], fill=c)
        else:
            pts = [(cx - s * 0.95 + i * s * 0.095, cy + s * 0.2 + math.sin(i * 0.8) * s * 0.18) for i in range(21)]
            for j in range(3): d.line([(x, y + j * s * 0.3) for x, y in pts], fill=c, width=max(2, int(s * 0.08)))
    def draw(self, ctx):
        t = ctx.t; W, H = ctx.size; o = _a(t, self.t0s[0] - 0.2, self.t1, 0.3, 0.4)
        if o <= 0.01: return
        x0, y0, x1, y1 = self.box[0] * W, self.box[1] * H, self.box[2] * W, self.box[3] * H; n = len(self.items); gap = W * 0.02; cw = (x1 - x0 - gap * (n - 1)) / n; d = ImageDraw.Draw(ctx.ui, "RGBA")
        for i, (title, sub, kind) in enumerate(self.items):
            a = o * E.out_cubic(E.seg(t, self.t0s[i], self.t0s[i] + 0.5));
            if a <= 0.01: continue
            hi = self.hi == i and self.t_hi is not None and t >= self.t_hi; cx0 = x0 + i * (cw + gap) + (1 - a) * W * 0.04; col = AMBER if hi else CYAN
            d.rectangle([cx0, y0, cx0 + cw, y1], fill=(8, 12, 18, int(205 * a)), outline=tuple(col) + (int((255 if hi else 120) * a),), width=max(2, int(H * (0.006 if hi else 0.003))))
            self._icon(d, kind, cx0 + cw / 2, y0 + (y1 - y0) * 0.32, (y1 - y0) * 0.17, col, a)
            px = H * 0.034; K.draw_text(ctx.ui, (cx0 + cw / 2, y0 + (y1 - y0) * 0.62), title.upper(), px, WHITE, "black", a, 0.04, "center")
            K.draw_text(ctx.ui, (cx0 + cw / 2, y0 + (y1 - y0) * 0.62 + px * 1.25), sub.upper(), px * 0.58, MUTED, "bold", a, 0.08, "center")
            if hi: K.draw_text(ctx.ui, (cx0 + cw / 2, y1 - px * 2.3), "ESA CAPTION: LARGELY THIS", px * 0.62, AMBER, "heavy", a, 0.08, "center")
        ctx.reg.add("suspects", (x0, y0, x1, y1), o)
    def describe(self): return dict(super().describe(), effect="suspect_cards")


class Bowls(Overlay):
    """beat 12: 3 hotspot rings flip to 6 'bowls' (schematic glyphs, NOT map positions); the worst one glows. ILLUSTRATION."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, t3, t6, t_worst, t1, box=(0.06, 0.24, 0.94, 0.62)):
        self.t3, self.t6, self.t_worst, self.t1, self.box = t3, t6, t_worst, t1, box
    def draw(self, ctx):
        t = ctx.t; W, H = ctx.size; o = _a(t, self.t3, self.t1, 0.3, 0.4)
        if o <= 0.01: return
        x0, y0, x1, y1 = self.box[0] * W, self.box[1] * H, self.box[2] * W, self.box[3] * H; px = H * 0.03
        panel(ctx, (x0, y0, x1, y1), o, (170, 140, 255)); n = 6 if t >= self.t6 else 3; flip = E.out_back(E.seg(t, self.t6, self.t6 + 0.6)) if t >= self.t6 else 1.0
        d = ImageDraw.Draw(ctx.ui, "RGBA"); cw = (x1 - x0) / 6
        for i in range(6):
            show = i < 3 or t >= self.t6
            if not show: continue
            a = o * (1.0 if i < 3 else E.out_cubic(E.seg(t, self.t6 + 0.15 * (i - 2), self.t6 + 0.15 * (i - 2) + 0.4))); cx = x0 + cw * (i + 0.5); cy = (y0 + y1) / 2 - px * 0.2
            worst = i == 3 and t >= self.t_worst; col = AMBER if worst else CYAN
            for j, r in enumerate((0.9, 0.62, 0.34)):
                rr = cw * 0.42 * r * (1.12 if worst else 1.0); d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=tuple(col) + (int(255 * a * (1 - 0.2 * j)),), width=max(2, int(H * (0.006 if worst else 0.0035))))
            if worst: d.ellipse([cx - cw * 0.14, cy - cw * 0.14, cx + cw * 0.14, cy + cw * 0.14], fill=tuple(AMBER) + (int(255 * a),))
        big = str(n); K.draw_text(ctx.ui, (x0 + px * 0.9, y0 + px * 0.4), (str(3) if t < self.t6 else str(6)) + (" HOTSPOTS · RADAR, 2016-2024" if t < self.t6 else " BOWLS · RADAR + GPS, 2014-2025"), px * 0.95, WHITE, "black", o, 0.04)
        K.draw_text(ctx.ui, (x1 - px * 0.9, y1 - px * 1.5), "SCHEMATIC COUNT · NOT MAP POSITIONS", px * 0.55, MUTED, "bold", o, 0.10, "right")
        ctx.reg.add("bowls", (x0, y0, x1, y1), o)
    def describe(self): return dict(super().describe(), effect="bowl_count")


class BandTimeline(Overlay):
    """beat 10: 1974 -> 2010 bar with the typical-rate band; ticks for the survey kinds (leveling, GPS, InSAR) come from claim C35."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, t0, t1, t_bar, t_band, box=(0.06, 0.52, 0.94, 0.72)):
        self.t0, self.t1, self.t_bar, self.t_band, self.box = t0, t1, t_bar, t_band, box
    def draw(self, ctx):
        t = ctx.t; W, H = ctx.size; o = _a(t, self.t0, self.t1, 0.3, 0.4)
        if o <= 0.01: return
        x0, y0, x1, y1 = self.box[0] * W, self.box[1] * H, self.box[2] * W, self.box[3] * H; px = H * 0.03; panel(ctx, (x0, y0, x1, y1), o, AMBER)
        ax0, ax1 = x0 + px * 1.2, x1 - px * 1.2; ay = y0 + (y1 - y0) * 0.58; f = E.out_cubic(E.seg(t, self.t_bar, self.t_bar + 1.4)); s = ctx.stroke(AMBER, 0.5)
        s.line([(ax0, ay), (ax0 + (ax1 - ax0) * f, ay)], 5, o)
        for yr in (1974, 1980, 1990, 2000, 2010):
            xx = ax0 + (ax1 - ax0) * (yr - 1974) / 36.0
            if f * 36 >= yr - 1974 - 0.1: K.draw_text(ctx.ui, (xx, ay + px * 0.35), str(yr), px * 0.8, WHITE, "heavy", o, 0.04, "center"); s.line([(xx, ay - 8), (xx, ay + 8)], 3, o)
        a = o * E.smooth(E.seg(t, self.t_band, self.t_band + 0.6))
        K.draw_text(ctx.ui, (x0 + px * 0.9, y0 + px * 0.4), "LEVELING · GPS · INSAR SURVEYS", px * 0.78, AMBER, "heavy", o, 0.08)
        if a > 0.01: K.draw_text(ctx.ui, ((ax0 + ax1) / 2, y0 + px * 1.3), "TYPICAL RATES: 3 TO 10 CM A YEAR", px * 1.15, WHITE, "black", a, 0.03, "center")
        ctx.reg.add("bandtl", (x0, y0, x1, y1), o)
    def describe(self): return dict(super().describe(), effect="band_timeline")


class CheckList(Overlay):
    """closing beat: PROVE / CANNOT PROVE columns, then the three-question label. rows appear at their times."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, cols, t1, box=(0.05, 0.20, 0.95, 0.74), final=None):
        self.cols, self.t1, self.box, self.final = cols, t1, box, final   # cols: [(head, color, [(text, t_start)]), ...]
    def draw(self, ctx):
        t = ctx.t; W, H = ctx.size; t0 = min(ts for _, _, rows in self.cols for _, ts in rows) - 0.3; o = _a(t, t0, self.t1, 0.3, 0.4)
        if o <= 0.01: return
        x0, y0, x1, y1 = self.box[0] * W, self.box[1] * H, self.box[2] * W, self.box[3] * H; px = H * 0.034; n = len(self.cols); gap = W * 0.02; cw = (x1 - x0 - gap * (n - 1)) / n
        for ci, (head, col, rows) in enumerate(self.cols):
            ha = o * E.out_cubic(E.seg(t, rows[0][1] - 0.4, rows[0][1] + 0.1)); cx0 = x0 + ci * (cw + gap)
            if ha <= 0.01: continue
            panel(ctx, (cx0, y0, cx0 + cw, y1), ha, col); K.draw_text(ctx.ui, (cx0 + px * 0.8, y0 + px * 0.5), head.upper(), px * 1.1, col, "black", ha, 0.06)
            for ri, (txt, ts) in enumerate(rows):
                a = o * E.out_cubic(E.seg(t, ts, ts + 0.4))
                if a > 0.01: self._wrap(ctx, txt.upper(), cx0 + px * 0.8 + (1 - a) * px * 0.6, y0 + px * 2.5 + ri * px * 3.3, cw - px * 1.4, px * 0.82, a)
        ctx.reg.add("checklist", (x0, y0, x1, y1), o)
    def _wrap(self, ctx, s, x, y, maxw, px, a):
        words = s.split(); lines, cur = [], ""
        for w in words:
            tst = (cur + " " + w).strip()
            if K.width(tst, px, "heavy", 0.03) > maxw and cur: lines.append(cur); cur = w
            else: cur = tst
        lines.append(cur)
        for i, ln in enumerate(lines): K.draw_text(ctx.ui, (x, y + i * px * 1.2), ln, px, WHITE, "heavy", a, 0.03)
    def describe(self): return dict(super().describe(), effect="check_list")


class Gauge(Overlay):
    """beat 16: radar-vs-GPS check card: a centre line (GPS vertical rate) and the radar value offset by +1.64 mm/yr, with the +/-9.40 mm RMSE band; values in text. DATA CARD."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, t0, t1, t_off, t_band, t_caveat, box=(0.06, 0.22, 0.94, 0.70)):
        self.t0, self.t1, self.t_off, self.t_band, self.t_caveat, self.box = t0, t1, t_off, t_band, t_caveat, box
    def draw(self, ctx):
        t = ctx.t; W, H = ctx.size; o = _a(t, self.t0, self.t1, 0.3, 0.4)
        if o <= 0.01: return
        x0, y0, x1, y1 = self.box[0] * W, self.box[1] * H, self.box[2] * W, self.box[3] * H; px = H * 0.03; panel(ctx, (x0, y0, x1, y1), o, CYAN); d = ImageDraw.Draw(ctx.ui, "RGBA")
        K.draw_text(ctx.ui, (x0 + px * 0.9, y0 + px * 0.5), "RADAR vs GPS · ONE STATION (CJKT)", px * 0.85, CYAN, "heavy", o, 0.08)
        cy = y0 + (y1 - y0) * 0.50; ax0, ax1 = x0 + px * 2.0, x1 - px * 2.0; K.draw_text(ctx.ui, (ax0, cy + px * 0.7), "GPS: VERTICAL RATE", px * 0.62, MUTED, "bold", o, 0.08)
        d.line([(ax0, cy), (ax1, cy)], fill=(240, 244, 248, int(230 * o)), width=3)
        sc = (ax1 - ax0) * 0.46 / 12.0                                                                       # px per mm/yr: the +/-9.4 band stays inside the card
        mid = (ax0 + ax1) / 2
        if t >= self.t_band:
            a = o * E.smooth(E.seg(t, self.t_band, self.t_band + 0.7)); d.rectangle([mid - 9.40 * sc, cy - px * 1.4, mid + 9.40 * sc, cy + px * 1.4], fill=(255, 194, 71, int(55 * a)), outline=(255, 194, 71, int(200 * a)), width=2)
            K.draw_text(ctx.ui, (mid + 9.40 * sc, cy - px * 2.6), "± 9.40 MM TYPICAL ERROR (RMSE)", px * 0.62, AMBER, "bold", a, 0.06, "right")
        f = E.out_cubic(E.seg(t, self.t_off, self.t_off + 0.9)); rx = mid + 1.64 * sc * f
        d.line([(rx, cy - px * 2.0), (rx, cy + px * 2.0)], fill=(92, 225, 230, int(255 * o)), width=max(3, int(px * 0.16))); d.line([(mid, cy - px * 1.0), (mid, cy + px * 1.0)], fill=(240, 244, 248, int(255 * o)), width=3)
        K.draw_text(ctx.ui, (rx, cy - px * 3.7), "RADAR (LINE OF SIGHT)" if f > 0.1 else "", px * 0.62, CYAN, "bold", o * f, 0.06, "center")
        if f > 0.8: K.draw_text(ctx.ui, ((mid + rx) / 2 + px * 2.2, cy + px * 1.5), "+1.64 MM/YR", px * 1.2, WHITE, "black", o, 0.02)
        if t >= self.t_caveat:
            a = o * E.smooth(E.seg(t, self.t_caveat, self.t_caveat + 0.6)); K.draw_text(ctx.ui, ((x0 + x1) / 2, y1 - px * 2.4), "STATION AND RADAR PIXEL ARE NOT IN THE SAME SPOT: THE CHECK HAS LIMITS", px * 0.66, AMBER, "heavy", a, 0.05, "center")
        ctx.reg.add("gauge", (x0, y0, x1, y1), o)
    def describe(self): return dict(super().describe(), effect="gps_gauge")


class Compare(Overlay):
    """beat 19 end: two bars on one scale - global sea-level rise vs the worst bowl (vertical, preprint). Values in mm/yr; own graphic of published numbers."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, t0, t1, t_a, t_b, box=(0.06, 0.20, 0.94, 0.70)):
        self.t0, self.t1, self.t_a, self.t_b, self.box = t0, t1, t_a, t_b, box
    def draw(self, ctx):
        t = ctx.t; W, H = ctx.size; o = _a(t, self.t0, self.t1, 0.3, 0.4)
        if o <= 0.01: return
        x0, y0, x1, y1 = self.box[0] * W, self.box[1] * H, self.box[2] * W, self.box[3] * H; px = H * 0.032; panel(ctx, (x0, y0, x1, y1), o, AMBER); d = ImageDraw.Draw(ctx.ui, "RGBA")
        K.draw_text(ctx.ui, (x0 + px * 0.9, y0 + px * 0.5), "MILLIMETERS A YEAR · SAME SCALE", px * 0.8, AMBER, "heavy", o, 0.08)
        bx0 = x0 + px * 0.9; bw = (x1 - px * 4.5) - bx0; sc = bw / 77.0
        rows = [("GLOBAL SEA LEVEL RISE", 3.1, "1993-2018 AVERAGE · SATELLITE ALTIMETRY", CYAN, self.t_a), ("WORST SINKING BOWL (UP TO)", 77.0, "VERTICAL · 2014-2025 · PREPRINT (7.7 CM/YR)", AMBER, self.t_b)]
        for i, (lab, v, src, col, ts) in enumerate(rows):
            yy = y0 + px * 2.3 + i * (y1 - y0 - px * 2.6) / 2; g = E.out_cubic(E.seg(t, ts, ts + 1.0))
            if g <= 0.01: continue
            K.draw_text(ctx.ui, (bx0, yy), lab, px * 0.85, WHITE, "heavy", o * min(1, g * 2), 0.05)
            d.rectangle([bx0, yy + px * 1.3, bx0 + v * sc * g, yy + px * 2.6], fill=tuple(col) + (int(240 * o),)); K.draw_text(ctx.ui, (bx0 + v * sc * g + px * 0.4, yy + px * 1.15), (f"{v:g}" if v < 10 else f"{v:g}"), px * 1.2, WHITE, "black", o * min(1, g * 2))
            K.draw_text(ctx.ui, (bx0, yy + px * 2.8), src, px * 0.5, MUTED, "bold", o * min(1, g * 2), 0.08)
        ctx.reg.add("compare", (x0, y0, x1, y1), o)
    def describe(self): return dict(super().describe(), effect="comparison_bars")


class LosView(Overlay):
    """beat 1: radar line of sight arrives at an angle; a dashed vertical drop is marked 'NOT THIS'. Screen-space illustration anchored on a map point."""
    layer = "ui"; cls = "DECOR"
    def __init__(self, p, t0, t1, t_vert):
        self.p, self.t0, self.t1, self.t_vert = np.asarray(p, float), t0, t1, t_vert
    def draw(self, ctx):
        t = ctx.t; W, H = ctx.size; o = _a(t, self.t0, self.t1)
        if o <= 0.01: return
        c = np.asarray(ctx.view.pt(self.p), float).ravel()[:2]; f = E.out_cubic(E.seg(t, self.t0, self.t0 + 0.8)); top = c + np.array([W * 0.30, -H * 0.55]); s = ctx.stroke(CYAN, 0.8)
        s.line([top, top + (c - top) * f], 4.0 * H / 720, o); px = H * 0.027
        if f > 0.95:
            K.draw_text(ctx.ui, (top[0] - px * 4.5, top[1] + (c[1] - top[1]) * 0.45), "LINE OF SIGHT", px, CYAN, "black", o, 0.08, "right")
            ImageDraw.Draw(ctx.ui, "RGBA").ellipse([c[0] - 9, c[1] - 9, c[0] + 9, c[1] + 9], outline=tuple(AMBER) + (int(255 * o),), width=3)
        if t >= self.t_vert:
            g = E.out_cubic(E.seg(t, self.t_vert, self.t_vert + 0.6)); dd = ImageDraw.Draw(ctx.ui, "RGBA")
            for j in range(10):
                if j / 10 < g: dd.line([(c[0], c[1] - H * 0.42 + j * H * 0.042), (c[0], c[1] - H * 0.42 + j * H * 0.042 + H * 0.022)], fill=(255, 107, 94, int(240 * o)), width=3)
            K.draw_text(ctx.ui, (c[0] + px * 0.5, c[1] - H * 0.42), "NOT THE VERTICAL DROP", px * 0.9, RED, "black", o * g, 0.05)
    def describe(self): return dict(super().describe(), effect="line_of_sight")
