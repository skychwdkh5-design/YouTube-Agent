# Episode 001: source audit, round 3 (2026-10-08): reviewer corrections and Landsat check

Adds to `source_audit_round2.md`. The narration is **not** approved and the fact check is **not complete**.

## A. Reviewer-approved corrections applied (script.md v0.2)

| ID | Before | After | Evidence |
|---|---|---|---|
| P20 (cold open) | "It has happened more than 230 times before." | "Geological records suggest it has happened more than 230 times before." | Larrasoaña et al. 2013 (round 2) |
| P20 (ACT 2) | "Sediment records suggest the Sahara has turned green more than 230 times in the last 8 million years." | "Geological records, mostly marine and desert sediments, point to more than 230 green Sahara periods in the last 8 million years. That's a reconstruction, not 230 events anyone observed." | same; sapropels are the markers |
| N1 (ACT 3) | "...then sinks over the subtropics, warming and drying as it falls. [pending] That sinking air is a big reason rain clouds struggle to form here." | "Near the equator, warm, moist air rises, and forms clouds and rain. High up, it flows toward the poles, then sinks around 30 degrees latitude, by then dry. NASA notes that descending air inhibits cloud formation, which is why clouds are rare and deserts are common at those latitudes." | NASA EO Cloudy Earth; NASA EO Southeastern Australia |
| L3 (ACT 4) | "New lakes appeared in the late 1990s. NASA measured them at up to about 1,450 square kilometers ... By 2012 they had shrunk by roughly 80 percent. By 2021, they were full again." | "In NASA's photographs, the lakes are full in 2002. By 2012, they had mostly dried up, as the Nile's flow dropped. In 2021, after floods upstream, they held more water than ever before." | NASA EO 149334 |
| S18 (ACT 7) | "...launched the Great Green Wall, aiming to restore 100 million hectares of land by 2030." | Two separate statements: the COP21 pledge of 100 Mha (S18), and the PA-GGW's own 25 Mha target (S18b); then the preliminary 4 Mha count (S19). | UNCCD GGW page; UNCCD 2020 report p.22 |
| S4 (ACT 6) | "about 182 million tons of Saharan dust blow out over the Atlantic every year" | "about 182 million tons of dust a year are carried past the Sahara's western edge, and out over the Atlantic. Roughly 28 million tons of it settle on the Amazon basin." | NASA SVS 4273 |
| R1 (ACT 6) | "One of the biggest sources is here: the Bodélé ... Green the Sahara, and much of that dust could disappear." | The Bodélé is "one of the world's most prolific dust sources", but "may not be the main supplier to the Amazon"; a newer analysis points to El Djouf (S7b). The effect of a greener Sahara on Amazon phosphorus is stated as "a hypothesis" that "no study has modeled" (G14). | NASA EO 146011, 147816 |

New IDs: **S7b** (El Djouf, NASA EO reporting) and **S18b** (PA-GGW 25 Mha). The unverified claims carry ⚠UNVERIFIED / ⛔BLOCKED marks in the script. L3 sentence uses "floods upstream" for NASA's "record-breaking floods in Sudan" (2020) and "approached record levels" (2021).

Storyboard scenes changed: 2, 3, 14, 16, 18, 19, 21, 29, 30, 31, 34.

## B. Landsat check (free metadata plus small previews only)

**Authentication: PASS.** `usgs_m2m.py auth` returned `authenticated: true`; scene search, `options`, `metadata` and one 0.9 MB download all worked. The order was removed from the USGS queue (`cleanup: removed`). No credential was printed or stored.

Method: M2M `scene-search` over TM (1984-2011), ETM+ (1999-2024) and OLI (2013-2026) Collection 2 Level-1. Reduced-resolution browse JPEGs (30-50 KB each, 16 scenes) were viewed as contact sheets in `landsat/previews/`. One full-resolution natural-colour browse (Landsat 9, 2024-01-05) was downloaded (914,635 bytes) for a measurement. Nothing else was downloaded. Candidate scenes: `landsat/scene_candidates.json`.

### East Oweinat (L1), path/row 177044
- Search found 400 TM, 438 ETM+ and 829 OLI scenes (counts include neighbouring path/rows and all cloud values). Earliest TM scene: **LT05_L1TP_177044_19840826_20200918_02_T1** (26 Aug 1984, cloud 0%). Earliest MSS scene not searched (yt-geo has no MSS support).
- Seen in the previews: no fields in 1984 or Jan 1990; the first tiny green patches at the southern edge in **Jan 2000** (LT05 20000111); clear field clusters in **Jan 2010** (LT05 20100122); large clusters in **Jan 2016** (LC08 20160107) and **Jan 2024** (LC09 20240105, `LC91770442024005LGN00`).
- Pivot size: on the 2024 scene 88 isolated circles had a median equivalent diameter of 29 px, or **about 0.87 km** at 30 m per pixel (10th-90th percentile 27-31 px). This measurement assumes 30 m pixels and counts only strongly green pixels, so the true figure is likely close to 0.9 km. "Roughly a kilometer" is acceptable; "about 0.9 km" is exact.
- The imagery supports the script's before/after, with two qualifications: it supports "in a 1984 Landsat image", not "in the earliest Landsat images"; and the 1984/1990 judgement comes from a ~180 m/pixel preview (small fields would be missed). NASA EO says agriculture began in the 1980s. Check the 1984 scene at full resolution before lock.
- **L1 status: NEEDS_REVISION (wording).**

### Toshka Lakes (L3), path/rows 176044 and 175044
- Search found 814 TM, 705 ETM+ and 829 OLI scenes (both paths; all cloud values).
- Seen in the previews: no lakes on **1997-02-12**, **1998-01-30** and **1999-01-01** (LT05_L1TP_176044_19990101_20200908_02_T1); two lake groups on **2000-01-12** (LE07_L1TP_176044_20000112_20200918_02_T1). So in this footprint the lakes first appear between 1 Jan 1999 and 12 Jan 2000.
- **2002-01-09** (LT05 20020109): lakes full. **2012-01-13** (LE07, striped by the scan-line corrector failure): one small lake and remnants. **2018-01-05** (LC08): a small lake and damp remnants. **2021-11-13** (LC08 20211113): lakes full, the eastern lakes running past the scene's edge.
- NASA's own photographs are dated 11 Sep 2002, 21 Jun 2012 and 30 Nov 2021. Better matches: adjacent path 175044 scenes LT05 20020729 and LE07 20211130 (listed, not previewed).
- The imagery supports the qualitative sequence the revised script uses (full 2002, mostly dry 2012, full again 2021). It does **not** measure area. A 1,450 km² or "-80%" claim needs a water mask (yt-geo) on full-resolution scenes of both paths; those downloads need approval.
- **L3 status: VERIFIED for the revised wording** (NASA EO 149334, round 2) with Landsat consistent; the removed numbers stay unverified.

## C. Not done / open
- Full-resolution scenes were not downloaded, so no yt-geo co-registered stack or water mask exists.
- Landsat 5 TM scene LE07 2011-12-12 is ETM+ (striped); a clean late-2011 Landsat 5 scene was not previewed.
- G4, G17, G18 and P10 remain BLOCKED; 27 claims remain ⚠UNVERIFIED (list in `claims.md`).
