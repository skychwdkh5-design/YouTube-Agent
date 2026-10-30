# Outlier research

Read before choosing every new long episode. Tool: `python3 .claude/skills/yt-viral/outliers.py <file.json> --markdown`.

## Method
1. Collect candidates for the topic (vidIQ `vidiq_outliers` / `vidiq_youtube_search`, YouTube Data API,
   channel RSS, manual list). Keep raw data in the run folder; never re-type numbers from memory.
2. For each promising video collect its channel's **own comparable videos** (same format, at least
   14 days old, within a year). Without them the ratio is a third-party score.
3. Run the detector. Baseline = median views of those comparables; ratio = views / baseline.
4. Study videos at **>= 3x** with `data: sufficient` and confidence not `low`. Focus on 3-4x: big enough
   to mean something, close enough to a normal video to learn from. Above 10x is usually luck, news or
   a different audience.

## Rules
- Never call a video viral. Use the tiers: typical, above (1.5-3x), strong (3-4x), exceptional (>= 4x).
- Under 5 comparables = insufficient: no tier. Under 14 days old = provisional.
- A feed of outliers has no base rate: it shows what won, never how often the topic fails.
- Separate **facts** (numbers collected, title, thumbnail, date, duration) from **hypotheses** (why it
  worked). A hypothesis goes to EXPERIMENT_LOG.md and is tested on our own videos before it is a rule.
- Sensational or AI-labeled outliers are demand signals, not models: we do not copy invented claims.
- Budgets: vidIQ: Orbital Atlas share is 45 credits per cycle, 10 per week (owner decision 2026-10-29); call `vidiq_balance` (free) before and after, and log every call. The quick swipe file (`yt-viral/swipe.py`) stays for informal lists; use outliers.py for decisions.

## Confirmed findings
_None yet. Only findings tested on our own episodes (EXPERIMENT_LOG.md, status confirmed) go here._

## Run log
| date | topic | videos / channels | focus videos | run folder |
|---|---|---|---|---|

