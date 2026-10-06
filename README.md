# YouTube-Agent

Claude Code workspace for running a YouTube channel.

## Skills

Each skill lives in `.claude/skills/<name>/` (a `SKILL.md` plus any helper scripts):
`yt-audit`, `yt-chapters`, `yt-comment`, `yt-edit`, `yt-package`, `yt-plan`, `yt-retention`,
`yt-script`, `yt-seo`, `yt-shorts`, `yt-viral`, `yt-satellite`, `yt-render` and `yt-qc`.

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
