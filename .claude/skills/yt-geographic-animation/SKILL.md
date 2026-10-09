---
name: yt-geographic-animation
description: >-
  Animated geographic overlays for OrbitalAtlas - traced coastlines, anchored place labels, land/sea
  fills, year counters, georegistration rules, map vs evidence separation, and honest camera classes.
  Use for any scene that annotates a satellite image or map, animates a coastline or boundary, compares
  places across years, or needs a locator map. Not for Landsat search (/yt-satellite) or co-registered
  stacks (/yt-geo), which it relies on for real georeferencing.
---

# yt-geographic-animation

Read: `docs/ANIMATED_CARTOGRAPHY.md`, `docs/CINEMATIC_CAMERA_SYSTEM.md`. Code: `productions/dubai/motion/engine/`
(`trace.py`, `validate.py`, `fx.py`, `motionlib.py`) until promoted to a shared package.

## Decision tree
- Image has no georeference (NASA WoC JPEGs, ISS photos) → class A only; overlays must be TRACED from that image's pixels
  (`trace` + `validate` ≥0.7) or hand-placed anchors verified on full-resolution frames. No lon/lat markers.
- Need real lon/lat marker or measured distance/area → need georeference: Landsat via `/yt-geo` (UTM grid), or GCP fit with
  ≥4 spread points and reported RMS (m). Without it, say "not georegistered".
- Locator map/globe → class B; blocked here (no pyproj, no network). Options: user supplies Natural Earth file; pure-numpy
  projection code. Label "stylised map, not satellite imagery". Never draw map lines on photos.
- Terrain/3D → class C; needs DEM + renderer; not available. Do not fake with parallax.
## Implementation rules
1. Define overlays in the source pixels of the image they sit on, so they move with the camera.
2. Validate tracing by sampling both sides of vertices; look at full-res crops; log scores.
3. Text along a coast uses the traced tangent; keep inside safe area for the whole shot (check start/mid/end).
4. Different dates/instruments are never wiped as if registered (EP002 claim 32); a cut at equal screen scale is allowed and labelled.
5. Source chip for every image: instrument, date, "colours as published", "view rotated N°" where rotated.
6. Keep geography out of global modules: scene files hold coordinates/anchors; engine takes them as parameters.
## Verify
Overlay residual/validation recorded · full-res frame review · label bbox inside frame at keyframes · collisions = 0.

## Shared engine (use it; do not copy it)
`orbitalatlas/` (repo root; see `orbitalatlas/README.md`): `camera`, `easing`, `layers` (Scene + overlays), `transitions`, `sequence`, `timing`, `qa`, `spec`.
Run from the repo root; tests: `python3 -m unittest discover -s orbitalatlas/tests -t .`; demo: `python3 -m orbitalatlas.demo.render_demo OUT.mp4 --qa`.
Keep episode data (images, anchors, outlines, text, timings) in the episode folder; do not edit the package for one episode.
Import only what exists; features marked NOT built in `docs/ORBITALATLAS_VISUAL_MASTER.md §7` must be listed as limitations.
Overlays live in `orbitalatlas.layers` (`DrawOnPolyline`, `AnchoredText`, `MaskFill`, `PulseMarker`, ...) and take SOURCE-pixel geometry; tracing/validation helpers are still in
`productions/dubai/motion/engine/` (promotion to the shared package is roadmap). `cls`/`source`/`validation` fields document what an overlay is; they are not enforced.

## Real geography (class B) — `orbitalatlas.geo`
Use for any locator (world → region → country → city). Fetch data with `tools/fetch_natural_earth.sh` (public domain, pinned, checksummed); never invent coastlines/borders; put dataset names in `source` fields and in an on-screen chip. Template: `orbitalatlas/demo/geo_locator_proof.py`. Map ends where the data stops being meaningful (city scale at 1:10M); hand off to documentary imagery with `GeoFocus` and the chips "STYLISED MAP" / "NOT GEOREGISTERED". Unregistered photographs are never a basemap.
Reference style and catalogue: `docs/references/`.
