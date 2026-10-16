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

## V4 rebuild (2026-10-13)
- VERIFIED: the voice started at 3.35 s in v1-v3 because `sync.PREROLL=3.0 + LEAD=0.35` plus a silent 3 s "result-first" scene (H0); a drone bed hid it and yt-qc `audio_starts` (first audio > -40 dB) cannot tell speech from atmosphere. RULE: measure VOICE_START on the narration track (RMS onset) and from provider word times; never accept a bed as the fix.
- VERIFIED: the narration.mp3 itself has 0.129 s of leading silence, so the best possible onset is ~0.13 s. `EP002_V4=1` / `build_final.py --hook|--full4` places word 0 at t=0 (no pre-roll, first scene window clamped to 0, tail 1.6 s).
- VERIFIED: windows between scenes depend only on word-time differences, so unchanged scenes' segments can be reused after an offset change; only changed scenes were re-rendered (6 scenes + hook ~12 min on 4 jobs).
- VERIFIED (2026-10-13, v4.1): the director's approval of the hook froze its segments (H1-H4 copied byte for byte) and its audio (first 34 s sample-identical); later fixes only touched other scenes. Readability bugs of the same class (amber/muted text on bright imagery) appear in many scenes: fix the class with a backing pill and run `qa_contrast.py` over all scenes, not only the one reported.

## EP004 Jakarta (2026-10-16) - what to repeat and what to avoid
- Owner-selected topic with evidence limits: every on-screen number carries its measurement kind (line of sight vs vertical), period and source class; preprints/abstracts are named as such; 5 targeted script fixes beat a rewrite.
- Cost safety worked: free voice check, recorded approval, one TTS pass at 5,790/5,800 characters, cache + audio on a media branch, no retry.
- First REVIEW looked "finished" but was 69 % static and had 86 phone-size text issues: run dyn.py and mqa.py BEFORE showing a REVIEW (solutions: static-landsat-shots-camera-paths, phone-text-size-floor-clamp).
- Render REVIEW at final size with the shot cache (solutions: shot-segment-cache-incremental-render); three full renders cost ~105 min.
- GitHub media: plain files must stay < 100 MB (raw link works); put the CRF master on a Git LFS branch and derive a 2-pass copy under 95 MB for the direct link.
