# Orbital Atlas — motion presets (v3, reusable)

Code: `motion.py` (easing, rigs, camera, sound synthesis). Episode assembly example: `build_pilot_v3.py`, `build_audio_v3.py`.

## 1. Easing by material and intent (named cubic-Bézier curves)
| Preset | cubic-bezier | Use for | Never use for |
|---|---|---|---|
| `camera_glide` | 0.45, 0.05, 0.20, 1.00 | motivated dollies, following the evidence | reaction hits |
| `camera_settle` | 0.16, 1.00, 0.30, 1.00 | reveals that arrive and then hold | heavy falls |
| `heavy_fall` | 0.55, 0.00, 0.90, 0.35 | trees, terrain blocks under gravity (slow start, accelerating) | light props |
| `heavy_land` | 0.10, 0.70, 0.25, 1.00 | massive object coming to rest — **no rebound** | pins |
| `light_drop` | 0.50, 0.00, 0.75, 0.00 | map pins and small markers falling | terrain |
| `unfold_rigid` | 0.65, 0.00, 0.35, 1.00 | hinged/rigid props (measuring bridge, scale bar) | organic things |
| `draw_on` | 0.30, 0.00, 0.10, 1.00 | arrows, scanlines, acquisition lines, corridor trace | camera |
| `orbit` | 0.25, 0.10, 0.75, 0.90 | satellite passes (near-constant speed, gentle ends) | anything with impact |
| `terrain_wave` | 0.40, 0.00, 0.60, 1.00 | change propagating through ground or across a map | text |
| `text_rise` | 0.20, 0.80, 0.20, 1.00 | titles rising out of a baseline mask | objects |
| `fade_soft` | 0.40, 0.00, 0.60, 1.00 | dissolves, light changes, haze | — |

Rules: overshoot only for light elastic objects (map pins: `damped(t, 3.2 Hz, ζ 0.32)`); heavy objects never bounce. One dominant motion at a time; follow fast action with a calm hold.

## 2. Secondary motion and physics
- `damped(t, freq, zeta)` — follow-through for canopy after a trunk lands (≈2–3 Hz, ζ 0.3–0.4).
- `gust(t, events, base)` — wind load: list of (start, peak, attack, release) + slow fBm turbulence; add a short **lull** before the main hit (anticipation).
- Propagation delays: canopy clusters read the wind at `t − (0.05 + 0.22·x/width)` (windward side first); trunk reads a lagged average (inertia).
- Debris order: clods at snap (+0.08 s), leaves on gusts, dust rises late and drifts slowly (light material).

## 3. Articulating flat painted PNGs
- `split_tree(img)` — hue/saturation segmentation into trunk+branches, ground, and k-means canopy clusters; clusters move independently on top of a mesh-bent trunk.
- `mesh_bend(img, f(h))` — height-weighted bend for trunks and stems.
- `band_split(img, n)` + `atmos(img, k)` — clouds as 4 feathered bands drifting at different speeds (anvil shears ahead, base drags) + a blurred, hazed far layer; atmospheric perspective by distance.
- Internal lightning: glow driven by the painting's own violet strokes (mask), not a full-frame flash.

## 4. Camera language
- `Cam([(t, (x, y, zoom), ease), ...])` keyframed, motivated targets only (follow the swath, track the real storm cluster, dive along the image footprint).
- Parallax by depth: far storm 0.35, ground 1.0, foreground rain/scud 1.3–1.4.
- Transitions: scale-continuous dissolves (pull-back from swath to region), focus-pull (map defocuses as the diorama comes into focus), tilt-up continuity (ground → sky → orbit), occluder wipe (storm front rolls across into the aftermath). No whip zooms, no shakes, no white flashes.

## 5. Documentary integrity helpers
- `corridor_mask` + `spotlight` — dim/brighten real pixels only along a verified track; never paint a track.
- Push-broom reveal for EO-1: rows develop behind a 2 px scanline with a 22-row soft band; guide edges are traced from the real image footprint.
- Labels: `ILLUSTRATION / NOT TO SCALE`, "Symbolic satellite, not the EO-1 spacecraft", "Illustration, not the observed storm cell", and a source credit on every documentary frame.

## 6. Sound presets (local synthesis, rights-free)
`snd_wind(gust_curve)`, `snd_creak`, `snd_snap`, `snd_thud`, `snd_debris`, `snd_scan`, `snd_bed`, `snd_pressure`, `snd_thunder(dist)`, `snd_settle`, `snd_air(up/down)`.
Mix rules: beds −30 dB low-passed (background perspective); wind leads the visual reaction; thunder delayed after the flash by distance; every transition uses a different filtered air move; SFX ducked ~8 dB under narration; loudnorm −16 LUFS, TP −1.5 dB.
