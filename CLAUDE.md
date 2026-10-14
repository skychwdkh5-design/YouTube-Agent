# YouTube-Agent

Claude Code workspace for running a YouTube channel. The skills live in `.claude/skills/yt-*`.
This file is the project-level audience strategy; every yt-* skill follows it.

## Audience strategy

- **Primary market: United States.** Highest priority for topics, hooks, titles, thumbnails,
  scripts and monetization. The US score is the dominant factor in every decision.
- **Secondary markets: Sweden, Norway, Denmark.**
- **Content language: English.** Do not translate scripts into Swedish, Norwegian or Danish unless
  the user asks.

### Choosing topics

Favour stories with strong visual and curiosity pull: unusual geography, strange borders, islands
and isolated territories, satellite discoveries, dramatic landscape changes, natural disasters,
abandoned places, unusual infrastructure, extreme environments, mysteries visible from orbit,
before/after transformations, unusual human impact on landscapes.

When comparing topics, rate each on:

1. US audience potential (dominant)
2. Sweden audience potential
3. Norway audience potential
4. Denmark audience potential
5. International English-speaking potential
6. Visual strength
7. Curiosity / click potential
8. Availability of reliable evidence
9. Availability of useful satellite imagery, when relevant
10. Monetization suitability

Decision rules:

- Never reject a strong US topic because its Scandinavian relevance is low.
- When two topics have similar US potential, prefer the one with stronger international and
  Scandinavian potential.
- Scandinavian appeal means the underlying story travels - not that it mentions Sweden, Norway or
  Denmark. Never force a Scandinavian angle into a video.
- A topic with no reliable evidence loses to one with evidence, whatever its other scores.

### Writing titles, hooks and scripts

- Natural English written for a US viewer, with American hook style and pacing.
- Avoid US slang an international English speaker would not follow.
- Explain US-specific concepts in a few words when they matter (a county, a state highway, the
  lower 48, a federal agency).
- Prefer units and references both audiences get; when a US unit is used for a key number, a
  metric equivalent in passing is fine.

### Satellite research

`/yt-satellite` works worldwide - Landsat covers the whole globe. Stories in Sweden, Norway, Denmark
or anywhere else may use it when satellite evidence materially improves the story. The no-
fabrication rules in that skill apply everywhere: no scene, no satellite claim.

## Visual production standards (mandatory for every video)

Before storyboarding or rendering any video, read `docs/ORBITALATLAS_VISUAL_MASTER.md` and load
`/yt-motion-design`, `/yt-cinematic-edit` and, for any map or satellite overlay, `/yt-geographic-animation`.
Rules in short:
- Motion storyboard per scene (fields in `docs/MOTION_DESIGN_STANDARDS.md`); filename + zoom is not a storyboard.
- Check every planned effect against the "Built?" table in the Visual Master; list unsupported ones as limitations
  before rendering. Never substitute a pan/zoom for a missing effect without saying so.
- Image-space zoom is not a 3D flyover; never fake spatial continuity between unregistered images.
- Render a 12-15 s proof of the hardest sequence first; scale only after user approval.
- Use locked narration and provider word timings only; no TTS, paid API, merge to main or large media commits
  without explicit user approval.
- Report status as TECHNICALLY_VALID, VISUALLY_REVIEWED or USER_APPROVED. Only the user grants USER_APPROVED;
  do not call unapproved work cinematic or premium.
- Reference library (VISUAL_REF_001 cinematic geography, VISUAL_REF_002 kinetic typography): `docs/references/library/UNIFIED_STYLE_GUIDE.md`; before storyboarding run `python3 -m orbitalatlas.refs consult "<scene type>"`. Narration -> events: `orbitalatlas.semantic.plan` (written by `storyboard.py plan` to `story/motion_plan.json`); motion render of the automatic storyboard: `python3 -m orbitalatlas.director render SLUG OUT.mp4`; captions A-E: `orbitalatlas.captions`; satellite pixels get `neutral`/`evidence_safe` grade only (`orbitalatlas.grade`).
- Reference style and effect catalogue: `docs/references/` (read before storyboarding a geographic video). Real geography: `orbitalatlas.geo` + `tools/fetch_natural_earth.sh`; never invent coastlines or borders.
- Shared motion engine: `orbitalatlas/` (README inside). Build scenes with it instead of writing a new renderer per episode; use `orbitalatlas.qa`
  before reporting TECHNICALLY_VALID. The Dubai-specific engine in `productions/dubai/motion/engine/` is kept for EP002 only.

