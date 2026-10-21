# Task: visual review (AGENT_REQUIRED)

Look at each frame file, decide whether it supports the on-screen text, and record what you SAW:
  python3 .claude/skills/yt-visualcheck/visualcheck.py --root productions/neom-line review --item "<item id>" --verdict supports|does_not_support|unclear --note "what the frame shows"

- `promise_006:shot` claims ['C20']: text 'y2026'; frames [0] `qa/frames/promise_006_shot_0.png`
- `method_019:label:1 PIXEL = 10 M OF GROUND` claims ['C15']: text '1 PIXEL = 10 M OF GROUND'; frames [0] `qa/frames/method_019_label_1_PIXEL___10_M_OF_GROUND_0.png`
- `method_019:shot` claims ['C15']: text 'y2026'; frames [0] `qa/frames/method_019_shot_0.png`
- `method_020:label:NOT VISIBLE: PERSON, CRANE, WINDOW` claims ['C15']: text 'NOT VISIBLE: PERSON, CRANE, WINDOW'; frames [0] `qa/frames/method_020_label_NOT_VISIBLE__PERSON__CRANE__WINDOW_0.png`
- `method_020:shot` claims ['C15']: text 'y2026'; frames [0] `qa/frames/method_020_shot_0.png`
- `method_021:shot` claims ['C16']: text 'flip y2020,y2021,y2022,y2023,y2024,y2025,y2026'; frames [0] `qa/frames/method_021_shot_0.png`, [1] `qa/frames/method_021_shot_1.png`, [2] `qa/frames/method_021_shot_2.png`, [3] `qa/frames/method_021_shot_3.png`, [4] `qa/frames/method_021_shot_4.png`, [5] `qa/frames/method_021_shot_5.png`, [6] `qa/frames/method_021_shot_6.png`
- `segment_039:graphic:i_ndwi_s1` claims ['C11']: text 'i_ndwi_s1'; frames [0] `qa/frames/segment_039_graphic_i_ndwi_s1_0.png`
- `checks_045:label:SENTINEL-2 - 10 M` claims ['C13']: text 'SENTINEL-2 - 10 M'; frames [0] `qa/frames/checks_045_label_SENTINEL-2_-_10_M_0.png`
- `checks_045:label:LANDSAT 8 - 30 M, SAME PLACE` claims ['C13']: text 'LANDSAT 8 - 30 M, SAME PLACE'; frames [0] `qa/frames/checks_045_label_LANDSAT_8_-_30_M__SAME_PLACE_0.png`
- `checks_045:shot` claims ['C13']: text 'wipe y2024->l2024'; frames [0] `qa/frames/checks_045_shot_0.png`, [1] `qa/frames/checks_045_shot_1.png`
- `limits_054:label:AT THIS RESOLUTION: NO BUILDING` claims []: text 'AT THIS RESOLUTION: NO BUILDING'; frames [0] `qa/frames/limits_054_label_AT_THIS_RESOLUTION__NO_BUILDING_0.png`

A review is bound to the frame's sha256; it is recorded as REVIEWED_BY_AGENT, never as machine-verified.
