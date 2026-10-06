---
name: yt-package
description: >-
  Write and lint the title and thumbnail for a YouTube video as one pairing,
  checking truncation, duplication and vagueness before publish. Use for
  "title ideas", "what should I call this", "thumbnail text", "my CTR is
  bad", packaging, or any request to rename or repackage an existing video.
---

# yt-package

The title and the thumbnail are ONE unit. Writing them separately is why most packaging fails: the
thumbnail repeats the title, and half the click surface says the same thing twice.

```bash
python3 title.py --title "..." --thumb "AI RAN IT"
python3 title.py titles.txt            # one per line, ranked
```

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

## Rules the tool enforces, and why

- **60 characters** is where desktop search truncates, **40** is a mobile home feed. Both are
  reported because they fail differently: a desktop cut loses the tail, a mobile cut can lose the
  subject.
- **The thumbnail must not repeat the title.** Different words, same promise.
- **Three words maximum on the thumbnail.** At feed size a fourth word is a grey smear.
- **A number, a name or a date** beats every adjective available to you.
- **Two all-caps words is the ceiling** before a title reads as spam.

## Write ten, keep two

Generate ten titles, run them all through `title.py`, show the user the top three with their scores
and the specific issue on each. For the winner, write the thumbnail brief: the expression, the
framing, the three words, and what the background has to do to hold contrast at feed size.

## Geography channel mode

When `channel/` exists:

- Run `python3 title.py --profile geo ...` - a place name counts as the "name", and U.S./D.C./U.K.
  are not read as shouting. Without the flag a geography title is wrongly told it has no name.
- **The thumbnail is a map, not a face.** Replace "the expression" in the brief with: the place or
  map shape, the one highlight, the framing, and how it reads at feed size - per
  `channel/visual-style.md`. Max three words, none shared with the title.
- **Titles are claims too.** "Only", "largest", "nobody", a number or a year in a title or on a
  thumbnail must match a VERIFIED or SOFTENED row in the video's `claims.md`.
- Curiosity yes, false promises never: the video must deliver what the pair promises
  (`channel/editorial.md`).

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: **ship it, or change it?**
