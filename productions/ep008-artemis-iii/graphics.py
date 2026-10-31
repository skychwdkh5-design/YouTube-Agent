"""EP008 animated diagrams + shared frame helpers (used by hook20.py and later the full draft).

Style and rules taken from NEXORA motion_spec.json (nexora-import/production-artemis3/motion_spec.json):
dark navy background, white ink, dim grey line art, one yellow accent; "original vector line art only; no company
artwork, no NASA insignia, no photoreal renders; every number shows its source line". Label changed from
"NEXORA GRAPHIC" to "ORBITAL ATLAS DIAGRAM". Nothing here is presented as footage.

d_orbit_vs_moon(u)  - motion_spec g-feb-orbit (orbit ring draws around an Earth outline) + g-moon-x (Moon outline),
                      extended: the Moon recedes, Earth and a low-Earth-orbit ring take over, "273 MILES UP".
d_sls_stack(u, mode) - new (not in motion_spec): SLS side view; the upper stage (ICPS) slides out, the spacer slides in.
All drawing at 2x then downsampled (anti-aliasing). u = 0..1 progress through the shot.
"""
import math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
S = 2                                            # supersampling
INK, DIM, ACC, BG = (240, 244, 250), (150, 162, 180), (255, 196, 64), (8, 14, 26)
EARTH, RED = (90, 150, 230), (229, 50, 45)
ANTON = "/home/claude/fonts/Anton-Regular.ttf"
INTER = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
_fc = {}


def font(size, face=ANTON):
    k = (face, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(face if os.path.exists(face) else INTER, size)
    return _fc[k]


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def seg(u, a, b):
    return ease((u - a) / max(b - a, 1e-6))


def label_lines(d, label, source):
    d.text((70 * S, (H - 64) * S), label, font=font(22 * S, INTER), fill=DIM)
    if source:
        d.text(((W - 70) * S, (H - 64) * S), source, font=font(22 * S, INTER), fill=DIM, anchor="ra")


def finish(im):
    return im.resize((W, H), Image.LANCZOS)


def d_orbit_vs_moon(u):
    """0-0.35: Moon outline large, recedes to the upper right (NOT TO SCALE); Earth grows in at left-centre.
    0.35-0.7: LEO ring draws around Earth (g-feb-orbit). 0.6+: '273 MILES UP' + metric, source line."""
    im = Image.new("RGB", (W * S, H * S), BG); d = ImageDraw.Draw(im)
    for i in range(140):                                      # faint fixed star field
        x = (i * 7919) % W; y = (i * 104729) % H
        d.point((x * S, y * S), fill=(60, 70, 90))
    m = seg(u, 0.0, 0.38)
    mr = (900 - 800 * m) * S; mx = (W * 0.62 + 640 * m) * S; my = (H * 0.62 - 450 * m) * S
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], outline=DIM, width=6 * S)
    if m > 0.6:
        d.text((mx, my + mr + 18 * S), "MOON", font=font(30 * S, INTER), fill=DIM, anchor="ma")
    e = seg(u, 0.12, 0.42)
    ex, ey, er = W * 0.30 * S, H * 0.50 * S, 330 * e * S
    if er > 2:
        d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(14, 30, 58), outline=EARTH, width=8 * S)
        d.text((ex, ey + er + 92 * S), "EARTH", font=font(30 * S, INTER), fill=EARTH, anchor="ma")
    r = seg(u, 0.38, 0.72)
    if r > 0:
        rr = (330 + 66) * S
        d.arc([ex - rr, ey - rr, ex + rr, ey + rr], -90, -90 + 360 * r, fill=ACC, width=14 * S)
    t = seg(u, 0.50, 0.62)
    if t > 0:
        a = int(255 * t)
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.text((W * 0.585 * S, H * 0.33 * S), "NOW:", font=font(84 * S), fill=INK + (a,))
        ld.text((W * 0.585 * S, H * 0.44 * S), "273 MILES UP", font=font(140 * S), fill=ACC + (a,))
        ld.text((W * 0.585 * S, H * 0.63 * S), "about 440 km · low Earth orbit", font=font(42 * S, INTER), fill=INK + (a,))
        im.paste(lay, (0, 0), lay)
    label_lines(d, "ORBITAL ATLAS DIAGRAM · NOT TO SCALE", "Source: NASA Artemis III flight profile, Oct 23, 2026")
    return finish(im)


