# EP008 — first 20 seconds (concept A)

Exact frames, text and sound. Times are estimates at 150 wpm and are re-locked to the approved voice.
Every frame is either a real NASA photo (credit on screen) or an own graphic labelled DIAGRAM.
No logo, no greeting, no channel ident.

| t (s) | picture | on-screen text | VO | sound |
|---|---|---|---|---|
| 0.0 | **a2-lunar-surface** (art002e009289, NASA, Artemis II flyby 2026-04-06) full frame, push-in 104→110 % over 3 s. Same photo and crop as the cover. | top-left yellow tag `ARTEMIS III` · centre white `THE PLAN: LAND HERE` (on at 0.2) · bottom-left credit `NASA · ARTEMIS II PHOTO, APR 2026` | "NASA's next Moon mission was supposed to land here." | 0.0 low sub hit; faint room tone of space (no music yet) |
| 2.9 | — | `THE PLAN` text cracks / red strike line draws through `LAND HERE` (0.3 s) | — | 2.7 reverse whoosh |
| 3.1 | **HARD CUT** → own diagram `d-orbit-vs-moon`: camera starts on the same lunar crop, pulls back fast past the Moon to Earth (1.2 s, ease-out); Moon shrinks to a dot | `DIAGRAM` (bottom-left) | "Now it won't even leave Earth orbit." | 3.1 impact + 0.2 s silence, then low drone |
| 4.6 | LEO ring around Earth lights up yellow; scale label pops | `NOW: 273 MILES UP` · small `(440 km)` | — | UI tick on number |
| 6.8 | **CUT** → a2-earthset (art002e009288) Earth setting behind the Moon through Orion's window; slow drift L→R | `ARTEMIS II · APRIL 2026` · credit `NASA · ARTEMIS II PHOTO` | "In April, four astronauts flew around the Moon on Artemis Two." | drone continues; soft swell |
| 10.8 | **CUT** → own diagram `d-sls-stack`: SLS side view, Artemis II config. Upper stage (ICPS) highlighted, then slides out of the stack (1 s) | `UPPER STAGE` → `GONE` | "And the next crew's rocket won't even carry the stage that sends Orion toward the Moon." | mechanical slide; tick |
| 14.2 | in the gap, a grey barrel slides in, labelled | `SPACER · NO ENGINE` · credit `DIAGRAM · NASA HARDWARE UPDATE 2026-08-05` | — | metallic clank |
| 16.4 | **CUT** → **spacer** photo (NASA/Sam Lott, Marshall, 2026-07-23), push-in on the weld seam | `NO ENGINE` (holds 1.5 s) · credit `NASA/SAM LOTT` | "In its place: a metal barrel with no engine." | clank tail; music bed starts at 19.5 (low pulse) |
| 20.0 | → s03 timeline (Feb 27 → Oct 23) | `ANNOUNCED FEB 27, 2026` | "NASA made this change back in February…" | — |

Information events in the first 10 s: subject (0.0), contrast text (0.2), strike (2.9), cut to orbit (3.1), 273 mi (4.6),
Artemis II date (6.8) = 6. Compositions in the first 10 s: 3 (photo, diagram, photo). Cover promise "NO MOON LANDING"
is answered at 3.1 s; the "why" promise of the title is opened at 20-30 s and answered in s04 and s12.

**Fact check of this segment:** F04 (photo date), F02 (landing moved), F06 (273 mi), F03 (Artemis II, April), F14 + F20 (spacer replaces the stage; the
stage's job). Every frame's asset: research/media.json.

**Blocking a real test of these 20 s:** the four stills (a2-lunar-surface, a2-earthset, spacer, + d-* diagrams built from
them) are not downloaded yet. Run `ep008-fetch.yml` (push of fetch_list.txt), then check each is ≥1920 px wide.
The diagrams `d-orbit-vs-moon` and `d-sls-stack` still have to be drawn (yt-graphics). Temporary voice (free Kokoro, as EP007) is enough for the test; no ElevenLabs.
