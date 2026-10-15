# EP004 critical proof - PLAN (not built; stop for owner approval rules apply)

**Target:** S3 "Radar reveals ground motion" (hardest: needs illustration primitives that do not exist, a truthful illustration -> measurement hand-off, and phone legibility). 13.5 s, 1920x1080, 30 fps = 405 frames, silent + CC0 synthesised SFX (`orbitalatlas.sfx`), no TTS, no paid service.

## Shot list (13.5 s)
| t (s) | content | class | engine |
|---|---|---|---|
| 0.0-1.0 | dark plane (PlaneTilt), stamp "ILLUSTRATION - NOT TO SCALE" | ILLUSTRATION | built |
| 1.0-3.0 | satellite glyph glides in; radar wavefronts expand to ground | ILLUSTRATION | **new** `illustrate.RadarBeam` |
| 3.0-5.0 | pass 1: cyan return wave drawn on a ruler of phase | ILLUSTRATION | new `illustrate.PhaseWave` |
| 5.0-7.0 | ground block lowers (exaggerated, label "EXAGGERATED") | ILLUSTRATION | new tween |
| 7.0-9.5 | pass 2: amber wave; visible phase shift; counter "phase shift -> millimetres" | ILLUSTRATION | new |
| 9.5-11.5 | LOS arrow vs vertical arrow; caption "measures along the line of sight" | ILLUSTRATION | new `illustrate.LosArrow` |
| 11.5-12.0 | flash_dip | transition | built |
| 12.0-13.5 | ESA 2024 map (P1) with legend and stamp "MEASURED - SENTINEL-1 - 2017-2018 - LINE OF SIGHT", credit chip | EVIDENCE | built |

## Acceptance (reported honestly after the build)
works / approximated / deficiencies / phone readability (mobile_qa + textrec) / scientific correctness (a second pass against C26 and the LOS definition) /
render cost / needed changes; direct comparison to `UNIFIED_STYLE_GUIDE.md` and `REFERENCE_COMPARISON.md`; frames inspected by eye (>= 12 listed).
New code only in a reusable module with isolated tests; run existing orbitalatlas (143) and autopilot (136) tests unchanged; render time recorded.

## Gate
PROOF_READY report -> **owner decides**. The proof is never labelled USER_APPROVED by me; full 8-minute production does not start before that approval.

## Why it is not built in this turn
The brief asks to build it "after RESEARCH_AND_CONCEPT_READY, per the project approval rules". The research stage is the deliverable here; the proof is the next autonomous step (free).
