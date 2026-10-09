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

## 6b. Reference style
Reference-derived mechanics (continuous camera, event cadence, highlight rules, labelling) are in `docs/references/ORBITALATLAS_REFERENCE_STYLE.md`; effect catalogue and engine gap status in `docs/references/VISUAL_EFFECT_CATALOG.md`; analyses of the two user-supplied references in `docs/references/REFERENCE_0{1,2}_ANALYSIS.md`.

## 7. Component status (honest; shared engine = `orbitalatlas/`, see `orbitalatlas/README.md`)
| capability | Built? | where |
|---|---|---|
| keyframed image-space camera: anchors, rotation, easing per key, spline/eased modes, subject tracking, safe-frame fit, crop checks | yes, tested | `orbitalatlas/camera.py` |
| camera motion blur (temporal sub-sampling) | yes | `orbitalatlas/layers.py` (`Scene.render`) |
| easing library incl. cubic-bezier | yes | `orbitalatlas/easing.py` |
| anchored overlays (draw-on line, marker, anchored/rotated text, chip, year counter, mask fill, spotlight, brackets) | yes | `orbitalatlas/layers.py` |
| transitions: dissolve, push (+blur), whip, cinematic push, mask reveal, geo focus, scale match, date/timeline | yes, render real frames, tested | `orbitalatlas/transitions.py` |
| shots + transitions on one timeline, FFmpeg encode | yes | `orbitalatlas/sequence.py` |
| narration cues from provider word timestamps | yes (lookup only; no audio code) | `orbitalatlas/timing.py` |
| automated visual QA (black, blank, jumps, static, transitions, crops, overlays, assets) | yes, heuristic | `orbitalatlas/qa.py` |
| contour tracing + validation of outlines from an image | yes, but still project-local | `productions/dubai/motion/engine/trace.py`, `validate.py` (promotion = roadmap) |
| word-timed subtitles (ASS), loudness mastering | yes, project-local | `productions/dubai/motion/engine/av.py` |
| georeferenced globe camera from vector data (class B: lon/lat, great-circle path, km scale, Natural Earth polygons/lines, labels, markers) | yes, tested; orthographic projection in pure numpy, no pyproj needed | `orbitalatlas/geo.py` (data: `tools/fetch_natural_earth.sh`) |
| flat/tilted map plane, photoreal basemap, relief, rivers | NO — needs raster/vector data not fetched (NASA hosts blocked; rivers not fetched) | — |
| 3D globe with terrain (class C) | NO — no DEM, no 3D renderer | — |
| split-screen compare, data charts, SVG shape animation, audio-reactive animation | NO | — |
| layer-class enforcement (map over photo refused) | NO — classes are metadata (roadmap R3) | `layers.py` |
The Dubai engine under `productions/dubai/motion/engine/` is unchanged and still works (EP002 scripts import it); the shared package
is an independent, geography-free generalisation, not yet used by EP002 scenes (roadmap: migrate in Phase E).
