"""Motion-graphics overlays (VISUAL_REF_002 techniques adapted to the OrbitalAtlas palette) and georeferenced highlight/route overlays (VISUAL_REF_001).

Screen-space (layer 'ui', never camera-blurred): NeonGrid, LightSweep, Particles, HudFrame, Waveform, MarkerPin.
World-space (follow the camera, class MAP/TRACED): RegionTint (mask highlight with flash, glow outline and draw-on), RouteArrow (curved arrow with head and
animated distance label), CometTrail.

Honesty rules baked in: a RegionTint/RouteArrow is an ANNOTATION layer (`cls` MAP or TRACED, with `source` and `validation` text) and never alters the picture
underneath; grading lives in `grade`. Decorative layers say so (`cls='DECOR'`). All randomness is seeded, so frames are reproducible."""
# effect-reuse-checked: orbitalatlas.layers has DrawOnPolyline/PulseMarker/MaskFill/Brackets (kept and reused for strokes); the Dubai engine's fx.trail is episode code.
# New here: tinted-region flash + glow outline from a mask, curved arrow with head and label, perspective neon grid, light sweep, seeded particles, waveform, HUD frame, pin drop.
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from . import easing as E
from . import kinetic as K
from .layers import Overlay, cumlen, partial

PURPLE = (124, 77, 255)
AMBER = (255, 194, 71)
CYAN = (92, 225, 230)
WHITE = (255, 255, 255)


