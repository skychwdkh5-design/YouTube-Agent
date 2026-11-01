# Suez collage pilot v6 — pending owner review
Date: 2026-11-01. Orbital Atlas / YouTube-Agent only.
V1/v2/v5 were rejected; v3/v4 also do not define an approved final look. V6 is a new test, not a migration, publication or approved template.

## Visual medium (important)
This is an animated documentary collage. The ship, captain, money and stopwatch are pre-rendered volumetric-looking generated raster props with transparency. They are independently translated, scaled and rotated above a NASA map; this is 2.5D compositing, not a fully rigged/physically simulated 3D scene. The captain has one authored expression, not facial animation. No claim of photorealistic 3D reconstruction.

## Story and shot/action timing
0–1.8s: camera follows a detailed container-ship prop along a growing route; voice "One ship."
1.8–3.1s: ship turns/stops; red arc and X identify obstruction; "One blocked canal."
3.1–5.1s: camera pulls back; twelve miniature ship symbols enter in staggered rows, generic captain pops into view with surprised pose; "Hundreds of ships waiting."
5.05–6.55s: money metaphor appears; camera travels toward it; "Cargo going nowhere."
6.3–8.55s: brass stopwatch enters with independently animated indicator, 6 DAYS label becomes the focus; "For six days."
8.7–10s: actual authored scene state 8.65 -> 0, camera state reverses with it; props, queue, ship rotation and route revert; "Let's rewind."
10.1–12s: camera returns to wider map context, MARCH 2021 label; "March twenty twenty-one."
12.1–15s: ship/obstruction/queue return without repeating money and clock; "The Suez Canal. One ship. One bottleneck."

Build.py is the exact executable motion specification and includes all voice cue windows. Caption and source labels are screen-space; action props are transformed with the shared map camera. Typical output: 15s, 1280×720, 30fps, H.264/AAC. Working voice: local Flite SLT, not Adam. Sound is original synthesized impacts, air/transitions, ticking and rewind sound; no paid APIs.

## Evidence and geographic limits
Source: https://science.nasa.gov/earth/earth-observatory/traffic-jam-on-the-suez-canal-148114/
NASA reports a six-day canal blockage, reopening March 29, 2021, hundreds of waiting ships, and cargo/tanker queues. No financial-loss figure is used. Money prop is a metaphor for held-up cargo/trade, not a dollar-loss estimate.
Background is the March 11, 2021 Landsat baseline image of the Gulf of Suez, NOT a photograph of the grounded Ever Given. It is rotated/cropped for the composition. Ship symbols, their counts, sizes, route, captain, location and motion are illustrative. The obstruction symbol is NOT a geolocated pin for the true grounding point. Persistent label: ILLUSTRATION / NOT TO SCALE; source line states objects/movement are illustrative. Do not reuse this layout as a measured map or event reconstruction.
The captain is an invented illustrative character, not a portrait of an actual crew member.
Full source credit: NASA Earth Observatory images by Lauren Dauphin and Joshua Stevens, using Landsat data from USGS (source article also covers VIIRS imagery, not used here).

## Assets and reproducibility
- atlas.webp is committed beside build.py: generated prop atlas, converted to WebP quality 92. SHA256 d9e42ee716c41f89885464f362ad67a2ce18aedc2545049b7de5877b87634838.
- NASA original https://assets.science.nasa.gov/content/dam/science/esd/eo/images/imagerecords/148000/148114/suezcanal_oli_202170_lrg.jpg ; dimensions 2653×3316; SHA256 46caf0253cf64157f7911ce4663578ca9857b2a338e781fd503ae481855565bf.
- build.py downloads NASA image if missing and checks SHA256. It reads committed atlas.webp. Run python build.py with Pillow, numpy, FFmpeg with libx264/AAC/Flite, and DejaVu Sans Bold at source font path.
- Output OA_suez_collage_v6_15s.mp4. It also writes temporary voice WAV/TXT and mix.wav alongside source.

## Review status
Keyframes and final one-second contact sequence inspected; file duration/streams/decode checked. Acceptance of visual style is for owner review. No retention or better-than-reference claims. No main merge, episode publication, queue change or paid voice request.

## Next full-video handoff
Keep docs/CLAUDE_VIDEO_HANDOFF.md: sourced full script, second-by-second storyboard, visual assets, exact actions, camera transitions, narration/audio anchors and QC gates. Do not extend a rejected pilot into a full episode.
