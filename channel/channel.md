# Channel profile

Every skill reads this file first. When something here changes, the whole system changes with it.

## Positioning

- **Niche:** global geography / geo-entertainment.
- **Promise:** the map is stranger than you think - and here is exactly why.
- **Audience market:** the United States. The U.S. is who we make videos *for*, not a limit on
  where the videos are *about*. A topic from anywhere in the world is in scope when it is the
  stronger idea.
- **Language:** native-sounding American English (see `voice.md`).
- **Format:** faceless. No host on camera. AI voice-over narration over maps, satellite imagery,
  licensed/public-domain footage, stock, motion graphics, animated maps and infographics, with AI
  visuals only where `visual-style.md` allows them.
- **Not:** school geography. No "today we will learn", no capital-city quizzes, no textbook tone.
  Every video is a curiosity with a payoff.

## Who is watching

- Curious U.S. adults, roughly 18-45, who click on "why is this like this?" videos: maps, history,
  infrastructure, weird places. They did not search for "geography"; they were surprised by a
  thumbnail.
- They know the U.S. map well, the rest of the world vaguely. Global topics get a U.S. bridge
  (a size, distance or situation they already know).
- They watch on phones and TVs. Labels must read at phone size; narration must make sense without
  the picture for a few seconds (TV in the background).
- They are quick to correct a wrong fact in the comments. Accuracy is part of the entertainment.

## Topic selection - in priority order

1. click potential
2. curiosity gap
3. proven audience interest
4. competitor / outlier performance
5. visual potential
6. strength of the story
7. reliable fact verification (a hard gate - below 3/5 the topic is rejected)
8. relevance or comprehensibility to a U.S. audience

There is no fixed U.S. / world ratio. U.S. topics stay an important pillar, and a global topic with
stronger potential always wins the slot. `/geo-topics` and `topicscore.py` apply these weights.

## Content pillars

| Pillar | What it covers | Example direction |
|---|---|---|
| **Border Weirdness** | strange borders, enclaves/exclaves, tripoints, split towns, disputed or unusual territories (neutral) | "The U.S. Town You Can Only Reach Through Canada" |
| **Explained by Geography** | why cities, states, countries and infrastructure ended up where and how they are; geography-driven history | "Why Does This Part of the U.S. Belong to Minnesota?" |
| **Empty & Extreme** | abandoned, isolated and nearly empty places; cities in extreme locations | "Why Almost Nobody Lives in This Huge Part of America" |
| **Map Anomalies** | unusual maps, countries with odd shapes, places that look impossible, geographic mysteries, surprising facts | "The Weirdest State Border in America" |
| **This vs. That** | unusual comparisons between countries, cities, regions; true-size comparisons | "This Country Is Bigger Than It Looks" |

Pillars describe the catalogue; they are not quotas.

## Weekly cadence (target once production is stable)

| Slot | Per week | Length | Production |
|---|---|---|---|
| Main long-form | 1 | 8-12 min (~1,200-1,800 words) | full pipeline, custom animated maps |
| Lower-production long-form | 1 | 4-6 min (~600-900 words) | one anomaly, simpler visuals, same fact-check |
| Shorts | 3-5 | 30-50 s (~75-125 words) | 2-3 cut from the main video, 1-2 standalone |

If the week breaks, drop in this order: the lower-production video, then standalone Shorts. The main
video and the fact-check are never the thing that gets cut.

## Competitors and reference channels

Phase 1 list (2026-10-06), pending the creator's approval. Full research, outliers, patterns and
caveats: `market.md`; data: `data/market-2026-10-06.json`. Figures are as reported by the linked
source (YouTube itself was not reachable); thumbnail and hook patterns were not observed. Median views
over the last 20 uploads are still to be collected (see `market.md`, "Next data step").