def _stack(d, x0, base, sc, upper, upper_dx=0, upper_glow=False, upper_dy=0):
    """SLS Block 1 side view, simplified line art. upper: 'icps' or 'spacer'. Returns the upper element box."""
    cw = 84 * sc; core_h = 520 * sc
    cx = x0
    # boosters
    for bx in (cx - cw / 2 - 30 * sc, cx + cw / 2 + 30 * sc):
        d.rounded_rectangle([bx - 26 * sc, base - 470 * sc, bx + 26 * sc, base], 10 * sc, outline=INK, width=4 * S)
        d.polygon([(bx - 26 * sc, base - 470 * sc), (bx, base - 530 * sc), (bx + 26 * sc, base - 470 * sc)], outline=INK, width=4 * S)
    d.rectangle([cx - cw / 2, base - core_h, cx + cw / 2, base], outline=(230, 140, 60), width=5 * S)
    d.text((cx, base - core_h / 2), "CORE\nSTAGE", font=font(int(20 * sc), INTER), fill=(230, 140, 60), anchor="mm", align="center")
    top = base - core_h
    d.polygon([(cx - cw / 2, top), (cx + cw / 2, top), (cx + cw * 0.35, top - 50 * sc), (cx - cw * 0.35, top - 50 * sc)], outline=DIM, width=4 * S)
    top -= 50 * sc
    uh = 110 * sc; uw = cw * 0.7
    ux = cx + upper_dx
    box = [ux - uw / 2, top - uh + upper_dy, ux + uw / 2, top + upper_dy]
    if upper == "icps":
        col = ACC if upper_glow else INK
        d.rectangle(box, outline=col, width=6 * S)
        d.polygon([(ux - uw * 0.25, top + upper_dy), (ux + uw * 0.25, top + upper_dy), (ux, top + upper_dy + 26 * sc)], outline=col, width=4 * S)   # engine bell
    elif upper == "spacer":
        d.rectangle(box, outline=(170, 176, 186), width=6 * S, fill=(40, 46, 58))
    top -= uh
    d.polygon([(cx - uw / 2, top), (cx + uw / 2, top), (cx + uw * 0.42, top - 40 * sc), (cx - uw * 0.42, top - 40 * sc)], outline=DIM, width=4 * S)
    top -= 40 * sc
    d.polygon([(cx - uw * 0.42, top), (cx + uw * 0.42, top), (cx, top - 110 * sc)], outline=INK, width=4 * S)  # Orion + LAS
    d.line([(cx, top - 110 * sc), (cx, top - 170 * sc)], fill=INK, width=4 * S)
    return box


def d_sls_stack(u, mode="swap"):
    """mode 'swap' (s02.2): ICPS glows (0-0.25), slides out right (0.25-0.5), spacer slides in from left (0.55-0.85).
    mode 'to_a4' (s05.6): the ICPS moves from an Artemis III stack to an Artemis IV stack."""
    im = Image.new("RGB", (W * S, H * S), BG); d = ImageDraw.Draw(im)
    sc = 1.9 * S; base = (H * 0.45 + 625 * 1.9) * S; x0 = W * 0.30 * S
    if mode == "swap":
        out = seg(u, 0.28, 0.50); inn = seg(u, 0.74, 0.90)
        if u < 0.74:
            box = _stack(d, x0, base, sc, "icps", upper_dx=out * 420 * S, upper_glow=u < 0.5, upper_dy=-out * 900 * S)
        else:
            box = _stack(d, x0, base, sc, "spacer", upper_dx=-(1 - inn) * 900 * S)
        tx = W * 0.58 * S
        if u < 0.74:
            d.text((tx, H * 0.30 * S), "ARTEMIS II ROCKET:", font=font(46 * S), fill=DIM)
            d.text((tx, H * 0.38 * S), "UPPER STAGE", font=font(130 * S), fill=ACC)
            d.text((tx, H * 0.56 * S), "the stage that sends Orion\ntoward the Moon", font=font(44 * S, INTER), fill=INK, spacing=10 * S)
        else:
            d.text((tx, H * 0.30 * S), "ARTEMIS III ROCKET:", font=font(46 * S), fill=DIM)
            d.text((tx, H * 0.38 * S), "SPACER", font=font(130 * S), fill=INK)
            if u > 0.9:
                d.text((tx, H * 0.56 * S), "NO ENGINE", font=font(110 * S), fill=ACC)
        if 0 < out < 1 and u < 0.74:
            d.text((box[0], box[1] - 54 * S), "UPPER STAGE", font=font(36 * S, INTER), fill=ACC)
    label_lines(d, "ORBITAL ATLAS DIAGRAM · SIMPLIFIED, NOT TO SCALE", "Source: NASA Artemis III hardware update, Aug 5, 2026")
    return finish(im)


# ---------------------------------------------------------------- photos
_src = {}


def load(path, max_w=3840):
    if path not in _src:
        im = Image.open(path).convert("RGB")
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        _src[path] = im
    return _src[path]


def photo(path, u, box0, box1, credit=None):
    """Ken Burns between two crop boxes given as fractions (x0, y0, x1, y1) of the source; never upscales past the
    source's own pixels (asserted)."""
    src = load(path); sw, sh = src.size
    k = ease(u)
    b = [box0[i] + (box1[i] - box0[i]) * k for i in range(4)]
    x0, y0, x1, y1 = b[0] * sw, b[1] * sh, b[2] * sw, b[3] * sh
    h = (x1 - x0) * 9 / 16; cy = (y0 + y1) / 2 if y1 > y0 else y0 + h / 2
    y0 = min(max(cy - h / 2, 0), sh - h); y1 = y0 + h
    orig_w = Image.open(path).width
    assert (x1 - x0) * orig_w / sw >= W * 0.98, f"{path}: crop would upscale"
    im = src.resize((W, H), Image.BICUBIC, box=(x0, y0, x1, y1))
    if credit:
        ImageDraw.Draw(im).text((W - 40, H - 34), credit, font=font(24, INTER), fill=INK, anchor="rs",
                                stroke_width=2, stroke_fill=(0, 0, 0))
    return im


