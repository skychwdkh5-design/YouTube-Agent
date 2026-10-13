# EP002 Dubai — 55-second audio-visual test (passage H1-A1) QA

Base: f914bf2 (preflight). One ElevenLabs request was made with your approval: Adam, eleven_multilingual_v2, 695 characters, 1 chunk, status ok. No other paid call. The actual credit deduction could not be read (the proxy key lacks `user_read`); the request size was 695 characters. SCRIPT_LOCK and narration untouched: the passage is contained in the locked narration (hash `d050d5e3...60d` recomputed before and after).

## Files (local, not committed)
- Video: `productions/dubai/visuals/_local_assets/previews/EP002_av_test_H1_A1.mp4`, SHA-256 `5765cd9193fa1fa6013171c4d7706f31c0b3d8a7de33a15dfeb75bf5b95367ca`.
- Narration: `.../audio/narration_H1_A1.wav`, SHA-256 `81b133cbb80b4fef0cb473b453920a2a637d81c9cba5d445249489537653d240`, 47.74 s, word-level provider timings (128 words, text identical to the passage apart from newline versus space).
- Committed, light: `av_test/render_av_test.py`, `motion/engine/av.py`, `av_test/subtitles_H1_A1.srt`, `av_test/narration_H1_A1.voice.json` (text and timings, no audio).

## Technical
H.264 High, yuv420p, 1920x1080, 30 fps, 1656 frames; AAC LC 48 kHz stereo; 55.200 s both streams; 33,448,129 bytes; full decode clean. Audio chain: mono to stereo at unity, 70 Hz high-pass, limiter at -1.5 dBFS, 2.5 s lead, fades. Measured on the final MP4: integrated -15.1 LUFS, LRA 5.4 LU, peak -1.4 dBFS, no clipping.

## Subtitles
17 sentence-based cues from the provider's word timings (two lines at most, longest line 43 characters, no overlaps, cue words identical to the spoken words), 46 px bold with outline, burned in with libass. Sync measured on the rendered video: in 396 of 396 frames (10 fps) where a cue should be visible, text is present; in 65 of 65 frames where none should be, no text. An early render had a bug that printed "\" and "N" in the subtitles; found in QA and fixed before this version.

## Narration to visual alignment (every time comes from a spoken word)
| visual event | word | video time (s) |
|---|---|---|
| '2000' ticker (shot 1) | 2000 | 3.09 |
| instrument chip | satellite | 4.18 |
| hard cut to 2003 frame | November (2nd) | 10.68 |
| 'three years' chip | three years | 17.99 |
| cut to ISS photograph | More than | 19.29 |
| '2022' ticker | decades | 19.96 |
| photograph-not-satellite chip | astronaut | 21.94 |
| Jumeirah bracket | palm-shaped | 26.22 |
| Jebel Ali bracket + move | islands stand | 26.92 |
| cut to Palm Jumeirah 2006 | So how | 28.79 |
| pull-out starts | And what happened | 31.57 |
| Dubai plates | This is Dubai | 34.28 |
| project rings | put that idea | 44.87 |
| cut to 2000 frame, ticker | year 2000 | 48.78 |

Total 55.2 s = 2.5 s lead, 47.74 s narration, 4.96 s closing hold with image credits and fade.

## Sources and attribution on screen
2000 frame: NASA ASTER (Terra), 11 Nov 2000; 2003 frame: 4 Nov 2003; ISS: astronaut photograph ISS067-E-3785, 6 Apr 2022, Nikon D4, cropped and contrast-enhanced by NASA, labelled "not satellite imagery"; 2006: NASA ASTER (Terra), 18 Sep 2006. ASTER frames say "colours as published" and "view rotated 90 degrees for display". Credit chips at the end name NASA Earth Observatory, ASTER on Terra and the ISS Crew Earth Observations. No registration, scale or map is claimed; images are separate stills joined by hard labelled cuts.

## Visual QA
16 frames at word events plus full-size checks: text readable on bright and dark ground, no collisions in a 0.1 s sweep of the layout (including the subtitle band), no black borders, camera moves smooth (v2 spline, motion blur only in the pull-out). Known limits: the year-2000 shot repeats in the closing hold (justified by the line "back to the year 2000"); the 2000 and 2003 shots share a framing on purpose; amber brackets and rings are restrained and small in the ISS and wide shots; Palm Deira is not marked in this passage; the ISS photo's right-hand sea contains a cluster of islands that is not named.
