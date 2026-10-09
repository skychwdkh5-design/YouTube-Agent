"""Layer compositing, overlays anchored in source pixels, and the Scene that renders one shot.

Layer classes (metadata only here; enforcement is roadmap R3): EVIDENCE, TRACED, MAP, ILLUSTRATION, TEXT, DECOR.
Overlays draw in SOURCE pixels of the image they sit on, so they move with the camera. An overlay of class TRACED
must say where its geometry came from (`source`) and how it was checked (`validation`); the engine records that
in Scene.manifest() but cannot verify it."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from . import easing as E
from . import text as T
from .camera import Camera, Pyramid, View

SS = 2
CLASSES = ("EVIDENCE", "TRACED", "MAP", "ILLUSTRATION", "TEXT", "DECOR")


# ---------------------------------------------------------------- blending ----
def blend(base, top, mode="normal", opacity=1.0, mask=None):
    """composite RGB/RGBA PIL `top` over RGB `base`. mode: normal|add|multiply|screen. mask: L image or float array 0..1."""
    b = np.asarray(base.convert("RGB"), np.float32) / 255.0
    tp = top.convert("RGBA"); t = np.asarray(tp, np.float32) / 255.0
    a = t[:, :, 3:4] * opacity
    if mask is not None:
        m = np.asarray(mask, np.float32); m = m / 255.0 if m.max() > 1.0 else m
        a = a * m[:, :, None]
    c = t[:, :, :3]
    if mode == "add": c = np.clip(b + c, 0, 1)
    elif mode == "multiply": c = b * c
    elif mode == "screen": c = 1 - (1 - b) * (1 - c)
    elif mode != "normal": raise ValueError(mode)
    out = b * (1 - a) + c * a
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))


class Stroke:
    """RGBA stroke layer drawn at 2x then reduced, initialised with the stroke colour so edges do not darken; optional glow."""
    def __init__(self, size, color):
        self.size = size; self.c = tuple(color)
        self.im = Image.new("RGBA", (size[0] * SS, size[1] * SS), self.c + (0,)); self.d = ImageDraw.Draw(self.im, "RGBA"); self.used = False
    def line(self, pts, width=3.0, alpha=1.0):
        pts = np.asarray(pts, float)
        if len(pts) < 2 or alpha <= 0: return
        W, H = self.size
        if pts[:, 0].max() < -50 or pts[:, 0].min() > W + 50 or pts[:, 1].max() < -50 or pts[:, 1].min() > H + 50: return
        self.d.line([tuple(q) for q in pts * SS], fill=self.c + (int(255 * E.clamp(alpha)),), width=max(1, int(width * SS)), joint="curve"); self.used = True
    def dot(self, p, r=5.0, alpha=1.0):
        x, y = p[0] * SS, p[1] * SS; self.d.ellipse([x - r * SS, y - r * SS, x + r * SS, y + r * SS], fill=self.c + (int(255 * E.clamp(alpha)),)); self.used = True
    def ring(self, p, r, width=2.0, alpha=1.0):
        x, y = p[0] * SS, p[1] * SS; self.d.ellipse([x - r * SS, y - r * SS, x + r * SS, y + r * SS], outline=self.c + (int(255 * E.clamp(alpha)),), width=max(1, int(width * SS))); self.used = True
    def finish(self, glow=0.0, radius=6):
        if not self.used: return None
        small = self.im.reduce(SS)
        if glow > 0:
            g = small.filter(ImageFilter.GaussianBlur(radius)); g.putalpha(g.getchannel("A").point(lambda v: int(min(255, v * glow * 2.2))))
            return Image.alpha_composite(g, small)
        return small


def cumlen(p): return np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(np.asarray(p, float), axis=0).T))])


def partial(p, cum, frac):
    """first `frac` of a polyline by arc length -> (points, head point)."""
    p = np.asarray(p, float)
    if frac >= 1.0: return p, p[-1]
    if frac <= 0.0 or len(p) < 2: return p[:1], p[0]
    L = cum[-1] * frac; i = min(int(np.searchsorted(cum, L, side="right") - 1), len(p) - 2)
    f = (L - cum[i]) / max(cum[i + 1] - cum[i], 1e-9); head = p[i] + (p[i + 1] - p[i]) * f
    return np.vstack([p[:i + 1], head]), head


class Ctx:
    """per-frame drawing context handed to overlays."""
    def __init__(self, size, view, t, theme=T.THEME, reg=None):
        self.size, self.view, self.t, self.theme = size, view, t, theme
        self.reg = reg if reg is not None else T.Registry()
        self.fills = Image.new("RGBA", size, (0, 0, 0, 0))     # world-space tints, drawn under strokes
        self.ui = Image.new("RGBA", size, (0, 0, 0, 0))        # text and plates, never motion-blurred
        self._strokes = {}; self._glow = {}
    def stroke(self, color, glow=0.0):
        k = tuple(color)
        if k not in self._strokes: self._strokes[k] = Stroke(self.size, k)
        self._glow[k] = max(self._glow.get(k, 0.0), glow)
        return self._strokes[k]
    def strokes(self):
        out = []
        for k, s in self._strokes.items():
            im = s.finish(glow=self._glow[k], radius=max(3, self.size[1] // 150))
            if im is not None: out.append(im)
        return out


# ---------------------------------------------------------------- overlays ----
class Overlay:
    """base: `layer` is 'world' (drawn with camera motion blur) or 'ui'. `cls` is the evidence class label."""
    layer = "world"; cls = "DECOR"; source = None; validation = None
    def draw(self, ctx): raise NotImplementedError
    def describe(self): return dict(type=type(self).__name__, cls=self.cls, source=self.source, validation=self.validation)


class DrawOnPolyline(Overlay):
    """line that draws on along arc length between t0 and t0+dur (source px). Optional head dot."""
    cls = "TRACED"
    def __init__(self, points, t0, dur=1.0, color=T.THEME.cyan, width=3.0, glow=1.0, ease="linear", head=True, fade_out=None,
                 closed=False, source=None, validation=None, cls="TRACED"):
        p = np.asarray(points, float); self.pts = np.vstack([p, p[:1]]) if closed else p
        self.cum = cumlen(self.pts); self.t0, self.dur, self.color, self.width, self.glow = t0, dur, color, width, glow
        self.ease, self.head, self.fade_out = E.get(ease), head, fade_out; self.source, self.validation, self.cls = source, validation, cls
    def draw(self, ctx):
        f = self.ease(E.seg(ctx.t, self.t0, self.t0 + self.dur))
        if f <= 0: return
        a = 1.0 if self.fade_out is None else 1 - E.smooth(E.seg(ctx.t, self.fade_out[0], self.fade_out[0] + self.fade_out[1]))
        if a <= 0: return
        pts, head = partial(self.pts, self.cum, f)
        s = ctx.stroke(self.color, self.glow); s.line(ctx.view.pt(pts), self.width * ctx.size[1] / 1080, a)
        if self.head and f < 1.0: s.dot(ctx.view.pt(head), 4.5 * ctx.size[1] / 1080, a)


class PulseMarker(Overlay):
    """anchored marker: ring that pulses, optional label in a plate with a leader line."""
    layer = "ui"; cls = "DECOR"          # ui: ring and plate are not motion-blurred; position still follows the camera
    def __init__(self, p, t0, label=None, color=T.THEME.amber, r=16.0, label_offset=(60, -50), out_t=None, group=None, source=None, validation=None, cls="DECOR"):
        self.p = np.asarray(p, float); self.t0, self.label, self.color, self.r = t0, label, color, r
        self.label_offset, self.out_t, self.group, self.source, self.validation, self.cls = label_offset, out_t, group, source, validation, cls
    def draw(self, ctx):
        k = ctx.size[1] / 1080; a = E.out_cubic(E.seg(ctx.t, self.t0, self.t0 + 0.4))
        if self.out_t is not None: a *= 1 - E.smooth(E.seg(ctx.t, self.out_t, self.out_t + 0.3))
        if a <= 0.003: return
        c = ctx.view.pt(self.p); s = ctx.stroke(self.color, 0.8)
        s.ring(c, self.r * k * (0.6 + 0.4 * E.out_cubic(E.seg(ctx.t, self.t0, self.t0 + 0.4))), 2.4 * k, a)
        ph = ((ctx.t - self.t0) % 1.4) / 1.4
        s.ring(c, self.r * k * (1 + 1.4 * ph), 1.6 * k, a * (1 - ph) * 0.8)
        if self.label:
            e = c + np.array(self.label_offset) * k; s.line([c + np.array(self.label_offset) * k * 0.0, e], 2 * k, a * 0.8)
            T.plate(ctx.ui, tuple(e + [4 * k, -14 * k]), self.label, 24 * k, ctx.t, self.t0 + 0.2, out_t=self.out_t, accent=self.color, reg=ctx.reg, group=self.group or self.label)


class AnchoredText(Overlay):
    """letters rise in; text is attached to a source-pixel point and follows the camera. Size is a cap height in SOURCE px
    clamped to [min_px, max_px] on screen. `angle` lays the text along a direction (e.g. parallel to a line you traced)."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, p, text, size_src, t0, color=T.THEME.text, angle=0.0, track=0.12, per=0.05, dur=0.45, out_t=None, out_dur=0.35,
                 min_px=24, max_px=240, glow=0.0, anchor="center", group=None, follow_rot=True):
        self.p = np.asarray(p, float); self.text, self.size_src, self.t0, self.color = text, size_src, t0, color
        self.angle, self.track, self.per, self.dur, self.out_t, self.out_dur = angle, track, per, dur, out_t, out_dur
        self.min_px, self.max_px, self.glow, self.anchor, self.group, self.follow_rot = min_px, max_px, glow, anchor, group or text, follow_rot
    def draw(self, ctx):
        v = ctx.view; k = ctx.size[1] / 1080
        px = E.clamp(self.size_src * v.k, self.min_px * k, self.max_px * k)
        ang = self.angle - (v.rot if self.follow_rot else 0.0)       # content rotation clockwise => text turns with it
        T.reveal_label(ctx.ui, v.pt(self.p), self.text, px, self.color, ctx.t, self.t0, angle=ang, track=self.track, dur=self.dur, per=self.per,
                       out_t=self.out_t, out_dur=self.out_dur, glow=self.glow, anchor=self.anchor, reg=ctx.reg, group=self.group)


