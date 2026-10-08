# YouTube-Agent

Claude Code workspace for running a YouTube channel.

## Skills

Each skill lives in `.claude/skills/<name>/` (a `SKILL.md` plus any helper scripts):
`yt-audit`, `yt-chapters`, `yt-comment`, `yt-edit`, `yt-package`, `yt-plan`, `yt-retention`,
`yt-script`, `yt-seo`, `yt-shorts`, `yt-viral`, `yt-satellite`, `yt-geo`, `yt-graphics`, `yt-render`, `yt-qc`, `yt-voice` and `yt-captions`.

### yt-satellite (optional)

Real Landsat evidence from the USGS EROS M2M API, used only when a video depends on satellite
imagery. It needs two environment variables - `USGS_M2M_USERNAME` and `USGS_M2M_TOKEN` (an M2M
application token). Nothing is stored in the repo. Without them every other skill works as before.

```bash
python3 .claude/skills/yt-satellite/usgs_m2m.py auth
python3 .claude/skills/yt-satellite/test_usgs_m2m.py          # offline tests
```

### yt-render and yt-qc

Real MP4 rendering from a `timeline.json` (stills and Landsat frames, Ken Burns, crossfades,
1920x1080 30 fps H.264 + AAC) and a technical check of the result. Local FFmpeg/FFprobe only - no
network, no credentials. Rendering needs `--confirm`; rendered MP4s are git-ignored.

```bash
python3 .claude/skills/yt-render/render.py --timeline timeline.json --output final.mp4 --confirm
python3 .claude/skills/yt-qc/qc.py final.mp4 --timeline timeline.json
python3 .claude/skills/yt-render/test_render.py && python3 .claude/skills/yt-qc/test_qc.py
```

### yt-voice and yt-captions

Narration through a TTS provider (ElevenLabs first, `ELEVENLABS_API_KEY` or `YT_VOICE_AUTH=proxy`)
with word timings, and SRT/VTT captions built from those timings. The channel narrator is Adam
(`pNInz6obpgDQGcFmaJgB`), the default voice. Generation is a paid request: it needs `--confirm` and
stays under `--max-chars`. Captions are local and free. How script → voice → captions → render
connect: [`docs/production-pipeline.md`](docs/production-pipeline.md).

```bash
python3 .claude/skills/yt-voice/voice.py --script script.md --output voice/narration.wav   # narrator: Adam
python3 .claude/skills/yt-captions/captions.py --voice voice/narration.voice.json --out-dir captions/
python3 .claude/skills/yt-voice/test_voice.py && python3 .claude/skills/yt-captions/test_captions.py
```

### Long-form documentaries (16:9)

Timeline v3 also renders `"profile": "long"`: 1920x1080, 30 fps, up to 15 minutes, in segments joined
without re-encoding, with landscape captions and the same camera, wipes, labels, credits and pacing
checks; `yt-qc --profile long` checks it. `yt-graphics` makes the explanatory diagrams, charts and annotated
satellite views that go into it.

### Vertical Shorts (MVP v0.1)

`yt-geo` aligns several Landsat dates on one grid; `yt-render` timeline version 3 renders a
1080x1920 Short (geographic camera, wipes, year flips, outlines, labels, word-anchored shots,
mobile-safe captions, per-shot credits); `yt-qc --profile short` checks it, including the
composition-reset rule (new information is not a new composition: at least 3 distinct compositions
in the first 10 s, about 7-10 resets, no composition held over 6 s). Storyboards can also tag each shot's
`visual_family`, so a new view of the same visual idea is not mistaken for something new (warnings only). See
[`docs/production-pipeline.md`](docs/production-pipeline.md).
