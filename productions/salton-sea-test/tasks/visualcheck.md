# Task: visual review (AGENT_REQUIRED)

Look at each frame file, decide whether it supports the on-screen text, and record what you SAW:
  python3 .claude/skills/yt-visualcheck/visualcheck.py --root productions/salton-sea-test review --item "<item id>" --verdict supports|does_not_support|unclear --note "what the frame shows"

- `hook_001:shot` claims ['C5']: text 'wipe y2022->y2026'; frames [0] `qa/frames/hook_001_shot_0.png`, [1] `qa/frames/hook_001_shot_1.png`
- `shows_009:shot` claims ['C5']: text 'y2022'; frames [0] `qa/frames/shows_009_shot_0.png`
- `shows_010:graphic:g_cmp_2022_2026_c5` claims ['C5']: text 'g_cmp_2022_2026_c5'; frames [0] `qa/frames/shows_010_graphic_g_cmp_2022_2026_c5_0.png`, [1] `qa/frames/shows_010_graphic_g_cmp_2022_2026_c5_1.png`
- `shows_011:shot` claims ['C5']: text 'wipe y2022->y2026'; frames [0] `qa/frames/shows_011_shot_0.png`, [1] `qa/frames/shows_011_shot_1.png`

A review is bound to the frame's sha256; it is recorded as REVIEWED_BY_AGENT, never as machine-verified.
