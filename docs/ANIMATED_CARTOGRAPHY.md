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

## Real geography data (added in Phase D)
| item | status |
|---|---|
| dataset | Natural Earth 5.2.0-pre vector (public domain, https://github.com/nvkelso/natural-earth-vector, commit `ca96624a56bd078437bca8184e78163e5039ad19`) — land 1:10M, admin-0 countries, populated places, marine polygons, regions |
| how obtained | `git clone --filter=blob:none --sparse` through the session's git proxy (`tools/fetch_natural_earth.sh`); naciscdn.org and raw.githubusercontent.com are blocked (HTTP 403 on CONNECT) |
| stored | `data/natural_earth/` (git-ignored, ~48 MB); checksums in `data/natural_earth.sha256` (committed) |
| licence | public domain; credit not required, chip still names the dataset |
| accuracy | 1:10M generalisation (≈1–2 km at best); disputed borders follow Natural Earth's de-facto lines; marine polygons are label-grade extents |
| coordinates used by the locator proof | Dubai (55.2869 E, 25.2149 N) = NE populated-places point; Persian Gulf label anchor (52.00 E, 26.82 N) = centroid of the NE marine polygon (bbox 47.72–57.20 E, 23.97–30.51 N); Arabian Peninsula label anchor (46.52 E, 22.61 N) = centroid of the NE region polygon; UAE anchor (54.31 E, 23.90 N) = centroid of the mainland ring. Anchors are label positions, not boundaries. |
| not available | imagery basemap (NASA hosts blocked), DEM, rivers (file not fetched), city-scale vector data (Palm Jumeirah-scale features come only from the photograph) |
| hand-off rule | the map ends at region/city-point scale; imagery is introduced as a separate class-A scene with "NOT GEOREGISTERED". ASTER/ISS frames are never used as a basemap. |
