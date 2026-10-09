"""Transition library. Every transition takes two ALREADY RENDERED frames (PIL RGB, same size) and a raw progress u in [0, 1],
and returns the composite. Duration and easing are configurable per instance; the Sequence decides when to call it.

All transitions work in screen space on rendered frames. They do not know geography and make no claim that the two
frames are registered to each other (see docs/TRANSITION_DESIGN_SYSTEM.md). Positions are fractions of the frame.

  Dissolve        plain cross-fade (reference baseline; same instrument / time passing only)
  Push            directional camera movement: both frames travel together, optional cover-slide and motion blur (shutter in seconds)
  WhipPan         Push preset with exponential easing and heavy shutter blur
  CinematicPush   2D crash-zoom hand-off about a point (A pushes in, B settles); NOT a 3D flyover
  MaskReveal      B revealed through a mask: linear / radial / custom time-map, feathered edge, optional glow edge
  GeoFocus        spotlight closes on a point of A, then B opens from that point
  ScaleMatch      A is scaled and moved so its subject lands on the subject of B at the same size, then cross-fades
  DateTransition  timeline sweep with rolling date digits (or dissolve) for a change of date/source
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from . import easing as E
from . import text as T


def _arr(im): return np.asarray(im, np.float32)
def _img(a): return Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8))


def warp(im, scale=1.0, src_pt=(0, 0), dst_pt=(0, 0), fill=(0, 0, 0)):
    """similarity warp: the point src_pt of `im` lands on dst_pt in the output, magnified by `scale` (pixels)."""
    s = float(scale)
    return im.transform(im.size, Image.AFFINE, (1 / s, 0, src_pt[0] - dst_pt[0] / s, 0, 1 / s, src_pt[1] - dst_pt[1] / s), resample=Image.BICUBIC, fillcolor=fill)


class Transition:
    name = "transition"; story = ""; limits = ""

    def __init__(self, duration=1.0, ease="smoother", shutter=0.0, samples=8):
        self.duration = float(duration); self.ease_name = ease; self.ease = E.get(ease); self.shutter = shutter; self.samples = samples

    def __call__(self, a, b, u):
        u = E.clamp(u)
        if u <= 0.0: return a
        if u >= 1.0: return b
        if self.shutter > 0:
            ds = np.linspace(-0.5, 0.5, self.samples) * self.shutter / self.duration      # shutter is in SECONDS (1/60 s = 180 degrees at 30 fps)
            acc = sum(_arr(self.core(a, b, self.ease(E.clamp(u + d)))) for d in ds) / len(ds)
            return _img(acc)
        return self.core(a, b, self.ease(u))

    def core(self, a, b, e): raise NotImplementedError

    def describe(self):
        return dict(name=self.name, duration=self.duration, ease=self.ease_name if isinstance(self.ease_name, str) else "custom", shutter=self.shutter, story=self.story, limits=self.limits)


class Dissolve(Transition):
    name = "dissolve"; story = "time passing within one instrument/source"; limits = "never between different instruments/dates as if registered"
    def core(self, a, b, e): return Image.blend(a, b, e)


_DIRS = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}


class Push(Transition):
    """both frames travel in `direction` (content moves that way, like a camera pan the other way).
    a_rate < 1 makes B slide OVER a slower A (cover) with a soft shadow on B's leading edge. shutter > 0 adds directional motion blur."""
    name = "push"; story = "move on to the next place/beat with continuous directional momentum"; limits = "screen-space slide, not a map camera; do not imply geographic adjacency of the frames"
    def __init__(self, direction="left", a_rate=1.0, duration=0.8, ease="in_out_cubic", shutter=0.0, samples=8, shadow=0.45):
        super().__init__(duration, ease, shutter, samples); self.d = _DIRS[direction]; self.a_rate = a_rate; self.shadow = shadow
    def core(self, a, b, e):
        W, H = a.size; dx, dy = self.d
        out = Image.new("RGB", a.size, (0, 0, 0))
        out.paste(a, (int(round(dx * e * W * self.a_rate)), int(round(dy * e * H * self.a_rate))))
        bx, by = int(round(-dx * (1 - e) * W)), int(round(-dy * (1 - e) * H))
        if self.a_rate < 1.0 and self.shadow > 0:
            sh = np.zeros((H, W), np.float32)
            if dx: x = bx + (0 if dx > 0 else W); sh[:, max(0, min(W - 1, x - 1 if dx < 0 else x))] = 1
            if dy: y = by + (0 if dy > 0 else H); sh[max(0, min(H - 1, y - 1 if dy < 0 else y)), :] = 1
            sh = np.asarray(Image.fromarray((sh * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(W * 0.02)), np.float32) / 255.0 * self.shadow * 6
            out = _img(_arr(out) * (1 - np.clip(sh, 0, 0.6))[:, :, None])
        out.paste(b, (bx, by))
        return out


class WhipPan(Push):
    name = "whip_pan"; story = "energy beat / fast relocation (use at most once per video)"; limits = "blur is a post effect; reads as camera whip only with matching sound/rhythm"
    def __init__(self, direction="left", duration=0.45):
        super().__init__(direction, 1.0, duration, "in_out_expo", shutter=0.05, samples=12)


class CinematicPush(Transition):
    """A pushes in about `point` while B settles from a larger scale; radial blur peaks mid-transition; B fades in over `fade`."""
    name = "cinematic_push"; story = "dive into a subject and arrive at the next shot (scale hand-off)"
    limits = "2D scale of rendered frames; not a 3D flyover; contents of A and B are not spatially continuous"
    def __init__(self, point=(0.5, 0.5), a_zoom=2.4, b_zoom=1.6, fade=(0.35, 0.8), blur=0.5, duration=1.0, ease="in_out_cubic", samples=9):
        super().__init__(duration, ease); self.p, self.az, self.bz, self.fade, self.blur, self.n = point, a_zoom, b_zoom, fade, blur, samples
    def _zoomed(self, im, s, strength):
        W, H = im.size; c = (self.p[0] * W, self.p[1] * H)
        if strength <= 0.01: return warp(im, s, c, c)
        acc = sum(_arr(warp(im, s * (1 + strength * d), c, c)) for d in np.linspace(-1, 1, self.n)) / self.n
        return _img(acc)
    def core(self, a, b, e):
        st = self.blur * math.sin(math.pi * e) * 0.35
        A = self._zoomed(a, E.lerp_log(1, self.az, e), st); B = self._zoomed(b, E.lerp_log(self.bz, 1, e), st)
        return Image.blend(A, B, E.smooth(E.seg(e, *self.fade)))


class MaskReveal(Transition):
    """B is revealed where a threshold map θ(x,y) ≤ progress. kind: linear (angle in degrees: 0 = left→right), radial (from `center`),
    or map (your own float array in 0..1: e.g. a coast-distance map, so the reveal sweeps along real geometry).
    feather = soft edge width as a fraction of the sweep; edge_color adds a glowing leading edge."""
    name = "mask_reveal"; story = "reveal the next view through a spatial gesture that has a meaning (direction of travel, point of interest, shape of the thing)"
    limits = "the gesture must be motivated; a linear wipe between two different instruments is a stylistic cut, not registration"
    def __init__(self, kind="linear", angle=0.0, center=(0.5, 0.5), tmap=None, feather=0.12, edge_color=None, edge_width=0.012, duration=1.0, ease="in_out_cubic"):
        super().__init__(duration, ease); self.kind, self.angle, self.center, self.tmap, self.feather = kind, angle, center, tmap, feather
        self.edge_color, self.edge_width = edge_color, edge_width; self._cache = {}
    def theta(self, size):
        if size in self._cache: return self._cache[size]
        W, H = size
        if self.kind == "map":
            m = Image.fromarray((np.clip(np.asarray(self.tmap, np.float32), 0, 1) * 255).astype(np.uint8)).resize(size, Image.BILINEAR); th = np.asarray(m, np.float32) / 255.0
        else:
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            if self.kind == "linear":
                a = math.radians(self.angle); proj = (xx - W / 2) * math.cos(a) + (yy - H / 2) * math.sin(a)
                lim = (abs(W / 2 * math.cos(a)) + abs(H / 2 * math.sin(a))); th = (proj + lim) / (2 * lim)
            elif self.kind == "radial":
                cx, cy = self.center[0] * W, self.center[1] * H; d = np.hypot(xx - cx, yy - cy)
                th = d / max(np.hypot(max(cx, W - cx), max(cy, H - cy)), 1e-6)
            else: raise ValueError(self.kind)
        self._cache[size] = th.astype(np.float32); return self._cache[size]
    def core(self, a, b, e):
        th = self.theta(a.size); f = max(self.feather, 1e-4)
        m = np.clip((e * (1 + f) - th) / f, 0, 1); m = m * m * (3 - 2 * m)
        out = _arr(a) * (1 - m[:, :, None]) + _arr(b) * m[:, :, None]
        if self.edge_color is not None:
            w = max(self.edge_width, 1e-4); d = np.abs(e * (1 + f) - f * 0.5 - th); g = np.clip(1 - d / w, 0, 1) ** 2
            out = out + g[:, :, None] * (np.array(self.edge_color, np.float32) - out) * 0.9
        return _img(out)


class GeoFocus(Transition):
    """phase 1: A pushes toward `focus`, the rest dims and a spotlight closes on it; phase 2: B opens from that point (B settles from `b_zoom`)."""
    name = "geo_focus"; story = "hand attention to the place the next beat is about, then arrive there"
    limits = "focus point is a screen position you must choose; it does not move the camera in the world"
    def __init__(self, focus=(0.5, 0.5), radius=0.17, dim=0.7, a_zoom=1.35, b_zoom=1.3, split=0.5, duration=1.2, ease="in_out_cubic"):
        super().__init__(duration, ease); self.f, self.r, self.dim, self.az, self.bz, self.split = focus, radius, dim, a_zoom, b_zoom, split
    def core(self, a, b, e):
        W, H = a.size; c = (self.f[0] * W, self.f[1] * H); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); d = np.hypot(xx - c[0], yy - c[1])
        far = float(np.hypot(max(c[0], W - c[0]), max(c[1], H - c[1]))); r0 = self.r * H
        p1 = E.smoother(E.seg(e, 0, self.split)); p2 = E.smoother(E.seg(e, self.split, 1))
        A = warp(a, E.lerp_log(1, self.az, p1), c, c)
        R1 = E.lerp(far * 1.1, r0, p1); fe = max(H * 0.08, 1)
        u = np.clip((d - R1) / fe, 0, 1); dimk = 1 - self.dim * p1 * (u * u * (3 - 2 * u))
        Aa = _arr(A) * dimk[:, :, None]
        if e <= self.split: return _img(Aa)
        B = _arr(warp(b, E.lerp_log(self.bz, 1, p2), c, c))
        R2 = E.lerp(r0 * 0.5, far * 1.15, p2); v = np.clip((R2 - d) / (H * 0.1), 0, 1); m = (v * v * (3 - 2 * v))[:, :, None]
        return _img(Aa * (1 - m) + B * m)


