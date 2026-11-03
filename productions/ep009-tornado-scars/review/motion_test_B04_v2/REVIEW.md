# EP009 B04 motion test v2 — review (2026-11-03)

**MOTION TEST ONLY.** No voice, not the pilot, no full EP009 change, nothing published.
Owner decision after test 1 (score 4/10): no tree on the satellite map; separate stylised 2.5D
scene; P03 as a multi-layer animated asset.

Files: `B04_v2_5s.mp4` (test), `B04_test1_vs_test2.mp4` (comparison), `B04_v2_contact_sheet.jpg`,
`B04_v2_key_frames.jpg`, `B04_v2_motion_chart.png`, `qc_report_v2.json`, `layers_preview.jpg`.
MP4s and the generated `layers/` folder are git-ignored; rebuild:
```
python3 productions/ep009-tornado-scars/tools/verify_illustrated_assets.py
python3 productions/ep009-tornado-scars/review/motion_test_B04_v2/cut_layers.py
python3 productions/ep009-tornado-scars/review/motion_test_B04_v2/build_b04_v2.py
python3 productions/ep009-tornado-scars/review/motion_test_B04_v2/qc_b04_v2.py
```

## What was built

No new artwork was generated. All pixels come from the verified EP009 paintings:

| Layer | Source | How |
|---|---|---|
| Bark (trunk + branches) | P03 intact | hue split bark/leaves (43°) |
| 8 foliage clumps + inner canopy shade | P03 intact | spatial clustering of leaf pixels; gaps behind moving clumps filled with the painting's own leaf colour, darkened |
| Grass mound (stays on the ground) | P03 intact | grass pixels below the trunk |
| Root plate | P03 uprooted | root ball cut out, re-oriented under the intact trunk; hidden under the ground until it lifts |
| Ground | P04 grass | flowers/stones removed by transplanting grass from the same painting; projected on a real ground plane with aerial haze |
| Bushes, far trees, storm | P04, P03, P02 | cutouts, hazed by distance |
| Leaves | P03 crown edge | 28 painted crops used as particles |

Camera: a pinhole camera over the ground plane (pan + dolly). Every layer moves by its depth:
sky barely, far trees a little, tree more, foreground bushes most. The tree is never enlarged above
its working resolution (max scale 0.985).

## Requirements vs result

| Requirement | Result | Evidence |
|---|---|---|
| Roots/base tied to the ground | Yes. Grass mound stays; root plate rises out of the soil on the windward side, soil pit opens, contact shadow follows | key frames 1.5–3.3 s |
| Trunk, branches, crown with different inertia | Partly. Crown trails the trunk in the fall (−0.5…−1.0° measured on pixels, up to 32 px at the crown) and overshoots on impact; 8 clumps sway with different frequencies. **Branches do not move individually** (see limits) | qc_report_v2.json, chart |
| Wind builds gradually | Yes, 0–1 s ramp, gusts travelling left→right, bushes and far trees sway | chart |
| Fall about a physical pivot | Yes. Lee edge of the root plate; `topple` curve (inverted pendulum), 14° → 63° in 1.5 s | chart |
| Tree stays down | Yes. Comes to rest on its crown at 63–64°; never rises (min after impact 63.0°) | frame log |
| Secondary motion on impact | Partly. Crown whip + compression, clump overshoot, 46 leaves burst, bushes recoil, dust. **Grass itself does not react** | video 3.5–5 s |
| No visible swap of drawings | Yes. One painting throughout; no dissolve between states | energy peak/median at impact 1.08 |
| Camera shows depth, not zoom | Yes, real parallax from a moving camera | contact sheet |

Technical QC: all 10 checks pass (format, no black/frozen frames, stays down, no upscaling, crown lag
and overshoot measured on pixels, no single-frame pop).

## Limitations — stated plainly

1. **The fallen crown is still the upright crown, rotated.** It is pressed flat where it meets the
   ground, but it keeps its round "standing tree" silhouette; nothing breaks. This is the most
   visible weakness.
2. **No branch-level animation.** The bark is one flat layer bent by a smooth field; individual
   limbs cannot flex, and branches hidden behind leaves do not exist in the painting.
   - Missing compositor function: **skeletal (bone) mesh deformation** of painted layers — a
     triangle-mesh warp driven by a branch hierarchy. Not present in tools/motion; could be written
     in NumPy (several days, untested risk) or done in a free tool with 2D rigging (Blender with
     armatures on image planes, free; Spine/Live2D are paid).
   - Missing asset (the real fix): P03 **painted as separate pieces** — root plate, trunk, 4–6
     main limbs each with its own foliage, a broken-limb/fallen-crown state, loose grass cards.
     Cutting a flat painting cannot recover what is hidden behind leaves.
3. **Grass does not move.** The ground is a painted texture on a plane. Wind and impact act on
   bushes and leaves only. Needs painted grass-tuft cards (asset) or a grass layer in the rig.
4. **Scene is assembled from other props** (P04 land block, P02 storm). The approved style is
   kept, but far trees repeat, the sky is a gradient, and the storm with a funnel is an
   illustrative choice — an editor should confirm it is wanted in B04.
5. **Render cost:** 1.4 s per frame, ~7 s on motion-blurred frames; this 5 s test took 4.2 min on
   2 cores. A 56 s pilot made like this ≈ 45–50 min. Acceptable for a pilot; heavy if every shot of
   a full episode is this complex.
6. Judged from frame sequences, pixel measurements and the chart; full-speed viewing by the owner
   decides.

## Verdict

Clearly better than test 1 in staging and physics (ground, roots, pivot, no swap, parallax, stays
down). It does not yet reach "natural tree" quality because the crown and branches cannot deform
like a real tree: that needs the layered P03 asset and, for limbs, bone-based deformation.
