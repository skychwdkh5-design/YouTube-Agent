---
name: yt-visual-planner
description: >-
  Generate episode.json and graphics_spec.json from the claims, the script and the satellite stacks - no hand-written JSON.
  Every visual is justified by claim ids found in its chapter; date labels come from scene metadata. Use after the script
  passes (yt-orchestrate stage visualplan) or to regenerate visuals.
---

# yt-visual-planner  (FULLY_AUTOMATED)

```bash
python3 .claude/skills/yt-visual-planner/planner.py --root productions/<slug>
python3 .claude/skills/yt-visual-planner/test_planner.py
```
Rules: original claim with `scale_km` + a wide stack -> scale graphic; >= 2 media/org claims (medium+) -> "what was reported" flow; observation with `years: [a, b]` -> wipe + same-ground compare;
`callouts` -> annotated frame; `years` list >= 3 -> year sequence; tiers graphic for limits; compact closing recap; `visual: false` claims (method, other datasets) attach nothing to shots;
compare views are clamped inside the stack; a chapter is capped at 10 visuals and what was dropped is reported (`planner_dropped`). Low-confidence claims are never drawn.
A hand-written `episode.json` (without `generated_by`) is left alone by the orchestrator.
