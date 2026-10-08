# EP001 full narration: status (2026-10-08)

**Blocked after request 1 of 5. Nothing is lost: request 1 is saved and verified. Waiting for approval to change the request split (same text, same budget).**

## What was authorised and done
Adam `pNInz6obpgDQGcFmaJgB`, `eleven_multilingual_v2`, stability 0.55, similarity 0.75, style 0, speed 1.0 (exactly the four reviewer values; no other voice setting sent). Plan verified before the first paid request: **10,510 billable characters in 5 requests** (2,276 / 2,484 / 2,481 / 1,944 / 1,325), equal to the authorised ceiling of 10,510 and not above it. Balance: not readable (the key has no `user_read`), so the authorisation was the control.

| # | chars | result |
|---|---|---|
| 1 | 2,276 | **ok**: 170.16 s of audio, `character-cost` header **1001** credits (0.44 per character), request id `uaUsA5xB7rFeuTC4RmNX`; saved at once (`voice/cache/`) |
| 2 | 2,484 | **HTTP 502 "upstream request failed" after about 30 s** |
| 2 (resume) | 2,484 | **the same 502 after 30.4 s** |
| 3-5 | | not sent |

The resume was a single manual re-send of the failed segment (resuming from cache, as authorised); it is the only retry and nothing ran automatically. I stopped after the second identical failure.

## What the evidence says
Both failures arrive at the same moment (about 30 s) with a generic gateway error, not an API error; request 1 (170 s of audio) got through. So a long response is cut off by a roughly 30 s limit somewhere between the sandbox and ElevenLabs, and request 2 (about 183 s of audio) is slightly over it. Sending request 2, 3 or 4 again as they are would fail again, and each failed attempt may or may not have been billed (not observable). I have not tested this with any further request.

## Credits
Measured: 1,001 credits for request 1. Not measured: whether the two failed attempts were charged (worst case at the same 0.44 rate: about 2 x 1,093). The measured rate suggests the whole narration costs about 4,700 credits, well inside the 10,510 ceiling even if the two failures were charged. `voice/ledger.json` records every attempt.

## Proposed fix, needs your approval (it departs from "five requests")
Keep request 1 exactly as cached and send the remaining 8,230 characters as **six shorter requests** of at most 1,679 characters (about 125 s of audio, a 30 percent margin under the failing size): `[2276 cached] + [1679, 1524, 1410, 1592, 1580, 445]` = 7 requests, 10,506 characters, same text, same voice and settings, same ceiling. No automatic retry, each success saved at once. Command (not run): `python3 generate_ep001.py --resplit 1700 --confirm`.

## Verified on the real audio of request 1 (free)
All 383 words aligned (word-level timestamps from ElevenLabs); the yt-captions run is valid (51 cues, wording preserved, no overlaps); 28 sentence units (S001-S028) located from real timings; speaking pace 135.1 words per minute (so the whole narration is about 13.2 minutes, not 12.3); loudness -17.2 LUFS integrated, true peak -1.3 dBFS (the renderer applies one constant gain to -16 LUFS); one pause over 1 s (1.2 s). Files: `voice/partial_test/` (local), `voice/cache/` (committed, so the paid audio survives this container).
