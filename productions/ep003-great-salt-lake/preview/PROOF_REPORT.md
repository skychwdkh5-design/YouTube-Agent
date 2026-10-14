# EP003 visual proof #1 (0-20 s, silent)

Status: **TECHNICALLY_VALID for a proof; VISUALLY_REVIEWED by the agent on frames only; not USER_APPROVED.**

- File: `proof.mp4` (1920x1080, 30 fps, 20.0 s, 15,352,043 bytes), SHA-256 `d6fa48f63cdc28c10a8893790bc1ee37aa48daf936857c75b7de5b7b4b94e125`. Not committed (media rule); regenerate with
  `python3 tools/autopilot/storyboard.py plan ep003-great-salt-lake && python3 tools/autopilot/storyboard.py preview ep003-great-salt-lake --start 0 --end 20 --confirm`.
  Rendering is deterministic, so the same inputs give the same hash (inputs: `assets/manifest.json` records each asset's sha256 and source URL).
- Made with the free local stages only: no TTS, no paid request, no upload. Timing is ESTIMATED (2.38 words/s), not provider timing.
- Renderer plan: 7 shots, 6 composition resets, 4 distinct compositions and 5 information events in the first 10 s (targets: >= 3 and >= 3).
- yt-qc `--profile long`: FAIL, and expected: `long_duration` (20 s < 60 s), `loudness` and `audio_starts` (silent). Warn: static 3.07 s (the number card).

## What I looked at
Nine frames (contact sheet `contact_sheet.jpg`, frames 20, 100, 170, 230, 300, 380, 450, 520, 590): hook stills with the NASA credit pill, the
4,209.7 ft number card with its source line, a 2023 still, the 4,211.6 FEET stat label over the 1985 still, the NASA time-lapse (1988, 1984, 1991 visible).

## Defects found by looking, and fixed
1. The number card label was cut mid-number ("...stood at 4,2") - invisible to every automatic check. Fixed (`callout_label`), regression test added, registry entry `graphic-label-cut-mid-number`.
2. Earlier planner versions showed a picture of the wrong year for a named year, and unrelated pictures for scenes without an asset. Fixed; the remaining mismatches are listed in `story/storyboard.plan.json` -> `needs`.

## Known weaknesses (not hidden)
- "July 2022" is shown with the 2023 frame (1 year off) and "1986" with the 1985 still: exact-year Landsat scenes are not acquired yet.
- Scenes 3 and 4 (callout then still) are the only graphics in 20 s; the opening relies on four stills of one subject - visually repetitive without more pictures.
- The time-lapse carries NASA's baked-in year labels; they run while the narration names other years (e.g. 1986): acceptable for a proof, to be re-timed to the real narration.
- Not verified: audio (none), pacing against real speech, readability on a phone, NASA licence for monetised reuse (the pages cite only the Reproduction Guidelines).
