# Render benchmarks (measured; assumptions marked)

Environment: cloud container, 4 CPU, 15 GB RAM, no GPU (`/dev/dri` absent), Chromium 1194 (Playwright), Node 22, FFmpeg 6.1. Date 2026-10-09.

| test | setup | measured result |
|---|---|---|
| WebGL capability | headless Chromium `--headless=new --no-sandbox --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist`, one triangle, 400×300 | WebGL1 OK, WebGL2 OK, renderer "ANGLE (Google, Vulkan 1.3.0, SwiftShader Device Subzero)", PNG not blank (37,085 colours), 2.8 s incl. start-up |
| CesiumJS 1.120.0 proof V1 | custom local caching server (jsdelivr + GIBS), Blue Marble L8 + Landsat WELD L12, perspective camera `lookAt`, 1280×720, 3 parallel Chromium workers, `requestRenderMode` | 146 of 168 planned frames in 545 s (stopped at the 9 min limit) = 0.27 frames/s aggregate; per frame 3.7–20.5 s (first frame 20.5 s = tile fetch; frames with only 4 polls still took 15.9 s = render cost); 1,180 image tiles / 8.7 MB cached; 5 tiles returned 502 |
| H.264 encode of those frames | `ffmpeg -framerate 24 -crf 20` | 146 frames → 6.08 s, 2.9 MB (encode time not recorded; negligible next to capture) |
| GIBS GetCapabilities | `curl` | 5.8 MB, HTTP 200 |

Findings (measured): CPU rasterisation dominates, not network; each frame was rendered ≥ 5 times (poll loop + pre-screenshot render); the three workers compete for 4 cores.
Estimates (**assumption, not measured**): removing redundant renders and prewarming tiles could give 2–3× speed-up → 7 s at 24 fps in 3–5 min at 720p. 1080p costs about 2.25× the pixels.
Rule: 12–15 s proofs only; log every benchmark here with date; do not repeat the WebGL capability test unless the environment changes.

| Cesium static frame (Phase 2) | same harness, 1 browser, 1280x720, close-up Dubai, GIBS layers | config A 12.4 s, config B 22.7 s including start-up and tile fetch (cold cache) |
| EP002 transition proof (Phase 3) | 56 Cesium frames 1280x720, 3 workers (cache warm for the Gulf region) | 187 s (first run; one worker timed out on page load and was re-run, +88 s); the earlier cfg-A render of the same path 267 s. Composite of 120 frames (GeoFocus, CPU) 58-62 s; H.264 encode 4 s |
