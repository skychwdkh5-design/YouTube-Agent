# EP009 — owner-confirmed 3D-look painted props; Claude handoff contract
Owner confirmed on 2026-11-03 that BOTH images below match approved art direction (not merely illustrative alternatives):
- `docs/assets/visual-style/painted-props.webp` — isolated painted ship/captain/bundles of money/stopwatch reference.
- `docs/assets/visual-style/painted-reference.webp` — collage of same painted props over map/water with directional graphics.
Main authoritative instructions:
- `docs/ORBITAL_ATLAS_VISUAL_STYLE.md`
- `docs/PAINTED_VIDEO_HANDOFF.md`
- V7 editable sample: `examples/painted-collage-v7` on branch `production/dynamic-motion-style-v1`.

## Non-negotiable workflow
1. ChatGPT/preproduction prepares episode-specific props and backgrounds as **actual usable file assets** BEFORE Claude assembly, not just prompt text. Prefer layered transparent RGBA WEBP/PNG for moving foreground items, full-resolution source imagery for satellite evidence, and reusable SVG/Lottie/code geometry only when rendering is deterministic.
2. All generated props must match the two owner's confirmed references: semi-realistic hand-painted editorial look, material texture, expressive proportional figures, sculpted light and depth; coherent palette. Objects should feel dimensional within a layered 2.5D or 3D composite. **Do not substitute glossy toy-like stock 3D**, generic flat pictograms or motionless map slides. It is not a claim that assets are rigged 3D meshes.
3. Separate every genuine NASA/USGS/NOAA image/video from invented/illustrative props; add `ILLUSTRATION / NOT TO SCALE` when composited reconstructions are used. Never synthesize a satellite track and then pass it off as original imagery.
4. A `ready` asset requires an actual repository or artifact path, dimensions, provenance, license/usage constraints, an inspectable preview and SHA-256. A reference image or a prompt is **not** ready.
5. Until such assets exist, Claude may only make a small planning/QC review, not spend tokens independently generating replacements or searching for source media. Missing assets are blockers: report IDs only.
6. Claude consumes supplied assets for purposeful movement: entrance, path, overlap/obstruction, reaction, consequence, rewind where narratively useful. Real source imagery shows tornado scar; illustrated elements explain scale, effects and satellite acquisition.
7. Start with 45–60 second narrated editorial pilot reviewed by owner; only then expand to full episode. Final paid Adam voice and release need explicit owner approval.

## Proposed episode-specific props to prepare (NOT YET CREATED)
| ID | Painted layer / planned use | Required output | Scene | State |
|---|---|---|---|---|
| P01 | GOES-like observation satellite (symbolic, NOT an exact spacecraft reproduction) | transparent cutout + silhouette | 0:28–0:50 | MISSING |
| P02 | Thick cumulonimbus cloud mass, layered segments with painterly volume | independently movable transparent layers | 1:25–2:15 | MISSING |
| P03 | Painted tree canopy and uprooted trunk, schematic vegetation-change illustration | transparent segmented layers | 2:15–3:04 | MISSING |
| P04 | Land cross-section showing intact vegetation vs damaged corridor | separate illustrated terrain layers | 3:04–4:15 | MISSING |
| P05 | Painted measurement pins, scale bar, state border/locator elements | transparent layers | 3:35–4:15 | MISSING |
| P06 | Surface block/buildings, non-identifying illustrative objects (not actual victim properties) | transparent layers | 5:04–5:46 | MISSING |

## Required actual deliverables prior to calling Claude assembly
- `handoff/assets.json`: for each ID: `kind`, `path`, `source`, `rights`, `sha256`, `width`, `height`, `alpha`, `status`, `crop_limits`.
- `handoff/storyboard.csv`: one row per second, action + visual consequence (ranges alone insufficient).
- `handoff/motion_spec.json`: real asset layer paths and transforms (not prose suggestions).
- `handoff/audio_cues.csv` and `handoff/acceptance.md`.
- Genuine images/video downloaded separately, quality checked against their NASA/USGS/NOAA source pages.

No hidden purchase or automatic publication. These requirements supersede generic references to "3D overlays" in the earlier EP009 motion outline.
