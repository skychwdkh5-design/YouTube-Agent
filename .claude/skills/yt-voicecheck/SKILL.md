---
name: yt-voicecheck
description: >-
  Automatic check of a generated narration before captions and render: file readable, duration plausible against the script, every word timed and in order,
  no long silence, loudness sane, and a list of risky pronunciations with timestamps for a human listen. Free, no network. Runs after yt-voice (yt-orchestrate stage voicecheck).
---

# yt-voicecheck

```bash
python3 voicecheck.py --root productions/<slug>
```

Result `FAIL` blocks captions and render. Otherwise the result is `NEEDS_HUMAN_LISTEN`, never "PASS": a script cannot hear a mispronounced word, so the
moments in `risky` are listed with timestamps and the owner listens to them (and the first 30 s) before the full render.
After voicing, the orchestrator re-times the storyboard from the real word timings and re-runs visualcheck automatically.
