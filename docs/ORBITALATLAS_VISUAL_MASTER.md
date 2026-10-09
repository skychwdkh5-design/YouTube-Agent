# OrbitalAtlas — Visual Master (source of truth)

Status of this file: architecture and rules. Phase A (audit) and B (architecture) of the visual upgrade.
Nothing here claims a feature is built unless the "Built?" column says so.

## 1. Goal
Code-driven, narration-led geographic documentary. Meaningful visual change at every beat, honest about
what each layer is. Not a slideshow, not Ken Burns on stills, not effects for their own sake.

## 2. Reading order for any new video
1. `CLAUDE.md` (audience, topics) → 2. this file → 3. `docs/VISUAL_QUALITY_RUBRIC.md` →
4. skills: `/yt-motion-design`, `/yt-cinematic-edit`, `/yt-geographic-animation` →
5. `docs/RENDER_ENGINE_DECISION_MATRIX.md` before choosing a renderer.
Detail lives in the other docs; this file stays short.

## 3. Evidence classes (inherited from `productions/dubai/motion/MOTION_DESIGN_SYSTEM.md`, still valid)
EVIDENCE (unmodified source image) · TRACED (contour computed from that same image's pixels) ·
MAP (open-data vector map, georeferenced) · ILLUSTRATION (schematic) · TEXT/TIMELINE.
Rules: a MAP line is never drawn on a photo/satellite image unless registered with control points and a
reported RMS error. A TRACED line is accurate to its own pixels only. Different instruments/dates are
never wiped/overlaid as if registered (EP002 claim 32). Every layer carries its class in a chip or credit.

## 4. Camera classes (never blur them)
A image-space (crop window over pixels) · B georeferenced map camera (needs CRS + extent) ·
C true 3D globe/terrain (needs DEM + georeferenced imagery + a 3D renderer). Only A exists today.
Calling A a "flyover" in a storyboard or report is a defect. See `CINEMATIC_CAMERA_SYSTEM.md`.

## 5. Status vocabulary
`TECHNICALLY_VALID` (automated gates pass) → `VISUALLY_REVIEWED` (agent watched frames + motion and wrote
rubric scores) → `USER_APPROVED` (only the user can set this; never self-assigned). A report must name the
highest level reached and must not use the words "approved/premium/cinematic" for the first two.

## 6. Mandatory process per episode
1. Storyboard with every field in `MOTION_DESIGN_STANDARDS.md §Storyboard` (no filename+zoom lists).
2. Capability check: each storyboard effect maps to an engine component marked Built; otherwise listed as
   a limitation *before* rendering, never silently replaced by a pan/zoom.
3. Render a short proof (12–15 s) of the hardest sequence first. User approves. Then scale.
4. Locked narration/word timings only; no TTS calls without explicit user authorisation.
5. Gates in `VISUAL_QUALITY_RUBRIC.md`; report status vocabulary honestly.

## 7. Component status (honest)
| capability | Built? | where |
|---|---|---|
| image-space spline camera, log zoom, motion blur | yes | `productions/dubai/motion/engine/motionlib.py` (SplineCam) |
| traced coastline/outline, validated | yes | `engine/trace.py`, `validate.py` |
| land/sea fills, spotlight, anchored/rotated text, year roll, coast trail | yes | `engine/fx.py` |
| word-timed cues, ASS subs, loudness | yes | `engine/av.py` |
| match cut between two images at equal scale | yes (in scene file, Dubai-specific) | `av_test/proof_v3.py` |
| generic transition library | NO (roadmap) | — |
| georeferenced map camera (CRS) | NO — no pyproj/GDAL, no network for pip/npm | — |
| 3D globe/terrain | NO — no Blender/DEM; WebGL via headless Chromium untested | — |
| split-screen compare, data charts, SVG shape animation | NO | — |
The engine lives under `productions/dubai/…/engine` and is partly Dubai-coupled (scene files hardcode
geography). Promoting it to a shared package is roadmap step R1.
