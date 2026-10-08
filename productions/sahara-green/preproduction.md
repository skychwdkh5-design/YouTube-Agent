# Episode 001 "What If We Turned the Sahara Desert Green?": preproduction package v0.1

- Phase 1 only. Nothing is voiced, rendered or published.
- No imagery has been downloaded.
- No paid API calls have been made.

| File | Contents |
|---|---|
| `script.md` | Narration draft v0.6: 1,759 spoken words (v0.1 had 1,374 by the same count method), about 12.1 minutes at 145 wpm |
| `story/claims.md` | Fact-check ledger |
| `storyboard.md` | 37 scenes, plus the visual novelty plan |

## Hooks (yt-script `hookscore.py`)

| Rank | Hook | Score | Formula |
|---|---|---|---|
| 1 | "You could turn the Sahara green. It has happened over 230 times before. But this time, what you'd change thousands of miles away is the part nobody plans for." | **71 WORKABLE** | Unclassified |
| 2 | "If you planted a forest across the Sahara, the models say the rain would come. But something you'd never expect changes thousands of miles away." | **55 WORKABLE** | The Impossible Claim |

- The script uses hook 1 with one softening: "nobody plans for" becomes "the part that's easy to miss". Scientists do model these effects, so "nobody plans for" would overstate the case.
- 13 hooks were tried in total. The first 10 scored WEAK (35–44).

## Landsat locations

Constraints:
- yt-geo works from one scene per date, so a view can be at most about 170 km wide.
- Datasets: TM 1984–2011, ETM+ only until 31 May 2003, OLI 2013 onward.
- No MSS (1972–83). See B6.
- Every scene must be checked in /yt-satellite before it is used ("no scene, no satellite claim").

| ID | Location | Centre (approx.) | UTM | Width | Dates to search | Visible at 30 m | Story role | Source |
|---|---|---|---|---|---|---|---|---|
| L1 | East Oweinat, Egypt | 22.56 N, 28.44 E | 35N | 8–60 km | earliest TM (1984–87), ~2000 ETM+, ~2010 TM, 2016 OLI, 2024/25 OLI | Yes (pivots ~1 km) | Main "greening today" location: wipe and timelapse | NASA EO 89820; ESA 2019 |
| L2 | Kufra, Libya | 24.18 N, 23.28 E (town) | 34N | 30–60 km | 1 recent OLI (optional early TM) | Yes | Second fossil-water oasis | NASA EO 152356 |
| L3 | Toshka Lakes, Egypt | ~23.1 N, 30.9 E (sources disagree: 23.42 N, 30.60 E) | 36N | 100–150 km | before the lakes (TM ≤1997), 2002 ETM+, Nov 2011 TM or 2013 OLI, Nov 2021 OLI/L9 | Yes | Rise, fall and refill of the lakes | NASA EO 149334 |
| L4 | Lakes of Ounianga / Lake Yoa, Chad | 19.06 N, 20.51 E (UNESCO) | 34N | 15–60 km | 1–2 OLI scenes | Yes | Living remnant of the green Sahara | UNESCO 1400; NASA EO 41425 |
| L5 | Bodélé Depression, Chad | 16.96 N, 17.78 E | 33N | 50–150 km | 1–2 OLI (optionally a dust-event day) | Yes for the lakebed; plumes need MODIS | Dust source and ancient Mega-Chad floor | NASA EO 146011, 147816 |
| L6 | Tassili n'Ajjer, Algeria | 25.5 N, 9.0 E (UNESCO) | 32N | 50–150 km | 1 OLI | Yes for the landscape; the rock art is not visible | Opening shot; people of the green Sahara | UNESCO 179 |
| L7 | Gilf Kebir / Wadi Sura, Egypt (optional) | 23.44 N, 25.84 E; Wadi Sura ~23.55 N, 25.28 E | 35N | 30–100 km | 1 OLI | Landscape only | Transition shot (ACT 3) | U. Cologne Wadi Sura; weakest sourcing |
| R1 | Lake Chad (reserve) | 13.0 N, 14.0 E | 33N | ≤150 km | 1987 TM vs 2023 OLI | Yes | Sahel context, only with both halves of S15/S16 | NASA EO 91291 |
| R2 | Richat Structure (reserve) | 21.12 N, 11.39 W | 29N | 50–70 km | 1 OLI | Yes | Beauty shot only, no climate claim | NASA EO "Eyeing the Richat Structure" |

**Not suitable for Landsat:** Great Green Wall and Niger restoration sites. Tree cover there is scattered and not visible in true colour at 30 m; only about a third of Senegal sites showed detectable change (Meroni et al. 2017). Use charts instead.

