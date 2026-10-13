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

