# Episode 001 storyboard: draft v0.7 (16:9, aligned with SCRIPT LOCK v1.1, profile `long`)

Round 2 (2026-10-08): scenes 2, 3, 14, 16, 21, 29, 30, 31 and 34 were aligned with the reviewer-approved corrections in `script.md` v0.2 (P20, N1, L3, R1/S4, S18). Narration is now 1,778 spoken words (SCRIPT LOCK v1.1), about 12.3 minutes at 145 wpm. Round 9 changed scenes 2, 10, 13, 14, 25, 31, 32 and 34 and added scene 25b. v0.6 removed scenes 26, 27 and 28 (kept as struck-through placeholders so numbering stays stable); scenes 4, 5, 7, 8, 10, 11, 19, 22, 29, 32, 33 and 36 were rewritten. Round 7 changed scenes 23, 24, new 24b, 25 and 32 (Ornstein and Pausata corrections); the per-scene times below are from v0.1 and must be re-timed after the voice pass. Landsat scene candidates are in `landsat/scene_candidates.json`.

## How to read this

- **Timing** is estimated from the narration at about 145 words per minute. Total: ~9:20, plus a 4-6 s outro.
- **Narration** quotes the opening words of each line from `script.md`.

### Visual families

| Family | What it shows |
|---|---|
| `orbit_wide` | Wide Landsat establishing shots |
| `oasis_lakes` | Lakes and wetlands from orbit |
| `rock_plateau` | Rock-art landscapes |
| `pivot_fields` | Centre-pivot fields |
| `lake_change` | Toshka |
| `dust_source` | Bodélé |
| `process_diagram` | yt-graphics diagram / flow / circulation |
| `data_chart` | bar / line |
| `number_callout` | Large numbers on their own |
| `annotated_map` | yt-graphics geo / compare |
| `external_still` | NASA public-domain still. **Not supported in v3 yet; see Blocker B4.** |

### Pacing targets (yt-render long)

- At least 5 composition resets per minute.
- At least 2 family transitions per minute.
- No family on screen longer than 30 s.
- No static hold longer than 8 s.

### Credits

| Shot type | On-screen credit |
|---|---|
| Landsat shots | "Landsat [n] · USGS" |
| Graphics | "Graphic: [channel] · [source]" (the source line inside the graphic carries the citation) |

---

## COLD OPEN (0:00-0:46)

