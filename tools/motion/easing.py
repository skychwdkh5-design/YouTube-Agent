"""Named easing curves for Orbital Atlas motion (1080p30 documentary video).

Pure Python, no dependencies. Every curve maps progress p in [0, 1] to eased progress; all
curves return exactly 0 at p=0 and 1 at p=1. Springs may overshoot 1 in between on purpose.

The names are the vocabulary used in motion_spec.json / keyframe files (field "easing").
docs/MOTION_GUIDE.md explains when to use each one. Adding a preset: add it to PRESETS and
document it in the guide; never invent a one-off curve inside a build script.

Credits: the UI curves "enter" and "move_strong" are the cubic-bezier values published by
Emil Kowalski in github.com/emilkowalski/skills (MIT licence, (c) Emil Kowalski); see
docs/MOTION_GUIDE.md for the full attribution. The "topple" curve is integrated from the
inverted-pendulum equation here; "v7_smoothstep" reproduces ease() in examples/painted-collage-v7.
"""
from __future__ import annotations

import math
from bisect import bisect_left
from functools import lru_cache
from typing import Callable, Iterable, Mapping, Sequence

Curve = Callable[[float], float]


def _clamp(p: float) -> float:
    return 0.0 if p <= 0 else 1.0 if p >= 1 else float(p)


# --- cubic bezier (CSS semantics: control points (x1,y1), (x2,y2), ends fixed at 0,0 and 1,1) --

def cubic_bezier(x1: float, y1: float, x2: float, y2: float) -> Curve:
    if not (0 <= x1 <= 1 and 0 <= x2 <= 1):
        raise ValueError("cubic_bezier x control points must be within [0, 1]")

    def coord(t: float, a: float, b: float) -> float:
        return 3 * a * t * (1 - t) ** 2 + 3 * b * t * t * (1 - t) + t ** 3

    def dcoord(t: float, a: float, b: float) -> float:
        return 3 * a * (1 - t) ** 2 + 6 * (b - a) * t * (1 - t) + 3 * (1 - b) * t * t

    def solve_t(x: float) -> float:
        t = x
        for _ in range(8):                      # Newton first, it is fast near the answer
            err = coord(t, x1, x2) - x
            if abs(err) < 1e-7:
                return t
            d = dcoord(t, x1, x2)
            if abs(d) < 1e-6:
                break
            t = min(1.0, max(0.0, t - err / d))
        lo, hi = 0.0, 1.0                       # bisection fallback, always converges
        t = x
        for _ in range(60):
            v = coord(t, x1, x2)
            if abs(v - x) < 1e-7:
                break
            lo, hi = (t, hi) if v < x else (lo, t)
            t = (lo + hi) / 2
        return t

    def f(p: float) -> float:
        p = _clamp(p)
        if p in (0.0, 1.0):
            return p
        return coord(solve_t(p), y1, y2)

    f.bezier = (x1, y1, x2, y2)  # type: ignore[attr-defined]
    return f


# --- physical curves -------------------------------------------------------------------------

def spring(bounce: float = 0.2, settle: float = 0.002) -> Curve:
    """Damped spring from 0 to 1 over the normalised duration (Apple-style 'bounce' parameter,
    0 = critically damped, 0.3 = clearly springy). The curve is time-scaled so the residual
    oscillation is below `settle` at p=1, then pinned to exactly 1 there."""
    if not 0 <= bounce < 1:
        raise ValueError("bounce must be in [0, 1)")
    zeta = 1 - bounce
    # time constant so that envelope e^{-zeta*w*T} hits `settle` at T=1
    w = -math.log(settle) / max(zeta, 0.05)

    def raw(t: float) -> float:
        if zeta >= 0.999:
            return 1 - (1 + w * t) * math.exp(-w * t)
        wd = w * math.sqrt(1 - zeta * zeta)
        e = math.exp(-zeta * w * t)
        return 1 - e * (math.cos(wd * t) + zeta * w / wd * math.sin(wd * t))

    end = raw(1.0)

    def f(p: float) -> float:
        p = _clamp(p)
        if p >= 1:
            return 1.0
        return raw(p) / end if end else raw(p)

    return f


@lru_cache(maxsize=8)
def _topple_table(theta0_deg: float, theta1_deg: float, steps: int = 4000):
    """Integrate theta'' = sin(theta) (rigid body tipping about its base) from theta0 to theta1.
    Returns normalised (time, progress) samples. Real constants only rescale time, so the shape
    of the curve is physical for any object size; the shot length is an editorial choice."""
    th, om, t = math.radians(theta0_deg), 0.0, 0.0
    end = math.radians(theta1_deg)
    dt = 1e-3
    ts, ths = [0.0], [th]
    while th < end and t < 1e4:
        # velocity Verlet
        a = math.sin(th)
        th += om * dt + 0.5 * a * dt * dt
        om += 0.5 * (a + math.sin(th)) * dt
        t += dt
        ts.append(t)
        ths.append(th)
    total, th0 = ts[-1], ths[0]
    span = ths[-1] - th0
    times = [x / total for x in ts]
    prog = [(y - th0) / span for y in ths]
    return tuple(times), tuple(prog)


