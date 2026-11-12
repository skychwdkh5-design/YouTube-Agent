"""ATLAS as the episode host: shots (placement on screen), actions keyed to the narration,
face driven by the real voice. Everything goes through the shared rig (production/atlas-rig).

Screen placement is per SHOT (camera framing): feet anchor (fx, fy), scale and facing
(+1 = faces right, -1 = mirrored, faces left). Inside a shot ATLAS moves only by walking;
placement/scale/facing may change only at a shot boundary (a cut), like a camera change.
"""
import json
import math
import os
import sys
from dataclasses import dataclass

import numpy as np

RIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'atlas-rig')
sys.path.insert(0, RIG)
from atlas_rig.character import Atlas, Performance            # noqa: E402
from atlas_rig.mathx import T, S, ap, smoothstep               # noqa: E402
from atlas_rig.facetrack import lip_tracks, blink              # noqa: E402
from atlas_rig.pose import solve                               # noqa: E402

FPS = 30


def seq(keys, blend=0.5):
    """Target that moves smoothly between screen points: keys = [(t, point|callable), ...].
    The hand travels to the next point over `blend` s (ease in/out) instead of jumping."""
    keys = sorted(keys, key=lambda k: k[0])
    val = lambda p, t: np.asarray(p(t) if callable(p) else p, float)

    def f(t):
        cur = val(keys[0][1], t)
        for tk, p in keys[1:]:
            if t <= tk:
                break
            u = smoothstep((t - tk) / blend)
            cur = cur + (val(p, t) - cur) * u
        return cur
    return f


@dataclass
class Shot:
    t0: float
    t1: float
    fx: float            # screen x of the pelvis at the shot start
    fy: float            # screen y of the floor line under the boots
    scale: float = 1.05
    face: int = 1        # +1 faces right, -1 faces left (mirrored drawing)


