# EP001 review master (1920x1080, 30 fps): report, 2026-10-08

**File (outside Git, scratchpad):** `ep001_build/EP001_review_master_1080p30.mp4`, 747.367 s, H.264 + AAC, 140.8 MB, sha256 `c9ab21e6d8da4ede13ba0e322988062a3f1ffbf0e8c9ec5a27d9d4217ee5403b`.
Narration: the locked Adam audio, sha256 `49e53528cd445a75a71c819c71d542b2f84d8c3898eff34c2a6c9fc7ee7245e2` (unchanged), 185 subtitle cues burned in. No TTS request and no ElevenLabs credit was spent in this stage. No 4K, no upscaling, nothing merged into main.

## yt-qc (long profile): PASS
Pass: container, streams, resolution, frame rate, decode, black frames (none), audio start, captions in the safe zone, shot credits, manifest, segments.
Warnings (none blocking, none waived): `freezes` max static interval **4.73 s** (limit: fail at 5.0 s; thresholds untouched, n = 0.0015, d = 2.5); loudness -17.8 LUFS, true peak -4.6 dBFS (the renderer's constant gain is -0.8 dB; a limiter is not built); duration 747 s is outside the 60-600 s target window; first 10 s has 0 counted information events; 3.05 composition resets per minute (target 5); one composition of 48.7 s without a reset (the water-budget graphic, which builds in 12 steps).
History: first render failed `black_frames` (1.2 s of black at the end of the NASA clip; title-only dark graphic steps) and `freezes` (18 intervals of 5.0-5.9 s on static graphics). Fixes were content, not thresholds: the NASA clip ends on frame 3084 (102.8 s), no dark graphic starts on a title-only step, and every graphic builds in steps (yt-graphics: `hl` emphasis ring, callout build steps, circulation `step_map`, with tests) timed to anchor words of the narration.

## Timing
`check_frame_accuracy.py`: all six video shots (East Oweinat x3 shots, Toshka, East Oweinat close-up, CALIPSO) land on exactly their frames (PSNR 40-46 dB at the expected index; first and last frame differ from the neighbour outside the shot). The 1984 hold is 9.1 s with the 3 percent push-in; East Oweinat ends 1.637 s into scene 19 (approved limit 2.2 s).

## Regression tests
yt-render 74 (compose 25, render 27, video 22), yt-graphics 16, yt-voice 31, yt-captions 28, yt-qc 21, yt-geo 8, yt-satellite 17, narration cues 6: all pass. `lock_check.py`: ALL_LOCKS_OK (script body hash, narration text, nine tone-B frame hashes).

## Open points for the reviewer
1. Landsat location stills: Ounianga (LC09 182/047, 2026-06-22) and Bodele (LC09 183/048, 2026-07-31) use source bands in tone B; Tassili (LC09 190/042, 2025-12-20), Gilf Kebir (LC09 179/044, 2025-11-21) and Kufra (LC09 181/043, 2026-09-19) use the USGS natural-colour browse as delivered, which is not tone-B comparable. Kufra could not be georeferenced (browse GeoTIFF returned HTTP 504, not retried); the pivot fields are identified visually.
2. Bodele is hazy in every cloud-free scene checked; the haze is real, not processing.
3. The NASA CALIPSO end card says 27.6 million tons; the narration and ledger say about 28 (SVS 11775: 27.7). Both round to 28.
4. The shot credit for graphics reads "Graphic: Sahara Green · sources on the graphic"; the channel name is a placeholder to confirm.
5. Pacing warnings above are heuristics of the renderer, not QC failures.
