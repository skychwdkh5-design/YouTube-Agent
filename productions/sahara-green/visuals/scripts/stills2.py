import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as r, vis_common as c
O = c.VIS + 'stills2/'; os.makedirs(O, exist_ok=True)
e = r.EO(); tgt = e.target(); t = r.TO(); meta = {}
e.frame(1.0, ('2024', None), 0, 0, tgt, 1.0, False)[0].save(O + 'eo_zoom_start.jpg', quality=92)
e.frame(1.0, ('2024', None), 0, 1.0, tgt, 0, True)[0].save(O + 'eo_zoom_end.jpg', quality=92)
for k in ('1984', '2010'): e.frame(1.0, (k, None), 0, 0, tgt, 1.0, False)[0].save(O + f'eo_{k}.jpg', quality=92)
e.frame(1.0, ('2010', '2016'), 0.5, 0, tgt, 1.0, False)[0].save(O + 'eo_dissolve_2010_2016.jpg', quality=92)
for k in r.TO_YEARS: t.frame(1.0, (k, None), 0)[0].save(O + f'toshka_{k}.jpg', quality=92)
t.frame(1.0, ('2011', '2021'), 0.5)[0].save(O + 'toshka_dissolve_2011_2021.jpg', quality=92)
print('ok')
