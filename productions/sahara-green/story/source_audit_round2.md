# Episode 001: source audit, round 2 (2026-10-08)

Adds to `source_audit.md` (round 1). Nothing in `script.md`, `claims.md` or the storyboard was changed. The narration is **not** approved and the fact check is **not complete**.

## Method

Each page below was fetched in full over HTTPS (curl through the agent proxy) and the page text was searched for the exact numbers. No search snippet is used as evidence. Where a primary paper stayed unreachable (Nature, Science, PNAS, Springer, Wiley, USGS, PMC: proxy 403 or anti-bot challenge), the claim stays **BLOCKED** and says so.

- Spoken words in `script.md`: **1,374**. Method: all lines under the headings, minus Markdown headings, the intro lines and every `[...]` tag. The preproduction figure of 1,386 is off by 12.

| Status | Meaning |
|---|---|
| VERIFIED | Number, units and wording are in a source read in full. |
| NEEDS_REVISION | The source was read and contradicts or does not contain part of the narrated wording. |
| REJECTED | The source contradicts the claim. None this round. |
| BLOCKED | The primary source could not be read, or only part of the claim is covered. |

## Results (19 claims checked)

### VERIFIED (12)

| ID | Original wording | Source read in full | Exact evidence | Evidence type | Correction / note |
|---|---|---|---|---|---|
| P20 | "more than 230 times in 8 million years" | Larrasoaña, Roberts & Rohling 2013, PLoS ONE 8(10): e76514, https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0076514 (Abstract; "Timing of green Sahara periods since 8 Ma") | "enables identification of over 230 GSPs within the last 8 million years"; "we take eastern Mediterranean sapropels ... as markers of over 230 GSPs back to 8 Ma". Each period "took 2-3 kyr to develop, peaked over 4-8 kyr ... ended within 2-3 kyr". | RECONSTRUCTION. The count is inferred from sapropel layers used as markers, not 230 observed green phases. | Keep "suggest" (ACT 2). The cold open states it flatly; recommend "more than 230 times, by one reconstruction". |
| S4 | "about 182 million tons of Saharan dust blow out over the Atlantic every year" | NASA SVS 4273, https://svs.gsfc.nasa.gov/4273/ (same text on SVS 11775) | "wind and weather pick up on average 182 million tons of dust each year and carry it past the western edge of the Sahara at longitude 15W" (CALIPSO, 2007-2013). 132 Mt remain airborne at 35W. | SATELLITE-DERIVED ESTIMATE (CALIPSO lidar plus transport estimate). | Number matches. Safer wording: "leave the Sahara's western edge". Underlying paper (GRL, Wiley) not read. |
| S5 | "roughly 28 million tons settle on the Amazon basin" | SVS 11775, https://svs.gsfc.nasa.gov/11775/ | "An average of 27.7 million tons of dust per year ... fall to the surface over the Amazon basin." | Satellite-derived estimate. | The 8-48 Mt range from round 1 is in the paper only; not re-read. |
| S6 | "an estimated 22,000 tons of phosphorus a year, about as much as the rainforest loses to rain and floods" | SVS 11775 | "The phosphorus portion, an estimated 22,000 tons per year, is about the same amount as that lost from rain and flooding." The phosphorus share is estimated from Bodélé samples plus Barbados and Miami stations (SVS 4273). | Estimate built on an estimate. | This is delivery, not uptake by plants. |
| S7 | "One of the biggest sources is here: the Bodélé Depression" | NASA EO 146011, https://science.nasa.gov/earth/earth-observatory/bodele-dust-146011/ | "among the world's most prolific sources of atmospheric dust. According to one estimate, it generates about half of the mineral dust that leaves the Sahara Desert." | Observation plus estimate. | See Risk R1 (Amazon framing). |
| S9 | "dry floor of old Lake Mega-Chad, covered in the fossil skeletons of tiny algae" | NASA EO 146011 and 147816, https://science.nasa.gov/earth/earth-observatory/another-dusty-day-in-chad-147816/ | Bodélé was "the northernmost part of Lake Megachad"; dust is "mostly ... quartz and the remains of ancient diatoms". | Observation / geology. | "Covered in" is loose; "dust made of" is closer. |
| S17 | "In 2007, African nations launched the Great Green Wall" | UNCCD, https://www.unccd.int/our-work/ggwi | "Launched in 2007 by the African Union". | Official record. | |
| S18 | "aiming to restore 100 million hectares of land by 2030" | Same page; UNCCD 2020 report (PDF, 68 pp.) | "ambition is to restore 100 million hectares of currently degraded land". | Official target. | Report p.22: the PA-GGW itself aims at **25 Mha**; 100 Mha is the COP21 pledge. Keep "the initiative's ambition". |
| S19 | "By 2020, the official count inside its core zones was about 4 million hectares" | https://www.unccd.int/sites/default/files/2024-08/1551_GGW_Report_ENG_Final_040920.pdf, section 3.3, p.22 | "only 4 Mha (4%) of this target has been reached by now"; "nearly 17.8 Mha" for the wider region. | Official self-report, preliminary. | Say "preliminary". The 17.8 Mha must not be shown as Wall progress. |
| S21 | "shifted from a literal wall of trees to a patchwork of restored land" | Same report, p.29 | "originally conceived as a green barrier ... adjusted its vision to become a mosaic of resilient land use systems". | Programme description. | Matches. |
| L2 | "water that soaked into the ground ... thousands of years ago or more"; Kufra on the same water | NASA EO 152356, https://science.nasa.gov/earth/earth-observatory/water-beneath-the-sand-152356/ | Fossil water "percolated ... anywhere from 10,000 to 1,000,000 years ago"; Kufrah farms use the Nubian Sandstone Aquifer. | Observation plus interpretation. | "Thousands ... or more" is an understatement; "at least 10,000 years" is exact. |
| G19 | "In the 1980s, Libya began building the Great Man-Made River" | Same page | The pipes "were constructed in the 1980s and 1990s". | Historical record. | The exact year 1984 is not on this page. |

