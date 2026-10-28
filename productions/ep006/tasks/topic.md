# Task: topic discovery

1. Run `python3 .claude/skills/yt-topic/topic.py collect --queries "q1;q2;..." --out topic/videos_<name>.json` for 3-5 candidate topics (CLAUDE.md: unusual geography, satellite-visible change, strong US appeal).
2. Run `topic.py imagery --aoi=minlon,minlat,maxlon,maxlat --years 2020,2022,2024,2026` for each (write `--aoi=...` with the equals sign: negative longitudes otherwise break argument parsing).
3. Write `topic/candidates.json` (schema in .claude/skills/yt-topic/SKILL.md) with ratings 1-5 and a written rationale for each of us/se/no/dk/intl/visual/curiosity/evidence/monetization. Do not invent audience, CTR or retention data.
4. Re-run the orchestrator. The owner may instead approve a topic by writing `topic/approval.json` {"approved": true, "title": ...}.
