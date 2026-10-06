# Market discovery - Phase 1 (2026-10-06)

Research for the U.S. geography / geo-entertainment market. Reused by `/yt-viral` and `/geo-topics`.
Competitor table: `channel.md`. Machine-readable data: `data/market-2026-10-06.json`. Topic backlog:
`ideas.md` (G01-G30).

## How this was researched - read before trusting any number

- **No direct YouTube data.** From this environment youtube.com, Social Blade, Wikipedia, Playboard,
  Feedspot, vidIQ and Apify were blocked by the network policy (WebFetch and curl both). The only
  working channel was web search, whose results quote pages such as vidIQ's public stats pages.
  **Every figure below is "as reported by" the linked source, not read from YouTube by us.**
- **Outlier multiples come in three grades:**
  - **[vidIQ]** - vidIQ's own published outlier score for that video (views vs the channel's typical video).
  - **[proxy]** - our calculation: video views / (channel total views / video count) = a multiple of
    the channel's *lifetime mean*. Not the recent median `swipe.py` uses. Overstates outliers on
    shrinking channels, understates them on growing ones.
  - **[series]** - Map Men only: views vs the series' least-viewed episode (1.32M). Weakest grade.
- **Recency is mostly unverified.** Dates are known for a few videos only (marked). Most "top video"
  lists are all-time.
- **Thumbnails and hooks were not observed** - no access to the pages or transcripts. Title patterns
  are from titles; thumbnail and hook columns say "not verified" rather than guess.
- **Not collected:** a 4-videos-per-channel recent list for `swipe.py`. Do that when YouTube access
  exists (see "Next data step").

## Outliers (31)

