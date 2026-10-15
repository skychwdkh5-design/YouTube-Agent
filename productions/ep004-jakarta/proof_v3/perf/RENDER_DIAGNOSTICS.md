# EP004 S3 V3 — 3-D render diagnostics and benchmark (2026-10-15)

Measured with `productions/ep004-jakarta/proof_v3/bench_v3.py` (compute budget 300 s, used 169 s + post/encode probe); raw numbers in
`bench_results.json`; full-batch log of 275 frames (1440x810, 8 spp) for the per-shot averages. Nothing here is a full render.

## Engine and method
pbrt-v4 (built from source, CPU only, `-march=native`, AVX-512), unidirectional spectral path tracer (`path`, max depth 5, regularize),
zsobol sampler, thin-lens camera with animated transform (motion blur), gbuffer film (colour + albedo + normal + position) ->
Intel OIDN 2.3.3 (CPU) -> numpy grade/haze/ACES -> Pillow 2-D layer -> ffmpeg x264. One frame at a time, pbrt uses 4 threads.

## Hardware
Intel Xeon @ 2.10 GHz, 4 cores / 4 threads (AVX-512), 15 GiB RAM. No GPU: no /dev/dri, no /dev/nvidia*, no CUDA/OptiX, no Vulkan device.
GPU acceleration is not used and cannot be used here; pbrt-v4's GPU path needs an NVIDIA GPU (OptiX).

## Scene (frame t = 6.0 s, pbrt --stats)
38 meshes, 108,066 triangles, 2 cylinders, 2 spheres; 165 lights (163 emissive area lights: beam dashes, rings, tubes, water column;
sun; sky map); 40 materials; 39 textures (27 MiB of image maps). BVH 63k nodes (4.7 MiB). Scene file 6.2 MB written per frame.
Camera rays 9.33 M (1440x810x8); avg path length 1.45; 58 % zero-radiance paths; 17.2 M regular + 8.5 M shadow rays in 33.4 s
= ~0.77 M rays/s on 4 cores.

## Where the time goes (one 1440x810, 8 spp underground frame; 37.0 s total)
| stage | s | share |
|---|---|---|
| Python scene write (6 MB text) | 0.52 | 1.4 % |
| pbrt parse + BVH + path tracing | 33.39 | 90.2 % |
| EXR -> PFM split + OIDN denoise + un-mirror | 2.07 | 5.6 % |
| grade (haze, ACES, bloom) | 0.99 | 2.7 % |
| upscale to 1080p | 0.04 | 0.1 % |
| compose 2-D layer (incl. load + grade) / x264 encode | 1.36 / 0.05 | separate pass |

Per-shot average of the full batch (render + denoise): orbit 21.6 s, dive 28.9 s, underground 33.9 s, pass-2 23.2 s; all 275 frames 27.0 s.

## Benchmarks (same frames; quality = mean absolute difference vs A on 0-255 after grade and 1080p upscale)
| test | settings | pbrt s | total s | quality diff |
|---|---|---|---|---|
| A current | 1440x810, 8 spp, blur + DOF + bump | 33.4 | 37.0 | 0 (reference) |
| B | 4 spp | 16.8 | 20.1 | 2.35 (not visible after OIDN) |
| B | 2 spp | 8.8 | 12.0 | 2.74 (not visible at viewing size) |
| C simplified geometry | 4 spp, 1,000+ distant buildings removed | 16.3 | 19.2 | 2.35 — geometry is NOT the bottleneck |
| D no motion blur / DOF / bump | 4 spp | 13.8 | 17.0 | 6.94 (look changes: no DOF) — saves 18 % |
| E path depth 2 | 4 spp | 17.3 | 20.7 | 2.36 — bounce depth is NOT the bottleneck |
| F lower resolution | 960x540, 4 spp | 7.6 | 9.3 | 2.94 (slightly softer) |
| wide shot (t = 1.2) | 1440x810 8 spp / 960x540 4 spp | 16.4 / 4.1 | 19.6 / 6.0 | 2.82 |
Earlier probe (960x540): gbuffer film vs rgb film +22 % cost (albedo/normal AOVs for OIDN).

Cost model: pbrt time ~ pixels x spp x 2.6e-6 s on this CPU (underground frames x1.35, wide x0.7).

## Findings
- Primary bottleneck: per-camera-sample path tracing on 4 slow CPU cores (shading, image/bump texture lookups, AOVs, 165-light sampling);
  not geometry, not bounce depth, not post-processing or encoding.
- 8 spp is wasted with OIDN: 4 spp (or 2 spp for wide shots) is visually identical after denoising.
- Python overhead is small (0.5 s/frame) but avoidable: static far city is regenerated and re-parsed every frame.
- Denoise/grade (~3 s) run serially after each pbrt call; they can overlap with the next frame.
