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

## Known QC friction
`audio_starts <= 1.0 s` measures the first audio above -40 dB, not speech: a silent cold open fails it (EP002 v1: 3.48 s), an atmosphere bed passes it (v2: 0.77 s) without changing when the voice starts; record which of the two you rely on. `loudness` warns for the Shorts range only.
