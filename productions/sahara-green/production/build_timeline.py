#!/usr/bin/env python3
"""EP001: assemble the complete yt-render v3 (profile long) timeline for all 36 scenes from the REAL narration.

  python3 build_timeline.py WORKSPACE      # WORKSPACE holds the large files (outside Git): sequences (build_sequences.py), CALIPSO 30 fps, narration wav
Reads scene_plan.json, narration/voice/narration.voice.json (word timings), captions, graphics/out, stills/. Writes WORKSPACE/timeline.json and
production/timeline_ep001.json (a copy without large-file paths). Every start/step time is an anchor word of the locked narration (seconds, snapped to 30 fps).
"""
import json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); REPO = os.path.dirname(os.path.dirname(ROOT))
FPS = 30
def q(t): return round(t * FPS) / FPS
NAR = os.path.join(ROOT, 'narration')
words = json.load(open(os.path.join(NAR, 'voice', 'narration.voice.json')))['words']
def norm(w): return re.sub(r"[^a-z0-9']", '', w.lower().replace('’', "'"))
NW = [norm(w['text']) for w in words]
def at(phrase, after=0.0, nth=1, edge='start'):
    """time of the first word of `phrase` (consecutive words) after `after` seconds; nth occurrence"""
    p = [norm(x) for x in phrase.split()]; k = 0
    for i in range(len(NW) - len(p) + 1):
        if words[i]['start'] + 1e-6 < after: continue
        if NW[i:i + len(p)] == p:
            k += 1
            if k == nth: return q(words[i]['start'] if edge == 'start' else words[i + len(p) - 1]['end'])
    raise SystemExit(f'phrase not found after {after}: {phrase!r}')
PLAN = {s['scene']: s for s in json.load(open(os.path.join(HERE, 'scene_plan.json')))['scenes'] if s['status'] == 'ok'}
def S(i): return q(PLAN[i]['start'])
def E(i): return q(PLAN[i]['end'])
CRED = {'landsat9': 'Landsat 9 · USGS', 'landsat8': 'Landsat 8 · USGS', 'nasa_bm': 'NASA Earth Observatory · Blue Marble', 'nasa_calipso': 'NASA Goddard SVS · CALIPSO dust (Dust in the Wind)',
        'gfx': 'Original graphic · sources on the image'}
