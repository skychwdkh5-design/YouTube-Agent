# EP009 final release — status 2026-11-03 23:5x (STOPPED at blocker, nothing paid was run)
Owner authorised: paid Adam voice for Long + 2 Shorts, in the order GOES rights → voice → assembly → QC. No upload, no schedule change.

## Step 1 — GOES-13 (M03): NOT CLOSED
- No explicit reuse licence found for `noaa_goes13_outbreak_2011.mp4` (see `GOES_RIGHTS_MEMO.md`); NOAA page thanks CIMSS for "some of the imagery" without saying which. Absence of a prohibition is not treated as permission.
- Documentary replacement with clear terms = NASA Earth Observatory GOES stills/animation (image 50347, "NASA image courtesy the GOES Project Science team. Animation by Jesse Allen"). Not in the repo; `assets.science.nasa.gov` is refused by this session's egress proxy (connect_rejected) → cannot download here. Needed from owner: upload `unitedstates_goe_2011117_lrg.jpg` (and optionally `unitedstates_goe_2011118_sd.mov`) to `media_original/`, or written NOAA/NASA confirmation for the MP4.
- Scenes affected (re-render only these): Long ≈ 28.7–46 s, 79.9–123 s, 357–372 s; Short 02 ≈ 0–22 s.

## Step 2 — ElevenLabs Adam: NOT RUN
- Gate 1 is open, and `api.elevenlabs.io` is also refused by the egress proxy in this session (connect_rejected), so the paid call cannot be made from here even with approval. Needed: allow `api.elevenlabs.io` for this session (claude.ai → Settings → Capabilities → allowed domains) or run `voice.py` elsewhere.
- Free dry-run of `.claude/skills/yt-voice/voice.py` (nothing sent): Adam `pNInz6obpgDQGcFmaJgB`, model `eleven_multilingual_v2`, mp3_44100_128. Characters: Long 4,748 (2 chunks; needs `--max-chars 5000`, default is 3000), Short 01 343, Short 02 398 → **5,489 total**. Texts: `voiceover_final/*.txt`. Generate each once, keep `*.voice.json` (word timings, sha256) for the retime.
- After the voice exists: retime pass (captions, scene cuts and counters are keyed to Flite sentence times), re-run QC (1920×1080/30, 1080×1920, H.264+AAC, loudness/peaks, black/freeze, captions, rights, cover↔first 3 s).
