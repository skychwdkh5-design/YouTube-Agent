#!/usr/bin/env python3
"""EP001 full-timeline subtitle overlap check: every burned-in caption box (renderer manifest) against all on-screen text of every graphic
(all build steps, conservative), label layers and the East Oweinat info panel, for the whole film.
  python3 check_subtitle_overlap_full.py TIMELINE.json MANIFEST.json CAPTIONS.srt OUT.json"""
import json, os, sys
import check_subtitle_overlap as c
HERE = os.path.dirname(os.path.abspath(__file__))
DIRS = [os.path.join(HERE, 'graphics', 'out_revision'), os.path.join(HERE, 'graphics', 'out')]
def gjson(gid):
    for d in DIRS:
        p = os.path.join(d, gid + '.json')
        if os.path.exists(p): return json.load(open(p))
    raise FileNotFoundError(gid)
def main(tl, man, srt, out):
    tlj = json.load(open(tl)); m = json.load(open(man)); cues = c.srt(srt)
    shots = tlj['shots']; ends = [s['start'] for s in shots[1:]] + [tlj['end']['seconds']]
    res = {'cues': len(cues), 'caption_boxes': len(m['caption_boxes']), 'overlaps': [], 'checked_pairs': 0, 'by_shot': {}}
    for cb in m['caption_boxes']:
        a, b = cues[cb['cue'] - 1]; box = cb['box']
        for s, e in zip(shots, ends):
            if min(b, e) - max(a, s['start']) < 1 / 30 - 1e-3: continue   # a cue that starts less than one frame before a cut is not on screen in the earlier shot
            for L in s['layers']:
                lt = L.get('t'); t0 = s['start'] + (lt[0] if lt else 0); t1 = s['start'] + (lt[1] if lt and lt[1] is not None else 1e9)
                if not (a < min(t1, e) and max(t0, s['start']) < b): continue
                rects = []
                if L['type'] == 'graphic': rects = [(t['where'], t['box']) for t in gjson(tlj['assets'][L['asset']]['group'])['text_boxes']]
                elif L['type'] == 'label': rects = [('label ' + L['text'], r) for r in c.label_rects(L)]
                elif L['type'] == 'video' and L['asset'] in ('seq_eo', 'seq_s6', 'seq_s35'): rects = [('East Oweinat info panel', (0, 0, 644, 1080))]
                elif L['type'] == 'video' and L['asset'] == 'seq_s22': rects = [('sequence date/info box', (1084, 896, 1840, 1010)), ('sequence scale bar', (80, 924, 246, 1006))]   # measured on frames of s22 (full-frame close-up; seq_eo/s6/s35 carry the left info panel)
                for nm, r in rects:
                    res['checked_pairs'] += 1; res['by_shot'][s['id']] = res['by_shot'].get(s['id'], 0) + 1
                    if c.inter(box, r): res['overlaps'].append({'cue': cb['cue'], 'caption_box': box, 'shot': s['id'], 'element': nm, 'rect': [round(v) for v in r]})
    res['ok'] = not res['overlaps']; json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('cues', 'caption_boxes', 'checked_pairs', 'ok')})); [print(o) for o in res['overlaps']]; return res
if __name__ == '__main__': main(*sys.argv[1:5])
