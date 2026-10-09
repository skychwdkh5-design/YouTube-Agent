# EP002 Dubai — Full-Resolution Visual Audit (WoC archive)

Base: 8985400. Inspected: the 12 extracted JPEGs (3000x3000 each) in the local, git-excluded folder `visuals/_local_assets/woc/`. Method: native-pixel crops viewed 1:1 for B1; 800 px grid sheets (yellow lines every 500 original px) for framing; arithmetic per-row scan for black no-data; 800x450 crops of one rectangle across all 12 frames. Everything below is what I saw in those views. Not inspected: any NASA text beyond earlier notes, EXIF/metadata. Locked script and SHA-256 untouched; no downloads.
Coordinates are ORIGINAL pixels, origin top-left, x right, y down. Grid readings are precise to about +/-30 px. No geographic registration or scale is claimed; one rectangle reused across frames is a pixel convenience, not alignment (claim 32 stays UNVERIFIED).

## 1. B1 (dubai_ast_20020202_cyl.jpg)
**Distinguishable, but small and not palm-shaped.** At native resolution there is one small light-grey rectangular patch in open sea with a bright curved edge on its north-west side, a few tiny dark and light specks around it and a faint pale plume. Location about x 215-245, y 1545-1572. No fronds, crescent or palm outline are visible. Compared on the same pixel box: the 2000 frame shows empty sea there; the 2002-10-16 frame shows crescent and fronds, and the patch lies within that frame's palm bounding box (about x 175-515, y 1480-1800). By eye only; not registered.
What this supports: "something has appeared in the water at the palm site". It does NOT show an archipelago by itself; the caption claim 22 remains NASA's wording. The locked narration is unchanged; the visual must be a tight push-in with a callout, never a wide shot where the patch is a few pixels.
Proposed B1 rects (16:9): context (140,1445,800,450); target (0,1422,480,270) = about 4x to 1920 px, patch about 120 px wide on screen; soft, ASTER native detail ends here.

## 2. Full-resolution frame check
| frame | no-data (black) | clouds / artifacts | avoid in composition |
|---|---|---|---|
| 2000-11-11 | none | clouds over sea in top-left, x 0-525 / y 75-1125; two small wisps at x 45-120, y 1575-1655; scattered inland cloud and shadow patches | x<525 above y 1130; x<130 near palm row |
| 2002-02-02 | tiny top-left corner (x<139 at y 0) | none notable | -- |
| 2002-10-16 | top-left diagonal: x<704 at y 0, <392 at y 500, <136 at y 1000, none from y 1500 | none notable | x<700 above y 600 |
| 2003-11-04 | small top-left corner (x<143 at y 0, <16 at y 500) | many clouds and dark shadows inland right and top-left sea (x 100-860, y 100-525) | right half inland; top |
| 2004, 2005, 2007 | none | none notable | -- |
| 2006-09-18 | small bottom-right wedge (x>2925 at y 2500, >2814 at y 2999); top-left x<136 at y 0 | none notable; very dark sea | bottom-right corner |
| 2008-11-17 | left diagonal: x<431 at y 0, <310 at y 500, <191 at y 1000, <69 at y 1500, none from y 2000 (4.2 % zero) | cloud streaks at top, x 250-1250 / y 0-830, close to the east side of The World | top-left triangle; y<830 near x 1000-1250 |
| 2009-02-05 | right side: valid only x<1894 at y 0 down to x<1165 at y 2999 (49 % zero) | clouds bottom-left, x 0-1000 / y 2150-2700 | whole right half; bottom-left |
| 2010-02-08 | top-left: x<318 at y 0, <196 at y 500, <76 at y 1000, none from y 1500 | clouds bottom-left and bottom, y>2300; sea colour differs from other frames | y>2300; top-left |
| 2011-04-25 | right side: x<2767 at y 0 down to x<2073 at y 2999 (19 % zero); x<30 at y 0 | faint horizontal line across the sea about y 845, x 0-1500 (cause unidentified) | right edge; the y 845 line |
Sea tone varies between frames (near black in 2000-2007 and 2011, bright blue in 2009-2010): matters for dissolves and for the E1 strip.

