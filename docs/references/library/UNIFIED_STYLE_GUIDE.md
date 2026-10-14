# Unified OrbitalAtlas style guide (VISUAL_REF_001 + VISUAL_REF_002)

Consult before storyboarding: `python3 -m orbitalatlas.refs consult "<scene type>"` (effects, status, presets, QA rules). CLAUDE.md points here; the storyboard planner reads `orbitalatlas.semantic` for the narration-driven part.

## Principle
Narration decides what the viewer must understand. Three layers, never more than one "event" per layer at a time:
1. **Background** (evidence): satellite imagery, maps, footage. Pixels are never recoloured. Grade `neutral` or `evidence_safe` only; `Graded.manifest()` says whether pixels were modified (`evidence_pixels_unmodified`).
2. **Motion graphics**: region tint (annotation, `TRACED`), route arrow (presentation curve, `MAP`), pins, HUD frame, grid, sweep, particles, waveform (`DECOR`). Every annotation states `source` and `validation`.
3. **Kinetic typography**: captions (A-E), titles, number/year pops. English only.

## Rules that survive from the references
- **Camera**: event-driven moves of 0.3-0.5 s (snap), 1.2-1.6 s for scale changes with a small pull-back, a creep or hold on arrival (never a frozen frame > 5 s; yt-qc freeze limit). Alternate wide and tight (zoom ratio >= 1.5) at least every 8 s. Use `camera_presets`.
- **Transitions by purpose**: `light_wipe` before/after of one subject, `flash_dip` revelation or change of footage type (at most 2 per minute), `whip_pan` once per video, `dissolve` only for time within one instrument.
- **Highlight**: flash 0.2 s then settle to alpha <= 0.2 on satellite pixels; outline glow draws on; label appears with the word.
- **Arrows**: curve 0.2-0.3 x length, white shaft, accent head, label from verified anchors or a VERIFIED claim.
- **Numbers**: count-up 0.4 s to the exact string; years: underline sweep; big numbers on arrows: 2.5D settle.
- **Captions** (planner `captions.plan_styles`): A default for long-form; B default for Shorts; D when the card holds a number, year, percentage or place; C only for a flagged revelation, <= 6 words, <= 2 per minute; E when the picture is busy (complexity > 0.7). A plain style is kept for at least 2 cards. Emphasise at most 1-2 words per card. Captions never overlap, stay in the safe frame and are registered for QA.
- **Density**: at most about 4 non-caption events per 10 s in long-form (`semantic.plan(max_events_per_10s)`), more only for a deliberate Short. Complex sentences (more than 24 words or 3+ data items) reduce clutter.
- **Colour**: one accent per layer. OrbitalAtlas tokens: amber = emphasis, cyan = data/annotation, violet = decor only. The references' purple is not the brand.
- **Honesty**: timing source is written into every plan (`provider`/`alignment` = frame accurate; `estimated`/`simulated` are not). Decorations are labelled `DECOR`; a waveform says whether it is measured.

## Focus and pacing (v2b, enforced by `orbitalatlas.director`)
- One focus at a time: impact card (revelation, <= 5 words) > number card > captions. The caption that says the same thing is hidden; numbers are never shown twice.
- Focus cards at least 5 s apart and at most 4 per minute in long-form; other numbers stay in style D captions. Captions never count up.
- Opening: the map lands from a tilted plane (PlaneTilt). Image date shown once per image change (HUD stamp), not on every shot.

## Not to do
Constant flashing; neon everywhere; text on every shot; flags/cloth (not built); noise glitch; recolouring Landsat; unlabeled arrows; claiming a 3D flyover (class A only).
