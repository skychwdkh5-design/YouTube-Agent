# Audio normalisation test (separate file; the locked narration and the approved master are untouched)

Script `production/audio_normalization_test.py`; data `production/audio_test/AUDIO_NORMALIZATION_TEST.json` and `alternatives.json`.
Locked source `narration.wav` sha256 `49e53528…45e2`: **identical before and after the test** (checked). Test output (local, 66 MB, not in Git): `scratchpad/audio_test/narration_norm16_test.wav`, sha256 `114ba576…7a32`. No TTS request.

## Why the master is at -17.8 LUFS
The raw narration measures **-17.03 LUFS integrated, true peak -0.66 dBTP, LRA 2.6 LU**. The renderer targets -16 LUFS but caps the peak at -1.5 dBTP, so its constant gain is `min(-16 - (-17.03) = +1.03 dB, -1.5 - (-0.66) = -0.84 dB) = -0.8 dB`: it cannot raise the level and lowers it by 0.8 dB. Result: -17.8 LUFS, true peak -4.6 dBTP.

## Test: -16 LUFS
One constant linear gain of **+1.03 dB** (no compression, no EQ, no speed or timing change), then a transparent look-ahead peak limiter that acts only where a sample would exceed -1.8 dBFS (a 6 ms Hann-shaped gain dip around that sample).
| | integrated | true peak | LRA |
|---|---|---|---|
| before (locked source) | -17.03 LUFS | -0.66 dBTP | 2.6 LU |
| **after (test)** | **-16.09 LUFS** | **-1.65 dBTP** | 2.5 LU |
| current approved master (for reference) | -17.8 LUFS | -4.6 dBTP | n/a |
Checks: samples in = samples out = 32,958,464, 44.1 kHz, duration 747.357 s (timing unchanged); 0 clipped samples; sample peak -1.8 dBFS; outside the limiter's dips the output equals the input times the gain exactly (maximum deviation 0.0); dynamics preserved (LRA 2.6 to 2.5 LU).
**The cost, stated plainly:** 30,322 samples (0.09 %) exceed the ceiling after the gain, because the narration is peaky (peak 0.7 dB below full scale, mean level -17). The limiter's dips cover 42.0 s (5.6 % of the duration) with a **maximum reduction of 2.13 dB**; typical dips are well under 1 dB. I have not listened to it for artefacts; two 38-s excerpts of the proposal section are provided for an A/B listen: `AUDIO_A_current_narration_357-395.mp3` (locked source, no gain) and `AUDIO_B_norm16_test_357-395.mp3` (test).

## Alternatives (same method, measured on the whole narration)
| target | gain | limiter touches | max reduction |
|---|---|---|---|
| -16.0 LUFS | +1.03 dB | 42.0 s (5.6 %) | 2.13 dB |
| -16.5 LUFS | +0.53 dB | 21.6 s (2.9 %) | 1.63 dB |
| -17.0 LUFS | +0.03 dB | 6.6 s (0.9 %) | 1.13 dB |
Any target above the present -17.8 needs some peak limiting, because the raw true peak is -0.66 dBTP and the -1.5 dBTP ceiling would otherwise require attenuation. -16.5 LUFS is the milder compromise.

## Not done
Normalisation is not applied to the approved master and not to the revised sections (they carry the master's -0.8 dB so that they sound like the master). Awaiting authorisation.
