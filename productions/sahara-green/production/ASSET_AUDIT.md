# EP001 asset audit (36 active scenes)

Status tally: {"browse_downloaded_unframed": 10, "to_build": 17, "downloaded_provenance_recorded": 2, "sequence_code_ready_render_pending": 6, "downloaded_needs_decimation": 1}

| scene | time | kind | asset | status |
|---|---|---|---|---|
| 1 | 0.0-2.06 | landsat_loc | Tassili n'Ajjer plateau, LC08 browse 2025-10-24 (path/row 183/048) | browse_downloaded_unframed |
| 2 | 2.06-8.24 | graphic | callout 230+ (claims.md) | to_build |
| 3 | 8.24-13.33 | landsat_loc | Bodele depression, browse LC09 2025-12-20 (190/042) | browse_downloaded_unframed |
| 4 | 13.33-17.3 | nasa | NASA SVS 3539 Blue Marble Next Generation, africa.0700.jpg | downloaded_provenance_recorded |
| 5 | 17.3-22.77 | graphic | callout 'a few inches of rain a year' | to_build |
| 6 | 22.77-36.26 | seq | East Oweinat wipe 1984->2024 with 1984 push-in <=3 percent | sequence_code_ready_render_pending |
| 7 | 36.26-57.92 | graphic | timeline 15,000 y to today, band 11,000-6,000 | to_build |
| 8 | 57.92-73.29 | landsat_loc | Bodele wide, 'floor of Lake Mega-Chad' callout | browse_downloaded_unframed |
| 9 | 73.29-94.11 | landsat_loc | Tassili canyons + callout ~200 burials | browse_downloaded_unframed |
| 10 | 94.11-117.4 | graphic | rainfall card ~100 / ~450 mm per year | to_build |
| 11 | 117.4-148.48 | landsat_loc | Ounianga lakes, wide and close (LC09 2025-12-30, 180/043) | browse_downloaded_unframed |
| 12 | 148.48-174.45 | graphic | 3-step orbital/monsoon diagram | to_build |
| 13 | 174.45-192.56 | graphic | model-vs-geology flow | to_build |
| 14 | 192.56-214.31 | graphic | schematic green episodes on a time axis | to_build |
| 15 | 214.31-236.91 | landsat_loc | Ounianga + N->S arrow insert | browse_downloaded_unframed |
| 16 | 236.91-265.96 | graphic | circulation diagram (yt-graphics circulation) | to_build |
| 17 | 265.96-274.33 | landsat_loc | Gilf Kebir slow pull-out (LC09 2025-11-21, 179/044) | browse_downloaded_unframed |
| 18 | 274.33-291.04 | seq | East Oweinat timelapse 1984/2000/2010/2016/2024 | sequence_code_ready_render_pending |
| 19 | 291.04-317.01 | seq | East Oweinat zoom to centre-pivot field; starts <=2.2 s late | sequence_code_ready_render_pending |
| 20 | 317.01-328.48 | landsat_loc | Kufra push-in with pin (LC09 2025-12-21, 181/047) | browse_downloaded_unframed |
| 21 | 328.48-348.77 | seq | Toshka wipe chain 1999/2002/2011-12/2021 | sequence_code_ready_render_pending |
| 22 | 348.77-357.18 | seq | East Oweinat close-up 2024 | sequence_code_ready_render_pending |
| 23 | 357.18-395.31 | graphic | desalination-pipeline flow, footer PROPOSAL (2009) | to_build |
| 24 | 395.31-397.99 | graphic | text card multi-trillion-dollar projects | to_build |
| 24b | 397.99-443.56 | graphic | callout >1,000 mm/yr (2009 simulation) | to_build |
| 25 | 443.56-492.27 | graphic | water-budget stacked bar (MODEL) | to_build |
| 25b | 492.27-498.16 | nasa | pull-out Sahara -> Africa/Atlantic: Blue Marble africa.0700.jpg as a still zoom | downloaded_provenance_recorded |
| 29 | 498.16-525.04 | nasa | NASA SVS 4362 Dust in the Wind (CALIPSO), webm 60 fps -> 30 fps | downloaded_needs_decimation |
| 30 | 525.04-556.06 | landsat_loc | Bodele 100-150 km, white diatomite flats | browse_downloaded_unframed |
| 31 | 556.06-568.18 | graphic | text card HYPOTHESIS - NO STUDY FOUND | to_build |
| 32 | 568.18-616.13 | graphic | simulation diagram ~6,000 y ago | to_build |
| 33 | 616.13-663.05 | graphic | callouts only; optional Lake Chad wipe dropped | to_build |
| 34 | 663.05-702.42 | graphic | three separate labelled bars (COP21, PA-GGW...) | to_build |
| 35 | 702.42-720.78 | seq | East Oweinat widest view wipe 1984->2024 | sequence_code_ready_render_pending |
| 36 | 720.78-740.04 | graphic | closing text card (uncertainty statement) | to_build |
| 37 | 740.04-747.36 | landsat_loc | Ounianga or Tassili slow pull-out | browse_downloaded_unframed |

## Provenance (acquired 2026-10-08)

- **svs3539**: title: Blue Marble Next Generation images from Terra/MODIS; url: https://svs.gsfc.nasa.gov/3539; file: africa.0700.jpg; credit: NASA Goddard Space Flight Center Scientific Visualization Studio; Blue Marble data: Reto Stockli, NASA Earth Observatory; data_date: 2004 monthly composites; released: 2008-08-29; licence: NASA media usage guidelines: public domain unless noted; credit NASA; acquired: 2026-10-08
- **svs4362**: title: Dust in the Wind (CALIPSO); url: https://svs.gsfc.nasa.gov/4362; file: SaharanDust_1080p_60fps.webm; credit: NASA Goddard Space Flight Center Scientific Visualization Studio; visualizer Kel Elkins (USRA); CALIPSO data; released: 2015-09-28; licence: NASA media usage guidelines: public domain unless noted; credit NASA; acquired: 2026-10-08; note: VP8 1920x1080, 60 fps, 104.25 s; must be decimated to 30 fps (every 2nd frame) before use
- **landsat_browse**: url: https://m2m.cr.usgs.gov/ (USGS EarthExplorer browse images); credit: U.S. Geological Survey / NASA Landsat; licence: USGS Landsat data are public domain; credit requested; acquired: 2026-10-08; scenes: ['LC08_L1TP_183048_20251024', 'LC09_L1TP_179044_20251121', 'LC09_L1TP_180043_20251230', 'LC09_L1TP_181047_20251221', 'LC09_L1TP_190042_20251220']; note: 8-bit natural colour browse at 30 m; not tone-B comparable to the locked sequences, used for location shots only; framing unchecked

No invented imagery stands in for scientific evidence. Every graphic carries only claims from `story/claims.md`.