class ScaleMatch(Transition):
    """A is magnified and moved so its subject (at `point_a`, apparent size `size_a`) lands on B's subject (`point_b`, `size_b`),
    then the frames cross-fade. Sizes are subject diameters as fractions of frame height, points are frame fractions.
    Honest use: same subject in two shots/dates. Requires the subject to be at rest in B. Check `match_error()` in tests."""
    name = "scale_match"; story = "same subject, new shot/date: the subject stays put while the world around it changes"
    limits = "background of A and B is not registered; subject match is only as good as the points/sizes you pass"
    def __init__(self, point_a, point_b, size_a, size_b, fade=(0.55, 0.92), settle=1.04, duration=1.2, ease="in_out_cubic"):
        super().__init__(duration, ease); self.pa, self.pb, self.sa, self.sb, self.fade, self.settle = point_a, point_b, size_a, size_b, fade, settle
    def a_transform(self, size, e):
        W, H = size; pa = (self.pa[0] * W, self.pa[1] * H); pb = (self.pb[0] * W, self.pb[1] * H)
        s = E.lerp_log(1, self.sb / self.sa, e); q = (E.lerp(pa[0], pb[0], e), E.lerp(pa[1], pb[1], e)); return s, pa, q
    def core(self, a, b, e):
        W, H = a.size; s, pa, q = self.a_transform(a.size, e); A = warp(a, s, pa, q)
        pb = (self.pb[0] * W, self.pb[1] * H); B = warp(b, E.lerp(self.settle, 1.0, e), pb, pb)
        return Image.blend(A, B, E.smooth(E.seg(e, *self.fade)))
    def match_error(self, size=(1920, 1080)):
        """screen-pixel error between A's subject centre and B's at the end of the transform, and size ratio error."""
        W, H = size; s, pa, q = self.a_transform(size, 1.0); pb = (self.pb[0] * W, self.pb[1] * H)
        return float(np.hypot(q[0] - pb[0], q[1] - pb[1])), abs(self.sa * s / self.sb - 1)


