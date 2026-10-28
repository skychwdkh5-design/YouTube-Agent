"""EP007 visuals: crops of the NASA originals (native pixels, never upscaled here) and original
explanatory graphics. All drawing is done in 1920x1080 design units at 2x (3840x2160)."""
import math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "assets", "src")
S = 2                                     # supersample factor
W, H = 1920 * S, 1080 * S
BG = (14, 15, 20); RUST = (193, 68, 14); YEL = (255, 210, 30); WHITE = (245, 245, 245)
GREY = (160, 165, 175); RED = (229, 50, 45); CYAN = (90, 200, 230)

FILES = {"PIA26309": "PIA26309.png", "PIA26307": "PIA26307.jpg", "PIA26308": "PIA26308.png",
         "PIA26245": "PIA26245.tif", "PIA26363": "PIA26363_full.tif", "PIA26410": "PIA26410.jpg",
         "PIA26366": "PIA26366.tif", "PIA26210": "PIA26210.tif", "PIA26367": "PIA26367.jpg",
         "PIA26471": "PIA26471.jpg"}
CREDIT = {"PIA26245": "NASA/JPL-Caltech/University of Arizona"}
_cache = {}


def src(pid):
    if pid not in _cache:
        _cache[pid] = Image.open(os.path.join(SRC, FILES[pid])).convert("RGB")
    return _cache[pid]


def font(style, px):
    names = {"black": "Inter-Black.otf", "bold": "Inter-Bold.otf", "semi": "Inter-SemiBold.otf",
             "reg": "Inter-Regular.otf", "med": "Inter-Medium.otf"}
    return ImageFont.truetype(f"/usr/share/fonts/opentype/inter/{names[style]}", int(px))


# ---------------- photo crops ----------------
def crop_still(pid, y):
    im = src(pid); w, h = im.size
    ch = round(w * 9 / 16)
    top = round((h - ch) * y)
    return im.crop((0, top, w, top + ch))


_masks = {}


def valid_mask(pid):
    """Preview-scale mask of real pixels (mosaic gaps are pure black / pure white padding)."""
    if pid not in _masks:
        im = src(pid); w, h = im.size
        pv = im.resize((2400, round(2400 * h / w)), Image.BILINEAR).convert("L")
        import numpy as np
        a = np.asarray(pv)
        # mosaic gaps are large flat areas; morphological opening drops small dark shadows on hardware/rocks
        inv = Image.fromarray(((a <= 4) | (a >= 254)).astype("uint8") * 255)
        inv = inv.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(11))
        _masks[pid] = np.asarray(inv) < 128
    return _masks[pid]


def fit_box(pid, box, min_src_w=1920, aspect=9/16):
    """Nearest window to `box` with essentially no mosaic gap; never below 1920 source px wide."""
    import numpy as np
    m = valid_mask(pid); H2, W2 = m.shape
    f = src(pid).width / 2400
    x, y, bw = box
    min_src_w = min_src_w if aspect < 1 else 1080
    best = None
    for scale in (1.0, 0.9, 0.8, 0.7, 0.6):
        w = bw * scale
        if w * f < min_src_w and scale < 1.0:
            break
        h = w * aspect
        for dx in range(-480, 481, 12):
            for dy in range(-300, 301, 12):
                cx, cy = x + (bw - w) / 2 + dx, y + (bw * aspect - h) / 2 + dy
                if cx < 0 or cy < 0 or cx + w > W2 or cy + h > H2:
                    continue
                win = m[int(cy):int(cy + h), int(cx):int(cx + w)]
                bad = 1 - win.mean()
                if bad <= 0.004:
                    cost = abs(dx) + abs(dy) + (1 - scale) * 800
                    if best is None or cost < best[0]:
                        best = (cost, [cx, cy, w])
        if best:
            return best[1]
    raise ValueError(f"no clean window near {box} in {pid}")


def crop_pano(pid, box):
    im = src(pid); w, h = im.size
    f = w / 2400
    x, y, bw = fit_box(pid, box)
    bh = bw * 9 / 16
    c = im.crop((round(x * f), round(y * f), round((x + bw) * f), round((y + bh) * f)))
    if c.width > 3840:
        c = c.resize((3840, 2160), Image.LANCZOS)
    return c


def crop_still_v(pid, x):
    im = src(pid); w, h = im.size
    cw = round(h * 9 / 16)
    left = round((w - cw) * x)
    return im.crop((left, 0, left + cw, h))


