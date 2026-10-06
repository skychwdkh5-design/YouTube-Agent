# YouTube-Agent

Claude Code workspace for running a YouTube channel.

## Skills

Each skill lives in `.claude/skills/<name>/` (a `SKILL.md` plus any helper scripts):
`yt-audit`, `yt-chapters`, `yt-comment`, `yt-edit`, `yt-package`, `yt-plan`, `yt-retention`,
`yt-script`, `yt-seo`, `yt-shorts`, `yt-viral`, and `yt-satellite`.

### yt-satellite (optional)

Real Landsat evidence from the USGS EROS M2M API, used only when a video depends on satellite
imagery. It needs two environment variables - `USGS_M2M_USERNAME` and `USGS_M2M_TOKEN` (an M2M
application token). Nothing is stored in the repo. Without them every other skill works as before.

```bash
python3 .claude/skills/yt-satellite/usgs_m2m.py auth
python3 .claude/skills/yt-satellite/test_usgs_m2m.py          # offline tests
```
