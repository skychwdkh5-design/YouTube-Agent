# Orbital Atlas — selected visual direction
Updated 2026-11-01. Owner selected option 3, "Живописная иллюстрация", from three style previews. The owner explicitly instructed that newly created objects in future Orbital Atlas videos must use this style. This is the standing art direction. V7 animation review remains pending. It is not publication permission.

## Selected look
Semi-realistic hand-painted editorial illustration: visible controlled brushwork, textured materials, sculptural light/shadow, fine ink detail, expressive natural-proportion people. Photographic/terrain map provides continuous spatial context.
- Ship: weathered emerald hull, orange/navy/cream cargo, detailed white superstructure.
- People: expressive human proportions and readable gestures; maritime example uses white officer shirt, dark trousers/tie, cap, bearded face. Invented illustrative character, not an actual crew portrait.
- Props: painterly paper/metal texture, natural depth, clean alpha silhouettes; no glossy plastic or toy-like miniatures.
- Palette: navy terrain/water, teal route, restrained warm ochre and red obstruction accents.
- Individual actors/props move independently. Camera follows action, reveals consequences and hands attention to the next object.
- Medium may be layered compositing of painted assets; do not call this full 3D simulation, rigging or actual documentary footage.

## Motion and narrative rules
Preserve the reference-led storytelling and the v6 direction the owner preferred: shared map space, actor movement, obstruction/consequence, staggered queue, expressive person/props, purposeful transitions and actual scene-state rewind.
Every shot/beat has a narrative job: actor, action, result, comparison, reaction or evidence. A new angle or still-image zoom alone is not a new story beat. One dominant focus at a time; do not accumulate props until action becomes unreadable.
Use verified numbers and source-based claims. Mark symbolic scale/positions and artistic reconstructions as Illustration. Real source images retain accurate credit and identity. A prop metaphor is not a numerical measurement or loss estimate.
Keep cover subject visible at the existing first-3-second gate; preserve all source/rights/voice/caption/QC/publication rules. No new paid services.

## Working model: ChatGPT -> Claude
ChatGPT prepares a complete sourced English script plus per-second action/storyboard/motion/assets plan in this repository; Claude assembles from it.
Read docs/PAINTED_VIDEO_HANDOFF.md for required package fields. Do not substitute zoomed stills for specified actions or silently change factual meaning. Align timings to actual final voice; authored temporary windows are not forced alignment.
The first production episode still needs a representative 45–60 s narrated pilot before the full edit. Existing releases/queues remain untouched.

## Current executable sample
Active art references: docs/assets/visual-style/painted-props.webp and docs/assets/visual-style/painted-reference.webp.
Editable V7 example (review branch): https://github.com/skychwdkh5-design/YouTube-Agent/tree/production/dynamic-motion-style-v1/examples/painted-collage-v7 . It contains build.py, atlas.webp and generation-prompt.txt.
The new atlas is generated from the selected preview; not extracted documentary evidence. Transparent assets are separate ship/captain/money/watch; output is an animated 2.5D collage, not a rigged 3D model.
build.py uses the v6 map/action/camera/rewind/audio structure with painted replacements. The voice is temporary local Flite SLT, not Adam.
Run python build.py with Pillow, numpy, FFmpeg (Flite, libx264, AAC), and DejaVu Sans Bold at source path.
Output OA_suez_painted_v7_15s.mp4, 15 seconds, 1280x720, 30fps.

## Source/provenance limits for this sample
NASA background is March 11, 2021 Landsat Gulf of Suez context, rotated/cropped. It is not a photograph of the grounded Ever Given or a measured reconstruction of its exact grounding point. Ship symbols/route/count/scale/positions and captain are illustrative. Label: ILLUSTRATION / NOT TO SCALE.
Source https://science.nasa.gov/earth/earth-observatory/traffic-jam-on-the-suez-canal-148114/ supports six-day blockage, March 29 reopening and hundreds of waiting ships. Money is a cargo/trade metaphor, no loss figure.
Map credit: NASA Earth Observatory / Lauren Dauphin and Joshua Stevens, Landsat data from USGS.
Original URL https://assets.science.nasa.gov/content/dam/science/esd/eo/images/imagerecords/148000/148114/suezcanal_oli_202170_lrg.jpg
Map SHA256 46caf0253cf64157f7911ce4663578ca9857b2a338e781fd503ae481855565bf.

## History
Earlier demos v1-v5 are not accepted visual templates. V6 was preferred as a direction; its glossy props are superseded by selected option 3. Old experiment documents are historical context, not mandatory setup reading. Current guide takes precedence on art direction; existing factual/publishing safeguards always remain.
