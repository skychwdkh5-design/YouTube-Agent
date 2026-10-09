# Episode 001: source audit, round 9 (2026-10-08): final corrections and SCRIPT LOCK v1.0

## A. Corrections applied (exact old and new wording)

| ID | Before | After |
|---|---|---|
| P20 (ACT 2) | "Geological records, mostly marine and desert sediments, point to more than 230 green Sahara periods..." | "Geological records, mainly layers of Mediterranean seabed mud laid down when African monsoon floods surged into the sea, point to more than 230 green Sahara periods in the last 8 million years. That's a reconstruction, not 230 events anyone observed." |
| S21 | "a patchwork of restored farmland, pasture and forest" | "a mosaic of different land uses, including regrown vegetation and water-holding measures" |
| S19 | "a preliminary UN assessment counted about 4 million hectares restored" | "a UN report, based on figures reported to the Wall's own agency, counted about 4 million hectares restored inside its core zones" |
| G14 | "No study has modeled it for a planted Sahara." | "That's a hypothesis, and we found no study that models it for a planted Sahara." |
| P19 | "retreating gradually southward over two to three thousand years" from "dated lake and river sediments" | "retreating southward over about two to three thousand years" from "dated lake, marsh and river sediments" |
| P5 | "Climate models struggle to reproduce all the rain that geologists think fell on the Sahara..." | "Climate models struggle to produce enough rain to fill all the lakes that geologists think the Sahara once had..." |
| P8 | "...For scale, NASA puts the Kufra district of Libya at about one millimeter of rain a year today." | sentence removed |
| P24 | "more tropical cyclones in both hemispheres" | "more tropical cyclone activity in both hemispheres" |
| Sahel (first mention, ACT 5) | "over the Sahel and the nearby ocean" | "over the Sahel, the semi-arid band just south of the Sahara, and the nearby ocean" (source: NASA EO "Vegetation and Rainfall in the Sahel"; recorded under S12) |
| COP21 | "a pledge made at the COP21 climate conference" | "a pledge made at the UN climate conference known as COP21" |
| ACT 5 structure | one 239-word paragraph (Ornstein rain, Kemena, totals, water) | three short paragraphs: Ornstein rain (G1b); "A later team..." with the two rainfall numbers kept apart (G5); "And the forest wouldn't water itself..." with totals, Sahel, desalinated water, assumption and "That's one simulation, not a measurement." (G6, G6b); then the new transition line |
| Transition | none | "But the biggest changes may not be in the Sahara at all." (framing, no fact; storyboard scene 25b) |
| NASA wording | "NASA reports more than 15,000..."; two "NASA says" in one passage | "a World Heritage site, there are more than 15,000 prehistoric etchings and illustrations" (P14); one "NASA says" for the aquifer sentence (G18). Attributions kept where the claim depends on NASA (P10, N1, P23). |

Preserved unchanged: the opening hook; G1, G1b, G2, G4, G5, G6, G6b and P24 values and qualifications (6.3 °C, 267 mm/yr, about 26%, 1,238 and 319 mm/yr, 919 mm/yr, more than 1,000 mm/yr over about half of the irrigated area, shrubs, dust cut by up to 80%).

## B. Kemena source decision (recorded)
The complete author manuscript (Kemenaetal_2017.pdf, 28 pages, read in full) is accepted as the supporting source for G5, G6 and G6b. The published journal PDF was not accessible and was not compared with the manuscript. This audit does not claim the two are textually identical and does not present the journal metadata (Climate Dynamics 50(11-12):4561-4581, 2018, doi:10.1007/s00382-017-3890-8) as verified by full-text inspection: it comes from a repository record seen in search results, and another listing gave a different year and volume.

## C. Final claim audit
- 47 claim IDs in the narration; every ID has a row in `claims.md` marked VERIFIED, or HYPOTHESIS for G14. 0 missing, 0 ⛔, 0 ⚠, 0 ✎.
- Every number in the narration was traced to a source row: 1,000 / 40 (G1b); 6.3 / 11 / 267 / 10 / 1,238 / 319 / 919 / 36 (G5, G6, G6b; unit conversions checked: 6.3 K = 11.3 °F, 267 mm = 10.5 in, 919 mm = 36.2 in); 182 / 28 / 22,000 (S4-S6); 2,500 / 1,600 (S7b); 100 / 450 / 4 / 18 (P8); 11,000 / 6,000 (P2); 230 / 8 million (P20); 7,000 (P10); 200 (P12); 15,000 (P14); 50 m / 160 ft / 300 km / 190 mi (P18); 10,000 to a million (L2/G18); 1984 (L1); 2002 / 2012 / 2021 (L3); 2009 (G1); about a century (G2); 2007 / 100 / 25 / 4 million hectares / 2020 / 2030 (S17-S19); 5 / 7 million hectares and 12 / 17 million acres (S14).
- Source-string check against the full texts read (NASA EO, Larrasoaña, Sereno, UNCCD report, Davies, Ornstein, Pausata): all phrases the narration relies on are present.
- Contradictions between script, storyboard and claims: none found. Storyboard changes this round: scenes 2, 10, 13, 14, 25, new 25b, 31, 32, 34.
- Stale phrases checked absent from the narration and storyboard: "mostly marine", "gradually", "all the rain", "No study has", "patchwork", "COP21 climate", "NASA reports", the Kufra comparison, "preliminary UN assessment", "tropical cyclones in both", all numbers of removed claims (400,000, 150,000, 9.2M, 0.16, 1,450, $2, 10,000 years).
- Rhetorical lines without IDs (not factual claims): "But this time, what you'd change thousands of miles away is the part that's easy to miss", "But first, the Sahara that was already green", "Now, the part that's easy to miss", "But the biggest changes may not be in the Sahara at all", "So the real question isn't whether the desert can be green. It's whether we should be the ones to flip the switch", and the subscribe line.

## D. Result
No unsupported narration, no blocked factual claims and no unresolved scientific contradiction remain. **SCRIPT LOCK v1.0** is recorded in `story/SCRIPT_LOCK.md` (word count 1,777; about 12.3 minutes; hash recorded there).