## Autonomous decision policy (permanent)

- **Zero budget.** Free tools, open data and assets whose licences permit monetised documentary use only. No paid APIs, subscriptions, stock footage or purchased imagery. Check `docs/ASSET_SOURCE_REGISTRY.md` first; never repeat a verified investigation.
- **Decide, do not ask.** Investigate, compare, choose and test libraries, data providers, rendering strategy and implementation details yourself. Ask the user only for credentials, permissions (network allowlist), payment, or a genuine creative decision; the user approves creative quality, not engineering steps.
- **Persist what you learn.** Every validated finding goes into `docs/ASSET_SOURCE_REGISTRY.md` (sources/licences), `docs/RENDER_BENCHMARKS.md` (measurements), `docs/RENDER_ENGINE_DECISION_MATRIX.md` (tools), `docs/KNOWN_LIMITATIONS.md` (limits/failed approaches). Mark facts VERIFIED (with URL) vs ASSUMED.
- **Quality bar.** Technical validity is not visual approval. Judge previews against the references with `docs/REFERENCE_VISUAL_QA_CHECKLIST.md`; do not lower the standard to fit a tool, and do not claim reference-level quality without evidence. Only the user grants USER_APPROVED.
- **Efficiency.** Reuse cached assets and shared components, run short diagnostics, avoid repeated network checks and redundant renders; 12-15 s proofs before scaling. Never modify EP001.

## Production knowledge base (read before every new release)

- Index: `docs/production-knowledge/README.md` (about 30 lines). Read the index first, then only the one or two documents your task needs; do not load the whole folder.
- Reuse existing components (`orbitalatlas/`, `productions/dubai/preview/`, `.claude/skills/yt-*`, `tools/cesium_proof/`) and run `python3 tools/memory/kb.py search WORDS` / `kb.py diagnose LOG` before debugging; do not repeat fixed mistakes or build a duplicate tool.
- Paid TTS: follow `docs/production-knowledge/TTS_ELEVENLABS.md` (preflight, character count, `--cache-dir`, one pass, never regenerate cached audio, no retry after an error before checking credits and the cache).
- After a verified fix add ONE entry to `knowledge/solutions.json` (`kb.py add`, then `kb.py render`; fields and tests: `.claude/skills/yt-autopilot`), tagged VERIFIED / HYPOTHESIS; keep rules (here) separate from episode facts; never document the same fix twice. Never write keys or secrets; media goes to `media/*` branches with a SHA-256 list, not to main.

## Autopilot and memory (mandatory)

- Start of a session: `git fetch origin '+refs/heads/*:refs/remotes/origin/*'` (EP001/EP002 history is on side branches; `docs/AUDIT_PHASE1.md` says what is where), then `/yt-autopilot`: `python3 tools/autopilot/orbital.py preflight` and `status SLUG`.
- One pipeline for every episode: `tools/autopilot/pipeline.json`, described in `docs/AUTOPILOT.md`. Do the next stage it names; do not invent a parallel process.
- Durable memory lives only in the repository: `knowledge/solutions.json` (verified fixes, generated view `docs/production-knowledge/SOLUTIONS.md`), CLAUDE.md (rules), `docs/production-knowledge/` (topic procedures). Container-local auto memory does not survive.
- Spending and publishing: paid TTS only through `orbital.py` after the owner's recorded approval (`approve ... --quote`); never upload to YouTube; never commit or push to main; never touch the finished EP001/EP002 files. The hook in `.claude/settings.json` enforces these as a safety net.
- Status words: TECHNICALLY_VALID (automatic gates), VISUALLY_REVIEWED (frames actually looked at, with what was not verified), USER_APPROVED (owner only).
