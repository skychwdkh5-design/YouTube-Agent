"""EP002 proof: CesiumJS descent (real GIBS imagery, real 3D camera) -> GeoFocus hand-off -> NASA ASTER 2006 still (Palm Jumeirah).
Usage: python3 build_transition.py CESIUM_FRAMES_DIR OUT_DIR [--palm2 PATH]   (frames f0000.png.. rendered by tools/cesium_proof/run_frames.js)
The hand-off is a SCALE/POSITION match chosen by eye (Palm Jumeirah at screen 0.38, 0.73), not a georegistration of the two sources.
Engine pieces used: orbitalatlas.transitions.GeoFocus and .warp, orbitalatlas.easing."""
import sys, os, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
from orbitalatlas.transitions import GeoFocus, warp
from orbitalatlas import easing as E

W, H, FPS, DUR = 1280, 720, 24, 5.0
T_CES_END = 2.3          # Cesium camera stops here (frame 55); last frame is held under the spotlight
T_GF0, T_GF = 2.0, 1.8   # GeoFocus start / duration
FOCUS = (487 / 1280, 527 / 720)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
cdir, out = sys.argv[1], sys.argv[2]
palm = sys.argv[sys.argv.index('--palm2') + 1] if '--palm2' in sys.argv else os.path.join(os.path.dirname(__file__), '../../visuals/palm2.jpg')
os.makedirs(out, exist_ok=True)
ces = sorted(glob.glob(os.path.join(cdir, 'f*.png'))); nc = len(ces)
pm = Image.open(palm).convert('RGB')
hi = pm.crop((350, 1020, 3000, 2511)).resize((1920, 1080), Image.LANCZOS)   # ASTER 2006 crop, Palm at FOCUS
chi = (FOCUS[0] * 1920, FOCUS[1] * 1080)
gf = GeoFocus(focus=FOCUS, radius=0.17, dim=0.7, a_zoom=1.2, b_zoom=1.2, split=0.45, duration=T_GF, ease='in_out_cubic')

def f(s): return ImageFont.truetype(FONT, s)
def pill(img, xy, text, a, size=17):
    if a <= 0.01: return
    o = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(o); ft = f(size); w = d.textlength(text, font=ft)
    d.rounded_rectangle([xy[0], xy[1], xy[0] + w + 22, xy[1] + size + 14], 6, fill=(8, 14, 22, int(200 * a)))
    d.text((xy[0] + 11, xy[1] + 6), text, font=ft, fill=(205, 222, 235, int(255 * a))); img.alpha_composite(o)
def spaced(img, xy, text, size, a, reveal):
    if a <= 0.01: return
    o = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(o); ft = f(size); x = xy[0]
    for i, ch in enumerate(text):
        k = E.clamp(reveal * (len(text) + 4) - i); dy = (1 - E.out_cubic(k)) * 14
        d.text((x, xy[1] + dy), ch, font=ft, fill=(255, 196, 90, int(255 * a * k))); x += d.textlength(ch, font=ft) + size * 0.28
    img.alpha_composite(o)
def ring(img, c, r, a, wd=3):
    if a <= 0.01: return
    o = Image.new('RGBA', img.size, (0, 0, 0, 0)); ImageDraw.Draw(o).ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=(255, 196, 90, int(255 * a)), width=wd); img.alpha_composite(o)

n = int(DUR * FPS)
for i in range(n):
    t = i / FPS
    a = Image.open(ces[min(i, nc - 1)]).convert('RGB').resize((W, H), Image.LANCZOS)
    kb = 1 + 0.12 * E.out_cubic(E.clamp((t - 2.0) / 3.0))                       # slow ASTER push about the Palm (<= 1.12x)
    b = warp(hi, kb, chi, chi).resize((W, H), Image.LANCZOS)
    u = (t - T_GF0) / T_GF
    fr = gf(a, b, u).convert('RGBA')
    # UI layers (labelled by evidence class)
    pill(fr, (48, H - 62), 'NASA GIBS · BLUE MARBLE + LANDSAT · 3D GLOBE VIEW (CESIUMJS)', E.clamp((t - 0.3) / 0.4) * (1 - E.clamp((t - 2.8) / 0.4)))
    pill(fr, (48, H - 62), 'ASTER / TERRA · 2006 · NASA EARTH OBSERVATORY · NOT GEOREGISTERED', E.clamp((t - 3.7) / 0.5))
    cx, cy = FOCUS[0] * W, FOCUS[1] * H
    for k in (0, 1):                                                               # ping on the Palm as the image lands
        ph = E.clamp((t - 3.65 - 0.45 * k) / 1.0)
        ring(fr, (cx, cy), 18 + 70 * ph, (1 - ph) * 0.8 * (t > 3.65))
    ring(fr, (cx, cy), 14, E.clamp((t - 3.65) / 0.3) * 0.95, 3)
    spaced(fr, (48, 44), 'PALM JUMEIRAH', 40, E.clamp((t - 3.85) / 0.3), E.clamp((t - 3.85) / 0.7))
    fr.convert('RGB').save(os.path.join(out, f'c{i:04d}.png'))
print('frames', n, 'cesium', nc)
