# Mandatory production checks
- SOURCE_MATCH: compare the hero PNG visually and via pixel provenance to original approved drawing. No substituted design.
- ALPHA_CHECK: inspect transparent asset on black, white, gray checkerboard backgrounds for leftover lettering or paper fragments.
- MOTION_BOUNDS: roll <= 2 degrees, scale <= 3%, bob <= 10px at preview 960x540. No limb animation in safe renderer.
- LAYER_CHECK: experimental_layers forbidden in release.
- SCENE_CHECK: no cropped body, character not behind subtitles, no accidental repeated static scenes > 10s.
- VIDEO_CHECK: 1920x1080 30fps H264, no black frames, no clips missing, correct timeline duration, voice matches subtitles.
- EDITORIAL_CHECK: approved thumbnail matches frame 0, sourced facts, licenses and attribution ready.
- PUBLISH: do not upload/schedule until explicit user signoff; do not claim end-to-end QC based only on numerical checks.
