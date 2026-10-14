# Visual engine baseline (frozen 2026-10-14)

**VISUAL_ENGINE_STATUS: PRODUCTION_BASELINE_V2C** - allowed for production; the style has **not** been USER_APPROVED. Do not start v3 or make
demo videos for effect development without a new task from the owner. Improvements wait in `FUTURE_VISUAL_ROADMAP.md`.

## How an episode uses it (one command, automatic choices)
`python3 -m orbitalatlas.director render SLUG OUT.mp4 --audio voice/narration.wav --sfx [--size 1920x1080 --workers 4]` after `storyboard.py plan`
(writes `story/motion_plan.json`). The director reads timeline v3 + motion plan, decides every effect, writes `OUT.director.json`
(decisions, skipped, focus, pacing, dates, intensity, sfx cues) and `OUT.mix.wav`. QA: `orbitalatlas.qa.run_video(..., cuts=report.intended_changes)`,
`orbitalatlas.demo.verify_sync.check`, ffmpeg ebur128/freezedetect. Cost: about 11 s render per 1 s of 1080p video on 4 cores (ep901: 26.8 s in 4 m 55 s).

## Capabilities -> components (all tested; tests in `orbitalatlas/tests/test_visual_v2*.py`)
| capability | component | selection rule (automatic) |
|---|---|---|
| cinematic map zoom (class A, image space) | `director.camera_keys`, `camera_presets` | snap 0.7 s / scale change 1.2-1.6 s from storyboard views; blur capped (max_blur_samples 6) |
| kinetic typography | `typeset` (rise, depth, slide, outline_fill, type, pop), ImpactCard, NumberCard | revelation -> impact card (<= 5 words); number -> number card; >= 5 s apart, <= 4/min |
| animated English captions | `captions` styles A-E, `make_cards` | calm sentence -> A; place/number/year -> D; C only near no impact card; never count-up |
| keyword lift text -> map | `interact.KeywordLift` | first mention of a pinned place outside focus; caption copy dimmed 40 % |
| motion graphics / arrows / callouts | `fx.RouteArrow`, `CalloutPanel`, `CompareLink`, `MarkerPin` | route rule 'from X to Y' or distance; one label per place |
| geographic highlights | `fx.RegionTint` (+ contour light) | place with a stack region; flash then alpha <= 0.2 on pixels |
| HUD overlays / dates | `interact.ImageStamp`, `EventYear`, `typeset.YearTag` | image date on every image change; event year amber + concurrent image stamp when different |
| camera parallax / depth | `interact.FloatingLabel`, `ParallaxDust`, `plane.PlaneTilt` | dust on every shot; tilt on the opening (camera held 1.6 s) |
| punch-in | `interact.Punch` | emphasis words in energetic sentences, >= 2.5 s apart |
| light transitions | `transitions.LightWipe`, `FlashDip`, `fx.LightSweep` | image date change -> light wipe; shot opening on revelation -> flash dip; scale jump -> push; energetic cut -> sweep |
| sound design | `sfx` (synthesised CC0) | cues from the report; >= 0.25 s apart; ducked, >= 12 dB under voice; -16 LUFS |
| traced shoreline / exposed-bed overlays | timeline v3 `fill`/`outline` layers -> `fx.RegionTint(thin=True)` + dated `CalloutPanel`; masks from `tools/autopilot/shoreline_masks.py` | placed by the storyboard author on the words that speak about the change (EP003) |
| grammatical on-screen phrases | `orbitalatlas.phrases` (clause_suffix, label, lint) | every kicker/label; report['texts'] lists them with lint problems |
| semantic storyboard | `semantic.plan`, `semantic.intensity` | priorities revelation 6, number 5, route 5, comparison 5, year 4, place 3; <= 6 events / 10 s |
| quality control | `qa`, `verify_sync`, director `report['pacing']` | pacing limits 3 / 4 / 6 s (energetic / normal / calm) |

## Evidence (tests and renders)
ep900 (v2b, 19.3 s) and ep901 (v2c, 26.8 s): `productions/ep901-visual-demo-c/qa/QA_V2C.md` - 0 freezes, qa ok, captions 17/17, onsets 62/65,
effects >= 13.9 dB under voice, pacing gaps <= 1.93 s. Masters: `media/visual-engine-v2c-demo`. Unit tests: orbitalatlas 143, autopilot 136 (2026-10-14).
Fixes found on the way: `knowledge/solutions.json` (ids event-year-vs-image-date, keyword-lift-caption-to-map, adaptive-intensity-and-pacing,
sound-design-synthesised-ducked, opening-tilt-then-move and the v2/v2b entries) - search with `kb.py search`.

## References
VISUAL_REF_001 (cinematic geography Short) and VISUAL_REF_002 (kinetic typography reel): `docs/references/library/` (analyses, 28 effect records,
`UNIFIED_STYLE_GUIDE.md`, `REFERENCE_COMPARISON.md` with the remaining gaps). The reference video files are not in the repository (copyright).

## EP003 quality pass (2026-10-15)
EP003 V2 used the baseline plus the two rows above; findings in `knowledge/solutions.json` (onscreen-phrase-grammar, shoreline-masks-seeded,
director-shoreline-layers, callout-anchor-off-screen, pronunciation-check-unavailable). Check fixes with `director stills` (about 1 min) before a full render (about 45 min).

## Known limits (not fixed)
Director renders geo shots from one stack per shot (no globe Earth -> country); 2.5D only; synthesised SFX, no music bed; count-up shows
intermediate values for 0.4 s; vertical Shorts layout not reviewed; the balance was mixed against the flite test voice, not a real narrator.
