---
name: yt-script
description: >-
  Write a YouTube video script from a raw idea - hook options off 21
  formulas, scored, then the full spoken script with the retention beats
  marked. Use whenever the user wants a video script, a hook, an opening
  line, "what should I say", "write my next video", or is about to record
  and does not have the first fifteen seconds yet.
---

# yt-script

One idea into a script somebody finishes.

Two tools live in this folder and both actually run. Use them. Do not eyeball the hook.

```bash
python3 hookscore.py hooks.txt              # rank your hook options
python3 hookscore.py --hook "one line"      # score a single one
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

## The shape

**The first 15 seconds is the whole job.** It does three things or the video leaks: confirm the
click the title promised, open a question the viewer cannot close, and prove the payoff exists.

1. **Hook.** Write FIVE against [the 21 formulas](hooks.json), run them through `hookscore.py`,
   keep the top two, and show the user both with their scores. Never hand over one hook.
2. **The turn** (0:15-0:45). Say what the video is going to do, in one sentence, and start doing it.
   No channel intro, no "before we get started", no subscribe pitch. Those are the single most
   common cause of the 0:30 cliff.
3. **The body.** One idea per beat. Mark each beat with what is ON SCREEN, not just what is said -
   a talking head with nothing to look at is a podcast.
4. **The payoff.** Deliver the thing the hook promised, explicitly, and say that you are delivering
   it: "that is the prompt, it is in the description".
5. **The close.** One ask. Not three.

## What to hand back

- the two best hooks with their scored panels
- the script, beat by beat, with `[ON SCREEN: ...]` on every beat
- the runtime estimate at 150 words per minute
- one line naming which formula the winning hook used and why it fits this idea

## Geography channel mode (faceless, AI narration)

When `channel/` exists, these replace the matching parts above; everything else still applies.

- **Research first.** No script before the video's `claims.md` has passed geo-factcheck Gate 1. The
  script may only use VERIFIED claims, and the Final wording of SOFTENED ones.
- **Hooks:** write five, run `python3 hookscore.py --profile geo hooks.txt` (ANOMALY replaces
  STAKES, and the geography formulas in `hooks-geo.json` join the 21), keep the top two, show both
  panels. The hook names or shows the place within 3 seconds.
- **Format:** use `channel/templates/script.md`. Narration lines start with `VO:`; every beat
  carries `[MAP: ...]` or `[VISUAL: ...]` - these are the `[ON SCREEN]` marks for a faceless video,
  describing maps, satellite, footage, graphics. There is no host, so never write a talking-head
  beat, and the narrator never says "I".
- **Claim tags:** every factual sentence ends with its ledger ID, `[C3]`. A sentence that looks
  factual but is not gets `[NC]`. Then run geo-factcheck Gate 2:
  `python3 ../geo-factcheck/claims.py --claims <claims.md> --script <script.md>`. A FAIL goes back to
  the script, not forward to packaging.
- **Write for the AI voice** as `channel/voice.md` says: native American English, short sentences,
  contractions, no parentheses or abbreviations the voice will misread, imperial units first, place
  names checked against the pronunciation dictionary.
- **Runtime** at the measured WPM in `voice.md` (150 until measured). Main video 8-12 min, lower-
  production 4-6 min, per `channel/channel.md`.
- **The payoff** is said out loud and shown on the map at the same moment.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: **ship it, or change it?**
