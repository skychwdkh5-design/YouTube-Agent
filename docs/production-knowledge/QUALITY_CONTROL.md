# Quality control (what to run before showing a render)
Tools: `.claude/skills/yt-qc/qc.py`, `productions/dubai/preview/monotony_audit.py`, ffmpeg filters. Status vocabulary: TECHNICALLY_VALID -> VISUALLY_REVIEWED -> USER_APPROVED (user only).
## Checklist (all **[VERIFIED]** as workable)
1. `qc.py FILE --expected-duration SEC --profile long`: streams, 1920x1080, 30 fps, h264/aac, size, full decode, black frames, audio start, loudness. Takes about 2-5 min on 9 minutes of 1080p; run it in the background.
2. Black frames: `blackdetect` flags any frame where >= 98 % of pixels are darker than about 10 % luma. A near-empty dark card counts. Lifted card background (Y mean ~31), content in frame 0, dissolve entries, no fade-to-black credits.
3. Freeze: `freezedetect=n=-55dB:d=2.0`; accept only declared holds.
4. Jumps: frame-difference on 96x54 grey; every spike > 30 must sit on a scene boundary or a declared move/cut (slide entry, whip window, intra-scene cut). Unexplained spikes = defect.
5. Monotony: `monotony_audit.py` (motion < 3 = LOW_MOTION).
6. Captions: no overlaps, <= 2 lines, <= 70 chars/cue; the cue words joined must equal the locked text word for word (checked); times come from provider words.
7. Audio: LUFS/true peak from loudnorm; first narration word time vs scene plan; silence only where designed.
8. Sync table: error between cue times and word starts (`sync.plan`); by construction exact at word starts for events.
9. Source/label audit: every image has a chip with source/instrument/year; no scale bars; ISS photo labelled "not satellite imagery".
10. Report what was NOT verified: nobody listened to the audio, pronunciation unchecked, frames reviewed as contact sheets, not continuous playback.
## EP002 final results
See `productions/dubai/final/QA_REPORT.md`.
## Added after EP002 v2
- **Cut-off text audit** `productions/dubai/preview/qa_text_bounds.py` **[VERIFIED]**: renders every scene at 0.5 s steps, spies on `SDraw.text` and flags any visible glyph box outside the frame. It found real defects the black/freeze/spike scans cannot see: callout labels clipped at the frame edge (C1, D1, B3), a label running off-frame (D5 tags), a label for an off-screen landmark overlapping a header (E5), filmstrip labels cut at the edge (E1). Fixes now in `kit.Canvas.callout` (clamp text to a 24 px margin and the 96..H-90 band, skip landmarks outside the frame, dark text stroke) and E1 (labels fade before the edge). Run it before every mux.
- Run-time: about 2-3 min for the whole film at 960x540 logical scale.
- Pronunciation: no local speech recogniser is available (PyPI/HF blocked, no whisper/vosk). Only a plausibility check is possible: provider word durations per syllable against the narrator mean (0.199 s/syllable, sd 0.069). EP002: ASTER 0.43-0.70 s (two-syllable word, not spelled out), Jumeirah 0.45-0.67 s, Deira 0.30-0.56 s, Nikon 0.48 s: plausible; vibroflot 0.91 s (3 syllables, about +1.5 sd: slow but not garbled). This is **not** a listening test.
- Caption/audio sync check **[VERIFIED]**: onsets of speech after pauses >= 0.25 s (20 ms RMS, -42 dB) vs SRT cue starts: 159 of 228 cues matched, mean offset +0.020 s, p95 0.057 s, max 0.125 s.

