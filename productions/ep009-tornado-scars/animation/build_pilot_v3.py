#!/usr/bin/env python3
"""EP009 pilot v3 — cinematic refinement on top of the v2 compositing primitives.
Same package only (NASA/NOAA originals + painted P01-P05). Motion comes from motion.py presets.
Usage:
  python3 build_pilot_v3.py full  out.mp4 [f0 f1]     # 56 s pilot (frame range optional)
  python3 build_pilot_v3.py test  out.mp4              # 20 s motion test: 12-18, 18-24, 30-38 s
  python3 build_pilot_v3.py stills t1,t2,...
"""
import math, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageChops, ImageFont
import build_pilot_v2 as v2
from motion import (EASE, ease, seg, lerp, clamp, damped, fbm, vnoise, h01, gust, split_tree, mesh_bend,
                    band_split, atmos, Cam)

W, H, FPS = 1920, 1080, 30
P, M01, M2A, M2B = v2.P, v2.M01, v2.M2A, v2.M2B
def _clean(im):
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: 0 if v < 24 else min(255, int((v - 24) * 255 / 200)))); return im
for _k in list(P): P[_k] = _clean(P[_k])
cam, scr, put, tag, ill, credit = v2.cam, v2.scr, v2.put, v2.tag, v2.ill, v2.credit
INK, OCHRE = v2.INK, v2.OCHRE
FI = "/usr/share/fonts/opentype/inter/"
F_HOOK = ImageFont.truetype(FI + "Inter-Black.otf", 112)
F_MID = ImageFont.truetype(FI + "Inter-ExtraBold.otf", 40)
F_DATE = v2.F_DATE

# ------------------------------------------------------------------ rigs built once from the supplied PNGs
TREE = split_tree(P["P03_tree_intact"], n_clusters=9, ground_frac=0.80)
UPR = split_tree(P["P03_tree_uprooted"], n_clusters=6, ground_frac=1.01, seed=2)
STORM = P["P02_storm"]
STORM_BANDS = band_split(STORM, 4, 0.22)
STORM_FAR = atmos(STORM.filter(ImageFilter.GaussianBlur(5)), 0.85)
_sa = np.asarray(STORM.convert("RGBA")).astype(np.int32)
_bolt = ((_sa[..., 2] > 170) & (_sa[..., 0] > 140) & (_sa[..., 1] < _sa[..., 2] - 25) & (_sa[..., 3] > 100))  # violet lightning strokes
BOLT = Image.fromarray((_bolt * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(14))
SCUD = _clean(STORM).crop((int(STORM.width * 0.55), int(STORM.height * 0.55), STORM.width, STORM.height))
_fm = Image.new("L", SCUD.size, 0); ImageDraw.Draw(_fm).ellipse([SCUD.width * 0.08, SCUD.height * 0.1, SCUD.width * 0.92, SCUD.height * 0.9], fill=255)
SCUD.putalpha(ImageChops.multiply(SCUD.getchannel("A"), _fm.filter(ImageFilter.GaussianBlur(SCUD.width * 0.08))))
SCUD = SCUD.filter(ImageFilter.GaussianBlur(9))
# debris cut from the supplied art (no new assets): soil clods from the scarred block, leaves from the canopy
def _bits(src, box_frac, n, size, seed, test):
    a = np.asarray(src.convert("RGBA")); out = []
    x0, y0, x1, y1 = [int(v) for v in (box_frac[0] * src.width, box_frac[1] * src.height, box_frac[2] * src.width, box_frac[3] * src.height)]
    for k in range(n * 40):
        x = int(lerp(x0, x1 - size, h01(seed + k * 3))); y = int(lerp(y0, y1 - size, h01(seed + k * 7)))
        patch = a[y:y + size, x:x + size]
        if patch[..., 3].mean() > 220 and test(patch):
            c = src.crop((x, y, x + size, y + size)); m = Image.new("L", (size, size), 0)
            ImageDraw.Draw(m).polygon([(size * (0.5 + 0.42 * math.cos(q * 1.1 + h01(k))), size * (0.5 + 0.38 * math.sin(q * 1.1 + h01(k + 1)))) for q in range(6)], fill=255)
            c.putalpha(ImageChops.multiply(c.getchannel("A"), m.filter(ImageFilter.GaussianBlur(1.5)))); out.append(c)
            if len(out) >= n: break
    return out
CLODS = _bits(P["P04_land_scared"], (0.2, 0.55, 0.8, 0.85), 14, 38, 11, lambda p: p[..., 0].mean() > p[..., 1].mean() + 8)
LEAVES = _bits(P["P03_tree_intact"], (0.05, 0.05, 0.95, 0.55), 22, 40, 23, lambda p: p[..., 1].mean() > p[..., 0].mean())

def pivot_put(fr, img, px, py, pivot, h, rot=0.0, a=1.0, sh=0.45):
    """Place img so that its pixel `pivot` (image px) lands on screen (px,py), rotating about that pivot."""
    k = h / img.height; im = img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.LANCZOS)
    pvx, pvy = pivot[0] * k, pivot[1] * k
    R = int(math.hypot(max(pvx, im.width - pvx), max(pvy, im.height - pvy))) + 2
    can = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0)); can.paste(im, (int(R - pvx), int(R - pvy)))
    if rot: can = can.rotate(rot, Image.BICUBIC, center=(R, R))
    if a < 1: can.putalpha(can.getchannel("A").point(lambda v: int(v * a)))
    if sh > 0:
        s = Image.new("RGBA", can.size, (6, 10, 22, 0)); s.putalpha(can.getchannel("A").point(lambda v: int(v * sh)).filter(ImageFilter.GaussianBlur(8)))
        fr.alpha_composite(s, (int(px - R + 10), int(py - R + 14)))
    fr.alpha_composite(can, (int(px - R), int(py - R)))

# ------------------------------------------------------------------ tree rig
GUSTS = [(12.9, 0.35, 0.6, 0.7), (13.55, 0.55, 0.5, 0.5), (14.32, 1.25, 0.18, 0.9)]
def wind_at(t): return gust(t, GUSTS, base=0.12) * (1 - 0.55 * ease("fade_soft", t, 14.0, 14.3) * (t < 14.32))  # lull before the hit