class Host:
    def __init__(self, atlas, shots, wav, words_json, dur, seed=7, offset=0.0):
        self.atlas = atlas
        self.rig = atlas.rig
        self.shots = sorted(shots, key=lambda s: s.t0)
        self.dur = dur
        self.perf = Performance(atlas, root0=(0.0, 0.0))
        self.words = [dict(w, start=w['start'] - offset, end=w['end'] - offset)
                      for w in json.load(open(words_json))['words'] if offset - 1 < w['end'] < offset + dur + 1]
        self.op, self.wd = lip_tracks(wav, words_json, offset, dur, FPS)
        self.rng = np.random.default_rng(seed)
        self.brow_ev = []          # (t, amount, dur)
        self.look_keys = [(0.0, -0.6)]
        self.used = {'n': [], 'f': []}   # busy intervals per arm
        self._walk_x = []          # (t_end, world distance) completed walks, for shot anchors

    # ---------------------------------------------------------------- placement
    def shot_at(self, t):
        cur = self.shots[0]
        for s in self.shots:
            if s.t0 <= t + 1e-9:
                cur = s
        return cur

    def world_x_at(self, t):
        """Root world x (sum of walks finished by t, plus the part of a walk in progress)."""
        x = 0.0
        for w in self.perf.walks:
            if t >= w.t_settle:
                x += w.D
            elif t >= w.t0:
                x += w.pelvis_x(t)
        return x

    def screen(self, t):
        s = self.shot_at(t)
        x_anchor = self.rig.J['pelvis'][0] + self.world_x_at(s.t0)
        return T(s.fx, s.fy) @ S(s.face * s.scale, s.scale) @ T(-x_anchor, -self.rig.ground)

    def to_world(self, t, p):
        return ap(np.linalg.inv(self.screen(t)), p)

    # ---------------------------------------------------------------- authoring
    def _busy(self, arm, a, b):
        return any(not (b <= x0 or a >= x1) for x0, x1 in self.used[arm])

    def walk(self, t0, screen_dist, **kw):
        s = self.shot_at(t0)
        w = self.perf.walk(t0, screen_dist / s.scale, **kw)
        assert w.t_settle < s.t1, f'walk at {t0} must settle inside its shot'
        return w

    def point(self, t0, target, hold_until, arm='f', gaze_lead=0.35, look_back=0.5, **kw):
        """target: screen point (or callable t -> screen point)."""
        tw = (lambda t, f=target: self.to_world(t, f(t))) if callable(target) else self.to_world(t0, target)
        # one gesture owns an arm at a time: an earlier point on this arm relaxes before this one starts
        for p in self.perf.points:
            if p.arm == arm and p.t0 < t0 < p.t_end + 0.05:
                p.hold_until = max(p.t0 + p.prep + p.move + 0.1, t0 - 0.08 - p.relax)
                if p.t_end > t0 - 0.03:
                    t0 = p.t_end + 0.03
        # close framings magnify every move on screen: give big gestures more time there
        k = max(1.0, (self.shot_at(t0).scale / 1.05) ** 0.5)
        kw.setdefault('move', 0.5 * k)
        kw.setdefault('prep', 0.22 * k)
        kw.setdefault('relax', 0.75 * k)
        g = self.perf.point(arm, t0, tw, hold_until, **kw)
        self.used[arm].append((t0 - 0.1, g.t_end + 0.1))
        self.gaze(t0 - gaze_lead, tw, look=0.8)
        self.gaze(g.hold_until + look_back, None, look=-0.6)
        self.brow(g.t_acc, 0.55, 0.9)
        return g

    def support(self, t0, t1, arm='n', offset=(12.0, -16.0)):
        if self._busy(arm, t0, t1):
            return None
        self.used[arm].append((t0, t1))
        return self.perf.support(arm, t0, t1, offset=offset)

    def gaze(self, t, target, look=None):
        """target: world point, screen point marked ('s', (x, y)), or None = viewer."""
        if isinstance(target, tuple) and len(target) == 2 and target[0] == 's':
            target = self.to_world(t, target[1])
        keys = list(self.perf._gaze.keys) + [(t, target)]
        keys.sort(key=lambda k: k[0])
        self.perf.gaze(keys)
        if look is not None:
            self.look_keys.append((t, look))

    def brow(self, t, amount, dur):
        self.brow_ev.append((t, amount, dur))

    def shift(self, t0, t1, amount):
        self.perf.shift_weight(t0, t1, amount)

    # ---------------------------------------------------------------- automatic layer
    def auto(self, emphasis=(), beat_every=3.2, idle_every=(6.0, 9.0)):
        """Small speech beats on emphasised words, brows, idle weight shifts, blinks."""
        emph = {e.lower() for e in emphasis}
        last = -10.0
        arm_cycle = ['n', 'n', 'f']
        k = 0
        for w in self.words:
            txt = w['text'].lower().strip('.,!?;:"\'’()')
            key = (txt in emph) or any(ch.isdigit() for ch in txt)
            if not key or w['start'] - last < beat_every:
                continue
            a = w['start'] - 0.18
            b = a + 0.95
            arm = arm_cycle[k % 3]
            if self._walking(a - 0.3, b + 0.3):
                continue
            if self._busy(arm, a - 0.3, b + 0.3):
                arm = 'n' if arm == 'f' else 'f'
                if self._busy(arm, a - 0.3, b + 0.3):
                    continue
            off = (10.0, -13.0) if arm == 'n' else (8.0, -10.0)
            if self.support(a, b, arm, off):
                self.brow(w['start'], 0.35, 0.6)
                last = w['start']
                k += 1
        # idle weight shifts while standing and not gesturing hard
        t = 2.0
        sign = 1
        while t < self.dur - 2:
            span = self.rng.uniform(*idle_every)
            a, b = t, t + min(span * 0.7, 5.0)
            if not self._walking(a - 0.5, b + 0.5):
                self.shift(a, b, 2.2 * sign)
                sign = -sign
            t += span
        # blinks: irregular, plus one on every gaze shift (added by Performance)
        t = 1.2
        bl = []
        while t < self.dur:
            bl.append(t)
            if self.rng.random() < 0.12:
                bl.append(t + 0.28)        # occasional double blink
            t += self.rng.uniform(2.3, 5.6)
        self.perf.blinks = bl

    def _walking(self, a, b):
        return any(not (b <= w.t0 - 0.2 or a >= w.t_settle) for w in self.perf.walks)

    # ---------------------------------------------------------------- per frame
    def face(self, t, i):
        br = 0.0
        for (t0, amt, d) in self.brow_ev:
            br = max(br, amt * min(smoothstep((t - t0 + 0.12) / 0.18), 1 - smoothstep((t - t0 - d) / 0.4)))
        look = self.look_keys[0][1]
        for (tk, v) in sorted(self.look_keys):
            if t >= tk:
                look = look + (v - look) * smoothstep((t - tk) / 0.18)
        # small saccades while looking at the viewer
        sac = 0.15 * math.sin(t * 1.7) * math.sin(t * 0.63)
        i = min(i, len(self.op) - 1)
        return dict(open_=float(self.op[i]), width=float(self.wd[i]),
                    blink=blink(t, self.perf.blink_times()), brow=br, look=max(-1, min(1, look + sac)))

    def _raw_drop(self, k):
        if k not in self._drops:
            self._drops[k] = solve(self.rig, self.perf.pose(k / FPS)).pelvis_drop
        return self._drops[k]

    def pose(self, t, i):
        """Pose for frame i with the keep-reach pelvis drop smoothed over +-6 frames, so a
        nearly straight leg never makes the knee pop at heel-off / heel strike."""
        if not hasattr(self, '_drops'):
            self._drops = {}
        m = [max(self._raw_drop(j) for j in range(k - 3, k + 4)) for k in range(i - 3, i + 4)]
        p = self.perf.pose(t, head_extra=self.speech_nod(i))
        p.drop_floor = sum(m) / len(m)
        return p

    def speech_nod(self, i):
        i = min(i, len(self.op) - 1)
        return 1.4 * self.op[i]
