# EP008 — two Shorts (cut from the long episode, 20-35 s like EP007)

Both use only material from the long video (same facts, same assets, same labels) and point to it via
"Related video" (set by hand in Studio). Vertical 1080x1920. No voice generated yet.

## Short 1 — "The Moon rocket with no upper stage" (~28 s)
Promise: one surprising, verified hardware fact.

| t | picture (9:16) | text | VO |
|---|---|---|---|
| 0-2 | spacer photo, tight on the barrel (NASA/Sam Lott) | `NO ENGINE` | "This is going on NASA's next Moon rocket." |
| 2-7 | d-sls-stack vertical: Artemis II stack, upper stage highlighted | `ARTEMIS II: UPPER STAGE` | "On Artemis Two, this spot held the stage that pushed Orion toward the Moon." |
| 7-13 | stage slides out, spacer slides in | `ARTEMIS III: SPACER` | "On Artemis Three, it's a spacer, a metal barrel with no engine." |
| 13-20 | d-orbit-vs-moon vertical, LEO ring | `EARTH ORBIT ONLY` | "Because Artemis Three won't leave Earth orbit. It's a docking test with two Moon landers." |
| 20-27 | d-sls-stack: stage moves to an 'ARTEMIS IV' stack | `UPPER STAGE → ARTEMIS IV` | "The upper stage moves to Artemis Four, the mission that actually lands." |
| 27-28 | — | `FULL STORY ↓` | — |
Facts: F14, F20, F02. Note: "Because Artemis Three won't leave Earth orbit" — NASA states the swap and the reassignment, not this causal line; owner to approve or replace with "Artemis Three stays in Earth orbit."

## Short 2 — "Two hours, nose to nose" (~32 s)
Promise: what the crew will actually do up there.

| t | picture | text | VO |
|---|---|---|---|
| 0-2 | a2-lunar-surface tight crop | `NOT LANDING` | "NASA's next Moon crew will spend two weeks in Earth orbit." |
| 2-9 | d-mission-sequence: Blue Moon dock (ILLUSTRATION) | `~2 DAYS · CREW INSIDE` | "First they dock with Blue Origin's lander, and up to two astronauts float inside, for about two days." |
| 9-17 | Starship test article at scale (171 ft) nose to nose with Orion (ILLUSTRATION) | `UP TO 2 HOURS` | "Then Starship, a hundred seventy-one feet tall, docks nose to nose. Up to two hours. Nobody goes inside." |
| 17-25 | Apollo 9 → Apollo 11 timeline (DIAGRAM) | `APOLLO 9 DID THIS IN 1969` | "Apollo Nine ran the same kind of test in Earth orbit in 1969, four months before the landing." |
| 25-31 | d-timeline: 2027 → 2028 | `LANDING: 2028` | "Artemis Four is supposed to land in twenty twenty-eight." |
| 31-32 | — | `FULL STORY ↓` | — |
Facts: F06, F07, F08, F10, F21, F13. Every docking frame labelled ILLUSTRATION - NOT REAL FOOTAGE.

QC: `qc.py --profile short --width 1080 --height 1920` (Shorts stay 20-35 s by owner order of 2026-10-28; the 35-60 s
default range will warn).