def tree_frame(t):
    """Articulated intact tree: trunk bends with load (lagged), canopy clusters respond windward->leeward."""
    Wt, Ht = TREE["size"]
    load = 0.0
    for k in range(6):  # trunk responds to the wind through a lagged, damped filter
        load += (wind_at(t - k * 0.06)) / 6
    bend_px = -50 + 300 * load          # wind from the left pushes crowns to the right
    flutter = lambda tt, s: 7 * fbm(tt * 3.1, s) + 4 * math.sin(tt * 9.0 + s)
    wood, pad = mesh_bend(TREE["wood"], lambda hh: bend_px * hh ** 1.9)
    can = Image.new("RGBA", wood.size, (0, 0, 0, 0))
    can.alpha_composite(TREE["ground"], (pad, 0)); can.alpha_composite(wood)
    for i, (lay, (cx, cy)) in enumerate(TREE["clusters"]):
        hh = 1 - cy / Ht; delay = 0.05 + 0.22 * (cx / Wt)        # gust reaches the windward side first
        ld = wind_at(t - delay); dx = (-50 + 300 * ld) * hh ** 1.9 + flutter(t - delay, i) * (0.4 + ld)
        dy = -abs(flutter(t - delay, i + 9)) * 0.4 * ld + 3 * ld * hh
        can.alpha_composite(lay, (int(pad + dx), int(dy)))
    return can, (pad + Wt * 0.5, Ht * 0.93)   # pivot = root collar

def upr_frame(t, t_land):
    """Uprooted tree: canopy clusters carry follow-through after the trunk lands (heavier, slower)."""
    Wt, Ht = UPR["size"]; can = Image.new("RGBA", (Wt + 40, Ht + 20), (0, 0, 0, 0))
    can.alpha_composite(UPR["wood"], (20, 10))
    for i, (lay, (cx, cy)) in enumerate(UPR["clusters"]):
        x = max(0.0, t - t_land - 0.03 * i); jig = 14 * math.exp(-x * 3.2) * math.sin(x * 11 + i) if t > t_land else 0
        can.alpha_composite(lay, (int(20 + jig), int(10 + abs(jig) * 0.5)))
    return can, (20 + Wt * 0.22, 10 + Ht * 0.80)   # root plate pivot

# ------------------------------------------------------------------ storm rig (multi-layer, atmospheric depth)
def storm_layer(t, h, haze=0.0, light=1.0, bolt=0.0, drift=0.0, t_ref=None):
    """Rolling storm: far hazy layer + 4 bands at different speeds with independent turbulence + internal lightning."""
    k = h / STORM.height; Ws, Hs = int(STORM.width * k), int(h); lt = t - (t_ref if t_ref is not None else t)
    can = Image.new("RGBA", (int(Ws * 1.8), int(Hs * 1.45)), (0, 0, 0, 0)); ox, oy = int(Ws * 0.4), int(Hs * 0.22)
    far = STORM_FAR.resize((int(Ws * 1.18), int(Hs * 1.18)), Image.BILINEAR)
    far.putalpha(far.getchannel("A").point(lambda v: int(v * 0.55)))
    can.alpha_composite(far, (int(ox - Ws * 0.12 + 18 * fbm(t * 0.15, 3) - drift * 0.4 * Ws), int(oy - Hs * 0.16)))
    speeds = [0.050, 0.030, 0.012, -0.010]          # anvil shears ahead, base drags
    for i, b in enumerate(STORM_BANDS):
        bb = b.resize((Ws, Hs), Image.BILINEAR)
        dx = (speeds[i] * lt + drift * (0.6 + 0.15 * i)) * Ws + 9 * fbm(t * 0.35, 20 + i) * (1 + i * 0.3)
        dy = 4 * fbm(t * 0.28, 40 + i)
        can.alpha_composite(bb, (int(ox + dx), int(oy + dy)))
    if bolt > 0:
        g = BOLT.resize((Ws, Hs), Image.BILINEAR).point(lambda v: int(min(255, v * 2.2 * bolt)))
        glow = Image.new("RGBA", (Ws, Hs), (225, 210, 255, 0)); glow.putalpha(g)
        can.alpha_composite(glow, (ox, oy))
    if haze > 0: can = atmos(can, haze)
    if light != 1.0:
        rgb = ImageEnhance.Brightness(can.convert("RGB")).enhance(light).convert("RGBA"); rgb.putalpha(can.getchannel("A")); can = rgb
    return can, (ox + Ws / 2, oy + Hs / 2)

def put_center(fr, img, x, y, a=1.0, blur=0.0):
    if a <= 0.01: return
    if blur > 0.3: img = img.filter(ImageFilter.GaussianBlur(blur))
    if a < 1: img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
    fr.alpha_composite(img, (int(x - img.width / 2), int(y - img.height / 2)))

# ------------------------------------------------------------------ shared finishing (no flashes / shakes)
def finish(fr, t, expo=0.0):
    fr.alpha_composite(v2.VIG)
    rgb = fr.convert("RGB"); g = v2.GRAIN[int(t * FPS) % 4]
    rgb = Image.blend(rgb, ImageChops.soft_light(rgb, Image.merge("RGB", (g, g, g))), 0.3)
    if expo: rgb = ImageEnhance.Brightness(rgb).enhance(1 + expo)
    return rgb

