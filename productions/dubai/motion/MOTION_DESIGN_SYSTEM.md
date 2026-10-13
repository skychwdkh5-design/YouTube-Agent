# OrbitalAtlas — Motion Design System v0.1 (proposal)

Status: PROPOSAL for approval. Written from the user's style brief only. The reference video was not viewed and nothing here is copied from it. Lives in `productions/dubai/motion/` for now; promote to a shared path once approved.

## 1. Principles
1. Every motion carries information (a place, a date, a status, a source). No motion for decoration.
2. Evidence first: NASA imagery is never colour-graded, tinted or composited with something that implies a measurement we do not have.
3. Premium means restraint: one hero movement per beat, at most three animated elements at once, long clean holds before the next reveal.
4. Honest labels: every layer states what it is (evidence, traced, map, illustration, text).

## 2. Evidence classes (the visual grammar)
| class | what it is | look | chip text | allowed over NASA imagery? |
|---|---|---|---|---|
| EVIDENCE | an unmodified NASA image or crop | thin 1 px light frame, source chip | "NASA ASTER (Terra), 2006 · colours as published" / "NASA ISS astronaut photograph, 2022" | n/a |
| TRACED | a contour computed from the pixels of that same image (coast, ring, island footprint) | thin cyan line, soft glow, draws on | "outline traced from this image" (once per scene) | YES: it is registered to that image by construction |
| MAP | stylised vector map from open data (Natural Earth / OSM) | dark flat map, dashed frame | "stylised map, not satellite imagery" | NO, unless georegistered with a documented residual error |
| ILLUSTRATION | schematic of a mechanism (dredging, vibroflot) | flat shapes, no photo textures | "illustration" | no |
| TEXT / TIMELINE | year tickers, plan ledgers, method cards | typographic | none | labels only |
A TRACED line is accurate to the pixels it came from, not a survey boundary and not a geographic claim. A MAP line is never drawn on a NASA image. A true geographic overlay needs ground control points and a reported RMS error (see Blockers).

## 3. Tokens (1080p)
Ink `#0B0F14` · text `#EAF0F6` · annotation amber `#FFC247` · traced cyan `#5CE1E6` · muted grey `#8A94A3` · caption bar black 55 %. Glow: Gaussian blur 6-10 px at 35 % strength, never full neon. Vignette: edges only, 12 % max, never over the data area. Safe margins 96 px. Type: DejaVu Sans now (installed); Inter or IBM Plex Sans (OFL) later if approved. Sizes: title 54, label 32, caption 20-26; at most two weights; micro-labels uppercase with +4 % tracking.

## 4. Motion language
- Easing: smoothstep for camera, ease-out-cubic for labels, linear for strokes that trace.
- Timing: camera moves 3-6 s; stroke draw-on 0.6-1.2 s; leader line 0.4 s; label in 0.3 s; stagger 120 ms; minimum hold 1.2 s after the last reveal.
- Camera = a crop rectangle moving through source pixels at constant 16:9; zoom at most 2.4x on ASTER (soft beyond that), a labelled 4x only for B1.
- Cuts across instruments (ASTER to ISS) are hard cuts with a label change; same-instrument stills may dissolve. No wipes or overlays between different dates or instruments (claim 32).
- Parallax: none on satellite imagery (no depth data). UI layers may drift up to 8 px against the image for depth. 2.5D tilt of the imagery is not used.

## 5. Components
Source chip · evidence badge · callout (anchor dot, leader, label, optional NASA-quote chip) · traced outline draw-on · focus reticle brackets · image-space path (glowing line between callout anchors, captioned "order as listed by NASA", never a distance) · year ticker · timeline scrub bar (dates from NASA captions only) · typographic counter (for example "about 300 planned") · split compare of two separate stills · lower-third · credit card.

## 6. Hard rules
- Every callout and ticker carries claim IDs in the cue sheet; wording comes from verified claims or locked narration.
- Forbidden: overlaying a world map or continents on The World islands; arrows or glow implying growth direction, speed or distances; building-level status marks; scale bars, coordinates or areas without georeferencing; any "sinking" or "abandoned" imagery; presenting the ISS photo as satellite imagery; colour grading or sharpening NASA pixels beyond resampling.
- Label anchors are defined in the pixel space of the image they sit on; when the camera moves they move with that image.

## 7. Cue sheet (per scene, JSON-like)
`scene`, `duration`, `layers[]` with `class`, `asset`, `crop_from/crop_to` (x,y,w,h in original pixels), `t0`, `t1`, `ease`, and `annotations[]` with `type`, `anchor_px`, `text`, `claims`, `t0`. Cue times come from VO word index at 2.42 words/s until yt-voice word timings exist, then are re-bound to those timings. Narration is never re-timed by graphics.

## 8. QA gates
Frame sampling for text overflow and overlap; contrast check on labels; no-data and cloud scan per crop; every annotation has a claim ID; contour overlay checked by eye on 10 sample frames; ffprobe and full decode; one human review pass before it goes into the timeline.
