# EP002 Dubai — Visual Production Plan (28 scenes)

Base: 0760a48. Narration and SCRIPT_LOCK untouched (VO SHA-256 d050d5e3...60d re-verified). Structure timings from story_structure_v1_4.md. No render, TTS or paid call was run.

## Source files (validated)
| key | file | native size | decode | SHA-256 | credit and date |
|---|---|---|---|---|---|
| ASTER-2006 | visuals/palm2.jpg | 3072x3797 | OK | `b97c188deedfbfe132b8fd316a43ac2960987f1b4b9f8da604f07898efe5c3f0` | ASTER on Terra, 18 Sep 2006; NASA page credit NASA/GSFC/MITI/ERSDAC/JAROS and U.S./Japan ASTER Science Team. The upload note said "NASA/JPL"; our NASA notes do not say JPL, so use the page credit until the original page is rechecked |
| ISS-2022 | visuals/iss067e003785_lrg.jpg | 2768x4928 | OK | `49ea68cdf6f62c081cdc7a02f5781b2086669e0e2cdb614a1569271d13bc3e90` | ISS astronaut photograph ISS067-E-3785, 6 Apr 2022, Nikon D4, ISS Crew Earth Observations; cropped and contrast-enhanced by NASA. A photograph, not satellite imagery |
| WOC x12 | visuals/OrbitalAtlas_EP002_Dubai_WOC_12_images.zip (extracted locally, git-excluded) | 3000x3000 each | OK | see FULL_RES_VISUAL_AUDIT.md | ASTER on Terra; NASA Earth Observatory; 2011 = year only |
Provenance: files were uploaded by the user; byte identity to NASA's originals was not verified (no download possible here). Dimensions match NASA's listed sizes.

## Verified by direct view
- ASTER-2006: Palm Jebel Ali (about x 315-790, y 2920-3360), Palm Jumeirah (x 1240-1550, y 2000-2350), The World (x 1285-1750, y 1140-1580) are clearly visible with their ring barriers. White reclaimed land at the top (about x 2045-2510, y 290-760) is consistent with the Deira construction area; that label rests on NASA's caption order and the user's screenshot review. Clouds only in the top-left corner (x<790, y<350). No no-data borders.
- ISS-2022: The World (about x 1215-1805, y 115-855), Palm Jumeirah (x 1725-2185, y 1050-1495), Palm Jebel Ali (x 1314-1938, y 2497-3055) visible; no no-data. Claim 33 is corroborated on this file (supplied copy only).
- Coordinates are original pixels, readings +/-30 px. No geographic registration, scale or alignment is claimed; frames from different dates or instruments are never overlaid.

## Rules across the video
- Labels: instrument or camera and year on every image; "colours as published" on ASTER; "photograph" on ISS. No band combination or "natural colour" statement.
- Transitions: hook uses hard labeled cuts; same-instrument stills may cross-dissolve; ASTER to ISS is a hard cut with label change.
- Crops are 16:9 and move rect-to-rect with the same aspect; scale factor is 1920 divided by rect width.

