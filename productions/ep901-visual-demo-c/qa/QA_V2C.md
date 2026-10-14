# ep901 / Visual Engine V2c demo - QA (2026-10-14)

Status: **TECHNICALLY_VALID + VISUALLY_REVIEWED by the agent** (frames at 1.5 fps looked at, two contact sheets). **Not USER_APPROVED.**
Master: branch `media/visual-engine-v2c-demo`, sha256 `8c85f5cda551444e9c7a8bb24c6aedefc435d1b056a4d6df1f910983fd4e3df7`, 97,055,139 bytes.

| check | result |
|---|---|
| format | 1920x1080, 30 fps, 803 frames, 26.77 s, H.264 + AAC |
| loudness | -15.7 LUFS integrated, LRA 2.2 LU |
| freezes (>2 s) | 0 |
| orbitalatlas.qa (with intended changes as cuts) | ok, 0 issues |
| voice onsets in the mix | 62/65; failed: 'straight' 1.30, 'it' 6.18, 'flows' 14.40 (an effect tail in the pause before the word; 'flows' also fails voice-only) |
| captions | 17/17 cards within +-4 frames |
| effects under the voice | >= 13.9 dB (5th percentile while speaking), 12 cues, all original CC0 |
| pacing | max gap between visual changes 1.93 / 1.68 / 1.32 / 1.79 / 1.89 s per sentence (limits 4 / 3 / 3 / 6 / 3) |
| dates | image July 2022 (cyan IMAGE stamp); event 1959 'causeway was finished' in amber, image stamp shown alongside; the July 2022 level is on the number card |
| duplication | number shown once (card, caption hidden); place names: one label each (lift or callout) |

Seen on frames: plane tilt lands before the zoom (sharp at 0.7-1.3 s); contour light on the lake outline; impact card 'IT IS A RAILROAD';
CAUSEWAY / GILBERT BAY / GUNNISON BAY lift from the caption to the map, caption copy dimmed; callouts TO THE SOUTH / TO THE NORTH; number card count-up to 4,190.2 FEET.
Not verified: subjective sound balance on headphones/TV speakers; vertical (Shorts) layout; behaviour with a real narrator.
Noted: during the 0.4 s count-up intermediate values (e.g. 3,393.4) are visible for a few frames; 13.3-14.7 s holds one caption over a static map (within the calm limit).
