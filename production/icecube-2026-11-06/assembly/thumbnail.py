#!/usr/bin/env python3
"""IceCube cover, 1280x720, channel style (orbit/aerial hero + data overlay, archetype C).
Top: the real IceCube Lab photo (Christopher Michel, CC BY-SA 4.0; this adapted cover is therefore
offered under CC BY-SA 4.0 too). Below the snow line: an original schematic of the sensor strings,
marked SCHEMATIC. Headline: TELESCOPE / UNDER THE ICE (key words yellow).
usage: thumbnail.py P01.jpg out.jpg"""
import sys, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H = 1280, 720
FI = "/usr/share/fonts/opentype/inter/"
SNOW = 372  # y of the snow line on the cover

src = Image.open(sys.argv[1]).convert("RGB")
# crop: building on the right, sky above for the headline. 3840x2625 source.
box = (380, 300, 380 + 3460, 300 + int(3460 * SNOW / W))
top = src.crop(box).resize((W, SNOW), Image.LANCZOS)
top = ImageEnhance.Color(top).enhance(1.45)
top = ImageEnhance.Contrast(top).enhance(1.18)
img = Image.new("RGB", (W, H))
img.paste(top, (0, 0))

# under the snow: deep glowing ice
ice = Image.new("RGB", (W, H - SNOW))
d = ImageDraw.Draw(ice)
for y in range(H - SNOW):
    u = y / (H - SNOW)
    d.line([(0, y), (W, y)], fill=(int(8 + 10 * (1 - u)), int(70 - 40 * u), int(140 - 60 * u)))
img.paste(ice, (0, SNOW))
d = ImageDraw.Draw(img)
d.rectangle([0, SNOW - 4, W, SNOW + 10], fill=(236, 246, 255))  # snow crust

# sensor strings, schematic: glow layer + crisp dots
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
crisp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(crisp)
cols = [560 + i * 52 for i in range(13)]
random.seed(3)
for i, x in enumerate(cols):
    cd.line([(x, SNOW + 10), (x, H - 40)], fill=(150, 220, 255, 150), width=2)
    for k in range(9):
        y = 470 + k * 26
        hot = (abs(i - 7) + abs(k - 4)) < 4
        col = (255, 214, 70) if hot else (120, 235, 255)
        r = 7 if hot else 5
        gd.ellipse([x - 16, y - 16, x + 16, y + 16], fill=col + (150 if hot else 90,))
        cd.ellipse([x - r, y - r, x + r, y + r], fill=col + (255,))
glow = glow.filter(ImageFilter.GaussianBlur(10))
img = img.convert("RGBA"); img.alpha_composite(glow); img.alpha_composite(crisp)
d = ImageDraw.Draw(img)

# depth bracket (gold) + badge
x0 = 1260 - 40
d.line([(x0 - 18, 470), (x0 - 18, 678)], fill=(255, 200, 60, 255), width=5)
for y in (470, 678):
    d.line([(x0 - 34, y), (x0 - 2, y)], fill=(255, 200, 60, 255), width=5)
fb = ImageFont.truetype(FI + "Inter-Black.otf", 34)
def badge(text, x, y, anchor_right=True):
    l, t, r, b = d.textbbox((0, 0), text, font=fb)
    w, h = r - l + 30, b - t + 20
    bx = x - w if anchor_right else x
    d.rounded_rectangle([bx, y, bx + w, y + h], 12, fill=(12, 18, 30, 230))
    d.text((bx + 15 - l, y + 10 - t), text, font=fb, fill=(255, 255, 255, 255))
badge("2.5 KM DOWN", 48, 520, anchor_right=False)
fs = ImageFont.truetype(FI + "Inter-Bold.otf", 22)
d.text((40, H - 46), "SCHEMATIC · NOT TO SCALE", font=fs, fill=(200, 225, 245, 255))

# headline: heavy uppercase, white + yellow, thick outline + shadow
def head(text, y, size, col):
    f = ImageFont.truetype(FI + "Inter-Black.otf", size)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((48 + 6, y + 10), text, font=f, fill=(0, 0, 0, 220), stroke_width=10, stroke_fill=(0, 0, 0, 220))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)))
    ImageDraw.Draw(img).text((48, y), text, font=f, fill=col, stroke_width=8, stroke_fill=(0, 0, 0, 255))
head("TELESCOPE", 26, 128, (255, 255, 255, 255))
head("UNDER THE ICE", 168, 128, (255, 210, 30, 255))

img.convert("RGB").save(sys.argv[2], quality=92)