GFX_DIR = os.path.join(HERE, 'graphics', 'out'); ST_DIR = os.path.join(HERE, 'stills')
def main(ws):
    seq = json.load(open(os.path.join(ws, 'sequences.json')))
    assets, shots = {}, []
    # --- assets -----------------------------------------------------------------------------------------------------------------------
    def put(src, name):
        d = os.path.join(ws, name)
        if not os.path.exists(d) or os.path.getsize(d) != os.path.getsize(src): shutil.copyfile(src, d)
        return name
    def still(aid, fname, credit_key, label, prov):
        rec = json.load(open(os.path.join(ST_DIR, fname[:-4] + '.json'))) if os.path.exists(os.path.join(ST_DIR, fname[:-4] + '.json')) else {}
        assets[aid] = {'src': put(os.path.join(ST_DIR, fname), fname), 'kind': 'external_still', 'credit': CRED[credit_key], 'label': label, **prov}
    LS_PROV = lambda k: {'source_url': 'https://earthexplorer.usgs.gov/', 'license': 'USGS Landsat: public domain, credit requested', 'retrieved': '2026-10-08',
                         'image_date': json.load(open(os.path.join(ST_DIR, f'{k}_toneB.json')))['date_acquired'], 'derived_from': json.load(open(os.path.join(ST_DIR, f'{k}_toneB.json')))['scene']}
    still('tassili', 'tassili_toneB.png', 'landsat9', 'Tassili n\'Ajjer', LS_PROV('tassili'))
    still('bodele', 'bodele_toneB.png', 'landsat9', 'Bodélé', LS_PROV('bodele'))
    still('ounianga', 'ounianga_toneB.png', 'landsat9', 'Ounianga', LS_PROV('ounianga'))
    still('gilf', 'gilf_toneB.png', 'landsat9', 'Gilf Kebir', LS_PROV('gilf'))
    still('kufra', 'kufra_toneB.png', 'landsat9', 'Kufra', LS_PROV('kufra'))
    nasa = json.load(open(os.path.join(ST_DIR, 'nasa_provenance.json')))
    still('bluemarble', 'africa.0700.jpg', 'nasa_bm', 'Blue Marble: Africa', {k: nasa['svs3539'][k] for k in ('source_url', 'license', 'retrieved', 'image_date')} | {'derived_from': 'SVS 3539 africa.0700.jpg'})
    for k, fn, cr in (('eo', 'seq_eo.mp4', 'Landsat 5, 7, 8, 9 · USGS (East Oweinat sequence)'), ('toshka', 'seq_toshka.mp4', 'Landsat 5, 7, 8 · USGS (Toshka sequence)'),
                      ('s6', 'seq_s6.mp4', 'Landsat 5, 9 · USGS (East Oweinat)'), ('s22', 'seq_s22.mp4', 'Landsat 9 · USGS (East Oweinat)'), ('s35', 'seq_s35.mp4', 'Landsat 5, 9 · USGS (East Oweinat)')):
        assets['seq_' + k] = {'src': fn, 'kind': 'video', 'credit': cr}
    assets['calipso'] = {'src': 'calipso_dust_30fps.mp4', 'kind': 'video', 'credit': CRED['nasa_calipso']}
    gfx_steps = {}
    def graphic(gid):
        j = json.load(open(os.path.join(GFX_DIR, gid + '.json'))); files = j['steps'] if isinstance(j.get('steps'), list) else [gid + '.png']
        ids = []
        for n, f in enumerate(files, 1):
            aid = f'{gid}_{n}'; assets[aid] = {'src': put(os.path.join(GFX_DIR, f), f), 'kind': 'graphic', 'credit': CRED['gfx'], 'group': gid}; ids.append(aid)
        gfx_steps[gid] = ids; return ids
    def gshot(sid, beat, start, gid, times):
        ids = graphic(gid); assert len(times) == len(ids), (gid, len(times), len(ids))
        t0 = start; layers = [{'type': 'graphic', 'asset': ids[0]}]
        for aid, t in list(zip(ids, times))[1:]:
            layers.append({'type': 'graphic', 'asset': aid, 't': [round(q(t) - t0, 4), None]})
        shots.append({'id': sid, 'beat': beat, 'start': t0, 'layers': layers})
    from PIL import Image
    SIZES = {}
    def vw(c, w, asset):
        if asset not in SIZES:
            with Image.open(os.path.join(ws, assets[asset]['src'])) as im: SIZES[asset] = im.size
        iw, ih = SIZES[asset]; w = min(w, 0.99, 0.99 * ih * 16 / 9 / iw); bw = w * iw; bh = bw * 9 / 16
        cx = min(max(c[0], bw / 2 / iw + 1e-4), 1 - bw / 2 / iw - 1e-4); cy = min(max(c[1], bh / 2 / ih + 1e-4), 1 - bh / 2 / ih - 1e-4)
        return {'center': [round(cx, 5), round(cy, 5)], 'width': round(w, 5)}
    def sshot(sid, beat, start, asset, v0, v1, labels=(), ease='in_out'):
        L = [{'type': 'still', 'asset': asset, 'view': {'from': vw(*v0, asset), 'to': vw(*v1, asset), 'ease': ease}}]
        for lab in labels:
            d = {'type': 'label', 'text': lab['text'], 'style': lab.get('style', 'tag'), 'slot': lab.get('slot', 'upper'), 't': [round(q(lab['t0']) - start, 4), round(q(lab['t1']) - start, 4)]}
            if lab.get('sub'): d['sub'] = lab['sub']
            L.append(d)
        shots.append({'id': sid, 'beat': beat, 'start': start, 'layers': L})
    def vshot(sid, beat, start, asset, cap, trim=None, labels=()):
        L = [{'type': 'video', 'asset': asset, 'credit': False, 'captions': True, 'caption': cap}]
        if trim is not None: L[0]['trim'] = trim
        for lab in labels:
            d = {'type': 'label', 'text': lab['text'], 'style': lab.get('style', 'tag'), 'slot': lab.get('slot', 'middle'), 't': [round(q(lab['t0']) - start, 4), round(q(lab['t1']) - start, 4)]}
            if lab.get('sub'): d['sub'] = lab['sub']
            L.append(d)
        shots.append({'id': sid, 'beat': beat, 'start': start, 'layers': L})
    CAP_EO = {'band': 0.76, 'center_x': 0.667, 'max_width': 1100}; CAP_TO = {'band': 0.76}
    # --- scenes -----------------------------------------------------------------------------------------------------------------------
    sshot('s01', 'scene 1', 0.0, 'tassili', ((0.5, 0.5), 0.80), ((0.5, 0.5), 0.72))
    gshot('s02', 'scene 2', S('2'), 'g02-230', [S('2'), at('geological', S('2')), at('than 230', S('2'))])
    sshot('s03', 'scene 3', S('3'), 'bodele', ((0.5, 0.5), 0.96), ((0.5, 0.5), 0.84), [{'text': 'THOUSANDS OF MILES AWAY', 't0': at('thousands of miles'), 't1': E('3')}])
    sshot('s04', 'scene 4', S('4'), 'bluemarble', ((0.5, 0.5), 0.90), ((0.36, 0.62), 0.62), [{'text': "WORLD'S LARGEST NON-POLAR DESERT", 't0': at("world's largest"), 't1': E('4')}])
    gshot('s05', 'scene 5', S('5'), 'g05-rain', [S('5'), at('tens of', S('5'))])
    vshot('s06', 'scene 6', seq['s6']['start'], 'seq_s6', CAP_EO)
    t7 = S('7'); gshot('s07', 'scene 7', t7, 'g07-timeline', [t7, at('11,000', t7), at('grassland', t7), at('dotted', t7), at('other records', t7), at('a few thousand', t7), at('not a jungle', t7)])
    t8 = S('8')
    sshot('s08', 'scene 8', t8, 'bodele', ((0.5, 0.45), 0.95), ((0.45, 0.58), 0.62),
          [{'text': 'FLOOR OF LAKE MEGA-CHAD', 'sub': 'ABOUT 7,000 YEARS AGO', 't0': at('7,000 years', t8), 't1': at('spanned', t8)},
           {'text': 'LARGER THAN ALL THE GREAT LAKES', 'sub': 'COMBINED · NASA', 't0': at('larger than', t8), 't1': E('8')}])
    t9 = S('9'); t9b = at("algeria's", t9)
    gshot('s09a', 'scene 9', t9, 'g09-burials', [t9, at('about 200', t9), at('beside a', t9), at('alongside the', t9)])
    sshot('s09b', 'scene 9', t9b, 'tassili', ((0.28, 0.40), 0.55), ((0.30, 0.45), 0.38),
          [{'text': "TASSILI N'AJJER, ALGERIA", 't0': t9b, 't1': at('15,000', t9b)}, {'text': '15,000+ ETCHINGS AND ILLUSTRATIONS', 'sub': 'PREHISTORIC · NASA', 't0': at('15,000', t9b), 't1': E('9')}])
    t10 = S('10'); gshot('s10', 'scene 10', t10, 'g10-rain', [t10, at('around 450', t10), at('those are rough', t10)])
    t11 = S('11')
    sshot('s11', 'scene 11', t11, 'ounianga', ((0.62, 0.50), 1.0), ((0.655, 0.525), 0.19),
          [{'text': 'LAKES OF OUNIANGA, CHAD', 't0': at('lakes of ounianga', t11), 't1': at('pollen', t11)},
           {'text': 'POLLEN FROM THE ORIGINAL LAKE', 'sub': 'WOODED GRASSLAND', 't0': at('pollen', t11), 't1': at('plants that now', t11)},
           {'text': 'SUCH PLANTS NOW GROW ~300 KM', 'sub': '(~190 MI) FARTHER SOUTH', 't0': at('plants that now', t11), 't1': at('so what turned', t11)}])
    t12 = S('12')
    gshot('s12', 'scene 12', t12, 'g12-orbit', [t12, at('sunnier', t12), at('monsoon', at('sunnier', t12)), at('deep into', t12), at('but sunlight', t12)])
    t13 = S('13'); a13 = at('one proposed', t13); gshot('s13', 'scene 13', t13, 'g13-models', [t13, at('researchers are still', t13), a13, at('more lakes', a13), at('more rain', a13), at('more plants', a13), q(at('more plants', a13) + 1.2)])
    t14 = S('14'); gshot('s14', 'scene 14', t14, 'g14-sapropel', [t14, q(at('laid down', t14) - 0.4), at('laid down', t14), q(at('point to', t14) - 0.5), at('point to', t14), at('8 million', t14)])
    t15 = S('15')
    sshot('s15', 'scene 15', t15, 'ounianga', ((0.655, 0.525), 0.30), ((0.5, 0.5), 1.0),
          [{'text': 'ABRUPT OR GRADUAL IS DEBATED', 't0': at('scientists still', t15), 't1': at('one reconstruction', t15)},
           {'text': 'RAINS RETREAT SOUTH OVER ~2-3,000 YEARS', 'sub': 'ONE RECONSTRUCTION · OTHER RECORDS: MORE ABRUPT', 't0': at('one reconstruction', t15), 't1': at('the desert crept', t15)},
           {'text': 'THE DESERT CREPT SOUTH', 't0': at('the desert crept', t15), 't1': E('15')}])
    t16 = S('16'); gshot('s16', 'scene 16', t16, 'g16-cell', [t16, at('forms clouds', t16), at('high up', t16), at('sinks', t16), at('so greening', t16)])
    sshot('s17', 'scene 17', S('17'), 'gilf', ((0.62, 0.52), 0.50), ((0.5, 0.5), 1.0))
    vshot('s18', 'scene 18', seq['eo']['start'], 'seq_eo', CAP_EO)
    t19 = seq['eo']['end']
    gshot('s19', 'scene 19', t19, 'g19-aquifer', [t19, at('egypt', t19), at('libya', t19), at('sudan', t19), at('chad', t19), at('nasa says', t19), at('soaked', t19), at('a million', t19), at('when the region', t19), at('recharges slowly', t19)])
    sshot('s20', 'scene 20', S('20'), 'kufra', ((0.58, 0.55), 1.0), ((0.689, 0.70), 0.42), [{'text': 'KUFRA, LIBYA', 't0': at('kufra', S('20')), 't1': E('20')}])
    vshot('s21', 'scene 21', seq['toshka']['start'], 'seq_toshka', CAP_TO)
    vshot('s22', 'scene 22', seq['s22']['start'], 'seq_s22', CAP_EO)
    t23 = S('23')
    steps23 = [t23, at('outback', t23), at('watered with', t23), at('desalinated', t23), at('seawater', t23), at('about as much carbon', t23), at('that estimate', t23), at('calculations', t23), at('not from a climate', t23), at('carbon removal', t23), at('stop gaining', t23)]
    gshot('s23', 'scene 23', t23, 'g23-proposal', steps23)
    gshot('s24', 'scene 24', S('24'), 'g24-trillion', [S('24')])
    t24b = S('24b'); gshot('s24b1', 'scene 24b', t24b, 'g24b-1000', [t24b, at('rainfall rose', t24b), at('more than 1,000', t24b), at('over roughly', t24b)])
    t24c = at('a later team', t24b); gshot('s24b2', 'scene 24b', t24c, 'g24b-267', [t24c, at('across the whole', t24c), at('rose by about', t24c), at('cooled by', t24c)])
    t24d = at('those two numbers', t24b); gshot('s24b3', 'scene 24b', t24d, 'g24b-diff', [t24d, at('versus', t24d), q(at('versus', t24d) + 1.5)])
    t25 = S('25'); gshot('s25', 'scene 25', t25, 'g25-budget', [t25, at('lost about', t25), at('evaporation', t25), at('total rainfall', t25), at("that's a ratio", t25), at('carried south', t25), at('semi-arid', t25), at('nearby ocean', t25), at('took about', t25), at('of desalinated', t25), at('the model simply', t25), at('whether it could', t25)])
    sshot('s25b', 'scene 25b', S('25b'), 'bluemarble', ((0.30, 0.62), 0.30), ((0.5, 0.5), 1.0))
    t29 = S('29'); n_fr = round((E('29') - t29) * FPS)
    vshot('s29', 'scene 29', t29, 'calipso', {'band': 0.2}, trim=round(3084 - n_fr + 1) / FPS,
          labels=[{'text': '~182 MILLION TONS OF DUST A YEAR', 'sub': "PAST THE SAHARA'S WESTERN EDGE · 2007-13 AVG", 't0': at('182 million', t29), 't1': at('roughly 28', t29)},
                  {'text': '~28 MILLION TONS SETTLE ON THE AMAZON', 'sub': 'SATELLITE-DERIVED ESTIMATE', 't0': at('roughly 28', t29), 't1': at('that dust carries', t29)},
                  {'text': '~22,000 TONS OF PHOSPHORUS A YEAR', 'sub': 'ESTIMATE · DELIVERED TO THE AMAZON BASIN', 't0': at('that dust carries', t29), 't1': E('29')}])
    t30 = S('30')
    sshot('s30', 'scene 30', t30, 'bodele', ((0.5, 0.5), 0.92), ((0.46, 0.55), 0.36),
          [{'text': 'BODÉLÉ DEPRESSION, CHAD', 'sub': 'ANCIENT LAKEBED', 't0': at('the bodélé', t30), 't1': at('but it may not', t30)},
           {'text': 'SOURCE OF AMAZON DUST: DEBATED', 't0': at('but it may not', t30), 't1': E('30')}])
    t31 = S('31'); gshot('s31', 'scene 31', t31, 'g31-hypothesis', [t31, at('would the amazon', t31), at('planted sahara', t31)])
    t32 = S('32'); gshot('s32', 'scene 32', t32, 'g32-storms', [t32, at('researchers simulated', t32), at('when the sahara', t32), at('covered in', t32), at('dust was cut', t32), at('compared with', t32), at('that produced', t32), at('in both hemispheres', t32), at('especially around', t32), at('though some', t32), at('a stronger', t32), at('changed winds', t32), at('of the past', t32), at("there aren't", t32), at('to check it', t32)])
    t33 = S('33'); gshot('s33', 'scene 33', t33, 'g33-sahel', [t33, at('after the droughts', t33), at('satellite records', t33), at('came back', t33), at('researchers concluded', t33), at('lasting desertification', t33), at('unccd', t33), at('more than five', t33), at('maradi', t33), at('over seven', t33), at('across niger', t33), at('those are reported', t33)])
    t34 = S('34'); gshot('s34', 'scene 34', t34, 'g34-gww', [t34, at('pledge made', t34), at('restore 100', t34), at('coordinating agency', t34), at('25 million', t34), at('figures reported', t34), at('about 4', t34), at('the project has', t34), at('mosaic', t34), at('including regrown', t34)])
    vshot('s35', 'scene 35', seq['s35']['start'], 'seq_s35', CAP_EO)
    t36 = S('36'); gshot('s36', 'scene 36', t36, 'g36-uncertain', [t36, at('coming centuries', t36)])
    sshot('s37', 'scene 37', S('37'), 'tassili', ((0.55, 0.60), 0.32), ((0.5, 0.5), 0.95))
    # --- checks ------------------------------------------------------------------------------------------------------------------------
    starts = [s['start'] for s in shots]
    assert starts == sorted(starts) and len(set(starts)) == len(starts), [(a, b) for a, b in zip(starts, starts[1:]) if b <= a]
    assert starts[0] == 0
    # --- narration, captions, timeline ------------------------------------------------------------------------------------------------
    put(os.path.join(NAR, 'voice', 'narration.wav'), 'narration.wav'); put(os.path.join(NAR, 'voice', 'narration.voice.json'), 'narration.voice.json')
    os.makedirs(os.path.join(ws, 'captions'), exist_ok=True)
    for f in ('captions.srt',): shutil.copyfile(os.path.join(NAR, 'captions', f), os.path.join(ws, 'captions', f))
    json.dump({'schema': 'yt-geo-stack/1', 'epsg': 32635, 'x0': 600000.0, 'y_top': 2600000.0, 'pixel_m': 30.0, 'width': 100, 'height': 100}, open(os.path.join(ws, 'grid.json'), 'w'))
    dur = json.load(open(os.path.join(NAR, 'voice', 'narration.voice.json')))['duration']
    tl = {'version': 3, 'profile': 'long', 'grid': 'grid.json', 'assets': assets, 'shots': shots,
          'voice': {'src': 'narration.wav', 'meta': 'narration.voice.json'}, 'captions': {'src': 'captions/captions.srt', 'preset': 'default'},
          'end': {'seconds': round(q(dur + 0.02) , 4)}, 'render': {'segment_s': 60},
          'meta': {'episode': 'EP001', 'title': 'What If We Turned the Sahara Desert Green?', 'review_master': True}}
    json.dump(tl, open(os.path.join(ws, 'timeline.json'), 'w'), indent=1, ensure_ascii=False)
    print(len(shots), 'shots,', len(assets), 'assets, end', tl['end'])
if __name__ == '__main__': main(sys.argv[1])