def topple(theta0_deg: float = 6.0, theta1_deg: float = 50.0) -> Curve:
    """Angular progress of an object tipping over its base: slow release, then accelerating
    until impact. Use for falls about a pivot (trees, towers, poles), never for UI."""
    times, prog = _topple_table(float(theta0_deg), float(theta1_deg))

    def f(p: float) -> float:
        p = _clamp(p)
        if p in (0.0, 1.0):
            return p
        i = bisect_left(times, p)
        t0, t1 = times[i - 1], times[i]
        q = (p - t0) / (t1 - t0) if t1 > t0 else 0.0
        return prog[i - 1] + (prog[i] - prog[i - 1]) * q

    return f


def power_in(k: float) -> Curve:
    return lambda p: _clamp(p) ** k


def v7_smoothstep(p: float) -> float:
    """Exactly ease() from examples/painted-collage-v7/build.py, kept for parity."""
    p = _clamp(p)
    return p * p * (3 - 2 * p)


# --- the named vocabulary ---------------------------------------------------------------------

PRESETS: dict[str, Curve] = {
    "linear": _clamp,
    "v7_smoothstep": v7_smoothstep,
    # entering the frame or appearing: fast start, long soft landing (Emil Kowalski's ease-out)
    "enter": cubic_bezier(0.23, 1, 0.32, 1),
    # leaving the frame / handing attention away: gentle start, accelerates out
    "exit": cubic_bezier(0.55, 0, 0.75, 0.2),
    # an object travelling across a visible space (strong ease-in-out, Emil Kowalski)
    "move_strong": cubic_bezier(0.77, 0, 0.175, 1),
    # the default on-screen move for documentary pacing: softer than move_strong
    "move": cubic_bezier(0.6, 0, 0.3, 1),
    # virtual camera push / drift / pan: sine-like, never snaps at the ends
    "camera": cubic_bezier(0.37, 0, 0.63, 1),
    # wipes, masks, line draws: quick reveal that decelerates while the eye reads it
    "reveal": cubic_bezier(0.16, 1, 0.3, 1),
    # anticipation before an action: small dip back before going forward
    "anticipate": cubic_bezier(0.36, 0, 0.66, -0.56),
    # free fall under gravity (height progress), for dropped objects
    "gravity": power_in(2.0),
    # tipping over a base (tree, mast, tower); physical, see topple()
    "topple": topple(6.0, 50.0),
    # landing after an impact or an arrival with weight
    "settle_soft": spring(0.12),
    "settle_impact": spring(0.32),
}


def get(name: str) -> Curve:
    try:
        return PRESETS[name]
    except KeyError:
        raise KeyError(f"unknown easing '{name}'; known: {', '.join(sorted(PRESETS))}") from None


def ease(name: str, p: float) -> float:
    return get(name)(p)


def segment(t: float, t0: float, t1: float, name: str = "linear") -> float:
    """Eased progress of time t inside [t0, t1] (clamped)."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return get(name)((t - t0) / (t1 - t0))


def lerp(a, b, q):
    if isinstance(a, (list, tuple)):
        return type(a)(lerp(x, y, q) for x, y in zip(a, b))
    return a + (b - a) * q


def interpolate(keyframes: Sequence[Mapping], t: float, prop: str, default_easing: str = "v7_smoothstep"):
    """Value of `prop` at time t from a keyframe list [{"at": s, prop: v, "easing": name}, ...].

    Convention (After Effects 'out' style): the easing named on keyframe i shapes the segment
    from keyframe i to keyframe i+1. Keyframes without the prop are skipped. Missing easing falls
    back to `default_easing`, which is the V7 behaviour, so older keyframe files render as before.
    Before the first / after the last keyframe the value holds."""
    ks = [k for k in keyframes if prop in k]
    if not ks:
        raise KeyError(prop)
    ks = sorted(ks, key=lambda k: k["at"])
    if t <= ks[0]["at"]:
        return ks[0][prop]
    for a, b in zip(ks, ks[1:]):
        if t <= b["at"]:
            q = segment(t, a["at"], b["at"], a.get("easing", default_easing))
            return lerp(a[prop], b[prop], q)
    return ks[-1][prop]


def validate_names(names: Iterable[str]) -> list[str]:
    """Return the unknown names (empty list = all valid)."""
    return sorted({n for n in names if n not in PRESETS})


if __name__ == "__main__":
    for n in PRESETS:
        print(f"{n:15s}", " ".join(f"{get(n)(i / 10):.3f}" for i in range(11)))
