# Hook playbook (first 30 seconds)

Read before writing the opening of every new long episode. The timings are editorial targets, not
platform rules.

| time | job | test |
|---|---|---|
| 0-3 s | show the promised object or event from the cover | could a viewer match frame 1 to the thumbnail? |
| 3-10 s | an unexpected fact, conflict or result | is it a verified claim with a source? |
| 10-30 s | why it matters + the next open question | does the video actually answer that question later? |

## Never
- A logo, channel ident, greeting, "in this video", general history or a slow scene-setter first.
- A false open loop (a question the video does not answer) or invented stakes.
- Saying a fact twice in different words to fill time.

## Write three
For each concept in `thumbnail_hook.json` write `hook_15s` with the 0-3 / 3-10 / 10-15 beats. The chosen
one is checked by QC (`thumbnail_hook_*`: subject by 3.0 s, cold open). `yt-script/hookscore.py` can score drafts; it favours talking-head "you" hooks, so treat it as a prompt, not a verdict.

## Confirmed (tested on our channel)
_None yet._
