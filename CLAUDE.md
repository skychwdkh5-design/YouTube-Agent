# YouTube-Agent - geography channel workspace

A Claude Code workspace for a **faceless, AI-narrated geography / geo-entertainment channel** made
for a **U.S. audience** in **native American English**. Topics come from anywhere in the world; the
U.S. is the audience market, not a topic filter.

## Read first, every session

1. `channel/channel.md` - positioning, audience, topic-selection order, pillars, weekly cadence.
2. `channel/voice.md` - the AI narrator: American English, writing for TTS, pronunciation.
3. `channel/editorial.md` - accuracy, claim words, disputed territories, AI use and disclosure.
4. `channel/research.md` - source tiers, the claims ledger, the two fact-check gates.
5. `channel/visual-style.md` - maps, pacing, licenses, AI visuals, thumbnails, Shorts framing.

## Hard rules

- **Nothing is published automatically.** Skills write drafts; the creator publishes. No skill
  uploads, posts, replies, schedules or changes anything on YouTube.
- **No YouTube API / OAuth** is connected. Analytics come from Studio exports in `channel/data/`.
- **Never invent a number, a result or a source.** Unknowns are asked for or marked `[NEEDED]`.
- **No script line ships without a verified claim behind it** (`geo-factcheck`, `claims.py`).
- **No asset ships without a source and a usable license** (`geo-visuals`, `assets.py`).

## The pipeline - one video

| # | Step | Skill | Output in `channel/videos/<slug>/` | Check |
|---|---|---|---|---|
| 1 | Topic discovery | `/geo-topics` | row in `channel/ideas.md` | `topicscore.py` |
| 2 | Competitor / outlier analysis | `/yt-viral` (`--profile geo`) | Evidence for the idea | `swipe.py` |
| 3 | Research | `/geo-research` | `brief.md`, draft `claims.md` | - |
| 4 | Fact verification - GATE 1 | `/geo-factcheck` | verified `claims.md` | `claims.py --claims` |
| 5 | Hooks | `/yt-script` | 5 hooks, top 2 scored | `hookscore.py --profile geo` |
| 6 | Script | `/yt-script` | `script.md` with `VO:`, `[MAP]`, `[C#]` | - |
| 7 | Script fact-check - GATE 2 | `/geo-factcheck` | gate result | `claims.py --claims --script` |
| 8 | Visual plan | `/geo-visuals` | `visuals.md`, credits | `assets.py` |
| 9 | Voice-over + edit | creator; `/yt-edit` for TTS gaps | - | `deadair.py` |
| 10 | Title / thumbnail | `/yt-package` | `package.md` | `title.py --profile geo` |
| 11 | SEO + chapters | `/yt-seo`, `/yt-chapters` | `seo.md` | `chapters.py` |
| 12 | Shorts extraction | `/yt-shorts` | `shorts.md` | `hookscore.py --profile geo`, Gate 2 for new lines |
| 13 | Publish | **the creator** | - | - |
| 14 | Post-publication analysis | `/yt-retention`, `/yt-comment`, monthly `/yt-audit` | `post.md`, new ideas, corrections | `retention.py` |
| - | Weekly planning | `/yt-plan` | the week's table | - |

Steps 8-12 do not start until Gate 2 passes. Anything changed after Gate 2 goes back through it.

## Weekly cadence (target)

1 main long-form (8-12 min) + 1 lower-production long-form (4-6 min) + 3-5 Shorts.
If the week breaks: drop the lower-production video, then standalone Shorts. Never the fact-check.

## Where things live

```
channel/            profile, rules, idea backlog, templates, per-video folders, data exports
.claude/skills/     11 yt-* skills (general YouTube) + 4 geo-* skills (this channel)
tests/              python3 -m unittest discover -s tests   (run after changing any tool)
```

## Tools and their geography mode

`--profile geo` is opt-in. Without it every original tool behaves exactly as before.

- `yt-script/hookscore.py --profile geo` - ANOMALY replaces STAKES; `hooks-geo.json` formulas join the 21.
- `yt-package/title.py --profile geo` - places in `places.txt` count as names; U.S./D.C. are not shouting.
- `yt-viral/swipe.py --profile geo` - classifies titles against the geography formulas too.
- `geo-factcheck/claims.py` - fact-check gate (ledger, then script vs ledger).
- `geo-visuals/assets.py` - license and AI-disclosure gate, credits block.
- `geo-topics/topicscore.py` - weighted topic ranking with verification as a hard gate.
