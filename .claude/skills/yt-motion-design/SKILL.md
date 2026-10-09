---
name: yt-motion-design
description: >-
  OrbitalAtlas motion-design rules for any video that has animated visuals - hierarchy, easing,
  typography timed to words, colour tokens, layer classes, information density, and the mandatory
  per-scene motion storyboard. Use before storyboarding or rendering any episode, for "design the
  motion", "storyboard", "make it look premium/cinematic", or when a render looks like a slideshow.
  Not for writing the script (/yt-script) or the final mux/QC (/yt-render, /yt-qc).
---

# yt-motion-design

Read first: `docs/ORBITALATLAS_VISUAL_MASTER.md`, `docs/MOTION_DESIGN_STANDARDS.md`,
`docs/VISUAL_QUALITY_RUBRIC.md`. Brand tokens: `productions/dubai/motion/MOTION_DESIGN_SYSTEM.md §3`.

## Procedure
1. Take the locked narration + word timings (`*.voice.json`). Never call TTS. If only estimated timing
   exists, say "estimated" in the storyboard and do not promise frame sync.
2. Write the motion storyboard (fields in `MOTION_DESIGN_STANDARDS.md`). One row per beat, not per image.
   A row that is only "image + zoom" is rejected.
3. Capability check against the table in `ORBITALATLAS_VISUAL_MASTER.md §7`. Every effect must be Built
   or listed as a limitation. Do not substitute a pan/zoom for a missing effect without saying so.
4. Build a 12–15 s proof of the hardest sequence. Review frames (contact sheet + individual full-res frames).
5. Report with the status vocabulary (TECHNICALLY_VALID / VISUALLY_REVIEWED / USER_APPROVED). Stop for approval.

## Hard rules
- One hero movement per beat; ≤3 elements animating at once; hold ≥1.2 s after the last reveal.
- Text reveals on word start (provider timing), exits before the next hero; safe margin 96 px; no collisions.
- Evidence imagery is never graded/tinted; fills/dims are UI layers and are labelled as such.
- Layer classes: EVIDENCE, TRACED, MAP, ILLUSTRATION, TEXT. A component must not claim accuracy it has no data for.
- Avoid repeating the same transition/camera move 3 times in a row.
## Verify
Run the gates in `docs/VISUAL_QUALITY_RUBRIC.md`; write one evidence sentence per rubric item.
## Do not
Claim "cinematic/premium/approved" below USER_APPROVED; patch one video instead of fixing the component.
