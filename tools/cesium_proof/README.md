# Cesium proof harness (CPU, free data only)
Local caching proxy + page + Playwright capture used for the Phase 2 visual gate. Not an episode renderer.
- `python3 server.py` serves `index.html`, proxies `/cesium/*` to cdn.jsdelivr.net (CesiumJS 1.120.0) and `/gibs/*` to NASA GIBS, caches under `./cache/` (create it).
- `node static.js '[{"cfg":"A","v":[lon,lat,range_m,heading_deg,pitch_deg],"out":"x.png"}]'` captures static frames (`cfg` A..D = GIBS layer sets in `index.html`). Needs global Playwright (`/opt/node22/lib/node_modules/playwright`).
- `run_frames.js` is the older frame-sequence capture that uses `setFrame(u)` (V1 proof; the current `index.html` no longer defines `setFrame`, keep for reference).
Results and verdict: `docs/KNOWN_LIMITATIONS.md`, `docs/RENDER_BENCHMARKS.md`.
