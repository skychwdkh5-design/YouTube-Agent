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
| EP002 A1 v2 Cesium capture (2026-10-10) | 372 frames 960x540, DSF 1.5, 3 workers, fast loop (`run_frames_fast.js`) | ~11 min wall after fixing two pitfalls; the same capture with a global-layer `minimumLevel` or the old force-render loop took 90 s+ per frame (measured over 3 frames, aborted) |
| EP002 full preview build V2 | 28 scenes at 24 fps, 4 parallel scene processes, ffmpeg raw pipe | 383 s for all scenes (12,912 frames); single-scene rebuilds 150-300 s; `qa_preview.py` 52 s, `qa_rects.py` ~30 s, `landmarks.py` ~35 s |
| EP002 final 1080p30 (2026-10-13) | 29 scenes, 15,682 frames, x264 crf 19 medium, 4 processes, native-scale kit (EP002_SCALE=2) | about 45 min wall; mux + two-pass loudnorm about 1 min; yt-qc full decode about 3-5 min; A1 Cesium HD capture (372 frames, DSF 2, 3 workers) 10.7 min |

| EP003 director render 1080p30 (2026-10-14/15) | 372.6 s, 11,177 frames, orbitalatlas.director, 4 workers, --sfx | 41.6-44.5 min wall (~7 s per video second); output ~890 MB (19 Mbit/s); review copy x264 crf 24 maxrate 1.7M = 85 MB in ~6 min; 720p 480k = 27 MB; stills (12 frames at 960x540) ~55 s - use stills, not full renders, to check fixes |
| EP004 S3 V1 proof (2026-10-15) | 13.5 s, 405 frames 1080p30, `orbitalatlas.illustrate`, 2x canvas, 4 workers | 112 s wall (~8.3 s per video second) |
| EP004 S3 V2 proof (2026-10-15) | 13.5 s, 405 frames 1080p30, `orbitalatlas.scene3d` + `subsidence3d` (~2.5k polygons/frame, 2x canvas, glow, grade), 4 workers | about 3.5-4 min wall (~1.0-1.4 s per frame single-thread, ~16 s per video second); QA script 72 s |
| EP004 S3 V3 true-3D (pbrt-v4 CPU path tracing + OIDN, 2026-10-15) | city block ~3,000 boxes + textured strata + well + satellite, motion-blurred camera, 4 cores, no GPU | 960x540 @ 8 spp: 11-15 s/frame (test 3-7 s, 120 frames: ~26 min); 1440x810 @ 8 spp: ~19 s/frame wide shots (full proof 383 frames: see the proof report); per-sample cost ~1.2 s per spp at 960x540; path depth 3 vs 5 no change; coateddiffuse -> diffuse saves ~30 %; OIDN + EXR/PFM conversion ~1-2 s/frame; post compose 120 frames ~60 s |
| EP004 S3 V3 render diagnostics (2026-10-15, `proof_v3/perf/RENDER_DIAGNOSTICS.md`) | pbrt-v4 CPU, 4 cores, no GPU; underground frame t=6.0 | 1440x810: 8 spp 37.0 s, 4 spp 20.1 s, 2 spp 12.0 s total; 960x540 4 spp 9.3 s; pbrt = 90 % of the frame; geometry cut and path depth 2 change nothing; no blur/DOF/bump -18 %; OIDN makes 4/2 spp visually equal to 8; cost ~ pixels x spp x 2.6e-6 s |
| EP004 S3 V3 REVIEW full render (2026-10-16) | 1280x720, 4 spp (8 spp under DOF 4.3-7.2 s), pipelined post, static cache, 4 cores | 352 frames in 64.7 min (11.0 s/frame wall; pbrt orbit 6.7, dive 8.9, DOF 8-spp 19.4, pass-2 8.3, side-on 10.1 s) + 31 reused test frames; compose + encode 405 frames 3.4 min; peak system RAM 1.74 GB; 2.4x faster than the 8-spp 1440x810 run |
