# Fact-check ledger: Episode 001 "What If We Turned the Sahara Desert Green?"

**Ledger status: DRAFT v0.1, not locked.**

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
| P20 | Green Sahara >230 times in 8 million years | ESTABLISHED (proxy compilation) | SNIPPET | Larrasoaña et al. 2013, PLoS ONE https://pmc.ncbi.nlm.nih.gov/articles/PMC3797788 | Used in the hook. Say "suggest". |
| P17 | Mauritania dust record: abrupt end | DISPUTED | SNIPPET | deMenocal et al. 2000, QSR 19:347 | |
| P19 | Time-transgressive end: fast locally, later further south | ESTABLISHED (leading synthesis) | SNIPPET | Shanahan et al. 2015, Nat. Geosci. 8:140 | |
| N1 | Sinking air of the subtropical (Hadley) circulation suppresses rain over the Sahara | ESTABLISHED (textbook) | **PENDING** | Needs a NOAA/NASA/NCAR explainer | **Blocking for ACT 3.** |
| L1 | East Oweinat: bare desert in the earliest Landsat images, now ~1 km center-pivot circles | ESTABLISHED | SNIPPET + **SCENE-CHECK** | NASA EO https://earthobservatory.nasa.gov/images/89820/cultivating-egypts-desert ; ESA 2019 | "Bare desert" must be confirmed on the actual earliest scene we use. |
| G17 | Nubian Sandstone Aquifer System holds >150,000 km³ under Egypt, Libya, Sudan and Chad | ESTABLISHED | SECONDARY (AGU Eos) | https://eos.org/articles/ancient-water-underlies-arid-egypt | **Needs an IAEA/UNESCO primary source.** |
| G18 | Recharge effectively zero ("barely being refilled") | ESTABLISHED | SECONDARY | Same Eos article (USGS hydrogeologist quoted) | |
| L2 | Kufra runs on the same fossil groundwater; the water entered the ground in wetter times | ESTABLISHED | SNIPPET | NASA EO https://earthobservatory.nasa.gov/images/152356/water-beneath-the-sand | EO gives roughly 10,000 to 1,000,000 years. The script says "thousands of years ago or more". |
| G19 | Libya began the Great Man-Made River in the 1980s (1984) | ESTABLISHED | SECONDARY (Wikipedia) | — | **Needs a primary source.** Do not use a capacity figure. |
| L3 | Toshka lakes appeared in the late 1990s, max ~1,450 km² (~560 sq mi), ~80% smaller by 2012, full again by 2021 | ESTABLISHED | SNIPPET + **SCENE-CHECK** | NASA EO https://earthobservatory.nasa.gov/images/149334/two-decades-of-change-at-toshka-lakes | The NASA page uses ISS photos. Our Landsat dates must bracket these years (see LANDSAT_LOCATIONS). |
| G1 | 2009 proposal: irrigated forests on the Sahara and the Outback, desalinated seawater, drip irrigation | ESTABLISHED (that it was proposed) | SNIPPET | Ornstein, Aleinov & Rind 2009, Climatic Change 97:409 https://link.springer.com/article/10.1007/s10584-009-9626-y | |
| G2 | The authors argued uptake could equal fossil-fuel emissions | HYPOTHESIS | SNIPPET (abstract) | Same | Always attribute ("they argued"). |
| G4 | Estimated cost ~$2 trillion a year | HYPOTHESIS | SECONDARY (Popular Science, SciDev) | https://www.popsci.com/environment/article/2009-09/scientists-concoct-2-trillion-year-plan-geoengineer-sahara-desert/ | **Confirm in the paper (open access).** |
| G5 | Irrigated forest in CESM-WACCM: −6 °C, +267 mm/yr | MODEL | SNIPPET (abstract) | Kemena et al. 2018, Climate Dynamics 50:4561 (doi:10.1007/s00382-017-3890-8); https://oceanrep.geomar.de/id/eprint/39547 | The journal is Climate Dynamics, not ESD. The year said is 2018. |
| G6 | Only ~26% recycled locally; much went south to the Sahel monsoon | MODEL | SNIPPET (abstract) | Same | "Wouldn't water itself" is our paraphrase of the authors' doubt about self-sustainment. |
| G8 | Wind and solar farms: rainfall more than doubles; Sahel +200–500 mm/yr | MODEL | SNIPPET | Li et al. 2018, Science 361:1019; UMD release https://umdrightnow.umd.edu/news-releases/large-scale-wind-and-solar-farms-sahara-would-increase-rain-and-vegetation | |
| G20 | Dryland afforestation: albedo warming cancels much of the carbon benefit | MODEL / analysis | SNIPPET | Rohatyn, Yakir, Rotenberg & Carmel 2022, Science 377:1436; Technion release | Covers drylands, not the hyper-arid Sahara. The script says "forests planted in drylands". |
| G10 | Panels over 20% of the Sahara: about +0.16 °C global | MODEL | SNIPPET | Lu, Pausata et al. 2021, GRL 48(2), doi:10.1029/2020GL090789 | The model name was not verified. |
| G11 | Lu 2021: rain shifted away from the Amazon (the tropical rain belt moves north) | MODEL | SNIPPET | Same | No percentage (the 10–30% figure is NOT VERIFIED). |
| S4 | ~182 million tons of dust a year leave the Sahara over the Atlantic (2007–2013 average) | ESTABLISHED (satellite-based estimate) | SNIPPET | Yu et al. 2015, GRL doi:10.1002/2015GL063040; NASA SVS https://svs.gsfc.nasa.gov/11775 | "Tons" means metric tonnes (Tg). On screen: "million tonnes". |
| S5 | ~28 million tons settle on the Amazon basin | ESTABLISHED (estimate, range 8–48) | SNIPPET | Same | |
| S6 | ~22,000 tons of phosphorus a year, comparable to the Amazon's hydrological loss | ESTABLISHED (estimate) | SNIPPET | Same | This is delivery to the basin, not uptake by plants. |
| S7 | The Bodélé is one of the biggest dust sources on Earth | ESTABLISHED | SNIPPET | NASA EO https://earthobservatory.nasa.gov/images/146011/bodele-dust ; Koren et al. 2006 | Do NOT say it supplies most of the Amazon's dust (DISPUTED: Yu et al. 2020 point to El Djouf). |
| S9 | The Bodélé floor is ancient Lake Mega-Chad lakebed, covered in diatomite (fossil algae skeletons) | ESTABLISHED | SNIPPET | NASA EO https://earthobservatory.nasa.gov/images/147816/another-dusty-day-in-chad | |
| G14 | The effect of a greened Sahara on Amazon nutrients has not been measured for a planted Sahara | HYPOTHESIS (narrated as an open question) | SNIPPET (absence) | — | The narration says "open question". It must stay that way. |
| P24 | Paleo-model: green, less dusty Sahara → more tropical cyclone activity, most over the Caribbean and the US East Coast | MODEL | SNIPPET | Pausata et al. 2017, PNAS 114:6221 https://pmc.ncbi.nlm.nih.gov/articles/PMC5474772 | Narrated as "a model of the past, not a forecast". |
| S12 | The Sahel has greened since the 1970s–80s droughts (NDVI) | ESTABLISHED | SNIPPET | Herrmann, Anyamba & Tucker 2005; NASA NTRS 20150018274 | Greening ≠ healthier ecosystems (Herrmann & Tappan 2013). |
| S13 | Mostly returning rain, partly farmers | DISPUTED (balance) | SNIPPET | Hickler et al. 2005; Niger FMNR literature | |
| S14 | Niger farmer-managed regeneration covered ~7 Mha (≈17M acres) by 2017 (USGS estimate) | ESTABLISHED (as a USGS estimate) | SNIPPET | Smale, Tappan & Reij 2018 (USGS) https://www.usgs.gov/publications/farmer-managed-restoration-agroforestry-parklands-niger | The source word is "affected"; the script says "covered". Keep this close to the source. |
| S17 | The Great Green Wall was launched in 2007 by African nations (African Union) | ESTABLISHED | SNIPPET | UNCCD https://www.unccd.int/our-work/ggwi | |
| S18 | Target: 100 Mha restored by 2030 | ESTABLISHED (target) | SNIPPET | Same | |
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
