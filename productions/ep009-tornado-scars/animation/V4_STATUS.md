# EP009 V4 — status at stop (03.11.2026)
Measured on V3 (OA_EP009_pilot_56s_v3.mp4): constant 30 fps, 1680 frames, no duplicates -> renderer timing is NOT the cause.
Causes found in code: int() placement of every layer (slow cloud bands: 53-84% of frames with 0 px step), camera easing stops at every key (velocity jump ~0 -> ~500 px/s at 14.3 s), value-noise dwell at lattice nodes, sprite swap + crossfade at tree fall, integer zoom crop, stepped storm-centroid tracking, GOES source clip repeats 313 of 590 frames at irregular gaps (intrinsic stutter).
V4 results: engine tests 10/10 pass; satellite scan test: camera residual 0.013 px RMS, 0 freeze frames, 0 duplicates; tree probe QC clean after fixing a real clod-landing discontinuity.
State: engine.py, ground_v4.py (tree physics), sat_v4.py done. Tree test renders were interrupted (tree_nb.mp4 not finalized, blur render stopped); pilot_v4.py is UNTESTED draft; OA_EP009_motion_diagnostic.md not written; audio v4 built only for test windows.
Not in git: MP4/WAV/voice files.
