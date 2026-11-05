#!/usr/bin/env python3
"""EP011 covers. A = frame 0 of the film (built by build.py frames ... 0). B and C are A/B alternatives from the real sources.
usage: thumbs.py FRAME0.jpg OUTDIR"""
import os, sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paint import font, shadow_text, pill
import scenes as S

W, H = 1920, 1080
YEL, WHT = (255, 210, 63, 255), (255, 255, 255, 255)


def save(img, path):
    img.convert("RGB").resize((1280, 720), Image.LANCZOS).save(path, quality=92)


def cover_b():
    ls = S.landsat()
    cx, cy, z = S.LS_EPI[0] - 120, S.LS_EPI[1] - 260, 1.25
    img = S.camera(ls, cx, cy, z)
    img = ImageEnhance.Color(img).enhance(1.35); img = ImageEnhance.Contrast(img).enhance(1.45)
    img = img.convert("RGBA")
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(dark)
    for y in range(420):
        dd.line([(0, y), (W, y)], fill=(4, 10, 20, int(190 * (1 - y / 420) ** 1.3)))
    img.alpha_composite(dark)
    x, y = S.to_screen(S.LS_EPI, (cx, cy, z))
    d = S.BD(img)
    for r, wdt in ((120, 14), (128, 4)):
        d.ellipse([x - r, y - r, x + r, y + r], outline=(235, 40, 40, 255), width=wdt)
    shadow_text(img, (70, 50), "WHAT HIT HERE?", font("Inter-Black.otf", 200), WHT, "la", stroke=8, blur=14)
    shadow_text(img, (78, 290), "1908 · NO CRATER", font("Inter-Black.otf", 104), YEL, "la", stroke=6, blur=12)
    pill(img, (W - 40, H - 80), "LANDSAT 8 · 2024 · NASA EO / USGS", 30, anchor="r", wt="Inter-Bold.otf")
    return img


def cover_c():
    ar = S.archive(); ls = S.landsat()
    left = S.camera(ar, ar.width * 0.42, ar.height * 0.55, H / ar.height * 1.35, out=(W // 2, H))
    right = S.camera(ls, S.LS_EPI[0], S.LS_EPI[1] - 150, 1.15, out=(W // 2, H))
    right = ImageEnhance.Color(right).enhance(1.5); right = ImageEnhance.Contrast(right).enhance(1.4)
    left = ImageEnhance.Contrast(left).enhance(1.45)
    img = Image.new("RGBA", (W, H)); img.paste(left, (0, 0)); img.paste(right, (W // 2, 0))
    d = S.BD(img)
    d.rectangle([W // 2 - 6, 0, W // 2 + 6, H], fill=(255, 210, 63, 255))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(dark)
    for y in range(400):
        dd.line([(0, H - y), (W, H - y)], fill=(4, 10, 20, int(200 * (1 - y / 400) ** 1.3)))
    img.alpha_composite(dark)
    shadow_text(img, (60, 40), "1929", font("Inter-Black.otf", 130), YEL, "la", stroke=6)
    shadow_text(img, (W // 2 + 60, 40), "2024", font("Inter-Black.otf", 130), YEL, "la", stroke=6)
    shadow_text(img, (W // 2, H - 250), "NO CRATER?", font("Inter-Black.otf", 190), WHT, "ma", stroke=8, blur=14)
    return img


if __name__ == "__main__":
    f0, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    save(Image.open(f0), os.path.join(out, "EP011_cover_A_no_crater.jpg"))
    save(cover_b(), os.path.join(out, "EP011_cover_B_what_hit_here.jpg"))
    save(cover_c(), os.path.join(out, "EP011_cover_C_1929_2024.jpg"))
