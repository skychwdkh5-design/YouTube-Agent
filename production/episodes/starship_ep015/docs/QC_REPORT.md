# EP015 Starship Flight 15 — QC report (2026-11-15)

**Status:** QC passed. **Not uploaded and not published.**

## Files and SHA256

| File | SHA256 |
|---|---|
| `final/EP015_Starship_1080p30.mp4` | 5f33f63e177148ece1bf7c1455912699b4f92a00961db3e1b321079491f52067 |
| `final/EP015_captions_en.srt` | a339f912ce475703d320d4e91d149aa201350e833531882aa86a422f1bdea35a |
| `cover/EP015_cover_1920x1080.png` | 7733d5034f33fb3bc4a4dbeb8ca2d518b5571bc2f9c1b6a1f18e3fd493e5b3b7 |
| `cover/EP015_cover_1280x720.jpg` (YouTube upload) | 3c9e2cbcaa3b5409bcbc0811631170cebd620a792d4a8f44ebc1b4b8130661a0 |
| `pilot/EP015_pilot_0-30s.mp4` (test, older cover) | c92234ae284a05c385bfbf91632ff54223c9e629b2294b4419eb9d7c70ca22e4 |
| `voice_timed/narration.wav` (Adam) | bc544ad8b458d0a483a11be68efb78e36545195c511bd963af6fc441c881c420 |

All paths are under `/mnt/project-files/starship/EP015/`.

## Technical

| Check | Result |
|---|---|
| Video | H.264, 1920×1080, 30 fps, 11,760 frames, 6:32.0 |
| Audio | AAC, 48 kHz stereo |
| Full decode | OK, no errors |
| Black frames (>0.1 s) | 0 |
| Loudness | −14.1 LUFS integrated (target −14 to −16), LRA 4.0 LU |
| True peak | −1.3 dBTP (limit ≤ −1) |
| Size | 93 MB |
| Render | 11,760 frames in 1,575 s (7.5 fps, 4 processes), no errors, no reprocessed frames |

## Cover and frame 0

- Thumbnail gate (`thumbcheck.py`): **PASS (objective part)**. The first version failed, so it was revised:

  | Metric | First version | Revised | Threshold |
  |---|---|---|---|
  | Contrast (luma std) | 41 | 62.2 | ≥ 58 |
  | Saturation | 0.39 | 0.65 | ≥ 0.40 |
  | White headline mass | 0.4 % | 2.8 % | ≥ 2.5 % |
  | Yellow accent | — | 1.3 % | ≥ 1.2 % |

- The revision added a larger "THEY" headline and a cover grade that eases out over the first 6 s.
- Frame 0 of the MP4 vs the cover PNG: PSNR 36.7 dB, i.e. the same image apart from H.264 compression.
  Frame 0 has no subtitle and no label.

## ATLAS motion (`engine/qc.py`, all 11,760 frames)

| Check | Result | Threshold |
|---|---|---|
| Foot slide during contacts | 0 px | ≤ 1 px |
| Joint jerk p99 | 3.5 px | ≤ 5 px |
| Joint jerk max | 18.6 px (before the fix: 116 px) | ≤ 25 px |
| Head off-screen | 0 frames | 0 |
| Mouth open in pauses | 0.6 % of pause frames | < 2 % |
| Lip-sync correlation with the WAV | 0.874 | ≥ 0.8 |
| ATLAS joints in the subtitle zone while a cue is on screen | 0 frames | 0 |

## Content and rights

- No SpaceX media is used. Every shot carries an ILLUSTRATION, SCHEMATIC or VISUALIZATION label.
- The Earth backdrop is NASA SVS 5570, credited.
- Score and SFX are original.
- Details: `docs/RIGHTS_AND_FACTS_LEDGER.md`.

## Fixes made after the first QC pass

Only the affected frames were re-rendered (frames 0–300 and 3300–3750); there was no full re-render.

1. The cover failed the channel style gate. It was revised as described above.
2. On the abort map (1:50–2:02), the "TOWER CATCH CALLED OFF" and "GULF OF MEXICO" labels overlapped the info boxes. They now fade out when the boxes appear.

## How it was reviewed (honest)

- **Motion:** checked with per-frame numeric QC on every frame, plus frame strips and stills (0/5/12/20/60/120/283/290/300 s). **I did not watch it in real time.**
- **Audio:** measured only (loudness, peak). I did not listen on speakers or headphones.
- The owner should watch it once at full speed before giving approval.

## Known limits

- The duration is 6:32, not 7:00. The narration with breathing pauses sets the length.
- The owner's joint sheet included forearm and glove pieces. They are not used yet: their palette differs from the base drawing and they show only one pose.
- **Booster cause:** unconfirmed as of Nov 15. Re-check the sources before publishing.
