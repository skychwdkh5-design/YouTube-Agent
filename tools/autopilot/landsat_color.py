#!/usr/bin/env python3
"""landsat_color.py - calibrated natural-colour stills from Landsat Level-1 band files, mosaicked onto one yt-geo grid.

    python3 tools/autopilot/landsat_color.py plan  SPEC.json
    python3 tools/autopilot/landsat_color.py build SPEC.json [--contact sheet.jpg]

Why not the browse image: the USGS browse GeoTIFF/JPEG is stretched per scene, so tones differ between dates and tiles of one mosaic show
seams. Here every pixel gets the SAME physical curve ("tone B" of EP001, docs/production-knowledge): TOA reflectance
r = (DN * REFLECTANCE_MULT_BAND_n + REFLECTANCE_ADD_BAND_n) / sin(sun elevation)  (both read from the scene's MTL file), then
colour = clip((r - 0.02) / 0.58, 0, 1) ** (1 / 1.8). It is a display curve, not a measurement; the same curve is used for every sensor and date.

SPEC.json: {"aoi": [lon_min, lat_min, lon_max, lat_max], "pixel_m": 60, "out_dir": "stack", "bands_dir": "bands",
            "scenes": [{"id": "y2022", "label": "July 2022",
                        "tiles": ["LC09_L1TP_038031_20220728_..._T1", ...],   # priority order: the first tile with real data wins a pixel
                        "provenance": {...}}]}
Per tile the files <bands_dir>/<displayId>_B4.TIF, _B3.TIF, _B2.TIF (OLI, LC08/LC09) or _B3, _B2, _B1 (TM/ETM+, LT04/LT05/LE07) and
<displayId>_MTL.txt must exist (usgs_m2m.py download-bands). Outputs: <out_dir>/<id>.png, grid.json (yt-geo-stack/1), provenance.json.

Rules: no blending, so no pixel is invented; every pixel of the AOI must be covered by some tile; the black collar of a scene (DN = 0) and a few
pixels inside it are never copied, which removes the bright seam line the browse mosaic had. Mosaic tiles may come from adjacent days (neighbouring
paths): this is written into provenance. Pure NumPy + Pillow, no network.
"""
import json, math, os, re, sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), ".claude", "skills", "yt-geo"))
import geostack as g  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
RGB_BANDS = {"LC08": (4, 3, 2), "LC09": (4, 3, 2), "LT04": (3, 2, 1), "LT05": (3, 2, 1), "LE07": (3, 2, 1)}
TONE = {"lo": 0.02, "span": 0.58, "gamma": 1.8}
EDGE_PX = 3                                   # grid pixels dropped around the no-data collar of a scene


class ColorError(Exception):
    pass


def parse_mtl(path):
    with open(path, encoding="utf-8") as f: t = f.read()
    def num(k):
        m = re.search(r"\b" + k + r"\s*=\s*([-0-9.Ee+]+)", t)
        if not m: raise ColorError(f"{os.path.basename(path)} has no {k}")
        return float(m.group(1))
    date = re.search(r"DATE_ACQUIRED\s*=\s*(\S+)", t)
    return {"sun_elevation": num("SUN_ELEVATION"), "date": date.group(1) if date else None, "text": t, "num": num}


def tone_b(refl):
    return np.clip((refl - TONE["lo"]) / TONE["span"], 0, 1) ** (1 / TONE["gamma"])


