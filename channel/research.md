# Research and fact-checking

How a claim becomes something the narrator is allowed to say. geo-research builds the ledger,
geo-factcheck verifies it, and `claims.py` is the gate.

## The workflow

```
geo-research ─► claims.md (all UNVERIFIED) ─► geo-factcheck GATE 1 ─► yt-script (tags [C#])
            ─► geo-factcheck GATE 2 (script vs ledger) ─► geo-visuals / yt-package / yt-seo
```

1. **Research** writes every claim into `claims.md` as UNVERIFIED with the best source found.
2. **Gate 1** verifies each row against its source: `claims.py --claims claims.md` exits 0.
3. **Script** tags every factual sentence with its ledger ID: `... through Canada [C3].`
4. **Gate 2** checks the script against the ledger: `claims.py --claims claims.md --script script.md`
   exits 0. Untagged numbers, years, measurements, rankings and superlatives fail it.
5. Anything changed after Gate 2 (a new line in the edit, a Short's new hook) goes back through it.

## What counts as a claim

Population, area, distance, elevation, dates and durations, border positions and status, rankings,
"largest / only / first / last / nobody", statistics and percentages, named causes ("because of a
treaty in 1818"), and comparisons ("bigger than Texas").

## Source tiers

| Tier | What | Examples |
|---|---|---|
| **1 - primary / official** | the body that measures, decides or records it | U.S. Census Bureau (decennial census, ACS, Gazetteer files, TIGER/Line), USGS (GNIS, National Map), NOAA, NASA, U.S. Board on Geographic Names, International Boundary Commission (U.S.-Canada), International Boundary and Water Commission (U.S.-Mexico), state statutes and legislatures, U.S. Supreme Court opinions, Library of Congress, National Archives, treaty texts, national statistics offices (Statistics Canada, INEGI, Eurostat, ONS...), UN Statistics Division, World Bank data |
| **2 - reputable secondary** | careful work that cites its sources | peer-reviewed papers, university research pages, Encyclopaedia Britannica, major newsrooms (AP, Reuters, NYT, WSJ), CIA World Factbook (as a cross-check), official tourism or municipal sites for local facts |
| **3 - leads only** | where to start looking, never the source | Wikipedia, Reddit, forums, YouTube videos, blogs, listicles, social media, AI answers |

Rules:

- A claim cannot be verified on Tier 3 alone. Follow the citation to Tier 1 or 2.
- Superlatives, rankings and "only / first / last" need **two independent sources** (two domains).
- Population and statistics carry their **year** and the **definition** used.
- Prefer the newest official figure; when the newest is an estimate, say "estimated".

## Definitions that cause most errors

- **Area:** total vs land vs water. Census Gazetteer gives both; say which.
- **Population:** city proper vs urban area vs metro (MSA/CSA); census count vs annual estimate.
- **Borders:** de jure (treaty/statute) vs de facto (administered). Maritime vs land.
- **Distance:** straight-line vs driving vs by water. Say which.
- **Elevation:** of the town center vs highest point vs the settlement's lowest house.
- **"Founded":** chartered, incorporated, first settled, or named - four different dates.
- **Exclave vs enclave:** an exclave is cut off from its parent; an enclave is surrounded by one other
  territory. Many places are both - say which you mean.

## The ledger - `claims.md`

| ID | Claim | Type | Source | URL | Accessed | Tier | Status | Final wording |
|---|---|---|---|---|---|---|---|---|
| C1 | what the script will say, precisely | population / area / distance / date / border / ranking / statistic / superlative / other | publisher - document | https://... (several separated by " ; ") | YYYY-MM-DD | 1 (or "1 ; 2") | VERIFIED / SOFTENED / UNVERIFIED / CONFLICT / CUT | the wording the script must use when SOFTENED |

Statuses: **VERIFIED** and **SOFTENED** pass; **UNVERIFIED**, **CONFLICT** and **CUT** block any
script line that uses them.

## Verifying in practice

- Open the page and find the figure yourself. Never verify from a search snippet, memory, or
  another video.
- When a source cannot be reached from this environment, the claim stays UNVERIFIED and the creator
  is asked to check it - it is not marked VERIFIED on trust.
- Record what the source says, not what we hoped it said.
- If sources disagree, use CONFLICT, then soften to what they agree on or cut.

## Lessons

Errors caught after publication, and the rule we added so they cannot recur.

| Date | Video | What was wrong | Rule added |
|---|---|---|---|