def title(fr, words, x, y, t0, t, font=F_MID, acc=OCHRE, gap=0.09, out_t=None):
    """Refined title: each word rises out of a baseline mask with text_rise easing; optional soft exit."""
    d0 = ImageDraw.Draw(fr); xx = x
    fade = 1 - ease("fade_soft", t, out_t, out_t + 0.35) if out_t else 1
    for i, w in enumerate(words):
        wpx = d0.textlength(w + " ", font=font); u = ease("text_rise", t, t0 + i * gap, t0 + i * gap + 0.55)
        if u > 0 and fade > 0:
            th = int(font.size * 1.35); lay = Image.new("RGBA", (int(wpx) + 30, th + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            c = acc if i == len(words) - 1 else INK; al = int(255 * fade)
            d.text((14, 10), w, font=font, fill=(0, 0, 0, int(al * 0.6))); sh = lay.filter(ImageFilter.GaussianBlur(8))
            lay2 = Image.new("RGBA", lay.size, (0, 0, 0, 0)); ImageDraw.Draw(lay2).text((12, 6 + (1 - u) * th), w, font=font, fill=c + (al,))
            m = Image.new("L", lay.size, 0); ImageDraw.Draw(m).rectangle([0, 0, lay.width, th + 8], fill=255)
            lay2.putalpha(ImageChops.multiply(lay2.getchannel("A"), m))
            comb = Image.new("RGBA", lay.size, (0, 0, 0, 0)); comb.alpha_composite(sh); comb.alpha_composite(lay2)
            fr.alpha_composite(comb, (int(xx - 12), int(y - 6)))
        xx += wpx

def arrow_draw(fr, img, tail, angle, length, u, a=1.0):
    """Arrow draws on from its tail along its own axis (draw_on), no bounce."""
    if u <= 0.01: return
    k = length / img.width; im = img.resize((max(2, int(img.width * k * u)), max(2, int(img.height * k))), Image.LANCZOS)
    full_w = img.width * k
    can = Image.new("RGBA", (int(full_w * 2) + 4, int(full_w * 2) + 4), (0, 0, 0, 0)); c = can.width // 2
    can.alpha_composite(im, (c, int(c - im.height / 2)))
    can = can.rotate(-angle, Image.BICUBIC, center=(c, c))
    if a < 1: can.putalpha(can.getchannel("A").point(lambda v: int(v * a)))
    s = Image.new("RGBA", can.size, (6, 10, 22, 0)); s.putalpha(can.getchannel("A").point(lambda v: int(v * 0.5)).filter(ImageFilter.GaussianBlur(6)))
    fr.alpha_composite(s, (int(tail[0] - c + 6), int(tail[1] - c + 9))); fr.alpha_composite(can, (int(tail[0] - c), int(tail[1] - c)))

def pin_drop(fr, img, pt, t, t0, h=112):
    """Map pin: light object -> accelerating fall, small elastic settle (the only overshoot in the film)."""
    if t < t0: return
    f = ease("light_drop", t, t0, t0 + 0.34); y = pt[1] - 230 * (1 - f)
    s = 1 + 0.16 * (damped(t - t0 - 0.34, 3.2, 0.32) - 1) * -1 if t > t0 + 0.34 else 1
    put(fr, img, pt[0], y, h, a=clamp(seg(t, t0, t0 + 0.12)), anc=(0.5, 0.96), sx=2 - s if s > 1 else 1, sy=s if s > 1 else 1, sh=0.45)
    if t > t0 + 0.34:
        u = ease("camera_settle", t, t0 + 0.34, t0 + 1.0)
        v2.ring(fr, pt[0], pt[1], 16 + 70 * u, 0.7 * (1 - u), w=3)

def measure_unfold(fr, p1, p2, u, lift=58, h=100):
    if u <= 0.01: return
    md = P["measure_double"]; ln = math.dist(p1, p2) * 0.9; nat = h * md.width / md.height
    put(fr, md, (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 - lift, h, rot=-math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])),
        sx=max(0.02, u) * ln / nat, a=clamp(u * 3), sh=0.4)

def focus_mix(a_img, b_img, u, blur_a=10, blur_b=10):
    """Focus-pull transition: A defocuses out while B comes into focus (no white flash, no whip)."""
    A = a_img.filter(ImageFilter.GaussianBlur(blur_a * u)) if u > 0.02 else a_img
    B = b_img.filter(ImageFilter.GaussianBlur(blur_b * (1 - u))) if u < 0.98 else b_img
    return Image.blend(A.convert("RGB"), B.convert("RGB"), EASE["fade_soft"](u)).convert("RGBA")

# ================================================================== SCENES
CAM_HOOK = Cam([(0.0, (2500, 3985, 1380), "camera_settle"), (0.9, (2512, 3975, 1560), "camera_glide"),
                (6.5, (2564, 3940, 1640), "camera_glide"), (7.4, (2564, 3940, 2600), "camera_glide")])
def sc_hook(t):  # 0-7.4 (B01-B02) — runs slightly into B03 for a scale-continuous hand-off
    cx, cy, vw = CAM_HOOK(t); base = cam(M01, cx, cy, vw)
    if t < 3.0: m = v2.corridor_mask(cx, cy, vw); amt = ease("fade_soft", t, 0.25, 1.1)
    else: m = v2.corridor_mask(cx, cy, vw, 0, lerp(0.03, 1, ease("draw_on", t, 3.5, 5.7))); amt = 1
    amt *= 1 - ease("fade_soft", t, 6.6, 7.3)
    fr = v2.spotlight(base, m, dim=lerp(1, 0.58, amt), lift=lerp(1, 1.26, amt)).convert("RGBA")
    p1, p2 = scr(v2.TRACK[0], cx, cy, vw), scr(v2.TRACK[-1], cx, cy, vw)
    if t < 3.4:   # arrow draws onto the swath, then retracts as the trace takes over
        mid = scr(v2.tr_pt(0.40), cx, cy, vw); ang = 32
        tail = (mid[0] - 330 * math.cos(math.radians(ang)), mid[1] + 330 * math.sin(math.radians(ang)) + 40)
        u = ease("draw_on", t, 0.85, 1.5) * (1 - ease("fade_soft", t, 2.8, 3.3))
        arrow_draw(fr, P["arrow_orange"], tail, ang, 300, u)
    pin_drop(fr, P["pin_red"], p1, t, 3.45); pin_drop(fr, P["pin_ochre"], p2, t, 5.55)
    measure_unfold(fr, p1, p2, ease("unfold_rigid", t, 5.95, 6.75) * (1 - ease("fade_soft", t, 6.7, 7.2)))
    if t < 3.05: title(fr, ["NOT", "A", "ROAD."], 118, 140, 0.1, t, font=F_HOOK, out_t=2.75)
    else: title(fr, ["NOT", "A", "RIVER."], 118, 140, 3.2, t, font=F_HOOK, out_t=6.5)
    if t > 3.4: ill(fr, seg(t, 3.4, 3.8) * (1 - seg(t, 6.8, 7.2)))
    credit(fr, v2.C_EO1)
    return fr

