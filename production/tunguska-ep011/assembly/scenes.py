"""EP011 scenes. Each scene(t, D, p) -> RGB 1920x1080 for local time t of a shot lasting D seconds.
Real sources: NASA EO Landsat 8 (2024-07-06) and the May 1929 Kulik expedition photo; everything else is original
painted illustration and is tagged as reconstruction / illustration on screen."""
import math, os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from paint import (W, H, clamp, seg, smooth, ease_in, ease_out, lerp, mix, font, noise, fbm, paint_texture, vgradient,
                   glow_sprite, tree_sprite, stamp, add_glow, camera, shadow_text, pill, grade)
import forest as F

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "sources")


def BD(im):
    """ImageDraw that alpha-blends semi-transparent colours onto an opaque canvas (plain Draw would overwrite alpha)."""
    d = ImageDraw.Draw(im)
    d.draw = Image.core.draw(im.im, 1)
    return d


YEL, WHT, INK = (255, 210, 63, 255), (255, 255, 255, 255), (244, 238, 226, 255)
CR_LS = "NASA EARTH OBSERVATORY / MICHALA GARRISON · LANDSAT 8 OLI, USGS · JULY 6, 2024"
CR_AR = "PHOTO: LEONID KULIK EXPEDITION, MAY 1929 · VIA NASA EARTH OBSERVATORY · PUBLIC DOMAIN"
ILL = "ILLUSTRATION · NOT TO SCALE"
REC = "RECONSTRUCTION · NOT FOOTAGE"


def tag_ill(img, text=ILL, a=1.0):
    pill(img, (W - 40, 36), text, 22, bg=(120, 52, 18, 200), anchor="r", alpha=a)


def credit(img, text, a=1.0):
    pill(img, (40, 36), text, 22, alpha=a)


def headline(img, lines, pos="bl", a=1.0, dx=0):
    """channel headline: uppercase Inter Black, first line big. lines = [(text, colour)]"""
    if a <= 0.01:
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if pos == "cover":  # thumbnail-size headline (cover A and frame 0 are the same composition)
        shadow_text(lay, (80 + dx, 70), lines[0][0], font("Inter-Black.otf", 230), lines[0][1], "la", stroke=8, blur=14)
        for k, (txt, col) in enumerate(lines[1:]):
            shadow_text(lay, (88 + dx, 330 + 120 * k), txt, font("Inter-Black.otf", 110), col, "la", stroke=6, blur=12)
        if a < 0.999:
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
        img.alpha_composite(lay)
        return
    right = pos.endswith("r")
    x = (W - 90 if right else 90) + dx
    n = len(lines)
    y0 = 170 if pos.startswith("t") else H - 130 - 92 - 66 * (n - 1)
    for k, (txt, col) in enumerate(lines):
        size = 84 if k == 0 else 52
        y = y0 + (0 if k == 0 else 100 + 66 * (k - 1))
        shadow_text(lay, (x, y), txt, font("Inter-Black.otf", size), col, "ra" if right else "la")
    if a < 0.999:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay)


def fade_io(t, D, i=0.35, o=0.35, d0=0.15):
    return smooth(seg(t, d0, d0 + i)) * (1 - smooth(seg(t, D - o - 0.05, D - 0.05)))


# ---------------------------------------------------------------- real images
@lru_cache(maxsize=1)
def landsat():
    im = Image.open(os.path.join(SRC, "russia_tunguskablast_oli_20240706_lrg.jpg")).convert("RGB")
    return im.resize((im.width * 2, im.height * 2), Image.LANCZOS)   # 2244 x 2182


LS_EPI = (534 * 2, 854 * 2)     # NASA EO label positions (720 px labelled version x 1.558, then x2)
LS_CHEKO = (288 * 2, 132 * 2)


def ls_view(t, D, p):
    src = landsat()
    u = smooth(seg(t, 0, D))
    z = lerp(p.get("z", (1.0, 1.0))[0], p.get("z", (1.0, 1.0))[1], u)
    c0 = p.get("c0", (0.5, 0.5)); c1 = p.get("c1", c0)
    cx = lerp(c0[0], c1[0], u) * src.width; cy = lerp(c0[1], c1[1], u) * src.height
    base = 1080 / 2182 * 1.0
    zoom = base * z * (1920 / 1080) * (2182 / 2244) if False else max(1920 / 2244, 1080 / 2182) * z
    half_w = W / zoom / 2; half_h = H / zoom / 2
    cx = clamp(cx, half_w, src.width - half_w); cy = clamp(cy, half_h, src.height - half_h)
    return camera(src, cx, cy, zoom), (cx, cy, zoom)


def to_screen(pt, cam):
    cx, cy, z = cam
    return (W / 2 + (pt[0] - cx) * z, H / 2 + (pt[1] - cy) * z)


def landsat_scene(t, D, p):
    img, cam = ls_view(t, D, p)
    img = img.convert("RGBA")
    a = fade_io(t, D)
    if p.get("desat"):
        k = smooth(seg(t, p["desat"][0], p["desat"][1]))
        g = img.convert("L").convert("RGBA")
        img = Image.blend(img, g, 0.85 * k)
    d = BD(img)
    if p.get("epi"):
        k = smooth(seg(t, p["epi"], p["epi"] + 0.6))
        x, y = to_screen(LS_EPI, cam)
        r = 26 + 10 * math.sin(t * 3)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 210, 63, int(255 * k)), width=5)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(255, 210, 63, int(255 * k)))
        pill(img, (x + 44, y - 26), "APPROX. EPICENTER, FROM FIELD SURVEYS", 24, alpha=k)
    if p.get("cheko"):
        k = smooth(seg(t, p["cheko"], p["cheko"] + 0.6))
        x, y = to_screen(LS_CHEKO, cam)
        d.ellipse([x - 46, y - 46, x + 46, y + 46], outline=(255, 255, 255, int(230 * k)), width=4)
        pill(img, (x + 62, y - 26), "LAKE CHEKO · IMPACT ORIGIN DEBATED", 24, alpha=k)
    for it in p.get("txt", []):
        k = smooth(seg(t, it.get("at", 0.2), it.get("at", 0.2) + 0.4)) * (1 - smooth(seg(t, it.get("until", D) - 0.4, it.get("until", D))))
        headline(img, it["lines"], it.get("pos", "bl"), k)
    credit(img, CR_LS, 1.0)
    if p.get("stamp"):
        pill(img, (W - 40, H - 90), p["stamp"], 30, bg=(10, 18, 34, 200), anchor="r", wt="Inter-Bold.otf")
    return img.convert("RGB")


