# Release package - Here's What Satellites Show Near the Construction Site (working title, not final)

Generated 2026-10-21T15:37:08Z. Nothing is published.

## Status
- topic: done owner-approved topic
- research: done 20 claims (15 usable), factual capacity about 5.6 min - INSUFFICIENT_FOR_6_MIN
- facts: done 20 claims, registry ok
- evidence: done 2 stacks + Landsat stack(s) + NDWI series
- script: done 943 words = 6.4 min, 16 claims used
- media: done 0 verified of 5 media entries (style v2: media optional)
- visualplan: done 62 visuals in 9 chapters, graphics ['g_scale', 'g_reports', 'g_tiers', 'g_cmp_2022_2026_c10', 'g_hero_c10', 'g_cmp_2025_2026_c12', 'g_cmp_2020_2024_c17', 'g_cmp_2020_2024_c19', 'i_scale', 'i_bloomberg', 'i_semafor', 'i_reuters', 'i_opened', 'i_described', 'i_source', 'i_orbit', 'i_season', 'i_cloud', 'i_ndwi', 'i_landsat', 'i_lengths', 'i_apart', 'i_growth', 'i_verdict', 'i_cannot', 'i_nomatch']
- visuals: done 60 graphics
- storyboard: done 66 shots, 385.312s, timing from voice
- visualcheck: done visual claims OK {'VERIFIED_SOURCE': 6, 'VERIFIED_DATA': 40, 'REVIEWED': 40} of 86 items; 21 orphan reviews (run `visualcheck.py prune`)
- voice: done narration already generated (not regenerated)
- voicecheck: done NEEDS_HUMAN_LISTEN: 21 risky words to listen to; storyboard re-timed from real word timings
- captions: done captions built from real word timings
- render: awaiting_approval approval present but --allow-render not given; plan validated
- qc: waiting waiting for ['render']

## Autonomy (what was automated)
- topic: AGENT_REQUIRED / now AGENT_REQUIRED / agent artifact, then code
- research: AGENT_REQUIRED / now AGENT_REQUIRED / agent artifact, then code
- facts: FULLY_AUTOMATED / now FULLY_AUTOMATED / code
- evidence: FULLY_AUTOMATED / now FULLY_AUTOMATED / code
- script: AGENT_REQUIRED / now AGENT_REQUIRED / agent artifact, then code
- media: AGENT_REQUIRED / now AGENT_REQUIRED / agent artifact, then code
- visualplan: FULLY_AUTOMATED / now FULLY_AUTOMATED / code
- visuals: FULLY_AUTOMATED / now FULLY_AUTOMATED / code
- storyboard: FULLY_AUTOMATED / now FULLY_AUTOMATED / code
- visualcheck: FULLY_AUTOMATED / now FULLY_AUTOMATED / agent artifact, then code
- voice: OWNER_REQUIRED / now OWNER_REQUIRED / code
- voicecheck: FULLY_AUTOMATED / now FULLY_AUTOMATED / code
- captions: FULLY_AUTOMATED / now FULLY_AUTOMATED / code
- render: OWNER_REQUIRED / now OWNER_REQUIRED / -
- qc: FULLY_AUTOMATED / now FULLY_AUTOMATED / -
- release: FULLY_AUTOMATED / now FULLY_AUTOMATED / -

## Title options (working title approved by owner; not final)
- Here's What Satellites Show Near the Construction Site
- Saudi Arabia Promised a 170 km City. Here's What Satellites Show.
- We Checked The Line From Space: 170 km Promised, This Is What's There

