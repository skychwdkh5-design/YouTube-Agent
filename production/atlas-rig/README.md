# ATLAS rig (shared character component)

Rules: `/AGENTS.md`. Design and how to add actions: `/docs/ATLAS_RIG.md`.

- `atlas_rig/` — the component (skeleton, IK, skinning, gait, gestures, face, debug overlay)
- `assets/parts/` — owner's 21-part pack at half resolution; `assets/ATLAS_reference_sheet.png` (head/face)
- `scenes/techtest.py` — technical test (stance, two steps, stop + weight shift, point, relax)
- `tests/check_rig.py` — automatic rig checks (run after every rig change)

Originals of the parts: `/mnt/project-files/atlas/parts_pack_v1/`.
