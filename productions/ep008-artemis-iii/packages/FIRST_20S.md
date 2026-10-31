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

## Test render 2026-10-31 (for owner review)
`hook20.py` → `test/EP008_hook20_test.mp4` (git-ignored; sent in chat) + `.srt` + `.timeline.json`. yt-qc: PASS (1920x1080, 30 fps,
20.0 s, full decode). Cuts follow the temporary voice (Kokoro am_michael, `tts_temp.py`): lunar 0.0-3.1 · orbit 3.1-5.8 ·
earthset 5.8-9.9 · SLS swap 9.9-16.9 · spacer 16.9-20.0. Frame 0 = the cover's exact crop of art002e009289.
Diagrams: `graphics.py` (`d_orbit_vs_moon`, `d_sls_stack`) in the NEXORA motion_spec style, labelled ORBITAL ATLAS DIAGRAM ·
NOT TO SCALE with source lines. Sound: synthesised in hook20.py (no library SFX), loudness -14 LUFS target.
Cover A: `covers/EP008_cover_A.jpg` - thumbcheck PASS (objective part: saturation 0.64, luma std 81). Grade only (warm
lunar tone, navy sky masked away from craters); no content added. Visual comparison with the four reference covers: done
by Claude, owner verdict pending (`thumbnail_hook.match_review`).

## Preview 2026-10-31 18:00 (owner request: first ~30 s, iPad)
`test/EP008_hook30_preview.mp4` (38.8 s = hook + scene s03 to the end of its open question; git-ignored, sent in chat),
captions `packages/EP008_hook30_preview.srt`. yt-qc PASS. H.264 High@4.1 + AAC, +faststart.
Mission chips on every frame (owner rule): blue "ARTEMIS II · FLOWN APR 2026 · REAL PHOTO" on all Artemis II pictures,
gold "ARTEMIS III · PLANNED 2027 · NOT FLOWN" on plan graphics, white "ARTEMIS III HARDWARE · ON THE GROUND, 2026" on hardware.
Frame 0 text now "ARTEMIS III PLAN: LAND HERE" over the Artemis II photo (no Artemis III tag on an Artemis II picture).
Cover A carries "Photo: NASA, Artemis II (2026)". Last hook line changed to the verifiable "and why the landing now
waits for Artemis Four" (the old "the Moon can wait a year" had no NASA source for a prior landing date).
