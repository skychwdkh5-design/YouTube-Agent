# EP006 - script, shot plan, Shorts, packaging, voice budget (no voice generated, nothing published)

Production folder: `productions/ep006/`. Script: `productions/ep006/script.md` (885 words, ~6 min by the gate's 2.45 words/s; passes the script gate and yt-facts). Claims: `productions/ep006/claims.json`.
Start test (silent, 38.5 s, 720p/15 fps, timings ESTIMATED, no narration, no captions): `productions/ep006/render/animatic/EP006_start_animatic_720p15_silent.mp4`.

## 1. Fact check against the primary sources (what changed in the script)
| point | result |
|---|---|
| USGS ~100 km | USGS: "nearly 100 km" / "approximately 100 kilometers" along the Lende Khola and Trishuli Khola, and it "impacted populated areas downstream ... including the Rasuwagadhi border post". It does NOT say the 100 km ends at Rasuwagadhi, and the script says so (our own trace shows ~20 km to the river turn near that post). |
| seismic signal | USGS: "energy equivalent to a M5.2 earthquake", second event ~3 h later "equivalent to M4.2". Script: energy comparison produced by the failure; never an earthquake that caused it. |
| cause | USGS has not determined landslide-with-glacier vs glacier failure; all preliminary. |
| ICIMOD 13 Oct (132 million m3, 40 cm) | ICIMOD page NOT readable from this environment (DNS). Figures come from coverage of the press release (ICIMOD, ESA story, Gizmodo, Down To Earth - search summaries). Deformation: Sentinel-1 radar, up to 40 cm, line of sight, 7 Jul-24 Aug 2026 (48 days, ends 2 days before the failure). Volume: ICIMOD ~132 million m3, but a preprint suggests a much smaller order of magnitude - script says estimates differ. Script says nothing proves it was predictable. These claims are MEDIUM confidence; the ICIMOD page should be read by the owner before voice. |
| deaths/missing | No exact figure used. Nepal: sources 1,367 (NDRRMA, Sept), 1,454 (4 Oct), 1,455 (7 Oct), 1,456 dead and 4,718-5,285 missing (30 Sep-14 Oct) -> script: "more than 1,400 dead, roughly five thousand listed missing, lists keep changing". Tibet counted separately: Xinhua 43 dead / 519 missing at Gyirong Port as of 5 Sept; overlap with Nepal's list unclear -> never added. Nepal Police/NDRRMA bulletins themselves not read (trackers/news only). |
| glacial lakes / 2015 | ICIMOD: not a conventional glacial lake outburst flood. "~200 dangerous lakes" and a July 2025 lake flood were seen in one outlet each only -> NOT used. 2015: USGS only (M7.8 earthquake, ~1,900 m fall, >200 killed); one source said 350, USGS wording kept. |

## 2. Real materials and licences
| item | rights | use in EP006 |
|---|---|---|
| Sentinel-2 L2A 12 Aug 2026 (our crop) | Copernicus free/open, commercial OK; credit "Contains modified Copernicus Sentinel data 2026" | USED (before view; clearest pass, 19 % scene cloud) |
| Landsat 9 26 Aug 2026 (our crop, USGS EROS browse GeoTIFF) | public domain; credit USGS | USED (after view; 30 m, on the 10 m grid by nearest neighbour, shown as blocks) |
| Sentinel-2 24 and 27 Aug | scene cloud 39-97 %; the valley is mostly hidden | NOT usable as "after" (checked by eye) |
| 3 US Air Force photos, relief supplies at Kathmandu airport, 2 Sep 2026 (`media/ledger.json`: palletized_life_saving_equip, a_member_of_the_nepali_armed, us_and_nepali_officials_besi) | US government work, VERIFIED (Commons metadata; DVIDS original not reachable); Commons 1920 px copies | NOT in the film: the narration has no sentence about relief flights (claim C12 has one source = low). Available if the owner wants one added. |
| 4th USAF photo | download blocked by Wikimedia robot policy | UNVERIFIED, not used |
| Gyirong CCTV videos + GIF (Commons "public domain", unknown author, Chinese news source) | rights unclear | REJECTED |
| ESA before/after images | CC BY-SA 3.0 IGO (share-alike) or CC BY 4.0 on the ESA Flickr copy | NOT used (we built our own from the data) |
| Umbra SAR (Commons, CC BY 4.0, 2026-08-29...09-13) | commercial OK with credit "Umbra Lab, Inc." | NOT downloaded: 8,000-16,000 px TIFF via Commons thumbnails would be a new workflow; possible later |
| rasuwaflood.org | licence unknown | not contacted (owner did not allow) |
| NASA image library (images-api.nasa.gov) | host blocked (CONNECT 403) | not checked, reported once |
Wikimedia Commons works (API with a User-Agent) but rate-limits hard (429); originals blocked, 1920 px thumbnails work.
Visual-standard exception (no verified ground photograph of the flood itself): chapters hook/plan/method/obs/limits/close are satellite data + own graphics only; nothing is presented as a photo.

## 3. Shot plan (timings ESTIMATED from word counts; they are re-timed from real word timings after the voice exists)
| time (s) | chapter | visual asset | source / licence |
|---|---|---|---|
| 0.0-6.7 | hook | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 6.7-13.5 | hook | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 13.5-23.8 | plan | y2026, y2026->l2026 | Landsat 9 L1TP 141/040, 26 Aug 2026; Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 23.8-38.5 | plan | i_usgs_s1, i_usgs | own graphic (text card/chart); sources on the card |
| 38.5-43.6 | plan | i_100km_s1, i_100km | own graphic (text card/chart); sources on the card |
| 43.6-48.7 | plan | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 48.7-54.9 | plan | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 54.9-59.3 | plan | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 59.3-75.6 | plan | i_seismic_s1, i_seismic_s2, i_seismic | own graphic (text card/chart); sources on the card |
| 75.6-92.8 | plan | i_cause_s1, i_cause | own graphic (text card/chart); sources on the card |
| 92.8-106.2 | plan | i_2015_s1, i_2015_s2, i_2015 | own graphic (text card/chart); sources on the card |
| 106.2-122.6 | plan | i_toll_s1, i_toll_s2, i_toll | own graphic (text card/chart); sources on the card |
| 122.6-134.6 | plan | i_china_s1, i_china | own graphic (text card/chart); sources on the card |
| 134.6-137.5 | plan | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 137.5-140.4 | plan | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 140.4-144.7 | method | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 144.7-149.1 | method | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 149.1-165.8 | method | i_icimod_s1, i_icimod_s2, i_icimod | own graphic (text card/chart); sources on the card |
| 165.8-192.4 | method | i_radar_s1, i_radar_s2, i_radar_s3, i_radar | own graphic (text card/chart); sources on the card |
| 192.4-200.4 | method | i_volume_s1, i_volume_s2, i_volume | own graphic (text card/chart); sources on the card |
| 200.4-202.7 | method | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 202.7-205.0 | method | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 205.0-207.3 | method | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 207.3-213.6 | obs | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 213.6-219.8 | obs | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 219.8-226.1 | obs | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 226.1-232.3 | obs | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 232.3-239.3 | obs | i_clouds | own graphic (text card/chart); sources on the card |
| 239.3-247.0 | obs | l2026 | Landsat 9 L1TP 141/040, 26 Aug 2026 |
| 247.0-251.9 | obs | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 251.9-262.6 | obs | y2026, y2026->l2026 | Landsat 9 L1TP 141/040, 26 Aug 2026; Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 262.6-276.4 | obs | y2026, y2026->l2026 | Landsat 9 L1TP 141/040, 26 Aug 2026; Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 276.4-279.6 | obs | l2026 | Landsat 9 L1TP 141/040, 26 Aug 2026 |
| 279.6-283.0 | obs | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 283.0-286.9 | obs | i_flow_scale_s1, i_flow_scale | own graphic (text card/chart); sources on the card |
| 286.9-288.8 | obs | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 288.8-290.7 | obs | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 290.7-296.8 | obs | i_official_s1, i_official | own graphic (text card/chart); sources on the card |
| 296.8-300.0 | obs | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 300.0-306.8 | limits | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 306.8-313.6 | limits | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 313.6-330.2 | limits | i_cannot_s1, i_cannot_s2, i_cannot_s3, i_cannot | own graphic (text card/chart); sources on the card |
| 330.2-335.1 | limits | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 335.1-339.7 | close | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 339.7-344.3 | close | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 344.3-348.9 | close | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 348.9-353.5 | close | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 353.5-357.4 | close | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |
| 357.4-361.2 | close | y2026 | Sentinel-2 L2A 12 Aug 2026 (tile 45RUM, orbit 119) |

Graphic cards carry their own source line (USGS 28 Aug 2026; ICIMOD 13 Oct via coverage; Xinhua/NBC; Nepali lists). Pins "RASUWAGADHI (APPROX.)" and the hand-traced swath are our own marks: the border-post position is approximate (from memory/maps, not from a source) and the trace is a visual judgement, both labelled on screen. Known plan warnings: few distinct visual families in the first 10 s; the radar card holds ~26 s (4 text steps); close chapter is map-only (rule-built); the hook/close chapters are built by the planner's rule, so the before/after reveal starts at ~13 s in the `plan` chapter rather than at 0 s.

## 4. Two Shorts (scripts from verified claims; not yet run through the Shorts pipeline or the claims gate)
**Short A - "The radar saw it move" (~35 s).** Hook (0-3 s, visual: Sentinel-2 12 Aug valley, slow push-in): "For seven weeks before the disaster, a radar satellite was picking up movement in a mountain slope in Nepal." Body: "ICIMOD said Sentinel-1 detected up to 40 centimeters along its line of sight, between 7 July and 24 August. That ended two days before the failure. We do not claim it was a warning anyone could have acted on." Bridge: "What the satellites saw on the day, in the full video." Claims C8; limit sentence {L}. ~450 characters.
**Short B - "Two weeks apart" (~30 s).** Hook (0-3 s, visual: wipe 12 Aug -> 26 Aug on the valley): "12 August: a quiet valley. 14 days later: a dark swath runs through it." Body: "Different satellites, different pixels - Landsat's are 30 meters, shown as blocks. We traced the swath by eye: about 30 kilometers in our frame, clouds hiding the rest. USGS said the flow traveled about 100 kilometers." Bridge: "The full path, and what we cannot say, in the long video." Claims C13, C14, C2; limit sentence {L}. ~430 characters.
Voice for both Shorts, if wanted: ~880 characters (~880 credits), separate approval.

## 5. Title and cover options (no real photograph on any cover; no victims)
Titles: (1) "A Mountain Moved for 7 Weeks. Then It Fell." (claim-safe? radar said movement; keep "slope" wording if the owner prefers: "Satellites Saw a Himalayan Slope Move Before It Failed") (2) "Nepal's Flood From Orbit: 12 August vs 26 August" (3) "What Satellites Saw Before the Langtang Disaster - And What They Didn't". Avoid "predicted/could have been prevented" and any death count in the title.
Covers: A - the 12 Aug / 26 Aug wipe split in half, text "14 DAYS APART"; B - the swath on the Landsat blocks with a thin arrow, text "~30 KM"; C - radar card style "40 CM" with a slope image (text must say "RADAR, LINE OF SIGHT" in small print).

## 6. Voice budget
Script characters sent to ElevenLabs: **5,001** (3 chunks), model eleven_multilingual_v2, rate 1.0 credit/char -> **5,001 credits for one generation** (limit set by the owner: 6,500; real account balance not readable: the key lacks user_read). A regeneration costs the same again. Voice is NOT approved/generated: stage `voice` = awaiting_approval.

## 7. Timing so far (`productions/ep006/produce_runs.json`)
Wall clock from first command to the plan and start test: ~20 min of session time in the first block + the animatic (render 40 s, 38.5 s of video at 15 fps) - stages: visuals 9 s, storyboard 1 s, visualcheck 11 s (automatic parts); the research, script writing, visual notes and frame reviews were Claude work and are not measurable from code (no model-call/token counters available). Not a 30-minute claim.

## 8. Still open
- Owner: read the ICIMOD page (or approve medium-confidence ICIMOD claims C7-C9), approve the script, approve voice (<= 6,500 characters).
- Hook is not a before/after at 0 s (planner rule; engine not changed as instructed).
- Label contrast and arrows were not seen in the still checks; they are visible in the animatic only for the first 38.5 s. Remaining chapters have not been rendered.
- Shorts and covers are text plans only.
