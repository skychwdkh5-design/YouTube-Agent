# EP004 S3 proof - technical report (2026-10-15)
Level reached: **TECHNICALLY_VALID** (proof). Audio QA is for an *effects-only temporary track*, not a final mix. Source: `proof/qa_proof.py` -> `qa/proof_qa.json`.

| check | result |
|---|---|
| file | `ep004_s3_proof.mp4`, 1,789,512 B, sha256 `5d38f15c877c0b979f1ef7cc1712cbceb84612d5df232c1fc911df3282d0687e` |
| format | H.264 1920x1080 yuv420p, 30 fps, 405 frames = 13.500 s; AAC 48 kHz stereo; decode of all 405 frames OK |
| yt-qc | PASS (streams, resolution, fps, codecs, size, duration vs 13.5 s, truncation, full decode) |
| orbitalatlas.qa.run_video | ok, 0 issues (blank/black/jumps/static/transition checks; the 1.5 s placeholder hold declared) |
| black frames (ffmpeg blackdetect d=0.04) | 0 |
| freeze runs (freezedetect n=0.001, d>=0.5 s) | 0 |
| scene transition | 1 flash dip (0.5 s, peak 0.7) at 11.5-12.0 s, all 24 frames of 11.4-12.2 s viewed - grey peak frame at ~11.75 s is intended |
| text collisions / outside title-safe frame | 0 (unit-tested at every 0.25 s and checked on the rendered frames, mobile_qa) |
| audio | integrated -20.7 LUFS, true peak -4.8 dBFS (effects only, +8 dB proof gain, alimiter 0.70). The repo's final-mix target (-16 LUFS / <= -1 dBTP) applies to the narrated master, not to this silent-voice proof; effects will be ducked >= 12 dB under the narrator there |
| word-level caption sync | **not applicable** (no narration yet; captions are written, timed by hand, flagged as estimated) |
| source attribution | chip text: ILLUSTRATION / PLACEHOLDER; no third-party data in the file (no credit needed). Sentinel-1 is named as the mission only |
| sha256 | above; also on `media/ep004-s3-proof` |
| determinism | each frame is a pure function of t (unit-tested); two renders of the same still are byte-identical |
Render cost: 405 frames, 4 workers, **112 s wall / ~6 min CPU** for 13.5 s of video (about 8.3 s wall per second of video, 2x supersampled 3840x2160 canvases); stills render in ~1 s.
Unit tests: orbitalatlas 182 (24 new), autopilot 136 - see PROOF_REPORT.md for the final run.
