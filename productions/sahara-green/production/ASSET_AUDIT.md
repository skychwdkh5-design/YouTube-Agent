# EP001 asset audit (36 active scenes)

Status tally: {"built_landsat_still": 10, "built_graphic": 18, "built_nasa_still": 2, "sequence_rendered": 5, "built_nasa_video_30fps": 1}

| scene | time | kind | asset | status |
|---|---|---|---|---|
| 1 | 0.0-2.06 | landsat_loc | Tassili n'Ajjer plateau, LC09_L1TP_190042_20251220 (natural-colour browse, native 30 m crop) | built_landsat_still |
| 2 | 2.06-8.24 | graphic | callout 230+ (claims.md) | built_graphic |
| 3 | 8.24-13.33 | landsat_loc | Bodele depression, LC09_L1TP_183048_20260731 (source bands B4/B3/B2, tone B) | built_landsat_still |
| 4 | 13.33-17.3 | nasa | NASA SVS 3539 Blue Marble Next Generation, africa.0700.jpg | built_nasa_still |
| 5 | 17.3-22.77 | graphic | callout 'a few inches of rain a year' | built_graphic |
| 6 | 22.77-36.26 | seq | East Oweinat wipe 1984->2024 with 1984 push-in <=3 percent | sequence_rendered |
| 7 | 36.26-57.92 | graphic | timeline 15,000 y to today, band 11,000-6,000 | built_graphic |
| 8 | 57.92-73.29 | landsat_loc | Bodele wide, 'floor of Lake Mega-Chad' callout | built_landsat_still |
| 9 | 73.29-94.11 | landsat_loc | g09 callout ~200 burials (Gobero, Niger) then Tassili canyons still | built_landsat_still |
| 10 | 94.11-117.4 | graphic | rainfall card ~100 / ~450 mm per year | built_graphic |
| 11 | 117.4-148.48 | landsat_loc | Ounianga lakes, LC09_L1TP_182047_20260622 (source bands, tone B), wide to close | built_landsat_still |
| 12 | 148.48-174.45 | graphic | 3-step orbital/monsoon diagram | built_graphic |
| 13 | 174.45-192.56 | graphic | model-vs-geology flow | built_graphic |
| 14 | 192.56-214.31 | graphic | schematic green episodes on a time axis | built_graphic |
| 15 | 214.31-236.91 | landsat_loc | Ounianga + N->S arrow insert | built_landsat_still |
| 16 | 236.91-265.96 | graphic | circulation diagram (yt-graphics circulation) | built_graphic |
| 17 | 265.96-274.33 | landsat_loc | Gilf Kebir slow pull-out, LC09_L1TP_179044_20251121 (natural-colour browse, native 30 m crop) | built_landsat_still |
| 18 | 274.33-291.04 | seq | East Oweinat timelapse 1984/2000/2010/2016/2024 | sequence_rendered |
| 19 | 291.04-317.01 | graphic | East Oweinat zoom ends 1.64 s into the scene (<=2.2 s approved); then g19 aquifer graphic (fossil water) | built_graphic |
| 20 | 317.01-328.48 | landsat_loc | Kufra push-in, LC09_L1TP_181043_20260919 (natural-colour browse, native 30 m crop) | built_landsat_still |
| 21 | 328.48-348.77 | seq | Toshka wipe chain 1999/2002/2011-12/2021 | sequence_rendered |
| 22 | 348.77-357.18 | seq | East Oweinat close-up 2024 | sequence_rendered |
| 23 | 357.18-395.31 | graphic | desalination-pipeline flow, footer PROPOSAL (2009) | built_graphic |
| 24 | 395.31-397.99 | graphic | text card multi-trillion-dollar projects | built_graphic |
| 24b | 397.99-443.56 | graphic | callout >1,000 mm/yr (2009 simulation) | built_graphic |
| 25 | 443.56-492.27 | graphic | water-budget stacked bar (MODEL) | built_graphic |
| 25b | 492.27-498.16 | nasa | pull-out Sahara -> Africa/Atlantic: Blue Marble africa.0700.jpg as a still zoom | built_nasa_still |
| 29 | 498.16-525.04 | nasa | NASA SVS 4362 Dust in the Wind (CALIPSO), webm 60 fps -> 30 fps | built_nasa_video_30fps |
| 30 | 525.04-556.06 | landsat_loc | Bodele 100-150 km, white diatomite flats | built_landsat_still |
| 31 | 556.06-568.18 | graphic | text card HYPOTHESIS - NO STUDY FOUND | built_graphic |
| 32 | 568.18-616.13 | graphic | simulation diagram ~6,000 y ago | built_graphic |
| 33 | 616.13-663.05 | graphic | callouts only; optional Lake Chad wipe dropped | built_graphic |
| 34 | 663.05-702.42 | graphic | three separate labelled bars (COP21, PA-GGW...) | built_graphic |
| 35 | 702.42-720.78 | seq | East Oweinat widest view wipe 1984->2024 | sequence_rendered |
| 36 | 720.78-740.04 | graphic | closing text card (uncertainty statement) | built_graphic |
| 37 | 740.04-747.36 | landsat_loc | Ounianga or Tassili slow pull-out | built_landsat_still |

## Provenance (acquired 2026-10-08)

- **svs3539**: title: Blue Marble Next Generation images from Terra/MODIS; url: https://svs.gsfc.nasa.gov/3539; file: africa.0700.jpg; credit: NASA Goddard Space Flight Center Scientific Visualization Studio; Blue Marble data: Reto Stockli, NASA Earth Observatory; data_date: 2004 monthly composites; released: 2008-08-29; licence: NASA media usage guidelines: public domain unless noted; credit NASA; acquired: 2026-10-08
- **svs4362**: title: Dust in the Wind (CALIPSO); url: https://svs.gsfc.nasa.gov/4362; file: SaharanDust_1080p_60fps.webm; credit: NASA Goddard Space Flight Center Scientific Visualization Studio; visualizer Kel Elkins (USRA); CALIPSO data; released: 2015-09-28; licence: NASA media usage guidelines: public domain unless noted; credit NASA; acquired: 2026-10-08; note: VP8 1920x1080, 60 fps, 104.25 s; must be decimated to 30 fps (every 2nd frame) before use
- **landsat_location_stills**: note: see production/stills/*.json (scene, date, window, sha256); bands_scenes: ['LC09_L1TP_182047_20260622_20260622_02_T1 (Ounianga)', 'LC09_L1TP_183048_20260731_20260731_02_T1 (Bodele)']; browse_scenes: ['LC09_L1TP_190042_20251220 (Tassili)', 'LC09_L1TP_179044_20251121 (Gilf Kebir)', 'LC09_L1TP_181043_20260919 (Kufra)']; credit: U.S. Geological Survey / NASA Landsat; licence: USGS Landsat data are public domain, credit requested; acquired: 2026-10-08; source_url: https://earthexplorer.usgs.gov/
- **landsat_browse_superseded**: url: https://m2m.cr.usgs.gov/ (USGS EarthExplorer browse images); credit: U.S. Geological Survey / NASA Landsat; licence: USGS Landsat data are public domain; credit requested; acquired: 2026-10-08; scenes: ['LC08_L1TP_183048_20251024', 'LC09_L1TP_179044_20251121', 'LC09_L1TP_180043_20251230', 'LC09_L1TP_181047_20251221', 'LC09_L1TP_190042_20251220']; note: 8-bit natural colour browse at 30 m; not tone-B comparable to the locked sequences, used for location shots only; framing unchecked

No invented imagery stands in for scientific evidence. Every graphic carries only claims from `story/claims.md`.
