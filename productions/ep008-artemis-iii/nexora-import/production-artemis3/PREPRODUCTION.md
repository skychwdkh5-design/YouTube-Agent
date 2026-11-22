# Artemis III — pre-production (2026-10-30)

Branch `production/artemis3` (from `youtube-ops`). Nothing rendered for release, voiced with a paid
service, uploaded or published. Inputs reused, not re-researched: `research/runs/2026-10-30-growth-demo/`
(sources, media, three packages, outline).

## Files
| file | what |
|---|---|
| `script.md` | 881 words, 6:34 with the temporary voice; every factual line tagged; plans worded as plans |
| `sources.json` | 30 claims from 6 official NASA pages (2026-02-27 … 2026-10-23), verbatim quotes where the re-check got them; `excluded` lists what was cut |
| `media.json`, `ASSETS_NEEDED.md` | 6 NASA originals with file URL, page, author, licence, size seen, every second used |
| `thumbnail_hook.json` | 3 cover + title + first-15-s packages; A chosen; QC 7/8 pass, `match` waits for the owner |
| `edit_plan_shots.csv` | 65 shots: in/out, picture, credit, on-screen text, direction, claims |
| `edit_plan.csv` | second-by-second map (0-394 s): picture, slot/graphic, on-screen text, temp voice |
| `motion_spec.json` | 22 original graphics: on-screen text, motion, label |
| `captions_temp.srt` | phrase captions timed to the temporary voice (re-time on the final voice) |
| `scenes.json` | nx-scenes plan (photo scenes point at `assets/<slot>.jpg`) |
| `hook20/` | first-20-s test builder + storyboard with labelled empty slots |
| `preprod.py`, `voice_temp.py` | rebuild everything after a script change |

## 1. Fact re-check (official NASA pages only, read 2026-10-30)
Flight order confirmed verbatim on NASA's 2026-10-23 mission page: Blue Moon Mark 2 test article launches
first into a circular LEO (can stay up to 30 days) → Orion on SLS from Kennedy "only days after" →
elliptical 18 × 1,122 mi → circular ~345 mi for thermal stabilization → 2 days of checkout → docking at
the port beside Blue Moon's crew cabin, crew enters, ~2 days of evaluations → Starship V3 test article
from Florida, lower orbit 206 nmi (communications coverage), docking on Orion's forward system, up to
two hours, crew does not enter → up to 5 more days of tests → splashdown in the Pacific, NASA + US Navy
recovery. 14-day mission. February page: test flight in LEO in 2027, one or both landers, landing on
Artemis IV in 2028, at least one landing per year after.

**Cut as unconfirmed or wrong:** Blue Moon at ~273 mi, splashdown "off California", Starship "about one day"
(wrong), any launch date, the unattributed "three spacecraft on three rockets" quote, anything after 2026-10-23.
**nx-sources:** FAIL by design until a person re-reads the six pages and sets claims to `verified`, and the six
files are downloaded and checked (`verified: true`). No line states a plan as a fact any more (the gate caught 33
and they were reworded with "plans", "expected", "according to NASA", "announced").

## 2. Choice of package (docs/growth/THUMBNAIL_PLAYBOOK.md criteria, 1-5)
| criterion | A "Won't Go to the Moon" | B "Docking … in Earth Orbit" | C "4 Astronauts - Not to the Moon" |
|---|---|---|---|
| promise literally true (NASA) | 5 | 5 | 5 |
| cover object = real legal NASA image usable at 0:00 | 5 (boosters photo) | 3 (NASA graphic, not a photo) | 5 (Orion photo) |
| one concrete question | 5 (why not the Moon?) | 3 (how?) | 4 |
| one object, readable at phone size | 4 (tall boosters; vertical crop) | 3 (busy graphic) | 4 |
| text ≤ 5 words | 5 (NOT THE MOON?) | 5 (DOCK FIRST) | 5 (ORBIT ONLY) |
| does not imply this week's news | 5 (hook says February) | 5 | 5 |
| **total** | **29** | 24 | 28 |

A wins on the question and the real cover object; C is a close alternate. These are editorial scores,
not a CTR forecast — B and C stay for the A/B test (H-T1 in docs/growth/EXPERIMENT_LOG.md).
**Cover ↔ first frames:** cover A = boosters photo `n1-boosters` + "NOT THE MOON?"; the video opens on the same
photo at 0.0 s, the line names the rocket at 0.0-3.5 s and "won't go to the Moon" lands at 3.5-8.1 s. QC
`thumbnail_hook_subject_first_3s` passes; `thumbnail_hook_match` passes only after the owner compares the real cover
with the rendered first frames.

## 3. Edit structure (6:34, 65 shots, average 6 s, longest ~12 s with a build inside)
Hook 0:00-0:24 · Part 1 what changed · Part 2 who flies (names only, no crew photos) · Part 3 the flight in five
steps (animated orbit/docking diagrams, labelled ILLUSTRATION) · Part 4 why dock first · Part 5 what it means +
honest "no launch date" · close on the boosters. Four 2-s chapter cards. Evidence on screen: date stamps and the
NASA source line on every number and plan.

## 4. Open risks
- Real NASA imagery is only **30 %** of screen time (6 stills); 70 % is original graphics. More NASA
  hardware video/photos would make it feel more documentary — they need the same download route as the 6 stills.
- The two portrait photos (n1, n2) need originals ≥ 1920 px wide for a sharp 16:9 crop.
- Temporary voice is Kokoro (local, free, Apache-2.0) — timing only, not for release.
- Plan wording is heavier after the gate ("plans", "expected"); read the script aloud once before the final voice.
