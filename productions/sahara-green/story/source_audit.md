# Episode 001: source audit, round 1 (2026-10-08)

This file sits next to `claims.md`. It does not change `claims.md`, `script.md` or any other preproduction file. The narration is **not** approved.

## How it was checked

Both target pages were requested directly with WebFetch and with curl through the proxy. Both failed: `journals.plos.org` and `www.nasa.gov` returned DNS ENOTFOUND to WebFetch and **proxy 403 (CONNECT denied by network policy)** to curl. The same block applies to `api.plos.org`, Europe PMC, Crossref, Wiley/AGU, `acd-ext.gsfc.nasa.gov` and `svs.gsfc.nasa.gov`.

The fallback was a web search restricted to the target domains (`journals.plos.org`, `nasa.gov`). That search returned the target pages themselves and the search engine's extract of their text. **No full page and no PDF was read.**

Status used below:

- **`AUDITED-INDEX`**: the target page's text, as returned by a domain-restricted search, matches the claim. A full-page read is still required before the lock.
- **`PENDING`**: not audited in this round.

## Audited claims

### P20: "The Sahara has turned green more than 230 times in the last 8 million years"

- **Target:** Larrasoaña, Roberts & Rohling (2013), "Dynamics of Green Sahara Periods and Their Role in Hominin Evolution", PLoS ONE 8(10): e76514, published 16 Oct 2013. https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0076514
- **What the page says (search extract of the abstract):**
  - the authors compiled continental and marine palaeoenvironmental records from North Africa and its surroundings;
  - they report "more than 230" green Sahara periods over the past 8 million years;
  - each period took about 2-3 thousand years to develop and peaked over 4-8 thousand years.
- **Evidence type: RECONSTRUCTION** (a compilation of proxy records). It is not a direct observation, and it is not a model result.
- **Result:** the number and the time span match. **AUDITED-INDEX.**
- **Wording notes** (for the reviewer only; the script is not changed):
  - The body line in `script.md` (ACT 2), "Sediment records suggest…", fits the evidence type. The source compiles "continental and marine palaeoenvironmental records", so "Geological records suggest" would be slightly more exact.
  - The hook states the claim flatly: "It has happened more than 230 times before." That is acceptable for a reconstruction, as long as ACT 2 carries the qualifier.
  - The storyboard callout for scene 2/14 ("230+ green periods in 8 million years") matches.

### S4 / S5 / S6: Saharan dust to the Atlantic and the Amazon

- **Target:** NASA Goddard feature "NASA Satellite Reveals How Much Saharan Dust Feeds Amazon's Plants". https://www.nasa.gov/centers-and-facilities/goddard/nasa-satellite-reveals-how-much-saharan-dust-feeds-amazons-plants/
- **Underlying study:** Yu et al. 2015, GRL, doi:10.1002/2015GL063040.

