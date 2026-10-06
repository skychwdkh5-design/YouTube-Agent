---
name: geo-topics
description: >-
  Find and rank geography video topics for a U.S. audience - strange borders,
  enclaves, anomalies, isolated places, maps that look wrong - scored by click
  potential, curiosity gap, proven interest and verifiability. Use for "find me
  topics", "what should the next video be about", "is this a good topic",
  "fill the idea backlog", or any geography idea that needs vetting.
---

# geo-topics

Topic choice decides most of a faceless channel's ceiling. A great script cannot rescue a topic
nobody wonders about, and a viral topic we cannot verify is a liability, not an asset.

```bash
python3 topicscore.py ../../../channel/ideas.md          # from this folder
python3 .claude/skills/geo-topics/topicscore.py channel/ideas.md --top 10   # from the repo root
```

## Before you start

1. Read `channel/channel.md` (pillars, audience, cadence) and `channel/editorial.md` (what we will
   not cover, and how disputed territories are handled).
2. Read `channel/ideas.md`. Never add a duplicate; improve the existing row instead.
3. Never invent evidence. A view count, a search volume or a Reddit thread is either linked in the
   Evidence cell or it does not exist.

## Where topics come from, in order of how much they prove

1. **Competitor outliers** - `/yt-viral` with `--profile geo`. A video at 3x its own channel's median
   is the strongest evidence of demand we can get without our own data.
2. **Our own audience** - repeated questions from `/yt-comment` triage, and later the retention and
   traffic data from `/yt-retention`.
3. **Recurring public curiosity** - long-running threads in map and geography communities, "why"
   questions people search, places that reappear in "weird maps" lists.
4. **Anomaly lists** - enclaves and exclaves, border quirks, extreme settlements, tripoints, odd
   shapes. These are leads to research, not evidence of demand.

**The world is the topic pool; the U.S. is the audience.** A global topic beats a U.S. topic whenever
it scores higher. Region is recorded for balance, never scored.

## Scoring - every criterion 1 to 5

| Criterion | 5 means | 1 means |
|---|---|---|
| Click | a U.S. viewer would tap it on a home feed | only a geography teacher would |
| Gap | a question they cannot answer themselves | the answer is in the title |
| Interest | linked proof of demand | a hunch |
| Outlier | a similar video beat its channel's median 3x+ | no comparable video found |
| Visual | the whole idea is visible in one map frame | needs a paragraph to see |
| Story | cause, conflict, payoff | a single fact |
| Verify | primary sources confirm every key claim | key claim is folklore |
| US | instantly relatable (a U.S. comparison exists) | needs a history lecture first |

Verify below 3 is REJECTED by the tool, whatever the other scores are. Interest or Outlier of 4-5
without Evidence is scored as 3.

Before scoring Verify, spend two minutes looking for the primary source of the ONE claim the video
depends on (the treaty, the census table, the survey). If you cannot find it, Verify is 2.

## What to hand back

- New or updated rows for `channel/ideas.md`, in its table format, with Evidence links.
- The `topicscore.py` ranking.
- For the top three: the working title direction, the one question the video answers, the map frame
  that shows it, and the riskiest claim to verify first.
- One line on pillar balance - only a note, never a quota.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: **ship it, or change it?**
