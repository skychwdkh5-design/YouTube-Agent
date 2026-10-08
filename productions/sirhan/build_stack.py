import json, glob, os
t = open("raw/metadata_raw.json").read()
dec = json.JSONDecoder(); i = 0; objs = []
while True:
    t2 = t[i:].lstrip()
    if not t2: break
    o, n = dec.raw_decode(t2); objs.append(o); i = len(t) - len(t2) + n
scenes, meta = [], []
SKIP = set()
for o in sorted({o["entityId"]: o for o in objs }.values(), key=lambda o: o["acquired"]):
    f = o["fields"]; disp = o["displayId"]
    src = f"raw/{disp}_refl.tif"
    assert os.path.exists(src), src
    sat = {"LC09": "Landsat 9", "LC08": "Landsat 8", "LT05": "Landsat 5", "LT04": "Landsat 4"}[disp[:4]]
    m = {"entityId": o["entityId"], "displayId": disp, "acquired": o["acquired"], "cloud": o["cloudCover"],
         "land_cloud": f["Land Cloud Cover"].strip(), "start_time": f["Start Time"], "sensor": "OLI_TIRS" if disp.startswith("LC") else "TM",
         "path": f["WRS Path"].strip(), "row": f["WRS Row"].strip(), "tier": f["Collection Category"]}
    meta.append(m)
    sid = "y" + o["acquired"][:4]
    scenes.append({"id": sid, "src": src, "label": o["acquired"][:4],
                   "provenance": {"kind": "landsat", "entityId": o["entityId"], "displayId": disp,
                                  "dataset": "landsat_ot_c2_l1" if disp.startswith("LC") else "landsat_tm_c2_l1", "satellite": sat, "sensor": "OLI/TIRS" if disp.startswith("LC") else "TM",
                                  "acquired": o["acquired"], "start_time_utc": f["Start Time"],
                                  "wrs_path_row": f"{m['path']}/{m['row']}", "land_cloud_cover": m["land_cloud"],
                                  "tier": m["tier"], "product": "Full-Resolution Browse (Natural Color) GeoTIFF",
                                  "source": "USGS EROS M2M API",
                                  "license": {"name": "Public domain (U.S. Government work)", "commercial_use": True},
                                  "credit": "Landsat imagery courtesy of the U.S. Geological Survey"}})
with open("raw/metadata.jsonl", "w") as fh:
    for m in meta: fh.write(json.dumps(m) + "\n")
json.dump({"aoi": [37.98, 29.78, 38.90, 30.55], "pixel_m": 30, "out_dir": "stack", "scenes": scenes},
          open("stack.json", "w"), indent=1)
for m in meta: print(m["acquired"], m["tier"], "scene", m["cloud"], "land", m["land_cloud"])
