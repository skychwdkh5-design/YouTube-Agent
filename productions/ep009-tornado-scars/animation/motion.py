"""Orbital Atlas — reusable motion presets (painted 2.5D collage).

Principles encoded here (see MOTION_PRESETS.md):
  * every movement uses a named cubic-Bezier curve chosen by MATERIAL / MASS, not one generic ease;
  * overshoot only for light, elastic things (map pins); heavy things (trees, terrain, satellites) never bounce;
  * cameras follow critically damped paths with motivated targets; no random shake, no whip blur;
  * painted PNGs are articulated by colour/position segmentation into layers that move with lag (secondary motion).
"""
import math
import numpy as np
from PIL import Image, ImageFilter, ImageChops, ImageDraw

# ---------------------------------------------------------------- easing
def bezier(p1x, p1y, p2x, p2y):
    """CSS-style cubic-bezier(p1x,p1y,p2x,p2y) -> f(u) for u in 0..1 (Newton + bisection solve)."""
    def bx(s): return 3 * p1x * s * (1 - s) ** 2 + 3 * p2x * s * s * (1 - s) + s ** 3
    def by(s): return 3 * p1y * s * (1 - s) ** 2 + 3 * p2y * s * s * (1 - s) + s ** 3
    def dbx(s): return 3 * p1x * (1 - s) ** 2 + 6 * (p2x - p1x) * s * (1 - s) + 3 * (1 - p2x) * s * s
    def f(u):
        u = min(1.0, max(0.0, u)); s = u
        for _ in range(6):
            d = dbx(s)
            if abs(d) < 1e-6: break
            s -= (bx(s) - u) / d; s = min(1.0, max(0.0, s))
        lo, hi = 0.0, 1.0
        for _ in range(12):
            if abs(bx(s) - u) < 1e-5: break
            if bx(s) < u: lo = s
            else: hi = s
            s = (lo + hi) / 2
        return by(s)
    return f

# Named curves (material / intention)
EASE = {
    "camera_glide":  bezier(0.45, 0.05, 0.20, 1.00),  # motivated dolly: soft start, long landing
    "camera_settle": bezier(0.16, 1.00, 0.30, 1.00),  # arrives fast, settles long (reveal holds)
    "heavy_fall":    bezier(0.55, 0.00, 0.90, 0.35),  # gravity: slow start, accelerating
    "heavy_land":    bezier(0.10, 0.70, 0.25, 1.00),  # massive object comes to rest, no rebound
    "light_drop":    bezier(0.50, 0.00, 0.75, 0.00),  # light object falling (pins)
    "unfold_rigid":  bezier(0.65, 0.00, 0.35, 1.00),  # hinged / rigid unfold (measure bridge)
    "draw_on":       bezier(0.30, 0.00, 0.10, 1.00),  # strokes, arrows, scanlines
    "orbit":         bezier(0.25, 0.10, 0.75, 0.90),  # near-constant orbital speed with gentle ends
    "terrain_wave":  bezier(0.40, 0.00, 0.60, 1.00),  # change propagating through ground
    "fade_soft":     bezier(0.40, 0.00, 0.60, 1.00),
    "text_rise":     bezier(0.20, 0.80, 0.20, 1.00),
}

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def lerp(a, b, u): return a + (b - a) * u
def ease(name, t, a, b): return EASE[name](seg(t, a, b))

def damped(t, freq=2.2, zeta=0.35):
    """Unit step response of a damped oscillator (secondary motion / follow-through), t>=0 seconds."""
    if t <= 0: return 0.0
    w = 2 * math.pi * freq
    if zeta >= 1: return 1 - math.exp(-w * t) * (1 + w * t)
    wd = w * math.sqrt(1 - zeta * zeta)
    return 1 - math.exp(-zeta * w * t) * (math.cos(wd * t) + zeta / math.sqrt(1 - zeta * zeta) * math.sin(wd * t))

def h01(i): v = math.sin(i * 127.1 + 311.7) * 43758.5453; return v - math.floor(v)
def vnoise(t, seed=0):
    i = math.floor(t); f = t - i; f = f * f * (3 - 2 * f)
    return lerp(h01(i + seed * 97.3), h01(i + 1 + seed * 97.3), f) * 2 - 1
