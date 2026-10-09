#!/usr/bin/env python3
"""EP001 targeted editorial pass: render ONLY two sections at 1920x1080 / 30 fps with the real narration slice and the master's own captions.
  opening   0.000-30.000 s          (scenes 1-5 re-staged, scene 6 sequence unchanged)
  proposal  357.167-395.300 s       (scene 23 re-staged)
Audio is the locked Adam narration cut from the locked WAV with the master's own constant gain (-0.8 dB, peak-limited by the renderer); no normalisation.
  python3 build_revision.py WORKSPACE [opening|proposal ...]"""
import json, os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_timeline as bt
from PIL import Image
FPS = 30; q = bt.q; at = bt.at
RENDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), '.claude', 'skills', 'yt-render', 'render.py')
GFX = os.path.join(HERE, 'graphics', 'out_revision'); ST = os.path.join(HERE, 'stills')
MASTER_GAIN_DB = -0.8                  # the renderer's constant gain on the whole narration (peak-limited); applied here so the sections sound exactly like the master
CRED_G = 'Original graphic · sources on the image'
def srt_cues(path):
    out = []
    for b in re.split(r'\n\s*\n', open(path, encoding='utf-8').read().replace('\r\n', '\n').strip()):
        L = b.split('\n'); t = L[1].split(' --> ')
        f = lambda s: (lambda h, m, x: int(h) * 3600 + int(m) * 60 + float(x))(*s.replace(',', '.').split(':'))
        out.append((f(t[0]), f(t[1]), '\n'.join(L[2:])))
    return out
def fmt(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t - 3600 * h - 60 * m
    return f'{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}'.replace(',1000', ',999')
def build(ws, name, S, D, shots_fn, extra_frames=0):
    d = os.path.join(ws, name); os.makedirs(os.path.join(d, 'captions'), exist_ok=True)
    S = q(S); frames = round(D * FPS); Dq = frames / FPS; E = S + Dq
    def put(src, nm=None):
        nm = nm or os.path.basename(src); dst = os.path.join(d, nm)
        if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src): shutil.copyfile(src, dst)
        return nm
    assets = {}
    def rel(t): return (round(t * FPS) - round(S * FPS)) / FPS          # exact frame multiples (no 4-decimal rounding: a start of 22.7667 s would land on frame 684, not 683)
    def gfx(gid, times, start, credit=CRED_G):
        j = json.load(open(os.path.join(GFX, gid + '.json'))); files = j['steps']; assert len(files) == len(times), (gid, len(files), len(times))
        ids = []
        for n, f in enumerate(files, 1):
            aid = f'{gid}_{n}'; assets[aid] = {'src': put(os.path.join(GFX, f)), 'kind': 'graphic', 'credit': credit, 'group': gid}; ids.append(aid)
        L = [{'type': 'graphic', 'asset': ids[0]}] + [{'type': 'graphic', 'asset': a, 't': [rel(t) - rel(start), None]} for a, t in list(zip(ids, times))[1:]]
        return L
    shots = shots_fn(d, assets, put, rel, gfx, S, E)
    starts = [s['start'] for s in shots]; assert starts[0] == 0 and starts == sorted(starts) and len(set(starts)) == len(starts), starts
    # narration slice: the locked WAV, cut exactly, with the master's constant gain
    wav = os.path.join(d, 'narration_slice.wav')
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{S:.4f}', '-t', f'{Dq:.4f}', '-i', os.path.join(bt.NAR, 'voice', 'narration.wav'), '-af', f'volume={MASTER_GAIN_DB}dB', '-c:a', 'pcm_s16le', wav], check=True)
    import hashlib
    master = json.load(open(os.path.join(bt.NAR, 'voice', 'narration.voice.json')))
    words = [{'text': w['text'], 'start': round(w['start'] - S, 3), 'end': round(w['end'] - S, 3)} for w in master['words'] if w['start'] >= S - 1e-6 and w['end'] <= E + 1e-6]
    meta = {k: master[k] for k in master if k not in ('words', 'audio', 'audio_sha256', 'duration')}
    meta.update({'audio': 'narration_slice.wav', 'audio_sha256': hashlib.sha256(open(wav, 'rb').read()).hexdigest(), 'duration': round(Dq, 3), 'words': words,
                 'window': {'master_start_s': S, 'master_end_s': round(E, 4), 'gain_db_applied': MASTER_GAIN_DB, 'note': 'slice of the locked narration; word timings shifted by the window start, not altered'}})
    json.dump(meta, open(os.path.join(d, 'narration_slice.voice.json'), 'w'), indent=1, ensure_ascii=False)
    cues = []
    for a, b, t in srt_cues(os.path.join(bt.NAR, 'captions', 'captions.srt')):
        a2, b2 = max(a, S) - S, min(b, E) - S
        if b2 - a2 > 0.25: cues.append((a2, b2, t))
    with open(os.path.join(d, 'captions', 'captions.srt'), 'w', encoding='utf-8') as f:
        for i, (a, b, t) in enumerate(cues, 1): f.write(f'{i}\n{fmt(a)} --> {fmt(b)}\n{t}\n\n')
    json.dump({'schema': 'yt-geo-stack/1', 'epsg': 32635, 'x0': 600000.0, 'y_top': 2600000.0, 'pixel_m': 30.0, 'width': 100, 'height': 100}, open(os.path.join(d, 'grid.json'), 'w'))
    tl = {'version': 3, 'profile': 'long', 'grid': 'grid.json', 'assets': assets, 'shots': shots,
          'voice': {'src': 'narration_slice.wav', 'meta': 'narration_slice.voice.json', 'normalize': False},
          'captions': {'src': 'captions/captions.srt', 'preset': 'default'}, 'end': {'seconds': round((frames + extra_frames) / FPS, 4)}, 'render': {'segment_s': 60},
          'meta': {'section': name, 'master_start_s': S, 'master_end_s': round(E, 4)}}
    json.dump(tl, open(os.path.join(d, 'timeline.json'), 'w'), indent=1, ensure_ascii=False)
    return d, tl
