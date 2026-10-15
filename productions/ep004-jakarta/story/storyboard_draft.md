# EP004 draft motion storyboard (2026-10-15) - DRAFT, timings are ESTIMATES (no provider alignment exists; TTS not authorised)

Legend: class = EVIDENCE / MAP / TRACED / ILLUSTRATION / TEXT (docs/ORBITALATLAS_VISUAL_MASTER.md s.3). Camera class A = image space, B = georeferenced globe (orbitalatlas.geo). "Built" = in the V2C baseline.
Every scene also carries: caption band (style A/D), source chip top-left, evidence disclaimer line, SFX cue from `orbitalatlas.sfx` (CC0), phone-safe text >= 30 px.

## S1 Hook, 0:00-0:30 - EVIDENCE
- Narration: see concept.md. Evidence: ESA 2024 map (P1), credit chip. Open state: full-frame map, desaturated 0 %, no grade (evidence_safe), legend visible, stamp "SENTINEL-1 RADAR · 2017-2018 · LINE OF SIGHT" (ImageStamp).
- Camera A: hold 1.2 s, then snap-zoom (0.7 s) onto the west cluster, 1.4 s scale change out to the north-west cluster, then the east one; each target gets a flash->alpha<=0.2 ring (fx.RegionTint) + count-up "≈12 cm/yr" (NumberCard, once, attributed "ESA, local maximum").
- Entrances: stamp 0.0 s, ring 1 at word "red patch" (~1.0 s), NumberCard 4.2 s, rings 2-3 at 8-11 s, three question cards (captions D) 18-28 s. Transition out: flash_dip 0.3 s into S2. Sound: rise + impact on NumberCard, UI blips on rings.
- Payoff: viewer sees measurement, not a CGI. Engine: camera_keys, RegionTint, NumberCard, ImageStamp = Built. Region rings are manual positions on a non-georeferenced JPG -> class TRACED/annotation, no district names (U7).

