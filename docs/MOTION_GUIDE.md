# Orbital Atlas — Motion Guide (1080p30 documentary)

Status: working standard for new Orbital Atlas motion, introduced with the EP009 B04 motion test
(2026-11-03). It does not change the approved art direction (`docs/ORBITAL_ATLAS_VISUAL_STYLE.md`,
style 3), the handoff contract (`docs/PAINTED_VIDEO_HANDOFF.md`) or any factual, rights, QC, cost or
publishing gate. The render engine stays the NumPy + Pillow compositor (V7 lineage) and FFmpeg.

Code: `tools/motion/easing.py` (named curves), `tools/motion/compositor.py` (pivot, bend, shadow,
camera, motion blur), tests in `tools/motion/test_motion.py`. Worked example and QC:
`productions/ep009-tornado-scars/review/motion_test_B04/`.

## 0. Credits and licence

Sections 1–3 adapt principles from **Emil Kowalski, "Skills for Designers and Engineers"**
(https://github.com/emilkowalski/skills, commit f1090be, skills `emil-design-eng`, `animate`,
`review-animations`, `animation-vocabulary`). Licensed under the **MIT License, Copyright (c) 2026
Emil Kowalski**: permission is granted free of charge to use, copy, modify, merge, publish and
distribute, provided the copyright notice and permission notice are included in copies or
substantial portions; the software is provided "as is", without warranty of any kind. The two
cubic-bezier curves marked *(EK)* below are his published values. Everything else — the
re-timing for broadcast video, the physical curves, the camera/depth rules — is Orbital Atlas
adaptation, because his rules target interactive UI (a 200 ms dropdown) and do not transfer to a
viewer watching a 1080p30 documentary without change.

## 1. Every motion needs a job

Before animating anything, name its narrative job (from the style guide): **actor, action, result,
comparison, reaction or evidence**. If the only answer is "it looks nicer", it does not move.
*(EK: "every animation must have a clear answer to why does this animate".)*

- One dominant moving subject at a time. Secondary motion (crown sway, dust, camera drift) must be
  smaller in amplitude and lower in contrast than the main action.
- Motion explains cause and consequence: the thing that causes moves first, the consequence follows.
- Nothing appears from nothing: no pop to full size, no `scale(0)` start, no hard opacity cut of a
  prop onto a static background (§5). *(EK: "never animate from scale(0)".)*

## 2. Named easing curves (use only these)

The easing on keyframe *i* shapes the segment to keyframe *i+1*. Keyframes without an easing render
with `v7_smoothstep`, i.e. exactly as V7 did. Never type a new bezier inside a build script — add a
preset to `easing.py` and to this table.

| Name | Shape | Use for | Typical 30 fps duration |
|---|---|---|---|
| `enter` *(EK, 0.23,1,0.32,1)* | fast start, long soft landing | props, panels, type arriving | 18–27 frames (0.6–0.9 s) |
| `exit` (0.55,0,0.75,0.2) | gentle start, accelerates away | objects leaving frame, handing attention on | 12–20 frames |
| `move` (0.6,0,0.3,1) | balanced ease-in-out | an object travelling across visible space | 24–60 frames |
| `move_strong` *(EK, 0.77,0,0.175,1)* | decisive ease-in-out | short purposeful moves, match moves | 15–30 frames |
| `camera` (0.37,0,0.63,1) | sine-like, never snaps | push, pull, pan, drift | whole beat (90–300 frames) |
| `reveal` (0.16,1,0.3,1) | quick reveal, slow read | wipes, masks, route/line draws | 20–45 frames |
| `anticipate` (0.36,0,0.66,-0.56) | dips back, then goes | wind-up before a launch, push, fall | 6–12 frames |
| `gravity` (p²) | free fall | dropped objects (height progress) | physics, see §4 |
| `topple` (integrated θ''=sin θ) | slow release, then accelerating | trees, masts, towers tipping over a base | 20–30 frames |
| `settle_soft` (spring, bounce 0.12) | lands with barely visible overshoot | light objects arriving | 12–20 frames |
| `settle_impact` (spring, bounce 0.32) | visible rebound | heavy object after impact | 15–25 frames |
| `linear` | constant | dissolves under motion blur, constant drifts, counters | — |
| `v7_smoothstep` | legacy | only to reproduce V7 renders | — |

**UI rule vs video rule.** In UI, `ease-in` is banned because the user waits for feedback *(EK)*.
In video it is correct for two things: objects leaving the frame (`exit`) and physical
acceleration (`gravity`, `topple`). It is still wrong for anything *arriving*.

## 3. Timing for a viewer, not a clicker

UI durations (100–300 ms) are too short for documentary: the viewer did not trigger the motion and
must first find it. Re-timed for 1080p30:

- **Arrivals** 0.6–0.9 s; **exits** 0.4–0.7 s (exits are shorter than entrances).
- **Read time**: text on screen ≥ 0.4 s + 0.25 s per word after it has finished moving; a number
  stays still at least 1.5 s. Text never moves while it must be read.
- **Holds**: after a key action, hold its result 0.5–1.0 s before the next beat starts.
- **Stagger** between sibling elements 3–5 frames (0.10–0.17 s); never more than 6 siblings.
- **Anticipation** ≤ 10 % of the main action's duration and ≤ 1/10 of its amplitude.
- **Word anchors**: the visible peak of an action sits on the stressed word of the final voice,
  within ±2 frames. Provisional timings (no final voice yet) must be re-anchored, never forced.
