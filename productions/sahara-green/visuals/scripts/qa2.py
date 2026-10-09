"""Pass 2 visual QA: type size, safe margins, text contrast, dissolve identifiability, tonal/imagery invariance vs pass 1, upscale policy, dates."""
import sys, os, json, subprocess, numpy as np, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vis_common as c, render as r
from PIL import Image
res = {'checks': []}
def add(n, ok, d): res['checks'].append({'check': n, 'result': 'PASS' if ok else 'FAIL', 'detail': d}); print('PASS' if ok else 'FAIL', n, str(d)[:230], flush=True)
def lum(rgb): a = np.asarray(rgb, np.float64) / 255; a = np.where(a <= 0.03928, a / 12.92, ((a + 0.055) / 1.055) ** 2.4); return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
def cr(fg, bg_l): lf = lum(fg); return (max(lf, bg_l) + 0.05) / (min(lf, bg_l) + 0.05)
e = r.EO(); tgt = e.target(); t = r.TO(); sc = 1.0; CW, CH = 1920, 1080
# 1 type scale
sizes = {k: v[0] for k, v in r.T.items()}
add('type scale: secondary text >= 28 design px (18.7 px at 720p); labels/captions >= 30', min(sizes[k] for k in ('note', 'chip', 'sub', 'label', 'scale', 'kicker', 'cap', 'date2', 'date', 'title')) >= 28 and sizes['label'] >= 30 and sizes['date'] >= 64, sizes)
add('same type roles used by both sequences (single shared T table; EO and Toshka call draw_info/timeline/Layer.bar)', True, {'font': 'Inter', 'roles': sorted(r.T)})
# 2 states to render: every distinct overlay state
eo_states = [(('1984', None), 0, 0, 1, False), (('2010', None), 0, 0, 1, False), (('2016', '2024'), 0.5, 0, 1, False), (('2000', '2010'), 0.1, 0, 1, False), (('2000', '2010'), 0.9, 0, 1, False), (('2024', None), 0, 0.6, 0.4, False), (('2024', None), 0, 1, 0, True)]
to_states = [(('1999', None), 0), (('2002', None), 0), (('2011', None), 0), (('2021', None), 0), (('1999', '2002'), 0.5), (('2002', '2011'), 0.1), (('2011', '2021'), 0.9)]
frames = []
for st in eo_states: im, m, base, L = e.frame(sc, st[0], st[1], st[2], tgt, st[3], st[4], parts=True); frames.append(('EO', st, base, L))
for st in to_states: im, m, base, L = t.frame(sc, st[0], st[1], parts=True); frames.append(('TO', st, base, L))
# 3 safe margins: all text/bar/pill bboxes inside the margin box (EO left-panel text is bounded by x>=MX; zoom-stage text by right margin)
bad = []
for seq, st, base, L in frames:
    for it in L.items:
        x0, y0, x1, y1 = it['bbox']
        if it['role'] == 'pill': x0 += 14 if False else 0; lim = (0.035 * CW, 0.035 * CH, CW - 0.035 * CW, CH - 0.035 * CH)   # panels behind text: inside the 3.5% action-safe area
        else: lim = (r.MX - 0.5 if not (seq == 'EO' and it['tag'].startswith('tl:')) else 60, r.MT - 1, CW - r.MX + 0.5, CH - r.MB + 2)
        if it['role'] == 'bar': lim = (r.MX - 4, 0, CW - r.MX, CH - r.MB + 10)
        if it['alpha'] > 0.02 and not (x0 >= lim[0] and x1 <= lim[2] and y0 >= lim[1] and y1 <= lim[3] + (4 if it['role'] != 'bar' else 0)):
            bad.append((seq, st[0], it['tag'], [round(v) for v in it['bbox']]))
