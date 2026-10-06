# Script: Why Does This Part of the U.S. Belong to Minnesota? (working) - V2 retention edit

- Format: main long-form
- Target set: about 8:00-8:20. Actual V2: 975 spoken words + 16 s of marked pauses = about 6:46 at 150 wpm (see footer note)
- Winning hook formula: The Only Way In (hookscore --profile geo: 76 STRONG) - the road through Canada is the anomaly the viewer can see on the map in the first three seconds
- Structure: B "Follow the Drive", with A's historical midpoint (approved 2026-10-06); V2 = retention rewrite from the approved audit
- Gate 2: PASS, 2026-10-06 (`claims.py --claims claims.md --script script.md`, 0 fails) - V2

Conventions:
- `VO:` lines are the narration - the only lines the AI voice reads and the only lines `claims.py` checks.
- `[VISUAL: ...]` says what is on screen while the line is read. Asset IDs (V1-V11) are from `visuals.md`.
- `[PAUSE n s]` is an intentional silent beat held on the visual; it counts toward runtime.
- `[C#]` after a factual sentence links it to the ledger. `[NC]` = reviewed, not a factual claim.
- SOFTENED claims use their Final wording or something more cautious. No line describes how Mitchell drew the lake or the river (C5, C6), names the Mississippi's source (C9), or mentions the RABC change (C32).
- Timecodes are computed from the narration at 150 wpm plus the marked pauses.

