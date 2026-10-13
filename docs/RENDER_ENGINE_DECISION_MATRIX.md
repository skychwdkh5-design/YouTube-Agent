# Render engine decision matrix
Audited in the cloud container on 2026-10-09 (4 CPU, 15 GB RAM, no GPU). **No PyPI/npm access** (DNS fails
from pip and npm; proxy blocks arbitrary hosts), so nothing can be installed here without a user-approved
network allowlist change. Re-run the audit if the environment changes.

| tool | installed | supports | headless | network | GPU | licence | fits pipeline | verdict |
|---|---|---|---|---|---|---|---|---|
| Python 3.13 + NumPy 2.5 + Pillow 12 | yes | per-pixel compositing, masks, curves, text | yes | no | no | open | current engine | KEEP (core) |
| FFmpeg 6.1 (libx264/265, libass, xfade, zoompan, geq, perspective, vidstab, blackdetect) | yes | encode, mux, subtitles, loudness, QC; xfade transitions | yes | no | no (nvenc listed, no GPU) | LGPL/GPL build | final stage | KEEP; do not use zoompan (jitter, stills only) for hero motion |
| ImageMagick 6 (`convert`) | yes | stills ops | yes | no | no | open | marginal | ignore |
| Node 22, npm | yes | runs JS | yes | npm DNS fails | no | — | — | usable only with vendored code |
| Playwright 1.56 + Chromium 1194 | yes | HTML/CSS/SVG/Canvas/WebGL1+WebGL2 (software SwiftShader), screenshots/frames | yes (WebGL1 and WebGL2 verified 2026-10-09, see RENDER_BENCHMARKS) | no | software only (slow) | open | possible renderer for SVG/CSS animation and Three.js if the library is vendored | CANDIDATE for SVG text/vector layers; frame-by-frame capture is slow; needs a spike |
| OpenCV, SciPy, scikit-image | NO | remap, warps, fast filters, morphology | — | pip blocked | — | BSD | — | not available; NumPy replaces what is needed now |
| pyproj/GDAL/rasterio/shapely | NO | CRS transforms, georeferencing | — | pip blocked | — | MIT/X | — | needed for class B; blocked. Pure-numpy projections (Mercator, UTM formulas, orthographic) are feasible for display |
| matplotlib/cairosvg/skia | NO | vector charts/SVG raster | — | blocked | — | — | — | Chromium can rasterise SVG instead |
| Blender | NO | real 3D, terrain, cameras | yes | needs install | CPU ok | GPL | class C | not installable now; heavy; only if a DEM story justifies it |
| Remotion | NO (npm blocked) | React video with Chromium | yes | npm | no | **commercial licence terms for companies** | would replace our compositor | REJECT for now (licence + install + duplicates engine) |
| Three.js | NO | WebGL 3D | via Chromium | npm | software | MIT | class C light | CANDIDATE only if vendored by user-approved download |
| MapLibre GL JS | NO | vector tiles, map camera | via Chromium | needs tiles (network) | software | BSD | class B | CANDIDATE; tiles need network allowlist; OSM tile fetch returned 403 |
| deck.gl / CesiumJS | CesiumJS loadable from cdn.jsdelivr.net (no npm); proof V1 rendered | 3D globe, perspective camera | via Chromium | jsdelivr OK; GIBS OK; ion needs token (paid for monetised use) | software, 0.27 fps aggregate at 720p | MIT/Apache (engine) | class C | WORKS as a renderer without ion; visual quality limited by free data (see KNOWN_LIMITATIONS); candidate for Earth→region shots only |
| yt-render (`.claude/skills/yt-render`) | yes | Ken Burns stills, crossfades, subtitles | yes | no | no | repo | long-form docs from stills | KEEP for QC/mux and simple scenes; NOT for hero motion |
| yt-geo / yt-graphics | yes | Landsat co-registered stacks, diagrams, scale bars | yes | USGS for data | no | repo | class A with real georef | KEEP; integrate for Landsat-based episodes |

## Recommended minimum stack
1. **NumPy+Pillow compositor** (existing engine, promoted to a shared package) for class A hero motion, transitions, typography.
2. **FFmpeg** for encode/mux/subs/loudness/QC only.
3. **yt-geo** for anything claiming georegistered change over time (Landsat).
4. **Optional spike, needs approval**: Chromium (already installed) as an SVG/vector-text layer renderer; and pure-numpy
   map projections for class B locator maps from a Natural Earth file the user approves downloading (or supplies).
5. Not recommended: Blender, Remotion, Cesium, deck.gl.
## Validating rendered output (any engine)
Contact sheet at 4 fps · blackdetect · frame-diff motion per second · overlay residual check · word-time vs reveal-frame check.

## Update 2026-10-09 (supersedes the lines above where they conflict)
- Network changed after the user allowlisted hosts: cdn.jsdelivr.net, Cesium hosts, GIBS, NASA/Google doc pages are reachable; registry.npmjs.org still fails DNS. Chromium WebGL2 works in software (RENDER_BENCHMARKS).
- Cesium rejection above is withdrawn as a *renderer* decision only; Cesium ion, Google 3D Tiles and Earth Studio are excluded by licence/cost (ASSET_SOURCE_REGISTRY).
- No engine has yet met the reference look with free data. Phase 2 must test the open candidates in KNOWN_LIMITATIONS and choose by `REFERENCE_VISUAL_QA_CHECKLIST.md`. Blender and Three.js remain untested here.
