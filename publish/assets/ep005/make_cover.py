#!/usr/bin/env python3
"""EP005 cover, concept #1 "170 KM PROMISED" (archetype A, before | after) - docs/THUMBNAIL_STYLE_GUIDE.md.

Real pixels only: the two halves are crops of the same ground from the Sentinel-2 comparison used in the video
(src/s2-cmp-2022-2026.png: 2022-10-14 and 2026-10-08, T36RYS, orbit 78). Allowed enhancement: crop, upscale, colour grade, vignette,
and the annotation layer (headline, ring, arrow, year badges). Nothing is drawn into the imagery itself.
    python3 make_cover.py [out.jpg]
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
WHITE, GOLD, BLACK = (255, 255, 255), (255, 210, 30), (0, 0, 0)
W, H = 1280, 720
PANELS = {"2022": (96, 248), "2026": (975, 248)}      # top-left of each photo panel in the source
CROP_W, CROP_H, CX = 355, 400, 262                      # same ground in both: segment sits at panel x~440, y~249


def grade(im):
    """Cinematic gradient map (deep brown -> burnt orange -> amber) on the real luminance; the dark green water-like
    pixels keep their own hue so the segment stays what the satellite saw."""
    from PIL import ImageChops, ImageOps
    gray = ImageOps.autocontrast(im.convert("L"), cutoff=1)
    gray = gray.point(lambda v: int(255 * (v / 255) ** 1.6))
    look = ImageOps.colorize(gray, black=(8, 3, 4), mid=(168, 72, 22), white=(255, 176, 70), midpoint=118)
    r, g, b = [c.convert("L") for c in im.split()]
    greenish = ImageChops.subtract(g, r).point(lambda v: 255 if v > 4 else 0).filter(ImageFilter.GaussianBlur(1.2))
    dark = im.convert("L").point(lambda v: 255 if v < 150 else 0)
    keep = ImageChops.multiply(greenish, dark)
    green = ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(0.9)).enhance(1.8)
    look = Image.composite(green, look, keep)
    vig = Image.new("L", im.size, 0); d = ImageDraw.Draw(vig)
    d.ellipse((-im.width * .25, -im.height * .2, im.width * 1.25, im.height * 1.2), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(90))
    return Image.composite(look, ImageEnhance.Brightness(look).enhance(0.4), vig)


def half(src, key):
    x0, y0 = PANELS[key]
    c = src.crop((x0 + CX, y0, x0 + CX + CROP_W, y0 + CROP_H)).resize((W // 2, H), Image.LANCZOS)
    return grade(c.filter(ImageFilter.UnsharpMask(2, 90, 2)))


def text_layer(text, size, fill, squeeze=0.82, stroke=9):
    f = ImageFont.truetype(FONT, size)
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    lay = Image.new("RGBA", (r - l + 40, b - t + 40), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((20 - l, 20 - t), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=BLACK)
    lay = lay.resize((int(lay.width * squeeze), lay.height), Image.LANCZOS)         # condensed display look
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 190), mask=lay.split()[3])
    out = Image.new("RGBA", (lay.width + 12, lay.height + 12), (0, 0, 0, 0))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)), (10, 10)); out.alpha_composite(lay, (0, 0))
    return out


def bez(p0, p1, p2, n=60):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def arrow(img, pts, color, w):
    d = ImageDraw.Draw(img)
    for col, ww in ((BLACK, w + 10), (color, w)):
        d.line(pts, fill=col, width=ww, joint="curve")
    (x0, y0), (x1, y1) = pts[-6], pts[-1]
    a = math.atan2(y1 - y0, x1 - x0)
    for col, s in ((BLACK, 1.35), (color, 1.0)):
        tip = (x1 + math.cos(a) * 22 * s, y1 + math.sin(a) * 22 * s)
        base = [(x1 - math.cos(a) * 40 * s + math.cos(a + k) * 46 * s * 0.0 + math.cos(a + math.pi / 2) * k * 38 * s,
                 y1 - math.sin(a) * 40 * s + math.sin(a + math.pi / 2) * k * 38 * s) for k in (-1, 1)]
        d.polygon([tip] + base, fill=col)


def badge(img, xy, text, fill):
    f = ImageFont.truetype(FONT, 64)
    d = ImageDraw.Draw(img, "RGBA"); l, t, r, b = d.textbbox((0, 0), text, font=f)
    x, y = xy; pad = 18
    if x < 0:
        x = W + x - (r - l + 2 * pad)
    d.rounded_rectangle((x, y, x + r - l + 2 * pad, y + b - t + 2 * pad), 18, fill=(6, 10, 16, 215), outline=(255, 255, 255, 60), width=2)
    d.text((x + pad - l, y + pad - t), text, font=f, fill=fill)


def build(out):
    src = Image.open(os.path.join(HERE, "src", "s2-cmp-2022-2026.png")).convert("RGB")
    img = Image.new("RGB", (W, H))
    img.paste(half(src, "2022"), (0, 0)); img.paste(half(src, "2026"), (W // 2, 0))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.rectangle((W // 2 - 8, 0, W // 2 + 8, H), fill=(255, 255, 255, 200)); glow = glow.filter(ImageFilter.GaussianBlur(7))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    d = ImageDraw.Draw(img); d.rectangle((W // 2 - 3, 0, W // 2 + 3, H), fill=WHITE)
    # ring around the real dark segment (2026 half), glow + outline
    cx, cy, rx, ry = 960, 448, 215, 70
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
    rd.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=GOLD + (255,), width=9)
    g2 = ring.filter(ImageFilter.GaussianBlur(10)); img = Image.alpha_composite(img.convert("RGBA"), g2); img = Image.alpha_composite(img, ring).convert("RGB")
    d = ImageDraw.Draw(img)
    arrow(img, bez((250, 640), (450, 500), (760, 540)), WHITE, 14)
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(shade)
    for y in range(H):
        a = int(150 * max(0, 1 - y / 360)) + int(120 * max(0, (y - 560) / 160))
        sd.line((0, y, W, y), fill=(0, 0, 0, min(a, 190)))
    img = Image.alpha_composite(img.convert("RGBA"), shade)
    badge(img, (36, 612), "2022", WHITE); badge(img, (-36, 612), "2026", GOLD)
    l1 = text_layer("170 KM", 215, WHITE); l2 = text_layer("PROMISED", 190, GOLD)
    img.alpha_composite(l1, (36, 6)); img.alpha_composite(l2, (36, 6 + l1.height - 48))
    cd = ImageDraw.Draw(img, "RGBA"); f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 18)
    t = "Contains modified Copernicus Sentinel data 2022, 2026"
    cd.rectangle((W // 2 - 270, H - 30, W // 2 + 270, H), fill=(0, 0, 0, 150)); cd.text((W // 2 - 262, H - 27), t, font=f, fill=(235, 235, 235))
    img.convert("RGB").save(out, quality=93)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "thumbnail_v2.jpg"))
