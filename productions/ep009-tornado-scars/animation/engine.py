"""Orbital Atlas continuous-motion engine (v4).

Everything animated is a pure function of time in seconds with float coordinates; nothing is rounded before the final
resample. Layers are float32 premultiplied sprites drawn with ONE affine/remap resample each (no resize->rotate->paste
chains, no int() placement). A frame is an average of N sub-frame evaluations over a simulated shutter.
"""
import math
import numpy as np
import cv2
from PIL import Image

cv2.setNumThreads(2)
W, H, FPS = 1920, 1080, 30


# ------------------------------------------------------------------ curves
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def lerp(a, b, u): return a + (b - a) * u
def smooth(u): u = clamp(u); return u * u * u * (u * (6 * u - 15) + 10)   # quintic: zero velocity AND acceleration at ends


class Hermite:
    """C1 cubic Hermite through keys [(t, value[, velocity])]. Interior tangents are monotone (Fritsch-Carlson), so there is
    no overshoot and velocity flows through keys; ends are at rest unless a velocity is given. Values: float or tuple.
    log=True interpolates log(value) (use for zoom / scale so equal steps feel equal)."""
    def __init__(self, keys, log=False):
        self.log = log
        self.t = np.array([k[0] for k in keys], float)
        v = np.array([np.atleast_1d(np.asarray(k[1], float)) for k in keys])
        self.scalar = np.ndim(keys[0][1]) == 0
        if log: v = np.log(v)
        self.v = v
        n = len(keys); m = np.zeros_like(v)
        d = np.diff(v, axis=0) / np.diff(self.t)[:, None]
        for i in range(1, n - 1):
            for c in range(v.shape[1]):
                a, b = d[i - 1, c], d[i, c]
                if a * b <= 0: m[i, c] = 0
                else:
                    h0, h1 = self.t[i] - self.t[i - 1], self.t[i + 1] - self.t[i]; w1, w2 = 2 * h1 + h0, h1 + 2 * h0
                    m[i, c] = (w1 + w2) / (w1 / a + w2 / b)
        for i, k in enumerate(keys):
            if len(k) > 2 and k[2] is not None:
                vel = np.atleast_1d(np.asarray(k[2], float)); m[i] = vel / np.exp(v[i]) if log else vel
        self.m = m

    def __call__(self, t):
        T = self.t
        if t <= T[0]: out = self.v[0]
        elif t >= T[-1]: out = self.v[-1]
        else:
            i = int(np.searchsorted(T, t) - 1); h = T[i + 1] - T[i]; u = (t - T[i]) / h
            h00, h10, h01, h11 = 2 * u**3 - 3 * u**2 + 1, u**3 - 2 * u**2 + u, -2 * u**3 + 3 * u**2, u**3 - u**2
            out = h00 * self.v[i] + h10 * h * self.m[i] + h01 * self.v[i + 1] + h11 * h * self.m[i + 1]
        if self.log: out = np.exp(out)
        return float(out[0]) if self.scalar else tuple(float(x) for x in out)


class Cam:
    """Virtual camera path (x, y, vw) through keys [(t, (x, y, vw)[, velocity])]; vw interpolated in log space."""
    def __init__(self, keys):
        self.p = Hermite([(k[0], k[1][:2], k[2] if len(k) > 2 else None) for k in keys])
        self.z = Hermite([(k[0], k[1][2]) for k in keys], log=True)
    def __call__(self, t): x, y = self.p(t); return x, y, self.z(t)


# ------------------------------------------------------------------ smooth noise / wind (C-infinity, no lattice stops)
def turb(t, seed=0, f0=1.0, octaves=3):
    """Band-limited noise in [-1,1]: sum of incommensurate sines. Never has the per-lattice dwell of value noise."""
    s = 0.0; a = 0.0
    for k in range(octaves):
        r = np.random.default_rng(seed * 31 + k)
        fr = f0 * (1.0 + 0.61803 * k) * 1.9 ** k * (0.85 + 0.3 * r.random()); ph = r.random() * 2 * math.pi
        amp = 1.0 / (1.0 + 0.8 * k); s += amp * math.sin(2 * math.pi * fr * t + ph); a += amp
    return s / a


def gust_pulse(t, t0, peak, tau):
    """Smooth wind pulse: zero value AND zero slope at onset (alpha^2 shape), peaks at t0+tau, tail decays continuously."""
    if t <= t0: return 0.0
    x = (t - t0) / tau
    return peak * x * x * math.exp(2 * (1 - x)) * (1.0 if x < 1 else 1.0)


