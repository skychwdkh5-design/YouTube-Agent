# Audio / video sync from provider word timings
Code: `productions/dubai/preview/sync.py`, `build_final.py`. Timing source: `narration.voice.json` words (ElevenLabs character alignment mapped to words; kept only when it matches the text exactly).
## Method **[VERIFIED on EP002]**
1. Locked VO lines -> word index ranges (`sum(words per line)` must equal the number of timed words; EP002: 1,225 = 1,225).
2. Scene window = first word of its first VO line - 0.35 s (LEAD) ... first word of the next scene - 0.35 s; last scene ends 2.4 s after the last word; 3.0 s silent cold open before scene 1; optional held seconds after a scene (`EXTRA`, H4 +1.8 s so the title is readable; silence is inserted in the audio at the cut inside the pause).
3. The scene functions keep an ESTIMATED timeline (`tw(i, n, d) = 0.5 + i*(d-1.1)/n`). Two real->estimated clocks per scene:
   - **word-level clock** (piecewise linear, exact at every word start): events (labels, counters, ring draw-on, cuts) fire on the spoken word;
   - **smooth clock** (monotone cubic through sentence starts; Fritsch-Carlson): camera paths, long eases (`seg` windows >= 3 s), A1 frame index; `kit.CLK`/`tm()`.
4. Captions: cues from word timings (<= 8 words / 70 chars / 4.2 s, break at sentence ends from 2 words, at commas from 3), gaps < 0.35 s closed, no overlap; burned in and exported as SRT/VTT with global times.
5. Audio: narration slices placed on the final timeline, 20 ms fades at cuts, silence elsewhere, two-pass `loudnorm` to -16 LUFS, TP -1.5 dBTP, 48 kHz stereo AAC 192 k.
## Measured
- Sentence-only warp: mean |cue error| 0.33 s, max 2.5 s (credits scene), typical max about 1 s **[VERIFIED]** -> not good enough for word cues.
- Word-level clock: exact at word starts by construction; smoothing the word-level warp (Gaussian) gave mean 0.11-0.19 s but 0.2-3x speed pulses **[VERIFIED]** -> use two clocks instead.
- Scene durations real/estimated: 0.69-1.08 for most scenes, E6 1.76 (slow credits reading) **[VERIFIED]**; narration 515.251 s -> film 522.8 s.
## Rules
Never edit the spoken text to fit the picture (locked); never estimate word times (yt-voice keeps `timing: null` instead); verify the word->scene mapping count before rendering; re-run `sync.plan` after any change of scene durations.
