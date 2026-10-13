#!/usr/bin/env python3
"""EP002 Dubai diagnostic visual preview (video only, no audio, not the episode).
Reads the approved local NASA stills, crops by rectangles from VISUAL_PRODUCTION_PLAN.md
and FULL_RES_VISUAL_AUDIT.md (original pixel coordinates, 16:9) and pipes frames to ffmpeg.
Usage: python3 render_diagnostic_preview.py OUT.mp4   (run from the repo root)
No registration between images is performed; every crop is a plain rectangle of one file."""
import subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None
V = "productions/dubai/visuals/"
W, H, FPS = 1920, 1080, 30
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F = {s: ImageFont.truetype(FONT, s) for s in (20, 26, 32, 40, 54)}
YEARS = ["20001111","20020202","20021016","20031104","20041106","20051024","20060918","20070304","20081117","20090205","20100208","20110425"]
woc = {d: Image.open(f"{V}_local_assets/woc/dubai_ast_{d}_cyl.jpg").convert("RGB") for d in YEARS}
palm2 = Image.open(V + "palm2.jpg").convert("RGB")
iss = Image.open(V + "iss067e003785_lrg.jpg").convert("RGB")
R_PALM = (140, 1445, 800, 450)

def ok(img, b):
    assert b[0] >= 0 and b[1] >= 0 and b[0]+b[2] <= img.size[0] and b[1]+b[3] <= img.size[1], (img.size, b)
    assert abs(b[2]*9 - b[3]*16) <= 16, b          # 16:9 within rounding
def lerp(a, b, t): return tuple(x+(y-x)*t for x, y in zip(a, b))
def ease(t): t = max(0, min(1, t)); return t*t*(3-2*t)
def crop(img, b, size=(W, H)):
    ok(img, b); x, y, w, h = b
    return img.resize(size, Image.LANCZOS, box=(x, y, x+w, y+h))
def shrink(b, f):   # centred zoom-in by factor f (<1)
    x, y, w, h = b; nw, nh = w*f, h*f
    return (x+(w-nw)/2, y+(h-nh)/2, nw, nh)
def label(im, text, sub=None, y=1000):
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rectangle([0, y-8, W, H], fill=(0, 0, 0, 150))
    d.text((40, y), text, font=F[32], fill=(255, 255, 255, 255))
    if sub: d.text((40, y+42), sub, font=F[20], fill=(210, 210, 210, 255))
    d.text((40, 20), "DIAGNOSTIC PREVIEW - NOT FINAL", font=F[20], fill=(255, 220, 0, 255))
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
def blank(): return Image.new("RGB", (W, H), (0, 0, 0))
def card(lines):
    im = blank(); d = ImageDraw.Draw(im); y = 300
    for i, (s, t) in enumerate(lines): d.text((120, y), t, font=F[s], fill=(255, 255, 255)); y += s+34
    return im

ASTER = "NASA ASTER (Terra), {y} - colours as published"
clips = []   # (duration, fn(t)->Image)

clips.append((3, lambda t: card([(54, "ORBITAL ATLAS - EP002 DUBAI"), (40, "Diagnostic visual preview (video only)"), (26, "Sources: NASA ASTER on Terra; NASA ISS astronaut photograph"), (26, "No narration. Frames are never registered to each other.")])))

# B1: 4x crop of the Feb 2002 frame with restrained callout
B1c, B1t = R_PALM, (0, 1422, 480, 270); PATCH = (230, 1558, 26)
def b1(t):
    k = ease((t-2.5)/4.5); b = lerp(B1c, B1t, k); im = crop(woc["20020202"], b)
    if t > 7.2:
        a = min(1, (t-7.2)/0.6); x = (PATCH[0]-b[0])/b[2]*W; y = (PATCH[1]-b[1])/b[3]*H; r = PATCH[2]/b[2]*W
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.ellipse([x-r, y-r, x+r, y+r], outline=(255, 220, 0, int(255*a)), width=3)
        d.text((x+r+14, y-14), "light patch in open water", font=F[26], fill=(255, 220, 0, int(255*a)))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    return label(im, ASTER.format(y=2002), "B1 test: crop up to 4x of original pixels, very soft; not a complete palm")
clips.append((10, b1))

# D1: Palm Jebel Ali then Palm Jumeirah (palm2.jpg)
JA, JU = (60, 2780, 1280, 720), (915, 1905, 960, 540)
def d1(t):
    a = crop(palm2, shrink(JA, 1-0.04*ease(t/6))); b = crop(palm2, shrink(JU, 1-0.04*ease((t-5.5)/6.5)))
    k = ease((t-5.5)/0.5)
    im = Image.blend(a, b, k) if 0 < k else a
    name = "Palm Jebel Ali" if t < 5.75 else "Palm Jumeirah"
    return label(im, f"{name} - " + ASTER.format(y=2006), "D1 test: circular breakwater visible around both palms; same image, same date")
