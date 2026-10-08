#!/usr/bin/env python3
"""EP001: render the East Oweinat / Toshka sequences from the REAL narration timings (cues.json) at 1920x1080, 30 fps.
Shot boundaries are snapped to the 30 fps grid (frame i = i/30 s) so every video frame lands on its timeline frame.
  python3 build_sequences.py WORKSPACE [name ...]     names: eo toshka s6 s22 s35 (default: all)"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'narration'))
import cues
FPS = 30
def q(t): return round(t * FPS) / FPS
def main(ws, names):
    os.makedirs(ws, exist_ok=True)
    units = json.load(open(os.path.join(ROOT, 'narration', 'cues.json')))['units']
    plan = {s['scene']: s for s in json.load(open(os.path.join(HERE, 'scene_plan.json')))['scenes'] if s['status'] == 'ok'}
    eo, to = cues.fit_eo(units), cues.fit_toshka(units)
    assert eo['fits'] and eo['scene19_start_shift_s'] <= 2.2
    def snap(sched):
        t0, t1 = q(sched['schedule'][0]['start']), q(sched['ends'])
        st = [dict(x) for x in sched['schedule']]; st[0]['start'] = t0; st[-1]['end'] = t1
        return {'schedule': st, 'clip_end': t1}
    eo_s, to_s = snap(eo), snap(to)
    s6, s22, s35 = plan['6'], plan['22'], plan['35']
    t22 = q(to['ends']); e22 = q(plan['22']['end'])
    custom = {
      's6': {'kind': 'dissolve', 'dur': round((q(s6['end']) - q(s6['start'])), 4), 't_d0': round(q(25.4) - q(s6['start']), 4), 'dissolve_s': 0.8, 'z_to': 0.5},
      's22': {'kind': 'close', 'dur': round(e22 - t22, 4), 'z_from': 1.0, 'z_to': 0.88},
      's35': {'kind': 'dissolve', 'dur': round(q(s35['end']) - q(s35['start']), 4), 't_d0': round(q(705.4) - q(s35['start']), 4), 'dissolve_s': 0.8, 'z_to': 0.3}}
    meta = {'eo': {'start': eo_s['schedule'][0]['start'], 'end': eo_s['clip_end']}, 'toshka': {'start': to_s['schedule'][0]['start'], 'end': to_s['clip_end']},
            's6': {'start': q(s6['start']), 'end': q(s6['end'])}, 's22': {'start': t22, 'end': e22}, 's35': {'start': q(s35['start']), 'end': q(s35['end'])},
            'fit_eo': eo_s, 'fit_toshka': to_s, 'custom': custom, 'scene19_start_shift_s': eo['scene19_start_shift_s']}
    json.dump(meta, open(os.path.join(ws, 'sequences.json'), 'w'), indent=1)
    VIS = os.path.join(ROOT, 'visuals', 'scripts', 'render.py')
    jobs = {'eo': ('eo-sched', eo_s), 'toshka': ('to-sched', to_s), 's6': ('eo-custom', custom['s6']), 's22': ('eo-custom', custom['s22']), 's35': ('eo-custom', custom['s35'])}
    for n in names or jobs:
        what, spec = jobs[n]
        sp = os.path.join(ws, f'spec_{n}.json'); json.dump(spec, open(sp, 'w'), indent=1)
        out = os.path.join(ws, f'seq_{n}.mp4')
        r = subprocess.run([sys.executable, '-I', VIS, what, '1.0', out, str(FPS), sp], capture_output=True, text=True)
        print(n, r.stdout.strip(), r.stderr.strip()[-300:], flush=True)
        assert r.returncode == 0
if __name__ == '__main__': main(sys.argv[1], sys.argv[2:])
