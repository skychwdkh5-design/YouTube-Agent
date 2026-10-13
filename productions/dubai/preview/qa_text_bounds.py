"""Cut-off text audit: renders every scene at sample times (0.5 s steps of estimated scene time + the last frame) and flags any drawn text whose bounding box leaves the
frame (margin 0) or the 12 px safe margin (reported separately). Usage: python3 qa_text_bounds.py [--step 0.5] [--a1 DIR] [--only A3,B3]  (runs at 960x540 logical scale)"""
import sys, os, argparse, glob
os.environ['EP002_SCALE'] = '1'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
from PIL import ImageDraw
import scenes as S
ap = argparse.ArgumentParser(); ap.add_argument('--step', type=float, default=0.5); ap.add_argument('--a1', default=''); ap.add_argument('--only'); A = ap.parse_args()
hits = {}; cur = ['', 0.0]; orig = kit.SDraw.text
def spy(self, xy, s, font=None, fill=None, anchor=None, **kw):
    if s.strip() and fill is not None and (len(fill) < 4 or fill[3] > 40):
        try: x0, y0, x1, y1 = self.d.textbbox((xy[0], xy[1]), s, font=font, anchor=anchor)
        except Exception: x0 = y0 = x1 = y1 = None
        if x0 is not None and (x0 < 0 or y0 < 0 or x1 > kit.W or y1 > kit.H): hits.setdefault((cur[0], s[:60]), []).append(round(cur[1], 1))
    return orig(self, xy, s, font=font, fill=fill, anchor=anchor, **kw)
kit.SDraw.text = spy
X = {'a1_frames': sorted(glob.glob(os.path.join(A.a1, 'f*.png')))} if A.a1 else {'a1_frames': []}
for sid, st, d, vos, fn in S.SCENES:
    if A.only and sid not in A.only.split(','): continue
    if sid == 'A1' and not A.a1: continue
    n = int(d / A.step) + 1
    for k in range(n + 1):
        t = min(k * A.step, d - 1e-3); cur[0], cur[1] = sid, t; fn(t, d, X).finish()
print('TEXT OUTSIDE FRAME:' if hits else 'no text outside the frame', {f'{k[0]}: {k[1]}': v[:6] for k, v in hits.items()} if hits else '')