## Claims ledger
- C1 [original/medium] The Line was announced as a 170 km linear city. (Construction Briefing (with Dezeen, AGBI), 2024-04-09, https://www.constructionbriefing.com/8036596.article)
- C2 [media/medium] Bloomberg reported (Apr 2024) only about 2.4 km of The Line expected by 2030 and fewer than 300,000 residents. (Bloomberg via Dezeen, 2024-04-09, https://www.dezeen.com/2024/04/09/the-line-neom-scaled-back-dezeen-agenda/)
- C3 [media/medium] Semafor reported (22 May 2026) that NEOM halted work on The Line until at least after 2030, citing unnamed sources. (Semafor, 2026-05-22, https://www.semafor.com/article/05/22/2026/saudis-neom-halts-work-on-the-line-until-after-2030)
- C4 [media/medium] Reuters reported (about 4 Oct 2026, two sources) that the NEOM stadium was shelved indefinitely, with no official announcement. (Reuters via Seoul Economic Daily, 2026-10-13, https://en.sedaily.com/international/2026/10/13/saudi-arabia-shelves-neom-stadium-as-megaproject-unravels)
- C5 [org/low] The PIF governor said completing The Line by 2030 would be good to have, but is not a must. (House of Saud (aggregator), 2026-04-01, https://houseofsaud.com/neom-2026-the-line-saudi-arabia-status-update/)
- C6 [media/low] Dezeen reported (Nov 2025) aerial photos of large, repetitive worker housing in the NEOM area. (Dezeen, 2025-11-10, https://www.dezeen.com/2025/11/10/neom-worker-housing-aerial-photos/)
- C7 [media/low] The Wall Street Journal reported (Mar 2025) more than 50 billion dollars spent on NEOM. (WSJ post on X, 2025-03-08, https://x.com/WSJ/status/1898659133521326373)
- C8 [media/low] Soar's analysis reported (Jun 2023) a faint straight earthwork in satellite imagery of the site. (Middle East Eye, 2023-06-01, https://www.middleeasteye.net/news/saudi-arabia-neom-line-satellite-images-progress-construction)
- C9 [observation/high] A straight, narrow cleared corridor crosses the area, at least 15 km long inside our 10 m frame: absent in 2020-21, faint in 2022, clear from 2023.
- C10 [observation/high] A dark segment is absent in Oct 2022 and 2023 and present in Oct 2024, 2025 and 2026: about 1.6 km long in 2024 and 2025 and about 1.9 km long in 2026, measured at 10 m.
- C11 [observation/medium] In 2024, 2025 and 2026 the dark segment is water-like in near-infrared (NDWI above zero, very low near-infrared); in 2022 and 2023 no pixel qualifies.
- C12 [observation/medium] Measured at 10 m, the segment is about 1.6 km long in Oct 2025 and about 1.9 km in Oct 2026; we cannot tell growth from water level or a threshold effect.
- C13 [observation/medium] Landsat 8 at 30 m shows the same segment but measures it differently: about 0.7 km in Oct 2024 (Sentinel-2: 1.6 km) and about 1.65 km in Oct 2025 and Sep 2026 (Sentinel-2: 1.6 and 1.9 km); the Landsat and Sentinel-2 scenes are two to three weeks apart.
- C14 [observation/medium] The segment appears on three different dates and on three different Sentinel-2 satellites (2A, 2B and 2C) in 2024, 2025 and 2026.
- C15 [observation/high] Each pixel in our Sentinel-2 frames covers 10 meters of ground.
- C16 [observation/high] Seven Sentinel-2 scenes, all from the same orbit, taken in late September or October of each year from 2020 to 2026, each with reported scene cloud cover under 0.1 percent.
- C18 [hypothesis/low] The dark segment may be standing water in a long, narrow excavation.
- C17 [observation/medium] A settlement-like complex at the western end of our frame grows from a small compound in 2020 to a large planned street grid by 2024; what it is is unknown.
- C19 [observation/medium] A second settlement-like complex at the eastern end of our frame grows from sparse tracks in 2020 to a planned street grid with buildings by 2024; what it is is unknown.
- C20 [original/medium] The Line is part of NEOM, on Saudi Arabia's Red Sea coast. (Gulf News and Dezeen on the Hidden Marina, 2025-02-17, https://gulfnews.com/business/property/saudi-arabia-neom-unveils-hidden-marina-as-first-phase-of-the-line-1.500037889)

## Costs
- {'stage': 'voice', 'chars': 5280, 'provider': 'elevenlabs', 'at': '2026-10-21T05:05:17Z', 'note': 'approved by owner'}

## Package is INCOMPLETE
Pending: render, qc

**Owner question: approve the paid step(s) listed as awaiting_approval, or change?**
