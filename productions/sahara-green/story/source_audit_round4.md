# Episode 001: source audit, round 4 (2026-10-08)

Adds to rounds 2 and 3. The narration is **not** approved and not locked.

## A. L1 correction (reviewer-approved)

| Before | After |
|---|---|
| "In the earliest Landsat images, it's bare desert. Today, it's covered in green circles, each roughly a kilometer across..." | "In a 1984 Landsat image, this area is almost entirely barren. Today, it's covered in green circles, each roughly a kilometer across, watered by rotating sprinkler arms." |

Evidence: `LT05_L1TP_177044_19840826_20200918_02_T1` (full-resolution natural-colour browse, 672,676 bytes) shows an even, featureless surface in the area where the 2024 fields lie; no circles and no regular geometry. This is a visual judgement. An automatic green-pixel count on the 1984 image is **not** used, because that image has an overall greenish colour cast. Scale caveat: a browse image shows 30 m pixels, so single small plots would be missed. Pivot diameter (median 0.87 km, 88 circles, Landsat 9, 2024-01-05) stays **provisional** until measured on original band data (not downloaded: the Level-1 bundle is 128 MB for TM and larger for OLI). Storyboard scenes 6, 18 and 35 now name the 1984 and 2024 scenes. L3 keeps NASA's 2002 / 2012 / 2021 chronology and no lake areas.

## B. Landsat downloads (round 4)

Eight full-resolution natural-colour browse JPEGs (0.7-4.6 MB each, about 15 MB in total); every order was removed from the USGS queue. No Level-1 bundle and no band file was downloaded. Repository copies are 1400 px wide, in `landsat/previews/`. IDs, entity IDs and footprints: `landsat/scene_candidates.json` (`round4_downloads`).

| Place | Scene | Date | Cloud | Finding |
|---|---|---|---|---|
| East Oweinat | LT05_L1TP_177044_19840826 (path/row 177044) | 1984-08-26 | 0 | barren |
| East Oweinat | LC09_L1TP_177044_20240105 | 2024-01-05 | 0 | many pivot circles |
| Toshka | LT05_L1TP_176044_19990101 | 1999-01-01 | 0 | no lakes |
| Toshka | LT05_L1TP_176044_20020109 | 2002-01-09 | 0 | lakes full (western and middle groups) |
| Toshka | LE07_L1TP_176044_20120113 | 2012-01-13 | 0 | one small lake plus remnants; SLC-off stripes |
| Toshka | LC08_L1TP_176044_20211113 | 2021-11-13 | 0 | lakes full |
| Toshka (east) | LT05_L1TP_175044_20020729 | 2002-07-29 | 0 | eastern lake and Lake Nasser in frame |
| Toshka (east) | LE07_L1TP_175044_20211130 | 2021-11-30 | 0 | eastern lakes full, new lakes and green fields; SLC-off stripes |

Coverage: path 176044 spans 29.0-31.3°E, so the eastern Toshka lakes lie outside it; path 175044 spans 30.5-32.7°E and holds them. A single-scene wipe would cut the 2002 and 2021 lakes; use both paths. NASA's photographs are dated 11 Sep 2002, 21 Jun 2012 and 30 Nov 2021; the Landsat dates above are the nearest clean scenes, not the same days.

## C. Claims checked in round 4 (15)

Access: academic hosts (science.org, nature.com, pnas.org, link.springer.com, Wiley/AGU, PMC, PubMed, Europe PMC, arXiv, repositories, Unpaywall, OpenAlex) refuse every request in this environment, and searches turned up no copy on an accessible host (PLOS, NASA, UNCCD). Statuses below rest only on full texts that could be read: Larrasoaña et al. 2013 (PLOS ONE), dust-record paper "Intensity of African Humid Periods Estimated from Saharan Dust Fluxes" (PLOS ONE 12(1): e0170989), and NASA Earth Observatory pages 41425 (Ounianga) and 153475 (Sebkha el Melah).

### NEEDS_REVISION (3)

