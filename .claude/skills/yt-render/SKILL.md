---
name: yt-render
description: >-
  Render the final publishable MP4 from a timeline.json with the installed FFmpeg - still images
  and Landsat frames with Ken Burns pan/zoom and crossfades, the yt-voice narration, burned-in
  yt-captions subtitles and the on-screen source credit, 1920x1080 30 fps H.264 + AAC. Use for
  "render this", "make the video", "turn these images into a video", or any request for an actual
  video file. Rendering needs --confirm. Not for edit lists from a transcript (that is /yt-edit).
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

## timeline.json

```json
{
  "version": 1,
  "output": {"width": 1920, "height": 1080, "fps": 30, "crf": 20, "preset": "medium"},
  "clips": [
    {"type": "landsat", "src": "assets/LC08_..._T1.jpg", "duration": 6,
     "credit": "Landsat imagery courtesy of the U.S. Geological Survey",
     "motion": {"type": "kenburns", "zoom": [1.0, 1.15], "pan": "left_to_right"},
     "transition": {"type": "crossfade", "duration": 0.75}},
    {"type": "image", "src": "assets/map.png", "duration": 4, "fit": "contain",
     "motion": {"type": "static"}}
  ],
  "audio": {"voice": [{"src": "voice/narration.wav", "start": 0.0,
                       "meta": "voice/narration.voice.json"}]},
  "subtitles": {"src": "captions/captions.srt", "burn_in": true},
  "credit": {}
}
```

`version` is 1 or 2 (the same format). `audio`, `subtitles` and `credit` are optional; a timeline
without them renders exactly as it always did, byte for byte.

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

### Narration - `audio.voice`

One track from `/yt-voice`. `start` (seconds, default 0) places it sample-exactly; the narration is
never stretched, trimmed or re-timed, so the yt-captions cues stay on the words. The clips must run
at least to `start + narration duration` - if they end earlier the render is refused rather than
cutting speech. Give `meta` (the `.voice.json`) and the audio is checked against its
`audio_sha256` and duration, so captions built from that metadata cannot drift from a swapped file.
`normalize` (default `true`) measures the narration (EBU R128) and applies **one constant gain** toward
-16 LUFS with the true peak under -1.5 dBFS - no compressor, no look-ahead, no timing change.
Without `audio.voice` the soundtrack is silence, as before.

### Subtitles - `subtitles`

An `.srt` from `/yt-captions`. It is validated first (numbered blocks, increasing, non-overlapping,
inside the video length). `burn_in: true` (default) draws it into the picture with libass:
white text, black outline, `font` (default Inter), `size` (default 15, libass units) and
`margin_v` (default 24). `burn_in: false` only validates it - keep the SRT for upload as a track.

### Source credit - `credit`

`{}` (or `true`) draws the clips' `credit` strings, de-duplicated, as one line over the whole video;
`{"text": "..."}` sets it explicitly. `position` is `top_left` (default), `top_right`,
`bottom_left` or `bottom_right`; `size` defaults to 24 px at 1080p; `opacity` to 0.85. A timeline
with `landsat` clips and no `credit` still renders, with a warning - the USGS credit belongs on
screen wherever the imagery is.

**Not supported yet:** `type: "video"`, `audio.music`, `audio.sfx`, `overlays`. They are refused
with `"status": "unsupported"` rather than silently dropped. There is no music source in the
pipeline, so a render has narration or silence - never unlicensed music.

## Safety

- **No render without `--confirm`.** Without it you get `"status": "confirm_required"` and the
  validated plan with the expected duration - use that to check the timeline first.
- Every `src` (images, narration, subtitles, voice metadata) is resolved inside the timeline's
  folder (or `--media-root`). URLs, `..` and symlinks that escape it are refused. Images are
  checked with ffprobe: JPEG, PNG, WebP, BMP, TIFF, at least 16 px a side, at most 120 MP, under
  `--max-input-mb` (200). Narration: WAV, MP3, M4A, AAC or FLAC with exactly one audio stream.
- The subtitle file and credit text are staged in a temp folder and referenced by fixed names, so
  no user path or text ever goes into the FFmpeg filter graph.
- `--max-duration` (900 s) and `--max-output-mb` (500) cap the job; `--timeout` (1800 s) caps FFmpeg.
- The MP4 is written to a hidden `.render-*.partial.mp4` and renamed into place only after FFmpeg
  exits cleanly, the size is under the cap, and ffprobe finds one video and one audio stream at the
  expected duration (and audio at least as long as the narration). A failed render leaves nothing
  that looks finished.
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
