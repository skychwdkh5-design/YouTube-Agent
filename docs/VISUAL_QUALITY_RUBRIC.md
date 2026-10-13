# Visual quality rubric and gates
Status levels: TECHNICALLY_VALID → VISUALLY_REVIEWED → USER_APPROVED (user only). Passing gates 1 ≠ quality.
## Gate 1 — automated (TECHNICALLY_VALID)
| check | method |
|---|---|
| 1920×1080, 30 fps, H.264+AAC, duration = audio | ffprobe; `/yt-qc` |
| full decode, no errors | `ffmpeg -v error -i f -f null -` |
| audio: integrated −16…−14 LUFS, true peak ≤ −1 dBTP | ebur128 (`engine/av.py ebur`) |
| subtitles: no overlap, ≤2 lines, ≤42 chars, lead ≤0.1 s | `av.check_cues` |
| missing assets | manifest vs files |
| black frames | `blackdetect` (d=0.1, pix_th=0.1); allow only declared fades |
| text clipping/safe margin | per-frame bbox of drawn text inside 96 px margin; UIREG collisions = 0 |
| transition continuity | frame pair around each cut: no blank, subject centroid shift as declared |
| overlay validity | each traced overlay has validation score ≥0.7 recorded; each map overlay has `rms_m` |
| attribution | every source visible as chip/credit at least once |
| script lock | narration hash == SCRIPT_LOCK hash; no text edits |
| motion presence | mean absolute frame difference per second; flag any 3 s with near-zero change unless a declared hold |
## Gate 2 — visual review (VISUALLY_REVIEWED): the reviewer actually watches frames at ≥4 fps contact sheets
Score 0–3 each, write one sentence of evidence: opening impact · production quality · geography clarity ·
camera · transitions · typography · variety · density · sync · engagement. Pass: no 0, mean ≥2.
Say plainly what was NOT checked (e.g. real-time playback feel).
## Gate 3 — USER_APPROVED: only an explicit user statement.
## Report wording
Never write "premium", "cinematic" or "approved" about work below USER_APPROVED. State level reached.
