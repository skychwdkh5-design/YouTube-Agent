# Shorts performance feedback (design, audit, protocol)

Status 2026-10-12. Built on branch `feature/shorts-performance-feedback`. **Nothing here collects data from YouTube**: there is no connected Analytics API, no
scheduled job and no credential in the repository. Numbers enter from a file a person exports. Everything below that is measured is stated with its sample size;
everything else is marked ASSUMPTION or HYPOTHESIS.

## 1. What the two published Shorts say (observations, not causes)

| | SHORT 001 The Sahara Is Turning Green? | SHORT 002 Can Humans Turn the Sahara Green? |
|---|---|---|
| duration | 51.0 s | 53.4 s |
| views / engaged views | 374 / 137 | 1,212 / 592 |
| stayed to watch / swiped away | 37.2 % (95 % interval 32.4-42.2) / 62.8 % | 54.0 % (51.1-56.7) / 46.0 % |
| average view duration / average % viewed | 17 s / 33.7 % (replay_ratio 0.33) | 75 s / 139.8 % (replay_ratio 1.41) |
| subscribers gained | 0 (rate < 8.0 per 1,000 views, 95 % bound) | 0 (< 2.5 per 1,000); both together 0 of 1,586 views (< 1.9 per 1,000) |

Intervals use Wilson's method on `views` as the denominator (ASSUMPTION: Studio does not state the denominator of the exported percentage; viewers are treated as independent).
`views` and `engaged_views` are different YouTube metrics (`engagedViews` = viewed past the first frame or tap-to-play, https://developers.google.com/youtube/analytics/metrics): the
stored ratio engaged/views (0.37 and 0.49) describes each video and is never used in place of "stayed to watch". The two Shorts differ in topic, story, first frame and
unknown traffic/publication time, so the gap between 37 % and 54 % is a lead for a test, not an effect size.

Replays are visible in SHORT 002 only: 75 s average on a 53.4 s file. The text seam of that Short (`... A WEAK INCREASE | YOU COULD TURN THE SAHARA GREEN IN 2009 ...`) shares no content word, so a
designed loop does **not** explain it; repeated playback can come from dense numbers, from autoplay looping of short files, or from something not measured here.
The Analytics API excludes looping-clips traffic from `averageViewDuration` and `averageViewPercentage` since 2021-12-13, whereas Studio's >100 % figure includes repeats:
never combine the two sources in one comparison (`metric_source` records which one a row came from).

## 2. Audit of the existing Shorts pipeline

| stage | mechanism in the repository | gap |
|---|---|---|
| scripts | `/yt-script` (21 hook formulas in `hooks.json`, `hookscore.py`); `/yt-shorts` (cut a Short from a long video, new first line, loop point note); claims ledger before TTS (`docs/production-pipeline.md`) | no record of how published scripts performed; `hookscore.py` states itself that it barely separates a creator's hits from misses |
| first frames | timeline v3 `shots[0].start == 0` ("the first frame is the hook", `compose.py`); `/yt-qc --profile short`: >= 3 distinct compositions in the first 10 s (fail), >= 5 information events (warn), >= 3 visual families (warn) | nothing compares alternative first seconds |
| visual transitions | layers `wipe`, `flip` (timelapse), camera moves; composition-reset and visual-family novelty rules | none needed for this task; the first-seconds variants reuse them |
| final scenes | `end: {after_last_word, min_total}`; `yt-script`: no subscribe pitch, one ask at the close | no loop construct, no series cue, nothing records what the ending did |
| feedback | `/yt-retention` reads one retention CSV per video | no store of published results, no hypotheses, no experiment ledger, no decision rules (**added here**) |

What can change without breaking a rule: variants of the first shot's camera/layers/labels (timeline JSON only), a closing shot that returns to the opening view, `end.after_last_word` (0-10 s), 
series cues outside the video (description, pinned comment), new analytics files. What cannot, and why: a different spoken first line (new TTS take: paid, needs explicit approval); Shorts shorter than
35 s (`yt-qc --profile short` fails below `min_s` 35: proposed change, not made, because it alters a production rule and its tests); a subscribe pitch inside the Short (`yt-script`); music/sfx (refused by yt-render).

## 3. Root-cause hypotheses (each is a candidate, with what would test it)

1. **H-001 opening form.** SHORT 001 opens with orientation (`THIS IS EAST OWEINAT`, `IN SOUTHERN EGYPT`) and states its payoff at 9.5 s; SHORT 002 opens with the claim at 0.1 s. Test: EXP-001 (claim-first vs orientation-first, same spoken line).
2. **H-002 loop and replays.** Not supported by the mechanical seam check; needs EXP-002 (loop-closed vs plain ending) before any claim.
3. **H-003 length.** No contrast in the data (51 s and 53 s). Test: 35-45 s vs 45-60 s (EXP-003); compare `stayed_to_watch_percent` and absolute `average_view_duration`, not percent viewed (mechanically easier on a short file).
4. **H-004 subscribers.** 0 of 1,586 views says the rate is below about 1.9 per 1,000, nothing more. A quiet series identity is a candidate (EXP-004) but needs thousands of views per arm.
Not claimed: that the visuals, thumbnail, title or posting time are or are not the cause. They were not reviewed or are unknown.

## 4. Experiment protocol

- **Unit.** The Short, not the view. Topic effects belong to the video, so every variant needs at least two Shorts (`plan-experiment` refuses fewer) with seeded, blocked assignment committed before publishing (`analytics/shorts/experiments.json`, EXP-001 for the next four Shorts).
- **Measurement.** Same age for every Short (7 days by default), `measurement_timestamp` recorded, primary metric fixed in advance, no early stopping. `feedback.py evaluate` answers `insufficient_data` until each arm has the pre-registered number of videos and views.
- **Power.** For a 45 % baseline `stayed_to_watch`, 1,000 views per arm detects a difference of about 6.3 points, 300 views about 11.4 (`feedback.py power`). Differences smaller than that need more Shorts, not a lower bar.
- **First 1-3 seconds.** `variants.py build` writes one timeline per variant, changing only the first shot's camera/layers/info/visual family; narration, captions, claims, timing, later shots and the end must be identical and are checked; `--validate` runs `render.py` without `--confirm` (plan only, nothing renders). Suggested factor values: first frame = strongest verified real image vs orientation view; on-screen text = claim (<= 6 words) vs question vs place/year label; first move = push-in vs static vs wipe. Keep `/yt-script`'s `hookscore.py` as a sanity check only.
- **Length.** Arms 35-45 s and 45-60 s within the current `short` profile. 30-35 s needs the `min_s` change above (not made). Match the story: same claims depth, cut or extend evidence, not speed.
- **Loop.** `variants.py loop-close` appends a `loop_return` shot whose camera ends on the opening view (layers from the first frame); set `end.after_last_word` small (for example 0.4 s) so the picture returns before the restart; `loopcheck.py` measures the text, picture and audio seams (descriptive labels, not predictions). Also test that the last spoken line sets up the first one; a seam that merely matches visually is not enough.
- **Subscribers, quietly.** Series identity instead of an ask: one consistent end tag (about 1.5 s, the same words each Short), a pinned comment naming the next Short only when it exists, a first description line pointing to the long-form video (EP001), a stable channel name/avatar (already in EP001 branding). ASSUMPTION, not verified: the Studio option that links a related video to a Short. Measure as `subscribers_per_1000_views`; the baseline is 0 of 1,586.
- **Style and science.** Variants may not change evidence, claims, labels or credits; every layer keeps its source label; Orbital Atlas visual identity is unchanged.

## 5. Future import (not connected)

`import-api-json` reads a saved `reports.query` response (one video per call, metrics `views, engagedViews, averageViewDuration, averageViewPercentage, subscribersGained`; names verified on the metrics page above)
and stores it with `metric_source: analytics_api`; `stayed_to_watch_percent` and `swiped_away_percent` are not listed there and stay null. A scheduled collector would need OAuth credentials, user consent and a
decision about where tokens live; none of that exists and none was added. `import-csv` maps Studio headers through an alias table (ASSUMPTION: headers vary; unmapped columns are reported, `--map` overrides).

## 6. Files

`analytics/shorts/*` (data), `.claude/skills/yt-shorts-feedback/` (`feedback.py`, `variants.py`, `loopcheck.py`, schema, tests, SKILL.md), `.claude/skills/yt-shorts/SKILL.md` (pointer), `docs/production-pipeline.md` (loop section), `CLAUDE.md` (rules).
