# Proposed narration correction for L1: NOT APPLIED (script lock v1.0 stays in force)

## Finding
Measured on original Level-1 bands, a typical complete irrigation circle at East Oweinat is **about 0.80-0.82 km across** (2024: median 819 m, n=1,350; 2010: 757 m over all circles, 804 m for 90 circles that are complete in both years; threshold range 0.2-0.4 gives 810-837 m; uncertainty 30 m per circle). **Neighbouring circles are about 0.9-1.0 km apart** (2024 median 985 m). The locked sentence says the circles are "each roughly a kilometer across": that is the spacing, not the diameter, and overstates the diameter by about 20%.

## Current text (script.md, ACT 4)
"Today, it's covered in green circles, each roughly a kilometer across, watered by rotating sprinkler arms."

## Minimal correction (recommended, option A)
"Today, it's covered in green circles, each about half a mile across, watered by rotating sprinkler arms."
(819 m = 0.51 mile; 0.80 km = 0.50 mile.) The spoken text gains one word (1,777 to 1,778), the runtime does not change.

## Alternative (option B), if the kilometer is kept
"Today, it's covered in a grid of green circles, about a kilometer apart, watered by rotating sprinkler arms."

## Audit changes required if A or B is approved
1. `script.md`: the one sentence; the L1 tag note ("exact pivot diameter PROVISIONAL") becomes "diameter measured on Level-1 bands, see landsat/measurements".
2. `storyboard.md`, scene 18: label "~1 KM CIRCLES" becomes "~0.8 KM (HALF A MILE) ACROSS" (option A) or "~1 KM APART" (option B).
3. `story/claims.md`, row L1: new wording, measured values, method and the 2010/2024 comparison; claim stays VERIFIED.
4. `story/source_audit_round10.md`: record this finding, the method and the uncertainty.
5. `story/SCRIPT_LOCK.md`: new version (v1.1), new SHA-256 of the narration text, word count 1,778, a note that only the L1 sentence changed.
6. `preproduction.md`: word count and the note that the L1 diameter is now measured.
7. Re-run the offline tests; commit and push only to this branch.
