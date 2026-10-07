---
name: yt-geo
description: >-
  Put several dates of real Landsat imagery onto exactly the same geographic grid (co-registered
  "stack"), and trace water masks for outlines and "lost area" fills. Use when a Short or video
  compares a place across years - shrinking lakes, glaciers, coastlines, urban growth - so a wipe
  or year flip compares like with like. Works on GeoTIFFs from /yt-satellite.
---

# yt-geo

A before/after is only evidence if both images show the same ground in the same place.

```bash
python3 geostack.py stack.json                              # plan: every date must cover the area
python3 geostack.py stack.json --contact dates.jpg --confirm # write stack/<id>.png + grid.json
python3 watermask.py stack/y2000.png --out geo/water_y2000.png
```

## Getting the imagery

Use `/yt-satellite` with `--dataset` per era: `landsat_tm_c2_l1` (Landsat 4-5, 1982-2012),
`landsat_etm_c2_l1` (Landsat 7 - only up to 31 May 2003; later scenes have scan-line gaps),
`landsat_ot_c2_l1` (Landsat 8-9, 2013-). Choose the same season and, if possible, the same
WRS path/row for every date. Download **"Full-Resolution Browse (Natural Color) GeoTIFF"** (a few
MB, 30 m, georeferenced) - the JPEG browse has no georeferencing and cannot be aligned.

## stack.json

```json
{"aoi": [lon_min, lat_min, lon_max, lat_max], "pixel_m": 30, "out_dir": "stack",
 "scenes": [{"id": "y2000", "src": "raw/LE07_..._refl.tif", "label": "2000",
             "provenance": {"entityId": "...", "displayId": "...", "acquired": "2000-07-06",
                            "license": {"name": "Public domain", "commercial_use": true}}}]}
```

The output grid is UTM (zone of the area's centre), north-up, `pixel_m` per pixel. Each date is
reprojected from its own GeoTIFF tags (any UTM zone) and sampled bilinearly. An area not fully
inside a scene, or touching its no-data fill, is refused - never a silent black corner.
`grid.json` lets `/yt-render` place a camera by longitude/latitude; `provenance.json` carries every
date's IDs, licence and processing.

## Water masks

`watermask.py` marks dark, non-red pixels as water, removes speckle (3x3 cross opening - it trims
single corner pixels) and drops regions under `--min-area-px`. It is a **display aid** traced from
real imagery, not a survey. A number derived from it (an area ratio, a retreat distance) must say
"about", and its method goes in the claims ledger. Clouds and their shadows can look like water;
build masks from cloud-free dates.

## No fabrication

Only real scenes go in a stack, with their IDs. Colour is left exactly as the browse product has it.
Crops, reprojection and masks are processing steps, recorded in provenance.
