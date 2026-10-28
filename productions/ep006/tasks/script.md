# Task: write script.md (AGENT_REQUIRED)

Target: 882-1323 spoken words (6-9 minutes at 2.45 words/s). Verified-fact capacity: about 825 words.
If capacity is below the target, write the honest shorter script and say so; padding and repetition fail validation.

## Style
- American English, spoken, second person plural 'we' for the investigation
- hook in the first 45 words: a concrete contrast, no throat-clearing
- one idea per sentence; no filler transitions; never repeat a fact to fill time
- keep PROMISED / REPORTED / OBSERVED apart in every chapter
- media/org claims contain their wording word (reported/said); hypotheses are hedged; limitations end with {L}
- no 'proves', 'reveals', 'collapsed', 'cancelled', 'built' unless a claim explicitly allows it
- explain US-specific references in a few words

## Chapters (headings must match exactly: `## id: Title`)
- `## hook: The first fifteen seconds` - claims: C13
- `## plan: What has been reported` - claims: C10, C11, C1, C2, C3, C4, C5, C6
- `## method: How we looked` - claims: C7, C8, C9
- `## obs: Obs` - claims: C13, C14, C15, C16
- `## limits: What we cannot say` - claims: (none; narrative/limits only)
- `## close: What to watch` - claims: (none; narrative/limits only)

## Claims you may use
- C1 [org/high] USGS says a rapid slope failure involving a glacier struck Langtang National Park in Nepal, near the China border, on the morning of 26 August 2026. (word: 'said')
- C2 [org/high] USGS says the debris flow and flood travelled approximately 100 kilometers (about 62 miles) along the Lende Khola and Trishuli Khola, and impacted populated areas downstream, including the Rasuwagadhi border post. (word: 'said')
- C3 [org/high] USGS says the slope failure generated seismic energy equivalent to a magnitude 5.2 earthquake, and a second event about three hours later was equivalent to magnitude 4.2; the signals were produced by the failure itself. (word: 'said')
- C4 [org/high] USGS has not determined whether the initial failure was a landslide that incorporated part of a glacier or a collapse of the glacier itself, and all information is preliminary. (word: 'said')
- C5 [org/high] USGS notes the same mountain produced a large debris avalanche in 2015, caused by the magnitude 7.8 Gorkha earthquake, which fell nearly 1,900 meters, buried a village and killed more than 200 people. (word: 'said')
- C6 [org/high] USGS is mapping the extent of the flood and debris by comparing satellite images from before and after the event. (word: 'said')
- C7 [science/medium] ICIMOD's preliminary analysis (13 October 2026) concludes the disaster was not a conventional glacial lake outburst flood: a bedrock failure sheared away part of an overlying glacier. (word: 'said')
- C8 [science/medium] ICIMOD reports that Sentinel-1 radar detected up to 40 centimeters of ground deformation along the satellite's line of sight between 7 July and 24 August 2026, two days before the collapse. (word: 'said')
- C9 [science/medium] Early estimates of the volume differ: ICIMOD's preliminary figure is about 132 million cubic meters of rock and ice, while a separate preprint suggests a much smaller order of magnitude. (word: 'said')
- C10 [media/medium] By mid-October 2026 Nepali figures put the confirmed death toll in Nepal above 1,400 people, with roughly five thousand still listed as missing; the lists keep changing as names are verified. (word: 'reported')
- C11 [media/medium] China counts casualties on its side of the border separately: Xinhua reported 43 dead and 519 missing at Gyirong Port as of 5 September, and it was not clear whether some people appear in both countries' counts. (word: 'reported')
- C13 [observation/medium] In a Landsat 9 image taken on 26 August 2026, a dark grey-brown swath follows the valley and river corridor below the glacier; the clear 12 August 2026 Sentinel-2 image of the same valley shows only a narrow pale river bed there.
- C14 [observation/medium] On our 10 m grid the dark swath can be followed for about 30 kilometers in the 26 August 2026 Landsat 9 image, about 20 kilometers of it before the river turns south near the Rasuwagadhi border post; clouds hide other stretches, so this is a lower bound inside our frame.
- C15 [observation/high] Optical satellites need clear sky: Sentinel-2 passes over this valley between 14 and 27 August 2026 had 39 to 97 percent scene cloud cover, and the clearest view before the event is from 12 August, with 19 percent scene cloud.
- C16 [observation/high] The Sentinel-2 frames in this video have 10 meter pixels; the Landsat 9 frame has 30 meter pixels, shown on the same grid by nearest-neighbor resampling, which adds no detail.

## Do NOT use (low confidence)
C12

When done run: `python3 .claude/skills/yt-script-agent/scriptagent.py validate --root productions/<slug>`
