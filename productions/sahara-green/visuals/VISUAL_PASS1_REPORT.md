# EP001 visual production pass 1: review report (2026-10-08)

Status: **review pass, not final.** Narration lock v1.1 untouched (hash `d646001c…f335` checked). Inputs: verified source-band stacks from commit 0d76377. Nothing generative was used.

## Deliverables (all in `visuals/`)
| Item | Path |
|---|---|
| East Oweinat review animation (1280x720, 24 fps, 22.5 s) | `previews/east_oweinat_review_720p.mp4` |
| Toshka review animation (1280x720, 24 fps, 17 s) | `previews/toshka_review_720p.mp4` |
| Representative stills (1920x1080 JPG) | `previews/stills/` (eo_1984/2000/2010/2016/2024, eo_zoom_50/100, toshka_1999/2002/2011/2021) |
| Tonal comparison | `previews/tonal_comparison.jpg`, `reports/tonal_stats.json` |
| Cloud/shadow validation | `previews/cloud_2011_overlay.jpg`, `previews/cloud_2011_blob_crops.jpg`, `reports/cloud_validation.json` |
| QA results | `reports/qa_results.json` (16 checks) |
| Scripts | `scripts/` (build_frames, render, stills, tonal_compare, cloud_check, qa, vis_common) |

## East Oweinat (Scene 18)
Layout: full 62 x 53 km AOI (2075 x 1757 px at 30 m) in a right panel with a left info panel (title, current date, sensor, timeline). Sequence: 1984, 2000, 2010, 2016, 2024, each 2.0 s with 1.0 s dissolves, then a 6 s eased zoom (log-scale) into the densest circle area of the 2024 frame, ending on a 960 x 540 source window (28.8 x 16.2 km) with a computed scale bar and the caption "Center-pivot circles, about half a mile across" (supported by the L1 measurement, round 10). Labels: August 26, 1984; January 2000; January 2010; January 2016; January 2024, each with its sensor. The sequence is a set of single dates, labelled "Single dates, not a continuous record".

## Toshka
Display frame: a fixed 3840 x 2160 crop (union grid y0=60, x0=312) of the feathered W+E (paths 176+175) mosaic, **1 source pixel = 1 screen pixel at 4K**. The crop and a 12 px margin lie inside the footprint of all four years (no black corners; no pure-black pixels in any frame). Sequence: January 1999, January 2002, January 2011, November 2021 (3.0 s holds, 1.2 s dissolves, 1.5 s end hold) with a four-point date timeline, scale bar and the line "Single dates, not a continuous record." No lake outline, area figure or trend graphic. The four dates are different seasons (three January, one November); the label says so by showing the month.

## Tonal policy
Baseline (used): TOA reflectance (as in the source-band step), then one fixed curve for every frame, band and place: `out = clip((r - 0.02) / (0.60 - 0.02), 0, 1) ** (1/1.8)`, identical constants for East Oweinat and Toshka and for TM, OLI and OLI-2. No per-frame or per-stack statistics, no colour matching between sensors, no local contrast, no sharpening. Rejected variants are shown in `tonal_comparison.jpg`: A (previous pooled per-stack stretch: sand near white, the 1984 frame loses all texture) and C (per-frame percentile stretch: hides the real August/January brightness difference and turns the featureless 1984 sand into false texture and colour). On unchanged bare sand (2.16 M pixels, red reflectance 0.30-0.55 in all frames) the median colour varies by at most 7, 8, 1 levels (R, G, B) across the five East Oweinat frames under the baseline, against 68, 70, 59 under variant C. Residual differences are physical (season, sun elevation, sensor) and are not corrected. Dissolves blend two toned frames linearly and add no image content.

## Cloud and shadow validation (Toshka January 2011, display region)
QA_PIXEL flags (dilated cloud, cirrus, cloud, shadow) inside the display crop: 2011 = 59,510 px (0.72% of the crop; W 2011-01-02: 1.43% of the area W covers in the crop, E 2011-01-11: 0.10%); 1999 0.14%, 2002 0.10%, 2021 0.11%. Inspection of the full-resolution flagged regions (three largest W blobs plus the overlay) shows **no cloud or cloud-shadow morphology**: the flags sit on shallow lake margins and wet lake bed, and on a bright salt/sand patch at the lower left of the crop. The flags are false positives of the Level-1 QA algorithm on bright sand and dark shallow water. **Effect on the composition: none**; nothing was masked or retouched. Consequence for later work: the QA mask must not be used as a water or cloud mask for the lakes.

## Upscale policy (documented; final render not run)
- Method: Lanczos resampling of the 30 m source (Pillow), sub-pixel crop box, no sharpening, no denoise, no AI or generative super-resolution, no synthetic texture.
- Maximum magnification at 4K (3840 x 2160): 4.0 screen pixels per source pixel (East Oweinat zoom end, 960 x 540 source window, i.e. one circle about 27 source px is about 107 px across). At 1080p this is 2.0x. The 4K Toshka frame is 1:1, no scaling. No zoom may go below a 960 x 540 source window.
- The source is 30 m; at 4.0x fine detail is smoothed, not sharper. Edges of circles are real (about 27 px diameter); no detail finer than a pixel is claimed.
- Review previews are 1280 x 720 (scale 2/3 of 1080p design); the same code renders 3840 x 2160 with `--scale 2`. A 4K test still of Toshka 2021 and the zoom end was rendered once to confirm the pipeline (3840 x 2160, scale 1.0 and 4.0); they are not committed.

## QA results (`reports/qa_results.json`: 16 PASS, 0 FAIL)
- Registration of the rendered display frames: East Oweinat all pairs within 0.13 px (SNR 110-310); Toshka crop within 0.03 px (SNR 1200+); tolerance 0.2 px at 30 m.
- Crop boundaries: identical grid and crop box for all frames; 0 pure-black pixels in 9 frames; Toshka crop plus 12 px margin inside all four footprints (min valid fraction 1.0).
- Dates: labels derived from metadata match for East Oweinat (1984 shown as August 26, 1984) and for both Toshka paths (2021 = November 2021).
- Temporal order: 1984, 2000, 2010, 2016, 2024 then zoom on 2024; 1999, 2002, 2011, 2021.
- Colour stability and artificial change: cached frames equal a fresh application of the fixed baseline (Toshka within 1 level from float16 storage); stable-sand spread within 8 levels.
- Captions: exact strings in `scripts/render.py`; the zoom note appears only at the end of the zoom. Videos probed: h264, yuv420p, 1280 x 720, 24 fps, 540 and 408 frames.
- Not automated: legibility of captions on the video (checked by eye on stills at 1920 x 1080 and frames at 640 px).

## Remaining blockers before "final"
1. Reviewer decision on look: the baseline is a natural, slightly warm "sand" tone; confirm or request a different fixed curve (any change applies to all frames).
2. The 1984 frame (late August, sun 57 deg) is physically brighter and featureless; acceptable as "barren", the label says August.
3. 2021 (November) frames are cooler and contrastier than January frames; labelled, not corrected.
4. Caption wording, fonts and layout need review; the zoom note ("about half a mile") matches narration v1.1; lower-third copy is not part of the locked narration.
5. Timings are placeholders until the voice pass (storyboard timings are still estimates).
6. 4K final render and QC run are pending reviewer approval (not run in this pass).
7. The zoom target (densest 2024 circle area, left side of the AOI) is automatic; a manual choice may be preferred.
