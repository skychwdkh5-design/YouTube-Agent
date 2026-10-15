# EP004 S3 V2 "Cutaway Descent" - proof report (2026-10-15)

STATUS: **S3_V2_PROOF_READY** - TECHNICALLY_VALID; frames reviewed (54/54 at 4 fps + 24 transition frames); USER_APPROVED: NO. Paid credits: 0. Main, EP001-EP003 untouched.

File: `s3v2.mp4` 13.5 s, 1920x1080, 30 fps, H.264 + AAC, 5395509 B, sha256 `8e534c4bcec03e8650a4a479f241791947263af452f0877742d9ddd619c5093d` (branch `media/ep004-s3-proof-v2`).
Content: ILLUSTRATION only (chips throughout), no ESA frame, no measured value, RSASE not used (abstract-level only, nothing in S3 needs it). Sound: CC0 synthesised cues, effects only.

## Choice (details: DESIGN_OPTIONS.md)
A "Cutaway Descent" (weighted 40) over B "Orbital Split" (20) and C "Beam Ride" (23): the only option where the cause (pumping -> clay compaction) and the measurement (two passes -> extra path -> LOS component) share one continuous space.

## Shot flow
0-1.6 s wide: satellite arrives on its orbit over a cut-away block of city ground -> 1.7-2.9 pass 1: pulse rings travel the beam, ground ripple, echo -> 3.0-4.6 camera dives to the cut face (topsoil, clay, saturated sand aquifer, clay, bedrock) -> 4.2-5.6 pumping: the water level in the well (pressure/head) drops, the aquifer stays saturated -> 5.3-7.2 clay layers thin, pore water leaves the clay, the surface sinks in a bowl and lights up (hero) -> 7.2-8.7 camera rises, the satellite returns, pass 2 hits the lowered point -> 8.6-9.4 EXTRA PATH (pass-2 range beyond the pass-1 distance arc) -> 9.9-11.7 side-on view, city recedes into depth fog: cyan LOS component vs white vertical drop with a true right angle; lockup LINE OF SIGHT / NOT THE VERTICAL DROP -> 11.8-12.8 camera rises to the top view -> 12.2-12.8 match dissolve into EVIDENCE MAP PENDING (same rectangle).

## What objectively improved vs V1 (measured on both files with the same QA script)
| measure | V1 | V2 |
|---|---|---|
| visual activity, median mean-abs frame difference per second | 0.52 | **1.98** |
| slowest second (activity) | 0.06 | 0.29 (0-2 s establishing) |
| camera | 1 push-in on a flat 2-D diagram | continuous keyed perspective camera through 10 keys: wide, dive, low hero, rise, side-on, top view; real parallax (floor, buildings, dust) |
| depth layers | 1 (flat) | floor grid, block, buildings, sky, dust, cut face, glow, depth-focus fog |
| max text blocks on screen at once (excl. chips) | 6 | **2** (one caption + at most one label; tested every 0.25 s) |
| typography | DejaVu, plain | Inter; word-rise captions with amber emphasis; heavy/outline weight-contrast lockup (VR2-01/07) |
| physical content | geometry only | cause + measurement: head drop, clay-only compaction (surface drop == clay loss, unit-tested), pass 2 to the lowered point, extra path, LOS projection |
| transitions | 1 flash dip | no flashes; continuous camera; one match dissolve (top view -> placeholder rectangle) |
| sinking as the hero | small bowl in a side diagram | bowl in the city block, lit, close camera, compacting layers below |
| yt-qc / orbitalatlas.qa / freezes / black frames | PASS / ok / 0 / 0 | PASS / ok / 0 / 0 |
| mobile readability issues | 0 | 0 (captions 52 px, labels/chips >= 30 px) |

## Rubric (docs/VISUAL_QUALITY_RUBRIC.md, my own scoring - not an audience test)
opening impact 2 (diagonal satellite -> beam -> block reads at once, but 0-1.6 s is slow) · production quality 2 (lit, fogged, glowing; flat shading, no textures/shadows) · geography n/a · camera 3 · transitions 2 · typography 2 · variety 3 · density 2 · sync 1 (no narration; hand timing) · engagement 2.
**Mean 19/9 = 2.11, no 0** -> passes the rubric line that V1 missed (1.56). That is a self-assessment against written reference analyses; the reference video files are not available (repo, branches, Drive searched), so no frame-to-frame comparison was possible.

## Against VISUAL_REF_001 / 002 (written analyses)
Closer: event-driven continuous camera with scale changes and holds (VR1-01), flash-then-settle hits as ground ripples (VR1-02 idea), one idea per beat with type as hero at the key moment (VR2 principle 1), weight contrast (VR2-07), text on a dark stage with one accent per layer.
Still short: VR1 snap/whip energy and motion blur (our moves are smooth, 0.8-1.2 s); VR2 extrusion/true 3-D type and dense HUD panels; flat-shaded geometry without textures; synthesised sound, no music.

## Scientific checks
Unit-tested: surface lowering equals clay thickness loss; sand aquifer thickness constant; head stays above the aquifer top (confined); drop at the point equals the declared drop; pumping precedes sinking; satellite over the beam plane while pinging; pass-2 target = lowered point; LOS component = drop x cos(incidence); right angle at the foot; camera exactly side-on during the construction; lens shift keeps angles. Not claimed: any rate, depth, distance, incidence angle or time between passes; "pressure drops" is shown as the well level only.

## Known defects (seen in the frames)
0-1.6 s establishing is slow; 9.5-9.8 s in-between move shows the outgoing caption fading over the aquifer; the "WATER PRESSURE DROPS" label partly overlaps building silhouettes while it fades in (4.5 s); 10-11 s lockup hold has low motion (cyan glow breathes, camera creeps); placeholder still plain. Not verified: real-time feel on a device, audio by ear.

## New reusable components (tests: orbitalatlas/tests/test_subsidence3d.py, 21)
`orbitalatlas/scene3d.py` (Camera3D with lens shift, CameraPath, staged Painter, box, sky) and `orbitalatlas/subsidence3d.py` (CutawayRadarDiagram). Catalogued in knowledge/effects.json; three knowledge-base entries (painter staging, lens-shift profile shot, session disk allowance). Render cost: ~1.2 s per 1080p frame (about 3.5-4 min for the proof on 4 workers).