M2CEN = (1500, 2250)          # B03 regional framing (kept inside the image at vw <= 2900)
M2FULL = (2048, 1592)         # whole-frame MODIS framing (vw <= 4096: never shows outside the image)
def sc_modis(t):  # 7-12 (B03): scale-continuous arrival, noisy storm front, date counter, blink comparator
    vw = lerp(2950, 2700, ease("camera_settle", t, 6.8, 8.2)) if t < 8.2 else lerp(2700, 2350, ease("camera_glide", t, 8.2, 12.3))
    b, a = cam(M2B, *M2CEN, vw), cam(M2A, *M2CEN, vw)
    f = ease("terrain_wave", t, 7.75, 9.7)
    yy = np.linspace(0, 1, 60)
    front = [(lerp(-0.5, 1.1, f) * W + 0.62 * H * (1 - y) + 34 * fbm(y * 3 + t * 0.8, 7) , y * H) for y in yy]
    mh = Image.new("L", (W, H), 0); ImageDraw.Draw(mh).polygon([(-60, H + 40)] + [(x, y) for x, y in front][::-1] + [(-60, -40)], fill=255)
    fr = Image.composite(a, b, mh.filter(ImageFilter.GaussianBlur(14)))
    live = 1 - ease("fade_soft", t, 9.5, 9.9)
    if live > 0 and f > 0:
        band = ImageChops.subtract(mh.filter(ImageFilter.GaussianBlur(80)), mh).point(lambda v: min(255, int(v * 2.0 * live)))
        fr = Image.composite(ImageEnhance.Brightness(fr).enhance(0.5), fr, band)
        edge = ImageChops.difference(mh.filter(ImageFilter.GaussianBlur(4)), mh).point(lambda v: min(255, int(v * 2.6 * live)))
        fr = Image.composite(Image.new("RGB", (W, H), (255, 214, 150)), fr, edge)
    blink = (10.05 <= t < 10.3) or (10.6 <= t < 10.85)
    if t >= 9.7: fr = b if blink else a
    fr = fr.convert("RGBA")
    day = (12 + int(round(16 * f))) if t < 9.9 else (12 if blink else 28)
    tag(fr, f"APR {day}, 2011", 70, 70, font=F_DATE, bg=(10, 18, 34, 190), a=seg(t, 7.3, 7.7))
    tag(fr, "BEFORE → AFTER" if t < 9.9 else ("BEFORE" if blink else "AFTER"), 70, 150,
        bg=(120, 52, 18, 200) if (t < 9.9 or blink) else (32, 70, 110, 200), a=seg(t, 7.3, 7.7))
    credit(fr, v2.C_MOD)
    return fr

# ---- 12-18 (B04) benchmark: tree + storm interaction diorama
CAM_G = Cam([(11.6, (0, 40, 1.10), "camera_settle"), (12.6, (0, 0, 1.00), "camera_glide"), (14.3, (-30, -10, 1.07), "camera_glide"),
             (15.4, (60, 0, 1.05), "camera_settle"), (17.2, (40, 0, 1.03), "camera_glide"), (18.3, (40, -1150, 1.03), "camera_glide")])