def crop_pano_v(pid, box):
    im = src(pid); f = im.width / 2400
    x, y, bw = fit_box(pid, box, aspect=16 / 9)
    c = im.crop((round(x * f), round(y * f), round((x + bw) * f), round((y + bw * 16 / 9) * f)))
    if c.height > 3840:
        c = c.resize((2160, 3840), Image.LANCZOS)
    return c


def label(img, text, sub=None):
    """Lower-left tag inside the 8 % safe area (stays visible through a 1.15x zoom)."""
    img = img.copy(); d = ImageDraw.Draw(img, "RGBA")
    k = (img.width / 1920) if img.width > img.height else (img.width / 1080) * 1.25
    f1 = font("black", 34 * k); f2 = font("semi", 24 * k)
    x0, y0 = int(0.085 * img.width), int((0.70 if img.width > img.height else 0.13) * img.height)
    tw = d.textlength(text, font=f1); sw = d.textlength(sub, font=f2) if sub else 0
    bw = max(tw, sw) + 44 * k; bh = (64 if not sub else 104) * k
    d.rectangle([x0, y0, x0 + bw, y0 + bh], fill=(10, 10, 14, 175))
    d.rectangle([x0, y0, x0 + 8 * k, y0 + bh], fill=YEL + (255,))
    d.text((x0 + 26 * k, y0 + 12 * k), text, font=f1, fill=YEL)
    if sub:
        d.text((x0 + 26 * k, y0 + 60 * k), sub, font=f2, fill=WHITE)
    return img


# ---------------- graphics helpers ----------------
def canvas(bg=BG):
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im, "RGBA")
    # subtle vignette-free gradient band for depth
    for i in range(0, H, 4):
        a = int(18 * (1 - i / H))
        d.rectangle([0, i, W, i + 4], fill=(193, 68, 14, a))
    return im, d


def T(d, xy, text, style="bold", size=40, fill=WHITE, anchor="la"):
    d.text((xy[0] * S, xy[1] * S), text, font=font(style, size * S), fill=fill, anchor=anchor)


def tag(d, xy, text, fill=YEL):
    f = font("black", 26 * S)
    x, y = xy[0] * S, xy[1] * S
    w = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x + w + 36 * S, y + 50 * S], 10 * S, fill=(30, 32, 40, 255), outline=fill, width=3 * S)
    d.text((x + 18 * S, y + 25 * S), text, font=f, fill=fill, anchor="lm")


def footer(d, text):
    T(d, (96, 1000), text, "med", 24, GREY)


def R(d, box, **kw):
    d.rounded_rectangle([v * S for v in box], radius=kw.pop("r", 14) * S, **kw)


def L(d, pts, fill, width):
    d.line([(x * S, y * S) for x, y in pts], fill=fill, width=int(width * S), joint="curve")


def arrow(d, a, b, fill=YEL, width=8, head=26):
    L(d, [a, b], fill, width)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    p1 = (b[0] - head * math.cos(ang - 0.45), b[1] - head * math.sin(ang - 0.45))
    p2 = (b[0] - head * math.cos(ang + 0.45), b[1] - head * math.sin(ang + 0.45))
    d.polygon([(b[0] * S, b[1] * S), (p1[0] * S, p1[1] * S), (p2[0] * S, p2[1] * S)], fill=fill)


def paste_photo(im, pid, box, crop=None):
    """Paste a real image into box (design units) at native-or-lower resolution, framed."""
    p = src(pid) if crop is None else src(pid).crop(crop)
    x, y, w, h = [v * S for v in box]
    sc = min(w / p.width, h / p.height)
    q = p.resize((int(p.width * sc), int(p.height * sc)), Image.LANCZOS)
    ox, oy = x + (w - q.width) // 2, y + (h - q.height) // 2
    im.paste(q, (ox, oy))
    ImageDraw.Draw(im).rectangle([ox - 3 * S, oy - 3 * S, ox + q.width + 3 * S, oy + q.height + 3 * S], outline=(255, 255, 255), width=2 * S)
    return (ox / S, oy / S, q.width / S, q.height / S, sc / S)


def crystals_panel(im, box):
    # tight 4:5 window on the real Mastcam crystals (native pixels)
    return paste_photo(im, "PIA26309", box, crop=(250, 250, 1530, 1590))


