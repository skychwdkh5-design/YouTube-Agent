# Task: research (AGENT_REQUIRED)

Topic: see topic/topic.json. Do the reading and searching with your own tools (WebSearch, WebFetch), prefer primary and scientific sources, and note every unreachable primary.
Log what you did so the work is auditable:
  python3 .claude/skills/yt-research/research.py --root productions/salton-sea-test log --tool WebSearch --query "..." --status ok --note "..."
  python3 .claude/skills/yt-research/research.py --root productions/salton-sea-test fetch <url>      # Python-side read; blocked/dns/timeout is logged, never replaced
Write `research/notes.json` (schema yt-research/1) - see .claude/skills/yt-research/SKILL.md:
  - "geo": {"focus": [lon,lat], "segment": [lon,lat], "ndwi_bbox": [...], "stacks": [{"name":"stack","aoi":[minlon,minlat,maxlon,maxlat],"years":[...],"pixel_m":10,"window":"MM-DD:MM-DD","cloud":3}, {"name":"wide","role":"wide",...}]}
    (the AOI and years are a research decision; check availability with `yt-topic imagery`)
  - "notes": one per claim: id C1.., kind, statement, short (<= 44 chars, drawn on screen), source {outlet,url,date,access,kind}, independent_outlets, or evidence+basis for observations.
Confidence is DERIVED from the sources (a primary read gives high; search summaries need >= 2 independent outlets; unreachable gives low). Do not try to raise it.
Then run the orchestrator again; `yt-research build` turns the notes into claims.json and a coverage report.
