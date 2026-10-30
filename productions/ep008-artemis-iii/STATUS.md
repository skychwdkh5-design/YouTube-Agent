# EP008 status — Artemis III (2026-10-30)

Owner decision 2026-10-30: Artemis III moves from NEXORA to Orbital Atlas; NEXORA no longer produces it.
Episode number EP008: free after checking every branch (production/*, media/*, publish/*, publish-data queue):
highest used is EP007.

## Where things are
- `nexora-import/` — NEXORA research copied unchanged (youtube-ops, research/runs/2026-10-30-growth-demo; see PROVENANCE.txt). NEXORA had no script, storyboard or downloaded files on any branch.
- `research/RESEARCH.md` — confirmed facts F01-F23, secondary/pending S1-S3, never-say list, corrections vs NEXORA.
- `research/media.json` — assets, credits, rights, cover use, needed resolution, excluded material.
- `research/TOPIC_SCORE.md`, `topics.json` — OA rescoring (3.83 GO-CANDIDATE); `OUTLIERS_external_vidiq.md` — NEXORA vidIQ data through OA outliers.py, labelled external.
- `beats.py` → `script/SCRIPT.md`, `script/EDIT_MAP.md`, `script/edit_map.json`, `script/narration.txt`.
- `packages/thumbnail_hook.json` (A chosen, B/C kept), `packages/FIRST_20S.md`, `packages/SHORTS.md`, `QC.md`.
- `fetch_list.txt`, `fetch_pages.txt`, `fetch_video_queries.txt` + `.github/workflows/ep008-fetch.yml` (this branch only, same pattern as EP007): runner downloads NASA originals to DRAFT release `ep008-originals`, commits `fetch_manifest.tsv`, `research/primary-texts/`, `research/video_candidates.json`.

## Not done / not allowed yet
- No voice (ElevenLabs/Adam only after owner approves script and draft). No upload, no queue entry, no schedule change.
- No vidIQ calls (0 credits). NEXORA untouched (read only).

## Next session, in order
1. Read `fetch_manifest.tsv` (sizes; SMALL = below 1920 px) and `research/primary-texts/` — re-check S1 against the Feb 27 release text; fix RESEARCH.md if anything differs.
2. Pick 3-5 NASA video clips from `research/video_candidates.json` (Artemis II launch/splashdown, booster stacking), add to a fetch list.
3. Draw d-orbit-vs-moon and d-sls-stack (yt-graphics); render the first 20 s with a free temporary voice (Kokoro, as EP007); owner reviews cover A vs first frames.
4. After owner approval of the script: full draft render → yt-qc --profile long → thumbcheck → owner.
