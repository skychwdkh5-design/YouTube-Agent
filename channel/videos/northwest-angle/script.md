# Script: Why Does This Part of the U.S. Belong to Minnesota? (working)

- Format: main long-form
- Target: 8-10 min at 150 wpm (voice.md planning default)
- Winning hook formula: The Only Way In (hookscore --profile geo: 76 STRONG) - the road through Canada is the anomaly the viewer can see on the map in the first three seconds
- Structure: B "Follow the Drive", with A's historical midpoint (approved 2026-10-06)
- Gate 2: PASS, 2026-10-06 (`claims.py --claims claims.md --script script.md`, 101 sentences, 0 fails)

Conventions:
- `VO:` lines are the narration - the only lines the AI voice reads and the only lines `claims.py` checks.
- `[VISUAL: ...]` says what is on screen while the line is read. Asset IDs (V1-V11) are from `visuals.md`.
- `[C#]` after a factual sentence links it to the ledger. `[NC]` = reviewed, not a factual claim.
- SOFTENED claims (C8, C13, C19, C20, C25, C30, C33, C35, C36, C39) use their Final wording or something more cautious.

## HOOK (0:00-0:15)
[VISUAL: V5 - contiguous U.S. outline from TIGER, slow push-in on Minnesota's northern edge; the "chimney" pulses once. Small label: "Northwest Angle".]
VO: You see that bump on top of Minnesota? [NC]
VO: It's American, but the only year-round road to it runs through about 40 miles of Canada. [C27] [C28]
VO: Why? [NC]

## TURN (0:15-0:40)
[VISUAL: V8 + V5 - the road route draws itself from Warroad up through Manitoba and back into the Angle, then freezes. Cut to V1 - the Mitchell map, full sheet, no annotations.]
VO: To answer that, we're going to make the drive. [NC]
VO: Then we're going back to a map from 1755. [C4]
VO: Because the story of this road starts on that map. [C3]

## BEAT 1 - The place that shouldn't be there (0:40-1:35)
[VISUAL: V5 - Minnesota counties fade in; Lake of the Woods County highlights, then Angle Township. Shade only the part north of 49°N as "the Angle". On-screen label: "Angle Township, Lake of the Woods County, MN".]
VO: This is the Northwest Angle. [NC]
VO: The Northwest Angle is part of Angle Township, in Lake of the Woods County, Minnesota. [C20]

[VISUAL: V5 - pin at 49°23'04"N, 95°09'12"W in the lake. Label: "Northernmost point of the Lower 48 - a boundary point in the water". Draw the 49th parallel as a dashed line; a measuring bracket from the pin down to the line reads "about 27 mi".]
VO: Its tip is the northernmost point of the Lower 48. [C23]
VO: And that tip isn't on land - it's a boundary point out in the water of Lake of the Woods. [C24]
VO: It sits about 27 miles north of the 49th parallel. [C26]
VO: Angle Township, which also takes in part of the lake to the south, covers about 125 square miles of land - about 600 counting the water. [C22]

[VISUAL: V3 - NASA Earth Observatory Landsat view "An Unusual Angle". Then V5 - sweep along 49°N from the boundary line east across the lake; every sample along the line is blue water. Caption: "Minnesota side along the 49th: all water (U.S. Census TIGER/Line)".]
VO: Now look at the gap between the Angle and the rest of Minnesota. [NC]
VO: On the American side, it's all lake. [C27]
VO: No year-round road crosses it. [C27]
VO: So if you want to drive there, you need a different plan. [NC]

## BEAT 2 - The drive (1:35-2:55)
[VISUAL: V8 - road animation on OpenStreetMap data. A small car icon starts at Warroad on the Minnesota shore. Highway shield "313" appears.]
VO: Start in Warroad, Minnesota. [NC]
VO: Head north on Highway 313, and it carries you straight into Manitoba. [C27]

[VISUAL: V8 - a border line flashes as the icon crosses; the map tint shifts from U.S. to Canada. Shield "308" appears.]
VO: Now you're in Canada. [NC]
VO: You follow Provincial Road 308 north. [C27]
VO: You're heading into Canada to reach Minnesota. [NC]

[VISUAL: V8 - shield "525"; the route turns east and the icon crosses the boundary line back into the Angle. A running counter in the corner ticks up to "≈40 mi in Canada".]
VO: Then Provincial Road 525 turns east and takes you back into Minnesota. [C27]
VO: Add it up, and you've spent about 40 miles of Canada just to get back to your own country. [C28]
VO: To drive from one part of Minnesota to another, you cross an international border twice. [C27]
VO: There's no turn you can take that keeps you inside the country. [C27]

[VISUAL: Simple motion graphic, no photos - a booth icon with a video-phone symbol and a phone icon with an app screen. Label: "Remote check-in". Map pin on Jim's Corner from V5.]
VO: And when you arrive, there's no staffed border post waiting. [C30]
VO: You check in remotely, at a video-phone booth like the one at Jim's Corner, or with an app. [C30]

[VISUAL: V8 + V5 - zoom out until the whole route, Warroad to the Angle, fits the frame. The route glows.]
VO: That's it. [NC]
VO: The only year-round road to the Angle runs through Manitoba. [C27]

## BEAT 3 - The question flips (2:55-3:40)
[VISUAL: V6 - Natural Earth continental map. The U.S.-Canada border runs along the 49th parallel from the Rockies east across the plains; at Lake of the Woods it suddenly jogs north. Freeze on the jog.]
VO: So why would a border do this? [NC]
VO: West of here, the line between the U.S. and Canada follows the 49th parallel across the plains. [C11]
VO: Then, at this one lake, it jumps north. [C26]
VO: The Angle is the only sizable piece of the Lower 48 north of the 49th parallel. [C25]

[VISUAL: V6 - camera pulls back in time: the modern map desaturates into parchment texture and cross-dissolves into V1.]
VO: You'll often hear it called a mapping mistake. [NC]
VO: That's close. [NC]
VO: But the real story is stranger, and it starts with a map. [NC]

## BEAT 4 - The map (3:40-4:30)
[VISUAL: V1 - John Mitchell, "A Map of the British and French Dominions in North America", Library of Congress. Slow pan across the full map. Title card: "John Mitchell, 1755". No arrows or labels on the lake or the river.]
VO: Meet John Mitchell's map of North America, first published in 1755. [C4]
VO: When American and British diplomats sat down in Paris in 1782 to make peace, this was the map they drew the new borders on. [C3]

[VISUAL: On-screen quote over V2 (second LoC copy, close-up on the cartouche): "Upon that map, and that only, were those boundaries delineated." - John Adams, 1796.]
VO: John Adams later wrote that the boundaries were drawn on that map, and that map only. [C3]
VO: Benjamin Franklin remembered it the same way: the map they traced the boundary on was the one Mitchell had published more than twenty years before. [C3]
VO: So this wasn't a rough sketch. [NC]
VO: It was the map both sides actually used to draw the new country's borders. [C3]

[VISUAL: V2 - slow drift west across the interior of the map. Overlay text only: "Badly inaccurate in the far west".]
VO: And here's the problem. [NC]
VO: It was a map that was badly wrong about the far west. [C3]
VO: And the far west is exactly where the border had to end. [NC]

## BEAT 5 - The impossible instruction (4:30-5:40)
[VISUAL: V6 base map. Typeset title: "Treaty of Paris - September 3, 1783". The boundary draws itself west through the Great Lakes to Lake of the Woods.]
VO: The Treaty of Paris was signed on September 3, 1783. [C1]
VO: It ran the border west to Lake of the Woods, and through the lake to "the most northwestern point thereof." [C2]
VO: Then it says: "on a due west course to the river Mississippi." [C2]

[VISUAL: V9 - from the lake's northwest corner a red line shoots due west along latitude 49°23'N. The real Mississippi, from TIGER data, lights up far to the south. The red line keeps going and never touches it. Label: "due west → never meets the river".]
VO: On paper, that sounds precise. [NC]
VO: Find the corner, draw a line due west, meet the river. [NC]
VO: Here's the catch. [NC]
VO: The Mississippi never comes that far north. [C7]
VO: Its northernmost reach stays roughly two degrees of latitude south of that corner of the lake. [C7]
VO: A line due west from the lake passes north of the river and never touches it. [C7]

[VISUAL: Typeset quote card: "uncertain whether the River Mississippi extends so far to the Northward" - Jay Treaty, Art. 4, 1794. Text from the Avalon Project.]
VO: By 1794, the doubt was in writing. [C10]
VO: A new treaty admitted it was "uncertain whether the River Mississippi extends so far to the Northward" - and planned a survey to find out. [C10]

[VISUAL: V9 - a small marker drops onto the river's headwaters region, well south of the lake. Label: "1798 - David Thompson".]
VO: In 1798, the fur-trade surveyor David Thompson showed that the Mississippi's headwaters lie south of Lake of the Woods. [C8]
VO: The 1783 line was impossible. [C7]
VO: The border needed a new rule. [NC]

## BEAT 6 - The 1818 rule (5:40-6:30)
[VISUAL: V6 + V10 - the 49th parallel draws itself west from Lake of the Woods toward the Rockies. On-screen quote from the Convention of 1818, Art. 2: "...due North or South as the Case may be, until the said Line shall intersect the said Parallel..."]
VO: That rule came in 1818. [C11]
VO: The two countries picked a line of latitude instead: the 49th parallel, running west to what the treaty calls the Stony Mountains. [C11]
VO: But they kept the one reference point they already had - the lake's most northwestern point. [C11]
VO: From that point, run a line due north or south until it hits the 49th parallel. [C11]
VO: Then turn west. [C11]

[VISUAL: V10 - the words "as the Case may be" highlight. A question mark hovers over the lake.]
VO: The treaty even adds "as the case may be." [C11]
VO: In other words, the treaty left room for either direction. [C11]
VO: Commissioners were already under orders to find that point and record its latitude and longitude. [C12]

## BEAT 7 - Finding the point (6:30-7:35)
[VISUAL: V5 + V3 - Lake of the Woods from Landsat; candidate markers pop up one by one. The first, far to the east at Rat Portage, labeled "Rat Portage - today's Kenora". A line drops south from it toward the parallel.]
VO: Finding it turned into a surveying puzzle. [NC]
VO: In the 1820s, the British boundary surveyor David Thompson put forward several possible "northwestern points" - the first of them at Rat Portage, far to the east. [C13]

[VISUAL: The dropped line from Rat Portage crosses a dotted "fur-trade canoe route" line and flashes red. Caption: "per historian Francis Carroll, Canada's History".]
VO: According to historian Francis Carroll, a line south from Rat Portage would have put a key fur-trade canoe route on the American side, and the Hudson's Bay Company objected. [C14]

[VISUAL: V3 - zoom into a narrow inlet on the lake's western side. Label: "Angle Inlet". Title card: "1825 - Johann Ludwig Tiarks".]
VO: So in 1825, an astronomer named Johann Ludwig Tiarks re-surveyed the candidates. [C14]
VO: He settled on a finger of water now called Angle Inlet. [C14]

[VISUAL: V5 - payoff animation. Pin on Angle Inlet; the 49th parallel below it; the boundary drops due south from the pin to the parallel, then runs west. The land caught between the drop, the parallel and the lake fills in - the chimney appears on the Minnesota map.]
VO: Now watch what the 1818 rule does with it. [NC]
VO: That point sits north of the 49th parallel, so the border drops due south from it to the parallel - about 27 miles. [C15] [C26]
VO: The land caught between that line, the parallel and the boundary through the lake stays American. [C11] [C15]
VO: That's the Angle. [NC]
VO: The Webster-Ashburton Treaty of 1842 locked it in. [C15]
VO: It even pinned the point down with coordinates: 49 degrees, 23 minutes north. [C16]

[VISUAL: V5 - the drop line gets a "1872-1876 survey" tag and small monument icons along it. On-screen: 1842 treaty coordinates "49°23'55\"N, 95°14'38\"W" shown briefly beside the pin, then the 1873 report quote typeset over the line.]
VO: In the 1870s, a joint commission surveyed this stretch of the border and marked it with monuments. [C17]
VO: The American report put it plainly: from that point, the boundary "follows a meridian south twenty-seven miles to the 49th parallel." [C26]

## BEAT 8 - The leftovers (7:35-8:10)
[VISUAL: V11 over V5 - quote card from the 1925 treaty, Art. I. Schematic only: two tiny blue pockets labeled "U.S. water - 2.5 acres total" inside Canadian water, marked "schematic".]
VO: Even then, it wasn't tidy. [NC]
VO: As early as 1871, Manitoba's lieutenant governor was calling that due-south line inconvenient and suggesting it be fixed. [C44]
VO: Nothing came of it. [C44]
VO: In 1908, the two countries agreed to re-survey and fully mark the boundary, all the way to the northwesternmost point of Lake of the Woods. [C18]
VO: Those surveys found the boundary lines crossing in the lake, leaving two tiny pockets of U.S. water, two and a half acres in all, completely surrounded by Canadian water. [C43]
VO: In 1925 a new treaty swapped the old northwestern point for a nearby point just south of it, and redefined the line along the 49th as straight lines between boundary markers. [C19]

## BEAT 9 - Living with the line (8:10-8:55)
[VISUAL: V5 - Angle Township outline. Counter animates to "149 residents - 2020 Census". Then the Red Lake Reservation boundary from Census TIGER overlays the Angle; label: "≈ two-thirds of township land - Red Lake Reservation (2020 Census boundaries)".]
VO: So what's it like to live with this border? [NC]
VO: About 150 people lived in Angle Township at the 2020 Census. [C21]
VO: About two-thirds of Angle Township's land lies within the Red Lake Reservation, by 2020 Census boundaries. [C35]

[VISUAL: V8 - the Manitoba route pulses again. Then a simple closed-gate icon over the border crossing, labeled "pandemic border closures" - no dates.]
VO: For most of the year, every drive in or out means that run through Canada. [C27] [C33]
VO: During the pandemic, border closures made the trip through Canada very hard for people at the Angle. [C39]

[VISUAL: Text card over V3: "In 2019, TIME called Angle Inlet School the last one-room public school in Minnesota." Source line: TIME, March 14, 2019. No TIME photos.]
VO: In 2019, TIME called Angle Inlet School the last one-room public school in Minnesota. [C36]

## BEAT 10 - The twist on the ice (8:55-9:30)
[VISUAL: V5 - lake in open-water blue; a dotted boat-route arrow crosses from the Minnesota mainland to the Angle without touching Canada. Label: "open-water season".]
VO: There is a way around Canada. [C34]
VO: In the open-water season, boats cross Lake of the Woods from the Minnesota mainland to the Angle. [C34]

[VISUAL: V7 - Landsat winter scene of the frozen lake. A schematic dashed arrow across the ice, labeled "seasonal ice road - schematic, route not shown to scale". No dates, no operator, no fee.]
VO: And in winter, when the ice is thick enough, a guest ice road - about 22 miles over the frozen lake - can let you reach the Angle without leaving Minnesota. [C33]
VO: It all depends on the ice. [C33]
VO: The road through Manitoba is still the only one that works all year. [C27]

## PAYOFF / CLOSE (9:30-10:00)
[VISUAL: Split screen - left: V8 route through Manitoba glowing; right: V1 Mitchell map. A red "due west" line from V9 slides across both and fades.]
VO: So think back to that drive through Manitoba. [NC]
VO: It's the end of a line that was drawn on a 1755 map, and told to run due west to a river that never came that far north. [C3] [C4] [C7]
VO: The map was wrong, and the instruction couldn't work. [C3] [C7]
VO: The fix left a piece of the United States you can only reach by road, all year, by leaving it. [C11] [C27]

[VISUAL: V5 - final wide shot of Minnesota, the chimney highlighted. End screen.]
VO: If borders like this are your thing, subscribe. [NC]
VO: There are plenty more where this came from. [NC]

---
Spoken words: 1,303  |  Runtime estimate: 1,303 / 150 = about 8 min 41 s

Claims used (33): C1, C2, C3, C4, C7, C8, C10, C11, C12, C13, C14, C15, C16, C17, C18, C19, C20, C21, C22, C23, C24, C25, C26, C27, C28, C30, C33, C34, C35, C36, C39, C43, C44.
Not used (UNVERIFIED/CONFLICT): C5, C6, C9, C29, C31, C32, C37, C38, C40, C41, C42.
