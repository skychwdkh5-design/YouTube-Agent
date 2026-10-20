---
name: yt-sentinel
description: >-
  Free Sentinel-2 L2A (10 m) imagery for a video: find scenes, pick one per year on the same orbit and season, build a
  co-registered UTM stack with provenance and the Copernicus credit, and run a water/shadow check. Use when a video
  needs sharper satellite frames than Landsat's 30 m, or a same-orbit before/after series.
---

# yt-sentinel

```bash
python3 sentinel.py pick  --aoi 35.10,28.07,35.32,28.15 --years 2020,2022,2024,2026 --window 09-28:10-20 --cloud 3
python3 sentinel.py stack --aoi ... --years ... --out evidence/stack --confirm          # free download; --pixel-m 10 default
python3 sentinel.py ndwi  --item <STAC item id> --bbox minlon,minlat,maxlon,maxlat
python3 test_sentinel.py            # offline;  YT_SENTINEL_LIVE=1 python3 test_sentinel.py  adds a live free fetch
```
Output: `y<year>.png`, `grid.json` (yt-geo-stack/1, UTM, square pixels), `provenance.json` (item id, date, orbit, cloud, baseline, sha256, licence, credit).

- Access: Planetary Computer STAC + data API (works from the cloud sandbox). The S3/blob asset buckets and Copernicus hubs are blocked there.
- One orbit and tile for all years; a year with no suitable scene is reported missing, never substituted. If the first scene does not cover the AOI, the next
  candidate is tried and the rejected ids are recorded.
- Processing baselines differ across years (02.12 .. 05.13): colour tone and the +1000 reflectance offset change, geometry does not. Indices only for >= 04.00.
- `ndwi` returns counts only (water-like pixels). A shadow has NDWI <= 0. It never names the object; claims say "consistent with".
- Credit on screen: "Contains modified Copernicus Sentinel data <year>".
