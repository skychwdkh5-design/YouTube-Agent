# Visual style

A faceless channel's identity is its maps. This file is the style guide for geo-visuals, the
thumbnail brief in yt-package, and the vertical framing in yt-shorts.

## Principles

- **The map is the host.** Every beat has something to look at, and it is usually a map.
- **One idea per frame.** One highlight, one label, one arrow. Remove everything the beat does not
  need (labels, roads, neighbouring countries' detail).
- **Readable on a phone.** Labels at least ~5% of frame height in 16:9; test at phone size before
  export.
- **Movement means something.** Zoom to locate, pan to follow, draw to explain, highlight to
  reveal. No motion for decoration.
- **The screen matches the ledger.** Every on-screen number is the verified figure, with its year.

## Map style (fill in once the look is chosen)

- Base map: muted, low-contrast land and water so highlights pop. _Palette: TBD_
- Highlight color (the anomaly): one saturated accent. _TBD_
- Secondary color (comparison / "the other side"): _TBD_
- Disputed areas: hatched or dashed boundary, labeled "disputed" - never shown as settled.
- Typography: one sans-serif family, two weights. _TBD_
- Projection: equal-area for any size comparison; say so on screen when it matters. True-size
  overlays for "bigger than it looks" stories.
- Every map carries its data credit in the corner or in the end credits (see licenses).

## Pacing of visuals

- First 15 seconds: a visual change every 2-4 seconds. The anomaly is visible by second 3.
- First minute: every 3-6 seconds. After: every 5-10 seconds.
- Talking over a still map for more than ~8 seconds is a retention risk - add a zoom, a label, or
  a cut.

## Asset types and when to use them

| Type | Use for | Notes |
|---|---|---|
| animated map | locating, borders, routes, change over time | our core asset; built from public data |
| satellite | proving a place is real, showing terrain | NASA/USGS Landsat (public domain), Copernicus Sentinel (credit), Google Earth (follow Google's attribution rules) |
| stock footage | atmosphere, everyday life, infrastructure | licensed; record provider and asset ID |
| archival | history beats | Library of Congress / National Archives items with no known restrictions |
| infographic | numbers, comparisons, timelines | numbers exactly as in the ledger |
| AI visual | illustrations, reconstructions, moods | never as a real place, a satellite image, or archival footage; see below |

## Licenses - the rules `assets.py` enforces

- **Allowed without attribution:** public domain, U.S. government works, CC0, our own work.
  (Credit agencies anyway.)
- **Allowed with attribution:** CC-BY, CC-BY-SA, OpenStreetMap (ODbL, "© OpenStreetMap
  contributors"), Copernicus Sentinel ("contains modified Copernicus Sentinel data [year]"),
  Google Earth (Google's required attribution on screen).
- **Allowed with a license record:** paid stock - provider + asset ID in the asset row.
- **Not allowed:** unknown license, non-commercial (NC), no-derivatives (ND), "fair use" without
  human legal sign-off, screenshots of other YouTube videos, search-engine images, Pinterest.
- Check the license on each **file's own page**, not on the website's front page.

## AI visuals

- Stylized illustrations, diagrams and moods: allowed, AI column `stylized`.
- Photorealistic AI: only when it cannot be mistaken for the real place (e.g. a clearly
  hypothetical reconstruction labeled on screen), AI column `realistic`, and the
  altered/synthetic-content disclosure is turned on at upload.
- Never: an AI image presented as a satellite view, a photo of a real town, or archival footage.

## Thumbnails

- One map shape or one place, one highlight, max three words that do not repeat the title.
- High contrast at feed size; the anomaly visible in under a second.
- Real or faithfully mapped geography - no invented borders or misplaced places.
- Brand consistency: same highlight color, same type family. _Template: TBD_

## Shorts (9:16)

- Re-frame maps for vertical, do not just crop: the highlight sits in the middle third, labels move
  above and below.
- On-screen text in the first 2 seconds, different words from the spoken line.
- Safe zones: keep text away from the bottom ~20% and right edge (YouTube UI).
