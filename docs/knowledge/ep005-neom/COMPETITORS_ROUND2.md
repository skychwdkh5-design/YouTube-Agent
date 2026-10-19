# EP005 - competitor analysis, round 2 (2026-10-19)

Data: public YouTube search/browse JSON, no login (`data/neom_videos_all.json`, 59 NEOM/The Line videos >= 20K views; scripts in `scripts/`).
"Median" = median views of the channel's ~10-30 most recent uploads (rounded by YouTube). "x median" = views / that median. Age is relative ("1y ago"); exact dates were not retrievable.
**Survivorship warning:** the list is what search surfaced, so it over-represents hits. It shows that views are achievable, not how often.

## Small and medium English-language channels (<= ~350K subscribers)
| Video | Views | Age | Len | Channel (subs) | x median | Views / sub |
|---|---|---|---|---|---|---|
| Saudi Just Cancelled NEOM's The Line - Inside the $8.8T Autopsy (bOG4qCx0peA) | 798K | 11mo | 42:00 | Gigaprojects (28.3K) | 4.1 | 28 |
| NEOM: The world's dumbest megaproject (6XNK55tc3x8) | 1.29M | 2y | 13:28 | If You're Listening (33.1K) | 2.2 | 39 |
| The Brutal Collapse of the World's Largest Megaproject (q__g6Zy39eo) | 494K | 2w | 25:16 | Luxified (29.3K) | 134 | 17 |
| This Is What The Line Megacity Looks Like In 2025! (4JI5I4NjV-U) | 545K | 1y | 11:24 | Billion Dollar Builds (143K) | 30 | 3.8 |
| End of the Line - The Greatest Mega Disaster in History (ZsyH-q8WF18) | 230K | 6mo | 39:50 | SIGNUM (25.9K) | 6.1 | 8.9 |
| The (Overdue) Collapse of Saudi Megaprojects (D3fi5dfqhMc) | 355K | 7d | 22:11 | The Invisible Hand (296K) | 2.1 | 1.2 |
| Inside Saudi's NEOM Crisis (S_1xHFr6kHo) | 273K | 10mo | 11:32 | Uptin (274K) | 3.2 | 1.0 |
| NEOM Lied About The Line (Moz1sK9ZPTQ) | 269K | 1y | 27:41 | Gigaprojects (28.3K) | 1.4 | 9.5 |
| Every FAILED Megacity Project Explained in 9 Minutes (kSGUaukWTTU) | 177K | 1y | 9:02 | Urban Planner Explained (58.4K) | 16 | 3.0 |
| The Line in 2026: What Is Really Happening? (jN45x-nivWI) | 83K | 11mo | 11:04 | BIGGER THE BETTER (5.97K) | 96 | 14 |
| The Line in 2026: What Have They Built So Far? (3KfHJy7rztw) | 41.5K | 5mo | 6:05 | Arkive (61K) | 0.3 | 0.7 |
Links: `https://www.youtube.com/watch?v=<id>`.

## What it shows
1. **Attention is live right now, including for small channels:** Luxified (29K subs) reached 494K in two weeks, The Invisible Hand 355K in a week. That follows the WSJ video (12.2M, ~1 month ago) and the Reuters stadium report (Oct 2026).
2. **Every small-channel hit is a long "collapse/disaster/autopsy" narrative (9-42 min).** None is a satellite-evidence video. Small-channel satellite videos found in round 1 got from tens of views to 41K (Orbis Info 24, Think Money 44, Tallest Order 264, Megaprojects Uncovered 4.5K, BIGGER THE BETTER 27K, Arkive 41K).
3. **The only big satellite-evidence video is Business Insider "Satellite Images Reveal..." (5.0M, 1y, 22:03, a 10.6M-sub channel).** Its thumbnail format (BEFORE / AFTER split of real satellite imagery, "VIEW FROM ABOVE") is the proof of format, not of our reach. BI's reach is not evidence that OrbitalAtlas gets a similar result.
4. The topic is crowded: at least five near-identical "How Saudi Arabia Was Building NEOM's The Line and Why It Collapsed" uploads exist (round 1).
5. Our edge is not the topic but the **evidence**: Sentinel-2 frames nobody in this list shows (water-like segment, same-orbit 2020-2026 series, measured, with the limits stated).

## Thumbnails (16 reviewed visually, contact sheet not stored - third-party artwork)
Common: AI/CGI renders of a mirrored wall; the crown prince's face with "GAME OVER", "FIRED", "NOT REAL"; red words FAILED / DISASTER; a host face with an alarmed expression; money figures ($200B, $500B). Real satellite imagery appears in only two: BI (before/after) and one aerial-photo thumbnail. Two thumbnails (Luxified, MegaBuilds) use real aerial photos of the excavation with green water pools, which independently suggests water in the pits.
Implication for us: a **real-image, no-face, no-CGI before/after** stands out in this field, but we cannot predict its CTR. `evidence_s2/thumb_S2_16x9.png` follows that format and states only a published number ("170 km promised"), two dates and an arrow to a visible feature.

## Not possible here (no data)
- **First 30 seconds:** captions and the player API require a logged-in session; I did not work around that. Hook analysis therefore rests on titles and thumbnails only.
- **Exact publish dates, CTR, retention, impressions:** not public. No CTR or retention forecast is made. OrbitalAtlas's own subscriber count and Analytics are needed for any estimate.
