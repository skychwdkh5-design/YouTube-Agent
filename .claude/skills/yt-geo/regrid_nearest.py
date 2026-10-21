#!/usr/bin/env python3
"""regrid_nearest.py - put a coarser stack onto a finer stack's grid WITHOUT interpolation: every target pixel takes the value of the source pixel that contains its centre.

    python3 regrid_nearest.py --source evidence/landsat --target evidence/stack --out evidence/landsat10

Both folders hold yt-geo output (grid.json + <id>.png + provenance.json), same UTM zone. A 30 m source on a 10 m target becomes flat 30 m blocks: no detail is added, no smoothing.
The provenance is carried over with one extra processing step that says so. Pixels outside the source are refused (never a silent border).
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image


def regrid(src_dir, tgt_dir, out_dir):
    sg = json.load(open(os.path.join(src_dir, "grid.json")))
    tg = json.load(open(os.path.join(tgt_dir, "grid.json")))
    if sg["epsg"] != tg["epsg"]:
        raise SystemExit(f"different UTM zones ({sg['epsg']} vs {tg['epsg']}): reproject with geostack first")
    xs = tg["x0"] + (np.arange(tg["width"]) + 0.5) * tg["pixel_m"]
    ys = tg["y_top"] - (np.arange(tg["height"]) + 0.5) * tg["pixel_m"]
    cols = np.floor((xs - sg["x0"]) / sg["pixel_m"]).astype(int)
    rows = np.floor((sg["y_top"] - ys) / sg["pixel_m"]).astype(int)
    if cols.min() < 0 or rows.min() < 0 or cols.max() >= sg["width"] or rows.max() >= sg["height"]:
        raise SystemExit("the target grid is not fully covered by the source grid")
    prov_in = json.load(open(os.path.join(src_dir, "provenance.json")))
    os.makedirs(out_dir, exist_ok=True)
    prov = {}
    for sid, p in prov_in.items():
        im = np.asarray(Image.open(os.path.join(src_dir, p["derived_png"])).convert("RGB"))
        out = im[rows][:, cols]
        Image.fromarray(out).save(os.path.join(out_dir, p["derived_png"]))
        prov[sid] = dict(p, processing=list(p.get("processing", [])) + [{"op": "regrid_nearest", "from_pixel_m": sg["pixel_m"], "to_grid_pixel_m": tg["pixel_m"],
                                                                           "note": "no interpolation: source pixels shown as flat blocks; this is NOT an increase of detail"}])
    json.dump(dict(tg, scenes=[{"id": k, "png": v["derived_png"], "native_pixel_m": sg["pixel_m"]} for k, v in prov.items()]), open(os.path.join(out_dir, "grid.json"), "w"), indent=1)
    json.dump(prov, open(os.path.join(out_dir, "provenance.json"), "w"), indent=1)
    return {"status": "ok", "out": out_dir, "scenes": list(prov), "native_pixel_m": sg["pixel_m"], "grid_pixel_m": tg["pixel_m"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", required=True); ap.add_argument("--target", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    print(json.dumps(regrid(a.source, a.target, a.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
