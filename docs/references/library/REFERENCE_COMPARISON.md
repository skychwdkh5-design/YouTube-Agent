# Engine vs references (after v2c, 2026-10-14)

Status words: **Reproduced** = built, tested and seen working in a rendered video; **Partial** = a weaker or composed version; **Not** = not built.
Evidence: `ep900-visual-demo` (automatic storyboard + director, 19.3 s, 1080p) and an automatic run on EP003's 300 s storyboard (first 30 s rendered).
Judged by the agent from frames of the rendered files; **not USER_APPROVED**.

## VISUAL_REF_001 (cinematic geography)
| id | technique | status | where / note |
|---|---|---|---|
| VR1-01 | fast scale changes, snap zooms with blur | Reproduced (image-space) | director.camera_keys: snap zoom / scale change / smooth move from storyboard views; blur capped (EP003 run showed smear at full blur) |
| VR1-02 | territory flash then settle | Reproduced | fx.RegionTint from stack `regions`; alpha capped on satellite pixels by rule |
| VR1-03 | flag cloth inside the country, glowing outline | Partial | glowing outline yes; flags/cloth not built (artwork + licence needed) |
| VR1-04 | boxed name label with leader line | Reproduced | fx.CalloutPanel (draw-on instead of blur-in), rows are narration words |
| VR1-05 | curved arrow with head + distance | Reproduced | fx.RouteArrow + RouteLabel; distance from pins (route events) |
| VR1-06 | big numeral in 2.5D flying in | Reproduced | kinetic.tilt_25d (used by RouteLabel) |
| VR1-07 | radial line burst | Partial | composable from DrawOnPolyline/CometTrail, no preset |
| VR1-08 | pin drop | Reproduced | fx.MarkerPin |
| VR1-09 | comet line across the map | Reproduced (component) | fx.CometTrail; not triggered by the planner yet |
| VR1-10 | ocean recoloured | Partial by policy | annotation tint only; real imagery is never recoloured |
| VR1-11 | word-by-word captions, active word coloured | Reproduced | captions B/D (amber/cyan instead of green) |
| VR1-12 | heavily graded basemap | Not on evidence (policy) | presets exist for presentation layers only |
| VR1-13 | blur-in of labels | Reproduced | kinetic.motion_streak / duplicate_offset |
| — | world-scale geography (continent -> country every 1-2 s) | **Not in the director** | the reference is a world map; our demos stay on one Landsat stack. orbitalatlas.geo (Natural Earth globe, class B) exists but the director does not use it yet |

## VISUAL_REF_002 (kinetic typography & motion graphics)
| id | technique | status | where / note |
|---|---|---|---|
| VR2-01 | outline type, type-on with cursor | Reproduced | typeset presets outline_fill, type (YearTag uses outline_fill) |
| VR2-02 | neon grid | Reproduced | PlaneTilt floor grid (opening), fx.NeonGrid |
| VR2-03 | light line unmasking text | Reproduced | v2c: light-sweep accents on energetic cuts, light travelling around region contours, glint on caption words |
| VR2-04 | full-frame colour card with huge type | Reproduced | typeset.ImpactCard on revelations (<= 5 words), captions hidden under it |
| VR2-05 | crosshair axes with ticks | Partial | YearTag tick line; no axis preset |
| VR2-06 | HUD panels | Reproduced (simpler) | NumberCard (kicker + count-up + unit + tail), CalloutPanel; the reference panels are denser |
| VR2-07 | heavy headline with colour duplicate / echo | Reproduced | duplicate_offset, ImpactCard outline echo |
| VR2-08 | easing graph, dot along an arc | Partial | v2c KeywordLift flies words on an arc; no easing-graph preset |
| VR2-09 | waveform | Reproduced (v2 demo) | fx.Waveform (measured); not used by the director |
| VR2-10 | timecode counter | Not | low value |
| VR2-11 | word emphasis in a sentence | Reproduced | captions + KineticLine emphasis (colour, glow, glint) |
| VR2-12 | noise glitch | Not (deliberate) | distracts in documentary |
| VR2-13 | text / map on a perspective plane | Reproduced | plane.PlaneTilt (opening of every director render) |
| VR2-14 | pulses, ring loaders | Partial | pin ring pulse only |
| VR2-15 | dark field, one accent | Adapted | OrbitalAtlas amber/cyan; violet only as decor |
| — | words travelling in depth, masks, line transitions | Reproduced | typeset presets depth_in/depth_out/rise, push_lines |
| — | true 3D type (extrusion, camera moving through letters) | Not | 2.5D only (perspective transforms of flat rasters) |

## v2c additions (ep901-visual-demo-c, 26.8 s, 1080p, automatic from script)
| technique (both references) | status | where |
|---|---|---|
| text interacting with map objects (word leaves the subtitle and lands on its place) | Reproduced | interact.KeywordLift; caption copy dimmed to 40 % |
| depth / parallax between text and map | Reproduced (2.5D) | interact.FloatingLabel, ParallaxDust (3 depths) |
| punch-in on stressed words | Reproduced | interact.Punch, energetic sentences only |
| flowing route dashes, light around contours | Reproduced | fx.RouteArrow, fx.RegionTint |
| adaptive intensity (calm / normal / energetic) | Built | semantic.intensity -> director |
| visual change every 1-3 s in dense passages | Measured | report['pacing']: max gap 1.3-1.9 s per sentence in ep901 |
| sound design (whoosh, sweep, impact, rise, UI blips, ticks) | Reproduced (original synthesised, CC0) | orbitalatlas.sfx; ducked >= 12 dB under the voice |
| image date vs historical year | OrbitalAtlas rule (not in the references) | ImageStamp (cyan, IMAGE ·) vs EventYear (amber) |

## Honest overall gap (after v2c)
Remaining differences, concrete: (1) the references are vertical Shorts with a new idea every 1-2 s; our long-form caps focus cards at 1 per 5 s, so v2c gets its
1-3 s rhythm from lifts, punches, stamps and accents, not from full-screen cards; (2) VR1's world-scale jumps (continent -> country) are still absent - the
director stays on one Landsat stack; (3) no true 3D type or camera moving through letters (2.5D only); (4) the sound effects are synthesised and simpler than
library foley; no music bed; (5) the test voice is flite - the energy of a real narrator is missing and the effects were mixed against a robotic voice; (6)
VR1 flags/cloth and VR2 dense HUD panels are not built.

## Earlier gap note (v2b)
The engine now has most of the vocabulary of both references and applies it automatically from the narration, with one focus at a time. What still separates the
output from the references: (1) density and rhythm - the references change something every 1-2 s, our long-form rules cap focus graphics at one per 5 s and
4 per minute (correct for a 10-minute documentary, slower than a Short); (2) world-scale map storytelling (VR1) needs the globe in the director; (3) the
references are vertical Shorts, our demos are 16:9 long-form; (4) no real voice yet (flite test voice); (5) no sound design (whooshes on transitions are a large
part of the references' energy and are absent here).
