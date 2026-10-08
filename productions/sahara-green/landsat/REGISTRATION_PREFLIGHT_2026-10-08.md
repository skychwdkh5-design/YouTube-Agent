# EP001 Landsat registration preflight (2026-10-08)

Local data only (13 browse GeoTIFFs, 2010 TM bundle, 2024 B4/B5). No new downloads. Method and raw numbers: `registration/registration_diag.json`, `registration/toshka_crosspath.json`, script `registration/registration_diag.py`. Previews: `registration/*_red_vs_*_cyan.jpg`.

Important: these are measurements on **browse** images (natural-colour, 30 m grid, already resampled by USGS and by yt-geo). Browse georeferencing alone does not prove pixel-level alignment. What is measured below is the *residual shift between frames* after yt-geo warping (gradient phase correlation), which is evidence of consistency, not proof of absolute accuracy.

## 1. Common CRS and pixel grid
| Stack | EPSG | Grid | Scenes | Source CRS |
|---|---|---|---|---|
| East Oweinat | 32635 | 2075x1757 px at 30 m | 5 (TM x3, OLI x2) | all 32635, 30 m, PixelIsArea |
| Toshka W (path 176) | 32636 | 2085x2251 | 4 | all 32636 |
| Toshka E (path 175) | 32636 | 2597x2985 | 4 | all 32636 |
All source rasters are north-up UTM at 30 m, so no reprojection is needed; yt-geo only crops/resamples to one grid per stack. Sub-pixel phase between each scene origin and the stack grid is 0.5 px in x and y for every scene (half-pixel resampling in the warp; same for all scenes, so it does not create relative shifts, but it softens detail slightly). W and E stacks have different grids (same EPSG) and are not yet on one common mosaic grid.

## 2. Relative alignment across years and sensors (whole-frame shift, px; 1 px = 30 m)
- **East Oweinat:** 2000 vs 2024: 0.01/0.01; 2010 vs 2024: -0.01/-0.01; 2016 vs 2024: -0.08/-0.03 (SNR 44-232). TM (2010) to OLI (2024) is therefore aligned within about 0.1 px by this measure. Red/cyan overlay of 2010 vs 2024 shows the same circles coinciding (`eo_2010_red_vs_2024_cyan.jpg`).
- **1984 (Landsat 5, August):** 1984 vs 2000: -0.03/-0.04 (SNR 97), but 1984 vs 2024 gave an unreliable -5/-17 (SNR 11, tiles inconsistent). The 1984 frame has almost no texture (gray std 1.7 vs 18 for 2024; featureless desert, different season), so correlation is weak. Treat 1984 alignment as **chained through 2000 (about 0.04 px), not independently confirmed**.
- **Toshka W:** 1999/2002/2021 within 0.08 px; 2011-07-29 vs 2021 failed (shift 240 px, SNR 9.9), because the lake state and season differ. Chained 2002 to 2011: -0.15/0.01 (SNR 74), so 2011 is probably aligned but not confirmed directly against 2021.
- **Toshka E:** all pairs within 0.15 px, SNR 165-790, 3x3 tiles within about 0.25 px. Best-behaved stack.
- 3x3 tile checks show no local distortion above about 0.5 px where texture exists; many tiles in low-texture or changing areas return no reliable value (blank or wild shifts), so tile results prove nothing there.

## 3. Cross-path alignment (Toshka W path 176 vs E path 175)
The AOIs overlap by only 6.5 km x 66.6 km (215 x 2219 px). Gradient correlation, same-year pairs: 1999 -0.01/-0.02; 2002 0.01/0.00; 2011 0.02/-0.15; 2021 -0.05/-0.06 px (SNR 70-299). Cross-path offsets are below about 0.15 px in this strip. Limitation: a strip along one seam only, and brightness differs (2011: mean gray 158 vs 151 because of season/date), so a visible seam would need radiometric matching even though geometry agrees.

## 4. No-data and black corners
Each raw scene has 69-75% valid pixels (diagonal black borders). Every AOI window lies 100% inside valid data and every stack frame has 0.0% no-data, so no black corners appear in the current crops. This holds only for these AOIs; wider framing (e.g. the 40-60 km view in scene 18) must be checked against the valid bounding polygon (yt-geo already refuses AOIs touching fill).

## 5. Seasonal differences
East Oweinat: five dates, four in January, 1984 in late August. Toshka: January (1999, 2002), July and October (2011), November (2021). Mean brightness varies by up to 25 grey levels and texture contrast by a factor of 10 (Toshka W 1999 std 5.7 vs 2021 std 47), mostly from sun angle, season and water. Any green-area or lake-area comparison across these frames must not be shown as seasonal-free change. Use same-season pairs where possible (EO 2000/2010/2016/2024 are all January).

## 6. Browse vs source bands
Browse is enough for: the time-lapse flip with registered frames, the zoom, and previews. It is not enough for: any measurement (colour-stretched, 8-bit, non-physical), NDVI/water masks, consistent brightness between frames, or a 4K zoom (30 m browse upsampled). Final visuals that make quantitative claims need source bands. I recommend source bands for final graphics so that all frames share one radiometric stretch (TOA reflectance).

## 7. Proposed next downloads (not executed)
Per-band files (individually addressable), natural colour plus NIR: TM B1-B4 (about 20 MB each, about 80 MB per scene); OLI B2-B5 (about 85 MB each, about 340 MB per scene); QA_PIXEL (<1 MB) and MTL for each. Sizes extrapolated from files already measured.
| Stack | Needed | Approx. size |
|---|---|---|
| East Oweinat | TM 1984, 2000 (B1-B4 + QA + MTL); OLI 2016 (B2-B5); OLI 2024 add B2, B3 (B4/B5 local); 2010 TM already local | about 0.67 GB |
| Toshka W+E | 6 TM (1999, 2002, 2011 x2 paths) B1-B4; 2 OLI (2021 x2 paths) B2-B5 | about 1.16 GB |
| Total | | about 1.8 GB |
Not recommended: full Level-1 bundles (OLI about 1.1 GB each). Toshka lake-area work should first fix the 2011 pair (same-season replacement scene) to avoid the 2011-07/10 vs 2021 mismatch. Waiting for the reviewer's approval of size and scene list before any download.

## 8. Conclusion
Geometry looks consistent to well under one pixel between 2000-2024 frames at East Oweinat and across all Toshka E and cross-path pairs; 1984 and Toshka W 2011 are only chained. This is a consistency check on browse products, not proof of absolute registration. Source bands plus the same diagnostics should be rerun on them before final render.
