# Visual effect catalog (reference-derived, re-implemented originally)

Each entry was **observed** in Reference 01 (R1) or Reference 02 (R2) (see the analysis files); the implementation notes are ours.
Status vs the current engine (`orbitalatlas/`), evidence = file/test:
`IMPLEMENTED` · `PARTIALLY_IMPLEMENTED` · `NOT_IMPLEMENTED` · `REQUIRES_GEOGRAPHIC_DATA` · `REQUIRES_NEW_DEPENDENCY`.
Camera classes: **A** image-space · **B** georeferenced map/globe camera from vector data · **C** true 3D terrain/globe with relief. Only A and a globe-projected B exist (see VE-01).

| id | effect | seen | status |
|---|---|---|---|
| VE-01 | continuous map camera (eased pans, zoom, blur) | R1, R2 | IMPLEMENTED for class B globe view (`geo.GeoCamera`, `GeoScene`); flat/tilted map plane and photoreal basemap: REQUIRES_GEOGRAPHIC_DATA |
| VE-02 | region highlight: fill + outline draw-on | R1, R2 | IMPLEMENTED (`geo.GeoFill`, `geo.GeoPolyline`; tests `test_geo`, demo) for Natural Earth polygons |
| VE-03 | labels anchored to a place, kinetic reveal | R1, R2 | IMPLEMENTED (`geo.GeoLabel`, `layers.AnchoredText`) |
| VE-04 | countdown/step badge with rolling digit | R1 | PARTIALLY_IMPLEMENTED (`text.roll`, `Breadcrumb` highlight; no disc badge that travels and scales) |
| VE-05 | shape comparison: move/rotate one country over another | R1 | NOT_IMPLEMENTED (data exists; needs rotating polygon vectors on the sphere and keeping true size) |
| VE-06 | crosshair + leader + label plate | R1 | PARTIALLY_IMPLEMENTED (`GeoMarker` leader/plate, Dubai-engine `crosshair`; not in shared package) |
| VE-07 | radial glow blob under a point | R1 | PARTIALLY_IMPLEMENTED (`MaskFill` radial wipe, `Spotlight`; no free glow blob) |
| VE-08 | ring pulse / ping | R1, R2 | IMPLEMENTED (`PulseMarker`, `GeoMarker`) |
| VE-09 | pin drop with bounce | R1, R2 | PARTIALLY_IMPLEMENTED (pulse marker; no pin icon, no drop/bounce) |
| VE-10 | flash-white cut to a different footage type | R1 | NOT_IMPLEMENTED (an additive white dip transition is easy to add) |
| VE-11 | whip pan with motion blur | R1, R2 | IMPLEMENTED (`transitions.WhipPan`; camera blur in `GeoScene.render`) |
| VE-12 | impact headline (bold, offset coloured duplicate, blur-in) | R2 | NOT_IMPLEMENTED (kinetic text exists; no duplicate layer, no horizontal blur-in) |
| VE-13 | glowing river/line network drawing on | R1 | REQUIRES_GEOGRAPHIC_DATA (rivers not fetched; line draw-on exists: `GeoPolyline`) |
| VE-14 | hand-drawn ellipse highlight | R1 | NOT_IMPLEMENTED (ellipse stroke draw-on is trivial, wobble not done) |
| VE-15 | icon in a badge (hex/octagon) with tag/count | R2 | NOT_IMPLEMENTED; REQUIRES original icon assets |
| VE-16 | comet trail along a path (bright head, fading tail) | R2 | PARTIALLY_IMPLEMENTED (Dubai-engine `fx.trail`; great-circle path via `GeoPolyline`; not shared) |
| VE-17 | icons flying with parallax / staggered pops | R2 | NOT_IMPLEMENTED; REQUIRES original icon assets |
| VE-18 | photo insert with flash/dip, then back to map | R1 | IMPLEMENTED as separate class-A `Scene` + transition (`GeoFocus` used in the proof); flash dip itself = VE-10 |
| VE-19 | map-to-evidence hand-off with a clear label | (OrbitalAtlas need) | IMPLEMENTED (`GeoFocus` between `GeoScene` and `Scene`; proof video) |
| VE-20 | caption cards phrase by phrase | R1, R2 | PARTIALLY_IMPLEMENTED (ASS cues in `productions/dubai/motion/engine/av.py`; not in the shared package) |

