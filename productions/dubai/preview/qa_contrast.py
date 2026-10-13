"""Text contrast audit (WCAG ratio) for Canvas.text / Canvas.kinetic runs. For every visible run (alpha >= 0.9, kinetic only once all letters are in) the scene is rendered twice, with and without
text, and the ratio is measured between the text colour and the BACKGROUND pixels (text-free render) under the run's bounding box: worst case = 75th luminance percentile for light text, 25th for dark.
Pills and chips carry their own dark backing and are not listed. Usage: python3 qa_contrast.py [--v4] [--only H1,H4] [--step 0.5] [--need 4.5] [--a1 DIR]"""
import sys, os, argparse, glob
os.environ['EP002_SCALE'] = '1'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import kit, scenes as S
ap = argparse.ArgumentParser(); ap.add_argument('--v4', action='store_true'); ap.add_argument('--only'); ap.add_argument('--step', type=float, default=0.5); ap.add_argument('--need', type=float, default=4.5); ap.add_argument('--a1', default=''); A = ap.parse_args()
rec = []; MUTE = [False]; o_text, o_kin = kit.Canvas.text, kit.Canvas.kinetic
def lum_img(a): a = a.astype(float) / 255.0; return np.where(a <= 0.03928, a / 12.92, ((a + 0.055) / 1.055) ** 2.4) @ np.array([0.2126, 0.7152, 0.0722])
def lum(c): return float(lum_img(np.array([[c[:3]]], float))[0, 0])
def box(self, xy, s, px, spacing, anchor, centered, bold=True):
    ft = kit.F(px, bold); w = sum(ft.getlength(c) + px * spacing for c in s) - px * spacing if spacing else ft.getlength(s); x, y = xy
    if centered or anchor[0] == 'm': x -= w / 2
    elif anchor[0] == 'r': x -= w
    if anchor[1] == 'a': y0 = y
    elif anchor[1] == 'm': y0 = y - px / 2
    else: y0 = y - px
    return (x, y0, x + w, y0 + px * 1.15)
def text(self, xy, s, px, fill=kit.TEXT, a=1.0, bold=True, anchor='la', spacing=0.0, shadow=True):
    if MUTE[0]: return
    if a >= 0.9 and s.strip(): rec.append((s, px, fill, box(self, xy, s, px, spacing, anchor, False, bold)))
    return o_text(self, xy, s, px, fill, a, bold, anchor, spacing, shadow)
def kinetic(self, xy, s, px, t0, t, fill=kit.AMBER, a=1.0, spacing=0.2, per=0.035):
    if MUTE[0]: return
    if a >= 0.9 and t > t0 + len(s) * per + 0.4: rec.append((s, px, fill, box(self, xy, s, px, spacing, 'la', self._center)))
    return o_kin(self, xy, s, px, t0, t, fill, a, spacing, per)
kit.Canvas.text, kit.Canvas.kinetic = text, kinetic
X = {'a1_frames': sorted(glob.glob(os.path.join(A.a1, 'f*.png')))} if A.a1 else {'a1_frames': []}
worst = {}
for sid, st, d, vos, fn in (S.SCENES_PREVIEW if A.v4 else S.SCENES):
    if A.only and sid not in A.only.split(','): continue
    if sid == 'A1' and not A.a1: continue
    for k in range(int(d / A.step) + 1):
        t = min(k * A.step, d - 1e-3)
        if sid in ('H3', 'H4', 'A1') and t < 1.0: continue                      # entry transitions re-render the previous scene (blends are not text runs)
        rec.clear(); MUTE[0] = False; fn(t, d, X).finish()
        if not rec: continue
        runs = list(rec); MUTE[0] = True; bg = np.asarray(fn(t, d, X).finish().convert('RGB')); MUTE[0] = False
        for s, px, fill, (x0, y0, x1, y1) in runs:
            x0, y0, x1, y1 = max(int(x0), 0), max(int(y0), 0), min(int(x1) + 1, kit.W), min(int(y1) + 1, kit.H)
            if x1 - x0 < 3 or y1 - y0 < 3: continue
            l = lum_img(bg[y0:y1, x0:x1]).ravel(); tl = lum(fill); bl = float(np.percentile(l, 75 if tl > np.median(l) else 25)); cr = (max(tl, bl) + 0.05) / (min(tl, bl) + 0.05)
            key = (sid, s[:48]); worst[key] = min(worst.get(key, (99, 0))[0], cr), t if cr < worst.get(key, (99, 0))[0] else worst.get(key, (99, 0))[1]
bad = {k: v for k, v in worst.items() if v[0] < A.need}
print(f'CONTRAST (need >= {A.need}): {len(worst)} runs checked, {len(bad)} below')
for k, v in sorted(bad.items()): print(' ', k, 'min ratio', round(v[0], 2), 'at t', round(v[1], 1))
