"""Rig checks for ATLAS. Run before any scene render after a rig change:

    python3 tests/check_rig.py [--sheet extreme.png] [--json report.json]

Checks (exit code 1 on any FAIL):
  lengths      segment lengths constant in every frame of the tech test and extreme poses
  bend         elbows/knees never switch side (techtest + full circles of targets)
  reach        reachable targets are met; unreachable ones stop on the target ray at the
               reach limit (no stretch, no NaN) with error = distance beyond the limit
  continuity   sweeping a target around the limb never makes the mid joint jump
  planted      planted contact points (from the SOLVED foot bones) do not move
  stop         no foot moves after the walk's last step has landed
  clearance    swinging foot clears the floor; no sole point ever goes below it
  pelvis       pelvis advance is monotone during the walk and settles (no drift)
  joints       no transparent holes at elbows / knees / hips / waist in extreme poses
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from atlas_rig.character import Atlas, Performance                      # noqa: E402
from atlas_rig.ik import two_bone, bend_side, max_reach, REACH_MAX       # noqa: E402
from atlas_rig.pose import Pose                                         # noqa: E402
from atlas_rig.gait import stand_ankle                                 # noqa: E402
from atlas_rig.mathx import ap, T, S                                    # noqa: E402

RESULTS = []


def check(name, ok, detail):
    RESULTS.append({'check': name, 'pass': bool(ok), 'detail': detail})
    print(f"{'PASS' if ok else 'FAIL'}  {name:<12} {detail}")


def techtest_checks(atlas):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scenes'))
    import techtest as tt
    _, perf, screen, _ = tt.build_with(atlas)
    rig = atlas.rig
    fps, n = tt.FPS, int(tt.DUR * tt.FPS)
    walk = perf.walks[0]
    len_err = 0.0
    bends = {k: set() for k in rig.bend}
    foot_err = 0.0
    arm_err = 0.0
    arm_clamps = 0
    drift = 0.0
    after_stop = 0.0
    below = 0.0
    min_clear = 1e9
    drop = 0.0
    hold = {'n': None, 'f': None}
    stop_ref = {}
    px_prev = -1e9
    px_back = 0.0
    drops = []
    for i in range(n):
        t = i / fps
        p = perf.pose(t)
        sol = atlas.solve(p)
        feet = perf.contacts(t)
        for k, L in rig.lengths.items():
            len_err = max(len_err, abs(sol.lengths[k] - L))
        for k in rig.bend:
            bends[k].add(sol.bend[k])
        drop = max(drop, sol.pelvis_drop)
        for s in 'nf':
            foot_err = max(foot_err, sol.ik[f'leg_{s}']['err'])
            arm_err = max(arm_err, sol.ik[f'arm_{s}']['err'])
            arm_clamps += sol.ik[f'arm_{s}']['clamp'] != ''
            Mf = sol.bones[f'foot_{s}']
            F = rig.foot[s]
            pts = {k: ap(Mf, rig.J[f'ankle_{s}'] + F[k]) for k in ('heel', 'ball', 'toe')}
            low = max(v[1] for v in pts.values())
            below = max(below, low - rig.ground - 0.5)
            c = feet[s]['contact']
            if c is None:
                st = next(st for st in walk.steps if st.foot == s and st.lift <= t < st.land)
                u = (t - st.lift) / (st.land - st.lift)
                if 0.2 < u < 0.8:
                    min_clear = min(min_clear, rig.ground - low)
                hold[s] = None
            else:
                key = {'flat': ('heel', 'ball'), 'toe': ('toe',), 'heel': ('heel',)}[c]
                cur = np.concatenate([pts[k] for k in key])
                if hold[s] is None or hold[s][0] != c:
                    hold[s] = (c, cur)
                else:
                    drift = max(drift, float(np.abs(cur - hold[s][1]).max()))
            if t >= walk.t_end:
                a = sol.joints[f'ankle_{s}']
                stop_ref.setdefault(s, a)
                after_stop = max(after_stop, float(np.hypot(*(a - stop_ref[s]))))
        drops.append((round(t, 2), round(sol.pelvis_drop, 2)))
        if walk.t0 <= t <= walk.t_settle + 0.5:
            px = walk.pelvis_x(t)
            px_back = max(px_back, px_prev - px)
            px_prev = px
    print('pelvis drop: rest %.2f px, max %.2f px' % (drops[0][1], max(d[1] for d in drops)))
    settle_move = abs(walk.pelvis_x(walk.t_settle + 1.0) - walk.D)
    check('lengths', len_err < 0.01, f'max segment length error {len_err:.4f} px (techtest)')
    check('bend', all(len(v) == 1 and list(v)[0] == rig.bend[k] for k, v in bends.items()),
          'bend sides seen: ' + ', '.join(f'{k}:{sorted(v)}' for k, v in bends.items()))
    check('reach', foot_err < 0.3, f'feet: max IK error {foot_err:.3f} px; pelvis lowered by up to {drop:.2f} px to keep feet reachable')
    check('reach', arm_err < 0.5, f'arms: max IK error {arm_err:.3f} px, {arm_clamps} clamped frames')
    check('planted', drift < 0.3, f'max movement of planted contact points {drift:.3f} px (heel/ball, from solved bones)')
    check('stop', after_stop < 0.05, f'ankles move {after_stop:.3f} px after the last step lands')
    check('clearance', below < 0.01 and min_clear > 4, f'sole never below floor (worst {max(0, below):.3f} px); mid-swing clearance >= {min_clear:.1f} px')
    check('pelvis', px_back < 0.01 and settle_move < 0.01, f'pelvis never moves back ({px_back:.4f} px), rests {settle_move:.4f} px from the stop mark')


def ik_sweep():
    worst_len, worst_err, jumps, flips, nan = 0.0, 0.0, 0.0, 0, 0
    for L1, L2, bend in ((96, 80, -1), (60, 54, 1), (60, 51.3, 1)):
        for r_k in (0.05, 0.3, 0.6, 0.9, 0.97, 0.99, 1.0, 1.05, 1.5, 3.0):
            prev = None
            for a in np.arange(0, 361, 1.0):
                r = (L1 + L2) * r_k
                tgt = np.array([math.cos(math.radians(a)), math.sin(math.radians(a))]) * r
                mid, end, info = two_bone((0, 0), tgt, L1, L2, bend)
                if not np.all(np.isfinite(mid)) or not np.all(np.isfinite(end)):
                    nan += 1
                    continue
                worst_len = max(worst_len, abs(np.hypot(*mid) - L1), abs(np.hypot(*(end - mid)) - L2))
                flips += bend_side((0, 0), mid, end) != bend
                if r <= max_reach(L1, L2) and r >= abs(L1 - L2) + 0.01:
                    worst_err = max(worst_err, info['err'])
                else:
                    # predictable: end lies on the target ray, never beyond the hard limit
                    u_ = tgt / max(r, 1e-9)
                    on_ray = abs(u_[0] * end[1] - u_[1] * end[0]) < 1e-6 and (u_ @ end) > 0
                    if not on_ray or np.hypot(*end) > (L1 + L2) * REACH_MAX + 1e-6:
                        nan += 1
                if prev is not None:
                    jumps = max(jumps, np.hypot(*(mid - prev)) / L1)
                prev = mid
    check('lengths', worst_len < 1e-6, f'IK sweep: max segment length error {worst_len:.2e} px')
    check('bend', flips == 0, f'IK sweep: {flips} bend-side flips over 10 radii x 361 angles x 3 limbs')
    check('reach', worst_err < 1e-6 and nan == 0, f'IK sweep: reachable targets met (max err {worst_err:.1e}); out-of-range ends on the ray at the limit ({nan} violations)')
    check('continuity', jumps < 0.06, f'IK sweep: mid joint moves <= {jumps * 100:.1f}% of the upper segment per 1 deg of target sweep')


def extreme_poses(atlas):
    rig, J = atlas.rig, atlas.rig.J
    root = np.zeros(2)
    poses = []
    def P(**kw):
        p = Pose(root=root, keep_reach=True)
        p.ankle = {s: stand_ankle(rig, s, root) for s in 'nf'}
        p.wrist = {}
        for k, v in kw.items():
            setattr(p, k, v)
        return p
    sh_f, sh_n = J['shoulder_f'], J['shoulder_n']
    poses.append(('arm up 160deg', P(wrist={'f': sh_f + np.array([30, -100]), 'n': sh_n + np.array([-20, 105])})))
    poses.append(('elbow 130deg', P(wrist={'f': sh_f + np.array([30, 10]), 'n': sh_n + np.array([25, 15])})))
    poses.append(('reach beyond', P(wrist={'f': sh_f + np.array([400, -50]), 'n': sh_n + np.array([300, 60])})))
    poses.append(('deep knee', P(pelvis_off=np.array([0, 55.0]), keep_reach=False)))
    poses.append(('lunge', P(ankle={'n': stand_ankle(rig, 'n', root) + [80, 0], 'f': stand_ankle(rig, 'f', root) + [-70, 0]})))
    poses.append(('torso lean', P(torso_rot=12.0, pelvis_rot=-4.0,
                                  wrist={'f': sh_f + np.array([90, 20]), 'n': sh_n + np.array([60, 60])})))
    screen = T(300, 700) @ S(1.4) @ T(-J['pelvis'][0], -rig.ground)
    tiles = []
    holes = []
    for name, p in poses:
        sol = atlas.solve(p)
        can = np.zeros((760, 600, 4), np.float32)
        atlas.draw(can, sol, screen, dict(open_=0.0), shadows=False)
        al = can[..., 3]
        worst = 1.0
        for jn in ('elbow_n', 'elbow_f', 'knee_n', 'knee_f', 'hip_n', 'hip_f', 'waist'):
            c = ap(screen, sol.joints[jn])
            r = 5 * 1.4
            yy, xx = np.mgrid[0:al.shape[0], 0:al.shape[1]]
            m = (xx - c[0]) ** 2 + (yy - c[1]) ** 2 < r * r
            if m.any():
                cov = float(al[m].min())
                worst = min(worst, cov)
                if cov < 0.95:
                    holes.append(f'{name}:{jn}={cov:.2f}')
        lens = max(abs(sol.lengths[k] - L) for k, L in rig.lengths.items())
        flips = [k for k in rig.bend if sol.bend[k] != rig.bend[k]]
        check('lengths', lens < 0.01, f'extreme pose "{name}": length error {lens:.4f} px; bend flips {flips or "none"}; min joint coverage {worst:.2f}')
        img = Image.new('RGB', (600, 760), (40, 44, 56))
        rgb = Image.fromarray((np.clip(can[..., :3] / np.maximum(can[..., 3:4], 1e-6), 0, 1) * 255).astype(np.uint8))
        img.paste(rgb, (0, 0), Image.fromarray((np.clip(al, 0, 1) * 255).astype(np.uint8)))
        from PIL import ImageDraw
        ImageDraw.Draw(img).text((12, 10), name, fill=(255, 255, 255))
        tiles.append(img)
    check('joints', not holes, 'no transparent holes at joints in extreme poses' if not holes else 'holes: ' + ', '.join(holes))
    sheet = Image.new('RGB', (600 * 3, 760 * 2))
    for k, im in enumerate(tiles):
        sheet.paste(im, ((k % 3) * 600, (k // 3) * 760))
    return sheet


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--sheet', default=None)
    a.add_argument('--json', default=None)
    args = a.parse_args()
    atlas = Atlas()
    ik_sweep()
    techtest_checks(atlas)
    sheet = extreme_poses(atlas)
    if args.sheet:
        sheet.save(args.sheet)
    if args.json:
        json.dump(RESULTS, open(args.json, 'w'), indent=1)
    bad = [r for r in RESULTS if not r['pass']]
    print(f'\n{len(RESULTS) - len(bad)}/{len(RESULTS)} checks passed')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
