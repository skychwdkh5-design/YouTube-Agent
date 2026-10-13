# Motion design standards
Each rule: WHEN · HOW (implementation) · VERIFY · NOT WHEN. Numbers are starting points, tuned by review.

| principle | when | how | verify | not when |
|---|---|---|---|---|
| Hierarchy: one hero per beat | every beat | one animated element leads; others static or <40 % contrast; ≤3 animating at once | frame-diff heat: motion area concentrated; reviewer names the hero in 1 s | dense data scenes that are *meant* to be scanned |
| Contrast/legibility | all text | text ≥ 4.5:1 vs local background, shadow/plate if image is busy; min 36 px label at 1080p | sample background luminance under text bbox (script) | decorative micro-chips (≥18 px, but never carrying a claim) |
| Gestalt: proximity/continuity | labels, callouts | label within 1 text-height of its subject, or tethered by a leader line; text parallel to a coast follows its direction | collision registry (UIREG), overlap = fail | |
| Easing | all motion | camera: smooth in/out (PCHIP/smootherstep); labels: ease-out cubic 0.25–0.4 s; traced strokes: linear; never linear camera starts/stops | plot velocity curve; no discontinuity in acceleration >1 frame | constant-speed "scan" strokes |
| Anticipation/follow-through | camera arrivals, reveals | 3–6 frame ease-in before big moves; overshoot ≤2 % then settle on arrivals; hold ≥1.2 s after final reveal | velocity at arrival → 0 | whip transitions |
| Spacing & rhythm | edit | alternate fast beats (1.5–3 s) with holds; vary shot size; no 3 identical moves in a row | storyboard table: camera type/transition per scene must not repeat 3× | |
| Typography animation | key words | reveal on the word's start time (±1 frame of provider word timing); per-glyph stagger 20–70 ms; exit before next hero | compare reveal frame to word timestamp | full sentences (use subtitles) |
| Type | all | one sans family, ≤2 weights, uppercase+tracking for place names, safe margin 96 px, subtitle zone bottom 12 % | bbox inside safe area, no clipping at any frame | |
| Color | all | brand tokens (see MOTION_DESIGN_SYSTEM §3): cyan = traced/sea, amber = land/annotation, white = hero text; one accent per beat | palette sampler | evidence imagery: never grade or tint it |
| Depth/parallax | UI over imagery only | blurred darkened copy as background for panels; UI drift ≤8 px | | parallax on satellite imagery (no depth data) |
| Motion blur | fast camera (>~600 px/s source) | temporal sub-sampling, speed-dependent samples | check no ghosting on text (UI drawn after blur) | slow moves (wasted time) |
| Masking/compositing | reveals | layer order: evidence → traced → fills → text; fills are alpha-masked from traced polygons | edge of fill sits on traced edge (visual) | |
| Information density | every beat | ≤1 new fact per 2 s; ≤2 labels visible together unless comparing | count text objects per frame | |
| Transition purpose | every cut | choose from TRANSITION_DESIGN_SYSTEM by what the story does (same place/other time, scale change, new place…) | storyboard column "why" filled | hiding a weak cut |

## Storyboard (mandatory per scene)
Narration passage + word timestamps · verified source assets (id, class, date, credit) · visual objective
(one sentence: what the viewer should understand) · camera class A/B/C + start/end view + easing · overlays
(class each) · geographic anchors (pixel or lon/lat + how validated) · transition in/out (named) ·
duration · narration sync points (word → action, "provider timing" or "estimated") · visual novelty
vs previous two scenes · technical implementation (component names, Built?) · factual limitations.
