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

## Hook atmosphere (EP002 v2, 2026-10-13) **[VERIFIED]**
Decision (director): replace the 3 s of absolute silence in the cold open by a local atmospheric low drone. Code: `productions/dubai/preview/atmosphere.py` (`build_final.py --mux --atmo`). No music, no stock, no API, no ElevenLabs request.
- Sound: partials 41.2 / 61.7 / 82.4 / 123.5 / 164.8 Hz (+/-0.35 Hz left-right detune for width), noise bed low-passed at 160 Hz, 0.12 Hz breathing, fixed seed 2026 (deterministic).
- Envelope: raised-cosine swell from silence, peak at 2.9 s (before the voice at 3.35 s), release `0.5(1+cos)^2.4` to silence by 6.2 s: about -6 dB one second into the speech, -26 dB two seconds later (so it never competes with "November 2000...").
- Level: peak momentary loudness of the atmosphere alone -28 LUFS (gain -10.9 dB on a half-scale synth); added AFTER the narration was normalised. Per-second RMS (dBFS): atmosphere -52, -39, -32, -28, -37, -61 for seconds 0-5; narration from second 3 about -22.
- The narration is not touched: the mix is an integer sum, `mix - atmosphere == narration` sample for sample (checked), identical to the normalised narration file after 5.85 s. Result: integrated -16.1 LUFS, LRA 2.9, sample/true peak -4.5 dBFS, 0 clipped samples.
- What it is not: it does not make the narration start earlier (first word 3.35 s; first RMS onset 3.475 s).
## yt-qc `audio_starts` after this change
The rule measures the first audio above -40 dB (`silencedetect`), not the first word. With the drone it reads 0.77 s and passes. That pass reflects the atmosphere, not speech: the narration still starts at 3.35 s. Record it as such; do not present it as "speech starts within 1 s". If the silent cold open had been kept, the 3.48 s fail would have been the honest exception.

