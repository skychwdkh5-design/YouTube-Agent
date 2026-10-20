# AUTONOMY_HANDOFF (updated 2026-10-20, round 3)

Branch `ep005/neom-research` (never main). Read `docs/ENVIRONMENT.md`, then `docs/AUTONOMY_REPORT.md` (measured autonomy per stage).

## Done and tested
- Round 2: yt-orchestrate (state machine, resume, hashes, gates), yt-topic, yt-facts, yt-sentinel, yt-storyboard.
- Round 3: **yt-research** (provenance journal, derived confidence, claims.json built from notes), **yt-script-agent** (brief + acceptance gate, honest INSUFFICIENT_FACTS), **yt-visual-planner**
  (episode.json + graphics_spec.json generated), **yt-visualcheck** (per-caption source/frame/wording audit; NEEDS_VISUAL_REVIEW is never auto-passed), orchestrator integration with
  FULLY_AUTOMATED / AGENT_REQUIRED / OWNER_REQUIRED classes, invalidation of stale downstream stages, task packets for the agent.
- EP005 regenerated from `research/notes.json` + `script.md` only: 891 words (6.1 min), 69 shots, 62 audited on-screen items, stopped at the owner's voice gate (4,987 characters, nothing paid).

## What the owner still does
Approve voice (`approvals/voice.json` with the current `script_sha256`, then `--allow-paid`), approve the full render (`approvals/render.json`, `--allow-render`), publishing, anything on main.

## What the agent still does (cannot be code)
Reading sources and writing `research/notes.json`; writing `script.md`; reviewing frames code cannot judge; rating topic candidates. Each is validated, resumable, and has a task packet.

## Open items / risks
1. Primary sources (Reuters, Bloomberg, WSJ, CNBC, Semafor, neom.com, pif.gov.sa) are blocked by the network policy -> media claims cap at medium. Owner: allow the domains.
2. Not yet exercised in the new chain: the real ElevenLabs call, the full render + QC of a whole video, topic discovery on a fresh subject end to end. First real run should be supervised.
3. The factual-capacity estimate (55 words per usable claim) is a heuristic; EP005 needed explanation, not new facts, to reach 6.1 minutes - the script is at the minimum.
4. Visual review by the agent is honest but not independent; the owner can re-review (`--reviewer owner`).
5. YouTube data: no Analytics; exact dates and first-30-seconds unavailable; YouTube page parsing may break.

## Next engineering steps
1. Run a fresh topic through `Создай новый ролик` end to end (topic -> research -> script) with the owner watching.
2. Supervised first paid voice + render run; extend qc to a per-chapter contact sheet.
3. Thumbnail generator from the evidence stack with the same claim audit.
4. Analytics import to weight yt-topic.

## EP005 controlled production (voice gate)

- Stage `voicecheck` (free, new `yt-voicecheck`) runs right after `voice`: audio readable, duration vs script words, every word timed in order, silence, loudness,
  list of risky pronunciations with timestamps. `FAIL` blocks captions/render; otherwise the result is `NEEDS_HUMAN_LISTEN` (never PASS). The storyboard is re-timed
  from the real word timings and visualcheck re-runs automatically (same run, bounded passes); the narration is never re-billed.
- `orchestrate.py render-test --slug S --seconds 30 [--run]`: first N seconds on the real timeline, a trimmed copy of the real narration and real captions into
  `render/test/`. Plan only without `--run`. Needs the narration to exist; not the full video.
- Billed character count now comes from yt-voice's own plan (EP005: 5,128), not from a local count.
- `productions/neom-line/approvals/voice.json` exists with `approved: false`. Owner approval = set it to `true`, then run the command in `voice/plan.json`.
