import json, sys, os
sys.path.insert(0, "/home/user/YouTube-Agent/.claude/skills/yt-sentinel")
import sentinel as S
items = {i["date"] + "_o" + str(i["orbit"]): i for i in json.load(open("scenes_found.json"))}
aoi = [float(x) for x in sys.argv[1].split(",")]
pm = float(sys.argv[2]); out = sys.argv[3]; os.makedirs(out, exist_ok=True)
g = S.utm_grid(aoi, pm)
print(g["width"], g["height"], g["epsg"])
for k in sys.argv[4:]:
    it = items[k]
    data = S._get(S.crop_url(it["id"], g))
    open(os.path.join(out, k + ".png"), "wb").write(data)
    print(k, len(data))