@lru_cache(maxsize=1)
def archive():
    im = Image.open(os.path.join(SRC, "kulik_1929_nasa_eo.jpg")).convert("L")
    return im.resize((im.width * 3 // 5, im.height * 3 // 5), Image.LANCZOS).convert("RGB")   # 3131 x 2126


def archive_scene(t, D, p):
    src = archive()
    u = smooth(seg(t, 0, D))
    z0, z1 = p.get("z", (1.0, 1.12))
    c0 = p.get("c0", (0.5, 0.5)); c1 = p.get("c1", (0.55, 0.48))
    zoom = max(W / src.width, H / src.height) * lerp(z0, z1, u)
    hw, hh = W / zoom / 2, H / zoom / 2
    cx = clamp(lerp(c0[0], c1[0], u) * src.width, hw, src.width - hw)
    cy = clamp(lerp(c0[1], c1[1], u) * src.height, hh, src.height - hh)
    img = camera(src, cx, cy, zoom).convert("RGBA")
    for it in p.get("txt", []):
        k = smooth(seg(t, it.get("at", 0.3), it.get("at", 0.3) + 0.4)) * (1 - smooth(seg(t, it.get("until", D) - 0.4, it.get("until", D))))
        headline(img, it["lines"], it.get("pos", "bl"), k)
    credit(img, CR_AR)
    return img.convert("RGB")


# ---------------------------------------------------------------- painted backgrounds
@lru_cache(maxsize=None)
def navy_bg(seed=1):
    im = vgradient(W, H, [(0, (10, 20, 38)), (0.6, (18, 34, 56)), (1, (12, 22, 36))])
    return paint_texture(im, seed, 0.10, 3.0)


@lru_cache(maxsize=None)
def stars(seed=3, n=900):
    im = navy_bg(seed).copy()
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        b = int(rng.uniform(90, 255)); r = rng.choice([0.6, 0.9, 1.4], p=[0.7, 0.25, 0.05])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, min(255, b + 15)))
    return im


@lru_cache(maxsize=None)
def blurred_forest(e=-9.0, blur=14):
    return F.render(e, (1200, 700, 1.0), shake=False).filter(ImageFilter.GaussianBlur(blur))


