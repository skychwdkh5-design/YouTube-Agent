# EP001 pre-final review package

Source: `EP001_prefinal_review_1080p30.mp4` (1920x1080, 30 fps, 747.367 s; sha256 in `../../production/qc/prefinal/SHA256.txt`).
Clips are re-encoded to 1280x720 (H.264 crf 24, AAC 128k) from that master at exact frame boundaries; times below are master times. Folder: `productions/sahara-green/review/pre_final/` (MP4 files are not tracked by Git).
Total 18.1 MB.

| file | master time | length | size | content |
|---|---|---|---|---|
| `01_opening_0-30s.mp4` | 0:00.000 - 0:30.000 (0.000-30.000 s) | 30.0 s | 3.2 MB | Opening 30 s: Tassili, 230+ callout, Bodele, Blue Marble, rain card, East Oweinat 1984 to 2024 |
| `02_water_balance_443.567-492.267.mp4` | 7:23.567 - 8:12.267 (443.567-492.267 s) | 48.7 s | 1.4 MB | Complete 48.7 s water-balance composition (scene 25) plus the first 0 s of the next shot |
| `03_satellite_east_oweinat_274.333-292.667.mp4` | 4:34.333 - 4:52.667 (274.333-292.667 s) | 18.3 s | 1.9 MB | East Oweinat: 1984 hold with push-in, dissolves 2000/2010/2016/2024, zoom into the circles |
| `04_satellite_toshka_328.467-349.500.mp4` | 5:28.467 - 5:49.500 (328.467-349.500 s) | 21.0 s | 1.5 MB | Toshka: 1999, 2002, 2011, 2021 dissolves |
| `05_satellite_east_oweinat_scene35_702.400-720.767.mp4` | 11:42.400 - 12:00.767 (702.400-720.767 s) | 18.4 s | 2.3 MB | East Oweinat widest view, 1984 to 2024 (scene 35) |
| `06_satellite_nasa_calipso_498.167-525.033.mp4` | 8:18.167 - 8:45.033 (498.167-525.033 s) | 26.9 s | 3.3 MB | NASA CALIPSO dust (30 fps) with narration-timed labels, then Bodele |
| `07_graphic_aquifer_292.667-317.000.mp4` | 4:52.667 - 5:17.000 (292.667-317.000 s) | 24.3 s | 0.6 MB | Animated graphic: Nubian aquifer (country rings, fossil-water banner) |
| `08_graphic_proposal_357.167-395.300.mp4` | 5:57.167 - 6:35.300 (357.167-395.300 s) | 38.1 s | 1.0 MB | Animated graphic: 2009 forest proposal build (11 steps) |
| `09_graphic_storms_568.167-600.000.mp4` | 9:28.167 - 10:00.000 (568.167-600.000 s) | 31.8 s | 0.8 MB | Animated graphic: tropical-storm simulation (first 32 s of 48 s) |
| `10_closing_727.367-747.367.mp4` | 12:07.367 - 12:27.367 (727.367-747.367 s) | 20.0 s | 2.1 MB | Closing 20 s: uncertainty card, Tassili pull-out, outro |

Not cut, but part of the master for reference: the full water-balance composition is clip 02 (443.567-492.267 s, 48.7 s, the whole scene 25, 12 build steps).

## Credits (reviewer decision 8)
- Graphics carried the provisional text "Graphic: Sahara Green · sources on the graphic". It is now **"Original graphic · sources on the image"**: neutral and accurate (the graphics are original, every one prints its own "Source:" line, and no channel name appears anywhere on screen). Source credits are untouched: each graphic's source line, "Landsat 9 · USGS", "NASA Earth Observatory · Blue Marble", "NASA Goddard SVS · CALIPSO dust (Dust in the Wind)".
- Legibility on light backgrounds: the credit is drawn on a dark translucent rounded pill (no outline halo) by yt-render (`compose.py _credit`), with a regression test on a white graphic (`test_compose.CreditPill`). Checked in the master on a white card, a dark card and three Landsat frames.
- The credit text of the sequences (East Oweinat, Toshka) is unchanged; the sequences carry their own source notes.

## Satellite alignment (reviewer decisions 4, 5, 7)
| place | scene | acquired | source | tone |
|---|---|---|---|---|
| Tassili n'Ajjer | LC09_L1TP_190042_20251220_20251220_02_T1 | 2025-12-20 | Level-1 B4/B3/B2 (255 MB) | B |
| Gilf Kebir | LC09_L1TP_179044_20251121_20251121_02_T1 | 2025-11-21 | Level-1 B4/B3/B2 (248 MB) | B |
| Kufra | LC09_L1TP_181043_20260919_20260919_02_T1 | 2026-09-19 | Level-1 B4/B3/B2 (247 MB) plus B5 (88 MB) for the NDVI check | B |
| Ounianga | LC09_L1TP_182047_20260622_20260622_02_T1 | 2026-06-22 | Level-1 B4/B3/B2 | B |
| Bodele | LC09_L1TP_183048_20260731_20260731_02_T1 | 2026-07-31 | Level-1 B4/B3/B2 | B (the haze is real; no cloud or dust removed) |
Total new download in this stage: 750 MB of band files plus 88 MB (B5 of Kufra). All tone B stills: native 30 m pixels, no resampling, USGS public domain, retrieved 2026-10-08/09, files and hashes in `production/stills/*.json`.
**Kufra** (`production/stills/kufra_alignment.json`, script `production/verify_kufra_alignment.py`): (1) the GeoTIFF transform reproduces the four product corners of the MTL file to under 1.5 px and 30 m; (2) the MTL footprint polygon contains the reference point Al Kufrah (24.18 N, 23.29 E); (3) green irrigated fields found by NDVI (B5, B4 TOA reflectance, > 0.20) form a cluster of 50,426 pixels whose centroid, converted through the verified transform, is 24.1814 N, 23.2583 E, **3.2 km** from the reference point; (4) the video window (UL 24.575 N 22.530 E, LR 24.013 N 23.585 E) contains the cluster core, and 99.9 percent of its pixels. The earlier visual placement is replaced by coordinates. The reference coordinates are a published place name position typed into the script (not downloaded); the verification is of the georeference and the field centroid against it.