def sample_band(path, grid, mult, add, sun_elev):
    """One band on the grid: (reflectance float32 array, valid bool array). Bilinear; a pixel is valid only if every neighbour it blends is real data."""
    im, info = g.read_geotiff(path)
    dn = np.asarray(im)
    if dn.ndim != 2: raise ColorError(f"{os.path.basename(path)} is not a single-band raster")
    dn = dn.astype(np.float32)
    real = (dn > 0).astype(np.float32)
    w, h, p = grid["width"], grid["height"], grid["pixel_m"]
    gx = grid["x0"] + (np.arange(w) + 0.5) * p
    gy = grid["y_top"] - (np.arange(h) + 0.5) * p
    X, Y = np.meshgrid(gx, gy)
    if info["epsg"] != grid["epsg"]:
        lon, lat = g.utm_to_lonlat(X, Y, grid["epsg"])
        X, Y = g.lonlat_to_utm(lon, lat, info["epsg"])
    off = 0.5 if info["pixel_is_area"] else 0.0
    col = (X - info["x0"]) / info["dx"] - off
    row = (info["y0"] - Y) / info["dy"] - off
    inside = (col >= 0) & (row >= 0) & (col <= info["width"] - 1) & (row <= info["height"] - 1)
    cc, rr = np.clip(col, 0, info["width"] - 1), np.clip(row, 0, info["height"] - 1)
    c0, r0 = np.floor(cc).astype(int), np.floor(rr).astype(int)
    c1, r1 = np.minimum(c0 + 1, info["width"] - 1), np.minimum(r0 + 1, info["height"] - 1)
    fc, fr = cc - c0, rr - r0
    def bil(a): return (a[r0, c0] * (1 - fc) + a[r0, c1] * fc) * (1 - fr) + (a[r1, c0] * (1 - fc) + a[r1, c1] * fc) * fr
    v = bil(dn); ok = bil(real)
    valid = inside & (ok > 0.9999)
    for _ in range(EDGE_PX):                                     # erode: the collar is dark and bilinear blending leaks it inwards
        e = valid.copy()
        e[1:, :] &= valid[:-1, :]; e[:-1, :] &= valid[1:, :]; e[:, 1:] &= valid[:, :-1]; e[:, :-1] &= valid[:, 1:]
        valid = e
    refl = ((v * mult + add) / math.sin(math.radians(sun_elev))).astype(np.float32)
    return refl, valid


def tile_rgb(bands_dir, display_id, grid):
    sensor = display_id[:4]
    if sensor not in RGB_BANDS: raise ColorError(f"unsupported sensor {sensor} in {display_id}")
    mtl_path = os.path.join(bands_dir, f"{display_id}_MTL.txt")
    if not os.path.isfile(mtl_path): raise ColorError(f"missing {display_id}_MTL.txt")
    mtl = parse_mtl(mtl_path)
    chans, valid = [], None
    for b in RGB_BANDS[sensor]:
        path = os.path.join(bands_dir, f"{display_id}_B{b}.TIF")
        if not os.path.isfile(path): raise ColorError(f"missing {display_id}_B{b}.TIF")
        refl, v = sample_band(path, grid, mtl["num"](f"REFLECTANCE_MULT_BAND_{b}"), mtl["num"](f"REFLECTANCE_ADD_BAND_{b}"), mtl["sun_elevation"])
        chans.append(tone_b(refl)); valid = v if valid is None else valid & v
    rgb = (np.dstack(chans) * 255 + 0.5).astype(np.uint8)
    return rgb, valid, {"displayId": display_id, "date": mtl["date"], "sun_elevation_deg": mtl["sun_elevation"], "bands": [f"B{b}" for b in RGB_BANDS[sensor]]}


def mosaic(bands_dir, tiles, grid):
    out = np.zeros((grid["height"], grid["width"], 3), np.uint8)
    have = np.zeros((grid["height"], grid["width"]), bool)
    used = []
    for did in tiles:
        rgb, valid, meta = tile_rgb(bands_dir, did, grid)
        take = valid & ~have
        out[take] = rgb[take]; have |= valid
        meta["pixels_used_pct"] = round(float(take.mean()) * 100, 2)
        used.append(meta)
    if not have.all():
        raise ColorError(f"the area is not fully covered by the {len(tiles)} tile(s): {(~have).mean() * 100:.2f} % of the grid has no data")
    return out, used


