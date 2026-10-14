# Verified solutions (generated - do not edit)

Source of truth: `knowledge/solutions.json`. Regenerate with `python3 tools/memory/kb.py render`; `kb.py validate` checks every reference. Search before debugging: `kb.py search WORDS`, `kb.py diagnose FILE`.
Status: **VERIFIED** = observed and checked in this repo; **HYPOTHESIS** = plausible, not proven.

## tts

### free-test-voice-measured-timing - Free test narration with measured word timestamps (ffmpeg flite)
*VERIFIED · general · 2026-10-14*

- **Problem:** Synchronisation, captions and motion must be tested without spending TTS credits; estimated timing proves nothing about sync.
- **Root cause:** A single flite pass has no word timestamps and 'estimated' timing is not frame accurate.
- **Fix:** orbitalatlas.testvoice.synth speaks each word separately (ffmpeg -f lavfi flite, atempo 1.45), concatenates with small gaps and records the measured start/end (source 'alignment'); numbers use a 'say' spelling. The voice is robotic and is NOT the channel voice. testvoice.envelope gives real loudness for Waveform.
- **Reuse when:** Any sync/caption/motion proof before the paid narration exists.
- **References:** `orbitalatlas/testvoice.py`; `docs/references/library/UNIFIED_STYLE_GUIDE.md`
- **Verification:** test: gaps between words are quiet and words are loud in the audio that was made; cache makes reruns identical; 41 words = 18.5 s.
- **Regression test:** `orbitalatlas/tests/test_visual_v2.py::test_word_times_match_the_audio_that_was_made`

### paid-tts-gate-in-the-calling-function - The paid-request wall must live in the code that makes the request
*VERIFIED · general · 2026-10-14*

- **Problem:** A text hook that matches `voice.py --confirm` is bypassed by any alternative path: another script, python -c, an import of voice.generate, a different shell wrapper.
- **Root cause:** Hooks see command text, not behaviour; the paid call itself had no check.
- **Fix:** yt-voice approval_gate() runs inside generate(): it needs approvals.json (found next to or above the output) with approved_by 'user', the owner's quote and max_chars >= the plan, else it refuses before any request. The hook stays as a second layer.
- **Reuse when:** Any new paid or irreversible action: put the check in the function that performs it, then add a hook as a safety net.
- **References:** `.claude/skills/yt-voice/voice.py`; `tools/autopilot/guard.py`; `tools/autopilot/orbital.py`
- **Verification:** 5 tests: no file, unapproved, agent-approved, too small budget, direct generate() call - none sends a request; found-above-output path works.
- **Regression test:** `.claude/skills/yt-voice/test_voice.py::test_calling_generate_directly_is_gated_too`

### pronunciation-check-unavailable - Pronunciation cannot be verified in the cloud container (no ASR)
*VERIFIED · general · 2026-10-15*

- **Problem:** Owner asked to verify Gunnison, Gilbert, Farmington, Saltair, Newfoundland, GRACE, methyl mercury.
- **Root cause:** No local ASR model; pypi.org and huggingface.co are denied by the egress policy (2026-10-15), so whisper/vosk cannot be installed.
- **Fix:** List exact timecodes for the owner to listen; use word durations from the provider alignment as indirect evidence only (spelled acronyms take > 1 s; GRACE 0.30 s = spoken as a word). Never report pronunciation as verified.
- **Reuse when:** Any narration with names or acronyms.
- **References:** `productions/ep003-great-salt-lake/voice/narration.voice.json`; `docs/production-knowledge/TTS_ELEVENLABS.md`
- **Verification:** pip download faster-whisper / vosk: no distribution; curl huggingface.co: connect_rejected. Re-checked 2026-10-15: ffmpeg has the 'asr' (pocketsphinx) filter and libpocketsphinx is installed, but no acoustic model; apt (archive.ubuntu.com not resolvable), pypi and huggingface are unavailable.
- **Regression test:** none - measurement / environment fact, not code

### rebuild-paid-narration-from-saved-responses - Paid narration can be rebuilt for free from the saved provider responses
*VERIFIED · EP001 · 2026-10-14*

- **Problem:** EP001's final master and WAV were lost with the container; re-voicing would cost ~10,500 credits again.
- **Root cause:** The WAV and word timings are derived locally; only the provider responses (audio + alignment) are paid, and they were committed (7 cache files).
- **Fix:** tools/autopilot/recover_narration.py splits the recorded text by the recorded chunk sizes (chunks are joined by a blank line), matches each chunk to its cache entry by alignment text (both cache layouts), and rebuilds with yt-voice's own to_wav/join_wavs. Result is compared with the recorded audio_sha256.
- **Reuse when:** After any container loss or whenever a WAV is missing but voice/cache and narration.voice.json exist.
- **References:** `tools/autopilot/recover_narration.py`; `tools/autopilot/archive.py`; `production/ep001-sahara-green:productions/sahara-green/narration/voice/narration.voice.json`; video: EP001 Sahara Green narration 747.357 s, wav sha256 49e53528cd44...
- **Verification:** Run on the real EP001 cache: 7/7 chunks matched, WAV byte-identical to the recorded sha256 49e53528...; the normalised -16 LUFS file also reproduced byte-identical (114ba576...) with the EP001 script.
- **Regression test:** `tools/autopilot/test_archive.py::test_rebuild_from_cache_in_both_layouts_is_byte_identical`

### tts-blank-lines-are-billable - Paragraph blank lines add billable characters
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** The same EP002 script cost 7,025 characters with blank-line paragraphs and 6,998 with single newlines; --max-chars fired although the words were right.
- **Root cause:** yt-voice bills the exact spoken text including newlines.
- **Fix:** Plan without --confirm and compare layouts; use single newlines when the budget is tight. tts_plan reports blank_line_chars.
- **Reuse when:** Budget-sensitive paid runs, and whenever a plan is over --max-chars by a small margin.
- **References:** `tools/autopilot/orbital.py`; `docs/production-knowledge/TTS_ELEVENLABS.md`
- **Verification:** Observed on the EP002 script; verified here again 2026-10-14: a 2-paragraph sample is 36 chars, 35 when collapsed.
- **Regression test:** `tools/autopilot/test_autopilot.py::test_tts_plan_caps_chunks_and_flags_blank_line_cost`

### tts-gateway-502-chunk-size - Paid TTS request cut by the ~30 s gateway and billed anyway
*VERIFIED · EP001 · 2026-10-08*

- **Problem:** EP001 narration request 2 (2,484 characters) failed twice with HTTP 502 and both failed requests were billed (2,186 credits lost of 6,808 total).
- **Root cause:** The egress gateway cuts a request at about 30 s. 2,484 characters is more than 30 s of synthesis; ElevenLabs had already started billing. (EP002 later passed chunks of 2,470-2,479 characters through a different session, so the limit is environment-dependent, not a constant.)
- **Fix:** Resplit to chunks of at most 1,700 characters (--max-chunk-chars 1700, 1,679 characters = 20-31 s passed). Autopilot plans and enforces 1,700 unless the owner approves a larger chunk after a free probe.
- **Reuse when:** Any paid TTS run from a cloud session, and every time the chunk size is not already proven in the current environment.
- **References:** `tools/autopilot/orbital.py`; `tools/autopilot/gates.py`; commit `1527ea2`; commit `19911e7`; `production/ep001-sahara-green:productions/sahara-green/narration/TTS_STATUS.md`; `production/ep001-sahara-green:productions/sahara-green/narration/voice/ledger.json`; video: EP001 Sahara Green narration, 747.357 s, 1,778 words timed
- **Verification:** EP001 narration complete in 7 requests with no further 502; usage-stats delta matched the character-cost header for every paid request. Autopilot test checks the cap.
- **Regression test:** `tools/autopilot/test_autopilot.py::test_tts_plan_caps_chunks_and_flags_blank_line_cost`

### tts-key-injected-by-egress-proxy - ElevenLabs key is not in the environment; the proxy injects it
*VERIFIED · general · 2026-10-07*

- **Problem:** voice.py refused to run: ELEVENLABS_API_KEY missing, although the session is connected to ElevenLabs.
- **Root cause:** In cloud sessions the egress proxy adds the credential to api.elevenlabs.io requests; there is no key variable.
- **Fix:** Run with --auth proxy (or YT_VOICE_AUTH=proxy). The balance endpoint may be unreadable (key lacks user_read): reconcile spending from the character-cost response header and /v1/usage/character-stats.
- **Reuse when:** Any cloud session that has the ElevenLabs connector.
- **References:** `.claude/skills/yt-voice/voice.py`; `tools/autopilot/orbital.py`; commit `470adff`; commit `17c2c55`
- **Verification:** EP001 ledger reconciled 6,808 credits against usage-stats deltas; orbital.py picks --auth proxy automatically when no key variable exists.
- **Regression test:** `.claude/skills/yt-voice/test_voice.py::test_proxy_auth_sends_no_key_and_needs_no_env`

### tts-no-blind-retry - After a paid error check credits and cache before any rerun
*VERIFIED · general · 2026-10-13*

- **Problem:** An automatic retry after a provider error can pay twice for the same audio (EP001: two failed requests were both billed).
- **Root cause:** A failed request may already have been billed; the response gives no proof either way.
- **Fix:** Paid stages are never retried automatically. After an error: read the ledger and voice/cache/, check the usage stats, only then rerun (the cache makes the rerun pay only what is missing).
- **Reuse when:** Any paid API stage.
- **References:** `tools/autopilot/orbital.py`; `docs/production-knowledge/TTS_ELEVENLABS.md`; `production/ep001-sahara-green:productions/sahara-green/narration/TTS_STATUS.md`
- **Verification:** orbital.py executes the tts stage with a single attempt and attaches this warning to the failure record.
- **Regression test:** `tools/autopilot/test_autopilot.py::test_non_transient_failure_and_paid_stages_are_not_retried`

### tts-persistent-chunk-cache - A failure in chunk 2 must never force paying chunk 1 again
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** A paid multi-chunk narration lost already-paid audio when a later chunk, an alignment mismatch or an ffmpeg step failed.
- **Root cause:** yt-voice kept chunk responses only in memory until the whole run succeeded.
- **Fix:** yt-voice --cache-dir stores every paid chunk (audio + alignment, never the key) the moment it succeeds; a rerun pays only missing chunks. Copy the cache to the media/<episode>-audio branch right after the run.
- **Reuse when:** Every paid TTS run. Never change text, voice, model, settings or --context between a run and its rerun: any change is a new cache key and a new charge.
- **References:** `.claude/skills/yt-voice/voice.py`; `docs/production-knowledge/TTS_ELEVENLABS.md`; `productions/dubai/TTS_PLAN.md`; commit `44696bd`; video: EP002 Dubai narration, 515.25 s, 1,225/1,225 words timed
- **Verification:** yt-voice unit test: a failure in the second chunk, then a rerun, pays only the missing chunk. EP002 narration (6,998 chars) paid once.
- **Regression test:** `.claude/skills/yt-voice/test_voice.py::test_cache_saves_paid_chunk_after_failure_and_rerun_pays_only_missing`

## sync

### caption-cards-overlapped-by-lead - Word captions: the next card's lead time overlapped the previous card's tail
*VERIFIED · general · 2026-10-14*

- **Problem:** Two caption cards were active for a few frames at once when words were close together.
- **Root cause:** The card end was clamped to next.t0 - 0.02 while the next card appears lead (0.05 s) early, and a minimum display time pushed the end past the next start.
- **Fix:** ends = min(max(end, t1 + 0.05), next.t0 - lead - 0.005); a unit test samples every 0.05 s and asserts at most one active card.
- **Reuse when:** Any overlay that shows items with a lead-in and a minimum duration.
- **References:** `orbitalatlas/captions.py`; `docs/references/library/UNIFIED_STYLE_GUIDE.md`
- **Verification:** found by test_no_two_captions_at_once, fixed, test passes; demo captions never stack.
- **Regression test:** `orbitalatlas/tests/test_visual_v2.py::test_no_two_captions_at_once`

### captions-from-provider-word-times - Captions must come from provider word timings, never from estimates
*VERIFIED · general · 2026-10-07*

