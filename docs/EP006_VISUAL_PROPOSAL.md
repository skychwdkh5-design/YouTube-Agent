# EP006 visual proposal on Visual Style V3 (proposal only: no production, no voice)

Topic is not chosen here. Candidates with satellite evidence already in the repo: Salton Sea (test production), others from `yt-topic`. The owner picks the topic; this document says how the film will *look* whatever it is.

## 1. One rule instead of quotas
For every claim in the script the planner/agent writes an **evidence card** (in `research/notes.json` -> `visual_choices` and in `story/STORYBOARD_*.md`): the claim id, the material that proves or explains it best, what was considered and rejected, the source and its rights status.
Ladder, in order of how well it proves a *measurement or event*: (1) our own satellite measurement; (2) archival footage or an official photograph of the event itself; (3) a documentary photograph of the ground; (4) an animated map / infographic built from verified data; (5) a labelled reconstruction (only when nothing real exists, and only to explain a mechanism or a plan, never to prove).
There is no minimum or maximum share of photos, video or maps. A scene may be satellite-only for two minutes if the measurement is the story, provided the reason is written down.

## 2. Toolbox and how each piece stays honest
| piece | what it is | how it is made / labelled |
|---|---|---|
| Real ground photographs | what the place looks like | `yt-media-research` ledger: source page, author, licence, rights evidence read on the page, file sha256; credit pill on screen; photo date and place in the caption; never used to carry a number |
| Archival footage / press video | what happened and when | same ledger; date and agency on screen ("NASA SVS, 2026"); played as released (no re-timing that changes speed without a "time-lapse" label) |
| Animated maps | where, how big, how it changed | built from our grid: scale bars computed, co-registered years, wipes only between same-grid frames; arrows and rings point at the measured feature |
| Infographics | numbers, comparisons, PROMISED / REPORTED / OBSERVED | yt-graphics from claims; one credit; appears when the claim is spoken |
| Camera language | slow push-ins; scale cascade orbit -> region -> site -> ground | match cut from a satellite frame to a photo only when the photo's location is verified on the grid; parallax ("2.5D") only on real stills, never on measured data |
| Edit | cinematic, narration-led | cuts on words and breaths, J/L cuts, one idea per beat, quiet space after a hard number; first 10 s: three different compositions |

## 3. Reconstructions and AI imagery (strict)
- A reconstruction (AI-generated, rendered or hand-drawn) enters the ledger as `kind: reconstruction|rendering|concept_art|illustration` with `depicts_reality: false` and a mandatory `on_screen_label`.
- The label is on screen for the whole shot ("AI RECONSTRUCTION - NOT A PHOTOGRAPH" / "ARTIST'S RENDERING") **and** spoken or captioned where the narration refers to it. yt-visualcheck FAILs a reconstruction that illustrates an observed fact.
- Never in the same frame as a measurement, never styled like satellite imagery or archival film (no film grain, no sensor look, no date stamps), never in the thumbnail as if real, never of identifiable real people.
- A reconstruction cannot support a claim; it can only help the viewer picture a mechanism or a plan that a verified source describes (cite that source on screen).

## 4. Pipeline status for this proposal
Working now: rights ledger, SVS public-page flow (real test passed), photo and video placement, evidence-justified monotony flag, word-anchored shot timing, graphics when the claim is spoken, single credit, kinetic captions.
To build before production (free, no cost): geolocated match cuts from satellite to photo; parallax for real stills; lower-third and reconstruction-badge templates in the renderer; video speed labels; Landsat frames in the evidence stack for checks that currently show Sentinel-2.

## 5. Blockers and owner decisions
See the closing report of 2026-10-21: network access to NASA Image Library, Earth Observatory image files, Wikimedia Commons and USGS files is denied by the environment (instructions in `docs/knowledge/media-access/MEDIA_ACCESS_TEST_2026-10-21.md`); topic choice; ElevenLabs plan check for commercial use; the owner's separate approvals for voice, full render and publication stay required.
