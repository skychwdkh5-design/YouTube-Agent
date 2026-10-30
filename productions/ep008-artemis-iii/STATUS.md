# EP008 status — Artemis III (2026-10-30)

Owner decision 2026-10-30: Artemis III moves from NEXORA to Orbital Atlas; NEXORA no longer produces it.
Episode number EP008: free after checking every branch (production/*, media/*, publish/*, publish-data queue):
highest used is EP007.

## Where things are
- `nexora-import/` — NEXORA research copied unchanged (youtube-ops, research/runs/2026-10-30-growth-demo; PROVENANCE.txt) and, received at 13:03, NEXORA's later preproduction from branch production/artemis3 (`nexora-import/production-artemis3/`: script, edit plan, motion spec, hook board). Reconciled claim by claim in research/RESEARCH.md §4b; its verified extras are in the EP008 script.
- `research/RESEARCH.md` — confirmed facts F01-F30, removed secondary claims S1-S3, never-say list, corrections vs NEXORA.
- `research/media.json` — assets, credits, rights, cover use, needed resolution, excluded material.
- `research/TOPIC_SCORE.md`, `topics.json` — OA rescoring (3.83 GO-CANDIDATE); `OUTLIERS_external_vidiq.md` — NEXORA vidIQ data through OA outliers.py, labelled external.
- `beats.py` → `script/SCRIPT.md`, `script/EDIT_MAP.md`, `script/edit_map.json`, `script/narration.txt`.
- `packages/thumbnail_hook.json` (A chosen, B/C kept), `packages/FIRST_20S.md`, `packages/SHORTS.md`, `QC.md`.
- `fetch_list.txt`, `fetch_pages.txt`, `fetch_video_queries.txt` + `.github/workflows/ep008-fetch.yml` (this branch only, same pattern as EP007): runner downloads NASA originals to DRAFT release `ep008-originals`, commits `fetch_manifest.tsv`, `research/primary-texts/`, `research/video_candidates.json`.

## Not done / not allowed yet
- No voice (ElevenLabs/Adam only after owner approves script and draft). No upload, no queue entry, no schedule change.
- No vidIQ calls (0 credits). NEXORA untouched (read only).

## Next session, in order
1. Fetch run 1 done: 13/15 stills downloaded (research/fetch_manifest_run1.tsv), NASA texts saved and re-read (S1/S2 removed). Run 2 (this push) requests `~large` for srb-nosecones and solar-array — read fetch_manifest.tsv.
2. Pick 3-5 NASA video clips from `research/video_candidates.json` (Artemis II launch/splashdown, booster stacking), add to a fetch list.
3. Reuse NEXORA's motion_spec.json/hook20 builder where it fits (do not redo); draw d-orbit-vs-moon and d-sls-stack (yt-graphics); render the first 20 s with a free temporary voice (Kokoro, as EP007); owner reviews cover A vs first frames.
4. After owner approval of the script: full draft render → yt-qc --profile long → thumbcheck → owner.
