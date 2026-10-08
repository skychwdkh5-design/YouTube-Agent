#!/usr/bin/env python3
"""EP001: storyboard scenes -> real narration timing. Anchors are the quoted first words of each storyboard row, matched word by word
against the real ElevenLabs word timings (voice/narration.voice.json). Nothing is estimated. Free, offline."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); NAR = os.path.join(ROOT, 'narration')
words = json.load(open(os.path.join(NAR, 'voice', 'narration.voice.json')))['words']; DUR = json.load(open(os.path.join(NAR, 'voice', 'narration.voice.json')))['duration']
man = json.load(open(os.path.join(NAR, 'narration_manifest.json'))); units = man['units']
norm = lambda w: re.sub(r"[^\w]", '', w.lower())
W = [norm(w['text']) for w in words]
# unit -> first word index
uidx, i = {}, 0
for u in units: uidx[u['id']] = (i, i + len(u['text'].split()) - 1); i += len(u['text'].split())
rows = []
for l in open(os.path.join(ROOT, 'storyboard.md'), encoding='utf-8'):
    if not l.startswith('|'): continue
    c = [x.strip() for x in l.strip().strip('|').split('|')]
    m = re.fullmatch(r'(~~)?(\d+[a-z]?)(~~)?', c[0]) if c else None
    if not m or len(c) < 7: continue
    struck = bool(m.group(1)) or c[1].startswith('~~') or c[2].startswith('~~')
    rows.append({'scene': m.group(2), 'old_time': c[1], 'first_words': c[2], 'family': c[3], 'visual': c[4], 'labels': c[5], 'source': c[6], 'struck': struck})
def find(phrase, start):
    toks = [norm(t) for t in re.sub(r'[“”"…]', ' ', phrase).split() if norm(t)][:5]
    if not toks: return None
    for i in range(start, len(W) - len(toks)):
        if W[i:i + len(toks)] == toks: return i
    return None
# storyboard first-words that do not occur verbatim in SCRIPT LOCK v1.1 (the storyboard predates later script rounds): anchor on the locked sentence that starts the same beat
OVERRIDE = {'14': "And it's not a one-time event.", '30': 'Where does it come from?', '31': "So here's the open question."}
scenes, pos = [], 0
for r in rows:
    if r['struck'] or r['family'].startswith('~~') or r['old_time'].startswith('~~'):
        scenes.append({**r, 'status': 'removed (struck through in the storyboard)'}); continue
    k = find(OVERRIDE.get(r['scene'], r['first_words']), pos)
    r['anchor_used'] = OVERRIDE.get(r['scene'], r['first_words'])
    if k is None: scenes.append({**r, 'status': 'ANCHOR NOT FOUND'}); continue
    scenes.append({**r, 'status': 'ok', 'word_index': k, 'start': words[k]['start']}); pos = k
active = [s for s in scenes if s['status'] == 'ok']
for a, b in zip(active, active[1:] + [None]):
    a['end'] = b['start'] if b else DUR
    a['duration'] = round(a['end'] - a['start'], 3)
    w0 = a['word_index']; w1 = (b['word_index'] if b else len(words)) - 1
    a['units'] = [u for u, (x, y) in uidx.items() if x <= w1 and y >= w0]
    a['words'] = w1 - w0 + 1
for s in active: s['start'] = round(s['start'], 3); s['end'] = round(s['end'], 3)
out = {'narration_duration_s': DUR, 'scenes': scenes, 'active_scenes': len(active), 'removed': [s['scene'] for s in scenes if s['status'].startswith('removed')], 'not_found': [s['scene'] for s in scenes if s['status'] == 'ANCHOR NOT FOUND']}
json.dump(out, open(os.path.join(HERE, 'scene_plan.json'), 'w'), indent=1, ensure_ascii=False)
print(f"{len(active)} active scenes, removed {out['removed']}, anchors not found {out['not_found']}")
for s in active: print(f"{s['scene']:>4} {s['start']:7.1f}-{s['end']:7.1f} {s['duration']:6.1f}s  old {s['old_time']:11s} {s['family'][:26]:26s} {s['units'][0]}-{s['units'][-1]}")
