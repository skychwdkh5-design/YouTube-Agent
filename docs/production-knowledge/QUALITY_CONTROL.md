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
## Known QC friction
`audio_starts <= 1.0 s` fails when a deliberate silent cold open is used (EP002: first word at 3.48 s); decide per episode and record it. `loudness` warns for the Shorts range only.
