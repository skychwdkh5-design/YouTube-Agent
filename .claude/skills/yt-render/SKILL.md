---
name: yt-render
description: >-
  Render a real MP4 from a timeline.json with the installed FFmpeg - still images and Landsat
  frames with Ken Burns pan/zoom, crossfades, 1920x1080 30 fps H.264 + AAC. Use for "render
  this", "make the video", "turn these images into a video", or any request for an actual video
  file. Rendering needs --confirm. Not for edit lists from a transcript (that is /yt-edit).
---

# yt-render

A timeline in, a real MP4 out. Everything runs on the local FFmpeg - no network, no credentials.

```bash
python3 render.py --timeline timeline.json                                  # validate, show the plan
python3 render.py --timeline timeline.json --output final.mp4 --confirm     # render
python3 render.py --timeline timeline.json --output final.mp4 --confirm --overwrite
```

Every command prints JSON. Then always run `/yt-qc` on the result:

```bash
python3 ../yt-qc/qc.py final.mp4 --timeline timeline.json
```

## timeline.json (version 1)

```json
{
  "version": 1,
  "output": {"width": 1920, "height": 1080, "fps": 30, "crf": 20, "preset": "medium"},
  "clips": [
    {"type": "landsat", "src": "LC08_..._T1.jpg", "duration": 6,
     "credit": "Landsat imagery courtesy of the U.S. Geological Survey",
     "motion": {"type": "kenburns", "zoom": [1.0, 1.15], "pan": "left_to_right"},
     "transition": {"type": "crossfade", "duration": 0.75}},
    {"type": "image", "src": "map.png", "duration": 4, "fit": "contain",
     "motion": {"type": "static"}}
  ]
}
```

- `output` is optional; the defaults are 1920x1080, 30 fps, H.264 (CRF 20, `medium`), AAC 192k
  48 kHz stereo. Width/height must be even; fps is one of 24/25/30/50/60.
- `type`: `image` or `landsat` (same rendering; `landsat` keeps the evidence role explicit). Keep
  `source`/`credit` on each clip - later stages (description, licence manifest) read them.
- `duration`: seconds, 0.2-600. It is rounded to whole frames; the plan shows the frame counts.
- `fit`: `cover` (default - scale to fill, crop the overflow) or `contain` (whole image, black
  bars). A source more than 4x off the output's aspect ratio is refused under `cover`, because
  cropping would throw most of it away - set `contain` deliberately.
- `motion`: `kenburns` (default, `zoom` 1.0-2.0 start/end, `pan` one of `center`,
  `left_to_right`, `right_to_left`, `top_to_bottom`, `bottom_to_top`) or `static`.
- `transition` sits on the clip it leaves: `crossfade` with a `duration`, or `none` (hard cut).
  A crossfade overlaps the two clips, so it shortens the total; it must be shorter than both.
- The audio track is silence for now, so the file is always valid for upload.

**Reserved, not yet supported:** `type: "video"`, `audio.voice`, `audio.music`, `audio.sfx`,
`subtitles`, `overlays`. Version 1 refuses them with `"status": "unsupported"` rather than silently
rendering without them.

## Safety

- **No render without `--confirm`.** Without it you get `"status": "confirm_required"` and the
  validated plan with the expected duration - use that to check the timeline first.
- Every `src` is resolved inside the timeline's folder (or `--media-root`). URLs, `..` and symlinks
  that escape it are refused. Each file is checked with ffprobe: still images only (JPEG, PNG,
  WebP, BMP, TIFF), at least 16 px a side, at most 120 MP, under `--max-input-mb` (200).
- `--max-duration` (900 s) and `--max-output-mb` (500) cap the job; `--timeout` (1800 s) caps FFmpeg.
- The MP4 is written to a hidden `.render-*.partial.mp4` and renamed into place only after FFmpeg
  exits cleanly, the size is under the cap, and ffprobe finds one video and one audio stream at the
  expected duration. A failed render leaves nothing that looks finished.
- An existing output is never replaced without `--overwrite`, and even then only after the new
  render succeeds.
- Output is deterministic: the same timeline, sources and FFmpeg build give the same bytes
  (metadata stripped, bitexact flags). The JSON includes the `sha256`.
- Rendered MP4s do not belong in git (`*.mp4` is ignored).

## No fabrication

A rendered Landsat frame is still a claim. Only put a `landsat` clip in the timeline if it came from
`/yt-satellite` with its `displayId`, date and credit. A generated or stock image is never a
`landsat` clip.

## The gate

Nothing here publishes. This skill renders a file and you decide what happens to it. The last line
of every run is the question: **QC it and watch it, or change the timeline?**
