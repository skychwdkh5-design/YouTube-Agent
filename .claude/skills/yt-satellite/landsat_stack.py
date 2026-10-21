#!/usr/bin/env python3
"""landsat_stack.py - build a co-registered Landsat stack from a yt-geo stack spec: download each scene's georeferenced natural-colour browse GeoTIFF (free, ~5 MB, USGS EROS M2M)
and run yt-geo on it. Idempotent: files already present are kept.

    python3 landsat_stack.py --spec research/landsat_stack.json --root productions/<slug> [--confirm]

The spec is the yt-geo stack.json (aoi, pixel_m, out_dir, scenes[] with provenance.entityId). Without --confirm nothing is downloaded: the plan (what would be fetched) is printed.
Credit on screen: "Landsat imagery courtesy of the U.S. Geological Survey" (public domain, commercial use allowed).
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
M2M = os.path.join(HERE, "usgs_m2m.py")
GEO = os.path.join(HERE, "..", "yt-geo", "geostack.py")
PRODUCT = "Full-Resolution Browse (Natural Color) GeoTIFF"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--spec", required=True); ap.add_argument("--root", default="."); ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args(argv)
    spec_path = os.path.join(a.root, a.spec)
    spec = json.load(open(spec_path))
    raw_dir = os.path.join(a.root, "evidence", "landsat_raw")
    todo = []
    for s in spec["scenes"]:
        dst = os.path.join(raw_dir, os.path.basename(s["src"]))
        todo.append({"id": s["id"], "entityId": s["provenance"]["entityId"], "file": os.path.relpath(dst, a.root), "have": os.path.exists(dst)})
    if not a.confirm:
        print(json.dumps({"status": "confirm_required", "to_download": [t for t in todo if not t["have"]], "have": [t["id"] for t in todo if t["have"]], "product": PRODUCT}, indent=1))
        return 0
    os.makedirs(raw_dir, exist_ok=True)
    for t in todo:
        if t["have"]:
            continue
        r = subprocess.run([sys.executable, M2M, "download", "--entity", t["entityId"], "--product", PRODUCT, "--out", raw_dir, "--confirm"], capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
        except ValueError:
            d = {"status": "error", "error": (r.stderr or r.stdout)[-300:]}
        if d.get("status") != "ok":
            print(json.dumps({"status": "error", "scene": t["id"], "error": d.get("error") or d.get("status")})); return 1
    ev = os.path.abspath(os.path.join(a.root, "evidence"))              # yt-geo resolves src and out_dir relative to the spec's folder
    local = dict(spec, scenes=[dict(s, src=os.path.join("landsat_raw", os.path.basename(s["src"]))) for s in spec["scenes"]], out_dir="landsat")
    local_spec = os.path.join(ev, "landsat_stack.resolved.json")
    json.dump(local, open(local_spec, "w"), indent=1)
    r = subprocess.run([sys.executable, GEO, local_spec, "--confirm"], capture_output=True, text=True)
    print(r.stdout[-1500:] if r.returncode == 0 else json.dumps({"status": "error", "error": (r.stderr or r.stdout)[-400:]}))
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
