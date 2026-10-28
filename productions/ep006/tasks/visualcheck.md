# Task: visual review (AGENT_REQUIRED)

Look at each frame file, decide whether it supports the on-screen text, and record what you SAW:
  python3 .claude/skills/yt-visualcheck/visualcheck.py --root productions/ep006 review --item "<item id>" --verdict supports|does_not_support|unclear --note "what the frame shows"

- `plan_002:shot` claims ['C13']: text 'wipe y2026->l2026'; frames [0] `qa/frames/plan_002_shot_0.png` (reviewed: supports), [1] `qa/frames/plan_002_shot_1.png`
- `obs_030:shot` claims ['C13']: text 'wipe y2026->l2026'; frames [0] `qa/frames/obs_030_shot_0.png` (reviewed: supports), [1] `qa/frames/obs_030_shot_1.png`
- `obs_031:shot` claims ['C14']: text 'wipe y2026->l2026'; frames [0] `qa/frames/obs_031_shot_0.png` (reviewed: supports), [1] `qa/frames/obs_031_shot_1.png`

A review is bound to the frame's sha256; it is recorded as REVIEWED_BY_AGENT, never as machine-verified.