---
## VE-01 Continuous map camera
- **Description**: eased pans between places (0.5–1.5 s), zooms into subjects (2–3 s), holds ≤ 3 s, motion blur on fast moves.
- **Purpose**: tells "where" without cutting; keeps spatial context.
- **Timing**: pan 0.5–1.5 s; zoom 2–3 s; hold ≤ 3 s with an animated overlay; keep ≥ 1 camera move or overlay event per 2 s.
- **Camera**: class B. `GeoCamera` keys (lon, lat, span_km, bearing); centre follows the great circle, span in log space, optional `arc` zoom-out bump on long hops.
- **Data**: lon/lat of each stop (cite the source); land polygons for the shading (public-domain Natural Earth).
- **Rendering**: inverse orthographic projection per pixel → land coverage raster (multi-resolution); coast/borders as projected lines; temporal sub-sampling for blur.
- **Component**: `orbitalatlas.geo` (`GlobeView`, `GeoCamera`, `GeoScene`, `GeoRaster`).
- **Limits**: orthographic globe only (curvature visible at wide spans, flat-looking at city scale); sphere approximation (~0.3 % scale error vs ellipsoid); no terrain; no imagery basemap; no tilt/perspective; data detail 1:10M (≈1–2 km).
- **Verify**: projection round-trip + great-circle distance tests (`test_geo`), camera continuity test, labelled points inside the safe frame (`GeoCamera.check`), eyeball frames at several times; compare known landmarks against data (Dubai inside the UAE polygon).

## VE-02 Region highlight (fill + outline)
- **Description**: translucent fill (amber/red/cyan) with a thin glowing outline that draws on; sometimes a short pulse.
- **Purpose**: say which region the narration is about.
- **Timing**: outline 1–2 s; fill 1–1.3 s, radial wipe from a point optional.
- **Camera**: stays registered to the map under zoom.
- **Data**: polygon(s) from a named dataset; for water bodies mark the polygon as "approximate extent".
- **Rendering**: raster coverage of the polygon sampled per pixel (`GeoFill`), geodesic radial wipe from an anchor, `GeoPolyline` for the outline (arc length by great-circle distance).
- **Component**: `geo.GeoFill`, `geo.GeoPolyline` (class MAP).
- **Limits**: fill edges soft (1/2-resolution base); marine polygons are label-grade; disputed borders follow the dataset's de-facto lines.
- **Verify**: sample polygon coverage at known inside/outside points (tests); view frames at several zooms; outline vs fill edge match.

## VE-03 Anchored place label
- **Description**: bold letter-spaced uppercase text, letters rise in; sometimes along the feature axis (Persian Gulf ≈ −26°).
- **Purpose**: name the place at the moment it is on screen.
- **Timing**: appear when the camera is ≥ 70 % arrived; exit before the next label; keep ≥ 1 s readable.
- **Data**: label anchor from the dataset (polygon centroid, marked as label anchor, not a boundary).
- **Rendering**: `text.reveal_label` at the projected point; hidden on the far side.
- **Component**: `geo.GeoLabel`, `layers.AnchoredText`.
- **Limits**: no collision avoidance across labels beyond `Registry`; the angle is set by hand.
- **Verify**: `qa.check_overlays` (safe frame, collisions), frames at start/mid/end of the label's life.

## VE-04 Step/countdown badge with rolling digit
- **Description**: gold disc with a big digit; big at the start of a segment, shrinks to a corner; digits roll vertically on change.
- **Purpose**: structure (countdown) — only for list-style videos. OrbitalAtlas EP002 is not a countdown: use the `Breadcrumb` ladder instead.
- **Rendering**: `text.roll` for digits; disc not implemented.
- **Component**: `text.roll`, `geo.Breadcrumb`. **Limits**: no travelling disc. **Verify**: digits end on the target value at the declared time.