def fbm(t, seed=0, oct=3):
    return sum(vnoise(t * (2 ** k), seed + k) / (2 ** k) for k in range(oct)) / 1.75

def lag(fn, t, delay): return fn(t - delay)  # read a motion signal later (propagation through a body)

# ---------------------------------------------------------------- wind / gust model
def gust(t, events, base=0.0):
    """Wind load 0..1+: sum of gust envelopes (start, peak, attack, release) + slow turbulence."""
    w = base
    for (t0, peak, att, rel) in events:
        if t >= t0:
            dt = t - t0
            w += peak * (EASE["fade_soft"](clamp(dt / att)) if dt < att else math.exp(-(dt - att) / rel))
    return w + 0.12 * fbm(t * 0.9, 5) * max(base, 0.2)

# ---------------------------------------------------------------- painted-asset articulation
def split_tree(img, n_clusters=8, ground_frac=0.80, seed=0):
    """Split a painted tree PNG into: ground (static base), wood (trunk+branches), canopy clusters.
    Leaves = green/yellow hue with saturation; wood = remaining opaque pixels. Clusters by k-means on leaf positions.
    Returns dict(wood, ground, clusters=[(layer, (cx, cy))]) in the image's own pixel space."""
    a = np.asarray(img.convert("RGBA")).astype(np.float32) / 255
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    mx, mn = a[..., :3].max(2), a[..., :3].min(2); d = mx - mn + 1e-6
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    sat = d / (mx + 1e-6)
    H, W = al.shape
    yy, xx = np.mgrid[0:H, 0:W]
    leaf = (al > 0.12) & (hue > 52) & (hue < 165) & (sat > 0.22) & (yy < H * ground_frac)
    ground = (al > 0.02) & (yy >= H * ground_frac)
    wood = (al > 0.02) & ~leaf & ~ground
    def layer(mask, feather=0):
        m = Image.fromarray((mask * 255).astype(np.uint8))
        if feather: m = m.filter(ImageFilter.GaussianBlur(feather))
        L = img.copy(); L.putalpha(ImageChops.multiply(img.getchannel("A"), m)); return L
    pts = np.stack([xx[leaf], yy[leaf]], 1).astype(np.float32)
    rng = np.random.default_rng(seed)
    cen = pts[rng.choice(len(pts), n_clusters, replace=False)]
    sub = pts[:: max(1, len(pts) // 40000)]
    for _ in range(12):
        lab = np.argmin(((sub[:, None, :] - cen[None]) ** 2).sum(2), 1)
        cen = np.array([sub[lab == k].mean(0) if (lab == k).any() else cen[k] for k in range(n_clusters)])
    full = np.argmin(((np.stack([xx, yy], -1)[..., None, :].astype(np.float32) - cen[None, None]) ** 2).sum(-1), -1)
    clusters = []
    for k in range(n_clusters):
        clusters.append((layer(leaf & (full == k), 1.2), (float(cen[k][0]), float(cen[k][1]))))
    clusters.sort(key=lambda c: c[1][1])  # back-to-front by height (upper canopy drawn first)
    return dict(wood=layer(wood), ground=layer(ground), clusters=clusters, size=(W, H))

def mesh_bend(img, shift_fn, strips=30):
    """Generic row-wise mesh warp: shift_fn(h) -> dx px for normalized height h (0 base .. 1 top)."""
    Hh = img.height; amp = max(abs(shift_fn(h / 10)) for h in range(11)); pad = int(amp) + 4
    Wd = img.width + 2 * pad; src = Image.new("RGBA", (Wd, Hh), (0, 0, 0, 0)); src.paste(img, (pad, 0)); mesh = []
    for i in range(strips):
        y0, y1 = int(Hh * i / strips), int(Hh * (i + 1) / strips)
        d0, d1 = shift_fn(1 - y0 / Hh), shift_fn(1 - y1 / Hh)
        mesh.append(((0, y0, Wd, y1), (-d0, y0, -d1, y1, Wd - d1, y1, Wd - d0, y0)))
    return src.transform((Wd, Hh), Image.MESH, mesh, Image.BICUBIC), pad

def band_split(img, n=4, overlap=0.18):
    """Split a cloud PNG into n horizontal bands with feathered overlaps (independent rolling layers)."""
    H = img.height; out = []
    for i in range(n):
        m = np.zeros((H, 1), np.float32); y = np.arange(H)[:, None] / H
        c0, c1 = i / n, (i + 1) / n
        lo, hi = c0 - overlap / 2, c1 + overlap / 2
        m = np.clip(np.minimum((y - lo) / overlap, (hi - y) / overlap), 0, 1)
        if i == 0: m = np.where(y < c1, 1, m)
        if i == n - 1: m = np.where(y > c0, 1, m)
        mm = Image.fromarray((np.repeat(m, img.width, 1) * 255).astype(np.uint8))
        L = img.copy(); L.putalpha(ImageChops.multiply(img.getchannel("A"), mm)); out.append(L)
    return out

def atmos(img, k, haze=(70, 82, 110)):
    """Atmospheric perspective: desaturate, lower contrast and tint toward haze by k (0 near .. 1 far)."""
    if k <= 0: return img
    rgb = img.convert("RGB"); g = rgb.convert("L").convert("RGB")
    rgb = Image.blend(rgb, g, 0.5 * k); rgb = Image.blend(rgb, Image.new("RGB", img.size, haze), 0.45 * k)
    out = rgb.convert("RGBA"); out.putalpha(img.getchannel("A")); return out

# ---------------------------------------------------------------- camera
class Cam:
    """Keyframed camera with per-segment named easing; value = (x, y, zoom). Motivated paths only."""
    def __init__(self, keys): self.keys = sorted(keys, key=lambda k: k[0])  # (t, (x,y,z), ease_name)
    def __call__(self, t):
        ks = self.keys
        if t <= ks[0][0]: return ks[0][1]
        for (t0, v0, _), (t1, v1, e) in zip(ks, ks[1:]):
            if t <= t1:
                u = EASE[e](seg(t, t0, t1)); return tuple(lerp(a, b, u) for a, b in zip(v0, v1))
        return ks[-1][1]

# ---------------------------------------------------------------- sound synthesis (local, rights-free)
SR = 48000
_rng = np.random.default_rng(11)
from scipy.signal import lfilter
def lp(x, fc, block=512):
    """One-pole low-pass; fc scalar or per-sample array (time-varying handled in short blocks with carried state)."""
    fca = np.asarray(fc, np.float64)
    if fca.ndim == 0:
        k = 1 - math.exp(-2 * math.pi * float(fca) / SR); return lfilter([k], [1, k - 1], x)
    fca = np.broadcast_to(fca, x.shape); y = np.empty_like(x); last = 0.0
    for i in range(0, len(x), block):
        k = 1 - math.exp(-2 * math.pi * float(fca[i]) / SR)
        y[i:i + block], _ = lfilter([k], [1, k - 1], x[i:i + block], zi=[(1 - k) * last])
        last = y[min(len(x), i + block) - 1]
    return y
def hp(x, fc): return x - lp(x, fc)
def noise(n): return _rng.standard_normal(n)
def env_ad(n, att, dec):
    t = np.arange(n) / SR; return np.clip(t / max(att, 1e-4), 0, 1) * np.exp(-np.clip(t - att, 0, None) / max(dec, 1e-4))

def snd_wind(dur, gust_curve):
    """Wind: band-limited noise, brightness & level follow the gust curve (array len n, 0..1+)."""
    n = int(dur * SR); g = np.interp(np.arange(n), np.linspace(0, n, len(gust_curve)), gust_curve)
    x = lp(noise(n), 250 + 1700 * np.clip(g, 0, 1.3)); x = hp(x, 60)
    whistle = np.sin(2 * np.pi * np.cumsum(500 + 380 * g) / SR) * 0.04 * np.clip(g - 0.5, 0, 1)
    return (x / (np.abs(x).max() + 1e-9) * (0.15 + 0.85 * np.clip(g, 0, 1.3)) + whistle)
def snd_creak(dur=0.9, f0=95):
    """Wood strain: stick-slip friction pulses through a resonant body."""
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n); pos = 0.0
    rate = 18 + 40 * t / dur
    while pos < dur:
        i = int(pos * SR); L = int(0.012 * SR)
        if i + L >= n: break
        tt = np.arange(L) / SR
        out[i:i + L] += np.sin(2 * np.pi * (f0 * (1 + 0.6 * pos / dur)) * tt) * np.exp(-tt * 140) * (0.5 + h01(i) * 0.5)
        pos += 1 / rate[min(n - 1, i)] * (0.7 + 0.6 * h01(i + 3))
    return out * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.5
def snd_snap():
    n = int(0.5 * SR); t = np.arange(n) / SR
    crack = hp(noise(n), 1800) * np.exp(-t * 60)
    splinter = sum(hp(noise(n), 3000) * np.exp(-np.clip(t - d, 0, None) * 90) * (t > d) * 0.5 for d in (0.02, 0.045, 0.07, 0.11))
    body = np.sin(2 * np.pi * 140 * t) * np.exp(-t * 25) * 0.6
    return crack + splinter + body
def snd_thud(f=48, dur=1.4, bright=600):
    n = int(dur * SR); t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * np.cumsum(f + 40 * np.exp(-t * 14)) / SR) * np.exp(-t * 3.2)
    dirt = lp(noise(n), bright) * np.exp(-t * 9) * 0.7
    return np.tanh((sub + dirt) * 1.3)
