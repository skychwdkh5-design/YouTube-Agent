"""Deterministic landmark coordinates for the EP002 stills (replaces by-eye callout positions).
Method (reproducible, no manual input beyond the search windows below):
  1. sea mask = pixels within a colour distance of the median colour of a sea-only reference patch;
  2. breakwater crescent / ring = non-sea pixels in an annulus around an approximate centre; the circle is fitted by least squares (Kasa) and
     re-fitted with inliers only (|dist - r| <= tol), 8 iterations; reported with the fit RMS and inlier count;
  3. small islands / patches = centroid of the largest non-sea connected component (4x down-sampled) inside a window.
All coordinates are ORIGINAL image pixels (x right, y down). No georeferencing is implied; frames of different dates are never registered to each other.
Usage: python3 landmarks.py [OUT.json]   (reads the WoC frames, palm2.jpg and the ISS photo from the EP002 visuals)"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit

def sea_mask(key, ref_box, thr):
    a = np.asarray(kit.src(key), np.float32); x, y, w, h = ref_box; ref = np.median(a[y:y + h, x:x + w].reshape(-1, 3), 0)
    return np.sqrt(((a - ref) ** 2).sum(2)) < thr, a

def circle_fit(xs, ys):
    A = np.c_[xs, ys, np.ones_like(xs)]; b = -(xs ** 2 + ys ** 2); s = np.linalg.lstsq(A, b, rcond=None)[0]
    cx, cy = -s[0] / 2, -s[1] / 2; return cx, cy, float(np.sqrt(max(cx ** 2 + cy ** 2 - s[2], 1)))

def fit_ring(land, c0, r0, tol=9, iters=8):
    h, w = land.shape; cx, cy, r = c0[0], c0[1], r0; R = int(r0 * 1.4)
    y0, x0 = max(int(cy - R), 0), max(int(cx - R), 0); sub = land[y0:int(cy + R), x0:int(cx + R)]; ys, xs = np.nonzero(sub); xs = xs + x0; ys = ys + y0
    for it in range(iters):
        d = np.hypot(xs - cx, ys - cy); band = max(tol * 2.5 - it * 2, tol); sel = np.abs(d - r) <= band
        if sel.sum() < 50: break
        cx, cy, r = circle_fit(xs[sel].astype(float), ys[sel].astype(float))
    d = np.hypot(xs - cx, ys - cy); sel = np.abs(d - r) <= tol
    return dict(center=[round(cx, 1), round(cy, 1)], radius=round(r, 1), inliers=int(sel.sum()), rms=round(float(np.sqrt(np.mean((d[sel] - r) ** 2))), 2) if sel.any() else None)

def component_centroid(land, win, scale=4, min_px=60):
    x, y, w, h = win; sub = land[y:y + h:scale, x:x + w:scale]; lab = np.zeros(sub.shape, np.int32); n = 0; sizes = {}
    H_, W_ = sub.shape
    for i in range(H_):
        for j in range(W_):
            if sub[i, j] and not lab[i, j]:
                n += 1; stack = [(i, j)]; lab[i, j] = n; cnt = 0; sx = sy = 0
                while stack:
                    a, b = stack.pop(); cnt += 1; sx += b; sy += a
                    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        p, q = a + da, b + db
                        if 0 <= p < H_ and 0 <= q < W_ and sub[p, q] and not lab[p, q]: lab[p, q] = n; stack.append((p, q))
                sizes[n] = (cnt, sx / cnt, sy / cnt)
    if not sizes: return None
    k = max(sizes, key=lambda z: sizes[z][0]); cnt, cx, cy = sizes[k]
    return dict(center=[round(x + cx * scale, 1), round(y + cy * scale, 1)], area_px=int(cnt * scale * scale)) if cnt * scale * scale >= min_px else None

def bright_component(key, win, luma_min, scale=4, min_px=2000):
    a = np.asarray(kit.src(key), np.float32); return component_centroid(a.mean(2) > luma_min, win, scale, min_px)

WOC_SEA = (0, 1250, 280, 150); WOC_THR = 38
def run():
    out = {'_method': __doc__.split('Usage')[0].strip(), 'woc': {}, 'palm2': {}, 'iss': {}}
    for key in ('2002b', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011'):
        sea, a = sea_mask(key, WOC_SEA, WOC_THR); land = ~sea
        out['woc'][key] = {'palm_jumeirah_ring': fit_ring(land, (350, 1637), 190)}
        if key == '2002b':                                   # centroid of the non-sea pixels inside the fitted ring (sand fronds), used for the B2/B5 callout
            c, r = out['woc'][key]['palm_jumeirah_ring']['center'], out['woc'][key]['palm_jumeirah_ring']['radius']; yy, xx = np.mgrid[int(c[1] - r):int(c[1] + r), int(c[0] - r):int(c[0] + r)]
            m = land[int(c[1] - r):int(c[1] + r), int(c[0] - r):int(c[0] + r)] & (np.hypot(xx - c[0], yy - c[1]) < 0.8 * r); out['woc'][key]['fronds_centroid'] = {'center': [round(float(xx[m].mean()), 1), round(float(yy[m].mean()), 1)], 'area_px': int(m.sum())}
    sea, a = sea_mask('2002a', WOC_SEA, WOC_THR); out['woc']['2002a'] = {'early_stage_patch': component_centroid(~sea, (140, 1480, 220, 160), 2, 30)}
    # palm2 (ASTER 2006 upload) and the ISS photograph: three projects each
    sea, a = sea_mask('palm2', (100, 1300, 300, 300), 40); land = ~sea
    out['palm2'] = {'palm_jumeirah_ring': fit_ring(land, (1380, 2180), 150), 'palm_jebel_ali_ring': fit_ring(land, (552, 3140), 200),
                    'the_world': component_centroid(land, (1200, 1050, 650, 600), 4, 500),
                    'deira_reclaimed_land': bright_component('palm2', (1900, 150, 700, 700), 175)}
    sea, a = sea_mask('iss', (200, 1700, 300, 300), 45); land = ~sea
    out['iss'] = {'palm_jumeirah_ring': fit_ring(land, (1840, 1290), 215), 'palm_jebel_ali_ring': fit_ring(land, (1626, 2776), 300), 'the_world': component_centroid(land, (1150, 80, 750, 850), 4, 500)}
    return out
if __name__ == '__main__':
    r = run(); p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'landmarks.json')
    json.dump(r, open(p, 'w'), indent=1); print(json.dumps({k: v for k, v in r.items() if k != '_method'}, indent=0)[:3000])
