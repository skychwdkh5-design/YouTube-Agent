# EP002 transition design: "Earth descent -> spotlight hand-off -> NASA still" (proof, 5 s, 1280x720, 24 fps)
Motivated editorial transition, not a fake continuous flight. Story function: from "somewhere on Earth" to "this exact place, as seen by NASA in 2006".
| t (s) | camera / layers | note |
|---|---|---|
| 0.0-2.3 | real CesiumJS perspective camera, 9,000 km -> 41 km, pitch -58 -> -90, heading 6 -> 16.5 deg (smootherstep). Layers: Blue Marble + Landsat WELD (sea keyed out), chip "NASA GIBS ... 3D GLOBE VIEW" | only genuine 3D part; heading chosen so the Dubai coast leans like the ASTER frame |
| 2.0-2.9 | GeoFocus phase 1: frozen Cesium frame pushes 1.2x toward the Palm, outside dims 70 %, spotlight closes on screen point (0.38, 0.73) | focus point is a screen position, no registration claim |
| 2.9-3.8 | phase 2: ASTER 2006 crop opens from the same point (1.2x settle), spotlight widens to full frame | scale/position matched by eye to the Palm |
| 3.7-5.0 | ASTER slow push <= 1.12x about the Palm; ring ping 3.65 s; label PALM JUMEIRAH 3.85 s; chip "ASTER / TERRA 2006 ... NOT GEOREGISTERED" | no map lines on the photo |
Why better than the failed tilted-photo preview: no warped card or black background; the only real 3D motion is the Cesium descent; the cut between sources is hidden by a focus device already catalogued (VE-18/19); geographic honesty chips on both layers; max zoom 1.2x per phase.
Known weaknesses: Cesium close frames are ~38 m/px and soft, WELD year unverified, Palm not present in the Cesium layer (the ASTER image shows what the Cesium layer does not), residual speckle in the sea, ASTER frame is a still with a slow push only.
Run: `node tools/cesium_proof/run_frames.js ...` (3 workers) then `python3 productions/dubai/motion/transition_proof/build_transition.py CESIUM_FRAMES OUT` then ffmpeg encode.

## V2 revision (user verdict on V1: NEEDS REVISION)
- Continuity: Cesium frames are tone-matched to the ASTER crop (mean/std transfer, up to 65 %, ramped 1.2-2.2 s; render only, ASTER pixels never graded), sharpened then softened as the spotlight closes; ASTER arrives with a rack focus (3.5 px blur -> 0 over 2.7-3.8 s); the same film grain on both sources.
- Focal point: steady ring around the Palm crown (radius 80 px x zoom), two pings, leader-line label PALM JUMEIRAH, persistent soft spotlight (outside dimmed up to 50 %, UI layer).
- Final 1.5 s: Palm drifts from (0.38, 0.73) to the third (0.40, 0.52) while the push goes to 1.30x total; no tilt, no parallax, no invented depth.
- Reused the 56 cached Cesium frames (no Cesium re-render). Compose + encode ~107 s.
- Media discrepancy: the exported V1 file was 1280x720, 24 fps, 120 frames, 3,084,621 bytes (ffprobe). A 910x512, 30 fps copy seen by the user is therefore a re-encode by the delivery/preview path, not our export. V2 is 1280x720, 24 fps, 120 frames, 5,785,326 bytes, md5 prefix e4f8cc5409af; compare size/checksum with the user's download.
Remaining weaknesses: soft Cesium close frames, a smudge in the sea where the Landsat layer has a pre-Palm sediment plume, Cesium and ASTER still differ in detail level.
