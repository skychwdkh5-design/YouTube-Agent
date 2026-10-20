# AUTONOMY_HANDOFF (updated 2026-10-20)

Goal: "Создай новый ролик" runs topic -> research -> fact check -> evidence -> script -> storyboard -> media -> QC -> release package; the owner only approves the result and paid steps.
Branch: `ep005/neom-research` (never main). Read `docs/ENVIRONMENT.md` first.

## Built and tested (this session)
| Piece | Where | Tests |
|---|---|---|
| Orchestrator (state machine, resume, dry-run, hashes, paid/heavy gates, release package) | `.claude/skills/yt-orchestrate/` | 15 end-to-end tests on EP005 (`test_orchestrate.py`): pipeline to the paid gate, idempotent rerun, state.json, hard-crash resume, changed-output detection, edited-script partial rerun, single-stage force, dry-run, claim blocks, paid blocks, max_chars, voice->captions->retimed storyboard->render gate (voice stubbed, no cost) |
| yt-facts (claims gate for script and on-screen text) | `.claude/skills/yt-facts/` | 13 unit tests |
| yt-sentinel (Sentinel-2 10 m search, same-orbit pick, UTM stack, provenance, NDWI) | `.claude/skills/yt-sentinel/` | 9 offline tests + live test (`YT_SENTINEL_LIVE=1`, passed) |
| yt-topic (collect, imagery check, transparent score) | `.claude/skills/yt-topic/` | 13 unit tests on saved EP005 data; live `collect` verified |
| yt-storyboard (script + visual vocabulary -> timeline v3 long + labels + report) | `.claude/skills/yt-storyboard/` | 9 unit tests; used by the orchestrator tests |
| EP005 as the reference production | `productions/neom-line/` | runs end to end with real Sentinel-2 imagery |

## Autonomous now
Everything up to the voice gate for an episode that has `episode.json`, `claims.json`, `script.md`, `graphics_spec.json` (evidence, graphics, fact lint, storyboard, renderer plan, release package are fully automatic). Resume is automatic.
After approval: voice -> captions -> storyboard retime -> render -> QC run by the same command (voice->captions->retime->render plan verified with a stub; the real paid call and the full render are NOT exercised yet).

## Still manual (agent judgement, by design)
1. Topic ratings (us/se/no/dk/intl/visual/curiosity/evidence/monetization with rationale) and candidate collection queries.
2. Research and `claims.json` (sources are read by the agent; primaries are unreachable here).
3. Writing `script.md`, `episode.json` visual vocabulary and `graphics_spec.json`.
4. Review that each frame supports its caption (no tool checks meaning), and the owner's approvals: voice, render, publish.

## Problems found
- Primary sources (Reuters, Bloomberg, WSJ, CNBC, Semafor, neom.com, pif.gov.sa, Wikipedia) blocked -> every media claim is "reported", medium/low confidence.
- EP005's script is 4:30 (660 words), below the 6-9 minute target; the storyboard warns. Adding real content (Landsat cross-check chapter, how shadows were excluded) would fix it; padding is refused.
- One 8.2 s static hold flagged by the renderer's pacing check in the `segment` chapter.
- yt-topic demand uses first-page channel medians (rounded), relative ages; exact dates and CTR are not available. OrbitalAtlas has no Analytics input yet.
- Caught by tests and fixed: tag tokens counted as spoken words, missing output folders, renderer refusing unknown asset keys, graphic stretched to fill a chapter, tile edge not covering the AOI (now falls back to the next scene and records it).
- Full render and the real ElevenLabs call have never been run in the new chain: first real run should be watched.

## Owner actions for full autonomy
1. Network: allow reuters.com, bloomberg.com, wsj.com, cnbc.com, semafor.com, neom.com, pif.gov.sa, en.wikipedia.org (and, optionally, dataspace.copernicus.eu) in the environment's Allowed domains.
2. Provide YouTube Analytics exports (CSV) into `docs/analytics/` or API access, so yt-topic and yt-retention can use real CTR/retention.
3. Decide EP005: approve voice (`productions/neom-line/approvals/voice.json` with the printed script hash) after the script is lengthened or accepted at 4:30.
4. Standing approval policy for paid steps (e.g. max characters per episode) so the agent can request fewer confirmations.

## Next engineering steps
1. A claim/frame reviewer pass (contact sheet per chapter with claim ids) in yt-qc.
2. Auto-draft `episode.json` visuals from the evidence manifest and chapter list.
3. Optional: a Landsat fallback in `yt-sentinel` when Sentinel-2 has no coverage; thumbnail generator from the evidence stack.
4. Exercise the paid and render stages once, supervised.
