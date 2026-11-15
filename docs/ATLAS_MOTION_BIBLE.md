# ATLAS Motion Bible

The standing motion rules for the Orbital Atlas host ATLAS. Every episode uses them. This file
says *what* good ATLAS motion is and *how the shared rig delivers it*. The architecture itself
(skeleton, IK, skinning, gait internals) is in `docs/ATLAS_RIG.md`. The mandatory agent rules
are in `AGENTS.md`. The code is in `production/atlas-rig/` (rig) and `production/episodes/engine/`
(episode host, render, QC).

First written for EP015 (Starship Flight 15, 2026-11-15), from the owner's motion brief, and
extended with the joint-cover parts the owner supplied (`ATLAS_joint_parts.png`).

## 1. Identity

- Use only the existing ATLAS drawings in `production/atlas-rig/assets/` (approved 2026-11-11).
  Never redesign him, never substitute NIX, never generate a new character.
- Never mirror one sleeve onto the other. Near and far limbs use their own drawings and lighting.
  The far side is darkened (×0.8) and drawn behind the torso.
- If a view or a part does not exist (for example a back view, or fingers), say so. Do not fake it
  with a flipped or warped copy.

## 2. Joints (all on anatomical pivots, defined once in `skeleton.py`)

| Joint | How it moves | Cover |
|---|---|---|
| Neck / head | Gaze-driven tilt, gain 0.35, clamped −12..+10° | — |
| Shoulder | IK root; lifts 3 px while the arm is raised | `cov_shoulder_n` (near shoulder cap) |
| Elbow | 2-bone IK, fixed bend side (no flipping pole) | `cov_elbow_n/f` (corrugated sleeve) |
| Wrist | Hand angle follows the forearm, then turns to the target 0.1 s after the arm starts moving | `cov_wrist_n/f` (glove cuff) |
| Fingers | Swappable hand poses only (`rest`, `point`, `point_near`, `palm`). There are no knuckle bones. | — |
| Hip / knee | 2-bone leg IK, fixed bend side | `cov_knee_n/f` (knee pad) |
| Ankle / toe | Rigid boot: heel-off rolls on the toe tip, heel strike, then roll to flat | — |
| Mouth / brows | Lip-sync from the real narration WAV; brow accents on gesture peaks; independent blinks | — |

### Joint covers (added for EP015)

Joint covers are painted overlap pieces that sit over the bend. A bent elbow, knee or wrist then
shows a continuous sleeve, not two sprites meeting at a seam.

- **Source:** `production/atlas-rig/assets/joints/*.png`, cropped from the owner's sheet.
- **Definition:** `Cover(name, img, joint, j_in, j_out, width, sy, along, squash, w_in)` in
  `skeleton.py`. They are placed in the layer order right after the limb they cover.
- **Placement (`character.cover_matrix`):**
  - The cover centres on the joint.
  - It is oriented along the bisector of the two bones. `w_in` weights the inner bone.
  - It compresses by `squash × bend/90°`, so it bunches as the joint folds.
- **Rule:** covers follow the solved skeleton every frame. They are never animated by hand.
- **Not used yet, on purpose:**
  - The forearm and glove pieces from the same sheet. Their palette differs from the base
    drawing, and they show only one pose.
  - Re-painting these is the next upgrade.

## 3. Motion rules (what the viewer must never see)

1. **No foot sliding.**
   - A planted foot is world-locked from heel strike to toe-off.
   - The pelvis only moves by stepping (`gait.Walk`).
   - A shot change is the only place the placement may change.
2. **No snaps.**
   - Every transition eases, using smoothstep, a minimum-jerk curve or a Bezier path.
   - A gesture that is cut short relaxes from where the hand actually is (`Point.wrist`, fixed
     2026-11-15). It never jumps to a precomputed pose.
3. **No folding through the body.**
   - The wrist path bows away from the shoulder.
   - The curve midpoint keeps at least 1.25 × the keep-out radius from the shoulder.
   - A soft, C1 keep-out disc bends any grazing path around the shoulder instead of clipping it
     onto the edge.
4. **One arm, one gesture.**
   - An arm finishes (or is cleanly relaxed) before its next gesture.
   - When pointing at a list, use one arm with a `seq([...])` target that glides from item to item.
   - Do not alternate arms every second: that reads as puppet flicks.
5. **Both arms live.**
   - While one arm points, the other supports (`Support`, open palm) or swings with the walk.
     It never hangs frozen through a whole scene.
6. **ATLAS walks.**
   - Each scene with a new beat moves him to a new place in the frame (`h.walk(t, dx)`), with
     anticipation and settle.
   - He turns by stepping. He never pivots on a planted foot.
7. **Eyes lead hands.** The gaze key comes about 0.35 s before the gesture starts.
8. **Mouth closed in pauses.**
   - Lip-sync comes from the WAV RMS, never from subtitles.
   - When the narration is retimed with inserted silences, the voice JSON must be regenerated
     (`engine/retime.py`).
9. **No random motion.** Every gesture is tied to a narration phrase (`cues.py`) and to an object
   on screen (point at the ship, trace the orbit, compare with the palms).

## 4. Staging

- ATLAS stays on screen for the whole episode, as a separate layer, at scale 0.6–0.75, standing on
  `FLOOR` (y 915 at 1080p).
- He must never cover:
  - the subtitle zone (checked every frame by `engine/subcheck.py`);
  - the main object of the shot (the ship, the tower, the key number).
- Do not imply he was present at real footage: he stands beside a NASA video or a schematic
  panel, never inside it.
- Frame 0 equals the approved cover, and the action starts at frame 1.

## 5. Writing a performance (episode code)

```python
h.point(t0, (x, y), hold_until, arm='f')          # screen target; eases, accents, holds, relaxes
h.point(t0, seq([(t, p), ...], blend=0.5), t1)    # one arm gliding across several targets
h.support(t0, t1, 'n')                             # other hand opens, explains
h.walk(t0, dx)                                     # real steps, world-locked feet
h.gaze(t, ('s', (x, y)), look=0.8)                 # head leads the hands
```

Close framings magnify motion, so `Host.point` automatically stretches prep, move and relax when a
shot's scale is above about 1.05.

## 6. Mandatory checks before a full render

1. `cd production/atlas-rig && python3 tests/check_rig.py` must report every check passed.
2. `python3 scenes/techtest.py OUT.mp4 --debug` and the clean pass, after any rig change.
3. `cd production/episodes && python3 engine/qc.py EP/episode.py --out qc.json` must show:
   - foot slide max ≤ 1 px;
   - joint jerk p99 ≤ 5 px and max ≤ 25 px. Each `spikes_gt_18` entry gives a time and a joint to
     look at; fix it in the gesture, never by blurring.
   - head never off-screen while hosting;
   - mouth open in pauses on < 2 % of pause frames;
   - lip-sync correlation with the WAV ≥ 0.8.
4. `engine/subcheck.py` shows no ATLAS joint in the subtitle zone while a cue is on screen.
5. A 20–30 s pilot of the opening, reviewed before the full render (the owner's EP015 instruction:
   test once, then build; no endless test loops).
6. **Honest reporting.** Say whether motion was reviewed as frame strips or in real-time playback.
   Never claim real-time review that did not happen.

## 7. Known gaps (do not hide them)

- There are no eye bones, so gaze is head tilt only.
- There are no finger knuckles, only hand-pose swaps.
- There is no back view or three-quarter head, so ATLAS faces left or right only.
- Linear-blend skinning cannot add folds. The joint covers carry the fold look.
- The backpack has no secondary motion.
