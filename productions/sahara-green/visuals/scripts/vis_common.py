"""EP001 visual pass 1: shared helpers (tone baseline, Toshka union mosaic, display crop)."""
import json, numpy as np
from PIL import Image
ACQ = '/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad/acq/out/'
VIS = '/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad/vis/'
# Fixed episode-wide baseline: identical constants for every frame, band and place. Nothing is derived from image statistics.
BASE = {'lo': 0.02, 'hi': 0.60, 'gamma': 1.8}
def tone(refl, valid=None, base=BASE):
    x = np.clip((np.nan_to_num(refl.astype(np.float32)) - base['lo']) / (base['hi'] - base['lo']), 0, 1) ** (1 / base['gamma'])
    out = (x * 255 + 0.5).astype(np.uint8)
    if valid is not None: out[~valid] = 0
    return out
def tone_auto(refl, valid):          # per-frame percentile stretch: the approach we do NOT use (comparison only)
    v = refl[valid]; lo = np.percentile(v, 1, axis=0); hi = np.percentile(v, 99, axis=0)
    x = np.clip((np.nan_to_num(refl) - lo) / (hi - lo), 0, 1) ** (1 / 1.6); out = (x * 255 + .5).astype(np.uint8); out[~valid] = 0; return out
def tone_pooled(refl, valid, rep):   # previous per-stack pooled stretch (review step before this pass)
    lo, hi = np.array(rep['stretch']['lo']), np.array(rep['stretch']['hi'])
    x = np.clip((np.nan_to_num(refl) - lo) / (hi - lo), 0, 1) ** (1 / 1.6); out = (x * 255 + .5).astype(np.uint8); out[~valid] = 0; return out
def union_mosaic(year):
    """Feathered W+E mosaic on the union grid (float32 reflectance RGB, validity). W path 176, E path 175, same lattice."""
    gW = json.load(open(ACQ + 'TW_report.json'))['grid']; gE = json.load(open(ACQ + 'TE_report.json'))['grid']
    cx = int(round((gE['x0'] - gW['x0']) / 30)); ry = int(round((gW['y_top'] - gE['y_top']) / 30))
    Wd = np.load(ACQ + 'TW_refl_f16.npz'); Ed = np.load(ACQ + 'TE_refl_f16.npz')
    UW = cx + gE['width']; H = max(gW['height'], ry + gE['height'])
    U = np.zeros((H, UW, 3), np.float32); WT = np.zeros((H, UW), np.float32)
    ov0, ov1 = cx, gW['width']
    wxW = np.ones(gW['width'], np.float32); wxW[ov0:] = np.linspace(1, 0, ov1 - ov0)
    wxE = np.ones(gE['width'], np.float32); wxE[:ov1 - ov0] = np.linspace(0, 1, ov1 - ov0)
    for d, wx, x0, y0 in ((Wd, wxW, 0, 0), (Ed, wxE, cx, ry)):
        a = np.nan_to_num(d[year].astype(np.float32)); v = d['valid_' + year]; h, w = v.shape
        wg = v * wx[None, :]; sl = (slice(y0, y0 + h), slice(x0, x0 + w))
        U[sl] += a * wg[..., None]; WT[sl] += wg
    valid = WT > 0; M = U / np.maximum(WT[..., None], 1e-9)
    return M, valid, {'cx': cx, 'ry': ry, 'W': gW, 'E': gE, 'union': (UW, H)}
def valid_union_any(year):
    gW = json.load(open(ACQ + 'TW_report.json'))['grid']; gE = json.load(open(ACQ + 'TE_report.json'))['grid']
    cx = int(round((gE['x0'] - gW['x0']) / 30)); ry = int(round((gW['y_top'] - gE['y_top']) / 30))
    Wd = np.load(ACQ + 'TW_refl_f16.npz'); Ed = np.load(ACQ + 'TE_refl_f16.npz')
    UW = cx + gE['width']; H = max(gW['height'], ry + gE['height']); v = np.zeros((H, UW), bool)
    v[:gW['height'], :gW['width']] |= Wd['valid_' + year]; v[ry:ry + gE['height'], cx:cx + gE['width']] |= Ed['valid_' + year]
    return v
