---
name: yt-orchestrate
description: >-
  Run the whole OrbitalAtlas video pipeline from one command - topic, research, fact check, satellite evidence,
  graphics, script, storyboard, voice, captions, render, QC, release package - resumable, with hard stops before
  anything paid. Use for "Создай новый ролик", "make a new video", "continue EP005", "resume production", "what
  stage is this video at".
---

# yt-orchestrate

```bash
python3 .claude/skills/yt-orchestrate/orchestrate.py new --slug my-topic          # skeleton (slug defaults to ep-YYYYMMDD)
python3 .claude/skills/yt-orchestrate/orchestrate.py run --slug neom-line         # run every stage that can run
python3 .claude/skills/yt-orchestrate/orchestrate.py run --slug neom-line --dry-run
python3 .claude/skills/yt-orchestrate/orchestrate.py run --slug neom-line --stage storyboard --force
python3 .claude/skills/yt-orchestrate/orchestrate.py status --slug neom-line
python3 .claude/skills/yt-orchestrate/test_orchestrate.py                         # 15 end-to-end tests on EP005
```

## When the owner says "Создай новый ролик"
1. `new` (or reuse the open episode), then `run`; read `stages`, `next` and `autonomy`. Run again after every agent task.
2. Stage classes - **FULLY_AUTOMATED** (code only), **AGENT_REQUIRED** (you must do an intellectual task; `tasks/<stage>.md` is written for you), **OWNER_REQUIRED** (`awaiting_approval`).
   - topic (AGENT_REQUIRED): `yt-topic collect` + ratings with rationale -> `topic/candidates.json`; or the owner's `topic/approval.json`.
   - research (AGENT_REQUIRED): read sources, log them with `yt-research`, write `research/notes.json`; claims.json is then DERIVED.
   - script (AGENT_REQUIRED): write `script.md` from `tasks/script.md` (`yt-script-agent`); the gate validates it.
   - visualcheck (AGENT_REQUIRED only for items code cannot judge): look at the frames, record honest reviews.
   - facts, evidence, visualplan, visuals, storyboard, captions, qc, release: FULLY_AUTOMATED. voice and render: OWNER_REQUIRED.
3. `blocked` = a gate said no (claims, coverage, review verdict, renderer plan): fix the cause, never the gate. `waiting` = an upstream stage is not done (a stage whose upstream stopped being done is invalidated, never trusted).
4. `awaiting_approval` (voice, render): show `voice/plan.json` / `render/plan.json` and `release/REVIEW.md`; ask. Do not create `approvals/*.json` yourself.
5. Never publish, never touch main, never call a paid API without `approvals/<x>.json` (current `script_sha256`) AND `--allow-paid` / `--allow-render`.

## Stages (order, class, outputs)
topic -> research (notes -> claims.json + report) -> facts (registry) -> evidence (yt-sentinel + NDWI series) -> script (brief + validation) -> visualplan (episode.json, graphics_spec.json) -> visuals (yt-graphics)
-> storyboard (timeline.json, labels, report; label lint) -> visualcheck (qa/) -> voice (PAID) -> captions -> render (heavy) -> qc -> release (`release/REVIEW.md` with the autonomy table).
`orchestrate.py status --slug S` prints the autonomy report: per stage nature, class now, and whether an agent artifact was involved.

## State and recovery (`productions/<slug>/state.json`)
Per stage: status, input and output sha256, attempts, note, error. Atomic writes. A stage is skipped only if its status is done,
its inputs are unchanged and every output still has its recorded hash. A run killed mid-stage is marked `interrupted` and re-run.
Editing `script.md` re-runs only script, storyboard and later stages. `--force` re-runs one stage (first pass only).
A lock file prevents two runs. Costs are recorded in `costs[]`; a regenerated narration is never re-billed (it is reused).

## Not covered
Publishing; analytics-driven topic choice (no Analytics data); matching claims to pictures by meaning (a human review of
`release/REVIEW.md` and the frames is still required).
