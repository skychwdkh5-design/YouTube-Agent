# ATLAS rig — architecture, parameters, adding actions

Code: `production/atlas-rig/` (package `atlas_rig`). The rules every agent must follow are in
`/AGENTS.md`; this document explains how the system works.

## 1. Audit of the previous implementation (v1–v5, `production/atlas-host-test/tools/`)

These findings come from reading `rig2.py` / `render2.py` / `render_atlas.py`:

- **No hierarchy object.** Each part matrix was computed inline in the scene's `frame()`. The torso,
  pelvis, arms, legs, head and helmet were independent matrices with hand-chosen pivots, and each
  scene file was a full copy of the renderer (`render_atlas.py` → `render2.py`).
- **Arms were FK keyframes.** `near_u`, `near_f_dir` and `far_u_aim` were per-scene angle curves.
  Only the far forearm aimed at a screen point, and the hand was rotated on its own. There was no
  arm IK.
- **Legs had 2-bone IK, but:**
  - the knee side was picked per frame as "the candidate with the larger x", which can flip;
  - the reach limit `min(dist, L1+L2-0.6)` let the foot silently miss its target (it was only
    logged).
- **Locomotion was not coupled.** The root followed its own curve (`root_x`), and steps were
  scheduled at a fixed period with an "ahead" fudge. The result was foot stretch or misses (up to
  25 px in v4 tuning), fast shuffle steps, and a half-squat walk.
- **No deformation.** Every PNG was one rigid affine, plus a `width_k` squash. Joints were hidden
  only by overlap and draw order, so the cloth never bent.
- **Constant crouch while walking.** The pelvis "dip" was a fixed offset.
- **Settle shuffles.** Settle steps of 4–9 px after the stop.

## 2. Architecture

| Module | Holds |
|---|---|
| `skeleton.py` | **The single source of truth.** Rest joints, bones and parents, part images, two-anchor placement, part thickness, skin zones, mesh resolution, layer order, hand poses, sole contact points, floor height, bend sides. |
| `ik.py` | Two-bone IK. The bend side is fixed per limb (`rig.bend`). The reach limit has a soft band. |
| `pose.py` | `Pose` (controls and targets) → `solve()` → bone matrices, joints, diagnostics. Lowers the pelvis rather than miss a planted foot (`keep_reach`). |
| `skin.py` | Grid meshes per part, linear-blend skin weights, triangle rasteriser (one owner per pixel, so there are no seams). |
| `gait.py` | Footstep planner: steps → pelvis path → ankle targets and foot pitch (heel-off on the toe tip, swing arc, heel strike, roll to flat). |
| `gesture.py` | `Point` (prep → move → accent → soft hold → relax), `Support` (other hand), `Gaze`. |
| `character.py` | `Atlas` (the reusable component: rig, meshes, face, draw) and `Performance` (the action timeline → `Pose`). Also the debug overlay. |
| `face.py`, `facetrack.py` | Head on the sheet's calm 3/4 face, plus jaw, mouth, blink and brow controls, all from the **existing** narration. |

Hierarchy:

- `pelvis` (root, driven by the gait) → `torso` (waist) → `head` / `helmet`
- `torso` → `upper_{n,f}` → `fore_{n,f}` → `hand_{n,f}`
- `pelvis` → `thigh_{n,f}` → `shin_{n,f}` → `foot_{n,f}`

`n` is the near (camera-side) limb and `f` is the far one.

Coordinate frames:

- **rest**: the sheet frame the parts were fitted in.
- **world**: rest + character root. Planted feet live here.
- **screen**: `camera @ world`.

Camera moves change only `screen`, so foot locks stay intact.

Draw order (back → front):

1. Far limbs: `hand_f`, `fore_f`, `upper_f`
2. Legs, far then near: `foot_f`, `shin_f`, `thigh_f`, `foot_n`, `shin_n`, `thigh_n`
3. Body: `pelvis`, `head`, `torso`, `helmet`
4. Near arm: `upper_n`, `fore_n`, `hand_n`

## 3. Joints and IK

- **Arms:** shoulder → elbow → wrist via IK. The hand is aimed by a direction, so the hand image is
  never a free rotation of the arm.
- **Legs:** hip → knee → ankle via IK. The foot pitches about the toe tip (heel-off), the heel
  (landing) or the ankle.
- **Bend sides:**

  | Limb | `rig.bend` value | Direction |
  |---|---|---|
  | Knees | −1 | forward |
  | Elbows | +1 | back / down |

  The bend side is a sign, never chosen per frame.
- **Reach handling** (`REACH_MAX = 0.998`, `SOFT = 0.018`):
  - A target inside `max_reach` is met exactly.
  - Beyond that, the end eases toward the hard limit and then stops **on the root→target ray**.
    There is no stretch, and `info['clamp']` reports `'far'`.
  - A target closer than `|L1−L2|` reports `'near'`.
  - Segment lengths are rigid by construction: `bone_matrix` is rotation only.

## 4. Deformation (skinning)

Each limb or torso part is a grid mesh (`Part.grid`, for example 6×30 for legs). A vertex near a
joint blends between its own bone and the neighbour (`Zone`):

- **Weight function:** `cap·(1−smoothstep(d/zone))` inside the part. For the cap that extends past
  the joint it rises to 1, so both overlapping drawings deform the same way across the joint.
- **Rigid pieces stay single-bone:** knee pads (on the thigh), elbow pads (on the upper arm), the
  shoulder pad, boots and hands. The next segment's cloth bends underneath them.