## Visuals the current pipeline cannot make

| Visual | Why not | Alternative (licence) | Pipeline change needed (later) |
|---|---|---|---|
| Whole-Sahara or Africa map; Sahara vs lower-48 size comparison | Larger than one Landsat scene; no mosaics | NASA Blue Marble NG (public domain, credit NASA EO); or a vector map from Natural Earth (public domain) | Continental base-map graphic type in yt-graphics, or non-grid still assets in v3 |
| Dust plume across the Atlantic; CALIPSO dust | MODIS/VIIRS/CALIPSO scale | NASA SVS 11775 / 4273 (credit per item; check each page's terms) | Non-grid still or video asset |
| Lake Mega-Chad outline; 1960s Lake Chad extent | Reconstruction, or larger than one view | Original yt-graphics map drawn from published outlines (needs a CC-BY or public-domain shapefile) | Vector overlay on a base map |
| Sahel NDVI greening map; Great Green Wall belt map | Continental data product | NASA/NOAA NDVI products; original map | Base map + raster overlay |
| Cyclone tracks (Pausata 2017) | Paper figure (copyright) | Original schematic only, no track data | — |
| Buried "radar rivers" | Shuttle radar, not Landsat | USGS McCauley 1982 (public domain; check figure credits) | — |
| Rock-art close-ups | Ground photography | Licensed or public-domain photos (none found yet) | — |
| Precession animation | No animated graphics | Build-step diagram (supported) | Animated graphics (later) |

Workaround, not a feature: a NASA still pre-sized to 1920x1080 could enter a v3 timeline as a `graphic` asset with its credit. It would play as a static full frame with no camera move, so keep it to 6 s or less.

## Monetization and licensing checklist

All items were checked from search snippets of the official pages. Re-check them before the first upload.

- [ ] **YPP ad tier:** 1,000 subscribers plus either 4,000 valid public long-form watch hours (12 months) or 10M Shorts views (90 days); AdSense; no strikes. The 2027 increase to 8,000 hours / 20M views reported by the press is **unverified**. Plan as if the bar doubles.
- [ ] **Inauthentic content** (renamed July 2025). Avoid templated, interchangeable videos. Keep:
  - a unique script per episode;
  - our own Landsat analysis and original graphics;
  - a varied structure.
  
  Archive scripts, sources and project files for a possible review.
- [ ] **Altered/synthetic disclosure:**
  - A realistic AI-generated scene requires disclosure.
  - Whether a generic premade AI narrator voice (ElevenLabs "Adam") requires it is **unresolved**. Recommendation: tick the box. It does not affect monetization (unverified).
  - Landsat and NASA imagery and our charts need no disclosure.
- [ ] **ElevenLabs:**
  - Final narration only on an active **paid** plan. The free tier carries no commercial licence.
  - No Beta/alpha models for the final audio.
  - Keep invoices and generation dates.
  - Check the "Adam" voice page for any notice.
- [ ] **Landsat:** public domain. Credit "Landsat [n] image courtesy of the U.S. Geological Survey" on screen and in the description, with scene IDs and dates.
- [ ] **NASA:**
  - Media are generally not copyrighted. Credit NASA.
  - No NASA logos or insignia, and no implied endorsement.
  - Third-party items on NASA sites are excluded.
  - Check each SVS item's credit and terms.
- [ ] **Scientific figures:**
  - Do not copy journal figures. Redraw from the numbers in our own design and cite the source.
  - CC-BY figures are fine with attribution.
  - CC-BY-NC is **not** allowed, because the channel is monetized.
- [ ] **Inter font:** SIL OFL 1.1. Video use is allowed. Do not redistribute the font files.
- [ ] **Music:** none in this episode. If added later, use the YouTube Audio Library with exact attribution text and keep licence screenshots.
- [ ] **Climate monetization policy:** the episode does not deny climate change and reports model results as models. Keep it that way.
- [ ] **Advertiser-friendly:** no graphic disaster imagery. Thumbnail and title must be answered by the video (misleading-metadata policy).
- [ ] **Audience:** set "Not made for kids".
- [ ] **Description:** full source list (`story/claims.md`) and Landsat scene IDs.

## Benchmark audit (read-only; no files changed)

| Benchmark | File | SHA-256 (actual file) | Bytes | render.json | production.json |
|---|---|---|---|---|---|
| Lake Mead | `productions/lake-mead/lake-mead_short.mp4` | `235bc6f0b44f0d144c5acee9b1a59cd84588eafee41e348b8bc7694639fc4813` | 30,415,749 | match | `render.sha256` match (older schema, no `video` block) |
| Kīlauea | `productions/kilauea-2018/kilauea-2018_short.mp4` | `86a56a54e3eff1d77581b416d359c4fe7c3c2a881198034e03d14b9ad07057a8` | 15,470,379 | match | `video.sha256` match |
| Wadi As-Sirhan | `productions/sirhan/sirhan_short.mp4` | `5544096049738930cbd592072bd2bf305b97232926be0b283cca8e0403285205` | 18,045,482 | match | `video.sha256` match |

Discrepancies:

1. **Hashes swapped in Claude's chat reports.** The final reports for PR #12 and the PR #13 merge labelled `86a56a54…` as Lake Mead and `235bc6f0…` as Kīlauea. The table above is correct. The `sha256sum` output was listed alphabetically by folder (kilauea-2018 before lake-mead) and then labelled in the wrong order.
   - The files, `render.json`, `production.json` and the PR #12/#13 descriptions are correct. The PR descriptions name only the Sirhan hash.
2. **No benchmark registry in the repo.** The benchmark status and the hashes exist only in chat and in each `render.json`. Recommendation for a later PR: add `productions/BENCHMARKS.md` (or JSON) listing name → path → sha256 → bytes → accepted date.
3. **Stale stage fields.**
   - kilauea-2018 and sirhan `production.json` still say `"stage": "rendered_awaiting_human_review"` and `"render": "not done"`, although both were rendered and accepted as benchmarks.
   - Lake Mead's `production.json` uses an older schema (no `stage`/`video` block; title "MVP v0.1 Short").
4. **Naming is inconsistent:**

   | Name | Folder | File prefix |
   |---|---|---|
   | Kīlauea | `kilauea-2018` | `kilauea-2018_short` |
   | Wadi As-Sirhan | `sirhan` | `sirhan_short` |
   | Lake Mead | `lake-mead` | `lake-mead_short` |

   Not an error, but a registry should hold the display names.

## Production blockers

| # | Blocker | Blocks | Fix |
|---|---|---|---|
| B1 | **Updated 2026-10-08 (round 8):** the narration's claims were re-read from full sources (rounds 2-8); no ⛔ or ⚠ claim remains in script v0.6. Original text: All sources were verified from search snippets only. | Ledger lock (factcheck.lock) | Remaining checks: Kemena journal version, Landsat scene-by-scene review of the final graphics, reviewer sign-off. |
| B2 | **Resolved (round 8):** N1, S1, S3, G17, G18, G19, S21, G4 and the other source gaps were fixed or removed; S2 and the model claims G8, G10, G11, G20 were removed from the episode. | ACT 3, cold-open numbers, ACT 4, ACT 5 | None for the narration. |
| B3 | **Update 2026-10-08:** scenes searched and previewed (see `landsat/scene_candidates.json`, `story/source_audit_round3.md`); L1 wording and L3 scene choice pending review. Original text: Landsat scenes not searched or downloaded yet. "Bare desert in the earliest images" (L1) and the Toshka year sequence (L3) are SCENE-CHECK lines. | ACT 4, close | /yt-satellite search, then browse review, then yt-geo stacks. This is free, but downloads await approval. |
| B4 | v3 cannot place non-grid stills (NASA Blue Marble, SVS dust) except as a static full-frame `graphic`. | Scenes 4 and 29 (fallbacks exist) | Use the fallbacks now. A feature later. |
| B5 | No continental base map or vector overlays (Mega-Chad outline, Sahara-vs-US, GGW belt, Sahel NDVI). | Scenes 4, 8 and 34 visual richness | Fallbacks are in the storyboard. Feature later. |
| B6 | No MSS (1972–83) dataset in yt-geo/yt-satellite. | Pre-1984 "before" images (Lake Chad 1973) | Not needed for this script. |
| B7 | Loudness: no timing-safe limiter. The last long integration measured −17.9 LUFS. | The final mix target | Known open item; not fixed in this phase. |
| B8 | ElevenLabs paid plan not active (by design). | TTS | Activate before narration. |
| B9 | ~9:20 of narration means a long render (estimated 20–40 min single-threaded) and 50+ shots to author. | Production time | Plan only. |

## Ready for script review

Yes, as a draft (script v0.6). B1 and B2 are cleared for the narration. Before a lock: confirm the Kemena journal version (G5, G6, G6b), review the final Landsat graphics scene by scene (B3), and get reviewer sign-off.