- **No dead frames** inside a beat: if a frame-to-frame difference is ~0 for > 0.5 s, either it
  is a deliberate hold (documented) or something should be drifting (camera, wind, light).

## 4. Natural motion of objects

- **Rotate about the physical pivot**, not the bitmap centre: the lee edge of a root plate, a
  hinge, a wheel contact, a ship's turning point. `compositor.place(..., pivot)`.
- **Use physics where the viewer knows physics**: falls accelerate (`gravity`), tipping starts slow
  and ends fast (`topple`), heavy things rebound little (`settle_impact` with small amplitude),
  air slows dust and leaves (drag).
- **Organic objects bend before they move**: crowns, cloth, smoke, water edges. Use
  `compositor.bend` (base planted, top displaced ∝ height², crown lags the trunk) instead of a
  rigid rotation. Amplitude grows before the main action (wind builds) and decays after.
- **Overlap and follow-through**: parts with more mass or length arrive later (crown after trunk,
  cargo after hull). Model it as a phase lag, not as separate random wobbles.
- **Two states of one painted object** (intact → broken) cannot be morphed by moving pixels. Swap
  inside the moment of highest motion (impact), in 2–4 frames, masked by motion blur, a blur of
  ~3 px on both layers *(EK: "use blur to mask imperfect transitions")*, shake and occlusion.
  Align the two silhouettes first (pivot, scale, angle) — the B04 test reaches IoU 0.50 on trunk
  and root plate. Report the swap; never pass it off as a continuous transformation.
- **Motion blur** only on frames that move > ~1.5 % of frame width per frame: 180° shutter,
  5–7 temporal samples (`compositor.supersample`). Static frames stay sharp.

## 5. Appearing and disappearing (2.5D painted objects)

Forbidden: a prop cut or faded in at full size on top of a still background ("sticker pop"), a
prop sliding while the background is frozen, scale-from-zero, spinning entrances.

An arrival combines at least three of: rise or travel from a motivated direction (24–40 px),
scale 0.94–0.97 → 1, defocus 6–8 px → 0, opacity, contact shadow growing as it lands, background
receding (soft focus + local dim), camera adjusting to frame it. All on `enter`.

A departure is motivated by the next beat: exit along the direction of the next action on `exit`,
or be occluded/obscured by the next layer (cloud, wipe, match cut). The shadow leaves with it.

Painted layers are **2.5D** (style guide): do not fake a 3D rotation by squashing a flat cutout
beyond ±10°; if a turn needs another view, a separate painted view is an asset request.

## 6. Virtual camera, depth, parallax, shadows, overlaps

- **Never upscale documentary pixels.** The camera window onto a NASA/USGS/NOAA frame is ≥ 1920
  source px wide (`compositor.Camera` refuses smaller windows). Pushes are bought by starting
  wider, not by enlarging.
- **Camera on `camera` easing, keyed over the whole beat**, not the clip: a push that decelerates
  to zero at a cut looks like a stall.
- **Parallax by depth**: background depth 1.0, illustrated foreground 1.15–1.35, labels/UI 0 (locked
  to the frame). `compositor.parallax` moves nearer layers further for the same camera move.
- **Camera follows action**: lead the subject slightly in its direction of travel; settle after it
  stops; never move the camera and the subject at the same speed in the same direction (it reads
  as a frozen subject).
- **Depth separation**: when a painted prop is the subject over a documentary image, the image
  recedes (0.5–2.5 px blur, 25–40 % local dim) and returns to full clarity when it is the evidence
  again. The documentary image itself is never repainted or altered.
- **Shadows follow the pose**: project the silhouette onto the ground plane from one consistent
  light (upper-left in the painted references) and add a tight contact occlusion where the object
  meets the ground (`compositor.ground_shadow`). V7's fixed offset drop shadow makes objects float
  and is kept only for parity.
- **Overlap order is story order**: the actor in front of what it affects; obstruction physically
  covers what it blocks; one focal element overlaps the rest.
- **Impacts**: damped shake 4–8 px, 12–14 Hz, decay ~0.3 s, slightly stronger on near layers;
  dust/debris in front of the contact point. Never shake for emphasis without an impact.

## 7. Test and review procedure for every new effect

1. Render a 5 s test of the effect in its real scene, plus the same 5 s with the previous method.
2. Run the QC script for the test (B04 example: `qc_b04.py`): format, black/freeze, motion energy
   per frame, curve fidelity measured on pixels, native-resolution rule.
3. Look at a 4 fps contact sheet, the before/after key frames and the full-speed video. Write the
   verdict in `REVIEW.md`: what improved, what is still wrong, what needs a new asset.
4. A clean FFmpeg exit is not a pass. The owner's full-speed viewing decides.

Review table format *(EK, review-animations)*: | Before | After | Why |, one row per issue.

## 8. Vocabulary for briefs

Use these words in storyboards/motion specs so intent is unambiguous *(adapted from EK
animation-vocabulary)*: **anticipation** (small opposite move before an action), **follow-through**
(parts keep moving after the main body stops), **overlap** (parts lag by mass), **settle** (decaying
rebound), **lead** (camera ahead of the subject), **match cut** (shape/position carried across a
cut), **reveal** (mask or wipe uncovering evidence), **rack focus** (depth separation shift),
**hold** (deliberate stillness to read).
