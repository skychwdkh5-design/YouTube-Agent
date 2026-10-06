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

To be filled during the first `/yt-viral` run and approved by the creator. Record channel name, URL,
why it is relevant (format, topics, audience), and median views over the last 20 uploads.

| Channel | URL | Why it is relevant | Median views (last 20) | Date checked |
|---|---|---|---|---|

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
