#!/usr/bin/env python3
"""geostack.py - put several dates of georeferenced imagery onto exactly the same grid.

    python3 geostack.py stack.json                 # plan: check every scene covers the area
    python3 geostack.py stack.json --confirm       # write stack/<id>.png, grid.json, provenance.json
    python3 geostack.py stack.json --contact sheet.jpg --confirm

stack.json:
    {"aoi": [lon_min, lat_min, lon_max, lat_max], "pixel_m": 30, "out_dir": "stack",
     "scenes": [{"id": "y2000", "src": "raw/LE07_..._refl.tif", "label": "2000",
                 "provenance": {...}}, ...]}

Reads GeoTIFFs with Pillow only (ModelPixelScale, ModelTiepoint and the projected EPSG from the
GeoKey directory - UTM / WGS84 zones 32601-32660 and 32701-32760), projects every output pixel
to each scene's own grid and samples it bilinearly, so dates from different sensors, paths or
UTM zones line up pixel for pixel. Pixels outside a scene are refused (an area that is not fully
covered is an error, never a silent black corner). Prints JSON; no network; no credentials.

The output grid is UTM in the zone of the area's centre, north-up, pixel_m metres per pixel.
grid.json records it so a renderer can place a camera by longitude/latitude.
"""
import json, math, os, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = 400_000_000
SCHEMA = "yt-geo-stack/1"

# --- WGS84 transverse Mercator (UTM), vectorised; Snyder 1987 series -------------------------
A, F = 6378137.0, 1 / 298.257223563
E2 = F * (2 - F)
EP2 = E2 / (1 - E2)
K0 = 0.9996


class GeoError(Exception):
    def __init__(self, message, status="error"):
        super().__init__(message)
        self.status = status


def utm_zone(lon):
    return int((lon + 180) // 6) + 1


def epsg_for(lon, lat):
    return (32600 if lat >= 0 else 32700) + utm_zone(lon)


def _zone_of(epsg):
    if 32601 <= epsg <= 32660:
        return epsg - 32600, True
    if 32701 <= epsg <= 32760:
        return epsg - 32700, False
    raise GeoError(f"EPSG {epsg} is not a WGS84 UTM zone; only UTM grids are supported")


def lonlat_to_utm(lon, lat, epsg):
    zone, north = _zone_of(epsg)
    lon, lat = np.radians(np.asarray(lon, float)), np.radians(np.asarray(lat, float))
    lon0 = math.radians((zone - 1) * 6 - 180 + 3)
    n = A / np.sqrt(1 - E2 * np.sin(lat) ** 2)
    t = np.tan(lat) ** 2
    c = EP2 * np.cos(lat) ** 2
    a = np.cos(lat) * (lon - lon0)
    m = A * ((1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256) * lat
             - (3 * E2 / 8 + 3 * E2 ** 2 / 32 + 45 * E2 ** 3 / 1024) * np.sin(2 * lat)
             + (15 * E2 ** 2 / 256 + 45 * E2 ** 3 / 1024) * np.sin(4 * lat)
             - (35 * E2 ** 3 / 3072) * np.sin(6 * lat))
    x = K0 * n * (a + (1 - t + c) * a ** 3 / 6 + (5 - 18 * t + t * t + 72 * c - 58 * EP2) * a ** 5 / 120) + 500000
    y = K0 * (m + n * np.tan(lat) * (a * a / 2 + (5 - t + 9 * c + 4 * c * c) * a ** 4 / 24
                                     + (61 - 58 * t + t * t + 600 * c - 330 * EP2) * a ** 6 / 720))
    if not north:
        y = y + 10000000
    return x, y


def utm_to_lonlat(x, y, epsg):
    zone, north = _zone_of(epsg)
    x = np.asarray(x, float) - 500000
    y = np.asarray(y, float) - (0 if north else 10000000)
    lon0 = math.radians((zone - 1) * 6 - 180 + 3)
    m = y / K0
    mu = m / (A * (1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - E2)) / (1 + math.sqrt(1 - E2))
    p = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * np.sin(2 * mu) + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * np.sin(4 * mu)
         + (151 * e1 ** 3 / 96) * np.sin(6 * mu) + (1097 * e1 ** 4 / 512) * np.sin(8 * mu))
    n1 = A / np.sqrt(1 - E2 * np.sin(p) ** 2)
    t1 = np.tan(p) ** 2
    c1 = EP2 * np.cos(p) ** 2
    r1 = A * (1 - E2) / (1 - E2 * np.sin(p) ** 2) ** 1.5
    d = x / (n1 * K0)
    lat = p - (n1 * np.tan(p) / r1) * (d * d / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 * c1 - 9 * EP2) * d ** 4 / 24
                                       + (61 + 90 * t1 + 298 * c1 + 45 * t1 * t1 - 252 * EP2 - 3 * c1 * c1) * d ** 6 / 720)
    lon = lon0 + (d - (1 + 2 * t1 + c1) * d ** 3 / 6
                  + (5 - 2 * c1 + 28 * t1 - 3 * c1 * c1 + 8 * EP2 + 24 * t1 * t1) * d ** 5 / 120) / np.cos(p)
    return np.degrees(lon), np.degrees(lat)


