import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as r, vis_common as c
O = c.VIS + 'stills/'; os.makedirs(O, exist_ok=True)
e = r.EO(); tgt = json.load(open(c.VIS + 'eo_target.json'))['zoom_target_src_px']; sc = 1.0; meta = {}
for k in r.EO_YEARS:
    im, m = e.frame(sc, (k, None), 0, 0, tgt, 0, 1.0, False); im.save(f'{O}eo_{k}.jpg', quality=90); meta[f'eo_{k}'] = m
for z in (0.5, 1.0):
    im, m = e.frame(sc, ('2024', None), 0, z, tgt, 0, max(0, 1 - z * 3), z == 1.0); im.save(f'{O}eo_zoom_{int(z*100)}.jpg', quality=90); meta[f'eo_zoom_{int(z*100)}'] = m
t = r.TO()
for k in r.TO_YEARS:
    im, m = t.frame(sc, (k, None), 0); im.save(f'{O}toshka_{k}.jpg', quality=90); meta[f'toshka_{k}'] = m
json.dump(meta, open(c.VIS + 'stills_meta.json', 'w'), indent=1)
# 4K pipeline test (not committed): Toshka 2021 and EO zoom end at 3840x2160
im, m = t.frame(2.0, ('2021', None), 0); assert im.size == (3840, 2160); im.save(c.VIS + 'test4k_toshka_2021.png'); meta['4k_toshka'] = m
im, m = e.frame(2.0, ('2024', None), 0, 1.0, tgt, 0, 0, True); assert im.size == (3840, 2160); im.save(c.VIS + 'test4k_eo_zoom_end.png'); print('4K EO zoom screen_px_per_src_px', m['screen_px_per_src_px'])
print('ok')