# ---------------- graphics ----------------
def g_first(step=0):
    im, d = canvas()
    crystals_panel(im, (1060, 110, 760, 860))
    T(d, (110, 300), "PURE", "black", 150, YEL)
    T(d, (110, 450), "SULFUR", "black", 150, YEL)
    T(d, (114, 640), "First time found on Mars", "bold", 52, WHITE)
    T(d, (114, 712), "Identified by the APXS instrument on Curiosity's arm", "med", 32, GREY)
    footer(d, "Image: NASA/JPL-Caltech/MSSS · Source: NASA/JPL, July 18, 2024")
    return im


def g_title(step=0):
    im, d = canvas()
    crystals_panel(im, (1060, 110, 760, 860))
    tag(d, (110, 250), "ORBITAL ATLAS")
    T(d, (110, 340), "THE CRYSTALS", "black", 104, WHITE)
    T(d, (110, 460), "THAT SHOULDN'T", "black", 104, WHITE)
    T(d, (110, 580), "BE THERE", "black", 104, YEL)
    T(d, (114, 730), "Curiosity, Gediz Vallis, Mars", "semi", 38, GREY)
    return im


def g_where(step=0):
    im, d = canvas()
    T(d, (96, 90), "WHERE IT HAPPENED", "black", 54, YEL)
    # panel 1: Mars disk (illustration)
    cx, cy, r = 330, 520, 200
    for i in range(r, 0, -2):
        t = i / r
        col = (int(150 + 60 * (1 - t)), int(60 + 30 * (1 - t)), int(25 + 10 * (1 - t)))
        d.ellipse([(cx - i) * S, (cy - i) * S, (cx + i) * S, (cy + i) * S], fill=col)
    gx, gy = cx + 70, cy - 10
    d.ellipse([(gx - 22) * S, (gy - 22) * S, (gx + 22) * S, (gy + 22) * S], outline=YEL, width=5 * S)
    T(d, (cx, cy + 250), "MARS", "black", 40, WHITE, "ma")
    T(d, (cx, cy + 300), "Gale crater, near the equator", "med", 28, GREY, "ma")
    arrow(d, (590, 520), (700, 520), WHITE, 6, 20)
    # panel 2: crater with central mountain (plan view, schematic)
    cx2 = 960
    d.ellipse([(cx2 - 200) * S, (cy - 200) * S, (cx2 + 200) * S, (cy + 200) * S], fill=(120, 55, 25), outline=(210, 120, 70), width=8 * S)
    d.ellipse([(cx2 - 60) * S, (cy - 70) * S, (cx2 + 90) * S, (cy + 80) * S], fill=(170, 90, 45))
    T(d, (cx2, cy + 250), "GALE CRATER", "black", 40, WHITE, "ma")
    T(d, (cx2, cy + 300), "about 154 km (96 mi) wide", "med", 28, GREY, "ma")
    T(d, (cx2 + 15, cy + 5), "Mount Sharp", "bold", 26, WHITE, "mm")
    arrow(d, (1220, 520), (1330, 520), WHITE, 6, 20)
    # panel 3: mountain profile
    base = 700
    pts = [(1380, base), (1480, 640), (1560, 600), (1640, 470), (1700, 380), (1740, 330), (1800, 400), (1840, base)]
    d.polygon([(x * S, y * S) for x, y in pts], fill=(170, 90, 45))
    for k in range(6):
        yy = base - 50 - k * 55
        L(d, [(1400 + k * 30, yy), (1820 - k * 10, yy)], (200, 120, 70, 120), 3)
    d.ellipse([(1545) * S, (590) * S, (1575) * S, (620) * S], fill=YEL)
    L(d, [(1560, 590), (1560, 300)], YEL, 3)
    T(d, (1560, 255), "Gediz Vallis", "bold", 30, YEL, "ma")
    T(d, (1610, base + 50), "MOUNT SHARP", "black", 40, WHITE, "ma")
    T(d, (1610, base + 100), "about 5 km (3 mi) tall", "med", 28, GREY, "ma")
    footer(d, "Schematic illustration, not to scale · Facts: NASA/JPL")
    return im


