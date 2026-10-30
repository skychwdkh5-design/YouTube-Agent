# Channel baselines — plan for week 2026-W45 (owner-approved: up to 15 vidIQ credits)

Purpose: replace vidIQ's undisclosed breakout scores with our own baselines for three on-topic,
non-sensational channels from the 2026-10-30 scan. Nothing else may be bought with these credits.

| channel | channel id | why | video in the scan |
|---|---|---|---|
| ALPHA TECH | UCO9Vgn2ayVe67fE5tP6JQFA | on-topic (Moon lander), 156K subs | iYJHiSEcmds, 522K, vidIQ 45x |
| Chris Pattison | UC-EjFMzCvkFXY5AJl5Zmm3g | on-topic (Artemis II photos), 57.5K subs | nR0RsJ4RJuA, 212K, vidIQ 8.1x |
| Ellie in Space | UCelXvXZDvx8_TdOOffevzGg | on-topic (Starship landing plan), 232K subs | miekYu3huBU, 430K, vidIQ 3.4x (young) |

## Steps (no earlier than Monday 2026-11-02, week 2026-W45)
1. `vidiq_balance` (free) → note the balance.
2. `python3 research/topic_radar.py budget --plan 15 --balance <live>` — exit 2 = stop, spend nothing.
3. Three calls, 5 credits each: `vidiq_channel_videos(channelId=<id>, videoFormat="long", popular=false)`.
   `popular=false` (recent uploads) on purpose: a most-popular list would inflate the baseline.
4. Save each raw response unchanged to `research/runs/2026-11-02-baselines/raw_<channel>.json`, with
   every video URL (`https://www.youtube.com/watch?v=<id>`).
5. Append one ledger line per call (also the free balance calls) to `research/vidiq/ledger.jsonl`.
6. `vidiq_balance` again; stop if the spend differs from 15.
7. Run `research/outliers.py` on the three channel lists plus the three scan videos; write `OUTLIERS.md`;
   update `docs/growth/OUTLIER_RESEARCH.md` run log. Hypotheses H-O1/H-O2 stay hypotheses.

Hard limits: 15 credits total, NEXORA weekly cap 20 and cycle cap 90 (`research/vidiq/budget.json`),
no other vidIQ tool, no generation, no channel changes.
