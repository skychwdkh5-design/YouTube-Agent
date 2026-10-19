# EP005 claims ledger (rev 2, 2026-10-19)

Rule: three tiers are never mixed in script or on screen. "Primary" = the original outlet or official body.
**Every primary host (reuters.com, bloomberg.com, wsj.com, cnbc.com, semafor.com, neom.com, pif.gov.sa) is blocked
by this environment's network policy (HTTP 403), so no primary article could be opened.** For each claim the URL
below is the best one found by search; the content was read only as search-engine summaries of it or of outlets that
retell it. Confidence reflects that. Nothing here was guessed to fill a gap.

## Tier 1 - original promise
| Claim | Source (date) | Link | Confidence |
|---|---|---|---|
| The Line was announced as a 170 km linear city | widely reported; official NEOM material (not readable here) | https://www.constructionbriefing.com/8036596.article (Apr 2024, retells Bloomberg) | high for "170 km"; year, 9M residents, 500 m height, 200 m width NOT verified - do not use yet |
| First segment "Hidden Marina": 2.5 km long, 500 m high, by the Red Sea | Gulf News (Feb 2025) | https://gulfnews.com/business/property/saudi-arabia-neom-unveils-hidden-marina-as-first-phase-of-the-line-1.500037889 | medium (official unveiling, retold) |
| Cost "more than $50 billion" spent | WSJ post on X (Mar 2025) | https://x.com/WSJ/status/1898659133521326373 | medium (snippet only) |

## Tier 2 - published plans and reports (attribute every one: "X reported")
| Claim | Source (date) | Link | Confidence |
|---|---|---|---|
| Only ~2.4 km of The Line expected by 2030; 2030 residents <300,000 (was 1.5M); linked to PIF not approving the 2024 NEOM budget; anonymous sources/documents | Bloomberg (~8-9 Apr 2024) via Dezeen, AGBI | https://www.dezeen.com/2024/04/09/the-line-neom-scaled-back-dezeen-agenda/ ; https://www.agbi.com/construction/2024/04/saudi-arabia-scales-down-plans-for-170km-line-by-2030 | medium-high (3 independent retellings agree; Bloomberg unreadable) |
| PIF review of NEOM/The Line under way | CNBC (18 Jul 2025) | https://www.cnbc.com/2025/07/18/saudi-arabias-the-line-at-neom-is-reviewed-as-it-considers-its-megaprojects.html | medium (title/snippet only) |
| Active construction workers fell ~35% after Apr 2025; large sections frozen | CNBC via search summary (2025) | same | low-medium |
| NEOM halted work on The Line until at least after 2030; 2030 population target cut to up to 100,000; Trojena investment frozen; PIF shifting to ports/data centres; unnamed sources; NEOM did not reply | Semafor, Matthew Martin (22 May 2026) | https://www.semafor.com/article/05/22/2026/saudis-neom-halts-work-on-the-line-until-after-2030 | medium (Domus notes it is not officially confirmed: https://www.domusweb.it/en/news/2026/05/27/%20the-line-postponed-beyond-2030-neom-saudi-arabia.html) |
| PIF governor Al-Rumayyan (Apr 2026): The Line by 2030 "would be good to have, but it's not a must"; no project cancelled | aggregators only (houseofsaud, aitimeline) | https://houseofsaud.com/neom-2026-the-line-saudi-arabia-status-update/ | low (no mainstream retelling found) |
| Reuters (~4 Oct 2026, two sources): NEOM Stadium shelved indefinitely; no official announcement | stadiumdb, Seoul Economic Daily (13 Oct 2026) | https://stadiumdb.com/news/2026/10/saudi_arabia_futuristic_neom_stadium_project_put_on_hold ; https://en.sedaily.com/international/2026/10/13/saudi-arabia-shelves-neom-stadium-as-megaproject-unravels | medium |
| PIF halted work ~16 Sep 2025 | aggregators | https://kanzotech.com/blog/neom-2026-status-whats-built-vs-delayed/ | low - use "reported to have paused in 2025" only |
| Leaked internal audit: $8.8 trillion to finish | WSJ (early 2025) via blogs | - | low, unverified: do not use |
| "2.4 km of foundations built" | blogs only | - | NOT CONFIRMED: do not use |
| Worker-camp housing aerial photos | Dezeen (10 Nov 2025) | https://www.dezeen.com/2025/11/10/neom-worker-housing-aerial-photos/ | medium |
| Earlier satellite analyses: faint horizontal line in Jun 2023 imagery (Soar); spoil piles and elevations (Mott MacDonald, Nov 2024); Hidden Marina taking shape (Business Insider, Feb 2025) | Middle East Eye; New Civil Engineer (11 Nov 2024); Business Insider | https://www.middleeasteye.net/news/saudi-arabia-neom-line-satellite-images-progress-construction ; https://www.newcivilengineer.com/latest/neom-satellite-imagery-reveals-more-details-and-motts-joins-as-city-infrastructure-engineer-11-11-2024/ ; https://www.yahoo.com/news/satellite-images-show-hidden-marina-174145771.html | medium; the Jun 2023 "faint line" matches our own 2022-2023 observation |

## Tier 3 - what we observed (our own measurements, not interpretation)
| Observation | Evidence | Confidence |
|---|---|---|
| A straight, narrow cleared corridor crosses the area at ~94 deg bearing (about 4 deg south of east), >= 21.9 km inside our 10 m frame (35.10-35.32 E, 28.07-28.15 N); a wider 40 m view suggests ~30 km. Absent in 2020-21, faint in Oct 2022, clear from Oct 2023 | Sentinel-2 L2A 10 m, same relative orbit 78 and season (`evidence_s2/`); Landsat 8 30 m (`evidence/`) | high that it exists and is straight; its length beyond the frame is approximate |
| A dark, green-black linear segment at 35.209-35.224 E, 28.106 N, about 1.4-1.6 km long and ~20-50 m wide: absent 2022 and 2023, present Oct 2024, 2025 and Sep/Oct 2026 | Sentinel-2 (+-10 m), Landsat (~1.65 km, +-30 m) | high |
| Spectrally water-like in 2024-2026 (NDWI > 0, near-infrared reflectance ~0.03): 462 / 829 / 579 qualifying pixels (about 4 / 7 / 5 hectares) in 2024 / 2025 / 2026; zero in 2022 and 2023 | `evidence_s2/dark_stats.json` | medium: consistent with standing water, not proof |
| Roughly equal extent 2025 vs 2026 (~1.6 km); no visible extension of the corridor 2025 -> 2026 at 10-30 m | Landsat + Sentinel-2 | medium |
| Settlement-like complexes near both ends of the frame grow 2020 -> 2024 | `evidence_s2/years_*` | high that they grow; what they are: unknown (Dezeen reported worker camps in the NEOM area) |

## What we may NOT say
- That the corridor or the dark segment "is The Line" or "a building": no primary map placed it (neom.com unreachable); the Wikipedia planning coordinate for the NEOM Stadium (28.116 N, 35.104 E, inside the planned Hidden Marina) lies ~1 km from the corridor, and Soar/MEE reported a faint straight earthwork in June 2023 where we see ours in 2023. That is **consistent with**, not confirmation.
- That the dark segment is water, a lake, a marina, a trench or foundations. Say "water-like in near-infrared; reporters have described water-filled excavation pits in aerial photos, but we cannot confirm that from orbit".
- That the pause is proven by 2025 vs 2026: it is compatible with the Semafor report.
- Any building, height, mirrored facade or population claim.
