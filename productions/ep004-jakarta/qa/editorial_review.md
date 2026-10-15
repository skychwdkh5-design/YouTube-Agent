# EP004 S3 proof - editorial / visual review (2026-10-15)
**What was actually reviewed:** all 54 frames at 4 fps of the delivered MP4 in three contact sheets (`proof/review_frames/contact_4fps_*.jpg`), four full-resolution key frames, all 24 frames of the transition window 11.4-12.2 s (smooth grey ramp, no artefacts), plus earlier-iteration frames that drove six fixes (below). **Not reviewed:** real-time playback feel, audio by ear, a real phone. Frame review of the *final* file: 54/54 frames viewed.

## Rubric (docs/VISUAL_QUALITY_RUBRIC.md gate 2; 0-3, one line of evidence each)
| criterion | score | evidence |
|---|---|---|
| opening impact | 1 | 0-1.2 s is a sparse frame (satellite sliding in over flat ground); fine mid-episode, weak as an opener |
| production quality | 2 | clean 2x-supersampled vector look, consistent tokens, soft glows; flat, no depth cues |
| geography clarity | n/a | schematic, no place shown by design |
| camera | 2 | one 0.8 s push-in (sharp, no upscale) + slow creep; nothing like VR1's snap/scale moves |
| transitions | 2 | one flash dip hides the illustration -> placeholder cut; correct purpose, but only one |
| typography | 2 | 48 px captions with per-glyph reveal and amber emphasis words; plain DejaVu, no weight contrast, nothing like VR2 lockups |
| variety | 1 | one visual vocabulary for 12 s (line diagram); no change of footage type until the placeholder |
| density | 2 | a new element every ~0.8-1.5 s, never more than 3 labels at once |
| sync | 1 | no narration exists; captions and effects are hand-timed against estimated timings |
| engagement | 1 | explains correctly but is not yet compelling; first-frame curiosity is low |
**Mean of scored criteria = 14/9 = 1.56. The rubric's pass line is mean >= 2 with no 0: gate 2 is NOT met.** The proof is TECHNICALLY_VALID and was frame-reviewed; I do not call it VISUALLY_REVIEWED-pass, and it is not USER_APPROVED.

## Fixes made from real frame findings (all re-rendered)
1. 1st render: LOS label overlapped the building and the ground line -> building moved to the bowl's edge, label placed in the soil under the construction.
2. The satellite drifted under the top-left chips during the push-in -> satellite, orbit and label fade out before the push; HUD panel fades first.
3. Phase bracket started outside the panel -> anchored to the second crest, panel widened to 610 px so its title no longer touches the border.
4. Captions were 40 px (repo floor 48) and 2 lines would not fit -> 48 px, text shortened and split in two.
5. SENTINEL-1 label plate crossed the safe margin (found by mobile_qa) -> moved.
6. Bowl centre and measurement point were offset (pulse 2 targeted a point the ground did not reach: a geometry bug found in the review) -> bowl centred on the point; unit test added (`test_the_pulse_target_is_where_the_ground_ends_up`).
Remaining defects seen in the final frames: a dark empty caption scrim while the next caption types in (cosmetic, ~0.3 s); 0.9 s (8.4-9.4 s) with only ground + dashed lines while the camera pushes; first second nearly empty; arrowhead of the vertical arrow pops in with the first pixels of the draw-on.

## Scientific correctness (second pass)
- Extra range is computed (`los_change`), not drawn by eye: the cyan segment is the projection of the vertical drop on the line of sight; the dashed segment from the sunk point meets the line of sight at a right angle (checked in the frames and in `test_foot_lies_on_the_line_of_sight...`).
- Echo phase panel: shift is proportional to twice the range change (round trip); amplitude/wavelength are illustrative and labelled "ILLUSTRATIVE"; no number is printed. Sentinel-1 is shown as a side-looking radar (antenna along the line of sight); no incidence angle, wavelength, altitude, revisit time or rate is claimed.
- "ILLUSTRATION · NOT TO SCALE" is on screen for the whole illustration; "GROUND DROP EXAGGERATED" from the moment the ground moves; the placeholder says "NO DATA SHOWN" and contains no colour scale or map shape (unit-tested: < 2 % chromatic pixels).
- Captions: "Each echo's phase records the distance to the ground" (phase is range modulo wavelength - simplified, acceptable for the level, a fuller wording is for the final script); "Radar sees motion along its line of sight, not the straight-down drop" (correct for a single geometry). The statement that a vertical estimate needs a second geometry/model/GNSS is NOT in the proof (add to the full scene).
