# EP009 B04 motion test — review (2026-11-03)

**Status: MOTION TEST ONLY.** Provisional timing, no voice, not the approved pilot, not a release.
Full EP009 / pilot is not rebuilt until the owner has watched this and confirmed.

Scene: pilot B04, 12.0–17.0 s (narration "That pale line crossing Alabama was carved into the
landscape by a tornado."): painted tree P03 over NASA EO-1 M01. Chosen because the pilot keys
describe the crudest motion in the pilot: an intact tree that slides, rotates about its bitmap
centre and fades out while a second painting fades in somewhere else.

| Version | File (git-ignored, sent in chat) | Built from |
|---|---|---|
| Before | `B04_before_5s.mp4` | `handoff/pilot_keyframes.json` B04 literally, V7 rendering model (centre scale, smoothstep, fixed drop shadow, crossfade) |
| After | `B04_after_5s.mp4` | `b04_improved_keyframes.json` + `tools/motion` (named curves, pivot topple, bend, projected shadow, depth, parallax, motion blur) |
| Review | `B04_side_by_side.mp4`, `B04_*_contact_sheet.jpg`, `B04_before_after_frames.jpg`, `B04_motion_chart.png`, `qc_report.json` | `qc_b04.py` |

Reproduce from the repository root:
```
python3 productions/ep009-tornado-scars/tools/verify_illustrated_assets.py
python3 productions/ep009-tornado-scars/review/motion_test_B04/build_b04.py all
python3 productions/ep009-tornado-scars/review/motion_test_B04/qc_b04.py
python3 -m unittest tools/motion/test_motion.py
```

## Technical QC (qc_report.json)

All measurable checks pass: 1920x1080, 30 fps, 150 frames, H.264 yuv420p, no black frames, NASA
frame never upscaled (camera window ≥ 2050 px), rendered rotation follows the `topple` curve within
0.10° (measured on the silhouette, not read from the JSON), motion peak sits on the impact (15.2 s).

| Measure | Before | After |
|---|---|---|
| Frames with no motion | 64 of 150 (freeze 0–2.07 s) | 0 |
| Mean motion energy | 0.40 | 1.24 |
| Where the strongest motion is | 14.33 s (the fade, not an event) | 15.20 s (the impact) |

A clean FFmpeg exit was not used as a pass criterion.

## Visual review (frames, contact sheets, chart)

| Before | After | Why |
|---|---|---|
| Tree is on screen fully formed at frame 0 over a frozen satellite frame | Rises 34 px, 0.95→1 scale, defocus 7→0 px on `enter`; background recedes (2.4 px blur, 38 % local dim) | No "sticker pop"; the illustration is separated from the evidence image |
| 2 s of total stillness | Wind builds 12.5–13.9 s: crown bends, top lags the trunk (`move`) | Cause before consequence; no dead frames |
| Tree rotates −12° about the bitmap centre and drifts down while fading | Anticipation +2° into the wind, then tips −54° about the lee edge of the root plate on `topple` (integrated θ''=sin θ) | Slow release, accelerating fall — what a viewer expects a heavy tree to do |
| Intact tree fades out at one spot, uprooted tree fades in 50 px away | Swap inside the impact: silhouettes aligned (IoU 0.50 on trunk/root plate), 2-frame dissolve under 3 px blur, motion blur, shake | The change of state reads as the landing, not as a slideshow dissolve |
| Fixed offset drop shadow: the tree floats above the map | Shadow projected from the pose onto a ground line + contact occlusion | Weight and ground contact |
| Uprooted tree keeps sliding and rotating after it has fallen | Spring rebound 2.5° → 0 (`settle_impact`), then only a light crown sway | A fallen tree stops; residual motion is organic, not drift |
| Camera static | Push 2112 → 2050 source px on `camera` keyed over the whole beat, foreground depth 1.25 (parallax) | Space without upscaling the NASA frame |

## What is still not right (honest list)

1. **The swap is visible if you look for it.** Two frames (15.17–15.20 s) show a blurred double
   image of the intact and the broken painting. They are different paintings (the broken crown is
   sparser, about 15 % larger to align the trunk). Fix needs an asset, not code: the intact tree
   cut into root plate / trunk / crown layers, or a "falling" painted frame.
2. **Grass-mound wedge during the fall.** The intact painting has no separate root plate, so the
   grass base rotates with the tree as a sharp wedge (14.9–15.15 s, partly hidden by motion blur).
3. **No ground for the illustration.** The storyboard asks for a separate illustration pane;
   pilot_keyframes put the tree straight onto the satellite map. I kept the pilot composition so
   the test compares motion only. The tree still sits on a city-scale map at an impossible scale;
   the shadow and depth-of-field help but a painted ground plate (P03 base) or the pane layout is
   the real fix — an editorial decision for the owner.
4. **Dust is almost invisible.** Procedural soft haze only; I deliberately did not push it, because
   procedural particles over painted style quickly look fake. A painted debris/leaf layer would be
   better.
5. **Wind sway is subtle** on a 486 px tree (crown moves ≤ 24 px). Judge it at full speed; amplitude
   is one number in the keyframe file.
6. Full-speed playback was judged from frame sequences and the motion chart here; the owner's
   viewing at full speed on the target screen is the deciding check (handoff: iPad review).

## Performance on the current engine (2-core workspace)

| | Before (V7 model) | After |
|---|---|---|
| Render time, 150 frames | 12 s (0.08 s/frame) | 89 s (0.59 s/frame; 0.34 s per pass + 7-sample motion blur on 18 frames) |

Extrapolated: the 56 s pilot ≈ 10–15 min; a 7-minute episode ≈ 1–1.5 h single process, about half
with one process per core (frames are independent). Peak memory measured at 270 MB per process. The cost is offline
render time only — acceptable — and is ~4–7× V7 per frame.
