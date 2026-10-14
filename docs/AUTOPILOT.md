# Autopilot: from viral topic research to MP4 and publication package

`tools/autopilot/orbital.py` runs one pipeline over the existing skills. State lives in `productions/<slug>/state.json`
(per stage: completion time, hash of upstream outputs, last failure + registry diagnosis); owner approvals in
`approvals.json`; paid requests in `ledger.json`. Stages and limits: `tools/autopilot/pipeline.json`.

```
research -> claims -> script -> tts_plan -> tts (PAID) -> captions -> storyboard -> render -> qc -> review -> package
 agent       agent     agent     auto        auto         auto        agent         auto     auto   agent    agent
```

| stage | who | produces | gate (what it proves - and what it does not) |
|---|---|---|---|
| research | Claude + `topics.py` | `research/candidates.json`, `topic_decision.json` | >= 3 candidates, chosen id among them, https evidence URLs. Scores are judgement; the tool applies CLAUDE.md rules (US dominant, evidence is a hard gate, Scandinavian reach only breaks near-ties) |
| claims | Claude (+ yt-satellite) | `story/claims.json` | every used claim VERIFIED with https source and evidence type |
| script | Claude (yt-script) | `script.md`, `story/SCRIPT_LOCK.json` | sha256 of the spoken text still matches the lock |
| tts_plan | auto, free | `voice/tts_plan.json` | exact billable characters, chunks <= 1,700, blank-line cost, within the approved budget |
| tts | auto, **paid** | `voice/narration.wav`, `.voice.json` | owner approval + budget + `--confirm`; one pass, persistent cache, no auto-retry; provider word timings present; voice onset <= 1.0 s measured on the narration |
| captions | auto, free | `captions/*` | wording preserved, no overlaps, valid timestamps |
| storyboard | Claude (motion/cinematic/geo skills) | `timeline.json`, `story/storyboard.md` | timeline v3 profile long, narration + subtitles present, a storyboard exists |
| render | auto, free | `final.mp4` | file exists (yt-render validates everything else) |
| qc | auto, free | `qc/qc.json` | yt-qc PASS = **TECHNICALLY_VALID only** |
| review | Claude, then owner | `qc/review.json` | >= 12 listed reviewed frames, what could not be verified, defects. Agent maximum: VISUALLY_REVIEWED. USER_APPROVED needs the owner's quoted approval |
| package | Claude | `release/*` | chapters valid, `published=false`, title <= 100, tags <= 500 characters |

There is no publish stage and the guard hook blocks upload commands. The owner uploads.

## Autonomy built in
* **Self-diagnosis:** every failed command is matched against `knowledge/solutions.json` symptoms; matches are saved in `state.json`.
* **Bounded retries:** free stages that are `retryable` get at most 2 attempts, only for transient errors (timeouts, 5xx, connection resets), backoff 2/4/8 s. Paid and non-transient failures are never retried.
* **Staleness:** changing an upstream output marks downstream stages `stale`; a changed script after the TTS plan blocks the paid call.
* **Memory loop:** SessionStart hook prints the registry brief; after a verified fix the agent adds an entry with a regression test (`kb.py add`).
* **Guard hook** (`.claude/settings.json`): blocks direct paid TTS, pushes to main, commits on main, YouTube uploads, edits of finished EP001/EP002 deliverables, and secrets written to files.

## What still needs Claude (not automatable today)
Choosing and verifying topics against real sources, writing the script, the motion storyboard, looking at the frames, packaging
copy. The tool prepares state, checks and bookkeeping; it does not replace those steps.

## Known gaps
* The EP002 scene engine (`productions/dubai/preview`) is hand-written per scene; EP003 should use `yt-render` timeline v3 + `orbitalatlas/` + `yt-graphics`.
  Porting EP002's best parts (hook atmosphere, audits) into shared code is not done.
* `storyboard -> timeline.json` is manual. No generator from script + claims + imagery exists yet.
* Quality audits from EP002 (text bounds, contrast, static runs) are not yet part of `yt-qc`; run them from `productions/dubai/preview/`.
* No analytics: nothing has been published, so no retention evidence exists to tune the process.