def text_on(im, xy, s, size, color=INK, anchor="la", alpha=1.0, face=ANTON):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text(xy, s, font=font(size, face), fill=color + (int(255 * alpha),), anchor=anchor,
           stroke_width=max(3, size // 14), stroke_fill=(0, 0, 0, int(255 * alpha)))
    im = im.convert("RGBA"); im.alpha_composite(lay); return im.convert("RGB")


# ---------------------------------------------------------------- mission chips (owner rule 2026-10-31)
# Every frame says which mission it belongs to, so Artemis II pictures are never read as a flown Artemis III.
CHIPS = {
    "a2":     ("ARTEMIS II · FLOWN APR 2026 · REAL PHOTO", (38, 104, 200), (255, 255, 255)),
    "a2vid":  ("ARTEMIS II · FLOWN APR 2026 · NASA VIDEO", (38, 104, 200), (255, 255, 255)),
    "a3plan": ("ARTEMIS III · PLANNED 2027 · NOT FLOWN", (255, 210, 30), (0, 0, 0)),
    "a3hw":   ("ARTEMIS III HARDWARE · ON THE GROUND, 2026", (245, 245, 245), (0, 0, 0)),
}


def chip(im, kind, size=30):
    text, fill, col = CHIPS[kind]
    im = im.convert("RGBA"); lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = font(size, INTER); w = d.textlength(text, font=f); x = W - 48 - w - 32; y = 44
    d.rounded_rectangle([x, y, x + w + 32, y + size + 22], 10, fill=fill + (240,)); d.text((x + 16, y + 9), text, font=f, fill=col)
    im.alpha_composite(lay); return im.convert("RGB")


def d_timeline(u):
    """s03: dated timeline, playhead runs Feb 27 -> Oct 23, 2026; then 2027 (Artemis III, Earth orbit) and 2028 (Artemis IV, landing)."""
    im = Image.new("RGB", (W * S, H * S), BG); d = ImageDraw.Draw(im)
    x0, x1, y = 160 * S, (W - 160) * S, H * 0.56 * S
    d.line([(x0, y), (x1, y)], fill=DIM, width=5 * S)
    marks = [(0.00, "APR 2026", "Artemis II flies\naround the Moon", (90, 150, 230)),
             (0.18, "FEB 27, 2026", "NASA changes\nthe plan", ACC),
             (0.42, "OCT 23, 2026", "Flight plan\npublished", ACC),
             (0.68, "2027", "Artemis III (planned):\nEarth orbit test", INK),
             (0.92, "2028", "Artemis IV (planned):\nfirst landing", INK)]
    marks.sort(key=lambda m: m[0]); marks[0], marks[1] = marks[1], marks[0]     # Feb 27 is left of April
    pos = [0.06, 0.24, 0.46, 0.70, 0.92]
    for k, ((_, date, what, col), p) in enumerate(zip(marks, pos)):
        a = seg(u, 0.08 + k * 0.15, 0.2 + k * 0.15)
        if a <= 0:
            continue
        x = x0 + (x1 - x0) * p
        c = tuple(int(BG[i] + (col[i] - BG[i]) * a) for i in range(3))
        d.ellipse([x - 14 * S, y - 14 * S, x + 14 * S, y + 14 * S], fill=c)
        d.text((x, y - 50 * S), date, font=font(54 * S), fill=c, anchor="ms")
        d.multiline_text((x, y + 44 * S), what, font=font(32 * S, INTER), fill=c, anchor="ma", align="center", spacing=8 * S)
    ph = seg(u, 0.08, 0.80)
    d.line([(x0, y), (x0 + (x1 - x0) * 0.92 * ph, y)], fill=ACC, width=7 * S)
    label_lines(d, "ORBITAL ATLAS DIAGRAM", "Sources: NASA Feb 27, Apr 11, Oct 23, 2026")
    return finish(im)



# ---------------------------------------------------------------- full-draft graphics (2026-10-31)
def _bg():
    im = Image.new("RGB", (W * S, H * S), BG); return im, ImageDraw.Draw(im)


def _alpha_text(im, xy, txt, f, col, a, anchor="la", spacing=0):
    if a <= 0:
        return
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    if "\n" in txt:
        ld.multiline_text(xy, txt, font=f, fill=col + (int(255 * a),), anchor=anchor, spacing=spacing)
    else:
        ld.text(xy, txt, font=f, fill=col + (int(255 * a),), anchor=anchor)
    im.paste(lay, (0, 0), lay)


def d_timeline2(u, highlight=None):
    """Owner 2026-10-31: only two key dates, large."""
    im, d = _bg()
    y = H * 0.55 * S; x0, x1 = 520 * S, (W - 520) * S
    ph = seg(u, 0.05, 0.6)
    d.line([(x0, y), (x1, y)], fill=DIM, width=6 * S)
    d.line([(x0, y), (x0 + (x1 - x0) * ph, y)], fill=ACC, width=10 * S)
    for k, (p, date, what) in enumerate([(0.0, "FEB 27, 2026", "NASA changes the plan"), (1.0, "OCT 23, 2026", "NASA publishes the flight plan")]):
        a = seg(u, 0.05 + k * 0.45, 0.2 + k * 0.45)
        x = x0 + (x1 - x0) * p
        if a > 0:
            d.ellipse([x - 26 * S, y - 26 * S, x + 26 * S, y + 26 * S], fill=ACC)
        _alpha_text(im, (x, y - 70 * S), date, font(110 * S), ACC, a, "ms")
        _alpha_text(im, (x, y + 70 * S), what, font(52 * S, INTER), INK, a, "ma")
    label_lines(d, "ORBITAL ATLAS DIAGRAM", "Sources: NASA, Feb 27 and Oct 23, 2026")
    return finish(im)


def card(u, title, items, source="", label="ORBITAL ATLAS GRAPHIC", title_col=ACC, item_size=58, big=None):
    """Generic motion_spec card: title lands, items build one by one."""
    im, d = _bg()
    _alpha_text(im, (150 * S, 170 * S), title, font(96 * S), title_col, seg(u, 0.0, 0.12))
    y = 340 * S
    n = max(len(items), 1)
    for k, it in enumerate(items):
        a = seg(u, 0.1 + 0.7 * k / n, 0.2 + 0.7 * k / n)
        if a > 0:
            d.rectangle([150 * S, y + 18 * S, 166 * S, y + 34 * S], fill=ACC)
        _alpha_text(im, (200 * S, y), it, font(item_size * S, INTER), INK, a)
        y += int(item_size * 1.75) * S
    if big:
        _alpha_text(im, ((W - 150) * S, (H - 170) * S), big, font(150 * S), ACC, seg(u, 0.3, 0.45), "rs")
    label_lines(d, label, source)
    return finish(im)


def quote(u, text, who, source):
    im, d = _bg()
    d.text((140 * S, 120 * S), "“", font=font(260 * S), fill=ACC)
    _alpha_text(im, (180 * S, 330 * S), text, font(66 * S, INTER), INK, seg(u, 0.03, 0.15), spacing=26 * S)
    _alpha_text(im, (180 * S, (H - 230) * S), who, font(44 * S), ACC, seg(u, 0.15, 0.27))
    label_lines(d, "QUOTE", source)
    return finish(im)


def d_plan_swap(u):
    """Feb 27 change: Artemis III LANDING -> EARTH ORBIT TEST 2027; Artemis IV FIRST LANDING 2028."""
    im, d = _bg()
    a3 = seg(u, 0.25, 0.45); a4 = seg(u, 0.55, 0.75)
    rows = [("ARTEMIS III", "MOON LANDING", "EARTH ORBIT TEST · 2027", a3), ("ARTEMIS IV", "", "FIRST LANDING · 2028 (TARGET)", a4)]
    for k, (name, old, new, a) in enumerate(rows):
        y = (300 + k * 300) * S
        d.text((150 * S, y), name, font=font(110 * S), fill=INK)
        if old:
            _alpha_text(im, (820 * S, y + 10 * S), old, font(96 * S), DIM, 1 - a * 0.6)
            if a > 0:
                tw = font(96 * S).getlength(old)
                d.line([(820 * S, y + 80 * S), (820 * S + tw * a, y + 80 * S)], fill=RED, width=12 * S)
            _alpha_text(im, (820 * S, y + 140 * S), new, font(72 * S), ACC, a)
        else:
            _alpha_text(im, (820 * S, y + 10 * S), new, font(96 * S), ACC, a)
    label_lines(d, "ORBITAL ATLAS DIAGRAM", "Source: NASA, Feb 27, 2026")
    return finish(im)


def d_stage_to_a4(u):
    """Artemis III stack (spacer) | Artemis IV stack: the upper stage moves across."""
    im, d = _bg()
    sc = 1.05 * S; base = (H - 110) * S
    _stack(d, W * 0.25 * S, base, sc, "spacer")
    m = seg(u, 0.25, 0.75)
    box = _stack(d, W * 0.62 * S, base, sc, "none")
    bx0 = (W * 0.25 - W * 0.62) * S * (1 - m)
    uw = box[2] - box[0]; uh = box[3] - box[1]
    cx = (box[0] + box[2]) / 2 + bx0; arc = math.sin(math.pi * m) * 220 * S
    d.rectangle([cx - uw / 2, box[1] - arc, cx + uw / 2, box[3] - arc], outline=ACC, width=6 * S)
    d.text((W * 0.25 * S, 70 * S), "ARTEMIS III", font=font(64 * S), fill=INK, anchor="ma")
    d.text((W * 0.62 * S, 70 * S), "ARTEMIS IV", font=font(64 * S), fill=ACC, anchor="ma")
    _alpha_text(im, (W * 0.78 * S, H * 0.42 * S), "UPPER STAGE\nREASSIGNED", font(72 * S), ACC, seg(u, 0.7, 0.85), spacing=10 * S)
    label_lines(d, "ORBITAL ATLAS DIAGRAM · SIMPLIFIED, NOT TO SCALE", "Source: NASA hardware update, Aug 5, 2026")
    return finish(im)


def d_orbits(u, step):
    """s08: Earth limb at the bottom; orbits drawn as arcs at relative heights (NOT TO SCALE). step 1..4."""
    im, d = _bg()
    R0 = 2600 * S; cx, cy = W * 0.5 * S, (H + 2250) * S
    d.ellipse([cx - R0, cy - R0, cx + R0, cy + R0], fill=(14, 30, 58), outline=EARTH, width=6 * S)
    def arc(h, col, wdt, a, label, xlab):
        r = R0 + h * S
        if a > 0:
            d.arc([cx - r, cy - r, cx + r, cy + r], 250, 250 + 40 * a, fill=col, width=wdt * S)
            _alpha_text(im, (xlab * S, cy - r - 70 * S), label, font(46 * S), col, a)
    arc(470, (200, 210, 225), 7, seg(u, 0.0, 0.3) if step >= 1 else 0, "BLUE MOON TEST ARTICLE · ~273 MI (237 NMI)", 120)
    if step >= 2:
        k = seg(u, 0.0, 0.5)
        r = R0 + 600 * S
        d.arc([cx - r, cy - r, cx + r, cy + r], 250, 250 + 40 * k, fill=ACC, width=9 * S)
        _alpha_text(im, (980 * S, cy - r - 70 * S), "ORION · 18 x 1,122 MI → ~345 MI", font(46 * S), ACC, k)
    if step >= 3:
        k = seg(u, 0.0, 0.4)
        r = R0 + 330 * S
        d.arc([cx - r, cy - r, cx + r, cy + r], 250, 250 + 40 * k, fill=(150, 200, 255), width=7 * S)
        _alpha_text(im, (980 * S, cy - r - 70 * S), "STARSHIP · 206 NMI (~237 MI)", font(46 * S), (150, 200, 255), k)
    if step >= 4:
        _alpha_text(im, (W * 0.5 * S, 120 * S), "ALL NUMBERS: NASA FLIGHT PROFILE", font(64 * S), INK, seg(u, 0.0, 0.3), "ma")
    label_lines(d, "ORBITAL ATLAS DIAGRAM · HEIGHTS NOT TO SCALE", "Source: NASA Artemis III flight profile, Oct 23, 2026")
    return finish(im)


def _orion(d, x, y, sc, col=INK):
    d.polygon([(x - 40 * sc, y + 30 * sc), (x + 40 * sc, y + 30 * sc), (x + 22 * sc, y - 30 * sc), (x - 22 * sc, y - 30 * sc)], outline=col, width=4 * S)
    d.rectangle([x - 40 * sc, y + 30 * sc, x + 40 * sc, y + 100 * sc], outline=col, width=4 * S)
    for sx in (-1, 1):
        d.line([(x + sx * 40 * sc, y + 70 * sc), (x + sx * 170 * sc, y + 40 * sc)], fill=col, width=4 * S)


def d_dock(u, mode):
    """Own line-art ILLUSTRATION (no company artwork): 'side' Orion beside a generic lander cabin; 'hatch' crew icons cross;
    'nose' Orion nose-to-nose with a tall generic vehicle (171 ft vs Orion to scale-ish); 'timer' up to 2 h, crew stays."""
    im, d = _bg(); sc = 2.0 * S
    if mode in ("side", "hatch"):
        lx, ly = W * 0.62 * S, H * 0.5 * S
        d.rectangle([lx - 120 * sc, ly - 220 * sc, lx + 120 * sc, ly + 160 * sc], outline=DIM, width=4 * S)        # generic lander
        d.rectangle([lx - 120 * sc, ly - 220 * sc, lx + 120 * sc, ly - 90 * sc], outline=INK, width=4 * S)         # crew cabin
        for sx in (-1, 1):
            d.line([(lx + sx * 120 * sc, ly + 160 * sc), (lx + sx * 190 * sc, ly + 260 * sc)], fill=DIM, width=4 * S)
        d.text((lx, ly + 300 * sc), "LANDER TEST ARTICLE (GENERIC)", font=font(26 * S, INTER), fill=DIM, anchor="ma")
        k = seg(u, 0.05, 0.7) if mode == "side" else 1.0
        ox = W * 0.10 * S + (lx - 120 * sc - 110 * sc - W * 0.10 * S) * k
        d.ellipse([ox - 60 * sc, ly - 215 * sc, ox + 60 * sc, ly - 95 * sc], outline=ACC, width=5 * S)
        d.text((ox, ly - 20 * sc), "ORION", font=font(40 * S), fill=ACC, anchor="ma")
        if mode == "side":
            _alpha_text(im, (110 * S, (H - 300) * S), "DOCK 1 · PORT BESIDE THE CREW CABIN", font(64 * S), INK, seg(u, 0.0, 0.15))
            _alpha_text(im, (110 * S, (H - 210) * S), "ORION'S SOFTWARE FLIES THE PAIR", font(52 * S), ACC, seg(u, 0.7, 0.85))
        else:
            for i in range(2):
                p = seg(u, 0.2 + i * 0.2, 0.55 + i * 0.2)
                fx = ox + (lx - ox) * p; fy = ly - 155 * sc
                d.ellipse([fx - 14 * sc, fy - 40 * sc, fx + 14 * sc, fy - 12 * sc], fill=(255, 140, 40))
                d.rectangle([fx - 16 * sc, fy - 10 * sc, fx + 16 * sc, fy + 40 * sc], fill=(255, 140, 40))
            _alpha_text(im, (110 * S, (H - 300) * S), "HATCH OPEN · UP TO 2 CREW INSIDE", font(64 * S), INK, seg(u, 0.0, 0.15))
            _alpha_text(im, (110 * S, (H - 210) * S), "ORANGE ORION SURVIVAL SUITS", font(52 * S), (255, 140, 40), seg(u, 0.3, 0.45))
    else:
        sx0 = W * 0.70 * S; top = 80 * S; bot = (H - 110) * S           # tall vehicle, nose at left-top
        d.rounded_rectangle([sx0 - 70 * S, top + 120 * S, sx0 + 70 * S, bot], 20 * S, outline=DIM, width=4 * S)
        d.polygon([(sx0 - 70 * S, top + 120 * S), (sx0, top), (sx0 + 70 * S, top + 120 * S)], outline=INK, width=4 * S)
        d.text((sx0 + 100 * S, H * 0.5 * S), "171 FT\n52 M", font=font(70 * S), fill=INK, spacing=8 * S)
        k = seg(u, 0.05, 0.6) if mode == "nose" else 1.0
        oy = (top - 10 * S) + 0; ox = W * 0.15 * S + (sx0 - 140 * S - W * 0.15 * S) * k
        d.ellipse([ox - 40 * S, oy + 10 * S, ox + 40 * S, oy + 70 * S], outline=ACC, width=5 * S)
        d.text((ox, oy + 90 * S), "ORION (TO SCALE: ~5 M WIDE)", font=font(26 * S, INTER), fill=ACC, anchor="ma")
        if mode == "nose":
            _alpha_text(im, (110 * S, H * 0.45 * S), "DOCK 2 · NOSE TO NOSE", font(76 * S), INK, seg(u, 0.0, 0.15))
            _alpha_text(im, (110 * S, H * 0.55 * S), "ORION FORWARD PORT\nSPACEX FLIES THE PAIR", font(52 * S), ACC, seg(u, 0.6, 0.75), spacing=10 * S)
        else:
            _alpha_text(im, (110 * S, H * 0.42 * S), "UP TO 2 HOURS", font(110 * S), ACC, 1)
            _alpha_text(im, (110 * S, H * 0.58 * S), "CREW STAYS IN ORION", font(76 * S), INK, seg(u, 0.2, 0.35))
            if u > 0.35:
                d.line([(sx0 - 60 * S, top + 300 * S), (sx0 + 60 * S, top + 420 * S)], fill=RED, width=10 * S)
                d.line([(sx0 + 60 * S, top + 300 * S), (sx0 - 60 * S, top + 420 * S)], fill=RED, width=10 * S)
    label_lines(d, "ORBITAL ATLAS ILLUSTRATION · NOT REAL FOOTAGE", "Source: NASA, Jul 15 and Oct 23, 2026")
    return finish(im)


def d_clock(u, big="~2 DAYS", sub="CHECKING CABIN · CONTROLS · LIFE SUPPORT"):
    im, d = _bg(); cx, cy, r = W * 0.27 * S, H * 0.5 * S, 260 * S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=DIM, width=6 * S)
    d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * seg(u, 0.05, 0.9), fill=ACC, width=18 * S)
    d.text((cx, cy), "48 H", font=font(110 * S), fill=INK, anchor="mm")
    _alpha_text(im, (W * 0.5 * S, H * 0.36 * S), big, font(150 * S), ACC, seg(u, 0.05, 0.2))
    _alpha_text(im, (W * 0.5 * S, H * 0.58 * S), sub.replace(" · ", "\n"), font(52 * S, INTER), INK, seg(u, 0.25, 0.4), spacing=14 * S)
    label_lines(d, "ORBITAL ATLAS GRAPHIC", "Source: NASA flight profile, Oct 23, 2026")
    return finish(im)


