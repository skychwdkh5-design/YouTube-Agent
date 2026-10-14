#!/usr/bin/env python3
"""shoreline_masks.py - water masks of a lake on one co-registered stack, for 'shoreline then/now' outlines and 'exposed lake bed' fills.

    python3 tools/autopilot/shoreline_masks.py SLUG --years 1986,2022 --seeds "Gunnison Bay,Gilbert Bay" --box -113.15,41.8,-111.85,40.62 \
        [--extra-seeds -112.25,41.35;-112.6,41.55] [--reject-reddish 1986] [--factor 4] [--max-luma 135] [--max-std 9]

Seeded region growing (orbitalatlas.regions.seeded_region) from named stack pins inside a lon/lat box, on a 1/factor copy of each
calibrated stack image. --reject-reddish YEAR excludes red-brown land (R > B + 6 and R >= G) before growing - use it for a year whose
lake is blue/green; never for a year with pink brine (Gunnison Bay 2022). Writes assets/geo/water_yYEAR.png (255 = water, 1/factor
resolution) + .json (method, params, missed seeds, water fraction). A display aid traced from real imagery, not a survey: an area
spoken about it needs its own source. Look at the overlay before using a mask (the tool also writes a check JPEG). Prints JSON.
"""
# effect-reuse-checked: reuses regions.seeded_region and the director Geo grid; yt-geo watermask.py thresholds failed on the calibrated EP003 stack (land classed as water)
import argparse, json, os, sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from orbitalatlas import regions  # noqa: E402
from orbitalatlas.director import Geo  # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def build(prod, years, seed_names, box, extra=(), reject=(), factor=4, max_luma=135, max_std=9.0):
    tl = json.load(open(os.path.join(prod, "timeline.json"))); grid = json.load(open(os.path.join(prod, tl["grid"])))
    st = (json.load(open(os.path.join(prod, "assets", "manifest.json"))).get("stacks") or [{}])[0]; pins = st.get("pins") or {}
    g = Geo(grid, (1920, 1080)); f = factor
    pts = [pins[n] for n in seed_names] + list(extra)
    (bx0, by0), (bx1, by1) = g.px(box[:2]), g.px(box[2:])
    os.makedirs(os.path.join(prod, "assets", "geo"), exist_ok=True); out = []
    for y in years:
        aid = f"y{y}"; im = Image.open(os.path.join(prod, tl["assets"][aid]["src"])).convert("RGB")
        sm = np.asarray(im.resize((im.width // f, im.height // f), Image.LANCZOS)).copy()
        if str(y) in reject:
            a = sm.astype(int); sm[(a[..., 0] > a[..., 2] + 6) & (a[..., 0] >= a[..., 1])] = 255
        seeds = [(g.px(p)[0] / f, g.px(p)[1] / f) for p in pts]
        m = regions.seeded_region(sm, seeds, max_luma=max_luma, max_std=max_std, box=(bx0 / f, by0 / f, bx1 / f, by1 / f), close=2, max_hole_px=300)
        path = os.path.join(prod, "assets", "geo", f"water_y{y}.png"); Image.fromarray((m * 255).astype(np.uint8)).save(path)
        info = dict(schema="orbitalatlas-shoreline/1", source=tl["assets"][aid]["src"], mask=os.path.relpath(path, prod), factor=f,
                    method="seeded region growing from stack pins inside a lon/lat box" + (" after excluding red-brown land" if str(y) in reject else ""),
                    params=dict(max_luma=max_luma, max_std=max_std, box=box, seeds=seed_names, extra_seeds=list(extra)),
                    missed_seeds=[list(s) for s in regions.seeded_region.last_missed], water_fraction=round(float(m.mean()), 5),
                    note="display aid traced from imagery; not a survey measurement")
        json.dump(info, open(path[:-4] + ".json", "w"), indent=1)
        chk = np.asarray(im.resize((im.width // f, im.height // f))).copy(); chk[m] = (chk[m] * 0.45 + np.array([0, 200, 255]) * 0.55).astype(np.uint8)
        Image.fromarray(chk).save(path[:-4] + "_check.jpg", quality=80); out.append(info)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("slug"); ap.add_argument("--years", required=True); ap.add_argument("--seeds", required=True)
    ap.add_argument("--box", required=True); ap.add_argument("--extra-seeds", default=""); ap.add_argument("--reject-reddish", default="")
    ap.add_argument("--factor", type=int, default=4); ap.add_argument("--max-luma", type=int, default=135); ap.add_argument("--max-std", type=float, default=9.0)
    a = ap.parse_args(argv); prod = a.slug if os.path.isdir(a.slug) else os.path.join(ROOT, "productions", a.slug)
    extra = [tuple(float(v) for v in s.split(",")) for s in a.extra_seeds.split(";") if s.strip()]
    res = build(prod, [y.strip() for y in a.years.split(",")], [s.strip() for s in a.seeds.split(",")], [float(v) for v in a.box.split(",")],
                extra, [y.strip() for y in a.reject_reddish.split(",") if y.strip()], a.factor, a.max_luma, a.max_std)
    print(json.dumps(dict(ok=True, masks=res), indent=1))


if __name__ == "__main__":
    main()
