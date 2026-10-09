"""EP002 transition proof V2: CesiumJS descent (real GIBS imagery, real 3D camera) -> GeoFocus hand-off -> NASA ASTER 2006 still (Palm Jumeirah).
Usage: python3 build_transition.py CESIUM_FRAMES_DIR OUT_DIR [--palm2 PATH]   (frames f0000.png.. rendered by tools/cesium_proof/run_frames.js)
The hand-off is a SCALE/POSITION match chosen by eye (Palm Jumeirah at screen 0.38, 0.73), not a georegistration of the two sources.
V3: GeoFocus replaced by a soft Palm-centred radial dissolve (no iris edge). V2 changes: Cesium side is tone/sharpness-matched to the ASTER crop (UI treatment of the render, never applied to ASTER), rack-focus on arrival,
shared film grain, final 1.5 s = slow push + drift that brings the Palm to the third, persistent soft spotlight and a leader-line label on the Palm.
Engine pieces used: orbitalatlas.transitions.GeoFocus, orbitalatlas.easing."""
import sys, os, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
from orbitalatlas.transitions import warp
from orbitalatlas import easing as E

W, H, FPS, DUR = 1280, 720, 24, 5.0
T_GF0, T_GF = 2.0, 1.8
FOCUS = (487 / 1280, 527 / 720)            # Palm at hand-off
END = (0.40, 0.52)                         # Palm at the end (third-ish, leaves room for the label on the left)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
cdir, out = sys.argv[1], sys.argv[2]
palm = sys.argv[sys.argv.index('--palm2') + 1] if '--palm2' in sys.argv else os.path.join(os.path.dirname(__file__), '../../visuals/palm2.jpg')
os.makedirs(out, exist_ok=True)
ces = sorted(glob.glob(os.path.join(cdir, 'f*.png'))); nc = len(ces)
pm = Image.open(palm).convert('RGB')
# larger ASTER window (Palm sits at (948, 913) in it) so the end drift never runs out of image; 0.7245 = 1920/2650 as in V1
S0 = 1920 / 2650
hi = pm.crop((50, 850, 3050, 2700)).resize((round(3000 * S0), round(1850 * S0)), Image.LANCZOS)
PALM_HI = ((1358 - 50) * S0, (2111 - 850) * S0)
T_SOFT0, T_SOFT = 2.2, 1.5
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_D = np.hypot(_xx - FOCUS[0] * W, _yy - FOCUS[1] * H); _FAR = float(np.hypot(max(FOCUS[0] * W, W - FOCUS[0] * W), max(FOCUS[1] * H, H - FOCUS[1] * H)))
def soft(a, b, u):
    """V3 hand-off: very soft radial dissolve centred on the Palm (feather 0.30 H, no iris edge, no dimming of the frame);
    A drifts in 1.0->1.10x toward the Palm, B settles 1.10->1.0x. Replaces the V2 GeoFocus spotlight."""
    e = E.smoother(E.clamp(u)); c = (FOCUS[0] * W, FOCUS[1] * H)
    R = E.lerp(0.02 * H, _FAR + 0.36 * H, e); v = np.clip((R - _D) / (0.30 * H), 0, 1); m = (v * v * (3 - 2 * v))[..., None]
    A = np.asarray(warp(a, E.lerp(1.0, 1.10, e), c, c), np.float32) * (1 - 0.12 * e)
    B = np.asarray(warp(b, E.lerp(1.10, 1.0, e), c, c), np.float32)
    return Image.fromarray(np.clip(A * (1 - m) + B * m, 0, 255).astype(np.uint8))
rng = np.random.default_rng(2)

def aster(s, pos):
    """ASTER window at scale s with the Palm at output fraction pos (pure similarity transform, no tilt)."""
    dx, dy = pos[0] * 1920, pos[1] * 1080
    return hi.transform((1920, 1080), Image.AFFINE, (1 / s, 0, PALM_HI[0] - dx / s, 0, 1 / s, PALM_HI[1] - dy / s), resample=Image.BICUBIC, fillcolor=(3, 8, 6))
# colour statistics of the target (ASTER start window) for tone matching of the Cesium render
ref = np.asarray(aster(1.0, FOCUS).resize((W, H), Image.LANCZOS), np.float32).reshape(-1, 3); MU, SD = ref.mean(0), ref.std(0)
def match(img, k):
    a = np.asarray(img, np.float32); m, s = a.reshape(-1, 3).mean(0), a.reshape(-1, 3).std(0) + 1e-3
    t = (a - m) / s * SD + MU; return Image.fromarray(np.clip(a * (1 - k) + t * k, 0, 255).astype(np.uint8))
def f(s): return ImageFont.truetype(FONT, s)
def pill(img, xy, text, a, size=17):
    if a <= 0.01: return
    o = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(o); ft = f(size); w = d.textlength(text, font=ft)
    d.rounded_rectangle([xy[0], xy[1], xy[0] + w + 22, xy[1] + size + 14], 6, fill=(8, 14, 22, int(200 * a)))
    d.text((xy[0] + 11, xy[1] + 6), text, font=ft, fill=(205, 222, 235, int(255 * a))); img.alpha_composite(o)
