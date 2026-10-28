#!/usr/bin/env python3
"""EP007 cover drafts (docs/THUMBNAIL_STYLE_GUIDE.md). Real NASA pixels only; allowed: crop, scale, grade,
vignette and the annotation layer (headline, ring, arrow, badges). Nothing is painted into the imagery.
A: archetype C (real image + ring), "IT SHOULDN'T BE HERE"  - quote from NASA's project scientist.
B: archetype A (split), "CRACKED OPEN"  - outside of a sulfur stone (PIA26308) | crystals inside a crushed one (PIA26309)."""
import os, sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, "assets", "src")
ANTON = "/home/claude/fonts/Anton-Regular.ttf"
W, H = 1280, 720; WHITE, GOLD, BLACK, RED = (255, 255, 255), (255, 210, 30), (0, 0, 0), (229, 50, 45)


def grade(im, sat=1.55, con=1.25, bri=1.08):
    im = ImageOps.autocontrast(im, cutoff=0.5, preserve_tone=True)
    im = ImageEnhance.Color(im).enhance(sat); im = ImageEnhance.Contrast(im).enhance(con)
    im = ImageEnhance.Brightness(im).enhance(bri)
    vig = Image.new("L", im.size, 0); d = ImageDraw.Draw(vig)
    d.ellipse((-im.width * .2, -im.height * .15, im.width * 1.2, im.height * 1.25), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(80))
    return Image.composite(im, ImageEnhance.Brightness(im).enhance(0.45), vig)


def cover_crop(im, cx, cy, w):
    h = w * 9 / 16
    return im.crop((int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2))).resize((W, H), Image.LANCZOS)


def headline(base, parts, size, y):
    """parts: [(text, color)], centred, Anton, black outline + shadow."""
    f = ImageFont.truetype(ANTON, size); st = 9
    widths = [f.getbbox(t, stroke_width=st)[2] for t, _ in parts]; gap = 26
    total = sum(widths) + gap * (len(parts) - 1)
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x = (W - total) / 2
    for (t, c), w in zip(parts, widths):
        d.text((x, y), t, font=f, fill=c, stroke_width=st, stroke_fill=BLACK); x += w + gap
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 200), mask=lay.split()[3])
    out = base.convert("RGBA"); out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)), (8, 10)); out.alpha_composite(lay)
    return out


def badge(img, xy, text, fill=(20, 20, 24, 230), color=WHITE, size=40):
    d = ImageDraw.Draw(img); f = ImageFont.truetype(ANTON, size)
    w = d.textlength(text, font=f); x, y = xy
    d.rounded_rectangle([x, y, x + w + 36, y + size + 22], 12, fill=fill)
    d.text((x + 18, y + 6), text, font=f, fill=color)


def cover_a():
    im = Image.open(os.path.join(SRC, "PIA26309.png")).convert("RGB")
    base = grade(cover_crop(im, 900, 850, 1500), sat=1.7)
    out = headline(base, [("IT SHOULDN'T BE", WHITE), ("HERE", GOLD)], 132, 14)
    d = ImageDraw.Draw(out)
    d.ellipse([400, 250, 860, 600], outline=RED, width=12)            # the yellow crystal mass in the crushed rock
    badge(out, (40, 610), "FIRST EVER ON MARS", fill=(229, 50, 45, 235))
    return out.convert("RGB")


def cover_b():
    out_im = Image.open(os.path.join(SRC, "PIA26308.png")).convert("RGB")
    in_im = Image.open(os.path.join(SRC, "PIA26309.png")).convert("RGB")
    left = grade(out_im.crop((260, 120, 260 + 900, 120 + 1012)).resize((W // 2, H), Image.LANCZOS), sat=1.25, bri=1.0)
    right = grade(in_im.crop((420, 560, 420 + 900, 560 + 1012)).resize((W // 2, H), Image.LANCZOS), sat=2.4)
    base = Image.new("RGB", (W, H)); base.paste(left, (0, 0)); base.paste(right, (W // 2, 0))
    d = ImageDraw.Draw(base); d.line([(W // 2, 150), (W // 2, H)], fill=WHITE, width=6)
    out = headline(base, [("CRACKED", WHITE), ("OPEN", GOLD)], 140, 8)
    d = ImageDraw.Draw(out)
    pts = [(470 + i * 6, 430 - 60 * (1 - ((i - 25) / 25) ** 2)) for i in range(51)]
    d.line(pts, fill=RED, width=14, joint="curve")
    d.polygon([(800, 445), (760, 395), (745, 455)], fill=RED)
    badge(out, (40, 610), "OUTSIDE"); badge(out, (W // 2 + 40, 610), "INSIDE", fill=(255, 210, 30, 240), color=BLACK)
    return out.convert("RGB")


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "covers"), exist_ok=True)
    for name, fn in (("EP007_cover_A.jpg", cover_a), ("EP007_cover_B.jpg", cover_b)):
        p = os.path.join(HERE, "covers", name); fn().save(p, quality=90); print(p)
