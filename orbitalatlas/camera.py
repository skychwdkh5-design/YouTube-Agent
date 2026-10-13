"""Image-space camera (class A): a rotated, scaled crop window over the pixels of ONE image.

Coordinates: SOURCE pixels (x right, y down, origin top-left of the image); SCREEN pixels (output frame).
`View` converts between them. `Camera` produces a View for any time from keyframes.
Rotation is in degrees, positive = content rotates clockwise on screen.
This is not georeferenced and not 3D; do not describe its output as a flyover."""
import math
import numpy as np
from PIL import Image
from . import easing as E

Image.MAX_IMAGE_PIXELS = None


class View:
    def __init__(self, center, height, rot, screen):
        self.c = np.array(center, float); self.h = float(height); self.rot = float(rot)
        self.W, self.H = screen
        self.k = self.H / self.h                      # screen px per source px
        th = math.radians(self.rot)
        self.R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])

    @property
    def width(self): return self.h * self.W / self.H

    def pt(self, p):
        """source -> screen (accepts one point or an (n,2) array)."""
        d = (np.asarray(p, float) - self.c) @ self.R.T
        return d * self.k + np.array([self.W / 2, self.H / 2])

    def inv(self, s):
        """screen -> source."""
        d = (np.asarray(s, float) - np.array([self.W / 2, self.H / 2])) / self.k
        return d @ self.R + self.c

    pts = pt

    def corners(self):
        """source-space corners of the visible window."""
        return self.inv([[0, 0], [self.W, 0], [self.W, self.H], [0, self.H]])

    def extent(self):
        """axis-aligned source bounding box (x0,y0,x1,y1) of the visible window."""
        c = self.corners()
        return (*c.min(axis=0), *c.max(axis=0))

    def on_screen(self, p, margin=0.0):
        s = self.pt(p)
        return bool(margin <= s[0] <= self.W - margin and margin <= s[1] <= self.H - margin)

    def affine(self, level_scale=1.0):
        """PIL AFFINE coefficients mapping OUTPUT pixels to a source image scaled by `level_scale`."""
        M = self.R.T / self.k * level_scale          # screen offset -> source offset (scaled)
        c = self.c * level_scale
        cx = c[0] - M[0, 0] * self.W / 2 - M[0, 1] * self.H / 2
        cy = c[1] - M[1, 0] * self.W / 2 - M[1, 1] * self.H / 2
        return (M[0, 0], M[0, 1], cx, M[1, 0], M[1, 1], cy)


