# VISUAL_REF_001 — Cinematic Geography (analysis)

Source: `OrbitalAtlas_Reference_01_Maps.mov` (sha256 in `sources.json`), 512x736, 30 fps, 29.63 s. A phone screen recording of a vertical map Short; the app interface (right edge, bottom bar) and a channel watermark are visible and are **not** reference content and not reproduced. Facts = seen in frames (2 fps contact sheets, 12 fps strips at 3.4-4.4 s, 5.8-6.8 s, 13-14 s). `[estimate]` = my reading. No pixel of the video is used in any OrbitalAtlas output.

## What it is
One continuous satellite-style world map. A country name is spoken, the camera jumps to it, the country is flashed, labelled and related to the next country with an arrow and a distance. About one graphic event every 1-2 s, no static hold longer than about 1.5 s. Bottom captions change word by word.

## Timeline (seconds in the file)
| t | observed | effect id |
|---|---|---|
| 0.0-1.5 | close view of a West African country filled red; zoom OUT to the whole world, red fill now on many countries (same colour = same name) | VR1-01, VR1-02 |
| 2.0-3.5 | camera back in; name label in a white box with leader line blurs in; country gets a flag texture with waving cloth and a yellow glowing outline | VR1-04, VR1-03 |
| 3.4-4.0 | fast zoom/pull with strong streak blur to the neighbouring country (10-12 frames at 12 fps) | VR1-01 |
| 4.0-5.5 | two small curved white arrows with red tails point at the next place | VR1-05 |
| 5.0-5.8 | second country: boxed label, flag texture, glow | VR1-04, VR1-03 |
| 5.9-6.6 | the numeral "2600 km" appears huge, rotated about the vertical axis with perspective and blur, flies past, becomes a small label on a thick white curved arrow with a violet head | VR1-06, VR1-05 |
| 8.5-11.0 | camera follows the arrow; a tiny outlined island group appears with a boxed label and flag | VR1-04 |
| 11.5-13.5 | "14000 km" arrow along a new route; scale jump to the Pacific; label box blurs in | VR1-05, VR1-01 |
| 14.2-15.0 | red pin drops on the location | VR1-08 |
| 15.3-15.8 | five curved lines radiate from the point | VR1-07 |
| 16.0-19.0 | the island is flat-filled red, then a violet comet line crosses the world back | VR1-02, VR1-09 |
| 19.8-23.5 | the ocean region is recoloured bright cyan; "Atlantic Ocean" scales in; "Gulf of Guinea" boxed label | VR1-10 |
| 24.0-26.0 | jump to another continent, whole continent red, then a single country magenta | VR1-01, VR1-02 |
| 27.0-29.6 | flag-textured country, then the neighbour appears red then white-flag textured | VR1-03 |

## Camera (what can be said)
Snap/whip moves of 0.3-0.5 s with exponential-in-out easing, motion blur at the peak, hold 0.5-1.2 s on arrival; scale changes of roughly 4-10x between world and country (estimated); at the scale changes the camera pulls back slightly before diving (VR1-01). No slow cinematic pans were visible; movement is event-driven. Tilt of the map plane could not be established at this resolution (uncertain).

## Colour
Strongly graded satellite basemap: deep blue oceans, ochre/orange deserts, dark green forest; fills in saturated red, magenta, cyan with glowing outlines. This is a **presentation** basemap. OrbitalAtlas separates the two classes (see `UNIFIED_STYLE_GUIDE.md`): measured imagery keeps `evidence_safe` at most; presentation layers may use `documentary_map`/`deep_ocean`.

## Typography
Bottom captions, 2-4 words visible, white italic bold with black outline, the spoken word in green (VR1-11); name labels in white-bordered boxes (VR1-04); big numerals with perspective (VR1-06).

## Not reproduced / uncertain
Flag cloth and flag textures (artwork and a cloth shader are missing; VR1-03 PARTIAL), the boxed-label blur-in as one preset (VR1-04), the radial line burst as a preset (VR1-07). Audio was not analysed. Resolution (about 420 px of picture) hides line widths and fonts: all sizes are estimates.
