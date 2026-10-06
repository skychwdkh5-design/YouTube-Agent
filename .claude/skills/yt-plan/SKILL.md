---
name: yt-plan
description: >-
  Plan a week or a month of YouTube uploads - what to post, when, and in
  what order, sized to the creator's actual capacity. Use for "plan my
  week", "content calendar", "what should I post", "I have no idea what to
  make next".
---

# yt-plan

A plan that does not fit the week is a list of regrets. Ask two questions before writing anything:
**how many hours do you actually have**, and **what is already half-made**.

## Before you write

1. **Channel profile first.** If the repository has a `channel/` directory, read `channel/channel.md`,
   `channel/voice.md` and `channel/editorial.md` before anything else. They are the voice profile and
   the rules, and they replace the rest of this step. That channel is faceless with AI narration: its
   voice is designed in `voice.md`, not inferred from videos, so never ask the creator for videos of
   themselves. Without a `channel/` directory, fall back to the original step:
   Read `~/.claude/youtube/voice.md` if it exists. That is the user's voice profile: how they talk
   on camera, the words they never use, who they are talking to, what they will not claim. If it
   does not exist, ask for **three of their own videos**, read or transcribe them, infer the voice,
   and write the file. A script in the wrong voice is worse than no script, because they have to
   read it out loud.
2. Never invent a number, a result or a source. If a figure would strengthen it and you do not have
   one, ask for it or write the line without it.

## The shape of a week

- **One anchor.** The video the week is for. It gets the most time and it goes out on the day the
  channel's own analytics say is best - ask for that, do not assume Tuesday.
- **One cheap one.** Built from something that exists: a clip, a reaction, a follow-up to the
  comment that got the most replies last week.
- **Shorts from the anchor.** Three, cut from the long video, not written separately. `/yt-shorts`
  finds them.

Three uploads on a seven-day week, not seven. A plan that posts daily is not a plan anyone
recognises, and the empty days are what make the filled ones survive a bad week.

## What to hand back

A table: day, format, working title, the one sentence it promises, and what already exists for it.
Then the honest line at the bottom - how many hours this costs, and what to drop first if the week
goes wrong.

## Geography channel mode

When `channel/` exists, the week follows `channel/channel.md` instead of the default shape:

- **1 main long-form** (8-12 min) - the anchor, picked from the top of
  `python3 .claude/skills/geo-topics/topicscore.py channel/ideas.md` (from the repo root).
- **1 lower-production long-form** (4-6 min) - one anomaly, simpler visuals, the same fact-check.
- **3-5 Shorts** - 2-3 cut from the main video by `/yt-shorts`, 1-2 standalone from verified facts.
- Budget the research and the two fact-check gates as real hours; they are never what gets cut.
  If the week breaks, drop the lower-production video first, then standalone Shorts.
- Topics may come from anywhere in the world - choose by score, not by region.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: **ship it, or change it?**
