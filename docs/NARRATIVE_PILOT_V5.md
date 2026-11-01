# Narrative pilot v5 — reveal, question, cause, evidence
Date: 2026-11-01. Status: rendered style experiment, owner review pending. Scope: Orbital Atlas / YouTube-Agent only.

## Purpose
Replace repeated angles on a single event with different narrative functions. Original NASA photo first creates a concrete question. Actual scene-state rewind bridges to an illustrative cause. Then the real image resolves the sequence. This is not a finished episode or approved final art direction.

## Full temporary narration (English)
Yellow crystals. On Mars.
What exposed them?
Rewind.
Curiosity drove over a rock.
And cracked it open.
Inside: elemental sulfur.
This is the actual Mastcam image.

Voice is local Flite SLT, not Adam. Timing windows are authored and temporary, not word-level forced alignment.

## Second-by-second storyboard
| Time | Narrative job | Visual action | Audio/text |
| --- | --- | --- | --- |
| 0–1 | Establish real discovery | Original NASA PIA26309 image, close crop on fractured crystalline interior | Yellow crystals. |
| 1–2 | Establish location | Hold readable real-image context, slight crop change only as support | On Mars. |
| 2–3 | Ask a concrete question | Progressive attention oval on the real fracture; it is an annotation, not a measured scientific boundary | What exposed them? |
| 3–4 | Return to cause | Cut to 3D wide state; rewind world 6.8 -> 2.3s between 3.1 and 4s. Halves rejoin, particles retract, rover backs up | Rewind. / reverse chirp |
| 4–5 | Introduce actor/action | Three-quarter tracking of generic original rover moving toward rock | Curiosity drove over a rock. |
| 5–6 | Set up contact | Cut at 5.6s to low wheel viewpoint; wheel approaches contact | Continue voice / transition sound |
| 6–7 | Show cause | Wheel contact and suspension bump, then crack begins at local world time 3.67s | And cracked it open. |
| 7–8 | Show consequence | Rock halves separate; small debris spreads; interior cluster appears | Continue phrase / impact and granular accents |
| 8–9 | Inspect result | Elevated changing view shows the exposed interior as rover departs | Breath between ideas |
| 9–10 | Name material | Short material label S / SULFUR appears over illustrative 3D detail | Inside: elemental sulfur. |
| 10–11 | Resolve illustrated explanation | Brief changing close view; do not replay action from more angles | Continue phrase |
| 11–12 | Switch to evidence | At 11.3s replace illustration with actual PIA26309 image. Image retracts into a frame | This is the actual Mastcam image. |
| 12–13 | Reveal full context | Frame settles to show uncropped full NASA photograph against dark background | Continue voice |
| 13–14 | Identify evidence | Curiosity / Mastcam / 7 JUN 2024 / PIA26309 shown beside full image | Image credit retained |
| 14–15 | Let evidence read | Hold resolved source image and metadata | Finish voice and sound tail |

3D and photo labels switch accurately at image boundaries. No claim that generic rover geometry, fracture animation, mineral shapes or sound reconstruct the actual event. Do not imply visual appearance alone established sulfur composition: source states the APXS instrument was used for composition.

## Fact/source map
All historical/scientific narration is grounded in NASA/JPL PIA26309 caption:
- Curiosity drove over/crushed rock May 30, 2024, exposing crystals.
- Mastcam image captured June 7, 2024.
- Material identified as elemental sulfur using APXS.
Source: https://science.nasa.gov/photojournal/curiosity-views-sulfur-crystals-within-a-crushed-rock/
Corroborating original JPL page: https://www.jpl.nasa.gov/images/pia26309-curiosity-views-sulfur-crystals-within-a-crushed-rock/
Credit: NASA/JPL-Caltech/MSSS.
Original color was adjusted by mission team to approximate Earth lighting. We preserve supplied image color; only crop/scale and separate annotations are used.

## Assets and reproducibility
Image: https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/pia26/pia26309/PIA26309.jpg
Dimensions: 1779×1590.
SHA-256: 8ef1e660a645e77d440670ee2360d4d9749062c4134668467aaf7642c4294c21.
JPL use policy reviewed: https://www.jpl.nasa.gov/jpl-image-use-policy/
Specific caption carries NASA/JPL-Caltech/MSSS credit and no additional restrictive notice. Keep credit; no NASA/JPL logos or endorsement claims.

Run python build.py in examples/narrative-pilot-v5/. Needs g++, Python Pillow/numpy, FFmpeg with Flite/libx264/AAC, DejaVu Sans Bold at source path. Download exact original image if missing. Original C++ geometry renderer supplies illustrative frames; Python composites genuine NASA photograph and annotations. Output OA_story_v5_15s.mp4, 1280×720, 30fps, H.264/AAC, 15 seconds. No paid service/API calls.

## Limits
Art is still a procedural 3D study, not photorealistic. Real image supports the factual claim; illustrative geometry is not evidence. Cold-open photo and end photo are intentional evidence beats, not approval of still-zoom as the main montage style. Owner has not approved the final look, publication or migration of main.
