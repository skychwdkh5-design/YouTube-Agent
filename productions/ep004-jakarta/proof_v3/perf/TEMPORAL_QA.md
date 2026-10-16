# EP004 S3 V3 — temporal quality of the optimised presets (2026-10-16)

Tool: `productions/ep004-jakarta/proof_v3/temporal_qa.py` (graded frames, same frame indices, same scene and camera). Raw JSON next to this file.
"Old" = the 270 frames of the first full run (1440x810, 8 spp), kept untouched in WORK/full and used as the independent reference.

## 1. Underground, the hardest shot (frames 162-206 = 5.4-6.9 s: tracking camera, macro, strong depth of field, motion blur, compaction)
REVIEW 1280x720 @ 4 spp + OIDN, 45 continuous frames, vs old 8 spp (downscaled to 1280x720):
| metric | value |
|---|---|
| PSNR / MAE per frame | 36.3 dB mean (min 35.5) / 2.55 of 255 |
| temporal high-frequency change (flicker), new / old | 0.96 (no extra flicker overall) |
| Laplacian detail stability (frame-to-frame CV) | 0.056 vs 0.057 |
| ghosting | none possible by construction (OIDN is per-frame, no temporal accumulation); none seen in the side-by-side |
| geometry, light, camera | identical (same scene, same camera path; side-by-side reviewed at 5 points) |
Controlled 4 vs 8 spp at the same 1280x720 (frames 180-189; static-pixel mask taken from the independent old render, so neither side
is favoured): static-pixel frame-to-frame change 0.90 vs 0.69 (x1.30), overall temporal HF ratio 0.98, PSNR 37.0 dB, Laplacian energy
x2.2 = residual blotchy OIDN grain in the defocused areas, visible at 2x zoom. Decision: **8 spp for 4.3-7.2 s** (depth of field active).
First metric version had a selection bias (static mask from the reference's own difference); corrected as above.

## 2. Wide orbit (frames 30-44), 2 / 4 / 8 spp at 1280x720
| spp | static-pixel change | temporal HF | Laplacian (detail) | PSNR vs 8 spp | render s/frame (pipelined) |
|---|---|---|---|---|---|
| 2 | 0.326 | 2.94 | 130 | 32.6 dB | 4.0 |
| 4 | 0.284 | 3.60 | 135 | 35.2 dB | 6.1 |
| 8 | 0.260 | 3.98 | 170 | — | 10.8 |
Decision: **2 spp rejected** (no flicker problem, but smeared/wobbly building edges at 2x zoom, -23 % detail); **4 spp accepted**.

## 3. Motion-blurred dive (frames 115-120, whip under the surface), 4 vs 8 spp
static-pixel change 0.47 vs 0.39, Laplacian 80 vs 82 (no excess grain), PSNR 34.5 dB -> **4 spp accepted**.

## 4. Optimisations measured
| change | result | kept |
|---|---|---|
| static geometry cache (distant city, ~1,100 buildings, written once, `Include`) | scene write 0.34 -> 0.13 s/frame, file 5.2 -> 3.1 MB; pbrt time unchanged (warm runs 0.45-0.59 s both); output bit-identical | yes |
| pipelined post (OIDN/EXR of frame i while frame i+1 path-traces) | 6 frames 78.2 -> 73.2 s (-6.4 %); pbrt +~1 s/frame from core contention; output bit-identical; peak system RAM 1.15 -> 1.47 GB (15 GB box) | yes |
| 4 spp (8 spp only under depth of field) | underground 1280x720: 11.4 s/frame at 4 spp, 21.8 s at 8 spp; wide 6.1 s | yes |