TL = [("MAY 30, 2024", "Rock crushed", "sol 4,200"), ("JUNE 4", "Arm camera close-up", "MAHLI"),
      ("JUNE 7", "Mast camera view", "Mastcam"), ("JUNE 18", "Drill hole #41", "\"Mammoth Lakes\""),
      ("OCT. 11, 2024", "Last look", "Mastcam"), ("AUG. 2026", "Science paper", "VanBommel et al.")]


def g_timeline(step=1):
    im, d = canvas()
    T(d, (96, 90), "WHAT HAPPENED, WHEN", "black", 54, YEL)
    hi = {1: {0, 1, 2}, 2: {3}, 3: {5}}[step]
    x0, x1, y = 150, 1770, 520
    L(d, [(x0, y), (x1, y)], (90, 95, 110), 6)
    for i, (dt, what, sub) in enumerate(TL):
        x = x0 + (x1 - x0) * i / (len(TL) - 1)
        on = i in hi
        col = YEL if on else (120, 125, 135)
        d.ellipse([(x - 16) * S, (y - 16) * S, (x + 16) * S, (y + 16) * S], fill=col)
        T(d, (x, y - 110), dt, "black", 30, col, "ma")
        T(d, (x, y + 50), what, "bold", 30, WHITE if on else (150, 150, 160), "ma")
        T(d, (x, y + 95), sub, "med", 24, GREY, "ma")
    if step == 1:
        R(d, (480, 760, 1440, 860), fill=(40, 20, 15, 255), outline=RED, width=3 * S)
        T(d, (960, 810), "No video of the moment it cracked: only photos taken afterwards", "bold", 30, WHITE, "mm")
    footer(d, "Dates: NASA/JPL releases 2024-100, 2024-160; Science 393:820 (2026)")
    return im


def g_scale(step=0):
    im, d = canvas()
    ox, oy, w, h, sc = paste_photo(im, "PIA26309", (120, 120, 1140, 820))
    # bracket across the crystal patch (caption: fragments ~13 cm across, left to right)
    p0 = ox + 230 * 1.977 * sc * S / S
    a = ox + w * 0.13; b = ox + w * 0.82; yy = oy + h + 40
    L(d, [(a, yy - 20), (a, yy), (b, yy), (b, yy - 20)], YEL, 6)
    T(d, ((a + b) / 2, yy + 20), "≈ 13 cm  ·  5 in", "black", 40, YEL, "ma")
    T(d, (1330, 380), "Scale", "black", 60, WHITE)
    T(d, (1330, 470), "The broken pieces", "semi", 36, GREY)
    T(d, (1330, 520), "span about 13 cm,", "semi", 36, GREY)
    T(d, (1330, 570), "left to right.", "semi", 36, GREY)
    T(d, (1330, 660), "About the width", "semi", 36, WHITE)
    T(d, (1330, 710), "of a hand.", "semi", 36, WHITE)
    footer(d, "Mastcam, June 7, 2024 · NASA/JPL-Caltech/MSSS · bracket approximate, per NASA caption")
    return im


def g_apxs(step=1):
    im, d = canvas()
    T(d, (96, 90), "HOW THEY KNEW: APXS", "black", 54, YEL)
    T(d, (98, 160), "Alpha Particle X-ray Spectrometer, on Curiosity's robotic arm", "med", 30, GREY)
    # rock + arm (schematic)
    d.polygon([(v[0] * S, v[1] * S) for v in [(160, 860), (260, 700), (520, 660), (700, 720), (760, 860)]], fill=(150, 80, 40))
    d.polygon([(v[0] * S, v[1] * S) for v in [(330, 760), (420, 700), (520, 720), (560, 790), (430, 830)]], fill=(220, 200, 60))
    L(d, [(900, 260), (700, 380), (520, 520)], (200, 205, 215), 26)
    R(d, (440, 520, 600, 620), fill=(200, 205, 215, 255), r=10)
    T(d, (620, 560), "APXS", "black", 30, WHITE)
    if step >= 2:
        for i, xx in enumerate([470, 520, 570]):
            arrow(d, (xx, 625), (xx - 10 + i * 10, 700), CYAN, 5, 16)
            arrow(d, (xx + 10, 700), (xx + 20, 630), YEL, 5, 16)
        T(d, (640, 640), "particles and X-rays in", "semi", 26, CYAN)
        T(d, (640, 680), "element signatures out", "semi", 26, YEL)
    if step >= 3:
        x0, y0 = 1040, 840
        L(d, [(x0, y0), (1800, y0)], WHITE, 3); L(d, [(x0, y0), (x0, 300)], WHITE, 3)
        bars = [("Na", 30), ("Mg", 40), ("Si", 55), ("S", 420), ("Cl", 25), ("Ca", 35), ("Fe", 45)]
        for i, (el, hgt) in enumerate(bars):
            x = x0 + 60 + i * 100
            col = YEL if el == "S" else (120, 125, 135)
            R(d, (x, y0 - hgt, x + 60, y0), fill=col + (255,), r=6)
            T(d, (x + 30, y0 + 15), el, "black", 30, col, "ma")
        T(d, (1420, 270), "Sulfur dominates", "black", 40, YEL, "ma")
        T(d, (1420, 920), "Illustration of the idea, not the measured spectrum", "med", 24, GREY, "ma")
    footer(d, "Schematic · APXS identification: NASA/JPL (PIA26307)")
    return im


