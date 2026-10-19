# EP005 NEOM / The Line - research log (2026-10-19)

Status: stage 1-2 research, nothing produced, nothing published.

## Method and limits (technical decisions)
- Competitor data: public YouTube search/browse JSON (no login). `competitors.json` holds 39 videos
  >=150K views with views, relative age, duration, channel subs, channel median of the ~10-30 most
  recent videos (rounded by YouTube, so approximate) and the multiple over that median.
- Exact publish dates were NOT retrievable: watch pages redirect to a blocked consent host and the
  `next` endpoint returned no date. Only relative age ("1mo ago") is recorded.
- Thumbnails and first 30 s were NOT analysed; no frame access in this sandbox.
- yt-dlp could not be installed (pip index unreachable). `yts.py`, `chan3.py` are the replacement.
- Sentinel hubs (Copernicus, AWS Earth Search, Planetary Computer) return 403 from this sandbox;
  NASA GIBS times out. USGS M2M and landsatlook STAC work. Landsat is the only usable source now.
- USGS `options` takes the entityId (e.g. `LC91730412026270LGN00`), not the displayId; displayId
  returns `no_options`.

## Landsat availability (point 28.0N 35.0E, r=15 km, cloud<=10)
Path/row 173/041 and 174/040-041. Scenes exist for every year checked (2020, 2022, 2024, 2025, 2026),
latest 2026-10-13 (LC09_L1TP_173041_20261013). Browse JPEG is whole-scene (7541x7681 px, 30 m); at
that scale The Line is not identifiable. UNVERIFIED: whether a 30 m crop shows the construction scar.
Needs the Natural Color GeoTIFF (14 MB) + yt-geo crop at known coordinates.

## Claims ledger (confidence)
- Announced 2021 as 170 km linear city: widely reported (official NEOM material) - high.
- 2024 Bloomberg: only ~2.4 km planned by 2030, 2030 population cut from 1.5M to <300K - medium-high (secondary retelling).
- Work paused/strategic review from Sept 2025, "2.4 km of foundations built": blogs only - LOW, must be re-sourced
  (WSJ, Bloomberg, Reuters, CNBC) before any on-screen claim. Do not say "built 2.4 km" yet.
- PIF governor: 2030 completion "good to have, not a must" - one aggregator, verify primary.
- Reuters Oct 2026: NEOM Stadium shelved - single aggregator, verify.