- **Problem:** Captions built from sentence estimates drift against the voice and can overlap.
- **Root cause:** Estimated timings are guesses; overlapping cues are rejected by players.
- **Fix:** yt-captions builds phrase-sized cues from yt-voice word timings, checks wording_preserved / no_overlaps / timestamps_valid; the autopilot captions gate requires all three.
- **Reuse when:** Every episode.
- **References:** `.claude/skills/yt-captions/captions.py`; `tools/autopilot/gates.py`; commit `ba56ed1`
- **Verification:** 28 yt-captions tests; EP001 185 cues and EP002 228 cues validated against the locked text word for word.
- **Regression test:** `.claude/skills/yt-captions/test_captions.py::test_no_overlaps_and_increasing`

### two-clocks-for-sync - Events on word starts, camera on a smooth clock
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** One sentence-level time warp left 0.3 s mean / 1.3 s max cue error; one word-level warp gave 0.2-3x speed pulses in camera moves.
- **Root cause:** Discrete events and continuous motion need different time maps.
- **Fix:** Use a word-level event clock (events fire exactly at word starts) and a smooth monotone-cubic sentence-level camera clock (productions/dubai/preview/sync.py).
- **Reuse when:** Narration-locked episodes with camera moves on the Dubai scene engine.
- **References:** `productions/dubai/preview/sync.py`; `docs/production-knowledge/AUDIO_SYNC.md`; commit `2327c62`
- **Verification:** EP002 sync table: events exact at word starts by construction; caption onsets vs speech: 159/228 matched, mean +0.020 s, max 0.125 s.
- **Regression test:** none - Needs rendered scenes and real narration; verified by the episode's own sync table, not by a unit test.

### voice-onset-measured-on-narration - A sound bed hid a voice that started at 3.35 s
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** EP002 v1-v3 started the voice at 3.35 s (PREROLL 3.0 + LEAD 0.35 plus a silent 3 s scene) but yt-qc audio_starts passed once a drone bed was added.
- **Root cause:** audio_starts measures the first audio above -40 dB, not speech; a bed satisfies the rule without changing when the voice starts.
- **Fix:** Measure the onset on the narration track (RMS onset) and from provider word times. The tts gate fails a voice later than 1.0 s. For EP002 v4: word 0 at t=0, narration.mp3 itself has 0.129 s leading silence.
- **Reuse when:** Every episode with a cold open, a pre-roll or any audio bed.
- **References:** `tools/autopilot/gates.py`; `productions/dubai/preview/sync.py`; `docs/production-knowledge/AUDIO_SYNC.md`; commit `f222902`; video: EP002 v4.1 hook 0-34 s
- **Verification:** EP002 V4/V4.1: voice from t=0; autopilot test measures a 3.35 s synthetic silence as 3.35 s and fails the gate.
- **Regression test:** `tools/autopilot/test_autopilot.py::test_late_voice_fails_the_tts_gate`

## render

### audio-only-change-remux-copy - When only audio changes, remux with -c:v copy
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** Re-encoding video for a pure audio fix costs ~25 min and changes pixels.
- **Root cause:** The whole build was rerun for an audio-only change.
- **Fix:** ffmpeg -c:v copy remux; keep the previous master as backup and name the new one v2.
- **Reuse when:** Audio-only fixes (mix, loudness, bed).
- **References:** `docs/production-knowledge/LESSONS_LEARNED.md`; commit `a9d0551`
- **Verification:** EP002 v2 delivered by remux.
- **Regression test:** none - Process rule; no deterministic check.

### cesium-capture-slow-and-tile-race - Cesium globe capture took 90 s per frame; tile cache raced
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** Capturing the GIBS globe descent was unusably slow and sometimes read half-written tiles.
- **Root cause:** Global-layer minimumLevel / force-render loop; non-atomic .ct writes in the tile server.
- **Fix:** Use run_frames_fast.js (3 workers, DSF 1.5-2: ~11 min for 372 frames) and the atomic write order in tools/cesium_proof/server.py.
- **Reuse when:** Any Cesium/GIBS capture.
- **References:** `tools/cesium_proof/run_frames_fast.js`; `tools/cesium_proof/server.py`; `docs/production-knowledge/RENDERING.md`
- **Verification:** EP002 A1 globe: 372 frames at 1920x1080 in 10.7 min.
- **Regression test:** none - Needs a browser and network access to jsdelivr and GIBS.

### crop-box-leaves-source - Image.resize(box=...) with a crop rect outside the source
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** ValueError: box offset can't be negative from Image.resize when a crop rectangle leaves the source image.
- **Root cause:** Rounding, or a panel so narrow that the box height exceeds the image.
- **Fix:** kit.view snaps offsets under 2 px; scenes_v6.fit limits the box to 98 % of the source; clamp rects with clampr. orbitalatlas camera clamps the rotated window inside the image; yt-render clamps still views (EP001 be555aa).
- **Reuse when:** Any crop-from-source render.
- **References:** `orbitalatlas/camera.py`; `productions/dubai/preview/kit.py`; commit `be555aa`; commit `89559f0`
- **Verification:** orbitalatlas clamp test; EP001 timeline builder clamps still views inside the image.
- **Regression test:** `orbitalatlas/tests/test_engine.py::test_clamp_keeps_rotated_window_inside_image`

### director-camera-leaves-image - Black strip at the frame edge on wide moves
*VERIFIED · general · 2026-10-14*

- **Problem:** EP003 at 1:48: a black strip on the right edge while the camera moved from the whole-lake view to a close view.
- **Root cause:** The director built scenes with clamp=False, so an eased pan/zoom could leave the image.
- **Fix:** director scenes use clamp=True (the camera keeps the rotated window inside the image).
- **Reuse when:** Every director render.
- **References:** `orbitalatlas/director.py`; `docs/production-knowledge/VISUAL_ENGINE_BASELINE.md`
- **Verification:** EP003 still at 108 s has no black edge after the change.
- **Regression test:** none - needs a full camera path over a real stack; verified on EP003 frames

### loudness-two-pass-and-int-sample-mix - Level narration with one constant gain; mix beds in integer samples
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** Mixing a bed changed the narration by 1 LSB (float round trip) and a one-pass loudnorm missed -16 LUFS; ebur128 output was not on stderr.
- **Root cause:** x/32768 then x*32767 is not lossless; loudnorm needs measurement before correction.
- **Fix:** Two-pass loudnorm (target -16 LUFS, -1.5 dBTP); add integer samples to the original int16 array and assert mix - bed == narration; read ametadata r128.M from stdout.
- **Reuse when:** Any audio assembly.
- **References:** `productions/dubai/preview/build_final.py`; commit `89559f0`; `production/ep001-sahara-green:productions/sahara-green/production/audio_normalization_test.py`
- **Verification:** EP002: -16.22 LUFS, -1.50 dBTP, LRA 2.9; EP001 audio_normalization_test.py compared alternatives.
- **Regression test:** none - Verified by measurement on episode audio (needs real narration).

### native-scale-render-no-upscale - Never render at 540p and upscale
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** A 960x540 preview upscaled to 1080p breaks the no-upscale rule and softens text.
- **Root cause:** Text and vectors drawn at logical resolution then scaled.
- **Fix:** Draw text/vectors at physical resolution through the logical-coordinate proxy (kit.SDraw, EP002_SCALE=2); crop images from the source at output size.
- **Reuse when:** Any render built on productions/dubai/preview/kit.py.
- **References:** `productions/dubai/preview/kit.py`; `docs/production-knowledge/RENDERING.md`; commit `319203a`
- **Verification:** SC=1 vs SC=2 frames downsampled: 84 sampled frames within 3 mean grey levels.
- **Regression test:** none - Equivalence was measured on rendered frames of EP002 scenes (needs the full scene set).

### no-4k-no-upscale - No 4K master without a native 4K source path
*VERIFIED · EP001 · 2026-10-09*

- **Problem:** EP001 4K was requested but graphics are 1920x1080 and the NASA clip is 1080p.
- **Root cause:** No native 4K path in compose; upscaling violates the no-upscale rule.
- **Fix:** Deliver the 1080p master; state that 4K was not produced and why; upscale only with explicit approval.
- **Reuse when:** Any 4K request.
- **References:** commit `b79e1f8`; `production/ep001-sahara-green:productions/sahara-green/final/FINAL_REPORT.md`
- **Verification:** EP001 final report states 4K NOT produced.
- **Regression test:** none - Policy decision, nothing to test.

### opening-tilt-then-move - Plane tilt and a fast camera move at the same time smear the opening
*VERIFIED · general · 2026-10-14*

- **Problem:** The opening plane tilt ran together with a snap zoom: the tilted map was a motion-blur smear.
- **Root cause:** Two moves overlapped in the first 1.7 s.
- **Fix:** Director holds the first shot's camera until the plane has landed (keys shifted by 1.6 s) and shifts the declared fast-move window and its whoosh accordingly.
- **Reuse when:** Any opening that combines PlaneTilt with a camera move.
- **References:** `orbitalatlas/director.py`; `docs/references/library/REFERENCE_COMPARISON.md`
- **Verification:** frames at 0.5 and 1.2 s are sharp in the re-render.
- **Regression test:** none - judged on rendered frames

### pil-float-width - Float width in ImageDraw raises TypeError
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** TypeError: float object cannot be interpreted as an integer in ImageDraw.ellipse/line.
- **Root cause:** Pillow wants integer line widths.
- **Fix:** Pass width=int(round(w)); the SDraw/SS wrappers round widths.
- **Reuse when:** Any Pillow drawing with computed widths.
- **References:** `productions/dubai/preview/kit.py`; commit `89559f0`
- **Verification:** Fixed in kit.SDraw; EP002 renders ran clean.
- **Regression test:** none - One-line wrapper behaviour inside the episode-specific kit.

### resumable-segments-part-rename - Parallel renders must write .part files and rename
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** A parallel batch that aborted left a truncated mp4 that later looked finished (frozen scene).
- **Root cause:** Workers wrote final names directly.
- **Fix:** Write seg/<ID>.part.mp4, rename on success; reruns skip existing segments; delete only changed segments to re-render (windows depend only on word-time differences).
- **Reuse when:** Any multi-process render; yt-render long profile does the same with segment sha256 in its manifest.
- **References:** `productions/dubai/preview/build_final.py`; `tools/autopilot/orbital.py`; `docs/production-knowledge/RENDERING.md`
- **Verification:** EP002 v4.1: only 8 changed scenes re-rendered (~25 min with 4 jobs).
- **Regression test:** none - Atomic rename pattern is also tested generically in yt-render's output tests; build_final.py itself has no unit test.

### segment-splice-instead-of-full-rerender - Fix one card without a 48-minute re-render: render the shot, splice the frames
*VERIFIED · general · 2026-10-15*

- **Problem:** After the EP003 V2 render one number card still read '39 % SINCE'; a full director re-render costs about 48 minutes.
- **Root cause:** The fix touched one overlay inside one shot; the rest of the video is byte-for-byte the same decision set.
- **Fix:** director render SLUG seg.mp4 --start A --end B renders the whole shot(s) overlapping [A,B] from the shot start (report t_offset). Compare seg frames with the master outside the changed window (mean abs diff ~0.5 = identical content; the first ~0.6 s differ because no transition leads into the segment). Encode three parts separately with identical x264 settings (master 0..N1, seg window, master from N2 via -ss + trim), join with the concat demuxer (-c copy) and mux the master audio unchanged. Never split one input twice in a filtergraph: ffmpeg buffered the second branch and was OOM-killed.
- **Reuse when:** A late fix that changes only a few seconds of a long render.
- **References:** `orbitalatlas/director.py`; `docs/production-knowledge/RENDERING.md`
- **Verification:** EP003 V2: 1.6 min segment render + ~10 min encode instead of 48 min; boundary frames checked against the master.
- **Regression test:** none - procedure measured on EP003

### snap-zoom-blur-smear - Full camera motion blur on a fast snap zoom smears the whole frame
*VERIFIED · general · 2026-10-14*

