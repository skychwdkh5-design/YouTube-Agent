"""Footstep-driven locomotion.

Order of authority: footsteps -> pelvis -> limbs. The planner places the footsteps
first (length and timing), then derives the pelvis path from where the feet are, so
the body's advance always matches the step length and cadence. Planted feet are
fixed in WORLD coordinates (camera moves never touch them).

Foot phases per step: flat stance -> heel-off (rigid boot rolls on its toe tip, toe fixed)
-> swing (clearance arc) -> heel strike (toe up) -> roll to flat (heel fixed).
"""
import math
from dataclasses import dataclass

import numpy as np

from .mathx import smoothstep, smootherstep, pchip

HEEL_OFF = 0.14      # s of heel peel before lift
HEEL_MAX = 18.0      # deg of heel lift at toe-off
LAND = 9.0           # deg of toe-up at heel strike
ROLL = 0.12          # s from heel strike to flat foot
CLEAR = 13.0         # rest px of swing clearance (sole above the floor)


def _rot(v, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]])


@dataclass
class Step:
    foot: str
    lift: float
    land: float
    x0: float     # displacement of this foot (world px) before / after the step
    x1: float


def stand_ankle(rig, s, root):
    """World ankle position with that boot's sole flat on the floor."""
    return np.array([rig.J[f'ankle_{s}'][0] + root[0], rig.ground - rig.foot[s]['heel'][1] + root[1]])


class Walk:
    """A walk of `distance` (world px, +x = forward) starting at t0 from a standing pose.

    Steps alternate feet; the last step closes the stance (feet together again), so a
    two-step walk = lead step + closing step. No step happens after the closing one.
    """

    def __init__(self, rig, root0, t0, distance, lead='n', step_len=95.0, step_time=0.62,
                 swing_time=0.48):
        self.rig = rig
        self.root0 = np.asarray(root0, float)
        self.t0 = t0
        self.D = float(distance)
        n_prog = max(1, math.ceil(abs(self.D) / step_len))
        disp = {'n': 0.0, 'f': 0.0}
        steps = []
        foot = lead
        t = t0 + HEEL_OFF
        for k in range(1, n_prog + 1):
            x1 = self.D * k / n_prog
            steps.append(Step(foot, t, t + swing_time, disp[foot], x1))
            disp[foot] = x1
            foot = 'f' if foot == 'n' else 'n'
            t += step_time
        steps.append(Step(foot, t, t + swing_time * 0.92, disp[foot], self.D))   # closing step
        disp[foot] = self.D
        self.steps = steps
        self.t_end = steps[-1].land + ROLL
        # ---- pelvis path from the footsteps (monotone, so it never slides back or overshoots)
        keys_t, keys_x = [t0 - 0.05, steps[0].lift - 0.04], [0.0, 0.06 * self.D]
        fpos = {'n': 0.0, 'f': 0.0}
        for st in steps:
            other = 'f' if st.foot == 'n' else 'n'
            prev = keys_x[-1]
            last = st is steps[-1]
            if not last:     # mid-stance: pelvis just past the support foot
                mid = max(prev, fpos[other] + 0.22 * (st.x1 - fpos[other]))
                land = 0.5 * (st.x1 + fpos[other])
            else:            # closing step: decelerate onto the closed stance
                mid = prev + 0.72 * (self.D - prev)
                land = self.D - 0.015 * self.D
            keys_t += [0.5 * (st.lift + st.land), st.land]
            keys_x += [mid, max(mid, land)]
            fpos[st.foot] = st.x1
        keys_t.append(steps[-1].land + 0.32)
        keys_x.append(self.D)
        self._px = pchip(keys_t, keys_x)
        self.t_settle = keys_t[-1]

    # ------------------------------------------------------------------ feet
    def _ankle_rest(self, s):
        return stand_ankle(self.rig, s, self.root0)

    def foot(self, s, t):
        """-> dict(ankle world, pitch deg, contact: 'flat'|'ball'|'heel'|None, points)"""
        F = self.rig.foot[s]
        base = self._ankle_rest(s)
        x = 0.0
        for st in self.steps:
            if st.foot != s:
                continue
            a0 = base + [st.x0, 0.0]
            a1 = base + [st.x1, 0.0]
            if t < st.lift - HEEL_OFF:
                return self._flat(a0, F)
            if t < st.lift:                                  # heel peels off, ball planted
                th = HEEL_MAX * smoothstep((t - (st.lift - HEEL_OFF)) / HEEL_OFF)
                toe = a0 + F['toe']        # rigid boot: rolls onto the toe tip
                return {'ankle': toe + _rot(-F['toe'], th), 'pitch': th, 'contact': 'toe',
                        'points': [toe]}
            if t < st.land:                                  # swing
                u = (t - st.lift) / (st.land - st.lift)
                start = a0 + F['toe'] + _rot(-F['toe'], HEEL_MAX)
                heel1 = a1 + F['heel']
                end = heel1 + _rot(-F['heel'], -LAND)
                p = start + (end - start) * smootherstep(u)
                p = p + [0.0, -CLEAR * math.sin(math.pi * u) ** 0.9]
                th = HEEL_MAX * (1 - smoothstep(u / 0.45)) - LAND * smoothstep((u - 0.5) / 0.5)
                return {'ankle': p, 'pitch': th, 'contact': None, 'points': []}
            if t < st.land + ROLL:                           # heel strike -> flat, heel fixed
                th = -LAND * (1 - smoothstep((t - st.land) / ROLL))
                heel = a1 + F['heel']
                return {'ankle': heel + _rot(-F['heel'], th), 'pitch': th, 'contact': 'heel',
                        'points': [heel]}
            x = st.x1
        return self._flat(base + [x, 0.0], F)

    @staticmethod
    def _flat(a, F):
        return {'ankle': a, 'pitch': 0.0, 'contact': 'flat', 'points': [a + F['heel'], a + F['ball']]}

    # ------------------------------------------------------------------ body
    def pelvis_x(self, t):
        return self._px(t)

    def pelvis_dip(self, t):
        """Lowest in double support (just after each heel strike), highest mid-stance."""
        d = 0.0
        for st in self.steps:
            d += 3.2 * math.exp(-((t - (st.land + 0.05)) / 0.12) ** 2)
        return d

    def weight(self, t):
        """0 standing .. 1 walking (for arm swing, counter-rotation)."""
        a = smoothstep((t - (self.t0 - 0.05)) / 0.3)
        b = 1 - smoothstep((t - self.steps[-1].land + 0.1) / 0.45)
        return min(a, b)

    def phase(self, t):
        """-1..1: + when the near foot is ahead of the far foot."""
        dn = self.foot('n', t)['ankle'][0] - self._ankle_rest('n')[0]
        df = self.foot('f', t)['ankle'][0] - self._ankle_rest('f')[0]
        return max(-1.0, min(1.0, (dn - df) / max(1.0, abs(self.D) * 0.6)))

    def swinging(self, t):
        return any(st.lift <= t < st.land for st in self.steps)
