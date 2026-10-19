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

---
# Update 2: Landsat evidence (same day, after owner approval)

## What was downloaded (free, USGS M2M, Natural Color GeoTIFF browse, ~3-5 MB each, order cleaned up)
Path/row 174/040, Landsat 8, all Sep-Nov for a like-for-like season: 2020-09-25, 2021-09-28, 2022-10-17,
2023-10-20, 2024-10-22, 2025-10-25, 2026-09-26 (IDs in `inputs/scenes174.json`, provenance in
`evidence/provenance.json`). Stack: AOI 34.7-35.3 E, 28.0-28.6 N, 30 m, UTM 36N (`inputs/stack_wide.json`).

## Technical decisions and lessons
- Path/row 173/041 cannot be used: the site sits on its rotated NW edge, yt-geo refuses (no-data fill).
  174/040 covers it. Always test coverage with yt-geo plan mode before downloading more.
- The first cloud-free-by-metadata 2020 scene (2020-10-27) had clouds over the area (metadata cloud is a
  whole-scene number). Replaced with 2020-09-25. Always look at the crop before trusting a date.
- USGS `options`/`download` need entityId, not displayId.
- Location was found visually, not from a source: the NEOM Stadium planning coordinate (28.116 N, 35.104 E,
  Wikipedia via search) was the only coordinate available; a straight E-W corridor passes ~1 km from it.
- Dark-segment length was measured from per-column luminance contrast on the yt-geo grid (rough, +-1 px = 30 m).
  `measure.json` 2022/2023 "strong runs" are noise (no segment yet); only 2024-2026 are meaningful.
  The "corridor km" values in it are crude; do not quote them. Visual estimate: corridor >= ~15 km inside the AOI.
- Evidence graphics via yt-graphics: credit text must be short (<= ~25 chars) in `compare` panels.

## Environment limits found (owner can lift in environment network settings)
Blocked hosts (403): reuters.com, bloomberg.com, wsj.com, cnbc.com, neom.com, pif.gov.sa, semafor.com,
newatlas.com, dezeen.com, agbi.com, archinect.com, wikipedia.org, earth-search.aws.element84.com,
catalogue.dataspace.copernicus.eu, planetarycomputer.microsoft.com; NASA GIBS times out.
Consequence: no primary-source reading; facts are verified only through search-engine summaries of secondary
coverage and are labelled as such in `CLAIMS.md`. Sentinel-2 (10 m, free) would make the imagery ~9x sharper
in area; it is the single best upgrade for CTR and visual quality.

---
# Update 3: round 2 (Sentinel-2, sources, competitors, prototype)
- Sentinel-2 is reachable only through the Planetary Computer *data API* (crop/resample/`npy` of any band); the Earth Search and PC asset hosts are blocked. Recorded in `SENTINEL2.md`, code in `scripts/s2fetch.py`.
- Tile T36RYS, relative orbit 78 gives small nodata at the site; orbit 121 slices have ~47 % nodata there - choose by nodata_pixel_percentage.
- The tiler returns RGBA PNG; with `coord_crs`/`dst_crs` = the UTM zone the output is on an exact UTM grid, so it drops into yt-geo/yt-graphics/yt-render via a hand-written `grid.json` (schema `yt-geo-stack/1`) without GeoTIFF reading.
- A yt-graphics `compare` panel allows at most (stack height x 16/9) km wide: 16 km for a 9.3 km-tall stack. Arrow/title/scale-bar collisions are refused, not drawn over: move the arrow or disable the graticule.
- A yt-render v3 long timeline needs no narration if `end.seconds` is set; `t` on a graphic layer must be `[0, null]`; a camera must stay inside the stack (width and centre).
- Do not put a custom label over a `wipe` layer: it draws its own year labels and the two overlap.
- yt-qc `--profile long` fails a 15 s silent clip (duration, loudness, audio start) - expected for a prototype.
- YouTube player/caption endpoints require login: first-30-seconds analysis is not possible without bypassing it; not attempted.
- Source hosts blocked this round as well: all primary news hosts, wikipedia, neom.com, pif.gov.sa, OSM/Overpass. Fix: Allowed domains in the environment's network settings.
