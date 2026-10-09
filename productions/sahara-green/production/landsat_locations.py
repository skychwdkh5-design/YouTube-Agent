#!/usr/bin/env python3
"""EP001 Landsat location stills.

Two source types:
  * band   - Level-1 B2/B3/B4 from the USGS M2M "Band File" product. TOA reflectance = (DN*2e-5-0.1)/sin(sun elevation);
             tone B of the visual lock: clip((r-0.02)/0.58,0,1)**(1/1.8). Native 30 m pixels, no resampling.
  * browse - USGS 8-bit natural-colour browse GeoTIFF. Display only: per-channel 1-99.5 percentile stretch over the valid
             (non-collar) pixels. NOT tone B, NOT radiometrically comparable with the locked sequences.
Usage: landsat_locations.py overview <key> | build <key>
"""
import json, os, re, sys, hashlib
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", ".claude", "skills", "yt-geo"))
import geostack as g
SCR = os.environ.get("EP001_SCRATCH", "/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad/loc")
OUT = os.path.join(HERE, "stills")
LOC = {
 "ounianga": {"type": "band", "scene": "LC09_L1TP_182047_20260622_20260622_02_T1", "dir": SCR + "/src/LC09_L1TP_182047_20260622_20260622_02_T1",
              "centre": (19.0, 20.55), "w": 3000, "note": "Lakes of Ounianga, Chad (Ounianga Kebir 19.05N 20.47E; Ounianga Serir 18.9N 20.7E)"},
 "bodele": {"type": "band", "scene": "LC09_L1TP_183048_20260731_20260731_02_T1", "dir": SCR + "/src/LC09_L1TP_183048_20260731_20260731_02_T1",
            "centre_px": (4200, 5000), "w": 5000, "note": "Bodele Depression, Chad"},

 "tassili": {"type": "band", "scene": "LC09_L1TP_190042_20251220_20251220_02_T1", "dir": SCR + "/src/LC09_L1TP_190042_20251220_20251220_02_T1",
             "centre_px": (2800, 3900), "w": 4200, "note": "Tassili n'Ajjer sandstone plateau and canyons, Algeria"},
 "gilf": {"type": "band", "scene": "LC09_L1TP_179044_20251121_20251121_02_T1", "dir": SCR + "/src/LC09_L1TP_179044_20251121_20251121_02_T1",
          "centre": (23.3, 26.0), "w": 3600, "note": "Gilf Kebir plateau, Egypt"},
 "kufra": {"type": "band", "scene": "LC09_L1TP_181043_20260919_20260919_02_T1", "dir": SCR + "/src/LC09_L1TP_181043_20260919_20260919_02_T1",
           "centre": (24.20, 23.50), "w": 3600, "note": "Kufra agricultural fields, Libya (placed by georeferenced coordinates; see kufra_alignment.json)"},
}
BROWSE_DIR = SCR.replace("/loc", "") + "/landsat_work/extra"
def mtl(d, scene):
    t = open(os.path.join(d, scene + "_MTL.txt")).read()
    f = lambda k: float(re.search(k + r"\s*=\s*([-0-9.Ee+]+)", t).group(1))
    return f("SUN_ELEVATION"), re.search(r'DATE_ACQUIRED = (\S+)', t).group(1), re.search(r'SCENE_CENTER_TIME = "([^"]+)"', t).group(1)
def load_band(path):
    im, info = g.read_geotiff(path); return np.asarray(im, np.uint16), info
def toneB(dn, sun):
    r = (dn.astype(np.float32) * 2e-5 - 0.1) / np.sin(np.radians(sun))
    return (np.clip((r - 0.02) / 0.58, 0, 1) ** (1 / 1.8) * 255 + 0.5).astype(np.uint8)
