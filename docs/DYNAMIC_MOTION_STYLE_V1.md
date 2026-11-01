# Orbital Atlas — dynamic documentary / motion style v1
Date: 2026-11-01. Source: owner's explicit instructions in this conversation.
Scope: Orbital Atlas only. Apply to the next new episode. EP008 and existing releases/queues are unchanged.
Status: editorial specification and pilot; no claim that renderer support or retention improvement has been verified.

## Owner-approved changes
More dynamic editing and a different, livelier delivery. Add explanatory motion graphics, selective color emphasis on parts of the image, progressive drawing of plans/diagrams and moving geometric shapes when useful. Motion directs attention and explains the story rather than decorating every shot.

## Editorial defaults to test (not measured performance claims)
- A visible event/discovery starts the film. Cover subject in first 3 seconds, consistent with the existing thumbnail-hook gate. No greeting/logo/history intro.
- One central question connects evidence and conclusion. Separate established facts from unresolved questions.
- Conversational English for US audience, short sentences, active verbs, deliberate pauses. Try Adam with revised direction before changing narrator.
- Typical shots 2–5 seconds, with longer holds for complex imagery or comparisons. These are flexible working targets, not mandatory cuts or a new automated QC rule.
- Rhythm alternates discovery, evidence, explanation and breathing room. Avoid incessant zooms, fast cuts without information, and excessive sound effects.
- Build a 45–60 s pilot with voice, sound and graphics before extending the style across the full episode. The 15 s demonstration is a visual vocabulary test, not the full pilot or publication approval.

## Motion vocabulary
1. Selective color: mask a verified object/region, slightly dim its surroundings, retain image readability and object detail.
2. Progressive drawing: trace boundaries, routes, plans and mechanisms over time. Use only verified geometry for documentary boundaries; schematic geometry must be labelled Illustration.
3. Moving geometry: tracked circles, lines, arrows and frames guide gaze or indicate direction/scale. One dominant focus per moment.
4. Explanatory motion: maps, timelines, size comparisons and counters with verified values and units.
5. Detail reveal: wide shot -> highlighted region -> detail -> explanation. Avoid pixelation from unsupported crops.

## Timing and visual integrity
- Attach graphics to actual narration/word timings; never reveal an answer before the corresponding spoken phrase unless intentionally storyboarded.
- Define color meanings per episode and use them consistently. Color is supplemented by labels/shapes.
- Keep pointers/masks attached to objects through pans/zooms; use the same coordinate transform or tracking.
- Do not stack large titles, full subtitles, several arrows and counters in one focal area.
- Keep captions and source credits readable on a phone; inspect actual delivery resolution.
- Mark reconstructions/schematics Illustration throughout relevant shots. Do not invent scientific imagery, boundaries, numbers or events.
- Use cleared open/free media, preserving existing source/rights/fact gates. No new paid dependencies.

## Pipeline integration
1. Research: retain primary sources, rights and media provenance as before.
2. Packaging: cover + title + first-15-s promise remains the existing gate.
3. Script/storyboard: add explicit Graphics and motion column to every relevant shot.
4. Motion specification: record anchors, purpose, masks, coordinates, movement, colors, layering and source.
5. Pilot: render representative 45–60 s with narration, sound and all graphics for owner review.
6. Full edit: apply approved visual direction; retain render, captions, source, audio and publishing checks.
7. Visual QC: inspect full-speed playback and frames around graphic entrances/exits; verify alignment, tracking, readability, factual meaning, credit visibility and no unwanted blank frames.
8. Archive: retain editable source, motion spec, timings, fonts, assets, source/rights records and render command.
9. Measure: assess retention after release using existing experiment log; never promise a performance increase.

## Required storyboard fields
time_in | time_out | narration | media + source | visual purpose | graphics and motion | word anchor | entry/exit | tracking/coordinates | color meaning | sound | captions/credits | illustration flag

## Motion-spec example (schematic, no factual claims)
```json
{
  "shot_id": "style-demo-focus",
  "illustration": true,
  "purpose": "Show wide-to-detail selective emphasis",
  "anchor": {"type": "time", "seconds": 3.0, "note": "Use real voice word anchor in production"},
  "target": {"space": "normalized_frame", "rect": [0.58, 0.31, 0.20, 0.28]},
  "effects": [
    {"type": "dim_surroundings", "opacity": 0.45},
    {"type": "stroke_reveal", "color": "#F5CD48", "duration_s": 0.6},
    {"type": "leader_line", "duration_s": 0.35}
  ],
  "exit": "clear before next scene"
}
```

## 15-second demonstration
Original schematic terrain, explicitly labelled ILLUSTRATION / STYLE TEST; no documentary image or scientific claim.
0–3 s: fast wide-to-detail reveal, clear question.
3–6 s: color isolation, dimmed background, progressive outline and leader.
6–10 s: animated route/plan and moving marker.
10–13 s: expanded schematic detail, moving geometric elements show direction.
13–15 s: wide/detail comparison resolves the visual sequence.
English on-screen text; original synthesized sound accents; no paid voice request.
The demonstration tests visual direction only. Actual documentary footage, Adam delivery and narration synchronization require the subsequent episode pilot.