def stills_helper(ws_d, assets, put, name, fname, credit, label, prov, size_cache={}):
    assets[name] = {'src': put(os.path.join(ST, fname)), 'kind': 'external_still', 'credit': credit, 'label': label, **prov}
def view(assets, ws_d, aid, c, w):
    with Image.open(os.path.join(ws_d, assets[aid]['src'])) as im: iw, ih = im.size
    w = min(w, 0.99, 0.99 * ih * 16 / 9 / iw); bw = w * iw; bh = bw * 9 / 16
    cx = min(max(c[0], bw / 2 / iw + 1e-4), 1 - bw / 2 / iw - 1e-4); cy = min(max(c[1], bh / 2 / ih + 1e-4), 1 - bh / 2 / ih - 1e-4)
    return {'center': [round(cx, 5), round(cy, 5)], 'width': round(w, 5)}
def opening(d, assets, put, rel, gfx, S, E):
    nasa = json.load(open(os.path.join(ST, 'nasa_provenance.json')))['svs3539']
    ls = lambda k: json.load(open(os.path.join(ST, f'{k}_toneB.json')))
    assets['bluemarble'] = {'src': put(os.path.join(ST, 'africa.0700.jpg')), 'kind': 'external_still', 'credit': bt.CRED['nasa_bm'], 'label': 'Blue Marble: Africa',
                            **{k: nasa[k] for k in ('source_url', 'license', 'retrieved', 'image_date')}, 'derived_from': 'SVS 3539 africa.0700.jpg'}
    r = ls('bodele'); assets['bodele'] = {'src': put(os.path.join(ST, 'bodele_toneB.png')), 'kind': 'external_still', 'credit': bt.CRED['landsat9'], 'label': 'Bodélé', 'source_url': r['source_url'], 'license': r['licence'], 'retrieved': r['retrieved'], 'image_date': r['date_acquired'], 'derived_from': r['scene']}
    assets['seq_s6'] = {'src': put(os.path.join(WS_ROOT, 'seq_s6.mp4')), 'kind': 'video', 'credit': 'Landsat 5, 9 · USGS (East Oweinat)'}
    def still(sid, beat, start, aid, v0, v1, labels=(), scrim=0.0):
        L = [{'type': 'still', 'asset': aid, 'view': {'from': view(assets, d, aid, *v0), 'to': view(assets, d, aid, *v1), 'ease': 'in_out'}, **({'scrim': scrim} if scrim else {})}]
        for lab in labels:
            x = {'type': 'label', 'text': lab['text'], 'style': lab.get('style', 'tag'), 'slot': lab.get('slot', 'upper'), 't': [rel(lab['t0']) - rel(start), rel(lab['t1']) - rel(start)]}
            if lab.get('sub'): x['sub'] = lab['sub']
            L.append(x)
        return {'id': sid, 'beat': beat, 'start': rel(start), 'layers': L}
    t = lambda i: bt.S(i); e = lambda i: bt.E(i)
    s = []
    s.append(still('o01', 'scene 1 (hook: the planet)', 0.0, 'bluemarble', ((0.5, 0.5), 0.99), ((0.42, 0.56), 0.74)))
    s.append({'id': 'o02', 'beat': 'scene 2 (230+ over the ground)', 'start': rel(t('2')), 'layers': gfx('r02-230', [t('2'), at('geological', t('2')), at('than 230', t('2'))], t('2'), 'Original graphic · sources on the image')})
    s.append(still('o03', 'scene 3', t('3'), 'bodele', ((0.30, 0.28), 0.55), ((0.45, 0.30), 0.42),
                   [{'text': 'THOUSANDS OF MILES AWAY', 't0': at('thousands of miles'), 't1': e('3')},
                    {'text': 'BODÉLÉ DEPRESSION, CHAD', 'sub': "ONE OF THE WORLD'S BIGGEST DUST SOURCES", 'slot': 'middle', 't0': at("part that's"), 't1': e('3')}], scrim=0.62))
    s.append(still('o04', 'scene 4', t('4'), 'bluemarble', ((0.5, 0.5), 0.90), ((0.36, 0.62), 0.62), [{'text': "WORLD'S LARGEST NON-POLAR DESERT", 't0': at("world's largest"), 't1': e('4')}]))
    s.append({'id': 'o05', 'beat': 'scene 5 (rain over a real landscape)', 'start': rel(t('5')), 'layers': gfx('r05-rain', [t('5'), at('few inches', t('5')), at('tens of', t('5'))], t('5'))})
    s.append({'id': 'o06', 'beat': 'scene 6', 'start': rel(WS_SEQ['s6']['start']), 'layers': [{'type': 'video', 'asset': 'seq_s6', 'credit': False, 'captions': True, 'caption': {'band': 0.76, 'center_x': 0.667, 'max_width': 1100}}]})
    return s