def bezier(p0, p1, bend=0.25, n=48):
    """quadratic Bezier between two points, bent sideways by `bend` x length (positive = to the left of the direction of travel)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); d = p1 - p0; nrm = np.array([-d[1], d[0]])
    c = (p0 + p1) / 2 + nrm * bend; t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t ** 2 * p1


# ---------------------------------------------------------------------------------------------------- screen-space
class NeonGrid(Overlay):
    """perspective floor grid + optional flat grid, fading in/out, scrolling towards the camera (REF_002 'perspective grids', 'animated grids')."""
    layer = "ui"; cls = "DECOR"
    def __init__(self, t0, t1, color=PURPLE, alpha=0.5, horizon=0.42, flat=False, spacing=0.07, speed=0.12, fade=0.5):
        self.t0, self.t1, self.color, self.alpha, self.horizon, self.flat, self.spacing, self.speed, self.fade = t0, t1, color, alpha, horizon, flat, spacing, speed, fade
    def draw(self, ctx):
        t = ctx.t; a = self.alpha * E.smooth(E.seg(t, self.t0, self.t0 + self.fade)) * (1 - E.smooth(E.seg(t, self.t1 - self.fade, self.t1)))
        if a <= 0.01: return
        W, H = ctx.size; layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer, "RGBA"); c = self.color + (int(255 * a),)
        if self.flat:
            sp = self.spacing * H
            for x in np.arange(-(t * self.speed * H) % sp, W, sp): d.line([(x, 0), (x, H)], fill=c, width=1)
            for y in np.arange(0, H, sp): d.line([(0, y), (W, y)], fill=c, width=1)
        else:
            hy = self.horizon * H
            for k in range(-14, 15): d.line([(W / 2 + k * W * 0.02, hy), (W / 2 + k * W * 0.2, H)], fill=c, width=1)
            ph = (t * self.speed) % 1.0
            for j in range(14):
                z = ((j + ph) / 14) ** 2.2; y = hy + (H - hy) * z; d.line([(0, y), (W, y)], fill=self.color + (int(255 * a * (0.25 + 0.75 * z)),), width=1)
        ctx.ui.alpha_composite(K.glow(layer, max(3, H / 180), 0.7))
    def describe(self): return dict(super().describe(), effect="neon_grid", flat=self.flat)


class LightSweep(Overlay):
    """soft diagonal light bar crossing the frame once (REF_002 'light sweeps'); an accent, not a wipe: alpha stays low."""
    layer = "ui"; cls = "DECOR"
    def __init__(self, t0, dur=0.9, color=WHITE, strength=0.22, angle=18.0, band=0.12):
        self.t0, self.dur, self.color, self.strength, self.angle, self.band = t0, dur, color, strength, angle, band
    def draw(self, ctx):
        u = E.in_out_cubic(E.seg(ctx.t, self.t0, self.t0 + self.dur))
        if u <= 0 or u >= 1: return
        W, H = ctx.size; th = math.radians(self.angle); yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
        d = (xx - W * (-0.2 + 1.4 * u)) * math.cos(th) + (yy - H / 2) * math.sin(th); sig = self.band * W
        a = np.exp(-(d / sig) ** 2) * self.strength * 255
        rgba = np.zeros(a.shape + (4,), np.uint8); rgba[..., 0], rgba[..., 1], rgba[..., 2], rgba[..., 3] = self.color[0], self.color[1], self.color[2], a.astype(np.uint8)
        im = Image.fromarray(rgba, "RGBA")
        ctx.ui.alpha_composite(im.resize((W, H), Image.BILINEAR))
    def describe(self): return dict(super().describe(), effect="light_sweep")


class Particles(Overlay):
    """seeded drifting motes with twinkle (REF_002 'moving particles'): count and alpha stay low; position is a pure function of time."""
    layer = "ui"; cls = "DECOR"
    def __init__(self, t0, t1, n=70, seed=7, color=(200, 220, 255), alpha=0.55, drift=(0.012, -0.02), size=2.2):
        r = np.random.RandomState(seed); self.p = r.rand(n, 2); self.ph = r.rand(n) * 6.28; self.sp = 0.5 + r.rand(n); self.sz = 0.5 + r.rand(n)
        self.t0, self.t1, self.color, self.alpha, self.drift, self.size = t0, t1, color, alpha, drift, size
    def draw(self, ctx):
        t = ctx.t; a0 = E.smooth(E.seg(t, self.t0, self.t0 + 0.6)) * (1 - E.smooth(E.seg(t, self.t1 - 0.6, self.t1))) * self.alpha
        if a0 <= 0.01: return
        W, H = ctx.size; layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer, "RGBA"); k = H / 1080
        for (x, y), ph, sp, sz in zip(self.p, self.ph, self.sp, self.sz):
            px = ((x + self.drift[0] * sp * t) % 1.0) * W; py = ((y + self.drift[1] * sp * t) % 1.0) * H
            tw = 0.5 + 0.5 * math.sin(t * 2.0 * sp + ph); r = self.size * sz * k * (0.7 + 0.5 * tw)
            d.ellipse([px - r, py - r, px + r, py + r], fill=self.color + (int(255 * a0 * (0.35 + 0.65 * tw)),))
        ctx.ui.alpha_composite(K.glow(layer, 3 * k, 0.6))
    def describe(self): return dict(super().describe(), effect="particles")


class HudFrame(Overlay):
    """corner brackets and a thin frame that draw on, with an optional small caption: a scientific-instrument look for data views (use sparingly)."""
    layer = "ui"; cls = "DECOR"
    def __init__(self, box, t0, t1=None, color=CYAN, label=None, dur=0.6, size=0.03):
        self.box, self.t0, self.t1, self.color, self.label, self.dur, self.size = box, t0, t1, color, label, dur, size
    def draw(self, ctx):
        t = ctx.t; u = E.out_cubic(E.seg(t, self.t0, self.t0 + self.dur)); o = 1 - (E.smooth(E.seg(t, self.t1, self.t1 + 0.3)) if self.t1 else 0)
        if u <= 0 or o <= 0: return
        W, H = ctx.size; x0, y0, x1, y1 = self.box[0] * W, self.box[1] * H, self.box[2] * W, self.box[3] * H; s = self.size * H; k = H / 1080
        st = ctx.stroke(self.color, 0.7); a = o
        for (cx, cy, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x1, y1, -1, -1), (x0, y1, 1, -1)):
            st.line([(cx + dx * s * u, cy), (cx, cy), (cx, cy + dy * s * u)], 3 * k, a)
        st.line([(x0, y0), (x0 + (x1 - x0) * u, y0)], 1.2 * k, a * 0.5)
        if self.label:
            b = K.draw_text(ctx.ui, (x0, y0 - 28 * k), self.label, 16 * k, self.color, "bold", u * o, track=0.14)
            if b: ctx.reg.add("hud", b, u * o)
    def describe(self): return dict(super().describe(), effect="hud_frame")


class Waveform(Overlay):
    """audio-style bars. `samples` = real audio amplitude per bar column (0..1 array, e.g. from the narration) or None for the DECORATIVE envelope
    (seeded noise shaped by `energy(t)`); the manifest records which one was used so a decoration is never presented as measured audio."""
    layer = "ui"; cls = "DECOR"
    def __init__(self, box, t0, t1, samples=None, color=PURPLE, seed=3, energy=None, fps=30.0, bars=64):
        self.box, self.t0, self.t1, self.color, self.fps, self.bars = box, t0, t1, color, fps, bars
        self.samples = None if samples is None else np.asarray(samples, np.float32); self.energy = energy
        self.noise = np.random.RandomState(seed).rand(2048, bars).astype(np.float32)
    def level(self, t):
        if self.samples is not None:
            i = int(max(0, (t - self.t0)) * self.fps); i = min(i, len(self.samples) - 1); return float(self.samples[i])
        return float(self.energy(t)) if self.energy else 0.55
    def draw(self, ctx):
        t = ctx.t; u = E.smooth(E.seg(t, self.t0, self.t0 + 0.4)) * (1 - E.smooth(E.seg(t, self.t1 - 0.3, self.t1)))
        if u <= 0.01: return
        W, H = ctx.size; x0, y0, x1, y1 = self.box[0] * W, self.box[1] * H, self.box[2] * W, self.box[3] * H
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer, "RGBA"); lv = self.level(t); n = self.bars; bw = (x1 - x0) / n
        row = self.noise[int(t * 24) % len(self.noise)]; mid = (y0 + y1) / 2
        for i in range(n):
            env = math.sin(math.pi * (i + 0.5) / n) ** 0.6; hgt = (y1 - y0) / 2 * (0.08 + 0.92 * lv * env * (0.35 + 0.65 * row[i])) * u
            d.rectangle([x0 + i * bw + bw * 0.2, mid - hgt, x0 + (i + 1) * bw - bw * 0.2, mid + hgt], fill=self.color + (int(255 * u),))
        ctx.ui.alpha_composite(K.glow(layer, max(3, H / 200), 0.8))
    def describe(self): return dict(super().describe(), effect="waveform", data="measured" if self.samples is not None else "decorative envelope")


class MarkerPin(Overlay):
    """map pin that drops with a bounce and settles; anchored to a SOURCE point so it follows the camera (VE-09)."""
    layer = "ui"; cls = "MAP"
    def __init__(self, p, t0, color=(235, 64, 52), label=None, out_t=None, source=None, validation=None, group=None):
        self.p = np.asarray(p, float); self.t0, self.color, self.label, self.out_t, self.source, self.validation, self.group = t0, color, label, out_t, source, validation, group
    def draw(self, ctx):
        k = ctx.size[1] / 1080; t = ctx.t; u = E.seg(t, self.t0, self.t0 + 0.45)
        if u <= 0: return
        o = 1 - (E.smooth(E.seg(t, self.out_t, self.out_t + 0.3)) if self.out_t else 0)
        if o <= 0.01: return
        c = ctx.view.pt(self.p); drop = (1 - E.out_back(u, 1.9)) * -120 * k if u < 1 else 0.0; x, y = c[0], c[1] + drop
        d = ImageDraw.Draw(ctx.ui, "RGBA"); r = 13 * k; a = int(255 * min(1, u * 3) * o)
        d.polygon([(x - r * 0.8, y - r * 1.1), (x + r * 0.8, y - r * 1.1), (x, y)], fill=self.color + (a,)); d.ellipse([x - r, y - r * 2.3, x + r, y - r * 0.3], fill=self.color + (a,))
        d.ellipse([x - r * 0.38, y - r * 1.65, x + r * 0.38, y - r * 0.95], fill=(255, 255, 255, a))
        if u >= 1 and drop == 0.0:
            ring = E.seg(t, self.t0 + 0.45, self.t0 + 1.0); st = ctx.stroke(self.color, 0.6); st.ring(c, r * (0.6 + 2.2 * ring), 2 * k, (1 - ring) * o)
        if self.label:
            b = K.draw_text(ctx.ui, (x + r * 1.6, y - r * 2.4), self.label, 21 * k, WHITE, "bold", min(1, u * 2) * o, shadow=0.08, stroke=max(1, int(1.2 * k)))
            if b: ctx.reg.add(self.group or self.label, b, min(1, u * 2) * o)
    def describe(self): return dict(super().describe(), effect="marker_pin", source=self.source, validation=self.validation)


# ------------------------------------------------------------------------------------------------------ world-space
class RegionTint(Overlay):
    """highlight a region given as a MASK in source pixels ('L' image, same size as the picture, or a lower-resolution one + `mask_scale`).
    Phases: flash (t0, strong tint) -> settle (translucent) with a glowing outline that draws on left->right (or radial) -> optional fade out.
    Annotation only: the picture is never recoloured; `source`/`validation` must say where the mask came from (e.g. 'water threshold, traced by tools/...')."""
    layer = "world"; cls = "TRACED"
    def __init__(self, mask, t0, color=AMBER, flash=(255, 64, 48), settle_alpha=0.30, dur=0.8, out_t=None, mask_scale=1.0, outline=True, source=None, validation=None, cls="TRACED"):
        self.mask = mask.convert("L") if isinstance(mask, Image.Image) else Image.fromarray(np.asarray(mask, np.uint8))
        self.t0, self.color, self.flash, self.settle, self.dur, self.out_t, self.ms, self.outline = t0, color, flash, settle_alpha, dur, out_t, mask_scale, outline
        self.source, self.validation, self.cls = source, validation, cls
    def draw(self, ctx):
        t = ctx.t; u = E.seg(t, self.t0, self.t0 + self.dur)
        if u <= 0: return
        o = 1 - (E.smooth(E.seg(t, self.out_t, self.out_t + 0.4)) if self.out_t else 0)
        if o <= 0.01: return
        view = ctx.view; k = ctx.size[1] / 1080
        m = self.mask.transform(ctx.size, Image.AFFINE, view.affine(1.0 * self.ms), resample=Image.BILINEAR, fillcolor=0)
        arr = np.asarray(m, np.float32) / 255.0
        if not arr.any(): return
        fl = max(0.0, 1 - E.seg(t, self.t0, self.t0 + 0.22) * 1.0) if u < 1 or True else 0.0
        a = (self.settle + (0.55 - self.settle) * fl) * E.smooth(E.seg(t, self.t0, self.t0 + 0.12)) * o
        col = np.array(self.color, np.float32) * (1 - fl) + np.array(self.flash, np.float32) * fl
        fill = np.zeros(arr.shape + (4,), np.float32); fill[..., :3] = col; fill[..., 3] = arr * a * 255
        ctx.fills.alpha_composite(Image.fromarray(fill.astype(np.uint8), "RGBA"))
        if self.outline:
            edge = np.clip(np.asarray(m.filter(ImageFilter.MaxFilter(5)), np.float32) - np.asarray(m.filter(ImageFilter.MinFilter(5)), np.float32), 0, 255) / 255.0
            reveal = E.out_cubic(E.seg(t, self.t0 + 0.05, self.t0 + self.dur)); W = ctx.size[0]
            xs = np.arange(W, dtype=np.float32)[None, :]; cols = np.asarray(m, np.float32).any(axis=0); xr = np.where(cols)[0]
            x_a, x_b = (xr.min(), xr.max()) if len(xr) else (0, W)
            gate = np.clip((x_a + (x_b - x_a + 1) * reveal - xs) / (0.04 * W) + 0.0, 0, 1)
            ed = Image.fromarray((edge * gate * 255 * o).astype(np.uint8), "L")
            ring = Image.new("RGBA", ctx.size, tuple(self.color) + (0,)); ring.putalpha(ed)
            glow = ring.filter(ImageFilter.GaussianBlur(max(3, 5 * k))); ga = glow.getchannel("A").point(lambda v: int(min(255, v * 2.4))); glow.putalpha(ga)
            ctx.fills.alpha_composite(glow); ctx.fills.alpha_composite(ring)
    def describe(self): return dict(super().describe(), effect="region_tint", annotation_only=True)


class RouteArrow(Overlay):
    """curved route arrow between two source points with an arrow head and an animated label (distance, name...). Path draws on, head follows, label pops
    once the arrow has travelled. The route is a presentation curve between two verified anchors, NOT a measured track: say so in `validation`."""
    layer = "world"; cls = "MAP"
    def __init__(self, p0, p1, t0, dur=1.0, bend=0.22, label=None, color=WHITE, head_color=AMBER, width=7.0, out_t=None, source=None, validation=None, group=None, cls="MAP"):
        self.pts = bezier(p0, p1, bend); self.cum = cumlen(self.pts); self.t0, self.dur, self.label = t0, dur, label
        self.color, self.head_color, self.width, self.out_t, self.source, self.validation, self.group, self.cls = color, head_color, width, out_t, source, validation, group, cls
    def draw(self, ctx):
        t = ctx.t; f = E.in_out_cubic(E.seg(t, self.t0, self.t0 + self.dur))
        if f <= 0: return
        o = 1 - (E.smooth(E.seg(t, self.out_t, self.out_t + 0.35)) if self.out_t else 0)
        if o <= 0.01: return
        k = ctx.size[1] / 1080; pts, head = partial(self.pts, self.cum, f); sp = ctx.view.pt(pts)
        ctx.stroke(self.color, 0.5).line(sp, self.width * k, o)
        if len(sp) >= 2:
            tv = sp[-1] - sp[max(0, len(sp) - 4)]; n = np.hypot(*tv) or 1.0; tv = tv / n; nv = np.array([-tv[1], tv[0]]); L = 34 * k; Wd = 24 * k; h = sp[-1]
            tri = [tuple(h + tv * L * 0.6), tuple(h - tv * L * 0.4 + nv * Wd * 0.6), tuple(h - tv * L * 0.4 - nv * Wd * 0.6)]
            ImageDraw.Draw(ctx.fills, "RGBA").polygon(tri, fill=self.head_color + (int(255 * o),))
    def label_pos(self, ctx):
        return ctx.view.pt(self.pts[len(self.pts) // 2])
    def describe(self): return dict(super().describe(), effect="route_arrow", label=self.label, presentation_curve=True)


class RouteLabel(Overlay):
    """the label of a RouteArrow as a UI overlay that follows the camera: 2.5D tilt settling into place, then holding."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, arrow, t0, px=64, color=WHITE, out_t=None):
        self.arrow, self.t0, self.px, self.color, self.out_t = arrow, t0, px, color, out_t
    def draw(self, ctx):
        o = 1 - (E.smooth(E.seg(ctx.t, self.out_t, self.out_t + 0.3)) if self.out_t else 0)
        if o <= 0.01: return
        k = ctx.size[1] / 1080; c = self.arrow.label_pos(ctx)
        K.tilt_25d(ctx.ui, (c[0], c[1] - 46 * k), self.arrow.label, self.px * k, ctx.t, self.t0, color=self.color, reg=ctx.reg, group=f"route_{self.arrow.label}", blur=0.03)
    def describe(self): return dict(super().describe(), effect="route_label")


