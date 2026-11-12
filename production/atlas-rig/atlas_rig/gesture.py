"""Arm actions and gaze, expressed as targets (never as part rotations).

A Point gesture runs  prep -> move -> accent -> soft hold -> relax:
  prep    the wrist gathers slightly in and back (anticipation)
  move    the wrist travels a shallow curved (Bezier) path to an aim point short of full
          reach, so the elbow stays soft; the hand turns to the target a beat later
  accent  a small push toward the target and settle
  hold    the elbow softens and the hand drops a little (no rigid freeze)
  relax   a curved path back to the resting hand position
The gaze turns to the target before the arm starts (Gaze lead), and the shoulder
lifts a little while the arm is up. IK turns wrist targets into shoulder/elbow angles.
"""
import math
from dataclasses import dataclass, field

import numpy as np

from .mathx import ap, ang, unit, smoothstep, lerp


def bezier(p0, c, p1, u):
    return (1 - u) ** 2 * p0 + 2 * (1 - u) * u * c + u * u * p1


def _rot(v, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]])


@dataclass
class Point:
    arm: str                 # 'f' (far arm) or 'n'
    t0: float                # prep start
    target: object           # world point, or callable t -> world point
    hold_until: float        # relax starts here
    prep: float = 0.22
    move: float = 0.5
    accent: float = 0.28
    relax: float = 0.75
    reach: float = 0.90      # aim point at this fraction of the arm's length (soft elbow)
    arc: float = 0.18        # curvature of the path (fraction of its length, bowed upward)

    def tgt(self, t):
        return np.asarray(self.target(t) if callable(self.target) else self.target, float)

    @property
    def t_move(self):
        return self.t0 + self.prep

    @property
    def t_acc(self):
        return self.t_move + self.move

    @property
    def t_end(self):
        return self.hold_until + self.relax

    def active(self, t):
        return self.t0 <= t < self.t_end

    def wrist(self, t, shoulder, rest, L):
        """World wrist target at time t (shoulder/rest are world points this frame)."""
        T = self.tgt(t)
        d = unit(T - shoulder)
        aim = shoulder + d * L * self.reach
        gather = rest + _rot(np.array([-7.0, -9.0]), 0) * 1.0
        soft = shoulder + _rot(d, 9) * L * (self.reach - 0.07)
        if t < self.t_move:
            return lerp(rest, gather, smoothstep((t - self.t0) / self.prep))
        if t < self.t_acc:
            u = smoothstep((t - self.t_move) / self.move)
            mid = 0.5 * (gather + aim)
            off = _up_perp(aim - gather) * self.arc * np.hypot(*(aim - gather))
            # bow the path AWAY from the shoulder, so the hand never folds through it
            c = mid + off if np.hypot(*(mid + off - shoulder)) >= np.hypot(*(mid - off - shoulder)) else mid - off
            return _keep_out(bezier(gather, c, aim, u), shoulder, 0.6 * L)
        if t < self.t_acc + self.accent:
            u = (t - self.t_acc) / self.accent
            return aim + d * 6.0 * math.sin(math.pi * u) * (1 - 0.4 * u)
        if t < self.hold_until:
            u = smoothstep((t - self.t_acc - self.accent) / 0.55)
            return lerp(aim, soft, u)
        u = smoothstep((t - self.hold_until) / self.relax)
        c = 0.5 * (soft + rest) + np.array([10.0, 12.0])
        return _keep_out(bezier(soft, c, rest, u), shoulder, 0.6 * L)

    def weight(self, t):
        """How much this gesture owns the arm (1 between prep start and relax end)."""
        if t < self.t0 or t >= self.t_end:
            return 0.0
        return 1.0

    def hand(self, t, wrist, elbow):
        """(direction deg, pose name) of the hand."""
        T = self.tgt(t)
        fore = ang(wrist - elbow) - 4
        aim = ang(T - wrist)
        lag = 0.10
        if t < self.t_move + lag:
            w = 0.0
        elif t < self.t_acc + lag:
            w = smoothstep((t - self.t_move - lag) / self.move)
        elif t < self.hold_until:
            w = 1.0
        else:
            w = 1 - smoothstep((t - self.hold_until - 0.05) / (self.relax * 0.8))
        soft = 8 * smoothstep((t - self.t_acc - self.accent) / 0.6) if t >= self.t_acc + self.accent else 0.0
        da = ((aim + soft - fore + 180) % 360) - 180
        pose = 'point' if (self.t_move + 0.35 * self.move <= t < self.hold_until + 0.35 * self.relax) else None
        return fore + da * w, pose

    def shoulder_lift(self, t):
        a = smoothstep((t - self.t_move) / self.move)
        b = 1 - smoothstep((t - self.hold_until) / self.relax)
        return 3.0 * min(a, b)


def _keep_out(p, centre, rmin):
    """Push p radially out of a small disc round the shoulder (no folded, flipping elbow)."""
    v = p - centre
    r = float(np.hypot(*v))
    if r >= rmin or r < 1e-6:
        return p
    return centre + v / r * rmin


def _up_perp(v):
    p = np.array([v[1], -v[0]])
    if p[1] > 0:
        p = -p
    n = np.hypot(*p)
    return p / n if n > 1e-9 else np.array([0.0, -1.0])


@dataclass
class Support:
    """Small supporting gesture of the other hand (opens forward a little, palm up)."""
    arm: str
    t0: float
    t1: float
    offset: tuple = (12.0, -16.0)     # torso-local wrist offset at full extent
    ramp: float = 0.35

    def amount(self, t):
        if t <= self.t0 or t >= self.t1:
            return 0.0
        return min(smoothstep((t - self.t0) / self.ramp), 1 - smoothstep((t - (self.t1 - self.ramp)) / self.ramp))


@dataclass
class Gaze:
    """Head target over time. keys: list of (t, target) where target is a world point or
    None (= neutral, toward the viewer). Each change eases over `blend` seconds."""
    keys: list
    blend: float = 0.32
    gain: float = 0.35
    lo: float = -12.0
    hi: float = 10.0

    def angle(self, t, neck):
        def a_of(tgt):
            if tgt is None:
                return 0.0
            p = np.asarray(tgt(t) if callable(tgt) else tgt, float)
            return max(self.lo, min(self.hi, self.gain * ang(p - neck)))
        cur = a_of(self.keys[0][1])
        for i in range(1, len(self.keys)):
            tk, tgt = self.keys[i]
            if t < tk:
                break
            cur = lerp(cur, a_of(tgt), smoothstep((t - tk) / self.blend))
        return cur

    def shift_times(self):
        return [k[0] for k in self.keys[1:]]