# --- GeoTIFF -----------------------------------------------------------------------------------

def read_geotiff(path):
    """(image, info) with the pixel-to-map transform of a north-up UTM GeoTIFF."""
    try:
        im = Image.open(path)
        tags = im.tag_v2
    except (OSError, AttributeError) as e:
        raise GeoError(f"cannot read {os.path.basename(path)} as a TIFF: {e}")
    scale, tie, keys = tags.get(33550), tags.get(33922), tags.get(34735)
    if not (scale and tie and keys):
        raise GeoError(f"{os.path.basename(path)} has no GeoTIFF georeferencing tags")
    if len(tie) != 6 or tie[0] or tie[1]:
        raise GeoError(f"{os.path.basename(path)}: only a single tie point at pixel (0,0) is supported")
    geo = {keys[i]: keys[i + 3] for i in range(4, 4 * (keys[3] + 1), 4)}
    epsg = geo.get(3072)
    if not epsg:
        raise GeoError(f"{os.path.basename(path)}: no projected EPSG code (GeoKey 3072)")
    _zone_of(epsg)
    area = geo.get(1025, 1) == 1          # PixelIsArea: tie point is the pixel's corner
    return im, {"epsg": int(epsg), "x0": float(tie[3]), "y0": float(tie[4]),
                "dx": float(scale[0]), "dy": float(scale[1]), "width": im.size[0],
                "height": im.size[1], "pixel_is_area": area}


def build_grid(aoi, pixel_m):
    lon_min, lat_min, lon_max, lat_max = aoi
    if not (-180 <= lon_min < lon_max <= 180 and -84 <= lat_min < lat_max <= 84):
        raise GeoError(f"invalid aoi {aoi}")
    epsg = epsg_for((lon_min + lon_max) / 2, (lat_min + lat_max) / 2)
    xs, ys = lonlat_to_utm([lon_min, lon_max, lon_min, lon_max], [lat_min, lat_min, lat_max, lat_max], epsg)
    x0, x1 = math.floor(min(xs) / pixel_m) * pixel_m, math.ceil(max(xs) / pixel_m) * pixel_m
    y0, y1 = math.floor(min(ys) / pixel_m) * pixel_m, math.ceil(max(ys) / pixel_m) * pixel_m
    w, h = int(round((x1 - x0) / pixel_m)), int(round((y1 - y0) / pixel_m))
    if w * h > 60_000_000:
        raise GeoError(f"grid {w}x{h} is too large; raise pixel_m or shrink the aoi")
    return {"epsg": epsg, "x0": x0, "y_top": y1, "pixel_m": pixel_m, "width": w, "height": h}


def warp(im, info, grid):
    """Sample a scene onto the grid (bilinear). Returns uint8 RGB array, or raises if not covered."""
    if im.mode != "RGB":
        im = im.convert("RGB")
    src = np.asarray(im, dtype=np.float32)
    w, h, p = grid["width"], grid["height"], grid["pixel_m"]
    gx = grid["x0"] + (np.arange(w) + 0.5) * p
    gy = grid["y_top"] - (np.arange(h) + 0.5) * p
    X, Y = np.meshgrid(gx, gy)
    if info["epsg"] != grid["epsg"]:
        lon, lat = utm_to_lonlat(X, Y, grid["epsg"])
        X, Y = lonlat_to_utm(lon, lat, info["epsg"])
    off = 0.5 if info["pixel_is_area"] else 0.0
    col = (X - info["x0"]) / info["dx"] - off
    row = (info["y0"] - Y) / info["dy"] - off
    if col.min() < 0 or row.min() < 0 or col.max() > info["width"] - 1 or row.max() > info["height"] - 1:
        raise GeoError("the area is not fully inside this scene", status="not_covered")
    c0, r0 = np.floor(col).astype(int), np.floor(row).astype(int)
    c1, r1 = np.minimum(c0 + 1, info["width"] - 1), np.minimum(r0 + 1, info["height"] - 1)
    fc, fr = (col - c0)[..., None], (row - r0)[..., None]
    top = src[r0, c0] * (1 - fc) + src[r0, c1] * fc
    bot = src[r1, c0] * (1 - fc) + src[r1, c1] * fc
    out = top * (1 - fr) + bot * fr
    if (out.max(axis=2) < 3).mean() > 0.001:
        raise GeoError("the area touches the scene's no-data fill", status="not_covered")
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


# --- driver ------------------------------------------------------------------------------------