def d_handoff(u):
    """Artemis IV plan (illustration): Orion in lunar orbit, a lander meets it, goes down near the South Pole and back."""
    im, d = _bg(); cx, cy, r = W * 0.42 * S, H * 0.56 * S, 330 * S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(40, 42, 50), outline=DIM, width=5 * S)
    d.text((cx, cy), "MOON", font=font(60 * S), fill=DIM, anchor="mm")
    ro = r + 120 * S; d.ellipse([cx - ro, cy - ro, cx + ro, cy + ro], outline=(90, 100, 120), width=3 * S)
    a = math.radians(-60 + 300 * seg(u, 0.0, 0.35)); ox, oy = cx + ro * math.cos(a), cy + ro * math.sin(a)
    d.ellipse([ox - 22 * S, oy - 22 * S, ox + 22 * S, oy + 22 * S], fill=ACC)
    _alpha_text(im, (ox + 34 * S, oy - 30 * S), "ORION", font(40 * S), ACC, 1)
    m = seg(u, 0.35, 0.55); dn = seg(u, 0.6, 0.85)
    if m > 0:
        lx, ly = ox + 60 * S * (1 - m), oy + 40 * S
        sp = (cx, cy + r)                                            # south pole
        px, py = lx + (sp[0] - lx) * dn, ly + (sp[1] - ly) * dn
        d.rectangle([px - 18 * S, py - 26 * S, px + 18 * S, py + 26 * S], outline=INK, width=4 * S)
        _alpha_text(im, (px + 30 * S, py), "LANDER", font(36 * S), INK, 1)
    _alpha_text(im, (cx, cy + r + 30 * S), "SOUTH POLE REGION", font(36 * S, INTER), ACC, seg(u, 0.6, 0.75), "ma")
    _alpha_text(im, (W * 0.66 * S, H * 0.30 * S), "ARTEMIS IV\n(PLANNED 2028)", font(76 * S), ACC, 1, spacing=10 * S)
    _alpha_text(im, (W * 0.66 * S, H * 0.55 * S), "ORION CAN'T LAND.\nA LANDER MEETS IT,\nGOES DOWN, COMES BACK.", font(42 * S, INTER), INK, seg(u, 0.3, 0.45), spacing=12 * S)
    label_lines(d, "ORBITAL ATLAS ILLUSTRATION · NOT TO SCALE", "Source: NASA, Feb 27 and Oct 23, 2026")
    return finish(im)


