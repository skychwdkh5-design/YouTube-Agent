# EP005 — full 720p preview (iPad): QC and remaining flaws
Status: `VISUAL_REVISION_IN_PROGRESS` · USER_APPROVED NO · FINAL_RENDER_APPROVED NO · PUBLISH_APPROVED NO. Script, narration, facts and duration (385.31 s of speech) unchanged; no ElevenLabs call; no master render; nothing published.

File: `productions/neom-line/render/EP005_full_preview_720p.mp4` (1280x720, 30 fps, H.264/AAC, 385.88 s incl. 0.56 s tail, 30.3 MB). Built from the real timeline, real narration and real captions, chapter by chapter, then re-encoded to 720p. Not a master.

## Automatic QC (ffprobe/ffmpeg, one pass) — PASS
format h264 1280x720 + aac · duration 385.88 s vs speech 385.31 s · decode clean · loudness -17.7 LUFS, true peak -4.1 dBFS · no black frames · no frozen picture over 6 s · no silence over 2.5 s.

## Checks done on the content
- Narrator sync: every card step, scene, pin, arrow, label and wipe is tied to words by word timings (ElevenLabs word level); all events appear 0.2-0.4 s before the words except one: the Bloomberg card appears at the start of its chapter, 2.0 s before the words 'Bloomberg reported' (it sits under 'First, the plans.'; left as is) (`docs/EP005_sync_check*.json`). Chapter seams checked on frames (a 4.5 s overlap at the "shows" seam was found and fixed during assembly).
- Contrast of labels on imagery: every pin/tag/callout/graticule/source line now sits on a dark plate (alpha 0.80). Computed contrast on the worst case (white sand): white text 11.1:1, yellow 7.7:1 (typical sand 12.5 / 8.6). Pin text is 49 px at 1080p (about 33 px in 720p), tags 58 px (39 px), card text 34 px (23 px).
- Pixels: scenes that explain resolution use nearest-neighbour (Sentinel-2 10 m pixels and Landsat 30 m pixels as flat squares); Landsat is regridded onto the 10 m grid by nearest neighbour (`yt-geo/regrid_nearest.py`, no interpolation), labelled "LANDSAT 8: 30 M PIXELS - INDEPENDENT SATELLITE, NOT SHARPENED". Nothing is sharpened or invented.
- Rights: the only external photograph (NASA ISS) is excluded; Sentinel-2 (Copernicus) and Landsat 8 (USGS, public domain) credits are on screen; no render, concept, AI or stock images.
- Final media search (reachable domains: esa.int, nasa.gov, science.nasa.gov, SVS, earthobservatory): nothing about NEOM/Tabuk/Gulf of Aqaba; no lawful real construction frames exist for this film, so it ends with satellite evidence (recorded as a visual-standard exception).

## Remaining flaws (honest list)
1. No real photo or video of the construction: none lawfully available here (neom.com and Commons are blocked from this machine; press photos are copyrighted).
2. Holds over 8 s on one composition (yt-render still warns, worst 15.6 s): intro scene `i_scale` 11.8 s (arrow appears on the words), Bloomberg 12.9 s, Semafor 11.9 s, Reuters 8.2 s, seven-scenes flip 8.7 s, orbit 8.6 s, NDWI 9.5 s, three-dates flip 15.6 s (flips every 4.6 s), Landsat wipe 8.8 s, length wipe 11.0 s, "three reasons" card 12.0 s, "why we stop" card 10.0 s. Inside each, new information arrives on the narrator's words; I did not add decorative motion to pass the test.
3. Landsat is hazy at 30 m; it looks pale next to Sentinel-2 (honest, labelled).
4. Cards in the "plan" chapter are text on dark: the chapter is about reports, not imagery.
5. The yellow measuring arrows are drawn along the NDWI-detected extent; they are thin on a bright desert.
