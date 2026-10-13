# Rendering, encoding, storage (EP002 final, 2026-10-13)
Benchmarks also in `docs/RENDER_BENCHMARKS.md`. All numbers **[VERIFIED]** on this container (4 vCPU, no GPU) unless tagged.
## Pipeline
`build_final.py OUT --scale 2 --fps 30 --a1 CESIUM_HD_FRAMES --jobs 4 [--only IDS] [--force] [--mux]`
- Scenes are independent segments `seg/<ID>.mp4` (video only, x264 crf 19 medium, GOP 2 s, yuv420p). Written as `.part.mp4` and renamed: an aborted run never leaves a half file; rerun resumes (existing segments are skipped, `--force` or deleting a segment re-renders it).
- `--mux`: concat copy -> assemble audio (`sync.assemble_audio`) -> two-pass loudnorm -> AAC mux (+faststart) -> SRT/VTT. No API calls anywhere.
- Native scale: `EP002_SCALE=2` -> 1920x1080; text and vectors are drawn at physical resolution through `kit.SDraw` / `SS`; images are cropped from the source at output size. Equivalence check SC=1 vs SC=2 (downsampled) on 84 frames: all within 3 grey levels mean difference.
## Timings
- 29 scenes, 15,682 frames at 1080p30: about 45 min wall with 4 processes (preview 960x540 at 24 fps took about 12 min).
- A1 globe (Cesium + NASA GIBS via `tools/cesium_proof`): 372 frames at 960x540 viewport, device scale factor 2 (1920x1080 PNGs), 3 workers: 10.7 min; with DSF 1.5: about 11 min earlier. Needs `python3 server.py` (cache dir), jsdelivr + gibs reachable. Keep frames 24 per estimated second; the scene indexes them through the smooth clock.
## Output (EP002)
1920x1080, 30 fps, H.264 yuv420p ~4.0 Mb/s video + AAC 192 k 48 kHz stereo, 522.73 s, 273,936,323 bytes. Integrated loudness -16.22 LUFS, true peak -1.50 dBTP, LRA 2.9 (loudnorm, target -16 LUFS / -1.5 dBTP).
## Storage rules
- Media never goes to main. Git hosts reject files > 100 MB: split the final MP4 into <= 90 MB parts on a `media/<episode>-final` branch with `SHA256SUMS` and the join command (`cat part_* > file.mp4`); keep audio + paid TTS cache on `media/<episode>-audio`.
- Keep `narration.voice.json`, captions (SRT/VTT), QA reports and checksums in the episode folder on the work branch.
## Do not repeat
Rendering at 540p and upscaling (violates the no-upscale rule); ffmpeg `xfade` between segments (shortens the timeline, breaks the sync map); parallel batches that write final names directly (truncated files after an abort).

## Final master v4.1 (2026-10-13)
- VERIFIED: `build_final.py OUT --full4 --scale 2 --fps 30 --a1 /tmp/h/a1_hd --jobs 4 --mux` builds the whole film from `scenes.SCENES_FULL` (hook H1-H4 + A1..E6, voice from 0 s). Delete only the changed `seg/*.mp4` and rerun; windows depend on word-time differences, so unchanged segments stay valid. Full render of 8 changed scenes ~25 min with 4 jobs; mux ~3 min.
- VERIFIED: the video length is the sum of segments (516.77 s); the "muxed" print shows the audio length (+1 s pad). Use the video duration as `--expected-duration` for yt-qc.
- VERIFIED: iPad copy: 854x480, x264 slow, 380 kb/s + AAC 56 kb/s mono = 28.6 MB for 8:37 (<30 MB limit).
- RULE: camera zoom on schematic scenes must keep panel titles below the top pill (zoom <= 1.2 there); check by looking at frames - qa_text_bounds does not see zoomed text.

## Delivering a >100 MB master (2026-10-13)
- VERIFIED: single-file delivery = Git LFS on the media branch (`git lfs track` the file, commit, push). Needs allowed hosts `github-cloud.s3.amazonaws.com` (object upload), `lfs.github.com` (verify) and `github.com` / `media.githubusercontent.com` (download check). Without them the push fails at upload (S3) or verify (lfs.github.com). Release creation is not permitted for this session type; Drive upload via the connector cannot carry a 272 MB file.
- VERIFIED: anonymous download `https://github.com/<owner>/<repo>/raw/<branch>/<path>` redirects (302) to `media.githubusercontent.com/media/...` and returns the real file (size and SHA-256 checked), not the LFS pointer. Public repo = public file; LFS free quota (storage/bandwidth) applies.
