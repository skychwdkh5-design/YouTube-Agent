"""Build shot images + timeline.json from beats.py and the draft narration timing.
python3 build.py <beats_module> <voice_dir> <out_prefix> [--short]"""
import importlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import visuals as V
from PIL import Image

mod, vdir, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
SHORT = "--short" in sys.argv
BEATS = importlib.import_module(mod).BEATS
tim = json.load(open(f"{vdir}/narration.timing.json"))
total = tim["duration"]
import shutil; shutil.rmtree(f"shots/{prefix}", ignore_errors=True); os.makedirs(f"shots/{prefix}")
XF = 0.4
clips, sheet = [], []
starts = [0.0] + [b["start"] - 0.12 for b in tim["beats"][1:]] + [total]
n = 0
for bi, (text, shots) in enumerate(BEATS):
    b0, b1 = starts[bi], starts[bi + 1]
    k = len(shots)
    for si, (kind, ref, o) in enumerate(shots):
        n += 1
        path = f"shots/{prefix}/{n:03d}_{ref}.png"
        if kind == "vgraphic":
            im = V.VGRAPHICS[ref](o.get("step", 0))
            credit = "NASA/JPL-Caltech/University of Arizona" if ref == "v_hirise" else "NASA/JPL-Caltech/MSSS"
        elif kind == "graphic":
            im = V.make_graphic(ref, o.get("step", 0))
            credit = ("NASA/JPL-Caltech/University of Arizona" if ref == "g_hirise"
                      else "NASA/JPL-Caltech/MSSS" if ref in ("g_first", "g_title", "g_quote", "g_scale") else None)
        else:
            im = {"still": lambda: V.crop_still(ref, o["y"]), "pano": lambda: V.crop_pano(ref, o["box"]),
                  "vstill": lambda: V.crop_still_v(ref, o["x"]), "vpano": lambda: V.crop_pano_v(ref, o["box"])}[kind]()
            if o.get("label"):
                im = V.label(im, o["label"], o.get("sub"))
            credit = V.CREDIT.get(ref, "NASA/JPL-Caltech/MSSS")
        im.save(path, optimize=False)
        dur = (b1 - b0) / k
        z = o.get("zoom", [1.0, 1.03])
        motion = {"type": "kenburns", "zoom": z, "pan": o.get("pan", "center")} if kind not in ("graphic", "vgraphic") else {"type": "kenburns", "zoom": [1.0, 1.025], "pan": "center"}
        last = bi == len(BEATS) - 1 and si == k - 1
        clip = {"type": "image", "src": path, "duration": round(dur + (0.2 if last else XF), 3), "fit": "cover",
                "motion": motion, "transition": {"type": "none"} if last else {"type": "crossfade", "duration": XF},
                "source": ref}
        if credit:
            clip["credit"] = credit
        clips.append(clip)
        sheet.append((path, f"{b0 + (b1 - b0) * si / k:6.1f}s {ref}"))
W, H = (1080, 1920) if SHORT else (1920, 1080)
tl = {"version": 1, "output": {"width": W, "height": H, "fps": 30, "crf": 18 if SHORT else 20, "preset": "veryfast"},
      "clips": clips,
      "audio": {"voice": [{"src": f"{vdir}/narration.wav", "start": 0.0}]},
      "subtitles": {"src": f"{vdir}/captions.srt", "burn_in": True, "size": 12 if SHORT else 15, "margin_v": 72 if SHORT else 24},
      "credit": {"position": "top_left", **({"size": 22} if SHORT else {})}}
json.dump(tl, open(f"{prefix}.timeline.json", "w"), indent=1)
# contact sheet
cols = 6; tw, th = (320, 180) if not SHORT else (180, 320)
rows = (len(sheet) + cols - 1) // cols
cs = Image.new("RGB", (cols * tw, rows * (th + 24)), (0, 0, 0))
from PIL import ImageDraw
d = ImageDraw.Draw(cs)
for i, (p, cap) in enumerate(sheet):
    t = Image.open(p).convert("RGB").resize((tw, th))
    x, y = (i % cols) * tw, (i // cols) * (th + 24)
    cs.paste(t, (x, y)); d.text((x + 4, y + th + 4), cap, fill=(255, 255, 0))
cs.save(f"{prefix}.contact.jpg", quality=85)
print(json.dumps({"clips": len(clips), "narration": total, "timeline": f"{prefix}.timeline.json"}))