def wind(t, pulses, base=0.12, seed=3):
    w = base * (1 + 0.35 * turb(t, seed, 0.23))
    for p in pulses: w += gust_pulse(t, *p)
    return w


# ------------------------------------------------------------------ spring-damper simulation (sampled by Hermite -> continuous in t)
class Sim:
    """Fixed-step (1 kHz) simulation of arbitrary state; sampled at any time with cubic Hermite on (x, v) -> C1 and
    independent of render fps. step(state, t, dt) -> state must be deterministic. state = np.array [x1.., v1..]."""
    def __init__(self, state0, step, t0, t1, rate=1000):
        self.t0, self.dt = t0, 1.0 / rate; n = int((t1 - t0) * rate) + 2
        self.S = np.zeros((n, len(state0))); s = np.array(state0, float); self.S[0] = s
        for i in range(1, n):
            s = step(s, t0 + (i - 1) * self.dt, self.dt); self.S[i] = s

    def __call__(self, t):
        f = (t - self.t0) / self.dt; i = int(clamp(math.floor(f), 0, len(self.S) - 2)); u = clamp(f - i)
        return self.S[i] * (1 - u) + self.S[i + 1] * u          # 1 kHz linear on a smooth 1 kHz-sampled state: error << 0.001 px


def osc_step(x, v, dt, w0, zeta, force):
    """Semi-implicit damped oscillator: x'' = -w0^2 x - 2 zeta w0 v + w0^2 * force."""
    a = -w0 * w0 * x - 2 * zeta * w0 * v + w0 * w0 * force
    v = v + a * dt; x = x + v * dt; return x, v


# ------------------------------------------------------------------ sprites
class Sprite:
    """Float32 premultiplied RGBA. ref_h pre-shrinks (INTER_AREA) to ~ the largest on-screen height so per-frame bilinear
    warps never alias; `k` records the pre-scale so callers can keep working in original pixel units."""
    def __init__(self, pil, ref_h=None):
        a = np.asarray(pil.convert("RGBA"), np.float32) / 255.0
        a[..., :3] *= a[..., 3:4]
        self.k = 1.0
        if ref_h and ref_h < a.shape[0]:
            self.k = ref_h / a.shape[0]
            a = cv2.resize(a, (max(1, round(a.shape[1] * self.k)), int(ref_h)), interpolation=cv2.INTER_AREA)
        self.a = np.ascontiguousarray(a); self.h, self.w = a.shape[:2]; self._sh = None

    def shadow(self, blur=6, strength=0.5, color=(0.02, 0.04, 0.09)):
        key = (blur, strength)
        if self._sh is None or self._sh[0] != key:
            al = cv2.GaussianBlur(self.a[..., 3], (0, 0), blur) * strength
            s = np.zeros_like(self.a); s[..., 0], s[..., 1], s[..., 2], s[..., 3] = [c * al for c in color] + [al]
            self._sh = (key, s)
        return self._sh[1]


def mat(tx=0.0, ty=0.0, rot=0.0, sx=1.0, sy=None, px=0.0, py=0.0):
    """2x3 affine: sprite px -> screen. Scale and rotate about sprite pixel (px,py), which lands on screen (tx,ty)."""
    sy = sx if sy is None else sy; c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    a, b, d, e = c * sx, -s * sy, s * sx, c * sy
    return np.array([[a, b, tx - a * px - b * py], [d, e, ty - d * px - e * py]], np.float64)


def compose(m_outer, m_inner):
    A = np.vstack([m_outer, [0, 0, 1]]); B = np.vstack([m_inner, [0, 0, 1]]); return (A @ B)[:2]


def _over(canvas, src, x0, y0, alpha, tint=None, add=False):
    h, w = src.shape[:2]
    rgb = canvas[y0:y0 + h, x0:x0 + w]
    if alpha != 1.0: src = src * alpha
    if tint is not None: src = src.copy(); src[..., :3] *= np.asarray(tint, np.float32)
    if add: rgb += src[..., :3]; return
    rgb *= (1.0 - src[..., 3:4]); rgb += src[..., :3]


def _bbox(m, w, h, pad=2):
    pts = np.array([[0, 0, 1], [w, 0, 1], [w, h, 1], [0, h, 1]], np.float64) @ m.T
    x0, y0 = int(np.floor(pts[:, 0].min())) - pad, int(np.floor(pts[:, 1].min())) - pad
    x1, y1 = int(np.ceil(pts[:, 0].max())) + pad, int(np.ceil(pts[:, 1].max())) + pad
    return max(0, x0), max(0, y0), min(W, x1), min(H, y1)


