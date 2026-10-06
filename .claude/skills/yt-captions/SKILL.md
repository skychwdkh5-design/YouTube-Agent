---
name: yt-captions
description: >-
  Build YouTube-ready SRT and VTT captions from the word timings yt-voice produced - readable
  phrase-sized cues, exact spoken wording, no overlaps. Use for "captions", "subtitles", "make
  an SRT", "add closed captions". Not for chapters (/yt-chapters).
---

# yt-captions

Exact words, exact timings, cut into blocks a viewer can read.

```bash
python3 captions.py --voice voice/narration.voice.json --out-dir captions/
python3 captions.py --words words.json --out-dir captions/ --max-chars 64 --max-duration 5
```

Writes `captions.srt`, `captions.vtt` and `captions.json` (schema `yt-captions/1`: the cues, the
settings and the validation report). Prints JSON. Local only - no network, no cost.

## Input

- `--voice`: a `yt-voice/1` metadata file. Its `words` are the provider's own timings for the exact
  text that was spoken - the preferred source.
- `--words`: any JSON list of `{"text", "start", "end"}` (or `{"language", "words": [...]}`), so a
  later forced-alignment or speech-to-text step can feed the same builder.

**No timings, no captions.** A narration without provider timing is refused with
`"status": "no_timing"`. Captions are not built from estimated timings.

## Rules

| setting | default | meaning |
|---|---|---|
| `--max-chars` | 84 | characters per cue (about 42 per line) |
| `--max-lines` | 2 | lines per cue, balanced, never splitting a word |
| `--max-duration` | 6.0 s | longest cue on screen |
| `--min-duration` | 0.8 s | shortest cue, extended only into silence before the next cue |
| `--pause` | 0.6 s | a pause this long ends a cue once it is half full |
| `--language` | from the input, else `en` | BCP 47 tag, stored in `captions.json` |

Cues break at sentence ends first (`. ! ? …` and their CJK/Arabic forms), then at clause marks
(`, ; : —`) or pauses once half full. Timestamps are whole milliseconds, always increasing.
Cues never overlap: an end is pulled back to the next start if needed. The text of every cue is
the spoken words joined by single spaces, with all punctuation kept. The run fails if the
cues do not reproduce the spoken words exactly, in order. VTT escapes `&`, `<` and `>`.

A single word longer than `--max-chars` gets its own cue and a warning.

Word splitting is on whitespace. A language written without spaces needs its word timings from
the provider or an aligner; the builder itself is language-neutral.

## Where it fits

`/yt-script` → `/yt-voice` → **`/yt-captions`** → `/yt-render` (burn-in) and the upload step
(SRT/VTT track). Layout and fields: [`docs/production-pipeline.md`](../../../docs/production-pipeline.md).

## The gate

Nothing here publishes. The last line of every run is the question: **read them against the audio,
or change the settings?**
