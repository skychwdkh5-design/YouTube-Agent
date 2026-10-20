---
name: yt-script-agent
description: >-
  The writing brief and acceptance gate for a 6-9 minute documentary script in American English: chapter skeleton from the
  verified claims, word budget, style rules, then validation (length, structure, hook, repetition/padding, claim coverage,
  yt-facts lint). Use when yt-orchestrate reports script needs_agent, or after editing script.md.
---

# yt-script-agent  (AGENT_REQUIRED: Claude writes the prose; the tool writes the brief and decides acceptance)

```bash
python3 .claude/skills/yt-script-agent/scriptagent.py brief    --root productions/<slug>    # -> tasks/script.md, research/brief.json
python3 .claude/skills/yt-script-agent/scriptagent.py validate --root productions/<slug>    # ok | blocked (reasons) | needs_agent
python3 .claude/skills/yt-script-agent/test_scriptagent.py
```
Write `script.md` with `## id: Title` chapters exactly as the brief lists, `{C#}` tags on factual sentences, `{L}` on limitations. Target 882-1,323 spoken words (2.45 words/s).
Gates: 6-9 minutes (if the verified facts cannot carry six minutes the brief says INSUFFICIENT_FACTS and a shorter honest script passes with a warning), hook <= 70 words,
repetition of 5-grams <= 3 % (padding fails), must-cover claims used, low-confidence claims unused, then the full yt-facts lint. The tool never writes or edits prose.
