# EP008 pre-render QC (2026-10-30)

| check | result | evidence |
|---|---|---|
| Facts match primary sources | **PASS with 3 open items** | every scene lists fact ids; `beats.py` fails if an id is missing from research/RESEARCH.md. Open: S1 (Feb 27 reasons, secondary), S2 ("next summer", secondary, attributed), s12 "days vs hours from home" (own explanation, not a NASA statement) — owner decides wording; S1 re-read against `research/primary-texts/` after the fetch run |
| Script vs visuals | PASS | every shot asset exists in research/media.json (21 assets/graphics); docking shown only as labelled ILLUSTRATION; Artemis II photos always labelled "ARTEMIS II PHOTO" |
| Cover promise = first seconds | PASS 7/8 (as intended) | packages/qc_thumbnail_hook_prerender.json — yt-qc `check_thumbnail_hook` on the edit map: subject at 0.0 s; `thumbnail_hook_match` fails until the owner confirms on a real draft |
| Image quality ≥ 1080p | **NOT VERIFIED** | no original downloaded (NASA hosts blocked from this session). Known risks: srb-nosecones and orion-joined are portrait (large 1280x1920, wp copy 768x1024) — used as vertical pans with blurred fill, never as full-frame 16:9 crops unless ~orig ≥ 1920 px wide. `ep008-fetch.yml` marks files < 1920 px as SMALL |
| Narration ↔ edit sync | PASS (estimate) | edit_map.json derived from word counts at 150 wpm; re-derived from voice timing after recording, as EP007 |
| No long static scenes | PASS | photo framings ≤ 6 s (re-frame resets inserted), animated diagram beats ≤ 9 s; 66 shots in ~5:50 |
| Hook rules | PASS | no logo/greeting/intro; 6 information events and 3 compositions in the first 10 s (packages/FIRST_20S.md) |
| Length | **WARN** | 858 words ≈ 5:50 at 150 wpm (EP007: similar pace gave 6:17 with Adam). Target 6-8 min; not padded on purpose — owner decides whether to add a verified beat |
| Rights | PASS (pending files) | NASA public-domain stills only; Blue Origin/SpaceX artwork excluded even when hosted by NASA; no astronaut portraits; no legible insignia on the cover |
| Skill tests | PASS | yt-qc, yt-plan, yt-viral tests: 46 passed |

Not run yet (needs a render): `qc.py --profile long`, `thumbcheck.py` on the cover, the visual comparison with the four published covers.
