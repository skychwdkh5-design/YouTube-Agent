# Episode 001: Landsat production, controlled first test (2026-10-08)

The locked narration (SCRIPT LOCK v1.0, commit 706a280) was not touched. No imagery is committed except small previews. Raw data lives in an ignored workspace outside the repository (`.../scratchpad/landsat_work/ep001`; ephemeral, so re-download when needed).

## Preflight
- USGS M2M authentication: PASS (token from the environment, never printed).
- Candidate scenes, sizes and coverage: `preflight_2026-10-08.json`. All cloud cover 0% on the scene metadata. East Oweinat pivots lie inside path/row 177044; Toshka needs both 176044 (west and middle lakes) and 175044 (middle and east lakes).
- Level-1 product bundles over the 1 GB budget: East Oweinat 2024 (LC09, 1,085,614,005 bytes on the API), Toshka 2021 (LC08 176044 1,086 MB; LC08 175044 1,132 MB). Because of that, the 2024 scene was not selected for the test.
- Same-season pairs for Toshka: 2002 TM 176044 (09 Jan) + 175044 (18 Jan); 2021 OLI 176044 (13 Nov) + 175044 (06 Nov). Late 2011: no TM scene exists for path 176044 after 2011-07-29; 175044 has 2011-10-10. Lake state in 2011 was not previewed.

## Test scene (one scene)
`LT05_L1TP_177044_20100122_20200825_02_T1` (entity `LT51770442010022MTI00`), Landsat 5 TM, Collection 2 Level-1 Tier 1, acquired 2010-01-22 08:22:51Z, cloud 0%, sun elevation 38.9°. Chosen because it is a scene of the planned East Oweinat sequence, it has dozens of clearly visible pivots, and its Level-1 bundle (145.4 MB) is far under budget.
Downloaded: Level-1 product bundle (tar, 152,647,680 bytes) and the Full-Resolution Browse (Natural Color) GeoTIFF (1,677,867 bytes). Total about 154 MB. The first bundle request failed with HTTP 504 (no partial file, order removed); a single retry succeeded.

## Validation
- Integrity: tar extracted without errors (23 members); all 19 band/metadata files match the sizes listed by USGS; all six reflective bands decode fully (7851 x 6951 px, 8-bit); QA_PIXEL decodes (fill 29.9% outside the rotated scene, cloud bit 0.05%).
- Metadata (MTL): Level-1 TP, WGS84, UTM zone 35N (EPSG 32635), 30 m pixels, geometric RMSE 3.88 m.
- Geographic positioning: the UL and LR corners computed from the GeoTIFF tie point with yt-geo's UTM routine reproduce the MTL corner latitudes and longitudes to 0.3 m (UL 27.43479E 24.06869N; LR 29.71211E 22.16329N). The band files are PixelIsPoint with a tie point at 544200/2661900; the browse GeoTIFF is PixelIsArea with 544185/2661915: the same grid, 15 m = half a pixel apart by convention only.
- yt-geo workflow: `geostack.py` plan and `--confirm --contact` both ran (AOI 28.55-28.80E, 22.55-22.72N; 865 x 638 px at 30 m; output UTM 35N). Detected pivot centres (from Level-1 bands) land on the dark circles of the yt-geo stack: 98 circles inside the AOI, all darker inside than outside (median contrast 32 DN), best alignment within 1 pixel (30 m). Unit tests: yt-geo 8, yt-satellite 17, all OK (mocked, no network).
- Previews: `previews/test_eo_20100122_L1_rgb.jpg` (Level-1 B3/B2/B1, per-band 1-99.5 percentile stretch, 5 km bar) and `previews/test_eo_20100122_ytgeo_stack.jpg`.

## Pivot (irrigation circle) measurement, 2010-01-22
Details and examples: `measurements/east_oweinat_pivots_20100122.json`. Method: NDVI from 8-bit Level-1 DN, threshold, 4-connected components, isolated near-circular components only (250-1,400 px, bounding box square within 2 px, fill ratio at least 0.85); equivalent diameter from area; bounding-box diameter as a second estimate.
- 287 circles at NDVI 0.30: equivalent diameter median 752 m (IQR 667-791 m, 90th percentile 810 m, maximum 815 m); bounding-box diameter median 765 m (IQR 675-795 m, maximum 825 m). Thresholds 0.20 and 0.40 move the median by 6 m or less (756 and 746 m).
- Centre-to-centre spacing of neighbouring pivots: median 901 m (IQR 829-996 m).
- Uncertainty: 1 pixel (30 m) on a single diameter; partly irrigated or harvested circles read small, so the median is biased low; the full-circle diameter is best read from the upper quartile and maximum, about 790-825 m.
- This is one date and one sensor. The earlier browse-JPEG estimate for 2024 (median 0.87 km, Landsat 9, green-pixel mask) used a different product and method; the two are not comparable and the 2024 scene has not been measured on original bands.

## Issues found
1. **Locked wording vs measurement.** The narration says the circles are "each roughly a kilometer across". On original Level-1 bands (2010) typical circles are about 0.75-0.8 km across (about half a mile) and about 0.9-1.0 km apart. "Roughly a kilometer" overstates the diameter by about 20-25%; it matches the spacing. The 2024 scene must be measured before deciding; any wording change needs a new audit entry because of the script lock.
2. A bundle for the 2024 OLI scene and for both 2021 Toshka OLI scenes exceeds 1 GB. The USGS options list "Band File" products with 20 secondary files each; the existing `usgs_m2m.py download` would fetch all of them and cannot pick bands. Not yet tested: whether single bands can be requested through the band-file dataset.
3. The bundle download can return HTTP 504 once; one retry worked.
4. Landsat 7 ETM+ scenes after 2003 have scan-line gaps (stripes); avoid them for Toshka 2012 and the 2021 east scene.
5. No TM scene exists between 2011-07-29 and the end of the TM archive for path 176044; check that late-2011 lakes are in the intended state before using that alternative.

Not claimed: that the full Landsat sequence is ready.
