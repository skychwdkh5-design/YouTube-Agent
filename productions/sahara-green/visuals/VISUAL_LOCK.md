# EP001 VISUAL LOCK v1.1 (East Oweinat and Toshka sequences)

v1.1 (2026-10-08, reviewer decision 5): one concise note on the Toshka January 2011 frame only, `Narration says "by 2012"; this image is from January 2011.` The image date, the label "January 2011", tone B, imagery, crops, zoom, scale bars and the 30 fps standard are unchanged. The sequences are now driven by narration timings (`narration/cues.py fit`): the hold, dissolve and zoom lengths come from the audio, so the delivered 21.7 s and 15.9 s review cuts are the *unfitted* versions. Dissolve length (0.8 s), the transition label and every visual rule below stay fixed.


Status: **LOCKED for production** (presentation v2.1, 2026-10-08), pending the reviewer's look at the two 30 fps review videos in `previews/visual_lock/`. Locked means: any change to the items below needs a new QA run and a new entry here. The final 4K render has not been started.

| Locked item | Value |
|---|---|
| Tone policy | B: `clip((r-0.02)/0.58,0,1)^(1/1.8)` on TOA reflectance, one curve for every frame |
| Imagery | sha256 of the cached tone-B frames in `reports/visual_lock_hashes.json`; derived from the verified source bands (manifest in `landsat/source_bands/`); geographic alignment unchanged (registration of rendered frames within 0.13 px) |
| Crops | East Oweinat full AOI 2075 x 1757 px (30 m); Toshka 3840 x 2160 union crop at y0=60, x0=312 (inside all four footprints with a 12 px margin) |
| East Oweinat zoom | target (480, 630) source px, end window 960 x 540 source px, max 4.0 screen px per source px at 4K |
| Scale bars | computed from the grid (East Oweinat 5 km at the zoom end, 2 km in stills; Toshka 20 km) |
| Dates | East Oweinat: August 26, 1984; January 2000; January 2010; January 2016; January 2024. Toshka: January 1999; January 2002; January 2011; November 2021 |
| Transition label | "Transition between satellite images" (replaces "Dissolve, not an observation"); both dates, both sensors and both timeline nodes stay visible during every dissolve |
| Frame rate | **30 fps** (see FPS audit below) |
| Renderer | `scripts/render.py` (sha256 in `reports/visual_lock_hashes.json`) |
| Narration | SCRIPT LOCK v1.1, body hash `d646001c83d3421d43510ece1926d7bd49bc197dcdde07b94fd2f4f3a049f335` (checked unchanged) |

## FPS audit
- The review MP4s delivered in passes 1 and 2 were encoded at **24 fps** (ffprobe: `r_frame_rate` = `avg_frame_rate` = 24/1; 540 and 408 frames in pass 1, 520 and 381 in pass 2). The pass-2 report said 24 fps, which matched the files in Git (sha256 of the pass-2 files: East Oweinat `dfca8ea38bef6c6ba23d2b536135155583b793cc10d4fc8d746fd831f4cbce90`, Toshka `e612bba20e4a80fbee9dd204bd7ee2b5d8c0012b7ce49b9a794b7a137ce805d2`). I cannot inspect the copies that reached the reviewer; a 30 fps appearance there would come from the app's preview or re-encoding, not from the repository files. If the sha256 of the received file differs from the repository one, it was re-encoded.
- Why 24: the pass-1 renderer hard-coded 24 fps while the project's render pipeline (yt-render, long profile, timeline v3) is 30 fps, so the previews did not follow the project policy. That was an inconsistency on my side.
- Policy now: **30 fps everywhere** (previews, final 4K, the yt-render timeline). All sequence times are defined in seconds (dissolve 0.8 s, East Oweinat 21.7 s, Toshka 15.9 s) and a frame is drawn at i / fps, so the duration does not change with the frame rate. `render.py` has a single `FPS = 30`; QA (`qa2.py`) now fails if the encoded r_frame_rate or avg_frame_rate is not 30/1, if the frame count differs from the timeline (651 and 477 frames), or if the duration depends on fps.
- New previews: `east_oweinat_review_720p_30fps.mp4` (651 frames, 21.7 s) and `toshka_review_720p_30fps.mp4` (477 frames, 15.9 s).

## QA (`reports/qa2_results.json`: all checks PASS)
Includes the new fps and label checks, type scale, safe margins, text contrast, imagery equal to tone B, unchanged zoom target and viewport boxes, resampling identical to pass 1, 4.0x maximum at 4K, dates against metadata, temporal order.
