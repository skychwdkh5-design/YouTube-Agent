# True 3-D pipeline (pbrt-v4 + OIDN) — OrbitalAtlas

Status: VERIFIED in EP004 S3 V3 (2026-10-15). Use it for any scene that must be real 3-D (geometry, perspective camera, light transport);
`orbitalatlas.scene3d` stays the fast flat-shaded 2.5-D illustrator. Do not call scene3d output "3-D rendering".

## Why pbrt-v4 and not Blender
- Blender is the first choice, but in the cloud container the network policy blocks `download.blender.org`, PyPI (`bpy`) and Ubuntu mirrors
  (only github.com reachable). VERIFIED 2026-10-15 (proxy 403 on download.blender.org; pip "Tunnel connection failed: 403").
  To use Blender: the owner adds `download.blender.org` under Allowed domains of the environment's network access.
- pbrt-v4 (Apache-2.0, github.com/mmp/pbrt-v4) is a physically based path tracer: real meshes and quadrics, thin-lens camera (depth of field),
  animated camera transforms (true motion blur), measured metal spectra, image textures + bump maps, area lights, physical sky
  (`imgtool makesky`, Hosek-Wilkie). Soft/contact shadows, AO and indirect light come from path tracing.
- Intel OIDN 2.3.3 (Apache-2.0) denoises with albedo + normal guides (gbuffer film), which allows 8-16 spp.

## Build (about 15 min, 4 cores)
`tools/pbrt3d/build_toolchain.sh [DIR]` — clones pbrt-v4 with submodules, stubs the interactive viewer (no X11/OpenGL dev files in the
container: GLFW needs RandR/Wayland headers), builds `pbrt` + `imgtool`, downloads OIDN. Export `PBRT_BIN` and `OIDN_BIN`.

## Use
`orbitalatlas/pbrt3d.py`: `Scene` (camera with eye1/target1 for motion blur, `sun_sky`, `texture`, `material`, `mesh`, `shape`), geometry helpers
(`box`, `grid` height field, `strip` cut-face, `tube`, `merge`), `make_sky`, `render`, `load_frame` (EXR -> PFM -> OIDN -> un-mirror; returns
HDR + camera distance), `finish` (white balance, depth haze, bloom, ACES filmic, grade, vignette), `project` (2-D labels on 3-D points).
Reference production: `productions/ep004-jakarta/proof_v3/` (`scene_v3.py`, `run_v3.py batch A B W H SPP TAG`, `compose_v3.py`).

## Pitfalls found (all VERIFIED)
1. `Scale -1 1 1` (the usual mirror fix) + `ActiveTransform` camera = blank frames (negative scale breaks the animated transform). No Scale;
   flip the image left-right in post (`load_frame` does it).
2. `makesky` leaves the lower hemisphere black: a black saw-tooth wedge shows where the ground plane meets the horizon. `make_sky` fills it
   with the horizon colour; also extend ground planes far (60 km).
3. Low warm sun + ACES turned beige clay into red: white-balance in post against the illuminant (`wb`), keep albedo textures neutral.
4. Emissive particles in front of a lit surface cast black shadows. Draw particles in post, projected through the same camera and
   depth-tested against the rendered distance (`compose_v3.drops`).
5. `coateddiffuse` is ~30 % slower than `diffuse`; use it only on small hero objects. Path depth 3 vs 5 made no difference: cost is the
   camera samples (~1.2 s per spp at 960x540 on 4 cores for a 3,000-building city + textured strata).
6. Lens shift (V2 style) = offset `screenwindow` on the perspective camera.

## Cost (this container: 4 cores, no GPU) — see docs/RENDER_BENCHMARKS.md
960x540 @ 8 spp + motion blur + OIDN: ~12-14 s/frame. 1280x720 @ 12 spp: see benchmarks. Plan 3-5 s tests first; full 13.5 s proofs take hours.
