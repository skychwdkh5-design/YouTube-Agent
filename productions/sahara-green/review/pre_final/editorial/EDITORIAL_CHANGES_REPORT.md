# EP001 targeted editorial pass: changes report

Baseline `614f0ed`. Scope: the opening (0-30 s) and the desalination proposal (357.167-395.300 s) only. Everything else in the master is untouched.
Unchanged by construction: SCRIPT LOCK v1.1, the Adam narration (the revised sections use the locked WAV, cut at the section boundaries, with the master's own constant gain of -0.8 dB), all word timings (shifted by the section start, not altered), every number and claim, the East Oweinat sequence (scene 6, frame-identical to the approved master, PSNR 41-54 dB), the Landsat stills, tone B.

## Phase 1: opening 0-30 s (`OPENING_REVISED_1080p30.mp4`)
| time | before | after | why |
|---|---|---|---|
| 0.0-2.1 | muted red-brown Tassili plateau | **NASA Blue Marble globe, slow push-in toward the Sahara** | the strongest image of the film now carries the first line; the viewer sees "the Sahara" at once; orbit motif |
| 2.1-8.2 | flat dark card "230+" for 6.2 s | **the same "230+" and its two lines over the Tassili landscape** (real Landsat tone B under a 48 % scrim); the three lines still appear on "Geological records", "more than 230" | no flat card; geographic context from the first number; same text, same source |
| 8.2-13.3 | hazy Bodele centre; label "THOUSANDS OF MILES AWAY" almost unreadable on the pale haze | **Bodele framed on the diatomite blocks (relief), slow push; same haze, nothing removed or corrected**; label legibility from a top scrim (display aid only); a second label "BODELE DEPRESSION, CHAD · ONE OF THE WORLD'S BIGGEST DUST SOURCES" on "the part that's easy to miss" (claim S7) | the haze stays authentic; the image now has structure; the label can be read |
| 13.3-17.3 | globe push with label | unchanged (same shot) | it already worked; with the new globe at 0 s the orbit motif repeats at 13 s |
| 17.3-22.8 | **white card**: one orange banner on an empty page, second line at 21.4 s | **three lines over a real landscape (Landsat Gilf Kebir, tone B, dim)**: "IN SOME AREAS OF THE SAHARA", "A FEW INCHES OF RAIN A YEAR", "= TENS OF MILLIMETERS", and the unit key "1 inch = 25.4 millimeters", each on its narrated phrase | no white flash; no empty page; the content is the narrated sentence (claim S3) plus a true unit conversion; no threshold, no "most of the Sahara" |
| 22.8-30 | East Oweinat 1984 to 2024 | unchanged (same sequence file, same frames) | locked |

Dark/bright jumps: the opening no longer contains a white card; every transition is imagery to imagery or dark to dark. Subtitle overlap check: 9 cues, 47 element pairs, no overlap.
**Editorial note on the Bodele order:** the shot order follows the narration (globe, number, Bodele, globe, rain, East Oweinat); I did not move Bodele away from "thousands of miles away", because that line is about the distance to the dust's destination and Bodele is the dust's source (claims S7, S7b). The NASA dust visual was not pulled forward: it is the payoff of scene 29.

## Phase 2: desalination proposal 357.167-395.300 (`PROPOSAL_REVISED_1080p30.mp4`)
Before: one dark node-and-arrow look for 38 s, 11 build steps (Seawater → Desalination → Pipeline → Irrigation → Forest, then two notes), static gaps of 4.07 s, 4.73 s and 4.33 s.
After: five different compositions, each tied to the narrated phrases:
| time | composition | content (all from the narration and claims G1, G2, G4) |
|---|---|---|
| 357.2-366.4 | **map**: NASA Blue Marble Africa under a scrim | "PROPOSAL (2009)", "GOING MUCH BIGGER" on "going much bigger", dashed "FORESTS OF FAST-GROWING TREES", "THE SAHARA", dashed "AND THE AUSTRALIAN OUTBACK" with "Not on this map" |
| 366.4-369.8 | **mechanism, diagonal staircase** | dashed FOREST ← IRRIGATION ← DESALINATION ← SEAWATER (solid), revealed in the order spoken ("watered with desalinated seawater"); "A conceptual schematic, not a route map: no site or route is shown" |
| 369.8-376.9 | **equivalence bars** | "CARBON TAKEN UP EACH YEAR (ESTIMATE)" (dashed, proposed forests) ≈ "CARBON RELEASED EACH YEAR" (fossil fuels); no number is drawn (none is narrated) |
| 376.9-385.4 | **what it is / what it is not** | "THE ESTIMATE CAME FROM: plantation data; calculations with large error bars" vs "IT WAS NOT: a climate-model result that simulated the carbon" |
| 385.4-395.3 | **schematic curve** | carbon stored vs time, rising then flat at "ABOUT A CENTURY" (dashed plateau), marked SCHEMATIC, not data; ends on "THE AUTHORS THEMSELVES DESCRIBED SUCH PROJECTS AS..." which leads into the next card |
Static gaps now at most 2.6 s (4.07 s and 4.73 s before). The empty-background problem is gone: no moment shows a single element.
**Proposed vs existing:** every proposed element has a dashed outline with a light colour wash; a legend states "DASHED = PROPOSED IN THE 2009 STUDY"; satellite imagery is only used for the place (the Sahara). Nothing existing is drawn as part of the proposal and nothing proposed is drawn as existing.
**Not done, and why (conflict reported, not silently resolved):** (1) a *geographic route* (pipeline path, plant sites) is not supported by any source in `claims.md`; the mechanism graphic says so on screen and shows no route or site. (2) The Australian Outback has no approved imagery in the asset set (the NASA Blue Marble set in SVS 3539 holds no Australia view), so it is named, dashed and marked "Not on this map" rather than placed on a map. (3) The scale facts in G1 (forest area of the paper's full and reduced swaths: 9.8x10^8 and 5.7x10^8 ha) are not shown: converted, they restate a Sahara area figure that the ledger removed (S1/S2), and the narration does not use them. (4) The energy numbers (G1c) are not narrated and are not shown.

## Engineering changes (tested)
- yt-graphics: `backdrop` (real image under a scrim, its credit printed in the source line), dashed `proposed` nodes and arrows (light colour wash), plain `lines`; subtitle and source line in full-contrast colour over a backdrop (16 + 3 tests).
- yt-render: still layer `scrim` (top-down darkening for label legibility, the picture is untouched), credit on a dark pill (earlier), 26 + 1 tests.
- New scripts: `build_revision.py`, `check_subtitle_overlap.py`, `audio_normalization_test.py`.

## Credits and attribution
Graphics: "Original graphic · sources on the image"; every graphic prints its source line; backdrops add "Imagery: ..." (NASA Blue Marble SVS 3539; Landsat 9 · USGS with the place named; Gilf Kebir marked "illustrative" under the rain card because NASA's statement is about "some areas", not about that place).