def sc_ground(t):
    cx, cy, z = CAM_G(t)
    st = ease("fade_soft", t, 12.2, 14.3) * (1 - 0.55 * ease("fade_soft", t, 15.8, 17.6))   # storm presence / darkness
    fr = v2.sky(t, st)
    # sky continues upward into space for the tilt-up to orbit (stars appear as the camera rises)
    def L(par): return (-cx * par, -cy * par)            # parallax offset per depth layer
    # far storm layer (parallax 0.35): approaches from the left, haze decreases as it nears
    sx = lerp(260, 1150, ease("camera_glide", t, 12.0, 17.8)); hz = lerp(0.85, 0.15, ease("fade_soft", t, 12.0, 14.4))
    bolt = 0.0
    for tb in (13.65, 14.38, 15.15):
        if tb <= t < tb + 0.22: bolt = max(bolt, (1 - (t - tb) / 0.22) ** 1.5)
    s_img, (scx, scy) = storm_layer(t, lerp(380, 600, ease("camera_glide", t, 12.0, 14.6)), haze=hz, light=lerp(1.0, 0.85, st), bolt=bolt, drift=0.08 * seg(t, 14.3, 17), t_ref=12.0)
    ox, oy = L(0.35)
    put_center(fr, s_img, sx + ox, 300 + oy, a=ease("fade_soft", t, 11.9, 12.6))
    # ground plane (parallax 1.0): block with propagating damage, tree rig on top
    ox, oy = L(1.0); bx, by, bh = 960 + ox, 800 + oy, 600
    tint = (120, 124, 150, 0.32 * st)
    put(fr, P["P04_land_intact"], bx, by, bh, sh=0.5, tint=tint)
    dmg = ease("terrain_wave", t, 14.7, 16.0)
    if dmg > 0:   # damage propagates outward from the root plate with a ragged front (no instant swap)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); put(lay, P["P04_land_scared"], bx + 6, by + 4, bh * 0.98, sh=0, tint=tint)
        q = 4; yy, xx = np.mgrid[0:H // q, 0:W // q].astype(np.float32)
        ox0, oy0 = (bx - 80) / q, (by - bh * 0.18) / q
        d = np.hypot(xx - ox0, (yy - oy0) * 1.8); ang = np.arctan2(yy - oy0, xx - ox0)
        R = dmg * 260 / q * 2.4; rag = 9 * np.sin(ang * 5 + 1.3) + 6 * np.sin(ang * 11 + 0.4)
        mm = np.clip((R - d + rag) / 10, 0, 1)
        mi = Image.fromarray((mm * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
        lay.putalpha(ImageChops.multiply(lay.getchannel("A"), mi)); fr.alpha_composite(lay)
    root = (bx - 80, by - bh * 0.17)
    # tree actor
    t_hit, t_snap, t_land = 14.32, 14.55, 15.05
    if t < t_snap + 0.25:
        tre, pv = tree_frame(t)
        fall = ease("heavy_fall", t, t_snap, t_snap + 0.5) * 34 if t > t_snap else 0     # gravity: slow start, accelerating
        a = 1 - ease("fade_soft", t, t_snap + 0.12, t_snap + 0.25)
        pivot_put(fr, atmos(tre, 0.25 * st) if st > 0.05 else tre, root[0], root[1], pv, 400, rot=-fall, a=a)
    if t >= t_snap + 0.12:
        ur, pv = upr_frame(t, t_land)
        rot = -lerp(16, 0, ease("heavy_land", t, t_snap + 0.12, t_land + 0.35))           # continues the fall, lands without rebound
        pivot_put(fr, ur, root[0] - 40, root[1] + 26, pv, 330, rot=rot, a=ease("fade_soft", t, t_snap + 0.12, t_snap + 0.25))
    # debris: clods thrown from the root plate (delayed after snap), leaves stripped by gusts
    for i, c in enumerate(CLODS):
        t0 = t_snap + 0.08 + 0.05 * h01(i)
        if t > t0:
            dt = t - t0; vx = (120 + 300 * h01(i + 1)) * (1 if i % 3 else -0.4); vy = -(260 + 260 * h01(i + 2))
            x = root[0] + vx * dt; y = root[1] + vy * dt + 900 * dt * dt
            if y < root[1] + 40 or dt < 0.2:
                put(fr, c, x, y, 18 + 16 * h01(i + 3), rot=dt * 300 * (h01(i + 4) - 0.5), a=1 - seg(dt, 0.7, 1.0), sh=0.3)
    for i, lf in enumerate(LEAVES):
        t0 = (13.0 + 1.2 * h01(i + 50)) if i < 7 else (t_hit + 0.25 * h01(i))
        if t > t0:
            dt = t - t0; wv = 260 + 420 * h01(i + 2)
            x = root[0] - 120 + (h01(i) - 0.3) * 300 + wv * dt + 30 * math.sin(dt * 4 + i)
            y = root[1] - 330 + (h01(i + 1) - 0.5) * 160 - 120 * dt + 70 * dt * dt + 18 * math.sin(dt * 5 + i)
            put(fr, lf, x, y, 26 + 14 * h01(i + 3), rot=dt * 240 * (h01(i + 4) - 0.5), a=1 - seg(dt, 1.7, 2.5), sh=0.2)
    # dust rises late and slow, after the impact (dust is light: drifts with residual wind)
    if t > t_land - 0.1:
        dt = t - (t_land - 0.1); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for i in range(12):
            r = (40 + 50 * h01(i + 60)) * (0.5 + EASE["camera_settle"](clamp(dt / 2.0)))
            x = root[0] + 60 + (h01(i + 61) - 0.3) * 320 + 70 * dt; y = root[1] - 10 - 50 * dt * h01(i + 62)
            d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=(150, 122, 92, int(85 * (1 - seg(dt, 0.6, 2.6)))))
        fr.alpha_composite(lay.filter(ImageFilter.GaussianBlur(22)))
    # foreground rain (parallax 1.4) — density follows the storm, wind-slanted
    if st > 0.05:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); w = clamp(wind_at(t))
        for i in range(int(110 * st)):
            x = (h01(i) * W * 1.4 + t * 700 * (0.4 + w)) % (W * 1.3) - W * 0.15
            y = (h01(i + 7) * H + t * 1400 * (0.8 + 0.4 * h01(i + 11))) % (H + 80) - 40
            d.line([(x, y), (x - 34 * (0.3 + w), y - 46)], fill=(200, 210, 232, int(55 * st)), width=2)
        fr.alpha_composite(lay)
    # camera: scale about frame centre (zoom) — one coherent virtual lens
    if abs(z - 1) > 1e-3:
        fr = fr.resize((int(W * z), int(H * z)), Image.BILINEAR).crop((int((W * z - W) / 2), int((H * z - H) / 2), int((W * z - W) / 2) + W, int((H * z - H) / 2) + H))
    # tilt-up into space (17.3-18.3): stars fade in over the darkening sky
    up = ease("camera_glide", t, 17.2, 18.3)
    if up > 0:
        space = Image.new("RGBA", (W, H), (6, 10, 22, int(255 * clamp(up * 1.05)))); fr.alpha_composite(space)
        stars(fr, t, up)
    if t > 12.4: ill(fr, seg(t, 12.4, 12.8) * (1 - seg(t, 17.6, 18.0)))
    title(fr, ["CARVED", "BY", "A", "TORNADO"], 640, 96, 15.55, t, out_t=17.2)
    return fr, bolt

def stars(fr, t, a):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(170):
        x, y = (h01(i) * W - t * 6 * (0.3 + h01(i + 1))) % W, h01(i + 2) * H
        tw = 0.75 + 0.25 * math.sin(t * (1 + 2 * h01(i + 5)) + i)
        d.point((x, y), fill=(220, 230, 255, int(a * tw * (70 + 140 * h01(i + 3)))))
        if h01(i + 9) > 0.93: d.point((x + 1, y), fill=(220, 230, 255, int(a * tw * 120)))
    fr.alpha_composite(lay)

# ---- 18-24 (B05) benchmark: orbital acquisition
SX0, SY0 = (W - v2.M01_SMALL.width) / 2 + 120, (H - 1000) / 2 + 40
_FOOTROWS = np.asarray(v2.FOOT)
def foot_edges(r):
    xs = np.nonzero(_FOOTROWS[int(clamp(r, 0, 999))] > 0)[0]; return (xs[0], xs[-1]) if len(xs) else (0, v2.M01_SMALL.width)
def sat_path(t):
    """Orbital arc: the symbol travels down-track with the footprint (push-broom), near-constant speed, gentle ends."""
    u = EASE["orbit"](seg(t, 18.2, 22.6))
    r = lerp(-120, 1140, u)                                    # ground row under the satellite
    gx = SX0 + v2.ROW_C[int(clamp(r, 0, 999))] if 0 <= r < 1000 else SX0 + v2.ROW_C[0 if r < 0 else 999]
    x = gx + 330 - 40 * u; y = SY0 + r - 250 - 60 * math.sin(math.pi * u)   # arc above the ground track
    return x, y, r, u
def sc_orbit(t):
    fr = Image.new("RGBA", (W, H), (6, 10, 22, 255)); stars(fr, t, 1)
    dive = ease("camera_glide", t, 21.9, 24.2)
    scan = clamp(sat_path(t)[2] - 70, 0, 1000) if t < 22.6 else 1000
    if dive < 1:
        strip = v2.M01_GHOST.copy()
        if scan > 1:
            rev = v2.M01_SMALL.crop((0, 0, v2.M01_SMALL.width, int(scan)))
            strip.paste(rev, (0, 0))
            band = 22   # soft development band behind the line (precise, not a hard wipe)
            if scan < 1000:
                y0 = max(0, int(scan) - band); g = np.linspace(1, 0, int(scan) - y0)[:, None]
                if len(g):
                    sa = np.asarray(v2.M01_SMALL.crop((0, y0, v2.M01_SMALL.width, int(scan))), np.float32)
                    sg = np.asarray(v2.M01_GHOST.crop((0, y0, v2.M01_SMALL.width, int(scan))), np.float32)
                    mix = sa * (1 - g[..., None] * 0.85) + sg * (g[..., None] * 0.85)
                    strip.paste(Image.fromarray(mix.clip(0, 255).astype(np.uint8)), (0, y0))
        st = strip.convert("RGBA"); st.putalpha(v2.FOOT)
        expo = 0.12 * (1 - seg(t, 21.35, 21.75)) if t >= 21.35 else 0   # capture: exposure pulse on the strip only
        if expo: st = ImageEnhance.Brightness(st).enhance(1 + expo)
        sc = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sc.alpha_composite(st, (int(SX0), int(SY0)))
        # footprint guide edges draw on with the scan (derived from the real image footprint, thin ochre)
        d = ImageDraw.Draw(sc)
        if 18.6 < t < 22.9:
            for r0 in range(0, int(scan), 8):
                l, rr = foot_edges(r0); l2, rr2 = foot_edges(r0 + 8)
                al = int(150 * (1 - seg(t, 22.3, 22.9)))
                d.line([(SX0 + l, SY0 + r0), (SX0 + l2, SY0 + r0 + 8)], fill=OCHRE + (al,), width=2)
                d.line([(SX0 + rr, SY0 + r0), (SX0 + rr2, SY0 + r0 + 8)], fill=OCHRE + (al,), width=2)
        x, y, r, u = sat_path(t)
        if 0 < scan < 1000:   # scanline: 2 px core + soft glow, plus fine line-of-sight to its ends
            l, rr = foot_edges(scan); gy = SY0 + scan
            gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dg = ImageDraw.Draw(gl)
            dg.line([(SX0 + l - 6, gy), (SX0 + rr + 6, gy)], fill=(255, 226, 160, 200), width=8)
            sc.alpha_composite(gl.filter(ImageFilter.GaussianBlur(7)))
            d.line([(SX0 + l, gy), (SX0 + rr, gy)], fill=(255, 246, 220, 255), width=2)
            for ex in (SX0 + l, SX0 + rr):
                d.line([(x - 40, y + 70), (ex, gy)], fill=(255, 236, 190, 70), width=1)
        fr.alpha_composite(sc)
        if t < 23.0:   # satellite: orbital arc, slow roll and yaw (foreshortening), restrained
            roll = -6 + 5 * math.sin(t * 0.8) ; yaw = 0.93 + 0.07 * math.cos(t * 0.6)
            a = ease("fade_soft", t, 18.1, 18.7) * (1 - ease("fade_soft", t, 22.4, 23.0))
            put(fr, P["P01_satellite"], x, y, 220, rot=roll, a=a, sx=yaw, sh=0.35, shoff=(0.5, 0.6))
        tag(fr, "Symbolic satellite, not the EO-1 spacecraft", W - 28, 86, True, a=seg(t, 18.7, 19.1) * (1 - seg(t, 21.9, 22.2)))
        tag(fr, "Real EO-1 image footprint", int(SX0 + v2.M01_SMALL.width + 30), int(SY0 + 60), a=seg(t, 19.4, 19.8) * (1 - seg(t, 21.9, 22.2)))
        if 21.35 < t < 23.0: tag(fr, "CAPTURED · MAY 2, 2011", int(SX0 + v2.M01_SMALL.width + 30), int(SY0 + 110), bg=(120, 52, 18, 200), a=seg(t, 21.4, 21.7) * (1 - seg(t, 22.6, 23.0)))
        ill(fr, seg(t, 18.4, 18.8) * (1 - seg(t, 21.9, 22.2)))
    if dive > 0:   # continuous dive from the whole footprint into the swath (same image, one camera)
        cxs, cys = (W / 2 - SX0) / v2.FS, (H / 2 - SY0) / v2.FS
        cx, cy = lerp(cxs, 2560, dive), lerp(cys, 3930, dive); vw = math.exp(lerp(math.log(W / v2.FS), math.log(1560), dive))
        base = cam(M01, cx, cy, vw); k = ease("fade_soft", t, 23.2, 24.0)
        img = v2.spotlight(base, v2.corridor_mask(cx, cy, vw), lerp(1, 0.6, k), lerp(1, 1.2, k)).convert("RGBA")
        if dive < 0.25:   # first part of the dive: stars/background give way as the image fills frame
            img = Image.blend(fr.convert("RGB"), img.convert("RGB"), ease("fade_soft", dive, 0, 0.25)).convert("RGBA")
        fr = img
    credit(fr, v2.C_EO1, seg(t, 19.2, 19.6))
    return fr

# ---- 24-30 (B06): honest search lens
def sc_search(t):
    if t < 24.9:   # scale pull-back hand-off: EO-1 swath -> regional MODIS (dissolve during motion)
        k = ease("camera_glide", t, 24.0, 24.9)
        a_ = cam(M01, 2560, 3930, lerp(1560, 3200, k)); b_ = cam(M2A, *M2FULL, lerp(1800, 4000, k))
        fr = Image.blend(a_, b_, EASE["fade_soft"](k)).convert("RGBA")
        credit(fr, v2.C_EO1 if k < 0.5 else v2.C_MOD); return fr
    vw = lerp(4000, 3600, ease("camera_glide", t, 24.9, 30))
    a, b = cam(M2A, *M2FULL, vw), cam(M2B, *M2FULL, vw)
    fr = ImageEnhance.Brightness(a).enhance(0.8).convert("RGBA")
    stops = [(25.1, (420, 820), "camera_settle"), (25.9, (780, 620), "camera_glide"), (27.0, (780, 620), "camera_glide"),
             (27.9, (1240, 440), "camera_glide"), (29.0, (1240, 440), "camera_glide"), (29.8, (1580, 330), "camera_glide")]
    x, y = stops[0][1]
    for (t0, p0, _), (t1, p1, e) in zip(stops, stops[1:]):
        if t0 <= t <= t1: u = EASE[e](seg(t, t0, t1)); x, y = lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u)
        elif t > t1: x, y = p1
    r = 200 * ease("camera_settle", t, 25.0, 25.6) * (1 - ease("fade_soft", t, 29.4, 29.9))
    if r > 4:
        blink = (26.15 <= t < 26.45) or (26.7 <= t < 26.95) or (28.15 <= t < 28.45) or (28.7 <= t < 28.95)
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse([x - r, y - r, x + r, y + r], fill=255)
        fr.paste((b if blink else a).convert("RGBA"), (0, 0), m.filter(ImageFilter.GaussianBlur(1.2)))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        d.ellipse([x - r - 10, y - r - 6, x + r + 10, y + r + 14], outline=(6, 10, 22, 120), width=14)   # contact shadow
        d.ellipse([x - r, y - r, x + r, y + r], outline=OCHRE + (255,), width=5)
        d.arc([x - r + 8, y - r + 8, x + r - 8, y + r - 8], 200, 300, fill=(255, 240, 210, 110), width=3)   # glass highlight
        fr.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0.8)))
        tag(fr, "APR 12" if blink else "APR 28", int(x - 46), int(y + r + 18), bg=(120, 52, 18, 210) if blink else (32, 70, 110, 210))
    title(fr, ["NOT", "THE", "ONLY", "LINE"], 118, 110, 24.4, t, out_t=29.3)
    tag(fr, "Lens compares the same NASA frame: Apr 28 vs Apr 12. Track positions not annotated.", 28, H - 116, a=seg(t, 25.3, 25.8))
    credit(fr, v2.C_MOD)
    return fr