# ---------------------------------------------------------------- cards
def card_scene(t, D, p):
    bg = p.get("bg", "forest")
    img = (blurred_forest() if bg == "forest" else blurred_forest(9.0) if bg == "flat" else navy_bg(5)).copy()
    # slow drift so the card is never a frozen frame
    z = 1 + 0.04 * smooth(seg(t, 0, D))
    img = camera(img, W / 2, H / 2, z).convert("RGBA")
    dk = Image.new("RGBA", (W, H), (6, 12, 22, 120))
    img.alpha_composite(dk)
    y = p.get("y", 330)
    for k, ln in enumerate(p["lines"]):
        at = ln.get("at", 0.2 + 0.25 * k)
        a = smooth(seg(t, at, at + 0.45)) * (1 - smooth(seg(t, D - 0.35, D - 0.02)))
        dy = 18 * (1 - ease_out(seg(t, at, at + 0.5)))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sz = ln.get("size", 64)
        shadow_text(lay, (W // 2, y + dy), ln["text"], font(ln.get("wt", "Inter-Black.otf"), sz), ln.get("col", WHT), "ma", stroke=2)
        if ln.get("strike") is not None and t > ln["strike"]:
            q = ease_out(seg(t, ln["strike"], ln["strike"] + 0.4))
            bb = ImageDraw.Draw(lay).textbbox((W // 2, y), ln["text"], font=font(ln.get("wt", "Inter-Black.otf"), sz), anchor="ma")
            ImageDraw.Draw(lay).line([(bb[0] - 10, (bb[1] + bb[3]) / 2), (lerp(bb[0] - 10, bb[2] + 10, q), (bb[1] + bb[3]) / 2)], fill=(230, 60, 50, 255), width=10)
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
        img.alpha_composite(lay)
        y += int(sz * 1.45)
    if p.get("tag"):
        tag_ill(img, p["tag"])
    return img.convert("RGB")


def cover_grade(img, k=1.0):
    from PIL import ImageEnhance
    g = ImageEnhance.Color(img).enhance(1 + 0.75 * k)
    g = ImageEnhance.Contrast(g).enhance(1 + 0.38 * k)
    return g


# ---------------------------------------------------------------- forest shots
def forest_scene(t, D, p):
    """p: e=(e0,e1) linear, or ekeys=[(t,e),...] piecewise-smooth; cam0/cam1=(cx,cy,zoom)"""
    if "ekeys" in p:
        ks = p["ekeys"]
        e = ks[-1][1]
        for (ta, ea), (tb, eb) in zip(ks, ks[1:]):
            if ta <= t <= tb:
                e = lerp(ea, eb, smooth(seg(t, ta, tb)) if p.get("ease", True) else seg(t, ta, tb)); break
        if t < ks[0][0]:
            e = ks[0][1]
    else:
        e0, e1 = p.get("e", (-9, -9)); e = lerp(e0, e1, seg(t, 0, D))
    u = smooth(seg(t, p.get("ct0", 0), p.get("ct1", D)))
    c0, c1 = p.get("cam0", (1200, 700, 1.0)), p.get("cam1", p.get("cam0", (1200, 700, 1.0)))
    cam = tuple(lerp(a, b, u) for a, b in zip(c0, c1))
    img = F.render(e, cam, shake=p.get("shake", True))
    if p.get("cover_grade"):  # cover look on the held frame, relaxing into the normal grade as the scene rewinds
        k = 1 - smooth(seg(t, *p["cover_grade"]))
        if k > 0.001:
            img = cover_grade(img, k)
    img = img.convert("RGBA")
    if p.get("rewind") and p["rewind"][0] <= t <= p["rewind"][1]:
        k = math.sin(math.pi * seg(t, *p["rewind"]))
        d = BD(img)
        for j in range(3):  # rewind chevrons
            x = W / 2 - 120 + j * 90
            d.polygon([(x + 50, H / 2 - 40), (x + 50, H / 2 + 40), (x, H / 2)], fill=(247, 237, 214, int(230 * k)))
        for yy in range(0, H, 6):
            d.line((0, yy, W, yy), fill=(15, 35, 45, int(40 * k)))
    for it in p.get("txt", []):
        at, un = it.get("at", 0.2), it.get("until", D)
        k = (1.0 if at <= 0 else smooth(seg(t, at, at + 0.4))) * (1 - smooth(seg(t, un - 0.4, un)))
        dx = it.get("slide", 0) * ease_in(seg(t, un - 0.6, un))
        headline(img, it["lines"], it.get("pos", "bl"), k if not it.get("slide") else 1.0 if t < un else 0.0, dx=dx)
    tag_ill(img, p.get("tag", REC))
    return img.convert("RGB")


# ---------------------------------------------------------------- globe
def globe_scene(t, D, p):
    img = stars(7).copy().convert("RGBA")
    lat0, lon0 = math.radians(60.9), math.radians(101.9)
    u = smooth(seg(t, 0, D * 0.75))
    lon_c = lon0 - math.radians(70) * (1 - u); lat_c = lat0 * (0.4 + 0.6 * u)
    R = lerp(300, 470, smooth(seg(t, 0, D)))
    cx, cy = W / 2 + 120, H / 2 + 20
    # lit sphere
    sz = int(R * 2)
    yy, xx = np.mgrid[0:sz, 0:sz].astype(np.float32)
    nx = (xx - R) / R; ny = (yy - R) / R
    m = nx * nx + ny * ny
    inside = m <= 1
    nz = np.sqrt(np.clip(1 - m, 0, 1))
    light = np.clip(-0.55 * nx - 0.45 * ny + 0.7 * nz, 0, 1)
    col = np.array((22, 60, 96), np.float32)[None, None] * (0.35 + 0.9 * light[..., None])
    rim = np.clip((m - 0.85) / 0.15, 0, 1)[..., None] * inside[..., None]
    col = col + rim * np.array((70, 140, 200), np.float32) * 0.6
    alpha = (np.clip((1 - m) * R / 2, 0, 1) * 255)
    sph = Image.fromarray(np.dstack([np.clip(col, 0, 255), alpha]).astype(np.uint8), "RGBA")
    sph = paint_texture(sph, 8, 0.12, 2.0)
    img.alpha_composite(sph, (int(cx - R), int(cy - R)))
    halo = glow_sprite(256, (80, 150, 220), power=2.2)
    img = add_glow(img, halo, cx, cy, R * 2.6, 0.35, mode="add").convert("RGBA")
    d = BD(img)

    def proj(lat, lon):
        x = math.cos(lat) * math.sin(lon - lon_c)
        y = math.cos(lat_c) * math.sin(lat) - math.sin(lat_c) * math.cos(lat) * math.cos(lon - lon_c)
        z = math.sin(lat_c) * math.sin(lat) + math.cos(lat_c) * math.cos(lat) * math.cos(lon - lon_c)
        return cx + R * x, cy - R * y, z
    for lat in range(-60, 90, 15):
        pts = [proj(math.radians(lat), math.radians(lo)) for lo in range(0, 361, 4)]
        for a, b in zip(pts, pts[1:]):
            if a[2] > 0 and b[2] > 0:
                d.line([a[:2], b[:2]], fill=(150, 200, 235, 70), width=2)
    for lo in range(0, 360, 20):
        pts = [proj(math.radians(la), math.radians(lo)) for la in range(-88, 89, 4)]
        for a, b in zip(pts, pts[1:]):
            if a[2] > 0 and b[2] > 0:
                d.line([a[:2], b[:2]], fill=(150, 200, 235, 70), width=2)
    px, py, pz = proj(lat0, lon0)
    k = smooth(seg(t, D * 0.45, D * 0.45 + 0.6))
    if pz > 0 and k > 0:
        r = 16 + 8 * math.sin(t * 4)
        d.ellipse([px - r * 2, py - r * 2, px + r * 2, py + r * 2], outline=(255, 210, 63, int(200 * k)), width=4)
        d.ellipse([px - 10, py - 10, px + 10, py + 10], fill=(255, 210, 63, int(255 * k)))
        pill(img, (px + 50, py - 70), "KRASNOYARSK REGION, RUSSIA", 30, alpha=k, wt="Inter-Bold.otf")
        pill(img, (px + 50, py - 14), "NEAR THE PODKAMENNAYA TUNGUSKA RIVER", 24, alpha=smooth(seg(t, D * 0.6, D * 0.6 + 0.5)))
        pill(img, (px + 50, py + 34), "≈ 60.9° N, 101.9° E", 24, alpha=smooth(seg(t, D * 0.7, D * 0.7 + 0.5)))
    tag_ill(img, "ILLUSTRATION · GRATICULE GLOBE")
    return img.convert("RGB")


# ---------------------------------------------------------------- cross-section physics
SEC_G = 860          # ground line
SEC_B = (1100, 360)  # burst point (illustrative height)


@lru_cache(maxsize=1)
def section_bg():
    im = vgradient(W, H, [(0, (8, 16, 34)), (0.5, (30, 52, 84)), (0.78, (120, 110, 120)), (0.8, (40, 54, 44)), (1, (22, 30, 24))])
    im = paint_texture(im, 31, 0.08, 3.0).convert("RGBA")
    d = BD(im)
    rng = np.random.default_rng(32)
    for i in range(140):   # thin atmosphere strokes
        x, y = rng.uniform(0, W), rng.uniform(40, SEC_G - 20)
        d.line([(x, y), (x + rng.uniform(30, 90), y)], fill=(160, 190, 230, 10), width=1)
    return im


@lru_cache(maxsize=1)
def section_trees():
    rng = np.random.default_rng(33)
    return [(x, int(rng.uniform(80, 120)), int(rng.integers(10))) for x in np.arange(30, W, 26) + rng.uniform(-6, 6, len(np.arange(30, W, 26)))]


BOLIDE = glow_sprite(128, (255, 200, 150), power=1.4, core=(255, 255, 240))
FIREB = glow_sprite(512, (255, 140, 50), power=1.2, core=(255, 250, 230), seed=12, turb=0.4)
HALO2 = glow_sprite(512, (255, 170, 100), power=2.6)


def section_scene(t, D, p):
    """ev: dict of event -> local time. entry, compress, stress, frag, burst, shock, fall, impact, alt, energy, unc, here"""
    ev = p.get("ev", {})
    img = section_bg().copy()
    d = BD(img)
    # altitude ruler (not to scale)
    for k in range(0, 6):
        y = SEC_G - k * 110
        d.line([(60, y), (84, y)], fill=(220, 230, 240, 120), width=2)
    def T(name, default=1e9):
        return ev.get(name, default)
    p0 = (-80, -60)
    # entry path
    te, tb = T("entry"), T("burst")
    if t >= te and t < tb + 0.3:
        u = ease_in(seg(t, te, tb)) if tb < 1e8 else seg(t, te, te + 6)
        hx, hy = lerp(p0[0], SEC_B[0], u), lerp(p0[1], SEC_B[1], u)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        tx, ty = lerp(p0[0], SEC_B[0], max(0, u - 0.4)), lerp(p0[1], SEC_B[1], max(0, u - 0.4))
        for wdt, a in ((22, 50), (10, 120), (4, 230)):
            dl.line([(tx, ty), (hx, hy)], fill=(255, 200, 150, a), width=wdt)
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(3)))
        frag = T("frag")
        if t < frag:
            img = add_glow(img, BOLIDE, hx, hy, 70 + 50 * u, 1.0, mode="add").convert("RGBA")
            # the body itself: dark irregular rock
            dd = BD(img)
            rr = 13
            dd.polygon([(hx + rr * math.cos(a) * (0.8 + 0.3 * math.sin(3 * a)), hy + rr * math.sin(a) * (0.8 + 0.3 * math.cos(2 * a))) for a in np.linspace(0, 2 * math.pi, 12)], fill=(70, 56, 48, 255))
        else:  # fragments spreading
            q = seg(t, frag, frag + 1.2)
            for j in range(9):
                ang = math.atan2(SEC_B[1] - p0[1], SEC_B[0] - p0[0]) + (j - 4) * 0.12
                L = 90 * q * (0.6 + 0.4 * ((j * 37) % 5) / 4)
                img = add_glow(img, BOLIDE, hx + L * math.cos(ang), hy + L * math.sin(ang), 46, 1 - 0.6 * q, mode="add").convert("RGBA")
        if t >= T("compress") and t < frag:  # bow shock arcs in front of the body
            dd = BD(img)
            ang = math.degrees(math.atan2(SEC_B[1] - p0[1], SEC_B[0] - p0[0]))
            for j in range(3):
                r = 40 + j * 22 + 6 * math.sin(t * 8 + j)
                dd.arc([hx - r, hy - r, hx + r, hy + r], ang - 60, ang + 60, fill=(200, 230, 255, 200 - 50 * j), width=4)
            if t >= T("stress"):
                for j in range(4):
                    a = j * 1.7 + t * 0.5
                    dd.line([(hx, hy), (hx + 16 * math.cos(a), hy + 16 * math.sin(a))], fill=(255, 240, 200, 255), width=2)
    # burst
    if t >= tb:
        q = ease_out(seg(t, tb, tb + 1.4))
        size = 80 + 520 * q
        img = add_glow(img, HALO2, *SEC_B, size * 2.6, 0.55 * (1 - 0.3 * seg(t, tb + 2, tb + 8)), mode="add").convert("RGBA")
        img = add_glow(img, FIREB, *SEC_B, size, 1.0 * (1 - 0.4 * seg(t, tb + 2, tb + 8)), mode="add").convert("RGBA")
    # shock shell down to the ground
    ts = T("shock")
    r_ground = SEC_G - SEC_B[1]
    if t >= ts:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        for j in range(3):
            r = (t - ts - j * 0.5) * 230
            if r <= 0:
                continue
            a = int(200 * clamp(1 - r / 1700))
            dl.ellipse([SEC_B[0] - r, SEC_B[1] - r, SEC_B[0] + r, SEC_B[1] + r], outline=(255, 214, 160, a), width=8)
        lay = lay.filter(ImageFilter.GaussianBlur(3))
        mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).rectangle([0, 0, W, SEC_G + 4], fill=255)
        img.paste(Image.alpha_composite(img, lay), (0, 0), mask)
    # ground trees: fall when the shell reaches them (outward), stripped under the burst
    for (x, h, var) in section_trees():
        ang = 0.0; strip = False
        if t >= ts:
            dist = math.hypot(x - SEC_B[0], r_ground)
            th = ts + (dist - 0) / 230
            if abs(x - SEC_B[0]) < 70:
                strip = t >= th
            else:
                ang = (-1 if x > SEC_B[0] else 1) * 82 * ease_in(seg(t, th, th + 0.5))
        stamp(img, F.tree(var, h, strip, 0.0), x, SEC_G + 6, angle=ang)
    d = BD(img)
    # impact comparison: dashed crater under a would-be impact, crossed out
    if t >= T("impact"):
        k = smooth(seg(t, T("impact"), T("impact") + 0.6))
        cxr = 520
        for a0 in range(0, 180, 12):
            d.arc([cxr - 170, SEC_G - 90, cxr + 170, SEC_G + 90], a0, a0 + 7, fill=(255, 255, 255, int(220 * k)), width=5)
        if t >= T("impact_x"):
            q = ease_out(seg(t, T("impact_x"), T("impact_x") + 0.4))
            d.line([(cxr - 190, SEC_G - 60), (lerp(cxr - 190, cxr + 190, q), lerp(SEC_G - 60, SEC_G + 80, q))], fill=(230, 60, 50, 255), width=12)
        pill(img, (cxr, SEC_G + 110), p.get("impact_label", "GIANT CRATER: NOT REQUIRED"), 28, anchor="c", alpha=k, wt="Inter-Bold.otf")
    if t >= T("alt"):
        k = smooth(seg(t, T("alt"), T("alt") + 0.6))
        x = SEC_B[0] - 330
        d.line([(x, SEC_B[1]), (x, SEC_G)], fill=(255, 210, 63, int(255 * k)), width=5)
        for yy in (SEC_B[1], SEC_G):
            d.line([(x - 22, yy), (x + 22, yy)], fill=(255, 210, 63, int(255 * k)), width=5)
        pill(img, (x - 40, (SEC_B[1] + SEC_G) / 2 - 40), "≈ 6–10 KM ABOVE THE GROUND", 32, anchor="r", alpha=k, wt="Inter-Bold.otf")
        pill(img, (x - 40, (SEC_B[1] + SEC_G) / 2 + 22), "NASA EARTH OBSERVATORY ESTIMATE", 22, anchor="r", alpha=k)
    if t >= T("energy"):
        k = smooth(seg(t, T("energy"), T("energy") + 0.6))
        x0, y0, w = 180, 150, 760
        d.rounded_rectangle([x0, y0, x0 + w, y0 + 34], 12, outline=(255, 255, 255, int(160 * k)), width=3)
        a0, a1 = 10 / 30, 20 / 30   # bar 0..30 Mt, highlight 10..20
        q = ease_out(seg(t, T("energy") + 0.3, T("energy") + 1.3))
        d.rounded_rectangle([x0 + w * a0, y0 + 4, x0 + w * lerp(a0, a1, q), y0 + 30], 10, fill=(255, 210, 63, int(255 * k)))
        for mt in (0, 10, 20, 30):
            d.text((x0 + w * mt / 30, y0 + 46), f"{mt}", font=font("Inter-Bold.otf", 24), fill=(230, 235, 240, int(255 * k)), anchor="ma")
        pill(img, (x0, y0 - 66), "≈ 10–20 MEGATONS OF TNT · MODEL ESTIMATES", 30, alpha=k, wt="Inter-Bold.otf")
        if t >= T("notmeas"):
            pill(img, (x0, y0 + 90), "NOT MEASURED IN 1908 · RESULTS VARY BY MODEL", 24, bg=(120, 52, 18, 210), alpha=smooth(seg(t, T("notmeas"), T("notmeas") + 0.5)))
    if t >= T("unc"):
        for j, s in enumerate(["PATH?", "SIZE?", "COMPOSITION?", "ENERGY?"]):
            k = smooth(seg(t, T("unc") + 0.45 * j, T("unc") + 0.45 * j + 0.4))
            pill(img, (140 + j * 360, 150), s, 34, alpha=k, wt="Inter-Black.otf", bg=(10, 18, 34, 210))
    if t >= T("here"):
        k = smooth(seg(t, T("here"), T("here") + 0.6))
        pill(img, (SEC_B[0] - 300, SEC_B[1] - 260), p.get("here_label", "ENERGY RELEASED HERE · IN THE AIR"), 30, anchor="r", alpha=k, wt="Inter-Bold.otf")
        d.line([(SEC_B[0] - 60, SEC_B[1] - 40), (SEC_B[0] - 300, SEC_B[1] - 215)], fill=(255, 210, 63, int(255 * k)), width=4)
    for it in p.get("txt", []):
        k = smooth(seg(t, it.get("at", 0.2), it.get("at", 0.2) + 0.4)) * (1 - smooth(seg(t, it.get("until", D) - 0.4, it.get("until", D))))
        headline(img, it["lines"], it.get("pos", "tl"), k)
    tag_ill(img, "ILLUSTRATION · HEIGHTS AND SIZES NOT TO SCALE")
    return img.convert("RGB")


# ---------------------------------------------------------------- crater expectation (ground cross-section)
@lru_cache(maxsize=1)
def strata_bg():
    im = vgradient(W, H, [(0, (26, 40, 62)), (0.42, (120, 104, 100)), (0.45, (48, 62, 44)), (0.55, (92, 74, 56)), (0.75, (70, 54, 44)), (1, (46, 36, 32))])
    im = paint_texture(im, 71, 0.14, 6.0).convert("RGBA")
    d = BD(im)
    for k, y in enumerate((560, 640, 760, 900)):
        d.line([(0, y + 10 * math.sin(k)), (W, y - 8)], fill=(30, 22, 18, 90), width=3)
    return im


def crater_scene(t, D, p):
    ev = p.get("ev", {})
    T = lambda n: ev.get(n, 1e9)
    img = strata_bg().copy()
    u = smooth(seg(t, 0, D)); z = 1 + 0.05 * u
    gy = 486
    for (x, h, var) in section_trees():
        fallen = p.get("fallen", False)
        stamp(img, F.tree(var, h + 10, False, 0.0), x, gy + 4, angle=((-1 if x > W / 2 else 1) * 84 if fallen and abs(x - W / 2) > 80 else 0))
    d = BD(img)
    cx = W / 2
    if t >= T("expect"):
        k = smooth(seg(t, T("expect"), T("expect") + 0.8))
        gone = smooth(seg(t, T("erase"), T("erase") + 1.0))
        a = int(255 * k * (1 - gone))
        q = ease_out(seg(t, T("expect"), T("expect") + 1.2))
        for a0 in range(0, int(180 * q), 10):
            d.arc([cx - 420, gy - 230, cx + 420, gy + 230], a0, a0 + 6, fill=(255, 255, 255, a), width=7)
        items = [("crater", "CRATER", (cx, gy + 270)), ("material", "SCATTERED MATERIAL", (cx - 560, gy - 120)), ("surface", "DISTURBED SURFACE", (cx + 560, gy - 120))]
        for key, lab, (x, y) in items:
            if t >= T(key):
                kk = smooth(seg(t, T(key), T(key) + 0.5)) * (1 - gone)
                pill(img, (x, y), lab, 30, anchor="c", alpha=kk, wt="Inter-Bold.otf")
                if key == "material":
                    rng = np.random.default_rng(5)
                    for j in range(26):
                        xx = cx + rng.uniform(-700, 700); yy = gy - rng.uniform(0, 30)
                        d.ellipse([xx - 6, yy - 5, xx + 6, yy + 5], fill=(60, 50, 44, int(255 * kk)))
        if t >= T("erase"):
            kk = smooth(seg(t, T("erase") + 0.4, T("erase") + 1.0))
            headline(img, [("NO GREAT", WHT), ("IMPACT CRATER", YEL)], "tl", kk) if False else None
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            shadow_text(lay, (cx, gy + 140), p.get("erase_text", "NO GREAT IMPACT CRATER"), font("Inter-Black.otf", 88), YEL, "ma")
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * kk)))
            img.alpha_composite(lay)
    if p.get("question") is not None and t >= p["question"]:
        k = smooth(seg(t, p["question"], p["question"] + 0.5))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        shadow_text(lay, (cx, gy + 120), "?", font("Inter-Black.otf", 260), YEL, "ma")
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * k)))
        img.alpha_composite(lay)
    for it in p.get("txt", []):
        k = smooth(seg(t, it.get("at", 0.2), it.get("at", 0.2) + 0.4)) * (1 - smooth(seg(t, it.get("until", D) - 0.4, it.get("until", D))))
        headline(img, it["lines"], it.get("pos", "tl"), k)
    tag_ill(img, "ILLUSTRATION · WHAT AN IMPACT WOULD LEAVE")
    return camera(img, W / 2, H / 2, z).convert("RGB")


