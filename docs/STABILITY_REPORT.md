# Stability report (2026-10-20), code commit 30084f6

## The two failures (reproduced at HEAD 6346754, 17 tests, 2 failed)
1. `Gates.test_negative_review_blocks`: expected `blocked`, got `done`.
2. `Gates.test_stale_review_is_not_accepted_after_the_picture_changes`: expected `needs_agent`, got `done`.
Evidence: `productions/neom-line/qa/visual_review.json` held 18 reviews, 4 of them orphans (frames from an earlier planner version, hashes matching no current frame). Both tests mutated `reviews[0]`, an orphan, so the mutation changed nothing. The product logic (a negative or stale review must block) was correct; the fixture and tests assumed a review that was no longer live. Not caused by parallel edits (reproduced in a sequential run).
Fix (no check weakened): tests now mutate a LIVE review; visualcheck reports orphan reviews and has an explicit `prune`; coverage self-audit (a missing item is a FAIL); `total` equals the sum of status counts (asserted); stage inputs for visualcheck now include graphics_spec, stack provenance (image hashes) and grid, tool hashes include geostack.
## Also found by a fresh-topic run (salton-sea-test, new geography, western hemisphere)
- Orchestrator passed `--aoi -115.8,...`: argparse read the negative longitude as an option (every western-hemisphere topic would have failed). Fixed (`--aoi=...`), 2 regression tests.
- Planner gave a 4-second chapter three pictures: storyboard refused. Planner now sizes pictures to chapter length and reports what it dropped.
- Planner focus placed on open water: the visual review (not the code) caught that frames showed no shoreline; focus corrected through research notes.
## Evidence (sequential, unchanged code, clean tree before and after)
- Orchestrator suite: run A 22/22 OK (268 s); run B inside the full regression 22/22 OK (263 s). The suite has 22 tests: the original 17 plus 5 added (live-review mutation variants, orphan/prune, counts+coverage, stack-image invalidation, negative-longitude args).
- Full regression: captions 28, facts 13, geo 8, graphics 19, orchestrate 22, qc 21, render compose 27, render 27, video 22, research 6, satellite 17, script-agent 9, sentinel 9 (+1 live), storyboard 10, topic 13, visual-planner 11, visualcheck 15, voice 31: all OK.
- visualcheck on EP005: 75 items = 7 VERIFIED_SOURCE + 58 VERIFIED_DATA + 10 REVIEWED_BY_AGENT, 0 NEEDS_VISUAL_REVIEW, 0 FAIL, 0 orphans. Salton test: 16 = 12 VERIFIED_DATA + 4 REVIEWED_BY_AGENT.
## Fresh topic without prior preparation (salton-sea-test, no paid call)
new -> topic (candidates from live YouTube data + Sentinel-2 availability, scored) -> research notes (agent) -> evidence (live Sentinel-2) -> script (agent; INSUFFICIENT_FACTS honestly reported: 199 words, 1.4 min) -> visualplan -> graphics -> storyboard -> visualcheck (agent review of 4 distinct frames) -> voice gate (1,141 characters). The topic is not production-quality: its verified facts cover 1.4 minutes; it tests the machinery, not a releasable video.
