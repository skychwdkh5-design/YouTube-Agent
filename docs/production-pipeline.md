# Production pipeline interface

How the production skills hand work to each other. Each stage reads files the previous one wrote
and never edits them. The audience strategy in `CLAUDE.md` applies to every stage.

```
/yt-script ──► script.md
                 │
/yt-voice  ──► voice/narration.wav + voice/narration.voice.json   (paid, --confirm, --max-chars)
                 │
/yt-captions ► captions/captions.srt + .vtt + .json               (local, free)
                 │
/yt-render ──► final.mp4                                           (local, --confirm)
                 │
/yt-qc     ──► PASS / FAIL report
```

## Project layout

One folder per video. Paths inside the timeline are relative to it, which is also yt-render's
media root.

```
productions/<slug>/
  script.md                    # /yt-script output, [ON SCREEN: ...] directions included
  voice/narration.wav          # /yt-voice
  voice/narration.voice.json   # /yt-voice metadata, schema yt-voice/1
  captions/captions.srt        # /yt-captions
  captions/captions.vtt
  captions/captions.json       # schema yt-captions/1
  assets/...                   # stills, Landsat frames (from /yt-satellite)
  timeline.json                # /yt-render input
  final.mp4                    # /yt-render output, checked by /yt-qc
```

`productions/` holds generated media and is git-ignored.

## 1. yt-script → yt-voice

`script.md` is plain text or Markdown. yt-voice speaks everything except `#` headings,
`[bracketed directions]`, list markers and bold markers. The exact spoken text is stored in the
voice metadata, and that text is the reference for captions.

## 2. yt-voice → yt-captions: `narration.voice.json` (schema `yt-voice/1`)

| field | type | meaning |
|---|---|---|
| `schema` | `"yt-voice/1"` | format version |
| `provider`, `model_id`, `voice_id` | string | who generated it |
| `language` | BCP 47 | e.g. `en` |
| `audio` | string | file name of the narration, next to the metadata |
| `audio_sha256`, `duration` | string, seconds | identity and length of the audio |
| `characters`, `text`, `text_sha256` | | exactly what was sent and billed |
| `chunks[]` | `{index, characters, offset, duration, timing}` | one per provider request |
| `timing` | object or `null` | `{"source": "provider", "level": "word"}` when word timings exist |
| `words[]` | `{text, start, end}` | seconds from the start of `audio`; empty when `timing` is null |

yt-captions accepts this file (`--voice`) or any `{text, start, end}` list (`--words`). That second
path is where a forced aligner or speech-to-text would plug in later.

## 3. yt-captions → yt-render and upload: `captions/`

- `captions.srt` and `captions.vtt`: standard files with no overlaps and whole-millisecond stamps.
- `captions.json` (schema `yt-captions/1`): `language`, `settings`, `cues[] {index, start, end,
  text}`, and `validation {wording_preserved, no_overlaps, timestamps_valid, problems, warnings}`.

## 4. → yt-render: `timeline.json`

yt-render v1 renders stills only. It already reserves the keys below and rejects them with
`"status": "unsupported"` until the render phase that adds them. When that lands, the narration
and captions plug in like this, with no change to the files above:

```json
{
  "version": 2,
  "clips": [ ... ],
  "audio": {
    "voice": [{"src": "voice/narration.wav", "start": 0.0,
               "meta": "voice/narration.voice.json"}],
    "music": [],
    "sfx": []
  },
  "subtitles": {"src": "captions/captions.srt", "burn_in": false}
}
```

- The video length comes from the clips. The narration `duration` is the minimum the clips must cover,
  and yt-render will check this rather than cut speech.
- `burn_in: false` keeps captions as a separate track for upload. `true` burns them into the
  picture with FFmpeg's `subtitles` filter (Shorts).
- yt-qc then gains checks against `voice.json` (audio duration ≥ narration) and `captions.json`
  (cues inside the video length).

## Rules every stage keeps

- JSON on stdout, structured errors, no tracebacks.
- Paid or real-world actions need `--confirm`. Cost and size limits are checked before they run.
- Outputs are written to temp files and renamed into place, and never replace existing files
  without `--overwrite`.
- Credentials come from the environment only and are never printed.
- No fabricated evidence or timings: missing data is reported, not guessed.
