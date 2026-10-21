# produce.py — the OrbitalAtlas factory command

```
python produce.py --topic "TOPIC" --slug my-slug --preview [--jobs 4] [--budget-chars N]
```
Chain (all existing modules): research → facts → script (Claude, stops with exit 2 and names the task file) → voice (paid; only inside `--budget-chars`, single-use approval) → media search (`yt-media-research/media_cache.py`) → scene planning + motion graphics (`yt-visual-planner`, `scene_templates.py`, `motion_presets.json`) → 720p preview, chapters in parallel with a per-chapter cache (`yt-orchestrate/preview.py`) → automatic QC. Per episode: `produce.config.json` and `produce_log.json` (seconds per step, agent steps, exceptions, what the owner must do). The final master (`--allow-render`) and any publish stay behind the owner.

## Audit result (what exists, what did not)
- Installed in this environment: the `yt-*` skills (research, facts, script, voice, storyboard, visual planner, visualcheck, graphics, render, qc, media-research, satellite, sentinel, geo, ...), 20 test modules. The skills called "Graphic Design" and "Motion Graphics" are NOT installed here (not in `.claude/skills`, not in the account's synced skills, not in the skill list). The only motion knowledge on disk is the old EP002 toolkit notes (`docs/production-knowledge/MOTION_GRAPHICS.md` in the earlier shorts clone). Their job is covered by `yt-graphics` (design: cards, charts, geo, compare) and the `yt-render` layer set (camera, wipe, flip, pin, arrow, label, still, video); the parameters are now one preset file, `yt-storyboard/motion_presets.json`, and six scene templates (`scene_templates.py`). If the owner has those two skills in another account/environment, they must be synced here before they can be wired in.
- Used per stage only (no full instruction load on every run): produce.py calls scripts; the SKILL.md files are read only when an agent step is needed.

## Visual standard
Every episode: real photos/video where rights are confirmed + satellite evidence + motion graphics. Chapters without a verified real photo/video are listed in `media/exceptions.json` and in the produce summary; nothing is invented, nothing unlicensed is used. Verified items are cached (`media_cache/index.json`) and reused across episodes.