### NEEDS_REVISION (2)

| ID | Original wording | Source read in full | Exact evidence | Evidence type | Correction |
|---|---|---|---|---|---|
| N1 | "...then sinks over the subtropics, warming and drying as it falls." | NASA EO 85843 (Cloudy Earth), https://science.nasa.gov/earth/earth-observatory/cloudy-earth-85843/; NASA EO 3973, https://science.nasa.gov/earth/earth-observatory/southeastern-australia-3973/ | "Hadley cells are defined by cool air sinking near the 30 degree latitude line"; "descending air inhibits cloud formation. Since air descends between about 15 and 30 degrees north and south of the equator, clouds are rare and deserts are common at this latitude"; "air has cooled and lost most of its water". | Established physics (textbook). | Core claim supported. "warming and drying as it falls" is not stated in these pages (NASA says the air arrives already dry). Replace with "dry air sinks". |
| L3 | "NASA measured them at up to about 1,450 square kilometers ... By 2012 they had shrunk by roughly 80 percent." | NASA EO 149334, https://science.nasa.gov/earth/earth-observatory/two-decades-of-change-at-toshka-lakes-149334/ | Page has no 1,450 km², no 80 percent and no "late 1990s". It says: lakes "full in 2002"; "by 2012 ... mostly dried up"; Nov 2021 "more water than ever before". Images are astronaut photographs, not measurements. | Satellite/astronaut observation. | The numbers cannot be attributed to this NASA page. Either find the source of 1,450 km² and 80%, or measure from our Landsat scenes, or drop them. "Full again by 2021" is supported. |

### BLOCKED (5)

| ID | What was read | Why blocked |
|---|---|---|
| G4 | Only the UNCCD web search and NASA/UNCCD pages. | (Superseded in round 7: the $2 trillion figure is NOT in Ornstein et al. 2009 and was removed from the episode.) The round-2 text said it was the authors' estimate in Climatic Change 97:409. link.springer.com is behind an anti-bot challenge and `WebFetch` cannot resolve it. UNCCD publications cover other numbers (e.g. $878 billion a year of losses in its 2024 assessment, per its search results) and do not support $2T. Keep it as "the authors' estimate", unconfirmed. |
| G17 | NASA EO 89820 and 152356 name the aquifer. | Neither gives 150,000 km³. IAEA/UNESCO/USGS sources unreachable. |
| G18 | EO 89820: the aquifer "recharges slowly and is considered a non-renewable resource". | Supports "barely refilled" in spirit; "effectively zero" needs the primary hydrogeology paper. |
| L1 | EO 89820: agriculture began in the 1980s; crops visible in 1999 and 2001 images; pivots watered from the aquifer. | "Bare desert in the earliest Landsat" and "~1 km" circles are not on the page. These are SCENE-CHECK lines and need the actual scenes. |
| P10 | EO 146011: Lake Megachad "spanned an area larger than all the Great Lakes combined", "the world's largest lake at the time". | The 400,000 km² figure needs Drake & Bristow 2006 (The Holocene, paywalled). The qualitative claim holds. |

## Scientific risks found

- **R1. Bodélé and the Amazon.** EO 147816: recent research finds "most of the dust that does reach the Amazon comes ... from El Djouf" in Mauritania and Mali, about 2,500 km west of the Bodélé. In ACT 6 the Bodélé sentence follows the Amazon numbers, so a listener will hear that the Bodélé feeds the Amazon. The sentence "Green the Sahara, and much of that dust could disappear" is a hypothesis with no source in the ledger. Recommend: cut "much of that dust could disappear" or attribute it as an open question, and name El Djouf or drop the Bodélé from that paragraph.
- **R2. Toshka numbers** have no NASA source on the cited page (see L3).
- **R3. 230 periods** is an inference from Mediterranean sapropel layers, not 230 observed greenings.
- **R4. S18** mixes the COP21 pledge (100 Mha) with the PA-GGW target (25 Mha).
- **R5. Dust figures** rest on one CALIPSO study (2007-2013). The paper itself was not read.

## Not yet checked (primary source unreachable or not tried)

S1, S2, S3, P2, P11, P12, P14, P8, L4, P18, P3, P5, P17, P19, G1, G2, G5, G6, G8, G20, G10, G11, G14, P24, S12, S13, S14, P23.
Hosts that still refuse reads: nature.com, science.org, pnas.org, ipcc.ch, nasa.gov (www), noaa.gov, weather.gov, pubs.giss.nasa.gov, ntrs.nasa.gov, cp.copernicus.org, link.springer.com (challenge), Wiley/AGU (challenge), usgs.gov (403), whc.unesco.org (challenge), PMC (reCAPTCHA), census.gov, britannica.com, eos.org, lamont.columbia.edu, news.uchicago.edu, bristol.ac.uk, umdrightnow.umd.edu, ess.uci.edu.