class CometTrail(Overlay):
    """bright head moving along a path with a fading tail (REF_002 'text trails' for objects)."""
    layer = "world"; cls = "DECOR"
    def __init__(self, pts, t0, dur=1.2, color=PURPLE, tail=0.35, width=5.0, ease="in_out_cubic"):
        self.pts = np.asarray(pts, float); self.cum = cumlen(self.pts); self.t0, self.dur, self.color, self.tail, self.width = t0, dur, color, tail, width
    def draw(self, ctx):
        f = E.in_out_cubic(E.seg(ctx.t, self.t0, self.t0 + self.dur))
        if f <= 0: return
        k = ctx.size[1] / 1080; st = ctx.stroke(self.color, 1.0)
        n = 14
        for i in range(n):
            a = max(0.0, f - self.tail * (i + 1) / n); b = max(0.0, f - self.tail * i / n)
            if b <= a: continue
            p0, _ = partial(self.pts, self.cum, b); seg = ctx.view.pt(p0[-max(2, int(len(p0) * (1 - a / b if b else 1)) + 1):])
            st.line(seg, self.width * k * (1 - i / n), 1 - i / n)
        _, head = partial(self.pts, self.cum, f); st.dot(ctx.view.pt(head), self.width * 1.3 * k, 1.0)
    def describe(self): return dict(super().describe(), effect="comet_trail")
