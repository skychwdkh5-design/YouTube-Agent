# OrbitalAtlas thumbnail style guide (standard for every long-form episode)

Status: permanent. A cover that visibly departs from this guide is **FAIL** and is revised before approval.
Reference set = the four covers published on the channel (screenshots in `docs/assets/thumbnail-reference/`):
**EP001 The Sahara Is Changing**, **EP002 Built From Nothing (Dubai)**, **EP003 20 Feet Lower (Great Salt Lake)**, **EP004 Jakarta Is Sinking**.
The earlier flat, dark draft covers kept in some branches are NOT the style. The first EP005 cover (beige, low contrast, tiny subject) is the counter-example.

## 1. What the four published covers share

| | Sahara | Dubai | Great Salt Lake | Jakarta |
|---|---|---|---|---|
| Headline | THE **SAHARA** / IS CHANGING | BUILT FROM **NOTHING** | 20 FEET **LOWER** | JAKARTA / **IS SINKING** |
| Image | Earth from orbit, gold desert, green circles | before beach | after island | glowing flooded skyline |
| Change device | 1984 -> 2024 badges + white curved arrow | thin white divider + yellow arrow | white divider + red arrow | red/yellow subsidence heat map |
| Extra | satellite in corner | red DUBAI ribbon, "3 YEARS" badge | red underline stroke | satellite + radar beam |

The DNA (measured on the four: saturation 0.46-0.58, luma contrast 64-73, white 3-7%, gold text and accents 1.5-6% of the frame):
- **Big YouTube documentary look**: glossy, hyper-saturated, high-contrast, golden-hour or deep-ocean colour, a glow around the hero.
- **Headline on top 25-35%**, two lines or one, condensed heavy display capitals (Anton / Impact family), **white + yellow/gold** (the key word is yellow), thick black outline and drop shadow.
- **One hero visual** from real satellite/aerial data, enhanced: Earth-from-orbit view, before | after split, or a data overlay (heat map). One clear arrow or divider shows the change.
- Small support badges only: years (dark rounded badge), one short label, one ribbon, a satellite icon.
- Reads in one glance at phone size; the picture explains the hook even without the title.

## 2. Specification

- 1280x720, under 2 MB, safe margin 48 px; must read at 168x94 px.
- Headline 2-7 words (3-7 incl. badges), UPPERCASE, heavy condensed sans, cap height at least 110 px, outline 6-10 px + shadow. White main, **yellow/gold #FFC245-#FFD21E accent on the key word**. Red (#E5322D) only for an alarm accent: arrow, underline or ribbon, never body text. Never grey text.
- Grade: saturated and bright-contrasty (target saturation >= 0.45, luma std >= 60). No grey, beige, washed-out or hazy frames.
- One focus + one message. Max one arrow, one divider/split, up to two small badges.
- Real data only: enhancement (grade, glow, 3D globe, heat-map styling, framing) is allowed; **inventing structures, events or numbers is not**. The hero must be the real pixels the video shows, and the headline must not claim more than the video's evidence (e.g. never "built" or "failed" if the video says "cannot tell").
- Must not: grey/beige, low contrast, long phrases, small text, clutter, news-banner, infographic, film-poster, clean minimalism, shocked faces, stock art.

## 3. Archetypes (stay inside one)

- **A. Before | After split** - divider + arrow, two year badges, 2-4 word headline on top. (Dubai, Great Salt Lake)
- **B. Orbit hero** - Earth/limb view or aerial hero with satellite, two-line headline on top, year badges, one arrow. (Sahara, Jakarta)
- **C. Data overlay** - real image + styled overlay on the one thing that matters (heat map, ring, arrow), headline on top. (Jakarta)

## 4. Per-cover checklist (all YES)

1. Side by side with the four published covers it looks like the same channel?
2. States the hook at once without the title?
3. One focus, one message?
4. Legible at 168x94 px?
5. Saturated, glossy, high contrast (no grey/beige)?
6. UPPERCASE heavy headline, white + one yellow word, outlined?
7. True to the video's evidence (no invented content)?

## 5. Gate (pipeline rule)

Before any long-form cover is approved or uploaded Claude must:
1. Run `python3 .claude/skills/yt-package/thumbcheck.py cover.jpg` (1280x720, <2 MB, contrast, saturation, white headline, yellow accent). Necessary, not sufficient.
2. View the cover next to the four reference covers and at phone size, answer section 4 and record the verdict in the episode review file.
3. Any failure of either step is **FAIL**: revise, never argue it through.
4. `publish/queue.json` carries `thumbnail_review: {"result": "PASS", "sha256": <sha256 of the cover file>}` for every long episode; `queue-run` refuses the upload otherwise or when the file changed after review. Claude's PASS is a precondition, not the owner's approval.
