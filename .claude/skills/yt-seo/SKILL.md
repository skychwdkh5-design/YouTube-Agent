---
name: yt-seo
description: >-
  Write the description, tags and search-facing text for a YouTube video,
  aimed at the query a real person types. Use for "write my description",
  "tags", "SEO", "help this video get found", "nobody is finding this".
---

# yt-seo

Search is a smaller lever than packaging and a bigger one than people think for evergreen videos.
For a video aimed at the subscriber feed, say so and spend the effort on `/yt-package` instead.

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

## The description

- **The first two lines are the only ones anyone reads.** They show above "...more" and they are
  the search snippet. Say what the video gives them, in the words they would have typed.
- Then the link or the resource, if there is one, so it is above the fold.
- Then chapters (`/yt-chapters` writes them).
- Then the long version: what is covered, who it is for, what it assumes.

## Tags, honestly

Tags are a weak signal and YouTube has said so. Use them for disambiguation - spellings, the tool
names, the abbreviations people actually type - and stop. Fifteen is plenty. A wall of tags is not
a strategy and stuffing unrelated ones is against the terms.

## The query test

Before handing anything over, write the three search queries this video should win, and check the
title and first two description lines contain the words in those queries. If they do not, the
problem is the title, not the description.

## Geography channel mode

When `channel/` exists:

- Write the three queries in the words a U.S. viewer types ("why does minnesota have a piece in
  canada", "town only reachable through canada").
- Spell place names the way U.S. searchers do, and put the common alternative spelling in tags.
- Below the long version, add **Sources** (the key Tier 1 sources from `claims.md`) and **Credits**
  (the block from `geo-visuals/assets.py --credits`). Both are required by `channel/editorial.md`
  and `channel/visual-style.md`.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: **ship it, or change it?**
