# EP003 full silent preview (0-300.167 s)

Status: **TECHNICALLY_VALID (renders, decodes, frame count) and VISUALLY_REVIEWED by the agent (all 40 shots and 14 label/pin moments looked at as frames); NOT USER_APPROVED.**
No audio exists, no TTS was run, nothing was published. Cost: 0 USD.

- File `preview/proof.mp4` (1920x1080, 30 fps, 300.167 s, 222,740,118 bytes), SHA-256 `da8fc6a6ae1f04cb621d016dfd652c761c581b5fcd2c090d9727a7930f8f8a74` (not committed; media rule). Regenerate:
  `python3 tools/autopilot/storyboard.py plan ep003-great-salt-lake && python3 tools/autopilot/storyboard.py preview ep003-great-salt-lake --start 0 --end 301 --confirm` (about 9.5 min).
- Timing is **ESTIMATED** (2.38 words/s), not provider timing. Labels and pins are word-anchored to estimated times and will move with the real narration; re-run `plan` after the voice exists.
- Images: five calibrated Landsat mosaics (1985, 1986, 1999, 2021, 2022), every pixel from real USGS Level-1 bands, no frame substituted, no unregistered image mixed in (`assets/landsat/stack_cal/provenance.json`, `spec_cal.json`).
- Renderer plan: 40 shots, 41 composition resets, 4 distinct compositions in the first 10 s.

## Checks
- Dates: `DATE_ACQUIRED` of all 20 tiles equals the date in the file name; labels say JUNE 1985, AUGUST 1986, AUGUST 1999, JULY 2021, JULY 2022. Each mosaic joins path 39 and path 38 scenes acquired 7 (1985, 1986, 1999, 2021) or 17 (2022) days apart; the credit pill and the narration say "mosaic of several scenes".
- Geography: pins overlaid on the 2022 mosaic: Salt Lake City and Saltair on their sites; the railroad causeway appears as a straight edge at 41.226 N in both the 2021 and 2022 mosaics (different tile sets), i.e. a real feature, not a tile seam; Gunnison Bay and Gilbert Bay pins sit in the water of the two arms.
- yt-qc `--profile long` (qc/qc_silent_preview.json): FAIL only on `loudness` and `audio_starts` (silent, expected). Warnings: `long_target_window` (300 s vs 480-720 s: the script is 4,795 characters), `composition_hold` 8.4 s (limit 8), `visual_families_first_10s` 2 (limit 3), `visual_family_dominance` geo_2022 52 s (227-279 s, one image year while the narration covers causes and dust).

## Defects found by looking and fixed
1. First storyboard held one view for 38.8 s and one beat for 22 s: beats split by sentence, wide/tight views alternated (registry `geo-beats-need-sentence-splits-and-camera-resets`).
2. yt-qc freeze check failed (5.6, 5.2 and 7.6 s of static picture in the hook, after the timelapse and in "a big lake"): those beats now move; check passes.
3. "GUNNISON BAY" pin collided with the year label; pin moved into the bay. "SALT LAKE CITY" pin appeared while the camera was in the north; the beat now starts wide. A "DROPPED ALMOST 6 FEET" label sat on a beat that does not contain the number; moved.
4. Wide view cut the lake's north tip; `whole` is now 228 km wide centred 41.2 N.
5. Preview subset dropped the images of wipe/flip layers; fixed with a regression test.

## Known weaknesses (not hidden)
- Mosaic seams: 1985 and 1986 show a diagonal tone edge in the lake where the two paths meet (different days, different water colour); 1999 and 2021 show the causeway as a hard edge (real). Not blended on purpose.
- Wipe labels render in mixed case (renderer style) while year labels are upper case.
- The 2022 image carries 2016-2023 topics (causeway channel opened 2016, snow of winter 2022-23) because no later calibrated image was acquired; the label always states the image's own date. A 2025 mosaic (scenes downloaded) could end the film on the present day.
- One stat label ("4,190.2 FEET", beat 3) is on screen about 1 s with estimated timing.
- Not verified: audio, pacing against real speech, readability on a phone, NASA/USGS credit wording for monetised use (Landsat is generally public domain, ASSUMED), pronunciation.
