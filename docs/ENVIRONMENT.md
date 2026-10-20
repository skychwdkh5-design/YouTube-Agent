# ENVIRONMENT - read this first in a new session (checked 2026-10-20)

No secret is stored in this repository. Credentials come from environment variables or the egress proxy only.

## Start here
1. `git checkout ep005/neom-research` (all work is on this branch; `main` is never changed by the agent).
2. `python3 .claude/skills/yt-orchestrate/orchestrate.py status --slug neom-line` shows where EP005 is; `run` continues it. State: `productions/neom-line/state.json`.
3. EP005 at the time of writing: every stage up to visualcheck is done (claims, episode.json, graphics, storyboard and the visual-claim audit are GENERATED from `research/notes.json` + `script.md`); voice = awaiting owner approval (4,987 characters, paid); captions, render, qc wait; release package = incomplete (`release/REVIEW.md`). Measured autonomy: `docs/AUTONOMY_REPORT.md`.
4. Imagery under `productions/neom-line/evidence/` and `graphics/` is git-ignored and regenerated for free by `run` (about 1 minute, needs network).

## Stage classes (read this before acting)
FULLY_AUTOMATED = code runs it; AGENT_REQUIRED = you (Claude) do an intellectual task, the orchestrator wrote `tasks/<stage>.md` and validates the result (topic, research notes, script, visual reviews); OWNER_REQUIRED = voice and render approvals.
`python3 .claude/skills/yt-orchestrate/orchestrate.py status --slug <slug>` prints the live table. Resume after any interruption: run the same command again.

## Tools in the container
Python 3.13 (numpy, Pillow), ffmpeg/ffprobe, git. No `yt-dlp`, no rasterio/GDAL, no `gh` CLI. Skills live in `.claude/skills/yt-*`; each has `SKILL.md` and tests.

| Env var | Used by | Note |
|---|---|---|
| `USGS_M2M_USERNAME`, `USGS_M2M_TOKEN` | yt-satellite (Landsat) | present in the owner's environment; never print |
| `ELEVENLABS_API_KEY` or `YT_VOICE_AUTH=proxy` | yt-voice | paid; the proxy injects the key for api.elevenlabs.io; call only with an owner approval |
| `OA_VOICE_TOOL`, `OA_CRASH_IN`, `OA_STOP_AFTER` | tests only | never set in production |

## Network (cloud sandbox egress proxy; fix in the environment's Network access settings)
- Works: `planetarycomputer.microsoft.com` (STAC + data API: Sentinel-2 crops), `earth-search.aws.element84.com` (STAC search only), `landsatlook.usgs.gov`, USGS M2M, `www.youtube.com` and `i.ytimg.com` (public pages, no login), `api.github.com`, git over the proxy, `api.elevenlabs.io` (proxy-authenticated).
- Blocked (403): reuters, bloomberg, wsj, cnbc, semafor, neom.com, pif.gov.sa, wikipedia, OSM/Overpass, Copernicus hubs, `sentinel-cogs` S3 and blob asset hosts, NASA GIBS (timeout). Consequence: primary-source fact checking is not possible; claims stay "reported" at medium/low confidence (`docs/knowledge/ep005-neom/CLAIMS.md`).
- YouTube player/caption endpoints need a login: first-30-seconds analysis and exact publish dates are unavailable; do not try to bypass.
- The GitHub MCP connector drops now and then; plain `git push -u origin <branch>` is the reliable path. Verify with `git ls-remote origin refs/heads/<branch>`.

## API rules
- Paid or irreversible actions (ElevenLabs, full render, publishing, main) need the owner. yt-voice needs `--confirm` and `--max-chars`; the orchestrator additionally needs `approvals/voice.json` whose `script_sha256` matches the current script, plus `--allow-paid`.
- Free but heavy: yt-render of a full video (minutes of CPU) needs `approvals/render.json` and `--allow-render`.
- YouTube JSON is parsed from public pages; it can change. A failed parse is reported (`no_data`), never replaced by guesses. No CTR, retention or audience numbers exist without YouTube Analytics.
- Satellite licences: Landsat public domain (credit USGS); Sentinel-2 free, full and open (credit "Contains modified Copernicus Sentinel data <year>"). No paid maps or imagery.

## Recovery
- Interrupted run: just run again; stages marked `running` become `interrupted` and re-run, finished stages are verified by hash and skipped.
- A blocked stage prints its reason in `state.json` (`note`). Fix the cause (claims, coverage, script), do not edit the gate.
- Stale `.lock`: removed automatically if its pid is dead; otherwise delete `productions/<slug>/.lock`.
- Lost container: media is gone, text and state are on the branch; `run` rebuilds evidence and graphics.
- Heavy files (mp4, wav, large PNG stacks) stay out of Git history; only `docs/knowledge/ep005-neom/prototype/first15s_proto.mp4` (7.6 MB) was committed deliberately. Use releases or external storage for finished videos.

## Known quirks (learned the hard way)
- Path/row 173/041 Landsat cuts the NEOM site; use 174/040. A scene's cloud cover is whole-scene: look at the crop.
- yt-graphics compare panels: width <= stack height x 16/9; collisions are refused (move arrows, drop the graticule).
- yt-render: grid and assets resolve inside the timeline's folder (so `timeline.json` sits at the episode root); a wipe draws its own year labels; no unknown asset keys.
- yt-voice speaks everything except headings, [directions], list markers and bold: the orchestrator strips `{C#}`/`{L}` tags into `voice/spoken.md` before voicing.
- yt-captions refuse narration without provider word timings.