def ring(img, c, r, a, wd=3):
    if a <= 0.01: return
    o = Image.new('RGBA', img.size, (0, 0, 0, 0)); ImageDraw.Draw(o).ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=(255, 196, 90, int(255 * a)), width=wd); img.alpha_composite(o)
def label(img, c, t, t0):
    k = E.out_cubic(E.clamp((t - t0) / 0.5))
    if k <= 0.01: return
    o = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(o); ft = f(30); txt = 'PALM JUMEIRAH'
    ex, ey = 64, c[1] - 175                                                    # text block upper-left of the Palm
    wtxt = sum(d.textlength(ch, font=ft) + 8 for ch in txt)
    p0 = (ex + wtxt * 0.55, ey + 44); p1 = (c[0] - 80 * s * 0.72, c[1] - 80 * s * 0.72)               # leader: from under the text to the ring
    q = (p0[0] + (p1[0] - p0[0]) * k, p0[1] + (p1[1] - p0[1]) * k)
    d.line([p0, q], fill=(255, 196, 90, int(230 * k)), width=2)
    x = ex
    for i, ch in enumerate(txt):
        kk = E.clamp(((t - t0) / 0.6) * (len(txt) + 3) - i); d.text((x, ey + (1 - E.out_cubic(kk)) * 12), ch, font=ft, fill=(255, 196, 90, int(255 * kk))); x += d.textlength(ch, font=ft) + 8
    img.alpha_composite(o)
def spot(fr, c, a):
    """persistent soft spotlight: outside ~0.30H dims by up to 50 % (UI layer; ASTER pixels under the Palm untouched)"""
    if a <= 0.01: return fr
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); d = np.hypot(xx - c[0], yy - c[1]); r = 0.27 * H
    u = np.clip((d - r) / (0.35 * H), 0, 1); k = 1 - 0.50 * a * (u * u * (3 - 2 * u))
    return Image.fromarray(np.clip(np.asarray(fr.convert('RGB'), np.float32) * k[..., None], 0, 255).astype(np.uint8)).convert('RGBA')

for i in range(int(DUR * FPS)):
    t = i / FPS
    a = Image.open(ces[min(i, nc - 1)]).convert('RGB').resize((W, H), Image.LANCZOS)
    kt = E.smooth(E.clamp((t - 1.2) / 1.0)) * 0.65                                 # tone match ramps in during the last Cesium second
    a = match(a, kt).filter(ImageFilter.UnsharpMask(1.6, int(70 * E.smooth(E.clamp((t - 1.0) / 1.0))), 2))
    a = a.filter(ImageFilter.GaussianBlur(1.6 * E.smooth(E.clamp((t - 2.0) / 0.8))))   # A softens as the spotlight closes
    s = 1 + 0.04 * E.smooth(E.clamp((t - 2.0) / 1.8)) + 0.26 * E.smooth(E.clamp((t - 3.5) / 1.5))   # <= 1.30x overall (Palm ~22 % of frame width at the end)
    pos_k = E.smoother(E.clamp((t - 3.6) / 1.4)); pos = (FOCUS[0] + (END[0] - FOCUS[0]) * pos_k, FOCUS[1] + (END[1] - FOCUS[1]) * pos_k)
    b = aster(s, pos).resize((W, H), Image.LANCZOS)
    b = b.filter(ImageFilter.GaussianBlur(3.5 * (1 - E.smooth(E.clamp((t - 2.7) / 1.1)))))   # rack focus: B arrives soft, then sharpens
    fr = (soft(a, b, (t - T_SOFT0) / T_SOFT) if t >= T_SOFT0 else a).convert('RGBA')
    c = (pos[0] * W, pos[1] * H)
    fr = spot(fr, c, E.smooth(E.clamp((t - 3.9) / 0.7)))
    pill(fr, (48, H - 62), 'NASA GIBS · BLUE MARBLE + LANDSAT · 3D GLOBE VIEW (CESIUMJS)', E.clamp((t - 0.3) / 0.4) * (1 - E.clamp((t - 2.8) / 0.4)))
    pill(fr, (48, H - 62), 'ASTER / TERRA · 2006 · NASA EARTH OBSERVATORY · NOT GEOREGISTERED', E.clamp((t - 3.7) / 0.5))
    for k in (0, 1):
        ph = E.clamp((t - 3.65 - 0.5 * k) / 1.1); ring(fr, c, 80 * s + 70 * ph, (1 - ph) * 0.8 * (t > 3.65))
    ring(fr, c, 80 * s, E.clamp((t - 3.65) / 0.35) * 0.9, 3)                       # steady ring around the Palm crown (crown radius ~72 px at s=1)
    label(fr, c, t, 3.95)
    arr = np.asarray(fr.convert('RGB'), np.float32) + rng.normal(0, 2.2, (H, W, 1)).astype(np.float32)   # shared grain across both sources
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(os.path.join(out, f'c{i:04d}.png'))
print('frames', int(DUR * FPS), 'cesium', nc)
