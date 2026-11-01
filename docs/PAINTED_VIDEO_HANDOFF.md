# Orbital Atlas — per-second production handoff
Read docs/ORBITAL_ATLAS_VISUAL_STYLE.md first. Owner-selected style 3 applies to every newly created illustrative object/character/prop in future Orbital Atlas videos.
ChatGPT prepares the package; Claude assembles, aligns audio, renders and verifies it.

## Episode folder
Use productions/<confirmed-episode-id>/handoff/ and link from episode README.
1. script.md — full English narration, beat IDs, factual source IDs, pronunciation/delivery; no unsupported claims.
2. storyboard.csv — one row per second, with shorter subevents when necessary. Fields: time_in, time_out, beat_id, narration, source_id, actor/prop, action, visual_consequence, composition, camera, transition, sound, captions/credit, illustration_flag.
3. motion_spec.json — all layer IDs, asset paths, start/end transforms, paths, easing, masks, reactions, layering, focus hierarchy, entry/exit, camera state and audio/word anchors. Rewind must evaluate previous scene states, not just add triangles to a still.
4. assets.json — local/repo paths or cleared source URLs, licences/credits, provenance, dimensions, crop, generated-vs-documentary status and scientific/geographic limits. New generated props must match selected painted reference; retain generation prompts.
5. audio_cues.csv — voice beat/word anchors, sound files/rights, cue and mix/ducking timings.
6. acceptance.md — expected actions, factual/rights/readability/audio checks and build command.
7. Editable source and pinned dependencies sufficient for Claude to reproduce the edit without redesigning it.

## Assembly and review
Verify assets and package; report material substitutions before silently replacing narrative action with still zooms or altering factual meaning.
Temporary timings are approximate until final voice exists. Align all dependent assets/captions/graphics to actual final voice and update package together.
Each beat must do narrative work. Preserve one coherent spatial/compositional language, one dominant focal cue, staged object action and purposeful transitions. Selective highlights explain verified features; do not fabricate boundaries/numbers.
Inspect temporal sequences and full-speed playback as well as frames. Run existing technical/factual/rights/caption/voice checks. Keep the approved-art direction distinct from approval of a particular episode.
For the first full episode with this approach, build a representative 45–60s narrated pilot before extending across the full edit.
Existing publication approval, cost limits and release queues stay in force. No publishing consent is implied by style selection.
