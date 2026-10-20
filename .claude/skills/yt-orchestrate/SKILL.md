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
1. `new` (or reuse the open episode), then `run`. Read the JSON: `stages` and `next`.
2. A stage with status `needs_agent` is YOUR job: open `productions/<slug>/tasks/<stage>.md`, do it, run again.
   Agent stages: **topic** (`yt-topic`: collect, rate with rationale, `candidates.json`), **research** (`claims.json`), **script** (`script.md`).
   Also write `episode.json` (assets, chapters -> visuals) and `graphics_spec.json`; the storyboard is generated from them.
3. `blocked` means a gate said no (claims, coverage, renderer plan). Fix the cause, never the gate. `waiting` = a dependency is not done.
4. `awaiting_approval` (voice, render) is the owner's decision. Show `voice/plan.json` / `render/plan.json` and `release/REVIEW.md`; ask. Do not create `approvals/*.json` yourself.
5. Never publish, never touch main, never call a paid API without both `approvals/<x>.json` (with the current `script_sha256`) and `--allow-paid` / `--allow-render`.

## Stages (order, kind, outputs)
topic (agent) -> research (agent) -> facts (yt-facts registry) -> evidence (yt-sentinel, free) -> visuals (yt-graphics; before the
storyboard because the renderer plan needs the PNGs) -> script (agent + yt-facts lint) -> storyboard (yt-storyboard + label lint +
renderer plan) -> voice (PAID, gated) -> captions -> render (heavy, gated) -> qc -> release (`release/REVIEW.md`, always regenerated).

## State and recovery (`productions/<slug>/state.json`)
Per stage: status, input and output sha256, attempts, note, error. Atomic writes. A stage is skipped only if its status is done,
its inputs are unchanged and every output still has its recorded hash. A run killed mid-stage is marked `interrupted` and re-run.
Editing `script.md` re-runs only script, storyboard and later stages. `--force` re-runs one stage (first pass only).
A lock file prevents two runs. Costs are recorded in `costs[]`; a regenerated narration is never re-billed (it is reused).

## Not covered
Publishing; analytics-driven topic choice (no Analytics data); matching claims to pictures by meaning (a human review of
`release/REVIEW.md` and the frames is still required).
