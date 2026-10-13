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
