# Animated cartography
## Geodata basics the code must respect
- CRS: store lon/lat in EPSG:4326; do metric work in an appropriate projected CRS (UTM zone for a city,
  Web Mercator only for display). Never measure area/distance in Web Mercator.
- Landsat scenes are UTM, 30 m (yt-geo co-registers to a common grid: use it for before/after).
- ASTER/ISS "World of Change"-type JPEGs have no embedded georeference: they are EVIDENCE with image-space
  overlays only. Georeferencing them needs ≥4 spread control points, an affine/projective fit and a reported
  RMS in metres; without that no lon/lat marker may be drawn on them.
- ISS astronaut photographs: oblique, perspective distortion; centre-point metadata is approximate; treat
  as photographs, not maps.
## Layer separation (code-enforced)
`evidence` (pixels) · `registered` (traced from the same pixels, or GCP-fitted) · `map` (open vector) ·
`illustration` · `type` · `decor`. A layer object carries `cls`, `source`, `validation` (how checked). A renderer
refuses to draw `map` over `evidence` unless `registered.rms_m` is set. (Enforcement: roadmap R3.)
## Techniques
| technique | use | implementation | accuracy statement |
|---|---|---|---|
| traced outline | coast, island footprint | `trace.py` + `validate.py` (both-side sampling) | accurate to image pixels, not a survey |
| land/sea fill | "land vs sea" emphasis | mask → radial wipe tint (`fx.highlight`) | from traced mask |
| anchored label | place name | `fx.anchored_text`: positions defined in source px, moves with camera | anchor must be validated by eye on full res |
| year counter | time | `fx.year_roll` | |
| coast comet | direction/flow | `fx.trail` along traced polyline | decorative; do not imply movement of data |
| globe-to-map | locator | class B/C | NOT built; needs Natural Earth + projection code (can be pure numpy for orthographic) |
| terrain | relief | needs DEM (SRTM/Copernicus) download | NOT built; network allowlist unknown |
Satellite evidence vs illustration: label illustrations "illustration"; never texture them with photo crops.
Validation of any overlay: sample both sides of each vertex; review full-res frame by eye; log residuals.
