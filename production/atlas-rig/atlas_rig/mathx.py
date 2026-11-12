"""Small 2D affine helpers (3x3 homogeneous matrices, y axis points down)."""
import math
import numpy as np


def T(x, y):
    return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], float)


def R(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)


def S(sx, sy=None):
    return np.array([[sx, 0, 0], [0, sx if sy is None else sy, 0], [0, 0, 1]], float)


def about(p, deg):
    return T(*p) @ R(deg) @ T(-p[0], -p[1])


def ap(M, p):
    v = M @ np.array([p[0], p[1], 1.0])
    return v[:2]


def ap_many(M, pts):
    pts = np.asarray(pts, float)
    return pts @ M[:2, :2].T + M[:2, 2]


def ang(v):
    return math.degrees(math.atan2(v[1], v[0]))


def unit(v):
    v = np.asarray(v, float)
    n = math.hypot(v[0], v[1])
    return v / n if n > 1e-9 else np.array([0.0, 1.0])


def smoothstep(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def smootherstep(u):
    u = min(1.0, max(0.0, u))
    return u * u * u * (u * (6 * u - 15) + 10)


def lerp(a, b, u):
    return a + (b - a) * u


def bone_matrix(a_rest, b_rest, a_world, b_world):
    """Rigid transform taking the rest segment a->b onto the world segment (no stretch)."""
    rot = ang(np.subtract(b_world, a_world)) - ang(np.subtract(b_rest, a_rest))
    return T(*a_world) @ R(rot) @ T(-a_rest[0], -a_rest[1])


def pchip(ts, vs):
    """Monotone cubic interpolant (Fritsch-Carlson). Returns f(t); flat outside the keys."""
    ts = np.asarray(ts, float)
    vs = np.asarray(vs, float)
    h = np.diff(ts)
    d = np.diff(vs) / h
    m = np.zeros_like(vs)
    for i in range(1, len(vs) - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    # end slopes 0: the motion starts and ends at rest

    def f(t):
        if t <= ts[0]:
            return float(vs[0])
        if t >= ts[-1]:
            return float(vs[-1])
        i = int(np.searchsorted(ts, t) - 1)
        u = (t - ts[i]) / h[i]
        h00 = 2 * u ** 3 - 3 * u ** 2 + 1
        h10 = u ** 3 - 2 * u ** 2 + u
        h01 = -2 * u ** 3 + 3 * u ** 2
        h11 = u ** 3 - u ** 2
        return float(h00 * vs[i] + h10 * h[i] * m[i] + h01 * vs[i + 1] + h11 * h[i] * m[i + 1])
    return f