## Release gate additions (EP002 v3, 2026-10-13) **[VERIFIED]**
- **Legibility audit at 540p** `productions/dubai/preview/qa_legibility.py`: for every visible text draw (1 s steps) records size in px at 540p and the WCAG contrast between the text colour and the median luminance under its box (glyphs are a minority of the pixels; pills count as background). Flags: size < 12 px, contrast < 3.0 for text >= 18 px, < 4.5 otherwise. It found: D2 labels at 1.1-2.1:1 (stacked muted text on busy imagery), H2 year ticks 1.7-2.0:1, C6 "2011" 2.8:1, callouts on sand/ice 2.0-2.9:1 (A2, B2, B5, E5), 11 px disclosure chips (H3, A3, D1). After the fixes the only flags left are callouts/chips at 3.5-4.5:1 on their own dark pill and transient fade-in frames.
- **Static-run metric**: 96x54 grey, difference between frames 1 s apart; a run >= 2 s below 1.5 = static hold. Whole-frame metric: it is blind to small moving elements (scan line, counters), so a residual flag is evidence to look, not proof. EP002 v3: E6 credits 14.1 s (by design), D5 5.5 s (anatomy card with scan line + zoom + tag pops), B5 2.5 s, C3 2.3 s, B4 1.9 s, B3 1.7 s (below the 2 s line: improvements proposed, not applied).
- **Overlap check by eye is still needed** for layers drawn at different times: the H2 timeline backing covered part of the date label, the A3 schematic caption was wider than its panel; neither is caught by the frame-bounds audit. Review the changed scenes at 540p after every fix.
- Audio splice check: max |sample difference| within +-30 ms of every scene cut <= 0.041 (speech p99.9 is 0.14): no clicks; provider's largest natural pause 1.12 s; silences >= 1.2 s are the designed H4 title hold, the C4/C5 paragraph pause (1.12 s + 0.35 s lead) and the end tail.

## Known QC friction
`audio_starts <= 1.0 s` measures the first audio above -40 dB, not speech: a silent cold open fails it (EP002 v1: 3.48 s), an atmosphere bed passes it (v2: 0.77 s) without changing when the voice starts; record which of the two you rely on. `loudness` warns for the Shorts range only.

## V4.1 tools (2026-10-13)
- `qa_contrast.py [--v4]`: WCAG ratio of every Canvas.text/kinetic run against the TEXT-FREE render of the same frame (75th/25th luminance percentile); skips entry-transition windows (they re-render the previous scene). `qa_legibility.py --v4 --need 4.5` kept for the old median method (per-letter kinetic text gives false flags). Hook V4.1 + A1: 0 runs below 4.5 (A1 t<1 s flags are transition blends).
- VERIFIED: audio continuity check = compare `audio_raw.wav` with `narration.mp3` at lag 0/-1 sample: zero difference in all scene windows (no repeated or missing speech); splices are silent.
- VERIFIED: build flags `--hook`, `--preview` (hook + A1 = 52 s), `--full4` in `build_final.py`; unchanged segments can be reused.

## Release package (2026-10-13)
- VERIFIED: pre-upload checklist used for EP002: concatenate media-branch parts and compare SHA-256 with the master; full decode (`ffmpeg -i f -f null -`); chapters validated (starts 0:00, >= 3, each >= 10 s) and aligned to scene starts (rounded, speech begins ~0.35 s later); description facts checked line by line against the locked script; thumbnail = two real NASA frames from the same pixel box + dated labels; copyright table in `productions/dubai/release/COPYRIGHT_CHECK.md`.
- RULE: no YouTube connector in the session -> deliver the package and Studio steps, never claim an upload.
- OPEN: ElevenLabs plan/commercial-use status is unknown to the agent; the owner confirms it before publishing.

## Final audit additions (EP003 V2, 2026-10-15)
- Monotony: `python3 tools/autopilot/visual_runs.py VIDEO --timeline productions/SLUG/timeline.json` - runs > 10 s and a base picture above ~40 % of screen time need a narrative reason. **[VERIFIED]**
- Phone check: downscale review frames to 390x219 (portrait inline) and 699x393 (landscape) and read every date, legend and label; text under ~7 pt there fails. **[VERIFIED as a method]**; the size fix is **HYPOTHESIS** until a full render (`mobile-legibility-hud-text`).
- Pronunciation cannot be machine-checked in the cloud container (no ASR model or package source); list timecodes for the owner.
