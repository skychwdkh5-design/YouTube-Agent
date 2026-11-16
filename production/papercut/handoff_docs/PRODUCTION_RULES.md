# Approved paper-cut character: frozen visual identity

## Absolute constraints
- `source/APPROVED_CONCEPT_UNMODIFIED.png` is the single source of truth.
- `characters/hero_approved_clean.png` is the primary production asset; it preserves approved visible pixels and removes the stray background elements from V2. Do not re-generate or reinterpret it.
- Stable production uses whole-character 2D transforms and original source poses ONLY.
- `experimental_layers` are overlapping region crops, NOT a usable bone rig. Do not rotate them independently. They have no hidden geometry or elbow underpaint.
- The character should generally occupy 12–24% of 1920x1080 width and never cover captions.
- No need for walking. For scene changes character may float, cut to an approved original pose, or exit frame.
- Do not try lip sync. It has NOT been implemented. Animated subtitles and scene motion can carry rhythm. Do not claim the character speaks with moving mouth.
- On-screen assets and historical/sci-fi imagery must be separately sourced with appropriate rights and fact checking.

## Shot construction
1. Build background/diagram, then character, then text overlay.
2. Use approved hero cutout; apply small translations, rotations, gentle scale.
3. Change expression only by carefully using original complete character pose, not by swapping face elements that may not align.
4. Avoid crossfading two mismatched poses if it looks like ghosting; use a hard cut on an edit or a wipe.
5. Keep 2–3 s of scene-specific environmental action between repeated hero motion cycles.
6. Do not extrapolate from one pose to a 3D model.

## What would be needed for full rig
To create accurate real arm/leg movement, artist must design separate visible body components from scratch and paint underlying joint overlaps, export a compatible layered file, plus create mouth-shapes. This pack does not honestly contain that. A future manual animation-rig milestone is separate.
