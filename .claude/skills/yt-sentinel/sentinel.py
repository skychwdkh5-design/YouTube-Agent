#!/usr/bin/env python3
"""yt-sentinel: free Sentinel-2 L2A (10 m) stacks for a video, via Planetary Computer.

STAC search + the Planetary Computer *data API* (crop/resample/npy). No credentials. The asset buckets
(sentinel-cogs S3, blob storage) are blocked in the cloud sandbox, the data API is not.
Every command prints JSON; errors are structured, never tracebacks. Nothing is substituted silently:
a year without a suitable scene is reported as missing.
"""
import argparse, datetime, hashlib, io, json, math, os, sys, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "yt-geo"))
PC = "https://planetarycomputer.microsoft.com/api"
COLLECTION = "sentinel-2-l2a"
LICENSE = {"name": "Copernicus Sentinel data - free, full and open (EU Reg. 1159/2013)", "commercial_use": True}


class SentinelError(Exception):
    def __init__(self, msg, status="error"):
        super().__init__(msg)
        self.status = status


def _post(url, body, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise SentinelError(f"STAC request failed: {e}", "network")


def stac_search(bbox, start, end, cloud_max=5.0, limit=200):
    """Normalised items: id, date, cloud, nodata, orbit, tile, platform, baseline."""
    body = {"collections": [COLLECTION], "bbox": list(bbox), "limit": limit,
            "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z", "query": {"eo:cloud_cover": {"lt": cloud_max}}}
    out = []
    for f in _post(PC + "/stac/v1/search", body).get("features", []):
        p = f["properties"]
        out.append({"id": f["id"], "date": p["datetime"][:10], "datetime": p["datetime"], "cloud": round(p["eo:cloud_cover"], 3),
                    "nodata": p.get("s2:nodata_pixel_percentage"), "orbit": p.get("sat:relative_orbit"),
                    "tile": f["id"].split("_")[-3] if "_T" in f["id"] else None, "platform": p.get("platform"),
                    "baseline": p.get("s2:processing_baseline")})
    return sorted(out, key=lambda i: i["date"])


def _tile(item_id):
    for part in item_id.split("_"):
        if part.startswith("T") and len(part) == 6:
            return part
    return None


def pick_per_year(items, years, month_day=("10-01", "10-31"), max_cloud=3.0, max_nodata=10.0):
    """One scene per year: same relative orbit and tile for every year, lowest cloud, closest to mid-window.

    Returns {"picks": {year: item}, "missing": [years], "orbit": n, "tile": t, "notes": [...]}.
    """
    notes, cand = [], {}
    for it in items:
        y = int(it["date"][:4])
        if y not in years or not (month_day[0] <= it["date"][5:] <= month_day[1]):
            continue
        if it["cloud"] > max_cloud or (it["nodata"] is not None and it["nodata"] > max_nodata):
            continue
        it = dict(it, tile=it.get("tile") or _tile(it["id"]))
        cand.setdefault((it["orbit"], it["tile"]), {}).setdefault(y, []).append(it)
    if not cand:
        return {"picks": {}, "missing": sorted(years), "orbit": None, "tile": None, "notes": ["no scene meets the limits"]}
    # the (orbit, tile) combination covering the most years, then the lowest mean cloud
    def key(k):
        by = cand[k]
        best = [min(v, key=lambda i: i["cloud"]) for v in by.values()]
        return (-len(by), sum(i["cloud"] for i in best) / len(best))
    orbit, tile = min(cand, key=key)
    mid = datetime.date(2000, int(month_day[0][:2]), int(month_day[0][3:])).toordinal() + \
        (datetime.date(2000, int(month_day[1][:2]), int(month_day[1][3:])).toordinal() -
         datetime.date(2000, int(month_day[0][:2]), int(month_day[0][3:])).toordinal()) // 2
    picks = {}
    for y, v in cand[(orbit, tile)].items():
        def dist(i):
            d = datetime.date.fromisoformat(i["date"])
            return abs(datetime.date(2000, d.month, d.day).toordinal() - mid)
        picks[y] = min(v, key=lambda i: (round(i["cloud"], 1), dist(i)))
    alts = {}
    for y in picks:
        pool = [i for (o, t), by in cand.items() for i in by.get(y, []) if i["id"] != picks[y]["id"]]
        alts[y] = sorted(pool, key=lambda i: (i["orbit"] != orbit, i["tile"] != tile, i["cloud"]))
    missing = sorted(y for y in years if y not in picks)
    if missing:
        notes.append(f"no scene on orbit {orbit} / tile {tile} for {missing}; not substituted")
    bl = sorted({p["baseline"] for p in picks.values() if p["baseline"]})
    if len(bl) > 1:
        notes.append(f"processing baselines differ ({bl[0]}..{bl[-1]}): tone and reflectance offset can differ; use indices only for baselines >= 04.00 with the +1000 offset removed")
    return {"picks": picks, "missing": missing, "orbit": orbit, "tile": tile, "notes": notes, "alts": alts}


def utm_grid(aoi, pixel_m=10, snap=20):
    snap = max(snap, pixel_m)
    import numpy as np, geostack as g
    lon0, lat0, lon1, lat1 = aoi
    epsg = g.epsg_for((lon0 + lon1) / 2, (lat0 + lat1) / 2)
    xs, ys = g.lonlat_to_utm(np.array([lon0, lon1, lon0, lon1]), np.array([lat0, lat0, lat1, lat1]), epsg)
    x0, x1 = math.floor(min(xs) / snap) * snap, math.ceil(max(xs) / snap) * snap
    y0, y1 = math.floor(min(ys) / snap) * snap, math.ceil(max(ys) / snap) * snap
    w, h = int((x1 - x0) / pixel_m), int((y1 - y0) / pixel_m)
    if w * h > 40_000_000:
        raise SentinelError(f"grid {w}x{h} too large; raise pixel_m or shrink the aoi")
    return {"schema": "yt-geo-stack/1", "epsg": int(epsg), "x0": float(x0), "y_top": float(y1), "pixel_m": float(pixel_m),
            "width": w, "height": h, "aoi": list(aoi), "_bounds": [x0, y0, x1, y1]}


def crop_url(item_id, grid, assets="visual", fmt="png", band=None):
    x0, y0, x1, y1 = grid["_bounds"]
    q = f"collection={COLLECTION}&item={item_id}&assets={assets}&nodata=0&coord_crs=EPSG:{grid['epsg']}&dst_crs=EPSG:{grid['epsg']}"
    q += f"&asset_bidx={assets}|{band or '1,2,3'}"
    return f"{PC}/data/v1/item/bbox/{x0},{y0},{x1},{y1}/{grid['width']}x{grid['height']}.{fmt}?{q}"


def _get(url, timeout=240):
    try:
        return urllib.request.urlopen(url, timeout=timeout).read()
    except (urllib.error.URLError, OSError) as e:
        raise SentinelError(f"data API request failed: {e}", "network")


def build_stack(picks, aoi, out_dir, pixel_m=10, overwrite=False, alts=None):
    """Write <out_dir>/y<year>.png on one UTM grid + grid.json + provenance.json (sha256, licence, credit)."""
    from PIL import Image
    import numpy as np
    os.makedirs(out_dir, exist_ok=True)
    grid = utm_grid(aoi, pixel_m)
    scenes, prov = [], []
    for y in sorted(picks):
        path = os.path.join(out_dir, f"y{y}.png")
        if os.path.exists(path) and not overwrite:
            raise SentinelError(f"{path} exists (use --overwrite)", "exists")
        tried, im = [], None
        for it in [picks[y]] + list((alts or {}).get(y, [])):
            cand = Image.open(io.BytesIO(_get(crop_url(it["id"], grid))))
            a = np.asarray(cand)
            if a.shape[-1] == 4 and (a[..., 3] == 0).mean() > 0.001:
                tried.append(it["id"])         # does not cover the AOI: the next candidate is tried and the substitution is recorded
                continue
            im = cand
            break
        if im is None:
            raise SentinelError(f"no scene for {y} covers the AOI; tried {tried}", "not_covered")
        tmp = path + ".part"
        im.convert("RGB").save(tmp, format="PNG")
        os.replace(tmp, path)
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        scenes.append({"id": f"y{y}", "label": str(y), "png": f"y{y}.png", "src": f"Sentinel-2 L2A TCI {it['id']}",
                       "scene_epsg": grid["epsg"], "scene_size": [grid["width"], grid["height"]]})
        prov.append({"id": f"y{y}", "itemId": it["id"], "datetime": it["datetime"], "platform": it["platform"], "cloud_cover": it["cloud"],
                     "relative_orbit": it["orbit"], "processing_baseline": it["baseline"], "sha256": sha, "license": LICENSE,
                     "credit": f"Contains modified Copernicus Sentinel data {y}", "source": "Microsoft Planetary Computer STAC + data API",
                     "processing": "bbox crop and resample by titiler to a UTM grid, TCI visual asset, no pan-sharpening",
                     "rejected_for_coverage": tried})
    g = {k: v for k, v in grid.items() if not k.startswith("_")}
    g["scenes"] = scenes
    for name, obj in (("grid.json", g), ("provenance.json", {"schema": "yt-geo-stack-provenance/1", "grid": "grid.json", "scenes": prov})):
        tmp = os.path.join(out_dir, name + ".part")
        json.dump(obj, open(tmp, "w"), indent=1)
        os.replace(tmp, os.path.join(out_dir, name))
    return {"out_dir": out_dir, "grid": g, "scenes": [p["id"] for p in prov]}


def ndwi_check(item_id, bbox_lonlat, size=(352, 178)):
    """Water-likeness of dark pixels: NDWI = (B03-B08)/(B03+B08) with the +1000 offset removed (baseline >= 04.00).

    A shadow is dark in every band and has NDWI <= 0; standing water has NDWI > 0 and very low B08.
    Returns counts only - it never names the object.
    """
    import numpy as np
    def band(b):
        x0, y0, x1, y1 = bbox_lonlat
        u = (f"{PC}/data/v1/item/bbox/{x0},{y0},{x1},{y1}/{size[0]}x{size[1]}.npy?collection={COLLECTION}&item={item_id}&assets={b}&asset_bidx={b}|1")
        return (np.load(io.BytesIO(_get(u)))[0].astype(float) - 1000) / 10000
    g, n = band("B03"), band("B08")
    ndwi = (g - n) / (g + n + 1e-6)
    water = (ndwi > 0) & (n < 0.05)
    cols = np.where(water.any(axis=0))[0]
    m_per_px = (bbox_lonlat[2] - bbox_lonlat[0]) * 111320 * math.cos(math.radians((bbox_lonlat[1] + bbox_lonlat[3]) / 2)) / size[0]
    return {"item": item_id, "extent_km": round(float((cols.max() - cols.min() + 1) * m_per_px / 1000), 2) if len(cols) else 0.0, "water_like_px": int(water.sum()), "mean_ndwi": round(float(ndwi[water].mean()), 3) if water.any() else None,
            "mean_b08": round(float(n[water].mean()), 4) if water.any() else None,
            "interpretation": "counts only: consistent with standing water if > 0, not proof; a shadow gives NDWI <= 0"}


def ndwi_series(provenance_path, bbox, out_path, min_baseline="04.00"):
    """NDWI counts for every scene of a stack -> evidence/ndwi.json. Baselines < 04.00 are skipped (different reflectance offset), recorded as null."""
    prov = json.load(open(provenance_path))["scenes"]
    years = {}
    for sc in prov:
        y = sc["id"][1:]
        if (sc.get("processing_baseline") or "00") < min_baseline:
            years[y] = {"water_like_px": None, "note": f"baseline {sc.get('processing_baseline')} < {min_baseline}: not comparable"}
            continue
        r = ndwi_check(sc["itemId"], bbox)
        years[y] = {k: r[k] for k in ("water_like_px", "mean_ndwi", "mean_b08", "extent_km")}
        years[y]["item"] = sc["itemId"]
    out = {"schema": "yt-sentinel-ndwi/1", "bbox": list(bbox), "method": "NDWI=(B03-B08)/(B03+B08), offset 1000 removed; water-like = NDWI>0 and B08<0.05", "years": years}
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    json.dump(out, open(out_path + ".part", "w"), indent=1)
    os.replace(out_path + ".part", out_path)
    return out


def _aoi(s):
    v = [float(x) for x in s.split(",")]
    if len(v) != 4 or not (v[0] < v[2] and v[1] < v[3]):
        raise SentinelError("--aoi must be minlon,minlat,maxlon,maxlat")
    return v


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("search", "pick", "stack"):
        p = sub.add_parser(name)
        p.add_argument("--aoi", required=True)
        p.add_argument("--years", required=True, help="e.g. 2020,2022,2026")
        p.add_argument("--window", default="09-20:11-10", help="MM-DD:MM-DD season window each year")
        p.add_argument("--cloud", type=float, default=3.0)
        if name == "stack":
            p.add_argument("--out", required=True)
            p.add_argument("--pixel-m", type=float, default=10)
            p.add_argument("--overwrite", action="store_true")
            p.add_argument("--confirm", action="store_true", help="download (free); without it only the plan is shown")
    p = sub.add_parser("ndwi")
    p.add_argument("--item", required=True)
    p.add_argument("--bbox", required=True)
    p = sub.add_parser("ndwi-series")
    p.add_argument("--provenance", required=True)
    p.add_argument("--bbox", required=True)
    p.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "ndwi":
            return _out(ndwi_check(a.item, _aoi(a.bbox)))
        if a.cmd == "ndwi-series":
            return _out({"status": "ok", **ndwi_series(a.provenance, _aoi(a.bbox), a.out)})
        aoi = _aoi(a.aoi)
        years = sorted(int(y) for y in a.years.split(","))
        w0, w1 = a.window.split(":")
        items = []
        for y in years:
            items += stac_search(aoi, f"{y}-{w0}", f"{y}-{w1}", max(a.cloud, 5.0))
        if a.cmd == "search":
            return _out({"status": "ok", "items": items})
        pk = pick_per_year(items, years, (w0, w1), a.cloud)
        if a.cmd == "pick":
            return _out({"status": "ok" if not pk["missing"] else "partial", **pk})
        if pk["missing"]:
            return _out({"status": "partial", "error": f"missing years {pk['missing']}", **pk}, 2)
        if not a.confirm:
            return _out({"status": "confirm_required", "note": "download is free; add --confirm", **pk})
        return _out({"status": "ok", **build_stack(pk["picks"], aoi, a.out, a.pixel_m, a.overwrite, pk["alts"]), "notes": pk["notes"]})
    except SentinelError as e:
        return _out({"status": e.status, "error": str(e)}, 1)


def _out(obj, code=0):
    print(json.dumps(obj, indent=1, default=str))
    return code


if __name__ == "__main__":
    sys.exit(main())
