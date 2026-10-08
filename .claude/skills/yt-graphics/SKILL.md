---
name: yt-graphics
description: >-
  Make original 16:9 documentary graphics (1920x1080 PNG) from a JSON spec - labelled scientific
  diagrams, flow diagrams, atmospheric circulation and water-cycle schematics, annotated Landsat
  imagery with callouts, coordinates and a scale bar computed from the yt-geo grid, before/after
  panels, bar and line charts and numerical callouts. Use for "make a diagram", "chart this", "explain
  this visually", "annotate the satellite image", or any explanatory visual for a long-form video.
  Output drops into a yt-render timeline v3 (profile long) as graphic assets.
---

# yt-graphics

Original explanatory visuals with their provenance on them. Local only: Pillow + NumPy, no network,
no stock or third-party artwork.

```bash
python3 graphics.py spec.json --out-dir graphics/              # every graphic in the spec
python3 graphics.py spec.json --out-dir graphics/ --only bars  # one graphic
```

Prints JSON. For each graphic it writes `<id>.png` (1920x1080, the full graphic), `<id>.stepN.png` for
build steps, and `<id>.json` (provenance, files with sha256, every text box, the scale bar). Same spec
and inputs -> the same bytes. `examples/sample_spec.json` shows every non-geographic type with
clearly labelled TEST DATA.

## Types

| type | what | key fields |
|---|---|---|
| `diagram` | boxes and labelled arrows | `nodes[] {id, text, x, y, w, h, style, step}`, `arrows[] {from, to, label, color, step}`, `notes[]` (x/y are 0-1 in the content area) |
| `flow` | a left-to-right process | `steps[]` (2-6), `arrow_labels[]`, `build` (one step at a time) |
| `circulation` | an overturning cell: rising, aloft, sinking, surface return | `labels {rising, aloft, sinking, surface}`, `ground_labels[] {x, text}`, `rising_cloud`, `build` |
| `water_cycle` | evaporation -> transport -> rainfall -> runoff | `labels {evaporation, transport, rainfall, runoff, sea, land}`, `build` |
| `geo` | annotated Landsat view | `image {stack, grid, center [lon, lat], width_km}`, `credit`, `date`, `callouts[] {at, text, step}`, `arrows[] {from, to, label, step}`, `graticule`, `scale_bar` |
| `compare` | before/after panels | `left` / `right` `{geo {...} or file, label, credit}`, `metric {left, right, unit}` |
| `bar` | bar chart | `unit`, `bars[] {label, value, highlight}`, `decimals` |
| `line` | line chart | `x_unit`, `y_unit`, `x_label`, `series[] {name, points [[x, y]...]}`, `annotations[]` |
| `callout` | one big number | `value`, `unit`, `label`, `context`, `decimals` |

Every graphic: `id` (lowercase), `source` (required), optional `title`, `subtitle`, `style`
(`documentary_dark` default, `documentary_light`), `caption_band` (default true).

The schematics draw geometry only: **all scientific wording comes from the spec's labels**, so the
claims ledger, not this tool, decides what a diagram says.

## Rules - refused rather than guessed

- **Provenance:** every graphic needs `source`; it is printed on the graphic ("Source: ...").
- **Chart data:** finite numbers only (no strings, NaN, booleans), at least one non-zero bar, x strictly
  increasing on lines, explicit units (`unit`, `x_unit`, `y_unit`).
- **Geographic scale:** a scale bar and coordinate labels need the yt-geo `grid.json` with a UTM `epsg`
  and `pixel_m`; without them the graphic is refused (`"status": "no_scale"`). The bar length is the
  longest 1/2/5 x 10^n km (or m) that fits, from the real metres per pixel of that view - never assumed.
  Distances are on the UTM grid (scale error well under 1 % within a zone).
- **Text:** each label shrinks to a minimum size and wraps to its allowed lines; if it still does not fit
  the graphic is refused (`"status": "overflow"`). Every text box must sit inside the landscape safe
  area (5 % sides, 7 % top, 13 % bottom) and, with `caption_band`, above the burned-in caption band
  (74 % of the height). A 44 px band under the top edge is left for yt-render's shot credit.
- Views that leave the imagery, callouts outside the view and paths outside the spec folder are refused.

## In a LONG timeline (yt-render v3)

```json
"assets": {"hadley1": {"src": "graphics/hadley.step1.png", "kind": "graphic", "credit": "Graphic: YouTube-Agent · NASA", "group": "hadley"},
           "hadley":  {"src": "graphics/hadley.png", "kind": "graphic", "credit": "Graphic: YouTube-Agent · NASA", "group": "hadley"}},
"shots": [{"id": "explain", "start": {"word": 40}, "visual_family": "circulation_diagram",
           "layers": [{"type": "graphic", "asset": "hadley1"},
                      {"type": "graphic", "asset": "hadley", "t": [3.0, null]}]}]
```

- A shot whose first layer is a graphic at `t = 0` needs no camera (a **graphics shot**); it may add
  labels but no map layers. A graphic layer with a `t` window in a map shot is a timed **insert**
  (0.35 s fade-in). Build steps are separate graphic layers with later `t`.
- Graphic assets must be exactly the profile's output size (1920x1080 for `long`) and carry a `credit`.
- Composition rules: a new graphic is a composition reset; its build steps (same `group`) are not;
  leaving a graphic back to the imagery is. Visual families work as on any shot.

## The gate

Nothing here publishes. The last line of every run is the question: **check the numbers and labels
against the claims ledger, or change the spec?**
