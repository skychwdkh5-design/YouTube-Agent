# EP002 creative preview — status 2026-10-10 (V2)
Current build: V2 (this folder), silent, 960x540, 24 fps, 538.0 s, 28 scenes, VO text unchanged (hash in SCRIPT_LOCK). Details, per-scene QA, audits and remaining weaknesses: `QA_REPORT_V2.md`. Previous build (`8f217e3`, 12 fps) is kept in git history; before/after stills in `qa_v2/compare/`.
Build: `python3 build_preview.py OUT --a1 CESIUM_A1_DIR` (Cesium A1 frames from `tools/cesium_proof`, function `setFrameA1v2`, 372 frames). Audits: `landmarks.py`, `qa_rects.py`, `audit_labels.py`, `qa_preview.py` (see QA_REPORT_V2.md).
Not done / blockers: no narration audio (paid TTS requires explicit approval), caption timing is estimated, no 4K render. Status vocabulary: VISUALLY_REVIEWED only.
