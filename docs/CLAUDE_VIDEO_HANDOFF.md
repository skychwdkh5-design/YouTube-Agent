# Orbital Atlas: writer/director -> Claude assembly handoff
Owner instruction, 2026-11-01: proposed operating model is ChatGPT prepares complete second-by-second script and visual plan in the correct GitHub repository; Claude assembles the episode in the agreed style. New style remains provisional until owner reviews the action pilot.
Scope: YouTube-Agent / Orbital Atlas only. Do not change NEXORA.
Current 15s action pilot is an original schematic illustration, NOT scientific reconstruction or documentary evidence. Narration describes the staged scene only. Stylized generic rover, simplified physical motion and illustrative yellow crystals; not accurate Curiosity geometry/mineral morphology. No claims about historical mission timing or chemical composition.

## Complete per-episode package
Use productions/<confirmed-episode-id>/handoff/ and link it from the episode README.
- README.md: episode/ref/head, build command, status, approved style, unresolved blockers.
- script.md: complete English narration with beat IDs, source IDs for factual claims, pronunciation and delivery.
- storyboard.csv: one row for every second; include continuation rows for longer actions; subdivide whenever a shorter event matters.
- motion_spec.json: exact actor/prop layers, start/end state, position/scale/rotation, motion paths, easing, masks, face states, camera, enter/exit, transitions, sound, illustration flags and timing anchors.
- assets.json: exact local/repo path or cleared source URL, licence/credit, dimensions, crop, intended beat, original vs generated vs documentary, any scientific limitations.
- audio_cues.csv: voice beat IDs/word anchors, sound/music files and rights, cue timing, mix/ducking.
- acceptance.md: content/rights/visual/audio/mobile-readability checks plus explicit expected scene actions.
- Editable motion source and dependencies/versioned build instructions.

## Division of work
ChatGPT researches and prepares the concrete package. Claude checks available assets and instructions, assembles the authored actions, generates/aligns approved narration, renders, inspects playback and reports deviations. Claude must not replace specified scene action with a zoomed still, silently rewrite factual meaning or invent missing evidence. It may fix routine implementation details; report material substitutions and their reasons.
Do not assume package upload activates CI or updates main. Existing publishing approval and cost limits stay in force. Full script is timed approximately before final voice: align to actual voice/word timings, then update storyboard and motion spec together.

## New visual acceptance
- Objects visibly act even with camera motion disabled.
- Semantic beats have an actor/object, action and visible consequence.
- Rewind traverses previous scene states, not just rewind triangles on a static picture.
- Reactions/props add readable meaning; characters are used only where useful.
- Camera follows story action; no slide-like heading sequence or single-still zoom montage.
- Exact scientific/territorial geometry needs verified inputs. Label illustrative reconstructions.
- Confirm style with 15s action test; later build a representative 45–60s narrated pilot before full episode.

## Action pilot v3 — second-by-second direction
Working English voice is locally synthesized Flite SLT, NOT Adam. Timing windows are authored; no forced-alignment claim.
| Second | Action / composition | Voice / sound |
|---|---|---|
| 0–1 | Wide layered desert; rover enters, wheels spin, suspension and mast separate from background | One wheel. / soft entry impact |
| 1–2 | Rover travels toward visible rock, wheel rotation follows horizontal travel | One ordinary rock. |
| 2–3 | Continue approach, maintain clear spatial relationship rover -> rock | Continue phrase, short breath |
| 3–4 | Front wheel reaches rock; chassis/wheel bump, rock begins splitting at 3.65s | Then, a surprise inside. / impact |
| 4–5 | Two rock halves separate, dust follows ballistic arcs, crystals become exposed | Continue phrase / crystal accent |
| 5–6 | Rover proceeds, arm opens; exclamation reaction appears; crystals sparkle | Finish phrase |
| 6–7 | Hold resolved state briefly so the discovery reads | Brief pause |
| 7–8 | Wait phrase, begin rewind at 7.8s | Wait. Rewind. |
| 8–9 | Actual world timeline reverses 7.7 -> 1.6s: reaction clears, halves rejoin, dust retracts, rover backs up | Rewind chirp / scan lines / three left triangles |
| 9–10 | Finish rewind at 9.5s; cut into contact close-up; replay begins from world time 2.8s | Watch the wheel. |
| 10–11 | Slow contact replay, independent wheel and chassis motion | Continue phrase |
| 11–12 | Rock split repeats more slowly in close-up; dust and exposed interior readable | The rock breaks. / impact |
| 12–13 | Finish replay; transition toward crystal macro at 12.8s | Finish phrase; detail accent |
| 13–14 | Crystal detail fills frame; leader draws toward exposed interior | The hidden detail appears. |
| 14–15 | Resolve on crystals, restrained label; sound tail finishes | Continue phrase |

## Reproduce pilot
Put render_action_v3.py in a writable directory; install Pillow and numpy; FFmpeg must have libx264, AAC and the Flite filter. Run python render_action_v3.py. It authors all illustration geometry and audio locally and writes OA_action_v3_15s.mp4 (1280x720, 30fps, 15s). No downloaded art, paid calls or scientific source footage. It writes intermediate voice/audio files alongside the script. Fonts: DejaVu Sans Bold system path in source. Camera/render/voice implementation here is an editable reference, not a production renderer integration.