def volcano(d, x, y, sc=1.0):
    d.polygon([((x - 220 * sc) * S, y * S), ((x - 40 * sc) * S, (y - 220 * sc) * S), ((x + 40 * sc) * S, (y - 220 * sc) * S), ((x + 220 * sc) * S, y * S)], fill=(95, 80, 75))
    for i in range(5):
        d.ellipse([((x - 50 + i * 22) * S), ((y - 235 - i * 30) * S), ((x - 10 + i * 22) * S), ((y - 205 - i * 30) * S)], fill=(200, 200, 205, 120))
    d.ellipse([(x - 70) * S, (y - 210) * S, (x - 20) * S, (y - 185) * S], fill=YEL)
    d.ellipse([(x + 15) * S, (y - 200) * S, (x + 60) * S, (y - 178) * S], fill=YEL)


def spring(d, x, y):
    d.ellipse([(x - 200) * S, (y - 60) * S, (x + 200) * S, (y + 40) * S], fill=(70, 150, 170))
    d.ellipse([(x - 210) * S, (y - 70) * S, (x + 210) * S, (y + 50) * S], outline=YEL, width=10 * S)
    for i in range(4):
        d.ellipse([(x - 60 + i * 35) * S, (y - 150 - i * 25) * S, (x - 20 + i * 35) * S, (y - 115 - i * 25) * S], fill=(220, 220, 225, 110))


def g_earth(step=1):
    im, d = canvas()
    if step == 1:
        T(d, (96, 90), "ON EARTH", "black", 54, YEL)
        volcano(d, 960, 820, 1.4)
        T(d, (960, 880), "Native sulfur crusts form around volcanic vents", "bold", 40, WHITE, "ma")
        footer(d, "Illustration")
        return im
    T(d, (96, 90), "WHERE PURE SULFUR USUALLY FORMS", "black", 54, YEL)
    volcano(d, 330, 700, 0.9); T(d, (330, 760), "Volcanoes", "bold", 38, WHITE, "ma")
    spring(d, 860, 640); T(d, (860, 760), "Hot springs", "bold", 38, WHITE, "ma")
    R(d, (1200, 330, 1820, 820), fill=(30, 32, 40, 255), outline=RED, width=3 * S)
    T(d, (1510, 400), "MOUNT SHARP", "black", 44, WHITE, "ma")
    T(d, (1510, 520), "No evidence", "black", 60, RED, "ma")
    T(d, (1510, 600), "of either nearby", "bold", 40, WHITE, "ma")
    T(d, (1510, 700), "per NASA/JPL, 2024", "med", 26, GREY, "ma")
    footer(d, "Illustration · Source: NASA/JPL release 2024-160")
    return im


