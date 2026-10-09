# Known limitations and failed approaches

## Failed / rejected (do not repeat)
| approach | outcome |
|---|---|
| Custom vector globe (`orbitalatlas.geo`) as the EP002 look | works technically, **not visually approved**; far below the references (no imagery, no relief, no tilt/perspective) |
| Cesium + GIBS only (proof V1) | real imagery and perspective camera work, but: blocky ocean/coast patches where Landsat WELD has no data over Blue Marble; half-black skybox on frame 0; flat ellipsoid (no terrain without ion); ~38 m/pixel at L12 so city streets and buildings are unreadable; WELD default date 2000-12-01 may predate modern Dubai (year unverified); render incomplete in 9 min |
| Landsat/GIBS + flat 2D city rendering as final EP002 style | **not approved** by the user |
| Google Photorealistic 3D Tiles | prohibited for documentary video (see ASSET_SOURCE_REGISTRY) |
| Cesium ion, Google Earth Studio | paid for monetised use / not operable on iPad |

## Current hard limits
- No GPU; WebGL is software (SwiftShader), slow; npm/pip generally blocked (jsdelivr reachable, registry.npmjs.org DNS fails).
- No free sub-metre imagery source identified; Sentinel-2/WELD/HLS (≈10–38 m) cannot give reference-level city detail alone.
- No free photoreal 3D buildings identified. Terrain: no source verified.
- Image-space zoom is not a 3D flyover; never fake continuity (see Visual Master).

## Open candidates (NOT yet tested; Phase 2 must investigate and decide autonomously within zero budget)
1. 3D approach with open data: Three.js or CesiumJS (no ion) + GIBS/Landsat imagery + open DEM + extruded OSM/Overture buildings. Need: reachable hosts, licences read, benchmark.
2. Blender (headless) + open DEM/imagery: needs a reachable download; not tested.
3. Hybrid: real 3D globe/camera for Earth→region only, then `orbitalatlas` motion graphics over real Landsat evidence stills with honest class labels.
Selection criteria: reference-level look (QA checklist), legal for monetised video, zero cost, renders in a few minutes on CPU, automatable.
