# Production knowledge base (YouTube-Agent / OrbitalAtlas)
Index for future sessions. **Read this file only, then open the one or two documents your task needs** (selective reading saves the context window). Every claim carries a tag: VERIFIED (done and checked here), ASSUMED/HYPOTHESIS (not proven), EPISODE-SPECIFIC, RULE (project rule).
| if you are about to ... | read |
|---|---|
| storyboard a video or a hook | `VISUAL_STYLE.md`, then `MOTION_GRAPHICS.md` |
| render an episode with the motion engine (automatic effects) | `VISUAL_ENGINE_BASELINE.md` (status PRODUCTION_BASELINE_V2C); deferred ideas: `FUTURE_VISUAL_ROADMAP.md` |
| choose camera moves / cuts | `TRANSITIONS.md` |
| use satellite images, photos, maps, outlines | `SATELLITE_DATA.md` (+ `docs/ASSET_SOURCE_REGISTRY.md`) |
| buy narration | `TTS_ELEVENLABS.md` (cost gate, cache) |
| sync picture to speech, captions | `AUDIO_SYNC.md` |
| render, encode, store media | `RENDERING.md` |
| check a render before showing it | `QUALITY_CONTROL.md` |
| something broke | `python3 tools/memory/kb.py diagnose LOG` / `search WORDS` (registry `knowledge/solutions.json`, readable view `SOLUTIONS.md`) |
| plan the process / avoid past mistakes | `LESSONS_LEARNED.md` |
Existing project docs stay authoritative for their topics: `CLAUDE.md` (rules), `docs/ORBITALATLAS_VISUAL_MASTER.md`, `docs/MOTION_DESIGN_STANDARDS.md`, `docs/TRANSITION_DESIGN_SYSTEM.md`, `docs/ASSET_SOURCE_REGISTRY.md`, `docs/KNOWN_LIMITATIONS.md`, `docs/RENDER_BENCHMARKS.md`, `docs/production-pipeline.md`.
Code to reuse (do not rebuild): `orbitalatlas/` (shared engine), `productions/dubai/preview/` (kit, scenes, scenes_v6, sync, build_final, monotony_audit, qa tools), `.claude/skills/yt-*`, `tools/cesium_proof/`.
## Where each kind of knowledge lives (no duplicates)
- **Solved problems** (symptom, root cause, fix, reuse, reference, test): only `knowledge/solutions.json` -> `SOLUTIONS.md` (generated). `TROUBLESHOOTING.md` is a pointer.
- **Rules and procedures** for a topic: the topic files here and `CLAUDE.md`. **Numbers of one episode**: its `productions/<slug>/` folder.
- **What exists on which branch / what was lost**: `docs/AUDIT_PHASE1.md`. **Pipeline and gates**: `tools/autopilot/pipeline.json`, `docs/AUTOPILOT.md`.

## After every release
Add only checked solutions: one registry entry per new failure (`kb.py add`, then `kb.py render`), and numbers in `RENDERING.md` / `QUALITY_CONTROL.md`. Mark anything unproven HYPOTHESIS. Never store keys, tokens or media here; media lives on `media/*` branches with a SHA-256 list.
Maintenance: keep each file under about 120 lines; if a topic grows, split it and update this index.