# ---------------------------------------------------------------- side-view treefall comparison
@lru_cache(maxsize=1)
def tf_bg():
    im = vgradient(W, H, [(0, (30, 44, 64)), (0.55, (150, 120, 108)), (0.74, (64, 76, 58)), (1, (26, 34, 26))])
    return paint_texture(im, 81, 0.10, 4.0).convert("RGBA")


def treefall_scene(t, D, p):
    ev = p.get("ev", {})
    T = lambda n: ev.get(n, 1e9)
    img = tf_bg().copy()
    gy = 800
    center = W / 2
    rng = np.random.default_rng(84)
    xs = list(np.arange(80, W, 64))
    for i, x in enumerate(xs):
        h = int(rng.uniform(300, 380)); var = int(rng.integers(10))
        dc = abs(x - center)
        th = T("wave") + dc / 420
        if dc < 230:
            strip = t >= th
            stamp(img, F.tree(var, h, strip, 0.0), x, gy, angle=0)
        else:
            ang = (-1 if x > center else 1) * 80 * ease_in(seg(t, th, th + 0.55))
            stamp(img, F.tree(var, h, False, 0.0), x, gy, angle=ang)
    d = BD(img)
    if t >= T("wave") - 0.6:
        q = seg(t, T("wave") - 0.6, T("wave") + 3)
        img = add_glow(img, HALO2, center, 120, 900 * (1 - 0.5 * q), 0.6 * (1 - q), mode="add").convert("RGBA")
        d = BD(img)
        for sgn in (-1, 1):
            x = center + sgn * (t - T("wave")) * 420
            if 0 < (t - T("wave")) < 3:
                for j in range(4):
                    d.line([(x + sgn * j * 22, gy - 300), (x + sgn * j * 22 + sgn * 40, gy - 150)], fill=(255, 230, 190, 120 - 25 * j), width=4)
    if t >= T("labels"):
        k = smooth(seg(t, T("labels"), T("labels") + 0.5))
        pill(img, (240, 150), "AWAY FROM THE CENTER: FLATTENED, POINTING OUTWARD", 26, alpha=k, wt="Inter-Bold.otf")
    if t >= T("center"):
        k = smooth(seg(t, T("center"), T("center") + 0.5))
        pill(img, (center, 230), "NEAR THE CENTER: STILL STANDING, STRIPPED", 30, anchor="c", alpha=k, wt="Inter-Bold.otf", bg=(120, 52, 18, 210))
        d.rounded_rectangle([center - 240, gy - 420, center + 240, gy + 20], 30, outline=(255, 210, 63, int(255 * k)), width=5)
    tag_ill(img, "ILLUSTRATION · SIMPLIFIED")
    return img.convert("RGB")


