# EP008 pre-render QC (2026-10-30)

| check | result | evidence |
|---|---|---|
| Facts match primary sources | **PASS, 1 owner item** | every scene lists fact ids (F01-F30); NASA texts saved in research/primary-texts/ and re-read: secondary claims S1/S2 were NOT in NASA text and were removed. Open: s12 "hours vs days from home" is an explanation, not a NASA quote (NEXORA uses the same line) — owner decides |
| Script vs visuals | PASS | every shot asset exists in research/media.json (21 assets/graphics); docking shown only as labelled ILLUSTRATION; Artemis II photos always labelled "ARTEMIS II PHOTO" |
| Cover promise = first seconds | PASS 7/8 (as intended) | packages/qc_thumbnail_hook_prerender.json — yt-qc `check_thumbnail_hook` on the edit map: subject at 0.0 s; `thumbnail_hook_match` fails until the owner confirms on a real draft |
| Image quality ≥ 1080p | **PASS 13/15, 2 pending** | GitHub run 41011659925: 13 originals 3648-6720 px (research/fetch_manifest_run1.tsv). srb-nosecones and solar-array `~orig` = 403; `~large` requested (run 2). Booster photo is portrait → vertical pan with blurred fill only |
| Narration ↔ edit sync | PASS (estimate) | edit_map.json derived from word counts at 150 wpm; re-derived from voice timing after recording, as EP007 |
| No long static scenes | PASS | photo framings ≤ 6 s (re-frame resets inserted), animated diagram beats ≤ 9 s; 78 shots in ~6:47 |
| Hook rules | PASS | no logo/greeting/intro; 6 information events and 3 compositions in the first 10 s (packages/FIRST_20S.md) |
| Length | PASS | 1,003 words ≈ 6:47 at 150 wpm; added beats are NASA-verified (F27-F30), not padding |
| Rights | PASS (pending files) | NASA public-domain stills only; Blue Origin/SpaceX artwork excluded even when hosted by NASA; no astronaut portraits; no legible insignia on the cover |
| Skill tests | PASS | yt-qc, yt-plan, yt-viral tests: 46 passed |

Not run yet (needs a render): `qc.py --profile long`, `thumbcheck.py` on the cover, the visual comparison with the four published covers.

## Final v1 with Adam (2026-11-01, owner approval 14:36 ICT)
| check | result | evidence |
|---|---|---|
| Narration | Adam (ElevenLabs, pNInz6obpgDQGcFmaJgB), 15 scenes, 5,800 chars, final script v2 (DAYS/HOURS removed) | adam/voice_manifest.txt (s04 first stopped by the 700-char guard before sending; charged once) |
| Words vs script | PASS | ElevenLabs alignment equals the script word for word in all 15 scenes (adam_timing.py asserts it) |
| Pronunciation / truncation | PASS | independent faster-whisper small.en: adam/transcript_check.json — names (Bresnik, Parmitano, Douglas, Rubio, Artemis, Orion, Starship, Blue Origin) heard correctly; last words of every scene heard; differences are number formatting only + 3 ASR merges |
| Scene edges | PASS | ≥ 0.29 s of silence after the last word in every scene, tails −86…−98 dB; 5 ms fade-in on hard starts |
| Edit sync | PASS | every shot anchored to Adam's sentence times (voice_adam/timing.json) |
| Captions | PASS | final/EP008_en.srt: 175 cues from Adam's word timings, ≤ 42 chars, no overlaps, none < 0.6 s, no cue crosses a sentence end |
| File | PASS | final/EP008_final_1080p.mp4: H.264 High@4.1 1920x1080 30 fps yuv420p + AAC-LC 48 kHz stereo, 6:32.6, 101.2 MB, faststart; −15.5 LUFS integrated, true peak −4.0 dBFS; sha256 in final/SHA256SUMS |
| yt-qc --profile long | technical PASS; warn length 6:33 (< 8 min target), warn one 3.4 s freeze; `thumbnail_hook_match` = owner confirmation pending | packages/qc_final_v1.json |
| Cover | thumbcheck PASS (objective part) | final/EP008_cover_A.jpg (= covers/EP008_cover_A.jpg) |
Final MP4 is not in Git (media rule) and could not be uploaded to the draft release from this session (proxy accepts JSON only); delivered in chat. Not published, not queued.
