#!/usr/bin/env python3
"""thumbcheck.py - objective half of the OrbitalAtlas thumbnail gate (docs/THUMBNAIL_STYLE_GUIDE.md).

    python3 thumbcheck.py cover.jpg [more.jpg ...]              # current style: Neon Contour (owner-approved 2026-11-20)
    python3 thumbcheck.py --style gold cover.jpg [...]          # superseded gold style (EP001-EP004 reference covers)

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


NEON_RULES = "calibrated on the 15 Neon Contour covers set on 2026-11-20: saturation 0.40-0.66, luma std 57-88, white 1-8.5%, lime 3.1-5.9%, magenta 1.5-7%"


def neon_shares(path):
    small = Image.open(path).convert("RGB").resize((320, 180))
    hsv = [colorsys.rgb_to_hsv(r / 255, g / 255, b / 255) for r, g, b in small.getdata()]
    n = len(hsv)
    lime = sum(1 for h, s, v in hsv if 0.17 <= h < 0.26 and s > 0.6 and v > 0.8) / n
    mag = sum(1 for h, s, v in hsv if 0.8 < h < 0.95 and s > 0.5 and v > 0.7) / n
    return round(lime, 3), round(mag, 3)


def check_neon(m):
    return {"is_1280x720": m["size"] == (1280, 720), "under_2MB": m["bytes"] <= MAX_BYTES,
            "strong_contrast(luma_std>=55)": m["luma_std"] >= 55,
            "saturated(mean_saturation>=0.38)": m["mean_saturation"] >= 0.38,
            "white_headline(>=0.8%)": m["white_share"] >= 0.008,
            "lime_hook_word(>=2.5%)": m["lime_share"] >= 0.025,
            "magenta_neon(>=1.0%)": m["magenta_share"] >= 0.010,
            "dark_field(>=45%)": m["dark_share"] >= 0.45}


def check(m):
    return {"is_1280x720": m["size"] == (1280, 720), "under_2MB": m["bytes"] <= MAX_BYTES,
            "strong_contrast(luma_std>=58)": m["luma_std"] >= 58,
            "saturated(mean_saturation>=0.40)": m["mean_saturation"] >= 0.40,
            "white_headline_mass(>=2.5%)": m["white_share"] >= 0.025,
            "yellow_accent(>=1.2%)": m["yellow_share"] >= 0.012}


def main(argv):
    out, ok, style = [], True, "neon"
    if argv[:1] == ["--style"]:
        style, argv = argv[1], argv[2:]
    for p in argv:
        m = metrics(p)
        if style == "neon":
            m["lime_share"], m["magenta_share"] = neon_shares(p); r = check_neon(m)
        else:
            r = check(m)
        good = all(r.values()); ok &= good
        out.append({"file": p, "metrics": m, "rules": r, "result": "PASS (objective part)" if good else "FAIL"})
    print(json.dumps(out, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) if len(sys.argv) > 1 else print(__doc__) or 2)
