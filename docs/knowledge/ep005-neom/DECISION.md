# EP005 decision (2026-10-19, round 2)

## Recommendation: **A - continue NEOM**, as a 6-9 minute "what the satellites show, and what they don't" video.
Nothing is rendered beyond the 15 s silent prototype; no voice, no publish, nothing on main.

### Why A (evidence)
1. **Real, sharp, reproducible evidence now exists.** Sentinel-2 at 10 m (free, via Planetary Computer's data API) shows a straight corridor absent in 2020-21, faint in 2022, clear from 2023, plus a ~1.5 km water-like segment present in Oct 2024-2026 and absent in 2022-23. Seven same-orbit, same-season dates. Round 1 (30 m Landsat) was soft; this is not. See `SENTINEL2.md`, `evidence_s2/`.
2. **The visual material carries a 15 s hook and ~4-5 minutes of motion** (wipes, pushes, year flips, scale changes) - prototype rendered with the existing engine.
3. **Attention is live in October 2026**, including for small channels (Luxified 29K subs -> 494K in 2 weeks; The Invisible Hand 355K in 1 week), after the WSJ video and the Reuters stadium report. See `COMPETITORS_ROUND2.md`.
4. **Differentiation is real:** the small-channel hits are all talk-over-b-roll "collapse" stories; nobody in the 59 videos reviewed shows a same-orbit Sentinel-2 series with measured limits. Business Insider's satellite video (5.0M) proves the format, for a channel 100x bigger.

### What A does NOT have
- Primary sources: Reuters, Bloomberg, WSJ, CNBC, Semafor, NEOM, PIF are blocked from this environment. Tier-2 facts are attributed "X reported" and stay at medium or low confidence. To fix: add those hosts under Allowed domains (environment network settings).
- A match of the corridor with NEOM's own maps (neom.com blocked). Consistency with secondary reporting only.
- Any CTR or retention estimate (needs OrbitalAtlas Analytics; none made). The subscriber count of OrbitalAtlas is still unknown.
- Enough material for 12 minutes. 6-9 minutes is what the evidence supports (`STRUCTURE_6_9MIN.md`).

### Risks to accept knowingly
| Risk | Level | Mitigation |
|---|---|---|
| Crowded topic; a new WSJ/Reuters/Bloomberg story can reset the news cycle | high | publish while the stadium story is fresh; the video is evidence-led and ages slowly |
| The dark segment gets over-interpreted by viewers/commenters | medium | script says "water-like in near-infrared", "we cannot confirm", chapter 6:15 |
| Claim errors on Tier 2 (secondary sources) | medium | attribute each; re-check when primaries become reachable; no number without a source line |
| Title/thumbnail promise exceeds evidence | medium | use "show", never "prove/reveal the truth"; thumbnail states only published number + dates |
| One site, 7 dates: repetitive | medium | scale changes, graphics, pacing checks |
| 500K+ is an upside case, not a baseline | high | judge success on CTR/retention after publish, not on the KPI alone |

## B - alternatives compared (judgment scores 1-5, not measurements)
Criteria from CLAUDE.md. Evidence column is what I actually checked; "not checked" means no satellite or YouTube test was run.

| | NEOM / The Line | Aral Sea | Salton Sea (US) |
|---|---|---|---|
| US audience potential (dominant) | 4: mainstream US news (WSJ, BI) | 3: evergreen, RealLifeLore 4.8M | 4: California, US news, dust/health angle |
| Sweden / Norway / Denmark | 2 | 3 | 2 |
| Visual strength | 4 (Sentinel-2 verified) | 5 (iconic NASA/Landsat time series) but well known | 4 (not checked) |
| Curiosity / click | 4 | 3: saturated explainers | 3 |
| Reliable evidence | 3: strong imagery, weak primaries | 5: decades of public science | 4 (not checked) |
| Free satellite imagery | 5 (checked) | 5 (global Landsat/Sentinel; not checked here) | 5 (same) |
| Monetization suitability | 4 | 5 | 4 |
| Freshness / news hook, Oct 2026 | 5 (WSJ Sep, Reuters Oct) | 2 (no new hook found) | 3 (recent small-channel hits: NBC Palm Springs 276K in 1 month at 7.7K subs; Places 290K in 2 weeks) |

YouTube data behind it (`data/alt_topics.json`): Aral - top hits are old (RealLifeLore 4.8M, 3y; Nas Daily 1.2M, 5y; BBC 1.5M, 11y); recent: Maxojir 584K (12.3K subs, 1y, "Restoration Update 2025"), SLICE 613K (1y, 50:47), Places 395K (1y). Salton Sea - Veritasium 5.5M (11y), recent: Places 290K (2w), NBC Palm Springs 276K (1mo). Great Salt Lake - top hits 0.8-1.9M but 1-6 years old, no recent small-channel hit found.
Reading: Aral is the stronger *visual* story and the safest evidence, but has no fresh hook and the best Aral videos are 3-11 years old and entrenched; the Great Salt Lake and Salton Sea are US-primary (CLAUDE.md's dominant factor). **If NEOM fails the conditions below, the better alternative is the Salton Sea, not the Aral Sea** - not yet verified with satellite frames; a 1-2 hour check would settle it. The Aral Sea is the better *second* episode (evergreen, strong evidence), not the replacement.

### Conditions that would flip the decision to B
- Allowed-domains change is refused AND a second look shows Tier 2 cannot be attributed safely, or
- A primary source (Reuters/Bloomberg/NEOM) contradicts the pause/plan narrative in a way that makes the video wrong, or
- The corridor turns out (via an official NEOM map) to be something unrelated to The Line (e.g. a utility or road project) - then the video would be a different story.