# ---- 30-47 (B07 benchmark + B08)
CAM_S = Cam([(29.6, (0, 0, 1.0), "camera_settle"), (30.6, (0, 0, 1.0), "camera_glide"), (36.6, (1, 1, 1.20), "camera_glide"),
             (38.0, (1, 1, 1.20), "camera_glide"), (40.2, (0, 0, 1.0), "camera_glide")])
THUNDER = [(32.1, 1.0), (33.85, 0.7), (35.25, 1.0), (36.55, 0.6)]
def sc_storm(t):
    ts = t - 30; ccx, ccy = v2.m3_c_smooth(max(0, ts)); _, _, z = CAM_S(t)
    follow = clamp((z - 1) / 0.2)
    fx, fy = lerp(W / 2, ccx, 0.55 * follow), lerp(H / 2, ccy, 0.55 * follow)
    if t < 30.4:   # arriving from the regional MODIS frame: it recedes (scale-down) as the continental GOES view dissolves in
        k = ease("fade_soft", t, 29.6, 30.4); g = v2.m3(0)
        mod = cam(M2A, *M2FULL, 4000); ms = lerp(1.0, 0.55, k)
        small = mod.resize((int(W * ms), int(H * ms)), Image.BILINEAR); bg = g.copy(); bg.paste(small, (int((W - small.width) / 2), int((H - small.height) / 2)))
        fr = Image.blend(mod, bg, EASE["fade_soft"](clamp(k * 2))) if k < 0.5 else Image.blend(bg, g, EASE["fade_soft"]((k - 0.5) * 2))
        fr = fr.convert("RGBA")
    else:
        fr = cam(v2.m3(ts), fx, fy, W / z).convert("RGBA")
    pcx, pcy = scr((ccx, ccy), fx, fy, W / z)
    bolt = 0.0
    for tb, s in THUNDER:
        if tb <= t < tb + 0.26: bolt = max(bolt, s * (1 - (t - tb) / 0.26) ** 1.6)
    # painted storm condenses out of the haze over the tracked cluster (illustration layer, labelled)
    grow = ease("camera_settle", t, 30.9, 33.2); leave = ease("fade_soft", t, 37.0, 38.4)
    if grow > 0 and t < 38.4:
        hz = lerp(0.9, 0.12, grow) + 0.6 * leave
        s_img, _ = storm_layer(t, lerp(300, 420, grow), haze=hz, light=0.95, bolt=bolt, drift=0.3 * leave, t_ref=30.9)
        put_center(fr, s_img, pcx - 150 + 260 * leave, pcy - 70 - lerp(40, 0, grow) - 50 * leave, a=clamp(grow * 1.3) * (1 - leave))
        tag(fr, "Illustration, not the observed storm cell", int(pcx - 350), int(pcy + 140), a=clamp(grow * 1.6) * (1 - leave))
        # foreground scud drifting across (fastest parallax layer), restrained
        sk = ease("fade_soft", t, 33.6, 34.4) * (1 - ease("fade_soft", t, 36.8, 37.6))
        if sk > 0:
            s2 = SCUD.resize((int(SCUD.width * 1.9), int(SCUD.height * 1.9)), Image.BILINEAR)
            put_center(fr, atmos(s2, 0.3), lerp(-200, W + 300, seg(t, 33.4, 37.8)), 840, a=0.42 * sk)
    if t < 38: title(fr, ["APRIL", "2011"], 118, 110, 30.35, t, out_t=37.6)
    # B08 evidence chain: orbital pass, acquisition lines lock onto the real cluster, arrow draws on
    if t >= 38:
        u = EASE["orbit"](seg(t, 38.1, 43.6)); sx, sy = lerp(-160, 760, u), 210 - 70 * math.sin(math.pi * u)
        a = ease("fade_soft", t, 38.1, 38.7) * (1 - ease("fade_soft", t, 43.0, 43.5))
        lock = ease("draw_on", t, 40.1, 40.8) * (1 - ease("fade_soft", t, 42.9, 43.4))
        if lock > 0:
            d = ImageDraw.Draw(fr)
            for ex in (pcx - 80, pcx + 80):
                ep = (lerp(sx + 30, ex, lock), lerp(sy + 60, pcy, lock))
                d.line([(sx + 30, sy + 60), ep], fill=(255, 236, 190, 150), width=2)
            v2.ring(fr, pcx, pcy, 80, 0.85 * lock, w=3)
        put(fr, P["P01_satellite"], sx, sy, 180, rot=-5 + 4 * math.sin(t * 0.7), sx=0.94 + 0.06 * math.cos(t * 0.5), a=a, sh=0.3, shoff=(0.4, 0.5))
        au = ease("draw_on", t, 40.85, 41.5) * (1 - ease("fade_soft", t, 42.9, 43.4))
        arrow_draw(fr, P["arrow_white"], (pcx - 470, pcy + 150), 18, 330, au)
        tag(fr, "STORMS · APR 27, 2011", int(pcx - 520), int(pcy + 190), a=au)
        ill(fr, a)
    # the front rolls across as a foreground occluder; behind it lies the aftermath (real MODIS, Apr 28)
    roll = ease("terrain_wave", t, 43.2, 45.0)
    if roll > 0:
        after = cam(M2A, *M2FULL, lerp(4000, 3600, seg(t, 43.2, 47))).convert("RGBA")
        xw = lerp(-500, W + 500, roll); m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon([(0, 0), (xw + 220, 0), (xw - 220, H), (0, H)], fill=255)
        fr.paste(after, (0, 0), m.filter(ImageFilter.GaussianBlur(60)))
        if roll < 1:
            s_img, _ = storm_layer(t, 760, haze=0.05, light=0.9, drift=roll * 0.4, t_ref=43.2)
            put_center(fr, s_img, xw + 160, H * 0.48, a=0.96 * math.sin(math.pi * clamp(roll * 1.05)))
        if t > 44.9: tag(fr, "AFTERMATH · APR 28, 2011", 70, 70, font=F_DATE, bg=(10, 18, 34, 190), a=seg(t, 44.9, 45.4))
    credit(fr, v2.C_GOES if t < 44.3 else v2.C_MOD)
    return fr, bolt

