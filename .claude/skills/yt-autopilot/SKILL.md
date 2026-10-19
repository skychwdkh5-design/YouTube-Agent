---
name: yt-autopilot
description: Run an OrbitalAtlas episode from topic research to a render-checked MP4 and a publication package, with persistent memory of verified fixes. Use for "make EP003", "next episode", "continue the production", "what is the next step", "why did this stage fail", or after fixing any production problem (to record it). Not for one-off skills (/yt-render, /yt-voice ...) used alone.
---

# yt-autopilot

One orchestrator (`tools/autopilot/orbital.py`) over the existing skills, plus the memory protocol. Full design: `docs/AUTOPILOT.md`.

## Start of every session (30 seconds)
1. `git fetch origin '+refs/heads/*:refs/remotes/origin/*'` - the history of EP001/EP002 is on side branches.
2. `python3 tools/autopilot/orbital.py preflight` - tools, credentials present (never shown), not on main, registry valid.
3. `python3 tools/autopilot/orbital.py status SLUG` then do exactly what `next` says.

## Loop
- `kind: auto` stage -> `orbital.py run SLUG` (it retries only transient failures, at most twice, and diagnoses every failure against the registry).
- `kind: agent` stage -> do the creative work with the named skill, then `orbital.py complete SLUG STAGE` (the gate must pass).
- A gate failure or error: `python3 tools/memory/kb.py diagnose LOG` and `kb.py search WORDS` **before** debugging. Do not rebuild a tool that exists.
- Paid TTS: `orbital.py approve SLUG tts --max-chars N --quote "<owner's words>"` only after the owner said yes in chat, then `orbital.py run SLUG --stage tts --confirm`. Never call `voice.py --confirm` directly (the guard hook blocks it).

## Phase 2 commands
- `python3 tools/autopilot/topics.py score research/candidates.json --out research/topic_decision.json` - the tool chooses; do not ask the owner.
- `python3 tools/autopilot/storyboard.py plan SLUG` then `preview SLUG --start 0 --end 20 --confirm` - editable timeline + silent proof. Read `story/storyboard.plan.json` (`gaps`, `needs`) and LOOK at frames before reporting anything.
- `python3 tools/memory/effects.py search WORDS` before writing any effect or transition.
- `python3 tools/autopilot/archive.py create SLUG --out DIR` / `verify DIR` / `restore DIR --to NEW` for release preservation; `recover_narration.py` rebuilds paid narration from voice/cache for free.
- `python3 tools/autopilot/protected.py verify` proves the finished EP001/EP002 files are untouched.

## After every verified fix (not before it is verified)
Write one entry (fields: id, title, status, scope, area, date, problem, root_cause, fix, reuse_when, refs, verification, regression_test or no_test_reason), then
`python3 tools/memory/kb.py add ENTRY.json && python3 tools/memory/kb.py render`. Add a regression test whenever one can exist offline. Mark unproven things HYPOTHESIS.
Never store keys. Never add a second place for the same knowledge (see docs/production-knowledge/README.md).

## Hard limits
No YouTube upload (the package has `published: false`; the owner uploads). No spending beyond an approval. No edits to finished EP001/EP002 files. No commits to main.
Automatic gates give TECHNICALLY_VALID at most; VISUALLY_REVIEWED needs frames actually looked at plus a list of what was not verified; USER_APPROVED is the owner's alone.
