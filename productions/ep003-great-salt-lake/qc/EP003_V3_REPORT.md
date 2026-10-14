# EP003 V3 - REVISE plan executed (2026-10-15)

Master: sha256 b0b28c62d6f37c5e190418fa486e7e2be97f05965227dd195c6fb217f67456ce, 1920x1080, 30 fps, 6:12.57, -15.9 LUFS, true peak -2.4 dBFS.
Same narration, music-free mix and word timings as V1/V2 (no ElevenLabs request). Branch `media/ep003-gsl-final-v3`.

## Status: RELEASE_CANDIDATE (not USER_APPROVED)
All automatic gates pass (yt-qc PASS, orbitalatlas.qa ok, MOBILE_READABILITY_QA ok, captions 198/198, 38 texts linted clean); visually reviewed by the agent.
Open: owner listening (pronunciation), real-phone viewing, approval.

## Changes (BEFORE/AFTER sheets: media branch `audit/`)
| time | before (V2) | after (V3) | why |
|---|---|---|---|
| all | image date 19 px, chip 18 px bottom-left, legends 32 px | 30 / 30 / 35 px, chip top-left, stamp under it | M1 phone legibility |
| all | white captions on bright salt flats (2-3:1) | soft dark band, >= 3:1 | M1 contrast |
| 0:12, 4:29-6:06 | shorelines ~2 px | 5 px with a dark under-stroke | M2 |
| 3:27 | arrow + '60 KM' | arrow only | number not spoken by the narrator |
| 3:31-3:49 | July 2022 picture, camera pulls out | Gilbert Bay traced and labelled 'DEEP BRINE LAYER NEAR THE BOTTOM · USGS', camera holds on the bay, layer leaves on 'dissipated by June 2014' | M3, claim C25 |
| 3:49-4:00 | Aug 1986 picture only | + July 2022 shoreline on 'not always been too low' | M3, claims C1/C7 |

## MOBILE_READABILITY_QA (qc/mobile_qa.json)
373 frames (1/s), 0 issues. Smallest sizes at 1080p and on a 6.1-inch phone (portrait inline / landscape):
captions 56 px (11.4 / 20.4 pt); image stamp and source chip 30 px (6.1 / 10.9 pt); event labels 33 px (6.7 / 12.0 pt); legends and number kickers 34.6 px (7.0 / 12.6 pt);
traced outline 5.0 px (1.0 / 1.8 pt). Human checks open: real-phone viewing, taste, pronunciation.

## Visual diversity (qc/visual_runs.json)
Visual changes per minute 28, 25, 24, 15, 23, 17 (minutes 0-5). Runs over 10 s (all evidence held on purpose while the narrator explains it):
3:32-3:45 Gilbert Bay layer, 3:49.5-4:00.5 1986 vs 2022 shoreline, 4:28.5-4:42 exposed lake bed, 4:47.5-5:11 dust passage with pins.
July 2022 is 67 % of screen time: the stack holds five dated pictures; no extra zooms or transitions were added for movement's sake.

## Pronunciation - NOT VERIFIED (no ASR in the container)
Saltair 1:20.39 · Gunnison 2:52.79, 3:26.19 · Gilbert 2:54.86, 3:29.62 · methyl mercury 3:39.91 · Newfoundland 4:02.67 · Farmington 4:50.11 · GRACE 5:26.37 (0.30 s, spoken as a word).
