# EP004 REVIEW 720p - QA (2026-10-16)
Status: TECHNICALLY_VALID + VISUALLY_REVIEWED (partial). USER_APPROVED: NO.
File: review/EP004_REVIEW_720p.mp4 (media branch media/ep004-jakarta-review), sha256 29cd341e0f5980151dbb36e2c8f4f665f889ec17cb998ef9122930d6d80d6352
Technical (measured): 1280x720, 30 fps, H.264 + AAC stereo, 428.13 s; loudness -15.9 LUFS, peak -2.1 dBFS; black frames 0; freezes >3 s 0; 12,844 frames.
Narration: ElevenLabs Adam, one pass, 5,790 chars (limit 5,800), word timings 1,013/1,013, no warnings. Captions from provider word times. Synthesised CC0 sfx.
Visual review: 54 frames (every 8 s) + 8 re-checks after fixes. Fixed: suspect-card text overlap, bar-label clipping, dyke hidden by water, hotspot/damage place markers off-screen, label overlaps.
Evidence classes on every frame: REAL SATELLITE (Landsat, optical context, NOT subsidence), DATA CARD, ILLUSTRATION, STYLISED MAP. No ESA frame; no EVIDENCE MAP PENDING; 2.5-D, not 3-D.
NOT verified: pronunciation (cannot listen; Tanjung Priok 0.55+0.67 s, Cengkareng 0.98 s, Pademangan 1.01 s, Perdanakusuma 1.08 s), motion smoothness between sampled frames, mobile-size legibility (orbitalatlas.mobile_qa not run), monotony report not run.
Honest limits: "west"/"northwest coast" markers are general directions (extent not shown); Tanjung Priok is a named place; hotspot/bowl glyphs are schematic, not map positions; beat 10 lost "one to four inches" to fit the credit limit.

## FINAL POLISH (v2, 2026-10-16) - audio, script and word timings unchanged (decoded audio md5 identical to v1)
v2: review/EP004_REVIEW_720p_v2.mp4, sha256 104963664b0e1ddf... (full hash in media branch SHA256SUMS). v1 kept for comparison.
Technical v2: 1280x720, 30 fps, 428.13 s, -15.9 LUFS, peak -2.1 dBFS, black 0, freeze>3 s 0.
Dynamics (picture motion, caption band excluded): seconds below motion threshold 294/428 (v1) -> 81/428 (v2); median motion 0.18 -> 1.59. Remaining low-motion runs: 87-97 s (radar diagram, LOS/vertical explanation), 147-151 (end of cut-away), 290-294, 317-328 (trend schematic), 395-404 (dyke schematic).
Mobile readability (6.1-inch phone rule: text >= 30 px at 1080p, captions >= 48 px): v1 86 text-size issues (smallest 15-25 px, 14 of 20 styles) -> v2 0; safe-area 6 -> 0; contrast 1 -> 0; remaining 7 text overlaps are single sampled frames inside dissolves (151.5, 190.5, 316.5 s).
Pronunciation: NOT verifiable with free tools here (no ASR/phonemiser installed; network limited). Listening clips cut from the existing narration: qc/pronunciation/*.mp3 (Tanjung Priok ~182 s, Mutiara/Cengkareng/Pademangan ~258-263 s, Perdanakusuma ~357 s). No ElevenLabs request made.
