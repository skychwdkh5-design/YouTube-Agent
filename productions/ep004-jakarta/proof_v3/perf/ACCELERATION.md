# OrbitalAtlas 3-D production — acceleration architecture and measured results (2026-10-16)

All numbers are measurements in this container (4-core Xeon 2.1 GHz, AVX-512, 15 GB RAM, no GPU), EP004 S3 V3 scene (~108k triangles,
textured strata, 165 lights). Quality = PSNR / block-SSIM vs the REVIEW path-traced frames (`quality_cmp.py`), same frame indices.

## Architecture: one scene description, several renderers, caches at every level
```
scene_v3.py (geometry, physics, camera)  ──>  pbrt3d.Scene  ──┬─> pbrt text ──> pbrt-v4 path tracing ──> OIDN ──> HDR npz  (PREVIEW / REVIEW / FINAL)
                                              (records data)  └─> raster3d bundle ──> three.js WebGL2 (Chromium, SwiftShader) ──> JPEG  (DRAFT)
caches: static geometry include (+ raster bundle) · frame cache keyed by the SHA-1 of the frame's full scene text · HDR npz per frame
        (grade, type, sound are post-only: never re-render for them) · sky map converted once
```
| preset | renderer | settings | what it is for |
|---|---|---|---|
| DRAFT | raster3d (real 3-D rasterisation: same meshes, perspective camera, lens shift, sun shadow map, sky image light, PBR, fog, ACES) | 960x540, 30 fps | geometry, camera motion, light direction, composition |
| PREVIEW | pbrt-v4 + OIDN | 640x360, 2 spp, 15 fps (frames doubled) | first look at GI, DOF, motion blur, materials |
| REVIEW | pbrt-v4 + OIDN | 1280x720, 4 spp; 8 spp automatically when the DOF blur circle >= 5 px | owner approval |
| FINAL | pbrt-v4 + OIDN | 1920x1080, same sample rule | only after separate approval |
No preset swaps 3-D for 2.5-D: DRAFT draws the identical triangle meshes in perspective (parallax and occlusion are real); it lacks GI
bounces, soft area shadows, DOF and motion blur.

## Same test fragment: frames 162-206 (5.4-6.9 s, underground macro, strong DOF, 45 frames)
| mode | time for the fragment | per frame | vs REVIEW | PSNR / SSIM vs REVIEW |
|---|---|---|---|---|
| REVIEW (pbrt 1280x720, 8 spp here by the DOF rule) | 928.7 s | 20.6 s | 1x | reference |
| old run (pbrt 1440x810, 8 spp) | ~1,525 s | 33.9 s | 0.6x | 39.2 dB / 0.970 |
| PREVIEW (pbrt 640x360, 2 spp, OIDN) | 91.8 s | 2.04 s | **10.1x** | 33.4 dB / 0.925 |
| DRAFT (raster 960x540) | 48.7 s | 1.08 s | **19x** | 20.6 dB / 0.656 (no DOF/GI: different look, same geometry and camera) |

## Whole proof, scene to MP4 (383 frames, 12.75 s of 3-D + card)
| mode | render | compose + encode | end to end | speed-up | PSNR / SSIM vs REVIEW |
|---|---|---|---|---|---|
| REVIEW | 64.7 min (352 frames) + 31 reused ≈ 71 min | 3.4 min | ≈ 74 min | 1x | — |
| DRAFT | 7.2 min (export 1.1 + raster 6.1) | 0.8 min | **8.0 min** | **9.3x** | 16.9 dB / 0.63 (exposure since re-matched: mean shift -15 -> -2) |
| PREVIEW (15 fps) | 5.6 min | 1.7 min | **7.3 min** | **10.2x** | 28.4 dB / 0.88 |
| REVIEW, nothing changed (frame cache) | 0 frames rendered | — | **71 s** (hashing 383 scenes) | 60x | identical |
| REVIEW after one camera-key edit (final rise) | 30 frames re-rendered (353-382), 353 from cache | — | **6.4 min** | 11x | identical outside the edit |
Peak system RAM: REVIEW 1.74 GB, PREVIEW 1.25 GB, DRAFT (Chromium + SwiftShader) not limiting.

## Adaptive samples (REVIEW / FINAL)
pbrt's own per-pixel variance and a denoised-grain/albedo ratio did NOT separate the frames that need 8 spp (variance 0.12-0.14 on
DOF frames and 0.13 on the sharp dive/side views). The defect is caused by depth-of-field blur, so the rule uses the scene's own optics:
CoC = 2 * lens radius * f_px / focus distance (1080-line px). Measured 4-vs-8-spp grain (Laplacian ratio): CoC 3-4 px 0.93 (no grain),
7-8 px 1.42, 8-11 px 1.21, 13-25 px 2.2 -> **8 spp when CoC >= 5 px**. On S3: 73 frames at 8 spp (frames 139-211) instead of the hand table's 87.

## What did not help (measured)
- Caching textures / lights inside pbrt: a pbrt process costs 0.30-0.38 s of parse + texture load + BVH per frame (3 % of REVIEW);
  pbrt-v4 renders one scene per process, so this cannot be kept between frames without patching pbrt — not worth it.
- Simplifying geometry (-1,000 buildings): no change. Path depth 2 vs 5: no change. Raster MSAA: +15 % time; shadow map 2048 vs 1024: +8 %.
- Raster cost is fragment shading in SwiftShader (~0.9 s at 960x540, ~1.2-1.5 s at 1280x720); draw submission is ~15 ms, readback/encode the rest.

## Recommended workflow (next episodes)
1. DRAFT the whole sequence (≈8 min) -> fix camera, timing, composition. Re-DRAFT is cheap.
2. PREVIEW (≈7 min) when light/DOF/motion blur need checking.
3. REVIEW with the frame cache: first full run ≈ 70 min on this box; every later change re-renders only the frames whose scene changed.
4. FINAL 1080p only after approval (same cache logic; FINAL frames are a separate cache key because the resolution is in the scene text).
Faster true-3-D options that need the owner: allowlist download.blender.org (Blender EEVEE/Cycles), or a paid GPU (pbrt-v4 GPU/OptiX).
