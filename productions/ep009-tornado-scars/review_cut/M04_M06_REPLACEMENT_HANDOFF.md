# EP009: Replace 46 s review placeholders with actual NASA/USGS imagery
Date: 2026-11-03. NO topic research or new visual generation.

## Verified originals, now IN THIS GIT BRANCH
- M04 `productions/ep009-tornado-scars/media_original/nasa_aster_birmingham_20110504.jpg` — Terra ASTER, 4 May 2011, **false color**. 4096x6146, SHA256 cdb6624ca3924e2db8ef36c21516886c02aa7fcd3f20f479e1597bec61c23b18. Source https://science.nasa.gov/earth/earth-observatory/tornado-damage-near-birmingham-alabama-50462/ ; credit NASA Earth Observatory / Jesse Allen, data NASA/GSFC/METI/ERSDAC/JAROS, U.S./Japan ASTER Science Team.
- M05 `productions/ep009-tornado-scars/media_original/usgs_landsat_tuscaloosa_tornado_scar.png` — USGS Landsat tornado-scar image. 1108x577, SHA256 af3e08af2f69d9b6d6f8ea43de1850fe23aac4cc969636831e2fb8a27c8fff6c. Source https://www.usgs.gov/media/images/tuscaloosa-birmingham-tornado-scar-april-2011 ; Public Domain.
- M06 `productions/ep009-tornado-scars/media_original/usgs_lcmap_landcover_change_2011.jpg` — USGS LCMAP landcover change, long purple streaks mark landscape change coincident with tornado tracks. 3200x3200, SHA256 0986876597161e7f005d2603b3c5768405e1ed1b244890654b25b5b826a71360. Source https://www.usgs.gov/media/images/lcmap-landcover-change-2011-tornadoes ; Public Domain.
- Machine proof `media_original/m04_m06_manifest.json`; all three format and hash checks passed. Asset-specific placement/editorial viewing still pending.

## Exact review interval requiring replacement
Long `OA_EP009_REVIEW_LONG_localvoice.mp4` 378.6 seconds; placeholders approximately 243–284 seconds (actual visual inspection in conversation at 243,250,260,270,280,284 shows slides labeled REVIEW CUT PLACEHOLDER).
- ~243–265: replace ASTER slide with actual M04, show FULL SOURCE then meaningful crop/reveal of beige tornado scar. Keep `FALSE COLOR` label and credit; never invent geographic positions.
- ~265–284: replace USGS slide with M06; highlight source's *purple* land-cover-change streaks, label landscape change (not tornado filmed in progress). M05 can provide one genuine Landsat comparison if script/timing support it.
- Avoid upscaling 1108x577 M05 into extreme close-ups; 4096x6146 ASTER and 3200x3200 LCMAP allow conservative crops.
- Preserve existing voice and sound as much as practical. Re-render ONLY replaced scene segments and stitch; don't rerender full motion scenes. Include source credits on screen.
- Review actual scene boundaries in saved timeline first; timestamps above approximate; don't hardcode a replacement that overlaps dialogue or other scenes.

## Separate blockers, NOT cleared by obtaining these images
- GOES NOAA video attribution/embedded rights must be checked: official NOAA source references special thanks to UW-Madison CIMSS and others; no blanket claim all embedded elements public domain without review.
- One narration geographical statement about `north of University Mall` is unverified: remove/correct based on source, no guesses.
- Final Adam TTS needs explicit owner authorization; current Flite review is not release-ready.
- Thumbnail words `FROM SPACE` vs 0–7 s `THIS ISN'T A ROAD`: choose one exact hook; proposed change thumbnail to `NOT A ROAD`, but no owner signoff yet.
- Real exported master 1920x1080 must be checked independently. Chat attachment may be downscaled to 910x512; do not silently upscale that attachment.

## Bounded next action
1. Pull latest branch, assert three new source files exist and SHA256 pass.
2. Inspect local review build code and replace placeholder scenes with originals; touch no other motion scenes unless they fail QC.
3. Run one targeted segment render and validate visible actual images and labels, then produce one updated Long review, two existing Shorts preserved.
4. If errors, report specific failure only; no animation R&D, no vidIQ.
5. NEVER upload/publish, launch ElevenLabs, or edit scheduling absent explicit authorization.