| # | Channel | Video | Views | Multiple | Grade | Known date | Source |
|---|---|---|---|---|---|---|---|
| 1 | Geography By Geoff | Why So Few Americans Live In This HUGE Area Of The West Coast | 9.97M | 18.7x | proxy | - | [vidIQ page](https://vidiq.com/youtube-stats/channel/@geographybygeoff/) |
| 2 | Geography By Geoff | Why So Few Americans Live In This HUGE Area Of The East Coast | 7.4M | 13.9x | proxy | - | same |
| 3 | Geography By Geoff | Why 60,000 People Live on a Rock with Zero Resources (Bermuda) | 6.19M | 11.6x | proxy | May 2026 | same; [Bernews](https://bernews.com/2026/05/video-60000-on-rock-with-zero-resources/) |
| 4 | Geography By Geoff | Why So Few Americans Live In This Huge Area In The Middle Of The Country | 5.31M | 10.0x | proxy | - | same |
| 5 | Geography By Geoff | Why "Nobody" Lives In Upstate New York | 5.12M | 9.6x | proxy | - | same |
| 6 | Geography and Space | World War II in Europe with Flags: Every Day | 20.13M | 14.9x | proxy | - | [vidIQ page](https://vidiq.com/youtube-stats/channel/@geographyandspace/) |
| 7 | Geography and Space | History of Asia in Flags: Every Year | 9.9M | 7.3x | proxy | - | same |
| 8 | Geography and Space | The Korean War with flags: Every Day | 6.22M | 4.6x | proxy | - | same |
| 9 | Geography and Space | The World: Timeline of National Flags 2024-3024 | 6.12M | 4.5x | proxy | - | same |
| 10 | Geography and Space | South America: Timeline of National Flags 1450-2021 | 5.07M | 3.8x | proxy | - | same |
| 11 | Geography Geek | Peru's Geography is CRAZY | 3.68M | 10.9x | proxy | - | [vidIQ page](https://vidiq.com/youtube-stats/channel/@geographygeek/) |
| 12 | Geography Geek | Geography & culture facts to learn if you're bored | 2.57M | 7.6x | proxy | - | same |
| 13 | Geography Geek | Why are there Giants in South America on Old Maps? | 2.54M | 7.5x | proxy | - | same |
| 14 | Geography Geek | Why is there a Sea in America on Old Maps? | 1.81M | 5.4x | proxy | - | same |
| 15 | Map Men | The world's silliest time zones | 5.20M | 3.9x | series | - | [Brilliant Maps](https://brilliantmaps.com/map-men-playlist/) |
| 16 | Map Men | The mystery of the squarest country | 4.76M | 3.6x | series | - | same |
| 17 | Map Men | Why every world map is wrong | 4.62M | 3.5x | series | - | same |
| 18 | Map Men | Bir Tawil - the land that nobody wants | 4.39M | 3.3x | series | - | same |
| 19 | Map Men | How many continents are there? | 4.07M | 3.1x | series | - | same |
| 20 | Map Men | What will the world look like in 250 million years? | 4.07M | 3.1x | series | - | same |
| 21 | Geography King | 10 Most Scenic Drives in the U.S. | 1.05M | 22.77x | vidIQ | ~4 yrs old | [vidIQ page](https://vidiq.com/youtube-stats/channel/@geographyking/) |
| 22 | Geography King | 10 Worst Big City Downtowns in the U.S. | 678K | 12.69x | vidIQ | ~2 yrs old | same |
| 23 | Geography King | Subregions of the U.S. Defined | 761K | 10.34x | vidIQ | ~4 yrs old | same |
| 24 | Geo Facts | I Simulated an Asian BATTLE ROYALE | 4.02M | 27.47x | vidIQ | - | [vidIQ page](https://vidiq.com/youtube-stats/channel/@geofacts/) |
| 25 | Counting Countries | We Traveled to Greenland (What It's Like) | 843K | >100x | vidIQ | - | [vidIQ page](https://vidiq.com/youtube-stats/channel/@countingcountries/) |
| 26 | Practical Engineering | The Bizarre Paths of Groundwater Around Structures | 14.03M | 8.1x | vidIQ | - | [vidIQ page](https://vidiq.com/youtube-stats/channel/UCMOqf8ab-42UUQIdVoKwjlQ/) |
| 27 | Practical Engineering | What Really Happened at the Arecibo Telescope | 9.41M | 9.66x | vidIQ | - | same |
| 28 | Practical Engineering | The Hidden Engineering of Landfills | 11.42M | 4.66x | vidIQ | - | same |
| 29 | Practical Engineering | The Wild Story of the Taum Sauk Dam Failure | 10.76M | 3.89x | vidIQ | - | same |
| 30 | Wendover Productions | China's Geography Problem | 12.65M | 4.3x | proxy | - | [vidIQ page](https://vidiq.com/youtube-stats/channel/UC9RM-iSvTu1uPJb8X5yp3EQ/) |
| 31 | Wendover Productions | The Failed Logistics of Russia's Invasion of Ukraine | 10.78M | 3.7x | proxy | - | same |

Not outliers, but useful: RealLifeLore's recent sample (Sep 2026: 382K-1.02M per video) sits well
below its lifetime mean (~3.9M) - a large channel's recent baseline is far lower than its history.
Source: [HypeAuditor](https://hypeauditor.com/youtube/UCP5tjEmvPItGyLhmjdwP7Ww/) as quoted in search.

## Recurring viral patterns

1. **"Why so few people live in [huge area]"** - population voids. 4 of Geography By Geoff's top 5,
   still running in July 2026 ("Why Nebraska is Empty by Design"). The single strongest, most
   repeatable pattern found. That channel owns the U.S. version; global and mechanism-led angles are open.
2. **"Why [N] people live in [an impossible place]"** - Bermuda, May 2026, 6.19M. Recent and repeatable:
   isolation or hostility + a surprising economic reason.
3. **Maps that are wrong** - "Why every world map is wrong", old-map errors (giants, an inland sea),
   continents. The viewer's mental map is the anomaly.
4. **Border and time absurdities** - time zones, land nobody claims, odd country shapes.
5. **"[Country]'s geography is CRAZY / its biggest problem"** - Peru, China, Pakistan (Geoff, Jun 2026):
   one country's terrain explains its fate.
6. **U.S. regional identity** - subregions defined, scenic drives, worst downtowns: Americans
   arguing about their own map (listicle format).
7. **Hidden infrastructure** - groundwater, landfills, dams: the human-made world explained by the
   ground under it.
8. **Animated timeline maps** - flags/borders every day or year: huge views, history-first; better
   suited to Shorts than to our long-form.
9. **News-hooked geography** - Greenland, Point Roberts (tariffs): spikes when a place hits the news,
   then saturates fast.

**Title patterns:** "Why ..." dominates; a number with a twist ("60,000 ... Zero Resources"); one
all-caps word (HUGE, CRAZY, NOBODY); a parenthetical reversal ("It's Not Just the Ice", "It's Not
What You Think"); "Nobody" in quotes to pre-empt the pedant.

**Thumbnail and hook patterns:** not verified (no access). To be collected when YouTube access exists.

## Saturation found

| Topic | Evidence | Implication |
|---|---|---|
| Canadians living near the U.S. border | 6+ videos, several "90%" titles | crowded; a myth-busting angle (StatCan 2021: 76% within 100 mi) is the only opening |
| Point Roberts | 4+ videos in 2025-26 incl. a tariff angle | crowded, news-driven |
| Pheasant Island | Half as Interesting + 3 more | crowded |
| California as an island | Johnny Harris + 4 more | crowded at the top; strong public-domain map archive still makes it viable later |
| Greenland population | "Why NOBODY Lives in Greenland" (2025) + news coverage | crowded, but demand proven |
| U.S. empty regions | Geography By Geoff series incl. Nebraska (Jul 2026) | that channel's home turf - avoid head-on |
| Public Land Survey grid | City Beautiful (2025) | covered once |
| Northwest Angle | PBS documentary + 3 travel vlogs; **no faceless explainer found** | open lane |

## Next data step (when allowed)

Real outlier analysis needs each competitor's recent uploads with views and dates. Options, in order:
1. Allow `www.youtube.com` in the environment's network settings, then `pip install yt-dlp` and
   collect `yt-dlp --flat-playlist -J <channel>/videos` into `data/competitors-<date>.json` for
   `swipe.py --profile geo`.
2. Connect the vidIQ connector (it lists an outliers tool).
3. Paste channel video lists by hand.
No YouTube API or OAuth is needed for any of these.
