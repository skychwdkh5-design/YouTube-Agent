# Task: write script.md (AGENT_REQUIRED)

Target: 882-1323 spoken words (6-9 minutes at 2.45 words/s). Verified-fact capacity: about 770 words.
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
- `## hook: The first fifteen seconds` - claims: C1, C9
- `## promise: The promise` - claims: C1
- `## plan: What has been reported` - claims: C2, C3, C4
- `## method: How we looked` - claims: C15, C16
- `## shows: What the satellites show` - claims: C9, C17, C19
- `## segment: The dark segment` - claims: C10, C11
- `## checks: How we tried to break it` - claims: C12, C13, C14
- `## limits: What we cannot say` - claims: C18
- `## close: What to watch` - claims: (none; narrative/limits only)

## Claims you may use
- C1 [original/medium] The Line was announced as a 170 km linear city.
- C2 [media/medium] Bloomberg reported (Apr 2024) only about 2.4 km of The Line expected by 2030 and fewer than 300,000 residents. (word: 'reported')
- C3 [media/medium] Semafor reported (22 May 2026) that NEOM halted work on The Line until at least after 2030, citing unnamed sources. (word: 'reported')
- C4 [media/medium] Reuters reported (about 4 Oct 2026, two sources) that the NEOM stadium was shelved indefinitely, with no official announcement. (word: 'reported')
- C9 [observation/high] A straight, narrow cleared corridor crosses the area, at least 21.9 km long inside our 10 m frame: absent in 2020-21, faint in 2022, clear from 2023.
- C10 [observation/high] A dark segment about 1.6 km long is absent in Oct 2022 and 2023 and present in Oct 2024, 2025 and 2026.
- C11 [observation/medium] In 2024, 2025 and 2026 the dark segment is water-like in near-infrared (NDWI above zero, very low near-infrared); in 2022 and 2023 no pixel qualifies.
- C12 [observation/medium] Measured at 10 m, the segment is about 1.6 km long in Oct 2025 and about 1.9 km in Oct 2026; we cannot tell growth from water level or a threshold effect.
- C13 [observation/medium] Landsat 8 at 30 m independently shows the same segment: about 0.7 km in Oct 2024 and about 1.65 km in Oct 2025 and Sep 2026.
- C14 [observation/medium] The segment appears on three different dates and on three different Sentinel-2 satellites (2A, 2B and 2C) in 2024, 2025 and 2026.
- C15 [observation/high] Each pixel in our Sentinel-2 frames covers 10 meters of ground.
- C16 [observation/high] Seven Sentinel-2 scenes, all from the same orbit, taken in late September or October of each year from 2020 to 2026.
- C18 [hypothesis/low] The dark segment may be standing water in a long, narrow excavation.
- C17 [observation/medium] A settlement-like complex at the western end of our frame grows from a small compound in 2020 to a large planned street grid by 2024; what it is is unknown.
- C19 [observation/medium] A second settlement-like complex at the eastern end of our frame grows from sparse tracks in 2020 to a planned street grid with buildings by 2024; what it is is unknown.

## Do NOT use (low confidence)
C5, C6, C7, C8

When done run: `python3 .claude/skills/yt-script-agent/scriptagent.py validate --root productions/<slug>`
