# OrbitalAtlas reference-derived style (original, not a copy)

Derived from two reference Shorts (see analysis files) as **mechanics**, not look-alikes. Do not copy any creator's branding, watermark,
icon artwork, topic, layout of title cards or exact edit order.

## What we adopt (rules)
1. **One continuous camera.** Between places move the camera (0.5–1.5 s eased pan, 2–3 s zoom) instead of cutting. A cut is allowed only for a medium change (map → photograph) and then via a motivated transition (`GeoFocus`).
2. **A new visual event every 1–3 s** (outline, label, marker, fill, counter, camera arrival). No static holds > 3 s unless an overlay animates (QA `max_static_s = 4`).
3. **Region emphasis = fill + outline draw-on**; the fill is a UI tint, the outline follows the dataset. One highlight colour per beat (amber = country, cyan = water).
4. **Labels sit on the thing they name**, appear when the camera is ≥ 70 % arrived, leave before the next label. Place names are uppercase, letter-spaced, one size per tier (continent 5 % of height, country 3–4 %).
5. **Breadcrumb ladder** (EARTH › … › DUBAI) tells where we are and how far we zoomed; scale bar in km at the screen centre.
6. **Every layer is labelled by class.** Stylised map = chip "STYLISED MAP · source"; photograph = chip "photograph · not georegistered"; never draw map lines on a photograph.
7. **Motion blur only on fast moves** (180° shutter); strokes and text stay readable.
8. **Captions** (when narration exists): 2–4 words per card, bottom centre, never over a hero label.
9. **Whips ≤ 1 per video**, flashes only between different media.
10. **Zoom story = scale ladder**: world → region → water body → country → city; each stop ≤ 3 s, one hero label per stop.

## What we do not adopt
Countdown/list format; emoji; watermarks; channel branding; military-style icons; explosion effects; caption styles that imitate a specific channel; anything that implies a measurement we do not have.

## Colour and type
Brand tokens from `productions/dubai/motion/MOTION_DESIGN_SYSTEM.md §3` (ink, text, amber, cyan, muted). Map palette (`geo.GeoStyle`): space (5,8,14), ocean deep (8,30,52), land (52,62,66), coast (150,205,215), glow (70,140,220). Font: DejaVu Sans Bold until an OFL face is installed.

## How future episodes use this
`/yt-motion-design` (rules) → `/yt-geographic-animation` (map/globe components, data) → `/yt-cinematic-edit` (camera/transition choice). Data: `tools/fetch_natural_earth.sh`. Proof first: `orbitalatlas/demo/geo_locator_proof.py` is the template for a locator sequence.