- **Problem:** A x2.4 snap zoom in 0.55 s rendered as an unreadable smear (EP003 automatic run, 6.0 s).
- **Root cause:** Scene motion blur samples scale with apparent speed (up to 16 sub-frames).
- **Fix:** Director scenes use max_blur_samples=6 and blur_threshold=10 and snap zooms of 0.7 s; QA receives the deliberate fast-move frames as declared changes (report.intended_changes).
- **Reuse when:** Fast camera presets on large images.
- **References:** `orbitalatlas/director.py`; `orbitalatlas/layers.py`; `docs/references/library/REFERENCE_COMPARISON.md`
- **Verification:** re-rendered frames at 5.8/6.2 s are readable; QA passes with the declared changes.
- **Regression test:** none - needs rendered video / repository state, checked on frames

### sound-design-synthesised-ducked - Sound design: original synthesised effects, cue plan from the director, ducked under the narration
*VERIFIED · general · 2026-10-14*

- **Problem:** The demos had no sound design; free libraries need licence checks and some hosts are blocked here.
- **Root cause:** No audio layer besides narration.
- **Fix:** orbitalatlas.sfx synthesises whoosh, sweep, impact, rise, ui_blip, tick (original, CC0 with the code, no attribution); plan_cues maps director decisions to effects with a 0.25 s minimum gap and priorities; mix ducks effects 8 dB while words are spoken and caps them 12 dB under the local voice level, then loudnorm to -16 LUFS; director --sfx writes OUT.mix.wav and reports the measured margin.
- **Reuse when:** Any render that needs transitions/impacts to be heard.
- **References:** `orbitalatlas/sfx.py`; `orbitalatlas/director.py`; `docs/ASSET_SOURCE_REGISTRY.md`
- **Verification:** ep901: 11 cues, effects >= 14.4 dB under the voice (5th percentile while speaking), -15.7 LUFS, voice offset in the mix 0.0 s.
- **Regression test:** `orbitalatlas/tests/test_visual_v2c.py::test_mix_keeps_effects_well_under_the_voice`

### xfade-shortens-timeline - ffmpeg xfade between segments shortens the timeline and breaks sync
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** Joining scene segments with xfade shortened the total and desynchronised the word map.
- **Root cause:** xfade overlaps clips, subtracting the overlap from the duration.
- **Fix:** Join segments with the concat demuxer (no re-encode); put dissolves inside the scene renderer.
- **Reuse when:** Any segmented render with a fixed narration timeline.
- **References:** `.claude/skills/yt-render/render.py`; `docs/production-knowledge/RENDERING.md`
- **Verification:** yt-render crossfade test shows the total shortens by the overlap; long profile joins by concat copy and verifies the frame count.
- **Regression test:** `.claude/skills/yt-render/test_video.py::test_crossfade_shortens_the_total_and_keeps_clean_frames_outside_the_overlap`

## qc

### black-frame-near-empty-card - A dark card with nothing drawn trips blackdetect
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** yt-qc black_frames flagged 0.3-0.5 s at the start of card scenes, and a dark navy card with a few elements is still >= 98 % dark.
- **Root cause:** blackdetect counts a frame black when >= 98 % of pixels are under ~10 % luma.
- **Fix:** Lift the card background (mean Y about 31), put content in frame 0, enter by dissolve, no fade-to-black credits. EP001: never a title-only dark step.
- **Reuse when:** Any text-card or graphic scene.
- **References:** `.claude/skills/yt-qc/qc.py`; commit `dab03c0`; commit `e5f168d`
- **Verification:** yt-qc black-frame test; EP002 final black_frames PASS; EP001 commit dab03c0 re-timed g19/g23/g32/g34.
- **Regression test:** `.claude/skills/yt-qc/test_qc.py::test_black_frames_and_manifest_failures`

### caption-count-up-showed-wrong-numbers - Count-up inside subtitles showed numbers that were never spoken
*VERIFIED · general · 2026-10-14*

- **Problem:** Style D captions counted 0 -> 4,190.2, so a frame read 'it measured 4,062.3'.
- **Root cause:** An animation meant for a graphic was applied to a subtitle, which must match the narration.
- **Fix:** No count-up in captions; count-up only in NumberCard, which settles on the exact string and is the focus element.
- **Reuse when:** Any animated number inside subtitles.
- **References:** `orbitalatlas/captions.py`; `orbitalatlas/typeset.py`; `docs/references/library/UNIFIED_STYLE_GUIDE.md`
- **Verification:** found on a frame of the EP003 automatic render, fixed, regression test.
- **Regression test:** `orbitalatlas/tests/test_visual_v2b.py::test_style_d_never_shows_an_intermediate_number`

### freeze-on-static-card - Static cards trip freezedetect
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** freezedetect flagged 2 s windows on card scenes; EP001 had 16 static graphic intervals of 4.0-4.7 s and a 48.7 s water-balance graphic.
- **Root cause:** A card with no moving element between narrated events.
- **Fix:** Add a slow push or a moving element, or one more build step tied to the next narrated phrase. Accept only declared holds. The whole-frame metric is blind to small movers (scan lines, counters): a residual flag is evidence to look, not proof.
- **Reuse when:** Graphic-heavy sections.
- **References:** `docs/production-knowledge/QUALITY_CONTROL.md`; commit `614f0ed`; `production/ep001-sahara-green:productions/sahara-green/review/pre_final/RETENTION_RISK_REPORT.md`
- **Verification:** EP001 pre-final retention report ranked the gaps; EP002 v3 static runs: E6 credits 14.1 s by design, D5 5.5 s fixed with a scan line.
- **Regression test:** none - Metric is computed on rendered video; no fixture-sized test.

### low-contrast-text-on-bright-imagery - Amber/muted text unreadable on sand, ice or cloud
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** Contrast 1.1-2.9:1 on sand/ice/cloud (D2 labels, H2 ticks, callouts); 11 px disclosure chips.
- **Root cause:** No backing behind the text; stacked muted text on busy imagery.
- **Fix:** Dark pill/backing behind text, minimum 12 px at 540p, fix the class of defect across all scenes, then run qa_contrast.py / qa_legibility.py (WCAG 3.0 for >=18 px, 4.5 otherwise).
- **Reuse when:** Any text over imagery.
- **References:** `productions/dubai/preview/qa_contrast.py`; `productions/dubai/preview/qa_legibility.py`; `docs/production-knowledge/QUALITY_CONTROL.md`; commit `94024ff`; commit `ca2b355`
- **Verification:** EP002 v4.1: 0 runs below 4.5:1 in hook + A1 after the fix; EP001 added a dark credit pill and a top scrim for labels.
- **Regression test:** `.claude/skills/yt-render/test_compose.py::test_scrim_darkens_the_top_for_labels_only`

### mobile-readability-qa - MOBILE_READABILITY_QA: automatic phone-readability check for every director render
*VERIFIED · general · 2026-10-15*

- **Problem:** Text sizes, outline widths and contrast were judged on desktop frames; on a 6.1-inch phone dates and legends were 3-6 pt and outlines vanished (EP003 V2).
- **Root cause:** No measurement of real font sizes or of what the viewer's phone shows.
- **Fix:** orbitalatlas/textrec.py records every string drawn by kinetic.draw_text, text.plate, typeset.put (settled filled words) and tilt/pop tiles (final screen box) with font px, box, colour and the overlay class. orbitalatlas/mobile_qa.py renders 1 frame/s of the director programme and checks: text >= 30 px at 1080p (6.1 pt portrait inline / 10.9 pt landscape), captions >= 48 px, title-safe frame (3.5 % x, 4 % y), no text box over a caption, no two overlays' texts overlapping, WCAG contrast >= 3:1 of the text colour against the median non-text pixels of the box grown by 6 px (skipped when the text is not visible in the final frame), thin outline width >= 4.5 px measured on a synthetic edge. human_checks lists what needs a person. orbital.py qc runs it (qc/mobile_qa.json) and the qc gate fails on it. Contrast is measured on settled text only (alpha >= 0.9: 0.1 s caption fades are not reading time); a KeywordLift word in flight (< 1 s) is not recorded, its landed label is. Caption band ends are 1.8x padded so the blur never thins the band under the first or last word.
- **Reuse when:** Every director episode (automatic in the qc stage).
- **References:** `orbitalatlas/mobile_qa.py`; `orbitalatlas/textrec.py`; `tools/autopilot/orbital.py`; `tools/autopilot/gates.py`; `docs/production-knowledge/QUALITY_CONTROL.md`
- **Verification:** EP003 V3 build: sampled ranges clean after the fixes; the first contrast method (non-text = far from the text colour) skipped exactly the low-contrast case and was caught by its own unit test. Full EP003 run at 2 fps (745 frames) before the last fix: 2 single-frame fade cases only; 'SALT LAKE CITY' flagged in flight (2:14.5), readable once landed.
- **Regression test:** `orbitalatlas/tests/test_mobile_qa.py::test_contrast_low_on_bright_ground_and_skipped_when_covered`

### overlap-between-layers-needs-eye - Frame-bounds audit cannot see layer-on-layer overlap
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** H2 timeline backing covered the date label; A3 schematic caption was wider than its panel; qa_text_bounds was clean.
- **Root cause:** The audit tests the frame edge only.
- **Fix:** Look at changed scenes at 540p after every fix; one main label per beat; keep backing right edge left of the date start.
- **Reuse when:** After any label or backing change.
- **References:** `docs/production-knowledge/QUALITY_CONTROL.md`; commit `433a655`
- **Verification:** Found in the v3 release gate by review.
- **Regression test:** none - Needs human or agent looking at frames; by definition not automatable with the current audits.

### qc-expected-duration-from-video - Use the video duration for yt-qc --expected-duration
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** The 'muxed' print shows the audio length (+1 s pad) and does not match the video.
- **Root cause:** The video length is the sum of segments; audio is padded.
- **Fix:** Pass the video duration (516.77 s for EP002) as --expected-duration, or --timeline.
- **Reuse when:** Manual yt-qc runs.
- **References:** `docs/production-knowledge/RENDERING.md`; commit `88b18e1`
- **Verification:** EP002 yt_qc_v41 PASS.
- **Regression test:** none - Usage note; orbital.py always passes --timeline.

### silent-proof-fails-yt-qc-by-design - A short silent proof always 'fails' yt-qc long: read which checks failed
*VERIFIED · general · 2026-10-14*

- **Problem:** yt-qc --profile long reports FAIL for a 20 s silent proof.
- **Root cause:** long_duration (60-900 s), loudness and audio_starts cannot pass without narration and full length.
- **Fix:** Treat those three as expected for proofs, list them, and look at the remaining checks (black frames, freezes, decode); a proof is judged by its frames, not by the QC verdict.
- **Reuse when:** Every 12-20 s proof render.
- **References:** `.claude/skills/yt-qc/qc.py`; `docs/AUTOPILOT.md`
- **Verification:** EP003 proof: fails were long_duration, loudness (silent), audio_starts; freezes warn 3.07 s (a number card).
- **Regression test:** none - Interpretation of an existing tool's output.

### subtitle-vs-graphic-overlap-check - Burned-in captions collided with on-screen graphics and NASA's own text
*VERIFIED · EP001 · 2026-10-09*

- **Problem:** Captions overlapped graphic elements and a NASA clip's own text lines.
- **Root cause:** Captions are drawn last in the low band; graphics and third-party clips use that band too.
- **Fix:** check_subtitle_overlap(_full).py tests every cue against every element box (EP001: 9 cues / 47 pairs in the opening, then the whole film); move captions to the upper band during the NASA CALIPSO clip.
- **Reuse when:** Long timelines with graphics or third-party video that carries its own text.
- **References:** commit `a92f0d6`; `production/ep001-sahara-green:productions/sahara-green/production/check_subtitle_overlap_full.py`; `production/ep001-sahara-green:productions/sahara-green/production/check_subtitle_overlap.py`; video: EP001 Sahara Green, CALIPSO clip, captions in the upper band
- **Verification:** EP001 final delivery: full subtitle-overlap validation, no overlaps.
- **Regression test:** none - Checker lives on the EP001 branch and is episode-specific (reads that timeline); port it into yt-qc when a second episode needs it.