## HOOK (0:00-0:10)
[VISUAL: V5 - contiguous U.S. outline from TIGER, slow push-in on Minnesota's northern edge; the "chimney" pulses once.]
VO: You see that bump on top of Minnesota? [NC]
VO: It's American, but the only year-round road to it runs through about 40 miles of Canada. [C27] [C28]
VO: Why? [NC]

## THE TIP IN THE WATER (0:10-0:25)
[VISUAL: V5 - pin on the tip; on-screen label "Northwest Angle - part of Angle Township, Lake of the Woods County, MN" (C20 wording, on screen only). HARD CUT to V3 - NASA Landsat "An Unusual Angle": the pin sits in open water.]
VO: This is the Northwest Angle. [NC]
VO: Its tip is the northernmost point of the Lower 48. [C23]
VO: And that tip isn't on land - it's a boundary point out in the water of Lake of the Woods. [C24]
[PAUSE 1 s]

## THE DRIVE (0:25-1:11)
[VISUAL: V8 - road animation on OpenStreetMap data. Car icon at Warroad. Shield "MN 313" on screen only.]
VO: To see why it's American, start with how you'd get there. [NC]
VO: Begin in Warroad, Minnesota, and head north. [C27]
VO: The highway carries you straight across the border, into Manitoba. [C27]

[VISUAL: V8 - the border line flashes as the icon crosses; the map tint shifts from U.S. to Canada. Shield "PR 308" on screen. Corner counter starts: "miles in Canada".]
VO: You keep driving north, through Canada. [C27]
VO: Then the road bends east, and crosses back into Minnesota. [C27]

[VISUAL: V8 - shield "PR 525"; the icon re-enters the Angle; the counter stops at "≈40 mi in Canada".]
VO: That's about 40 miles of another country, just to reach your own state. [C28]
[PAUSE 1.5 s]

[VISUAL: Simple motion graphic, no photos - a booth icon with a video-phone symbol, and a phone with an app screen. Label: "Remote check-in". Map pin on Jim's Corner from V5.]
VO: And when you arrive, there's no staffed border post waiting. [C30]
VO: You check in remotely, at a video-phone booth like the one at Jim's Corner, or with an app. [C30]

[VISUAL: V8 + V5 - zoom out until the whole route fits the frame. The words "only year-round road" type on, then "year-round" stays highlighted while the rest fades.]
VO: So the only year-round road to the Angle runs through Manitoba. [C27]
VO: Notice that word, though. [NC]
VO: Year-round. [NC]
VO: Hold on to it. [NC]
VO: First, the bigger question. [NC]
[PAUSE 1 s]

## THE BORDER BREAKS ITS OWN RULE (1:11-1:44)
[VISUAL: V6 - Natural Earth continental map. The U.S.-Canada border draws itself along the 49th parallel from the Rockies east across the plains; label "49th parallel". At Lake of the Woods it jogs north; a bracket on the jog reads "≈27 mi". Freeze on the jog.]
VO: Zoom out, and the strangeness gets clearer. [NC]
VO: Out west, the border between the U.S. and Canada follows one line of latitude across the plains: the 49th parallel. [C11]
VO: Then, at this one lake, it jumps about 27 miles north. [C26]
VO: The Angle is the only sizable piece of the Lower 48 north of the 49th parallel. [C25]
VO: So why would a border do that? [NC]

[VISUAL: V6 - the modern map desaturates into parchment texture and cross-dissolves into V1.]
VO: You'll often hear it called a mapping mistake. [NC]
VO: That's close. [NC]
VO: But the real story is stranger, and it starts with a map. [NC]

## THE MAP (1:44-2:22)
[PAUSE 1.5 s - hold on the parchment before the first line]
[VISUAL: V1 - John Mitchell's map, Library of Congress. Slow push across the full sheet, then a move to a second region. Title card: "John Mitchell, 1755". No arrows or labels on the lake or the river.]
VO: This is John Mitchell's map of North America, first published in 1755. [C4]
VO: When American and British diplomats sat down in Paris in 1782 to make peace, this is the map they drew the new borders on. [C3]

[VISUAL: Quote card over V2 (second LoC copy, cartouche close-up), held about 4 s: "Upon that map, and that only, were those boundaries delineated." - John Adams, 1796.]
VO: John Adams later wrote that the boundaries were drawn on that map, and that map only. [C3]

[VISUAL: 2-second CALLBACK - cut back to the V8 route glowing through Manitoba, caption "it starts here"; then return to V2, drifting west across the interior. Overlay text only: "Badly inaccurate in the far west".]
VO: So the story of that road through Manitoba starts right here. [C3]
VO: And here's the problem. [NC]
VO: It was a map that was badly wrong about the far west. [C3]
VO: And the far west is exactly where the border had to end. [NC]

## THE IMPOSSIBLE INSTRUCTION (2:22-3:15)
[VISUAL: V6 base map. Typeset title: "Treaty of Paris, 1783". The boundary draws itself west through the Great Lakes to Lake of the Woods, then a pin pops on the lake's northwest corner.]
VO: The peace treaty was signed in 1783. [C1]
VO: It ran the border west to Lake of the Woods, and through the lake to "the most northwestern point." [C2]
VO: And from there? [NC]
VO: "On a due west course to the river Mississippi." [C2]

[VISUAL: V9 - from the pin, a red line shoots due west along 49°23'N. The real Mississippi, from TIGER data, lights up far to the south. The red line passes north of it and keeps going. FREEZE the frame as it overshoots.]
VO: On paper, that sounds precise. [NC]
VO: Find the corner, draw a line due west, meet the river. [NC]
VO: Here's the catch. [NC]
VO: The Mississippi never comes that far north. [C7]
[PAUSE 1.5 s]
VO: Its northernmost reach stays roughly two degrees of latitude south of that corner of the lake. [C7]
VO: A line due west from the lake passes north of the river and never touches it. [C7]

[VISUAL: Typeset quote card, typeset by us from the Avalon Project text (same source and license as V10): "uncertain whether the River Mississippi extends so far to the Northward" - Jay Treaty, 1794.]
VO: The diplomats noticed. [C10]
VO: By 1794, a new treaty admitted it was "uncertain whether the River Mississippi extends so far to the Northward." [C10]
VO: The 1783 line couldn't work. [C7]
VO: The border needed a new rule. [NC]

## THE 1818 RULE (3:15-3:44)
[VISUAL: Step-by-step animation on V5/V6, one step per sentence. Step 1: the 49th parallel draws itself west from the lake. Step 2: the northwest-corner pin glows. Step 3: from the pin, two arrows - one up, one down - with a "?" between them. Step 4: a line drops to the parallel and turns west. A short V10 caption appears with step 3 only: "due North or South as the Case may be" - Convention of 1818.]
VO: That rule came in 1818. [C11]
VO: West of the lake, the border would follow the 49th parallel. [C11]
VO: But the lake's most northwestern point stayed in the deal. [C11]
VO: So here's the rule. [NC]
VO: Start at that point. [C11]
VO: Run a line due north or south until you hit the 49th parallel. [C11]
VO: Then turn west. [C11]
VO: Think of it as a recipe with one missing ingredient. [NC]
VO: Simple - as long as you know where the point is. [NC]
[PAUSE 1 s]

## FINDING THE POINT (3:44-4:51)
[VISUAL: V3 - Landsat view of Lake of the Woods. Candidate markers pop up one by one; the first, far to the east, labeled "Rat Portage - today's Kenora". Title card: "1820s".]
VO: And that turned into a surveying puzzle. [NC]
VO: Which spot on this lake counts as the most northwestern? [NC]
VO: Even the surveyors came up with more than one answer. [C13]
VO: In the 1820s, a British boundary surveyor put forward several possible "northwestern points" - the first of them at Rat Portage, far to the east. [C13]

[VISUAL: Rat Portage COUNTERFACTUAL on V3/V5 - a dashed line drops south from Rat Portage and crosses a dotted line labeled "fur-trade canoe route (schematic)"; the dashed line flashes red and is struck out. Caption: "per historian Francis Carroll, Canada's History". Canoe route drawn schematically - its real course is not in the ledger.]
VO: Picture the border dropping south from there instead. [NC]
VO: According to historian Francis Carroll, a line south from Rat Portage would have put a key fur-trade canoe route on the American side, and the Hudson's Bay Company objected. [C14]

[VISUAL: V3 - the red line vanishes; the camera snaps west to a finger of water on the lake's western side. Label: "Angle Inlet". Title card: "1825 - Johann Ludwig Tiarks".]
VO: So in 1825, an astronomer named Johann Ludwig Tiarks re-surveyed the candidates. [C14]
VO: He settled on a finger of water now called Angle Inlet. [C14]

[VISUAL: V5 - PAYOFF animation. Pin on Angle Inlet; the 49th parallel below it; the 1818 rule replays: the boundary drops due south from the pin to the parallel, then runs west. The land caught between the drop, the parallel and the boundary through the lake fills in - the chimney appears on the Minnesota map. Hold.]
VO: Now watch what the 1818 rule does with it. [NC]
VO: That point sits north of the 49th parallel, so the border drops due south from it to the parallel. [C11] [C15]
VO: The land caught between that line, the parallel and the boundary through the lake stays American. [C11] [C15]
[PAUSE 1 s]
VO: That's the Angle. [NC]
[PAUSE 2 s - hold on the finished chimney]

## THE LINE PEOPLE LIVE WITH (4:51-5:43)
[VISUAL: V5 - the chimney pulses, then the "year-round" highlight from the drive section returns for a beat and fades.]
VO: So that's the mystery of the road, solved. [NC]
VO: But remember that word from the drive? [NC]
VO: Year-round. [NC]
VO: We'll get there. [NC]
VO: First, it's worth seeing what this line means for the people who live with it. [NC]

[VISUAL: V5 - the due-south boundary line highlights and pulses; small title card "Manitoba, 1871". No document image.]
VO: As early as 1871, Manitoba's lieutenant governor was calling that due-south line inconvenient and suggesting it be fixed. [C44]
VO: Nothing came of it. [C44]

[VISUAL: V5 - Angle Township outline from TIGER. Counter animates to "149 residents - 2020 Census". Then the Red Lake Reservation boundary from TIGER AIANNH overlays the Angle; label "≈ two-thirds of township land - Red Lake Reservation (2020 Census boundaries)".]
VO: At the 2020 Census, about 150 people lived in Angle Township. [C21]
VO: About two-thirds of Angle Township's land lies within the Red Lake Reservation, by 2020 Census boundaries. [C35]

[VISUAL: Text card over V3 Landsat (no TIME photos): "In 2019, TIME called Angle Inlet School the last one-room public school in Minnesota." Source line: TIME, March 14, 2019.]
VO: In 2019, TIME called Angle Inlet School the last one-room public school in Minnesota. [C36]

[VISUAL: V8 - the Manitoba route pulses; a simple closed-gate icon drops over the border crossing, labeled "pandemic border closures" - no dates.]
VO: And during the pandemic, border closures made the trip through Canada very hard for people at the Angle. [C39]
VO: Which raises the obvious question. [NC]
VO: Is there really no other way in? [NC]
[PAUSE 1 s]

## THE SECOND PAYOFF (5:43-6:14)
[VISUAL: V5 - lake in open-water blue; a dotted boat-route arrow crosses from the Minnesota mainland to the Angle without touching Canada. Label: "open-water season".]
VO: There is. [C34]
VO: In the open-water season, boats cross Lake of the Woods from the Minnesota mainland to the Angle. [C34]
VO: But this is where "year-round" matters. [NC]
VO: Because when the lake freezes, the way in can change. [C33]

[VISUAL: SEASON FLIP - V3 open-water Landsat wipes to the V7 Landsat winter scene of the frozen lake. A schematic dashed arrow crosses the ice, labeled "seasonal ice road - schematic, route not shown to scale". No dates, no operator, no fee.]
[PAUSE 1 s]
VO: In winter, when the ice is thick enough, a guest ice road - about 22 miles over the frozen lake - can let you reach the Angle without leaving Minnesota. [C33]
VO: No border crossing. [C33]
VO: It all depends on the ice. [C33]
[PAUSE 1 s]

## CLOSE (6:14-6:46)
[VISUAL: Split screen - left: the V8 route through Manitoba glowing; right: V1 Mitchell map. The red "due west" line from V9 slides across both and fades.]
VO: So think back to that drive through Manitoba. [NC]
VO: It's the end of a line that was drawn on a 1755 map, and told to run due west to a river that never came that far north. [C3] [C4] [C7]
[PAUSE 1 s]
VO: And it left a piece of the United States you can only reach by road, all year, by leaving it. [C11] [C27]
[PAUSE 1.5 s]

[VISUAL: V5 - final wide shot of Minnesota, the chimney highlighted. End screen.]
VO: If borders like this are your thing, subscribe. [NC]
VO: There are plenty more where this came from. [NC]

---
Spoken words: 975  |  Marked pauses: 16 s  |  Runtime estimate: 975 / 150 wpm + pauses = about 6:46

Runtime note: V2 is shorter than the 8:00-8:20 target. The audit's cuts removed about 370 words of
repetition and secondary history; reaching 8:00 would need about 200 more words, which means either
filler lines or restoring cut history (C16-C19, C43), both ruled out for this pass. Creator's call.

Claims used (24): C1, C2, C3, C4, C7, C10, C11, C13, C14, C15, C21, C23, C24, C25, C26, C27, C28,
C30, C33, C34, C35, C36, C39, C44. C20 appears on screen only, in its Final wording.
Cut from V1 by the approved audit: C8, C12, C16, C17, C18, C19, C22, C43 (still VERIFIED/SOFTENED, unused).
Not used (UNVERIFIED/CONFLICT): C5, C6, C9, C29, C31, C32, C37, C38, C40, C41, C42.
