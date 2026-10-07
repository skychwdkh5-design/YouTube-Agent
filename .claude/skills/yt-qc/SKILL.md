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

## Profile `short` (vertical Shorts)

```bash
python3 qc.py short.mp4 --profile short --timeline timeline.json --contact-sheet sheet.jpg
```

1080x1920 30 fps, 35-60 s (45-55 s target - warn), no black frames, no static freeze (warn 1.5 s,
fail 2.5 s), audio within 0.5 s, loudness reported (warn outside -16..-12 LUFS). From the render
manifest (`<video>.manifest.json`, or `--manifest`): at least 5 information events in the first 10 s,
every caption inside the Shorts safe area, a source credit on every shot, and composition resets:
at least 3 distinct compositions in the first 10 s (`compositions_first_10s`, fail), about 7-10
resets (`composition_resets`, warn) and no composition held over 6 s (`composition_hold`, warn).
They are recounted from the manifest's reset list; a manifest rendered before the rule has no
`compositions` block and the check is skipped.
When the storyboard tags `visual_family`, the manifest's `visual_novelty` runs are also checked - warnings
only: `visual_families_first_10s` (>= 3), `visual_family_transitions` (>= 6) and `visual_family_dominance`
(no family over 10 s unless it is transforming). Untagged manifests skip it. `--contact-sheet`
writes the first frame plus the middle of every shot, labelled, for review.

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