### text-clipped-at-frame-edge - Labels cut at the frame edge
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** Callout labels clipped (C1, D1, B3), a label ran off-frame (D5), a label for an off-screen landmark overlapped a header (E5).
- **Root cause:** Left-anchored callouts near the edge; landmarks outside the frame still got labels.
- **Fix:** kit.Canvas.callout clamps text to a 24 px margin and the 96..H-90 band, skips off-frame landmarks, strokes dark; audit with qa_text_bounds.py on final frames, not previews. orbitalatlas places anchors inside the safe frame.
- **Reuse when:** Any scene with text.
- **References:** `productions/dubai/preview/qa_text_bounds.py`; `productions/dubai/preview/kit.py`; `orbitalatlas/qa.py`; `docs/production-knowledge/QUALITY_CONTROL.md`; commit `be9a828`
- **Verification:** qa_text_bounds found 6 defects that 3 contact-sheet reviews and the black/freeze/spike scans missed; orbitalatlas test keeps anchors in the safe frame.
- **Regression test:** `orbitalatlas/tests/test_qa.py::test_anchor_must_stay_in_safe_frame`

### video-frame-accuracy-check - Video shots must be frame-exact
*VERIFIED · EP001 · 2026-10-08*

- **Problem:** Native video clips in the long timeline risked off-by-frames trims against the narration.
- **Root cause:** Timestamp seeking vs frame-count decoding.
- **Fix:** Trim video clips frame-exactly at the 30 fps policy and verify with check_frame_accuracy.py (frame-count decoding).
- **Reuse when:** Timelines with type 'video' clips.
- **References:** commit `fdf50d7`; commit `82855c7`; `production/ep001-sahara-green:productions/sahara-green/production/check_frame_accuracy.py`; video: EP001 NASA CALIPSO dust clip
- **Verification:** EP001 master: frame accuracy ALL OK.
- **Regression test:** none - Checker is on the EP001 branch, needs the rendered master; yt-render video tests cover the trim logic.

### viewer-reencodes-files - Chat/file viewers show a re-encoded copy
*VERIFIED · general · 2026-10-13*

