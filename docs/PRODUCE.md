# produce.py — the OrbitalAtlas factory command

```
python produce.py --topic "TOPIC" --slug my-slug --preview [--jobs 3] [--fps 30] [--budget-chars N]
```
Chain (all existing modules): research → facts → script (Claude, stops with exit 2 and names the task file) → voice (paid; only inside `--budget-chars`, single-use approval) → media search (`yt-media-research/media_cache.py`) → scene planning + motion graphics (`yt-visual-planner`, `scene_templates.py`, `motion_presets.json`) → 720p preview, chapters in parallel with a per-chapter cache (`yt-orchestrate/preview.py`) → automatic QC. Per episode: `produce.config.json` and `produce_log.json` (seconds per step, agent steps, exceptions, what the owner must do). The final master (`--allow-render`) and any publish stay behind the owner.

## Audit result (what exists, what did not)
- Installed in this environment: the `yt-*` skills (research, facts, script, voice, storyboard, visual planner, visualcheck, graphics, render, qc, media-research, satellite, sentinel, geo, ...), 20 test modules. The skills called "Graphic Design" and "Motion Graphics" are NOT installed here (not in `.claude/skills`, not in the account's synced skills, not in the skill list). The only motion knowledge on disk is the old EP002 toolkit notes (`docs/production-knowledge/MOTION_GRAPHICS.md` in the earlier shorts clone). Their job is covered by `yt-graphics` (design: cards, charts, geo, compare) and the `yt-render` layer set (camera, wipe, flip, pin, arrow, label, still, video); the parameters are now one preset file, `yt-storyboard/motion_presets.json`, and six scene templates (`scene_templates.py`). If the owner has those two skills in another account/environment, they must be synced here before they can be wired in.
- Used per stage only (no full instruction load on every run): produce.py calls scripts; the SKILL.md files are read only when an agent step is needed.

## Visual standard
Every episode: real photos/video where rights are confirmed + satellite evidence + motion graphics. Chapters without a verified real photo/video are listed in `media/exceptions.json` and in the produce summary; nothing is invented, nothing unlicensed is used. Verified items are cached (`media_cache/index.json`) and reused across episodes.

## Defaults (production mode, baseline commit 39fe499, branch `baseline-39fe499`)
- Preview: 720p / **15 fps** with caption cache, 3 parallel chapters (`--fps 30` for a 30 fps preview). Final master: 1080p / 30 fps, only with the owner's permission (`--allow-render`).
- Architecture is frozen until a full timed run exists: no new PIL/ffmpeg/process experiments.

## EP006 timed run (first full measurement)
1. Owner names the topic and a voice budget in characters (ElevenLabs spends only inside it, one approval per script).
2. `python produce.py --topic "TOPIC" --slug ep006 --preview --budget-chars N` — repeat after each agent step (research, facts, script, visual notes); each stop names the task file.
3. Measured automatically in `productions/ep006/produce_runs.json`: seconds per orchestrator stage (`started`/`finished`), per-invocation seconds, wall clock since the first run, ElevenLabs characters/credits (plan + voice cost ledger), sizes of agent artifacts. Model calls and tokens are NOT readable from the repo: copy them from the session usage panel at the end.
4. Stage time spent waiting between invocations is Claude/owner time, visible as the gap between runs in `runs[].at`.

## Checks per release vs regression
Production never calls any `test_*.py` (verified: no caller in produce.py, orchestrate.py, preview.py). Per video the gates are the fast, video-facing ones: yt-facts, yt-visualcheck, yt-voicecheck, caption/sync checks and the single-pass preview QC (decode errors, loudness, black/freeze/silence). `test_orchestrate.py` (~17 min) and the other suites run only after code changes.
