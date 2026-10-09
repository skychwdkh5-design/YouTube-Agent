"""Easing curves and scalar interpolation. All easing functions map [0,1] -> [0,1] with f(0)=0, f(1)=1
(out_back overshoots in between by design)."""
import math


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def seg(t, t0, t1):
    """normalised position of t inside [t0, t1], clamped to 0..1 (a step if the interval is empty)."""
    return clamp((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t1)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_log(a, b, t):
    """interpolate positive quantities (zoom, height) at constant perceived rate."""
    return math.exp(lerp(math.log(a), math.log(b), t))


def linear(t): return clamp(t)
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
def smoother(t): t = clamp(t); return t * t * t * (t * (6 * t - 15) + 10)
def in_quad(t): t = clamp(t); return t * t
def out_quad(t): t = clamp(t); return 1 - (1 - t) ** 2
def in_out_quad(t): t = clamp(t); return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2
def in_cubic(t): t = clamp(t); return t ** 3
def out_cubic(t): t = clamp(t); return 1 - (1 - t) ** 3
def in_out_cubic(t): t = clamp(t); return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2
def in_expo(t): t = clamp(t); return 0.0 if t == 0 else 2 ** (10 * t - 10) * (1 if t < 1 else 1)
def out_expo(t): t = clamp(t); return 1.0 if t == 1 else 1 - 2 ** (-10 * t)


def in_out_expo(t):
    t = clamp(t)
    if t in (0.0, 1.0): return t
    return 2 ** (20 * t - 10) / 2 if t < 0.5 else (2 - 2 ** (-20 * t + 10)) / 2


def out_back(t, s=1.70158):
    t = clamp(t) - 1
    return 1 + t * t * ((s + 1) * t + s)


def cubic_bezier(x1, y1, x2, y2):
    """CSS-style cubic-bezier easing through (0,0), (x1,y1), (x2,y2), (1,1); x is solved by bisection."""
    def bx(u): return 3 * (1 - u) ** 2 * u * x1 + 3 * (1 - u) * u * u * x2 + u ** 3
    def by(u): return 3 * (1 - u) ** 2 * u * y1 + 3 * (1 - u) * u * u * y2 + u ** 3

    def f(t):
        t = clamp(t)
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if bx(mid) < t: lo = mid
            else: hi = mid
        return by((lo + hi) / 2)
    return f


EASINGS = {
    "linear": linear, "smooth": smooth, "smoother": smoother, "in_quad": in_quad, "out_quad": out_quad,
    "in_out_quad": in_out_quad, "in_cubic": in_cubic, "out_cubic": out_cubic, "in_out_cubic": in_out_cubic,
    "in_expo": in_expo, "out_expo": out_expo, "in_out_expo": in_out_expo, "out_back": out_back,
    # camera-friendly names
    "camera": smoother, "ease": cubic_bezier(0.25, 0.1, 0.25, 1.0), "whip": in_out_expo,
}


def get(e):
    """resolve an easing given by name, by (x1,y1,x2,y2) bezier tuple, or by callable."""
    if callable(e): return e
    if isinstance(e, (tuple, list)) and len(e) == 4: return cubic_bezier(*e)
    try:
        return EASINGS[e]
    except KeyError:
        raise ValueError(f"unknown easing {e!r}; known: {sorted(EASINGS)}")


def pchip_slopes(ts, ys):
    """monotone cubic (Fritsch-Carlson style) slopes: continuous velocity, no overshoot."""
    n = len(ts)
    m = [0.0] * n
    if n < 2: return m
    h = [ts[i + 1] - ts[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    for k in range(1, n - 1):
        if d[k - 1] * d[k] > 0:
            w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / d[k - 1] + w2 / d[k])
    return m


def hermite(t, ts, ys, ms):
    """evaluate the cubic Hermite spline defined by knots ts, values ys and slopes ms."""
    t = min(max(t, ts[0]), ts[-1])
    i = 0
    while i < len(ts) - 2 and t > ts[i + 1]: i += 1
    h = ts[i + 1] - ts[i]
    s = (t - ts[i]) / h
    return ((2 * s ** 3 - 3 * s ** 2 + 1) * ys[i] + (s ** 3 - 2 * s ** 2 + s) * h * ms[i]
            + (-2 * s ** 3 + 3 * s ** 2) * ys[i + 1] + (s ** 3 - s ** 2) * h * ms[i + 1])
