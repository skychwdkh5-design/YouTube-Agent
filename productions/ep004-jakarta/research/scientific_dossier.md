# EP004 Jakarta - scientific dossier (2026-10-15, v2)

Evidence tiers used below:
- **PRIMARY_READ** - I read the source page/full text in this session (ESA x2, Data in Brief via PMC, NASA Earth Observatory, Crossref metadata).
- **SNIPPET** - only a search-engine summary of the page (peer-reviewed or news). Usable for planning, NOT for the script until read.
- **UNREAD** - exists (verified title/DOI) but no content seen.

## Central question
What is happening beneath Jakarta, how can satellites measure it, and can the sinking be slowed?

## 1. What satellites actually show (PRIMARY_READ)
**ESA "Ground motion over Jakarta, Indonesia" (27 Nov 2024)**: mean ground-displacement **rates from Sentinel-1 radar, 2017-2018**; local sinking "reaches around 12 cm per year".
Credit: *Contains modified Copernicus Sentinel data (2019), processed by ESA, GEP, CNR-IREA & BRGM.* Licence: CC BY-SA 3.0 IGO **or** ESA Standard Licence.
The image legend reads **"Sentinel-1 LOS Ground Displacement Rates"**, colour scale about -11 ... 0 ... +5 cm/year. The 2019 companion page says: displacement is
"largely a result of groundwater extraction", "values correspond to **line-of-sight velocities**", local patterns about 12 cm/year; inset over the harbour shows rates > 1.5 cm/yr.
Looking at the image (not georeferenced; a JPG): strongest red clusters are (a) the north-west coast/harbour zone, (b) a west inland blob, (c) a large red blob far to the east
of the city, plus scattered yellow patches. **Where each cluster lies administratively is not stated by ESA and I have not georeferenced it - do not name districts from this image.**
ESA's text also says "researchers suggest parts of the megacity could be entirely submerged by 2050". ESA gives no model/assumptions -> **we do not repeat it.**

**Data in Brief 67:113048 (Shabrina et al., 2026, CC BY 4.0; PMC13380226)**, Sentinel-1 via COMET-LiCS + LiCSBAS, **1 Jan 2016 - 31 Dec 2024**, DKI Jakarta bounding box, ~100 m, LOS:
- Max subsidence in DKI Jakarta **-29.86 mm/yr (LOS, after quality mask)**. Three hotspots: west, north-west (coastal, warehouses and Pantai Indah Kapuk 2 construction), north-east (near Tanjung Priok).
- **"The western region has experienced rapid subsidence since 2016, which has since slowed significantly. The north-eastern and north-western regions ... linear deformation with no significant signs of slowing."**
- Pixels with coherence < 0.6 are masked; **the northern coastal strip (vegetation, sea, construction) fails the filter and is excluded** - i.e. part of the fastest-moving coast is invisible to this dataset.
- Reference pixel assumed stable, **not independently verified**; GNSS check at one station (CJKT): LOS velocity overestimates GNSS vertical by 1.64 mm/yr, RMSE 9.40 mm; GNSS itself noisy (surrounded by tall buildings). Only LOS (no vertical) available because of insufficient descending data. A cited study notes 10 mm/yr unmodelled east-west motion can cause ~8 mm/yr vertical error.
- **Why this differs from ESA's ~12 cm/yr:** different period (2016-2024 vs 2017-2018), different footprint (DKI only vs a wider scene), masking of coherence-poor pixels, ~100 m averaging, and processing. These are not contradictory; they are different measurements. **Never put them on one axis as "the rate".**

**NASA Earth Observatory, "As Jakarta Grows, So Do the Water Issues" (12 May 2021; Landsat 5 9 Jul 1990, Landsat 8 11 Sep 2019)**:
groundwater pumping drives sinking; "by some estimates as much as 40 percent of the city sits below sea level"; metro area 32 million people; at least 1,185 ha of new coastal land since 1990;
**artificial islands are among the fastest-subsiding land (up to ~80 mm/yr, Sengupta)** because fill compacts - i.e. not every sinking spot is groundwater; mean global sea level rise 3.3 mm/yr
(as stated there); 2007 flood: > 70 % of the city submerged. Landsat imagery is shown as urban-growth evidence, not a subsidence measurement.

