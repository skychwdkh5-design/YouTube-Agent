# Known limitations and failed approaches

## Failed / rejected (do not repeat)
| approach | outcome |
|---|---|
| Custom vector globe (`orbitalatlas.geo`) as the EP002 look | works technically, **not visually approved**; far below the references (no imagery, no relief, no tilt/perspective) |
| Cesium + GIBS only (proof V1) | real imagery and perspective camera work, but: blocky ocean/coast patches where Landsat WELD has no data over Blue Marble; half-black skybox on frame 0; flat ellipsoid (no terrain without ion); ~38 m/pixel at L12 so city streets and buildings are unreadable; WELD default date 2000-12-01 may predate modern Dubai (year unverified); render incomplete in 9 min |
| Landsat/GIBS + flat 2D city rendering as final EP002 style | **not approved** by the user |
| Google Photorealistic 3D Tiles | prohibited for documentary video (see ASSET_SOURCE_REGISTRY) |
| Cesium ion, Google Earth Studio | paid for monetised use / not operable on iPad |

| Cesium + GIBS with improved layering, static visual gate (Phase 2, 2026-10-09) | close-up Dubai (lon 55.20, lat 25.15, range 14 km, pitch -50, 1280x720): **FAIL**. Config A (Blue Marble + Landsat WELD L12): coast and roads visible but soft ~38 m pixels, no recognisable landmarks, mosaic looks older than modern Dubai (content year unverified), visible tile-boundary tint over the sea. Config B (Blue Marble + VIIRS L9 + HLS L12, 2026-10-07): blurry mush, no usable detail. Checklist A3/A4/D2 FAIL, so no motion proof was rendered |

## Current hard limits
- No GPU; WebGL is software (SwiftShader), slow; npm/pip generally blocked (jsdelivr reachable, registry.npmjs.org DNS fails).
- No free sub-metre imagery source identified; Sentinel-2/WELD/HLS (≈10–38 m) cannot give reference-level city detail alone.
- No free photoreal 3D buildings identified. Terrain: no source verified.
- Image-space zoom is not a 3D flyover; never fake continuity (see Visual Master).

## Phase 3: spotlight hand-off proof (2026-10-09)
Design in `productions/dubai/motion/transition_proof/DESIGN.md`. Result: the hand-off device works (no black edges, matched coast orientation, honest chips; `orbitalatlas.qa.run_video` ok) but the Cesium close frames are soft and still show a smudge where the Palm is not yet in the WELD layer; keying the sea out of Landsat WELD (`colorToAlpha`) removed the swath stripes but leaves speckle. Status VISUALLY_REVIEWED at best, below the references on A3/D2.

## Phase 2 conclusion (2026-10-09)
The renderer is not the bottleneck; **free reachable data is**. Hosts tested and blocked (HTTP 403 via proxy): overpass-api.de, overpass.kumi.systems, tile.openstreetmap.org, overturemaps-us-west-2.s3.amazonaws.com, elevation-tiles-prod.s3.amazonaws.com, copernicus-dem-30m.s3.amazonaws.com, planetarycomputer.microsoft.com, earth-search.aws.element84.com, sentinel-cogs.s3.us-west-2.amazonaws.com, download.blender.org, raw.githubusercontent.com, unpkg.com, cdnjs.cloudflare.com (github.com returned 400). Only GIBS (<=38 m) and USGS Landsat (30 m, 15 m pan; large scene downloads) remain, which cannot reach reference-level city detail. Photoreal Dubai close-ups from free, legally usable data are not currently obtainable; a creative decision (hybrid, below) or an allowlist for open buildings/DEM hosts is required. Do not re-test these hosts; re-check one only if the user says the allowlist changed.

## Open candidates (NOT yet tested; Phase 2 must investigate and decide autonomously within zero budget)
1. 3D approach with open data: Three.js or CesiumJS (no ion) + GIBS/Landsat imagery + open DEM + extruded OSM/Overture buildings. Need: reachable hosts, licences read, benchmark.
2. Blender (headless) + open DEM/imagery: needs a reachable download; not tested.
3. Hybrid: real 3D globe/camera for Earth→region only, then `orbitalatlas` motion graphics over real Landsat evidence stills with honest class labels.
Selection criteria: reference-level look (QA checklist), legal for monetised video, zero cost, renders in a few minutes on CPU, automatable.

