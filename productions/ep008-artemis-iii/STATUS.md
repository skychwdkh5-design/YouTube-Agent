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

## Draft status (2026-10-31)
- Owner approved the hook direction (18:08) with changes, all applied: larger Earth-orbit diagram, zoomed upper-stage →
  spacer swap, timeline cut to two dates (Feb 27 / Oct 23, 2026), NASA con-ops graphic shown as large sequential fragments
  with the narrated item lit (graphics.conops, never above native resolution), frame 1 text "LAND ON THE MOON" (no specific
  landing point is confirmed for that photo).
- Mission chips on every picture: blue Artemis II (flown) / gold Artemis III plan / white Artemis III hardware.
- Full draft: `draft.py` (shots anchored to sentences of the temporary voice) → `draft/EP008_draft_v1.mp4` (git-ignored, sent
  in chat) + `.srt` + `.timeline.json`. Temporary voice: Kokoro am_michael via `tts_temp.py` (all scenes, ~6:55).
- 5 NASA clips used: v1 launch, v2 Orion window, v3 splashdown (1920x1012 with blurred fill, not upscaled), v4 booster
  stacking, v5 RS-25. Stills: 13 originals + 2 `~large` (srb-nosecones portrait shown height-fit over blurred fill).
- Not started: ElevenLabs Adam (needs owner OK after the draft), Shorts, final cover gate, publishing.

## Draft v2 (2026-10-31 20:20, owner edit notes of 20:04)
- Text lists → visuals: yearly-landing calendar, "faster" bars, crew around an Orion silhouette (names only), training and
  extra-test icon tiles, suit-mass-simulator cutaway. Quotes → short lower thirds over picture (Isaacman, Parsons).
- Recognisable vehicles (own drawings, labelled ILLUSTRATION): Orion (CM + ESM + wings), Blue Moon test article (tall
  lander, side port by the cabin), Starship (52 m, flaps, nose port). Docking shown in phases APPROACH → CONTACT → DOCKED.
- DAYS/HOURS comparison removed: no NASA source for a return time from LEO (RESEARCH.md §4d); s12 shortened by ~15 s.
- draft/EP008_draft_v2.mp4 6:42, QC: technical PASS; warn length (<8 min target) and one 3.9 s freeze; thumbnail_hook_match
  waits for the owner. Changed-fragment reel: draft/EP008_v2_changes.mp4 (git-ignored, sent in chat).

## Next session, in order
1. Owner reviews draft v1. Fixes → re-render with `python3 draft.py --media <dir> --render --confirm` (or `--scenes sNN` for parts).
2. After owner approval of the draft: ElevenLabs Adam via yt-voice (--confirm), re-time draft.py on Adam's timing, final render,
   two Shorts (packages/SHORTS.md), SRT, cover gate (section 5), QC report.