## VE-05 Shape comparison
- **Description**: a country shape is lifted and laid over another place with a white arrow.
- **Purpose**: scale comparison ("Australia fits over the US"). **Data**: polygons (Natural Earth) — real sizes must be preserved (rotate on the sphere, do not rescale).
- **Rendering**: rotate polygon vectors by a rotation about the globe centre (Rodrigues) per frame, rasterise; draw outline. **Status**: not implemented (needs rotation of unit vectors + an arrow overlay). **Limits**: apparent size varies with latitude in projections; label which projection. **Verify**: area ratio of the moved shape equals the original on the sphere (test).

## VE-06 / VE-07 Crosshair callout + glow blob
- **Description**: lines sweep out from a point, a label plate with an overline, soft glow under the point.
- **Purpose**: pinpoint a location. **Component**: `GeoMarker` (+ Dubai `crosshair`, `layers.MaskFill`/`Spotlight`). **Limits**: free glow blob and line-sweep not built. **Verify**: label inside safe frame; marker inside the target polygon.

## VE-08/09 Ring pulse and pin drop
- Ring: `PulseMarker`/`GeoMarker` (done). Pin drop: a red dot grows, becomes a pin with 1–2 bounces (0.5 s). Needs an original pin icon (vector, drawn in code) — not built. **Verify**: marker at the exact lon/lat (projection test), bounce settles on the point.

## VE-10 Flash cut / VE-18 photo insert
- **Description**: whole frame blooms to white (≈0.25 s), then the next footage fades in from white.
- **Purpose**: change of medium (map → real photograph/footage). **Rendering**: additive white dip on both frames; not built. OrbitalAtlas uses `GeoFocus` for map→evidence because it keeps the place in view. **Limits**: do not use a flash between two maps. **Verify**: peak luma frame exists for 1–2 frames only; no black frames.

## VE-11 Whip pan with blur
- **Camera**: ≥ 0.8 W in ≤ 1 s, in_out_expo, shutter ≈ 1/45 s. **Component**: `transitions.WhipPan`, `Push(shutter=…)`, `GeoScene` blur. **Limits**: ≤ 1 per video (rhythm rule). **Verify**: blur streak present, endpoints sharp, `qa` jump check passes inside declared window.

## VE-12 Impact headline
- **Description**: large bold words with a coloured offset duplicate; each word scales/blurs in on its spoken time.
- **Purpose**: the hook phrase. **Not built**: needs a text object with duplicate layer + horizontal blur-in; build on `text.reveal_label`. **Limits**: use sparingly (≤ 3 per video); never over a label. **Verify**: reveal frame = word start (provider timing), legibility 4.5:1.

## VE-13 Line network (rivers) / VE-14 hand-drawn ellipse
- Rivers: `GeoPolyline` with data from `ne_10m_rivers_lake_centerlines` (**not fetched**, REQUIRES_GEOGRAPHIC_DATA). Ellipse: stroke draw-on with slight wobble; not built.

## VE-15 / VE-17 Icons and badges
- Original icon assets are required (no external or reference artwork may be copied). Until drawn, no icon effects. **Verify** licence note for each asset.

## VE-16 Comet trail
- Bright head, fading tail along a great-circle arc over 1–2 s. Components: Dubai `fx.trail` (screen space) and `GeoPolyline` (arc). To do: shared geo trail. **Limits**: decorative; do not imply a real trajectory.

## VE-19 Map-to-evidence hand-off (OrbitalAtlas-specific)
- **Description**: the map camera ends on a marker; spotlight closes on it; the NASA photograph opens from that point.
- **Purpose**: keep the viewer oriented when switching from stylised map to documentary imagery.
- **Rules**: chip on the map "STYLISED MAP · source"; chip on the photo "NOT GEOREGISTERED"; no map lines over the photo; the marker position is a dataset point, the photo is not claimed to be centred on it.
- **Component**: `transitions.GeoFocus` + `geo.GeoScene` + `layers.Scene`. **Verify**: both chips present; transition frames have no black frames (`qa`).

## VE-20 Caption cards
- White 2–4-word cards bottom centre, small shadow, change each 0.7–1.2 s; current code: `productions/dubai/motion/engine/av.py` (ASS). Promotion to shared package pending.