- **Problem:** A 960x540 / 24 fps file looked like 910x512 / 30 fps in the viewer.
- **Root cause:** The viewer transcodes.
- **Fix:** Compare SHA-256 of the original; never claim identity of a viewed copy.
- **Reuse when:** Whenever a file is reviewed through a viewer.
- **References:** commit `89559f0`; `production/ep001-sahara-green:productions/sahara-green/final/SHA256.txt`
- **Verification:** SHA-256 recorded for every EP001/EP002 master. EP003 V2 (2026-10-15): a 1280x720 / 27,163,742-byte file (sha256 bb1d5d6b...) was reported by the owner as 910x512 / 228 MB; no such file exists in the container or on media/* branches - the viewer copy is a re-encode. Point the owner to the media branch file and its SHA-256.
- **Regression test:** none - Procedure only.

### visual-runs-monotony-check - Measure monotony: longest near-identical picture runs and screen time per base image
*VERIFIED · general · 2026-10-15*

- **Problem:** EP003 V2 looked repetitive although pacing reports (events per sentence) were fine.
- **Root cause:** Pacing counts overlay events; it does not see that the base picture (July 2022, 67 % of screen time) and the camera views (whole <-> whole_in) repeat.
- **Fix:** tools/autopilot/visual_runs.py VIDEO --timeline TL: runs of frames within a mean-abs-diff threshold of the run start (64x36, caption band ignored), changes per minute, screen time per base picture, repeated view pairs. Review runs > 10 s against the narration; a base picture above ~40 % of screen time needs a reason.
- **Reuse when:** Before calling any long-form render VISUALLY_REVIEWED.
- **References:** `tools/autopilot/visual_runs.py`; `docs/production-knowledge/QUALITY_CONTROL.md`
- **Verification:** EP003 V2: longest runs 3:32-3:49.5 (17.5 s), 4:28.5-4:43.5 (15 s), 4:58-5:11 (13 s); y2022 249 s (67 %).
- **Regression test:** none - measured on rendered frames; fix proposed, not yet applied to a full render

## visual

### callout-anchor-off-screen - A callout whose anchor is off screen drew a cut panel at the frame edge
*VERIFIED · general · 2026-10-15*

- **Problem:** EP003 352 s: the 'SHORELINE · AUG 1986' legend was cut at the top edge.
- **Root cause:** The anchor sat at the top of the view and the offset pushed the panel above it; CalloutPanel drew even when its anchor was outside the frame.
- **Fix:** CalloutPanel draws nothing when the anchor is outside the frame (2-98 % x, 4-96 % y); place legends below anchors near the top.
- **Reuse when:** Every callout/legend.
- **References:** `orbitalatlas/fx.py`; `docs/production-knowledge/VISUAL_ENGINE_BASELINE.md`
- **Verification:** EP003 still at 352.5 s: legend fully visible.
- **Regression test:** `orbitalatlas/tests/test_ep003_quality.py::test_callout_with_an_off_screen_anchor_draws_nothing`

### caption-scrim-contrast - White captions over bright salt flats need a soft dark band
*VERIFIED · general · 2026-10-15*

- **Problem:** White captions with a 2 px stroke measured 2-3:1 contrast over the bright EP003 playa; big style C headlines 1.2-2.3:1.
- **Root cause:** Stroke and shadow alone are too thin at phone scale on near-white ground.
- **Fix:** WordCaptions.scrim (default 0.55): a blurred rounded dark band behind the caption lines (styles A/B/D) and behind the style C headline; fades with the card. KeywordLift landed labels get a 0.14 px stroke and a stronger shadow.
- **Reuse when:** All captions.
- **References:** `orbitalatlas/captions.py`; `orbitalatlas/interact.py`; `docs/references/library/UNIFIED_STYLE_GUIDE.md`
- **Verification:** EP003 ranges 40-70, 120-140, 200-245, 320-372 s: 0 contrast issues after the band.
- **Regression test:** none - judged on rendered frames

### director-renders-the-automatic-storyboard - Render the automatic storyboard with motion graphics: storyboard -> motion_plan.json -> orbitalatlas.director
*VERIFIED · general · 2026-10-14*

- **Problem:** Graphics were hand-placed per demo; the storyboard generator produced only yt-render layers (labels, pins, wipes) with no kinetic type, cards or captions.
- **Root cause:** No link between the narration plan (semantic) and the timeline.
- **Fix:** storyboard.py plan now writes story/motion_plan.json (semantic.plan with the stack's pins/regions as gazetteer, timing source from the voice file) and timeline.meta.motion_plan; python3 -m orbitalatlas.director render SLUG OUT.mp4 builds cameras (snap / scale change / smooth), wipes/flips, pins, region tints, routes, comparisons, callouts, year tags, number and impact cards and captions from it, and writes OUT.director.json with every decision.
- **Reuse when:** Any episode with a geo stack: after storyboard plan, before reviewing motion.
- **References:** `orbitalatlas/director.py`; `tools/autopilot/storyboard.py`; `docs/references/library/REFERENCE_COMPARISON.md`
- **Verification:** ep900-visual-demo (19.3 s, alignment timing) and EP003 (300 s, 40 shots, estimated timing) built automatically; 30 s of EP003 and the full demo rendered and inspected.
- **Regression test:** `orbitalatlas/tests/test_visual_v2b.py::test_focus_hides_duplicate_captions_and_decisions_are_reported`

### director-shoreline-layers - Director renders v3 'fill' and 'outline' mask layers with a dated legend
*VERIFIED · general · 2026-10-15*

- **Problem:** Timeline v3 fill/outline layers were ignored by the director, so long passages on one image (EP003 4:44-5:46) had nothing evidence-based to show.
- **Root cause:** The director only knew image/wipe/flip/pin layers.
- **Fix:** director: layer fill {mask, minus} = water in mask and not in minus (opened 1 px) as a soft RegionTint without outline; outline {mask} = thin RegionTint line (thin=True, no glint); optional CalloutPanel legend with the mask date; each listed in report['dates'] as kind 'overlay'. Masks are timeline assets kind 'mask' with 'scale'.
- **Reuse when:** Episodes with co-registered stacks and a change story.
- **References:** `orbitalatlas/director.py`; `orbitalatlas/fx.py`; `docs/production-knowledge/VISUAL_ENGINE_BASELINE.md`
- **Verification:** EP003 stills at 275-365 s: exposed-bed fill, 1986 and 2022 shorelines, legends inside the frame.
- **Regression test:** `orbitalatlas/tests/test_ep003_quality.py::test_fill_and_outline_layers_are_drawn_dated_and_reported`

### event-year-vs-image-date - A historical year must never read as the date of the satellite picture
*VERIFIED · general · 2026-10-14*

- **Problem:** v2b showed '1959' (causeway finished) and '2022' (image) in the same YearTag style; a viewer could take 1959 for the image date.
- **Root cause:** One component was used for two meanings.
- **Fix:** interact.ImageStamp ('IMAGE · <sensor> · <month year>', cyan, top-left, from asset metadata) vs interact.EventYear (amber outline-to-fill year + the narration's clause, top-right). When an event year differs from the image date, the director shows the ImageStamp at the same time; an event year in a sentence whose number card carries the date is skipped. report['dates'] lists every displayed date with its role.
- **Reuse when:** Any narration year over imagery of another date.
- **References:** `orbitalatlas/interact.py`; `orbitalatlas/director.py`; `docs/references/library/UNIFIED_STYLE_GUIDE.md`
- **Verification:** ep901: 1959 shown with 'IMAGE · LANDSAT 8, 9 · USGS · JULY 2022' beside it; July 2022 date carried by the number card.
- **Regression test:** `orbitalatlas/tests/test_visual_v2c.py::test_image_stamp_says_image_and_event_year_never_does`

### evidence-pixels-never-recoloured - Satellite pixels get only neutral or evidence_safe grading; highlights are annotations
*VERIFIED · general · 2026-10-14*

- **Problem:** Reference 1 recolours the ocean to bright cyan and fills countries with flags; doing that to real imagery would present altered data as observation.
- **Root cause:** A map basemap (presentation) and a satellite picture (evidence) look alike on screen.
- **Fix:** grade.Graded(scene, preset, evidence=True) refuses presets other than neutral/evidence_safe and writes evidence_pixels_unmodified into the manifest; highlights are RegionTint/RouteArrow overlays with source + validation, alpha <= 0.2 over evidence; localised recolour only on presentation layers.
- **Reuse when:** Any scene mixing Landsat/NASA imagery with graphics or a stylised look.
- **References:** `orbitalatlas/grade.py`; `orbitalatlas/fx.py`; `docs/references/library/UNIFIED_STYLE_GUIDE.md`
- **Verification:** tests: guard raises on documentary_map with evidence=True; manifest flags enhanced pixels; localised grade leaves the rest identical.
- **Regression test:** `orbitalatlas/tests/test_visual_v2.py::test_evidence_guard_refuses_strong_presets`

### flip-and-wipe-image-date-stuck - During a year flip or a wipe the image date stayed on the first picture
*VERIFIED · general · 2026-10-14*

- **Problem:** EP003: during the 1985->2022 flip the footer said 'JUNE 1985' over 2021/2022 pictures; after a wipe the footer kept the old date. Event years 'from 1985 to 2022' were drawn as amber event years with labels like 'PUT'.
- **Root cause:** One SourceChip/ImageStamp per storyboard shot, built from the shot's base image; the year rule did not recognise ranges.
- **Fix:** director: every part of a shot (wipe target, each flip image) gets its own SourceChip and ImageStamp (flip stamps appear instantly, type_s=0); dates report lists them; years in 'from X to Y' are skipped; event-year labels are whole words of the last clause (max 4, no digits).
- **Reuse when:** Any wipe or flip, any narration with year ranges.
- **References:** `orbitalatlas/director.py`; `orbitalatlas/interact.py`; `docs/production-knowledge/VISUAL_ENGINE_BASELINE.md`
- **Verification:** EP003 stills at 23-29 s: IMAGE · LANDSAT 5 · AUGUST 1986 -> LANDSAT 8 · JULY 2021 -> LANDSAT 8, 9 · JULY 2022, footer follows.
- **Regression test:** `orbitalatlas/tests/test_visual_v2c.py::test_year_range_is_not_an_event_year_and_a_wipe_dates_both_pictures`

### geo-beats-need-sentence-splits-and-camera-resets - Single-image geographic beats hold too long: split by sentence, alternate zoom, set a timelapse step
*VERIFIED · general · 2026-10-14*

- **Problem:** The first storyboard of EP003 had a composition held 38.8 s and one beat of 22 s; a flip timelapse at 1.7 s per picture did not count as a timelapse.
- **Root cause:** One [VIS] beat = one camera move; the pacing rule counts a reset only when the view changes by >=1.5x zoom or >=0.35 shift. A flip needs <=1 s per picture.
- **Fix:** Split long narration at sentence boundaries into separate [VIS] beats (about 20 words max), alternate wide and tight views with a ratio >=1.5, use flip_step=0.9 on timelapse beats, keep the wide view tall enough for the whole subject (whole = 228 km wide centred 41.2 N for the Great Salt Lake). Re-run storyboard plan and read renderer_warnings.
- **Reuse when:** Writing [VIS: geo=...] hints for any map or satellite episode.
- **References:** `tools/autopilot/storyboard.py`; `docs/AUTOPILOT.md`
- **Verification:** EP003: longest static hold fell from 38.8 s to 10 s and composition resets rose from 19 to 34 for the same script.
- **Regression test:** `tools/autopilot/test_storyboard.py::test_flip_step_hint_sets_a_timelapse_rhythm_and_preview_keeps_wipe_and_flip_assets`

### graphic-label-cut-mid-number - Callout graphic label was truncated in the middle of a number
*VERIFIED · general · 2026-10-14*

- **Problem:** The number graphic printed 'In June 1985 the surface of the Great Salt Lake stood at 4,2' because the claim text was cut at 60 characters.
- **Root cause:** Character slicing of free text; passed unit tests and yt-render's own validation (it checks length, not meaning).
- **Fix:** callout_label(): hint, else '<PLACE> · <DATE>' from the manifest and the sentence, else a cut at a word boundary with an ellipsis, never inside a number.
- **Reuse when:** Any text derived from a sentence.
- **References:** `tools/autopilot/storyboard.py`
- **Verification:** Found only by LOOKING at a contact sheet of the proof frames; after the fix the frame reads 'GREAT SALT LAKE · JUNE 1985'.
- **Regression test:** `tools/autopilot/test_storyboard.py::test_callout_labels_are_whole_words_and_never_cut_a_number`

### hud-layout-phone - Phone-safe HUD layout: source chip top-left, image stamp below it, legends between 20 % and 78 % of the height
*VERIFIED · general · 2026-10-15*

- **Problem:** At phone size the 30 px source chip at the bottom collided with two-line captions and left the title-safe area; the image stamp repeated the chip for 3 s.
- **Root cause:** Bottom-left was shared with the caption band; the chip and the stamp carry the same facts.
- **Fix:** SourceChip at (0.035, 0.045) H with px 0.028 H; ImageStamp 30 px at (0.035, 0.115); the chip waits until the stamp has gone (wipes: stamp of the new picture then its chip; flips: one stamp per picture, chip on the last); CalloutPanel 0.032 H, clamped with its real width inside the title-safe frame and between 0.20 H and 0.78 H; EventYear label >= 30 px, clamped to the right edge; RouteLabel clamped to the title-safe frame.
- **Reuse when:** Every director render.
- **References:** `orbitalatlas/director.py`; `orbitalatlas/fx.py`; `orbitalatlas/interact.py`; `docs/production-knowledge/VISUAL_ENGINE_BASELINE.md`
- **Verification:** MOBILE_READABILITY_QA on EP003 ranges: 0 safe-area / overlap issues.
- **Regression test:** none - judged on rendered frames

### keyword-lift-caption-to-map - Keywords leave the subtitle line and land on the map; the caption keeps them dimmed
*VERIFIED · general · 2026-10-14*

- **Problem:** Captions and map labels were separate layers, so names appeared twice and text never interacted with the map.
- **Root cause:** No shared word positions between captions and scene overlays.
- **Fix:** WordCaptions.word_box/locate expose the caption layout; interact.KeywordLift flies the word on an arc to its pin (parallax depth) and lands as the label; the caption word is dimmed to 40 % (still readable, not duplicated at full weight); the pin's own label and the callout title are dropped for that place.
- **Reuse when:** Place names with stack pins mentioned in the narration.
- **References:** `orbitalatlas/interact.py`; `orbitalatlas/captions.py`; `orbitalatlas/director.py`; `docs/references/library/REFERENCE_COMPARISON.md`
- **Verification:** ep901 frames: CAUSEWAY, GILBERT BAY, GUNNISON BAY lifted and landed; overlay QA 0 collisions.
- **Regression test:** `orbitalatlas/tests/test_visual_v2c.py::test_lift_starts_on_the_caption_word_and_lands_on_the_anchor`

### labels-vs-captions-bands - Main labels must not sit in the caption band
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** Hook labels overlapped captions in the bottom 70 px.
- **Root cause:** Captions own the bottom of the frame.
- **Fix:** Main labels at y = 0.13-0.21 H or 0.40 H; yt-render landscape layout reserves a low caption band; only one main label per beat.
- **Reuse when:** Storyboard layout.
- **References:** `.claude/skills/yt-render/compose.py`; `docs/production-knowledge/VISUAL_STYLE.md`
- **Verification:** EP002 hook V6 and v4.1 reviewed on frames.
- **Regression test:** none - Layout rule; enforced by yt-render's safe-area/caption-band for timeline v3 and by review.

### landsat-tone-b-consistent-stills - One tonal curve for all Landsat stills in an episode
*VERIFIED · EP001 · 2026-10-09*

- **Problem:** Landsat location stills differed in tone, breaking continuity (Tassili, Gilf Kebir, Kufra switched to source bands).
- **Root cause:** Browse images vs source bands carry different tone.
- **Fix:** Build stills from source bands with one tone-B curve; label illustrative uses (Gilf Kebir under the rain card is 'illustrative' because NASA's statement is about 'some areas').
- **Reuse when:** Any episode that uses several Landsat locations.
- **References:** commit `ca2b355`; commit `3c05f27`; `production/ep001-sahara-green:productions/sahara-green/production/landsat_locations.py`; `production/ep001-sahara-green:productions/sahara-green/production/stills/tassili_toneB.json`
- **Verification:** EP001 pre-final: all five location stills and both sequences use tone B; QA JSON per place on the EP001 branch.
- **Regression test:** none - Visual judgement; per-place QA JSON exists but needs the 1.9 GB source bands.

### mobile-legibility-hud-text - Image dates, source chip, legends and event labels are illegible on a phone
*VERIFIED · general · 2026-10-15*

- **Problem:** EP003 V2 final audit: on a 6.1-inch phone in portrait (video 390x219 pt) the IMAGE stamp (19 px at 1080p) renders at ~3.9 pt, the source chip (0.017 H) ~3.7 pt, callout legends (0.026 H x 1.15) ~6.5 pt, event-year labels (~25 px) ~5 pt; in landscape (699x393 pt) the stamp is ~6.9 pt. Thin shoreline outlines (~2 px at 1080p) almost vanish (0.7 px portrait).
- **Root cause:** Sizes were judged on 1080p frames at desktop size; no phone-scale check.
- **Fix:** Applied in EP003 V3: see hud-layout-phone (sizes, positions), caption-scrim-contrast and director-shoreline-layers (outline 5 px with a dark under-stroke); checked automatically by mobile-readability-qa.
- **Reuse when:** Every render reviewed for YouTube (mobile is the main screen).
- **References:** `orbitalatlas/interact.py`; `orbitalatlas/layers.py`; `orbitalatlas/fx.py`; `docs/production-knowledge/QUALITY_CONTROL.md`
- **Verification:** Proof stills of 0:12.5 and 5:53.5 with the proposed sizes are legible at phone scale; brightness unchanged (124.6 vs 123.6 mean luma); one legend clipped at the right edge -> clamp fix needed. V3 (2026-10-15): outline width measured 5.0 px at 1080p; HUD text >= 30 px; MOBILE_READABILITY_QA clean on sampled ranges.
- **Regression test:** `orbitalatlas/tests/test_mobile_qa.py::test_outline_is_wide_enough_for_a_phone`

### monotony-text-cards-and-graphic-runs - Long graphic-only runs and text cards drive the retention risk
*HYPOTHESIS · general · 2026-10-13*

- **Problem:** EP001: 135 s and 146 s graphics-only runs, a white card flash in the hook; EP002: text-card scenes were the monotony source.
- **Root cause:** Facts delivered as text/diagram cards without imagery or motion.
- **Fix:** Break graphic runs with approved imagery, vary the look of consecutive graphics, put the first strong image in the first seconds, keep the hook dark (no white flash), carry the same facts with dated filmstrips, timeline thumbnails and traced outlines.
- **Reuse when:** Storyboarding any long documentary.
- **References:** `productions/dubai/preview/monotony_audit.py`; commit `7a19735`; commit `b706c4c`; `production/ep001-sahara-green:productions/sahara-green/review/pre_final/RETENTION_RISK_REPORT.md`; `production/ep001-sahara-green:productions/sahara-green/review/pre_final/editorial/EDITORIAL_CHANGES_REPORT.md`
- **Verification:** EP001 pre-final report ranked 15 risks; editorial pass fixed the opening and a 38 s proposal block (static gaps <= 2.6 s). Retention benefit itself is unmeasured (no analytics yet).
- **Regression test:** none - Retention effect is a HYPOTHESIS until published analytics exist; monotony_audit.py measures motion on rendered frames.

### number-card-unit-crosses-sentence - Number card unit took words from the next sentence ('4,209.7 FEET IN JULY 2022')
*VERIFIED · general · 2026-10-14*

- **Problem:** EP003 first full render: number cards read '4,209.7 FEET IN JULY 2022' (a wrong fact), '48 % AND THAT ITS', '6 FEET USGS SAYS THE'; long kickers overflowed the card.
- **Root cause:** The tail loop started after the unit even when the unit word itself closed the sentence, and kept function words.
- **Fix:** director: no tail when the unit (or number) ends the clause; tail keeps only content words and stops at TAIL_STOP/STOP words or digits (max 3); kicker = words after the last colon, at most 9.
- **Reuse when:** Every number card.
- **References:** `orbitalatlas/director.py`; `docs/production-knowledge/VISUAL_ENGINE_BASELINE.md`
- **Verification:** EP003 re-render stills: '4,190.2 FEET', '3.7 FEET HIGHER', kicker 'IN JULY 2022, THE GREAT SALT LAKE MEASURED' fits.
- **Regression test:** `orbitalatlas/tests/test_visual_v2c.py::test_unit_stops_at_the_end_of_its_sentence`

### onscreen-phrase-grammar - Number-card kickers and event-year labels must be whole clauses of the narration
*VERIFIED · general · 2026-10-15*

- **Problem:** EP003: kickers like 'BY NASA FOUND THAT THE LAKE'S VOLUME HAS SHRUNK' and labels like 'AT' (1986) or 'COMPLETED ACROSS MIDDLE LAKE'; a 9-word kicker ran off the frame.
- **Root cause:** Kickers were 'the last 9 words before the number'; labels dropped stop words from the middle of the clause; nothing checked width or grammar.
- **Fix:** orbitalatlas/phrases.py: clause_suffix (clause-initial, no dangling first word, max 9 words / 44 chars), label (contiguous clause, strips leading/trailing function words, falls back to the words after the year), lint (contiguous narration words, no dangling start/end). The director uses them and lists every dynamic text with its lint result in report['texts']; event years with < 1.2 s on screen are skipped.
- **Reuse when:** Every director render; check report['texts'] for problems before rendering.
- **References:** `orbitalatlas/phrases.py`; `orbitalatlas/director.py`; `docs/production-knowledge/VISUAL_ENGINE_BASELINE.md`
- **Verification:** EP003 build: 15 kickers and 8 labels, 0 lint problems, 0 overlay issues (was 1 card outside the frame).
- **Regression test:** `orbitalatlas/tests/test_ep003_quality.py::test_lint_flags_the_ep003_defects`

### route-label-spoken-only - A route arrow must not show a distance the narrator does not say
*VERIFIED · general · 2026-10-15*

- **Problem:** EP003: 'Dense brine from Gunnison Bay sank into ... Gilbert Bay' drew the arrow with '60 KM' (computed pin distance) - a number on screen with no source in the narration.
- **Root cause:** The director labelled every route with the great-circle distance between the pins.
- **Fix:** Route label = the distance spoken in the same sentence (number + km/miles, the narrator's words); otherwise the arrow has no label. The computed distance stays in the arrow's validation text only.
- **Reuse when:** Every route event.
- **References:** `orbitalatlas/director.py`; `docs/production-knowledge/VISUAL_ENGINE_BASELINE.md`
- **Verification:** EP003 3:27 arrow without a number.
- **Regression test:** `orbitalatlas/tests/test_ep003_quality.py::test_no_distance_label_unless_the_narrator_says_one`

### single-focus-no-number-duplication - One focus at a time: a number/impact card hides the caption that says the same thing; pacing limits cards
*VERIFIED · general · 2026-10-14*

- **Problem:** The first demo showed 4,190.2 in the caption and again as a big pop; EP003's automatic run put a number card every 2-3 s and a 6.7 s impact card.
- **Root cause:** Captions and graphics were planned independently; no pacing rule for focus graphics.
- **Fix:** director focus manager: impact (revelation, <= 5 words) > number; overlapping caption cards are hidden (the card carries kicker + value + unit + trailing words, e.g. '20 FEET LOWER'); map dims behind a number card; min 5 s between focus cards, max 4 per minute (others stay as style D captions); captions never count up (subtitles show the spoken words).
- **Reuse when:** Planning any on-screen number or statement.
- **References:** `orbitalatlas/director.py`; `orbitalatlas/captions.py`; `docs/references/library/UNIFIED_STYLE_GUIDE.md`
- **Verification:** EP003 auto plan: 15 focus cards in 300 s, impact cards over 5 words refused; demo: captions hidden exactly under the two cards.
- **Regression test:** `orbitalatlas/tests/test_visual_v2b.py::test_storyboard_stat_label_is_not_drawn_twice`

### storyboard-never-shows-an-unrelated-or-wrong-year-picture - A generated storyboard must not fake relevance: no unrelated picture, wrong years are reported
*VERIFIED · general · 2026-10-14*

- **Problem:** The first generator version filled scenes with the 'best neighbour' asset (an Aral Sea image under a Lake Chad sentence) and showed a 2023 frame for 'July 2022' and a 2015 frame for 'the 1986 record' without saying so.
- **Root cause:** Scoring rewarded novelty (asset not used recently) above relevance, and years were not compared.
- **Fix:** Only relevant assets (tags/place, partial multi-word match, author hint) or the current subject (continuation) are candidates; a scene without any is a reported gap and the previous shot continues; years named in the text are compared with the picture's years (penalty up to 9, nearest wins, remaining gap goes to plan.needs).
- **Reuse when:** Any automatic picture selection.
- **References:** `tools/autopilot/storyboard.py`
- **Verification:** Found by reading the plan and looking at rendered frames of the EP003 proof; 18 storyboard tests incl. 'no unrelated picture', 'gap not a fake', 'nearest year wins'.
- **Regression test:** `tools/autopilot/test_storyboard.py::test_no_unrelated_picture_is_ever_shown`

### visual-engine-v2-reuse-map - Visual engine v2: which module to use for captions, kinetic type, graphics, grading, camera and narration-driven events
*VERIFIED · general · 2026-10-14*

- **Problem:** A new episode needs word-synced captions, kinetic titles, arrows, region highlights, grading and narration-driven timing; the old engine only had per-glyph text, markers and transitions.
- **Root cause:** Caption code lived in Dubai episode scripts; no shared planner from narration to visual events; no evidence/presentation grade separation.
- **Fix:** Use orbitalatlas.semantic.plan(words, places) for events and caption styles, captions.WordCaptions for A-E, kinetic.* for type, fx.* for overlays (RegionTint, RouteArrow, MarkerPin, HudFrame, NeonGrid, LightSweep, Waveform), grade.Graded (evidence_safe only on satellite pixels), camera_presets.*, transitions.FlashDip/LightWipe, sequence.Program for global overlays, demo/visual_v2.py as the worked integration. Consult python3 -m orbitalatlas.refs consult SCENE_TYPE first.
- **Reuse when:** Before storyboarding any map/satellite episode or writing a new caption/typography/overlay effect.
- **References:** `orbitalatlas/semantic.py`; `orbitalatlas/captions.py`; `orbitalatlas/kinetic.py`; `orbitalatlas/fx.py`; `orbitalatlas/grade.py`; `orbitalatlas/demo/visual_v2.py`; `docs/references/library/UNIFIED_STYLE_GUIDE.md`
- **Verification:** 44 offline tests; 18.7 s demo on real EP003 Landsat mosaics rendered at 1920x1080 and inspected frame by frame.
- **Regression test:** `orbitalatlas/tests/test_visual_v2.py::test_every_style_draws_inside_the_frame_and_registers_boxes`

## geo

### landsat-two-paths-calibrated-mosaic - Lake-sized Landsat stills need two paths and calibrated bands, not the USGS browse image
*VERIFIED · general · 2026-10-14*

- **Problem:** Browse GeoTIFFs of the Great Salt Lake gave a bright diagonal seam, different tones per tile and date, and one path (38) did not cover the lake's west half.
- **Root cause:** Browse images are stretched per scene; neighbouring Landsat paths (38 and 39) are acquired on different days (here 7 days apart) and each scene has a black no-data collar.
- **Fix:** Download Level-1 bands (fetch_bands.py), build with tools/autopilot/landsat_color.py: TOA reflectance from the MTL, one fixed tone curve for every date/sensor, first-tile-wins in the order path 39 rows then path 38 rows, collar eroded by 3 px, no blending. A remaining hard edge between two days is real and is disclosed ('mosaic of scenes'), not hidden. Check geography by overlay: the causeway edge fell at 41.226 N in both 2021 and 2022 mosaics (different tile sets), Saltair and Salt Lake City pins landed on their sites.
- **Reuse when:** Any episode with a before/after Landsat sequence over an area wider than one scene (~185 km) or spanning several sensors.
- **References:** `tools/autopilot/landsat_color.py`; `.claude/skills/yt-geo/geostack.py`; `docs/production-knowledge/README.md`
- **Verification:** EP003: 5 mosaics (1985, 1986, 1999, 2021, 2022) of 4 tiles each, 3971x3122 px at 60 m, DATE_ACQUIRED of all 20 tiles equals the date in the file name; frames inspected.
- **Regression test:** `tools/autopilot/test_landsat_color.py::test_two_tiles_give_one_seamless_picture_with_no_collar_line`

### natural-earth-real-coastlines-only - Never invent coastlines or borders
*VERIFIED · EP002 · 2026-10-09*

- **Problem:** Hand-drawn coastlines would be fabricated evidence.
- **Root cause:** No real geography source in the early scene engine.
- **Fix:** Use Natural Earth (public domain) via tools/fetch_natural_earth.sh and orbitalatlas.geo; checksum in data/natural_earth.sha256; data stays out of git.
- **Reuse when:** Any map or globe scene.
- **References:** `orbitalatlas/geo.py`; `tools/fetch_natural_earth.sh`; `data/natural_earth.sha256`; commit `86e204c`
- **Verification:** orbitalatlas geo tests; locator proof renders.
- **Regression test:** `orbitalatlas/tests/test_geo.py::test_span_log_interpolation_and_monotone_zoom`

### outline-mask-includes-coast-and-clouds - Traced outlines picked up coast arcs and cloud specks
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** Threshold masks around a landmark included all land and cloud near it.
- **Root cause:** A bare threshold cannot tell new land from old coast.
- **Fix:** Restrict the radius, use the difference mask (new_land) between two registered dates, raise the threshold (ASTER 2006: 110).
- **Reuse when:** Traced outlines on real imagery.
- **References:** `.claude/skills/yt-geo/watermask.py`; `docs/production-knowledge/SATELLITE_DATA.md`; commit `89559f0`
- **Verification:** EP002 C2/C4/C6 outlines reviewed on contact sheets.
- **Regression test:** `.claude/skills/yt-geo/test_geo.py::test_dates_align_on_one_grid`

### registered-images-only-continuity - Never fake spatial continuity between unregistered images
*VERIFIED · general · 2026-10-09*

- **Problem:** Image-space zoom was presented as a 3D flyover; EP001 Kufra stills risked misalignment.
- **Root cause:** Different dates/sensors have different footprints and pixel grids.
- **Fix:** Check registration with phase correlation (EP002) or verify_kufra_alignment.py (EP001); use yt-geo to put dates on one UTM grid; label anything unregistered; use dissolves, not wipes, between unregistered images.
- **Reuse when:** Any before/after or camera move between two images.
- **References:** `.claude/skills/yt-geo/geostack.py`; commit `3c05f27`; commit `fc3cf67`; `production/ep001-sahara-green:productions/sahara-green/production/verify_kufra_alignment.py`; `production/ep001-sahara-green:productions/sahara-green/production/stills/kufra_alignment.json`
- **Verification:** EP001 Kufra alignment verification; EP002 registration check before the 2000-2003 wipe; yt-geo test puts dates on one grid.
- **Regression test:** `.claude/skills/yt-geo/test_geo.py::test_dates_align_on_one_grid`

### shoreline-masks-seeded - Traced shoreline masks on a calibrated stack: seeded growth, not the brightness threshold
*VERIFIED · general · 2026-10-15*

- **Problem:** yt-geo watermask.py (dark & non-red threshold) classified forested mountains as water and missed the pink 2022 north arm on the calibrated EP003 stack.
- **Root cause:** The calibrated tone curve lifts lake brightness above the fixed threshold; brine colour is reddish.
- **Fix:** tools/autopilot/shoreline_masks.py: regions.seeded_region from manifest pins (+ extra lon/lat seeds) inside a lon/lat box at 1/4 resolution; --reject-reddish YEAR removes red-brown land only for years whose lake is blue/green (1985, 1986), never for pink-brine years (2022). Writes masks + JSON + a check JPEG; look at the check JPEG before use. Masks are display aids, not surveys.
- **Reuse when:** Any 'shoreline then/now' or 'exposed lake bed' visual.
- **References:** `tools/autopilot/shoreline_masks.py`; `orbitalatlas/regions.py`; `docs/production-knowledge/SATELLITE_DATA.md`
- **Verification:** EP003 1985/1986/2022 masks checked on overlays (islands cut out, Bear River and Farmington bays inside 1986, west desert excluded).
- **Regression test:** none - measurement / environment fact, not code

## storage

### ep001-chain-link1-reproduced-final-unproven - EP001 rebuild: source bands and reflectance stacks reproduce exactly; the final video is not proven
*VERIFIED · EP001 · 2026-10-14*

- **Problem:** After the container loss only text and code of EP001 remained; the render chain depended on 78 Landsat band files and on scripts with hard-coded scratch paths.
- **Root cause:** Source bands, scratch caches and intermediate videos live outside Git; process.py, build_frames.py and vis_common.py point at a fixed old scratch directory.
- **Fix:** Restore bands with restore_source_bands.py (rerun after a 504), then run tools/autopilot/recover_ep001_stacks.py: it patches the three path lines of a scratch copy of process.py, rebuilds the grids from the stored reports and compares the new reports with the stored ones. Never edit the EP001 files in the repo. Claim byte-identity of the final video only after the later links (frames, sequences, CALIPSO clip, stills, graphics, normalized narration, render) are rebuilt and hashes compared.
- **Reuse when:** Anyone asks whether EP001 can be re-rendered or reproduced; before building a similar restore tool.
- **References:** `tools/autopilot/recover_ep001_stacks.py`; `tools/autopilot/recover_narration.py`; `docs/production-knowledge/SATELLITE_DATA.md`
- **Verification:** 78/78 files SHA-512 verified; EO, TW and TE reports rebuilt in 51 s, ~2 min, ~2 min and equal the stored reports (valid fractions, medians, registration, stretch).
- **Regression test:** `tools/autopilot/test_recover_ep001_stacks.py::test_paths_are_patched_and_nothing_else`

### ep003-manifest-not-in-git - EP003 assets/manifest.json (with the stack) was ignored by git
*VERIFIED · general · 2026-10-14*

- **Problem:** The automatic EP003 test could not take the manifest from the branch: productions/ep###-*/assets/ is ignored, and the manifest lives there.
- **Root cause:** .gitignore ignores the whole assets/ folder of new episodes, text included.
- **Fix:** Force-add the manifest (git add -f productions/<slug>/assets/manifest.json); episodes keep media out of git but the manifest is text and must be committed.
- **Reuse when:** Committing any new episode.
- **References:** `tools/autopilot/storyboard.py`; `docs/AUTOPILOT.md`
- **Verification:** found while copying EP003 for the director test; ep900 manifest force-added; EP003 fix pushed to its branch.
- **Regression test:** none - needs rendered video / repository state, checked on frames

