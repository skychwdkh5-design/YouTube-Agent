#!/usr/bin/env python3
"""neon_cover.py - Orbital Atlas long-form cover in the owner-approved "Neon Contour" style (2026-11-20).

    python3 neon_cover.py --hero frame.png [--crop 0.3,0.1,0.8,1.0] [--grade 1.5,1.2,1.05] \
        --top "THE PACIFIC" --top "TURNED" --big RED --chip "NASA SVS · SEA SURFACE TEMP" --out cover.jpg [--overwrite]

Layout (fixed, see docs/THUMBNAIL_STYLE_GUIDE.md): black field with lime contour lines, the real hero inside a disc on the
right (magenta neon ring + lime orbit ring with ticks + magenta speed streaks), 0-2 short white lines (Unbounded Black) and
ONE neon-lime hook word/number with magenta glow on the left, a lime pill with the source / honesty label
(ILLUSTRATION, RECONSTRUCTION, credit), "ORBITAL ATLAS" in magenta top right.
--crop is a fraction box on the hero; --seed varies the contour pattern only. Prints JSON; refuses to overwrite without --overwrite.
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1280, 720
LIME, MAG, INK, WHITE = (198, 255, 0), (255, 43, 214), (7, 6, 11), (255, 255, 255)
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Unbounded-Black.woff")


def F(size):
    return ImageFont.truetype(FONT, size)


def tw(s, f):
    b = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def fit(s, start, maxw, minsize=40):
    size = start
    while size > minsize and tw(s, F(size)) > maxw:
        size -= 4
    return size


def fill(im, w, h, cx=0.5, cy=0.5):
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x = int((im.width - w) * cx); y = int((im.height - h) * cy)
    return im.crop((x, y, x + w, y + h))


def grade(im, sat, con, bri):
    im = ImageEnhance.Color(im).enhance(sat)
    im = ImageEnhance.Contrast(im).enhance(con)
    return ImageEnhance.Brightness(im).enhance(bri)


def contours(seed, alpha=70, spacing=0.09, width=0.012):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    x, y = xx / W, yy / H
    f = (np.sin(x * 5.1 + seed) * np.cos(y * 4.3 - seed) + 0.6 * np.sin((x + y) * 7.7 + seed * 2)
         + 0.4 * np.cos(x * 11 - y * 3 + seed) + 1.2 * np.exp(-((x - 0.72) ** 2 + (y - 0.5) ** 2) * 6))
    frac = np.abs((f / spacing) % 1 - 0.5)
    a = np.clip(1 - frac / (width / spacing), 0, 1) * alpha
    L = np.zeros((H, W, 4), np.uint8); L[..., :3] = LIME; L[..., 3] = a.astype(np.uint8)
    return Image.fromarray(L, "RGBA")


def neon_ring(bg, c, r, col, w):
    L = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    ImageDraw.Draw(L).ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), outline=col + (255,), width=w)
    bg.alpha_composite(L.filter(ImageFilter.GaussianBlur(10))); bg.alpha_composite(L.filter(ImageFilter.GaussianBlur(4)))
    bg.alpha_composite(L)


def streaks(bg, n=26, seed=3):
    rng = np.random.default_rng(seed)
    L = Image.new("RGBA", bg.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for _ in range(n):
        y = rng.integers(420, 700); x = rng.integers(-200, W); ln = rng.integers(120, 520); wd = int(rng.integers(2, 5))
        for k in range(0, ln, 6):
            d.line([(x + k, y), (x + k + 6, y)], fill=MAG + (int(255 * (k / ln) ** 1.5),), width=wd)
    bg.alpha_composite(L.filter(ImageFilter.GaussianBlur(0.8)))


def neon_cover(hero, top, big, chip, seed=1.3):
    if len(top) > 2 or not big or len(big) > 12:
        raise ValueError("style allows 0-2 short top lines and one neon word of at most 12 characters")
    bg = Image.new("RGBA", (W, H), INK + (255,))
    bg.alpha_composite(contours(seed))
    c, r = (910, 360), 300
    neon_ring(bg, c, r + 18, MAG, 8)
    disc = fill(hero.convert("RGB"), 2 * r, 2 * r)
    m = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(m).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
    o = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0)); o.paste(disc, (0, 0), m)
    bg.alpha_composite(o, (c[0] - r, c[1] - r))
    neon_ring(bg, c, r + 46, LIME, 3)
    d = ImageDraw.Draw(bg)
    for i in range(0, 360, 10):
        a = math.radians(i); r1 = r + 60; r2 = r + (78 if i % 30 == 0 else 68)
        d.line([(c[0] + r1 * math.cos(a), c[1] + r1 * math.sin(a)), (c[0] + r2 * math.cos(a), c[1] + r2 * math.sin(a))], fill=LIME + (200,), width=3)
    streaks(bg)
    tsz = min([fit(t, 76, 540) for t in top] or [76])
    bsz = fit(big, 190 if len(top) >= 2 else 210, 700)
    y = max(36, (590 - (tsz * 1.25 * len(top) + bsz * 1.2)) / 2 - 10)
    for t in top:
        ImageDraw.Draw(bg).text((46, y), t, font=F(tsz), fill=WHITE); y += tsz * 1.25
    fb, by = F(bsz), y - bsz * 0.05
    L = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    ImageDraw.Draw(L).text((40, by), big, font=fb, fill=MAG + (255,), stroke_width=6, stroke_fill=MAG + (255,))
    gl = L.filter(ImageFilter.GaussianBlur(22)); bg.alpha_composite(gl); bg.alpha_composite(gl)
    ImageDraw.Draw(bg).text((40, by), big, font=fb, fill=LIME, stroke_width=7, stroke_fill=INK)
    fc = F(fit(chip, 20, 500, minsize=12)); cw = tw(chip, fc)
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((46, 612, 46 + cw + 36, 658), 23, outline=LIME, width=3)
    d.text((64, 635), chip, font=fc, fill=LIME, anchor="lm")
    d.text((W - 270, 34), "ORBITAL ATLAS", font=F(20), fill=MAG)
    return bg.convert("RGB")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--hero", required=True); p.add_argument("--crop"); p.add_argument("--grade", default="1.5,1.2,1.05")
    p.add_argument("--top", action="append", default=[]); p.add_argument("--big", required=True); p.add_argument("--chip", required=True)
    p.add_argument("--seed", type=float, default=1.3); p.add_argument("--out", required=True); p.add_argument("--overwrite", action="store_true")
    a = p.parse_args(argv)
    if os.path.exists(a.out) and not a.overwrite:
        print(json.dumps({"ok": False, "error": f"{a.out} exists; pass --overwrite"})); return 1
    hero = Image.open(a.hero).convert("RGB")
    if a.crop:
        x0, y0, x1, y1 = (float(v) for v in a.crop.split(","))
        hero = hero.crop((int(x0 * hero.width), int(y0 * hero.height), int(x1 * hero.width), int(y1 * hero.height)))
    hero = grade(hero, *(float(v) for v in a.grade.split(",")))
    try:
        im = neon_cover(hero, a.top, a.big, a.chip, a.seed)
    except ValueError as ex:
        print(json.dumps({"ok": False, "error": str(ex)})); return 1
    tmp = a.out + ".tmp.jpg"
    im.save(tmp, quality=92); os.replace(tmp, a.out)
    print(json.dumps({"ok": True, "out": a.out, "top": a.top, "big": a.big, "chip": a.chip})); return 0


if __name__ == "__main__":
    sys.exit(main())
