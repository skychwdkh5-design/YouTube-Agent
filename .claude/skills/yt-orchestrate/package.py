#!/usr/bin/env python3
"""Release package from real pipeline outputs: chapters (from storyboard chapter times), description (claims ledger + credits), tags, thumbnail.
Nothing is typed in by hand except the thumbnail text and tags in research/notes.json (optional keys: thumbnail {top, bottom}, tags)."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(SK, "yt-geo")); sys.path.insert(0, os.path.join(SK, "yt-render"))
import numpy as np
from PIL import Image, ImageDraw, ImageFont

DEFAULT_TAGS = ["NEOM", "The Line", "Saudi Arabia", "satellite imagery", "Sentinel-2", "Copernicus", "Landsat", "megaproject", "mega projects", "documentary",
                "satellite images", "NEOM The Line", "Saudi Vision 2030", "OrbitalAtlas"]


def mmss(t):
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def chapters(root, notes=None):
    sb = json.load(open(os.path.join(root, "story", "storyboard.json")))
    heads = dict(re.findall(r"^##\s+([a-z0-9_]+)\s*:\s*(.+)$", open(os.path.join(root, "script.md"), encoding="utf-8").read(), flags=re.M))
    titles = (notes or {}).get("chapter_titles") or {}
    rows = [(mmss(a), titles.get(c) or heads[c].strip()) for c, (a, b) in sb["chapters"].items()]
    rows[0] = ("0:00", rows[0][1])
    secs = [a for a, _ in sb["chapters"].values()] + [sb["duration"]]
    bad = [r for r, (x, y) in zip(rows, zip(secs, secs[1:])) if y - x < 10]
    if bad or len(rows) < 3:
        raise SystemExit(f"chapters break YouTube's rules (>=3 chapters, each >=10 s): {bad}")
    return rows


def description(root, notes, rows, dur):
    claims = json.load(open(os.path.join(root, "claims.json")))["claims"]
    prov = json.load(open(os.path.join(root, "evidence", "stack", "provenance.json")))["scenes"]
    title = notes["titles"][0]
    L = [f"{title}", "",
         "Saudi Arabia announced a 170 km linear city. We pointed free Sentinel-2 satellite images at the same stretch of desert, year after year (2020-2026), and kept three things apart: what was PROMISED, what was REPORTED, and what we OBSERVED.", "",
         "CHAPTERS", *[f"{t} {n}" for t, n in rows], "",
         "WHAT WE CLAIM, AND HOW SURE WE ARE",
         "- Observed: a straight corridor and a dark segment of about 1.6-1.9 km, measured at 10 m per pixel. A water index reads it as water-like, which is a clue, not proof.",
         "- Not claimed: that the corridor is The Line, that it is a finished city, that the segment grew, or what the segment is.",
         "- Reported items are attributed to the outlets named. We could not open the original Bloomberg, Semafor and Reuters articles from our research setup, so those lines rest on how other outlets described them.", "",
         "SOURCES (as reported; links are to the pages we actually read)"]
    for c in claims:
        if c["tier"] in ("original", "media", "org") and c["confidence"] != "low" and c.get("url"):
            L.append(f"- {c['id']} {c.get('attribution', '')} ({c.get('date', 'n.d.')}): {c['url']}")
    L += ["", "SATELLITE DATA",
          "Contains modified Copernicus Sentinel data " + ", ".join(sorted({s["datetime"][:4] for s in prov})) + ". Sentinel-2 L2A via Microsoft Planetary Computer; scenes from relative orbit 78, tile T36RYS, late September-October each year.",
          "Scene IDs: " + "; ".join(s["itemId"] for s in prov), "",
          f"Narration: ElevenLabs synthetic voice (Adam). Runtime {mmss(dur)}.", "Made by OrbitalAtlas."]
    return "\n".join(L) + "\n"


def thumbnail(root, notes, out):
    import geostack as g
    grid = json.load(open(os.path.join(root, "evidence", "stack", "grid.json")))
    img = Image.open(os.path.join(root, "evidence", "stack", f"y{max(int(y) for y in notes['geo']['stacks'][0]['years'])}.png")).convert("RGB")
    lon, lat = notes["geo"].get("segment") or notes["geo"]["focus"]
    x, y = g.lonlat_to_utm(np.array([lon]), np.array([lat]), grid["epsg"])
    cx, cy = (x[0] - grid["x0"]) / grid["pixel_m"], (grid["y_top"] - y[0]) / grid["pixel_m"]
    w = 520; h = w * 9 / 16
    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    im = img.resize((1280, 720), Image.LANCZOS, box=box)
    a = np.asarray(im).astype(float)
    ramp = np.linspace(0.38, 0.0, 720)[:, None, None]            # darken the top for the text; the picture itself is otherwise untouched
    ramp2 = np.linspace(0.0, 0.38, 720)[:, None, None]
    im = Image.fromarray((a * (1 - np.clip(ramp + ramp2, 0, 0.7))).astype(np.uint8))
    d = ImageDraw.Draw(im)
    import render as r
    bold = r.font_file("Inter:style=Black") or r.font_file("DejaVu Sans:style=Bold")
    top, bottom = (notes.get("thumbnail") or {}).get("top", "170 KM PROMISED"), (notes.get("thumbnail") or {}).get("bottom", "THIS IS WHAT WE SEE")
    f1, f2, f3 = ImageFont.truetype(bold, 104), ImageFont.truetype(bold, 84), ImageFont.truetype(bold, 26)
    d.text((56, 44), top, font=f1, fill=(255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0))
    d.text((56, 560), bottom, font=f2, fill=(255, 210, 63), stroke_width=7, stroke_fill=(0, 0, 0))
    d.ellipse((665 - 185, 360 - 62, 665 + 185, 360 + 62), outline=(255, 210, 63), width=7)    # the dark segment sits at the frame centre
    d.text((56, 700), "Contains modified Copernicus Sentinel data 2026", font=f3, fill=(255, 255, 255), anchor="ls", stroke_width=3, stroke_fill=(0, 0, 0))
    im.save(out, "JPEG", quality=90)
    return os.path.getsize(out)


def main(slug):
    root = os.path.join(SK, "..", "..", "productions", slug)
    notes = json.load(open(os.path.join(root, "research", "notes.json")))
    sb = json.load(open(os.path.join(root, "story", "storyboard.json")))
    rel = os.path.join(root, "release"); os.makedirs(rel, exist_ok=True)
    rows = chapters(root, notes)
    open(os.path.join(rel, "chapters.txt"), "w").write("\n".join(f"{t} {n}" for t, n in rows) + "\n")
    open(os.path.join(rel, "description.txt"), "w", encoding="utf-8").write(description(root, notes, rows, sb["duration"]))
    tags = notes.get("tags") or DEFAULT_TAGS
    meta = {"title": notes["titles"][0], "title_alternatives": notes["titles"][1:], "working_title_note": "working title approved by the owner, not final",
            "tags": tags, "tags_chars": len(",".join(tags)), "chapters": [{"t": t, "title": n} for t, n in rows], "language": "en", "category": "Education",
            "altered_or_synthetic_content": "narration is a synthetic voice (ElevenLabs Adam); imagery is real satellite data; yes, disclose synthetic voice in YouTube Studio",
            "published": False}
    json.dump(meta, open(os.path.join(rel, "metadata.json"), "w"), indent=1, ensure_ascii=False)
    size = thumbnail(root, notes, os.path.join(rel, "thumbnail.jpg"))
    print(json.dumps({"status": "ok", "chapters": len(rows), "thumbnail_bytes": size, "dir": rel}))


if __name__ == "__main__":
    main(sys.argv[1])