class DateTransition(Transition):
    """change of date/source on a timeline. mode 'sweep': a scrub line moves left→right revealing B behind it while digits roll
    `old`→`new` and a thin timeline bar marks progress; mode 'dissolve': digits roll over a cross-fade (same-instrument only)."""
    name = "date_transition"; story = "time (or source) changes; the viewer is told when, and sees the change happen"
    limits = "sweep is an editorial device; it does not register A to B. Digits are labels you supply; the engine does not verify dates"
    def __init__(self, old, new, mode="sweep", pos=(0.93, 0.07), px_frac=0.11, color=T.THEME.text, line_color=T.THEME.cyan, theme=T.THEME, duration=1.2, ease="in_out_cubic", anchor="right"):
        super().__init__(duration, ease); self.old, self.new, self.mode, self.pos, self.px, self.color, self.line_color, self.anchor = str(old), str(new), mode, pos, px_frac, color, line_color, anchor
    def core(self, a, b, e):
        W, H = a.size
        if self.mode == "dissolve": base = Image.blend(a, b, e)
        else:
            x = int(round(e * W)); base = a.copy(); 
            if x > 0: base.paste(b.crop((0, 0, x, H)), (0, 0))
        lay = Image.new("RGBA", a.size, (0, 0, 0, 0)); px = self.px * H; f = T.font(px, True); w = (f.getlength("0") + px * 0.04) * len(self.new)
        xy = (self.pos[0] * W - (w if self.anchor == "right" else 0), self.pos[1] * H)
        T.roll(lay, xy, self.old, self.new, E.seg(e, 0.12, 0.88) * 0.9, 0.0, px, dur=0.7, color=self.color)
        d = ImageDraw.Draw(lay, "RGBA")
        by = int(H * 0.96); d.line([(W * 0.05, by), (W * 0.95, by)], fill=(255, 255, 255, 70), width=max(1, H // 360))
        for i in range(11):
            tx = W * 0.05 + W * 0.9 * i / 10; d.line([(tx, by - H * 0.006), (tx, by + H * 0.006)], fill=(255, 255, 255, 110), width=max(1, H // 540))
        mx = W * 0.05 + W * 0.9 * e; d.ellipse([mx - H * 0.008, by - H * 0.008, mx + H * 0.008, by + H * 0.008], fill=tuple(self.line_color) + (255,))
        if self.mode == "sweep":
            lx = e * W; d.line([(lx, 0), (lx, H)], fill=tuple(self.line_color) + (210,), width=max(2, H // 270))
            g = lay.filter(ImageFilter.GaussianBlur(H * 0.006)); lay = Image.alpha_composite(g, lay)
        out = base.convert("RGBA"); out.alpha_composite(lay); return out.convert("RGB")


REGISTRY = {c.name: c for c in (Dissolve, Push, WhipPan, CinematicPush, MaskReveal, GeoFocus, ScaleMatch, DateTransition)}


def from_spec(d):
    """build a transition from a dict: {"type": "push", "direction": "left", "duration": 0.8, ...}"""
    d = dict(d); name = d.pop("type")
    if name not in REGISTRY: raise ValueError(f"unknown transition {name!r}; known: {sorted(REGISTRY)}")
    return REGISTRY[name](**d)
