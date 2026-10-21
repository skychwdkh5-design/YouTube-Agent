# Task: visual review (AGENT_REQUIRED)

Look at each frame file, decide whether it supports the on-screen text, and record what you SAW:
  python3 .claude/skills/yt-visualcheck/visualcheck.py --root productions/neom-line review --item "<item id>" --verdict supports|does_not_support|unclear --note "what the frame shows"

- `plan_011:graphic:i_semafor_s1` claims ['C3']: text 'i_semafor_s1'; frames [0] `qa/frames/plan_011_graphic_i_semafor_s1_0.png`
- `plan_014:graphic:i_opened_s1` claims []: text 'i_opened_s1'; frames [0] `qa/frames/plan_014_graphic_i_opened_s1_0.png`
- `plan_015:graphic:i_described_s1` claims []: text 'i_described_s1'; frames [0] `qa/frames/plan_015_graphic_i_described_s1_0.png`
- `method_019:label:1 PIXEL = 10 M OF GROUND` claims ['C15']: text '1 PIXEL = 10 M OF GROUND'; frames [0] `qa/frames/method_019_label_1_PIXEL___10_M_OF_GROUND_0.png`
- `method_019:label:5 PIXELS = 50 M` claims ['C15']: text '5 PIXELS = 50 M'; frames [0] `qa/frames/method_019_label_5_PIXELS___50_M_0.png`
- `method_019:shot` claims ['C15']: text 'y2026'; frames [0] `qa/frames/method_019_shot_0.png`
- `method_022:graphic:i_orbit_s1` claims ['C16']: text 'i_orbit_s1'; frames [0] `qa/frames/method_022_graphic_i_orbit_s1_0.png`
- `method_023:graphic:i_season_s1` claims ['C16']: text 'i_season_s1'; frames [0] `qa/frames/method_023_graphic_i_season_s1_0.png`
- `checks_046:label:SENTINEL-2: 10 M PIXELS` claims ['C13']: text 'SENTINEL-2: 10 M PIXELS'; frames [0] `qa/frames/checks_046_label_SENTINEL-2__10_M_PIXELS_0.png`
- `checks_046:label:LANDSAT 8: 30 M PIXELS` claims ['C13']: text 'LANDSAT 8: 30 M PIXELS'; frames [0] `qa/frames/checks_046_label_LANDSAT_8__30_M_PIXELS_0.png`
- `checks_046:shot` claims ['C13']: text 'wipe y2024->l2024'; frames [0] `qa/frames/checks_046_shot_0.png`, [1] `qa/frames/checks_046_shot_1.png`

A review is bound to the frame's sha256; it is recorded as REVIEWED_BY_AGENT, never as machine-verified.
