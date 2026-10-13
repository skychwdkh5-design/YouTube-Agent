# Transitions (what worked, what did not)
Principle: a transition says what changes. Source docs: `docs/TRANSITION_DESIGN_SYSTEM.md`, `/yt-cinematic-edit`.
| change | transition | status |
|---|---|---|
| same place, other year, different source | **match cut + iris** at the shared landmark (same screen radius) | **[VERIFIED]** EP002 H0->H1 |
| same grid, two dates (ASTER 2000 -> 2003) | **cross-dissolve** (1.5 s) then highlight the difference | **[VERIFIED]**, user-requested instead of a wipe |
| time passes between blocks | slide (0.5 s) | **[VERIFIED]** H2->H3 |
| medium change (orbit photo -> satellite, globe -> map) | dissolve 0.6-0.7 s | **[VERIFIED]** H3->H4, H4->A1 |
| card/diagram scene following imagery | dissolve entry so the scene never starts blank | **[VERIFIED]** (blank dark starts were flagged by blackdetect) |
| hard cut | only between different sources, labelled, never mid-move | **[RULE]** |
Not suitable: wipes between unregistered images (**[RULE]** EP002 claim 32); wipes at all in EP002 (SCRIPT_LOCK); whips (>1 per video); flashes; rotating/spinning effects; any transition that implies spatial continuity between unregistered images.
Implementation note **[VERIFIED]**: entries are rendered inside the scene (blend with the previous scene's last frame), so segment durations and narration windows are unchanged; ffmpeg `xfade` would shorten the timeline.
Check: frame-difference spikes (> 30 on 96x54 grey) must coincide with declared boundaries/moves (`QUALITY_CONTROL.md`).