def g_sulfate(step=1):
    im, d = canvas()
    T(d, (96, 90), "SULFUR ON MARS: TWO VERY DIFFERENT THINGS", "black", 50, YEL)
    R(d, (120, 230, 900, 860), fill=(30, 32, 40, 255), outline=(150, 155, 165), width=3 * S)
    T(d, (510, 280), "SULFATES", "black", 54, WHITE, "ma")
    T(d, (510, 350), "common in this region", "semi", 30, GREY, "ma")
    for i, (f, n) in enumerate([("CaSO₄", "calcium sulfate"), ("MgSO₄", "magnesium sulfate")]):
        T(d, (510, 450 + i * 150), f, "black", 64, (230, 150, 110), "ma")
        T(d, (510, 530 + i * 150), n, "med", 28, GREY, "ma")
    T(d, (510, 780), "sulfur bound to oxygen and metals", "bold", 30, WHITE, "ma")
    if step >= 2:
        R(d, (1020, 230, 1800, 860), fill=(40, 34, 10, 255), outline=YEL, width=4 * S)
        T(d, (1410, 280), "ELEMENTAL SULFUR", "black", 54, YEL, "ma")
        T(d, (1410, 350), "found at Gediz Vallis", "semi", 30, GREY, "ma")
        T(d, (1410, 470), "S", "black", 200, YEL, "ma")
        T(d, (1410, 720), "just sulfur, on its own", "bold", 32, WHITE, "ma")
        T(d, (1410, 775), "forms only in a narrow range of conditions", "med", 28, GREY, "ma")
    footer(d, "Source: NASA/JPL release 2024-100")
    return im


def g_quote(step=0):
    im, d = canvas()
    crystals_panel(im, (1180, 150, 640, 760))
    T(d, (110, 250), "“", "black", 200, YEL)
    T(d, (120, 420), "It shouldn't be there,", "black", 70, WHITE)
    T(d, (120, 510), "so now we have to", "black", 70, WHITE)
    T(d, (120, 600), "explain it.”", "black", 70, YEL)
    T(d, (124, 730), "Ashwin Vasavada", "bold", 38, WHITE)
    T(d, (124, 785), "Curiosity project scientist, NASA JPL (July 2024)", "med", 30, GREY)
    return im


def g_hirise(step=1):
    im, d = canvas()
    T(d, (96, 90), "THE VIEW FROM ORBIT", "black", 54, YEL)
    ox, oy, w, h, sc = paste_photo(im, "PIA26245", (100, 170, 1060, 820))
    T(d, (1240, 300), "HiRISE camera", "black", 44, WHITE)
    T(d, (1240, 360), "Mars Reconnaissance Orbiter", "semi", 32, GREY)
    T(d, (1240, 440), "Dec. 29, 2023 · enhanced color", "med", 28, GREY)
    if step >= 2:
        rx, ry = ox + 510 * sc * S / S * 1, oy + 400 * sc * S / S
        rx, ry = ox + 510 * (w / 1013), oy + 400 * (h / 804)
        d.ellipse([(rx - 34) * S, (ry - 34) * S, (rx + 34) * S, (ry + 34) * S], outline=YEL, width=5 * S)
        arrow(d, (rx + 200, ry - 150), (rx + 40, ry - 35), YEL, 6, 22)
        T(d, (rx + 210, ry - 190), "CURIOSITY", "black", 34, YEL)
        T(d, (1240, 560), "Sees the rover:", "bold", 36, WHITE)
        T(d, (1240, 610), "yes", "black", 44, YEL)
        T(d, (1240, 700), "Resolves the sulfur", "bold", 36, WHITE)
        T(d, (1240, 750), "stones: no", "black", 44, RED)
    footer(d, "Image PIA26245: NASA/JPL-Caltech/University of Arizona · stones not resolved: NASA/JPL 2024-160")
    return im


def g_question(step=0):
    im, d = canvas()
    T(d, (960, 420), "HOW DID PURE SULFUR", "black", 96, WHITE, "ma")
    T(d, (960, 540), "GET HERE?", "black", 96, YEL, "ma")
    return im


def g_age(step=0):
    im, d = canvas()
    T(d, (96, 90), "HOW OLD?", "black", 54, YEL)
    T(d, (960, 250), "≈ 3 BILLION YEARS", "black", 110, YEL, "ma")
    T(d, (960, 400), "estimated age of the sulfur stones", "semi", 38, WHITE, "ma")
    x0, x1, y = 200, 1720, 650
    L(d, [(x0, y), (x1, y)], (120, 125, 135), 8)
    for gy, lab in [(4.5, "4.5 billion years ago\nMars forms"), (0, "today")]:
        x = x1 - (x1 - x0) * gy / 4.5
        d.ellipse([(x - 12) * S, (y - 12) * S, (x + 12) * S, (y + 12) * S], fill=WHITE)
        for j, line in enumerate(lab.split("\n")):
            T(d, (x, y + 40 + j * 40), line, "med", 28, GREY, "ma")
    x = x1 - (x1 - x0) * 3 / 4.5
    d.ellipse([(x - 20) * S, (y - 20) * S, (x + 20) * S, (y + 20) * S], fill=YEL)
    T(d, (x, y - 80), "sulfur stones form (roughly)", "bold", 32, YEL, "ma")
    footer(d, "VanBommel et al., Science 393:820 (2026); Washington University in St. Louis release")
    return im


