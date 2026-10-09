# Transition design system
Rule: pick by what changes in the story. Never use one pattern 3 times in a row. Test every transition for
black frames (mean luma < 8 for >2 frames unless a deliberate fade), text jump, and registration claims.
Status: only the first three have working reference code (EP002 `proof_v3.py`, Dubai-specific). None is in a
shared library yet (roadmap R2).

| transition | story purpose | implementation | limits | verify |
|---|---|---|---|---|
| Geographic match cut | same place, other time/source | cut at equal screen scale/position; year roll; labels persist | NOT a registered before/after unless co-registered (yt-geo); say so on screen | frame pair at cut: subject bbox centroid within 3 % |
| Push-through / scale | zoom from region to detail | log-zoom spline into a feature, cut at max zoom to a wider/other view | resolution limit of source | no blur beyond limit; cut frame sharp |
| Coast-follow dive | continue along a linear feature | camera follows traced coast polyline tangent, rotated to it | needs traced path | camera heading continuous |
| Mask reveal (radial/linear) | highlight one region | alpha mask from traced polygon, wipe fill | | fill edge coincides with outline |
| Line-trace reveal | introduce a boundary | stroke draw-on by arc length | traced/geo only | start/end at anchors |
| Focus (spotlight) | direct attention | dim outside mask 35–55 % | not on evidence's pixels for measurement claims (dim is a UI layer, flagged) | |
| Temporal jump | time change | rolling year digits + cut/dissolve | dissolve only same instrument | digits end on target year at cut |
| Directional motion | travel between places on a map | class B camera along geodesic | needs georeferenced data: NOT available | |
| Map-to-imagery reveal | locator → evidence | map camera lands on extent, image fades in in its real footprint | needs footprint georeferencing | footprint inside tolerance |
| Whip | energy beat | fast pan with blur into next | sparingly: ≤1 per video | |
Every transition entry in a storyboard must name: purpose, class, limits, verification.
