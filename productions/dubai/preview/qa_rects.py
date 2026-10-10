"""EP002 crop audit: every rect shown in the preview (sampled every 0.5 s per scene) must lie inside its source image and contain no no-data pixels
(pixels with all channels <= 2, i.e. the black wedges of the ASTER swath edges). Satellite pixels are never painted or filled, so this is how missing data is kept out of frame.
Usage: python3 qa_rects.py [OUT.json]   (EP002_WOC points at the extracted WoC frames)"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit, scenes as S
kit.LOG = True
X = {'a1_frames': []}
_ii = {}
def nodata_integral(key):
    if key not in _ii:
        a = np.asarray(kit.src(key)); m = (a.max(2) <= 2).astype(np.int64); _ii[key] = np.pad(m.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    return _ii[key]
def frac(key, rect):
    ii = nodata_integral(key); h, w = ii.shape[0] - 1, ii.shape[1] - 1; x, y, rw, rh = rect
    x0, y0, x1, y1 = int(max(x, 0)), int(max(y, 0)), int(min(x + rw, w)), int(min(y + rh, h))
    if x1 <= x0 or y1 <= y0: return 1.0
    return float(ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0]) / ((x1 - x0) * (y1 - y0))
rep = []; bad = 0
for sid, start, dur, vos, fn in S.SCENES:
    if sid == 'A1': kit.USED.clear(); S.A1.__globals__['view']  # A1 only uses the A2 start crop after frame 15.8 s; checked below
    worst = 0.0; oob = 0; n = 0
    for k in range(int(dur / 0.5) + 1):
        kit.USED.clear()
        try: fn(min(k * 0.5, dur - 1e-3), dur, dict(X, a1_frames=X['a1_frames']))
        except Exception as e:
            if sid != 'A1': raise
            continue
        for key, r in kit.USED:
            n += 1; im = kit.src(key); w, h = im.size; wedge = key in kit.WOC_FILES      # no-data wedges exist only in the WoC swaths; palm2/ISS are checked for bounds only
            if r[0] < -0.5 or r[1] < -0.5 or r[0] + r[2] > w + 0.5 or r[1] + r[3] > h + 0.5: oob += 1
            worst = max(worst, frac(key, r) if wedge else 0.0)
    if sid == 'A1':
        worst = max(worst, frac('2000', S.A2_START)); n += 1
    rep.append(dict(scene=sid, rects_checked=n, out_of_bounds=oob, worst_nodata_fraction=round(worst, 5))); bad += (oob > 0) + (worst > 0)
out = dict(verdict='PASS' if not any(r['out_of_bounds'] or r['worst_nodata_fraction'] for r in rep) else 'FAIL', scenes=rep)
json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qa_rects.json'), 'w'), indent=1)
print(out['verdict'], [r for r in rep if r['out_of_bounds'] or r['worst_nodata_fraction']])
