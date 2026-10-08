# Benchmark productions

The full per-file inventory is in `BENCHMARKS.json`: path, bytes, SHA-256, kind, role and storage.

| Benchmark | Folder | Final video | Bytes | SHA-256 |
|---|---|---|---|---|
| Lake Mead | `productions/lake-mead` | `lake-mead_short.mp4` | 30,415,749 | `235bc6f0b44f0d144c5acee9b1a59cd84588eafee41e348b8bc7694639fc4813` |
| Kilauea (Kapoho, 2018) | `productions/kilauea-2018` | `kilauea-2018_short.mp4` | 15,470,379 | `86a56a54e3eff1d77581b416d359c4fe7c3c2a881198034e03d14b9ad07057a8` |
| Wadi As-Sirhan | `productions/sirhan` | `sirhan_short.mp4` | 18,045,482 | `5544096049738930cbd592072bd2bf305b97232926be0b283cca8e0403285205` |

## Where things are stored

- **Text files** (scripts, claims ledgers, factcheck locks, timelines, storyboards, render/QC/production JSON, manifests, captions, voice metadata, build scripts, scene metadata) are committed on branch `preservation/benchmarks`. Generated media stays git-ignored.
- **Binary files** (final MP4s, animatic, narration WAVs, Landsat extracts, stack PNGs, contact sheets) are listed with their SHA-256 values but are not in Git. The only exception is the Kilauea final MP4, which is on branch `media/kilauea-2018-short`.
- The `production.json` stage fields for Kilauea and Sirhan ("rendered_awaiting_human_review", "render: not done") are stale. They are preserved unchanged, as is the older Lake Mead schema.

## Recovery

Each final MP4 is deterministic. Given its `timeline.json`, `stack/` PNGs, voice WAV and captions, yt-render reproduces it byte for byte; Sirhan was verified this way.

The Landsat extracts can be downloaded again by scene ID. The stack PNGs can then be rebuilt from them with each benchmark's build scripts and `stack.json`.

The **narration WAVs** can only be replaced by paying for new ElevenLabs requests, and the new audio would not be identical. Without them, the MP4s cannot be reproduced.
