---
name: geo-visuals
description: >-
  Turn a verified geography script into a beat-by-beat visual plan for a
  faceless video - animated maps, satellite imagery, stock and archival
  footage, infographics, AI visuals - with a source and license for every
  asset. Use for "visual plan", "shot list", "what goes on screen", "storyboard
  this", "find footage", or before editing any faceless video.
---

# geo-visuals

A faceless video has no face to look at, so every second of the screen has a job. The map is the
host. If a beat has nothing to look at, it is a podcast, and people leave.

```bash
python3 assets.py channel/videos/<slug>/visuals.md --credits
```

## Before you start

1. Read `channel/visual-style.md` - map style, palette, type, motion, and the license rules.
2. The script must have passed geo-factcheck Gate 2. Visuals are built on verified wording.

## The plan

Work from the `[VISUAL]` and `[MAP]` notes in `script.md`, beat by beat, into `visuals.md`:

- **One asset row per distinct visual**, with Beat, Type, Description, Source, URL, License,
  Attribution and AI (no / stylized / realistic).
- **A visual change every 3-6 seconds** in the first minute, every 5-10 after. A zoom, a label, a
  highlight or a cut all count. Mark the beats where the screen would sit still.
- **The map tells the story.** Locator → zoom → the anomaly highlighted → the explanation drawn on
  top. Every key claim in the narration should be visible on screen as it is said.
- **Numbers on screen match the ledger exactly**, including the year ("Population: about X
  (2020 Census)").
- **True size, not Mercator,** whenever area is compared. Say which projection in the asset row.

## Sources, in order of preference

1. **Built by us** - maps drawn from public-domain data (U.S. Census TIGER/Line, Natural Earth,
   USGS) or OpenStreetMap data with attribution. Original work is the safest asset there is.
2. **Public-domain imagery** - NASA, USGS/Landsat, NOAA, Library of Congress items marked no known
   restrictions. Credit the agency even when not required.
3. **Attribution licenses** - Copernicus Sentinel, CC-BY and CC-BY-SA files (check each file's own
   page, not the site), Google Earth under Google's published attribution rules.
4. **Licensed stock** - record the provider and asset ID so the license can be shown later.
5. **AI-generated** - only for illustrations, reconstructions and moods, never as evidence. Never as
   a satellite image, a photo of a real place, or archival footage. Realistic AI means the
   synthetic-content disclosure is switched on at upload.

Never: screenshots of other YouTube videos, images from search results, Pinterest, or anything
with an unknown, NC or ND license.

## What to hand back

- `visuals.md` complete, and the `assets.py` result with GATE: PASS.
- The credits block for the description (`--credits`).
- Whether the upload needs the altered/synthetic-content disclosure, and which assets trigger it.
- The beats with the weakest visuals, so the editor knows where to spend time.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: **ship it, or change it?**
