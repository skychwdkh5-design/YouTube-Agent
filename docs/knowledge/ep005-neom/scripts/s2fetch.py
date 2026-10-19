import json,urllib.request,urllib.parse,io,sys
from PIL import Image
import numpy as np
PC="https://planetarycomputer.microsoft.com/api"
BBOX=(35.10,28.07,35.32,28.15); W,H=2160,890
def post(u,b):
    r=urllib.request.Request(u,data=json.dumps(b).encode(),headers={"Content-Type":"application/json"}); return json.loads(urllib.request.urlopen(r,timeout=60).read())
def items(a,b,cloud=5):
    d=post(PC+"/stac/v1/search",{"collections":["sentinel-2-l2a"],"bbox":[35.10,28.07,35.32,28.15],"datetime":f"{a}T00:00:00Z/{b}T23:59:59Z","limit":100,"query":{"eo:cloud_cover":{"lt":cloud}}})
    out=[]
    for f in d["features"]:
        p=f["properties"]; out.append((p["datetime"][:10],f["id"],round(p["eo:cloud_cover"],2),p.get("s2:nodata_pixel_percentage"),p.get("sat:relative_orbit"),p.get("view:sun_elevation"),p.get("view:sun_azimuth")))
    return sorted(out)
def crop(item,assets="visual",fmt="png",extra="",bbox=BBOX,wh=(W,H)):
    q=f"collection=sentinel-2-l2a&item={item}&"+"&".join(f"assets={a}" for a in assets.split(","))+extra
    u=f"{PC}/data/v1/item/bbox/{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}/{wh[0]}x{wh[1]}.{fmt}?{q}"
    return urllib.request.urlopen(u,timeout=180).read()
if __name__=="__main__":
    import datetime
    for y in (2020,2021,2022,2023,2024,2025,2026):
        print("==",y)
        for it in items(f"{y}-09-20",f"{y}-11-10" if y<2026 else "2026-10-19",5): print("  ",it)
