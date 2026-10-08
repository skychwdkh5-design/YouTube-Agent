# Fact-check ledger: Episode 001 "What If We Turned the Sahara Desert Green?"

**Ledger status: DRAFT v0.2, not locked.**

**Round 2/3 (2026-10-08).** Sources for the IDs below were read in full (see `source_audit_round2.md`, `source_audit_round3.md`). Where this table and those files differ, the audit files are newer.

| Round-2 status | IDs |
|---|---|
| ✓ VERIFIED (wording as in script v0.2) | P20, S4, S5, S6, S7, S7b, S9, S17, S18, S18b, S19, S21, L2, G19, N1, L3 |
| ⛔ BLOCKED (primary source unreachable) | G4, G17, G18, P10 |
| ◇ HYPOTHESIS (narrated as one) | G14 |
| NEEDS_REVISION / SCENE-CHECK | L1 (Landsat supports bare 1984 scene; "earliest Landsat" and "~1 km" pending) |
| ⚠ UNVERIFIED (not yet read in full) | S1, S2, S3, P2, P11, P12, P14, P8, L4, P18, P3, P5, P17, P19, G1, G2, G5, G6, G8, G20, G10, G11, P24, S12, S13, S14, P23 |

Corrections applied in script v0.2 (reviewer-approved): N1 (no "warming and drying"; NASA: air descends at about 15-30° and inhibits cloud formation), L3 (1,450 km², 80% and "late 1990s" removed; NASA's 2002 / 2012 / 2021 observations kept), S18 (COP21 100 Mha ambition and the PA-GGW 25 Mha target stated separately), R1 (Bodélé not presented as the Amazon's main source; reduction in Amazon phosphorus narrated as an unmodeled hypothesis), P20 (a reconstruction, not 230 observed events), S4 (dust carried past the Sahara's western edge).

**How the checks were done.** Direct page fetches from this environment were refused for every source host: nasa.gov, science.nasa.gov, svs.gsfc.nasa.gov, noaa.gov, unccd.int, unesco.org, ncbi/pmc, springer, wiley/agu and support.google.com (DNS ENOTFOUND or proxy 403). Each claim was therefore checked only against search-engine snippets of the source: abstracts, press releases and the agency pages themselves. Earlier productions (Lake Mead, Kīlauea, Sirhan) used the same method. Before the lock, the primary page for every **USED** claim has to be opened by a human, or from an environment with web access.

**Status codes**

| Code | Meaning |
|---|---|
| `SNIPPET` | Supported by the source's own snippet (agency page, abstract or institutional release). The primary page or PDF was not read in full. |
| `SECONDARY` | Supported only by news, encyclopedia or secondary write-ups. A primary source must be found before use. |
| `PENDING` | No source checked yet. The line is in the script but blocked until it is sourced. |
| `ATTRIBUTED` | Narrated only as a named person's statement or estimate. |

**Category codes:** ESTABLISHED = broad consensus or measurement; MODEL = simulation result; HYPOTHESIS = proposal or speculation; UNCERTAIN = weak or single-source; DISPUTED = published disagreement.

## Used in the narration

| ID | Claim as narrated | Category | Status | Primary source(s) | Caveat |
|---|---|---|---|---|---|
| S1 | Sahara is about 9 million km² (≈3.5 million sq mi) | ESTABLISHED | SECONDARY | Wikipedia "Sahara"; Guinness "largest desert" (9.1M km²) | The figure depends on where the boundary is drawn. **Needs an agency or encyclopedic primary source (Britannica, USGS).** |
| S2 | Bigger than the entire lower 48 (≈8.08M km² incl. water; 7.66M km² land) | ESTABLISHED | SECONDARY | US Census QuickFacts note https://www.census.gov/quickfacts/fact/note/US/LND110210 | Needs the Census Gazetteer table itself. |
| S3 | Most of the Sahara gets <100 mm (4 in) of rain a year | ESTABLISHED | SECONDARY | WWF ecoregion https://ecoregions.worldwildlife.org/ecoregions/pa1327 | 100 mm is the usual boundary. |
| P2 | Green Sahara roughly 11,000–5,000 years ago | ESTABLISHED | SNIPPET | Tierney, Pausata & deMenocal 2017, Sci. Adv. 3:e1601503 https://pmc.ncbi.nlm.nih.gov/articles/PMC5242556 | Other records start at about 14,800 years ago (deMenocal 2000). Say "roughly". |
| P11 | Grassland and savanna with lakes and wetlands, not jungle | ESTABLISHED | SNIPPET | Hély et al. 2014, Clim. Past 10:681 https://cp.copernicus.org/articles/10/681/2014/ | "East Africa plains" is an analogy, not a claim. |
| P10 | Lake Mega-Chad ≥400,000 km² (>150,000 sq mi) | ESTABLISHED (size varies) | SNIPPET | Drake & Bristow 2006, The Holocene 16:901; Bouchette et al. 2010 (>350,000 km²) | Do **not** compare it to the Caspian Sea. |
| P12 | Gobero, Niger: ~200 graves beside an ancient lake, with crocodile and large-fish bones | ESTABLISHED | SNIPPET | Sereno et al. 2008 PLoS ONE; UChicago release https://news.uchicago.edu/article/2008/08/14/stone-age-graveyard-reveals-lifestyles-green-sahara-two-successive-cultures-thriv | No hippo claim. |
| P14 | Tassili n'Ajjer: >15,000 drawings and engravings | ESTABLISHED | SNIPPET | UNESCO https://whc.unesco.org/en/list/179 | |
| P8 | Tierney: "ten times as wet as today" | ESTABLISHED as a quote | ATTRIBUTED + SNIPPET | Lamont press release https://lamont.columbia.edu/news/green-saharas-ancient-rainfall-regime-revealed | A quote, not a measured number. Keep the attribution. |
| L4 | Lakes of Ounianga (Chad): lakes in the desert, fed by fossil groundwater | ESTABLISHED | SNIPPET | UNESCO https://whc.unesco.org/en/list/1400 | |
| P18 | Lake Yoa sediments record the drying | ESTABLISHED (record); DISPUTED (interpretation) | SNIPPET | Kröpelin et al. 2008, Science 320:765 | The narration describes the record, not the dispute. |
| P3 | Orbital wobble (~21,000 yr precession) → sunnier northern summers → monsoon pushed north | ESTABLISHED | SNIPPET | Armstrong et al. 2023, Nat. Commun. (PMC10491769); Bristol release https://bristol.ac.uk/news/2023/september/sahara-desert-greening.html | "Wobble in Earth's orbit" is a simplification of precession. Acceptable. |
| P5 | Models match the evidence only with vegetation and dust feedbacks | ESTABLISHED + MODEL | SNIPPET | Tierney et al. 2017 | |
| P20 | Geological records suggest the Sahara turned green >230 times in 8 million years (a reconstruction from marine and desert sediments, esp. Mediterranean sapropels; not 230 observed events) | RECONSTRUCTION | **VERIFIED (read in full, round 2)** | Larrasoaña et al. 2013, PLoS ONE 8(10): e76514 https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0076514 | "over 230 GSPs within the last 8 million years"; sapropels used "as markers". |
| P17 | Mauritania dust record: abrupt end | DISPUTED | SNIPPET | deMenocal et al. 2000, QSR 19:347 | |
| P19 | Time-transgressive end: fast locally, later further south | ESTABLISHED (leading synthesis) | SNIPPET | Shanahan et al. 2015, Nat. Geosci. 8:140 | |
| N1 | NASA: descending air at about 15-30° latitude inhibits cloud formation, so clouds are rare and deserts common there; the air has already lost most of its water | ESTABLISHED (textbook) | **VERIFIED (read in full, round 2)** | NASA EO Cloudy Earth https://science.nasa.gov/earth/earth-observatory/cloudy-earth-85843/ ; NASA EO Southeastern Australia https://science.nasa.gov/earth/earth-observatory/southeastern-australia-3973/ | No "warming as it falls" claim: it is not in these sources. |
| L1 | East Oweinat: no visible fields in a 1984 Landsat 5 scene (LT05_L1TP_177044_19840826), first small fields by Jan 2000, large pivot fields by 2016-2024; pivots measure ~0.9 km (median of 88 circles, Landsat 9, 2024-01-05) | OBSERVATION (Landsat) | **NEEDS_REVISION (wording)** | USGS Landsat Collection 2 scenes in `landsat/scene_candidates.json`; NASA EO https://science.nasa.gov/earth/earth-observatory/cultivating-egypts-desert-89820/ (development began in the 1980s) | "Earliest Landsat images" is not shown: MSS scenes (1972-83) were not searched. Recommended: "in a 1984 Landsat image" and "each close to a kilometer across". Reviewer to approve before the script changes. |
| G17 | Nubian Sandstone Aquifer System holds >150,000 km³ under Egypt, Libya, Sudan and Chad | ESTABLISHED | SECONDARY (AGU Eos) | https://eos.org/articles/ancient-water-underlies-arid-egypt | **Needs an IAEA/UNESCO primary source.** |
| G18 | Recharge effectively zero ("barely being refilled") | ESTABLISHED | SECONDARY | Same Eos article (USGS hydrogeologist quoted) | |
| L2 | Kufra runs on the same fossil groundwater; the water entered the ground in wetter times | ESTABLISHED | SNIPPET | NASA EO https://earthobservatory.nasa.gov/images/152356/water-beneath-the-sand | EO gives roughly 10,000 to 1,000,000 years. The script says "thousands of years ago or more". |
| G19 | Libya began the Great Man-Made River in the 1980s (1984) | ESTABLISHED | SECONDARY (Wikipedia) | — | **Needs a primary source.** Do not use a capacity figure. |
| L3 | NASA photographs: Toshka lakes full in 2002, mostly dried up by 2012 (low Nile flow), more water than ever before in Nov 2021 | OBSERVATION | **VERIFIED (read in full, round 2)** | NASA EO https://science.nasa.gov/earth/earth-observatory/two-decades-of-change-at-toshka-lakes-149334/ | 1,450 km², ~80% and "late 1990s" REMOVED: not on the page. Landsat check in `source_audit_round3.md`. |
| G1 | 2009 proposal: irrigated forests on the Sahara and the Outback, desalinated seawater, drip irrigation | ESTABLISHED (that it was proposed) | SNIPPET | Ornstein, Aleinov & Rind 2009, Climatic Change 97:409 https://link.springer.com/article/10.1007/s10584-009-9626-y | |
| G2 | The authors argued uptake could equal fossil-fuel emissions | HYPOTHESIS | SNIPPET (abstract) | Same | Always attribute ("they argued"). |
| G4 | Estimated cost ~$2 trillion a year | HYPOTHESIS | SECONDARY (Popular Science, SciDev) | https://www.popsci.com/environment/article/2009-09/scientists-concoct-2-trillion-year-plan-geoengineer-sahara-desert/ | **Confirm in the paper (open access).** |
| G5 | Irrigated forest in CESM-WACCM: −6 °C, +267 mm/yr | MODEL | SNIPPET (abstract) | Kemena et al. 2018, Climate Dynamics 50:4561 (doi:10.1007/s00382-017-3890-8); https://oceanrep.geomar.de/id/eprint/39547 | The journal is Climate Dynamics, not ESD. The year said is 2018. |
| G6 | Only ~26% recycled locally; much went south to the Sahel monsoon | MODEL | SNIPPET (abstract) | Same | "Wouldn't water itself" is our paraphrase of the authors' doubt about self-sustainment. |
| G8 | Wind and solar farms: rainfall more than doubles; Sahel +200–500 mm/yr | MODEL | SNIPPET | Li et al. 2018, Science 361:1019; UMD release https://umdrightnow.umd.edu/news-releases/large-scale-wind-and-solar-farms-sahara-would-increase-rain-and-vegetation | |
| G20 | Dryland afforestation: albedo warming cancels much of the carbon benefit | MODEL / analysis | SNIPPET | Rohatyn, Yakir, Rotenberg & Carmel 2022, Science 377:1436; Technion release | Covers drylands, not the hyper-arid Sahara. The script says "forests planted in drylands". |
| G10 | Panels over 20% of the Sahara: about +0.16 °C global | MODEL | SNIPPET | Lu, Pausata et al. 2021, GRL 48(2), doi:10.1029/2020GL090789 | The model name was not verified. |
| G11 | Lu 2021: rain shifted away from the Amazon (the tropical rain belt moves north) | MODEL | SNIPPET | Same | No percentage (the 10–30% figure is NOT VERIFIED). |
| S4 | ~182 million tons of dust a year are carried past the Sahara's western edge (15°W); the dust then crosses the Atlantic (2007–2013 average) | SATELLITE-DERIVED ESTIMATE | **VERIFIED (read in full, round 2)** | NASA SVS 4273 https://svs.gsfc.nasa.gov/4273/ ; Yu et al. 2015, GRL doi:10.1002/2015GL063040 (paper not read) | "Tons" as on NASA's page; on screen "million tons". |
| S5 | ~28 million tons settle on the Amazon basin | ESTABLISHED (estimate, range 8–48) | SNIPPET | Same | |
| S6 | ~22,000 tons of phosphorus a year, comparable to the Amazon's hydrological loss | ESTABLISHED (estimate) | SNIPPET | Same | This is delivery to the basin, not uptake by plants. |
| S7 | The Bodélé is one of the biggest dust sources on Earth | ESTABLISHED | **VERIFIED (read in full, round 2)** | NASA EO https://earthobservatory.nasa.gov/images/146011/bodele-dust ; Koren et al. 2006 | Do NOT say it supplies most of the Amazon's dust (DISPUTED: Yu et al. 2020 point to El Djouf). |
| S7b | A newer analysis finds most Amazon-bound dust comes from El Djouf (Mauritania/Mali), ~2,500 km (1,600 mi) west of the Bodélé | ESTABLISHED (reported by NASA EO; DISPUTED vs Koren 2006) | **VERIFIED as NASA's reporting (round 2)** | NASA EO https://science.nasa.gov/earth/earth-observatory/another-dusty-day-in-chad-147816/ | Underlying paper (Yu et al. 2020) not read. The narration says "may not be the main supplier". |
| S9 | The Bodélé floor is ancient Lake Mega-Chad lakebed, covered in diatomite (fossil algae skeletons) | ESTABLISHED | SNIPPET | NASA EO https://earthobservatory.nasa.gov/images/147816/another-dusty-day-in-chad | |
| G14 | The effect of a greened Sahara on Amazon nutrients has not been measured for a planted Sahara | HYPOTHESIS (narrated as an open question) | SNIPPET (absence) | — | The narration says "open question". It must stay that way. |
| P24 | Paleo-model: green, less dusty Sahara → more tropical cyclone activity, most over the Caribbean and the US East Coast | MODEL | SNIPPET | Pausata et al. 2017, PNAS 114:6221 https://pmc.ncbi.nlm.nih.gov/articles/PMC5474772 | Narrated as "a model of the past, not a forecast". |
| S12 | The Sahel has greened since the 1970s–80s droughts (NDVI) | ESTABLISHED | SNIPPET | Herrmann, Anyamba & Tucker 2005; NASA NTRS 20150018274 | Greening ≠ healthier ecosystems (Herrmann & Tappan 2013). |
| S13 | Mostly returning rain, partly farmers | DISPUTED (balance) | SNIPPET | Hickler et al. 2005; Niger FMNR literature | |
| S14 | Niger farmer-managed regeneration covered ~7 Mha (≈17M acres) by 2017 (USGS estimate) | ESTABLISHED (as a USGS estimate) | SNIPPET | Smale, Tappan & Reij 2018 (USGS) https://www.usgs.gov/publications/farmer-managed-restoration-agroforestry-parklands-niger | The source word is "affected"; the script says "covered". Keep this close to the source. |
| S17 | The Great Green Wall was launched in 2007 by African nations (African Union) | ESTABLISHED | SNIPPET | UNCCD https://www.unccd.int/our-work/ggwi | |
| S18 | The initiative's ambition, pledged at COP21: restore 100 Mha by 2030 | OFFICIAL TARGET | **VERIFIED (read in full, round 2)** | UNCCD https://www.unccd.int/our-work/ggwi ; UNCCD 2020 report p.22 | Never combine with S18b. |
| S18b | The Wall's own coordinating agency (PA-GGW) targets 25 Mha by 2030 | OFFICIAL TARGET | **VERIFIED (read in full, round 3)** | UNCCD 2020 report, section 3.3, p.22: "the PA-GGW aims to restore 25 Mha by 2030" | Separate from S18. |
| S19 | 2020 status report: ~4 Mha inside the core zones | ESTABLISHED (official self-report) | SNIPPET | UNCCD 2020 https://www.unccd.int/resources/publications/great-green-wall-implementation-status-and-way-ahead-2030 | Do not present the 18 Mha "wider" figure as Wall progress. |
| S21 | Shift from a literal tree line to a mosaic of land restoration | ESTABLISHED | SECONDARY | ISS Africa; Wikipedia | **Needs a UNCCD wording source.** |
| P23 | One scientist estimates the next orbital window is ~10,000 years away | UNCERTAIN | ATTRIBUTED + SNIPPET | UC Irvine (Kathleen Johnson) https://ess.uci.edu/news/858 | Name her on screen, or keep "one scientist". |

## Researched but not used, or to avoid

| ID | Item | Why it is not used |
|---|---|---|
| S8 | "The Bodélé supplies half of the Amazon's dust" | DISPUTED (Koren 2006 vs Yu et al. 2020). |
| S15/S16 | Lake Chad "shrank 90%" | True for the 1960s–80s. Since about 2000 the lake is stable or partly recovered (Pham-Duc 2020). Left out of the narration to save time. If it is added, use both halves. |
| G3 | Ornstein "up to 8 °C cooler, 700–1,200 mm rain" | Press-only figures. |
| G15 | "Up to 5 trillion m³ of water a year" | A secondary policy brief only. UNCERTAIN. |
| G16 | Desalination "3–4 kWh/m³" | No IEA, IDA or review source in hand. |
| P7 | Dust-feedback monsoon +50% | NOT VERIFIED; disputed. |
| P15 | "Cave of Swimmers proves people swam" | Dating and meaning are uncertain. |
| G19b | Great Man-Made River capacity of 6.5M m³/day | NOT VERIFIED. |
| — | "Greening the Sahara would end global warming" | That is the 2009 paper's title and claim, not a finding. |
| — | "A green Sahara would kill the Amazon" / "more US hurricanes" as a forecast | Speculative, or model-only. |
| — | YPP 8,000 hours from 2027 | Not part of the narration. Monetization item, unverified (see checklist). |
