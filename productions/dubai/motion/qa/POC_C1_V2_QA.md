# EP002 Dubai — Motion POC v2 (scene C1) QA

Base: 5597c38. Code: `productions/dubai/motion/poc_c1_v2.py` + `engine/motionlib.py`. Local output (not committed): `productions/dubai/visuals/_local_assets/previews/EP002_motion_poc_C1_v2.mp4`. Silent, no TTS, no paid API; narration and SCRIPT_LOCK untouched. Source pixels: the same palm2.jpg (ASTER 18 Sep 2006); displayed rotated 90 degrees clockwise, stated on screen.

## File
H.264 High, yuv420p, 1920x1080, 30 fps, 600 frames, 20.000 s, 19,378,965 bytes, SHA-256 prefix `a2277a3173db5f12`. Full decode clean. Render about 2 min on 4 workers.

## Changes requested and what was done
1. Opening: Palm Jumeirah close-up (about 2.2x of the source), then a continuous pull-out through intermediate framings to a full-frame coastline (2.2-4.5 s) before any text.
2. Empty right panel removed: no framed panel anywhere. The portrait source is rotated for display so the coast fills a 16:9 frame edge to edge (south at left, north at right as listed by NASA).
3. Continuity: one spline camera through all key positions; the dive to Jebel Ali and each flight is a single move with eased start and stop, plus short motion blur on fast legs; no repeated stop-and-start.
4. The World: no glow; thin outlines only for the large landforms (2 px, 0.9 alpha) plus three corner-bracket markers round the main groups.
5. Palm Deira: outline dropped; a crosshair point marker at the white reclaimed land (source pixel 2300, 430), position checked by eye on a 1:1 overlay, and the chip says "point marker, not an outline".
6. Text: titles and chips sit on translucent plates; collision registry sampled every 0.1 s: no overlaps and no safe-margin breaches in the final file's timeline. Tag moved to the top right, direction chip raised off the source line.
7. Pacing: names cued at 5.4, 6.6, 7.4 and 8.7 s (word index estimate), statuses at 12.0, 14.8 and 17.6 s, close at 19.0-19.8 s.
8. Attribution: source chip on every frame, credit line in the last second, "colours as published", "view rotated 90 degrees for display". Status chips use only the 2006 NASA wording.

## Accuracy
- No map data, no registration claim, no scale. Anchors: length-weighted centroids of traced outlines (Jebel Ali, Jumeirah, The World); Deira is the checked point above. The closing path is captioned "not a distance".
- Outline checks unchanged from v1 (vertex pass 0.855 / 0.862 / 0.819 for Jebel Ali, Jumeirah, The World).
- Rotation is a display change only; north is not claimed, only NASA's listed south-to-north order.
- Palm Deira's identity as the marked land rests on NASA's caption order and the earlier screenshot review.

## Visual QA
16 sampled frames and three full-size frames checked: no black borders (the earlier overscan feather band was removed by fitting the wide shot to the image width), no cut-off text, labels readable on bright and dark ground, no ghosting in the blur frames after raising the sample count. Known limits: the closing path line passes under the 02 and 03 plates; Deira's marker sits close to the lower edge in the wide shot (about 75 px); Jebel Ali's ring touches the top edge in the wide shot; timing is word-index estimated.

## Delivered file
Resolution verified with ffprobe on the exact file handed to the interface (see the task report); the user-side copy cannot be inspected from this session.
