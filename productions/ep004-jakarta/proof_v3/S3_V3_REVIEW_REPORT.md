# EP004 S3 V3 "Cutaway Descent" — TRUE 3-D REVIEW render (2026-10-16)

Status: **S3_V3_REVIEW_READY · TECHNICALLY_VALID · VISUALLY_REVIEWED (contact sheet 4 fps + temporal tests) · USER_APPROVED: NO**.
Not rendered: FINAL 1080p (needs the owner's separate approval). Budget $0. Main, EP001-EP003 and V2 untouched. Nothing published.

File (not in the public repo): `EP004_S3_V3_REVIEW.mp4`, 13.5 s, 1920x1080 container (3-D rendered at 1280x720, Lanczos-upscaled, 2-D type
drawn at 1080p), 30 fps, H.264 High yuv420p + AAC, faststart, 20,981,018 B,
sha256 `6125c262ca1c1b9c46dc31641514e6aef5b99b9b648946bc73c81827cfdf5130`.

## What it is
pbrt-v4 path-traced scene (real meshes, perspective thin-lens camera, motion blur, depth of field, textures + bump, physical sky + sun,
GI/soft shadows) — the same scene and V2 physics as the first V3 run, only the render settings changed. Scientific illustration, not a
reconstruction of a real site (chip on screen); no measured rate, coordinate or period; ESA and RSASE not used.

## Performance (measured, this container: 4-core Xeon 2.1 GHz, no GPU)
| | old run (first V3) | REVIEW |
|---|---|---|
| settings | 1440x810, 8 spp everywhere, serial post | 1280x720, 4 spp (8 spp only 4.3-7.2 s under strong DOF), pipelined post, static geometry cache |
| per frame, orbit / dive / underground / pass 2 / side-on | 21.6 / 28.9 / 33.9 / 23.2 / n.a. s | 6.7 / 8.9 / 19.4 (8 spp) / 8.3 / 10.1 s (pbrt) |
| average wall per frame | 27.0 s | 11.0 s |
| full 383 frames | ~172 min (projected; stopped at 270 frames) | 64.7 min for 352 frames + 31 reused test frames (~71 min equivalent) |
| post compose + encode (405 frames) | — | 3.4 min |
| peak RAM (whole system) | — | 1.74 GB of 15 GB |
Speed-up ~2.4x. The 270 frames of the old run are kept (reference for temporal QA).

## Quality (perf/TEMPORAL_QA.md)
- Underground, 45 continuous frames, REVIEW vs old 8 spp: no extra flicker (ratio 0.96), PSNR 36.3 dB, detail stability equal, no ghosting.
- 4 vs 8 spp under strong DOF: blotchy OIDN grain at 4 spp (Laplacian x2.2) -> that section rendered at 8 spp.
- Wide shots: 2 spp rejected (smeared edges), 4 spp accepted (PSNR 35.2 dB vs 8 spp, no flicker). Dive: 4 spp accepted.
- Loss vs the old settings: 1280x720 is slightly softer than 1440x810 on fine window textures (visible only zoomed in).

## QA of the REVIEW video (perf/review/qa_v3.json)
yt-qc PASS; 405/405 frames decoded; 0 black runs, 0 freezes; audio 13.5 s, -19.3 LUFS integrated, -4.8 dBTP (CC0 synthesised effects only,
like V2); phone readability 0 issues (captions 52 px, labels/chips >= 30 px). One float16 overflow pixel (inf) in frame 298 found and fixed
(clamped; render pipeline now clamps before saving).

## V2 vs V3
| | V2 (2.5-D, scene3d) | V3 REVIEW (true 3-D, pbrt-v4) |
|---|---|---|
| geometry | flat-shaded polygons sorted by depth | triangle meshes + quadrics, ~108k triangles, real strata thickness, half-cut well |
| light | Lambert + fog, no shadows | path tracing: sun + physical sky, GI, soft/contact shadows, AO from light transport |
| camera | painter projection, no blur | thin lens: depth of field underground, true motion blur on whips |
| materials | flat colours | textured strata with bump relief and per-layer face relief, gold-foil satellite, window facades |
| activity per second (mean abs frame diff, 320x180) | 0.3-5.3 | 2.6-18.9 |
| render time | ~4 min | ~71 min (REVIEW) |
| same | V2 physics (head drop, clay-only compaction, LOS = drop x cos i), captions, labels, lockup, placeholder card, sound cues |

## Known weaknesses (seen in the frames)
- 4.0-6.5 s underground holds one wall of the cut for long; macro and track help but the shot reads similar for ~2.5 s.
- City is procedural boxes; no volumetric light (post haze only); satellite is small in the wide shots.
- Not verified: sound by ear; real-time feel on the iPad.