def load_spec(path):
    try:
        with open(path, encoding="utf-8") as f:
            spec = json.load(f)
    except (OSError, ValueError) as e:
        raise GeoError(f"cannot read {path}: {type(e).__name__}: {e}")
    base = os.path.dirname(os.path.abspath(path))
    for k in ("aoi", "scenes"):
        if k not in spec:
            raise GeoError(f"stack spec needs '{k}'")
    if not isinstance(spec["scenes"], list) or len(spec["scenes"]) < 1:
        raise GeoError("scenes must be a non-empty list")
    ids = [s.get("id") for s in spec["scenes"]]
    if len(set(ids)) != len(ids) or not all(isinstance(i, str) and i.replace("_", "").isalnum() for i in ids):
        raise GeoError("every scene needs a unique alphanumeric id")
    pixel = spec.get("pixel_m", 30)
    if not isinstance(pixel, (int, float)) or not 5 <= pixel <= 1000:
        raise GeoError("pixel_m must be between 5 and 1000")
    spec["pixel_m"] = float(pixel)
    for s in spec["scenes"]:
        p = os.path.realpath(os.path.join(base, s.get("src", "")))
        if os.path.commonpath([p, base]) != base or not os.path.isfile(p):
            raise GeoError(f"scene {s['id']}: src not found inside the spec folder")
        s["_path"] = p
    spec["_base"] = base
    return spec


def run(spec, confirm=False, contact=None):
    grid = build_grid(spec["aoi"], spec["pixel_m"])
    out_dir = os.path.join(spec["_base"], spec.get("out_dir", "stack"))
    plan, arrays = [], {}
    for s in spec["scenes"]:
        im, info = read_geotiff(s["_path"])
        arr = warp(im, info, grid)
        arrays[s["id"]] = arr
        plan.append({"id": s["id"], "label": s.get("label", s["id"]), "src": os.path.relpath(s["_path"], spec["_base"]),
                     "scene_epsg": info["epsg"], "scene_size": [info["width"], info["height"]]})
    result = {"status": "ok" if confirm else "confirm_required", "grid": grid, "scenes": plan}
    if not confirm:
        result["error"] = "writing the stack needs --confirm; every scene covers the area"
        return result
    os.makedirs(out_dir, exist_ok=True)
    prov = {}
    for s, p in zip(spec["scenes"], plan):
        name = f"{s['id']}.png"
        Image.fromarray(arrays[s["id"]]).save(os.path.join(out_dir, name), optimize=False)
        p["png"] = name
        prov[s["id"]] = dict(s.get("provenance") or {}, derived_png=name,
                             processing=[{"op": "reproject_resample", "method": "bilinear",
                                          "grid_epsg": grid["epsg"], "pixel_m": grid["pixel_m"]}])
    grid_doc = dict(grid, schema=SCHEMA, aoi=spec["aoi"], scenes=plan)
    with open(os.path.join(out_dir, "grid.json"), "w") as f:
        json.dump(grid_doc, f, indent=1)
    with open(os.path.join(out_dir, "provenance.json"), "w") as f:
        json.dump(prov, f, indent=1, ensure_ascii=False)
    if contact:
        contact_sheet([arrays[s["id"]] for s in spec["scenes"]], [p["label"] for p in plan],
                      os.path.join(spec["_base"], contact))
        result["contact_sheet"] = contact
    result["out_dir"] = os.path.relpath(out_dir, spec["_base"])
    return result


def contact_sheet(arrays, labels, path, tile_w=640):
    h0, w0 = arrays[0].shape[:2]
    tile_h = int(tile_w * h0 / w0)
    cols = min(3, len(arrays))
    rows = math.ceil(len(arrays) / cols)
    sheet = Image.new("RGB", (cols * tile_w, rows * tile_h), (0, 0, 0))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
    except OSError:
        font = ImageFont.load_default()
    for i, (a, lab) in enumerate(zip(arrays, labels)):
        x, y = (i % cols) * tile_w, (i // cols) * tile_h
        sheet.paste(Image.fromarray(a).resize((tile_w, tile_h), Image.LANCZOS), (x, y))
        draw.text((x + 16, y + 12), lab, font=font, fill="white", stroke_width=3, stroke_fill="black")
    sheet.save(path, quality=90)


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or "-h" in a or "--help" in a:
        print(__doc__); return 0
    try:
        contact = None
        if "--contact" in a:
            i = a.index("--contact")
            if i + 1 >= len(a): raise GeoError("--contact needs a path")
            contact = a[i + 1]
        files = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] != "--contact")]
        if len(files) != 1: raise GeoError("give exactly one stack spec")
        print(json.dumps(run(load_spec(files[0]), "--confirm" in a, contact), indent=1))
        return 0
    except GeoError as e:
        print(json.dumps({"status": e.status, "error": str(e)}, indent=1)); return 2
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"unexpected {type(e).__name__}: {e}"}, indent=1)); return 2


if __name__ == "__main__":
    sys.exit(main())
