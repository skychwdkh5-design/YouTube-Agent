#!/usr/bin/env python3
"""Slice the validated EP009 painted map-marker sheet into independent RGBA objects.
Requires pillow. Input must come from SHA-256 verified illustration ZIP.
Coordinates are for the approved 1448x1086 sheet only. Stores actual cutouts locally.
"""
from pathlib import Path
from PIL import Image
import hashlib, json
p=Path(__file__).resolve().parents[1]/"handoff/assets/P05_markers_sheet.png"
out=p.parent/"markers"
im=Image.open(p).convert("RGBA")
assert im.size==(1448,1086), f"Incorrect image size: {im.size}"
regions={
"pin_red":(165,0,510,435),
"pin_ochre":(555,0,895,435),
"pin_pushpin":(940,0,1230,445),
"arrow_white":(50,434,675,656),
"arrow_orange":(50,628,670,818),
"measure_double":(725,435,1400,715),
"scale_bar":(25,795,1425,1086),
}
out.mkdir(parents=True,exist_ok=True)
manifest=[]
for name,bbox in regions.items():
    v=im.crop(bbox)
    alpha=v.getchannel("A")
    tight=alpha.getbbox()
    if tight is None:raise RuntimeError(f"empty region: {name}")
    v=v.crop(tight)
    target=out/(name+".png")
    v.save(target)
    manifest.append(dict(name=name,path=str(target),width=v.width,height=v.height,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
(out/"markers_manifest.json").write_text(json.dumps(manifest,indent=2))
for a in manifest:print(a["name"],a["width"],a["height"],a["sha256"])
