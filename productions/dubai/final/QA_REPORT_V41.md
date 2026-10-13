# EP002 final master v4.1 - QA (2026-10-13)
Status: TECHNICALLY_VALID. Hook v4.1 = USER_APPROVED (user, 2026-10-13); the full film is NOT yet user-approved. Not published.
- File: 1920x1080, 30 fps, h264/aac, 516.77 s, 272 MB; SHA-256 504412b34925974517eea4b34462c616e86237996b5521fa24297cb53adfe7d8 (media/ep002-dubai-final, ep002/final_v41/). iPad copy 854x480, 28.6 MB (27.3 MiB), SHA-256 379943807960509ada5e1134655672ad5a6fd5f96fd3108f1ccf3d704685ed32.
- yt-qc (profile long): PASS (warn only: loudness -16.1 LUFS vs the Shorts range; skips: no manifest). yt_qc_v41.json.
- VOICE_START 0.129 s (RMS onset in the mux; word 0 at 0.00 s). Hook audio identical to the approved preview (first 34 s, sample-exact). Hook video segments H1-H4 are the approved files.
- Audio: -16.1 LUFS, LRA 2.8; speech identical to narration.mp3 in 483 of 512 speech seconds, the other 29 are scene-boundary seconds (20 ms fades); no repeats/gaps. No black frames; no freeze >= 2 s (one 1.5 s hold at the end of C5).
- Captions: 228 cues, no overlaps, caption words == locked vo_text (1225 = 1225), last cue ends 515.25 s.
- Text: no text outside the frame (all scenes, 0.5 s steps); contrast audit (qa_contrast.py) - confirmed defects fixed: dates and labels on bright imagery (E2, E4, E5, C1, C3, A3 strip, E6 credits, E2 captions, C5/C6 captions) and B4 camera that cut the panel titles/collided with the illustration pill.
- Remaining risks (not fixed, below the confirmed-defect bar): near-static stretches of 1.5-2.6 s on text cards (C3 tail, C5 end, D2/D5 around 388-399 s, E1 ~434 s, A3/B1 ~102 s) - text must be read, slow push only; qa_contrast still flags B4 muted labels and D5 year chips by its own method (visual check: legible); full film not watched frame by frame (contact sheets/proofs of changed scenes only); no listening check.
- Credits used: 0 (cached Adam narration).
