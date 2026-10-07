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
/yt-render ──► final.mp4: picture + narration + burned-in captions + credit  (local, --confirm)
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
| `provider`, `model_id`, `voice_id` | string | who generated it (channel narrator: Adam, `pNInz6obpgDQGcFmaJgB`) |
| `voice_name`, `voice_source` | string | `Adam` / `default` unless `--voice-id` overrode the narrator |
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

yt-render produces the finished file in one step. Narration, captions and the credit go in the same
timeline as the clips, with no change to the files above and no FFmpeg step outside the skills:

```json
{
  "version": 1,
  "clips": [ ... ],
  "audio": {"voice": [{"src": "voice/narration.wav", "start": 0.0,
                       "meta": "voice/narration.voice.json"}]},
  "subtitles": {"src": "captions/captions.srt", "burn_in": true},
  "credit": {}
}
```

- The video length comes from the clips. The narration must fit inside it (`start + duration`);
  otherwise the render is refused instead of cutting speech. Narration timing is sample-exact;
  levelling is one constant gain to -16 LUFS (true peak ≤ -1.5 dBFS).
- `meta` ties the audio to its yt-voice metadata (`audio_sha256`, duration), so the captions built
  from those word timings cannot drift.
- `burn_in: true` draws the captions into the picture. `false` only validates them; the same SRT is
  then uploaded as a caption track.
- `credit: {}` draws the clips' `credit` strings (the USGS Landsat credit) on screen.
- `audio.music` and `audio.sfx` are still refused: there is no licensed music source, so nothing
  is ever added that the channel has no right to use.
- Then `/yt-qc final.mp4 --timeline timeline.json` checks the file.

## Vertical Short (timeline v3)

```
/yt-satellite (several dates, Natural Color GeoTIFF) ──► raw/*.tif
/yt-geo geostack.py ──► stack/<date>.png + grid.json + provenance.json   (same grid for every date)
/yt-geo watermask.py ──► geo/water_<date>.png                            (outlines, lost-area fills)
story/claims.json  ──► every spoken or on-screen claim, sourced, verified before TTS
/yt-voice ──► voice/narration.wav + .voice.json
/yt-captions --preset short ──► captions/captions.srt
/yt-render (version 3) ──► short.mp4 + short.manifest.json
/yt-qc --profile short --contact-sheet ──► PASS / FAIL + review sheet
```

Shots anchor to words of the narration, so the edit follows Adam's real timing. The first frame is
the hook. Production folders (raw imagery, stacks, audio, renders) stay in `productions/`, which
is git-ignored.

## Shorts format rule: composition resets

New information is not automatically a new visual composition. A Short has to reset the viewer's
attention periodically with a picture that is materially different, not only with new words on
the same picture.

| counts as a composition reset | does not count |
|---|---|
| a meaningful geographic zoom in or out | changed text or a new label |
| moving the camera somewhere else | a new year label |
| a full-frame before/after wipe | an outline, fill, arrow or pin |
| a rapid multi-year timelapse | a number or statistic |
| switching from the lake view to the river system | a caption |
| a close-up of one geographic feature | any overlay on essentially the same view |
| a scale comparison | |
| a different verified visual source (future) | |

Targets for a 45-60 s Short:

- first 10 s: at least 3 materially distinct compositions;
- whole Short: about 7-10 composition resets;
- no visually equivalent composition on screen for more than about 6 s, unless a continuous
  transformation (a timelapse, a wipe, a large camera move) is itself the visual event.

How it is measured - storyboard arithmetic on timeline v3, not computer vision. yt-render works it
out from the shots' cameras and layers: a view is materially different at a zoom of 1.5x or more,
or when its centre moves 35 % of the frame width or more; a `wipe` and a `flip` of 3 or more dates
(step up to 1 s) are resets; a continuous move counts once; changes within 0.75 s are one reset.
The plan and the render manifest carry `compositions`, the plan warns on a miss, and
`/yt-qc --profile short` checks it (fewer than 3 compositions in the first 10 s fails; the reset
count and the 6 s hold warn). Future visual sources will declare themselves as resets the same way.

## Rules every stage keeps

- JSON on stdout, structured errors, no tracebacks.
- Paid or real-world actions need `--confirm`. Cost and size limits are checked before they run.
- Outputs are written to temp files and renamed into place, and never replace existing files
  without `--overwrite`.
- Credentials come from the environment only and are never printed.
- No fabricated evidence or timings: missing data is reported, not guessed.
