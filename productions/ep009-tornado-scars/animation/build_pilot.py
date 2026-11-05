#!/usr/bin/env python3
"""EP009 painted 2.5D pilot (56 s, 1920x1080, 30 fps).
Assembles ONLY supplied package assets: NASA/NOAA originals (media_original/) + painted P01-P05 (+ P05 marker slices).
Documentary imagery is never repainted; illustrations sit on separate layers and carry ILLUSTRATION / NOT TO SCALE.
Usage: python3 build_pilot.py [--frames 0,90,...]   (frames -> PNG stills for QC instead of video)
"""
import json, math, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

REPO = "/home/claude/skychwdkh5-design/youtube-agent/productions/ep009-tornado-scars"
MO = f"{REPO}/media_original"
AS = f"{REPO}/handoff/assets"
MK = f"{AS}/markers"
W, H, FPS, DUR = 1920, 1080, 30, 56.0
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F_SM = ImageFont.truetype(FONT, 22)
F_MD = ImageFont.truetype(FONT, 30)

# ---------- helpers ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_back(x):
    x = clamp(x); c = 1.6; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)

def load(p): return Image.open(p).convert("RGBA" if p.endswith(".png") else "RGB")
M01 = load(f"{MO}/nasa_tuscaloosa_EO1_20110502.jpg")
M2B = load(f"{MO}/nasa_modis_before_20110412.jpg")
M2A = load(f"{MO}/nasa_modis_after_20110428.jpg")
P = {n: load(f"{AS}/{n}.png") for n in ["P01_satellite", "P02_storm", "P03_tree_intact", "P03_tree_uprooted", "P04_land_intact", "P04_land_scared"]}
for n in ["pin_red", "pin_ochre", "arrow_white", "arrow_orange", "measure_double"]:
    P[n] = load(f"{MK}/{n}.png")
for k in list(P):  # trim transparent margins so placement is about the painted object
    bb = P[k].getchannel("A").getbbox(); P[k] = P[k].crop(bb)

# Tornado damage swath on M01 (EO-1 ALI, full-res px), read visually from the tan corridor SW->NE through Tuscaloosa.
# NOTE: the thin straight white line just north-west of it is a contrail and is NOT marked.
TRACK = [(2024, 4242), (2420, 4008), (2780, 3792), (3104, 3612)]

def view(img, cx, cy, vw, out=(W, H), bright=1.0, sat=1.0):
    """Camera on a documentary image: centre (cx,cy) in source px, vw = source px across the frame width."""
    vh = vw * out[1] / out[0]
    box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
    fr = img.transform(out, Image.EXTENT, box, Image.BILINEAR, fillcolor=(0, 0, 0))
    if sat != 1.0: fr = ImageEnhance.Color(fr).enhance(sat)
    if bright != 1.0: fr = ImageEnhance.Brightness(fr).enhance(bright)
    return fr

def to_screen(pt, cx, cy, vw):
    s = W / vw
    return (W / 2 + (pt[0] - cx) * s, H / 2 + (pt[1] - cy) * s)

def place(fr, im, x, y, h, rot=0.0, alpha=1.0, anchor=(0.5, 0.5), shadow=True, flip=False):
    """Paste painted prop with a soft drop shadow (2.5D depth). h = target height px."""
    if alpha <= 0.01 or h < 4: return
    s = h / im.height
    a = im.resize((max(1, int(im.width * s)), max(1, int(h))), Image.LANCZOS)
    if flip: a = a.transpose(Image.FLIP_LEFT_RIGHT)
    if rot: a = a.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1:
        al = a.getchannel("A").point(lambda v: int(v * alpha)); a.putalpha(al)
    px, py = int(x - a.width * anchor[0]), int(y - a.height * anchor[1])
    if shadow:
        sh = Image.new("RGBA", a.size, (8, 12, 24, 0))
        sh.putalpha(a.getchannel("A").point(lambda v: int(v * 0.55)).filter(ImageFilter.GaussianBlur(max(2, h * 0.03))))
        fr.alpha_composite(sh, (px + int(h * 0.04), py + int(h * 0.06))) if fr.mode == "RGBA" else fr.paste(sh, (px + int(h * 0.04), py + int(h * 0.06)), sh)
    fr.alpha_composite(a, (px, py)) if fr.mode == "RGBA" else fr.paste(a, (px, py), a)