def snd_debris(dur=1.6, density=40, bright=4000):
    n = int(dur * SR); out = np.zeros(n)
    for k in range(int(density * dur)):
        tt = (h01(k + 7) ** 1.6) * dur; i = int(tt * SR); L = int(0.03 * SR)
        if i + L >= n: continue
        g = np.exp(-np.arange(L) / SR * (120 + 200 * h01(k))) * (1 - tt / dur) * (0.4 + 0.6 * h01(k + 1))
        out[i:i + L] += hp(noise(L), 800 + bright * h01(k + 2)) * g
    return out
def snd_scan(dur):
    """Satellite scan: soft high sine with slow glide + faint regular data ticks (quiet, elegant)."""
    n = int(dur * SR); t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * np.cumsum(1900 + 250 * t / dur) / SR) * 0.18 + np.sin(2 * np.pi * 3820 * t) * 0.05
    ticks = np.zeros(n)
    for k in range(int(dur * 12)):
        i = int(k / 12 * SR); L = int(0.006 * SR)
        if i + L < n: ticks[i:i + L] += np.sin(2 * np.pi * 5200 * np.arange(L) / SR) * np.exp(-np.arange(L) / SR * 900) * 0.35
    return (tone + ticks) * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.3
def snd_bed(dur, f=(55, 82.5, 110, 164.8), bright=1.0):
    """Atmospheric pad: detuned sines + airy filtered noise, slow breathing."""
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for i, fr in enumerate(f):
        x += np.sin(2 * np.pi * fr * (1 + 0.002 * i) * t + i) * (0.5 / (i + 1)) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.07 * t + i))
    air = lp(noise(n), 900 * bright) * 0.12
    return x + air