def build(key, overview=False):
    L = LOC[key]
    if L["type"] == "band":
        sun, date, t = mtl(L["dir"], L["scene"])
        bands = {b: load_band(f"{L['dir']}/{L['scene']}_B{b}.TIF") for b in (4, 3, 2)}
        info = bands[4][1]
        valid = bands[4][0] > 0
        rgb = np.dstack([toneB(bands[b][0], sun) for b in (4, 3, 2)]); rgb[~valid] = 0
    else:
        raw = np.asarray(Image.open(f"{SCR}/nat/{L['scene']}.jpg").convert("RGB")); valid = raw.sum(2) > 30
        if L["file"]:                                                               # georeferencing from the browse GeoTIFF (same pixel grid)
            _, info = g.read_geotiff(f"{BROWSE_DIR}/{L['file']}")
            assert raw.shape[1] == info["width"] and raw.shape[0] == info["height"], "JPEG and GeoTIFF grids differ"
        else:                                                                       # no GeoTIFF reachable (HTTP 504): place by the visible pivot fields
            info = {"epsg": None, "dx": 30.0, "dy": 30.0, "x0": None, "y0": None}
        sun, date, t = None, re.search(r"_(\d{8})_\d{8}_02_T1", L["scene"]).group(1), None
        rgb = raw.copy()                                                           # USGS natural-colour browse as delivered, no stretch
        rgb[~valid] = 0
    if overview:
        Image.fromarray(rgb).resize((1000, int(1000 * rgb.shape[0] / rgb.shape[1])), Image.LANCZOS).save(f"{SCR}/ov_{key}.png"); return
    if "centre_px" in L:
        cx, cy = L["centre_px"]
    else:
        x, y = g.lonlat_to_utm(L["centre"][1], L["centre"][0], info["epsg"])
        cx, cy = (x - info["x0"]) / info["dx"], (info["y0"] - y) / info["dy"]
    w = L["w"]; h = int(w * 9 / 16)
    ii = np.pad(valid.astype(np.int64).cumsum(0).cumsum(1), ((1, 0), (1, 0)))        # nearest all-valid window to the wanted centre
    def full(a, b_):
        return a >= 0 and b_ >= 0 and a + w <= valid.shape[1] and b_ + h <= valid.shape[0] and \
               ii[b_ + h, a + w] - ii[b_, a + w] - ii[b_ + h, a] + ii[b_, a] == w * h
    cands = sorted(((dx, dy) for dx in range(-3000, 3001, 25) for dy in range(-2000, 2001, 25)), key=lambda d: d[0] ** 2 + d[1] ** 2)
    x0 = y0 = None
    for dx, dy in cands:
        a, b_ = int(round(cx - w / 2)) + dx, int(round(cy - h / 2)) + dy
        if full(a, b_):
            x0, y0 = a, b_; break
    assert x0 is not None, "no all-valid window of that size"
    print("centre px", round(cx), round(cy), "window origin", x0, y0, "target offset in window", round(cx - x0), round(cy - y0))
    crop = rgb[y0:y0 + h, x0:x0 + w]
    assert (valid[y0:y0 + h, x0:x0 + w]).all(), "crop includes the black collar"
    os.makedirs(OUT, exist_ok=True)
    p = f"{OUT}/{key}_toneB.png"; Image.fromarray(crop).save(p)
    ul = g.utm_to_lonlat(info["x0"] + x0 * info["dx"], info["y0"] - y0 * info["dy"], info["epsg"]) if info["epsg"] else (None, None)
    rec = {"key": key, "kind": "landsat_toneB_crop", "scene": L["scene"], "date_acquired": (date if "-" in str(date) else f"{date[:4]}-{date[4:6]}-{date[6:]}"), "scene_center_time_utc": t, "sun_elevation": sun,
           "epsg": info["epsg"], "pixel_m": info["dx"], "src_window_px": [x0, y0, w, h], "ul_lonlat": ([round(ul[0], 5), round(ul[1], 5)] if ul[0] is not None else None), "georeferenced": bool(info["epsg"]), "note": L["note"],
           "bands": "B4,B3,B2 (red,green,blue)", "processing": ("TOA reflectance, tone B (lock), native 30 m pixels, no resampling, black collar excluded" if L["type"] == "band" else
                          "USGS 8-bit Natural Color browse JPEG as delivered (no stretch)" + ("; georeferenced with the browse GeoTIFF of the same scene" if info["epsg"] else "; not georeferenced (GeoTIFF unreachable), location identified from the visible centre-pivot fields") + "; NOT tone B, not radiometrically comparable with the locked sequences; native pixels, no resampling, collar excluded"),
           "kind_source": L["type"], "file": os.path.basename(p), "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "size": [w, h],
           "credit": "Landsat 9 · USGS" if L["scene"].startswith("LC09") else "Landsat 8 · USGS", "licence": "USGS Landsat: public domain, credit requested",
           "source_url": "https://earthexplorer.usgs.gov/ (USGS M2M, Landsat Collection 2 Level-1 " + ("band file)" if L["type"] == "band" else "Full-Resolution Browse Natural Color JPEG)"), "retrieved": "2026-10-08"}
    json.dump(rec, open(f"{OUT}/{key}_toneB.json", "w"), indent=1); print(json.dumps(rec, indent=1))
if __name__ == "__main__":
    build(sys.argv[2], overview=sys.argv[1] == "overview")