### ipad-review-copy - Make a small review copy for the iPad
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** The owner reviews from an iPad; a 272 MB master cannot be opened comfortably.
- **Root cause:** Size and codec of the master.
- **Fix:** ffmpeg 854x480, x264 slow, 380 kb/s + AAC 56 kb/s mono = 28.6 MB for 8:37 (<30 MB limit) on the media branch.
- **Reuse when:** Every review hand-off.
- **References:** `docs/production-knowledge/RENDERING.md`; commit `3f083d8`; video: EP002 v4.1 iPad copy
- **Verification:** EP002 iPad copy delivered.
- **Regression test:** none - Encode recipe; verified by file size.

### landsat-bulk-data-stays-out-of-git - Landsat bundles must never be committed
*VERIFIED · EP001 · 2026-10-08*

- **Problem:** Landsat step: 1.946 GB, 68 source-band files for EP001.
- **Root cause:** Scene bundles and GeoTIFFs are huge and regenerable.
- **Fix:** Gitignore landsat/raw, landsat/work, *.tar, *_B[0-9]*.TIF, *_refl.tif; keep manifest + restore script + validation JSON in git so the data can be re-fetched.
- **Reuse when:** Any yt-satellite acquisition.
- **References:** `.gitignore`; commit `0d76377`; `production/ep001-sahara-green:productions/sahara-green/landsat/source_bands/manifest.json`
- **Verification:** EP001 manifest verified 68 files; .gitignore carries the rules.
- **Regression test:** none - .gitignore rule, verified by git check-ignore.

