# EP002 Dubai — Visual Evidence Check

Base: e062dac. Script and structure unchanged. Result: **no image could be viewed in this environment.** curl to assets.science.nasa.gov returned a 403 proxy block and WebFetch could not resolve the host, so every image is **VISUAL_UNINSPECTED**. Nothing below is a visual finding. Dimensions come from URL parameters in a page-fetch summary and are unconfirmed.

## Source images
| key | image | URL | attribution | acquisition | size (unconfirmed) |
|---|---|---|---|---|---|
| ASTER-2006 | Palm Islands, Dubai (ASTER, Terra) | page: https://science.nasa.gov/earth/earth-observatory/palm-islands-dubai-7040/ · file: https://assets.science.nasa.gov/content/dam/science/esd/eo/images/imagerecords/7000/7040/palmis_ast_2006261_lrg.jpg | NASA/GSFC/MITI/ERSDAC/JAROS, and U.S./Japan ASTER Science Team (claim 26) | 18 Sep 2006 (page text; filename day-of-year 261 agrees, which is a consistency check only) | about 3072 x 3797 portrait, JPEG about 1,005 KB |
| ISS-2022 | Astronaut photograph ISS067-E-3785 | page: https://science.nasa.gov/earth/earth-observatory/a-new-world-built-of-sand-149861/ · file: https://assets.science.nasa.gov/content/dam/science/esd/eo/images/imagerecords/149000/149861/iss067e003785_lrg.jpg | ISS Crew Earth Observations Facility and Earth Science and Remote Sensing Unit, Johnson Space Center; Nikon D4 (claim 27) | 6 Apr 2022 | about 2768 x 4928 portrait, JPEG about 4.10 MB |

## Scene by scene
| scene | image needed | caption evidence (claims) | direct inspection | status |
|---|---|---|---|---|
| C1 | ASTER-2006 full frame | Four projects listed south to north; Jebel Ali and Jumeirah largely complete as landforms; Deira earliest stage (26, 12) | none | VISUAL_UNINSPECTED |
| C3 | ASTER-2006 Deira crop | Deira earliest stages in 2006 (26) | none; whether Deira is distinguishable in a crop is unknown | VISUAL_UNINSPECTED |
| C5 | ASTER-2006 Deira crop | same (10, 26) | none | VISUAL_UNINSPECTED |
| E2 | ISS-2022 crops of the two palm islands | NASA text: both palm-shaped islands stand out in the photograph (28) | none; crop coverage unknown | caption-supported, crops UNINSPECTED |
| C4 | none by default | claim 9 is caption text only | The World in the ISS frame is claim 33 PARTIAL and uninspected | text-card fallback |
Also dependent on these two images but outside the requested list: H3 and E5 (ISS), H4, B7 and D-act crops using ASTER 2006.

## C4 decision
Keep the safe default: text card over a labeled ASTER 2006 crop of The World only if a person confirms The World is identifiable there; otherwise a plain text card. Do not show the ISS photograph as evidence for The World until claim 33 is resolved by eye.

## Risks
- Both files are portrait (about 0.81 and 0.56 aspect). A 16:9 frame needs crops or pillarboxing; the ISS file is much taller, so a 16:9 crop uses a thin slice and may cut islands. Resolution looks adequate on paper (width 2768 to 3072 px) but is unconfirmed.
- Script C3 says "in the 2006 image, you can see how much was still ahead: Palm Deira had barely begun". This is a visual statement; caption-supported (26) but unverified by eye.
- ISS crops: NASA says the palm islands stand out, not where in the frame; crop boundaries and any alignment are unknown. No geographic boundary or pixel alignment is claimed.
- Image cropping or contrast enhancement was done by NASA on the ISS photo (claim 27): label as such if shown.

## To close
A person opens the two file URLs above (about 5 MB total), confirms: (1) Palm Jumeirah, Jebel Ali, The World and Deira are identifiable in ASTER-2006; (2) both palm islands are in the ISS frame and whether The World is; (3) which 16:9 crops work. Then script lock.
