# EP001: can the locked sequences go into the final timeline? (dry run, SIMULATED timings)

**Everything about timing below is simulated.** No narration audio exists. `dry_run/build_dry_run.py` generates word timings from the locked text at 145 words per minute, a silent WAV and a `*_SIMULATED.voice.json` flagged `"simulated": true`. The real run replaces those files with the ElevenLabs output and re-runs the same steps. Large files stay outside Git; committed: `timeline_dry_run_SIMULATED.json`, `dry_run_report.json`, six stills.

## What was built
A 82.5 s profile-`long` timeline (30 fps, segmented 30 s) covering narration units S046-S058: placeholder card (scene 17), East Oweinat (video asset, 17 s), placeholder card (scenes 19-20), Toshka (video asset, 20.6 s), placeholder tail. Captions come from the real yt-captions pipeline run on the simulated words. The two sequences are the locked renderer's output (`visuals/scripts/render.py`) driven by `cues.py fit` schedules at 720p / 30 fps.

## Results
| Question | Result |
|---|---|
| Do the sequences insert as native video assets? | Yes: plan validated, render ok (82.5 s, 3 segments, 2,475 frames, 30 fps). |
| Are they frame-exact on the timeline? | Yes. 16 sampled frames (first, last and interior frames of both clips) compared with the sequence videos by PSNR (38-45 dB, same frame). The first frame of each clip differs strongly from the preceding shot (6-7 dB) and the last frame from the following shot (7-8 dB), so both boundaries are exact to the frame. Inside static holds neighbouring frames are identical, so there the offset cannot be told apart (ties accepted, documented in the report). |
| Do the sequences follow the narration? | Yes: `fit_east_oweinat` and `fit_toshka` (report) place 1984 from S047, the dissolve chain from 0.25 s before S049, the zoom 3.5 s into S050; Toshka 2002/2011/2021 land on S056/S057/S058. |
| Captions vs the sequences' own text | 0 collisions in 11 caption cues inside the two sequence shots, using `caption` placement (East Oweinat: `band 0.76, center_x 0.667, max_width 1100`; Toshka: `band 0.76`). |
| "By 2012" clarification | `Narration says "by 2012"; this image is from January 2011.` appears only on the single January 2011 frame (about 4 s while S057 is spoken; see `stills/toshka_2011_clarification_caption.jpg`). The image date and label stay January 2011. |
| Pixel preservation | Locked imagery, tone B, crops and zoom window are unchanged (visual QA 19/19 still passes; clarification is an overlay on one frame). |

## Findings that need a decision
1. **East Oweinat does not fit its narration window with the delivered 21.7 s pacing.** At 145 wpm the window S047 to the end of S050 is about 17 s. The fitted schedule: 1984 held 7.5 s, then holds of 0.9 s per frame, and a **3.5 s** zoom (the delivered cut had 6 s). It only fits because the zoom may run until the end of S050 ("The water comes from below."). Scene 19's card then starts about 2.2 s later than the storyboard assumed. With the real audio the solver either fits or reports the shortfall in seconds; narration is never sped up.
2. **The 1984 hold is a static 7.5 s** (barren sand plus a static panel). yt-qc flags `freezes`: 5.43 s static against a 5.0 s limit. Options: a very slow push-in on the 1984 view (at most 3 percent, 30 m Lanczos, inside the upscale policy), start the 2000 dissolve earlier (during "barren"), or waive the check. Not changed without your decision (VISUAL LOCK).
3. **yt-qc on the dry run FAILS for reasons that belong to the simulation**: silent audio (loudness, audio start) and placeholder cards (pacing warnings: 35 s on one composition, 2.9 resets per minute). They are not film defects and will not occur with the narration and the other scenes. The only qc item about the real design is the freeze above.
4. The dry run uses the 720p sequence renders scaled to 1080p; the final render uses `render.py --scale 2` (3840x2160 clips, then yt-render scales to 1080p or the final profile). The production timeline needs the 4K clips only if the master is 4K; yt-render's long profile is 1920x1080.
