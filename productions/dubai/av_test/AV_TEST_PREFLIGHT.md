# EP002 Dubai — 60-second audio-visual test: PREFLIGHT (Phase 1)

Base: e992816. **No paid request has been made.** Phase 2 is blocked until you approve the TTS spend below.

## Script lock
The narration hash recomputed from `script_draft_v1_2.md` is `d050d5e30db834f42315850945b2d4b7eb1a0c99bafa994b1f1b2e49d3360d0d`, equal to SCRIPT_LOCK.md; file blob `fdc3e87d117b54daade1b62225bd86f8ddf13d98`. No VO line is changed by this test.

## Selected passage (continuous, scenes H1 to A1 of the locked script)
128 words, 695 characters. SHA-256 of the passage text with a trailing newline: `ed31cf69d63f089bff7b68044d0280d60e867530276cfa9e7b01dd163518d1eb`.

| scene | words | chars | locked narration |
|---|---|---|---|
| H1 | 20 | 104 | November 2000. A satellite looks down at a patch of the Persian Gulf. There is no island here. Just sea. |
| H2 | 16 | 98 | November 2003. The same place. A palm tree, fully formed. Between these two pictures: three years. |
| H3 | 25 | 167 | More than two decades after that first image, an astronaut aboard the International Space Station photographs this coast. The palm-shaped islands stand out from orbit. |
| H4 | 20 | 97 | So how do you build land where there was only sea? And what happened to the plans that came next? |
| A1 | 47 | 225 | This is Dubai, in the United Arab Emirates, on the shore of the Persian Gulf. A coastline seems like the one thing on a map that nobody gets to choose. Dubai put that idea to the test. To see how, we go back to the year 2000. |

Why this passage: it is the real opening of the film, has a geographic reveal (empty sea, finished palm, orbit view, then the whole coast) and needs only verified NASA images that already exist locally (World of Change 2000 and 2003, the ISS photograph, palm2.jpg 2006). It avoids the diagrams that are not built yet (B3, B4) and the map flight that needs data we do not have (A1 is shown as the rotated ASTER coast, not a map).

## Expected duration
About 46-54 s of speech (695 characters at roughly 13-15 characters per second for this voice); the real figure comes only from the audio. Video target 55-60 s: about 3 s lead-in plus the narration plus 3-4 s closing hold. If the audio runs under 50 s the closing hold absorbs it; if over 56 s the hold shrinks. This is an estimate, not a timing.

## Existing audio and word timings
None for Dubai. No wav, mp3 or voice.json exists in the repository or the session. EP001's narration is a different script and its files are not in this checkout. No free narration can be reused. Local offline speech tools were not found (espeak, piper, flite, festival, pico2wave), and in any case they would not give an English male documentary narrator.

## ElevenLabs configuration
yt-voice provider `elevenlabs`, narrator Adam (`pNInz6obpgDQGcFmaJgB`, source default), model `eleven_multilingual_v2` (the yt-voice default), language en, authentication through the egress proxy (no key in the session). A free dry run of yt-voice on this exact text returned `status: confirm_required`, 695 characters, 1 chunk, 1 request. yt-voice requests per-character alignment and keeps word timings only when they match the text exactly; otherwise it records none and never estimates.

## Credits
Expected cost: 695 characters, which is about 695 credits at ElevenLabs' published rate of 1 credit per character for Multilingual v2 (Flash and Turbo models cost half). **Balance not verified**: the proxy-injected key is restricted; `GET /v1/user/subscription` returned 401 `missing_permissions: user_read` and `GET /v1/models` returned 401 `missing_permissions: models_read`. So neither the remaining credits nor the model's cost factor could be confirmed without generating audio. A failure for lack of credit is possible but would be reported by the API, and yt-voice stores nothing on failure. yt-voice's `--max-chars` default (3000) is above the request.

## Visual plan checked against narration and evidence (uses Motion v2 components)
| scene | visual | evidence | status |
|---|---|---|---|
| H1 | WoC 2000 crop of the empty palm site, ticker 2000 | claims 2, 21 | verified, local |
| H2 | WoC 2003 crop, same framing, ticker 2003; hard cut | claims 3, 21 | verified, local |
| H3 | ISS photo, move between the two palm islands, ticker 2022, markers on the two palms | claims 27, 28 | verified, local |
| H4 | palm2 close-up of Palm Jumeirah, slow push (the v2 opening) | claims 12, 26 | verified, local |
| A1 | pull-out to the full rotated ASTER coast, plate "Dubai coast, UAE, Persian Gulf, September 2006" | claims 29, 26 | verified, local |
| close | cut back to the 2000 frame as the line "we go back to the year 2000" ends | claim 2 | verified, local |
All sources are displayed rotated 90 degrees for consistency and say so. Images are separate stills joined by labelled cuts and dissolves; no registration is claimed.

## Gate
Approval needed: voice this passage with ElevenLabs (Adam, eleven_multilingual_v2), 695 characters, about 695 credits, one request. Nothing else is paid. If you would rather not spend, the alternative is a silent re-render with on-screen captions only, which would not satisfy the narration and timing brief.
