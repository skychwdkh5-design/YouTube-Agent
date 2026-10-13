# Motion graphics toolkit (EP002 implementation notes)
Code: `productions/dubai/preview/{kit,scenes,scenes_v6,sync,build_final}.py`. Rule for new episodes: reuse these components or promote them to `orbitalatlas/`; do not write a new renderer per episode.

| need | component | status |
|---|---|---|
| camera path through keyframes (Catmull-Rom on centre and log-width, 16:9 kept, clamped inside the source) | `scenes.path`, `key_rect`, `clampr` | **[VERIFIED]** |
| traced shoreline / land outline from image pixels (colour distance from a sea-only patch, persistence filter) | `scenes.coast_line`, `scenes_v6.trace`, `overlay` | **[VERIFIED]** by eye on every frame set; thresholds: ASTER 2000-2011 = 38, ASTER 2006 = 110 |
| "new land" = non-sea in later frame AND sea in earlier frame (same grid), fill + outline draw-on | `scenes.new_land`, `overlay_new_land` | **[VERIFIED]** for ASTER 2000 vs 2003 only |
| draw-on arrow, dashed ring draw-on, sea tint, spotlight, ping, callout, counter, timeline strip | `scenes.arrow/ring_dashed/sea_tint/spot`, `kit.Canvas.ping/callout`, `scenes_v6.strip` | **[VERIFIED]** |
| one-label-at-a-time pill | `scenes.big` | **[VERIFIED]** |
| entry transitions (iris, slide, dissolve) from the previous scene's last frame, duration unchanged | `scenes.with_entry` | **[VERIFIED]** |
| two-panel compare, filmstrip with dated playhead, thumbnails on a dated axis | `scenes_v6.C6/E1/D5` | **[VERIFIED]** |
| globe descent (class C) | Cesium + NASA GIBS via `tools/cesium_proof` | **[VERIFIED]**, slow (see RENDERING.md) |
| scale bar, distances, coordinates | none | **[RULE]** forbidden without a verified georeference |

Outline pitfalls **[VERIFIED]**: coast and clouds leak into masks (restrict by radius around the landmark; use the "new land" difference mask for a palm; rows above 1090 of the 2000 frame are unreliable because of the creek and clouds); thin fronds vanish with a 5 px structuring element (use MaxFilter(3) on the edge only); outlines drawn from a 3x3-px mask edge need 3-5 px lines to read.
Hypothesis **[HYPOTHESIS]**: per-sentence cue anchoring is enough for sync of graphics; confirm on the next episode with a frame-accurate check.
- Labels **[VERIFIED]**: `Canvas.callout` keeps text inside a 24 px margin and the 96..H-90 band, hides labels whose landmark is outside the frame, and strokes text dark (2 px) so amber stays readable on sand; scrolling elements (filmstrip) must fade labels before the edge.
- Legibility rules **[VERIFIED, EP002 v3]**: any text on imagery sits on a dark pill (`Canvas.pill`, `Canvas.callout` backing, `scenes.big`); amber/white text straight on sand, ice or cloud measured 1.1-2.9:1. Muted grey is for chips on dark pills only. Disclosure chips (instrument, "not satellite imagery", "schematic") are >= 12 px at 540p. Captions inside a schematic panel are wrapped to the panel width (two lines). A timeline backing must end before the date label starts.
- Minimal motion for static card moments **[VERIFIED]**: a scan line over the image being described plus a stronger slow zoom (D5), slow pan + 14 % drift on both panels (C6). Proposed, not applied (below the 2 s threshold): B3 floating particles + surface shimmer + pulse along the dredge pipe; B4 cell-by-cell fill progress on the placement grid + pulsing GPS rings.


## V4 additions (2026-10-13)
- VERIFIED: hook opener = real NASA GIBS globe descent (Cesium frames 60..end, compressed to ~4.5 s) dissolving into ASTER 2000 on "a patch of the Persian Gulf"; top scrim keeps the spoken date readable on bright desert. Chip states "orientation only" (modern imagery, not the 2000 scene).
- VERIFIED: schematic scenes (B3, B4) get a keyed zoom/pan camera (`camk` + `cam_apply` in scenes.py) applied to the finished illustration; fixed pills are drawn after it. Zoom <=1.3-1.5 and focus clamped; callouts need `out=` before the camera leaves them (half-cut text during pans otherwise).
- VERIFIED: B5 multi-key satellite camera (`lerp_keys`), C3 recession timeline (2006-2009 axis, 2007-2008 shaded), E6 credits over a drifting dimmed ASTER 2006 frame, A1 starts over the Gulf (frame 140) so the globe is not shown twice.
- HYPOTHESIS: text-bounds QA does not see zoomed text in camera scenes; check frames of B3/B4 by eye.
