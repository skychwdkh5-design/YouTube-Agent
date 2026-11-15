# EP015 Starship Flight 15 — rights and facts ledger

Facts are as of November 15, 2026. **Re-check the booster cause and any update before publishing.**

## Rights: everything you see and hear

| Element | Source | Rights basis | Label on screen |
|---|---|---|---|
| Ship, booster, tower, chopsticks, plumes, skies, maps, diagrams | Drawn procedurally in code (`production/episodes/starship_ep015/art.py`) | Original work of the channel | ILLUSTRATION / SCHEMATIC / VISUALIZATION |
| ATLAS host | The channel's own rig and art (`production/atlas-rig`), plus the owner's joint-parts sheet | Owned by the channel | — |
| Earth (orbit scene 2:11–2:34) | NASA Scientific Visualization Studio #5570, `Earth_wAtmos_spin_02_1080p60.mp4` | NASA media policy (informational use, no endorsement implied). Credit: "NASA's Scientific Visualization Studio" | "EARTH: NASA SVS VISUALIZATION · SHIP, ORBIT, SATELLITES: ILLUSTRATION" |
| Narration | ElevenLabs, Adam voice, on the channel's paid account | Commercial use under the account plan | — |
| Music and SFX | Synthesized in code (`engine/score.py`) | Original, no samples | — |
| **SpaceX photos and video** | **Not used** | SpaceX Flickr media is licensed for non-commercial use only, which does not fit a monetized channel | — |
| Livestream rips or news footage | **Not used** | — | — |

Description credit line: *Earth visualization: NASA's Scientific Visualization Studio. All rocket
imagery is illustration, not flight footage.*

## Facts: script claim → source

| Claim in narration | Status | Source |
|---|---|---|
| Ship caught by the tower on Nov 14, 2026 | Reported | AP (Nov 15); Space.com live (Nov 14); The Verge (Nov 15) |
| Launch on Nov 13 from Starbase, Texas | Reported | Space.com live (22:47 UTC) |
| The ship is Ship 42 | Reported | Space.com live |
| The plan was to catch both stages on the same flight | Mission plan | SpaceX Flight 15 page |
| The booster catch was called off, it was diverted toward the Gulf, and it did not come back | Reported | AP; Space.com |
| The cause is unconfirmed, and early reports differ | Stated as such in the script | AP reports a guidance-triggered self-destruct; Space.com reports a low-fuel-mass alarm. **We do not show a breakup mechanism.** |
| Super Heavy boosters were caught on earlier flights | Background, widely reported | Public flight history |
| About 275 km orbit | **Mission plan.** The script says "according to the mission plan" | SpaceX Flight 15 page |
| 26 Starlink V3 satellites deployed | Reported | AP |
| Three satellites were *planned* to carry heat-shield inspection cameras | **Mission plan.** The script says "planned" | SpaceX Flight 15 page |
| 14 orbits, more than 22 hours / about 22.5 hours | Reported | AP (14 orbits); Space.com (about 22.5 h) |
| About 17,000 mph / 28,000 km/h in low orbit | General physics (LEO orbital speed is about 7.8 km/s). This is **not** a Flight 15 entry-speed claim | Textbook value |
| Deorbit burn, plasma, tiles, flaps, belly-flop, flip, catch | General description of the published Starship return profile | SpaceX Flight 15 page (planned sequence) |
| "First Starship upper stage caught after orbit" | Reported as a first | The Verge; AP |
| Legs vs payload mass rationale | The general design argument SpaceX gives | SpaceX public statements. Phrased as "the idea is…" |

Numbers the script deliberately avoids:

- exact entry speed;
- temperatures;
- arm gap;
- reflight date;
- price;
- Mars dates;
- any claim that the booster survived splashdown;
- any claim that "the tower landed the ship".

## Source URLs (for the description)

- SpaceX, Flight 15 mission page: https://www.spacex.com/launches/starship-flight-15
- AP, Nov 15, 2026: https://apnews.com/article/df394c1b5a0f85e11194f9ff7db9ee6b
- Space.com live updates, Nov 14, 2026: https://www.space.com/news/live/spacex-starship-flight-15-live-updates-nov-14-2026-starship-first-double-landing-attempt
- The Verge, Nov 15, 2026: https://www.theverge.com/science/1033930/spacex-chopstick-starship-catch
- NASA SVS 5570: https://svs.gsfc.nasa.gov/5570

**Verification note:** I could not open the AP, Space.com or Verge pages directly from this
environment because of network blocks. The claims above come from those outlets' search snippets
and the ZIP's source ledger. Open each link once before publishing.

## v2 (2026-11-15): live archive footage, no host

No Flight 15 footage is used. SpaceX media is not used (non-commercial licence). Every live shot carries an on-screen ARCHIVE label with the flight, the date and the credit. Licences were read from the Wikimedia Commons file metadata (imageinfo extmetadata) on 2026-11-15. The files were supplied by the owner because upload.wikimedia.org returned 429 here. The sizes and durations match the Commons originals exactly.

| File (src/) | Commons file | Licence / author | SHA256 (prefix) | Used for |
|---|---|---|---|---|
| ift5_catch.webm | SpaceX Starship integrated flight test -5 - launch and catch - 13 October 2024.webm | CC BY 3.0, Anne Toal | 9008ca41 | Flight 5 booster catch (hook, earlier catches) |
| ift5_booster_cc0.webm | Space X Starship Flight 5 Booster Landing.webm | CC0, TimBunning1 | 63004d31 | Flight 5 crowd and booster return (portrait) |
| ift2_nasa.webm | Starship IFT2 NASA Video 2 Part 1.webm | Public domain, NASA | fa84d7b1 | Flight 2 ascent and booster loss, plus launch audio |
| ift2_aerostat.webm | RF IFT2 Aerostat.webm | Public domain, US Customs and Border Protection | 5e8a6c49 | Flight 2 liftoff, tower close-up |
| ift1_wb57.webm | SpaceX Starship IFT-1 NASA WB-57 Cam 0.webm | Public domain, NASA | 353348c2 | Flight 1 tumble and explosion ("not routine yet") |
| ship25_debris.webm | SpaceX Starship Ship 25 debris re-entering the atmosphere.webm | Public domain, NOAA/NWS | 6da98edb | Flight 2 ship debris on weather radar |
| cira6.webm | Starship Sixth Flight Test From SpaceX (CIRA 2024-11-19 - nolabels).webm | Public domain, GOES (NOAA/CIRA) | 9c6c5980 | Flight 6 seen from orbit |
| cira8.webm | SpaceX's Eighth Starship Launch and Reentry (CIRA 2025-03-06 - nolabels).webm | Public domain, GOES (NOAA/CIRA) | 01cbc94f | not used in v2 |

The v1 explainer graphics remain for the beats that have no free footage: the abort map, orbit (NASA SVS 5570), re-entry, the reason for the chopsticks, and the ship catch. These are labelled SCHEMATIC, ILLUSTRATION or VISUALIZATION.

Fact recheck (2026-11-15, web search):
- CNBC, Engadget and Space.com confirm that Ship 42 was caught on Nov 14 after 14 orbits and that 26 Starlink V3 satellites were deployed.
- The Booster 22 catch was called off, and the booster was diverted to the Gulf.
- Musk said the booster was "slightly low on fuel" and had GNC issues. No official root cause has been published, which matches the narration ("not confirmed").