### master-over-100mb-lfs-or-parts - A >100 MB master cannot be pushed to git
*VERIFIED · general · 2026-10-13*

- **Problem:** Final MP4s (EP001 747 s, EP002 273 MB) exceed GitHub's 100 MB file limit; main must stay free of media.
- **Root cause:** Host file limit.
- **Fix:** Put media on media/<episode>-final: either 90 MB parts + SHA256SUMS + join command, or Git LFS (needs github-cloud.s3.amazonaws.com and lfs.github.com allowed). Keep voice cache on media/<episode>-audio. Commit only text, QC JSON and checksums to work branches.
- **Reuse when:** Every delivery.
- **References:** `docs/production-knowledge/RENDERING.md`; commit `9bdc3c0`; video: EP002 v4.1 final master, media/ep002-dubai-final
- **Verification:** media/ep002-dubai-final holds v4.1 as one LFS file, SHA-256 checked after an anonymous download.
- **Regression test:** none - Depends on the host and credentials; verified by the download check.

## process

### adaptive-intensity-and-pacing - Animation intensity follows the meaning; pacing is measured per sentence
*VERIFIED · general · 2026-10-14*

- **Problem:** Fixed density rules made dense passages slow and explanations busy.
- **Root cause:** No notion of how complex or dramatic a sentence is.
- **Fix:** semantic.intensity: revelations, emphasis, data and fast speech raise the score, long explanations lower it (calm / normal / energetic). Director: calm -> captions A, no punches; energetic -> punch-ins on emphasis (2.5 s apart), light accents on cuts; lifts everywhere outside focus cards. report['pacing'] gives the max gap between visual changes per sentence with limits 3 / 4 / 6 s.
- **Reuse when:** Every automatic edit.
- **References:** `orbitalatlas/semantic.py`; `orbitalatlas/director.py`; `docs/references/library/UNIFIED_STYLE_GUIDE.md`
- **Verification:** ep901: max gaps 1.3-1.9 s in all five sentences; the 22-word explanation is calm.
- **Regression test:** `orbitalatlas/tests/test_visual_v2c.py::test_long_explanation_is_calm_and_a_revelation_is_energetic`

### agent-cannot-listen-or-watch - The agent cannot listen to audio or watch continuous video
*VERIFIED · general · 2026-10-13*

- **Problem:** Pronunciation and pacing cannot be verified: no ASR (PyPI/HF blocked), frames only.
- **Root cause:** No audio or video playback tool in the session.
- **Fix:** Report plausibility only (provider word duration per syllable vs narrator mean 0.199 s sd 0.069), contact sheets and frame samples; list exactly what was not verified; the owner listens before publishing.
- **Reuse when:** Every review report.
- **References:** `tools/autopilot/gates.py`; `docs/production-knowledge/QUALITY_CONTROL.md`
- **Verification:** Autopilot review gate requires not_verified and the list of reviewed frames.
- **Regression test:** `tools/autopilot/test_autopilot.py::test_agent_cannot_grant_user_approved`

### command-guard-quote-aware-parsing - Command guards must parse commands, and be tested against bypass forms
*VERIFIED · general · 2026-10-14*

- **Problem:** The first guard blocked harmless text (a heredoc that merely mentioned a script) and missed real bypasses: `rm path` (regex needed a leading slash), `bash -lc "..."`, `perl -pi`, `cp` with a protected SOURCE, youtube uploader binaries.
- **Root cause:** Substring matching on the whole command line; splitting on ';' inside quotes; assuming flag spellings.
- **Fix:** Split on unquoted separators only, tokenise each command, unwrap sh/bash -c (any flag cluster containing c), env/nohup/xargs, judge by command head and arguments (cp/rsync only by destination). Keep a whole-line check only for network clients (curl, urllib, node) because quoted code bodies defeat tokenising.
- **Reuse when:** Writing or extending any PreToolUse guard.
- **References:** `tools/autopilot/guard.py`
- **Verification:** 29 bypass-form tests (paid TTS, git push spellings, GitHub MCP, uploads, writes to finished files, effect duplication) found 4 real gaps during development; all pass.
- **Regression test:** `tools/autopilot/test_guard.py::test_every_way_of_writing_to_a_finished_file_is_blocked`

### fix-the-class-not-the-instance - Fix the whole class of a defect across all scenes
*VERIFIED · EP002 · 2026-10-13*

- **Problem:** Readability defects of one class (amber/muted text on bright imagery) kept reappearing in other scenes after the reported one was fixed.
- **Root cause:** Only the reported instance was fixed.
- **Fix:** Fix the class (backing pill) and run the audit over every scene; freeze the director-approved segments (copy byte for byte) and touch only the others.
- **Reuse when:** After any review finding.
- **References:** `docs/production-knowledge/LESSONS_LEARNED.md`; commit `8d0058e`
- **Verification:** v4.1: hook segments copied byte for byte, 8 other scenes re-rendered.
- **Regression test:** none - Process rule.

### pgrep-f-matches-itself - `until ! pgrep -f NAME` waits forever because it finds its own shell
*VERIFIED · general · 2026-10-14*