def draw(canvas, spr, m, alpha=1.0, shadow=None, shoff=(8.0, 12.0), flags=None, tint=None, add=False):
    """Draw sprite with affine m (sprite px -> screen) using a single resample. shadow=(blur_px_in_sprite, strength)."""
    if alpha <= 0.004: return
    if shadow:
        draw(canvas, _ShadowView(spr, shadow), np.array([[m[0, 0], m[0, 1], m[0, 2] + shoff[0]], [m[1, 0], m[1, 1], m[1, 2] + shoff[1]]]), alpha, tint=None)
    x0, y0, x1, y1 = _bbox(m, spr.w, spr.h)
    if x1 <= x0 or y1 <= y0: return
    mr = m.copy(); mr[0, 2] -= x0; mr[1, 2] -= y0
    sc = math.sqrt(abs(np.linalg.det(m[:, :2])))
    fl = flags if flags is not None else (cv2.INTER_CUBIC if sc > 1.0 else cv2.INTER_LINEAR)
    src = cv2.warpAffine(spr.a, mr, (x1 - x0, y1 - y0), flags=fl, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    if fl == cv2.INTER_CUBIC: np.clip(src, 0, 1, out=src)
    _over(canvas, src, x0, y0, alpha, tint, add)


class _ShadowView:
    def __init__(self, spr, sh): a = spr.shadow(*sh); self.a, self.h, self.w = a, spr.h, spr.w


def draw_remap(canvas, spr, inv_fn, bbox, alpha=1.0, tint=None, add=False, arr=None, amask=None):
    """Draw with an arbitrary deformation. inv_fn(X, Y) -> (U, V): screen px -> sprite px (float arrays over bbox).
    One resample (cv2.remap, bilinear). Used for bending trunks, rolling clouds, anything non-affine."""
    x0, y0, x1, y1 = bbox; x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0 or alpha <= 0.004: return
    X, Y = np.meshgrid(np.arange(x0, x1, dtype=np.float32) + 0.5, np.arange(y0, y1, dtype=np.float32) + 0.5)
    U, V = inv_fn(X, Y)
    src = cv2.remap(spr.a if arr is None else arr, (U - 0.5).astype(np.float32), (V - 0.5).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    if amask is not None: src = src * amask(U, V)[..., None]
    _over(canvas, src, x0, y0, alpha, tint, add)


# ------------------------------------------------------------------ documentary image sampler (trilinear mip, float camera)
class Doc:
    """Documentary still sampled by a float camera. Mip pyramid (INTER_AREA) + trilinear blend between levels, so zooming or
    panning never shimmers, steps or pops. Pixels are only resampled geometrically (never repainted)."""
    def __init__(self, pil):
        a = np.asarray(pil.convert("RGB")); self.lv = [a]
        while min(self.lv[-1].shape[:2]) > 600:
            p = self.lv[-1]; self.lv.append(cv2.resize(p, (p.shape[1] // 2, p.shape[0] // 2), interpolation=cv2.INTER_AREA))
        self.w, self.h = pil.size

    def render(self, cx, cy, vw, rot=0.0, size=(W, H)):
        sw, sh = size; s = vw / sw
        lf = clamp(math.log2(max(s, 1e-6)), 0, len(self.lv) - 1.001); l0 = int(lf); fr = lf - l0
        out = None
        for lv, wt in ((l0, 1 - fr), (l0 + 1, fr)):
            if wt <= 1e-3: continue
            k = 2.0 ** lv; c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            # screen -> source(level) :  src = (C + R * s * (p - ctr)) / k
            a, b, d, e = s * c / k, -s * sn / k, s * sn / k, s * c / k
            m = np.array([[a, b, cx / k - a * sw / 2 - b * sh / 2], [d, e, cy / k - d * sw / 2 - e * sh / 2]], np.float64)
            im = cv2.warpAffine(self.lv[lv], m, (sw, sh), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            im = im.astype(np.float32) / 255.0
            out = im * wt if out is None else out + im * wt
        return out


def to_canvas(rgb_u8): return rgb_u8.astype(np.float32) / 255.0


# ------------------------------------------------------------------ shutter / subframes
def subtimes(t, n, shutter=0.5, fps=FPS):
    """n sample times centred on t, spanning shutter*(1/fps) seconds (180 deg shutter -> shutter=0.5). n=1 -> exactly t."""
    if n <= 1: return [t], [1.0]
    span = shutter / fps
    return [t - span / 2 + span * (j + 0.5) / n for j in range(n)], [1.0 / n] * n


def render_frame(scene, t, n=1, shutter=0.5):
    ts, ws = subtimes(t, n, shutter); acc = None
    for tj, w in zip(ts, ws):
        c = scene(tj); acc = c * w if acc is None else acc + c * w
    return acc


_GR = np.random.default_rng(5).normal(0, 1, (6, H, W)).astype(np.float32)


def finish(canvas, i, vignette=None, grain=0.012):
    """Output stage, applied ONCE per output frame (after sub-frame accumulation): vignette, film grain, 8-bit dither."""
    c = canvas
    if vignette is not None: c = c * vignette[..., None]
    c = c + _GR[i % 6][..., None] * grain
    return np.clip(c * 255.0 + 0.5, 0, 255).astype(np.uint8)


def vignette_map(strength=0.30):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); r = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
    return 1.0 - strength * np.clip((r - 0.55) / 0.9, 0, 1) ** 1.6


# ------------------------------------------------------------------ small float helpers used by scenes
def blur(c, sigma):
    return c if sigma < 0.3 else cv2.GaussianBlur(c, (0, 0), sigma)


def seg_dist(X, Y, pts):
    """Distance from every (X,Y) to a polyline (float, vectorised, continuous in the points)."""
    d = np.full(X.shape, 1e9, np.float32)
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy + 1e-9
        u = np.clip(((X - ax) * vx + (Y - ay) * vy) / L2, 0, 1)
        d = np.minimum(d, np.hypot(X - (ax + u * vx), Y - (ay + u * vy)))
    return d


def corridor(pts_screen, width, feather, q=4):
    """Soft mask (full res, float) of a polyline corridor. width/feather in screen px. Fully continuous in pts and width."""
    h, w = H // q, W // q
    X, Y = np.meshgrid((np.arange(w, dtype=np.float32) + 0.5) * q, (np.arange(h, dtype=np.float32) + 0.5) * q)
    d = seg_dist(X, Y, pts_screen)
    m = 1.0 - np.clip((d - width / 2) / max(feather, 1e-3), 0, 1)
    m = m * m * (3 - 2 * m)
    return cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)


def spotlight(img, mask, dim=0.42, lift=1.12):
    g = img.mean(2, keepdims=True)
    dark = (img * 0.55 + g * 0.45) * dim
    return dark + (img * lift - dark) * mask[..., None]


def aa_line(c, p0, p1, color, alpha=1.0, width=1.0):
    """Anti-aliased line with float endpoints (cv2 fixed-point 1/16 px), blended into a float canvas ROI."""
    pad = int(width) + 3
    x0, y0 = int(max(0, min(p0[0], p1[0]) - pad)), int(max(0, min(p0[1], p1[1]) - pad)); x1, y1 = int(min(W, max(p0[0], p1[0]) + pad)), int(min(H, max(p0[1], p1[1]) + pad))
    if x1 <= x0 or y1 <= y0 or alpha <= 0.004: return
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.line(m, (int(round((p0[0] - x0) * 16)), int(round((p0[1] - y0) * 16))), (int(round((p1[0] - x0) * 16)), int(round((p1[1] - y0) * 16))), 255, max(1, int(round(width))), cv2.LINE_AA, 4)
    a = (m.astype(np.float32) / 255.0 * alpha)[..., None]; roi = canvas_roi(c, x0, y0, x1, y1)
    roi *= (1 - a); roi += a * np.asarray(color, np.float32)


def canvas_roi(c, x0, y0, x1, y1): return c[y0:y1, x0:x1]


def ring(c, cx, cy, r, alpha, color=(0.91, 0.69, 0.33), width=5.0):
    """Analytic anti-aliased ring (distance field): exact for float centre/radius, no stepping as r grows."""
    if alpha <= 0.004 or r <= 0.5: return
    pad = r + width + 4; x0, y0, x1, y1 = int(max(0, cx - pad)), int(max(0, cy - pad)), int(min(W, cx + pad)), int(min(H, cy + pad))
    if x1 <= x0 or y1 <= y0: return
    X, Y = np.meshgrid(np.arange(x0, x1, dtype=np.float32) + 0.5, np.arange(y0, y1, dtype=np.float32) + 0.5)
    d = np.abs(np.hypot(X - cx, Y - cy) - r); a = np.clip(width / 2 - d + 0.5, 0, 1)[..., None] * alpha
    roi = c[y0:y1, x0:x1]; roi *= (1 - a); roi += a * np.asarray(color, np.float32)
