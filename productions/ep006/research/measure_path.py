"""EP006: length of the dark swath visible in the Landsat 9 image of 26 Aug 2026, traced by hand on the 10 m grid (nearest-neighbour Landsat on the Sentinel-2 grid) and converted to km.
The tracing is a visual judgement (writes the polyline it used) - it is NOT an automatic detection. Also converts the Rasuwagadhi border-post location to grid pixels."""
import json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".claude", "skills", "yt-geo"))
import geostack as g
G = json.load(open(os.path.join(os.path.dirname(__file__), "..", "evidence", "stack", "grid.json")))
import numpy as np
def ll2px(lon, lat):
    x, y = g.lonlat_to_utm(np.array([lon]), np.array([lat]), G["epsg"])
    return ((x[0] - G["x0"]) / G["pixel_m"], (G["y_top"] - y[0]) / G["pixel_m"])
def px2ll(px, py):
    x = G["x0"] + px * G["pixel_m"]; y = G["y_top"] - py * G["pixel_m"]
    lon, lat = g.utm_to_lonlat(np.array([x]), np.array([y]), G["epsg"])
    return float(lon[0]), float(lat[0])
S = 2.5      # display (0.4x) -> full resolution
disp = [(840,600),(800,520),(745,430),(725,380),(650,370),(580,372),(500,400),(450,430),(455,470),(400,540),(340,600),(310,630),(305,690),(260,740),(235,800),(232,860),(215,930),(205,990)]
pts = [(x * S, y * S) for x, y in disp]
seg = [math.dist(pts[i], pts[i+1]) * G["pixel_m"] for i in range(len(pts) - 1)]
cum = np.cumsum(seg)
rg = ll2px(85.3722, 28.2858)     # Rasuwagadhi border post (approximate; Wikipedia/OSM-level position, to be checked)
nearest = min(range(len(pts)), key=lambda i: math.dist(pts[i], rg))
out = {"grid": "evidence/stack/grid.json (10 m)", "polyline_px": pts, "polyline_lonlat": [px2ll(*p) for p in pts],
       "total_km_in_frame": round(float(cum[-1]) / 1000, 1), "rasuwagadhi_px": rg, "rasuwagadhi_lonlat_assumed": [85.3722, 28.2858],
       "nearest_trace_vertex_to_rasuwagadhi": nearest, "km_from_glacier_foot_to_that_vertex": round(float(cum[nearest-1]) / 1000, 1) if nearest else 0,
       "distance_to_rasuwagadhi_px_m": round(math.dist(pts[nearest], rg) * G["pixel_m"]),
       "method": "hand-traced centre line of the dark grey-brown swath in the 26 Aug 2026 Landsat 9 image; length = sum of straight segments x 10 m; clouds hide parts, so it is a lower bound inside the frame"}
json.dump(out, open(os.path.join(os.path.dirname(__file__), "..", "evidence", "path_measure.json"), "w"), indent=1)
print({k: out[k] for k in out if k not in ("polyline_px", "polyline_lonlat")})
print("start lonlat", out["polyline_lonlat"][0], "end", out["polyline_lonlat"][-1])
