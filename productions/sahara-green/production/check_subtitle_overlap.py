#!/usr/bin/env python3
"""EP001 subtitle overlap check for a rendered section: does any burned-in caption box (renderer manifest) intersect meaningful on-screen information
that is visible while the cue is shown? Information = every text box of the graphic on screen (conservative: all steps of the graphic), the label layers
(position and size reproduced from compose.py), and the East Oweinat sequence's left info panel.
  python3 check_subtitle_overlap.py SECTION_DIR NAME      (NAME: opening | proposal)"""
import json, os, re, sys
from PIL import ImageFont
W, H = 1920, 1080
HERE = os.path.dirname(os.path.abspath(__file__)); GFX = os.path.join(HERE, 'graphics', 'out_revision')
FD = '/usr/share/fonts/opentype/inter/'
SLOTS = {'top': 0.16, 'upper': 0.27, 'middle': 0.4}; STYLES = {'year': (104, 'Black'), 'stat': (84, 'Black'), 'tag': (44, 'Bold'), 'sub': (34, 'SemiBold'), 'legend': (34, 'Bold')}
def tl(a, b): return a < b
def inter(a, b): return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
def label_rects(L):
    size, w = STYLES[L['style']]; y = int(H * SLOTS[L['slot']])
    f = ImageFont.truetype(f'{FD}Inter-{w}.otf', size)
    while f.getlength(L['text']) > W * 0.82 and size > 30: size -= 6; f = ImageFont.truetype(f'{FD}Inter-{w}.otf', size)
    tw = f.getlength(L['text']); r = [(W / 2 - tw / 2, y - size * 0.6, W / 2 + tw / 2, y + size * 0.6)]
    if L.get('sub'):
        f2 = ImageFont.truetype(f'{FD}Inter-SemiBold.otf', 34); sw = f2.getlength(L['sub']); sy = y + size // 2 + 30
        r.append((W / 2 - sw / 2, sy - 20, W / 2 + sw / 2, sy + 20))
    return r
def srt(path):
    out = []
    for b in re.split(r'\n\s*\n', open(path, encoding='utf-8').read().replace('\r\n', '\n').strip()):
        L = b.split('\n'); t = L[1].split(' --> ')
        f = lambda s: (lambda h, m, x: int(h) * 3600 + int(m) * 60 + float(x))(*s.replace(',', '.').split(':'))
        out.append((f(t[0]), f(t[1])))
    return out
def main(d, name):
    tlj = json.load(open(os.path.join(d, 'timeline.json'))); man = json.load(open(os.path.join(d, f'{name.upper()}_REVISED_1080p30.manifest.json')))
    cues = srt(os.path.join(d, 'captions', 'captions.srt')); shots = tlj['shots']; ends = [s['start'] for s in shots[1:]] + [tlj['end']['seconds']]
    res = {'section': name, 'cues': len(cues), 'caption_boxes': len(man['caption_boxes']), 'overlaps': [], 'checked_pairs': 0}
    for cb in man['caption_boxes']:
        a, b = cues[cb['cue'] - 1]; box = cb['box']
        for s, e in zip(shots, ends):
            if not (a < e and s['start'] < b): continue
            for L in s['layers']:
                lt = L.get('t'); t0 = s['start'] + (lt[0] if lt else 0); t1 = s['start'] + (lt[1] if lt and lt[1] is not None else 1e9)
                if not (a < min(t1, e) and max(t0, s['start']) < b): continue
                rects = []
                if L['type'] == 'graphic':
                    gid = tlj['assets'][L['asset']]['group']; rects = [(t['where'], t['box']) for t in json.load(open(os.path.join(GFX, gid + '.json')))['text_boxes']]
                elif L['type'] == 'label': rects = [('label ' + L['text'], r) for r in label_rects(L)]
                elif L['type'] == 'video' and L['asset'].startswith('seq_s') or L['asset'] == 'seq_eo' if L['type'] == 'video' else False: rects = [('East Oweinat info panel', (0, 0, 644, 1080))]
                for nm, r in rects:
                    res['checked_pairs'] += 1
                    if inter(box, r): res['overlaps'].append({'cue': cb['cue'], 'caption_box': box, 'shot': s['id'], 'element': nm, 'rect': [round(v) for v in r]})
    res['ok'] = not res['overlaps']; print(json.dumps({k: res[k] for k in ('section', 'cues', 'caption_boxes', 'checked_pairs', 'ok')}), res['overlaps'][:5]); return res
if __name__ == '__main__':
    out = main(sys.argv[1], sys.argv[2]); json.dump(out, open(os.path.join(sys.argv[1], 'subtitle_overlap.json'), 'w'), indent=1)
