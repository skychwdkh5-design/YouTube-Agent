# OrbitalAtlas motion engine (numpy + Pillow + FFmpeg)

Used by `../poc_c1.py`. No OpenCV, scipy, geodata or network. Run from the repo root.

## Modules
- `trace.py` land/sea contour tracing from one image: half-resolution box average, dark-water threshold (70 on the max channel for the ASTER 2006 file, chosen from a pixel profile), sea region by run-length union-find, marching squares, smoothing, Douglas-Peucker. Output polylines in full-resolution edge coordinates. Outlines belong to the pixels they were traced from; they are not survey boundaries and carry no coordinates.
- `validate.py` samples both sides of every vertex along the normal and requires a dark side of 75 or less and a bright side at least 40 levels higher; clips outlines to a project box and keeps runs that pass (score 0.7 or more). Projects that fail fall back to a focus marker.
- `motionlib.py` components below.

## Components (reusable)
| component | function | scenes it serves |
|---|---|---|
| camera path (rect-to-rect, log zoom, smoother easing, window morph from framed panel to full bleed) | `camera_at`, `make_view`, `View` | all image scenes: H1-H4, A2, B1, B2, B5-B7, C1, C3-C5, D1, D2, E2, E5 |
| image pyramid with box-resampled crops | `Pyramid` | all |
| depth background (blurred, darkened copy of the same image), vignette that skips the data window, window shadow | `depth_background`, `vignette`, `window_shadow` | panel scenes: C1 intro/outro, E1, D5, E6 |
| supersampled stroke layer with glow and window clipping | `Stroke`, `window_mask` | all overlays |
| draw-on polylines by arc length with head dot, staggered by distance | `partial`, `cumlen`, `outline()` in the scene file | B2, B5, C2, C4, C5, D1 |
| coast sweep (segment reveal by scan line) | scene file | C1, C2 |
| anchored pins with pulse ring, elbow leader, kinetic label | scene file | C1, E2, E5, A2 |
| kinetic typography (per-glyph rise and fade, optional shadow and fade-out) | `text_kinetic` | all titles, tickers |
| status chip with accent bar and growing plate | `chip` | NASA-status chips in C1, C3, C4, C5; source and legend chips everywhere |
| image-space path through anchors (Chaikin curve) | `chaikin` | C1 close, E5 |
| year ticker, timeline scrub bar, tile strip | not yet built; same primitives | B5, B6, D2, E1 |
| split compare of two separate stills | not yet built; two `Pyramid.render` calls | C6, E4 |
| typographic counter, plan ledger | not yet built; `text_kinetic` | A3, C2 |
| diagrams (dredge, GPS, vibroflot) | to be drawn with `Stroke` or yt-graphics | B3, B4 |
| stylised map flight | needs Natural Earth data (not downloaded) | A1 |

## Conventions
Source-pixel coordinates are in PIL box (edge) convention. Every annotation is defined in the pixel space of the image it sits on, so it moves with the camera. Cue times come from word index / 2.42 words per second of the locked narration until yt-voice word timings exist. Output is deterministic and video-only; yt-render can take it as a `video` asset.

## v2 additions (motionlib.py, used by ../poc_c1_v2.py)
| component | function | notes |
|---|---|---|
| continuous camera | `SplineCam` | monotone cubic (PCHIP) per channel through keys (t, cx, cy, crop height): velocity is continuous, no overshoot, rest only at the first and last key and at true turning points; log-space zoom; allows up to 15 % overscan |
| image paste with honest edges | `paste_image` | pastes the part of the image inside the view; if the view runs past the image the edge is feathered, never extended |
| motion blur on fast travel | `SplineCam.speed` plus sub-frame blending in the scene file | 2-11 samples at a 0.4-frame shutter only while the camera moves quickly; overlays stay sharp |
| selective markers | `brackets`, `crosshair` | for groups or points where individual outlines are not readable |
| title plate | `title_plate` | large title on a translucent plate with accent bar |
| collision registry | `UIREG`, `ui_reset`, scene `--ui-check` | every text or plate registers its rectangle; the check samples the timeline every 0.1 s and reports overlaps and safe-margin breaches |
| display rotation | scene file (`rot`, `rot1`) | the source can be shown rotated 90 degrees so a coast runs left to right; outlines and anchors are rotated with it and the on-screen note says so |
