# EP009 REVIEW CUT — QC report (2026-11-03)
**Status: REVIEW CUT. Temporary local voice (ffmpeg flite, slt) — NOT the release master. No ElevenLabs, no upload, queue/schedule untouched.**
Build code: `ep9_voice.py` (voice+timeline+SRT), `produce_ep009.py` (Long/Shorts), `thumb.py`, `qc_video.py`. MP4s are external (not in git).

| File | Duration | Res / fps | Loudness | Motion QC | Verdict |
|---|---|---|---|---|---|
| OA_EP009_REVIEW_LONG_localvoice.mp4 | 6:18.6 (378.6 s; target 375–420) | 1920×1080 / 30, H.264 + AAC 48k | −16.0 LUFS, LRA 3.5 | 11358 frames, pts regular, 0 frozen frames, 0 black frames, no cuts (only 0.5 s dissolves) | **PASS as review cut; FAIL as release (blockers below)** |
| OA_EP009_REVIEW_SHORT_01_localvoice.mp4 | 25.4 s | 1080×1920 / 30 | −14.2 LUFS | 763 frames, regular, 0 frozen, 0 jumps | **PASS review** (see note: shorter than 30–38 s spec) |
| OA_EP009_REVIEW_SHORT_02_localvoice.mp4 | 29.9 s | 1080×1920 / 30 | −14.2 LUFS | 896 frames, regular, 0 frozen, 1 dissolve | **PASS review** (≈30 s lower bound) |
| OA_EP009_thumbnail_A.jpg | 1280×720 | — | — | — | PASS with WARN (text mismatch) |

## Defects found by QC and fixed before this report
Long: corridor-highlight pop at 7.3 s; hard cut EO-1→MODIS at 19.5 s; 3.2 s frozen camera hold 163–166 s. Shorts: MODIS/GOES not filling 9:16 (black bars, edge streaks), clipped captions/headlines, hard cuts, black strip at EO-1 end.
Checks used: ffprobe pts, per-frame diff (zero-diff/jump), luma black-frame scan, EBU R128, contact-sheet review of ~60 frames. NOT run: phase-correlation sub-pixel stepping test on the final files; real-device playback.

## Blockers (Long is not publishable until closed)
1. **M04 ASTER (≈243–265 s), M06 USGS LCMAP (≈265–284 s), M05 USGS Landsat**: files are not in the repo and the sandbox cannot download NASA/USGS. ~46 s of the Long shows labelled placeholder cards ("REVIEW CUT PLACEHOLDER"). Owner: supply the three files or approve cutting those beats.
2. **Voice**: robotic Flite voice; final voice needs your approval (Adam/ElevenLabs) and a retime pass (captions/animations are keyed to sentence times).
3. **NOAA GOES rights**: asset-level rights for the NESDIS video still unverified (manifest: "verify specific media credits"). Source is 720p upscaled to 1080p.
4. qc_checklist items still open: georeferenced track placement (track polyline for EO-1 was read visually from the image, MODIS tracks not annotated), EP-number ledger check, thumbnail approval.

## Facts vs sources.json
- 362 tornadoes / 321 deaths (C01, NCEI retrospective) ✔ shown with source tag. ~80-mile / 1.5-mile path attributed to NWS (C04) ✔. EO-1 May 2 (C02), Aqua MODIS Apr 12/28 (C03) ✔ — on-screen credit uses neutral "NASA MODIS" (draft credit string said Terra; manifest says Aqua). ASTER on Terra, May 4 (C05) ✔ card only.
- FIXED in narration: "the day after the devastating outbreak" → "the day after the April twenty-seventh tornadoes" (Apr 28 is the last outbreak day).
- WARN: narration line "south of Bryant-Denny Stadium and north of University Mall" — stadium is in C02, **"north of University Mall" is unsourced**; no on-screen annotation was made for either. Contrail/scar relation is narration + caption only, no drawn marker (positions not verified).
- Funnel never shown or implied; no casualty imagery; illustration (P02 storm) tagged "ILLUSTRATION / NOT TO SCALE".
- Short 1: "wasn't there before April 27" — consistent with C02/C03. Short 2: "NASA and NOAA recorded…storm systems" ✔.

## Licenses
NASA EO imagery: NASA media guidelines (C09), credit shown on screen. NOAA GOES: see blocker 3. Illustrations: owner-supplied handoff assets (provenance = owner). Voice: Flite (permissive). Background bed: synthesized in code (rights-clean). No third-party music.

## Subtitles / sync
English SRT generated from the same sentence timeline as the voice (≤2 lines × 42 chars); burned in on all three videos. Sync is exact by construction (audio and captions share `timeline.json`). Long captions: `captions/long.srt`.

## Thumbnail–Hook Match
Same EO-1 crop and corridor highlight as frame 0 of the Long (t≈1 s) ✔. WARN: thumbnail text "FROM SPACE" first appears on screen at ~13–19 s, while 0–7 s says "THIS ISN'T A ROAD". Options: change thumbnail text to "NOT A ROAD" (matches the hook) or accept. Owner decision.

## Other notes
GOES footage is reused (promise 29–46 s, storms 80–122 s, close) and plays at source cadence (no invented in-between frames). Short 1 is 25.4 s vs 30–38 s spec; Short 2 is 29.9 s — both are bounded by the supplied VO scripts.
