# EP002 Dubai - final 1080p30 master (stable storage, not a code branch, do not merge into main)
Status: TECHNICALLY_VALID / VISUALLY_REVIEWED only. NOT USER_APPROVED. Nothing is published.
Join: `cat ep002/final/parts/EP002_Dubai_1080p30.mp4.part* > EP002_Dubai_1080p30.mp4`, then compare with the "(joined)" SHA-256 in `ep002/final/SHA256SUMS`.
Specs: 1920x1080, 30 fps, H.264 yuv420p ~4.0 Mb/s, AAC 192 k 48 kHz stereo, 522.733 s, -16.2 LUFS. Captions: ep002.srt / ep002.vtt (word-timed, 228 cues). Narration audio and the paid TTS cache are on `media/ep002-dubai-audio`.

## v2 (2026-10-13): hook atmosphere added, later QA fixes
`ep002/final_v2/` = master v2 (1080p30, 4 parts + joined SHA-256 in SHA256SUMS) and `EP002_Dubai_ipad_540p_v2.mp4` (960x540, 29 MB, review copy). v2 mixes a locally synthesised low drone under the first 6 s (narration untouched, integer-sum verified) and contains the label/clipping fixes (C1, D1, D5, E1, E5, B3). `ep002/final/` (v1, silent cold open) is kept unchanged. Status: TECHNICALLY_VALID / VISUALLY_REVIEWED; NOT USER_APPROVED; not published.

## v3 (2026-10-13): release-gate fixes
`ep002/final_v3/` = master v3 (1080p30, 3 parts + joined SHA-256 in SHA256SUMS) and the iPad review copy. v3 = v2 audio (hook atmosphere, narration untouched) + legibility/overlap/static-hold fixes (callout backing pills, D2, H2, C6, D5, A3, E5 header, 12 px disclosure chips). v1 (`final/`) and v2 (`final_v2/`) are kept unchanged as backups. Status: TECHNICALLY_VALID / VISUALLY_REVIEWED; NOT USER_APPROVED; not published.
