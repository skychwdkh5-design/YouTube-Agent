# Episode 001: source audit round 10 (2026-10-08): L1 pivot diameter, SCRIPT LOCK v1.1

## Change (Option A, approved by the reviewer)
ACT 4, one sentence.

- OLD: "Today, it's covered in green circles, each roughly a kilometer across, watered by rotating sprinkler arms."
- NEW: "Today, it's covered in green circles, each about half a mile across, watered by rotating sprinkler arms."

All other spoken words are unchanged (checked sentence by sentence: 120 sentences, exactly 1 differs). Spoken words 1,777 to 1,778. The tag after the sentence changed from "PROVISIONAL" to "diameter measured on Level-1 source bands".

## Evidence (Level-1 source bands; the browse image was only a first estimate)
| Measurement | Value |
|---|---|
| 2024-01-05 Landsat 9 (LC09_L1TP_177044_20240105), B4/B5, TOA NDVI, isolated near-circular components | N = 1,350; median equivalent diameter 819 m; IQR 796-829 m; nearest-neighbour centre spacing about 985 m |
| 2010-01-22 Landsat 5 (LT05_L1TP_177044_20100122) | N = 300; median 757 m (younger, partly grown circles) |
| Same circles matched 2010 vs 2024 | 115 pairs, median difference -5 m; both-full pairs 804 m vs 803 m |
| NDVI threshold 0.2-0.4 | 810-837 m |
| Uncertainty | about ±30 m (one pixel) |

Half a mile is 805 m. About 1 km is the centre spacing, not the diameter. Files: `landsat/measurements/east_oweinat_pivots_2024_vs_2010_source_bands.json`, `east_oweinat_pivots_20100122.json`, `browse_verification.json`. The earlier browse-only figure (0.87 km) counted green pixels on a 30 m browse image and is superseded.

## Limits
Circle shape is a detection criterion (isolated, near-circular, fill >= 0.85), so partial circles and fused fields are excluded by design. The statement is about typical circles, not every field. The measurement says nothing about vegetation change.

## Hashes (method: SHA-256 of UTF-8 text from the line "## COLD OPEN" to end of `script.md`)
- v1.0 (commit 706a280, recomputed): `14a046218fa590d06f44605bb6ad6ed1965ab85da8bcb88216e3d91a8e5ed950`
- v1.0 as recorded in the old SCRIPT_LOCK.md: `e58756dff1179d5ae6d20d29f2f9d9215d6820899300e6630196e464446dfa18` (does not reproduce, see the note in `SCRIPT_LOCK.md`)
- v1.1: `d646001c83d3421d43510ece1926d7bd49bc197dcdde07b94fd2f4f3a049f335`

## Files changed
`script.md`, `storyboard.md` (scene 18 label), `story/claims.md` (L1 row and header), `story/SCRIPT_LOCK.md`, `preproduction.md`, this file.
