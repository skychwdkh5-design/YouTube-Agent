# Growth-system demo — 2026-10-30

Future NEXORA episode, nothing produced. No script, voice, render or upload. vidIQ: 5 credits
(balance 135 before; NEXORA week 2026-W44 now at its 20-credit cap), logged in `research/vidiq/ledger.jsonl`.

## 1. Competitor research (Outlier Detector)

`python3 research/outliers.py vidiq_outliers.json --as-of 2026-10-30 --markdown > OUTLIERS.md`

**Facts**
- One `vidiq_outliers` call (Artemis III / Moon-mission keyword, long-form, English, 6 months): 25 videos, 23 channels.
- Every ratio in the table is **vidIQ's** breakout score. vidIQ does not disclose its baseline or sample,
  and the channels' own comparable videos were not collected (5 credits per channel; YouTube RSS and
  the YouTube Data API are blocked in this environment). So the detector marks all 25 as
  `data: external, confidence: low` and lists **0 focus videos**. That is the correct result, not a bug:
  there is not enough data to call anything a confirmed 3-4x outlier.
- A feed that only returns outliers has no base rate; it cannot say how often Moon videos fail.
- 9 of 25 are sensational or AI-labeled ("found something beneath the Moon") — demand signal, not a model
  (NEXORA rule 1 forbids invented claims).
- On-topic and honest: CSA "Return to Earth with the Artemis II crew" (83x, 387K, 2:19), ALPHA TECH
  Starship HLS cabin (45x, 522K), Chris Pattison "12,000 New Artemis 2 Photos" (8.1x, 212K),
  Ellie in Space "NASA Reveals NEW Starship Moon Landing Plan" (3.4x, 430K, **6 days old → provisional**).

**Hypotheses (unverified)**
- H-O1: titles naming a concrete, new change ("NEW plan", "12,000 photos") outperform generic explainers on this subject.
- H-O2: first-person crew footage travels further than rocket hardware.
Neither is a fact; both go to `docs/growth/EXPERIMENT_LOG.md` as hypotheses.

**To make this confident next week (W45, ≤ 20 credits):** `vidiq_channel_videos` for 3 on-topic channels
(15 credits) gives each channel's own comparables, and the detector then computes our baseline.

## 2. Topic choice (`topic_radar.py score`, growth rubric) — `TOPICS.md`

Revised 2026-10-30 after the owner's review: gate evidence (rights, facts, length_fit) must be a URL or a
file, otherwise the topic cannot be GO. The first version had Artemis III at GO without that — fixed.

| # | Topic | Total | Status |
|---|---|---|---|
| 1 | Artemis III won't go to the Moon: NASA's docking test in Earth orbit | 4.09 | GO-CANDIDATE (gates: sources.json, media.json, OUTLINE.md) |
| 2 | Proactive AI agents | 3.26 | HOLD (unverified gates) |
| 3 | Microduck | 3.77 | BLOCKED (rights) |
| 4 | Honor Robot Phone | 3.11 | BLOCKED (rights, length_fit) |
| 5 | 1X NEO fact-check | 3.09 | BLOCKED (rights, facts) |

**Chronology (official NASA, 2026-10-23 and earlier — `sources.json`)**
2026-02-27 Artemis III becomes a 2027 test flight in low Earth orbit; landing moves to Artemis IV (2028) →
2026-06-09 crew named → 2026-07-30 Orion modules joined → 2026-09-30 booster forward assemblies done →
2026-10-23 NASA publishes the 14-day flight profile and the acceleration briefing.
The change is **not** new this week; the hook says "in February". The 2026-10-28 core-stage article is not used.

Corrections against the first draft: Starship stays docked **up to two hours** and the crew does not enter it
(not "about one day"); the novelty is lowered from 5 to 4 because the change is eight months old.

## 3. Three cover + title + first-15-s packages — `thumbnail_hook.json`

| | Title | Cover text | Cover object (asset) | First 3 s |
|---|---|---|---|---|
| **A (chosen)** | NASA's Next Moon Mission Won't Go to the Moon | NOT THE MOON? | Artemis III boosters (NASA/Cory S Huston) | that photo |
| B | Artemis III: Docking With Two Moon Landers - in Earth Orbit | DOCK FIRST | NASA concept graphic (labelled) | that graphic |
| C | This Spacecraft Will Carry 4 Astronauts - Just Not to the Moon | ORBIT ONLY | Artemis III Orion (NASA/Amanda Stevenson) | that photo |

Rights (`media.json`, checked against NASA's media guidelines): NASA photos only; no NASA insignia legible
on covers; no astronaut likeness on covers (NASA restricts current astronauts in promotional material);
Blue Origin and SpaceX artwork excluded (company copyright). Files still have to be downloaded from the
NASA pages and logged before production.

nx-qc package check: 7 pass; `thumbnail_hook_match` fails until the owner confirms on a real draft — as intended.

## 4. Open items
1. A person re-reads the six NASA pages in `sources.json` before the script (NEXORA rule 1).
2. Channel baselines: up to 15 vidIQ credits in week 2026-W45 (owner-approved), three channels — see `BASELINE_PLAN.md`.
3. Owner: OK the topic, or pick another.

Sources: [NASA 2026-02-27](https://www.nasa.gov/news-release/nasa-adds-mission-to-artemis-lunar-program-updates-architecture/),
[NASA 2026-06-09](https://www.nasa.gov/news-release/nasa-marches-toward-artemis-iii-mission-in-2027-names-crew-members/),
[NASA 2026-08-05](https://www.nasa.gov/blogs/missions/2026/08/05/nasa-joins-artemis-iii-orion-modules-rocket-hardware-update/),
[NASA 2026-10-13](https://www.nasa.gov/blogs/missions/2026/10/13/nasa-completes-artemis-iii-booster-stacking-shares-status-update/),
[NASA 2026-10-23 profile](https://www.nasa.gov/missions/artemis/nasas-artemis-iii-mission-to-test-future-moon-lander-operations/),
[NASA 2026-10-23 briefing](https://www.nasa.gov/blogs/missions/2026/10/23/nasa-shares-artemis-acceleration-plans-for-moon-missions/),
[NASA media guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/),
vidIQ `vidiq_outliers` 2026-10-30 (`vidiq_outliers.json`), 2026-10-29 run for the other topics.
