# OrbitalAtlas Visual Style V3 (from EP006)

V2 (EP002-EP005) is a continuous demonstration of satellite images with infographics. V3 is a documentary for an American audience: **satellite data + real photographs +
real video + infographics + purposeful motion graphics**, with the satellite data still carrying every measurement. Style is switched on per episode with
`research/notes.json` -> `"style": "v3"`. Everything below is enforced by tools, not by good intentions.

## 1. Material classes and what each is for
| class | use it for | never use it for |
|---|---|---|
| Satellite frames (Sentinel-2, Landsat) | evidence, measurement, change over time | decoration; filling time |
| Real photographs / video (rights VERIFIED) | context: what the place, structure, people, event looks like on the ground | proving a measurement; anything a caption would claim it shows without a reviewer |
| Infographics (yt-graphics) | numbers, comparisons, the PROMISED / REPORTED / OBSERVED separation, timelines | restating what the narrator just said word for word |
| Maps (locator, scale) | where, how big (scale bars computed from the grid) | a "cool" flyover with no data meaning |
| Renderings, concept art, illustrations | showing a plan or an idea | standing in for a photograph of something that exists. Always labelled on screen (ARTIST'S RENDERING / CONCEPT ART / ILLUSTRATION) |

## 2. Rights: a material enters a render only with status VERIFIED
`yt-media-research` keeps `media/ledger.json`. Per entry: source page URL, author / rights holder, licence, commercial-use answer, attribution requirement and text,
modification limits (class notes), the scene it serves, the claims it carries (usually none), `rights_evidence` (the licence statement read ON the source page, with the date),
local file and sha256, and a status:
- **VERIFIED** - recognised free licence (public domain, CC0, CC BY with attribution text, US government work, Pexels / Pixabay / Unsplash licence) + evidence + author + file + sha256.
- **NEEDS_OWNER** - CC BY-SA and other licences that carry conditions on our film; the owner decides.
- **UNVERIFIED** - rights look fine but evidence or file is missing, or the file changed after verification.
- **DISCOVERED** - found (for example by a Google/web search) but the licence was never read on the source page. A search result is a pointer, never a permission.
- **REJECTED** - all rights reserved, NC, ND, stock-agency or editorial-only material.
The planner draws only VERIFIED entries whose file still has the recorded sha256. yt-visualcheck FAILs a shot whose media is not VERIFIED, whose file changed, or a rendering used
to illustrate an observed fact. Pending entries are listed in the storyboard report ("media PENDING") with the slot they would take.
Sources: Wikimedia Commons, NASA Image and Video Library, USGS (manual), Pexels, Pixabay, Unsplash, official press kits (manual, quoting the terms sentence). Commercial-use and
modification rules are encoded in `yt-media-research/media.py` (`RULES`), including the caveat that a US-government work can contain third-party material that is not free.
Network access and legal permission are separate questions. Reachability is measured (`media.py probe`: free public hosts and API providers, one row per host); the right to use a file comes only from `rights_evidence`.
Free public pages need no API key: `media.py svs --url <SVS page>` reads an SVS page and its rights FAQ and builds the entry; `fetch --confirm` downloads and hashes. Paid APIs and stock agencies are not used.

## 3. Shot grammar (checked by `story/diversity.json`) - no quotas
There is **no percentage or minimum count of photographs or video**. Every scene uses the material that best proves or explains its claim: a measurement is shown by the satellite frames, a
comparison by a graphic, a place or an event the viewer must *see* by a real photograph or archival clip. The tools only flag monotony so that a person has to decide on purpose:
- A run of more than **4 satellite-map shots** in a chapter is flagged. It clears when the chapter has a stated reason in `research/notes.json` -> `visual_choices[<chapter>]` (why maps are the best evidence there) or when other material breaks the run.
- Neighbouring map shots that end at the same scale class (wide >= 10 km / mid 4-10 km / tight < 4 km) are flagged; alternate scales.
- In `style v3` every chapter needs either a VERIFIED medium or a `visual_choices` sentence before planning (stage `media`), and an unresolved monotony flag blocks the storyboard stage.
- First 10 s: at least 3 distinct compositions, 3 information events, 3 visual families (yt-render lint).
- Year images and wipe reveals appear **when the narrator says the year**; a graphic that cites claims appears when the claim is spoken (and is never squeezed below 3.5 s).
- A wipe is one reveal followed by the revealed picture, never repeated. Beats of one visual alternate wide and tight (>= 1.5x). Every full-frame graphic or photo has a slow push-in; nothing is a still for more than 7 s.

## 4. Motion graphics and type (meaningful only)
Allowed: slow push-ins, camera moves that change scale, a wipe between co-registered years, an arrow or ring that points at the measured thing, a counter that lands on its number,
kinetic captions with the **spoken word lit** (amber), a soft shade behind captions for legibility, date badges taken from scene metadata.
Not allowed: decorative glitch/flash/shake, particle effects with no data meaning (an illustration is labelled as one), 3D text that hides the picture, music-driven cuts that fight the narration,
any effect that moves a measured feature relative to the grid.
Type: Inter; amber `#FFD23F` for emphasis, white text with dark stroke, cyan for data/source; captions inside the safe area (long: lower band; Shorts: x 80-1000, y 250-1500).
Credits: one credit pill per picture, printed once (graphics do not print their own).

## 5. Science and honesty rules that do not change
Three-way separation PROMISED / REPORTED / OBSERVED where relevant; observations carry the data check; limitations are said aloud; hypotheses are hedged; low-confidence claims are not drawn; a
photograph never makes a claim stronger than its caption.

## 6. Pipeline
`topic -> research -> facts -> evidence -> script -> media -> visualplan -> visuals -> storyboard -> visualcheck -> voice (paid, owner) -> voicecheck -> captions -> render (owner) -> qc -> release`.
`media` is AGENT_REQUIRED in v3 until each chapter has a VERIFIED medium or a stated `visual_choices` reason (`tasks/media.md` tells the agent how) and a pass-through for v2.

## 7. Known limits
- Network access to the free public media sources is partial in the build environment (measured, see docs/knowledge/media-access/MEDIA_ACCESS_TEST_2026-10-21.md).
- Video clips are supported by the renderer (same fps and aspect required); the planner currently places photos only.
- Rendering/concept art needs its on-screen label text in `on_screen_label`.