class ScreenText(Overlay):
    """kinetic text fixed to the screen (titles, tickers). Positions are fractions of the frame so the spec is resolution independent."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, xy_frac, text, px_frac, t0, color=T.THEME.text, track=0.1, per=0.05, out_t=None, anchor="left", group=None, bold=True, glow=0.0):
        self.xy, self.text, self.px, self.t0, self.color, self.track, self.per = xy_frac, text, px_frac, t0, color, track, per
        self.out_t, self.anchor, self.group, self.bold = out_t, anchor, group or text, bold
    def draw(self, ctx):
        W, H = ctx.size
        T.kinetic(ctx.ui, (self.xy[0] * W, self.xy[1] * H), self.text, self.px * H, self.color, ctx.t, self.t0, per=self.per, track=self.track,
                  out_t=self.out_t, bold=self.bold, group=self.group, reg=ctx.reg, anchor=self.anchor)


class SourceChip(Overlay):
    """credit/status plate at a screen position (fractions); carries the layer's evidence label."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, xy_frac, text, t0, out_t=None, accent=T.THEME.cyan, px_frac=0.017, anchor="left", group=None):
        self.xy, self.text, self.t0, self.out_t, self.accent, self.px, self.anchor, self.group = xy_frac, text, t0, out_t, accent, px_frac, anchor, group or ("chip:" + text)
    def draw(self, ctx):
        W, H = ctx.size; px = self.px * H; f = T.font(px); w = T.text_width(self.text, f) + px * 1.4 + 8
        x = self.xy[0] * W - (w if self.anchor == "right" else 0)
        T.plate(ctx.ui, (x, self.xy[1] * H), self.text, px, ctx.t, self.t0, out_t=self.out_t, accent=self.accent, reg=ctx.reg, group=self.group)


