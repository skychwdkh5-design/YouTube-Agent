# Reference-based visual QA checklist (preview frames and motion)

Targets come from `docs/references/REFERENCE_01_ANALYSIS.md`, `REFERENCE_02_ANALYSIS.md`, `ORBITALATLAS_REFERENCE_STYLE.md`. Mechanics only; never copy branding, footage or distinctive graphics.
Passing this list is VISUALLY_REVIEWED at best. USER_APPROVED needs the user's explicit word.

Method: contact sheet at 4 fps + 6–8 full-size frames (start, mid-move, arrival, overlay peak) + motion check (frame difference per second). Score each item PASS / PARTIAL / FAIL with the frame or time as evidence. Any FAIL in A–C blocks the proof from being shown as "close to the reference".

| # | item | pass criterion |
|---|---|---|
| A1 | continuous camera | eased moves 0.5–1.5 s pan, 2–3 s zoom, no jump cuts inside a location |
| A2 | spatial truth | imagery georegistered, coastlines/borders from data, no invented geometry |
| A3 | imagery detail at final zoom | landmarks readable at the closest frame; no blocky tiles/seams/black patches |
| A4 | depth cue | perspective/tilt or parallax; not a flat plane unless declared |
| B1 | pacing | new visual event every 1–3 s; no static hold > 3 s without animation |
| B2 | labels | on the named thing, appear when camera ≥ 70 % arrived, uppercase letter-spaced, readable (contrast ≥ 4.5:1), inside safe margin |
| B3 | highlights | fill + outline draw-on, one colour per beat |
| B4 | motion blur | only on fast moves; text/strokes stay sharp |
| C1 | layer honesty | stylised map vs photograph chips; no map lines on photos |
| C2 | claims | every label/number backed by evidence in the research file |
| D1 | typography | one family, one size per tier, captions 2–4 words bottom centre |
| D2 | no artefacts | no black frames, half skyboxes, tile pop-in, aliasing shimmer |
| E1 | technical | `orbitalatlas.qa` + `/yt-qc` pass (necessary, not sufficient) |

Report format: `STATUS: TECHNICALLY_VALID | VISUALLY_REVIEWED` + table of FAIL/PARTIAL items with frames + one-line verdict "below / near / at reference" with evidence. Never write "cinematic" or "premium" without the user's approval.
