---
name: yt-qc
description: >-
  Check a rendered MP4 with FFprobe/FFmpeg before it is called finished - streams, resolution,
  frame rate, codecs, size, duration against the timeline, truncation and a full decode pass.
  Use after /yt-render, before any upload, or for "is this file OK", "check the render", "QC".
---

# yt-qc

A render that exists is not a render that works. This proves the file is what the spec says.

```bash
python3 qc.py final.mp4 --timeline timeline.json        # expected duration from the timeline
python3 qc.py final.mp4 --expected-duration 10.5
python3 qc.py final.mp4 --quick                         # skip the full decode pass
```

Defaults are the yt-render v1 spec: 1920x1080, 30 fps, H.264 + AAC in MP4, at most 2000 MB,
duration within 0.25 s. Override with `--width --height --fps --vcodec --acodec --max-mb
--tolerance`.

Exit code: `0` PASS, `1` FAIL, `2` could not run (bad arguments, ffprobe missing).

## What it checks

| id | fails when |
|---|---|
| `file_exists`, `container_readable`, `container` | missing, unreadable, or not MP4 |
| `file_size` | empty, or over `--max-mb` |
| `video_stream`, `audio_stream` | not exactly one of each |
| `resolution`, `frame_rate`, `video_codec`, `audio_codec` | different from the spec |
| `pixel_format` | not yuv420p - a **warn**, not a fail |
| `duration_readable`, `duration_matches_timeline` | no duration, or off the timeline by more than the tolerance |
| `streams_aligned`, `frame_count` | video/audio/container end at different times, frames missing |
| `full_decode` | FFmpeg hits any error decoding every frame (catches truncation) |

Each check reports `status` (`pass`/`fail`/`warn`/`skip`), `expected` and `actual`. Only a `fail`
makes the result FAIL. A `skip` says why it did not run (e.g. no expected duration given).

## Adding checks later

Every check is a function in `CHECKS` that takes the probe context and returns a list of results.
Loudness (`ebur128`), black frames (`blackdetect`), silence (`silencedetect`), subtitle validation
and the licence manifest each become one more function there - the output format does not change.

## Report it straight

FAIL is reported as FAIL with the failing ids and their `actual` values. Never re-run QC with a
looser tolerance to turn a FAIL into a PASS without saying so.

## The gate

Nothing here publishes. A PASS means the file is technically sound, not that the video is good or
approved. The last line of every run is the question: **watch it, or fix it?**