- **Problem:** A background wait loop `until ! pgrep -f fetch_bands; do sleep 20; done` ran for 30+ minutes after all downloads had finished; it looked like a hung download.
- **Root cause:** pgrep -f matches the full command line of every process, including the bash -c process that is running the loop (its command line contains the pattern). The check can never come back empty.
- **Fix:** Do not wait on a process by substring. Use tools/autopilot/procs.py: `procs.py wait NAME --timeout S` (matches an interpreter running script NAME, excludes shells and the caller's ancestors, bounded, prints progress), or wait on a result marker (log line / output file) with a timeout. Diagnose a 'stuck' job by looking at the log mtime, file sizes and /proc/PID/cmdline before killing anything.
- **Reuse when:** Before writing any wait/poll loop for a background job; whenever a 'running' process has no CPU and no new output.
- **References:** `tools/autopilot/procs.py`; `docs/AUTOPILOT.md`
- **Verification:** EP003: the pattern reproduced the endless loop; pids 10089/11757 were the waiting shells, not downloads. procs.py tests check shell lines are not matches, a real script process is found, the caller is excluded and wait is bounded.
- **Regression test:** `tools/autopilot/test_procs.py::test_shell_command_line_mentioning_the_name_is_not_a_match`

### proof-first-then-scale - Render a 12-15 s proof of the hardest sequence, get review, then scale
*VERIFIED · general · 2026-10-13*

- **Problem:** V3 (monotony), V4 (clutter) and V5 (text overload) of the EP002 hook were only caught by proofs.
- **Root cause:** Full builds hide the defect behind 25 min of render.
- **Fix:** Proof of the hardest sequence first (12-41 s), review, then the full film; batch audits, fix once, re-render only changed scenes.
- **Reuse when:** Every new visual style or sequence.
- **References:** `docs/production-knowledge/LESSONS_LEARNED.md`; `docs/ORBITALATLAS_VISUAL_MASTER.md`; commit `4d7c12a`; commit `b706c4c`
- **Verification:** Three rejected versions were caught by proofs, not by the full film.
- **Regression test:** none - Process rule.

### qc-rule-met-but-goal-missed - A passing QC check is not the goal it stands for
*VERIFIED · general · 2026-10-13*

- **Problem:** yt-qc audio_starts passed with a bed while the voice started late; a master that passed yt-qc still had 8 legibility defects and 4 static holds.
- **Root cause:** Automatic checks measure a proxy.
- **Fix:** Report the measurement and its reason, never the goal; release gate = yt-qc + contrast audit + text-bounds + static-run scan + eyes on frames. Status vocabulary TECHNICALLY_VALID -> VISUALLY_REVIEWED -> USER_APPROVED (owner only).
- **Reuse when:** Every release.
- **References:** `tools/autopilot/gates.py`; `docs/production-knowledge/QUALITY_CONTROL.md`; `docs/production-knowledge/LESSONS_LEARNED.md`
- **Verification:** Autopilot's review gate refuses USER_APPROVED from the agent and demands the list of frames looked at and of what could not be verified.
- **Regression test:** `tools/autopilot/test_autopilot.py::test_agent_cannot_grant_user_approved`

### release-package-without-upload - No YouTube connector: deliver the package, never claim an upload
*VERIFIED · general · 2026-10-13*

- **Problem:** Publishing is the owner's call and the session has no YouTube connector.
- **Root cause:** Policy and tooling.
- **Fix:** Deliver description (facts checked line by line against the locked script), chapters (0:00, >= 3, each >= 10 s), tags, thumbnail from two real frames, copyright table and Studio steps; metadata.json published=false; the owner also confirms the ElevenLabs plan allows commercial use.
- **Reuse when:** End of every episode.
- **References:** `tools/autopilot/gates.py`; `tools/autopilot/guard.py`; `productions/dubai/release/README.md`; `productions/dubai/release/COPYRIGHT_CHECK.md`; commit `82fecaa`
- **Verification:** EP002 release package; autopilot package gate refuses published=true and bad chapters; guard hook blocks upload commands.
- **Regression test:** `tools/autopilot/test_autopilot.py::test_package_requires_published_false`

### script-lock-sha256 - Lock the spoken text by hash before paying for TTS
*VERIFIED · general · 2026-10-09*

- **Problem:** Edits after narration make the paid audio and the captions wrong.
- **Root cause:** The text changed while the audio was fixed.
- **Fix:** SCRIPT_LOCK stores the sha256 of the spoken text (only VO lines); orbital.py refuses the paid call when script.md no longer matches the plan or lock. Narration-locked episodes still allow reordering visuals.
- **Reuse when:** Between script approval and render.
- **References:** `tools/autopilot/orbital.py`; `productions/dubai/SCRIPT_LOCK.md`
- **Verification:** EP002 SCRIPT_LOCK; autopilot test blocks the paid call after a post-plan edit.
- **Regression test:** `tools/autopilot/test_autopilot.py::test_script_change_after_plan_blocks_the_paid_call`

### timeline-v3-gate-keys - Storyboard gate and yt-qc disagreed on timeline v3 keys
*VERIFIED · general · 2026-10-14*

- **Problem:** The storyboard gate demanded audio.voice + subtitles; yt-qc rejects those keys in a version 3 timeline (allowed: voice, captions) and returned ERROR.
- **Root cause:** gates.timeline was written for v1/v2 timelines.
- **Fix:** gates.timeline accepts v3 voice.src / captions (or v1/v2 audio.voice / subtitles). A v3 timeline carries voice={src,meta} and captions={src}.
- **Reuse when:** Any version 3 timeline through orbital.py.
- **References:** `tools/autopilot/gates.py`; `docs/AUTOPILOT.md`
- **Verification:** EP003: storyboard gate ok and yt-qc PASS on the same timeline.
- **Regression test:** none - covered by the EP003 run; the existing autopilot tests pass

## env

### git-stop-hook-untracked-files - Session stop hook complains about untracked or uncommitted files
*VERIFIED · general · 2026-10-13*

- **Problem:** The git stop hook blocked the end of a session because of tile caches and new code.
- **Root cause:** Caches and generated files were not ignored.
- **Fix:** Ignore caches (tools/cesium_proof/.gitignore, voice/cache/); commit code and text; media goes to media/* branches. Commit and push before finishing.
- **Reuse when:** End of every session.
- **References:** `.gitignore`; `tools/cesium_proof/.gitignore`; commit `89559f0`
- **Verification:** EP002 sessions ended clean after the ignores.
- **Regression test:** none - Hook behaviour; the .gitignore entries are the fix.

### orbitalatlas-tests-need-repo-root - orbitalatlas tests fail when run from their own folder
*VERIFIED · general · 2026-10-14*

- **Problem:** python3 orbitalatlas/tests/test_engine.py -> ModuleNotFoundError: No module named 'orbitalatlas'.
- **Root cause:** The tests import the package by name; running a file puts only its folder on sys.path.
- **Fix:** Run from the repo root as modules: python3 -m unittest discover -s orbitalatlas/tests -t . (61 tests). kb.py verify --run-tests does this automatically.
- **Reuse when:** Any run of the orbitalatlas tests.
- **References:** `tools/memory/kb.py`; `orbitalatlas/tests/test_engine.py`
- **Verification:** Found in the 2026-10-14 audit; 61 tests pass with -t . (4 skipped).
- **Regression test:** `tools/memory/test_kb.py::test_orbitalatlas_tests_run_as_modules_from_the_repo_root`

### rm-denied-write-new-dir - Relative-glob rm is denied by the permission policy
*VERIFIED · general · 2026-10-13*

- **Problem:** rm of relative globs was blocked.
- **Root cause:** Permission policy.
- **Fix:** Write outputs to a new directory; do not clean up with rm; the scratchpad is for temporary files.
- **Reuse when:** Cleanups.
- **References:** commit `89559f0`
- **Verification:** Observed in EP002 sessions.
- **Regression test:** none - Environment policy.

### shell-pkill-exit-144 - pkill -f kills the shell that runs it
*VERIFIED · general · 2026-10-13*

- **Problem:** Shell dies with exit 144 after pkill -f <pattern>.
- **Root cause:** The pattern also matches the shell's own command line.
- **Fix:** pgrep -f "^<exact start of command>" and kill the PIDs, or let the jobs finish.
- **Reuse when:** Stopping background render jobs.
- **References:** commit `89559f0`
- **Verification:** Observed during EP002 renders.
- **Regression test:** none - Shell behaviour of the cloud session.

### unpushed-work-is-lost - Cloud containers are ephemeral; only pushed branches survive
*VERIFIED · general · 2026-10-14*

- **Problem:** The audit found the knowledge of EP001/EP002 spread over 16 branches, 5 of them never merged, plus local-only files; two sessions' worth of auto memory (~/.claude/projects) does not exist in a fresh container.
- **Root cause:** Work stayed on side branches and in session-local memory.
- **Fix:** Keep durable memory in the repository (knowledge/solutions.json + docs/production-knowledge + CLAUDE.md); paid or large media on media/* branches with SHA-256; fetch all branches at session start: git fetch origin '+refs/heads/*:refs/remotes/origin/*'.
- **Reuse when:** Every session start and end.
- **References:** `tools/memory/kb.py`; `docs/AUDIT_PHASE1.md`
- **Verification:** docs/AUDIT_PHASE1.md lists what each branch holds.
- **Regression test:** none - Repository organisation; checked by kb.py validate (references must resolve).

## research

### claims-audit-primary-sources - Audit every claim against the primary source before it can be narrated
*VERIFIED · EP001 · 2026-10-08*

- **Problem:** EP001 needed 10 audit rounds: corrections to P20, S4, N1, L3, G1-G20; a $2T claim and several 'most of the Sahara' phrasings were removed; unverifiable claims were cut, not softened.
- **Root cause:** Secondary summaries overstate (thresholds, 'most of', cost figures).
- **Fix:** Per claim: source URL, evidence type (observation / satellite-derived estimate / reconstruction / model), status; narrate only VERIFIED claims; lock the script by SHA-256 afterwards. Autopilot claims gate enforces it from claims.json.
- **Reuse when:** Every episode, before the script is written.
- **References:** `productions/dubai/research/claims.md`; `productions/dubai/SCRIPT_LOCK.md`; commit `706a280`; commit `be14ca1`; commit `f8ce0c8`; `production/ep001-sahara-green:productions/sahara-green/story/claims.md`; `production/ep001-sahara-green:productions/sahara-green/story/source_audit_round10.md`; `production/ep001-sahara-green:productions/sahara-green/story/SCRIPT_LOCK.md`
- **Verification:** EP001 SCRIPT LOCK v1.1; EP002 claims table with 33 claims; claims gate unit test.
- **Regression test:** `tools/autopilot/test_autopilot.py::test_claims_must_be_verified_and_sourced`

### nasa-image-host-blocked-use-svs - NASA Earth Observatory image files are unreachable; SVS movies and stills are
*VERIFIED · general · 2026-10-14*

- **Problem:** assets.science.nasa.gov (hosts the Earth Observatory / World of Change JPEGs) returns no response from this environment.
- **Root cause:** Network allowlist.
- **Fix:** Use svs.gsfc.nasa.gov (HEAD 200, movies up to 5760x3240 and stills), extract frames locally with ffmpeg (record frame index and sha256), or fetch Landsat with the USGS M2M credentials. Credit NASA's Goddard Space Flight Center; the pages state no explicit licence, only the Reproduction Guidelines - confirm before release.
- **Reuse when:** Planning imagery for any NASA-sourced episode.
- **References:** `docs/ASSET_SOURCE_REGISTRY.md`
- **Verification:** EP003: SVS 15020 1080p movie (30 fps, 13 s, 16,204,354 bytes) downloaded and frames extracted; assets.science.nasa.gov HEAD failed.
- **Regression test:** none - Depends on the live network and the host allowlist.

### shorts-feedback-small-samples - A 2-vs-2 Shorts experiment can never be significant
*HYPOTHESIS · general · 2026-10-13*

- **Problem:** The Shorts feedback loop compared 2 vs 2 videos; views are not independent observations; Studio and Analytics API metrics differ (engagedViews, looping).
- **Root cause:** Minimum two-sided p for 2v2 is 0.33.
- **Fix:** Classify such experiments as exploratory, not conclusive; use video-level permutation tests; Shorts are excluded from the current production plan (PR #16 is parked).
- **Reuse when:** Any analytics-driven decision.
- **References:** `docs/production-knowledge/LESSONS_LEARNED.md`; commit `d4a330a`
- **Verification:** Reasoned in PR #16 audit patches (WIP, tests not yet updated).
- **Regression test:** none - Statistical reasoning; code is on the unmerged feature/shorts-performance-feedback branch.

### source-pages-blocked-by-proxy - Primary-source pages can return 403 through the egress proxy
*VERIFIED · EP001 · 2026-10-06*

- **Problem:** Target pages were blocked by network policy (proxy 403), so claims could not be read in full.
- **Root cause:** Egress allowlist.
- **Fix:** Record the audit level honestly (AUDITED-INDEX = domain-restricted search result vs read in full), list blocked claims in missing_sources.md, ask the owner to widen the allowlist; re-verify after widening. Cut claims that stay unverifiable.
- **Reuse when:** Any research pass in a restricted session.
- **References:** commit `f8ce0c8`; commit `75ff01e`; `production/ep001-sahara-green:productions/sahara-green/story/missing_sources.md`; `production/ep001-sahara-green:productions/sahara-green/story/source_audit.md`
- **Verification:** EP001 rounds 1-2 and the Northwest Angle 'third pass' after the allowlist widening.
- **Regression test:** none - Network-dependent; procedure.

### topic-decision-by-fixed-rule - Pick the topic by gates + weighted score + fixed tie-break, and let the gate recompute it
*VERIFIED · general · 2026-10-14*

- **Problem:** Asking the owner to choose between topics wastes their time; a free-form choice is not reproducible.
- **Root cause:** No decision rule.
- **Fix:** topics.py: gates (sources, zero_cost), weighted score, auto-decision at margin >= 0.25, otherwise the tie-break order audience_evidence, us, zero_cost, originality, reach; the research gate recomputes the winner from candidates.json and rejects a mismatching decision.
- **Reuse when:** Every episode's research stage.
- **References:** `tools/autopilot/topics.py`; `tools/autopilot/gates.py`; `docs/AUTOPILOT.md`
- **Verification:** EP003: St. Helens led the weighted sum (4.16 vs 4.08) but under the margin, so the tie-break chose the Great Salt Lake; documented in the decision file.
- **Regression test:** `tools/autopilot/test_autopilot.py::test_near_tie_is_decided_by_a_fixed_rule_never_left_to_the_owner`

### usgs-504-bounded-retry - USGS band downloads fail with HTTP 504: bounded retry, never a single try or an endless wait
*VERIFIED · general · 2026-10-14*

- **Problem:** 5 of 24 Landsat tile downloads (EP003) ended with 'HTTP Error 504: Gateway Time-out; removed partial file'; the one-shot script just logged the error and moved on, leaving gaps in the mosaic inputs.
- **Root cause:** Transient gateway time-outs of the USGS download server. Re-requesting the same tile succeeded on the first retry (14-71 s) for all five.
- **Fix:** Use .claude/skills/yt-satellite/fetch_bands.py SPEC.json --confirm: skips tiles whose bands + MTL exist, hard wall-clock limit per attempt (child killed), 4 attempts with back-off 30/60/120/240 s, retries only transient errors (504/502/503/429/timeouts/not ready), stops at once on permanent ones (no download option, --max-mb, auth), prints [i/n] progress, exit 0 only when every tile is complete. usgs_m2m download-bands itself resumes (existing files are skipped).
- **Reuse when:** Any episode that downloads Landsat Level-1 bands or other USGS M2M files, and whenever a download log shows 504 / Gateway Time-out.
- **References:** `.claude/skills/yt-satellite/fetch_bands.py`; `.claude/skills/yt-satellite/usgs_m2m.py`; `.claude/skills/yt-satellite/SKILL.md`
- **Verification:** EP003: the five failed tiles (1985 038032, 1999 039031/039032, 2021 038031/038032) downloaded on attempt 1 with the same logic; 24/24 tiles, 72 bands + 24 MTL present, TIFF headers readable. Offline tests cover 504, timeout, back-off cap, permanent errors, resume and skipping.
- **Regression test:** `.claude/skills/yt-satellite/test_fetch_bands.py::test_http_504_is_retried_with_exponential_backoff_then_succeeds`

### youtube-metrics-unavailable-no-invented-numbers - YouTube audience metrics cannot be read here: score from documented signals and cap the rest
*VERIFIED · general · 2026-10-14*

- **Problem:** Topic selection asks for confirmed audience interest, but youtube.com / the Data API are blocked from this environment and public search results carry no view counts.
- **Root cause:** Network allowlist; no API key.
- **Fix:** audience_evidence above 3 requires a measured signal (metric, value, https URL, date) - e.g. press/festival attention; otherwise the score is capped at 3 and the note says so. Never write a view count that was not read.
- **Reuse when:** Every research stage until a YouTube connector or the owner's Studio exports exist (/yt-retention reads those).
- **References:** `tools/autopilot/topics.py`; `docs/AUTOPILOT.md`
- **Verification:** EP003 research: 7 candidates, Great Salt Lake got a measured signal (Sundance 2026 film, sold-out screenings), all others capped.
- **Regression test:** `tools/autopilot/test_autopilot.py::test_audience_evidence_is_capped_without_a_measured_signal`
