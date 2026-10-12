---
name: yt-shorts
description: >-
  Find the Shorts hiding inside a long video and write them, using the
  transcript to pick self-contained moments. Use for "cut this into shorts",
  "clip this", "repurpose this video", "what should I clip".
---

# yt-shorts

A Short cut out of a long video is not a clip of the best moment. It is a moment that **survives
without the video around it**, which is a much smaller set.

## Picking

Read the transcript and find spans of 20-55 seconds where all three are true:

1. It opens on a complete thought. If the first sentence needs the previous minute, it is not a Short.
2. There is a turn in it - a claim, then something that complicates or proves it.
3. It ends on a line, not a trail-off.

Rank the candidates and show the user the top five with their timecodes and first line, so they can
reject one without reading the whole transcript.

## Writing each one

- **A NEW first line.** The long video's line assumes context this viewer does not have. Write the
  replacement and run it through `../yt-script/hookscore.py`.
- **On-screen text for the first two seconds**, different words from the spoken line.
- **A loop point**: what the last line sets up so the first line answers it.
- Vertical framing note - what gets cropped out of a 16:9 frame and whether that matters.

## Use what the channel has learned

Before writing, read `analytics/shorts/hypotheses.json` and the open experiment in `analytics/shorts/experiments.json` (`/yt-shorts-feedback`). If the Short is a slot in a
running experiment, change only the declared variable. Record the loop point, the first-seconds form (claim, question or orientation) and the length bucket in the block you hand over so the result can be attributed.
After publishing, the user logs the numbers with `/yt-shorts-feedback`. Results are leads, never promises.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: **ship it, or change it?**
