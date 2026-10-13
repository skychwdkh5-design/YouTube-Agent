# Troubleshooting (symptom -> cause -> verified fix)
All entries **[VERIFIED]** in this repo unless tagged.
| symptom | cause | fix |
|---|---|---|
| shell dies with exit 144 after `pkill -f ...` | the pattern matches the shell running the command | `pgrep -f "^<exact start of command>"` and `kill` the PIDs; or let jobs finish |
| `rm` of relative globs denied / blocked | permission policy | write to a new output dir; do not clean up with rm |
| `ValueError: box offset can't be negative` in `Image.resize(box=...)` | crop rect leaves the source (rounding, or a panel so narrow that the box height exceeds the image) | `kit.view` snaps < 2 px; `scenes_v6.fit` limits box to 98 % of the source; clamp rects with `clampr` |
| `TypeError: float object cannot be interpreted as an integer` in `ImageDraw.ellipse/line` | float `width` | pass `width=2` (int); the SDraw/SS wrappers round widths |
| a scene mp4 looks frozen after a failed batch | a parallel build aborted and left a truncated mp4 | `build_final.py` writes `.part.mp4` then renames; delete stale parts, rerun (resumable) |
| blackdetect flags 0.3-0.5 s at the start of card scenes | dark navy card with nothing drawn yet | put a label/graphic in frame 0 and enter by dissolve (`with_entry`) |
| freezedetect flags 2 s windows on card scenes | static card between events | add a slow push or a moving element; accept only declared holds |
| viewer shows 910x512 / 30 fps for a 960x540 / 24 fps file | the chat/file viewer re-encodes | compare SHA-256 of the original; never claim identity of a viewed copy |
| `qa` reports false discontinuities | resampling the preview to 30 fps | use native-fps checks (`qa_preview.py`) |
| Cesium capture takes 90 s+ per frame | global-layer `minimumLevel` / force-render loop | use `run_frames_fast.js` (3 workers, DSF 1.5-2: about 11 min for 372 frames) |
| Cesium tile server race on `.ct` | non-atomic write | atomic write order (fixed in `tools/cesium_proof/server.py`) |
| git stop hook: untracked/uncommitted files | tile cache, new code | ignore caches (`tools/cesium_proof/.gitignore`, `voice/cache/`), commit code; media goes to `media/*` branches |
| `yt-voice` run fails after a paid chunk | no persistent chunk cache (before 2026-10-13) | use `--cache-dir`; a rerun pays only missing chunks |
| `--max-chars` over limit although text is right | blank-line paragraphs add characters | single newlines (EP002: 6,998 vs 7,025) |
| outlines include coast arcs / cloud specks | threshold mask includes all land near the landmark | restrict radius; use the difference mask (`new_land`); raise threshold (ASTER 2006: 110) |
| hook labels overlap captions | big label placed in the bottom 70 px | main labels at y = 0.13-0.21 H or 0.40 H; captions own the bottom |
