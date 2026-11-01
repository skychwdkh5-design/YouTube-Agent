# Orbital Atlas — 3D action pilot v4

Owner steering: action pilot v3 was a step in the right direction, but shots must be more dynamic and the primary visual must not be 2D graphics. V1/v2 were rejected; v3 is not an approved final visual style. V4 is pending owner review.

## Direction
Independent object action in actual 3D geometry, changing perspective and occlusion, multiple camera setups, directional lighting/cast shadows and meaningful scene-state rewind. No substitute using only crops of a single still or flat puppet graphics. Scientific source imagery remains an evidence layer for production episodes, not replaced by fictional geometry.

## This demonstration
15 seconds, 1280×720, 30fps. Original generic rover mesh, six wheels with rotating treads/spokes, suspension bump, chassis/mast/arm, rock-half meshes, yellow faceted illustrative crystals, debris meshes, terrain/gravel/mountains. Full XYZ perspective projection, depth buffer, directional shadow map and specular shading. Not photorealistic; a stylized procedural 3D blocking/material study. Not accurate Curiosity geometry, mineral morphology or physical reconstruction. Always labelled Illustration / 3D motion test. Local temporary Flite voice, not Adam; original synthesized sound accents. No paid services.

## Timed shot plan
- 0–2.2s: follow shot, three-quarter rover view moving across 3D terrain.
- 2.2–4.2s: low wheel/rock view; wheel contact at world time 3.62s, rock split starts 3.67s.
- 4.2–5.7s: close fracture/interior view, separate rock halves and particles.
- 5.7–7.7s: camera orbit around the revealed detail, parallax and changing occlusion.
- 7.7–9.2s: wide rewind; actual world time 7.6 -> 2.4s, objects reverse together. Overlay and audio mark rewind.
- 9.2–10.7s: low-angle close contact replay; world time proceeds 3.25 -> 4.5s across the full replay.
- 10.7–12.5s: reverse-side close angle on fracture, continuing the same replay.
- 12.5–15s: macro orbit on exposed illustrative crystals; resolved state at world time 6.8s.

Voice/caption windows are authored in build.py. They are temporary scene description, not sourced historical narration or forced-aligned production speech.

## Reproduce
In examples/3d-action-pilot-v4/, run python build.py. Requires g++, Python numpy and FFmpeg with libx264, AAC, libass and Flite. No external 3D engine/assets needed. build.py compiles the custom C++ CPU mesh renderer, builds temporary narration/audio/captions and renders OA_3D_action_v4_15s.mp4. Intermediate files are written alongside source. Source is editable and deterministic apart from fixed synthetic texture/particle patterns; no external API calls.

## Handoff
Keep docs/CLAUDE_VIDEO_HANDOFF.md workflow: ChatGPT writes sourced script + second-by-second action/storyboard/motion/assets plan; Claude assembles and verifies it. The owner has not yet approved the final look. Do not merge/publish or treat this demo as scientific evidence. Main, episode queue and published releases are unaffected by this branch.
