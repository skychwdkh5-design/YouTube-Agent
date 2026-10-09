# EP002 creative preview (silent) — status 2026-10-09
Built by `build_preview.py` (kit.py, scenes.py) from the locked script (`SCRIPT_LOCK.md`, VO hash unchanged), `story_structure_v1_4.md` and `visuals/VISUAL_PRODUCTION_PLAN.md`. 28 scenes, 538 s, 960x540, 12 fps, no audio.
Build: ~120 s on 4 CPU (scenes rendered in parallel, piped to ffmpeg; Cesium A1 frames 186 x 960x540 rendered once, ~9 min including one worker re-run). Command: `python3 productions/dubai/preview/build_preview.py OUT --a1 CESIUM_A1_DIR` with `EP002_WOC` pointing to the extracted WoC frames (the script unzips them to /tmp/ep002_woc by default).
## What is real and what is a placeholder
- Real: ASTER WoC 2000-2011 frames, ASTER 2006 (palm2.jpg) crops and the ISS photo crops exactly as planned (rects from the plan); NASA GIBS globe descent in A1 (CesiumJS).
- Illustrations (labelled): B3 dredging, B4 GPS/vibroflot, C2 layouts, C6 comparison, D1 inset. Stylised, not to scale, no volumes.
- Captions: the locked VO text split into phrases and spread over each scene window at 145 words/min = ESTIMATED timing. No TTS was generated (paid, needs explicit approval); no audio exists. Provider word timings will replace the estimates.
## Decisions made autonomously
- A1 uses the real Cesium globe descent (labels anchored from the Cesium camera projection) instead of the schematic locator, then the V4 soft radial dissolve with tone matching into the ASTER-2000 start crop. The plan's schematic locator stays as a fallback.
- The V4 clip itself is NOT placed: its destination (ASTER 2006 Palm Jumeirah) would contradict the 2000 baseline of A2. The V4 method (soft Palm-centred dissolve, tone match, ring/label language) is reused.
- C4 keeps the SAFE DEFAULT (text card over ASTER 2006 The World; the ISS photo is not used there).
- Year labels moved top-right, source chips top-left on every image; evidence imagery is never graded (only the Cesium render is tone-matched).
## QA
- ffprobe (small file): h264 High, 960x540, 12 fps, 6456 frames, 538.000 s; full decode clean; blackdetect (0.15 s) none.
- `orbitalatlas.qa.run_video` flags only duplicate-frame artefacts (12 fps video resampled to 30 fps) and one intended near-black globe-on-space opening; not used as a pass/fail here.
- Visual: mid-frame contact sheets of all scenes plus A1/A1-dissolve frames reviewed; not watched frame by frame. Status VISUALLY_REVIEWED, not USER_APPROVED.
## Known limitations / blockers
- No narration audio yet: needs explicit approval for the paid ElevenLabs call (voice and `--max-chars`), then captions/timing re-synced to provider timestamps.
- A1: Cesium close frames are soft (~38 m/px); the Landsat no-data swath over the Gulf is painted deep-sea blue (UI cleanup); the descent crosses ~3 s of empty desert.
- Illustration scenes are plain (vector shapes); B3/B4 are the weakest against the references.
- Callout positions on WoC frames use coordinates read by eye (+-30 px); the same palm coordinates are reused across dates (not registered).
- E1 grid and D5 card are text-heavy; 12 fps preview motion is choppy by design.
