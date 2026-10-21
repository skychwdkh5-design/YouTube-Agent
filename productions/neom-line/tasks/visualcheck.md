# Task: visual review (AGENT_REQUIRED)

Look at each frame file, decide whether it supports the on-screen text, and record what you SAW:
  python3 .claude/skills/yt-visualcheck/visualcheck.py --root productions/neom-line review --item "<item id>" --verdict supports|does_not_support|unclear --note "what the frame shows"

- `method_018:graphic:i_source` claims ['C16']: text 'i_source'; frames [0] `qa/frames/method_018_graphic_i_source_0.png`
- `checks_047:graphic:i_apart_s1` claims ['C13']: text 'i_apart_s1'; frames [0] `qa/frames/checks_047_graphic_i_apart_s1_0.png`
- `checks_049:graphic:i_growth_s1` claims ['C12']: text 'i_growth_s1'; frames [0] `qa/frames/checks_049_graphic_i_growth_s1_0.png`

A review is bound to the frame's sha256; it is recorded as REVIEWED_BY_AGENT, never as machine-verified.
