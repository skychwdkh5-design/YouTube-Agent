---
name: yt-topic
description: >-
  Choose the next video topic with a transparent score: what similar YouTube videos achieved (views vs channel size and age),
  free satellite availability, and written 1-5 ratings per the CLAUDE.md criteria. Use for "what should the next video be",
  "pick a topic", or when yt-orchestrate has no topic yet.
---

# yt-topic

```bash
python3 topic.py collect --queries "Salton Sea satellite;Great Salt Lake drying" --out topic/videos_salton.json   # public YouTube JSON, no login
python3 topic.py imagery --aoi 35.1,33.2,35.9,33.6 --years 2020,2022,2024,2026                                   # free Sentinel-2 check
python3 topic.py score --candidates topic/candidates.json --out topic/topic.json --memo topic/topic.md
python3 test_topic.py
```
`candidates.json`: `{"candidates": [{"id", "title", "needs_satellite", "videos": [collected rows with views, subs, age_days], "imagery": {...from imagery...},
"ratings": {us,se,no,dk,intl,visual,curiosity,evidence,monetization: 1-5}, "rationale": {same keys: >= 10 characters each}}]}`.

- Measured: demand (recent hits by channels <= 350K subscribers, fresh 500K+ videos, supply, crowding) and imagery (years with a usable scene).
- Judged: the nine ratings, each with a written rationale. Missing ratings, rationale, videos or imagery => `needs_data`, never a guess.
- Weights (US 3.0, demand 2.0, ...). Sweden/Norway/Denmark only reorder near-ties (CLAUDE.md). Gates: evidence rating <= 2 or no usable scene => disqualified.
- It models nothing about YouTube's algorithm and forecasts no CTR or retention; add OrbitalAtlas Analytics when available. Not available: first-30-seconds and exact dates (login-gated).
