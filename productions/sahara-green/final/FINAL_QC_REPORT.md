# EP001 final QC report (1080p delivery; 4K not produced by decision)

## Documentary FINAL_EP001_1080P.mp4
- 1920x1080, 30 fps, H.264 + AAC stereo 48 kHz, 747.367 s, 22,421 frames. Full decode: no errors.
- yt-qc --profile long: PASS (0 black frames; longest freeze 4.7 s < 5.0 s fail threshold).
- Loudness: -16.1 LUFS integrated, LRA 2.6 LU, max sample peak -4.2 dBFS (true peak of the normalized narration -1.65 dBTP). No clipping, timings unchanged.
- Frame accuracy of all pre-rendered video shots: ALL OK.
- Full-timeline subtitle overlap (new script production/check_subtitle_overlap_full.py): 185 cues, 4,753 caption-vs-element pairs including all satellite-backdrop graphics: 0 overlaps.
- SCRIPT LOCK v1.1 body sha256 d646001c...f335 matches. Narration not regenerated.
- Heuristic pacing warnings (not failures): 0 information events in the first 10 s; 3.4 composition resets/min; one 48.7 s composition at 443.6-492.3 s (scene 25 narration-timed build steps).

## Shorts (1080x1920, 30 fps)
- SHORT1 51.03 s, -15.6 LUFS (peak -1.7 dBFS); SHORT2 53.37 s, -15.9 LUFS (peak -1.6 dBFS). Full decode OK, no black or frozen frames, burned-in captions, audio sliced from the existing narration.

## Regression tests (all pass after the latest changes)
yt-captions 28, yt-geo 8, yt-graphics 19, yt-qc 21, yt-render 76 (compose+render+video), yt-satellite 17, yt-voice 31 = 200 tests OK.

## Not done / decisions
4K upscale not created (user decision). Nothing published; channel name Orbital Atlas is provisional and its handle/trademark availability is unverified.
