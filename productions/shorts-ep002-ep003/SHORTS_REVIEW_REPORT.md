# SHORTS_REVIEW_REPORT — EP002 Dubai Islands / EP003 Great Salt Lake (2026-10-15)

Status: **SHORTS_REVIEW_READY · TECHNICALLY_VALID · VISUALLY_REVIEWED (frames inspected; see "not verified") · USER_APPROVED: NO**.
Format of all four: 1080×1920, 30 fps, exactly 15.000 s (450 frames), H.264 + AAC 48 kHz, original music + approved narration excerpts.
Budget spent: $0 (no TTS, no paid API, no stock). Nothing uploaded to YouTube. `main` and the EP002/EP003 masters are untouched
(`tools/autopilot/protected.py verify`: 23 files, 0 violations).

## Comparison (one line each)

| Short | Story / angle | Hook (0–1 s) | Picture source | Strongest moment | Main risk |
|---|---|---|---|---|---|
| EP002_Dubai_Short_01 "JUST SEA." | **Time:** open sea becomes the Palm in 3 years | `NO ISLAND.` on frame 0, `JUST SEA.` on the word | NASA World of Change ASTER series (Nov 2000 → Feb 2002 → Oct 2002 → Nov 2003), false colour | beat-cuts 2000→2002→2002→2003 and the snap-zoom on “a palm tree, fully formed” | WoC frames are false-colour (labelled); the start is a slow push on empty water — viewers need the type to know what to watch |
| EP002_Dubai_Short_02 "4 PROJECTS. ONE PICTURE." | **Space:** the scale of the build in one frame | `4 PROJECTS.` on frame 0, `ONE PICTURE.` on “2006” | ASTER 18 Sep 2006 on a tilted 2.5-D plane; ISS astronaut photo 6 Apr 2022 | south→north camera, four anchored labels landing on the spoken names | label anchors are hand-placed on the image (checked by eye); the tilt is a flat photo in perspective, not terrain |
| EP003_GreatSaltLake_Short_01 "20 FEET." | **Measured change:** record high → 20+ ft lower | `RECORD HIGH` on frame 0, `1986` badge, `4,211.6 FT` on the number | co-registered Landsat stack (Aug 1986 / July 2022 + 1985, 1999, 2021) | light-wipe 1986→2022 with the 1986 shoreline traced in amber, `20+ FT LOWER.` | strongest data story; least “motion design” — mostly one map |
| EP003_GreatSaltLake_Short_02 "WHAT THE WATER LEFT BEHIND" | **Consequence:** exposed lakebed and dust | title on frame 0, amber lakebed reveal on “lake bed” | Landsat July 2022 + EP003 traced water masks; dust = labelled illustration | `17 SITES` → As / Pb / Cd tiles → tilted map, dust drifting toward Salt Lake City | health topic: kept to the USGS wording and closes with “not yet formally evaluated (USGS)” |

Recommendation for a first upload test: **EP002 Short 01** (clearest before/after, strongest hook) and **EP003 Short 01** (hard number, US
audience). Short 02 of each is the follow-up/series piece.

## How the reference was adapted (not copied)
Taken from the reference: one idea per beat (0.5–1 s), heavy uppercase type, one accent colour, word slams, colour-card punches, extruded
2.5-D words, starburst badge, fast push/zoom transitions, hook repeated at the end. Not taken: its wording (Russian, profanity), red palette,
grid-floor/HUD décor (no data meaning here), whiteout flashes. OrbitalAtlas version: amber = emphasis, cyan = data/source, Inter Black,
real satellite imagery as the stage, every number from a VERIFIED claim. Cuts land on the 128 BPM grid (beat = 0.469 s); impacts and whooshes
sit on the narration words.

## Honesty and labels
- Every frame carries a source chip (instrument · agency · date). False-colour ASTER is labelled “FALSE COLOR: PLANTS APPEAR RED”.
- Dubai Short 01: the NASA World of Change frames share NASA's framing but are **not re-registered**, so changes are shown by cuts and by two
  separate side-by-side panels — never by a wipe that would imply pixel registration.
- Dubai Short 02: ISS frame labelled as an astronaut photograph (ISS067-E-3785, NASA JSC); the tilt is a flat image in perspective.
- GSL Short 01: wipes are honest (same 60 m UTM grid). The amber 1986 shoreline is labelled TRACED.
- GSL Short 02: amber = water in Aug 1986, dry in July 2022, labelled TRACED; dust particles labelled “ILLUSTRATION, NOT A MEASURED PLUME”;
  health effects closed with the USGS caveat. Salt Lake City pin is computed from its coordinates through the same tilt.