## S2 Geographic establishment, 0:30-0:55 - MAP (class B)
- Narration: where Jakarta is. Evidence: Natural Earth (P9) coastline/admin polygons; Landsat 2026-09-14 (P7) for the last frames.
- Camera B (`geo.GeoCamera`): orthographic globe, great-circle glide from Southeast Asia to Java to Jakarta Bay, log zoom, 2.4 s of the glide, then **cross-dissolve at matched coastline** into the Landsat stack (image-space). Labels: Indonesia, Java, Jakarta (GeoLabel), scale bar.
- Transition: geographic match cut (coastline outline stays, fill changes) 0.8 s. Sound: whoosh at glide start, tick on each label.
- Limit: not a 3-D flyover (no DEM); labelled in the report as "georeferenced globe camera + image-space". Engine: geo.GeoScene/GeoCamera built, **not wired into the director** (FUTURE_VISUAL_ROADMAP #2) -> a short episode-specific driver is needed; to be proved free.

## S3 Radar reveals ground motion, 0:55-1:50 - ILLUSTRATION then EVIDENCE (proof target)
- Narration: pulses, two passes, phase shift, millimetres along the line of sight. Evidence: concept explanation C26 (after source read). Disclaimer on screen: "ILLUSTRATION - not to scale".
- Open state: dark ground plane (PlaneTilt, 2.5D), a satellite glyph at top, ground line with a house/road block.
- Layers: (1) orbit track with satellite sliding in 1.5 s; (2) radar beam drawn as expanding wavefronts to ground (fx/DrawOnPolyline); (3) wave of pass 1 in cyan, pass 2 in amber, a visible phase offset between returns as the ground block lowers by an exaggerated amount (label "exaggerated"); (4) fringe counter "1 colour cycle ≈ 2.8 cm" (after read); (5) line-of-sight arrow vs vertical arrow with angle to explain LOS; (6) hard cut + flash_dip to the measured ESA map, legend sweeping (light_wipe), stamp "MEASURED". 
- Timings: beam 1.0-3.0 s; pass 1 3.0-5.0 s; ground drops 5.0-7.0 s; pass 2 + offset 7.0-9.5 s; LOS arrow 9.5-11.5 s; cut 12.0 s; map hold 12-15 s. Sound: sweep for beam, tick for phase, impact on cut.
- Engine: layers/PlaneTilt/DrawOnPolyline/NumberCard built; **wavefront/phase-offset drawing and LOS-angle diagram are NOT built** (need `orbitalatlas/illustrate.py`, new reusable, with isolated tests).

## S4 Underground mechanism, 1:50-3:00 - ILLUSTRATION (layered 2.5D cross-section)
- Layers back-to-front: sky gradient, city skyline silhouette, surface soil, clay/silt layer (compressible), confined aquifer (sand), deeper clay; wells with a draw-down cone.
- Animation: pumping starts (well level drops, 1.2 s) -> pore-pressure arrows shrink -> clay layer thins by a few px (compaction, easing out) -> surface line lowers and building tilts slightly -> label "compaction is largely not reversible" only once C28 sourced; until then "may not fully recover". Scale disclaimer "not to scale; depths illustrative".
- Parallax depth 3 planes; section reveal by mask (MaskReveal). Not uniform: a second column at the right with smaller well lowers less (shows non-uniform). Sound: low rumble (sfx rise), UI blip on labels.
- Engine: MaskReveal, PlaneTilt, ParallaxDust built; **cross-section primitives and layer-thinning tween NOT built** (illustrate.py).

## S5 District comparison, 3:00-4:10 - EVIDENCE + TRACED
- Landsat 2026-09-14 stack (P7, true colour, calibrated mosaic via tools/autopilot/landsat_color.py), Natural Earth boundaries for locator. Region cutouts for three hotspot areas **only as placed from Data in Brief's described locations (PIK 2 area, Tanjung Priok, western Tangerang border)**; marker accuracy "approximate, ±km" disclosed. Dated radar overlays are shown only where georeferenced (otherwise side by side, no overlay).
- Camera A between three views, snap 0.7 s; callouts name place + study period. Split-screen compare NOT built (VISUAL_MASTER) -> use light_wipe between 1990 and 2026 Landsat for urban growth (same grid) and compose side-by-side as two Scenes in one frame (new `SplitFrame`, simple).
- Disclaimer: "Optical image shows land cover, not subsidence."

## S6 What radar cannot see, 4:10-5:00 - EVIDENCE + ILLUSTRATION
- The ESA map with the missing-coherence strip outlined as an annotation (dashed amber, "no reliable radar signal here - Data in Brief 2026") drawn on Landsat context rather than on the ESA JPG (no unregistered map-on-image).
- Beats: coherence concept as speckle vs stable return (small illustration), reference-point caveat, LOS vs vertical arrow, GNSS check "RMSE 9.4 mm".

## S7 Flood risk, 5:00-5:55 - ILLUSTRATION
- Side-view animation: land lowers (S4 rig reused), tide line rises, river outlet blocked by high sea level, rain streaks. Water levels illustrative; label "ILLUSTRATION"; observed floods shown as dated text cards only (2007 > 70 % submerged per NASA; Jan 2020 377 mm/day after source read).
- No rain/tide/subsidence percentage anywhere.

## S8 Response, 5:55-6:50 - TEXT + MAP
- Policy timeline: 2021 regulation, Aug 2023 in force, Feb 2026 rule, sea wall "planned" (dates from primary sources only; claims C22-C24 pending read). Coast Landsat with dated cards. One chart only (hotspot time series from Data in Brief figure if reusable under CC BY with credit, else redrawn from stated values - none stated, so no redraw).

## S9 The twist, 6:50-7:40 - EVIDENCE
- Visual shift: the big "≈12 cm/yr" number dissolves into a map of three hotspots with three small time-series insets (west flattening; NE/NW linear) from Data in Brief fig. 4 (CC BY 4.0, credited, unmodified) -> "not one sinking city". RSASE-based recovery content only if read.

## S10 Resolution, 7:40-8:15 - EVIDENCE
- Return to the S1 map, now with its legend labelled "what it measures" / "what it can't". Closing card lists the limits (LOS, masked coast, 2016-24). No call-to-action stock phrases.

## Capability summary (honest)
| needed | status | plan |
|---|---|---|
| snap/scale camera, region rings, number/year cards, stamps, light wipe, flash dip, captions A-E, SFX | Built (V2C) | use as is |
| globe -> country -> Landsat match cut | geo.py built, director not wired | episode driver + test (free) |
| radar geometry/phase/LOS illustration | NOT built | new `illustrate.py` (proof target) |
| cross-section 2.5D with compaction tween | NOT built | same module |
| split-screen / side-by-side | NOT built | `SplitFrame` |
| true 3D flyover, DEM | NOT possible (no DEM host) | not claimed |
| georeferencing the ESA JPG | NOT possible without control points | keep as class A, no district names |