## 3. Palm Jebel Ali in the WoC sequence
**Not covered by any of the 12 frames.** I looked at every frame; the coast leaves the image at the lower left (about x 0, y 2400-3000) before any Palm Jebel Ali shape appears. Palm Jumeirah and The World appear (The World from 2004; roughly x 340-920, y 560-1200, position differs by frame); Palm Deira is NOT identifiable here: reclaimed shapes sit along the top edge in 2005-2011 and are cut by the frame. Locked-script scenes naming Palm Jebel Ali: C1 (ASTER-2006 from NASA's Palm Islands page, not WoC), C2 (graphic only), D1 (narration names both palms; planned visual WOC-2002b shows only Palm Jumeirah), E2 (ISS photograph). Only **D1** mixes Jebel Ali narration with a WoC visual: it needs a non-WoC visual for the Jebel Ali half, or accepts that the picture shows Jumeirah only.

## 4. Crop rectangles (original px; x, y, w, h; 16:9)
Verified visually: (140,1405,800,450) on all 12 frames. In 2008-2011 the lower crescent arm touches the bottom edge, so I recommend moving down 40 px: **R_PALM = (140,1445,800,450)**; the +40 px shift is arithmetic and is not re-viewed.
| scene | frame(s) | rect | note |
|---|---|---|---|
| H1 | 2000 | R_PALM | clean sea; wisps start x<130, outside |
| H2 | 2003 | R_PALM | palm complete; no cloud in rect |
| A2 | 2000 | start (550,600,2400,1350) to end R_PALM | start avoids top-left clouds; includes creek, city, desert |
| B1 | 2002-02 | context R_PALM, target (0,1422,480,270) | see section 1 |
| B2 | 2002-10 | R_PALM | crescent and fronds fit; callout on ring |
| B5 | 2002-10 and 2003 | R_PALM for both | dissolve only, by eye |
| B6 | 2004, 2005, 2006, 2007, 2008 | R_PALM each | 2008 left border x<69 at these rows, safe |
| D1 | 2002-10 | R_PALM | Jumeirah only |
| D2 | 2000 and 2011 | (600,1000,1600,900) | avoids 2000 clouds, 2011 right no-data (valid to x about 2330 at y 1900) and the y 845 line |
| E1 | all 12 | R_PALM each (palm strip) | full frames would show black wedges; palm strip matches narration (empty sea, early stage, fronds in ring, finished palm, years of buildings) |
| E4 | 2000, 2003 | R_PALM | |
| E5 | 2000, 2003 | R_PALM | ISS crop is separate and not assessed here |
Never reuse these rects on the N3 ASTER-2006 or ISS files; their coordinates differ.

## 5. False-colour labelling
Direct evidence: vegetation and irrigated areas render bright red, sea blue to near-black, desert tan: colours are not natural. Documented evidence: none. Our NASA notes (claims 21-27, URL audit) give "ASTER on Terra" and no band combination. So: say nothing about bands (do not write "infrared", "bands 3-2-1" or similar); recommended on-screen wording until NASA's text is read: "NASA ASTER, [year], colours as published". Whether NASA calls it false colour is UNVERIFIED; the colours are visibly non-natural.

## 6. Scenes requiring changes (manifest edits, not made here)
- B1: tight crop and callout; expectation: small patch, not a palm.
- A2, H1, H2, B2, B5, B6, D1, D2, E1, E4, E5: replace "UNVERIFIED" crop text with the rects above.
- E1: palm strip (R_PALM), not full-frame thumbnails.
- D1: visual does not show Jebel Ali; add a source or accept Jumeirah-only imagery.
- All ASTER labels: add "colours as published"; do not claim a band combination.
- 2011: year only on screen.
Narration: no change required.

## Files audited
SHA-256 (first 16 hex) of each extracted JPEG:
| frame | sha256 prefix |
|---|---|
| 20001111 | `c4a93174e8c9c78f` |
| 20020202 | `8406807028a021d2` |
| 20021016 | `cf9c61b55c571135` |
| 20031104 | `2f217d353c1dd283` |
| 20041106 | `a57a51802e36b7af` |
| 20051024 | `6fb80e9a633abcfe` |
| 20060918 | `1e4aeb39c9da6b44` |
| 20070304 | `9e37bbb5da6b0abf` |
| 20081117 | `98b0570968fd5962` |
| 20090205 | `4f2c90f4f5a28294` |
| 20100208 | `1e747d9028485182` |
| 20110425 | `e6a17d657c7d3e4f` |

READY_FOR_NEXT_STAGE: YES for assembly planning with the rects above; B1 needs a person's eye on the final 4x crop.
