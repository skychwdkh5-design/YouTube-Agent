# AUTONOMY_HANDOFF - goal: "Сделай новый ролик" runs end to end

Goal for tomorrow: one command starts competitor analysis, topic choice, fact check, production and QC; the owner only approves the finished video and paid actions (ElevenLabs, publish).
State: 2026-10-19, after EP005 round 2. Evidence for every line below is in `docs/knowledge/ep005-neom/` and `docs/production-pipeline.md`.

## 1. Already automated (local, tested, free unless noted)
| Stage | What exists |
|---|---|
| Satellite evidence | `yt-satellite` (Landsat via USGS M2M, token in env); Sentinel-2 10 m via Planetary Computer data API (`docs/knowledge/ep005-neom/scripts/s2fetch.py`, not yet a skill) |
| Co-registration | `yt-geo` stacks on one UTM grid; hand-written `grid.json` works for Sentinel-2 |
| Graphics | `yt-graphics` (compare, geo with scale bar, charts) with provenance and collision checks |
| Script / packaging / SEO / chapters / Shorts | `yt-script`, `yt-package`, `yt-seo`, `yt-chapters`, `yt-shorts` (writing skills, human-in-the-loop) |
| Voice, captions | `yt-voice` (paid, `--confirm`, `--max-chars`), `yt-captions` (free) |
| Render and QC | `yt-render` v3 long (segments, pacing checks), `yt-qc` |
| Competitor scan | ad hoc scripts `scripts/yts.py`, `chan2.py`, `chan3.py`, `small.py`, `alt.py` (public YouTube JSON, no login); `yt-viral` ranks but needs a hand-made input file |
| Knowledge base | markdown in `docs/knowledge/<episode>/` (research log, claims ledger, decision) |

## 2. What blocks fully autonomous production
1. **No orchestrator.** Skills are separate; nothing chains topic -> research -> script -> media -> QC, and there is no state file saying where an episode is.
2. **Network policy blocks primary sources** (reuters, bloomberg, wsj, cnbc, semafor, neom.com, pif.gov.sa, wikipedia, OSM, Copernicus, Earth Search assets, NASA GIBS). Fact checking is limited to search summaries, so claims stay medium/low confidence.
3. **Competitor/topic scoring is manual.** The scripts are not a skill, are fragile (YouTube HTML/JSON can change; exact dates, first-30-seconds, captions need login and are out of reach), and the CLAUDE.md 10-criteria scoring is done by judgment each time.
4. **Sentinel-2 is not a skill.** Scene choice (same orbit, season, low nodata), cropping, NDWI/shadow checks and the false-conclusion rules were done by hand.
5. **No claims gate in code.** `claims.json` verification before TTS exists for Shorts only; long-form claims live in markdown and are not machine-checked against script text and on-screen labels.
6. **Script is not generated into a timeline.** Shots, camera moves and word anchors for long-form are written by hand; `yt-voice` is the first paid step but the script-to-storyboard step has no tool.
7. **No QC of meaning.** `yt-qc` checks the file, not whether a frame supports its caption; a visual-claim reviewer is missing.
8. **Cold sessions.** Each session re-learns environment limits (blocked hosts, token variables, tool quirks); media in `productions/` is git-ignored and lost with the container.
9. **No analytics loop.** No YouTube Analytics access, so CTR/retention cannot drive topic choice or iteration. OrbitalAtlas subscriber count is unknown to the agent.
10. **GitHub MCP drops out**; git push over the proxy works and is the reliable path.

## 3. Concrete changes needed (in order)
1. **Owner: network** - add to Allowed domains: reuters.com, bloomberg.com, wsj.com, cnbc.com, semafor.com, neom.com, pif.gov.sa, en.wikipedia.org, earth-search.aws.element84.com assets (sentinel-cogs.s3.us-west-2.amazonaws.com), dataspace.copernicus.eu. (Docs: environment.network.)
2. **Skill `yt-orchestrate`** (the "Сделай новый ролик" command): a state machine over `productions/<slug>/state.json` with stages research -> topic -> facts -> evidence -> script -> storyboard -> media -> qc -> review package; every stage idempotent, resumable, writes a log. Hard stops only at: owner approval of topic (optional), ElevenLabs `--confirm`, publish.
3. **Skill `yt-topic`**: promote `scripts/` into one tested tool: collect 10-20 candidates, compute x-median and views/sub, apply the CLAUDE.md scoring table, require an evidence check (is imagery available and visible at 10/30 m?) before ranking, output a ranked JSON + decision memo. Keep "no data -> say so".
4. **Skill `yt-sentinel`** (or extend `yt-satellite`): STAC search, same-orbit/season picker, crop to a UTM grid + provenance + licence credit, NDWI/shadow/cloud checks, auto contact sheet. Reuse `s2fetch.py`.
5. **Skill `yt-facts`**: claims.json for long-form (tier, source, date, URL, confidence); fail the build when a script sentence or on-screen label has no claim id, or a tier-2 claim lacks "reported".
6. **Skill `yt-storyboard`**: script + claims + available frames -> timeline v3 long (camera, wipes, graphics inserts, word anchors after voice), with pacing warnings fixed automatically where possible.
7. **Extend `yt-qc`**: contact sheet per chapter, frame-vs-label check (a reviewer pass that must cite the claim id), credit line presence, no unconfirmed words ("proves", "reveals", "collapsed") unless a claim allows them.
8. **Persist state**: commit text artefacts and small evidence to the episode branch automatically (extend the `.gitignore` exceptions pattern from EP001/EP005), push over git, never to main; open a draft PR only on request.
9. **Session bootstrap file** `docs/ENVIRONMENT.md`: blocked hosts, env vars needed (`USGS_M2M_*`, `ELEVENLABS` via proxy), known tool quirks, so a new session starts warm.
10. **Analytics (owner)**: export YouTube Analytics CSV per video into `docs/analytics/` (or grant API access); wire `yt-retention` output into `yt-topic` weights.
11. **Review package**: final stage writes one folder: video, thumbnail(s), title options, description, chapters, claims ledger, QC report, and the single question "approve / change / pay for voice".

## 4. Autonomy boundary (keep)
Paid actions (`yt-voice --confirm`), publishing, main branch, and any claim at confidence below medium stay with the owner. No CTR/retention forecasts without Analytics data.

## 5. Suggested plan for tomorrow
1. Owner applies step 3.1. 2. Build `yt-sentinel` + `yt-facts` (EP005 is the test case). 3. Build `yt-topic` from `scripts/`. 4. Build `yt-orchestrate` and dry-run it on EP005 up to "voice requires approval". 5. Add `yt-storyboard`/QC extensions.
