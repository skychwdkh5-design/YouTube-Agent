# EP006 - concept and pre-check (Nepal, 26 Aug 2026). No production, no voice, nothing paid.

## 1. Is the event documented? YES
| point | source (all read on the day, preliminary) |
|---|---|
| 26 Aug 2026, morning local time: rapid slope failure involving a glacier in Langtang NP, Nepal; debris flow + flood ran ~100 km down the Lende Khola / Trishuli Khola to the Rasuwagadhi border post; China-Nepal highway damaged | USGS Landslide Hazards page (updated 28 Aug) |
| seismic energy of the failure = M5.2 equivalent; a second signal ~3 h later = M4.2 equivalent | USGS (same page) |
| ICIMOD: an ice/rock avalanche, **not** a classic glacial-lake outburst flood | ICIMOD (via search summary; icimod.org not fetchable here) |
| ~132 million m3 of rock and ice; Sentinel-1 deformation up to 40 cm between 7 Jul and 24 Aug | ESA story (search summary only; esa.int was offline when fetched) |
| Landsat-9 image ~2 h after the collapse; Sentinel-2 12 Aug (before) and 27 Aug (after) | ESA / Copernicus image of the day |
**Open conflicts the script must not smooth over:** (a) USGS says it is not yet determined whether it was a landslide incorporating glacier ice or a glacier collapse; (b) deaths/missing differ a lot by source and date (Al Jazeera 27 Aug: 359 dead / 1,300+ missing incl. Tibet; later ICIMOD figure 1,451 dead / 5,745 missing in Nepal; USGS gives no toll). Rule: no number without source + date; say "reported"; re-check right before voice. Volume (132 million m3) and the 2015 same-peak event need a primary source before they enter claims.json. Details are preliminary and will change.

## 2. Materials and rights (commercial YouTube use)
| material | what | rights | verdict |
|---|---|---|---|
| Landsat-9 26 Aug 2026 (path 141 rows 40/41; scene cloud 48 % / 68 %) and Landsat-8 18 Aug, 3 Sep | our own pipeline, 30 m | USGS/NASA public domain, credit "Landsat, USGS" | USE (local cloud over the site still to be checked on the crop) |
| Sentinel-2 L2A tiles 45RUL/45RUM: 11-12 Aug (scene cloud 13-28 %), 24 Aug, 27 Aug (54 %), 8 Sep | our own pipeline, 10 m, via free STAC | Copernicus free, full and open incl. commercial; credit "Contains modified Copernicus Sentinel data 2026" | USE |
| ESA / Copernicus before-after "image of the day" | ready-made | EU/ESA terms differ per item, not readable here (esa.int offline, eu-space host not fetchable) | do NOT use; we make our own from the data |
| USGS inundation map | map | listed "Public Domain" on the USGS page | USE if the file is obtained from USGS |
| Planet Labs images (in Al Jazeera) | commercial | copyrighted | NO |
| Ground photos: CARE (CSRC/CARE), UN News (c) UNICEF, WHO Nepal, news agencies | documentary | all copyrighted, permission needed | NO without a written licence |
| rasuwaflood.org (VIVA-D evidence archive) | geolocated photos/videos | licence not stated; host not reachable from here | UNKNOWN: owner to ask for the licence |
| Wikimedia Commons / NASA image library | possible CC / PD ground photos | hosts blocked in this environment; Commons had no file for this event in search | UNCHECKED until domains are opened |
**Bottom line:** the film can be built honestly from free satellite data plus motion graphics. Verified real ground photographs are NOT available now. EP006 would therefore carry a recorded visual-standard exception for ground photos unless the owner opens the Commons/NASA domains (and one of them yields a CC0/CC BY file), or obtains written permission from an agency or the archive. Nothing is used on assumption.

## 3. Concept (draft, ~7 min, 5 chapters)
Working title: "The Mountain That Fell" (packaging is a later step).
1. Hook: one frame from orbit, same valley, 12 Aug vs 27 Aug - a hanging glacier is gone, a grey tongue runs down the valley.
2. Warning: Sentinel-1 deformation before the collapse (only as reported, cited; no invented radar frames).
3. The fall: ~1.2 km drop, M5.2-equivalent signal, what "rock-ice avalanche vs lake outburst" means.
4. The 100 km path: Landsat-9 two hours after, then Sentinel-2 mapping the flow to Rasuwagadhi; arrows and distance measured from our grid.
5. What it means: the same peak in 2015, ~200 dangerous glacier lakes (ICIMOD) as context only, uncertainty stated.
US viewer: explain Langtang/Trishuli in a few words, metres + feet, "about 62 miles". Scandinavian travel: glacier hazard and avalanches resonate in Norway/Sweden without forcing an angle.
Topic scores (1-5): US 4, Sweden 3, Norway 4, Denmark 3, international 5, visual 5, curiosity 5, evidence 4 (satellite) / 2 (ground), satellite imagery 4, monetization 3 (sensitive: mass casualty - sober tone, no sensational thumbnails, no victim imagery).

## 4. ElevenLabs budget (nothing run)
EP005 measured: 5,280 characters = 385.3 s (13.7 chars/s), eleven_multilingual_v2, 1.0 credit/char, one generation.
| length | characters | credits (1 generation) |
|---|---|---|
| 6 min | ~4,900 | ~4,900 |
| **7 min (recommended)** | **~5,750** | **~5,750** |
| 8 min | ~6,600 | ~6,600 |
Proposed approval: `--budget-chars 6500` (7 min + ~13 % margin). A regeneration costs the same again, so the script must pass facts, visualcheck and an owner read BEFORE voice. Real balance cannot be read (the API key lacks user_read), so cost is the published rate, not a measured balance.

## 5. Needed from the owner
1. Confirm topic EP006 and length (7 min) and budget (6,500 characters).
2. Decide on ground photos: open commons.wikimedia.org, upload.wikimedia.org, images.nasa.gov (and the other NASA hosts), or accept satellite-only with the recorded exception.
3. Sensitivity: keep the tone sober; no casualty imagery.