def load_spec(path):
    with open(path, encoding="utf-8") as f: spec = json.load(f)
    base = os.path.dirname(os.path.abspath(path))
    for k in ("aoi", "scenes"):
        if k not in spec: raise ColorError(f"spec needs '{k}'")
    spec["_base"] = base
    spec["_bands"] = os.path.join(base, spec.get("bands_dir", "bands"))
    spec["pixel_m"] = float(spec.get("pixel_m", 60))
    return spec


def plan(spec):
    grid = g.build_grid(spec["aoi"], spec["pixel_m"])
    missing = []
    for s in spec["scenes"]:
        for did in s["tiles"]:
            if did[:4] not in RGB_BANDS: missing.append(f"{did}: unsupported sensor"); continue
            for b in RGB_BANDS[did[:4]]:
                if not os.path.isfile(os.path.join(spec["_bands"], f"{did}_B{b}.TIF")): missing.append(f"{did}_B{b}.TIF")
            if not os.path.isfile(os.path.join(spec["_bands"], f"{did}_MTL.txt")): missing.append(f"{did}_MTL.txt")
    return {"ok": not missing, "grid": grid, "scenes": len(spec["scenes"]), "missing_files": missing}


def build(spec, contact=None):
    grid = g.build_grid(spec["aoi"], spec["pixel_m"])
    out_dir = os.path.join(spec["_base"], spec.get("out_dir", "stack"))
    os.makedirs(out_dir, exist_ok=True)
    arrays, prov, plan_rows = [], {}, []
    for s in spec["scenes"]:
        arr, used = mosaic(spec["_bands"], s["tiles"], grid)
        Image.fromarray(arr).save(os.path.join(out_dir, f"{s['id']}.png"), optimize=False)
        arrays.append(arr)
        dates = sorted({u["date"] for u in used if u["date"]})
        prov[s["id"]] = dict(s.get("provenance") or {}, derived_png=f"{s['id']}.png", tiles=used,
                             acquisition_dates=dates, days_between_tiles=(int((np.datetime64(dates[-1]) - np.datetime64(dates[0])).astype(int)) if len(dates) > 1 else 0),
                             processing=[{"op": "toa_reflectance", "formula": "(DN*MULT+ADD)/sin(sun_elevation), from MTL"},
                                         {"op": "tone_B", "formula": "clip((r-0.02)/0.58,0,1)**(1/1.8)"},
                                         {"op": "reproject_resample", "method": "bilinear", "grid_epsg": grid["epsg"], "pixel_m": grid["pixel_m"]},
                                         {"op": "mosaic", "rule": "first tile with real data wins; no blending", "edge_px_dropped": EDGE_PX}])
        plan_rows.append({"id": s["id"], "label": s.get("label", s["id"]), "png": f"{s['id']}.png", "tiles": [u["displayId"] for u in used]})
    with open(os.path.join(out_dir, "grid.json"), "w") as f:
        json.dump(dict(grid, schema=g.SCHEMA, aoi=spec["aoi"], scenes=plan_rows), f, indent=1)
    with open(os.path.join(out_dir, "provenance.json"), "w") as f:
        json.dump(prov, f, indent=1, ensure_ascii=False)
    res = {"ok": True, "out_dir": out_dir, "grid": grid, "scenes": plan_rows}
    if contact:
        g.contact_sheet(arrays, [r["label"] for r in plan_rows], os.path.join(spec["_base"], contact))
        res["contact_sheet"] = contact
    return res


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) < 2 or a[0] not in ("plan", "build"):
        print(__doc__); return 2
    try:
        spec = load_spec(a[1])
        r = plan(spec) if a[0] == "plan" else build(spec, a[a.index("--contact") + 1] if "--contact" in a else None)
    except (ColorError, g.GeoError, OSError, ValueError, KeyError) as x:
        print(json.dumps({"ok": False, "error": f"{type(x).__name__}: {x}"})); return 2
    print(json.dumps(r, indent=1, default=str)); return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
