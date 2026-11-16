# ATLAS APPROVED PAPER-CUT CHARACTER · V3

READY FOR CLAUDE AS A PRODUCTION-SAFE BASELINE, NOT A FULL ARTICULATED RIG.

## Where to start
1. `source/APPROVED_CONCEPT_UNMODIFIED.png` is canonical approved design.
2. `characters/hero_approved_clean.png` is the approved-character pixel cutout for use in releases.
3. `code/render_safe.py` is an executable proof of stable whole-body motion.
4. `presets/MOTION_LIBRARY.json` defines supported animations.
5. `poses` and `expressions` contain additional sketches from the approved sheet, but need manual edge/composition review before publishing.
6. `experimental_layers` are overlapping crops only, NOT true articulation; FORBIDDEN in release builds.
7. `docs/CLAUDE_HANDOFF.md`, `docs/PRODUCTION_RULES.md` and `docs/QA_GATES.md` are mandatory.

## Run preview
`python code/render_safe.py --character atlas --seconds 4 --output preview.mp4`
Requires Python 3, Pillow, ffmpeg, libx264.

## Safety and fidelity
No generated redraws, no V1 vector substitutes, no simulated articulations through invalid overlaps. A fully separable rig needs a dedicated artist redraw of hidden joints and approval; absent from current assets.

## File hygiene
All checksums in SHA256SUMS.txt. Do not silently claim 12 mouth shapes / lip-sync or realistic walking is included.