## 2. Mechanisms and what is NOT proven
Groundwater extraction from the upper confined aquifer -> pore-pressure drop -> compaction of clay/silt -> surface lowering (SNIPPET: Abidin et al. PIAHS 372, 2015; Harintaka 2024).
Other contributors (SNIPPET): load of buildings on compressible young alluvium; natural consolidation of alluvial soil; fill compaction on reclaimed land (PRIMARY_READ, NASA).
Compaction of clay is largely **inelastic: not fully reversible when water returns** - needs a primary source before the script says so (UNREAD; textbook claim, will cite).
Sea-level rise is separate and slower (3.3 mm/yr global, NASA); it is why subsidence matters for coastal flooding, not the cause of subsidence.

## 3. Rates by study (all differ in period, extent, method)
| study | period | what | status |
|---|---|---|---|
| Abidin et al. 2015 review | 1974-2010 | typical 3-10 cm/yr; some sites up to ~20-28 cm/yr | SNIPPET |
| Chaussard, Amelung, Abidin | 2006-2009 ALOS | up to 24 cm/yr across six Indonesian cities (Jakarta max unconfirmed) | SNIPPET |
| ESA map | 2017-2018 S-1 | local ~12 cm/yr, LOS | PRIMARY_READ |
| EGU21-14347 | 2019-2020 S-1A | province +1.8 to -10.7 cm/yr; North Jakarta mean ~-4.9 | SNIPPET |
| Harintaka et al. Geocarto 2024 | 2017-2022 | SBAS; abstracts disagree on "deceleration" vs "linear" | SNIPPET, conflicting |
| Data in Brief 2026 | 2016-2024 | max -29.86 mm/yr LOS masked; west slowed; NE/NW linear | PRIMARY_READ |
| Lapadat/Brouwer/Hanssen (FRINGE 2026 slides; TU Delft record) | 2014-2025 | 3-D InSAR+GNSS; six main bowls; slide figures "~7.7-7.8 cm/yr" max and ~1.1 (or 0.9) cm/yr regional mean - versions disagree | SNIPPET, unstable |
| Hakim et al. 2025 GIScience & RS (doi 10.1080/15481603.2025.2465349, CC BY 4.0) | S-1 2015-2023 | ICOPS+MintPy rate maps + CNN/LSTM susceptibility | SNIPPET (rate figure not seen) |
| Yunus et al. 2026 RSASE (doi 10.1016/j.rsase.2026.102176) "Uncovering land subsidence recovery in the Jakarta metropolitan region, Indonesia, from satellite remote sensing" | not confirmed | heterogeneous subsidence; slowing in some areas; local uplift; continuing coastal subsidence; elastic vs irreversible (qualitative). "-180 -> -70 mm/yr" reported but extent/period unverified | ABSTRACT_VERIFIED (via owner), number blocked |

## 4. Policy and response
- Pergub 93/2021 groundwater-free zones; in force 1 Aug 2023; enforcement criticised (SNIPPET). Pergub 5/2026 (Feb 2026) tightens building groundwater use (SNIPPET).
- SSRN preprint (SNIPPET, correlational, not peer-reviewed): 137,070 PS-InSAR points 2019-2025; **5.4 % of points inside groundwater-free zones sink > 1 cm/yr vs 23.8 % elsewhere**. A PALSAR-2 study (2017-2022) found the zone poorly aligned with where subsidence is worst.
- 2019 conference paper (SNIPPET): rate slowed to ~10 mm/yr when aquifers recharged 2011-2017.
- Piped coverage figures conflict (62 %, ~80 %, 81 %, NGO 35 %) -> not used as fact.
- Sea wall: Jakarta governor targeted Sept 2026 groundbreaking (Jan 2026); a later ANTARA item (search summary) says the national ministry planned an **October 2026 ceremony beginning with mangrove planting; hard infrastructure targeted for 2027**. Not confirmed as having happened. Script wording: "planned".
- Nusantara relocation is context only; not needed for the central question.