| ID | Original wording | What the readable sources say | Type | Recommended wording (not applied; reviewer decides) |
|---|---|---|---|---|
| P2 | "Between roughly 11,000 and 5,000 years ago, much of the Sahara was grassland and savanna..." | Larrasoaña et al. 2013: "Holocene GSP (~11 to 6 ka)"; dated wet sediments cluster at 7.5-8.5 ka. NASA EO 41425: the African Humid Period was "about 14,800 to 5,500 years ago". The 5,000 figure belongs to Tierney et al. 2017 (not readable). | Reconstruction | "Between roughly 11,000 and 6,000 years ago" matches the one readable primary study; "roughly 11,000 to 5,500" matches NASA. Keep "roughly". |
| P3 | "Earth's orbit has a slow wobble, a cycle of roughly 21,000 years. ... sunnier northern summers ... the monsoon pushed its rains far north" | Mechanism supported: "Astronomically forced insolation changes have driven monsoon dynamics and recurrent humid episodes" (abstract); "eccentricity modulation of precession (and hence of insolation)"; "progressive northward expansion ... of monsoonal precipitation". NASA EO 153475: "generally accepted ... Milankovitch cycles were key drivers". The number 21,000 appears in neither. | Theory + reconstruction | Keep the mechanism. Either cite the 21,000-year precession figure to a source or say "a cycle of about twenty thousand years" only after it is sourced. Note the monsoon peak lags the insolation peak by 1.5-3 kyr. |
| P19 | "At any one place, the end came fairly fast. But it came later the farther south you go. ... The leading explanation today..." | Larrasoaña: "ended within 2-3 kyr"; "progressive (2-3 kyr) northward expansion and southward retraction of monsoonal precipitation at the onset and termination". That supports a gradual southward retreat in the Sahara, not "later the farther south". The e0170989 record finds the end abrupt after sapropels S3-S5 (gradient 0.8-1.1 per kyr over 1.5-2 kyr) but gradual after S6 and S1 (0.15-0.25 per kyr). The label "leading explanation" is Shanahan et al. 2015 (not readable). | Reconstruction | Say "One reconstruction finds the rains retreated south over two to three thousand years" and drop "leading explanation" until Shanahan 2015 is read. |

### BLOCKED (12)

| ID | Original study | Why blocked |
|---|---|---|
| P5 | Tierney et al. 2017, Sci. Adv. 3:e1601503 | science.org and PMC unreachable. **Risk:** NASA EO 153475 (Oct 2024) says climate models "struggle to reproduce the rainfall required to fill as many Saharan lakes" as geologists infer, so "models only match with plants and less dust" may overstate agreement. |
| P17 | deMenocal et al. 2000, Quat. Sci. Rev. 19:347 | ScienceDirect unreachable. The existence of an "abrupt versus gradual" debate is confirmed by e0170989 (introduction). |
| P18 | Kröpelin et al. 2008, Science 320:765 | science.org unreachable. NASA EO 41425 supports only that pollen from the older Ounianga lake shows a wooded-grassland savanna and that vegetation zones now lie 300 km farther south; it does not name Lake Yoa or describe a "layer-by-layer" drying record. |
| G1, G2 | Ornstein, Aleinov & Rind 2009, Climatic Change 97:409 | Springer challenge page; NASA GISS unreachable. |
| G5, G6 | Kemena et al. 2018, Climate Dynamics 50:4561 | Springer and GEOMAR repository unreachable. The −6 °C, +267 mm/yr and ~26% figures stay unverified. |
| G8 | Li et al. 2018, Science 361:1019 | science.org and PubMed unreachable. |
| G10, G11 | Lu, Pausata et al. 2021, GRL 48 | Wiley returns a Cloudflare challenge. |
| G20 | Rohatyn et al. 2022, Science 377:1436 | science.org unreachable. |
| P24 | Pausata et al. 2017, PNAS 114:6221 | pnas.org and PMC unreachable. |

No claim could be marked VERIFIED this round and none REJECTED. G4, G17, G18 and P10 (round 2) stay BLOCKED.

## D. Hook precision

Opening lines scored with `.claude/skills/yt-script/hookscore.py` (a rough tool: it separates bad hooks from real ones, not a prediction of retention).

| Version | Score | Precision |
|---|---|---|
| v0.1 "It has happened more than 230 times before." | 63 WORKABLE | Overstates: reads as 230 observed events |
| **v0.2 (current) "Geological records suggest it has happened more than 230 times before."** | 52 WEAK | Matches the evidence type: a reconstruction, with "suggest" |
| Proposed "Geological records reveal more than 230 ancient humid periods across North Africa." | 44 WEAK | See below |
| "Sediment records suggest it has happened over 230 times before." | 56 | Shorter, same precision |

Trade-off of the proposed line. Gains: "humid periods" is the neutral term for what the proxies show, and it avoids "green" meaning a uniform savanna. Costs: (1) "reveal" is stronger than the evidence, since the count is inferred from Mediterranean sapropel layers used as markers ("identification of over 230 GSPs"; Larrasoaña et al. 2013), so "suggest" or "point to" is more exact; (2) "across North Africa" claims a spatial pattern the paper does not state for each period; (3) it drops the word "green" and the link to "turn the Sahara green", so "it" no longer has a referent and the hook loses its image; (4) it scored lowest (44), mostly on length. The source paper itself uses "green Sahara periods" for savanna expansion "throughout most of the desert", so "green" is not imprecise. **Recommendation: keep the v0.2 line or use the shorter "Sediment records suggest it has happened over 230 times before."** The line was not replaced.

## E. Counts

15 claims checked this round: 0 VERIFIED, 3 NEEDS_REVISION (P2, P3, P19), 12 BLOCKED, 0 REJECTED. L1 closed by reviewer approval (wording). Still ⚠ UNVERIFIED: S1, S2, S3, P11, P12, P14, P8, L4, S12, S13, S14, P23.
