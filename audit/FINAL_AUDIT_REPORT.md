# EP003 V2 - final audit before approval (2026-10-15)

Master audited: sha256 0284e660b9ab343101649e19a01cfdfbf54817224687d86d58adcc510a009004 (1920x1080, 30 fps, 6:12.57, 11,177 frames), branch `media/ep003-gsl-final-v2`.
Evidence images (phone simulation, proof of the size fix): same media branch, `audit/`.

## 1. 720p / 27 MB vs 910x512 / 228 MB
The delivered review copy is `EP003_V2_ipad_720p.mp4`: 1280x720, 27,163,742 bytes, sha256 bb1d5d6b136a3c5d... (ffprobe). No 910x512 or 228 MB file exists in the
container or on any media/* branch. 910x512 is the size the chat/file viewer re-encodes to (512 px height); the same discrepancy was recorded in EP002
(`viewer-reencodes-files`). Not a defect of the master or the copy. Owner check: download the file from the media branch and compare the SHA-256.

## 2. Visual variety (tools/autopilot/visual_runs.py, 2 fps, caption band ignored)
- Base picture screen time: July 2022 249 s (67 %), Aug 1999 50 s (13 %), Jul 2021 20 s, Aug 1986 19 s, Jun 1985 19 s, flips 15 s.
- Visual changes per minute: 28, 25, 24, 15, 21, 18 (min 0-5); median run 1.5 s.
- Longest near-identical runs: 3:32.0-3:49.5 (17.5 s), 4:28.5-4:43.5 (15 s), 4:58-5:11 (13 s), 3:49.5-4:00.5 (11 s), 4:47.5-4:58 (10.5 s).
- First 30 s: 16 runs, longest 7 s (0:25-0:32, year flip) - fine. Middle: 3:31-4:00 is the weakest passage. Final minute: 5:11-5:23 (snow) has no new visual; 5:24-6:06 carries the shoreline overlays.
- Repeated compositions: July 2022 190->75 km (4 shots), 228->70 km (3), 55->228 km (3).

## 3-4. Readability on a phone (simulated 390x219 pt portrait, 699x393 pt landscape)
| element | size at 1080p | portrait | landscape |
|---|---|---|---|
| captions | 56 px | ~11 pt, readable | ~20 pt |
| number cards (value / kicker) | 173 / 35 px | ~35 / 7 pt | ~63 / 13 pt |
| IMAGE date stamp | 19 px | ~3.9 pt, illegible | ~6.9 pt, marginal |
| source chip | ~18 px | ~3.7 pt, illegible | ~6.6 pt |
| legends (shoreline, exposed bed) | ~32 px | ~6.5 pt, hard | ~11.6 pt |
| event-year label | ~25 px | ~5 pt, illegible | ~9 pt |
| shoreline outline | ~2 px line | ~0.7 px, almost invisible | ~1 px, faint |
Captions sit at 82-87 % of the height: clear of YouTube's progress bar, inside the title-safe area; burned captions + an uploaded SRT will double if a viewer turns CC on.

## 5. Pronunciation
NOT VERIFIED. No ASR model in the container; ffmpeg's `asr` filter exists but has no acoustic model; pypi, huggingface and apt are unavailable. Indirect
evidence only: GRACE lasts 0.30 s (spoken as a word, not spelled), other names have normal durations. Owner must listen: Saltair 1:20.39,
Gunnison 2:52.79 and 3:26.19, Gilbert 2:54.86 and 3:29.62, methyl mercury 3:39.91, Newfoundland 4:02.67, Farmington 4:50.11, GRACE 5:26.37.

## 6. Findings
CRITICAL: none found. Numbers on screen match the narration (38 dynamic texts linted, 0 problems), image dates match the pictures, captions 198/198 in sync,
-15.9 LUFS, true peak -2.4 dBFS, no freezes, black frames or decode errors, yt-qc PASS.

MAJOR
- M1 Phone legibility: IMAGE dates, source chip, legends and event labels are too small (table above) - the dates are the channel's honesty element.
- M2 The new shoreline outlines are too thin for phones (0:12, 5:24-6:06), so the main evidence overlay is weak where most viewers watch.
- M3 Monotony at 3:31-3:49 (deep brine layer / mercury, 18 s on the unchanged July 2022 picture) and 3:49-4:00 (1986 high, no reference to today).

MINOR
- m1 5:11-5:23 (record snow 2022-2023): no snow imagery on the stack; July 2022 picture held 12.5 s.
- m2 Short motion-blur smears in fast camera moves (0:12, 4:56, 5:30).
- m3 Landsat mosaic seams (1985/1986/1999) - data, disclosed.
- m4 Burned captions + uploaded SRT double when CC is on (upload choice).
- m5 Pauses 4:13 (0.98 s, TTS chunk join on a sentence end) and 5:23 (before a rhetorical question): acceptable.
- m6 6:13 is below the 8-12 min long-form window; not padded on purpose.

## 7. Fix plan (zero cost, no ElevenLabs, audio and timings unchanged)
1. M1+M2 engine sizes (proof stills done): ImageStamp 19->30 px, SourceChip 0.017->0.024 H, CalloutPanel 0.026->0.032 H with a real-width clamp, EventYear label x1.3,
   thin outline ~2x wider with a dark under-stroke (the proof at 3x width brightened 5:53 by 6 luma; use about 2x).
2. M3 3:31-3:49: soft cyan fill of Gilbert Bay from the July 2022 mask, south of the causeway, legend 'GILBERT BAY' + 'DEEP BRINE LAYER (USGS)', words from claim C25;
   camera held on the south view. 3:49-4:00: thin cyan 'SHORELINE · JUL 2022' outline over the Aug 1986 picture on 'The lake has not always been too low'.
3. Re-check with stills (about 1 min), phone simulation, regression tests (callout real-width clamp), then one full render (~48 min), QA, review copies.
m1-m6: no change (documented limits or owner decisions).

## Recommendation
**REVISE** (no CRITICAL issues; three MAJOR issues that hurt the phone viewer and the middle passage, fixable for free in about 1.5 hours of machine time).
USER_APPROVED: NO - owner decision.
