# Episode 001: Landsat browse sequence and 2024 band access test (2026-10-08)

The locked narration, its hash and `story/SCRIPT_LOCK.md` were not touched. Raw imagery stays outside Git (ignored workspace outside the repository; ephemeral). Only previews, metadata and logs are committed.

## Phase 1: browse GeoTIFFs
Product: "Full-Resolution Browse (Natural Color) GeoTIFF". 12 new files (`browse_downloads.json`), **24,206,010 bytes (23.1 MiB)**; the 2010 file came from the previous step. Exact scene IDs from `preflight_2026-10-08.json`: East Oweinat 1984-08-26, 2000-01-11, 2010-01-22, 2016-01-07 (`LC81770442016007LGN02`), 2024-01-05; Toshka 2002-01-09 (176044) and 2002-01-18 (175044), 2011-07-29 (176044) and 2011-10-10 (175044), 2021-11-13 (176044) and 2021-11-06 (175044). **Added, not requested:** the 1999 baseline before the lakes (`LT05_L1TP_176044_19990101` and `LT05_L1TP_175044_19990110`), because storyboard scene 21 uses a "before the lakes" frame. All orders were removed from the USGS queue.
Verification (`measurements/browse_verification.json`): each file decodes fully; georeferenced north-up UTM (EPSG 32635 for path 177044, 32636 for paths 175044 and 176044), 30 m pixels, PixelIsArea; the corner longitudes and latitudes agree with the USGS scene footprint (the browse image bounds are 0.01-0.15 degrees wider than the footprint polygon, as expected for a rotated scene inside its bounding box); the scene centre falls inside the footprint in all 13 cases; 69-75% of each image is imagery, the rest is the black no-data corner fill.

## Phase 2: 2024 band access: SUPPORTED
`LC09_L1TP_177044_20240105_20240105_02_T1` (entity `LC91770442024005LGN00`, Landsat 9 OLI-2, Collection 2 Level-1 Tier 1, cloud 0%). The M2M "Band File" product lists each file as its own addressable entity (`L1_<scene>_B4_TIF` and so on, 20 per scene, with size and sha512). A `download-request` naming only the four wanted entities returned exactly four URLs; nothing else was requested or transferred. Downloaded: `B4` (red, 84,233,606 bytes), `B5` (near infrared, 86,048,274), `QA_PIXEL` (336,408) and `MTL.txt` (12,204): **170,630,492 bytes (162.7 MiB)**, sizes and sha512 all match the USGS listing. The 1.085 GB bundle was not requested. The stock `usgs_m2m.py download` command cannot do this (it fetches every file of a product), so a small helper script outside the repository was used; adding single-file download to the tool is a possible later improvement.
Georeferencing: 7571 x 7711 px, 30 m, UTM 35N, PixelIsPoint tie point (549300, 2672100) equal to the MTL upper-left corner; the corners computed with yt-geo's UTM routine reproduce the MTL latitudes and longitudes to 0.5 m. Geometric RMSE 5.04 m.

## Phase 3: pivot measurement (source bands, same pipeline for both years)
Full numbers: `measurements/east_oweinat_pivots_2024_vs_2010_source_bands.json`. Method: top-of-atmosphere reflectance from the MTL coefficients, NDVI (OLI B5/B4; TM B4/B3), threshold 0.30, isolated near-circular components, equivalent diameter from area.
| | 2010-01-22 (Landsat 5) | 2024-01-05 (Landsat 9) |
|---|---|---|
| circles measured | 300 | 1,350 |
| diameter, median (IQR) | 757 m (673-797) | 819 m (796-829) |
| diameter, 90th percentile / maximum | 821 / 828 m | 843 / 890 m |
| full circles only (fill >= 0.95), median | 764 m (n=261) | 821 m (n=1,234) |
| centre-to-centre spacing, median (IQR) | 896 m (831-994) | 985 m (940-1,153) |
Uncertainty: 1 pixel (30 m) per circle; NDVI thresholds 0.2-0.4 move the 2024 full-circle median between 837 and 810 m (2010: 779 to 761 m). Only isolated circles are measured; touching circles are skipped.
Comparison: 115 circles are found in both years (centres within 90 m, mean offset 10 m). Paired difference, 2024 minus 2010: median -5 m (IQR -18 to +14 m). Where both are complete circles (90 pairs) the medians are 804 m and 803 m. The higher 2024 population median comes from which circles are detected and how complete they are in January, not from circles getting bigger; **a vegetation mask cannot show physical expansion or contraction, and none is claimed.**
**Diameter versus spacing:** a typical complete circle is about 0.80-0.82 km across (about half a mile); neighbouring circle centres are about 0.9-1.0 km apart. Preview with detected circles: `previews/east_oweinat_2024_pivot_detection_overlay.jpg`.

## Phase 4: production previews (low resolution, exact dates labelled)
`previews/production_preview_east_oweinat_1984-2024.jpg`, `production_preview_toshka_west_1999-2021.jpg`, `production_preview_toshka_east_1999-2021.jpg`. Built with yt-geo (`geostack.py --confirm`, same grid for all dates of one place). Each image is labelled "PRELIMINARY: not a validated co-registered scientific comparison". Alignment rests on the USGS L1TP georeferencing (RMSE 3.9-5 m for the two scenes with a full MTL); no independent alignment test has been run for the other dates; seasons differ (January against August, July, October and November), so colour and brightness vary between frames. The Toshka AOIs are limited to the area covered by each path and do not show the full lake system. Not for use as a final graphic.

## Transfer total this step
Browse GeoTIFFs 24,206,010 bytes + 2024 bands 170,630,492 bytes = **194,836,502 bytes (185.8 MiB)**. Under the 100 MB (browse) and 400 MB (bands) limits.

## Not done / open
- Water masks, area figures and the final co-registered stacks for Toshka.
- Single-band download for TM scenes (the same mechanism should work; not tested).
- Independent alignment check between sensors.
- Decision on the L1 wording: see `PROPOSED_NARRATION_CORRECTION_L1.md` (not applied).
