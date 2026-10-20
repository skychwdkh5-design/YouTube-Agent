---
name: yt-storyboard
description: >-
  Turn a script and a visual vocabulary into a timed storyboard and a yt-render v3 long timeline: shots, camera moves, wipes,
  graphics inserts, labels - re-timed from real word timings once the narration exists. Use after the script passes yt-facts.
---

# yt-storyboard

```bash
python3 storyboard.py --episode productions/<slug> [--voice-meta voice/narration.voice.json --captions captions/captions.srt]
python3 test_storyboard.py
```
Reads `episode.json` (assets, chapters -> visuals; a visual is a map view `{asset, zoom:[from,to], focus, label}`, a `wipe: [a, b]`, or a graphic `{asset, kind:"graphic", min_s}`) and
`script.md` (`## id: Title` headings must match the chapters). Writes `timeline.json` (episode root = render media root), `story/storyboard.json`, `story/labels.json`
(for yt-facts), `story/report.md` (the yt-render planner's pacing warnings, shot list). Timing: words / 2.45 per second, or the real word timings when a voice exists.

Rules built in: camera views are clamped inside the imagery; map shots are split to <= 7 s with alternating zoom direction (each beat is a real composition change); graphics get
a fixed time (<= 7 s, never stretched to fill a chapter); on-screen numbers need claim ids; the plan is validated by `render.py` without rendering. A duration outside 6-12 minutes is a warning:
add real content, never filler.
