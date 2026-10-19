# First 15 s - prototype v2 (rendered, silent): `prototype/first15s_proto.mp4`

Rendered with yt-render v3 (profile long) from `prototype/timeline.json`; 1920x1080 30 fps, 7.6 MB, no audio, no narration, no music. `yt-qc --profile long` fails only on what a silent 15 s clip cannot satisfy (duration < 60 s, no loudness, audio start); technical checks pass.

| t | Picture | Draft VO (not generated) | Tier |
|---|---|---|---|
| 0.0-3.5 | Sentinel-2 56 km frame, gold arrow "170 km announced length" running off the frame, 10 km scale bar | "Saudi Arabia announced a city 170 kilometers long. About 105 miles." | T1 |
| 3.5-7.5 | push from 15 km to 8 km on the site, "OCT 2022" | "So we looked at the same ground, every October, from space." | method |
| 7.5-11 | wipe 2022 -> 2026 over 1.7 s (new composition) | "In 2022, a faint line." | T3 |
| 11-15 | push to 2.8 km on the dark segment, "OCT 2026", tag "About 1.5 km" | "By 2026, this. Here's what it is - and what it isn't." | T3 |

Claims on screen: 170 km (published promise), dates, scale bars, "About 1.5 km" (our Sentinel-2 measurement, +-10 m). No building, no "The Line" label on the image.
Known flaws: the hook graphic's arrow label sits on the title band; the first 3.5 s is a graphic, so the first motion is at 3.5 s - consider animating the arrow. Credit text is long ("Contains modified Copernicus Sentinel data 2022 / ... 2026"): shorten per shot when the timeline grows.