| Zone | Bone pair | Length (rest px) | Cap |
|---|---|---|---|
| Waist | torso ↔ pelvis | 16 | 0.5 |
| Hip | thigh ↔ pelvis | 14 | 0.5 |
| Knee | shin ↔ thigh | 16 | 0.5 |
| Ankle | shin ↔ foot | 10 | 0.3 |
| Elbow | forearm ↔ upper arm | 14 | 0.5 |
| Shoulder | upper arm ↔ torso | 8 | 0.25 |

The engine is numpy and PIL only. The rasteriser assigns every pixel to exactly one triangle and
samples premultiplied colour bilinearly, using a ½-scale level when the part is minified.

**Limit:** this is linear-blend skinning on flat paintings. The cloth bends and closes, but it does
not grow new folds. Strong bends (more than ~110° at the elbow) compress the inner side.
Hand-painted corrective bend drawings would be the next step (see §8).

## 5. Locomotion (`gait.Walk`)

1. **Footsteps first.**
   - The step count is `ceil(distance/step_len)` plus a closing step, so a two-step walk is a lead
     step and a closing step.
   - Times: lift at `t0 + HEEL_OFF + k·step_time`, landing after `swing_time`.
2. **The pelvis path follows from the feet.** It is a monotone cubic through these keys:
   - start at 0;
   - small anticipation before the first lift;
   - mid-stance just past the support foot;
   - between the feet at each double support;
   - the closed stance at the end.

   The pelvis never slides back and never overshoots. It settles 0.32 s after the last landing and
   then stays fixed.
3. **Pelvis height:**
   - a small dip at each double support;
   - `keep_reach` lowers it only as much as needed for the feet to stay exactly on target.
4. **Foot phases:**
   - flat (heel and ball locked);
   - heel-off (`HEEL_OFF` 0.14 s, up to 18°, the toe tip locked);
   - swing (13 px clearance arc, with pitch unrolling and the toe lifting);
   - heel strike (9° toe-up), then roll to flat (`ROLL` 0.12 s, the heel locked).
5. **No action after the closing step lands.** There are no more steps and no bouncing. Idle weight
   shifts (`Performance.shift_weight`) move the pelvis a few px while the feet stay planted.
6. **Counter-rotation and arm swing** come from the foot phase (`Walk.phase`). They show as an
   opposite width change of the torso and pelvis, plus wrist swing.

## 6. Gestures (`gesture.Point`, `Support`, `Gaze`)

- **`Point(arm, t0, target, hold_until)`** runs through these phases:

  | Phase | Default | What the wrist does |
  |---|---|---|
  | prep | 0.22 s | Gathers slightly in and up. |
  | move | 0.5 s | Follows a quadratic Bezier, bowed upward, to an aim point at 90% of arm length (soft elbow). |
  | accent | 0.28 s | Pushes 6 px toward the target and settles. |
  | hold | until `hold_until` | The elbow softens and the hand drops about 9°. |
  | relax | 0.75 s | Follows a curved path back to rest. |

  - The hand turns toward the target 0.1 s after the wrist starts moving.
  - The hand image swaps (relaxed ↔ point) while the hand is moving.
  - The shoulder lifts 3 px while the arm is raised, and the torso opens slightly.
- **`Gaze([(t, target|None), …])`:** the head turns toward the target (gain 0.35, clamped −12..+10°).
  Put the gaze key about 0.35 s before the gesture's `t0`. A blink is added automatically on each
  gaze shift.
- **`Support(arm, t0, t1)`:** the other hand opens forward and up a little (palm pose) during the
  explanation, then returns.
- **Rest arms** hang with soft elbows, swing during walks and stay out of the chest area.

## 7. Adding a new action

1. **Express it as targets.** That means ankle or wrist world points, a pelvis offset, gaze targets,
   or a hand pose name. Do not express it as part rotations.
2. **Write it as a small class** (like `Point` or `Support`) in `gesture.py`, or a planner in
   `gait.py`. Add a method on `Performance` that schedules it, and evaluate it inside
   `Performance.pose()`.
3. **Add geometry only in `skeleton.py`:** new hand poses go in `hands`, and new parts or zones go
   in `parts`.
4. **Test it before any scene uses it:**
   1. Extend `scenes/techtest.py` (or add a `scenes/test_<action>.py`).
   2. Run `python3 tests/check_rig.py --sheet extreme.png`.
   3. Render the debug pass with `--debug` and the clean pass, then review both.

## 8. Known limits

- **One drawing angle (3/4 right).** Turning toward the camera needs new drawings.
- **Head:**
  - It comes from the reference sheet, so it is softer than the parts.
  - There are no separate eyes; gaze is head tilt only.
  - The mouth is a transplanted painted opening on a jaw warp, not phoneme drawings.
- **Linear-blend skinning cannot add folds.** Deep elbow or knee bends would benefit from
  corrective drawings (for example, an "elbow 90°" forearm and a "knee 90°" shin). Each would be
  selected per joint angle and cross-faded.
- **Single drawings:**
  - The backpack is part of the torso drawing, so it has no secondary motion.
  - The pelvis is a frontal drawing squashed to 3/4.
  - There is one thigh drawing for both legs.
- **No collision.** Hands can pass in front of the body without contact.

## 9. Commands

```sh
cd production/atlas-rig
python3 tests/check_rig.py --sheet /tmp/extreme.png --json /tmp/report.json   # must print N/N passed
python3 scenes/techtest.py /tmp/techtest_debug.mp4 --debug                     # bones, joints, IK targets, contacts
python3 scenes/techtest.py /tmp/techtest_clean.mp4
```
