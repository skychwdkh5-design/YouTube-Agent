"""Cache baseline-toned frames: EO full AOI (5) and Toshka 3840x2160 display crop (4). Also tonal-comparison data."""
import sys, json, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vis_common as c
CACHE = c.VIS + 'cache/'; os.makedirs(CACHE, exist_ok=True)
TOSH_BOX = (60, 312)   # (y, x) of the 3840x2160 display crop inside the 3017x4467 union grid; valid in all 4 years with a 12 px margin
if __name__ == '__main__':
    eo = np.load(c.ACQ + 'EO_refl_f16.npz'); rep = json.load(open(c.ACQ + 'EO_report.json'))
    for k in ('1984', '2000', '2010', '2016', '2024'):
        np.save(f'{CACHE}EO_{k}_base.npy', c.tone(eo[k], eo['valid_' + k]))
    for y in ('1999', '2002', '2011', '2021'):
        M, v, g = c.union_mosaic(y); yy, xx = TOSH_BOX
        crop, cv = M[yy:yy + 2160, xx:xx + 3840], v[yy:yy + 2160, xx:xx + 3840]
        assert cv.all(), y
        np.save(f'{CACHE}TOSH_{y}_base.npy', c.tone(crop)); np.save(f'{CACHE}TOSH_{y}_refl.npy', crop.astype(np.float16))
        print(y, 'ok', flush=True)
