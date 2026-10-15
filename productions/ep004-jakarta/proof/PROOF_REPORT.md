# EP004 S3 "Radar Reveals Ground Motion" - PROOF report (2026-10-15)

PROOF_STATUS: **PROOF_READY** - TECHNICALLY_VALID, frames reviewed, rubric mean 1.56 (< 2.0 pass line) -> **not** called VISUALLY_REVIEWED-pass; USER_APPROVED: NO.
Authorised: PROOF_BUILD yes; FULL_PRODUCTION no; PAID no. Paid credits used: 0. No narration, no TTS.

## Deliverable
`ep004_s3_proof.mp4` - 13.5 s, 1920x1080, 30 fps, H.264 + AAC, 1.79 MB, sha256 `5d38f15c877c0b979f1ef7cc1712cbceb84612d5df232c1fc911df3282d0687e`.
Copies: `media/ep004-s3-proof` branch (with checksums) and delivered to the owner's iPad via the session. Review frames: `proof/review_frames/`.
Content: 0-12 s original radar-geometry illustration (ILLUSTRATION chips throughout) -> 0.5 s flash dip -> 2 s "EVIDENCE MAP PENDING" placeholder (no data, no colour scale, no ESA frame, no licensed material).
Sources used in the picture: none (all drawn from code). Sound: orbitalatlas synthesised CC0 cues, effects only.

## Owner decisions applied
- ESA: only an explicitly CC BY-SA 3.0 IGO item may be used (2024 map); not in the proof; 2019 map excluded, no permission awaited. Conditions and a safer path (original map from CC BY 4.0 data) in `research/licence_audit.md`.
- RSASE 2026 recorded as **ABSTRACT_VERIFIED** (not FULL_TEXT_VERIFIED), `verified_by` = owner (the container cannot read the abstract hosts); the "-180 -> -70 mm/yr" number is blocked (extent/period unknown); no uplift location is invented; it feeds Seq. F as words only.

## New reusable components (`orbitalatlas/illustrate.py`, tests `orbitalatlas/tests/test_illustrate.py`, catalogued in `knowledge/effects.json`)
| component | what | tests |
|---|---|---|
| `los_change`, `incidence_deg` | exact share of a ground drop seen along a radar line of sight (range change, projection, foot point) | 6 |
| `dashed`, `arc_points`, `arrow`, `satellite`, `bowl_surface`, `wave` | drawing primitives on a 2x canvas | 3 |
| `Diagram` | time-parametrised picture with the `Scene` face -> works in `sequence.Shot`, transitions, `render_video` | via sequence test |
| `RadarGeometryDiagram` | the S3 diagram: pulses/echoes, sinking bowl, phase panel, LOS vs vertical, sharp camera push (2x crop), kinetic captions with emphasis, title-safe/phone-size rules built in | 11 |
| `EvidencePending` | honest placeholder (no data) | 2 |
Reuse for later episodes: any "how do we measure this" scene (altimetry, GNSS, gravimetry) can subclass `Diagram` and reuse `los_change`/primitives. Existing episodes untouched: orbitalatlas 182 tests pass, protected EP001-EP003 files verified identical.
Performance: 112 s / 405 frames on 4 workers (~8.3 s wall per video second); stills ~1 s each.

## What genuinely works / approximations / deficiencies
Works: geometry is computed and consistent; clear cause-and-effect order; phone-size rules met (0 mobile issues); no freezes/black frames; yt-qc PASS; honest labelling.
Approximations: 2-D side view; phase panel scale illustrative; satellite/orbit schematic; sink bowl is a Gaussian, not a model; amber/cyan assignment is a convention.
Deficiencies (see qa/editorial_review.md): flat look vs references; one camera move and one transition; weak first second; labels 6.5 pt in portrait-inline; captions timed by hand, not by narration; vertical-estimate caveat (needs 2nd geometry/GNSS/model) absent.
Missing visual capabilities for the full episode: 2.5D layered cross-section (S4 - the same module can host it, not yet built), `SplitFrame`, globe -> country driver (S2), georeferenced measured map layer (needs a cleared dataset), number/impact cards wired to narration (director), music bed.

## Technical decision record
1. A standalone `Diagram` class instead of a `layers.Scene` overlay: radar geometry is not an image-space annotation; the `Scene` face keeps it compatible with Sequence/transitions.
2. Draw at 2x and crop for the camera push: no upscaling blur up to 2x zoom.
3. HUD panel in screen space, scene in world space: the panel fades before the push so labels never ride on a moving map.
4. Illustration and evidence never share a frame; cut by flash dip (style-guide: change of footage type).
5. Captions at the 48 px caption floor; labels 34 px; margins from mobile_qa (3.5 % / 4 %).
6. No ESA frame in the proof: owner rule + licence analysis; placeholder instead.
7. Audio: effects only, +8 dB proof gain so it is audible on an iPad; final mix rules unchanged.

## Next stage (needs the owner's go; nothing below has started)
1. Owner reviews the proof on the iPad -> approve / change list. 2. If approved: PREVIEW_READY work - finalise script with claims (RSASE full text if obtainable), build S4 cross-section + S2 globe driver + SplitFrame, storyboard S1-S10 into `timeline.json`, silent/temporary-audio preview, thumbnails, visual-activity + attention-risk reports, TTS character count and credit estimate. 3. Free unblockers I can use at once if you allow hosts: `cdn.ncbi.nlm.nih.gov` and `zenodo.org` (CC BY 4.0 measured map for S1/S5/S9), `scholar.undip.ac.id` / `researchoutput.ncku.edu.tw` (read the abstract myself). 4. Still wanted: EP001-EP003 Studio export.
