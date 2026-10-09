# EP002 proof v3 — audit, storyboard, engine changes

Status: **awaiting human approval**. The 60 s rebuild has NOT been started.

## Audit of the rejected `EP002_av_test_H1_A1.mp4` (55.2 s)
`render_av_test.py` imports the single POC v2 scene (`poc_c1_v2`: rotated palm 2 plus anchors/markers)
and runs it under the whole narration. What the code does: one image, a slow camera over it, source chips,
subtitles. It does not use the engine's strongest capabilities (match cut between two instruments,
fills, kinetic typography tied to words). Visually that is a slideshow with camera drift.
Per-second timestamps of the failure were not logged during the earlier render; this audit is
based on the code and on the user's review of the video, not on a frame-by-frame measurement.

## Root cause
1. Storyboard: the passage was chosen for audio quality, not for what can be shown; one scene covered it.
2. The engine had no land/sea fills, spotlight, anchored/rotated text, year roll, comet trail or match cut.
3. Automated QA (loudness, sync, collisions) passed, but nothing measured visual change per second.

## Proof v3 (narration window 23.35–37.85 s of H1_A1, 14.5 s)
Times are relative to the proof; words from the ElevenLabs word timestamps (no new TTS).
| t (s) | Words | Visual |
|---|---|---|
| 0.0–2.9 | The palm-shaped islands stand out from orbit. | ISS photo 2022, camera pushes in; Palm Jumeirah / Jebel Ali / World outlines traced from the image pixels; "FROM ORBIT" text; year ticker |
| 3.0–5.6 | So how do you build land where there was only sea? | zoom to palm; LAND (amber fill + spotlight) then SEA (cyan) words on the word times |
| 5.6–6.4 | And what happened… | match cut ISS 2022 → ASTER 2006 at equal screen scale, year rolls 2022→2006; palm appears as unbuilt/partial |
| 6.4–8.3 | …to the plans that came next? | camera pulls over Jebel Ali and The World outlines (traced from ASTER) |
| 8.4–13.5 | This is Dubai, in the United Arab Emirates, on the shore of the Persian Gulf. | DUBAI / UNITED ARAB EMIRATES lie parallel to the traced coast; PERSIAN GULF over the sea; coast comet on "on the shore" |
| 13.5–14.5 | A coastline | dive along the coast (transition into the next scene) |

## Engine changes
New `engine/fx.py` (masks, radial-wipe fills, spotlight, anchored/rotated text, year roll, coast comet);
`trace.py` and `validate.py` accept a colour channel (ISS tracing uses red). 

## Limitations and evidence
- ISS (2022) and ASTER (2006) are different instruments and dates and are not registered to each other;
  the match cut is an editorial dissolve at equal screen scale, not a pixel-exact before/after (claim 32 stays unverified).
- Both sources are shown rotated 90° (labelled on screen); ASTER colours as published.
- Outlines are traced from the image's own pixels, not drawn by hand; the ASTER palm outline shows what
  was built by 2006 — it is not a claim about plans.
- Proof was reviewed by eye on frames; that is still a single reviewer's pass, not user approval.
