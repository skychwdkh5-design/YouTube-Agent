---
name: yt-shorts-feedback
description: >-
  Record what happened to published Shorts and turn it into checkable hypotheses and experiments: first
  1-3 seconds variants, 35-45 s vs 45-60 s length, loop endings, quiet series cues for subscribers.
  Use for "how did my Short do", "log these Studio numbers", "what should the next Short test",
  "why do people swipe away", "make the end loop", "A/B the first seconds".
---

# yt-shorts-feedback

Shorts are small samples. This skill keeps the numbers honest, remembers every published result and makes the
next Short a test of one thing. It never collects anything by itself and never promises a result.

```bash
python3 feedback.py report                      # what we know, with intervals and caveats
python3 feedback.py add --video-id ... --duration-seconds ... --views ...   # append one Studio reading (never overwrites)
python3 feedback.py import-csv export.csv       # dry run; add --write to store. Headers are an ASSUMPTION: use --map "Column=field"
python3 feedback.py import-api-json r.json --video-id ID   # a SAVED Analytics API response; nothing is fetched
python3 feedback.py evaluate                    # apply each hypothesis' pre-registered rule; "insufficient_data" is the normal answer
python3 feedback.py power --baseline 45 --n 1000            # smallest detectable difference (percentage points)
python3 feedback.py plan-experiment --id EXP-002 --factor loop_ending --variants A,B --videos S7,S8,S9,S10 --seed 11 --write
python3 variants.py build spec.json --validate  # single-variable timelines for the first seconds (no render, no TTS)
python3 variants.py loop-close timeline.json --start 49.5
python3 loopcheck.py --captions captions.json --video short.mp4 --declared visual_return
python3 test_feedback.py && python3 test_loop_variants.py
```

Data lives in `analytics/shorts/` (see its README): `measurements.jsonl` (append-only), `videos.json`, `hypotheses.json`, `experiments.json`.
Design, metric definitions, experiment protocol and limits: `docs/shorts-performance-feedback.md`.

## Rules

1. **`views` and `engaged_views` are different metrics.** Never substitute one for the other. `stayed_to_watch_percent` and `swiped_away_percent` are
   Studio's "viewed vs swiped away"; the Analytics API does not list them, so they are entered by hand or stay null.
2. **Unknown is `null`.** Publication date, YouTube id and measurement time that nobody supplied stay null. Never fill them from memory.
3. **Do not mix Studio and Analytics API numbers** in one comparison: the API excludes looping-clips traffic from `averageViewDuration` and
   `averageViewPercentage` (https://developers.google.com/youtube/analytics/metrics, read 2026-10-12), Studio's 139.8 % figure shows repeats are included there.
4. **One variable per test.** A variant may change only the first shot's camera, layers, info or visual family. Narration, captions, claims, timing and every later
   shot stay identical; `variants.py` checks it. A different spoken line is a new TTS take: paid, needs the user's explicit approval, not done here.
5. **Pre-register.** Hypotheses, decision rules, seeds and assignments are committed before the Shorts publish. `evaluate` refuses a verdict on one Short per
   arm, on an unknown measurement window, or on mixed sources.
6. **Results are leads.** A 5-point difference between two different stories is not a result. Say what the interval is and what else differs.
7. **Nothing publishes and nothing renders here.** This skill writes files; the user publishes.

## After every publish

Add the reading at a fixed age (7 days by default) with `measurement_timestamp`, then `report` and `evaluate`. If an experiment is running, record
`experiment_variant` as `<experiment id>:<variant>`.

## Before the next Short

Read `analytics/shorts/hypotheses.json` and the open experiment in `experiments.json`. If the next Short is a slot in a running experiment, build it with the
assigned variant and nothing else different. If not, write the Short with `/yt-shorts` and `/yt-script` as usual and record `baseline_unplanned`.
