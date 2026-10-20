# Task: visual review (AGENT_REQUIRED)

Look at each frame file, decide whether it supports the on-screen text, and record what you SAW:
  python3 .claude/skills/yt-visualcheck/visualcheck.py --root productions/neom-line review --item "<item id>" --verdict supports|does_not_support|unclear --note "what the frame shows"

- `shows_033:graphic:g_cmp_2020_2024_c17` claims ['C17']: text 'g_cmp_2020_2024_c17'; frames [0] `qa/frames/shows_033_graphic_g_cmp_2020_2024_c17_0.png`, [1] `qa/frames/shows_033_graphic_g_cmp_2020_2024_c17_1.png` (reviewed: supports)
- `shows_034:shot` claims ['C17']: text 'wipe y2020->y2024'; frames [0] `qa/frames/shows_034_shot_0.png`, [1] `qa/frames/shows_034_shot_1.png` (reviewed: supports)
- `shows_036:graphic:g_cmp_2020_2024_c19` claims ['C19']: text 'g_cmp_2020_2024_c19'; frames [0] `qa/frames/shows_036_graphic_g_cmp_2020_2024_c19_0.png`, [1] `qa/frames/shows_036_graphic_g_cmp_2020_2024_c19_1.png` (reviewed: supports)
- `shows_037:shot` claims ['C19']: text 'wipe y2020->y2024'; frames [0] `qa/frames/shows_037_shot_0.png`, [1] `qa/frames/shows_037_shot_1.png` (reviewed: supports)

A review is bound to the frame's sha256; it is recorded as REVIEWED_BY_AGENT, never as machine-verified.
