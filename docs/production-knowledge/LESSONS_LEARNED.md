# Lessons learned (EP002, Shorts feedback, and the process)
Tags: **[VERIFIED]** observed here · **[HYPOTHESIS]** not proven · **[PROCESS]** how to work.
## Process
- **[PROCESS]** Proof first (12-41 s), user review, then scale. Every rejected version (V3 monotony, V4 clutter, V5 text overload) was caught by a proof, not by the full film.
- **[PROCESS]** Take director feedback literally and itemise it (10 points -> 10 changes); do not add new hook versions without a reason; report deviations (title lands at 39 s, not 30 s, because the narration is locked).
- **[PROCESS]** Measure instead of asserting: registration (phase correlation), monotony (frame-change metric), black/freeze/spike scans, sync error table. A number beats "looks fine".
- **[PROCESS]** Persist expensive artifacts immediately (paid TTS cache -> `media/ep002-dubai-audio` branch; Cesium frames are regenerable, ~11 min).
- **[PROCESS]** Do not call work approved/premium/cinematic; only the user sets USER_APPROVED; say what could not be verified (the agent cannot listen to audio or watch video continuously: frames/contact sheets only).
## Technical
- **[VERIFIED]** Narration-locked episodes still allow strong visual change: reorder visuals within windows, add a silent cold open, keep the text byte-identical (hash in SCRIPT_LOCK).
- **[VERIFIED]** Two clocks are needed for sync: events must fire on word starts (word-level clock), camera must move smoothly (sentence-level monotone cubic). A single sentence-level warp left 0.3 s mean / 1.3 s max cue error; a single word-level warp gives 0.2-3x speed pulses.
- **[VERIFIED]** Render at native scale by drawing text/vectors at physical resolution through a logical-coordinate proxy (`kit.SDraw`, `SC`), validated by comparing SC=1 and SC=2 frames downsampled (all 84 sampled frames within 3 mean grey levels). Do not upscale a 540p render.
- **[VERIFIED]** Text-card scenes are the monotony source; a dated filmstrip, thumbnails on a timeline and traced outlines carry the same facts with motion.
- **[HYPOTHESIS]** Retention benefit of the V6 hook is unproven (no analytics yet); measure with `/yt-retention` after publication.
- **[VERIFIED]** An automated glyph-bounds audit found 6 text defects that 3 contact-sheet reviews and the black/freeze/spike scans missed; add it to every release gate, not only the preview.
- **[VERIFIED]** A QC rule can be satisfied without fixing the problem it stands for (`audio_starts` passes with a bed although the voice starts at 3.35 s): report the measurement and the reason, never claim the underlying goal.
- **[PROCESS]** When only the audio changes, remux with `-c:v copy`; keep the previous master (v1 silent) in storage and name the new one v2.
- **[HYPOTHESIS]** The drone helps first-seconds retention; unmeasured until analytics exist.

- **[VERIFIED]** A master that passed yt-qc and three reviews still contained 8 confirmed legibility/overlap defects and 4 static holds >= 2 s; the release gate must include a contrast audit and a static-run scan, not only technical QC.
- **[PROCESS]** Each fix round costs about 25 min (re-render, mux, QC); batch the audits first, fix once, re-render only the changed scenes (diff sampled frames before/after to find them), keep the previous master as backup.
- **[VERIFIED]** The agent has no real way to check pronunciation here (no ASR, PyPI/HF blocked); report plausibility only and leave listening to the director.

## Shorts feedback (parallel track, PR #16, not merged)
Views are not independent observations; Studio and Analytics API metrics differ (engagedViews, looping clips); an exploratory 2-vs-2 design can never reach significance (minimum two-sided p = 0.33): classify as exploratory. Work is on `feature/shorts-performance-feedback`; Shorts are excluded from the current production plan.