## Claims used (all VERIFIED in the episode ledgers)
EP002 (`productions/dubai/research/claims.md`): #4 sand dredged from the seafloor, protected by rock breakwaters; #21 dates; #22 first stage
(Feb 2002); #23 fronds inside a circular breakwater (Oct 2002); #26 four projects south→north in the 18 Sep 2006 image; #27/#28 ISS photo.
Spoken lines are the approved narration (“There is no island here. Just sea.”, “November 2003. The same place. A palm tree, fully formed.”,
“Between these two pictures: three years.”, “That 2006 image shows four projects …”).
EP003 (`productions/ep003-great-salt-lake/story/claims.json`): C1, C2 (4,211.6 ft record high in 1986; > 20 ft lower by July 2022;
4,190.2 ft July 2022), C15 (USGS: dust at 17 sites; arsenic, lead, cadmium; no formal health evaluation), C16 (NASA: dust worsens regional air
pollution), C19 (scene dates).

## QA (see qa/*.json)
| Short | frames / video s / audio s | black | longest near-static | loop seam (MAD) | LUFS / true peak | text QA | yt-qc |
|---|---|---|---|---|---|---|---|
| EP002_Dubai_Short_01 | 450 / 15.0 / 15.0 | 0 | 0.13 s | 0.59 (a cut ≈ 28.83) | -14.8 / -1.4 dBFS | 0 violations, max 8 big words | PASS |
| EP002_Dubai_Short_02 | 450 / 15.0 / 15.0 | 0 | 0.4 s | 0.71 (a cut ≈ 36.79) | -14.9 / -1.5 dBFS | 0 violations, max 7 big words | PASS |
| EP003_GreatSaltLake_Short_01 | 450 / 15.0 / 15.0 | 0 | 0.67 s | 0.67 (a cut ≈ 20.83) | -15.2 / -1.1 dBFS | 0 violations, max 5 big words | PASS |
| EP003_GreatSaltLake_Short_02 | 450 / 15.0 / 15.0 | 0 | 0.2 s | 1.04 (a cut ≈ 14.06) | -14.6 / -1.4 dBFS | 0 violations, max 10 big words | PASS |

SHA-256: `EP002_Dubai_Short_01.mp4` 98f8dda92304f88d0a6bc865c681b5146ff487d407bc05cd178117c8530078e7; `EP002_Dubai_Short_02.mp4` c4bff3eeb4c7e13d0b9e4f8e2ae1147710588a47ac388adc638a8e03639b3328; `EP003_GreatSaltLake_Short_01.mp4` 9bff662fb8edfbcf8af6aa89fa03e9118fa819cbc1a77f067b99cc21604ce2fd; `EP003_GreatSaltLake_Short_02.mp4` 514f3980a6b86ff15fd1bdcdad15e146f46be627daa580caa9a65b5e6b2559da

Text QA (`qa_text.py`, every 0.1 s): all type inside the Shorts safe box x 80–940, y 250–1380 (source chips above it, left of the button
column); no text under 30 px; 0 violations in all four. Every one of the 450 frames of each Short renders without error.
Engine tests: 221 OK (new `orbitalatlas/tests/test_shorts.py`: 18), V2C untouched.

## Not verified / limitations
- Sound was checked by loudness meter and by the cue timetable against the word timings, **not by ear** (no listening in this container).
- Label anchors in Dubai Short 02 (four projects in the 2006 image) are hand-placed on the picture and checked visually, not geocoded.
- Procedural music: one style, not a composed track. Music and SFX are original (CC0); no third-party audio.
- The narration is ElevenLabs output from the approved episodes: before publishing, confirm the plan covers commercial use (knowledge base:
  `youtube-synthetic-disclosure-and-tts-rights`).
- 15 s is shorter than the project’s Shorts profile (35–60 s) by the owner's request; `yt-qc --profile short` length warnings do not apply.
- Quality is my own review against the reference; it is not USER_APPROVED.

## Files
Deliverables (not in this public repository): `EP002_Dubai_Short_01.mp4`, `EP002_Dubai_Short_02.mp4`, `EP003_GreatSaltLake_Short_01.mp4`,
`EP003_GreatSaltLake_Short_02.mp4`, SHA-256 in `SHA256SUMS`. Code: `orbitalatlas/shorts.py`, `orbitalatlas/music.py`,
`productions/shorts-ep002-ep003/shorts_build.py`, `qa_text.py`, `qa_video.py`, `CONCEPTS.md`.
Rebuild: `python3 productions/shorts-ep002-ep003/shorts_build.py render dubai1 OUT.mp4` (sources restored as in CONCEPTS.md).