def d_hours(u):
    im, d = _bg()
    for k, (title, big, note, col) in enumerate([("NEAR THE MOON", "DAYS", "Artemis II: flyby Apr 6 → splashdown Apr 10", DIM),
                                                 ("LOW EARTH ORBIT", "HOURS*", "*typical return, not a mission time", ACC)]):
        a = seg(u, 0.05 + k * 0.35, 0.2 + k * 0.35); x = (W * (0.27 + 0.46 * k)) * S
        _alpha_text(im, (x, H * 0.28 * S), title, font(64 * S), INK, a, "ma")
        _alpha_text(im, (x, H * 0.40 * S), big, font(200 * S), col, a, "ma")
        _alpha_text(im, (x, H * 0.70 * S), note, font(36 * S, INTER), INK, a, "ma")
    d.line([(W * 0.5 * S, H * 0.22 * S), (W * 0.5 * S, H * 0.80 * S)], fill=DIM, width=3 * S)
    label_lines(d, "ORBITAL ATLAS GRAPHIC · GENERAL EXPLANATION, NOT A NASA STATEMENT", "Artemis II dates: NASA, Apr 2026")
    return finish(im)


def d_apollo(u):
    im, d = _bg(); y = H * 0.40 * S; y2 = H * 0.72 * S; x0, x1 = 300 * S, (W - 300) * S
    rows = [(y, [("MAR 1969", "APOLLO 9\nLander tested in Earth orbit"), ("JUL 1969", "APOLLO 11\nFirst landing")], 0.0),
            (y2, [("2027", "ARTEMIS III (planned)\nLander tests in Earth orbit"), ("2028", "ARTEMIS IV (target)\nFirst Artemis landing")], 0.5)]
    for yy, pts, t0 in rows:
        a = seg(u, t0, t0 + 0.2)
        if a > 0:
            d.line([(x0, yy), (x0 + (x1 - x0) * a, yy)], fill=DIM, width=6 * S)
        for k, (date, what) in enumerate(pts):
            b = seg(u, t0 + 0.1 + k * 0.15, t0 + 0.25 + k * 0.15); x = x0 + (x1 - x0) * k
            if b > 0:
                d.ellipse([x - 18 * S, yy - 18 * S, x + 18 * S, yy + 18 * S], fill=ACC if t0 else INK)
            _alpha_text(im, (x, yy - 40 * S), date, font(72 * S), ACC if t0 else INK, b, "ms")
            _alpha_text(im, (x, yy + 34 * S), what, font(36 * S, INTER), INK, b, "ma", spacing=8 * S)
    label_lines(d, "ORBITAL ATLAS DIAGRAM · HISTORICAL PARALLEL, NOT A NASA STATEMENT", "Apollo dates: historical record; Artemis: NASA 2026")
    return finish(im)