class Pyramid:
    """power-of-two image pyramid so down-scaled views are sampled from a nearby level (anti-aliasing)."""
    def __init__(self, img, min_side=256):
        self.size = img.size
        self.levels = [(1.0, img.convert("RGB"))]
        while min(self.levels[-1][1].size) // 2 >= min_side:
            f, im = self.levels[-1]
            self.levels.append((f / 2, im.resize((max(1, im.width // 2), max(1, im.height // 2)), Image.LANCZOS)))

    def level_for(self, k):
        """coarsest level whose scale is still >= k (screen px per source px) / 1.0 -> never upsampled from a coarser level."""
        for f, im in reversed(self.levels):
            if f >= k * 0.999: return f, im
        return self.levels[0]

    def render(self, view, size=None, fill=(0, 0, 0)):
        """render the view -> (RGB image, coverage fraction 0..1: share of output pixels that came from inside the image)."""
        size = size or (view.W, view.H)
        f, im = self.level_for(view.k)
        coeff = view.affine(f)
        out = im.transform(size, Image.AFFINE, coeff, resample=Image.BICUBIC, fillcolor=fill)
        return out

    def coverage(self, view):
        """fraction of the screen inside the source image (exact for rotated rectangles via sampling a coarse grid)."""
        xs, ys = np.meshgrid(np.linspace(0, view.W, 17), np.linspace(0, view.H, 9))
        p = view.inv(np.stack([xs.ravel(), ys.ravel()], 1))
        ok = (p[:, 0] >= 0) & (p[:, 0] <= self.size[0]) & (p[:, 1] >= 0) & (p[:, 1] <= self.size[1])
        return float(ok.mean())


def fit(points, screen, margin=0.1, rot=0.0, min_height=1.0):
    """smallest centred view (center, height) that keeps every source point inside the safe rectangle
    `margin` (fraction of each screen side) away from the edges. Returns (center, height)."""
    pts = np.asarray(points, float)
    W, H = screen
    th = math.radians(rot)
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    q = pts @ R.T                                   # rotated into screen axes (unscaled)
    lo, hi = q.min(axis=0), q.max(axis=0)
    mid = (lo + hi) / 2
    need_h = max((hi[1] - lo[1]) / (1 - 2 * margin), (hi[0] - lo[0]) / (1 - 2 * margin) * H / W, min_height)
    return mid @ R, need_h                          # R orthonormal: R.T inverse of R.T is R


class Camera:
    """keyframed image-space camera.

    keys: list of dicts, sorted by t:
      t       seconds
      center  (x, y) in source px   -or-   anchor: name in `anchors` (+ optional offset (dx, dy) in source px)
      height  source px visible vertically (smaller = closer)
      rot     degrees (default 0)
      at      (fx, fy) where the anchor/center lands on screen as a fraction (default (0.5, 0.5)); lets you
              compose off-centre (rule of thirds) while still tracking the subject
      ease    easing from this key to the next (mode 'eased' only; default `default_ease`)
    mode: 'eased'  -> each segment eased with its own curve, rest at every key (deliberate beats)
          'spline' -> monotone cubic through all keys, continuous velocity, no stops at interior keys (flowing path)
    track: optional (fn(t)->(x,y), lag_seconds): overrides the centre by following a moving subject with a delay.
    Heights are interpolated in log space. `clamp` keeps the window inside the image (exact for rotation)."""

    def __init__(self, keys, image_size, screen=(1920, 1080), anchors=None, mode="eased", default_ease="smoother",
                 clamp=True, track=None, overscan=1.0):
        assert mode in ("eased", "spline")
        self.size = tuple(image_size); self.screen = tuple(screen); self.anchors = {k: np.array(v, float) for k, v in (anchors or {}).items()}
        self.mode, self.default_ease, self.clamp_on, self.track, self.overscan = mode, E.get(default_ease), clamp, track, overscan
        self.keys = sorted(keys, key=lambda k: k["t"])
        if len(self.keys) < 1: raise ValueError("camera needs at least one key")
        self._resolved = [self._resolve(k) for k in self.keys]       # (t, cx, cy, log h, rot)
        self.ts = [r[0] for r in self._resolved]
        if mode == "spline" and len(self.keys) > 1:
            self._ys = [[r[i] for r in self._resolved] for i in (1, 2, 3, 4)]
            self._ms = [E.pchip_slopes(self.ts, y) for y in self._ys]
        self._ease = [E.get(k.get("ease", default_ease)) for k in self.keys]

    # -- key resolution: place the anchor at `at` on screen for the key's own height/rotation
    def _resolve(self, k):
        h = float(k["height"]); rot = float(k.get("rot", 0.0))
        if "anchor" in k:
            if k["anchor"] not in self.anchors: raise KeyError(f"unknown anchor {k['anchor']!r}")
            p = self.anchors[k["anchor"]] + np.array(k.get("offset", (0, 0)), float)
        else:
            p = np.array(k["center"], float)
        fx, fy = k.get("at", (0.5, 0.5))
        if (fx, fy) != (0.5, 0.5):
            v = View(p, h, rot, self.screen)
            off = (np.array([fx * v.W, fy * v.H]) - np.array([v.W / 2, v.H / 2])) / v.k
            p = p - off @ v.R                                         # shift centre so p appears at (fx, fy)
        return (float(k["t"]), float(p[0]), float(p[1]), math.log(h), rot)

    def _raw(self, t):
        r = self._resolved
        if len(r) == 1 or t <= r[0][0]: return r[0][1:]
        if t >= r[-1][0]: return r[-1][1:]
        if self.mode == "spline":
            return tuple(E.hermite(t, self.ts, y, m) for y, m in zip(self._ys, self._ms))
        i = max(j for j in range(len(r) - 1) if r[j][0] <= t)
        a, b = r[i], r[i + 1]
        e = self._ease[i](E.seg(t, a[0], b[0]))
        return tuple(E.lerp(x, y, e) for x, y in zip(a[1:], b[1:]))

    def view(self, t):
        cx, cy, lh, rot = self._raw(t)
        if self.track is not None:
            fn, lag = self.track
            cx, cy = fn(t - lag)
        h = math.exp(lh)
        v = View((cx, cy), h, rot, self.screen)
        return self.constrain(v) if self.clamp_on else v

    def constrain(self, v):
        """keep the rotated window inside the image (reduces height first, then shifts the centre)."""
        W0, H0 = self.size[0] * self.overscan, self.size[1] * self.overscan
        th = math.radians(v.rot); c, s = abs(math.cos(th)), abs(math.sin(th))
        def half(h):
            w = h * v.W / v.H
            return (c * w + s * h) / 2, (s * w + c * h) / 2
        hx, hy = half(v.h)
        h = v.h
        if 2 * hx > W0 or 2 * hy > H0:
            sc = min(W0 / (2 * hx), H0 / (2 * hy)); h = v.h * sc; hx, hy = hx * sc, hy * sc
        cx = E.clamp(v.c[0], hx - (self.overscan - 1) * self.size[0] / 2, self.size[0] - hx + (self.overscan - 1) * self.size[0] / 2)
        cy = E.clamp(v.c[1], hy - (self.overscan - 1) * self.size[1] / 2, self.size[1] - hy + (self.overscan - 1) * self.size[1] / 2)
        return View((cx, cy), h, v.rot, self.screen)

    def speed(self, t, dt=1 / 60):
        """apparent camera speed in screen px per 1/30 s (translation of the centre + zoom contribution)."""
        a, b = self.view(t - dt), self.view(t + dt)
        move = np.hypot(*(b.pt(a.c) - a.pt(a.c)))                   # where a's centre ends up on screen under b
        zoom = abs(math.log(b.h / a.h)) * 0.5 * self.screen[1]
        return float((move + zoom) / (2 * dt * 30))

    # -- composition QA -------------------------------------------------------------------------------------
    def check(self, must_show=None, safe=0.05, step=1 / 30, tmax=None, max_magnification=None):
        """sample the path and report problems: window leaving the image, anchors outside the safe frame,
        magnification beyond `max_magnification` (screen px per source px). must_show: {anchor: (t0, t1)}."""
        issues = []
        tmax = tmax if tmax is not None else self.ts[-1]
        n = int((tmax - self.ts[0]) / step) + 1
        pyr_cover = _Cover(self.size)
        for i in range(n):
            t = self.ts[0] + i * step
            v = self.view(t)
            cov = pyr_cover(v)
            if cov < 0.999: issues.append(("window_outside_image", round(t, 3), round(cov, 3)))
            if max_magnification and v.k > max_magnification: issues.append(("over_magnified", round(t, 3), round(v.k, 2)))
            for name, (t0, t1) in (must_show or {}).items():
                if t0 <= t <= t1 and not v.on_screen(self.anchors[name], margin=safe * min(v.W, v.H)):
                    issues.append(("anchor_outside_safe_frame", round(t, 3), name))
        return issues


class _Cover:
    def __init__(self, size): self.size = size
    def __call__(self, v):
        xs, ys = np.meshgrid(np.linspace(0, v.W, 17), np.linspace(0, v.H, 9))
        p = v.inv(np.stack([xs.ravel(), ys.ravel()], 1))
        ok = (p[:, 0] >= -0.5) & (p[:, 0] <= self.size[0] + 0.5) & (p[:, 1] >= -0.5) & (p[:, 1] <= self.size[1] + 0.5)
        return float(ok.mean())