class YearCounter(Overlay):
    """rolling year/date digits at a fixed screen position; the value changes from `old` to `new` at t0."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, xy_frac, old, new, t0, px_frac=0.11, dur=0.7, color=T.THEME.text, anchor="left", group="counter"):
        self.xy, self.old, self.new, self.t0, self.px, self.dur, self.color, self.anchor, self.group = xy_frac, str(old), str(new), t0, px_frac, dur, color, anchor, group
    def draw(self, ctx):
        W, H = ctx.size; px = self.px * H; f = T.font(px, True); w = (f.getlength("0") + px * 0.04) * len(self.new)
        x = self.xy[0] * W - (w if self.anchor == "right" else 0)
        T.roll(ctx.ui, (x, self.xy[1] * H), self.old, self.new, ctx.t, self.t0, px, dur=self.dur, color=self.color, reg=ctx.reg, group=self.group)


class MaskFill(Overlay):
    """tint inside a source-pixel mask, optionally grown by a radial wipe from a source-pixel anchor between t0 and t0+dur.
    Mask: bool/float array in SOURCE pixels (same size as the image). A UI layer, never evidence: mark it as such on screen."""
    cls = "DECOR"
    def __init__(self, mask, color, t0, dur=0.9, alpha=0.4, anchor=None, max_radius_src=None, feather=0.06, out_t=None, out_dur=0.4, source=None, validation=None, cls="DECOR"):
        m = np.asarray(mask, np.float32); self.pyr = Pyramid(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).convert("RGB"), min_side=128)
        self.color, self.t0, self.dur, self.alpha, self.anchor, self.max_r = color, t0, dur, alpha, anchor, max_radius_src
        self.feather, self.out_t, self.out_dur, self.source, self.validation, self.cls = feather, out_t, out_dur, source, validation, cls
    def draw(self, ctx):
        e = E.smoother(E.seg(ctx.t, self.t0, self.t0 + self.dur))
        a = self.alpha * e
        if self.out_t is not None: a *= 1 - E.smooth(E.seg(ctx.t, self.out_t, self.out_t + self.out_dur))
        if a <= 0.003: return
        m = np.asarray(self.pyr.render(ctx.view, ctx.size).convert("L"), np.float32) / 255.0
        if self.anchor is not None and self.max_r:
            W, H = ctx.size; c = ctx.view.pt(self.anchor); r = self.max_r * ctx.view.k * e; fe = max(8.0, self.feather * H)
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); d = np.hypot(xx - c[0], yy - c[1]); u = np.clip((r - d) / fe, 0, 1)
            m = m * (u * u * (3 - 2 * u))
        ov = Image.new("RGBA", ctx.size, tuple(self.color) + (0,)); ov.putalpha(Image.fromarray((m * a * 255).astype(np.uint8)))
        ctx.fills.alpha_composite(ov)


class Spotlight(Overlay):
    """dim everything outside a soft disc around a source-pixel point (focus cue). Applied to the world image, so it is a UI tint, not evidence."""
    layer = "world"; cls = "DECOR"
    def __init__(self, p, radius_src, t0, t1, strength=0.5, feather=0.2, ramp=0.4):
        self.p, self.r, self.t0, self.t1, self.s, self.f, self.ramp = np.asarray(p, float), radius_src, t0, t1, strength, feather, ramp
    def draw(self, ctx):
        a = E.smooth(E.seg(ctx.t, self.t0, self.t0 + self.ramp)) * (1 - E.smooth(E.seg(ctx.t, self.t1 - self.ramp, self.t1)))
        if a <= 0.003: return
        W, H = ctx.size; c = ctx.view.pt(self.p); r = self.r * ctx.view.k; fe = max(10.0, self.f * H)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); d = np.hypot(xx - c[0], yy - c[1]); u = np.clip((d - r) / fe, 0, 1)
        dim = (u * u * (3 - 2 * u)) * self.s * a
        ov = Image.new("RGBA", ctx.size, (0, 0, 0, 0)); ov.putalpha(Image.fromarray((dim * 255).astype(np.uint8)))
        ctx.fills.alpha_composite(ov)


class Brackets(Overlay):
    """four corner brackets that close around a source-pixel rectangle (focus reticle)."""
    layer = "world"; cls = "DECOR"
    def __init__(self, rect_src, t0, dur=0.8, color=T.THEME.amber, arm=24.0, width=2.0, out_t=None):
        self.rect, self.t0, self.dur, self.color, self.arm, self.width, self.out_t = rect_src, t0, dur, color, arm, width, out_t
    def draw(self, ctx):
        k = ctx.size[1] / 1080; p = E.smoother(E.seg(ctx.t, self.t0, self.t0 + self.dur))
        a = 1.0 if self.out_t is None else 1 - E.smooth(E.seg(ctx.t, self.out_t, self.out_t + 0.3))
        if p <= 0 or a <= 0: return
        (x0, y0), (x1, y1) = ctx.view.pt([self.rect[0:2]])[0], ctx.view.pt([self.rect[2:4]])[0]
        grow = (1 - p) * 40 * k; x0, y0, x1, y1 = x0 - grow, y0 - grow, x1 + grow, y1 + grow; arm = self.arm * k; s = ctx.stroke(self.color, 0.6)
        for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x1, y1, -1, -1), (x0, y1, 1, -1)):
            s.line([(cx + sx * arm, cy), (cx, cy), (cx, cy + sy * arm)], self.width * k, a * min(1.0, p * 3))


# ---------------------------------------------------------------- scene ----
class Scene:
    """one shot: an image seen through a Camera plus overlays.
    render(t) -> PIL RGB. Camera motion blur is temporal sub-sampling when the apparent speed is high.
    `image` may be a PIL image or a path. `reg` collects text boxes for QA."""
    def __init__(self, image, camera_keys=None, size=(1920, 1080), anchors=None, overlays=(), camera_mode="eased", default_ease="smoother",
                 theme=T.THEME, background=None, max_blur_samples=16, blur_threshold=6.0, camera=None, name="scene", clamp=True, overscan=1.0):
        self.name = name; self.size = tuple(size); self.theme = theme
        img = Image.open(image) if isinstance(image, str) else image
        self.pyr = Pyramid(img.convert("RGB")); self.image_size = img.size
        self.camera = camera or Camera(camera_keys, img.size, self.size, anchors, camera_mode, default_ease, clamp=clamp, overscan=overscan)
        self.overlays = list(overlays); self.background = background or theme.ink
        self.max_blur_samples, self.blur_threshold = max_blur_samples, blur_threshold
        self.reg = T.Registry(); self.last_view = None
    @property
    def start(self): return self.camera.ts[0]
    @property
    def end(self): return self.camera.ts[-1]

    def _world(self, t, view):
        img = self.pyr.render(view, self.size, fill=self.background)
        ctx = Ctx(self.size, view, t, self.theme)
        for o in self.overlays:
            if o.layer == "world": o.draw(ctx)
        return img, ctx

    def render(self, t, blur=True, overlays=True):
        view = self.camera.view(t); self.last_view = view
        speed = self.camera.speed(t) if blur else 0.0          # screen px per frame
        # 180-degree shutter: blur length = speed / 2; samples spaced <= 2 px so copies merge into a smooth streak
        n = int(min(self.max_blur_samples, math.ceil(speed * 0.5 / 2.0) + 1)) if speed > self.blur_threshold else 1
        shutter = 0.5 / 30
        acc = None; ctx0 = None
        for i in range(n):
            tt = t + (0 if n == 1 else (i / (n - 1) - 0.5) * shutter)
            v = view if n == 1 else self.camera.view(tt)
            img, ctx = self._world(tt if overlays else t, v) if overlays else (self.pyr.render(v, self.size, fill=self.background), None)
            if overlays:
                base = img.convert("RGBA"); base.alpha_composite(ctx.fills)
                for s in ctx.strokes(): base.alpha_composite(s)
                img = base.convert("RGB")
            a = np.asarray(img, np.float32)
            acc = a if acc is None else acc + a
            if i == (n - 1) // 2: ctx0 = ctx
        frame = Image.fromarray((acc / n + 0.5).astype(np.uint8))
        if overlays:
            self.reg.reset(); uctx = Ctx(self.size, view, t, self.theme, self.reg)
            for o in self.overlays:
                if o.layer == "ui": o.draw(uctx)
            base = frame.convert("RGBA"); base.alpha_composite(uctx.fills)
            for st in uctx.strokes(): base.alpha_composite(st)
            base.alpha_composite(uctx.ui); frame = base.convert("RGB")
        return frame

    def manifest(self):
        return [o.describe() for o in self.overlays]