## Delivery and QA findings (2026-10-10)
- A copy of our exports reported by the user as 910x512 at 30 fps matches a re-encode to 512 px height at 30 fps (`scale=-2:512,fps=30` reproduces exactly 910x512@30 from both the 1280x720 and the 960x540 files). Treat chat previews as lossy; verify the original with ffprobe + SHA-256 (the Artifact page recomputes the hash in the browser).
- `orbitalatlas.qa.run_video` resamples to 30 fps and mislabels frame duplication as discontinuities; use `productions/dubai/preview/qa_preview.py` (native fps, duplicate-aware) for any non-30 fps render.
- Never paint or fill missing satellite data (V1 A1 coloured the Landsat swath deep-sea blue and lifted blacks; removed). Audit crops with `qa_rects.py`.
- Hand-placed callout coordinates were off by up to ~36 px (Palm site (350, 1637) vs fitted (364, 1669)); use `landmarks.py` outputs.

## EP002 V6 (2026-10-13)
- Delivered proof files are re-encoded by the chat/file viewer (user saw 910x512, 30 fps, other SHA-256 for an original 960x540, 24 fps file; original SHA-256 15fd288e... for the V6 hook proof). Byte identity of a viewed copy cannot be claimed; compare against the SHA-256 in the message. VERIFIED locally (ffprobe of the original).
- Outlines in V6 scenes are thresholded sea/land masks of the frame they sit on (colour distance from a sea-only patch; thresholds 38 for ASTER 2000-2011, 110 for ASTER 2006). They follow image pixels, not surveyed coastlines; cloud/shallow-water pixels can leak (checked by eye). Shorelines are traced only where rows >= 1090 in the 2000 frame (creek and clouds above). Fills/tints/arrows are UI explanations and labelled.
- No scale bars, distances or coordinates: ASTER/ISS frames have no verified georeference (claim 32).
- Registration of ASTER 2000 vs 2003 measured by phase correlation (<= 1 px at 6 land patches); 2011 and 2002 frames are assumed to share the grid (same product) but were not measured.
- All cue times in scenes are ESTIMATED (145 wpm); replace with provider word timings after TTS.


## Visual engine v2 (2026-10-14)
See `docs/references/library/IMPLEMENTATION_STATUS.md`: class-A camera only; no flag/cloth, outline type, colour cards, noise glitch; storyboard generator not yet wired to `semantic.plan`; test voice is not the channel voice; Shorts layout not reviewed.

## EP003 quality pass (2026-10-15)
- Pronunciation cannot be checked in the cloud container: no ASR model, pypi.org and huggingface.co are denied by the egress policy. Only word durations from the provider alignment are available as indirect evidence.
- Traced shoreline masks are display aids (seeded growth on a 1/4-resolution stack), not surveys; mosaic seams can leave straight edges in a mask (EP003 1985, Bear River Bay).
- The director still renders geo shots only (no video/still shots, no NASA SVS time-lapse); snow imagery for winter 2022-2023 was not available on the stack, so that passage shows the July 2022 image with the shoreline overlays.
- A ~1 s pause can occur at a TTS chunk join (EP003 253.1-254.1 s); it is kept when it falls on a sentence boundary, because trimming would shift every later word timing.

## EP004 S3 V2 3-D illustration (2026-10-15)
- `orbitalatlas.scene3d` is a painter renderer (no z-buffer): ordering = stage, then mean depth. Big polygons (a whole cut face) must sit in their own stage or they cover details drawn on them; polygons crossing the near plane are dropped (keep geometry in front of the camera). No textures, shadows or anti-aliasing beyond 2x supersampling.
- The reference videos VISUAL_REF_001/002 are not in the repository, any branch, or the owner's Google Drive (searched 2026-10-15): comparisons are against the written analyses, never frame-to-frame.
- The cloud session's disk allowance can run out although `df` shows space: `git fetch` of all `media/*` branches made `.git` 8.8 GB; delete scratch rasters (or fetch only needed branches) before long renders.

## Shorts EP002/EP003 (2026-10-15)
- NASA World of Change frames are not re-registered: Shorts compare them by beat cuts and separate side-by-side panels, never by a wipe (VERIFIED by inspection).
- Tilted evidence planes (`shorts.tilted_view`) are flat pictures in perspective, not terrain; label anchors are as good as their source pixel positions (Dubai 2006 positions hand-placed).
- Procedural music (`orbitalatlas.music`) is one electronic style; sound is checked by meter and cue timetable, not by ear, in a cloud session.
- Private GitHub repository creation from this session failed: `403 Resource not accessible by integration` (needs owner action/permission).