def d_distance(u):
    """s06: a few hundred miles vs the Moon (Moon distance shown as a broken bar)."""
    im, d = _bg(); y = H * 0.55 * S; x0 = 200 * S
    d.ellipse([x0 - 60 * S, y - 60 * S, x0 + 60 * S, y + 60 * S], fill=(14, 30, 58), outline=EARTH, width=6 * S)
    k = seg(u, 0.05, 0.35); d.line([(x0 + 60 * S, y), (x0 + 60 * S + 140 * S * k, y)], fill=ACC, width=16 * S)
    _alpha_text(im, (x0, y - 200 * S), "ARTEMIS III: ~345 MI", font(80 * S), ACC, k)
    m = seg(u, 0.4, 0.8); xe = x0 + 60 * S + (W - 460) * S * m
    for xx in range(int(x0 + 220 * S), int(xe), 60 * S):
        d.line([(xx, y), (xx + 30 * S, y)], fill=DIM, width=6 * S)
    if m > 0.95:
        d.ellipse([xe - 50 * S, y - 50 * S, xe + 50 * S, y + 50 * S], outline=DIM, width=5 * S)
    _alpha_text(im, ((W - 150) * S, y + 100 * S), "MOON: ~239,000 MI (AVERAGE)", font(60 * S), INK, seg(u, 0.75, 0.9), "ra")
    label_lines(d, "ORBITAL ATLAS DIAGRAM · DISTANCES TO SCALE ALONG THE LINE ARE NOT", "Source: NASA flight profile; Moon average distance")
    return finish(im)


