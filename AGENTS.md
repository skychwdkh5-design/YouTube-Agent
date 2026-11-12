# AGENTS.md

Project rules for agents. Project strategy and publishing rules are in `CLAUDE.md`.

## ATLAS character animation (mandatory)

Details, parameters and how to add actions: `docs/ATLAS_RIG.md`. Code: `production/atlas-rig/`.

1. Every scene uses the shared ATLAS component (`atlas_rig.character.Atlas` + `Performance`).
   Do not copy the renderer into scene files. Skeleton geometry, segment lengths, joints, layer
   order and deformation settings live only in `atlas_rig/skeleton.py`.
2. Any rig change (skeleton, IK, skinning, gait, gestures, parts) first passes the technical
   test before it is used in an episode:
   - `tests/check_rig.py` must report all checks passed;
   - render the debug pass (`scenes/techtest.py --debug`) and the clean pass and review them.
   Do not re-render a full episode until the owner has reviewed that test.
3. New actions use the existing joint and contact system: wrist/ankle IK targets, footsteps from
   `gait.Walk`, gestures and gaze from `gesture.py`, hand poses from `skeleton.py`.
4. Never bypass the system with independent rotations of part images, per-scene pivots or
   hand-placed PNG transforms.
5. Never hide rig defects with blur, motion blur, shrinking the character, cropping, or covering
   them with graphics. Fix the rig or report the defect.
6. When reporting, state how motion was checked (frame sheets vs real-time playback). Never claim
   real-time review that did not happen.