| ID | Page wording (search extract) | Script wording | Match |
|---|---|---|---|
| S4 | Wind and weather pick up "on average 182 million tons of dust each year and carry it past the western edge of the Sahara" (CALIPSO, 2007-2013) | "about 182 million tons of Saharan dust blow out over the Atlantic every year" | The number matches. The page anchors it at "the western edge of the Sahara". "Over the Atlantic" is a paraphrase; reviewer's choice. |
| S5 | "27.7 million tons fall to the surface over the Amazon basin". The paper gives a 7-year mean of ~28 Mt, range 8-48 Mt, and year-to-year variation up to 29% (negatively correlated with the previous year's Sahel rainfall). | "roughly 28 million tons settle on the Amazon basin" | Matches ("roughly"). |
| S6 | An estimated "22,000 tons per year" of phosphorus is deposited in the Amazon basin, "about the same amount as that lost from rain and flooding". The phosphorus content comes from dust samples from the Bodélé Depression and ground stations in Barbados and Miami. | "an estimated 22,000 tons of phosphorus a year, about as much as the rainforest loses to rain and floods" | Matches. |

- **Evidence type: SATELLITE-DERIVED ESTIMATE**, not a direct measurement of deposition.
  - CALIPSO's lidar observes the dust in the atmosphere directly, in 3-D.
  - Transport and deposition are then *estimated* from those observations.
  - Phosphorus is a further estimate: the deposition estimate multiplied by the measured phosphorus content of dust samples.
  - "Comparable to the hydrological loss" compares the result with independent estimates of loss.
- **Not checked this round:** the exact estimation method (which wind fields, mass conversion) and the exact page date. These need the full page or the paper.
- **Result:** **AUDITED-INDEX** for all three numbers.

## Evidence type of every narrated claim

All claims not listed above remain **PENDING**: not audited in this round, whatever `claims.md` currently says. "SNIPPET" in `claims.md` was produced by the research subagents and has **not** been audited.

| ID | Claim (short) | Evidence type | Audit status |
|---|---|---|---|
| S1 | Sahara ≈ 9 M km² | Geographic measurement (definition-dependent) | PENDING |
| S2 | Larger than the lower 48 | Official statistic (Census) | PENDING |
| S3 | Rainfall < 100 mm/yr | Instrumental climatology (observation) | PENDING |
| P2 | Green Sahara ≈ 11,000-5,000 years ago | Reconstruction (proxies) | PENDING |
| P11 | Savanna/grassland, not jungle | Reconstruction (pollen, proxies) | PENDING |
| P10 | Mega-Chad ≥ 400,000 km² | Reconstruction (shorelines, DEM) | PENDING |
| P12 | Gobero: ~200 graves, crocodile and fish bones | Direct archaeological observation | PENDING |
| P14 | Tassili: > 15,000 images | Direct observation (inventory) | PENDING |
| P8 | "Ten times as wet as today" (Tierney) | Quote summarising a reconstruction | PENDING |
| L4 | Ounianga lakes fed by fossil groundwater | Observation + hydrogeological interpretation | PENDING |
| P18 | Lake Yoa sediment record of drying | Reconstruction | PENDING |
| P3 | Orbital precession → stronger monsoon | Established theory + reconstruction + model | PENDING |
| P5 | Feedbacks needed to match the evidence | Model vs reconstruction comparison | PENDING |
| P17 | Abrupt end (Mauritania dust record) | Reconstruction (DISPUTED) | PENDING |
| P19 | End came later farther south | Reconstruction synthesis | PENDING |
| N1 | Subtropical sinking air suppresses rain | Established physics; no source yet | PENDING (no source) |
| L1 | East Oweinat bare → green circles | Direct satellite observation (needs our scenes) | PENDING + SCENE-CHECK |
| G17 | Nubian aquifer > 150,000 km³ | Hydrogeological estimate | PENDING |
| G18 | Recharge effectively zero | Hydrogeological estimate/interpretation | PENDING |
| L2 | Kufra on fossil groundwater | Observation + interpretation | PENDING |
| G19 | Great Man-Made River begun 1984 | Historical record | PENDING |
| L3 | Toshka: appeared late 1990s, ~1,450 km² max, −80% by 2012, full by 2021 | Direct satellite observation (NASA measurement) | PENDING + SCENE-CHECK |
| G1 | 2009 Sahara/Outback forest proposal | Published proposal | PENDING |
| G2 | Uptake ≈ fossil-fuel emissions | Authors' claim (proposal/estimate) | PENDING |
| G4 | ~$2 trillion/yr | Authors' cost estimate (press only so far) | PENDING |
| G5 | −6 °C, +267 mm/yr | Model result | PENDING |
| G6 | ~26% recycled locally; rest to the Sahel | Model result | PENDING |
| G8 | Wind/solar farms: rain more than doubles; Sahel +200-500 mm | Model result | PENDING |
| G20 | Albedo cancels much of the dryland carbon benefit | Model/analysis (built on field data) | PENDING |
| G10 | Panels on 20% of the Sahara → +0.16 °C global | Model result | PENDING |
| G11 | Rain shifts away from the Amazon | Model result | PENDING |
| S4-S6 | Dust 182 Mt / ~28 Mt / 22,000 t P | Satellite-derived estimate | **AUDITED-INDEX** |
| S7 | Bodélé among the biggest dust sources | Satellite observation + estimates | PENDING |
| S9 | Bodélé = Mega-Chad lakebed, diatomite | Direct observation (geology) | PENDING |
| G14 | Amazon effect of a planted Sahara unmeasured | Absence of evidence (open question) | PENDING |
| P24 | Paleo-model: more tropical cyclones | Model result | PENDING |
| S12 | Sahel greening since the 1980s | Satellite observation (NDVI) | PENDING |
| S13 | Mostly rain, partly farmers | Interpretation (DISPUTED) | PENDING |
| S14 | Niger FMNR ~7 Mha by 2017 | Estimate (USGS publication) | PENDING |
| S17/S18 | GGW 2007; 100 Mha target | Official record/target | PENDING |
| S19 | ~4 Mha by 2020 (core zones) | Official self-report | PENDING |
| S21 | Shift to mosaic restoration | Programme description | PENDING |
| P20 | > 230 green periods / 8 Myr | Reconstruction | **AUDITED-INDEX** |
| P23 | Next window ~10,000 years (one scientist) | Expert opinion (attributed) | PENDING |

## To finish the full fact-check

1. **Open the target pages in full.** Either a human does it, or the environment's network policy allows these hosts. This also upgrades P20 and S4-S6 from AUDITED-INDEX to read-in-full.

   | Area | Hosts |
   |---|---|
   | Journals | journals.plos.org, agupubs.onlinelibrary.wiley.com, link.springer.com, www.science.org |
   | NASA | www.nasa.gov, science.nasa.gov, svs.gsfc.nasa.gov, earthobservatory.nasa.gov |
   | Other sources | www.usgs.gov, whc.unesco.org, www.unccd.int, pmc.ncbi.nlm.nih.gov |
   | Publisher, university and press sites | cp.copernicus.org, lamont.columbia.edu, news.uchicago.edu |

2. Find sources for N1 (none yet) and for the secondary-only claims (S1-S3, G17-G19, S21, G4).
3. Do the SCENE-CHECK lines (L1, L3) against real Landsat scenes.
4. The human reviewer decides the two wording notes above (P20 "sediment" vs "geological"; S4 "over the Atlantic").
