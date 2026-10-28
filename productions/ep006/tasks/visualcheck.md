# Task: visual review (AGENT_REQUIRED)

Look at each frame file, decide whether it supports the on-screen text, and record what you SAW:
  python3 .claude/skills/yt-visualcheck/visualcheck.py --root productions/ep006 review --item "<item id>" --verdict supports|does_not_support|unclear --note "what the frame shows"

- `plan_002:label:26 AUG 2026 - LANDSAT 9 (30 M)` claims ['C13']: text '26 AUG 2026 - LANDSAT 9 (30 M)'; frames [0] `qa/frames/plan_002_label_26_AUG_2026_-_LANDSAT_9__30_M__0.png`
- `plan_002:shot` claims ['C13']: text 'l2026'; frames [0] `qa/frames/plan_002_shot_0.png`
- `plan_003:label:RADAR NUMBERS ARE ICIMOD'S` claims []: text "RADAR NUMBERS ARE ICIMOD'S"; frames [0] `qa/frames/plan_003_label_RADAR_NUMBERS_ARE_ICIMOD_S_0.png`
- `plan_012:graphic:i_toll_s1` claims ['C10']: text 'i_toll_s1'; frames [0] `qa/frames/plan_012_graphic_i_toll_s1_0.png`

A review is bound to the frame's sha256; it is recorded as REVIEWED_BY_AGENT, never as machine-verified.
