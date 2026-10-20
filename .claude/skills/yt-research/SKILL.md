---
name: yt-research
description: >-
  Auditable research for a video: a provenance journal of every search/fetch, structured notes, and claims.json with
  confidence DERIVED from source access (never typed in), plus a coverage report and an honest factual-capacity estimate.
  Use when starting research for an episode or when yt-orchestrate reports research needs_agent.
---

# yt-research  (AGENT_REQUIRED for the reading; FULLY_AUTOMATED for provenance, claims and report)

```bash
R=.claude/skills/yt-research/research.py; E=productions/<slug>
python3 $R --root $E log   --tool WebSearch --query "..." --status ok --note "what it returned"      # journal your own tool calls
python3 $R --root $E fetch https://...        # Python-side read; blocked/dns/timeout/http_N is logged and NEVER replaced by a guess
python3 $R --root $E add   --json '{...note...}'                                                      # or edit research/notes.json
python3 $R --root $E build                    # notes.json -> claims.json + research/report.md
python3 .claude/skills/yt-research/test_research.py
```
`research/notes.json` (schema yt-research/1): `geo` (focus, segment, ndwi_bbox, stacks[] with aoi/years/pixel_m/window/cloud; a stack with `"role":"wide"` feeds the scale graphic) and `notes[]`:
`id (C1..), kind (original|media|org|science|observation|hypothesis), statement, short (<= 44 chars, drawn on screen), source {outlet,url,date,access: read|summary_only|unreachable, kind: primary|secondary|search_summary}, independent_outlets, corroboration`;
observations: `evidence (file), basis (two_checks|one_check|visual_only)`, optional `group, years, focus, anchor, callouts, check, visual:false, must_cover, compare_km`.

Derived confidence: primary read -> high; secondary read or search summary with >= 2 independent outlets -> medium, else low; unreachable -> low; observation two_checks -> high, one_check -> medium, visual_only -> low; hypothesis -> low.
Independent outlets means outlets that independently report/confirm the statement (several retellings of one report corroborate that the report exists, not that its content is true).
The report lists usable claims, low-confidence claims (not for the script), unreachable sources, and `INSUFFICIENT_FOR_6_MIN` when the verified facts cannot carry six minutes (heuristic 55 words per usable claim).
