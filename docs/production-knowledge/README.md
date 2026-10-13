# Production knowledge base (YouTube-Agent / OrbitalAtlas)
Index for future sessions. **Read this file only, then open the one or two documents your task needs** (selective reading saves the context window). Every claim carries a tag: VERIFIED (done and checked here), ASSUMED/HYPOTHESIS (not proven), EPISODE-SPECIFIC, RULE (project rule).
| if you are about to ... | read |
|---|---|
| storyboard a video or a hook | `VISUAL_STYLE.md`, then `MOTION_GRAPHICS.md` |
| choose camera moves / cuts | `TRANSITIONS.md` |
| use satellite images, photos, maps, outlines | `SATELLITE_DATA.md` (+ `docs/ASSET_SOURCE_REGISTRY.md`) |
| buy narration | `TTS_ELEVENLABS.md` (cost gate, cache) |
| sync picture to speech, captions | `AUDIO_SYNC.md` |
| render, encode, store media | `RENDERING.md` |
| check a render before showing it | `QUALITY_CONTROL.md` |
| something broke | `TROUBLESHOOTING.md` |
| plan the process / avoid past mistakes | `LESSONS_LEARNED.md` |
Existing project docs stay authoritative for their topics: `CLAUDE.md` (rules), `docs/ORBITALATLAS_VISUAL_MASTER.md`, `docs/MOTION_DESIGN_STANDARDS.md`, `docs/TRANSITION_DESIGN_SYSTEM.md`, `docs/ASSET_SOURCE_REGISTRY.md`, `docs/KNOWN_LIMITATIONS.md`, `docs/RENDER_BENCHMARKS.md`, `docs/production-pipeline.md`.
Code to reuse (do not rebuild): `orbitalatlas/` (shared engine), `productions/dubai/preview/` (kit, scenes, scenes_v6, sync, build_final, monotony_audit, qa tools), `.claude/skills/yt-*`, `tools/cesium_proof/`.
## After every release
Add only checked solutions: one bullet in the right file with a tag and a date, a row in `TROUBLESHOOTING.md` for each new failure (symptom, cause, fix), and numbers in `RENDERING.md` / `QUALITY_CONTROL.md`. Mark anything unproven HYPOTHESIS. Never store keys, tokens or media here; media lives on `media/*` branches with a SHA-256 list.
Maintenance: keep each file under about 120 lines; if a topic grows, split it and update this index.
