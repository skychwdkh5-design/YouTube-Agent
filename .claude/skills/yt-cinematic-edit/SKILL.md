---
name: yt-cinematic-edit
description: >-
  Narration-led documentary editing for OrbitalAtlas - shot rhythm, camera paths, transitions chosen
  by story purpose, retention-oriented openings, audio-visual sync from word timestamps, subtitle
  placement, and the proof-first workflow. Use for "edit this episode", "pacing", "transitions",
  "camera movement", "make the opening stronger", or before assembling any multi-scene render.
  Not for cutting raw footage (/yt-edit) or for Landsat processing (/yt-geo).
---

# yt-cinematic-edit

Read: `docs/CINEMATIC_CAMERA_SYSTEM.md`, `docs/TRANSITION_DESIGN_SYSTEM.md`, `docs/MOTION_DESIGN_STANDARDS.md`.

## Procedure
1. Segment the narration by *story function* (hook, setup, reveal, turn, evidence, payoff), not by sentence.
2. Per segment choose camera class (A image-space / B map / C 3D). Only A is built; B/C = stated limitation.
3. Choose the transition by what changes (see TRANSITION table). Fill "purpose, limits, verify" per cut.
4. Opening: first 3 s must show the strongest real image in motion with the hook phrase on screen or spoken;
   no logo/title card first. Reveal geography within 8 s.
5. Sync: map each reveal/arrival/year change to a word start (±1 frame at 30 fps) from provider timestamps.
6. Subtitles: bottom safe zone, ≤2 lines, ≤42 chars, never over the hero label; build with `engine/av.py`.
7. Sound: narration −16…−14 LUFS, true peak ≤ −1 dBTP; music/sfx only with licensed/original sources.
8. Proof clip → review frames → user approval → scale.

## Rhythm rules
Establishing 3–5 s · reveal 2–4 s · detail hold ≥1.2 s · nothing >7 s without a new element · vary shot size ·
no identical move/transition 3× in a row · ≤1 whip per video.
## Verify
blackdetect, frame-diff per second, cut-frame centroid check, subtitle check, word-vs-reveal frame check.
## Do not
Hide weak story with flashy transitions; claim spatial continuity between unregistered images;
describe an image zoom as a flyover.

## Shared engine (use it; do not copy it)
`orbitalatlas/` (repo root; see `orbitalatlas/README.md`): `camera`, `easing`, `layers` (Scene + overlays), `transitions`, `sequence`, `timing`, `qa`, `spec`.
Run from the repo root; tests: `python3 -m unittest discover -s orbitalatlas/tests -t .`; demo: `python3 -m orbitalatlas.demo.render_demo OUT.mp4 --qa`.
Keep episode data (images, anchors, outlines, text, timings) in the episode folder; do not edit the package for one episode.
Import only what exists; features marked NOT built in `docs/ORBITALATLAS_VISUAL_MASTER.md §7` must be listed as limitations.
Transitions available in code: `Dissolve, Push, WhipPan, CinematicPush, MaskReveal, GeoFocus, ScaleMatch, DateTransition`
(`transitions.from_spec({"type": "push", ...})`). Chain them with `sequence.Sequence`; run `qa.run_video` with declared cuts/holds;
`qa.check_schedule` flags out-of-range durations and three identical transitions in a row. `ScaleMatch` needs the subject's frame position and size in both shots.