# ---------------------------------------------------------------- radial top-down map
RC = (W / 2, H / 2 + 20)


@lru_cache(maxsize=1)
def radial_bg():
    a = fbm(W, H, 91, cells=(220, 90, 30, 9), weights=(0.4, 0.3, 0.2, 0.1))
    c1 = np.array((32, 66, 46), np.float32); c2 = np.array((70, 96, 60), np.float32)
    rgb = c1 + (c2 - c1) * a[..., None]
    rv = noise(W, H, 300, 92, 3.0)  # meandering darker drainage
    rgb *= (1 - 0.25 * np.clip((rv - 0.6) * 5, 0, 1))[..., None]
    return paint_texture(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)), 93, 0.12, 1.5).convert("RGBA")


def butterfly_r(theta, R):
    return R * (1 + 0.28 * math.cos(2 * (theta - 0.5)) + 0.12 * math.cos(theta - 2.4))


@lru_cache(maxsize=1)
def radial_points():
    rng = np.random.default_rng(95)
    pts = []
    for _ in range(2600):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        pts.append((x, y, rng.uniform(-0.25, 0.25)))
    return pts


def radial_scene(t, D, p):
    ev = p.get("ev", {})
    T = lambda n: ev.get(n, 1e9)
    R = 400
    img = radial_bg().copy()
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    wave_r = (t - T("wave")) * 330 if t >= T("wave") else (1e5 if p.get("fallen") else -1)
    for (x, y, jit) in radial_points():
        dx, dy = x - RC[0], y - RC[1]
        r = math.hypot(dx, dy); th = math.atan2(dy, dx)
        inside = r < butterfly_r(th, R)
        if inside and r < wave_r and r > 34:
            a = th + jit
            L = 16
            d.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=(150, 108, 74, 235), width=3)
        elif inside and r <= 34 and r < wave_r:
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(120, 84, 60, 255))
        else:
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(24, 58, 40, 230))
            d.ellipse([x - 3, y - 4, x + 2, y + 1], fill=(56, 100, 66, 230))
    img.alpha_composite(lay)
    d = BD(img)
    if 0 < wave_r < 1600:
        for j in range(3):
            r = wave_r - j * 30
            if r > 0:
                d.ellipse([RC[0] - r, RC[1] - r * 0.92, RC[0] + r, RC[1] + r * 0.92], outline=(255, 226, 180, int(160 * (1 - wave_r / 1600)) // (j + 1)), width=6)
    if t >= T("outline"):
        k = smooth(seg(t, T("outline"), T("outline") + 0.8))
        pts = [(RC[0] + butterfly_r(a, R) * math.cos(a), RC[1] + butterfly_r(a, R) * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 120)]
        n = int(len(pts) * ease_out(seg(t, T("outline"), T("outline") + 1.2)))
        if n > 1:
            d.line(pts[:n], fill=(255, 210, 63, int(255 * k)), width=6, joint="curve")
    if t >= T("area"):
        k = smooth(seg(t, T("area"), T("area") + 0.5))
        pill(img, (W - 60, 150), "≈ 2,000 KM²  (≈ 770 SQ MI)", 40, anchor="r", alpha=k, wt="Inter-Black.otf")
        pill(img, (W - 60, 222), "APPROXIMATE · MOST COMMONLY CITED", 24, anchor="r", alpha=k)
    if t >= T("onetree"):
        k = smooth(seg(t, T("onetree"), T("onetree") + 0.4)) * (1 - smooth(seg(t, T("onetree") + 2.6, T("onetree") + 3.0)))
        x, y = RC[0] - 260, RC[1] + 60
        d.ellipse([x - 26, y - 26, x + 26, y + 26], outline=(255, 255, 255, int(255 * k)), width=4)
        pill(img, (x - 40, y + 40), "ONE FALLEN TREE", 26, anchor="r", alpha=k, wt="Inter-Bold.otf")
    if t >= T("survey"):
        q = seg(t, T("survey"), T("survey") + 4.0)
        x = lerp(200, W - 200, q)
        for gx in range(200, W - 199, 120):
            d.line([(gx, 120), (gx, H - 120)], fill=(255, 255, 255, 40), width=1)
        for gy in range(120, H - 119, 120):
            d.line([(200, gy), (W - 200, gy)], fill=(255, 255, 255, 40), width=1)
        d.line([(x, 120), (x, H - 120)], fill=(255, 210, 63, 200), width=4)
        pill(img, (240, H - 110), "PATTERN RECONSTRUCTED FROM FIELD SURVEYS · SIMPLIFIED HERE", 24, alpha=smooth(seg(t, T("survey"), T("survey") + 0.5)))
    if t >= T("center"):
        k = smooth(seg(t, T("center"), T("center") + 0.5))
        d.ellipse([RC[0] - 44, RC[1] - 44, RC[0] + 44, RC[1] + 44], outline=(255, 210, 63, int(255 * k)), width=5)
        pill(img, (RC[0] + 60, RC[1] + 40), p.get("center_label", "CENTER: TRUNKS LEFT STANDING"), 26, alpha=k, wt="Inter-Bold.otf")
    if t >= T("arrows"):
        k = smooth(seg(t, T("arrows"), T("arrows") + 0.5))
        for j in range(8):
            a = j * math.pi / 4 + 0.2
            r0, r1 = 120, 120 + 200 * ease_out(seg(t, T("arrows"), T("arrows") + 1.0))
            x0, y0 = RC[0] + r0 * math.cos(a), RC[1] + r0 * math.sin(a)
            x1, y1 = RC[0] + r1 * math.cos(a), RC[1] + r1 * math.sin(a)
            d.line([(x0, y0), (x1, y1)], fill=(255, 240, 220, int(230 * k)), width=6)
            d.polygon([(x1 + 18 * math.cos(a), y1 + 18 * math.sin(a)), (x1 + 12 * math.cos(a + 2.2), y1 + 12 * math.sin(a + 2.2)), (x1 + 12 * math.cos(a - 2.2), y1 + 12 * math.sin(a - 2.2))], fill=(255, 240, 220, int(230 * k)))
    for it in p.get("txt", []):
        k = smooth(seg(t, it.get("at", 0.2), it.get("at", 0.2) + 0.4)) * (1 - smooth(seg(t, it.get("until", D) - 0.4, it.get("until", D))))
        headline(img, it["lines"], it.get("pos", "tl"), k)
    tag_ill(img, "ILLUSTRATION · TOP-DOWN, PATTERN SIMPLIFIED")
    z0, z1 = p.get("z", (1.0, 1.08))
    return camera(img, W / 2, H / 2, lerp(z0, z1, smooth(seg(t, 0, D)))).convert("RGB")


# ---------------------------------------------------------------- timeline ribbon
def timeline_scene(t, D, p):
    bg = p.get("bg", "forest")
    if bg == "landsat":
        base, _ = ls_view(t, D, {"z": (1.05, 1.15)})
        k = smooth(seg(t, 0.3, D * 0.8))
        base = Image.blend(base, base.convert("L").convert("RGB"), 0.8 * k).filter(ImageFilter.GaussianBlur(2 + 10 * k))
        base = Image.blend(base, blurred_forest(), smooth(seg(t, D * 0.5, D)))
    else:
        base = camera(blurred_forest(9.0 if bg == "flat" else -9.0, 10), W / 2, H / 2, 1 + 0.04 * smooth(seg(t, 0, D)))
    img = base.convert("RGBA")
    img.alpha_composite(Image.new("RGBA", (W, H), (6, 12, 22, 110)))
    d = BD(img)
    y0, y1 = p.get("years", (1908, 1927))
    marks = p.get("marks", [])
    xa, xb = 180, W - 180
    yl = 620
    d.line([(xa, yl), (xb, yl)], fill=(244, 238, 226, 200), width=4)
    lo, hi = min(y0, y1), max(y0, y1)
    for yr in range(lo, hi + 1):
        x = lerp(xa, xb, (yr - lo) / (hi - lo))
        big = yr in (y0, y1) or any(m[0] == yr for m in marks)
        d.line([(x, yl - (18 if big else 8)), (x, yl + (18 if big else 8))], fill=(244, 238, 226, 220), width=3 if big else 2)
    u = smooth(seg(t, p.get("t0", 0.4), p.get("t1", D - 0.6)))
    yr = lerp(y0, y1, u)
    x = lerp(xa, xb, (yr - lo) / (hi - lo))
    d.ellipse([x - 16, yl - 16, x + 16, yl + 16], fill=(255, 210, 63, 255))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow_text(lay, (W / 2, 300), f"{int(round(yr))}", font("Inter-Black.otf", 200), YEL, "ma")
    img.alpha_composite(lay)
    for (myr, label, at) in marks:
        k = smooth(seg(t, at, at + 0.5))
        mx = lerp(xa, xb, (myr - lo) / (hi - lo))
        pill(img, (mx, yl + 50 + 62 * (marks.index((myr, label, at)) % 3)), label, 26, anchor="c", alpha=k, wt="Inter-Bold.otf")
    if p.get("rewind"):
        k = math.sin(math.pi * seg(t, 0.2, D - 0.2))
        for j in range(3):
            xx = W / 2 - 120 + j * 90
            d.polygon([(xx + 50, 180), (xx + 50, 250), (xx, 215)], fill=(247, 237, 214, int(200 * k)))
    return img.convert("RGB")


# ---------------------------------------------------------------- Chelyabinsk schematic
@lru_cache(maxsize=1)
def city_layer():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(101)
    x = 0
    wins = []
    while x < W:
        w = int(rng.uniform(90, 200)); h = int(rng.uniform(160, 420))
        d.rectangle([x, 900 - h, x + w - 8, 900], fill=(28, 34, 48, 255))
        for wy in range(900 - h + 20, 880, 34):
            for wx in range(x + 14, x + w - 24, 28):
                wins.append((wx, wy))
        x += w
    d.rectangle([0, 900, W, H], fill=(214, 220, 228, 255))  # winter snow
    return paint_texture(im, 102, 0.10, 2.0), wins


def city_scene(t, D, p):
    ev = p.get("ev", {})
    T = lambda n: ev.get(n, 1e9)
    img = vgradient(W, H, [(0, (40, 70, 110)), (0.7, (190, 170, 160)), (1, (220, 220, 225))]).convert("RGBA")
    img = paint_texture(img, 103, 0.06, 3.0).convert("RGBA")
    ts, tb, tw = T("streak"), T("burst"), T("wave")
    if t >= ts:
        u = ease_in(seg(t, ts, tb))
        p0, p1 = (W + 100, 80), (520, 300)
        hx, hy = lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        dl.line([p0, (hx, hy)], fill=(250, 250, 240, 130 if t < tb else int(130 * (1 - seg(t, tb, tb + 6)))), width=16)
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(5)))
        if t < tb + 0.5:
            img = add_glow(img, BOLIDE, hx, hy, 160 + 300 * seg(t, tb - 0.4, tb), 1.0, mode="add").convert("RGBA")
    fl = smooth(seg(t, tb - 0.1, tb + 0.3)) * (1 - smooth(seg(t, tb + 0.3, tb + 2.5)))
    city, wins = city_layer()
    img.alpha_composite(city)
    d = BD(img)
    for i, (wx, wy) in enumerate(wins):
        th = tw + (abs(wx - 520) / 900) + (i % 7) * 0.03
        if t < th:
            d.rectangle([wx, wy, wx + 14, wy + 18], fill=(250, 214, 140, 255))
        else:
            q = seg(t, th, th + 0.8)
            if q < 1:
                for j in range(3):
                    sx = wx + 7 + (j - 1) * 14 * q; sy = wy + 9 + 60 * q * q + j * 4
                    d.polygon([(sx, sy), (sx + 5, sy + 3), (sx + 1, sy + 7)], fill=(220, 240, 255, int(255 * (1 - q))))
            d.rectangle([wx, wy, wx + 14, wy + 18], fill=(18, 22, 32, 255))
    if t >= tw - 0.3:
        r = (t - tw + 0.3) * 900
        d.ellipse([520 - r, 300 - r * 0.7, 520 + r, 300 + r * 0.7], outline=(255, 255, 255, int(120 * clamp(1 - r / 2200))), width=10)
    img = img.convert("RGB")
    if fl > 0.01:
        a = np.asarray(img).astype(np.float32)
        img = Image.fromarray(np.clip(a + fl * (255 - a) * 0.5, 0, 255).astype(np.uint8))
    img = img.convert("RGBA")
    pill(img, (40, 36), "CHELYABINSK, RUSSIA · FEBRUARY 15, 2013", 26, wt="Inter-Bold.otf")
    tag_ill(img, "SCHEMATIC · NOT TUNGUSKA · NOT FOOTAGE")
    for it in p.get("txt", []):
        k = smooth(seg(t, it.get("at", 0.2), it.get("at", 0.2) + 0.4)) * (1 - smooth(seg(t, it.get("until", D) - 0.4, it.get("until", D))))
        headline(img, it["lines"], it.get("pos", "tl"), k)
    return img.convert("RGB")