def section(d, top=300, bottom=880):
    cols = [(150, 85, 45), (170, 95, 50), (140, 75, 40), (160, 90, 48)]
    for i in range(4):
        yy = top + i * (bottom - top) / 4
        d.rectangle([180 * S, yy * S, 1740 * S, (yy + (bottom - top) / 4) * S], fill=cols[i])


def g_hypA(step=1):
    im, d = canvas()
    T(d, (96, 90), "IDEA 1 · PROPOSED IN SCIENCE (2026)", "black", 48, YEL)
    section(d, 330, 900)
    # magma
    d.ellipse([700 * S, 800 * S, 1220 * S, 1000 * S], fill=(230, 80, 20))
    T(d, (960, 880), "magma", "black", 34, WHITE, "ma")
    if step >= 1:
        for x in [800, 900, 1010, 1110]:
            arrow(d, (x, 800), (x + (960 - x) * 0.15, 520), (255, 230, 150), 6, 20)
        T(d, (1300, 640), "sulfur-rich gases rise", "bold", 34, WHITE)
    if step >= 2:
        d.rectangle([180 * S, 380 * S, 1740 * S, 470 * S], fill=(150, 175, 200))
        T(d, (200, 395), "frozen ground", "bold", 30, (20, 30, 45))
        d.ellipse([820 * S, 400 * S, 1100 * S, 470 * S], fill=YEL)
        T(d, (1300, 420), "gases cool, likely with water,", "bold", 32, WHITE)
        T(d, (1300, 465), "and leave pure sulfur", "bold", 32, YEL)
    if step >= 3:
        d.polygon([(700 * S, 330 * S), (1220 * S, 330 * S), (1100 * S, 430 * S), (820 * S, 430 * S)], fill=BG)
        T(d, (960, 250), "valley erodes: deposit exposed", "black", 40, YEL, "ma")
    footer(d, "Schematic of the authors' proposal, not to scale · VanBommel et al., Science 2026")
    return im


def g_hypB(step=1):
    im, d = canvas()
    T(d, (96, 90), "IDEA 2 · CONFERENCE ABSTRACTS (2026)", "black", 48, (240, 160, 90))
    # valley profile: upstream left high, downstream right low
    pts = [(150, 420), (500, 470), (900, 560), (1300, 660), (1770, 760), (1770, 900), (150, 900)]
    d.polygon([(x * S, y * S) for x, y in pts], fill=(150, 85, 45))
    d.polygon([(x * S, y * S) for x, y in [(150, 420), (500, 470), (500, 540), (150, 500)]], fill=(215, 190, 140))
    T(d, (180, 330), "upstream layer", "bold", 30, WHITE)
    d.arc([300 * S, 370 * S, 440 * S, 470 * S], 180, 360, fill=WHITE, width=5 * S)
    T(d, (370, 300), "impact", "black", 30, WHITE, "ma")
    L(d, [(440, 470), (900, 560), (1300, 660), (1560, 712)], YEL, 16)
    arrow(d, (1500, 700), (1600, 720), YEL, 16, 34)
    T(d, (1000, 480), "liquid sulfur flows ~4 km, then freezes", "bold", 34, YEL)
    if step >= 2:
        R(d, (130, 560, 760, 700), fill=(40, 20, 15, 255), outline=RED, width=3 * S)
        T(d, (445, 600), "Sulfur-rich? NOT MEASURED YET", "black", 32, RED, "ma")
        T(d, (445, 650), "the idea depends on it", "med", 26, WHITE, "ma")
    footer(d, "Schematic · Rapin et al., Maggioni et al., EGU26 / LPSC 2026 abstracts")
    return im


def g_notlife(step=0):
    im, d = canvas()
    T(d, (960, 330), "NOT EVIDENCE", "black", 120, WHITE, "ma")
    T(d, (960, 470), "OF LIFE", "black", 120, RED, "ma")
    T(d, (960, 680), "The team sees no sign that microbes played any role.", "bold", 40, WHITE, "ma")
    footer(d, "VanBommel et al., Science 2026; Washington University in St. Louis release")
    return im


