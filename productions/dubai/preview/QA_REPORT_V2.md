# EP002 preview V2 — scene-by-scene visual QA (2026-10-10)
Status: **VISUALLY_REVIEWED, not USER_APPROVED.** Built from `8f217e3`; narration, scene order and durations unchanged (VO hash untouched). Silent preview, 960x540, 24 fps, 538.0 s, captions = locked VO at ESTIMATED timing.
Evidence files: `qa_v2/qa_preview.json` (native-fps technical QA), `qa_v2/qa_scenes.md`, `qa_v2/qa_rects.json` (crop/no-data audit), `qa_v2/audit_labels.{json,md}` (label/date audit), `landmarks.json` (deterministic coordinates), `qa_v2/compare/*.jpg` (before = `8f217e3` build, after = V2).

## Automated results (this build)
| check | result |
|---|---|
| ffprobe vs expectation 960x540@24 | OK: h264 High, yuv420p, 12,912 frames, 538.000 s |
| full decode, black frames (0.15 s) | clean, none |
| native-fps motion QA (`qa_preview.py`) | TECHNICALLY_VALID: 0 freezes, 0 jumps, duplicate ratio 4 % (not regular) |
| crop audit (`qa_rects.py`, every 0.5 s of every scene) | PASS: all rects inside their source; no ASTER no-data pixels in any shown crop |
| label audit (`audit_labels.py`) | PASS: every year on screen comes from the displayed asset or the scene's locked VO (D5 example chips listed in `EXTRA_YEARS`) |

## Scene by scene
Checklist = `docs/REFERENCE_VISUAL_QA_CHECKLIST.md`. "Det." = positions now from `landmarks.json`. All image scenes keep source/instrument/year chips derived from the asset key.
| scene | change in V2 | verification | verdict / remaining weakness |
|---|---|---|---|
| H1 | none (cold-open crop R_PALM kept on purpose); date label moved top-right | labels = ASTER 2000 (11 Nov 2000 file), crop in bounds | A1-A3 ok; very slow push (LOW motion) |
| H2 | same | ASTER 2003 (4 Nov 2003) | same framing as H1 on purpose (pair) |
| H3 | none | ISS photograph, 6 Apr 2022 | ok |
| H4 | none | ASTER 2006 | title card static after reveal |
| A1 | **re-rendered**: Dubai-centred descent (no desert transit), 24 fps, 1.5x supersampled capture, no painted pixels; labels anchored from the Cesium camera projection; soft dissolve into ASTER-2000 | real GIBS tiles only; swath remnants left visible (authentic); label audit n/a for Cesium text | closest frames still ~38 m/px (soft); grey Landsat tile patches over the Gulf at ~8 s; UAE label is in frame only briefly |
| A2 | callouts from data: city/desert points derived from the detected coastline, offshore ring = palm site (median of fitted rings) | crop audit PASS | ok; callouts are labels, not registration |
| A3 | **redesigned**: one continuous ledger + timeline strip, 300-dot schematic counter, blank-page frame | 'ISLANDS IN THE PLAN (SCHEMATIC)'; no geography invented; unsupported '2000' tick removed | still text-led; low motion |
| B1 | patch marker = detected centroid (252, 1534); push spread over the whole scene | crop in bounds; 4x upscale remains soft | ok; callout moved to avoid the date label |
| B2 | medium framing (differs from H1/H2); ring left edge and fronds centroid from fitted circle / pixel centroid | det. | ok |
| B3 | **redesigned** cross-section: dredger, suction pipe with moving sand, rainbowing arc, growing island, rock breakwaters, water motion | labels per NASA method text; no volumes | much cleaner than V1; plain vector style |
| B4 | **redesigned**: plan-view GPS placement grid + vibroflot cross-section with packing grains | labelled ILLUSTRATION, not to scale | ok; weakest remaining graphic |
| B5 | palm-centred framing; dissolve only | no wipe, separate images stated | ok |
| B6 | **five different framings** (crown, trunk, shore, wide) instead of five identical crops | 2008 rect shifted to avoid the left no-data wedge (audit caught 0.8 %) | ok |
| B7 | ring at fitted crown (1395.8, 2191.1, r 154) | det. | ok |
| C1 | rings from fitted circles (Jebel Ali, Jumeirah), The World centroid, Deira bright-component centroid | Deira label stays "NASA caption order" | ok; stop-to-stop moves declared in QA |
| C2 | glyphs draw on over the scene | labelled stylised | still two icons on a dark card |
| C3 | both crops now drift (no frozen dissolve) | text claims unchanged | ok |
| C4 | slow push added | safe default kept (no ISS) | text card |
| C5 | none | ASTER 2006 | ok |
| C6 | glyph draw-on, slow push | labelled illustration | text card |
| D1 | rings from fitted circles | det. | double exposure during the dissolve (intended) |
| D2 | slow drift added on both halves | year-only 2011 label; rect clear of no-data | ok |
| D5 | row-synchronised icons (chip, satellite, camera, not-overlaid frames, year-only chip) | audit exception documented | text card |
| E1 | tiles centred on the palm site per frame (deterministic) | 12 files, 2011 year only | small tiles |
| E2 | rings from ISS fitted circles | photograph label kept | ok |
| E4 | **split screen** 2000 / 2003, both fully visible (no overlay or wipe) | labelled "separate days, not registered" | clear improvement |
| E5 | wider framings for 2000/2003, continuous ISS move | ring from fitted circles | ok |
| E6 | credit card adds the NASA GIBS/CesiumJS line for the globe sequence | locked VO unchanged | credit wording for ASTER 2006 page ("NASA/GSFC/METI/ERSDAC/JAROS") not read at source: UNVERIFIED, not added |

