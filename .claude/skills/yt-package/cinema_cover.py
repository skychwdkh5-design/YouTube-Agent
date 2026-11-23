"""Orbital Atlas "Cinema Poster" cover (owner-approved 2026-11-23, replaces Neon Contour).

cinema_cover(hero, pre, word, loc, credit, latlon=None, coords=None, focus=(.5,.5)) -> 1280x720 RGB

  hero   : PIL RGB image of the real subject, edge to edge (a clean frame from the video / source image,
           no burned-in captions)
  pre    : one short white line above the hook word (e.g. "THIS LAKE LEAKS A GAS THAT")
  word   : ONE huge hook word / short phrase (e.g. "BURNS"), only verified facts and numbers
  loc    : place label shown top-right (e.g. "FAIRBANKS, ALASKA")
  credit : source / honesty label bottom-right (e.g. "NASA ABoVE FOOTAGE", "ILLUSTRATION")
  latlon : (lat, lon) on Earth -> locator mini-globe with a red pin; None for space subjects
  coords : coordinate text under loc (e.g. "64.8°N  147.7°W"); optional

Layout: full-bleed graded frame, dark bottom gradient + vignette, giant white Anton word bottom-left,
red tick + Oswald pre-line above it, locator chip + globe top-right, mono credit + ORBITAL ATLAS bottom-right.
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H = 1280, 720
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, 'fonts')
ANTON = 'anton-latin-400-normal.woff'
OSW = 'oswald-latin-700-normal.woff'
MONO = 'space-mono-latin-700-normal.woff'
RED = (255, 59, 48)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def fill_frame(im, size=(W, H), focus=(0.5, 0.5)):
    iw, ih = im.size; tw, th = size
    s = max(tw / iw, th / ih)
    im = im.resize((max(tw, round(iw * s)), max(th, round(ih * s))), Image.LANCZOS)
    x = int((im.width - tw) * focus[0]); y = int((im.height - th) * focus[1])
    return im.crop((x, y, x + tw, y + th))


def tsize(d, text, f):
    b = d.textbbox((0, 0), text, font=f); return b[2] - b[0], b[3] - b[1], b


def fit(d, text, name, maxw, maxh, start):
    s = start
    while s > 10:
        f = font(name, s); w, h, _ = tsize(d, text, f)
        if w <= maxw and h <= maxh: return f
        s -= 4
    return font(name, 10)


def draw_text(base, xy, text, f, fill, shadow=None, anchor='la'):
    if shadow:
        lay = Image.new('RGBA', base.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
        ox, oy, blur, a = shadow
        dd.text((xy[0] + ox, xy[1] + oy), text, font=f, fill=(0, 0, 0, a), anchor=anchor)
        base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(base).text(xy, text, font=f, fill=fill, anchor=anchor)


def vignette(im, strength=0.55, bottom=0.92):
    m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    d.ellipse((-W * 0.25, -H * 0.35, W * 1.25, H * 1.35), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new('RGB', (W, H), (0, 0, 0))
    out = Image.composite(im, Image.blend(im, dark, strength), m)
    g = Image.linear_gradient('L').resize((W, H))
    g = g.point(lambda v: int(max(0, (v - 255 * 0.35)) / (255 * 0.65) * 255 * bottom))
    return Image.composite(dark, out, g)


_LAND = None
def _land():
    global _LAND
    if _LAND is None:
        tj = json.load(open(os.path.join(HERE, 'land-110m.json')))
        sc, tr = tj['transform']['scale'], tj['transform']['translate']
        arcs = []
        for a in tj['arcs']:
            x = y = 0; pts = []
            for dx, dy in a:
                x += dx; y += dy; pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
            arcs.append(pts)
        def ring(idx):
            out = []
            for i in idx:
                p = arcs[i] if i >= 0 else arcs[~i][::-1]
                out.extend(p if not out else p[1:])
            return out
        polys = []
        for g in tj['objects']['land']['geometries']:
            if g['type'] == 'Polygon': polys.append(ring(g['arcs'][0]))
            else: polys.extend(ring(p[0]) for p in g['arcs'])
        _LAND = polys
    return _LAND


def globe(r, lat0, lon0, ocean=(18, 32, 52), land=(70, 92, 110)):
    ss = 3; R = r * ss; size = 2 * R + 8 * ss; c = size / 2
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((c - R, c - R, c + R, c + R), fill=ocean + (255,))
    p0, l0 = math.radians(lat0), math.radians(lon0)
    def proj(lon, lat):
        p, l = math.radians(lat), math.radians(lon)
        v = math.sin(p0) * math.sin(p) + math.cos(p0) * math.cos(p) * math.cos(l - l0)
        x = math.cos(p) * math.sin(l - l0)
        y = math.cos(p0) * math.sin(p) - math.sin(p0) * math.cos(p) * math.cos(l - l0)
        return (c + R * x, c - R * y), v
    def polyline(pts):
        seg = []
        for pt, v in pts:
            if v > 0: seg.append(pt)
            else:
                if len(seg) > 1: d.line(seg, fill=(255, 255, 255, 40), width=ss)
                seg = []
        if len(seg) > 1: d.line(seg, fill=(255, 255, 255, 40), width=ss)
    for la in range(-60, 90, 30): polyline([proj(lo, la) for lo in range(-180, 181, 4)])
    for lo in range(-180, 180, 30): polyline([proj(lo, la) for la in range(-90, 91, 4)])
    for rng in _land():
        pts = [proj(lo, la) for lo, la in rng]
        if all(v <= 0 for _, v in pts): continue
        cl = []
        for pt, v in pts:
            if v > 0: cl.append(pt)
            else:
                a = math.atan2(pt[1] - c, pt[0] - c); cl.append((c + R * math.cos(a), c + R * math.sin(a)))
        if len(cl) > 2: d.polygon(cl, fill=land + (255,))
    d.ellipse((c - R, c - R, c + R, c + R), outline=(255, 255, 255, 230), width=2 * ss)
    (px, py), _ = proj(lon0, lat0)
    for rr, a in ((22, 70), (14, 140)):
        d.ellipse((px - rr * ss, py - rr * ss, px + rr * ss, py + rr * ss), outline=RED + (a,), width=2 * ss)
    d.ellipse((px - 7 * ss, py - 7 * ss, px + 7 * ss, py + 7 * ss), fill=RED + (255,), outline=(255, 255, 255, 255), width=2 * ss)
    return im.resize((size // ss, size // ss), Image.LANCZOS)


def cinema_cover(hero, pre, word, loc, credit, latlon=None, coords=None, focus=(0.5, 0.5)):
    bg = fill_frame(hero.convert('RGB'), focus=focus)
    bg = ImageEnhance.Color(ImageEnhance.Contrast(bg).enhance(1.2)).enhance(1.15)
    r, g, b = bg.split()
    bg = Image.merge('RGB', (r.point(lambda v: min(255, int(v * 1.04 + 4))), g, b.point(lambda v: int(v * 0.94 + 10))))
    bg = vignette(bg).convert('RGBA')
    d = ImageDraw.Draw(bg)
    wf = fit(d, word, ANTON, 900, 230, 300)
    ww, wh, wb = tsize(d, word, wf)
    y_word = H - 52 - wb[3]
    draw_text(bg, (56, y_word), word, wf, (255, 255, 255), shadow=(0, 6, 14, 170))
    py = y_word + wb[1] - 58
    pf = fit(d, pre, OSW, 900, 48, 40)
    d = ImageDraw.Draw(bg)
    d.rectangle((56, py + 6, 62, py + 44), fill=RED)
    draw_text(bg, (76, py), pre, pf, (255, 255, 255), shadow=(0, 2, 6, 200))
    # top-right locator
    lf, mf = font(OSW, 26), font(MONO, 20)
    if latlon is not None:
        gl = globe(78, *latlon)
        bg.alpha_composite(gl, (W - gl.width - 34, 30))
        tx = W - gl.width - 46
    else:
        tx = W - 40
    d = ImageDraw.Draw(bg)
    lw1 = tsize(d, loc, lf)[0]; lw2 = tsize(d, coords, mf)[0] if coords else 0
    y1 = 70 if latlon is not None else 40
    bottom = y1 + (64 if coords else 36)
    chip = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(chip).rounded_rectangle((tx - max(lw1, lw2) - 16, y1 - 8, tx + 12, bottom), 10, fill=(0, 0, 0, 150))
    bg.alpha_composite(chip)
    draw_text(bg, (tx, y1), loc, lf, (255, 255, 255), shadow=(0, 2, 6, 220), anchor='ra')
    if coords:
        draw_text(bg, (tx, y1 + 34), coords, mf, (255, 120, 110), anchor='ra')
    draw_text(bg, (W - 40, H - 40), credit + '   ORBITAL ATLAS', font(MONO, 16), (220, 220, 220), shadow=(0, 1, 4, 220), anchor='rs')
    return bg.convert('RGB')
