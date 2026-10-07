---
name: yt-voice
description: >-
  Generate the narration audio for a finished script through a TTS provider (ElevenLabs first),
  with word timings for captions. Paid request - needs --confirm and stays under --max-chars. Use
  for "voice this", "make the voiceover", "narrate the script", "generate the audio". Not for
  writing the script (/yt-script) or captions (/yt-captions).
---

# yt-voice

The script in, the narration out - plus the exact words and when each one was said.

```bash
python3 voice.py --script script.md --output voice/narration.wav             # plan, free
python3 voice.py --script script.md --output voice/narration.wav --confirm   # PAID
```

Every command prints JSON. Then build captions from the timings with `/yt-captions`.

## The channel narrator

**Adam** (ElevenLabs voice ID `pNInz6obpgDQGcFmaJgB`) is the channel's permanent narrator and the
default whenever `--voice-id` is not given. It is set once, as `default_voice` on the ElevenLabs
provider in `voice.py`. Use `--voice-id` only for a deliberate one-off; the plan, the result and the
metadata record `voice_id`, `voice_name` and `voice_source` (`default` or `argument`), so a video
narrated in a different voice is visible.

Authentication stays with the environment: `YT_VOICE_AUTH=proxy` is set there, so the egress proxy
adds the ElevenLabs key and no key is passed, stored or committed.

## Cost first, every time

1. **Run without `--confirm` first.** Nothing is sent. You get the spoken text, the character count
   and the number of requests. Show the user the count before you spend anything.
2. `--max-chars` (default 3000, about 3 minutes of speech) is checked **before any request**. Over it,
   the run stops with `"status": "over_limit"`. Raise it only when the user has agreed to that size.
3. Only then run with `--confirm`. ElevenLabs bills per character of the text sent.

## What is spoken

`--script` takes a `/yt-script` script and drops what is not said aloud: `#` headings, every
`[ON SCREEN: ...]` / `[B-ROLL]` style direction, list markers and `**bold**` markers. Every spoken
word and its punctuation stays. The dropped parts are listed under `removed_from_script` - check
them. `--keep-markup` sends the text as-is; `--text "..."` takes a string instead of a file.

Long scripts are split at paragraph, then sentence, then word boundaries (`--max-chunk-chars`,
default 2500), one request per chunk, joined into one file with exact per-chunk offsets.

## Output

- `voice/narration.wav` (PCM 16-bit 44.1 kHz mono, or `.mp3` if the output name says so)
- `voice/narration.voice.json` (schema `yt-voice/1`): provider, model, voice id, language,
  `audio_sha256`, `duration`, `characters`, the exact spoken `text`, `chunks` with offsets, and
  `words` - `[{"text": "world.", "start": 1.23, "end": 1.61}, ...]` - when the provider returned
  alignment.

Timings are kept only when the provider's character alignment matches the text exactly and the
times make sense. Otherwise `"timing": null`, `words` is empty, and a warning says so. No timing is
ever estimated.

## Providers

| provider | credential | notes |
|---|---|---|
| `elevenlabs` (default, narrator Adam `pNInz6obpgDQGcFmaJgB`) | `ELEVENLABS_API_KEY`, or `--auth proxy` (or `YT_VOICE_AUTH=proxy`) when the key is a network secret the egress proxy adds | `/v1/text-to-speech/{voice_id}/with-timestamps`, `eleven_multilingual_v2` unless `--model`, mp3 44.1 kHz, character alignment |

A new provider is one class in `PROVIDERS` (`voice.py`) with `synthesize(text, voice_id)` returning
the audio bytes, their format and an optional character alignment, plus an optional `default_voice`
(without one, `--voice-id` is required). Nothing downstream changes.

## Safety

- With `--auth proxy` the script sends no key at all: the session's egress proxy adds the
  configured network secret to requests for `api.elevenlabs.io`, so the key never enters this
  process. Otherwise the key comes from the environment only. It is sent only in the provider's auth header, and
  it is redacted from every message. It is never printed, logged or written into the metadata. If it is
  missing the run says which variable, and you pass that on - never ask the user to paste a key.
- Audio and metadata are built in a hidden temp folder and renamed into place only after every
  chunk succeeded, so a network failure, a malformed response or undecodable audio leaves nothing
  behind. Existing files are not replaced without `--overwrite`.
- `--voice-id` is restricted to letters, digits, `-` and `_`. An error is reported verbatim from the
  `error` field and never retried in a loop - a retry is another paid request.
- A cloned voice of a real person needs that person's consent. Realistic synthetic content may need
  YouTube's altered-content disclosure.

## Where it fits

`/yt-script` → **`/yt-voice`** → `/yt-captions` → `/yt-render`. The file layout and fields are in
[`docs/production-pipeline.md`](../../../docs/production-pipeline.md).

## The gate

Nothing here publishes. The last line of every run is the question: **listen to it, or change
the script?**