clips.append((12, d1))

# E1: chronological World of Change crops, same pixel rectangle in every frame
tiles = [crop(woc[d], R_PALM, (480, 270)) for d in YEARS]
def e1(t):
    im = blank(); d = ImageDraw.Draw(im)
    d.text((40, 82), "World of Change - ASTER on Terra - same pixel rectangle in every frame; not geographically registered", font=F[26], fill=(255, 255, 255))
    for i, tl in enumerate(tiles):
        a = ease((t-i*0.9)/0.35)
        if a <= 0: continue
        x, y = (i % 4)*480, 135+(i//4)*270
        base = Image.new("RGB", (480, 270), (0, 0, 0)); im.paste(Image.blend(base, tl, a), (x, y))
        yr = YEARS[i][:4]
        if yr == "2002": yr += " (Feb)" if YEARS[i] == "20020202" else " (Oct)"   # two 2002 frames
        dd = ImageDraw.Draw(im); dd.text((x+11, y+9), yr, font=F[32], fill=(0, 0, 0)); dd.text((x+10, y+8), yr, font=F[32], fill=(255, 220, 0))
    return label(im, "NASA Earth Observatory - ASTER on Terra - colours as published", "2011 frame shown as year only", y=1000)
clips.append((16, e1))

# ISS: representative crop, move between the two palm islands
H3A, H3B = (1155, 820, 1600, 900), (826, 2326, 1600, 900)
def iss_clip(t):
    im = crop(iss, lerp(H3A, H3B, ease((t-1)/6)))
    return label(im, "NASA ISS astronaut photograph, 2022", "Photograph (cropped and contrast-enhanced by NASA), not satellite imagery")
clips.append((8, iss_clip))

# Variation test for E4 / E5 / H3
E5A = (1315, 910, 1280, 720)
def v_e4(t):
    b = lerp(R_PALM, (180, 1470, 640, 360), ease(t/5))
    k = ease((t-1.8)/0.8); a = crop(woc["20001111"], b); c = crop(woc["20031104"], b)
    im = Image.blend(a, c, k); yr = "2000" if k < 0.5 else "2003"
    dd = ImageDraw.Draw(im); dd.text((W-259, 61), yr, font=F[54], fill=(0, 0, 0)); dd.text((W-260, 60), yr, font=F[54], fill=(255, 220, 0))
    return label(im, "TEST E4: dissolve + push-in - NASA ASTER, 2000 to 2003 - colours as published", "dissolve only, no wipe; frames are not registered")
def v_e5a(t):
    if t < 1.6: im, txt = crop(woc["20001111"], R_PALM), ASTER.format(y=2000)
    elif t < 3.2: im, txt = crop(woc["20031104"], R_PALM), ASTER.format(y=2003)
    else: im, txt = crop(iss, H3A), "NASA ISS astronaut photograph, 2022"
    return label(im, "TEST E5 (plan): " + txt, "hard labeled cuts across instruments")
def v_split(t):
    im = blank(); im.paste(crop(iss, H3A, (960, 540)), (0, 270)); im.paste(crop(iss, E5A, (960, 540)), (960, 270))
    d = ImageDraw.Draw(im); d.text((40, 220), "H3 framing (wide)", font=F[26], fill=(255, 220, 0)); d.text((1000, 220), "E5 alternative (mid)", font=F[26], fill=(255, 220, 0))
    return label(im, "TEST: H3 vs E5 framing - NASA ISS astronaut photograph, 2022", "same file, two crops")
def variation(t):
    if t < 5: return v_e4(t)
    if t < 10: return v_e5a(t-5)
    return v_split(t-10)
clips.append((14, variation))

clips.append((3, lambda t: card([(40, "Credits"), (26, "NASA Earth Observatory - ASTER on NASA's Terra satellite (World of Change; Palm Islands, Dubai)"), (26, "NASA ISS Crew Earth Observations - astronaut photograph ISS067-E-3785"), (26, "Diagnostic preview only; no narration, no registration, no scale.")])))

out = sys.argv[1]
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
n = 0
for dur, fn in clips:
    for i in range(int(dur*FPS)):
        ff.stdin.write(fn(i/FPS).tobytes()); n += 1
ff.stdin.close(); ff.wait()
print("frames", n, "rc", ff.returncode)