def snd_pressure(dur):
    """Storm pressure: sub rumble 28-45 Hz with slow amplitude swell (felt more than heard)."""
    n = int(dur * SR); t = np.arange(n) / SR
    r = lp(noise(n), 70) * 4 + np.sin(2 * np.pi * 33 * t) * 0.3
    return r * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t))
def snd_thunder(dur=3.0, dist=0.6):
    """Distant thunder: initial crack (less when distant) + long low-passed rumble."""
    n = int(dur * SR); t = np.arange(n) / SR
    rumble = lp(noise(n), 160 + 300 * (1 - dist)) * np.exp(-t * (0.9 + dist)) * (1 - np.exp(-t * 12))
    crack = hp(noise(n), 1200) * np.exp(-t * 30) * (1 - dist) * 0.5
    return rumble * 3 + crack
def snd_settle(f=180, dur=0.35):
    """Small dimensional object landing on a map: soft papery tap + low body."""
    n = int(dur * SR); t = np.arange(n) / SR
    return lp(noise(n), 2200) * np.exp(-t * 45) * 0.6 + np.sin(2 * np.pi * f * t) * np.exp(-t * 22) * 0.5
def snd_air(dur=0.8, up=True):
    """Soft directional air move (camera travel) — each call gets its own filter path."""
    n = int(dur * SR); t = np.linspace(0, 1, n)
    sweep = 250 + 1600 * (t if up else 1 - t) ** 1.3
    x = lp(noise(n), sweep); return x * np.sin(np.pi * t) ** 2
