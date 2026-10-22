# OrbitalAtlas thumbnail style guide (standard for every long-form episode)

Status: permanent. A cover that visibly departs from this guide is **FAIL** and is revised before approval.
Reference covers (approved): **EP002 Dubai**, **EP003 Great Salt Lake**, **EP004 Jakarta**.
Counter-example: the first EP005 cover (beige, low contrast, tiny subject) - it is what we do NOT make.

## 1. What the approved covers share

| | EP002 Dubai | EP003 Great Salt Lake | EP004 Jakarta |
|---|---|---|---|
| Layout | split screen, amber divider | diagonal split, white divider | one frame, headline stacked left |
| Hook | **3 YEARS** | **20 FEET LOWER** | **JAKARTA IS SINKING** |
| Years / sub | NOV 2000 (white) / NOV 2003 (amber) | 1986 (white) / 2022 (amber) | WHAT RADAR CAN'T SEE (dark strip) |
| Image | dark blue sea, false-colour red vegetation, white island | dark teal lake vs pale lake bed | dark blue sea, grey port city |
| Extra | - | amber outline of the lost area | - |
| Credit | small bottom strip | small bottom-right | small bottom strip |

The DNA: real satellite imagery, **dark and saturated** backdrop so white text pops, a heavy sans-serif headline in capitals with a thick black
outline, **one amber accent** (#FFC245), one focal object, a tiny credit line. Measured: luma contrast (std) 56-68, mean saturation 0.17-0.44.

## 2. Specification

- 1280x720 PNG/JPG, under 2 MB. Safe margin 48 px. Must read at 168x94 px (phone feed) in one glance.
- Headline: **3-7 words, uppercase**, heavy/black sans-serif (Inter Black / DejaVu Sans Bold or heavier), 90-170 px cap height, black outline 6-8 px plus soft shadow.
- Colours: white #FFFFFF = main words; amber #FFC245 = the one key accent (a number, a year, the key word); red #E5322D only for a real warning accent, at most one element; dark sub-strip #050A10 at ~85% for a secondary line; never grey text.
- One focus: one object or one change (island, lake edge, port, the dark segment). One message, readable without the title.
- Allowed helpers: before/after split with year labels, amber outline of the changed area, one arrow, one scale/number marker, one dark strip subline.
- Imagery: real satellite/aerial data only, graded darker and more saturated (never inventing detail); credit line stays small but present.
- Must not: grey or beige washed-out frames, low contrast, long phrases, small text, clutter (more than one focus), news-banner look, infographic look, film-poster look, clean minimalism, stock "shocked face", any claim the video does not support.

## 3. Archetypes (pick one, stay inside it)

- **A. Split change** - before | after, years top, 2-4 word headline bottom, amber outline of what changed. (EP002, EP003)
- **B. Hero frame** - one dramatic frame, 2-line headline (white line + amber line) on the left, optional dark subline strip. (EP004)
- **C. Zoom call-out** - dramatic frame with one amber ring/arrow on the single thing to look at, 3-5 word headline. (EP003 outline logic)

## 4. Per-cover checklist (every item must be YES)

1. Same family as EP002-EP004 (side by side they look like one channel)?
2. States the hook at once, without the title?
3. One focus?
4. Legible at 168x94 px?
5. Dark, saturated, high contrast (no grey/beige)?
6. 3-7 words, uppercase, white + one amber accent?
7. True to the video and its evidence (no implied "built/finished" that the video does not claim)?

## 5. Gate (pipeline rule)

Before any long-form cover is approved or uploaded Claude must:
1. Run `python3 .claude/skills/yt-package/thumbcheck.py cover.jpg` (size, contrast, saturation, white headline, amber accent). It is necessary, not sufficient.
2. Look at the cover next to the EP002/EP003/EP004 covers and the phone-size crop, answer the checklist in section 4, and write the verdict in the episode's review file.
3. Anything that fails either step is **FAIL**: revise, do not argue it through.
4. In `publish/queue.json` a long episode carries `thumbnail_review: {"result": "PASS", "sha256": <sha256 of the thumbnail file>}`. `queue-run` refuses the upload when it is missing, not PASS, or the file changed after review. Only the owner approves; Claude's PASS is a precondition, not approval.