## Missing-data audit (item 6)
- No pixel of any satellite image is painted, filled or interpolated. V1's `clean_swath` and floor-lift in A1 (which coloured no-data swaths deep-sea blue) were **removed**.
- WoC frames: `qa_rects.py` proves no shown rect contains the black swath wedges (found and fixed one: B6/2008).
- Cesium: the Landsat layer is colour-keyed over water so Blue Marble shows beneath (both real NASA imagery, listed in the chip); remaining swath patches are visible as they are.
- UI treatments (labelled where relevant): dim/vignette under text, tone matching of the Cesium render before the dissolve, mild unsharp on the Cesium render, film-style push on graphic scenes. ASTER/ISS pixels are never graded.

## Delivery metadata (item 7)
Exported files (ffprobe): `ep002_preview.mp4` 960x540 24 fps 12,912 frames; the 910x512 30 fps copy seen externally is not a property of our exports. A simulated conversion `scale=-2:512,fps=30` of our file yields exactly 910x512 at 30 fps, matching the report; the earlier V4 file (1280x720, 24 fps) also maps to 910x512 under the same rule. Inference (not verified, the viewer pipeline is not accessible): the chat/preview path re-encodes to 512 px height and 30 fps. Mitigation: the Artifact page serves the unchanged file and recomputes its SHA-256 in the browser.

## QA workflow repair (item 8)
`orbitalatlas.qa` resamples to 30 fps, so a 12 fps render became runs of identical frames and ~34 "discontinuities" (median 0). `qa_preview.py` decodes at the native rate, collapses exact duplicates, and separates intentional duplication (regular run lengths, reported as info), freezes (a held unique frame >1 s, minus declared static windows) and jumps (per-frame change vs the local median of unique frames, minus declared cuts and move windows). Validation: the same tool on a simulated 910x512@30 conversion of the first 120 s reports 0 issues; the old tool on the native clip reports 6 discontinuities.

## Remaining weaknesses
1. Reuse of the same 14 NASA images is inherent; V2 varies framing, not content. Text-card scenes (A3, C2, C4, C6, D5, E6) remain the least cinematic; their motion is a slow push plus staged reveals.
2. Cesium close frames are soft (free GIBS data, ~38 m/px) and show authentic grey Landsat patches over the Gulf.
3. Illustrations are plain vector graphics (identity-consistent but not reference-level).
4. Callout geometry is deterministic per image but the stills are not registered to each other; nothing is claimed beyond "same pixel site".
5. No audio; captions are estimated until provider word timings exist (paid TTS needs explicit approval).
6. 24 fps preview at 960x540 only; no 4K render started.
