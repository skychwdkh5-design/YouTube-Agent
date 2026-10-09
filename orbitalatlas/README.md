# orbitalatlas — shared motion-graphics engine (v0.1)

numpy + Pillow + FFmpeg only. No place names, coordinates, labels or claims live in this package: episodes pass them in
(scene specs / scene files). Camera class implemented: **A, image-space** (a rotated, scaled crop window over one image's
pixels). `geo` adds a georeferenced globe camera (class B, orthographic, vector data only). Neither is a 3D flyover.

Run from the repo root: `python3 -m unittest discover -s orbitalatlas/tests -t .`

| module | what it does | status |
|---|---|---|
| `easing` | named curves, CSS cubic-bezier, PCHIP/Hermite, log lerp | tested |
| `camera` | `View` (source↔screen with rotation), `Camera` (keys: centre or named anchor, height, rotation, per-key easing, `at=(fx,fy)` composition, `eased`/`spline` modes, subject tracking with lag, clamp for rotated windows), `fit` (safe framing), `check` (crop/anchor/magnification issues), `Pyramid` (anti-aliased affine render) | tested |
| `text` | theme tokens, kinetic text, rotated/reveal labels, plates, rolling digits, collision/outside `Registry` | tested |
| `layers` | blend modes, `Scene` (image + camera + overlays, camera motion blur by temporal sub-sampling), overlays: `DrawOnPolyline`, `PulseMarker`, `AnchoredText`, `ScreenText`, `SourceChip`, `YearCounter`, `MaskFill`, `Spotlight`, `Brackets`; each overlay carries `cls` (EVIDENCE/TRACED/MAP/ILLUSTRATION/TEXT/DECOR), `source`, `validation` | tested; class/validation are metadata only (not enforced, roadmap R3) |
| `transitions` | `Dissolve`, `Push` (+cover/parallax, shutter blur), `WhipPan`, `CinematicPush`, `MaskReveal` (linear/radial/custom time-map, glow edge), `GeoFocus`, `ScaleMatch`, `DateTransition`; `from_spec` | tested; all produce real frames |
| `sequence` | `Shot`/`Sequence` with overlapping transitions, `schedule()`, `render_video()` (multiprocessing → FFmpeg H.264/AAC) | tested |
| `timing` | `Track` scalar animation, `Cues.from_words` (provider word timestamps; `source='estimated'` is never "frame accurate") | tested |
| `qa` | black frames, blank fill regions, discontinuities, static runs, transition motion/pop/duration/repetition, camera crop, out-of-frame/collision overlays, missing assets | tested; thresholds in `QAConfig` |
| `spec` | JSON/dict → `Scene` (one code path for any image) | tested |
| `geo` | `GlobeView` (lon/lat ↔ screen, orthographic, bearing), `GeoCamera` (great-circle path, log zoom, `arc`, spline mode, `check`), `GeoData` (Natural Earth GeoJSON), `GeoRaster` (multi-resolution land/polygon coverage), `GeoScene` (shaded globe, coast lines, graticule, camera blur), overlays `GeoFill`, `GeoPolyline`, `GeoMarker`, `GeoLabel`, `ScaleBar`, `Breadcrumb`; data via `tools/fetch_natural_earth.sh` (public domain, not committed) | tested; class B from vector data only |
| `synthetic` | procedural test images with exact geometry | test data only |
| `demo` | seven-shot demo from specs; `python3 -m orbitalatlas.demo.render_demo OUT.mp4 --qa` | |

## Using it in an episode
1. Keep project data (image paths, anchors, traced outlines, label text, narration timings) in the episode folder (a spec or a scene file).
2. `from orbitalatlas import spec, sequence, transitions, qa`; build scenes, join with transitions, `render_video`, run `qa.run_video` with declared cuts/holds.
3. Time reveals with `timing.Cues.from_words(words)` from locked provider word timestamps.
4. Report TECHNICALLY_VALID only after QA; VISUALLY_REVIEWED after you looked at frames; USER_APPROVED only from the user.

Geo proof (needs the data): `python3 -m orbitalatlas.demo.geo_locator_proof OUT.mp4 --qa`. Data: `tools/fetch_natural_earth.sh` (git sparse clone through the session proxy), checksums in `data/natural_earth.sha256`.

## Not implemented (do not claim)
Flat/tilted map plane, imagery basemap (needs raster data), terrain/relief, SVG shape animation, data charts, split-screen compare, audio-reactive animation,
GPU rendering, tracing/validation (still in `productions/dubai/motion/engine/` until promoted), layer-class enforcement.