# ---- 47-56 (B09): terrain block emerges from the real swath, damage propagates, sinks back; scale reveal
CAM_E = Cam([(46.4, (2560, 3930, 3000), "camera_settle"), (47.6, (2560, 3930, 1560), "camera_glide"),
             (53.2, (2540, 3925, 1600), "camera_glide"), (56.0, (2330, 3890, 2300), "camera_glide")])
def sc_scale(t):
    cx, cy, vw = CAM_E(t); base = cam(M01, cx, cy, vw)
    if t < 47.3:   # hand-off from the MODIS aftermath: push-in dissolve
        k = ease("fade_soft", t, 46.4, 47.3)
        base = Image.blend(cam(M2A, *M2FULL, lerp(3600, 2600, k)), base, k)
    fr = v2.spotlight(base, v2.corridor_mask(cx, cy, vw), 0.58, 1.18).convert("RGBA")
    mid = scr(v2.tr_pt(0.5), cx, cy, vw)
    rise = ease("camera_settle", t, 47.5, 48.8); sink = ease("heavy_fall", t, 52.2, 53.0); k = rise * (1 - sink)
    if k > 0.01:
        bx, by = lerp(mid[0], 960, k), lerp(mid[1], 640, k); bh = 560 * k
        yaw = 2.0 * math.sin((t - 47.5) * 0.7)          # slow turn shows the block's depth while hovering
        put(fr, P["P04_land_intact"], bx, by, bh, rot=yaw, a=clamp(k * 1.5), sh=0.55, shoff=(0.05, 0.11))
        dmg = ease("terrain_wave", t, 49.2, 50.9)
        if dmg > 0:   # change propagates ALONG the swath direction with a ragged front
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); put(lay, P["P04_land_scared"], bx, by, bh, rot=yaw, sh=0)
            q = 4; yy, xx = np.mgrid[0:H // q, 0:W // q].astype(np.float32)
            along = (xx - (bx - bh * 0.7) / q) * 0.85 - (yy - by / q) * 0.5
            front = dmg * bh * 1.6 / q + 7 * np.sin(yy * 0.35 + t) + 5 * np.sin(yy * 0.9)
            mm = np.clip((front - along) / 9, 0, 1)
            lay.putalpha(ImageChops.multiply(lay.getchannel("A"), Image.fromarray((mm * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)))
            fr.alpha_composite(lay)
            for i, c in enumerate(CLODS[:9]):          # debris lifts just behind the front, delayed
                t0 = 49.4 + 1.3 * h01(i + 70)
                if t > t0:
                    dt = t - t0; x = bx - bh * 0.5 + bh * 1.0 * h01(i + 71) + 60 * dt; y = by - bh * 0.25 - 180 * dt + 420 * dt * dt
                    if dt < 0.9: put(fr, c, x, y, 16 + 10 * h01(i), rot=dt * 260, a=1 - seg(dt, 0.6, 0.9), sh=0.25)
        tag(fr, "INTACT", int(bx - bh * 0.6), int(by + bh * 0.45), a=clamp(k * 2) * (1 - dmg))
        tag(fr, "DAMAGE CORRIDOR", int(bx - bh * 0.3), int(by + bh * 0.45), a=clamp(k * 2) * dmg)
        ill(fr, clamp(k * 2))
    if t > 53.0:   # the block lands back into the real swath: settling dust ring, no flash
        u = ease("camera_settle", t, 53.0, 54.2); v2.ring(fr, mid[0], mid[1], 30 + 150 * u, 0.6 * (1 - u), w=3)
    p1, p2 = scr(v2.TRACK[0], cx, cy, vw), scr(v2.TRACK[-1], cx, cy, vw)
    pin_drop(fr, P["pin_red"], p1, t, 53.6, 92); pin_drop(fr, P["pin_ochre"], p2, t, 53.95, 92)
    mu = ease("unfold_rigid", t, 54.25, 55.0)
    if mu > 0: measure_unfold(fr, p1, p2, mu, lift=48, h=86); ill(fr, clamp(mu * 3))
    title(fr, ["THE", "SCALE", "OF", "DESTRUCTION"], 118, 110, 54.3, t)
    credit(fr, v2.C_EO1)
    return fr

def frame(t):
    bolt = 0.0
    if t < 7.4 and t < 7.0: fr = sc_hook(t)
    elif t < 7.4:   # overlap: hook pulls back while MODIS arrives (scale-continuous dissolve)
        fr = Image.blend(sc_hook(t).convert("RGB"), sc_modis(t).convert("RGB"), ease("fade_soft", t, 7.0, 7.4)).convert("RGBA")
    elif t < 11.6: fr = sc_modis(t)
    elif t < 12.4:  # focus pull: map defocuses as the ground-level diorama comes into focus
        g, _ = sc_ground(t); fr = focus_mix(sc_modis(t), g, ease("fade_soft", t, 11.6, 12.4))
    elif t < 18.3: fr, bolt = sc_ground(t)
    elif t < 24.0: fr = sc_orbit(t)
    elif t < 29.6: fr = sc_search(t)
    elif t < 46.4: fr, bolt = sc_storm(t)
    else: fr = sc_scale(t)
    if 18.0 <= t < 18.3:   # tilt-up continuity: ground scene's space blends into the orbit scene
        o = sc_orbit(t); fr = Image.blend(fr.convert("RGB"), o.convert("RGB"), ease("fade_soft", t, 18.0, 18.3)).convert("RGBA")
    return finish(fr, t, 0.06 * bolt)

TEST_RANGES = [(12.0, 18.0), (18.0, 24.0), (30.0, 38.0)]
def main():
    mode = sys.argv[1]
    if mode == "stills":
        for t in [float(x) for x in sys.argv[2].split(",")]: frame(t).save(f"/home/claude/ep009/v3_{t:05.2f}.jpg", quality=86)
        return
    out = sys.argv[2]
    if mode == "test": frames = [i / FPS for a, b in TEST_RANGES for i in range(int(a * FPS), int(b * FPS))]
    else:
        f0 = int(sys.argv[3]) if len(sys.argv) > 3 else 0; f1 = int(sys.argv[4]) if len(sys.argv) > 4 else 56 * FPS
        frames = [i / FPS for i in range(f0, f1)]
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for n, t in enumerate(frames):
        p.stdin.write(frame(t).tobytes())
        if n % 150 == 0: print("frame", n, "/", len(frames), flush=True)
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    main()