## 5. Flooding (interacting hazards)
Jan 2020 event: BMKG recorded 377 mm/day at Halim, highest since 1866 (SNIPPET). A compound-flooding study (SNIPPET) found North Jakarta flooding came from river-inlet overspill when high sea level blocked drainage, not direct sea-wall overtopping. No source separated rain vs tide vs subsidence shares - **we will not assign percentages.**

## 6. What InSAR can and cannot do (for Sequence B)
Can: map millimetre-to-centimetre per-year motion along the satellite's line of sight over wide areas using phase change between repeat radar passes; Sentinel-1 is C-band (wavelength ~5.6 cm; one fringe = ~2.8 cm LOS) (SNIPPET, NGU/Utah).
Cannot: give vertical motion without a model/2nd geometry/GNSS; measure pixels that lose coherence (vegetation, water, new construction) - Data in Brief shows this for the Jakarta coast; reference everything to an assumed-stable point. Optical Landsat/Sentinel-2 do **not** measure cm subsidence.

## 7. Twist (Sequence F) - what the evidence supports today (updated 2026-10-15, after the owner supplied the RSASE abstract)
Three independent layers, in descending strength:
1. PRIMARY_READ (Data in Brief 2026): of three hotspots, the western one slowed significantly after rapid subsidence from 2016; the north-eastern and north-western ones show no sign of slowing.
2. ABSTRACT_VERIFIED (Yunus et al., RSASE 2026, doi 10.1016/j.rsase.2026.102176; summary supplied by the owner, abstract not read by the agent; NOT FULL_TEXT_VERIFIED): the subsidence is heterogeneous; some areas slow
   down; some patches of land rise locally; coastal areas keep subsiding; elastic recovery differs from irreversible compaction. The abstract is reported to cite individual rates falling from about -180 to -70 mm/yr -
   **that number is NOT usable**: its geography, period and measurement type are unconfirmed (it is also much larger than the -29.86 mm/yr maximum in the 2016-2024 Data in Brief dataset, so it must refer to a different extent/period/method).
3. SNIPPET (not scripted): groundwater-free zones sink less (SSRN preprint); recharge-period slowdown (2019 paper).
Safe story: "It is not one sinking city. Satellites show several bowls moving at different speeds; some have slowed, a few spots may even be rising, and the coast keeps sinking. Sinking ground can partly rebound only
when the compaction was elastic - the irreversible part stays." Rules: no uplift location is drawn or named; no -180/-70 figure; "recovery" is said about specific areas, never the city; coastal subsidence is stated next to it.
Open: the full text (extent, period, uplift locations, rates) and whether its figures can be reused (Elsevier, not open access -> no figures).

## Sources
- https://www.esa.int/ESA_Multimedia/Images/2024/11/Ground_motion_over_Jakarta_Indonesia (read 2026-10-15)
- https://www.esa.int/ESA_Multimedia/Images/2019/07/Ground_motion_in_Jakarta (read 2026-10-15)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC13380226/ (Data in Brief, read 2026-10-15); https://doi.org/10.1016/j.dib.2026.113048
- https://science.nasa.gov/earth/earth-observatory/as-jakarta-grows-so-do-the-water-issues-148303/ (read 2026-10-15)
- Crossref metadata for the three mandatory DOIs (read 2026-10-15; licence fields)
- SNIPPET-level: piahs.copernicus.org/articles/372/115/2015/ ; meetingorganizer.copernicus.org/EGU21/EGU21-14347.html ; tandfonline.com/doi/full/10.1080/10106049.2024.2364726 ;
  fringe2026.esa.int/iframe-agenda/files/ID_472.pdf ; papers.ssrn.com/sol3/papers.cfm?abstract_id=7192498 ; thejakartapost.com 2026/02/09 ; en.antaranews.com/amp/news/434454 ; PBS/Jakarta Post flood items
