# S3 V2 - three staging options and the choice (2026-10-15)

Owner review of V1: REVISE (flat, presentation-like, too much text, sinking not the hero). Constraints kept: ILLUSTRATION only, no measured values,
no ESA frame, RSASE = ABSTRACT_VERIFIED only, physics of line-of-sight measurement exact. Reference files VISUAL_REF_001/002 are NOT available
(not in the repo, any branch, or the owner's Google Drive - searched 2026-10-15); comparison uses the written analyses and effect records.

| criterion (weight) | A "Cutaway Descent" | B "Orbital Split" | C "Beam Ride" |
|---|---|---|---|
| idea | perspective camera over a 3-D cut-away block of city ground; satellite passes; camera follows the pulse down, dives to the cut face (aquifer + clay), pumping -> pressure drop -> clay compaction -> ground sinks (hero), second pass, then the camera settles exactly side-on to the cut plane where the LOS vs vertical geometry is drawn true | two side-by-side 2.5D panels "PASS 1 / PASS 2" with kinetic type between them | first-person ride along the radar pulse from orbit to the ground and back |
| depth / parallax (3) | real perspective, layered floor, dust, buildings - 3 | panels tilt only - 1 | strong but one-dimensional - 2 |
| sinking as hero (3) | the cut face shows *why* and *where* the ground drops - 3 | small in two panels - 1 | ground seen only head-on - 1 |
| LOS correctness readable (3) | final camera is perpendicular to the plane that holds satellite, point and drop: right angle shown true - 3 | good (side view) - 2 | poor (looking along the beam hides the angle) - 1 |
| text load (2) | one caption or one label at a time; LOS lockup replaces labels - 2 | needs labels per panel - 1 | low - 2 |
| reference match: VR1 camera language / VR2 type (2) | continuous moving camera + weight-contrast lockup - 2 | type-led - 1 | camera-led - 2 |
| risk / cost (1) | new reusable 3-D-lite module, ~1 day - 1 | low - 2 | medium - 1 |
| **weighted** | **40** | 20 | 23 |

**Choice: A.** It is the only option where the cause (pumping, compaction) and the measurement (two passes, extra path, LOS projection) live in one
continuous space, which is what VR1's continuous camera does for geography. Honesty: it is a schematic 3-D illustration (camera class "illustration"),
not a georeferenced flyover; labelled ILLUSTRATION / NOT TO SCALE / DROP EXAGGERATED on screen.
Physics kept explicit: confined aquifer stays saturated (pumping lowers pressure/head, shown by the water level in the well), compaction happens in
the clay layers, surface lowering = sum of clay thickness loss (the geometry enforces it), echo of pass 2 goes to the lowered point, extra range and
LOS component computed by `illustrate.los_change`.
