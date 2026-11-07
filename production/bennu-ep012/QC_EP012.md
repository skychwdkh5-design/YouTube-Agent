# EP012 Bennu — QC report (2026-11-07)

Final: `EP012_Bennu_final_1080p30.mp4` sha256 `8cbcfc73256c6867b64dd30caddd2809c9556820284bf0473f4490c52128d290`, 6:01.5, 178 MB (CRF 22 delivery encode of the CRF 18 master sha256 29226238…, 629 MB, kept in the session only; qc.py PASS on both).
Not uploaded, not queued.

## Checks performed

| Check | Result | Evidence |
|---|---|---|
| Format 1920×1080, 30 fps, H.264 yuv420p + AAC 48 kHz | PASS | `yt-qc/qc.py` (all checks pass) |
| Full decode of every frame | PASS | qc.py `full_decode`, 10 843 frames, streams aligned |
| Duration vs timeline 361.533 s | PASS | qc.py |
| Black frames (≥0.1 s, 95% black) | PASS | ffmpeg blackdetect: none. A 1.4 s black start of the NavCam clip found in v3 was cut. |
| Static freezes ≥3 s | PASS | ffmpeg freezedetect: none |
| Loudness | PASS | −14.6 LUFS integrated, true peak −1.0 dBFS, LRA 2.6 |
| Source files | PASS | all 10 `silent/` hashes match `compact_manifest.json` |
| Missing material / placeholders | PASS | every shot renders a source or a finished illustration; reviewed on contact sheets (1 frame / 3 s for the whole film, 1 frame / 0.5 s for 0–15 s) |
| Speech sync | PASS (by construction + spot check) | every shot starts on a word time from the provider timings; caption chips appear on the spoken word |
| Caption/label readability | PASS (static frames) | labels 25–56 px, dark backing; checked on full-res frames |
| First 15 s | PASS | frame 0 = cover composition (real SamCam image, graded); Adam starts at 0.25 s; movement from frame 1; burst at 13 s; sinking reconstruction at 18 s |
| Cover | PASS (objective) | `thumbcheck.py`: saturation 0.51, luma std 64.9, white 2.5%, yellow accent; viewed beside reference covers and at 168×94 |

**Not done:** a real-time viewing of the motion with sound. I reviewed decoded frames and sheets only, so judder, pacing and audio feel need your watch.

## Accuracy and labelling

- Every shot carries a type label: REAL IMAGES (SamCam, NavCam 2, spacecraft camera, before/after), NASA VIDEO (capsule), NASA ANIMATION / DATA-DRIVEN RECONSTRUCTION, NASA DATA MODEL, ILLUSTRATION · NOT TO SCALE.
- SamCam is labelled "still photos, sped up"; NavCam "10 fps image sequence"; no interpolated in-between frames (nearest real frame only).
- Contact clock: T = M04 file time − 10.6 s (contact frame in the close-up; thrusters appear at 16.6 s = T+6). Labelled "approx."; slowed sections show the factor.
- M10 before/after order checked against NASA SVS 13837 stills (Nightingale_Before/After.png, correlation 0.965/0.966): before = 2019-03-07, after = 2021-04-07.
- 8 m ruler drawn from NASA's own 10 m scale bar; labelled "size only, not position".
- "Kept sinking" shown as a ghost arm, labelled "NASA analysis · conditional result, not what happened".
- Not claimed: liquid or hollow Bennu, crash, manual rescue, life/DNA/RNA, real-time footage, single-touch crater.
- Audio: Adam narration (one paid run), generated low noise bed and two soft low hits. No NASA audio, no music.

## Known limits

- The illustrations are code-painted 2.5D (textured gradients, painted grains, simple props). They follow the OA direction but are simpler than the painted reference sheets.
- M11 (capsule) is a 720p source shown at 1.7–1.8× zoom for 3.8 s, so it is soft.
- The chemistry epilogue (~23 s) is a text-card scene over painted grains.

## v2 (2026-11-07)

File `EP012_Bennu_final_v2_1080p30.mp4`, SHA-256 `2114ce02723fcc0e97393e662356614d09fd15e036b093275769ec900d8efece`, 183 588 994 bytes, 1920×1080, 30/1, 362.100 s. Changes: `CHANGES_v2.md`.

| Check | Result | Evidence |
|---|---|---|
| qc.py (format, duration 362.1, streams aligned, 10 863 frames, full decode) | PASS | 16/16 checks pass |
| Black frames | PASS | blackdetect: none |
| Static freezes ≥3 s | PASS | freezedetect: none |
| Loudness | PASS | −14.6 LUFS, true peak −1.1 dBFS, LRA 2.6 |
| Speech sync | PASS (spot check) | speech onsets at 0.51 / 8.91 / 14.85 / 17.40 / 19.76 / 314.46 / 333.73 s vs. word timings 0.44 / 8.82 / 14.79 / 17.33 / 19.70 / 314.42 / 333.70 s |
| Motion in changed scenes | PASS (numeric) | per-frame luma difference: no stalled frames in 0–30, 105–189, 199–212, 311–348 s; cross-sections median 0.4–0.7, p95 ≤ 4.9; spikes only at planned cuts and at the source cadence of SamCam/NavCam photo sequences |
| Missing material | PASS | contact sheets 1 frame/3 s (whole film) and 2 frames/s (0–15 s) |
| Cover | PASS (objective) | regenerated from new frame 0; thumbcheck PASS |

**Not done:** real-time viewing with sound. Checked by decoded frames, sheets and numeric motion/audio analysis only.
