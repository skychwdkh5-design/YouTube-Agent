# Competitor analysis - EP004 (produced 2026-10-15)

**Method and honest limits.** Metrics = YouTube search-result cards read with `curl` on **2026-10-15 05:3x-05:4x UTC** (view count, duration, relative age).
Thumbnails = `i.ytimg.com/vi/<id>/maxresdefault.jpg`, downloaded and actually looked at. **Not available in this container:** YouTube watch pages
(redirect to a Google "sorry" bot check - I did not try to bypass it), captions/transcripts, the video streams. Therefore the columns "first-5-s hook",
"first-30-s structure", "motion style", "scene density", "open loops", "ending" are **NOT OBSERVED** and are left empty on purpose: nothing was inferred from
thumbnails. Publication age is YouTube's relative wording ("5y ago"), not an exact date. View counts are observed performance, not causal evidence.
Metrics were read once; a re-snapshot is cheap (`tools/ytsearch.py` pattern, see data_provenance.md).

## Channels covered (12 of the brief's list + 2 extra)
Vox, neo, fern, The B1M, Geography By Geoff, RealLifeLore, Wendover Productions, Practical Engineering, City Beautiful, Half as Interesting (extra), BBC (extra),
DW News (extra). **Urbana:** a search for the channel returned no matching channel/video - not verified, not used.

