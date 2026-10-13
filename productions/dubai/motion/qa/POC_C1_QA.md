# EP002 Dubai — Motion POC (scene C1) QA

Base: 34585f0 (approved plan). Code: `productions/dubai/motion/poc_c1.py` + `engine/`. Local output (not committed): `productions/dubai/visuals/_local_assets/previews/EP002_motion_poc_C1.mp4`. Silent, no TTS, no paid API; narration and SCRIPT_LOCK untouched.

## File
H.264 High, yuv420p, 1920x1080, 30 fps, 600 frames, 20.000 s, 16,710,166 bytes (about 15.9 MiB), SHA-256 prefix `af055b095ad0c0a7`. Full decode (`ffmpeg -f null`) clean. Rendered with 4 workers in about 88 s (about 0.45 CPU-s per frame).

## Accuracy
- Source: ASTER (Terra) 18 Sep 2006, palm2.jpg only. No map data, no new imagery.
- Outlines are traced from that file's own pixels (trace threshold 70, half-resolution). Checked in two ways: by eye on 1:1 overlays of the four project crops (contours follow the land edge; a first pass at threshold 27 followed shallow water and was rejected), and by sampling both sides of every vertex. Vertex pass rate: Palm Jebel Ali 0.855, Palm Jumeirah 0.862, The World 0.819, Palm Deira 0.739; length kept after filtering 0.98 / 0.94 / 0.90 / 0.93. All four above the 0.7 and 0.85 gates, so no fallback marker was needed. Palm Deira is the weakest.
- Cloud corner (top left) excluded from the coast sweep. Where the traced coast meets dark port basins it assumes they are water; the legend says "dark water vs bright ground".
- Anchors are length-weighted centroids of each project's traced outline (Jebel Ali 555, 3140; Jumeirah 1399, 2199; The World 1482, 1385; Deira 2382, 527 in source px). They sit on the four project footprints in the final frame.
- No registration is claimed: nothing is drawn on the image that is not traced from it or anchored in its pixel space; the closing path is captioned "not a distance". No scale bar, coordinates or map.
- Status chips quote the 2006 NASA wording only: "largely complete as landforms", "under construction", "earliest stages". Credits use the NASA page credit.
- Deira label depends on NASA's caption order and the user's screenshot review.

## Visual QA (16 sampled frames, two full-size frames)
Camera moves are smooth with no jump at stop arrivals; titles and chips legible over bright and dark ground (shadow or plate); no black no-data borders in full-bleed frames; no text overflow; end composition holds 1 s with all four labels, path and credit; the early subtitle was cut off at the end in the first render and was fixed.
Known limits: glow on the many small World islands makes them read as cyan blobs; JA title overlaps the ring's lower edge at 10 s; the first 8 s leave the right panel mostly empty; timing is estimated from word index, not from audio.

## Comparison with the previous diagnostic preview
Diagnostic: captioned static crops, rectangle moves, one callout, a tile grid. POC: framed-to-full-bleed camera morph, traced outlines drawn on, anchored pins and leaders, NASA-status chips, kinetic type, depth background and a closing path. Same source pixels, same attribution; new information on screen comes only from the image and the 2006 NASA statements.

## Reuse
See `engine/README.md`.
