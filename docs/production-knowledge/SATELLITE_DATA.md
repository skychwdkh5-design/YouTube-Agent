# Satellite data and geographic honesty
Sources and licences: `docs/ASSET_SOURCE_REGISTRY.md` (check first; do not re-investigate). Evidence rules: `productions/dubai/motion/MOTION_DESIGN_SYSTEM.md`, `/yt-geographic-animation`.
## What each source is
- **ASTER on Terra (NASA Earth Observatory images)**: satellite imagery; EP002 uses 12 frames 2000-2011 (3000x3000 "cyl" JPEGs, colours as published, false-colour) + ASTER 2006 `palm2.jpg` (3072x3797). Label: instrument + date ("colours as published"). Month only where NASA's captions give it; 2011 = year only **[EP002]**.
- **ISS astronaut photograph (Nikon D4, NASA, cropped/contrast-enhanced)**: a photograph, **not satellite imagery**; the chip says so. Do not narrate content beyond what NASA's caption says (EP002 claim 33: The World is not described as visible).
- **NASA GIBS + CesiumJS** for a globe descent: free, works from this container via `tools/cesium_proof` (jsdelivr and gibs reachable, SwiftShader WebGL). Real tiles only; coarse at close range (about 38 m/px closest frames) **[VERIFIED]**.
## Registration and measurement **[VERIFIED]**
- ASTER 2000 vs 2003: phase correlation of 512 px land patches at 6 places: shift <= 1 px (peaks 0.07-0.29); coast agrees within 4 px. This justified dissolve + difference outline. 2011 and 2002 frames: same product, grid sharing **assumed, not measured**.
- ASTER vs ISS vs ASTER 2006: **never** registered or overlaid; compare side by side, labelled; the 2006 frame is a different file/grid.
- No pixel is painted; fills/tints are UI layers.
## Forbidden **[RULE]**
Scale bars, distances, areas, coordinates on ASTER/ISS frames (no verified georeference); invented coastlines/borders (use `orbitalatlas.geo` + Natural Earth for maps); statements about the present from older imagery ("nothing assumed since 2022").
## Limits of traced outlines **[VERIFIED]**
They follow image pixels (thresholds, clouds, shallow water can leak), not surveyed coastlines; they are labelled "traced from this image".
