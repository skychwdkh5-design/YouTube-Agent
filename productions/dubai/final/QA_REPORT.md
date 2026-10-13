# EP002 Dubai - final QA report (2026-10-13)
Status: **TECHNICALLY_VALID with one declared yt-qc exception; VISUALLY_REVIEWED on contact sheets and frame scans; NOT USER_APPROVED. Nothing is published.**
Master: `media/ep002-dubai-final` (4 parts of 90 MB + SHA256SUMS). Joined SHA-256 `c934b5da431b02335321ce35bfd1a627cfe417ad0af3ee347ec0ab778bd2e9ba`, 274,561,114 bytes.
## Specs
1920x1080, 30 fps, H.264 yuv420p (x264 crf 19, ~4.0 Mb/s), AAC 192 kbps 48 kHz stereo, 522.733 s = 15,682 frames, narration Adam / eleven_multilingual_v2 (515.251 s), silent 3.0 s cold open, 29 scenes.
## yt-qc (profile long, expected 522.8 s): FAIL on one item only
Pass: container, streams, resolution, fps, codecs, pixel format, duration vs plan, streams aligned, frame count, **full decode**, long-form window, **black frames 0**.
Warn: freezes 2.6 s (credits hold at the end, by design); loudness -16.1 (warn belongs to the Shorts range).
**Fail: audio_starts 3.482 s (limit 1.0 s)** - deliberate: the V6 hook opens on 3 s of silent real imagery; narration starts at 3.35 s. Decision for the director: keep, or add an original synthetic swell under the cold open (no music/stock; not done without approval).
## Audio
Loudnorm two-pass: input -17.98 LUFS / TP -1.27 -> output -16.22 LUFS, TP -1.50 dBTP, LRA 2.9 LU (`loudnorm_measure.json`). Segments cut inside pauses with 20 ms fades; silence inserted only for the H4 title hold (+1.8 s).
## Sync (sync.py; word-level event clock + smooth camera clock)
- All 1,225 words timed by the provider; scene map consistent (1,225 = 1,225).
- Event onset measured on the final MP4 (H1 label "NO ISLAND HERE" vs word "There"): label starts to appear at the word start, 0.0-0.15 s after (fade-in), before it nothing (frame difference flat).
- Sentence-only warp (rejected): mean cue error 0.33 s, max 2.5 s; word-level smoothing gave 0.2-3x speed pulses (rejected).
- Scene real/estimated duration ratios 0.69-1.08 (E6 1.76 slow credits).
## Captions
`ep002.srt` / `ep002.vtt`: 228 cues, 0 overlaps, max 63 chars, max 5.64 s, last cue ends 520.4 s; joined cue words equal the locked narration word for word (checked). Burned in (bottom safe zone) and delivered as files.
## Motion / continuity scans (96x54 grey frame difference)
15,682 frames; 29 spikes > 30, all explained: 20 scene boundaries, the 0.5 s slide H2->H3, declared fast move in C1 (232 s), C6 panel split (327 s), declared hard cuts in E2 (444.9 s) and E5 (499 s). No unexplained jump. D5 static card fixed (slow zoom + anatomy card); freezedetect 2 s: only the final credits hold.
## Visual review (agent, contact sheets of 29 mid-scene frames + hook frames)
Defects found and fixed in this pass: near-black empty cards at B4/D5/E1/E6 starts (lifted card background, content in frame 0, dissolve entries, credits held to the last frame); B3 label clipped at the right edge; D5 empty axis between anatomy card and thumbnails. Remaining known weaknesses: B3/B4 diagrams are low-motion illustrations; D2 date label and subtitle crowd slightly; first-frame A1 label "DUBAI" is small.
## Geographic honesty
No scale bars/distances/coordinates; 2000->2003 cross-dissolve on a measured shared grid (<= 1 px); ISS photo labelled "not satellite imagery"; all outlines labelled traced/UI; The World not described as visible in the ISS frame; no claims after 2022.
## NOT verified (cannot be done by the agent)
Listening to the narration (pronunciation of ASTER, Jumeirah, vibroflot, Deira unchecked); continuous playback review; device/phone readability test; YouTube processing. USER_APPROVED needs the director.
## Budget
ElevenLabs: one pass, 6,998 characters (~6,998 credits, assumed 1 credit/char), cache stored; no retries. Other spend: none (free tools only).
