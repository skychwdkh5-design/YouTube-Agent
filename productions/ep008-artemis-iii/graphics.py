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
    mr = (900 - 780 * m) * S; mx = (W * 0.62 + 420 * m) * S; my = (H * 0.62 - 380 * m) * S
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], outline=DIM, width=6 * S)
    if m > 0.6:
        d.text((mx, my + mr + 18 * S), "MOON", font=font(30 * S, INTER), fill=DIM, anchor="ma")
    e = seg(u, 0.12, 0.42)
    ex, ey, er = W * 0.38 * S, H * 0.54 * S, 210 * e * S
    if er > 2:
        d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(14, 30, 58), outline=EARTH, width=8 * S)
        d.text((ex, ey + er + 72 * S), "EARTH", font=font(30 * S, INTER), fill=EARTH, anchor="ma")
    r = seg(u, 0.38, 0.72)
    if r > 0:
        rr = (210 + 48) * S
        d.arc([ex - rr, ey - rr, ex + rr, ey + rr], -90, -90 + 360 * r, fill=ACC, width=9 * S)
    t = seg(u, 0.50, 0.62)
    if t > 0:
        a = int(255 * t)
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.text((W * 0.62 * S, H * 0.40 * S), "NOW:", font=font(70 * S), fill=INK + (a,))
        ld.text((W * 0.62 * S, H * 0.50 * S), "273 MILES UP", font=font(96 * S), fill=ACC + (a,))
        ld.text((W * 0.62 * S, H * 0.645 * S), "about 440 km · low Earth orbit", font=font(34 * S, INTER), fill=INK + (a,))
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
    sc = 1.15 * S; base = (H - 120) * S; x0 = W * 0.36 * S
    if mode == "swap":
        out = seg(u, 0.28, 0.50); inn = seg(u, 0.74, 0.90)
        if u < 0.74:
            box = _stack(d, x0, base, sc, "icps", upper_dx=out * 420 * S, upper_glow=u < 0.5, upper_dy=-out * 900 * S)
        else:
            box = _stack(d, x0, base, sc, "spacer", upper_dx=-(1 - inn) * 900 * S)
        tx = W * 0.58 * S
        if u < 0.74:
            d.text((tx, H * 0.30 * S), "ARTEMIS II ROCKET:", font=font(46 * S), fill=DIM)
            d.text((tx, H * 0.38 * S), "UPPER STAGE", font=font(104 * S), fill=ACC)
            d.text((tx, H * 0.52 * S), "the stage that sends Orion\ntoward the Moon", font=font(36 * S, INTER), fill=INK, spacing=10 * S)
        else:
            d.text((tx, H * 0.30 * S), "ARTEMIS III ROCKET:", font=font(46 * S), fill=DIM)
            d.text((tx, H * 0.38 * S), "SPACER", font=font(104 * S), fill=INK)
            if u > 0.9:
                d.text((tx, H * 0.52 * S), "NO ENGINE", font=font(80 * S), fill=ACC)
        if 0 < out < 1 and u < 0.74:
            d.text((box[0], box[1] - 40 * S), "UPPER STAGE", font=font(26 * S, INTER), fill=ACC)
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
