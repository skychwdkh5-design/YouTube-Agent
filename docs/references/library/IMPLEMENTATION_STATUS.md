# Visual engine v2: audit, what was built, what is not (2026-10-14)

## Existing capabilities reused (not rewritten)
yt-render (timeline v3 long/short, Ken Burns stills, crossfade, burned captions, credits) and yt-qc (freeze, loudness, composition rules); yt-geo stacks and `watermask`; yt-satellite/`landsat_color` (calibrated mosaics); yt-captions (SRT/VTT from provider words); yt-voice (paid ElevenLabs, untouched); `orbitalatlas/` camera, layers, transitions, geo, qa, timing (`Cues.from_words`); storyboard generator `tools/autopilot/storyboard.py` (geo scenes, hints); registry/effects/guard.

## Gaps found
Word-timed multi-style captions existed only as Dubai episode code; no narration -> event planner; no shared kinetic typography beyond per-glyph reveal; no 2.5D, count-up, duplicate/impact type; no arrow with head and label, no mask-based region highlight; no evidence/presentation grade separation; no camera presets; no flash/light-wipe transitions; no free way to test sync; references not recorded.

## Built (all in `orbitalatlas/`, offline tests in `tests/test_visual_v2.py` and `tests/test_refs.py`)
`kinetic`, `captions`, `semantic`, `fx`, `regions`, `grade`, `camera_presets`, `transitions.FlashDip/LightWipe`, `sequence.Program` (+ overlay QA), `testvoice`, `refs`, `demo/visual_v2.py`, `demo/verify_sync.py`; reference library (`VISUAL_REF_001/002`, 28 effect records, style guide); registry entries; effects catalogue entries.

## Not built / limits (do not claim)
- The storyboard generator (`tools/autopilot/storyboard.py`) does not yet translate `semantic.plan` events into timeline v3 layers: the v2 engine renders through its own `Sequence`/`Program` (as EP001 did with sequences) and the result can be placed in a timeline as a video asset. yt-render burn-in captions are unchanged (single style).
- Camera class A only (image-space zooms): no 3D globe/terrain flyover, no map-plane tilt.
- Flag textures and cloth, outline-only type, full-frame colour cards, timecode counter, noise glitch, ring loader: not built (see effect status).
- Gazetteer must be supplied by the episode (stack pins/views); no geocoding; semantic rules are English and rule-based (no NLP model).
- Test voice is robotic flite with per-word synthesis; final narration needs provider timestamps (ElevenLabs `with-timestamps`) and the Adam voice. Sync of captions to a real voice is proven only by the same mechanism, not yet on that audio.
- Caption sync check is coarse (+-4 frames upper bound); audio onset check works on pauses only.
- Region masks are display shapes (seeded smooth-dark areas), not measurements; arrows are presentation curves.
- Performance: demo 18.7 s at 1080p = about 3.5 min on 4 cores; 960x540 is about 4x faster.
- Shorts (vertical) layout paths exist (`WordCaptions` portrait positions) but were not rendered or reviewed.
