# Task: visual review (AGENT_REQUIRED)

Look at each frame file, decide whether it supports the on-screen text, and record what you SAW:
  python3 .claude/skills/yt-visualcheck/visualcheck.py --root productions/neom-line review --item "<item id>" --verdict supports|does_not_support|unclear --note "what the frame shows"

- `shows_028:shot` claims ['C9']: text 'y2020'; frames [0] `qa/frames/shows_028_shot_0.png`
- `shows_029:shot` claims ['C9']: text 'y2022'; frames [0] `qa/frames/shows_029_shot_0.png`
- `shows_030:shot` claims ['C9']: text 'y2023'; frames [0] `qa/frames/shows_030_shot_0.png`
- `shows_031:shot` claims ['C9']: text 'y2026'; frames [0] `qa/frames/shows_031_shot_0.png`

A review is bound to the frame's sha256; it is recorded as REVIEWED_BY_AGENT, never as machine-verified.