def g_know(step=1):
    im, d = canvas()
    T(d, (96, 90), "WHERE IT STANDS", "black", 54, YEL)
    rows = [("What the stones are", True), ("Where they are", True), ("Roughly how old", True), ("How they formed", False)]
    show = {1: 0, 2: 3, 3: 4}[step]
    for i, (txt, ok) in enumerate(rows[:show]):
        y = 260 + i * 160
        col = (110, 210, 120) if ok else RED
        R(d, (300, y, 1620, y + 120), fill=(30, 32, 40, 255), outline=col, width=3 * S)
        T(d, (360, y + 60), "KNOWN" if ok else "OPEN", "black", 34, col, "lm")
        T(d, (620, y + 60), txt, "bold", 48, WHITE, "lm")
    if show == 0:
        T(d, (960, 520), "Known, and still open", "bold", 52, WHITE, "mm")
    return im


GRAPHICS = {k: v for k, v in globals().items() if k.startswith("g_")}


def make_graphic(name, step):
    im = GRAPHICS[name](step)
    return im


# ---------------- vertical (Shorts) cards, 1080x1920 design units at 2x ----------------
VW, VH = 1080 * S, 1920 * S


def vcanvas():
    im = Image.new("RGB", (VW, VH), BG); d = ImageDraw.Draw(im, "RGBA")
    for i in range(0, VH, 4):
        d.rectangle([0, i, VW, i + 4], fill=(193, 68, 14, int(18 * (1 - i / VH))))
    return im, d


def v_hirise(step=1):
    im, d = vcanvas()
    T(d, (540, 250), "FROM ORBIT", "black", 84, YEL, "ma")
    T(d, (540, 360), "HiRISE · Mars Reconnaissance Orbiter", "semi", 34, GREY, "ma")
    ox, oy, w, h, sc = paste_photo(im, "PIA26245", (60, 470, 960, 760))
    if step >= 2:
        rx, ry = ox + 510 * (w / 1013), oy + 400 * (h / 804)
        d.ellipse([(rx - 34) * S, (ry - 34) * S, (rx + 34) * S, (ry + 34) * S], outline=YEL, width=5 * S)
        arrow(d, (rx + 180, ry - 160), (rx + 40, ry - 35), YEL, 6, 22)
        T(d, (rx + 60, ry - 220), "CURIOSITY", "black", 40, YEL)
    T(d, (540, 1600), "Dec. 29, 2023 · enhanced color", "med", 30, GREY, "ma")
    T(d, (540, 1700), "NASA/JPL-Caltech/University of Arizona", "med", 26, GREY, "ma")
    return im


def v_title(step=0):
    im, d = vcanvas()
    paste_photo(im, "PIA26309", (90, 640, 900, 820), crop=(250, 250, 1530, 1590))
    T(d, (540, 260), "PURE SULFUR", "black", 110, YEL, "ma")
    T(d, (540, 400), "ON MARS", "black", 110, WHITE, "ma")
    T(d, (540, 1520), "First time ever found there", "bold", 46, WHITE, "ma")
    return im


def v_photo(pid, cx, head, sub, foot):
    im, d = vcanvas()
    p = src(pid); cw = min(p.width, 960)
    left = int((p.width - cw) * cx)
    paste_photo(im, pid, (40, 470, 1000, 1330), crop=(left, 0, left + cw, p.height))
    T(d, (540, 250), head, "black", 84, YEL, "ma")
    T(d, (540, 360), sub, "semi", 36, WHITE, "ma")
    T(d, (540, 1700), foot, "med", 26, GREY, "ma")
    return im


VGRAPHICS = {"v_hirise": v_hirise, "v_title": v_title,
             "v_mahli_a": lambda s=0: v_photo("PIA26307", 0.2, "YELLOW CRYSTALS", "arm camera close-up, June 2024", "MAHLI · NASA/JPL-Caltech/MSSS"),
             "v_mahli_b": lambda s=0: v_photo("PIA26307", 0.9, "PURE SULFUR", "identified by the rover's APXS", "MAHLI · NASA/JPL-Caltech/MSSS"),
             "v_snow": lambda s=0: v_photo("PIA26308", 0.5, "THE OUTSIDE", "white, full of holes", "\"Snow Lake\" · MAHLI · NASA/JPL-Caltech/MSSS")}