# ---------------------------------------------------------------- planetary defense sky
def sky_scene(t, D, p):
    img = stars(11, 1400).copy().convert("RGBA")
    d = BD(img)
    # earth limb
    R = 2600; cx, cy = W / 2, H + R - 260
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    dl.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(14, 40, 70, 255), outline=(120, 190, 255, 255), width=10)
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(2)))
    d = BD(img)
    rng = np.random.default_rng(111)
    for j in range(7):  # orbits and tracked objects
        a, b = rng.uniform(500, 900), rng.uniform(120, 260)
        ox, oy = W / 2 + rng.uniform(-200, 200), 430 + rng.uniform(-60, 60)
        rot = rng.uniform(-0.4, 0.4)
        k = smooth(seg(t, 0.3 + j * 0.35, 1.0 + j * 0.35))
        pts = []
        for s in np.linspace(0, 2 * math.pi, 90):
            x, y = a * math.cos(s), b * math.sin(s)
            pts.append((ox + x * math.cos(rot) - y * math.sin(rot), oy + x * math.sin(rot) + y * math.cos(rot)))
        d.line(pts + [pts[0]], fill=(150, 200, 255, int(80 * k)), width=2)
        s = rng.uniform(0, 6) + t * 0.12
        x, y = a * math.cos(s), b * math.sin(s)
        px, py = ox + x * math.cos(rot) - y * math.sin(rot), oy + x * math.sin(rot) + y * math.cos(rot)
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(255, 210, 63, int(255 * k)))
        d.rectangle([px - 18, py - 18, px + 18, py + 18], outline=(255, 255, 255, int(160 * k)), width=2)
    # survey sweep
    q = (t * 0.18) % 1
    x = lerp(-200, W + 200, q)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    dl.polygon([(x - 160, 0), (x + 160, 0), (x + 60, H), (x - 60, H)], fill=(120, 200, 255, 26))
    img.alpha_composite(lay)
    for it in p.get("txt", []):
        k = smooth(seg(t, it.get("at", 0.2), it.get("at", 0.2) + 0.4)) * (1 - smooth(seg(t, it.get("until", D) - 0.4, it.get("until", D))))
        headline(img, it["lines"], it.get("pos", "tl"), k)
    tag_ill(img, "ILLUSTRATION · ORBITS NOT TO SCALE")
    return img.convert("RGB")


SCENES = dict(forest=forest_scene, landsat=landsat_scene, archive=archive_scene, card=card_scene, globe=globe_scene,
              section=section_scene, crater=crater_scene, treefall=treefall_scene, radial=radial_scene,
              timeline=timeline_scene, city=city_scene, sky=sky_scene)
