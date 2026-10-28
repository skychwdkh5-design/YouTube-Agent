"""EP006: list Sentinel-2 L2A scenes (Planetary Computer STAC) over the Langtang Lirung / Lende Khola area, 20 Jul - 10 Sep 2026. Free; writes scenes_found.json."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".claude", "skills", "yt-sentinel"))
import sentinel as S
AOI = [85.30, 28.10, 85.70, 28.45]
items = S.stac_search(AOI, "2026-07-20", "2026-09-10", cloud_max=100.0)
items.sort(key=lambda i: i["datetime"])
json.dump(items, open(os.path.join(os.path.dirname(__file__), "scenes_found.json"), "w"), indent=1)
for i in items:
    print(i["date"], i["tile"] if "tile" in i else "", i["id"][-40:], "cloud", i["cloud"], "orbit", i["orbit"], "nodata", i["nodata"])
