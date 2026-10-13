"""Legibility audit at 540p (logical scale 1): for every visible text draw in every scene (1 s steps) records font size (px at 540p), alpha and the WCAG contrast ratio between the
text colour and the median luminance of the pixels under its bounding box (the glyphs are a minority of those pixels, so the median is the local background; pills count as background).
Flags: size < 12 px (secondary chips are allowed at 12), contrast < 3.0 for text >= 18 px or < 4.5 otherwise. Usage: python3 qa_legibility.py [--step 1.0] [--only D2,E6] [--a1 DIR] [--min-alpha 0.7]"""
import sys, os, argparse, glob
os.environ['EP002_SCALE'] = '1'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import kit, scenes as S
ap = argparse.ArgumentParser(); ap.add_argument('--step', type=float, default=1.0); ap.add_argument('--only'); ap.add_argument('--a1', default=''); ap.add_argument('--min-alpha', type=float, default=0.7); A = ap.parse_args()
rec = []; orig = kit.SDraw.text
def lum(c): c = np.asarray(c[:3], float) / 255.0; c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4); return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])
def spy(self, xy, s, font=None, fill=None, anchor=None, **kw):
    if s.strip() and fill is not None and (len(fill) < 4 or fill[3] >= 255 * A.min_alpha) and fill[:3] != (0, 0, 0):
        try: bb = self.d.textbbox((xy[0], xy[1]), s, font=font, anchor=anchor)
        except Exception: bb = None
        if bb: rec.append((s, font.size, fill, bb))
    return orig(self, xy, s, font=font, fill=fill, anchor=anchor, **kw)
kit.SDraw.text = spy
X = {'a1_frames': sorted(glob.glob(os.path.join(A.a1, 'f*.png')))} if A.a1 else {'a1_frames': []}
flag = {}; sizes = {}
for sid, st, d, vos, fn in S.SCENES:
    if A.only and sid not in A.only.split(','): continue
    if sid == 'A1' and not A.a1: continue
    for k in range(int(d / A.step) + 1):
        t = min(k * A.step, d - 1e-3); rec.clear(); im = np.asarray(fn(t, d, X).finish().convert('RGB'))
        for s, px, fill, bb in rec:
            x0, y0, x1, y1 = [int(v) for v in bb]; x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, kit.W), min(y1, kit.H)
            if x1 - x0 < 3 or y1 - y0 < 3: continue
            reg = im[y0:y1, x0:x1].reshape(-1, 3).astype(float) / 255.0; l = np.where(reg <= 0.03928, reg / 12.92, ((reg + 0.055) / 1.055) ** 2.4) @ np.array([0.2126, 0.7152, 0.0722]); bg = float(np.median(l)); tl = lum(fill)
            cr = (max(tl, bg) + 0.05) / (min(tl, bg) + 0.05); need = 3.0 if px >= 18 else 4.5
            sizes.setdefault(sid, set()).add(px)
            if px < 12 or cr < need: flag.setdefault((sid, s[:50], int(px)), []).append((round(t, 1), round(cr, 1)))
print('LEGIBILITY FLAGS (scene, text, px at 540p) -> [(t, contrast)]; small chips are 12 px by design')
for k, v in sorted(flag.items()):
    if len(k[1]) > 1: print(k, v[:4], f'({len(v)} samples)')
print('done; scenes with flags:', sorted({k[0] for k in flag}))
