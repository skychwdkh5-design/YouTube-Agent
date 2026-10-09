# EP001 Landsat source-band acquisition and validation (2026-10-08)

Narration lock v1.1 untouched. Imagery stays outside Git (manifest + restore script only). No credentials stored.

## 1. Toshka 2011 seasonal review (before any download)
Searched Landsat 5 TM C2 L1 Tier 1 scenes, paths 176044 and 175044 (all 2009-2011 dates in `ls/all.json` metadata, all cloud <= 27%). Browse jpgs of the candidates are in `previews/toshka_2011_candidates.jpg`.
| | Old choice | **Selected** |
|---|---|---|
| Path 176 (W) | 2011-07-29 | **2011-01-02** `LT05_L1TP_176044_20110102_20200823_02_T1` (entity LT51760442011002MTI00, cloud 0% per USGS, 1.3% flagged in the AOI by QA_PIXEL) |
| Path 175 (E) | 2011-10-10 | **2011-01-11** `LT05_L1TP_175044_20110111_20200823_02_T1` (LT51750442011011MTI00, cloud 0%) |
Reason: January matches the January 2002 and 1999 frames (sun elevation 37 deg vs 36 deg) and is 2 months from the November 2021 frames; the pair is 9 days apart like the 1999 pair. Other near candidates (2010-12-01/17, 2010-12-10, 2011-01-27) are no better. Both cover the AOIs. Lake conditions: in January 2011 the lakes are much smaller than in 2002 and 2021, with exposed light lake bed; this is a real state and useful for the story, but see the limitation in section 8 (late-2011 TM scenes do not exist after 2011-10).

## 2. Exact scene list (13 scenes, 78 files)
East Oweinat (WRS 177044, EPSG 32635): 1984-08-26 LT05 `..19840826_20200918`, 2000-01-11 LT05 `..20000111_20200907`, 2010-01-22 LT05 `..20100122_20200825` (reused), 2016-01-07 LC08 `..20160107_20200907`, 2024-01-05 LC09 `..20240105_20240105` (B4/B5/QA/MTL reused, B2/B3 new).
Toshka W (176044, EPSG 32636): 1999-01-01 LT05, 2002-01-09 LT05, 2011-01-02 LT05, 2021-11-13 LC08. Toshka E (175044): 1999-01-10 LT05, 2002-01-18 LT05, 2011-01-11 LT05, 2021-11-06 LC08. Full IDs, entity IDs and file names are in `manifest.json`.
Files per TM scene: B1, B2, B3, B4, QA_PIXEL, MTL.txt. Per OLI scene: B2, B3, B4, B5, QA_PIXEL, MTL.txt.

## 3. Exact transfer budget (recalculated from USGS file sizes, 1999 included)
New transfer: **1,945,917,679 bytes (1,945.9 MB; 1.812 GiB)** against the 2.0 GB authorization. Reused local files: 251,356,957 bytes (2010 TM set, 2024 B4/B5/QA/MTL). The earlier 1.8 GB estimate covered 2011 and 1999; the real per-band sizes (`reports/usgs_download_options_2026-10-08.json`) gave 1,945.9 MB. Actual downloaded bytes equal the planned bytes (no failed partial bytes were counted: failed files were removed by the downloader).

## 4. Download status and checksums
68 of 68 planned files downloaded, 0 failed in the end. USGS returned HTTP 504 on individual files in 5 runs (not credentials, not budget); the script resumes by skipping verified files, runs 1-6 progressed each time; two small files failed once more and succeeded on the next run. Each file was checked against the USGS SHA-512 and size when saved, then all 68 were hashed again from disk: **0 mismatches**. The 10 reused files (2010 TM, 2024 OLI) also match the USGS checksums (manifest field `sha512_matches_usgs`: true for all 78).

## 5. Manifest and restore
`manifest.json` (scene IDs, file names, USGS entity/product IDs, SHA-512, sizes, status, local path hints), `scripts/restore_source_bands.py` (verify, then download only missing/corrupt files within a budget; env `USGS_M2M_USERNAME`/`USGS_M2M_TOKEN`), `scripts/download.py` and `scripts/preflight.py` (what was actually run). Tested: `--check-only` reports 78 files ok on the local workspace and 78 missing (2,197,274,636 bytes) on an empty one. Workflow: `python3 scripts/restore_source_bands.py --manifest manifest.json --workspace <dir>`.

