# Episode 001: source audit, round 6 (2026-10-08): Kemena et al. (G5, G6, G6b)

Not a full fact-check and not a script lock. Only G5, G6 and the new G6b were changed.

## Source and metadata

| Item | Finding | Verified how |
|---|---|---|
| File | `Kemenaetal_2017.pdf`, 28 pages; no journal header, no DOI, no page numbers of the journal; embedded name `Kemenaetal_161011_finalform_without_fieldfunctions.docx`; PDF created 2018-07-16 | `pdfinfo`, read in full |
| Title in the file (manuscript) | "Atmospheric Feedbacks from an Irrigated, Afforested Sahara in Northern Africa" | PDF p.1 |
| Authors | Tronje Peer Kemena, Katja Matthes, Thomas Martin, Sebastian Wahl, Andreas Oschlies (GEOMAR Helmholtz Centre for Ocean Research Kiel; Christian-Albrechts-Universität zu Kiel) | PDF p.1 |
| Journal version | Climate Dynamics 50(11-12): 4561-4581, doi:10.1007/s00382-017-3890-8; title there is "Atmospheric feedbacks in North Africa from an irrigated, afforested Sahara" | **Not verified at the source.** Taken from a GEOMAR repository listing and a CDR-bibliography entry (2017-09-18) that appeared in a search; I could not open the DOI page: `doi.org` redirects to `link.springer.com`, which returns an anti-bot challenge, and Crossref and the GEOMAR repository are blocked from this environment. One search result gave a different volume and year, so this stays UNCONFIRMED. |
| Year | The file is the **2017 manuscript**. A journal version with volume 50 is described as a **2018** publication; the online date was not seen. Spoken narration says "A later study" (reviewer decision). | Reviewer to confirm on the DOI page |
| Manuscript vs final | Numbers in the abstract and text of the manuscript match the figures already in our ledger (−6 K, +267 mm/yr, 26%), but the journal version could differ in details. | Not checked against the journal PDF |

## Verified findings (all MODEL results; page / manuscript line)

| ID | Result | Where |
|---|---|---|
| G5 | Saharan mean surface-air temperature: −6.3 K (abstract: 6 K); regionally up to −8 K west and about −4 K east; global mean −0.04 K | p.5 l.190-194 |
| G5 | Mean precipitation +267 mm/yr (control 52, forest run 319); about +200 mm/yr in the western Sahara, weak in the east; "weak" and "much smaller compared to earlier studies" (Bowring 2014: +1,000 mm/yr winter, +365 summer; Ornstein 2009: about +1,000 mm/yr over half the Sahara) | abstract p.1; p.6 l.212-220; p.7 l.284-288 |
| G6 | Evapotranspiration 1,238 mm/yr (90% transpiration, 1,112 mm) against precipitation 319 mm/yr: "only 26% of the deployed water is recycled" | p.7 l.289-296; Fig. 4 (p.21) |
| G6 | The rest is advected south to the Sahel zone, the Guinea coast and the tropical Atlantic; August monsoon maximum moves about 400 km north (10°N to 14°N) and strengthens by 48% | p.6 l.208-211; p.8 l.335-338 |
| G6b | Desalinated water required: 919 mm/yr (6.9×10¹² m³/yr); effective irrigation 2,625 mm/yr, 65% lost to drainage in the model's scheme (observed losses are lower) | p.7 l.268-281 |

## Model assumptions and limits
CESM 1.0.2 with WACCM4, grid 1.9°×2.5°, 66 levels; two simulations (control, afforested), 50 years each, the first 20 spin-up; CO₂ fixed at 1960 (so no carbon-uptake effect, and no test of Ornstein's carbon claim G2); tropical broadleaf evergreen trees fully grown at the start; interactive irrigation scheme (factor 70%); no ensemble, no uncertainty range; the control run's monsoon has biases (weak, early coastal rain; a possible double ITCZ; jet about 4° too far north). The authors describe their analysis as qualitative and say results may differ with other models (p.13 l.581-583; p.15 l.669-675). They state the self-sustainability indicator as 26% of "deployed water" recycled, and that most moisture goes south, "which would lead to higher desalination and pumping costs" (p.13 l.573-575). Nothing in the paper shows that producing or delivering the desalinated water is technically or economically demonstrated.

## The 26% explained
It is a ratio of two area-mean totals, 319 / 1,238 mm/yr. The 319 includes the 52 mm/yr that fall in the control run without a forest, and evapotranspiration includes evaporation from soil and canopy as well as transpiration. No water is tracked molecule by molecule. A difference-based figure (+267 / +1,186 mm/yr) is about 22.5% (our own arithmetic, not stated by the authors). The script therefore says "a ratio of totals, not a tracked drop of water".

## Changes made
- `script.md` v0.4, ACT 5 paragraph "Would it rain?": "A later study..."; 6.3 °C / 11 °F; 267 mm/year / 10 inches; "weak"; totals 1,238 and 319; "That's a ratio of totals, not a tracked drop of water"; moisture carried south to the Sahel and nearby ocean; 919 mm / 36 inches of desalinated water; "The model simply assumes that water is supplied; whether it could be produced and delivered at that scale is not something the simulation shows. That's one simulation, not a measurement." Tags: G5 ✓, G6 ✓, G6b ✓.
- `storyboard.md` v0.4, scene 25: stacked water-budget bar (1,238 = 319 rain + 919 desalinated), separate "+267 mm/yr" label, separate "26% ratio of totals" label, optional "−6.3 °C" callout, permanent model-assumption footer; no cost and no "solution" framing.
- `claims.md`: G5, G6 rewritten; G6b added; header table updated. `missing_sources.md`: publication 2 marked received.
- Unchanged: the opening hook and every unrelated claim.

## Status
G5: VERIFIED with qualifications. G6: VERIFIED with qualifications. G6b: VERIFIED as a model assumption. Open: confirm the journal metadata and that the journal version has the same numbers.