| Channel | Size (as of) | Format | Faceless | Typical length | Typical views | Strongest topics | Title patterns | Notable outliers | Source |
|---|---|---|---|---|---|---|---|---|---|
| RealLifeLore | 7.94M (Sep 2026) | narrated maps + animation; geopolitics/geography docs | yes (per overseeros.com) | not verified | recent sample 382K-1.02M (Sep 2026) | geopolitics, 'why' geography, what-if | Why ... / How ... / What if ... | none found in recent sample | hypeauditor.com/youtube/UCP5tjEmvPItGyLhmjdwP7Ww |
| Wendover Productions | 4.92M (Sep 2026) | narrated animation; logistics, systems, geography | yes (narration; not re-verified) | not verified | not verified | logistics, country geography problems | [Country]'s Geography Problem; How X quietly ... | China's Geography Problem 12.65M (4.3x proxy) | vidiq.com/youtube-stats/channel/UC9RM-iSvTu1uPJb8X5yp3EQ |
| Half as Interesting | 2.94M (Jun 2026) | short witty explainers, one oddity each | yes (narration; not re-verified) | 5-10 min (per Wikipedia via search) | not verified | oddities, borders, transport quirks | The Weird ... ; The $X ... Mistake | not available | vidiq.com/youtube-stats/channel/UCuCkxoKLYO_EQ2GeFtbM_bw |
| Geography By Geoff | 1.06M (2026) | population geography explainers, weekly | not verified | not verified | 9.76M views in last 30 days (vidIQ) | why so few/so many live here; country geography | Why So Few ... Live In This HUGE Area ...; Why [N] People Live on ... | 5 videos 5.1M-9.97M (9.6-18.7x proxy) | vidiq.com/youtube-stats/channel/@geographybygeoff |
| Map Men | 1.78-1.81M (2026) | comedy + animated maps, two presenters | no (presenters on camera) | not verified | 1-5M per episode (Wikipedia via search) | time zones, map projections, odd borders | The mystery of ... ; Why every ... is wrong | top 6 episodes 4.07-5.20M | brilliantmaps.com/map-men-playlist |
| Johnny Harris | 7.97M (Oct 2026) | host-led investigative explainers with maps | no (host on camera) | not verified | not verified | borders, geopolitics, map history | The Biggest ... of ALL TIME | not available | vidiq.com/youtube-stats/channel/@johnnyharris |
| Geography Now | 3.9M (Aug 2026) | country-by-country profiles, host-led | no (host on camera) | not verified | not verified | country profiles A-Z | [Country]! | 'So I went to Ukraine...' 2.38M (~4.3x proxy, personal) | vidiq.com/youtube-stats/channel/@geographynow |
| Atlas Pro | 1.27M (2026) | narrated explainers: geography, biogeography | not verified | not verified | not verified | physical geography, biogeography, rare animals | not verified | not available | vidiq.com/youtube-stats/channel/UCz1oFxMrgrQ82-276UCOU9w |
| PolyMatter | 1.93M (Sep 2026) | narrated animation; geopolitics/economics | yes (narration; not re-verified) | not verified | not verified | geopolitics, economics | not verified | not available | socialblade.com/youtube/handle/polymatter (via search) |
| CaspianReport | 1.85-1.9M (Sep 2026) | narrated geopolitics over maps/footage | yes (narration; not re-verified) | not verified | not verified | geopolitics | not verified | not available | creatordb.app/creatorstats/caspianreport (via search) |
| fern | 5.14M (Jul 2026) | faceless 'armchair documentaries', near-weekly | yes | not verified | not verified | broad documentaries incl. places | not verified | not available | hypeauditor.com/youtube/UCODHrzPMGbNv67e84WDZhQQ (via search) |
| Practical Engineering | 4.73-4.83M (2026) | infrastructure explainers, host + models | no (host on camera) | not verified | not verified | hidden infrastructure, failures | The Hidden Engineering of ... ; The Wild Story of ... | 4 videos 9.4-14.0M (3.9-9.7x vidIQ) | vidiq.com/youtube-stats/channel/UCMOqf8ab-42UUQIdVoKwjlQ |
| The B1M | 4.05M (Aug 2026) | construction/megaproject documentaries | not verified | not verified | 32M monthly viewers (B1M site, via search) | megaprojects, cities | not verified | not available | theb1m.com/about |
| Casual Scholar | 479K (2026) | long explainers: why nations are rich or poor | not verified | not verified | not verified | economic geography, geopolitics | not verified | not available (very high views per video) | speakrj.com (via search) |
| Map Pack (Mappack) | 439K (2026) | weekly geography deep dives; long compilations; IT/PL/FR/DE spin-offs | not verified | IT/PL versions avg ~30 min | not verified | hidden geography, borders, history | 2 Hours Of HIDDEN Geography Secrets | not available | app.thoughtleaders.io (via search) |
| Geography and Space | 357K (Jun 2026) | animated flag/border timelines | yes (animation; not re-verified) | not verified | 3.87M views in last 30 days | history in flags, timelines | [Region]: Timeline of National Flags ... | 5 videos 5.1-20.1M (3.8-14.9x proxy) | vidiq.com/youtube-stats/channel/@geographyandspace |
| Geography Geek | 372K (2026) | geography explainers, old maps | not verified | not verified | 87.96K views in last 30 days (inactive) | old maps, country geography | Why is there ... on Old Maps?; [Country]'s Geography is CRAZY | 4 videos 1.8-3.7M (5.4-10.9x proxy) | vidiq.com/youtube-stats/channel/@geographygeek |
| Geography King | not found (-) | U.S. regional listicles | not verified | not verified | not verified | U.S. regions, rankings, drives | 10 Most/Worst ... in the U.S.; ... Defined | 3 videos 10.3-22.8x (vidIQ) | vidiq.com/youtube-stats/channel/@geographyking |
| Geo Facts | 515K (2026) | Shorts-led geography/history, simulations | not verified | Shorts | not verified | simulations, geography facts | I Simulated ... | 'I Simulated an Asian BATTLE ROYALE' 4.02M (27.47x vidIQ) | vidiq.com/youtube-stats/channel/@geofacts |
| Counting Countries | 330K (2026) | travel vlogs to countries | no (travel vlog; not re-verified) | not verified | not verified | travel, remote countries | We Traveled to [Place] (What It's Like) | Greenland 843K (>100x vidIQ) | vidiq.com/youtube-stats/channel/@countingcountries |

## Market research

See `market.md` (Phase 1, 2026-10-06) for outliers, viral patterns and saturation.

## Channel facts

- Channel name: _TBD_
- Channel URL: _TBD_
- Upload days/times: _TBD - set from our own analytics once there are 10+ uploads; until then
  choose a fixed schedule and keep it._
- AI voice service and voice: _TBD (record in `voice.md`)_
- Editing tool: _TBD_

## Rules every skill keeps

- **Nothing is published automatically.** Skills write; the creator publishes.
- **No YouTube API or OAuth connection** is configured yet. Data comes from exports the creator
  saves in `channel/data/`.
- **Never invent a number, a result or a source.** Missing data is asked for or marked `[NEEDED]`.
