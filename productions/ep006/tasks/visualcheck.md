# Task: visual review (AGENT_REQUIRED)

Look at each frame file, decide whether it supports the on-screen text, and record what you SAW:
  python3 .claude/skills/yt-visualcheck/visualcheck.py --root productions/ep006 review --item "<item id>" --verdict supports|does_not_support|unclear --note "what the frame shows"

- `plan_006:shot` claims ['C2']: text 'y2026'; frames [0] `qa/frames/plan_006_shot_0.png`

A review is bound to the frame's sha256; it is recorded as REVIEWED_BY_AGENT, never as machine-verified.
