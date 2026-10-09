# Asset source registry (persistent; reuse, do not re-investigate)

Last audit: 2026-10-09 (network allowlist of that session; re-check one host with a single `curl -sI` before relying on it).
Status: **VERIFIED** = read in an official source (URL given) · **ASSUMED** = from memory, not read · **PROHIBITED** · **BLOCKED** = could not read the terms.
Budget rule: zero. A source needing payment, a subscription or a credit-card key is excluded unless the user explicitly changes the rule.

## Allowed (free, commercial documentary use plausible)
| source | what | access | licence / use | attribution | status |
|---|---|---|---|---|---|
| NASA GIBS WMTS `gibs.earthdata.nasa.gov` (epsg3857 `best/`) | global imagery tiles. Layers seen: `BlueMarble_NextGeneration` (L8, jpeg), `VIIRS_SNPP_CorrectedReflectance_TrueColor` (L9, daily), `Landsat_WELD_CorrectedReflectance_TrueColor_Global_Annual` (L12, default date 2000-12-01, year of content NOT verified), `HLS_S30_Nadir_BRDF_Adjusted_Reflectance` (L12, daily, png) | no token; HTTP 200 | NASA "full and open sharing of data" with industry and the public (https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-information-guidance). NASA content used factually, without implying endorsement, needs no permission (https://www.nasa.gov/nasa-brand-center/images-and-media/). Layer-specific terms for WELD/Blue Marble/VIIRS **not read** | "NASA must be acknowledged as source": credit "NASA GIBS" + layer provider on screen/description; no NASA logos | VERIFIED (general NASA policy) / ASSUMED (per-layer) |
| USGS Landsat via `/yt-satellite` (`earthexplorer.usgs.gov`) | Landsat scenes, 30 m | existing skill; USGS login in repo setup | USGS credit policy page returned 403, not read; Landsat is generally public domain (**ASSUMED**) | "Landsat imagery courtesy of NASA / U.S. Geological Survey" (**ASSUMED** wording) | ASSUMED |
| Natural Earth (`tools/fetch_natural_earth.sh`) | coastlines, borders (1:10M) | script in repo | public domain per project notes | optional | VERIFIED in repo notes, not re-read |

## Prohibited or not usable
| source | reason | evidence |
|---|---|---|
| Google Photorealistic 3D Tiles (Map Tiles API) | Video allowed only as "promotional" ≤ 30 s about the customer's app, labelled "for promotional purposes only"; no pre-fetch/cache/storage; no offline use | https://developers.google.com/maps/documentation/tile/policies (read 2026-10-09). Pricing also not zero: Photorealistic 3D Tiles SKU 1,000 free/month then $6 per 1,000 (https://developers.google.com/maps/billing-and-pricing/pricing). Exclude until Google gives written permission |
| Cesium ion Community account for monetised video | Community = non-commercial personal projects or exploratory development; Commercial plan $149/month | https://cesium.com/platform/cesium-ion/pricing (read). Cesium World Imagery/Terrain/OSM Buildings through ion need a token; excluded under zero budget |
| Google Earth Studio | cannot run on the user's only device (iPad); terms not read (domain unreachable) | user constraint |
| Sentinel-2 as a substitute for sub-metre imagery | 10 m cannot give reference-level city detail | user decision |

## Unverified / blocked (do not use until read)
| source | state |
|---|---|
| Esri World Imagery, Airbus Pléiades, Planet SkySat, Maxar Open Data | official pages blocked by the network allowlist; every claim about coverage/price/licence is an assumption. Sub-metre Dubai imagery under a free commercial licence: **none identified** |
| EOX Sentinel-2 cloudless (`tiles.maps.eox.at`) | host returned 403; licence believed non-commercial in some editions (ASSUMED) |
| Copernicus DEM / AWS Terrain Tiles (terrain) | not tested: hosts not allowlisted or not checked; terms not read |
| OpenStreetMap / Overture buildings | not tested; ODbL/attribution assumed |

## Network facts (2026-10-09)
Reachable: cdn.jsdelivr.net, cesium.com, api.cesium.com (405), assets.ion.cesium.com (401, token), gibs.earthdata.nasa.gov, earthexplorer.usgs.gov, developers.google.com, cloud.google.com, www.earthdata.nasa.gov, www.nasa.gov.
Blocked or failing then: registry.npmjs.org (DNS), tiles.maps.eox.at, services.arcgisonline.com, basemaps.cartocdn.com, www.usgs.gov (403), esri/airbus/planet/maxar pages, earth.google.com. Web fetch tool has no network; use `curl` in Bash (proxy trusted via /root/.ccr/ca-bundle.crt).

Phase 2 host check (2026-10-09, all HTTP 403 from the proxy): overpass-api.de, tile.openstreetmap.org, overturemaps S3, AWS terrain-tiles and Copernicus DEM S3, planetarycomputer.microsoft.com, earth-search (element84), sentinel-cogs S3, download.blender.org, raw.githubusercontent.com, unpkg.com, cdnjs. Open buildings, open DEM and Blender are therefore unreachable until the user allowlists them.