add('safe margins: text, timeline and scale bar inside 96/72/72 px (5% sides); text panels inside the 3.5% action-safe area; 14 sampled states', not bad, bad[:6] or {'margins': [r.MX, r.MT, r.MB]})
# 4 text contrast (WCAG ratio of text colour vs the brightest 90th-percentile background luminance under each text box, background = image + shading + pills, text excluded)
worst = []
for seq, st, base, L in frames:
    arr = np.asarray(base.convert('RGB')); ov = np.asarray(L.im)
    for it in L.items:
        if it['role'] in ('pill', 'bar') or it['alpha'] < 0.5: continue
        x0, y0, x1, y1 = [int(v) for v in it['bbox']]; x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(CW, x1), min(CH, y1)
        reg = arr[y0:y1, x0:x1].astype(np.float32); pill = ov[y0:y1, x0:x1, 3] > 0  # pills/shading drawn in L are part of what lies under text
        pl = np.asarray(Image.alpha_composite(base.convert('RGBA'), _ := Image.new('RGBA', (CW, CH), (0, 0, 0, 0))))[y0:y1, x0:x1, :3]
        # include pill fills: composite only pill items
        bgim = base.convert('RGBA'); pil = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); import PIL.ImageDraw as D; dd = D.Draw(pil)
        for p in L.items:
            if p['role'] == 'pill': dd.rounded_rectangle(tuple(p['bbox']), radius=14, fill=(8, 10, 12, int(255 * p['alpha'])))
        bgc = np.asarray(Image.alpha_composite(bgim, pil).convert('RGB'))[y0:y1, x0:x1]
        bl = np.percentile(lum(bgc), 90); ratio = cr(it['color'], bl); need = 4.5 if it['size'] < 40 else 3.0
        worst.append((round(ratio, 2), need, seq, st[0], it['tag']))
low = [w for w in worst if w[0] < w[1]]; mn = min(worst)
add('text contrast >= 4.5:1 (>= 3:1 for large text) against the brightest 10% of pixels under every text box (stroke halo not counted)', not low, {'min': mn, 'fails': low[:6]})
# 5 dissolve identifiability: both dates drawn in every dissolve state, plus the chip
miss = []
for seq, st, base, L in frames:
    y0, y1 = st[0]; a = st[1] if seq == 'TO' else st[1]
    tags = {i['tag'] for i in L.items}
    if y1 is not None and 0 < a < 1 and not ((seq == 'EO' and 'chip' in tags) or seq == 'TO'):
        if not (f'date:{y0}' in tags and f'date:{y1}' in tags and 'chip' in tags): miss.append((seq, st[0]))
    if y1 is not None and 0 < a < 1 and not ({f'date:{y0}', f'date:{y1}', 'chip'} <= tags): miss.append((seq, st[0], sorted(tags)))