| # | ~Time | Narration (first words) | Family | Visual | On-screen labels | Source on screen |
|---|---|---|---|---|---|---|
| 1 | 0:00-0:06 | "You could turn the Sahara green." | orbit_wide | Tassili n'Ajjer plateau (L6), slow push-in, 2024 OLI | — | Landsat 8 · USGS |
| 2 | 0:06-0:12 | "Geological records suggest it has happened more than 230 times before." | number_callout | callout "230+" with the subtitle "reconstructed green Sahara periods, last 8 million years" | 230+ RECONSTRUCTED GREEN PERIODS | Larrasoaña et al. 2013 |
| 3 | 0:12-0:18 | "…what you'd change thousands of miles away…" | annotated_map | Bodélé (L5) geo graphic, with a plain arrow pointing west labelled "dust crosses the Atlantic" (no claim that the Bodélé is the source of the Amazon's dust; see R1) | THOUSANDS OF MILES AWAY | Landsat 8 · USGS |
| 4 | 0:18-0:30 | "The Sahara is the world's largest non-polar desert." | external_still → fallback number_callout | Preferred: NASA Blue Marble Africa (B4). Fallback: text callout "World's largest non-polar desert". **No area number and no comparison with the United States** (S1 revised, S2 removed). | WORLD'S LARGEST NON-POLAR DESERT | NASA Earth Observatory (A Deluge for the Sahara) |
| 5 | 0:30-0:36 | "In some areas, it gets just a few inches of rain…" | number_callout | Callout "a few inches (tens of millimeters) of rain a year, in some areas". No "<100 mm" threshold, no "most of the Sahara". | IN SOME AREAS | NASA Earth Observatory (A Deluge for the Sahara) |
| 6 | 0:36-0:46 | "So could we really cover it in green?" | pivot_fields | East Oweinat (L1), wipe from the 1984 scene (LT05_L1TP_177044_19840826) to the 2024 scene (LC09_L1TP_177044_20240105) | GREEN, IN THE DESERT, TODAY | Landsat 5 / 9 · USGS |

## ACT 1: The Green Sahara (0:46-1:59)

| # | ~Time | Narration (first words) | Family | Visual | On-screen labels | Source on screen |
|---|---|---|---|---|---|---|
| 7 | 0:46-0:58 | "According to one reconstruction of the last green period…" | data_chart | A line/timeline graphic from 15,000 years ago to today with a shaded band from 11,000 to 6,000 | ONE RECONSTRUCTION: GREEN SAHARA ≈11,000–6,000 YEARS AGO (OTHER RECORDS DIFFER) | Larrasoaña et al. 2013 |
| 8 | 0:58-1:08 | "In north-central Africa, about 7,000 years ago, a lake called Mega-Chad…" | annotated_map | Bodélé (L5) wide view with the callout "floor of Lake Mega-Chad". The lake outline is not drawn (B5). Text card: "LARGER THAN ALL THE GREAT LAKES COMBINED · ~7,000 YEARS AGO". **No km² figure.** | MEGA-CHAD · LARGER THAN ALL THE GREAT LAKES COMBINED (NASA) | Landsat 8 · USGS; NASA Earth Observatory (Bodélé Dust) |
| 9 | 1:08-1:20 | "At a site called Gobero…" | number_callout → rock_plateau | callout "~200 burials" (insert), then Tassili n'Ajjer canyons (L6) | GOBERO, NIGER · TASSILI N'AJJER: 15,000+ ETCHINGS AND ILLUSTRATIONS | Sereno et al. 2008; NASA Earth Observatory (A Plateau of Chasms) |
| 10 | 1:20-1:32 | "How much wetter?" | number_callout | Card: "~100 mm/yr at the core of the NE Sahara; ~450 mm/yr near 18°N" with the subtitle "one reconstruction, last green period; rough estimates, no error bars". | RECONSTRUCTION · ROUGH ESTIMATES | Larrasoaña et al. 2013 |
| 11 | 1:32-1:59 | "And a piece of that world is still here." | oasis_lakes | Ounianga (L4): wide view of both groups at 60 km, push to Ounianga Serir at 15 km. Text card: "POLLEN FROM THE ORIGINAL LAKE: WOODED GRASSLAND · SUCH PLANTS NOW GROW ~300 KM (~190 MI) FARTHER SOUTH". **No Lake Yoa callout and no "drying record" claim.** | LAKES OF OUNIANGA | Landsat 8 · USGS; NASA Earth Observatory (Ounianga Lakes) |

## ACT 2: What flips the switch (1:59-3:12)

| # | ~Time | Narration (first words) | Family | Visual | On-screen labels | Source on screen |
|---|---|---|---|---|---|---|
| 12 | 1:59-2:20 | "Not people. Earth's orbit." | process_diagram | Diagram with 3 build steps: sunnier northern summer → monsoon pushed north → rain in the Sahara | ORBITAL CYCLE (PRECESSION) · NO CYCLE LENGTH SHOWN | Larrasoaña et al. 2013; NASA EO |
| 13 | 2:20-2:38 | "…models struggle to produce enough rain to fill all the lakes…" | process_diagram | Flow with build steps: "models struggle to fill all the lakes geologists infer" → "what are the models missing?" → proposed feedback loop: more lakes and plants → more rain → more plants (labelled as a proposal; no dust step) | MODELS STRUGGLE · FEEDBACK IS A PROPOSAL | NASA Earth Observatory (Sebkha el Melah, 2024); Larrasoaña et al. 2013 |
| 14 | 2:38-2:48 | "…more than 230 times in the last 8 million years." | data_chart | Graphic of discrete green episodes on a time axis. **Schematic only: real episode dates are not in hand**, so the graphic is labelled "schematic" or reduced to a callout. | RECONSTRUCTED, MAINLY FROM MEDITERRANEAN SEABED LAYERS: 230+ GREEN PERIODS IN 8 MILLION YEARS | Larrasoaña 2013 |
| 15 | 2:48-3:12 | "How did the last one end?" | annotated_map | Ounianga (L4) geo graphic. Insert: a simple N→S arrow, "monsoon rains retreat southward over ~2-3 thousand years (one reconstruction)". No site dates and no latitude-by-date numbers (not verified). | THE DESERT CREPT SOUTH · ABRUPT OR GRADUAL IS DEBATED | Larrasoaña et al. 2013 |

## ACT 3: Why it's a desert now (3:12-3:39)

| # | ~Time | Narration (first words) | Family | Visual | On-screen labels | Source on screen |
|---|---|---|---|---|---|---|
| 16 | 3:12-3:30 | "Today, the Sahara sits under a belt of sinking air." | process_diagram | yt-graphics `circulation`: rising air at the equator, flow aloft, sinking at ~30°N, surface return (build steps) | RISING AIR · SINKING AIR (DRY, ~30° LATITUDE) | NASA Earth Observatory (Cloudy Earth; Southeastern Australia) |
| 17 | 3:30-3:39 | "You'd be planting against the atmosphere itself." | orbit_wide | Gilf Kebir (L7) or a Tassili wide view, slow pull-out | — | Landsat 8 · USGS |

## ACT 4: Already doing it, in patches (3:39-5:00)

| # | ~Time | Narration (first words) | Family | Visual | On-screen labels | Source on screen |
|---|---|---|---|---|---|---|
| 18 | 3:39-3:58 | "This is East Oweinat…" | pivot_fields | L1 timelapse flip, 1984 (Landsat 5, no fields visible) → 2000 → 2010 → 2016 → 2024 at 40-60 km (scene IDs in `landsat/scene_candidates.json`), then zoom to the circles at 8 km | EAST OWEINAT, EGYPT · ("~0.8 KM (HALF A MILE) ACROSS", measured on Level-1 source bands, `story/source_audit_round10.md`) | Landsat 5/7/8 · USGS |
| 19 | 3:58-4:15 | "The water comes from below." | annotated_map / number_callout | Text card "FOSSIL WATER: SOAKED IN 10,000 TO 1,000,000 YEARS AGO", then a geo graphic of East Oweinat with the label "Nubian Sandstone Aquifer (Egypt, Libya, Sudan, Chad)". **No volume figure and no "recharge = 0" label.** | ANCIENT GROUNDWATER · RECHARGES SLOWLY · NON-RENEWABLE | NASA Earth Observatory (Water Beneath the Sand; Cultivating Egypt's Desert) |
| 20 | 4:15-4:27 | "Across the border in Libya, the Kufra oasis…" | pivot_fields | Kufra (L2): one date, push-in, with a pin on the field cluster | KUFRA, LIBYA | Landsat 8 · USGS |
| 21 | 4:27-4:50 | "And at Toshka…" | lake_change | Toshka (L3) wipe chain: before the lakes (Landsat 5, 1 Jan 1999; no lakes visible), 2002, ~2011-12, Nov 2021 (Landsat 8). Candidate scene IDs: `landsat/scene_candidates.json` | TOSHKA LAKES · FULL 2002 · MOSTLY DRY 2012 · FULL AGAIN 2021 | Landsat 5/7/8 · USGS; NASA EO. No area or percent figures are shown (not verified). |
| 22 | 4:50-5:00 | "So yes, we can green the desert." | pivot_fields | East Oweinat close-up, 2024 | WATER STORED LONG AGO · ONLY SLOWLY REPLACED | Landsat 8 · USGS |

## ACT 5: The big plan (5:00-6:09)

| # | ~Time | Narration (first words) | Family | Visual | On-screen labels | Source on screen |
|---|---|---|---|---|---|---|
| 23 | 5:00-5:20 | "In 2009, three researchers proposed…" | process_diagram | Flow: seawater → desalination → pipeline → irrigation → forest (build steps). Footer: "PROPOSAL (2009) · CARBON UPTAKE = ESTIMATE FROM PLANTATION DATA, LARGE ERROR BARS · NOT A CLIMATE-MODEL RESULT · FOREST STOPS GAINING CARBON AFTER ABOUT A CENTURY". | PROPOSAL (2009) | Ornstein, Aleinov & Rind 2009 (Climatic Change 97:409-437)
| 24 | 5:20-5:28 | "…multi-trillion-dollar undertakings." | number_callout | Text card: "multi-trillion-dollar projects" with the subtitle "the authors' own description, not a calculated annual cost". No dollar figure per year anywhere on screen. | THE AUTHORS' WORDS · NOT AN ANNUAL COST | Ornstein et al. 2009, conclusion (p.431) |
| 24b | 5:28-5:36 | "Would it rain? In the authors' own simulation…" | number_callout | Callout: ">1,000 mm/yr over roughly half of the irrigated Sahara" (about 40 in), subtitle "2009 simulation, one model (GISS ModelE); the authors asked other models to check it". Not drawn as an average. | ONE MODEL · RAIN OVER ABOUT HALF THE FOREST · DIFFERENT METRIC FROM THE NEXT SCENE | Ornstein et al. 2009, section 3.1 (p.418) |
| 25 | 5:28-5:52 | "And the forest wouldn't water itself." | data_chart | **Water-budget graphic (MODEL; mm per year, Sahara average of a 30-year simulation).** One stacked bar: "Water lost to evaporation + transpiration: 1,238" = "rain 319" + "desalinated water supplied in the model 919" (Kemena et al., Fig. 4). The 319 is total rain, which includes 52 that also falls without a forest. **Separate label, outside the bar:** "Rain increase vs. no-forest run: +267 mm/yr (authors: weak, much smaller than earlier simulations)". **Separate label:** "Ratio of totals: 319 / 1,238 ≈ 26% (not tracked water)". Optional second callout: "Surface-air cooling: −6.3 °C on average (about 4 to 8 °C by region)". **Not comparable with scene 24b:** this scene shows a Sahara-wide average, scene 24b rain over about half the forest; never draw them on one axis. **Footer, on screen for the whole scene:** "ONE MODEL SIMULATION (CESM-WACCM) · CO₂ FIXED AT 1960 · TREES FULLY GROWN FROM THE START · WATER SUPPLY ASSUMED, NOT DEMONSTRATED". No dollar amount and no "solution" framing on this graphic. | CLIMATE MODEL RESULT · NOT A MEASUREMENT | Kemena et al., Climate Dynamics (manuscript 2017; journal version 2018) |
| 25b | 5:52-5:58 | "But the biggest changes may not be in the Sahara at all." | orbit_wide | Slow pull-out from the Sahara to a wider view of Africa and the Atlantic (Landsat or NASA Blue Marble; no labels, no numbers) | — | Landsat · USGS or NASA Earth Observatory |
| 26 | — | ~~"A different simulation covered the Sahara with wind and solar farms…"~~ | — | **REMOVED in v0.6** (G8: source unreachable; research record kept in `story/source_audit_round8.md`) | — | — |

## ACT 6: What you'd change far away (6:09-7:50)

| # | ~Time | Narration (first words) | Family | Visual | On-screen labels | Source on screen |
|---|---|---|---|---|---|---|
| 27 | — | ~~"First, color."~~ | — | **REMOVED in v0.6** (G20: source unreachable; research record kept in `story/source_audit_round8.md`) | — | — |
| 28 | — | ~~"…a 2021 model found that solar panels…"~~ | — | **REMOVED in v0.6** (G10, G11: source unreachable; research record kept in `story/source_audit_round8.md`) | — | — |
| 29 | 6:45-7:05 | "First, dust." | external_still → fallback process_diagram | Preferred: a NASA SVS CALIPSO dust visual (B4, licence check per item). Fallback: a flow graphic Sahara → Atlantic → Amazon with the numbers. | 182M t / yr PAST THE SAHARA'S WESTERN EDGE · 28M t SETTLE ON THE AMAZON · 22,000 t PHOSPHORUS (SATELLITE-DERIVED ESTIMATES, 2007-2013) | NASA / Yu et al. 2015 |
| 30 | 7:05-7:25 | "One of the biggest sources is here: the Bodélé…" | dust_source | Bodélé (L5) at 100-150 km, push to the white diatomite flats | BODÉLÉ DEPRESSION, CHAD · ANCIENT LAKEBED · SOURCE OF AMAZON DUST: DEBATED | Landsat 8 · USGS; NASA EO (Bodélé Dust; Another Dusty Day in Chad) |
| 31 | 7:25-7:30 | "What that would mean for the Amazon is an open question." | number_callout | Text card: "HYPOTHESIS · NO STUDY FOUND" (less Saharan dust → less phosphorus for the Amazon?) | — | — |
| 32 | 7:30-7:50 | "Second, storms." | process_diagram | Diagram of a simulation of the world ~6,000 years ago: Sahara = shrubs (not an artificial forest) + dust cut by up to 80% → stronger West African monsoon → winds change across the tropics → more tropical cyclone activity in both hemispheres, most around the Caribbean and the southeastern US; label "some ocean regions: fewer". Footer: "ONE MODEL (EC-EARTH) · PAST SIMULATION · NOT A FORECAST FOR A PLANTED SAHARA · TOO FEW PALEOSTORM RECORDS TO CHECK IT". **No track map** (B5). | SIMULATION OF THE PAST, NOT A FORECAST | Pausata et al. 2017, PNAS 114:6221 |

## ACT 7: What's actually happening (7:50-8:38)

| # | ~Time | Narration (first words) | Family | Visual | On-screen labels | Source on screen |
|---|---|---|---|---|---|---|
| 33 | 7:50-8:10 | "…something real has been happening on the Sahara's southern edge." | orbit_wide → text callouts | Optional: Lake Chad (reserve location), 1987 vs 2023 single wipe, **no area claim**. Callout 1: "VEGETATION FOLLOWED THE RAINS: DOWN IN THE 1980s DROUGHTS, BACK IN THE 1990s–2000s (NASA satellite record)". Callout 2: "UNCCD DOCUMENTS: >5 MILLION HA (MARADI, NIGER) · >7 MILLION HA (NIGER)" with the subtitle "reported figures; they differ by region and report". No "by 2017", no "USGS". | SAHEL · NIGER · REPORTED FIGURES | NASA Earth Observatory (Defining Desertification); UNCCD (GGW report 2020; Land Outlook working paper) |
| 34 | 8:10-8:38 | "In 2007, the African Union launched the Great Green Wall…" | data_chart | Three separately labelled bars, never combined into one percentage: "COP21 pledge: 100 Mha by 2030", "PA-GGW target: 25 Mha", "Counted in core zones by 2020, as reported to the Wall's agency (preliminary): ~4 Mha" | GREAT GREEN WALL · TWO TARGETS, ONE PRELIMINARY COUNT | UNCCD 2020 |

## CLOSE (8:38-9:21)

| # | ~Time | Narration (first words) | Family | Visual | On-screen labels | Source on screen |
|---|---|---|---|---|---|---|
| 35 | 8:38-8:58 | "So, could we turn the Sahara green?" | pivot_fields | East Oweinat widest view, wipe 1984 → 2024 | — | Landsat · USGS |
| 36 | 8:58-9:10 | "…Orbital cycles turned the Sahara green before…" | text_callout | Text card: "UNCLEAR WHETHER, AND HOW MUCH, THE SAHARA MIGHT GREEN AGAIN OVER THE COMING CENTURIES AND MILLENNIA" with "greenhouse gases are layered on top of the orbital cycles". No year count. | NASA EARTH OBSERVATORY | NASA Earth Observatory (Water for a Desert Lake in Algeria) |
| 37 | 9:10-9:21 + outro | "…whether we should be the ones to flip the switch." | orbit_wide | Ounianga or Tassili, slow pull-out, then the outro | — | Landsat 8 · USGS |

---

## Visual novelty plan

The aim is to avoid the "slideshow + TTS" pattern named in YouTube's inauthentic-content policy.

1. **Family rotation.** 11 families. The storyboard never places the same family in more than 2 consecutive scenes, and each act mixes Landsat, graphics and callouts.
2. **Every Landsat shot moves.** Each one has a camera move (push, pull, pan), a wipe or a flip. Static locations (Ounianga, Tassili, Bodélé, Gilf Kebir) use different scales (15 / 60 / 150 km), so the same place is never shown twice at the same framing.
3. **Graphics build in steps.** Every diagram reveals itself in 2-5 build steps timed to the narration words, so no graphic is static for more than ~6 s.
4. **Numbers appear as timed inserts** over imagery: the 0.35 s fade inserts from PR #13.
5. **Light and dark styles alternate.** Data charts use `documentary_light`; schematics use `documentary_dark`. Each act has at least one of each.
6. **The change locations each tell a different story:**

   | Location | Story |
   |---|---|
   | East Oweinat | Growth |
   | Toshka | Rise, fall, rise |
   | Kufra | Single-date context |

7. **One recurring visual motif:** "orbit → ground". The same location at 150 km, then at 15 km. It is used at most once per act.
8. **No AI-generated imagery.** No stock footage. No talking-head substitutes.
