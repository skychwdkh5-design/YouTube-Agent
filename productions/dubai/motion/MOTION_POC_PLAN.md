# EP002 Dubai — Motion Proof of Concept: "Four projects, south to north" (scene C1)

Status: PLAN ONLY. Nothing has been rendered. Needs approval before any build. Length 20 s, 1920x1080, 30 fps, video only. Uses the locked C1 narration purely as a timing guide (cue times = word index / 2.42 words per second; 46 words = 19.0 s, plus a 1 s hold). Real timings replace these when yt-voice word timings exist.

Locked C1 narration (not changed): "That 2006 image shows four projects in a row, from south to north: Palm Jebel Ali, Palm Jumeirah, The World, and Palm Deira. Jebel Ali and Jumeirah already look largely complete as landforms. The World is still under construction. Palm Deira is in its earliest stages."

Image: ASTER (Terra), 18 Sep 2006, `visuals/palm2.jpg` (3072x3797). Claims 12, 26. Class: EVIDENCE plus TRACED. No map layer, no new download.

## Storyboard
| t (s) | cue | camera (source px) | layers and motion | text |
|---|---|---|---|---|
| 0.0-1.2 | title in | full height of the frame, portrait image centred left, dark right panel | image fades in, 1 px frame, vignette 10 % | chip: "NASA ASTER (Terra), 18 Sep 2006 · colours as published" |
| 1.7-4.0 | "four projects ... south to north" | full frame | the coastline contour traced from the image draws on from south to north, cyan, soft glow, 2.3 s; a small "S to N, order as listed by NASA" arrow along the left edge | chip: "outline traced from this image" |
| 5.4 | "Palm Jebel Ali" | full frame | pin 1 (anchor ring at Jebel Ali, about x 552, y 3140) pops, leader to label | "Palm Jebel Ali" |
| 6.6 | "Palm Jumeirah" | full frame | pin 2 (about x 1395, y 2175) | "Palm Jumeirah" |
| 7.4 | "The World" | full frame | pin 3 (about x 1517, y 1360) | "The World" |
| 8.7 | "Palm Deira" | full frame | pin 4 (Deira construction area, about x 2275, y 525; label rests on NASA's order and the user's screenshot review) | "Palm Deira" |
| 9.5-12.8 | "Jebel Ali and Jumeirah already look largely complete" | fly (60,2780,1280,720) then (915,1905,960,540), 3.3 s | traced palm and ring outlines draw on (0.9 s each); pins fade to small anchors | NASA-quote chip: "largely complete as a landform, 2006" |
| 13.6-15.6 | "The World is still under construction" | fly to (878,1000,1280,720), 1.6 s | traced footprint of the island cluster draws on | chip: "under construction, 2006" |
| 16.1-18.6 | "Palm Deira ... earliest stages" | fly to (1700,150,1280,720), 1.8 s | traced outline of the white reclaimed land draws on | chip: "earliest stages, 2006" |
| 18.6-20.0 | end | pull back to full frame | a thin glowing path joins the four anchors south to north, captioned "order as listed by NASA, not a distance"; credit line | "NASA Earth Observatory · ASTER on Terra" |
Simultaneous animated elements never exceed three. Every chip text is a short paraphrase of claim 26 or claim 12; claim IDs travel in the cue sheet, not on screen.

## What it proves
Smooth rect-based camera travel; draw-on of outlines traced from the exact pixels; anchored labels and pins; NASA-quote chips; timing bound to narration cues; honest chips that separate evidence from tracing.

## Implementation plan
1. P0 (approval): approve system, POC and the tooling decision below.
2. P1 contour tool: land/sea mask by threshold plus flood fill from the sea edge, boundary extraction, simplification, polyline ordering; numpy only (no scipy or OpenCV installed). Output JSON polylines in original pixel coordinates; I check overlays by eye on sample frames.
3. P2 motion engine: Python and Pillow, 2x supersampled vector layer, glow via blur-and-add, text chips, easing, rect-interpolated camera, frames piped into ffmpeg; same pattern as the diagnostic preview.
4. P3 POC render and QA (ffprobe, decode pass, 10 sampled frames, contour overlay review, text overflow check), send the file to the user.
5. P4 after approval: roll the engine out to P1 scenes, then P2/P3 scenes, then drop motion clips into yt-render as `video` assets over the narration.
Decision for approval: write the contour code in numpy (zero new dependencies, slower to build) or install opencv-python-headless (BSD) and scipy (faster, more robust). I recommend OpenCV if the sandbox allows installs; the choice affects only tooling, not the look.

## Estimated render cost (estimates)
Measured baseline: the diagnostic preview, 1980 frames of simple crops and text, took 136 s wall on 4 cores (about 69 ms per frame). Motion frames add supersampled vectors and glow: expect 150-400 ms per frame. POC: 600 frames, about 1.5-4 min. Full episode (about 538 s, 16,140 frames): about 40-110 min single process, roughly 15-35 min with four parallel scene workers, plus ffmpeg encode. No paid services; disk well under 1 GB; the build itself is a few hours of work, mostly the contour tool and QA.

## Blockers and risks
1. No georeferencing exists for the ASTER or ISS files (claim 32). So no map or country outline may be drawn on them; only outlines traced from their own pixels. A true geographic overlay needs ground control points with sourced coordinates and a reported RMS error; not planned for the POC.
2. A1's map flight needs open vector data (Natural Earth public domain or OpenStreetMap with attribution), which is not downloaded and needs your approval.
3. Cue timing uses an estimate until yt-voice word timings exist; yt-voice is a paid, confirm-gated call and was not used.
4. yt-render has no overlay or SFX support; the workaround is full-frame `video` assets, which is supported.
5. Contour quality on dark urban areas and port shapes is untested; may need manual cleanup.
6. Palm Deira label depends on NASA's caption order and the user's screenshot identification.
7. Reference video not viewed; style is built from the written brief only.
8. Fonts: DejaVu Sans is available; an OFL font needs a download approval.
