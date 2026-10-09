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
