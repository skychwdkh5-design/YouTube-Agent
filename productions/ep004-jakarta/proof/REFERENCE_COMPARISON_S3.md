# S3 proof vs VISUAL_REF_001 / VISUAL_REF_002 and the unified style guide (2026-10-15)
Basis: the library analyses (`docs/references/library/*`) and `REFERENCE_COMPARISON.md`; the reference videos themselves are not in the repository (copyright), so comparison is against the written analyses, not frame by frame.

| aspect | reference says | S3 proof does | gap |
|---|---|---|---|
| composition | one idea per screen; type is the hero, grid the stage (REF_002); a continuous map camera (REF_001) | one idea per beat (ray -> echo -> sink -> shift -> LOS); grid backdrop, dark stage, accent tokens amber/cyan (UNIFIED_STYLE_GUIDE); evidence/illustration separated by chips | no continuous camera; flat 2-D, no 2.5D tilt/parallax |
| animation | events of 0.3-0.5 s snaps, 1.2-1.6 s scale changes, never a frozen frame > 5 s | draw-ons 0.8-1.3 s, one 0.8 s push (ease in-out cubic), creep after; longest near-still stretch < 1 s; no frame freezes (freezedetect) | no snap/blur language; fewer, calmer events (correct for explanation, weaker than the Shorts) |
| typography | kinetic words on beat, emphasis on 1-2 words, caption styles A-E | 48 px captions, per-glyph reveal (`text.kinetic`), amber on 1-2 words per card, dark scrim | no weight contrast/outline type, no number cards or impact card; plain font |
| transitions | purpose-driven: flash dip for change of footage type (<= 2/min) | one flash dip illustration -> evidence placeholder | none other; light wipe/push unused |
| highlight/labels | flash then settle; label arrives with the word | rings on pulse arrival (flash then fade), labels fade in when their element appears | labels not tied to narration words (no narration yet) |
| colour | one accent per layer; amber emphasis, cyan data, violet decor only | cyan = pass 1/LOS, amber = pass 2/emphasis/chips, white = vertical; no violet | - |
| honesty | ILLUSTRATION vs EVIDENCE labelled; no map over photo | ILLUSTRATION chip, EXAGGERATED chip, PLACEHOLDER chip | - |
| sound | whoosh/sweep/impact/blip, ducked >= 12 dB under voice | CC0 synthesised cues at each event (whoosh 0.25, sweep x2, blips, rise, impact at the flash) | no narrator to duck under; no music bed |
| density | long-form: <= ~4 non-caption events / 10 s | ~3-4 / 10 s | - |
Verdict: **matches the style guide's rules; does not reach the references' energy or depth** - see the rubric (1.56/3).
