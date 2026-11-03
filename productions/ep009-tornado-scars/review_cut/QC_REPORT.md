# EP009 REVIEW CUT — QC report (2026-11-03)
**Status: REVIEW CUT. Temporary local voice (ffmpeg flite, slt) — NOT the release master. No ElevenLabs, no upload, queue/schedule untouched.**
Build code: `ep9_voice.py` (voice+timeline+SRT), `produce_ep009.py` (Long/Shorts), `thumb.py`, `qc_video.py`. MP4s are external (not in git).

| File | Duration | Res / fps | Loudness | Motion QC | Verdict |
|---|---|---|---|---|---|
| OA_EP009_REVIEW_LONG_localvoice_v2.mp4 | 6:18.6 (378.6 s; target 375–420) | 1920×1080 / 30, H.264 + AAC 48k | −16.0 LUFS, LRA 3.6 | 11358 frames, pts regular, 0 frozen, 0 black, no cuts (only 0.5 s dissolves) | **PASS as review cut (v2: placeholders replaced); not release (blockers below)** |
| OA_EP009_REVIEW_SHORT_01_localvoice.mp4 | 25.4 s | 1080×1920 / 30 | −14.2 LUFS | 763 frames, regular, 0 frozen, 0 jumps | **PASS review** (see note: shorter than 30–38 s spec) |
| OA_EP009_REVIEW_SHORT_02_localvoice.mp4 | 29.9 s | 1080×1920 / 30 | −14.2 LUFS | 896 frames, regular, 0 frozen, 1 dissolve | **PASS review** (≈30 s lower bound) |
| OA_EP009_thumbnail_A.jpg | 1280×720 | — | — | — | PASS with WARN (text mismatch) |

## Defects found by QC and fixed before this report
Long: corridor-highlight pop at 7.3 s; hard cut EO-1→MODIS at 19.5 s; 3.2 s frozen camera hold 163–166 s. Shorts: MODIS/GOES not filling 9:16 (black bars, edge streaks), clipped captions/headlines, hard cuts, black strip at EO-1 end.
Checks used: ffprobe pts, per-frame diff (zero-diff/jump), luma black-frame scan, EBU R128, contact-sheet review of ~60 frames. NOT run: phase-correlation sub-pixel stepping test on the final files; real-device playback.

## v2 update (M04–M06 replaced, 2026-11-03)
- 238–285 s: placeholder cards replaced by the real originals (hashes verified vs handoff): M04 ASTER (full source → crop to the beige track, FALSE COLOR label, credit NASA EO / J. Allen, ASTER data credit) and M06 USGS LCMAP (full → crop to purple streaks, legend visible, "landscape change — not photos of a tornado", USGS public domain). M05 (1108×577) not used: native size too small for a safe crop. No placeholder text remains in the video or code path.
- Removed the unverified "north of University Mall" from voice, burned captions and SRT; the sentence now ends "…south of Bryant-Denny Stadium" (C02). Timeline unchanged (new sentence sits in the old slot; silence after it).
- Only these segments were re-rendered (197.6–214.3 s captions; 231.0–289.9 s sensors scene incl. dissolves) and spliced by stream copy at keyframes; all other frames are bit-identical to the previous cut. Shorts unchanged.
- Track/streak positions on ASTER and LCMAP were read visually from the images for camera framing only; nothing is drawn on them, no coordinates claimed.

## Remaining blockers (Long is not release-ready)
1. **Voice**: robotic Flite voice; final Adam voice needs your approval and a retime pass.
2. **NOAA GOES rights**: embedded elements (CIMSS etc.) need asset-level review; source is 720p upscaled.
3. **Thumbnail words**: "FROM SPACE" vs hook "THIS ISN'T A ROAD" — owner to choose (proposal: thumbnail "NOT A ROAD").
4. qc_checklist items still open: georeferenced track placement, EP-number ledger check, thumbnail approval. Master should be re-checked on a real 1920×1080 export (chat previews may downscale).

## Facts vs sources.json
- 362 tornadoes / 321 deaths (C01, NCEI retrospective) ✔ shown with source tag. ~80-mile / 1.5-mile path attributed to NWS (C04) ✔. EO-1 May 2 (C02), Aqua MODIS Apr 12/28 (C03) ✔ — on-screen credit uses neutral "NASA MODIS" (draft credit string said Terra; manifest says Aqua). ASTER on Terra, May 4 (C05) ✔ card only.
- FIXED in narration: "the day after the devastating outbreak" → "the day after the April twenty-seventh tornadoes" (Apr 28 is the last outbreak day).
- FIXED in v2: unsourced "north of University Mall" removed; "south of Bryant-Denny Stadium" is in C02. Contrail/scar relation is narration + caption only, no drawn marker (positions not verified).
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
