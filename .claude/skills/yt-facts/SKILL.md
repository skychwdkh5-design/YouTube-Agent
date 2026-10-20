---
name: yt-facts
description: >-
  Claims gate for a script and its on-screen text: every factual sentence carries a claim id, media/organisation claims
  carry their attribution word, hypotheses are hedged, low-confidence claims and overreaching words are blocked. Use before
  voice generation, after editing a script, or when asked to fact-check a video.
---

# yt-facts

```bash
python3 facts.py --claims claims.json --script script.md --labels story/labels.json --root .   # exit 0 pass, 1 blocked
python3 facts.py --claims claims.json --defer-evidence --root .                                 # registry only (before evidence exists)
python3 test_facts.py
```
`claims.json` (schema `yt-facts/1`): `id, tier (original|media|org|science|observation|hypothesis), text, confidence (high|medium|low),
attribution, date, url, wording ("reported"/"said"), evidence (file, for observations), forbid [], allow []`.

Script rules: a sentence with a digit or a strong word (prove, reveal, confirmed, collapsed, cancelled, built, completed...) must end with `{C#}`;
a media/org claim sentence must contain its `wording`; a hypothesis sentence must hedge (may/could/consistent with); a claim below `--min-confidence`
(default medium) cannot be used (hypotheses are exempt but must be hedged); limitations end with `{L}` and must contain a negation. Observations need an
existing evidence file. Labels: a number on screen needs a claim; graphics declare `claims` in episode.json.
When a gate fires, change the wording or drop the sentence - never raise a confidence or add an `allow` to pass.
