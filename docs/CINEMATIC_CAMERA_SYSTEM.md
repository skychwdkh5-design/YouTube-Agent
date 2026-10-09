# Cinematic camera system
## Classes
| class | what moves | needs | status |
|---|---|---|---|
| A image-space | a crop window (x, y, height, optional rotation) over one image's pixels | image only | Built (`SplineCam`, `View`) |
| B georeferenced map | a camera over a CRS (lon/lat, or projected) with real extent | CRS, extent, georeferenced rasters/vectors, map renderer | NOT built: no pyproj/GDAL; MapLibre/GDAL cannot be installed here (no PyPI/npm DNS) |
| C 3D globe/terrain | a 3D camera over DEM + imagery | DEM, georeferenced imagery, 3D renderer (Blender or WebGL/Three.js/Cesium) | NOT built; Chromium has software WebGL (tested), Blender absent |
**Language rule**: class A is called "image push/pan", never "flyover". A "flyover" needs C. Spatial continuity
between two unregistered images is not claimed; such a cut is labelled as a cut between sources.

## Camera spec (all classes share it)
keys `(t, center, height, rotation?)` · easing per segment · anchors (named points, source px or lon/lat) ·
tracking (follow a named anchor with lag 0.15–0.3 s) · safe framing (subject inside the central 80 %, text
zones reserved) · composition constraint (rule of thirds default; hero anchor near a third line or centre when
reveal-centred) · transition duration (0.4–1.2 s for cuts, 3–6 s for moves).

## Rules
- Motivated movement: every move reveals, follows or compares. Verify: storyboard states the motive.
- Accel/decel: PCHIP through keys, velocity continuous. Verify: plot |v(t)|; no jump >15 %/frame.
- Zoom in log space (constant perceived rate). Max useful zoom is set by source resolution; beyond 1:1 pixel
  the render softens: fail if effective magnification of source >2.4× (ASTER) unless labelled enlargement.
- Shot length: establishing 3–5 s, reveal 2–4 s, detail hold ≥1.2 s, none >7 s without a new element.
- Match cut: equal screen scale and subject position across the cut; same subject.
- Scale transition: change at least 3× in view height, log-eased, with a clean label hand-off.
- Rotation: sources may be displayed rotated (e.g. coast horizontal); always label "rotated 90°".
