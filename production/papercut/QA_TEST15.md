# QA — paper-cut ATLAS test scene (15 s), 2026-11-16

Video: `/mnt/project-files/papercut/test15/papercut_test15_v1.mp4`
(sha256 573d54e5…bd5c8, 10.4 MB, not committed — `*.mp4` is gitignored). Not published anywhere.

## Handoff checks
| Check | Result |
|---|---|
| ZIP SHA256SUMS.txt (32 files) | all OK |
| `code/validate_assets.py` (run with `python3 -I`, after reading it) | PASS |
| `code/render_safe.py --seconds 4` (960x540 and 1920x1080) | rendered, 120 frames, no errors |

## Gates (`papercut/qa.py`, automated)
| Gate | Result | Evidence |
|---|---|---|
| SOURCE_MATCH | PASS | hero = exact pixel crop of the approved sheet at (0,18): 220 154 visible px, max diff 0 |
| ALPHA_CHECK | PASS + visual | alpha 0..255; reviewed on black/white/grey/checker — no lettering or paper fragments |
| LAYER_CHECK | PASS | no experimental_layers in the package; loader refuses them |
| MOTION_BOUNDS | PASS | roll ≤ 1.6°, scale ≤ 2.5 %, bob ≤ 16 px @1080 (= 8 px @540), width 12.5–15.6 % |
| SCENE_CHECK | PASS | 0 frames cropped while on screen, 0 frames over the caption box |
| Smoothness | PASS | holding: max accel 0.02 / 0.10 / 0.41 px/frame²; eased entrance/exit max 3.7 / 4.6 |
| VIDEO_CHECK | PASS | H.264 1920x1080 30/1 yuv420p, 450 frames, 15.000 s, full decode clean, no black, no frozen segments |

## Visual review (done by me, from frames)
- Contact sheet every 0.5 s and 1:1 crops of the hero in all three shots: the character's outline,
  face, scarf and colours are identical to the approved cutout; no ghosting, no torn edges, no
  stray elements, no double images.
- Not done: real-time playback with eyes on a screen. Smoothness is judged from per-frame motion
  data and frame sheets, not from watching.

## Shots
- A 0–2.8 s: NASA SVS 15110 Artemis II Earthrise footage (source 4.20–7.00 s, contains one source cut
  at 0.8 s), slow push-in; hero slides in from the left, bottom-left, "listen".
- B 2.8–9.0 s: paper map, free-return path draws itself, capsule follows, camera pushes then pulls back,
  star parallax; hero floats bottom-right, "explain".
- C 9.0–15.0 s: paper orbit diagram, planets orbit, comet trail draws, camera push-in; hero left,
  "surprise", exits left at 14.2 s.

## Not implemented (by design)
Joint animation, walking, lip sync, blinks, expression changes. The test shows none of these and
claims none.
