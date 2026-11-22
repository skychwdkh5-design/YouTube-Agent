#!/usr/bin/env python3
"""EP009 painted 2.5D pilot v2 (56 s, 1920x1080, 30 fps) — scene-actor rebuild.
Uses ONLY the supplied package: NASA/NOAA originals (media_original/) and painted P01-P05 (+ P05 marker slices).
Documentary pixels are never repainted: highlights only dim/brighten real pixels inside a corridor mask;
painted actors live on separate layers with ILLUSTRATION / NOT TO SCALE.
Usage: python3 build_pilot_v2.py out.mp4 | --frames t1,t2,...
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageChops

REPO = "/home/claude/skychwdkh5-design/youtube-agent/productions/ep009-tornado-scars"
MO, AS = f"{REPO}/media_original", f"{REPO}/handoff/assets"
MK = f"{AS}/markers"
W, H, FPS, DUR = 1920, 1080, 30, 56.0
FI = "/usr/share/fonts/opentype/inter/"
F_TAG = ImageFont.truetype(FI + "Inter-SemiBold.otf", 22)
F_DATE = ImageFont.truetype(FI + "Inter-Bold.otf", 46)
F_HOOK = ImageFont.truetype(FI + "Inter-Black.otf", 118)
F_MID = ImageFont.truetype(FI + "Inter-ExtraBold.otf", 40)
INK, OCHRE, RUST = (244, 238, 226), (232, 176, 84), (196, 82, 38)

# ---------------- math / easing ----------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def lerp(a, b, u): return a + (b - a) * u
def e_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def e_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def e_in(x): x = clamp(x); return x ** 3
def e_back(x, c=1.7): x = clamp(x); return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def spring(x, k=9.0, z=4.0):  # 0->1 with damped overshoot
    x = max(0.0, x); return 1 - math.exp(-z * x) * math.cos(k * x)
def h01(i): v = math.sin(i * 127.1 + 311.7) * 43758.5453; return v - math.floor(v)
def noise1(t, s=0):  # smooth value noise -1..1
    i = math.floor(t); f = t - i; f = f * f * (3 - 2 * f)
    return lerp(h01(i + s * 97), h01(i + 1 + s * 97), f) * 2 - 1

# ---------------- assets ----------------
def ld(p): return Image.open(p).convert("RGBA" if p.endswith(".png") else "RGB")
def trim(im, thr=24):
    bb = im.getchannel("A").point(lambda v: 255 if v > thr else 0).getbbox(); return im.crop(bb)
M01 = ld(f"{MO}/nasa_tuscaloosa_EO1_20110502.jpg")
M2B = ld(f"{MO}/nasa_modis_before_20110412.jpg")
M2A = ld(f"{MO}/nasa_modis_after_20110428.jpg")
P = {n: trim(ld(f"{AS}/{n}.png")) for n in ["P01_satellite", "P02_storm", "P03_tree_intact", "P03_tree_uprooted", "P04_land_intact", "P04_land_scared"]}
for n in ["pin_red", "pin_ochre", "arrow_white", "arrow_orange", "measure_double"]: P[n] = trim(ld(f"{MK}/{n}.png"))

# Tornado damage swath on M01 (full-res px): tan corridor SW->NE through Tuscaloosa, read visually (editor to confirm).
# The thin straight white line ~45 px north-west of it is a contrail and is deliberately left out of the corridor.
TRACK = [(2024, 4248), (2420, 4014), (2780, 3798), (3104, 3618)]
TR_LEN = sum(math.dist(a, b) for a, b in zip(TRACK, TRACK[1:]))
def tr_pt(s):  # s in 0..1 along the swath
    d = clamp(s) * TR_LEN
    for a, b in zip(TRACK, TRACK[1:]):
        l = math.dist(a, b)
        if d <= l: return (lerp(a[0], b[0], d / l), lerp(a[1], b[1], d / l))
        d -= l
    return TRACK[-1]
TR_ANG = math.degrees(math.atan2(TRACK[-1][1] - TRACK[0][1], TRACK[-1][0] - TRACK[0][0]))  # screen angle (deg, y down)

# leaf particles cut from the supplied intact canopy (no new art)
def leaf_bits():
    t = P["P03_tree_intact"]; a = np.asarray(t.getchannel("A")); bits = []
    for k in range(18):
        for _ in range(50):
            x = int(h01(k * 7 + _) * (t.width - 60)); y = int(h01(k * 13 + _ + 3) * t.height * 0.45)
            if a[y:y + 46, x:x + 46].mean() > 200:
                c = t.crop((x, y, x + 46, y + 46)); m = Image.new("L", (46, 46), 0)
                ImageDraw.Draw(m).ellipse([4, 8, 42, 38], fill=255); m = m.filter(ImageFilter.GaussianBlur(3))
                c.putalpha(ImageChops.multiply(c.getchannel("A"), m)); bits.append(c); break
    return bits
LEAVES = leaf_bits()

# ---------------- compositing primitives ----------------
def cam(img, cx, cy, vw, rot=0.0, size=(W, H)):
    """Camera on documentary image: centre (cx,cy) source px, vw = source px across frame width, rot = roll deg."""
    vh = vw * size[1] / size[0]
    if not rot:
        return img.transform(size, Image.EXTENT, (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2), Image.BILINEAR, fillcolor=(0, 0, 0))
    s = vw / size[0]; c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    a, b = s * c, -s * sn; d, e = s * sn, s * c
    ox, oy = size[0] / 2, size[1] / 2
    return img.transform(size, Image.AFFINE, (a, b, cx - a * ox - b * oy, d, e, cy - d * ox - e * oy), Image.BILINEAR, fillcolor=(0, 0, 0))
def scr(pt, cx, cy, vw): s = W / vw; return (W / 2 + (pt[0] - cx) * s, H / 2 + (pt[1] - cy) * s)

def put(fr, im, x, y, h, rot=0.0, a=1.0, anc=(0.5, 0.5), sh=0.55, shoff=(0.04, 0.06), sx=1.0, sy=1.0, blur=0.0, tint=None):
    """Painted actor with contact shadow; sx/sy = squash/stretch; blur = depth-of-field."""
    if a <= 0.01 or h < 3: return
    k = h / im.height
    im2 = im.resize((max(1, int(im.width * k * sx)), max(1, int(im.height * k * sy))), Image.LANCZOS)
    if tint: im2 = grade(im2, tint)
    if blur > 0.3: im2 = im2.filter(ImageFilter.GaussianBlur(blur))
    if rot: im2 = im2.rotate(rot, Image.BICUBIC, expand=True)
    if a < 1: im2.putalpha(im2.getchannel("A").point(lambda v: int(v * a)))
    px, py = int(x - im2.width * anc[0]), int(y - im2.height * anc[1])
    if sh > 0:
        s = Image.new("RGBA", im2.size, (6, 10, 22, 0)); s.putalpha(im2.getchannel("A").point(lambda v: int(v * sh)).filter(ImageFilter.GaussianBlur(max(2, h * 0.035))))
        fr.alpha_composite(s, (px + int(h * shoff[0]), py + int(h * shoff[1])))
    fr.alpha_composite(im2, (px, py))
def grade(im, tint):  # tint=(r,g,b,amount) colour-match a painted layer to the scene light
    r, g, b, amt = tint; base = im.convert("RGB"); col = Image.new("RGB", im.size, (r, g, b))
    out = Image.blend(base, ImageChops.multiply(base, col), amt).convert("RGBA"); out.putalpha(im.getchannel("A")); return out

def bend(im, amt, pivot_frac=1.0, power=2.0, strips=28):
    """Mesh-warp a standing object: rows shift horizontally by amt*h^power (h=0 at base). Natural sway/bend."""
    pad = int(abs(amt) * im.height) + 4; Wd = im.width + 2 * pad
    src = Image.new("RGBA", (Wd, im.height), (0, 0, 0, 0)); src.paste(im, (pad, 0))
    mesh = []; Hh = im.height
    for i in range(strips):
        y0, y1 = int(Hh * i / strips), int(Hh * (i + 1) / strips)
        h0, h1 = 1 - y0 / Hh, 1 - y1 / Hh
        d0, d1 = amt * Hh * h0 ** power, amt * Hh * h1 ** power
        mesh.append(((0, y0, Wd, y1), (0 - d0, y0, 0 - d1, y1, Wd - d1, y1, Wd - d0, y0)))
    return src.transform((Wd, Hh), Image.MESH, mesh, Image.BICUBIC), pad

def churn(im, t, amp=0.025, strips=20):
    """Living cloud: rows drift with phase-shifted sine (turbulent churn) — mesh warp, no new pixels."""
    pad = int(amp * im.width) + 4; Wd = im.width + 2 * pad
    src = Image.new("RGBA", (Wd, im.height), (0, 0, 0, 0)); src.paste(im, (pad, 0)); mesh = []
    for i in range(strips):
        y0, y1 = int(im.height * i / strips), int(im.height * (i + 1) / strips)
        d0 = amp * im.width * math.sin(t * 2.1 + i * 0.7); d1 = amp * im.width * math.sin(t * 2.1 + (i + 1) * 0.7)
        mesh.append(((0, y0, Wd, y1), (-d0, y0, -d1, y1, Wd - d1, y1, Wd - d0, y0)))
    return src.transform((Wd, im.height), Image.MESH, mesh, Image.BICUBIC)

def corridor_mask(cx, cy, vw, s0=0.0, s1=1.0, width_src=95, feather=0.5):
    """Screen-space soft mask over the documented swath only (drawn at 1/4 res then blurred/upscaled)."""
    q = 4; m = Image.new("L", (W // q, H // q), 0); d = ImageDraw.Draw(m)
    n = 24; pts = [scr(tr_pt(lerp(s0, s1, i / n)), cx, cy, vw) for i in range(n + 1)]
    pts = [(x / q, y / q) for x, y in pts]; wpx = max(2, int(width_src * W / vw / q))
    if s1 > s0 + 1e-3: d.line(pts, fill=255, width=wpx, joint="curve")
    return m.filter(ImageFilter.GaussianBlur(wpx * feather)).resize((W, H), Image.BILINEAR)

def spotlight(fr_rgb, mask, dim=0.42, lift=1.12):
    dark = ImageEnhance.Brightness(ImageEnhance.Color(fr_rgb).enhance(0.55)).enhance(dim)
    lit = ImageEnhance.Brightness(fr_rgb).enhance(lift)
    return Image.composite(lit, dark, mask)

def measure(fr, p1, p2, u, lift=60, h=110):
    if u <= 0.01: return
    md = P["measure_double"]; ln = math.dist(p1, p2) * 0.9; nat = h * md.width / md.height
    put(fr, md, (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 - lift, h, rot=-math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])),
        sx=max(0.02, u) * ln / nat, a=clamp(u * 2), sh=0.4)

def ring(fr, x, y, r, a, col=OCHRE, w=6):
    if a <= 0.01: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse([x - r, y - r * 0.55, x + r, y + r * 0.55], outline=col + (int(255 * a),), width=w)
    fr.alpha_composite(lay)

def text_k(fr, words, x, y, t0, t, font=F_HOOK, col=INK, acc=None, gap=0.16, anchor="l"):
    """Kinetic title: each word slams in (scale 1.25->1, blur->sharp, rise), staggered."""
    d0 = ImageDraw.Draw(fr); widths = [d0.textlength(w_ + " ", font=font) for w_ in words]
    total = sum(widths); xx = x - (total / 2 if anchor == "c" else 0)
    for i, w_ in enumerate(words):
        u = seg(t, t0 + i * gap, t0 + i * gap + 0.28)
        if u <= 0: xx += widths[i]; continue
        sc = lerp(1.35, 1.0, e_out(u)); al = int(255 * clamp(u * 2.5))
        tw, th = int(widths[i] * 1.5) + 40, int(font.size * 1.6)
        lay = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        c = acc if (acc and i == len(words) - 1) else col
        dl.text((20, 10), w_, font=font, fill=(0, 0, 0, int(al * 0.7)))
        sh = lay.filter(ImageFilter.GaussianBlur(10)); dl2 = ImageDraw.Draw(lay := Image.new("RGBA", (tw, th), (0, 0, 0, 0)))
        dl2.text((20, 10), w_, font=font, fill=c + (al,))
        comb = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); comb.alpha_composite(sh, (4, 8)); comb.alpha_composite(lay)
        if u < 1: comb = comb.filter(ImageFilter.GaussianBlur((1 - e_out(u)) * 6))
        comb = comb.resize((int(tw * sc), int(th * sc)), Image.LANCZOS)
        fr.alpha_composite(comb, (int(xx - 20 * sc - (sc - 1) * tw / 3), int(y - 10 * sc + (1 - e_out(u)) * 26)))
        xx += widths[i]

def tag(fr, text, x, y, right=False, font=F_TAG, bg=(10, 18, 34, 170), fg=INK, a=1.0):
    if a <= 0.01: return
    tw = ImageDraw.Draw(fr).textlength(text, font=font); pad = 10; x0 = x - tw - 2 * pad if right else x
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([x0, y, x0 + tw + 2 * pad, y + font.size + 2 * pad - 2], 8, fill=bg[:3] + (int(bg[3] * a),))
    d.text((x0 + pad, y + pad - 3), text, font=font, fill=fg + (int(255 * a),)); fr.alpha_composite(lay)
ILL = "ILLUSTRATION / NOT TO SCALE"
def ill(fr, a=1.0): tag(fr, ILL, W - 28, 28, True, bg=(120, 52, 18, 190), a=a)
def credit(fr, s, a=1.0): tag(fr, s, 28, H - 62, a=a)
C_EO1 = "NASA EO-1 ALI · May 2, 2011 · NASA Earth Observatory"
C_MOD = "NASA Terra MODIS · J. Schmaltz, MODIS Rapid Response · NASA Earth Observatory"
C_GOES = "NOAA NESDIS · GOES-13 imagery, April 2011"

# grain + vignette (global finish)
RNG = np.random.default_rng(3)
GRAIN = [Image.fromarray((RNG.normal(128, 20, (H // 2, W // 2))).clip(0, 255).astype(np.uint8)).resize((W, H)) for _ in range(4)]
_v = Image.new("L", (W, H), 0); ImageDraw.Draw(_v).ellipse([-W * 0.12, -H * 0.18, W * 1.12, H * 1.18], fill=255)
VIG = Image.new("RGBA", (W, H), (4, 8, 18, 0)); VIG.putalpha(_v.filter(ImageFilter.GaussianBlur(170)).point(lambda v: int((255 - v) * 0.5)))
def finish(fr, t, flash=0.0):
    fr.alpha_composite(VIG)
    rgb = fr.convert("RGB")
    g = GRAIN[int(t * FPS) % 4]
    rgb = Image.blend(rgb, ImageChops.soft_light(rgb, Image.merge("RGB", (g, g, g))), 0.35)
    if flash > 0: rgb = Image.blend(rgb, Image.new("RGB", (W, H), (255, 246, 228)), clamp(flash) * 0.85)
    return rgb

def shake(t, t0, amp, dur=0.5, freq=26):
    if t < t0 or t > t0 + dur: return 0.0, 0.0
    k = (1 - (t - t0) / dur) ** 2 * amp
    return noise1((t - t0) * freq, 1) * k, noise1((t - t0) * freq, 2) * k

def offset(fr, dx, dy):
    if abs(dx) < 0.5 and abs(dy) < 0.5: return fr
    return ImageChops.offset(fr, int(dx), int(dy))

def zoom_blur(fr, amt):
    """Motion streak for whip transitions: average of progressively scaled copies (radial blur)."""
    if amt < 0.02: return fr
    acc = np.asarray(fr, dtype=np.float32); n = 5
    for i in range(1, n):
        s = 1 + amt * 0.08 * i; c = fr.resize((int(W * s), int(H * s)), Image.BILINEAR)
        c = c.crop(((c.width - W) // 2, (c.height - H) // 2, (c.width - W) // 2 + W, (c.height - H) // 2 + H))
        acc += np.asarray(c, dtype=np.float32)
    return Image.fromarray((acc / n).astype(np.uint8))

# GOES frames (pre-extracted, 1920x1080) + storm-cluster tracking over the South (brightness centroid)
M3DIR = "/home/claude/ep009/m3"; M3N = len(os.listdir(M3DIR))
def m3(ts): return Image.open(f"{M3DIR}/f{int(clamp(ts * 30000 / 1001, 0, M3N - 1)) + 1:04d}.jpg").convert("RGB")
_CEN = {}
def m3_centroid(ts):
    i = int(clamp(ts * 30000 / 1001, 0, M3N - 1)) // 6 * 6
    if i not in _CEN:
        a = np.asarray(Image.open(f"{M3DIR}/f{i + 1:04d}.jpg").convert("L").resize((480, 270)), dtype=np.float32)
        sub = a[95:205, 150:370]; m = (sub > 200).astype(np.float32)
        if m.sum() < 50: _CEN[i] = (W * 0.5, H * 0.55)
        else:
            ys, xs = np.mgrid[95:205, 150:370]; _CEN[i] = (float((xs * m).sum() / m.sum()) * 4, float((ys * m).sum() / m.sum()) * 4)
    return _CEN[i]
def m3_c_smooth(ts):
    pts = [m3_centroid(ts + d) for d in (-0.6, -0.3, 0, 0.3, 0.6)]
    return sum(p[0] for p in pts) / 5, sum(p[1] for p in pts) / 5

# M01 footprint geometry (for the push-broom acquisition scene)
FS = 1000 / M01.height
M01_SMALL = M01.resize((int(M01.width * FS), 1000), Image.LANCZOS)
_fa = np.asarray(M01_SMALL.convert("L")) > 12
ROW_C = []
for r in range(1000):
    xs = np.nonzero(_fa[r])[0]; ROW_C.append((xs[0] + xs[-1]) / 2 if len(xs) else M01_SMALL.width / 2)
M01_GHOST = ImageEnhance.Brightness(ImageEnhance.Color(M01_SMALL).enhance(0.0)).enhance(0.28)
FOOT = Image.fromarray((_fa * 255).astype(np.uint8))

# ============================== SCENES ==============================
def sc_hook(t):  # B01 + B02: 0-7 s — the scar reads instantly, then is traced end to end
    u = e_io(seg(t, 0, 7))
    cx, cy = lerp(2500, 2564, u), lerp(3985, 3940, u)                 # dolly ALONG the swath direction (motivated)
    vw = lerp(1300, 1560, e_out(seg(t, 0, 0.7))) if t < 0.7 else lerp(1560, 1640, e_io(seg(t, 0.7, 7)))
    rot = lerp(-4, -2, u)
    base = cam(M01, cx, cy, vw, rot)
    # corridor light: B01 whole swath lights at once; B02 re-trace from SW pin to NE pin
    if t < 3: m = corridor_mask(cx, cy, vw); amt = e_out(seg(t, 0.15, 0.9))
    else: m = corridor_mask(cx, cy, vw, 0, lerp(0.02, 1, e_io(seg(t, 3.5, 5.6)))); amt = 1
    lit = spotlight(base, m, dim=lerp(1, 0.58, amt), lift=lerp(1, 1.28, amt))
    fr = lit.convert("RGBA")
    p1, p2 = scr(TRACK[0], cx, cy, vw), scr(TRACK[-1], cx, cy, vw)
    # B01 arrow lands on the swath with anticipation & settle
    if t < 3.2:
        a = seg(t, 0.85, 1.25); mid = scr(tr_pt(0.38), cx, cy, vw)
        if a > 0:
            k = spring(seg(t, 0.85, 2.2) * 2.2); dx = (1 - k) * -260
            put(fr, P["arrow_orange"], mid[0] - 210 + dx, mid[1] + 120, 120, rot=-TR_ANG * 0.6 + 10, a=a * (1 - seg(t, 2.8, 3.2)))
        ring(fr, mid[0], mid[1], 40 + 120 * e_out(seg(t, 1.2, 1.8)), 0.8 * (1 - seg(t, 1.2, 1.8)))
    # B02 pins: drop -> squash -> settle, impact ring; measurement bridge unfolds between them
    for (pt, key, t0) in ((p1, "pin_red", 3.45), (p2, "pin_ochre", 5.55)):
        if t >= t0:
            f = seg(t, t0, t0 + 0.32); y = pt[1] - 260 * (1 - e_in(f))
            sq = 1 + 0.22 * math.exp(-9 * max(0, t - t0 - 0.32)) * math.sin(14 * max(0, t - t0 - 0.32)) if f >= 1 else 1
            put(fr, P[key], pt[0], y, 118, a=clamp(f * 3), anc=(0.5, 0.96), sx=sq, sy=2 - sq)
            ring(fr, pt[0], pt[1], 20 + 90 * e_out(seg(t, t0 + 0.32, t0 + 0.9)), 1 - seg(t, t0 + 0.32, t0 + 0.9))
    if t > 6.0: measure(fr, p1, p2, e_back(seg(t, 6.0, 6.6), 1.2))
    # kinetic statements synced to the voice
    if t < 3.0: text_k(fr, ["NOT", "A", "ROAD."], 120, 150, 0.12, t, acc=OCHRE)
    elif t < 7.0: text_k(fr, ["NOT", "A", "RIVER."], 120, 150, 3.2, t, acc=OCHRE)
    if t > 3.4: ill(fr, seg(t, 3.4, 3.8))
    credit(fr, C_EO1)
    flash = 0.3 * (1 - seg(t, 0, 0.12))                         # brief light-pop; frame 1 stays the clear thumbnail image
    dx, dy = shake(t, 0.0, 14, 0.35)
    fr = offset(fr, dx, dy)
    out = finish(fr, t, flash)
    if t > 6.6: out = zoom_blur(out, e_in(seg(t, 6.6, 7.0)) * 3)   # whip-out into the regional view
    return out

M2C = (2048, 1592)
def sc_modis(t):  # B03 7-12: storm-front wipe across the real MODIS pair, date counter, blink comparator
    u = seg(t, 7, 12)
    vw = lerp(4200, 2700, e_out(seg(t, 7, 7.8))) if t < 7.8 else lerp(2700, 2400, e_io(seg(t, 7.8, 12)))
    b, a = cam(M2B, 1500, 2250, vw), cam(M2A, 1500, 2250, vw)
    # front sweeps SW->NE (the direction the outbreak moved); soft painterly edge, shadow band leads it
    f = e_io(seg(t, 7.7, 9.6))
    pos = lerp(-0.45, 1.05, f) * W
    mh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mh).polygon([(-40, H + 40), (pos, H + 40), (pos + H * 0.6, -40), (-40, -40)], fill=255)
    m = mh.filter(ImageFilter.GaussianBlur(16))
    fr = Image.composite(a, b, m)
    live = 1 - seg(t, 9.4, 9.8)
    if live > 0:
        band = ImageChops.subtract(mh.filter(ImageFilter.GaussianBlur(70)), mh).point(lambda v: min(255, int(v * 2.2 * live)))
        fr = Image.composite(ImageEnhance.Brightness(fr).enhance(0.45), fr, band)          # storm shadow leads the front
        edge = ImageChops.difference(mh.filter(ImageFilter.GaussianBlur(5)), mh).point(lambda v: min(255, int(v * 3.0 * live)))
        fr = Image.composite(Image.new("RGB", (W, H), (255, 214, 140)), fr, edge)          # luminous leading edge
    # blink comparator: before/after alternate — "it wasn't there"
    show_before = 10.0 <= t < 10.25 or 10.5 <= t < 10.75
    if t >= 9.6: fr = b if show_before else a
    fr = fr.convert("RGBA")
    day = 12 + int(round(16 * f)) if t < 10 else (12 if show_before else 28)
    tag(fr, f"APR {day}, 2011", 70, 70, font=F_DATE, bg=(10, 18, 34, 190))
    tag(fr, "BEFORE  →  AFTER" if (t < 9.6 and f > 0) else ("BEFORE" if day < 28 else "AFTER"), 70, 150, bg=(120, 52, 18, 200) if day < 28 else (32, 70, 110, 200))
    credit(fr, C_MOD)
    out = finish(fr, t, 0.25 * (1 - seg(t, 7, 7.25)))
    if t < 7.25: out = zoom_blur(out, (1 - seg(t, 7, 7.25)) * 3)
    if t > 11.5:  # iris-dive toward the ground: transition into the illustrated ground-level story
        k = e_in(seg(t, 11.5, 12.0)); out = zoom_blur(out.resize((int(W * (1 + k)), int(H * (1 + k)))).crop((int(W * k / 2), int(H * k / 2), int(W * k / 2) + W, int(H * k / 2) + H)), k * 4)
    return out

SKY = None
def sky(t, storm_k):
    """Painted-looking backdrop: vertical gradient only (no invented landscape), darkens as the storm arrives."""
    top = tuple(int(lerp(a, b, storm_k)) for a, b in zip((44, 66, 98), (18, 22, 36)))
    bot = tuple(int(lerp(a, b, storm_k)) for a, b in zip((196, 150, 98), (70, 60, 58)))
    g = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(top)[None, None] * (1 - g) + np.array(bot)[None, None] * g).repeat(W, 1)
    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")

def leaves_burst(fr, t, t0, ox, oy, wind, n=18):
    if t < t0: return
    for i, lf in enumerate(LEAVES[:n]):
        dt = t - t0 - h01(i) * 0.25
        if dt <= 0 or dt > 2.4: continue
        vx = wind * (380 + 520 * h01(i + 5)); vy = -160 - 240 * h01(i + 9)
        x = ox + (h01(i + 2) - 0.5) * 260 + vx * dt; y = oy + (h01(i + 4) - 0.5) * 200 + vy * dt + 230 * dt * dt
        put(fr, lf, x, y, 34 + 24 * h01(i + 1), rot=dt * 360 * (h01(i + 3) - 0.5) * 2, a=1 - seg(dt, 1.6, 2.4), sh=0)

def dust(fr, t, t0, x, y, spread=1.0, n=14, col=(150, 118, 84)):
    if t < t0 or t > t0 + 2.2: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); dt = t - t0
    for i in range(n):
        ang = math.pi * (0.15 + 0.7 * h01(i + 20)); r = (60 + 260 * h01(i + 30)) * e_out(dt / 1.4) * spread
        cx_, cy_ = x + math.cos(ang) * r * (1 if i % 2 else -1), y - math.sin(ang) * r * 0.45
        rad = (30 + 50 * h01(i + 40)) * (0.6 + dt); al = int(110 * (1 - seg(dt, 0.4, 2.2)))
        d.ellipse([cx_ - rad, cy_ - rad * 0.7, cx_ + rad, cy_ + rad * 0.7], fill=col + (al,))
    fr.alpha_composite(lay.filter(ImageFilter.GaussianBlur(18)))

def rain(fr, t, k, wind=0.35):
    if k <= 0.02: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(int(140 * k)):
        x = (h01(i) * W * 1.4 + t * 900 * wind * (0.8 + h01(i + 3))) % (W * 1.3) - W * 0.15
        y = (h01(i + 7) * H + t * 1500 * (0.8 + 0.4 * h01(i + 11))) % (H + 80) - 40
        d.line([(x, y), (x - 40 * wind, y - 48)], fill=(200, 210, 230, int(70 * k)), width=2)
    fr.alpha_composite(lay)

def sc_ground(t):  # B04 12-18: cause -> effect diorama (illustration, full frame, no box)
    st = e_io(seg(t, 12.0, 14.3)) * (1 - 0.6 * e_io(seg(t, 16.2, 17.6)))     # storm presence
    fr = sky(t, st)
    # far layer: the painted storm advances and churns (depth blur, parallax)
    sx_ = lerp(-260, 1120, e_io(seg(t, 12.0, 17.8))); sy_ = lerp(330, 300, st)
    storm = churn(P["P02_storm"], t, 0.018)
    put(fr, storm, sx_, sy_, lerp(520, 640, st), a=0.95, sh=0, blur=2.0, tint=(150, 160, 190, 0.25 * (1 - st)))
    # light dims with the storm; lightning pulses on the gust
    lightning = 0.0
    for tl in (13.6, 14.42, 15.1):
        if tl <= t < tl + 0.12: lightning = 1 - (t - tl) / 0.12
    # land block: intact -> scarred via wipe travelling with the wind (left->right)
    by, bh = 790, 600
    wipe = e_io(seg(t, 14.45, 15.6))
    blk_i = P["P04_land_intact"]; blk_s = P["P04_land_scared"]
    put(fr, blk_i, 960, by, bh, a=1 - wipe * 0.0, sh=0.5, tint=(120, 120, 140, 0.35 * st))
    if wipe > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); put(lay, blk_s, 960, by + 6, bh * 0.98, sh=0, tint=(120, 120, 140, 0.35 * st))
        m = Image.new("L", (W, H), 0); xw = lerp(500, 1460, wipe)
        ImageDraw.Draw(m).polygon([(0, 0), (xw + 160, 0), (xw - 160, H), (0, H)], fill=255)
        lay.putalpha(ImageChops.multiply(lay.getchannel("A"), m.filter(ImageFilter.GaussianBlur(50))))
        fr.alpha_composite(lay)
    # tree actor: idle sway -> wind load (anticipation lean-back) -> violent gust -> topple; then uprooted settles
    tx, ty, th = 880, by - bh * 0.17, 380
    wind = 0.015 * math.sin(t * 2.3) + 0.03 * math.sin(t * 5.1) * st
    if t < 14.3: amt = wind - 0.05 * e_io(seg(t, 13.7, 14.3))                       # lean back into the wind (anticipation)
    else: amt = lerp(-0.05, 0.42, e_in(seg(t, 14.3, 14.62))) + 0.04 * math.sin(t * 30) * seg(t, 14.3, 14.62)
    fall = e_io(seg(t, 14.55, 14.95))
    if fall < 1:
        img, pad = bend(P["P03_tree_intact"], amt, power=2.2)
        put(fr, img, tx + pad * th / P["P03_tree_intact"].height * 0, ty, th, rot=-28 * fall, a=1 - fall, anc=(0.5, 1.0), sh=0.45,
            tint=(120, 120, 140, 0.35 * st))
    if t >= 14.62:
        k = seg(t, 14.62, 16.4); rr = lerp(-34, 0, spring(k * 1.6, 10, 5))
        up_img, _ = bend(P["P03_tree_uprooted"], 0.03 * math.exp(-4 * k) * math.sin(t * 18))
        put(fr, up_img, tx + 50, ty + 40, 360, rot=rr, a=clamp((t - 14.62) / 0.12), anc=(0.5, 1.0), sh=0.5, tint=(120, 120, 140, 0.35 * st))
    leaves_burst(fr, t, 14.4, tx, ty - th * 0.7, 1.0)
    leaves_burst(fr, t, 13.4, tx, ty - th * 0.75, 0.6, n=6)
    dust(fr, t, 14.75, tx + 40, ty + 40, 1.2)
    rain(fr, t, st * 0.9)
    dx, dy = shake(t, 14.5, 22, 0.6)
    camz = 1 + 0.06 * e_io(seg(t, 12, 14.4)) + 0.04 * e_out(seg(t, 14.5, 15.0))
    fr = fr.resize((int(W * camz), int(H * camz)), Image.BILINEAR).crop((int((W * camz - W) / 2 + dx), int((H * camz - H) / 2 + dy), int((W * camz - W) / 2 + dx) + W, int((H * camz - H) / 2 + dy) + H))
    if t > 12.6: ill(fr, seg(t, 12.6, 13.0))
    text_k(fr, ["CARVED", "BY", "A", "TORNADO"], 960, 110, 15.4, t, font=F_MID, anchor="c", acc=OCHRE, gap=0.12)
    out = finish(fr, t, lightning * 0.55 + 0.5 * (1 - seg(t, 12, 12.2)))
    if t > 17.55:  # lift-off: camera rockets up to orbit
        k = e_in(seg(t, 17.55, 18.0)); out = zoom_blur(ImageEnhance.Brightness(out).enhance(1 - 0.7 * k), k * 4)
    return out

def sc_orbit(t):  # B05 18-24: push-broom acquisition — the satellite's pass *produces* the real EO-1 strip
    fr = Image.new("RGBA", (W, H), (6, 10, 22, 255))
    # stars/space depth
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(160):
        x, y = (h01(i) * W - t * 12 * (0.3 + h01(i + 1))) % W, h01(i + 2) * H
        d.point((x, y), fill=(220, 230, 255, int(80 + 120 * h01(i + 3))))
    fr.alpha_composite(lay)
    dive = e_io(seg(t, 21.9, 24.0))
    # strip placement on screen; scan progress 0..1000 rows
    scan = e_io(seg(t, 18.6, 21.35)) * 1000
    sx0 = (W - M01_SMALL.width) / 2; sy0 = (H - 1000) / 2 + 40
    strip = M01_GHOST.copy()
    if scan > 1:
        rev = M01_SMALL.crop((0, 0, M01_SMALL.width, int(scan))); strip.paste(rev, (0, 0))
    st = strip.convert("RGBA"); st.putalpha(FOOT)
    # flash on "photographed": whole strip snaps to full fidelity
    if dive <= 0:
        fr.alpha_composite(st, (int(sx0), int(sy0)))
        r = int(clamp(scan, 0, 999)); gx = sx0 + ROW_C[r]; gy = sy0 + scan
        if 18.6 < t < 21.4:   # scanline glow across the footprint at the satellite's ground point
            gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dg = ImageDraw.Draw(gl)
            dg.rectangle([sx0, gy - 3, sx0 + M01_SMALL.width, gy + 3], fill=(255, 226, 150, 230))
            gl = gl.filter(ImageFilter.GaussianBlur(6)); fr.alpha_composite(gl)
            beam = Image.new("RGBA", (W, H), (0, 0, 0, 0)); db = ImageDraw.Draw(beam)
            db.polygon([(gx + 330, gy - 300), (gx + 360, gy - 280), (sx0 + M01_SMALL.width, gy), (sx0, gy)], fill=(255, 236, 190, 70))
            fr.alpha_composite(beam.filter(ImageFilter.GaussianBlur(16)))
        # satellite actor rides the strip axis (motivated by push-broom geometry), banking gently
        if t < 22.2:
            ent = e_out(seg(t, 18.0, 18.8)); sxp, syp = gx + 360 + (1 - ent) * 500, gy - 290 - (1 - ent) * 300
            if t > 21.35: sxp += (t - 21.35) * 900; syp -= (t - 21.35) * 300
            put(fr, P["P01_satellite"], sxp, syp, 230, rot=-8 + 4 * math.sin(t * 1.7), a=ent * (1 - seg(t, 21.8, 22.2)), sh=0.35, shoff=(0.25, 0.3))
        tag(fr, "Symbolic satellite, not the EO-1 spacecraft", W - 28, 86, True, a=seg(t, 18.6, 19.0) * (1 - seg(t, 21.8, 22.1)))
        tag(fr, "Real EO-1 image footprint", sx0 + M01_SMALL.width + 30, sy0 + 40, a=seg(t, 19.2, 19.6) * (1 - seg(t, 21.8, 22.1)))
        ill(fr, seg(t, 18.4, 18.8) * (1 - seg(t, 21.8, 22.1)))
    else:
        # dive from the whole footprint into the swath (same image, continuous camera)
        cxs, cys = (W / 2 - sx0) / FS, (H / 2 - sy0) / FS
        cx, cy = lerp(cxs, 2560, dive), lerp(cys, 3930, dive); vw = math.exp(lerp(math.log(W / FS), math.log(1500), dive))
        base = cam(M01, cx, cy, vw)
        m = corridor_mask(cx, cy, vw); k = seg(t, 23.2, 23.9)
        fr = spotlight(base, m, lerp(1, 0.5, k), lerp(1, 1.12, k)).convert("RGBA")
        fr = zoom_blur(fr.convert("RGB"), (1 - abs(dive * 2 - 1)) * 2.5).convert("RGBA")
    credit(fr, C_EO1, seg(t, 19.0, 19.5))
    flash = 0.9 * (1 - seg(t, 21.35, 21.7)) if t >= 21.35 else 0
    out = finish(fr, t, flash + 0.4 * (1 - seg(t, 18, 18.2)))
    if t > 23.7: out = zoom_blur(out, e_in(seg(t, 23.7, 24.0)) * 3)
    return out

def sc_search(t):  # B06 24-30: honest search — comparison lens sweeps the real MODIS pair, no invented tracks
    vw = lerp(4400, 3800, e_io(seg(t, 24, 30)))
    a, b = cam(M2A, *M2C, vw), cam(M2B, *M2C, vw)
    fr = ImageEnhance.Brightness(a).enhance(0.82).convert("RGBA")
    # lens path: two deliberate dwell stops, travels SW->NE with the storm direction
    keys = [(24.3, (360, 860)), (25.4, (760, 640)), (26.6, (760, 640)), (27.6, (1250, 430)), (28.8, (1250, 430)), (29.6, (1600, 300))]
    x, y = keys[0][1]
    for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
        if t0 <= t <= t1: k = e_io(seg(t, t0, t1)); x, y = lerp(p0[0], p1[0], k), lerp(p0[1], p1[1], k)
        elif t > t1: x, y = p1
    r = 210 * e_back(seg(t, 24.1, 24.6)) * (1 - e_in(seg(t, 29.4, 29.9)))
    if r > 5:
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse([x - r, y - r, x + r, y + r], fill=255)
        inner = a.copy()   # inside lens: full-brightness AFTER; blink to BEFORE at dwell stops
        blink = (25.6 <= t < 25.9) or (26.2 <= t < 26.45) or (27.9 <= t < 28.2) or (28.45 <= t < 28.7)
        if blink: inner = b
        fr.paste(inner.convert("RGBA"), (0, 0), m)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        d.ellipse([x - r - 8, y - r - 8, x + r + 8, y + r + 8], outline=(10, 14, 26, 160), width=16)
        d.ellipse([x - r, y - r, x + r, y + r], outline=OCHRE + (255,), width=6)
        fr.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1)))
        tag(fr, "APR 12" if blink else "APR 28", int(x - 46), int(y + r + 18), bg=(120, 52, 18, 210) if blink else (32, 70, 110, 210))
    text_k(fr, ["NOT", "THE", "ONLY", "LINE"], 120, 120, 24.35, t, font=F_MID, acc=OCHRE, gap=0.1)
    tag(fr, "Lens compares the same NASA frame: Apr 28 vs Apr 12. Track positions not annotated.", 28, H - 116, a=seg(t, 25, 25.5))
    credit(fr, C_MOD)
    out = finish(fr, t, 0.35 * (1 - seg(t, 24, 24.2)))
    if t > 29.65: out = zoom_blur(out, e_in(seg(t, 29.65, 30.0)) * 3)
    return out

def sc_storm(t):  # B07 30-38 + B08 38-47: living GOES storm, painted storm emerges from the tracked cluster, evidence chain
    ts = t - 30
    cxs, cys = m3_c_smooth(ts)
    z = 1 + 0.22 * e_io(seg(t, 30, 36.5)) - 0.18 * e_io(seg(t, 38, 40))      # push into the outbreak, back out for the chain
    lightning = 0.0
    for tl in (32.2, 33.9, 35.3, 36.6):
        if tl <= t < tl + 0.1: lightning = 1 - (t - tl) / 0.1
    g = m3(ts)
    fx, fy = lerp(W / 2, cxs, 0.6 * (z - 1) / 0.22 if z > 1 else 0), lerp(H / 2, cys, 0.6 * (z - 1) / 0.22 if z > 1 else 0)
    vw = W / z; g = cam(g, fx, fy, vw)
    dk = 0.3 * e_io(seg(t, 31, 33)) * (1 - e_io(seg(t, 37.3, 38.5)))
    g = ImageEnhance.Brightness(g).enhance(1 - dk + 0.35 * lightning)
    fr = g.convert("RGBA")
    pcx, pcy = scr((cxs, cys), fx, fy, vw)
    # painted storm: grows OUT of the real cluster position, churns, lightning flicker, then rolls away as the hand-off
    grow = e_back(seg(t, 31.0, 32.4), 1.1); leave = e_in(seg(t, 37.2, 38.4))
    if grow > 0 and t < 38.4:
        storm = churn(P["P02_storm"], t, 0.022)
        if lightning > 0: storm = ImageEnhance.Brightness(storm).enhance(1 + 0.6 * lightning)
        hh = 400 * grow * (1 + 0.05 * math.sin(t * 1.3))
        put(fr, storm, pcx - 160 + 900 * leave, pcy - 90 - 60 * leave, hh, a=clamp(grow * 1.5) * (1 - leave), sh=0.4, shoff=(0.05, 0.12))
        tag(fr, "Illustration, not the observed storm cell", int(pcx - 160 - 200), int(pcy - 90 + hh / 2 + 10), a=clamp(grow * 2) * (1 - leave))
    rain(fr, t, 0.5 * clamp(grow) * (1 - leave), wind=0.5)
    text_k(fr, ["APRIL", "2011"], 120, 120, 30.3, t, font=F_MID, acc=OCHRE, gap=0.14) if t < 38 else None
    # B08: satellite observes, beam locks on the real cluster; arrow lands on it; then the front rolls into MODIS
    if t >= 38:
        ent = e_out(seg(t, 38.2, 39.4)); sx, sy = lerp(-200, 360, ent) + (t - 39.4) * 40 * (t > 39.4), 190
        lock = seg(t, 40.2, 40.7)
        if lock > 0 and t < 43.4:
            beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(beam).polygon([(sx + 40, sy + 60), (sx + 70, sy + 70), (pcx + 90 * lock, pcy), (pcx - 90 * lock, pcy)], fill=(255, 236, 190, int(60 * lock)))
            fr.alpha_composite(beam.filter(ImageFilter.GaussianBlur(12)))
            ring(fr, pcx, pcy, 60 + 30 * math.sin(t * 6), 0.85 * lock)
        put(fr, P["P01_satellite"], sx, sy, 190, rot=-6 + 3 * math.sin(t * 1.5), a=ent * (1 - seg(t, 43.2, 43.6)), sh=0.3, shoff=(0.3, 0.4))
        aa = seg(t, 40.9, 41.2)
        if aa > 0 and t < 43.4:
            k = spring(seg(t, 40.9, 42.0) * 2); put(fr, P["arrow_white"], pcx - 250 - 140 * (1 - k), pcy + 70, 100, rot=12, a=aa * (1 - seg(t, 43.0, 43.4)))
            tag(fr, "STORMS · APR 27, 2011", int(pcx - 470), int(pcy + 130), a=aa * (1 - seg(t, 43.0, 43.4)))
        ill(fr, ent * (1 - seg(t, 43.2, 43.6)))
    # the storm front rolls across: behind it, the aftermath (real MODIS, Apr 28)
    roll = e_io(seg(t, 43.3, 44.9))
    if roll > 0:
        after = cam(M2A, *M2C, lerp(4200, 3900, seg(t, 43.3, 47))).convert("RGBA")
        m = Image.new("L", (W, H), 0); xw = lerp(-300, W + 300, roll)
        ImageDraw.Draw(m).polygon([(0, 0), (xw + 200, 0), (xw - 200, H), (0, H)], fill=255)
        fr.paste(after, (0, 0), m.filter(ImageFilter.GaussianBlur(40)))
        if roll < 1:
            put(fr, churn(P["P02_storm"], t, 0.03), xw + 120, H * 0.5, 820, rot=-8, a=0.95 * math.sin(math.pi * roll), sh=0.5)
        if t > 44.9:
            tag(fr, "AFTERMATH · APR 28, 2011", 70, 70, font=F_DATE, bg=(10, 18, 34, 190), a=seg(t, 44.9, 45.3))
    if t < 44.3: credit(fr, C_GOES)
    else: credit(fr, C_MOD)
    dx, dy = shake(t, 32.2, 8, 0.3)[0] + shake(t, 35.3, 10, 0.3)[0], 0
    fr = offset(fr, dx, dy)
    out = finish(fr, t, 0.3 * lightning + 0.3 * (1 - seg(t, 30, 30.2)))
    if t > 46.6: out = zoom_blur(out, e_in(seg(t, 46.6, 47.0)) * 3)
    return out

def sc_scale(t):  # B09 47-56: block emerges from the real swath, transforms, sinks back; pull back to full scale
    pull = e_io(seg(t, 53.2, 56)); cx, cy = lerp(2560, 2330, pull), lerp(3930, 3890, pull)
    vw = lerp(1500, 2300, pull); base = cam(M01, cx, cy, vw)
    m = corridor_mask(cx, cy, vw); fr = spotlight(base, m, lerp(0.55, 0.45, pull), 1.14).convert("RGBA")
    mid = scr(tr_pt(0.5), cx, cy, vw)
    rise = e_back(seg(t, 47.4, 48.5), 1.2); sink = e_in(seg(t, 52.2, 53.1))
    k = rise * (1 - sink)
    if k > 0.01:
        bx, by = lerp(mid[0], 960, k), lerp(mid[1], 640, k); bh = 560 * k
        wipe = e_io(seg(t, 49.2, 50.6))
        rock = 3 * math.sin(t * 1.2) * k
        put(fr, P["P04_land_intact"], bx, by, bh, rot=rock, a=clamp(k * 1.4), sh=0.6, shoff=(0.05, 0.10))
        if wipe > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); put(lay, P["P04_land_scared"], bx, by, bh, rot=rock, sh=0)
            mm = Image.new("L", (W, H), 0); xw = lerp(bx - bh * 0.8, bx + bh * 0.8, wipe)
            ImageDraw.Draw(mm).polygon([(0, 0), (xw + 120, 0), (xw - 120, H), (0, H)], fill=255)
            lay.putalpha(ImageChops.multiply(lay.getchannel("A"), mm.filter(ImageFilter.GaussianBlur(30))))
            fr.alpha_composite(lay)
        dust(fr, t, 49.25, bx, by - bh * 0.15, 0.9, 10)
        tag(fr, "INTACT", int(bx - bh * 0.6), int(by + bh * 0.45), a=clamp(k * 2) * (1 - wipe))
        tag(fr, "DAMAGE CORRIDOR", int(bx - bh * 0.3), int(by + bh * 0.45), a=clamp(k * 2) * wipe)
        ill(fr, clamp(k * 2))
    ring(fr, mid[0], mid[1], 30 + 160 * e_out(seg(t, 53.1, 53.8)), 1 - seg(t, 53.1, 53.8))
    # scale annotation: pins + measuring bridge spanning the real swath
    p1, p2 = scr(TRACK[0], cx, cy, vw), scr(TRACK[-1], cx, cy, vw)
    for (pt, key, t0) in ((p1, "pin_red", 53.6), (p2, "pin_ochre", 53.9)):
        if t >= t0:
            f = seg(t, t0, t0 + 0.3); put(fr, P[key], pt[0], pt[1] - 200 * (1 - e_in(f)), 96, a=clamp(f * 3), anc=(0.5, 0.96))
    u2 = e_back(seg(t, 54.2, 54.9), 1.2)
    if u2 > 0: measure(fr, p1, p2, u2, lift=50, h=95); ill(fr, clamp(u2 * 2))
    text_k(fr, ["THE", "SCALE", "OF", "DESTRUCTION"], 120, 120, 54.3, t, font=F_MID, acc=OCHRE, gap=0.12)
    credit(fr, C_EO1)
    dx, dy = shake(t, 49.25, 10, 0.4)
    fr = offset(fr, dx, dy)
    out = finish(fr, t, 0.35 * (1 - seg(t, 47, 47.2)))
    return out

def frame(t):
    if t < 7: return sc_hook(t)
    if t < 12: return sc_modis(t)
    if t < 18: return sc_ground(t)
    if t < 24: return sc_orbit(t)
    if t < 30: return sc_search(t)
    if t < 47: return sc_storm(t)
    return sc_scale(t)

def main():
    if "--frames" in sys.argv:
        for t in [float(x) for x in sys.argv[sys.argv.index("--frames") + 1].split(",")]:
            frame(t).save(f"/home/claude/ep009/v2_{t:05.2f}.jpg", quality=86)
        return
    out = sys.argv[1]; s0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0; s1 = int(sys.argv[3]) if len(sys.argv) > 3 else int(DUR * FPS)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(s0, s1):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 150 == 0: print("frame", i, flush=True)
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    main()