## 6. Radiometric processing (documented, same for every frame)
1. Level-1 DN from the band GeoTIFFs; DN 0 and QA_PIXEL fill bit are no-data.
2. TOA reflectance = (REFLECTANCE_MULT x DN + REFLECTANCE_ADD) / sin(sun elevation), coefficients and sun elevation from each scene's MTL. No atmospheric correction, no BRDF, no cross-sensor harmonization.
3. RGB: TM B3/B2/B1, OLI B4/B3/B2.
4. One fixed stretch per stack (Toshka mosaic: one stretch for both paths): per-channel pooled p1 to p99.5 over all frames, linear, gamma 1/1.6. The same limits for every frame, so brightness differences between frames are physical or seasonal, not per-frame auto-contrast.
5. Common grid: the old browse-derived grid was half a pixel off the Landsat lattice; the grids were shifted by 15 m so every scene sits at an integer pixel offset (all 13 scenes: offset 0.0, 0.0 relative to the grid). Result: cropping only, **no resampling** at 30 m.
Per-scene numbers: `reports/EO_report.json`, `TW_report.json`, `TE_report.json`.

## 7. Validation results
Registration (gradient phase correlation on the red band, whole frame, px at 30 m; reference = latest frame):
- East Oweinat: 1984 vs 2024 -0.03/-0.07 (SNR 60); 2000 vs 2024 -0.01/0.01; 2010 -> 2024 0.02/0.00; 2016 -> 2024 -0.01/-0.04. Adjacent pairs all within 0.12 px. This resolves the browse-only weakness of 1984 (SNR 11 then). 3x3 tiles are within 0.2 px wherever the tile has texture; a few featureless sand tiles return meaningless large values (ignore, no texture to correlate).
- Toshka W: all pairs within 0.11 px (SNR 276-492), including the new Jan-2011 frame (2011 vs 2021: 0.04/0.01), which could not be matched with the old July 2011 frame.
- Toshka E: all pairs within 0.08 px (SNR 1000-1530).
- Sensors: TM vs OLI pairs (2010-2016-2024, 2011-2021) agree to the same tolerance.
Cross-path seam W vs E (overlap strip 215 x 2219 px, 6.5 x 66.6 km, same-year pairs): shifts 1999 -0.01/0.00, 2002 0.00/0.00, 2011 0.00/-0.02, 2021 0.00/0.00 px (SNR 280-490). Reflectance difference E-W (median) <= 0.01 in every band; E/W ratio 0.98-1.04, blue +2 to +4% in all years, 2021 +2.6% in all bands. The feathered mosaic (`previews/toshka_mosaic_2x2.jpg`, `toshka_seam_crops.jpg`) shows no visible seam in 4 years. The union canvas is not a rectangle: black areas are outside both AOIs, not Landsat no-data.
No-data: every AOI window lies inside valid data (valid fraction 0.9969-1.0; TE 1999 loses 0.3% at an edge, 2021 TE 0.06%); QA cloud/shadow flags 0 to 0.3% except W 2011-01-02 at 1.3% (small cloud areas, check before use as a hero frame).
Seasonal vs long-term: East Oweinat 2000-2024 are all early/mid January with sun elevation 35-39 deg, comparable; 1984 is 26 August (sun 57 deg, desert brighter, almost no shadows), not comparable in tone. Toshka 1999/2002/2011 are January; 2021 is November (sun 45-47 deg), the whole frame is visibly pinker and lower in contrast. Lake extent differences between the 1999/2002/2011/2021 frames are mixtures of real change and season; no area figures or masks were made.
Previews: `previews/` (eo_sequence_source_bands, eo_field_crops_2010_2016_2024, align_*_red_vs_*_cyan, toshka_mosaic_2x2, toshka_seam_crops, toshka_2011_candidates).

## 8. Status and remaining blockers
- Geometry: **pass** (consistency within about 0.1 px between all dates and sensors; it measures relative alignment, not absolute georeferencing accuracy).
- Final-visual quality: **not yet production-ready**. Open items: (a) tone mapping: the pooled stretch makes the sand near white and the 1984 frame almost featureless, final grading is needed; (b) 1984 is a summer scene, 2021 a November scene: label or tone-match them; (c) no atmospheric correction or sensor harmonization (TOA only), so cross-sensor colour is approximate; (d) W 2011 has 1.3% flagged cloud/shadow; (e) 4K zoom to 30 m pixels needs a stated upscaling policy; (f) lake extent or water-area claims need validated water masks (not built, not narrated); (g) 2011 January lakes are low because of real change and are not a seasonal-matched proof of trend; (h) Toshka framing must avoid the non-rectangular union corners.