## Videos with >= 500,000 observed views (19)
| # | channel | exact title | URL | duration | age (rel.) | views @2026-10-15 | thumbnail concept (observed) | title promise |
|---|---|---|---|---|---|---|---|---|
| 1 | Vox | Why Jakarta is sinking | https://www.youtube.com/watch?v=Z9cJQN6lw3w | 11:19 | 5y | 4,977,746 | split frame: orbital map with "Jakarta" label + photo of man standing in flood water | a cause ("why") for the exact city |
| 2 | BBC | Jakarta is sinking! - Equator from the Air - BBC | https://www.youtube.com/watch?v=qOSwBIstZUs | 6:37 | 7y | 3,840,087 | big red "JAKARTA IS SINKING"; man on sea wall beside a half-submerged building (real photo) | statement + aerial tour |
| 3 | The B1M | This Megacity is Sinking 75x Faster Than Venice | https://www.youtube.com/watch?v=B7PHRVQgTKM | 14:14 | 1y | 1,887,854 | 3-D render of planned island city, arrow + "THIS IS MAD." | comparison multiplier |
| 4 | RealLifeLore | Why Indonesia is Moving Their Capital City | https://www.youtube.com/watch?v=t9p1bS1ThwY | 18:27 | 4y | 4,713,255 | relief map, red route arrow Jakarta -> Borneo, "NEW CAPITAL" | a decision explained by geography |
| 5 | DW News | Why Indonesia is spending billions to build its new capital Nusantara | https://www.youtube.com/watch?v=DVX7c3kmisA | 11:39 | 4y | 1,374,985 | architectural render + "$33 billion" | money figure |
| 6 | fern | The Netherlands is a Giant City | https://www.youtube.com/watch?v=cShCsp0mdPM | 9:34 | 3y | 1,382,627 | Netherlands shape with red 3-D New York overlay, two labels, arrow | scale comparison with a US anchor |
| 7 | Practical Engineering | Why are the Dutch So Good at Waterworks? | https://www.youtube.com/watch?v=qQCB3N8Vaxk | 22:20 | 1y | 3,428,591 | top-down photo of a road on a lens-shaped island, no text | curiosity from an odd real structure |
| 8 | Practical Engineering | The Bizarre Paths of Groundwater Around Structures | https://www.youtube.com/watch?v=bY1E2IkvQ3k | 14:02 | 4y | 14,260,645 | presenter holding a see-through sand tank with dyed flow lines, "GROUNDWATER IS WEIRD" | physical model of the hidden mechanism |
| 9 | neo | The Densest City on Earth | https://www.youtube.com/watch?v=4YuNvIfM-YA | 17:49 | 3y | 13,032,076 | red background, 3-D block model "KOWLOON WALLED CITY" | superlative + one object |
| 10 | neo | Why Egypt Is Building a New Capital City | https://www.youtube.com/watch?v=9-ThusbaRW8 | 15:23 | 4y | 6,482,914 | satellite-style map with two speech-bubble labels "CAIRO", "NEW CAPITAL" | why (decision) |
| 11 | Vox | Who made these circles in the Sahara? | https://www.youtube.com/watch?v=twAP3buj9Og | 27:08 | 4y | 9,205,090 | aerial desert pattern, "WHO MADE THESE?" + arrow | mystery visible from above |
| 12 | Geography By Geoff | Why Nobody Lives on Indonesia's Largest Island | https://www.youtube.com/watch?v=ZeOMfTIq2fA | 18:29 | 2mo | 1,715,317 | map, one region red, "UNLIVABLE", arrow | paradox |
| 13 | Geography By Geoff | Why Planes Avoid The South Atlantic | https://www.youtube.com/watch?v=EEQ7hvXj0RE | 12:46 | 1y | 1,477,140 | map, circled empty area "NO PLANES", "WHY?" | gap on a map |
| 14 | The B1M | Japan's $40BN Kansai Airport is Sinking | https://www.youtube.com/watch?v=ec37fkICRF8 | 12:27 | 2y | 2,580,210 | aerial of artificial island, "8.2 METRES AND STILL SINKING" | one measured number |
| 15 | City Beautiful | A Brief History of U.S. City Planning | https://www.youtube.com/watch?v=2Q5bICcek6s | 14:31 | 7y | 1,210,381 | antique city view, "History of Cities" | history overview |
| 16 | Wendover Productions | The Surprising Success of Gondola Transit Systems | https://www.youtube.com/watch?v=a5126u88E7E | 23:27 | 1y | 1,532,290 | aerial city with cable-car overlay map, "THE RISE OF URBAN GONDOLAS" | surprising success |
| 17 | Vox | How China is designing flood-resistant cities | https://www.youtube.com/watch?v=nf-Yy3EuZi0 | 6:50 | 2y | 1,744,330 | aerial park, "SPONGE CITY" | named concept |
| 18 | Half as Interesting | Why Venice's New EUR 8 Billion Flood Barrier Only Kinda Works | https://www.youtube.com/watch?v=ubzTs8ybYZM | 6:51 | 3y | 510,493 | illustrated map, "78 MOVING SEA WALLS" | number + "only kinda works" |
| 19 | Evan Edinger | Mexico City Has a Problem You Can See from Space | https://www.youtube.com/watch?v=tYbb-jaWzWE | 10:49 | 3mo | 725,849 | presenter beside stone steps, arrow: "This used to be street level" | physical proof of subsidence |

Below the threshold but directly on topic: Half as Interesting "How Indonesia Is Accidentally Sinking Their Capital" pF1OkiOBsUQ (6:47, 11mo, 267,820 views; illustrated
cross-section, "WORLD'S FASTEST SINKING CITY"); Geography By Geoff "Why Indonesia Is Building A Brand New Capital City (It's A Disaster!)" Ihv_YLDF3PM (15:07, 1y, 273,317).

## Fields left empty (see method)
hook_0-5s, first_30s_structure, central_question (only title-level promise recorded), visual evidence used, motion graphics style, scene density, open loops/payoffs,
ending: **NOT OBSERVED** for all rows. To fill them the owner can paste transcripts / chapter lists, or the container needs a transcript route (see report).

## What the title/thumbnail layer does show (observation, not causation)
- 14 of 19 thumbnails are built on ONE geographic object (map, aerial, render or model) plus 0-5 words of text; 9 add an arrow or circle pointing at the thing.
- Real photographic proof objects appear in 4 (BBC mosque, Vox flood, Edinger steps, Practical Engineering tank).
- Length of videos in this set: 6:37-27:08; the 6:3x-6:5x group (BBC, Vox China, HAI x2) shows that a 7-9 minute episode is within what performs.
