import json, glob, os
t = open("raw/metadata_raw.json").read()
dec = json.JSONDecoder(); i = 0; objs = []
while True:
    t2 = t[i:].lstrip()
    if not t2: break
    o, n = dec.raw_decode(t2); objs.append(o); i = len(t) - len(t2) + n
scenes, meta = [], []
SKIP = {"LC80620462018182LGN00", "LC80620462018214LGN00", "LC80620472018230LGN00"}   # row 046 misses the summit; 08-18 is cloud
for o in sorted({o["entityId"]: o for o in objs if o["entityId"] not in SKIP}.values(), key=lambda o: o["acquired"]):
    f = o["fields"]; disp = o["displayId"]
    src = f"raw/{disp}_refl.tif"
    assert os.path.exists(src), src
    sat = "Landsat 9" if disp.startswith("LC09") else "Landsat 8"
    m = {"entityId": o["entityId"], "displayId": disp, "acquired": o["acquired"], "cloud": o["cloudCover"],
         "land_cloud": f["Land Cloud Cover"].strip(), "start_time": f["Start Time"], "sensor": "OLI_TIRS",
         "path": f["WRS Path"].strip(), "row": f["WRS Row"].strip(), "tier": f["Collection Category"]}
    meta.append(m)
    sid = "d" + o["acquired"].replace("-", "")
    scenes.append({"id": sid, "src": src, "label": o["acquired"],
                   "provenance": {"kind": "landsat", "entityId": o["entityId"], "displayId": disp,
                                  "dataset": "landsat_ot_c2_l1", "satellite": sat, "sensor": "OLI/TIRS",
                                  "acquired": o["acquired"], "start_time_utc": f["Start Time"],
                                  "wrs_path_row": f"{m['path']}/{m['row']}", "land_cloud_cover": m["land_cloud"],
                                  "tier": m["tier"], "product": "Full-Resolution Browse (Natural Color) GeoTIFF",
                                  "source": "USGS EROS M2M API",
                                  "license": {"name": "Public domain (U.S. Government work)", "commercial_use": True},
                                  "credit": "Landsat imagery courtesy of the U.S. Geological Survey"}})
with open("raw/metadata.jsonl", "w") as fh:
    for m in meta: fh.write(json.dumps(m) + "\n")
json.dump({"aoi": [-155.32, 19.25, -154.78, 19.56], "pixel_m": 30, "out_dir": "stack", "scenes": scenes},
          open("stack.json", "w"), indent=1)
for m in meta: print(m["acquired"], m["tier"], "scene", m["cloud"], "land", m["land_cloud"])
