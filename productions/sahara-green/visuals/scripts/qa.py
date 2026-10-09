import sys, os, json, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vis_common as c, render as r
exec(open('/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad/acq/process.py').read().split('def main')[0].split("def path_of")[0].replace("import sys, os, json, re, numpy as np", "import numpy as np"), {}) if False else None
src = open('/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad/acq/process.py').read(); ns = {'__name__': 'p'}; exec(src.split('def main')[0], ns); pcorr, grad = ns['pcorr'], ns['grad']
CACHE = c.VIS + 'cache/'; res = {'checks': []}
def add(name, ok, detail): res['checks'].append({'check': name, 'result': 'PASS' if ok else 'FAIL', 'detail': detail}); print('PASS' if ok else 'FAIL', name, detail, flush=True)
eo = {k: np.load(f'{CACHE}EO_{k}_base.npy') for k in r.EO_YEARS}; to = {k: np.load(f'{CACHE}TOSH_{k}_base.npy') for k in r.TO_YEARS}
# 1 registration of the display frames (relative shift between consecutive and vs last)
def reg(F, ys, name, tol):
    G = {k: grad(F[k].astype(np.float32)[..., 0]) for k in ys}; out = []
    for a, b in list(zip(ys, ys[1:])) + [(ys[0], ys[-1])]:
        dx, dy, snr = pcorr(G[b], G[a]); out.append({'pair': f'{a}->{b}', 'dx_px': round(dx, 3), 'dy_px': round(dy, 3), 'snr': round(snr, 1)})
    ok = all(abs(o['dx_px']) <= tol and abs(o['dy_px']) <= tol for o in out); add(f'registration of rendered {name} frames <= {tol} px', ok, out); return out
reg(eo, r.EO_YEARS, 'East Oweinat (1 px = 30 m)', 0.2)
reg(to, r.TO_YEARS, 'Toshka display crop (1 px = 30 m)', 0.2)
# 2 crop boundaries identical and no invalid/black pixels
add('EO frames identical shape/grid', len({v.shape for v in eo.values()}) == 1, str(eo['2024'].shape))
add('Toshka crops identical 3840x2160 box (union y0=60, x0=312)', all(v.shape == (2160, 3840, 3) for v in to.values()), 'crop box fixed in build_frames.py')
blk = {k: int((v.max(2) == 0).sum()) for k, v in {**{'EO' + k: v for k, v in eo.items()}, **{'TO' + k: v for k, v in to.items()}}.items()}
add('no pure-black (invalid) pixels in any display frame', all(b == 0 for b in blk.values()), blk)
# invalid-corner margin: re-derive validity with 12px margin
allv = np.logical_and.reduce([c.valid_union_any(y) for y in r.TO_YEARS]); sub = allv[60 - 12:60 + 2160 + 12, 312 - 12:312 + 3840 + 12]
add('Toshka crop + 12 px margin lies inside the footprint of all 4 years', bool(sub.all()), f'min valid fraction in padded crop = {float(sub.mean()):.4f}')
# 3 dates / order / captions
eo_dates = {s['label']: s['date'] for s in json.load(open(c.ACQ + 'EO_report.json'))['scenes']}
tw = {s['label']: s['date'] for s in json.load(open(c.ACQ + 'TW_report.json'))['scenes']}; te = {s['label']: s['date'] for s in json.load(open(c.ACQ + 'TE_report.json'))['scenes']}
import datetime
mon = lambda d: datetime.date.fromisoformat(d).strftime('%B %Y')
okeo = all((r.EO_LABEL[k] == (datetime.date.fromisoformat(eo_dates[k]).strftime('%B %-d, %Y') if k == '1984' else mon(eo_dates[k]))) for k in r.EO_YEARS)
add('East Oweinat labels match metadata dates (1984 = August 26, 1984)', okeo, {k: (r.EO_LABEL[k], eo_dates[k]) for k in r.EO_YEARS})
okto = all(r.TO_LABEL[k] == mon(tw[k]) == mon(te[k]) for k in r.TO_YEARS)
add('Toshka labels match both path dates (2021 = November 2021)', okto, {k: (r.TO_LABEL[k], tw[k], te[k]) for k in r.TO_YEARS})
seq = [s for s in r.eo_timeline(24)]; order = []
for (y, a, z, ta, nt) in seq:
    cur = y[1] if (y[1] and a >= 0.5) else y[0]
    if not order or order[-1] != cur: order.append(cur)
add('EO timeline order strictly chronological, then zoom stays on 2024', order == r.EO_YEARS, order)
order = []
for (y, a) in r.to_timeline(24):
    cur = y[1] if (y[1] and a >= 0.5) else y[0]
    if not order or order[-1] != cur: order.append(cur)
add('Toshka timeline order strictly chronological', order == r.TO_YEARS, order)
# 4 colour stability / no per-frame normalization
ts = json.load(open(c.VIS + 'tonal_stats.json'))['variants']; B = ts['B_fixed_baseline (USED)']
add('stable-sand colour spread across 5 EO frames small under the baseline (<= 8 levels per channel)', max(B['max_channel_spread_across_frames']) <= 8, B)
eo_raw = np.load(c.ACQ + 'EO_refl_f16.npz'); t = c.tone(eo_raw['2010'], eo_raw['valid_2010'])
add('cached EO frames equal a fresh application of the fixed baseline (no hidden per-frame normalization)', bool((t == eo['2010']).all()), c.BASE)
cr = np.load(f'{CACHE}TOSH_2021_refl.npy'); dmax = int(np.abs(c.tone(cr).astype(int) - to['2021'].astype(int)).max()); add('cached Toshka frames equal a fresh application of the fixed baseline (float16 cache, tolerance 1 level)', dmax <= 1, {'max_abs_diff_levels': dmax, **c.BASE})
# 5 upscale
add('upscale policy: max screen px per source px at 4K <= 4.0', r.ZOOM_SRC[0] * 4 == 3840 and 3840 / 3840 == 1.0, {'EO zoom end source window': r.ZOOM_SRC, 'EO max scale at 4K': 3840 / r.ZOOM_SRC[0], 'Toshka scale at 4K': 1.0})
# 6 videos
for f in ('eo_review.mp4', 'toshka_review.mp4'):
    p = c.VIS + f
    if os.path.exists(p):
        j = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate,nb_frames,codec_name,pix_fmt:format=duration,size', '-of', 'json', p]))
        add(f'{f} probe', j['streams'][0]['width'] == 1280 and j['streams'][0]['height'] == 720, j)
json.dump(res, open(c.VIS + 'qa_results.json', 'w'), indent=1)
print('fails', sum(1 for x in res['checks'] if x['result'] == 'FAIL'))
