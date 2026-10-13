# Visual style (OrbitalAtlas, from EP002 V1-V6)
Status tags: **[VERIFIED]** done and checked in this repo · **[HYPOTHESIS]** believed, not measured · **[EP002]** specific to that episode · **[RULE]** project rule (CLAUDE.md / SCRIPT_LOCK).
Reference mechanics: `docs/references/ORBITALATLAS_REFERENCE_STYLE.md`; component status: `docs/ORBITALATLAS_VISUAL_MASTER.md` §7.

## Hook (first 40 s)
- **[VERIFIED, user-approved direction V6]** Result first (3 s silent cold open on the strongest real image, labelled), then the contrast (same place, other year) via a match cut, then the change as the main event, then scale/orbit, then the open question and title. Do not stay on empty sea or a static wide shot; change scale every 2-3 s.
- Match cut recipe: size the second view so the shared landmark has the same screen radius as the first, open with an iris around that point (`with_entry(..., 'iris')`).
- The title lands last (about 39 s in EP002), after rising dynamics (pull-back accelerates, project pings), not first.
- **[RULE]** A different spoken line is a new paid TTS take: change visuals around locked narration, never the text.

## Labels and text
- **[VERIFIED, user feedback]** One main label at a time, 26-46 px on a 960x540 canvas (readable on a phone), dark pill + amber accent bar; source chips 12 px, 0.85 alpha, top-left; captions bottom centre. Long technical chips are a defect (V5 was rejected for text overload).
- Labels sit on the thing they name; nothing outside the 22 px margin; no label collides with captions (bottom 70 px) or the date (top right).
- Numbers/years appear on the word that says them (counters: "1/2/3 YEARS", "21+ YEARS" derived from labelled dates only).

## Scale ladder and variety
- Vary scale, framing and move type between consecutive shots: pull-out, pan along a traced line, push-in, glide between landmarks, split/two-panel, filmstrip scroll, spotlight. No identical move three times in a row.
- Text-card scenes were the monotony problem (motion metric < 3): replace with real imagery + traced outline + counter/timeline. Audit with `productions/dubai/preview/monotony_audit.py` (mean frame-to-frame change, 12 samples/scene; < 3 = LOW_MOTION).

## Evidence classes on screen
EVIDENCE (unmodified image) / TRACED (outline computed from that image) / UI (tint, spotlight, arrows, rings; always labelled or obviously a pointer) / ILLUSTRATION. Never paint satellite pixels; dimming is a UI treatment and says so in the chip.

## What the user rejected (do not repeat)
Triple split-screen (V4); line-by-line text cards; pan/zoom called a "flyover"; wipes between sources (SCRIPT_LOCK says no wipes: use cross-dissolve); technical text at equal weight with the main label; static empty-sea holds.
