# EP001 full narration: status (2026-10-08)

**COMPLETE.** All 10,506 billable characters of the locked narration (SCRIPT LOCK v1.1) are voiced by Adam `pNInz6obpgDQGcFmaJgB`, `eleven_multilingual_v2`, stability 0.55, similarity 0.75, style 0, speed 1.0 (only these four settings sent).

## Result
- 7 successful requests (request 1 cached from the first run, then six requests of at most 1,679 characters after `--resplit 1700`), sent sequentially, no automatic retries, no further HTTP 502.
- Audio: `voice/narration.wav` (local, gitignored; re-assembled from `voice/cache/` at zero cost), 747.357 s, 1,778 words with ElevenLabs word-level timestamps (`voice/narration.voice.json`).
- Subtitles synchronised to the real timings: `captions/captions.srt|vtt|json`, 185 cues.
- Sentence-unit timings S001-S120: `cues.json`.

## Credits (ceiling 10,510)
| item | credits |
|---|---|
| 7 successful requests (`character-cost` header) | 4,622 |
| two failed HTTP 502 requests on the first attempt (billed, matched by `/v1/usage/character-stats`) | 2,186 |
| **total spent** | **6,808** |

Remaining headroom under the ceiling: 3,702. `voice/ledger.json` records every attempt. The usage-stats delta matched the header for every paid request.

## Lessons
The gateway cuts a request at about 30 s; 1,679 characters (about 20-31 s) passed, 2,484 failed twice and was billed both times. Never send more than about 1,700 characters per request from this environment.
