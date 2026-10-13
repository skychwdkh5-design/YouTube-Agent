# EP002 Dubai - release review v2 (2026-10-13)
Status: **TECHNICALLY_VALID and VISUALLY_REVIEWED (contact sheets + automated scans). NOT USER_APPROVED. Not published.** v1 (silent cold open) is kept unchanged in `media/ep002-dubai-final/ep002/final/`.
Master v2: `media/ep002-dubai-final/ep002/final_v2/` (4 parts, joined SHA-256 `6561c7e30406973dce5ad7492464abb010ebd74c3af8f61435a5143c30d6a56c`). iPad review copy: `EP002_Dubai_ipad_540p_v2.mp4`, 960x540, H.264 High + AAC-LC 64 k, 30,310,741 bytes, SHA-256 `0e2a6607...43c23d5fa43570c644d0`.
## Hook atmosphere (AUDIO_HOOK_STATUS: implemented, measured, NOT auditioned)
Local synthesis (`preview/atmosphere.py`, seed 2026): 41-165 Hz partials + <= 160 Hz noise bed, swell from silence (peak 2.9 s), release to silence by 6.2 s; momentary peak -28 LUFS (gain -10.9 dB); added after narration normalisation. Narration untouched: integer sum, `mix - atmosphere == narration` exactly; identical to the normalised narration after 5.85 s. Final programme -16.1 LUFS, LRA 2.9, peak -4.5 dBFS, 0 clipped samples. The agent cannot hear audio: whether the drone is tasteful is a listening decision for the director.
## yt-qc (profile long, expected 522.8 s): PASS
All 20 hard checks pass (streams, 1920x1080, 30 fps, h264/aac, duration 522.733 s = 15,682 frames, full decode, black frames 0, **audio_starts 0.77 s**). Warnings: freezes 2.6 s (credits hold at the end); loudness (warn belongs to the Shorts range). **Documented interpretation:** `audio_starts` measures the first audio above -40 dB, so it passes because of the atmosphere; the narration still starts at 3.35 s (first RMS onset 3.475 s). Not declared as "speech starts within 1 s".
## Additional checks
- 29/29 scenes present; every segment duration equals the plan within 40 ms; sum 522.733 s.
- Subtitles vs speaker: 228 cues, 0 overlaps; cue words equal the locked narration word for word; 159 cue starts after pauses matched to audio onsets: mean +0.020 s, p95 0.057 s, max 0.125 s.
- Cut-off text audit (`qa_text_bounds.py`, whole film, 0.5 s steps): **no text outside the frame** after fixes. Before: C1, D1, B3, D5, E5/E6, E1 had clipped or off-frame labels (fixed: callout clamp, off-frame landmark skip, dark stroke, D5 tag position, E1 label fade).
- Frame scans: blackdetect 0; freezedetect 2 s: only the final credits hold; 29 difference spikes, all explained (20 scene boundaries, H2->H3 slide, C1 declared move, C6 split, declared cuts in E2 and E5).
- First 45 s and last 30 s reviewed frame by frame on contact sheets (hook sequence, titles, E5, credits card held to the last frame, no fade to black).
- Pronunciation (no local recogniser available): provider durations per syllable are plausible for ASTER (0.43-0.70 s, two-syllable word, not spelled out), Jumeirah (0.45-0.67), Deira (0.30-0.56), Nikon 0.48; vibroflot 0.91 s is slow (+1.5 sd) but not garbled. **This is not a listening check; no auditory verification was performed.**
## Budget
ElevenLabs additional credits this iteration: **0** (no request made; cache untouched). Total EP002 TTS: one pass, 6,998 characters (~6,998 credits assumed).
## Remaining weaknesses
B3/B4 low-motion diagrams; D2 date label crowds the subtitle; E1 filmstrip tiles are cut by the frame edge by design (labels fade); phone/device readability and continuous playback unreviewed.
