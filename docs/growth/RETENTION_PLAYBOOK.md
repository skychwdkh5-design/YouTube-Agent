# Retention playbook

Read before the script and again before the edit of every new long episode.

## Structure
- Every scene adds new information. If a scene could be cut without losing a fact, cut it.
- Show the evidence **while** the narration states it (the photo, the chart, the document) - not before,
  not after.
- Open questions only when the video answers them; answer each before opening the next big one.
- Length follows the story: 6-8 minutes without stretching beats 10 padded minutes.

## After publishing (day 7 and day 28 snapshots)
`python3 .claude/skills/yt-retention/episode_report.py metrics.json --history docs/growth/history.jsonl --retention retention.csv --markdown` builds the report: impressions, CTR by traffic source, 30-second retention, average view
duration, percent viewed, retention dips and peaks, A/B result. It compares only with earlier episodes at
a similar age and names differences in length and traffic mix. Small samples are "inconclusive".

The report answers four questions: which assumptions held, which did not, where viewers left, what to
test next. **Correlation is not causation**: a better episode after a change does not prove the change
caused it.

Data: YouTube Studio exports (Analytics -> Advanced mode -> export; retention chart -> download).
The publishing OAuth has no Analytics scope; adding one means a new consent - owner decision, not part of this change. Plan: `docs/growth/ANALYTICS_API_PLAN.md`.

## Confirmed (tested on our channel)
_None yet._
