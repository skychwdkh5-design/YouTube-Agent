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
