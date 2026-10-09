import sys, os, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vis_common as c
from render import font
eo = np.load(c.ACQ + 'EO_refl_f16.npz'); rep = json.load(open(c.ACQ + 'EO_report.json')); EY = ['1984', '2000', '2010', '2016', '2024']
R = {k: eo[k].astype(np.float32) for k in EY}; V = {k: eo['valid_' + k] for k in EY}
stable = np.logical_and.reduce([(R[k][..., 0] > 0.30) & (R[k][..., 0] < 0.55) & V[k] for k in EY])
# erode stable mask by 15 px to keep only interior of unchanged sand
from numpy.lib.stride_tricks import sliding_window_view
st = stable.copy()
for d in (-15, 15):
    st &= np.roll(stable, d, 0); st &= np.roll(stable, d, 1)
print('stable px', int(st.sum()), flush=True)
out = {'stable_desert_mask_px': int(st.sum()), 'definition': 'pixels with TOA red 0.30-0.55 in all 5 East Oweinat frames, eroded 15 px (unchanged bare sand)', 'variants': {}}
variants = {'A_pooled_per_stack (previous pass)': lambda k: c.tone_pooled(R[k], V[k], rep), 'B_fixed_baseline (USED)': lambda k: c.tone(R[k], V[k]), 'C_per_frame_auto (rejected)': lambda k: c.tone_auto(R[k], V[k])}
rows = []
for name, f in variants.items():
    ims = {k: f(k) for k in ('1984', '2010', '2024')}
    med = {k: [int(np.median(f(k)[..., ch][st])) for ch in range(3)] for k in EY} if name.startswith('B') or True else None
    out['variants'][name] = {'stable_sand_median_rgb_8bit': med, 'max_channel_spread_across_frames': [int(max(med[k][i] for k in EY) - min(med[k][i] for k in EY)) for i in range(3)]}
    tiles = []
    for k in ('1984', '2010', '2024'):
        im = Image.fromarray(ims[k]); im.thumbnail((420, 360)); tiles.append(im)
    # Toshka crop 1999 vs 2021 (display crop) per variant
    for y in ('1999', '2021'):
        crop = np.load(f'{c.VIS}cache/TOSH_{y}_refl.npy').astype(np.float32); v = np.ones(crop.shape[:2], bool)
        t = c.tone(crop) if name.startswith('B') else (c.tone_auto(crop, v) if name.startswith('C') else c.tone_pooled(crop, v, json.load(open(c.ACQ + 'TW_report.json'))))
        im = Image.fromarray(t); im.thumbnail((420, 360)); tiles.append(im)
    rows.append((name, tiles))
W = 420 * 5; sheet = Image.new('RGB', (W, 360 * 3 + 40), (14, 17, 20)); d = ImageDraw.Draw(sheet)
labels = ['EO Aug 1984', 'EO Jan 2010', 'EO Jan 2024', 'Toshka Jan 1999', 'Toshka Nov 2021']
for i, (name, tiles) in enumerate(rows):
    for j, t in enumerate(tiles):
        sheet.paste(t, (j * 420, 40 + i * 360)); d.rectangle((j * 420, 40 + i * 360, j * 420 + 300, 40 + i * 360 + 18), fill=(0, 0, 0)); d.text((j * 420 + 4, 40 + i * 360 + 3), f'{name.split(" ")[0]}  {labels[j]}', font=font(13), fill=(255, 220, 90))
d.text((8, 10), 'Tonal comparison: A = previous pooled stretch, B = fixed episode baseline (used), C = per-frame auto-normalize (rejected: hides real brightness differences and exaggerates contrast)', font=font(14), fill=(240, 240, 236))
sheet.save(c.VIS + 'tonal_comparison.jpg', quality=85)
json.dump(out, open(c.VIS + 'tonal_stats.json', 'w'), indent=1)
for n, v in out['variants'].items(): print(n, v['stable_sand_median_rgb_8bit'], v['max_channel_spread_across_frames'])
