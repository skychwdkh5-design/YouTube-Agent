#!/usr/bin/env python3
"""EP001 narration -> visual timing. The narration audio is the master clock; nothing here guesses a time.

  python3 cues.py verify  voice/narration.voice.json   # spoken words in the provider alignment == narration_text.txt, word for word
  python3 cues.py locate  voice/narration.voice.json   # writes cues.json: start/end seconds of every sentence unit (S001..S120)
  python3 cues.py fit     cues.json                    # schedules for the East Oweinat and Toshka sequences from those cues (or an error with the shortfall)

Frame i of a final render is drawn at i / fps (30 fps policy), so cue times map to frames without drift.
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
D = 0.8                      # dissolve length (s), fixed by the visual lock
EO = {'lead': 0.25, 'hold_min': 0.7, 'hold_pref': 0.9, 'hold_max': 1.5, 'zoom_min': 3.5, 'zoom_max': 6.0, 'tail_into_next_max': 2.6}
TO = {'cue_offset': 0.3, 'end_pad': 1.0}
def tok(s): return re.findall(r"\S+", s)
def norm(w): return re.sub(r'[^\w]', '', w.lower())
def verify(words, text):
    a, b = [norm(w['text']) for w in words], [norm(w) for w in tok(text)]
    if a != b:
        i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        raise ValueError(f'alignment words differ from the narration text at word {i}: {a[i:i+3]} vs {b[i:i+3]} (lengths {len(a)} vs {len(b)})')
    return True
def locate(words, units):
    """Map every sentence unit to (start, end) seconds by consuming the aligned words in order."""
    out, i = {}, 0
    for u in units:
        n = len(tok(u['text'])); seg = words[i:i + n]
        if len(seg) != n or [norm(w['text']) for w in seg] != [norm(w) for w in tok(u['text'])]: raise ValueError(f"unit {u['id']} does not match the aligned words at index {i}")
        out[u['id']] = {'start': seg[0]['start'], 'end': seg[-1]['end']}; i += n
    if i != len(words): raise ValueError('aligned words left over after the last unit')
    return out
def fit_eo(c, p=EO):
    """East Oweinat: 1984 from the start of S047 until the lead before S049; then 2000, 2010, 2016, 2024 with 0.8 s dissolves and a zoom that may run
    into the start of S050 (scene 19) by at most tail_into_next_max. Returns the schedule or raises with the shortfall."""
    t0, t1, t_end = c['S047']['start'], c['S049']['start'] - p['lead'], c['S049']['end'] + p['tail_into_next_max']
    if 'S050' in c: t_end = min(t_end, c['S050']['end'])          # the zoom never runs past the end of S050 ("The water comes from below.")
    A = t_end - t1; need_min = 4 * D + 3 * p['hold_min'] + p['zoom_min']
    if A < need_min: raise ValueError(f'East Oweinat window too short by {need_min - A:.2f} s (have {A:.2f} s, need {need_min:.2f} s): extend the scene or drop a frame')
    Z = min(p['zoom_max'], max(p['zoom_min'], A - 4 * D - 3 * p['hold_pref'])); H = min(p['hold_max'], (A - 4 * D - Z) / 3)
    seq, t = [('1984 hold', t0, t1)], t1
    for y in ('2000', '2010', '2016'):
        seq += [(f'dissolve to {y}', t, t + D)]; t += D; seq += [(f'{y} hold', t, t + H)]; t += H
    seq += [('dissolve to 2024', t, t + D)]; t += D; seq += [('zoom into circles', t, t + Z)]; t += Z
    return {'schedule': [{'step': s, 'start': round(a, 3), 'end': round(b, 3)} for s, a, b in seq], 'hold_s': round(H, 3), 'zoom_s': round(Z, 3), 'ends': round(t, 3), 'window_end_limit': round(t_end, 3), 'fits': t <= t_end + 1e-6}
def fit_toshka(c, p=TO):
    """Toshka: 1999 from the start of S055; 2002 fully in at S056 (+offset), 2011 at S057, 2021 at S058; 2021 holds to the end of S058 + pad."""
    t0 = c['S055']['start']; cuts = [('2002', c['S056']['start']), ('2011', c['S057']['start']), ('2021', c['S058']['start'])]
    seq, prev_end = [], t0
    for y, s in cuts:
        a, b = s + p['cue_offset'] - D, s + p['cue_offset']
        if a < prev_end + 0.5: raise ValueError(f'Toshka: previous frame would be on screen only {a - prev_end:.2f} s before the dissolve to {y}')
        seq += [{'step': f'hold before {y}', 'start': round(prev_end, 3), 'end': round(a, 3)}, {'step': f'dissolve to {y}', 'start': round(a, 3), 'end': round(b, 3)}]; prev_end = b
    seq.append({'step': '2021 hold', 'start': round(prev_end, 3), 'end': round(c['S058']['end'] + p['end_pad'], 3)})
    return {'schedule': seq, 'ends': seq[-1]['end']}
if __name__ == '__main__':
    cmd = sys.argv[1]; man = json.load(open(os.path.join(HERE, 'narration_manifest.json'))); text = open(os.path.join(HERE, 'narration_text.txt'), encoding='utf-8').read()
    if cmd == 'verify': words = json.load(open(sys.argv[2]))['words']; print(json.dumps({'ok': verify(words, text), 'words': len(words)}))
    elif cmd == 'locate':
        d = json.load(open(sys.argv[2])); verify(d['words'], text); c = locate(d['words'], man['units']); json.dump({'duration': d['duration'], 'units': c}, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1); print(f'cues.json: {len(c)} units')
    elif cmd == 'fit':
        c = json.load(open(sys.argv[2]))['units']; print(json.dumps({'east_oweinat': fit_eo(c), 'toshka': fit_toshka(c)}, indent=1))
