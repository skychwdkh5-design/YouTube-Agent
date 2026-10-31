# EP008 pre-render QC (2026-10-30)

| check | result | evidence |
|---|---|---|
| Facts match primary sources | **PASS, 1 owner item** | every scene lists fact ids (F01-F30); NASA texts saved in research/primary-texts/ and re-read: secondary claims S1/S2 were NOT in NASA text and were removed. Open: s12 "hours vs days from home" is an explanation, not a NASA quote (NEXORA uses the same line) — owner decides |
| Script vs visuals | PASS | every shot asset exists in research/media.json (21 assets/graphics); docking shown only as labelled ILLUSTRATION; Artemis II photos always labelled "ARTEMIS II PHOTO" |
| Cover promise = first seconds | PASS 7/8 (as intended) | packages/qc_thumbnail_hook_prerender.json — yt-qc `check_thumbnail_hook` on the edit map: subject at 0.0 s; `thumbnail_hook_match` fails until the owner confirms on a real draft |
| Image quality ≥ 1080p | **PASS 13/15, 2 pending** | GitHub run 41011659925: 13 originals 3648-6720 px (research/fetch_manifest_run1.tsv). srb-nosecones and solar-array `~orig` = 403; `~large` requested (run 2). Booster photo is portrait → vertical pan with blurred fill only |
| Narration ↔ edit sync | PASS (estimate) | edit_map.json derived from word counts at 150 wpm; re-derived from voice timing after recording, as EP007 |
| No long static scenes | PASS | photo framings ≤ 6 s (re-frame resets inserted), animated diagram beats ≤ 9 s; 78 shots in ~6:47 |
| Hook rules | PASS | no logo/greeting/intro; 6 information events and 3 compositions in the first 10 s (packages/FIRST_20S.md) |
| Length | PASS | 1,003 words ≈ 6:47 at 150 wpm; added beats are NASA-verified (F27-F30), not padding |
| Rights | PASS (pending files) | NASA public-domain stills only; Blue Origin/SpaceX artwork excluded even when hosted by NASA; no astronaut portraits; no legible insignia on the cover |
| Skill tests | PASS | yt-qc, yt-plan, yt-viral tests: 46 passed |

Not run yet (needs a render): `qc.py --profile long`, `thumbcheck.py` on the cover, the visual comparison with the four published covers.
