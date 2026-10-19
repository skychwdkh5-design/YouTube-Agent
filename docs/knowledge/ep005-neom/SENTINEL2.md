# Sentinel-2 access and checks (2026-10-19)

## Access that works from this environment (free, no credentials)
- STAC search: `https://earth-search.aws.element84.com/v1` (200) and `https://planetarycomputer.microsoft.com/api/stac/v1` (200).
- The assets bucket `sentinel-cogs.s3.us-west-2.amazonaws.com` and `*.blob.core.windows.net` are BLOCKED (403), so Earth Search items cannot be downloaded.
- **Workaround that is legitimate and free:** the Planetary Computer *data API* (the same host that is allowed) crops and returns pixels:
  `.../api/data/v1/item/bbox/{minx},{miny},{maxx},{maxy}/{W}x{H}.png?collection=sentinel-2-l2a&item=<id>&assets=visual&asset_bidx=visual|1,2,3&nodata=0&coord_crs=EPSG:32636&dst_crs=EPSG:32636`
  (`.npy` instead of `.png` returns the raw digital numbers + mask for any band: B03, B04, B08, B11, B12, SCL). Script: `scripts/s2fetch.py`.
- Copernicus Data Space, NASA GIBS and Sentinel Hub: blocked or time out. Earth Search used only to confirm scene availability.

## Scenes (relative orbit 78, tile T36RYS, same 2-week window each October; `evidence_s2/provenance.json`)
2020-10-19 (S2A), 2021-10-04 (S2A), 2022-10-14 (S2B), 2023-10-14 (S2A), 2024-10-13 (S2B), 2025-10-13 (S2C), 2026-10-08 (S2C; cloud 1.04 %, area clear). Cloud <= 1.04 % scene-wide; the area was checked by eye in every frame.
Grid: UTM 36N, 10 m, 2180 x 928 px (21.8 x 9.3 km), all dates on the same grid (`evidence_s2/grid.json`), so wipes compare like with like.
Credit line (required by the Copernicus licence): "Contains modified Copernicus Sentinel data <year>".

## Controls against false conclusions
- **Shadows:** a shadow is dark in every band but has NDWI <= 0 and does not appear only in late years. The dark segment has NDWI > 0 with very low near-infrared in 2024, 2025 and 2026, on three different dates and satellites (S2B, S2C), and is absent in 2022-2023 under the same orbit and sun geometry. Sun elevation/azimuth are not published in the STAC properties used; dates are within 6 days of each other each year, so geometry is close but not identical.
- **Clouds:** scene cloud <= 1.04 %; no cloud shadow visible in any crop.
- **Processing differences:** the processing baseline ranges 02.12 (2020) to 05.13 (2026). It changes colour tone and the reflectance offset (+1000 from baseline 04.00), not geometry. Index analysis was run only on 2022-2026 (all >= 04.00) with the offset removed. 2020-2021 are used only visually.
- **Automatic scene classification (SCL)** labels the same pixels as water (202 px), non-vegetated (566) and dark (61) in 2025: unreliable for a target 40-60 m wide, so it is not used as evidence.
- **Geolocation:** all frames share one UTM grid built from the tiler's georeferencing; features in unchanged terrain (hills, roads) line up across dates. The corridor was fit as a straight line (88 of 105 samples inliers; `evidence_s2/corridor_fit.json`) and visually verified over the 2026 frame.
- **Official NEOM maps could not be opened** (neom.com blocked), so the corridor has NOT been matched against NEOM's own maps. It was matched only against secondary reporting (see CLAIMS.md).

## What the dark segment is
Spectrally consistent with standing water in a long, narrow, straight excavation: ~1.4-1.6 km long and about 20-50 m wide at its median (up to ~80 m at its widest, i.e. 2-8 pixels), inside a straight corridor; grey mounds nearby in the 2026 frame are consistent with excavated material but were not verified. Not established: depth, purpose, whether it is part of The Line's foundations or a drainage/stormwater/cut-and-cover section, or whether it was filled by groundwater or flood water. Do not name it.