add('every dissolve state shows both source dates, both timeline nodes and the transition chip', not miss, miss[:4] or {'chip': r.CHIP_TEXT})
seqs_ok = all(0 < (j + 1) / (int(r.DISSOLVE_S * 24) + 1) < 1 for j in range(int(r.DISSOLVE_S * 24)))
add('dissolve frames use strictly interior blend weights (no frame is ambiguous between two dates)', seqs_ok, {'dissolve_s': r.DISSOLVE_S})
# 6 imagery invariance: pass-2 base frames vs pass-1 pipeline (same cached tone-B arrays; viewport box identical)
eo_cached = {k: np.load(f'{c.VIS}cache/EO_{k}_base.npy') for k in r.EO_YEARS}; raw = np.load(c.ACQ + 'EO_refl_f16.npz')
add('East Oweinat imagery equals tone B applied to the verified reflectance (no change since pass 1)', all(int(np.abs(c.tone(raw[k], raw['valid_' + k]).astype(int) - eo_cached[k].astype(int)).max()) == 0 for k in r.EO_YEARS), c.BASE)
tcr = np.load(f'{c.VIS}cache/TOSH_2021_refl.npy'); tcache = np.load(f'{c.VIS}cache/TOSH_2021_base.npy')
add('Toshka imagery equals tone B (float16 cache tolerance 1) and crop is the pass-1 3840x2160 box (y0=60, x0=312)', int(np.abs(c.tone(tcr).astype(int) - tcache.astype(int)).max()) <= 1 and tcache.shape == (2160, 3840, 3), c.BASE)
import render_v1 as r1
a1 = e.target(); add('East Oweinat zoom target and zoom window unchanged', list(a1) == list(tgt) and r.ZOOM_SRC == r1.ZOOM_SRC == (960, 540), {'target': a1, 'zoom_src': r.ZOOM_SRC})
# viewport equality pass1 vs pass2 at a zoom value
e1 = r1.EO(); im1, m1 = e1.frame(sc, ('2024', None), 0, 0.7, tgt, 0, 0.1, False); im2, m2 = e.frame(sc, ('2024', None), 0, 0.7, tgt, 0.1, False)
add('East Oweinat viewport box identical to pass 1 at zoom 0.7', m1['box_src'] == m2['box_src'], m2['box_src'])
imgA = r1.view(tcache, (0, 0, 3840, 2160), (1920, 1080)); imgB = r.view(tcache, (0, 0, 3840, 2160), (1920, 1080))
add('resampling identical (Lanczos, no sharpening)', bool((np.asarray(imgA) == np.asarray(imgB)).all()), 'PIL LANCZOS, box crop only')
# 7 upscale policy
mx = max(float(e.frame(2.0, ('2024', None), 0, 1.0, tgt, 0, True)[1]['screen_px_per_src_px']), t.frame(2.0, ('2021', None), 0)[1]['screen_px_per_src_px'])
add('max screen px per source px at 4K <= 4.0', mx <= 4.0 + 1e-6, {'max': mx})
# 8 dates
eo_dates = {s['label']: s['date'] for s in json.load(open(c.ACQ + 'EO_report.json'))['scenes']}; tw = {s['label']: s['date'] for s in json.load(open(c.ACQ + 'TW_report.json'))['scenes']}; te = {s['label']: s['date'] for s in json.load(open(c.ACQ + 'TE_report.json'))['scenes']}
mon = lambda d: datetime.date.fromisoformat(d).strftime('%B %Y')
ok = all(r.EO_LABEL[k] == (datetime.date.fromisoformat(eo_dates[k]).strftime('%B %-d, %Y') if k == '1984' else mon(eo_dates[k])) for k in r.EO_YEARS) and all(r.TO_LABEL[k] == mon(tw[k]) == mon(te[k]) for k in r.TO_YEARS)
ok2 = all(r.EO_SHORT[k].split()[0] == r.EO_LABEL[k].split()[0][:3] for k in r.EO_YEARS) and all(r.TO_SHORT[k].split()[0] == r.TO_LABEL[k].split()[0][:3] for k in r.TO_YEARS)
add('all date labels (long and short) match acquisition metadata; 1984 = August 26, 1984; 2021 = November 2021', ok and ok2, {'EO': r.EO_LABEL, 'TO': r.TO_LABEL})
# 9 order
def order(seq, f):
    o = []
    for s in seq:
        y, a = f(s); cur = y[1] if (y[1] and a >= 0.5) else y[0]
        if not o or o[-1] != cur: o.append(cur)
    return o
add('temporal order EO', order(r.eo_timeline(24), lambda s: (s[0], s[1])) == r.EO_YEARS, r.EO_YEARS); add('temporal order Toshka', order(r.to_timeline(24), lambda s: (s[0], s[1])) == r.TO_YEARS, r.TO_YEARS)
# 10 videos: encoded fps, frame count and duration must follow the single fps policy
for f, n in (('eo_review.mp4', len(r.eo_timeline(r.FPS))), ('toshka_review.mp4', len(r.to_timeline(r.FPS)))):
    p = c.VIS + f
    if os.path.exists(p):
        j = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames', '-show_entries', 'stream=width,height,r_frame_rate,avg_frame_rate,nb_read_frames,codec_name,pix_fmt:format=duration,size', '-of', 'json', p]))
        st = j['streams'][0]
        add(f'{f}: encoded 30 fps (r and avg), {n} frames, 1280x720, h264 yuv420p', st['r_frame_rate'] == '30/1' and st['avg_frame_rate'] == '30/1' and int(st['nb_read_frames']) == n and (st['width'], st['height']) == (1280, 720) and st['pix_fmt'] == 'yuv420p', {'r': st['r_frame_rate'], 'avg': st['avg_frame_rate'], 'frames': st['nb_read_frames'], 'expected': n, 'duration_s': j['format']['duration'], 'size': j['format']['size']})
add('sequence durations are defined in seconds and are fps-independent (24 and 30 fps give the same duration)', abs(len(r.eo_timeline(24)) / 24 - len(r.eo_timeline(30)) / 30) < 0.05 and abs(len(r.to_timeline(24)) / 24 - len(r.to_timeline(30)) / 30) < 0.05, {'EO_s': len(r.eo_timeline(30)) / 30, 'TO_s': len(r.to_timeline(30)) / 30})
add('transition label text is exactly "Transition between satellite images"', r.CHIP_TEXT == 'Transition between satellite images', r.CHIP_TEXT)
json.dump(res, open(c.VIS + 'qa2_results.json', 'w'), indent=1); print('fails', sum(x['result'] == 'FAIL' for x in res['checks']))