# ---------------------------------------------------------------- NASA con-ops graphic in large fragments
CONOPS = "a3_conops_oct2026.jpg"
CO = {  # item boxes as fractions of the NASA graphic (4000x2250)
    "leo": (0.015, 0.54, 0.09, 0.66), "bm_check": (0.09, 0.22, 0.175, 0.435), "phasing": (0.215, 0.22, 0.315, 0.435),
    "bm_ops": (0.343, 0.22, 0.448, 0.435), "free": (0.468, 0.22, 0.565, 0.435), "ss_ops": (0.578, 0.22, 0.69, 0.435),
    "tests": (0.708, 0.27, 0.79, 0.415), "reentry": (0.82, 0.22, 0.915, 0.55), "splash": (0.855, 0.59, 0.97, 0.745),
    "r_ng": (0.055, 0.54, 0.21, 0.98), "r_sls": (0.205, 0.54, 0.33, 0.96), "r_ss": (0.565, 0.5, 0.715, 0.96),
}


def conops(path, u, view, boxes, title=None, sub=None, push=0.03):
    """view = (x0, y0, w) fraction of the graphic (w >= 0.48 keeps it at or above native resolution);
    boxes = keys of CO to highlight: everything else is dimmed, highlights get a yellow frame."""
    src = load(path, max_w=4000); sw, sh = src.size
    x0, y0, w = view; k = ease(u) * push
    bx = (x0 + k * w / 2) * sw, (y0 + k * w / 2 * 16 / 9 * sh / sw * 0) * sh
    cw = w * (1 - k) * sw; ch = cw * 9 / 16
    vx, vy = x0 * sw + k * w * sw / 2, y0 * sh + k * w * sw * 9 / 32
    vy = min(max(vy, 0), sh - ch); vx = min(max(vx, 0), sw - cw)
    assert cw >= W * 0.98, "con-ops crop would upscale"
    im = src.resize((W, H), Image.BICUBIC, box=(vx, vy, vx + cw, vy + ch))
    if boxes:
        dim = ImageEnhance_Brightness(im, 0.35); mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask)
        rects = []
        for b in boxes:
            X0, Y0, X1, Y1 = CO[b]
            r = ((X0 * sw - vx) / cw * W, (Y0 * sh - vy) / ch * H, (X1 * sw - vx) / cw * W, (Y1 * sh - vy) / ch * H)
            rects.append(r); md.rounded_rectangle(r, 18, fill=255)
        im = Image.composite(im, dim, mask.filter(ImageFilter.GaussianBlur(6)))
        d = ImageDraw.Draw(im); pulse = 6 + 3 * math.sin(u * 12)
        for r in rects:
            d.rounded_rectangle(r, 18, outline=ACC, width=int(pulse))
    if title:
        band = Image.new("L", (W, H), 0); bd = ImageDraw.Draw(band)
        for yy in range(240):
            bd.line([(0, yy), (W, yy)], fill=int(200 * (1 - max(0, yy - 170) / 70)))
        im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, band)
        im = text_on(im, (60, 50), title, 74, ACC, alpha=min(1, u * 6 + 0.2))
    if sub:
        im = text_on(im, (60, 140), sub, 50, INK, alpha=min(1, max(0, u * 6 - 0.6)))
    ImageDraw.Draw(im).text((W - 40, H - 34), "NASA CONCEPT GRAPHIC, OCT 23, 2026", font=font(24, INTER), fill=INK, anchor="rs", stroke_width=2, stroke_fill=(0, 0, 0))
    return im


def ImageEnhance_Brightness(im, f):
    from PIL import ImageEnhance
    return ImageEnhance.Brightness(im).enhance(f)


def portrait(path, u, credit):
    """Portrait still below 1920 px wide: shown at native height-fit (downscale only) over a blurred, darkened fill."""
    src = Image.open(path).convert("RGB")
    h = H; w = round(src.width * H / src.height)
    assert src.height >= H, "portrait would upscale"
    fg = src.resize((w, h), Image.LANCZOS)
    bg = src.resize((W, round(src.height * W / src.width)), Image.BILINEAR).crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(40))
    bg = ImageEnhance_Brightness(bg, 0.45); bg.paste(fg, ((W - w) // 2, 0))
    ImageDraw.Draw(bg).text((W - 40, H - 34), credit, font=font(24, INTER), fill=INK, anchor="rs", stroke_width=2, stroke_fill=(0, 0, 0))
    return bg
