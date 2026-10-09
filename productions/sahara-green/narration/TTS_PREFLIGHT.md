# EP001 ElevenLabs pre-flight (2026-10-08): no audio generated, no credits spent

## What was checked (free calls only)
| Call | Result |
|---|---|
| GET /v1/voices/{id} for Brian, Bill, Adam | HTTP 200: premade, American male, models listed |
| POST /v1/text-to-speech/{voice}/with-timestamps with an EMPTY body | HTTP 422 `text: Field required`. Validation, not authorisation, answered: the key is very likely allowed to use text-to-speech. No text was sent, nothing was generated. |
| GET /v1/user, /v1/user/subscription | 401: key lacks `user_read` (plan and credit balance are invisible) |
| GET /v1/models | 401: key lacks `models_read` |
| GET /v1/pronunciation-dictionaries | 401: key lacks `pronunciation_dictionaries_read` |
| elevenlabs.io pricing page | unreachable from this environment (no pricing was verified) |

## Voices (selected order, exact IDs)
1. **Brian** `nPczCjzI2devNBz1zQrb` (American, middle-aged, "Deep, Resonant and Comforting")
2. **Bill** `pqHfZKP75CvOlQylNhV4` (American, "Wise, Mature, Balanced", crisp)
3. **Adam** `pNInz6obpgDQGcFmaJgB` (American, "Dominant, Firm"; channel default)

## Models and pronunciation
Use `eleven_multilingual_v2` for the narration (quality first). Faster, cheaper models (`eleven_turbo_v2_5`, `eleven_flash_v2_5`) are listed for Brian and Bill but are not recommended for the final read. Pronunciation: see `voice_config.json` (`preflight_findings.pronunciation`); the key cannot manage dictionaries, so the first answer is the listening test.

## Identical sample for every narrator
`audition/sample_text.txt`: 677 characters, three paragraphs, verbatim from the locked narration (S001-S003 the hook, S047-S049 East Oweinat, S055-S058 Toshka: numbers 230, 1984, 2002, 2012, 2021 and the names Oweinat, Toshka, NASA's). Same text, same settings (stability 0.55, similarity 0.75, style 0, speed 1.0, speaker boost), one request per voice.

## Credits
| Item | Characters | Credits (multilingual_v2, 1 credit per character) |
|---|---|---|
| Sample per voice (voice.py plan: 677 characters, 1 chunk) | 677 | 677 |
| Three samples (Brian, Bill, Adam) | 2,031 | 2,031 |
| Full narration (voice.py plan: 10,510 characters, 5 chunks) | 10,510 | 10,510 |
| Minimum: one sample plus the full narration | 11,187 | 11,187 |
| Planned: three samples plus one full narration | 12,541 | 12,541 |
| Worst case: three samples plus two full narrations | 23,051 | 23,051 |
| The same full narration on a 0.5-credit model (not recommended) | 10,510 | 5,255 |

Exactly what is counted: the characters of the `text` field of each request, including spaces and the blank lines between paragraphs; `previous_text` and `next_text` (continuity context) are sent but are, per ElevenLabs' documentation as I know it, not billed.

## Uncertainty (none of this can be verified without a paid call)
1. **The rate of 1 credit per character for Multilingual v2** (0.5 for Flash/Turbo) is documented behaviour I cannot read back: `models_read` is denied and the pricing page is unreachable.
2. **Balance and plan are unknown** (`user_read` denied). Plan and credits must come from you; the free tier (about 10,000 credits) does not cover one full narration (10,510).
3. **Failed requests**: an HTTP error normally costs nothing, but I cannot prove it; yt-voice never retries automatically, so a failure costs at most one request.
4. **Regeneration** (a retake of any chunk or the whole narration) is billed again in full.
5. **Does the `with-timestamps` endpoint cost the same?** It is documented as the same price; unverified.
6. **Dollar cost**: not computed; depends on your plan. As an order of magnitude, 12.5k credits is roughly 12% of a 100k-credit monthly plan.
7. TTS permission is inferred (422 instead of 401), not proven.

## Next steps (each paid step needs your explicit "yes" and `--confirm`)
1. You tell me the plan and remaining credits (at least 12.6k for the planned path).
2. Listening test: `voice.py --script audition/sample_text.txt --voice-id <id> --output voice/sample_<name>.wav --max-chars 700 --voice-settings '{...}' --context --confirm` for Brian, Bill, Adam (2,031 credits).
3. You pick the narrator; then the full narration (10,510 credits) and `cues.py`, captions, final timeline.
