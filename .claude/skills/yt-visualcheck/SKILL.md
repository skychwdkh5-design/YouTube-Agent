---
name: yt-visualcheck
description: >-
  Visual-claim audit: for every claim-bearing on-screen text, graphic or shot - the source, the exact frame, the allowed wording and what was
  actually verified (VERIFIED_SOURCE, VERIFIED_DATA, REVIEWED_BY_AGENT/OWNER, NEEDS_VISUAL_REVIEW, FAIL). Use after the storyboard, before voice.
---

# yt-visualcheck  (FULLY_AUTOMATED checks; AGENT_REQUIRED or OWNER_REQUIRED for what code cannot judge)

```bash
python3 .claude/skills/yt-visualcheck/visualcheck.py --root productions/<slug>          # -> qa/visual_claims.json + .md, qa/frames/*.png; exit 0 only if OK
python3 .claude/skills/yt-visualcheck/visualcheck.py --root productions/<slug> review --item "<id>" --frame 0 --verdict supports|does_not_support|unclear --note "what the frame shows"
python3 .claude/skills/yt-visualcheck/test_visualcheck.py
```
- VERIFIED_DATA: date labels equal the scene metadata; a measured check (NDWI presence/absence/extent, scene metadata) passes AND the view contains the measured location. What the picture looks like is NOT machine-judged.
- VERIFIED_SOURCE: attributed statements (yt-facts checks the wording); flow graphics must carry each claim's exact short text; the scale arrow must equal the claim's length.
- NEEDS_VISUAL_REVIEW: the text asserts something about the picture and no machine check exists. A crop of every involved frame is written. A review must say what was seen (>= 20 characters), is bound to the frame's sha256 and the claim set (a changed picture invalidates it), and is recorded as REVIEWED_BY_AGENT - never as verified.
- Every frame of a wipe/compare must be reviewed. "unclear" does not pass. "does_not_support" fails. A claim below medium confidence fails.
