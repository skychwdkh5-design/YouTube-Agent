# ElevenLabs narration: cost-safe procedure (EP002 pass, 2026-10-13)
Skill: `.claude/skills/yt-voice` (`voice.py`). Full record: `productions/dubai/TTS_PLAN.md`.
## Procedure **[VERIFIED]**
1. SCRIPT_LOCK hash must match the spoken text (`grep '^VO: ' script | sed 's/^VO: //' | sha256sum`). Keep the TTS input to spoken text only; do not edit it for pronunciation (the text is locked).
2. Plan without `--confirm`: characters, chunks, voice, model. **Billable characters = sum of chunk lengths.** Paragraph blank lines add characters (EP002: 6,998 with single newlines, 7,025 with blank lines): choose the cheaper layout when the budget is tight.
3. Free checks that need no credits: `GET /v1/voices/{id}` (voice reachable); the key may lack `user_read`/`models_read`, so the balance cannot be read.
4. One run: `python3 voice.py --script TEXT --output voice/narration.mp3 --max-chars N --context --cache-dir voice/cache --confirm`.
5. `--context` (previous/next text) smooths chunk joins and bills no extra characters. `--cache-dir` stores each paid chunk response (audio + alignment, no key) the moment it succeeds: a failure in chunk 2, an alignment mismatch or an ffmpeg error never forces paying chunk 1 again. **Never** re-run with a changed text/voice/model/settings/context without approval (any change is a new cache key = new charges).
6. After the run: copy `voice/cache/` and the mp3 to stable storage immediately (branch `media/ep002-dubai-audio`), commit only `narration.voice.json`.
## EP002 numbers **[VERIFIED]**
Adam `pNInz6obpgDQGcFmaJgB`, `eleven_multilingual_v2`, 3 chunks (2470+2479+2049 = 6,998 chars), 515.251 s, 1,225/1,225 words timed, no warnings, one pass, no retries. Credits: about 6,998 **[ASSUMED 1 credit/char; balance unreadable]**.
## Failure policy
On an API error do not retry automatically: first check whether credits were charged and whether a cache entry exists; the unit test `ChunkCache` covers the resume path.
## Open items
Pronunciation of "ASTER", "Jumeirah", "vibroflot", "Deira" is **UNVERIFIED** (nobody listened; the agent cannot listen). The user must listen before approval; a respelled retake costs credits and needs approval.
