# Reference 01 analysis — "Top 5 geography facts" countdown Short

Status: **analysed from frames** (file inspected locally, not committed). Facts = seen in frames. Inference = my reading of how it was probably made; marked `[inferred]`.

## Source and limits
| item | value |
|---|---|
| URL given by the user | https://youtube.com/shorts/ZdC2vjJnyhM (not downloaded by me; the user supplied a screen recording) |
| file | `reference_01_compact.mov` (user upload; not committed) |
| container | H.264, 384×552, 24 fps, 43.75 s, **no audio stream** |
| what it really is | a phone screen recording of the YouTube app: video window ≈ 292×519 px at x 46…337, app icons on the right, channel bar at the bottom |
| not reference content | 0.00–2.29 s (another app, then the YouTube app loading) and 41.92–43.75 s (swipe-up hint / loop). Not analysed and not reproduced. |
| consequences | tiny effective resolution (~292 px wide): typography details, thin lines and texture grain cannot be judged. No audio, so music, SFX and narration timing against picture are **unknown**. Camera numbers below come from phase correlation (translation only, zoom not separated) plus viewing frames. |
Observed channel text on screen: a title line "Top 5 Wild Geography Facts" and a handle. Branding is not reproduced anywhere in OrbitalAtlas.

## Overview (facts)
- Format: countdown 5→1 over one continuous virtual camera on a photoreal-looking world map, with ~11 hard-cut-free "set pieces". Only two true cuts in the content: into the content (2.29 s) and a flash-white cut to an aerial photograph (24.58 s).
- Beat rate: a new graphic element (shape, label, badge change, camera move) roughly every 1.5–3 s; the longest near-static camera hold is ≈3 s (17–19 s, camera still while a label and glow animate).
- Subtitles: bottom centre, 2–4 words per card, white, thin shadow, change about every 0.7–1.2 s (a few cards keep the previous phrase dimmed while the next fades in).
- Countdown badge: gold translucent disc with a large digit; large at the start of a number, shrinks into the top-left corner; digit changes with a vertical roll.

## Timecoded analysis
| t (s) | observed (fact) | camera (fact; numbers = translation estimate) | graphics | transition / mechanism | reusable effect |
|---|---|---|---|---|---|
| 2.29 | hard cut into a tilted world map with a blue blueprint-grid border, Greenland/Eurasia in view; caption "Here are" | still; map plane appears tilted (grid border visible at top and bottom) | blue glass disc with digit that rolls 5→4→3→2 (≈2.5–3.4 s) | hard cut | VE-04 rolling badge |
| 3.3–5.3 | digit disc grows to centre; exploding-head emoji + big "1"; caption "top five shocking facts", then "you never knew." with a kinetic title "You Never Knew!" | slow zoom on the map | emoji, title with horizontal blur-in | — | VE-12 headline |
| 5.3–6.7 | countdown settles on "5"; map pans west→east from the Americas over Africa to Asia; the disc moves from centre to top-left | pan ≈ 1.6 W/s at peak (6–7 s), roll/tilt changes visible in the first frames (horizon line diagonal at 5.3 s), then level | "United States" polygon outline appears with blue glow, labelled in the shape; at 6.5 s a red glowing Australia silhouette appears | continuous camera (a pan with eased start and stop) | VE-01 map camera, VE-02 region highlight |
| 7–9 | Australia red shape big, labelled; then camera pulls out to the whole world with Australia small ("on opposite sides of the world") | zoom out | label on shape | zoom out | VE-01 |
| 9.0–14.0 | Australia silhouette moved over the United States to compare sizes; white arrow marker shows the shift; US blue outline stays | slow push in, pan ≈ 0.3 W/s | translate of a shape to another place; arrow | shape translation | VE-05 shape compare |
| 14.26–15.0 | **camera pan east** from the Americas to Eurasia in ≈0.7 s with ease-in/out; badge digit rolls 5→4 (14.38–14.50) and moves from corner to centre | pan ≈ 1.2 W in 1 s, ease in/out | rolling digit, badge move | motivated pan, no cut | VE-01, VE-04 |
| 15–19 | Xinjiang: white crosshair lines sweep out from a point, label "Xin Jiang" with overline plate, soft red heat blob under the point; badge shrinks to corner | slow zoom-in then hold ≈ 3 s | crosshair lines, label plate, radial glow | line draw-on | VE-06 crosshair callout, VE-07 glow blob |
| 19–22 | pulse ring around the point ("right in the middle"); then the badge "4" enlarges again for "in Europe." | still → pan | ring pulse | — | VE-08 pulse ring |
| 22–24.5 | badge "3"; zoom into Finland; label "Neitokainen" with leader and glowing outline of Finland | zoom-in ≈ 0.4 H over 3 s | outline draws on in blue with glow | line-trace reveal | VE-02, VE-06 |
| 24.45–24.80 | **flash**: image over-exposes to white with warm tint, then reveals an aerial photograph of the lake | static | — | flash-white cut (white frame at ≈24.60 s) to a different footage type | VE-10 flash cut |
| 24.8–26.7 | aerial photo of the lake with autumn colours; small, nearly still motion | near-static | caption only | photo insert | class A scene |
| 26.7–29.0 | back to the map: Finland outline glowing, lake pin and label; camera pulls out | zoom-out ≈ 0.55 H in 2 s | same overlays | match to the earlier map framing | VE-01 |
| 29.0–34.0 | badge "2"; South America shape (green glow fill) lifts off and moves/rotates onto Africa's coast, white arrow; shapes "fit" | pan/zoom to Africa, dx ≈ 0.1 W/s | shape translation + rotation with glow | shape compare | VE-05 |
| 34.0–34.5 | badge digit rolls 2→1 over Africa | — | rolling digit | — | VE-04 |
| 34.6–36.2 | camera zooms from Africa to the Middle East; a red dot grows at Egypt and becomes a map pin that drops with a bounce | zoom-in ≈ 0.5 H/s | red dot → pin drop + ring | — | VE-09 pin drop |
| 36–39 | yellow translucent area fill spreads (Egypt/Nile); zoom into the Nile; cyan river lines draw on with glow | zoom-in, ≈ 0.45 W/s pans | area fill, river lines | line-trace reveal | VE-02, VE-13 river lines |
| 39–41.9 | hand-drawn-looking yellow ellipse and label "Nile Delta" (bold yellow, slight tilt) around the delta; camera holds | hold | ellipse draws on, label pops with overshoot | — | VE-14 hand-drawn highlight |
| 41.92 | end of content (loop) | — | — | — | — |

## Camera behaviour (observed)
- One continuous virtual camera: pans of 0.7–1.5 s between places, zooms of 2–3 s into the subject, short holds (≤3 s) while overlays animate. All moves are eased at both ends. Roll/tilt appears at the very start only.
- Subjects are geographic shapes (countries, lakes, rivers) that sit on the map and stay registered when the camera moves.
- Basemap: photoreal Earth texture (looks like blue-marble-style imagery) `[inferred]` mapped on a flat plane `[inferred]`.

## Inference about the production method `[inferred]`
Compositing-style pipeline: a world texture on a plane moved by a 2D/3D camera, vector country shapes as masks with glow, icons and text as layers, a flash dip as a transition, subtitles as burned-in text. Nothing in the frames shows what software was used.

## What is NOT known
Audio/music/SFX; the original resolution; the exact easing curves; whether the map is 3D; fonts (low resolution).