def tag(fr, text, x, y, align="left", font=F_SM, bg=(10, 18, 34, 175), fg=(240, 236, 226), alpha=1.0):
    if alpha <= 0.01: return
    d0 = ImageDraw.Draw(fr)
    tw = d0.textlength(text, font=font); th = font.size
    pad = 10
    x0 = x if align == "left" else x - tw - 2 * pad
    lay = Image.new("RGBA", fr.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([x0, y, x0 + tw + 2 * pad, y + th + 2 * pad - 2], 8, fill=bg[:3] + (int(bg[3] * alpha),))
    d.text((x0 + pad, y + pad - 3), text, font=font, fill=fg + (int(255 * alpha),))
    fr.alpha_composite(lay)

ILL = "ILLUSTRATION / NOT TO SCALE"
def ill(fr, a=1.0): tag(fr, ILL, W - 28, 28, "right", bg=(120, 52, 18, 190), alpha=a)
def credit(fr, text, a=1.0): tag(fr, text, 28, H - 62, alpha=a)

def panel(fr, box, alpha=1.0):
    """Painted-paper inset card for illustrations (keeps them visually separate from documentary imagery)."""
    x0, y0, x1, y1 = box
    lay = Image.new("RGBA", fr.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([x0 + 10, y0 + 14, x1 + 10, y1 + 14], 22, fill=(0, 0, 0, int(110 * alpha)))
    lay = lay.filter(ImageFilter.GaussianBlur(10)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle(box, 22, fill=(18, 30, 52, int(232 * alpha)), outline=(214, 170, 96, int(200 * alpha)), width=3)
    fr.alpha_composite(lay)

VIG = None
def vignette(fr):
    global VIG
    if VIG is None:
        m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
        d.ellipse([-W * 0.15, -H * 0.2, W * 1.15, H * 1.2], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(160))
        VIG = Image.new("RGBA", (W, H), (4, 8, 18, 0)); VIG.putalpha(m.point(lambda v: int((255 - v) * 0.55)))
    fr.alpha_composite(VIG)

def track_cam(u):
    """Camera point along the documented damage swath, u in 0..1."""
    n = len(TRACK) - 1; f = clamp(u) * n; i = min(int(f), n - 1); r = f - i
    return (lerp(TRACK[i][0], TRACK[i + 1][0], r), lerp(TRACK[i][1], TRACK[i + 1][1], r))

M3N = len(os.listdir("/home/claude/ep009/m3"))
def m3_frame(t_src):
    i = int(clamp(t_src * 30000 / 1001, 0, M3N - 1)) + 1
    return Image.open(f"/home/claude/ep009/m3/f{i:04d}.jpg").convert("RGB")

M2_CX, M2_CY = 2048, 1592

# ---------- scenes ----------
def frame(t):
    # B01 0-3  hook: exact EO-1 corridor, fixed then 3% push; painted arrow points at the real swath
    if t < 3:
        vw = lerp(1900, 1845, ease_io(seg(t, 0.8, 3)))
        fr = view(M01, 2380, 3930, vw).convert("RGBA")
        a = ease_out(seg(t, 0.5, 1.1))
        sx, sy = to_screen(TRACK[1], 2380, 3930, vw)
        place(fr, P["arrow_orange"], sx - 330 + 60 * (1 - a), sy + 150, 120, rot=28, alpha=a)
        vignette(fr); credit(fr, "NASA EO-1 ALI · May 2, 2011 · NASA Earth Observatory"); ill(fr, a * 0.9)
        return fr
    # B02 3-7  pan along the swath; pins drop only on its documented ends; span marker hovers beside it
    if t < 7:
        u = ease_io(seg(t, 3, 7)); cx, cy = lerp(2420, 2600, u), lerp(3960, 3900, u); vw = lerp(1650, 1500, u)
        fr = view(M01, cx, cy, vw).convert("RGBA")
        p1 = to_screen(TRACK[0], cx, cy, vw); p2 = to_screen(TRACK[-1], cx, cy, vw)
        d1 = ease_back(seg(t, 3.3, 3.9)); d2 = ease_back(seg(t, 5.2, 5.8))
        place(fr, P["pin_red"], p1[0], p1[1] - 140 * (1 - d1), 120, alpha=clamp(d1 * 3), anchor=(0.5, 0.95))
        place(fr, P["pin_ochre"], p2[0], p2[1] - 140 * (1 - d2), 120, alpha=clamp(d2 * 3), anchor=(0.5, 0.95))
        m = ease_out(seg(t, 5.8, 6.5))
        if m > 0:
            mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            ang = -math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
            ln = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            h = ln * P["measure_double"].height / P["measure_double"].width * m
            place(fr, P["measure_double"], mx + 70 * math.sin(math.radians(-ang)) * 0, my - 70, h, rot=ang, alpha=m)
        vignette(fr); credit(fr, "NASA EO-1 ALI · May 2, 2011 · NASA Earth Observatory"); ill(fr)
        return fr
    # B03 7-12 locked-registration wipe, MODIS Apr 12 -> Apr 28 (same NASA EO image pair)
    if t < 12:
        vw = lerp(4096, 3900, ease_io(seg(t, 7, 12)))
        b = view(M2B, M2_CX, M2_CY, vw); a = view(M2A, M2_CX, M2_CY, vw)
        r = ease_io(seg(t, 7.6, 11.2)); xw = int(r * W)
        fr = b.copy(); fr.paste(a.crop((0, 0, xw, H)), (0, 0)); fr = fr.convert("RGBA")
        if 0 < xw < W:
            d = ImageDraw.Draw(fr); d.line([(xw, 0), (xw, H)], fill=(240, 220, 170, 230), width=4)
        tag(fr, "BEFORE · Apr 12, 2011", 28, 28, font=F_MD, alpha=1 - seg(t, 10.6, 11.2))
        tag(fr, "AFTER · Apr 28, 2011", W - 28, 28, "right", font=F_MD, alpha=seg(t, 8.0, 8.6))
        vignette(fr); credit(fr, "NASA Terra MODIS · Jeff Schmaltz, MODIS Rapid Response · NASA Earth Observatory")
        return fr
    # B04 12-18 split: painted tree breaks (left, illustration) | real pale swath (right, documentary)
    if t < 18:
        u = ease_io(seg(t, 12, 18)); cx, cy = track_cam(0.45); vw = lerp(1300, 1050, u)
        right = view(M01, cx, cy, vw, out=(W // 2, H))
        fr = Image.new("RGBA", (W, H), (14, 22, 40, 255)); fr.paste(right, (W // 2, 0))
        panel(fr, (40, 120, W // 2 - 40, H - 120))
        sway = math.sin(t * 7.0) * 6 * seg(t, 13.0, 14.6)
        fall = ease_io(seg(t, 14.5, 15.0))
        place(fr, P["P03_tree_intact"], W // 4, 830, 600, rot=sway - 14 * fall, alpha=1 - fall, anchor=(0.5, 0.97))
        up = ease_back(seg(t, 14.7, 15.4))
        place(fr, P["P03_tree_uprooted"], W // 4 + 40 * (1 - up), 840, 520, rot=-4 * (1 - up), alpha=clamp(up * 2), anchor=(0.5, 0.95))
        d = ImageDraw.Draw(fr); d.line([(W // 2, 0), (W // 2, H)], fill=(214, 170, 96, 255), width=4)
        tag(fr, ILL, 60, 140, bg=(120, 52, 18, 190))
        vignette(fr); tag(fr, "NASA EO-1 ALI · May 2, 2011", W - 28, H - 62, "right")
        return fr
    # B05 18-24 symbolic satellite pass; the real EO-1 capture "develops" as it passes overhead
    if t < 24:
        dev = ease_io(seg(t, 20.2, 21.6))
        vw = lerp(2350, 2000, ease_io(seg(t, 18, 24)))
        fr = view(M01, 2250, 3800, vw, bright=lerp(0.45, 1.0, dev), sat=lerp(0.2, 1.0, dev)).convert("RGBA")
        k = [(18, -0.2, 0.2, -7, 0), (20, 0.35, 0.25, -3, 1), (23.5, 1.1, 0.15, 4, 0)]
        if t < 20: a, b = k[0], k[1]
        else: a, b = k[1], k[2]
        r = ease_io(seg(t, a[0], b[0]))
        x, y = lerp(a[1], b[1], r) * W, lerp(a[2], b[2], r) * H
        rot = lerp(a[3], b[3], r); op = lerp(a[4], b[4], r) if t < 20 else lerp(1, 0, seg(t, 22.5, 23.5))
        if 19.4 < t < 22.2:  # soft acquisition light falling from the symbol
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            g = math.sin(math.pi * seg(t, 19.4, 22.2))
            d.polygon([(x - 30, y + 60), (x + 30, y + 60), (x + 260, H), (x - 260, H)], fill=(255, 236, 190, int(60 * g)))
            fr.alpha_composite(lay.filter(ImageFilter.GaussianBlur(30)))
        place(fr, P["P01_satellite"], x, y, 300, rot=rot, alpha=op)
        vignette(fr); credit(fr, "NASA EO-1 ALI · May 2, 2011 · NASA Earth Observatory", a=dev); ill(fr)
        tag(fr, "Symbolic satellite, not EO-1", W - 28, 86, "right", alpha=op)
        return fr
    # B06 24-30 widen out on MODIS Apr 28 (no markers: track coordinates in MODIS frame not supplied/verified)
    if t < 30:
        u = ease_io(seg(t, 24, 30)); vw = lerp(1500, 4096, u)
        cx, cy = lerp(1500, M2_CX, u), lerp(1500, M2_CY, u)
        fr = view(M2A, cx, cy, vw).convert("RGBA")
        vignette(fr); credit(fr, "NASA Terra MODIS · Apr 28, 2011 · NASA Earth Observatory")
        return fr
    # B07 30-38 real NOAA GOES-13 loop + painted storm only in an explanatory inset
    if t < 38:
        fr = m3_frame(t - 30).convert("RGBA")
        e = ease_out(seg(t, 30, 32.5)); out = seg(t, 37.0, 37.8)
        if e > 0 and out < 1:
            bx = int(lerp(W + 40, W - 640, e)); panel(fr, (bx, 260, bx + 600, 780), alpha=1 - out)
            sw = 1 + 0.06 * ease_io(seg(t, 32.5, 37.5))
            place(fr, P["P02_storm"], bx + 300, 520, 400 * sw, alpha=1 - out)
            if int(t * 10) % 13 == 0 and t > 33:  # lightning flicker
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lay).rectangle([bx, 260, bx + 600, 780], fill=(200, 190, 255, 40)); fr.alpha_composite(lay)
            tag(fr, ILL, bx + 20, 280, bg=(120, 52, 18, 190), alpha=1 - out)
        credit(fr, "NOAA NESDIS · GOES-13 imagery, April 2011")
        return fr
    # B08 38-47 GOES clouds -> MODIS damage evidence chain; symbol crosses, arrows switch on in sequence
    if t < 47:
        if t < 44.8:
            fr = m3_frame(t - 30).convert("RGBA")
        else:
            fr = view(M2A, M2_CX, M2_CY, 4096).convert("RGBA")
        if 43.8 <= t < 44.8:
            fr = Image.blend(m3_frame(t - 30), view(M2A, M2_CX, M2_CY, 4096), ease_io(seg(t, 43.8, 44.8))).convert("RGBA")
        r = ease_io(seg(t, 38, 47)); x = lerp(0.1, 1.1, r) * W
        op = min(seg(t, 38, 39.5), 1 - seg(t, 46, 47))
        place(fr, P["P01_satellite"], x, 0.2 * H, 200, rot=-3 + 6 * r, alpha=op)
        a1 = ease_out(seg(t, 40.2, 40.9)) * (1 - seg(t, 43.6, 44.2))
        place(fr, P["arrow_white"], 820, 640, 110, rot=8, alpha=a1)   # toward the storm band over the South (GOES frame)
        tag(fr, "STORMS · APR 27, 2011", 560, 700, alpha=a1)
        a2 = ease_out(seg(t, 43.2, 44.0)) * (1 - seg(t, 46, 47)); ax = lerp(300, 1500, ease_io(seg(t, 43.2, 46.0)))
        place(fr, P["arrow_orange"], ax, 900, 100, alpha=a2)            # directional hand-off, not pointing at a feature
        tag(fr, "AFTERMATH · APR 28, 2011", W // 2, 960, alpha=ease_out(seg(t, 44.8, 45.4)) * (1 - seg(t, 46.4, 47)))
        if t < 44.3: credit(fr, "NOAA NESDIS · GOES-13 imagery, April 2011")
        else: credit(fr, "NASA Terra MODIS · Apr 28, 2011 · NASA Earth Observatory")
        ill(fr, op)
        return fr
    # B09 47-56 painted land cutaway (intact vs scarred) folds away; pull back to the full real swath
    u = ease_io(seg(t, 47, 56)); cx, cy = lerp(2500, 2250, u), lerp(3930, 3880, u); vw = lerp(1600, 2350, ease_io(seg(t, 52.5, 56)))
    fr = view(M01, cx, cy, vw).convert("RGBA")
    i1 = ease_back(seg(t, 47.3, 48.3)); i2 = ease_back(seg(t, 49.0, 50.0)); fold = ease_io(seg(t, 52.3, 53.3))
    if fold < 1:
        panel(fr, (180, 560, 1740, 1000), alpha=max(i1, 0.001) * (1 - fold))
        place(fr, P["P04_land_intact"], 560, 780 + 40 * (1 - i1), 380 * (1 - 0.4 * fold), alpha=clamp(i1 * 2) * (1 - fold))
        place(fr, P["P04_land_scared"], 1360, 780 + 40 * (1 - i2), 380 * (1 - 0.4 * fold), alpha=clamp(i2 * 2) * (1 - fold))
        tag(fr, "INTACT", 500, 980, alpha=clamp(i1 * 2) * (1 - fold)); tag(fr, "DAMAGE CORRIDOR", 1270, 980, alpha=clamp(i2 * 2) * (1 - fold))
    sc = ease_out(seg(t, 53.4, 54.4))
    if sc > 0:
        p1 = to_screen(TRACK[0], cx, cy, vw); p2 = to_screen(TRACK[-1], cx, cy, vw)
        ang = -math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])); ln = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        place(fr, P["measure_double"], (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 - 50, 0.8 * ln * P["measure_double"].height / P["measure_double"].width, rot=ang, alpha=sc)
    vignette(fr); credit(fr, "NASA EO-1 ALI · May 2, 2011 · NASA Earth Observatory"); ill(fr, max(1 - fold, sc))
    return fr

def main():
    if "--frames" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--frames") + 1].split(",")]
        for t in ts: frame(t).convert("RGB").save(f"/home/claude/ep009/qc_{t:05.1f}.jpg", quality=88)
        return
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/ep009/video_noaudio.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        p.stdin.write(frame(i / FPS).convert("RGB").tobytes())
        if i % 150 == 0: print("frame", i, "/", n, flush=True)
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    main()