## Scene plan
| scene | start | s | asset | crop rect(s) (x,y,w,h) | transition | on-screen label | claims | limits |
|---|---|---|---|---|---|---|---|---|
| H1 | 0:00 | 10 | WOC-2000 | R_PALM (140,1445,800,450) | hard cut in | NASA ASTER, 2000 · colours as published | 2, 21 | Wisps at x<130 just outside rect; sea only. |
| H2 | 0:10 | 8 | WOC-2003 | R_PALM (140,1445,800,450) | hard cut (separate still, not footage) | NASA ASTER, 2003 · colours as published | 3, 21 | Palm complete; rect clear of clouds. |
| H3 | 0:18 | 11 | ISS-2022 (iss067e003785_lrg.jpg) | H3a (1155,820,1600,900) down to H3b (826,2326,1600,900); both 16:9, 1.2x | hard cut in; slow downward move between the two palm islands | NASA ISS astronaut photograph, 2022 | 27, 28 | Photograph, not satellite imagery. Two palms are about 1500 px apart vertically, so a move is needed. |
| H4 | 0:29 | 9 | ASTER-2006 (palm2.jpg) | H4 (500,1100,2368,1332), slow drift; title card over it | hard cut; title card fade | NASA ASTER, 2006 · colours as published | 9, 10, 26 | Shows The World and Palm Jumeirah; no Jebel Ali. |
| A1 | 0:38 | 20 | none | n/a | fade/cut | none | 29 | Schematic locator only; no verified basemap. |
| A2 | 0:58 | 23 | WOC-2000 | pan (550,600,2400,1350) to R_PALM, 45 s | cut in; end of push flows into A3 text cards | NASA ASTER, 2000 · colours as published | 13, 2, 21 | Start rect avoids top-left clouds (x<525, y<1125). |
| A3 | 1:21 | 27 | none | n/a (text cards) | dissolve between cards | none | 8, 30, 31 | Typographic only; no invented geometry. |
| B1 | 1:48 | 13 | WOC-2002a | context R_PALM, then 4x target (0,1422,480,270) with callout | cut from A3; push-in from context to target | NASA ASTER, 2002 · colours as published | 22, 1 | Target shows a small light patch with a bright edge, not a palm; 4x upscale is soft. Preview: _local_assets/previews/B1_target_4x_callout_preview.jpg. |
| B2 | 2:01 | 15 | WOC-2002b | R_PALM, callout on the ring | dissolve from B1 context | NASA ASTER, 2002 · colours as published | 23, 6 | Crescent and fronds fit the rect. |
| B3 | 2:16 | 20 | none | n/a (diagram) | cut | illustration | 4 | No volumes. |
| B4 | 2:36 | 17 | none | n/a (schematic) | cut | illustration | 5 | None. |
| B5 | 2:53 | 30 | WOC-2002b then WOC-2003 | R_PALM both | cross-dissolve only (no wipe) | year on each still: 2002, 2003 | 23, 3, 24 | Registration unverified; coast looks similar by eye, nothing claimed. |
| B6 | 3:23 | 15 | WOC-2004, 2005, 2006, 2007, 2008 | R_PALM each | cut or short dissolve, about 5 s per still | year on each | 24, 3 | WOC-2006 is a different file from palm2.jpg; both dated 18 Sep 2006. |
| B7 | 3:38 | 14 | ASTER-2006 (palm2.jpg) | C1b (915,1905,960,540), 2x | cut | NASA ASTER, 2006 · colours as published | 1, 12, 26 | Palm Jumeirah complete with ring; 2x upscale. |
| C1 | 3:52 | 20 | ASTER-2006 (palm2.jpg) | four stops: C1a Jebel Ali (60,2780,1280,720); C1b Jumeirah (915,1905,960,540); C1c The World (878,1000,1280,720); C1d Deira construction area (1700,150,1280,720) | slow moves south to north, about 4-5 s per stop | NASA ASTER, 2006; stop labels Palm Jebel Ali, Palm Jumeirah, The World, Palm Deira | 12, 26 | Deira identified from caption order and the user's screenshot review, not independently confirmed. Top-left clouds (x<790, y<350) avoided. |
| C2 | 4:12 | 20 | none | n/a (layout schematic) | cut | illustration | 7, 8, 1, 6 | Stylised, not traced from imagery. |
| C3 | 4:32 | 18 | ASTER-2006 (palm2.jpg) | C1d Deira then C1c The World | dissolve between the two crops | NASA ASTER, 2006 · colours as published | 10, 26, 12 | Same date and file as C1; different crops. |
| C4 | 4:50 | 23 | ISS-2022 | C4 (710,35,1600,900), slow zoom | cut; fallback text card | NASA ISS astronaut photograph, 2022 | 9 (33 confirmed on this file by direct view) | The World fits with margin; a partial reclaimed shape is cut at the top-right edge. Layout of islands looks like clusters; development state cannot be judged from the picture, narration relies on NASA's caption. |
| C5 | 5:13 | 21 | ASTER-2006 (palm2.jpg) | C5 (704,0,2368,1332), slow push toward Deira | dissolve from C3 | NASA ASTER, 2006 · colours as published | 10, 26 | The World is cut by the bottom edge; acceptable. |
| C6 | 5:34 | 25 | none | n/a (graphic); optional: palm2 C1b and C1c side by side | cut | illustration | 1, 4, 7, 9, 25 | Optional crops reuse C1; keep graphic unless the cut feels empty. |
| D1 | 5:59 | 17 | ASTER-2006 (palm2.jpg) + diagram | C1a Palm Jebel Ali then C1b Palm Jumeirah, ring callouts | dissolve between the two crops | NASA ASTER, 2006 · colours as published | 4, 6 | D1 mismatch resolved: Palm Jebel Ali and its ring are visible in palm2.jpg, so WoC-2002b is no longer used here. |
| D2 | 6:16 | 17 | WOC-2000 and WOC-2011 | (600,1000,1600,900) for both | labeled cut | NASA ASTER, 2000 and 2011 · colours as published | 13, 21, 25 | 2011: year only; avoids the right no-data wedge and the y 845 line. |
| D5 | 6:33 | 30 | none | n/a (method card) | cut | none | 21, 27 (+ editorial) | No overlay or comparison between ASTER and ISS. |
| E1 | 7:03 | 20 | WOC all 12 frames | R_PALM each, 4x3 grid of 480x270 tiles with year labels, sequential reveal | tiles pop in on narration beats | year on each tile (2011 year only) | 21, 22, 23, 24, 25 | Full frames avoided because of black wedges. |
| E2 | 7:23 | 32 | ISS-2022 | E2a (1475,1002,960,540) Jumeirah, E2b (1066,2461,1120,630) Jebel Ali | cut between crops | NASA ISS astronaut photograph, 2022 | 6, 11, 26, 27, 28 | Tight crops; the built-up trunk (Jumeirah) versus mostly bare land (Jebel Ali) is visible, but the narration states it from NASA's caption. |
| E4 | 7:55 | 27 | WOC-2000 then WOC-2003 | R_PALM both | cross-dissolve | years on stills | 1, 3, 4, 7 | Repeats the H1/H2 pair on purpose; new element is the synthesis text. Consider replacing if too echoey. |
| E5 | 8:22 | 27 | WOC-2000, WOC-2003, ISS-2022 | R_PALM, R_PALM, H3a with ring callouts | labeled hard cuts, no dissolve across instruments | NASA ASTER 2000; NASA ASTER 2003; NASA ISS astronaut photograph 2022 | 2, 3, 10, 28 | Deliberate bookend; reuses H3a framing. |
| E6 | 8:49 | 9 | none | n/a (credit card) | fade out | NASA Earth Observatory; ASTER on Terra; astronaut photograph ISS067-E-3785 | none | Credit wording per claims 21, 26, 27. |

Total 538 s (v1.4 estimate).

## Previews generated (local only, not committed)
`visuals/_local_assets/previews/B1_target_4x_callout_preview.jpg` (4x, callout, labelled PREVIEW ONLY) and `B1_context_preview.jpg` (context with the target box). Verified by eye: the patch is a small light rectangle with a bright edge on its north-west side; no palm or fronds. Crop sheet for the new images was viewed and all 13 rects fit inside their images.

## Known limitations
1. ASTER stills are soft at 2x or more; B1 at 4x is very soft.
2. Palm Deira label in C1 and C3 is caption-order based.
3. H3/E5 share a framing; E1/E2/E5 and H1/H2/E4/E5 reuse stills; palm2.jpg appears in H4, B7, C1, C3, C5, D1.
4. WoC frames are not registered to each other or to palm2.jpg; any apparent similarity is by eye.
5. C4 relies on NASA's caption for development state; the picture alone does not show it.
6. The 2011 frame has an unexplained faint line at y about 845; WoC right/left no-data wedges listed in the audit.
7. All rects need a last look in the editor at 1920x1080 before the preview render.
