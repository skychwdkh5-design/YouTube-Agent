"""ATLAS - the one reusable character component.

    atlas = Atlas()                         # rig + skinned meshes + face, built once
    perf = Performance(atlas, root0=(x, 0))
    perf.walk(t0=1.2, distance=90)          # footsteps -> pelvis -> limbs
    perf.point('f', t0=3.7, target=(x, y), hold_until=5.4)
    perf.support('n', 4.3, 5.3)
    perf.gaze([(0, None), (3.35, (x, y)), (5.9, None)])
    pose = perf.pose(t); solved = atlas.solve(pose)
    atlas.draw(canvas, solved, screen, face_ctrl)      # + debug overlay if wanted

Scenes describe actions and targets; they never rotate part images.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from .mathx import T, S, ap, ang, lerp, smoothstep
from .skeleton import build_rig, ASSETS
from .skin import SkinnedPart, rasterize, quad_mesh, _premult
from .pose import Pose, solve
from .gait import Walk, stand_ankle
from .gesture import Point, Support, Gaze
from .face import Face
from .facetrack import blink

import os


class Atlas:
    def __init__(self, parts_dir=None, ref=None):
        self.rig = build_rig(parts_dir)
        self.skinned = {n: SkinnedPart(p, self.rig.J) for n, p in self.rig.parts.items()}
        self.face = Face(ref or os.path.join(ASSETS, 'ATLAS_reference_sheet.png'), glass=False)
        self._hand_px = {k: _premult(h.img) for k, h in self.rig.hands.items()}

    def solve(self, pose):
        return solve(self.rig, pose)

    def draw(self, canvas, sol, screen, face_ctrl, shadows=True):
        """canvas: float32 premultiplied RGBA (H, W, 4)."""
        if shadows:
            self._shadows(canvas, sol, screen)
        for layer in self.rig.layers:
            if layer in ('hand_n', 'hand_f'):
                s = layer[-1]
                h, Mh = sol.hands[s]
                key = next(k for k, v in self.rig.hands.items() if v is h)
                U, tris = quad_mesh(h.img.shape[1], h.img.shape[0])
                rasterize(canvas, self._hand_px[key], U, _apply(screen @ Mh, U), tris)
            elif layer == 'head':
                im = self.face.render(**face_ctrl)
                a = np.asarray(im).astype(np.float32) / 255
                U, tris = quad_mesh(a.shape[1], a.shape[0])
                rasterize(canvas, _premult(a), U, _apply(screen @ sol.head, U), tris)
            else:
                sp = self.skinned[layer]
                sp.draw(canvas, sp.deform(sol.bones, screen))

    def _shadows(self, canvas, sol, screen):
        H, W = canvas.shape[:2]
        for s in 'nf':
            a = sol.joints[f'ankle_{s}']
            g = ap(screen, (a[0] + 10, self.rig.ground))
            lift = max(0.0, self.rig.ground - 44 - a[1])
            sc = abs(screen[0, 0])
            rx, ry = 34 * sc, 7 * sc
            alpha = 0.42 * max(0.3, 1 - lift / 25)
            x0, x1 = int(max(0, g[0] - rx)), int(min(W, g[0] + rx))
            y0, y1 = int(max(0, g[1] - ry)), int(min(H, g[1] + ry))
            if x1 <= x0 or y1 <= y0:
                continue
            yy, xx = np.mgrid[y0:y1, x0:x1]
            d = ((xx - g[0]) / rx) ** 2 + ((yy - g[1]) / ry) ** 2
            m = (np.clip(1 - d, 0, 1) ** 1.5 * alpha)[..., None]
            canvas[y0:y1, x0:x1] *= (1 - m)
            canvas[y0:y1, x0:x1, 3:4] += m


def _apply(M, U):
    return U @ M[:2, :2].T + M[:2, 2]


# ============================================================================ performance
class Performance:
    """Timeline of actions for one ATLAS in one scene."""

    def __init__(self, atlas, root0=(0.0, 0.0)):
        self.atlas = atlas
        self.rig = atlas.rig
        self.root0 = np.asarray(root0, float)
        self.walks = []
        self.points = []
        self.supports = []
        self._gaze = Gaze([(0.0, None)])
        self.blinks = []
        self.weight_shift = []          # (t0, t1, amount px: + toward the front foot)
        self.lean_walk = 2.0

    # ---- authoring API
    def walk(self, t0, distance, **kw):
        start = self.root0 + [sum(w.D for w in self.walks), 0.0]
        w = Walk(self.rig, start, t0, distance, **kw)
        self.walks.append(w)
        return w

    def point(self, arm, t0, target, hold_until, **kw):
        g = Point(arm, t0, target, hold_until, **kw)
        self.points.append(g)
        return g

    def support(self, arm, t0, t1, **kw):
        g = Support(arm, t0, t1, **kw)
        self.supports.append(g)
        return g

    def gaze(self, keys, **kw):
        self._gaze = Gaze(keys, **kw)

    def shift_weight(self, t0, t1, amount):
        self.weight_shift.append((t0, t1, amount))

    # ---- evaluation
    def _walk_at(self, t):
        cur = None
        for w in self.walks:
            if w.t0 - 0.2 <= t:
                cur = w
        return cur

    def blink_times(self):
        auto = [t + 0.03 for t in self._gaze.shift_times()]
        return sorted(self.blinks + auto)

    def pose(self, t):
        rig, J = self.rig, self.rig.J
        w = self._walk_at(t)
        if w is None:
            root = self.root0.copy()
            px, dip, ww, ph = 0.0, 0.0, 0.0, 0.0
            feet = {s: Walk._flat(stand_ankle(rig, s, root), rig.foot[s]) for s in 'nf'}
        else:
            root = w.root0.copy()
            px, dip, ww, ph = w.pelvis_x(t), w.pelvis_dip(t), w.weight(t), w.phase(t) * w.weight(t)
            feet = {s: w.foot(s, t) for s in 'nf'}
        # idle: breathing and slow, deliberate weight shifts (feet stay planted)
        breath = math.sin(2 * math.pi * t / 3.6)
        shift = 0.0
        for (a, b, amt) in self.weight_shift:
            shift += amt * min(smoothstep((t - a) / 0.6), 1 - smoothstep((t - b) / 0.8))
        g_w = 0.0
        for g in self.points:
            if g.active(t):
                g_w = max(g_w, min(smoothstep((t - g.t0) / 0.4), 1 - smoothstep((t - g.hold_until) / g.relax)))
        p = Pose(root=root)
        p.pelvis_off = np.array([px + shift, dip + 0.25 * abs(shift)])
        p.pelvis_rot = -0.35 * shift
        p.pelvis_cr = 0.022 * ph
        p.torso_cr = 0.022 * ph
        p.torso_rot = self.lean_walk * ww - 1.5 * g_w + 0.4 * breath * (1 - ww)
        p.breath = breath
        p.ankle = {s: feet[s]['ankle'] for s in 'nf'}
        p.foot_pitch = {s: feet[s]['pitch'] for s in 'nf'}
        self._feet = feet
        # pass 1: body without arm targets -> torso / shoulders for this frame
        pre = solve(rig, p)
        Mtor = pre.bones['torso']
        neck = pre.joints['neck']
        p.head_rot = self._gaze.angle(t, neck) + 0.5 * breath
        wr, hd, hp, so = {}, {}, {}, {}
        for s in 'nf':
            swing = (14.0 if s == 'f' else -12.0) * ph
            rest_local = J[f'wrist_{s}'] + np.array([3.0 + swing, -6.0 - 0.25 * abs(swing)])
            sup = next((g for g in self.supports if g.arm == s and g.amount(t) > 0), None)
            hp[s] = 'relaxed' if s == 'f' else 'relaxed_near'
            if sup is not None:
                k = sup.amount(t)
                rest_local = rest_local + np.array(sup.offset) * k
                if k > 0.5:
                    hp[s] = 'palm' if s == 'f' else 'palm_near'
            rest_w = ap(Mtor, rest_local)
            so[s] = np.zeros(2)
            g = next((g for g in self.points if g.arm == s and g.active(t)), None)
            if g is None:
                wr[s] = rest_w
                k_up = sup.amount(t) if sup is not None else 0.0
                hd[s] = (lambda wrist, elbow, k=k_up: ang(wrist - elbow) - 4 - 28 * k)
            else:
                L = rig.lengths[f'upper_{s}'] + rig.lengths[f'fore_{s}']
                so[s] = np.array([0.0, -g.shoulder_lift(t)])
                sh = ap(Mtor, J[f'shoulder_{s}'] + so[s])
                wr[s] = g.wrist(t, sh, rest_w, L)
                hd[s] = (lambda wrist, elbow, g=g: g.hand(t, wrist, elbow)[0])
                pose_name = g.hand(t, wr[s], wr[s] - [1, -1])[1]
                if pose_name:
                    hp[s] = pose_name
        p.wrist = wr
        p.hand_dir = hd
        p.hand_pose = hp
        p.shoulder_off = so
        return p

    def contacts(self, t):
        """Foot contact state used by the overlay and the checks (call after pose(t))."""
        return self._feet


# ============================================================================ debug overlay
def draw_debug(img, sol, screen, pose, feet, rig, t, label=''):
    """Bones, joints, IK targets and foot contacts drawn over the rendered frame."""
    d = ImageDraw.Draw(img, 'RGBA')
    sp = lambda p: tuple(ap(screen, p))
    j = sol.joints
    chains = [('waist', 'neck'), ('pelvis', 'waist')]
    for s in 'nf':
        chains += [(f'neck', f'shoulder_{s}'), (f'shoulder_{s}', f'elbow_{s}'), (f'elbow_{s}', f'wrist_{s}'),
                   ('pelvis', f'hip_{s}'), (f'hip_{s}', f'knee_{s}'), (f'knee_{s}', f'ankle_{s}')]
    for a, b in chains:
        col = (255, 255, 255, 230) if not a.endswith('_f') and not b.endswith('_f') else (170, 190, 255, 230)
        d.line([sp(j[a]), sp(j[b])], fill=col, width=4)
    for k, v in j.items():
        x, y = sp(v)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], outline=(255, 210, 40, 255), width=3)
    # IK targets
    for s in 'nf':
        for tgt, col in ((pose.wrist[s], (40, 230, 255, 255)), (pose.ankle[s], (255, 70, 220, 255))):
            x, y = sp(tgt)
            d.line([x - 11, y - 11, x + 11, y + 11], fill=col, width=3)
            d.line([x - 11, y + 11, x + 11, y - 11], fill=col, width=3)
        # hand direction
        h, Mh = sol.hands[s]
        a0 = sp(ap(Mh, h.wrist))
        a1 = sp(ap(Mh, h.tip))
        d.line([a0, a1], fill=(40, 230, 255, 160), width=2)
    # foot contacts: filled green = planted point, hollow red = foot in the air
    for s in 'nf':
        f = feet[s]
        if f['contact']:
            for p in f['points']:
                x, y = sp(p)
                d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(60, 230, 90, 255))
        else:
            x, y = sp(f['ankle'] + rig.foot[s]['ball'])
            d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(255, 60, 60, 255), width=3)
    try:
        from PIL import ImageFont
        font = ImageFont.load_default(size=30)
    except Exception:
        font = None
    d.text((24, 20), f't={t:5.2f}s  {label}', fill=(255, 255, 255, 255), font=font)
    d.text((24, 60), 'white/blue: bones (near/far)  yellow: joints  cyan X: wrist IK target  '
           'magenta X: ankle IK target  green: planted contact  red ring: foot in air',
           fill=(200, 205, 215, 255), font=ImageFont.load_default(size=20) if font else None)
