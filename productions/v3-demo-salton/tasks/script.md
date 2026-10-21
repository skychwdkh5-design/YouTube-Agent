# Task: write script.md (AGENT_REQUIRED)

Target: 882-1323 spoken words (6-9 minutes at 2.45 words/s). Verified-fact capacity: about 165 words.
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
- `## hook: The first fifteen seconds` - claims: C5
- `## plan: What has been reported` - claims: C1
- `## method: How we looked` - claims: C6
- `## shows: What the satellites show` - claims: C5
- `## limits: What we cannot say` - claims: (none; narrative/limits only)
- `## close: What to watch` - claims: (none; narrative/limits only)

## Claims you may use
- C1 [org/medium] The Salton Sea is shrinking mainly because less Colorado River water reaches it since the 2003 water transfers, according to a UC Riverside-led task force report, the Congressional Research Service and the Water Education Foundation. (word: 'according to')
- C5 [observation/medium] In a window over the southern shore, the number of water-like pixels fell from 42,022 in October 2022 to 33,784 in October 2026, about 20 percent fewer; the counts for 2024 and 2025 are 38,436 and 37,550.
- C6 [observation/high] Four Sentinel-2 scenes, all from the same orbit, taken between October 3 and October 31 in 2022, 2024, 2025 and 2026.

## Do NOT use (low confidence)
C2, C3, C4

When done run: `python3 .claude/skills/yt-script-agent/scriptagent.py validate --root productions/<slug>`