def proposal(d, assets, put, rel, gfx, S, E):
    t23 = bt.S('23')
    p2 = q(at('watered with', t23) - 0.3); p3 = at('by their estimate', t23); p4 = at('that estimate', t23); p5 = at("and it wasn't", t23)
    s = []
    s.append({'id': 'p1', 'beat': 'scene 23a: where (Sahara; Outback not on map)', 'start': 0.0, 'layers': gfx('r23a-sites', [t23, at('going much', t23), at('forests of', t23), at('across the sahara', t23), at('australian outback', t23)], t23)})
    s.append({'id': 'p2', 'beat': 'scene 23b: mechanism (conceptual)', 'start': rel(p2), 'layers': gfx('r23b-mechanism', [p2, at('watered with', t23), at('desalinated', t23), at('seawater', t23)], p2)})
    s.append({'id': 'p3', 'beat': 'scene 23c: the estimate (equivalence, no numbers)', 'start': rel(p3), 'layers': gfx('r23c-carbon', [p3, at('take up', t23), at('as much carbon', t23), at("world's fossil", t23)], p3)})
    s.append({'id': 'p4', 'beat': 'scene 23d: what the estimate is / is not', 'start': rel(p4), 'layers': gfx('r23d-estimate', [p4, at('plantation data', t23), at('calculations with', t23), at('not from a climate', t23)], p4)})
    s.append({'id': 'p5', 'beat': 'scene 23e: stops gaining carbon (schematic)', 'start': rel(p5), 'layers': gfx('r23e-century', [p5, at('stop gaining', t23), at('the authors themselves', t23)], p5)})
    return s
def main(ws, which):
    global WS_ROOT, WS_SEQ
    WS_ROOT = ws; WS_SEQ = json.load(open(os.path.join(ws, 'sequences.json')))
    out = {}
    for name in which or ('opening', 'proposal'):
        if name == 'opening': d, tl = build(ws, 'opening', 0.0, 30.0, opening)
        else: d, tl = build(ws, 'proposal', 357.167, 38.133, proposal, extra_frames=1)
        r = subprocess.run([sys.executable, RENDER, '--timeline', os.path.join(d, 'timeline.json'), '--output', os.path.join(d, name.upper() + '_REVISED_1080p30.mp4'), '--confirm', '--overwrite'], capture_output=True, text=True)
        try: res = json.loads(r.stdout)
        except Exception: res = {'status': 'error', 'raw': (r.stdout + r.stderr)[-600:]}
        print(name, res.get('status'), res.get('error', '')[:300], res.get('duration'), res.get('warnings')); out[name] = res
    return out
if __name__ == '__main__': main(sys.argv[1], sys.argv[2:])
