#!/usr/bin/env python3
"""thumbcheck.py - objective half of the OrbitalAtlas thumbnail gate (docs/THUMBNAIL_STYLE_GUIDE.md).

    python3 thumbcheck.py cover.jpg [more.jpg ...]

Prints JSON per file: metrics, rule results and PASS/FAIL. It checks only what a script can measure (size, saturation, contrast,
white headline mass, yellow accent). Similarity to the approved covers, one focus, true-to-content and phone legibility are
judged by Claude against the guide and recorded in the review - a script PASS is necessary, never sufficient.
Thresholds were calibrated on the four PUBLISHED covers (Sahara, Dubai, Great Salt Lake, Jakarta; docs/assets/thumbnail-reference/):
saturation 0.46-0.58, luma std 64-73, white 3.3-6.8%, yellow 1.6-5.7% (gold, hue 41-61 deg).
"""
import colorsys, json, os, sys
from PIL import Image, ImageStat

MAX_BYTES = 2 * 1024 * 1024


def metrics(path):
    im = Image.open(path).convert("RGB")
    small = im.resize((320, 180))
    px = list(small.getdata())
    hsv = [colorsys.rgb_to_hsv(r / 255, g / 255, b / 255) for r, g, b in px]
    n = len(px)
    luma = ImageStat.Stat(small.convert("L"))
    white = sum(1 for r, g, b in px if min(r, g, b) > 235) / n
    yellow = sum(1 for h, s, v in hsv if 0.115 < h < 0.17 and s > 0.6 and v > 0.85) / n
    dark = sum(1 for v in (c[2] for c in hsv) if v < 0.25) / n
    return {"size": im.size, "bytes": os.path.getsize(path), "mean_saturation": round(sum(c[1] for c in hsv) / n, 2),
            "luma_std": round(luma.stddev[0], 1), "white_share": round(white, 3), "yellow_share": round(yellow, 3), "dark_share": round(dark, 3)}


def check(m):
    return {"is_1280x720": m["size"] == (1280, 720), "under_2MB": m["bytes"] <= MAX_BYTES,
            "strong_contrast(luma_std>=58)": m["luma_std"] >= 58,
            "saturated(mean_saturation>=0.40)": m["mean_saturation"] >= 0.40,
            "white_headline_mass(>=2.5%)": m["white_share"] >= 0.025,
            "yellow_accent(>=1.2%)": m["yellow_share"] >= 0.012}


def main(argv):
    out, ok = [], True
    for p in argv:
        m = metrics(p); r = check(m); good = all(r.values()); ok &= good
        out.append({"file": p, "metrics": m, "rules": r, "result": "PASS (objective part)" if good else "FAIL"})
    print(json.dumps(out, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) if len(sys.argv) > 1 else print(__doc__) or 2)
