#!/usr/bin/env python3
"""EP001 dry run: can the two locked Landsat sequences be inserted into a long-profile timeline, driven by narration timings?

EVERYTHING TIMING-RELATED HERE IS SIMULATED. No narration audio exists yet. The 'narration' is a silent WAV whose word timings are
generated from the locked text at 145 words per minute; the metadata is flagged "simulated": true and the files are named *_SIMULATED.
A real run replaces narration_SIMULATED.* with the ElevenLabs output and re-runs `cues.py locate` and this script unchanged.

  python3 build_dry_run.py WORKSPACE      # WORKSPACE holds the large files (outside Git); writes timeline + report next to this script
Free: local ffmpeg only.
"""
import hashlib, json, os, subprocess, sys, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); NAR = os.path.dirname(HERE); ROOT = os.path.dirname(NAR); REPO = os.path.dirname(os.path.dirname(ROOT))
sys.path.insert(0, NAR)
import cues
FPS = 30
VIS = os.path.join(ROOT, 'visuals', 'scripts')
RENDER = os.path.join(REPO, '.claude', 'skills', 'yt-render', 'render.py')
CAPTIONS = os.path.join(REPO, '.claude', 'skills', 'yt-captions', 'captions.py')
QC = os.path.join(REPO, '.claude', 'skills', 'yt-qc', 'qc.py')
def sh(cmd, **kw):
    p = subprocess.run(cmd, capture_output=True, text=True, **kw)
    return p
def q(t): return round(t * FPS) / FPS                       # every shot boundary on a frame
def simulate(text, units, wpm=145.0):
    """Simulated word timings for the whole narration, calibrated to `wpm` overall (pauses at commas, sentence and paragraph ends)."""
    toks = text.split(); target = len(toks) / wpm * 60
    def build(f):
        t, out = 0.0, []
        for w in toks:
            d = (0.045 * len(w) + 0.09) * f; out.append({'text': w, 'start': round(t, 3), 'end': round(t + d, 3)}); t += d
            t += 0.18 if w[-1] in ',;:' else (0.5 if w[-1] in '.!?' else 0.04)
        return out, t
    lo, hi = 0.3, 3.0
    for _ in range(40):
        mid = (lo + hi) / 2; _, t = build(mid)
        lo, hi = (mid, hi) if t < target else (lo, mid)
    words, total = build((lo + hi) / 2)
    return words, total
def placeholder(path, line1, line2):
    im = Image.new('RGB', (1920, 1080), (30, 34, 40)); d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Medium.otf', 64); f2 = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Regular.otf', 36)
    d.text((960, 480), line1, font=f1, fill=(240, 240, 236), anchor='mm'); d.text((960, 580), line2, font=f2, fill=(246, 184, 70), anchor='mm'); im.save(path)
def psnr(a, b):
    mse = float(((a.astype(np.float64) - b.astype(np.float64)) ** 2).mean()); return 99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse)
def frames_at(path, idx, w, h):
    out = {}
    for i in idx:
        r = subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-i', path, '-vf', f'select=eq(n\\,{i}),scale={w}:{h}:flags=lanczos', '-vsync', '0', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)
        out[i] = np.frombuffer(r.stdout, np.uint8).reshape(h, w, 3) if len(r.stdout) == w * h * 3 else None
    return out
def main(ws):
    os.makedirs(ws, exist_ok=True)
    man = json.load(open(os.path.join(NAR, 'narration_manifest.json'))); text = open(os.path.join(NAR, 'narration_text.txt'), encoding='utf-8').read()
    words, total = simulate(text, man['units']); units = cues.locate(words, man['units'])
    eo, to = cues.fit_eo(units), cues.fit_toshka(units)
    W0 = q(units['S046']['start'] - 1.0)
    # shot boundaries on frame boundaries, in window time
    t_eo, t_eo_end = q(units['S047']['start'] - W0), q(eo['ends'] - W0)
    t_to, t_to_end = q(units['S055']['start'] - W0), q(to['ends'] - W0)
    t_end = q(t_to_end + 4.0)
    for a, b, n in ((t_eo, t_eo_end, 'East Oweinat'), (t_eo_end, t_to, 'mid'), (t_to, t_to_end, 'Toshka'), (t_to_end, t_end, 'tail')):
        assert b > a + 0.5, f'{n} shot too short'
    def shift(sched, end):
        steps = [dict(s, start=round(s['start'] - W0, 3), end=round(s['end'] - W0, 3)) for s in sched['schedule']]
        steps[0]['start'] = t_eo if n_is_eo(sched) else t_to
        return {'schedule': steps, 'clip_end': end}
    def n_is_eo(s): return s['schedule'][0]['step'] == '1984 hold'
    eo_s, to_s = shift(eo, t_eo_end), shift(to, t_to_end)
    json.dump(eo_s, open(os.path.join(ws, 'sched_eo_SIMULATED.json'), 'w'), indent=1); json.dump(to_s, open(os.path.join(ws, 'sched_toshka_SIMULATED.json'), 'w'), indent=1)
    # simulated narration for the window: silent audio, shifted words
    win_words = [{'text': w['text'], 'start': round(w['start'] - W0, 3), 'end': round(w['end'] - W0, 3)} for w in words if w['end'] > W0 and w['start'] - W0 < t_end]
    win_words = [w for w in win_words if w['start'] >= 0 and w['end'] <= t_end - 0.05]
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-t', f'{t_end:.3f}', '-c:a', 'pcm_s16le', os.path.join(ws, 'narration_SIMULATED.wav')], check=True)
    sha = hashlib.sha256(open(os.path.join(ws, 'narration_SIMULATED.wav'), 'rb').read()).hexdigest()
    json.dump({'schema': 'yt-voice/1', 'simulated': True, 'provider': 'SIMULATED (silent audio, timings generated at 145 wpm; not a TTS result)', 'voice_name': None, 'voice_id': None,
               'audio': 'narration_SIMULATED.wav', 'audio_sha256': sha, 'duration': round(t_end, 3), 'timing': {'source': 'simulated', 'unit': 'seconds', 'level': 'word'}, 'words': win_words,
               'window': {'narration_start_offset_s': W0, 'first_unit': 'S046', 'last_unit': 'S058'}},
              open(os.path.join(ws, 'narration_SIMULATED.voice.json'), 'w'), indent=1)
    os.makedirs(os.path.join(ws, 'captions_SIMULATED'), exist_ok=True)
    r = sh([sys.executable, CAPTIONS, '--voice', os.path.join(ws, 'narration_SIMULATED.voice.json'), '--out-dir', os.path.join(ws, 'captions_SIMULATED'), '--overwrite']); assert r.returncode == 0, r.stdout + r.stderr
    # sequences at 720p / 30 fps (review size; the final render uses the same script at --scale 2) and placeholders
    seq = {}
    for name, what, sched in (('eo', 'eo-sched', 'sched_eo_SIMULATED.json'), ('toshka', 'to-sched', 'sched_toshka_SIMULATED.json')):
        out = os.path.join(ws, f'seq_{name}_SIMULATED_720p.mp4')
        r = sh([sys.executable, '-I', os.path.join(VIS, 'render.py'), what, '0.6667', out, str(FPS), os.path.join(ws, sched)], cwd=os.path.join(ws))
        assert r.returncode == 0, r.stdout + r.stderr
        seq[name] = out
    for n, (a, b) in {'pre': ('PLACEHOLDER: scene 17', 'simulated timing'), 'mid': ('PLACEHOLDER: scenes 19-20 (aquifer, Kufra)', 'simulated timing'), 'tail': ('PLACEHOLDER: next scene', 'simulated timing')}.items():
        placeholder(os.path.join(ws, f'ph_{n}.png'), a, b)
    json.dump({'schema': 'yt-geo-stack/1', 'epsg': 32635, 'x0': 600000.0, 'y_top': 2600000.0, 'pixel_m': 30.0, 'width': 100, 'height': 100}, open(os.path.join(ws, 'grid.json'), 'w'))
    capEO = {'band': 0.76, 'center_x': 0.667, 'max_width': 1100}; capTO = {'band': 0.76}
    def timeline(captions):
        shots = [{'id': 'pre', 'start': 0, 'layers': [{'type': 'graphic', 'asset': 'ph_pre'}]},
                 {'id': 'east_oweinat', 'beat': 'scene 18', 'start': t_eo, 'layers': [{'type': 'video', 'asset': 'seq_eo', 'credit': False, 'captions': captions, 'caption': capEO}]},
                 {'id': 'mid', 'start': t_eo_end, 'layers': [{'type': 'graphic', 'asset': 'ph_mid'}]},
                 {'id': 'toshka', 'beat': 'scene 21', 'start': t_to, 'layers': [{'type': 'video', 'asset': 'seq_toshka', 'credit': False, 'captions': captions, 'caption': capTO}]},
                 {'id': 'tail', 'start': t_to_end, 'layers': [{'type': 'graphic', 'asset': 'ph_tail'}]}]
        tl = {'version': 3, 'profile': 'long', 'grid': 'grid.json', 'shots': shots,
              'assets': {**{f'ph_{n}': {'src': f'ph_{n}.png', 'kind': 'graphic', 'credit': 'Placeholder (simulated timing)'} for n in ('pre', 'mid', 'tail')},
                         'seq_eo': {'src': 'seq_eo_SIMULATED_720p.mp4', 'kind': 'video', 'credit': 'Landsat 5, 8, 9 / USGS (locked sequence, 720p review render)'},
                         'seq_toshka': {'src': 'seq_toshka_SIMULATED_720p.mp4', 'kind': 'video', 'credit': 'Landsat 5, 8 / USGS (locked sequence, 720p review render)'}},
              'voice': {'src': 'narration_SIMULATED.wav', 'meta': 'narration_SIMULATED.voice.json', 'normalize': False},
              'end': {'seconds': t_end}, 'render': {'segment_s': 30}, 'meta': {'SIMULATED': 'narration timings are simulated; replace narration_SIMULATED.* with the real narration'}}
        if captions: tl['captions'] = {'src': 'captions_SIMULATED/captions.srt', 'preset': 'default'}
        return tl
    rep = {'SIMULATED': True, 'window': {'start_offset_s': W0, 'duration_s': t_end}, 'simulated_pace_wpm': 145, 'full_narration_simulated_s': round(total, 1),
           'shots': {'pre': [0, t_eo], 'east_oweinat': [t_eo, t_eo_end], 'mid': [t_eo_end, t_to], 'toshka': [t_to, t_to_end], 'tail': [t_to_end, t_end]},
           'fit_east_oweinat': eo_s, 'fit_toshka': to_s}
    # 1) no captions: pixel check that the sequences land on the exact frames
    json.dump(timeline(False), open(os.path.join(ws, 'timeline_nocap.json'), 'w'), indent=1)
    r = sh([sys.executable, RENDER, '--timeline', os.path.join(ws, 'timeline_nocap.json'), '--output', os.path.join(ws, 'dry_nocap.mp4'), '--confirm', '--overwrite']); res = json.loads(r.stdout); assert res['status'] == 'ok', res
    rep['render_nocaptions'] = {k: res[k] for k in ('duration', 'expected_duration', 'segments', 'composition_resets', 'warnings')}
    checks = []
    for name, (a, b) in (('seq_eo', (t_eo, t_eo_end)), ('seq_toshka', (t_to, t_to_end))):
        f0, f1 = round(a * FPS), round(b * FPS); n = f1 - f0
        pick = sorted({0, 1, 2, n // 3, n // 2, n - 3, n - 2, n - 1})
        src = frames_at(seq[name.replace('seq_', '')], pick, 1920, 1080)
        out = frames_at(os.path.join(ws, 'dry_nocap.mp4'), [f0 + k + d for k in pick for d in (-1, 0, 1)], 1920, 1080)
        for k in pick:
            ps = {d: psnr(src[k], out[f0 + k + d]) for d in (-1, 0, 1) if out.get(f0 + k + d) is not None and src[k] is not None}
            best = max(ps, key=ps.get)
            checks.append({'sequence': name, 'frame': k, 'psnr_same_frame_db': round(ps[0], 2), 'psnr_prev_db': round(ps.get(-1, 0), 2), 'psnr_next_db': round(ps.get(1, 0), 2), 'best_offset': best, 'ok': best == 0 and ps[0] > 30})
    rep['frame_accuracy'] = {'checked_frames': len(checks), 'all_best_offset_zero': all(c['best_offset'] == 0 for c in checks), 'checks': checks}
    # 2) with captions: collisions between caption boxes and the sequences' own UI
    tl = timeline(True); json.dump(tl, open(os.path.join(ws, 'timeline.json'), 'w'), indent=1)
    r = sh([sys.executable, RENDER, '--timeline', os.path.join(ws, 'timeline.json'), '--output', os.path.join(ws, 'dry_run_SIMULATED.mp4'), '--confirm', '--overwrite']); res = json.loads(r.stdout); assert res['status'] == 'ok', res
    man_r = json.load(open(os.path.join(ws, 'dry_run_SIMULATED.manifest.json')))
    rep['render'] = {k: res[k] for k in ('duration', 'expected_duration', 'segments', 'composition_resets', 'warnings')}
    srt = open(os.path.join(ws, 'captions_SIMULATED', 'captions.srt'), encoding='utf-8').read().replace('\r\n', '\n').strip().split('\n\n')
    def tsec(s): h, m, x = s.replace(',', '.').split(':'); return int(h) * 3600 + int(m) * 60 + float(x)
    cues_t = [(tsec(b.split('\n')[1].split(' --> ')[0]), tsec(b.split('\n')[1].split(' --> ')[1])) for b in srt]
    UI = {'toshka': [(74, 56, 880, 310), (942, 56, 1786, 196), (82, 924, 448, 1010), (1100, 920, 1838, 1010)],
          'east_oweinat_panel': [(0, 0, 644, 1080)], 'east_oweinat_zoom': [(82, 924, 330, 1010), (1084, 896, 1838, 1010)]}
    coll = []
    for cb in man_r['caption_boxes']:
        t0, t1 = cues_t[cb['cue'] - 1]; x0, y0, x1, y1 = cb['box']
        for shot, (a, b) in (('toshka', rep['shots']['toshka']), ('east_oweinat_panel', (rep['shots']['east_oweinat'][0], rep['shots']['east_oweinat'][0] + sum(s['end'] - s['start'] for s in eo_s['schedule'] if 'zoom' not in s['step']))), ('east_oweinat_zoom', (rep['shots']['east_oweinat'][1] - 8, rep['shots']['east_oweinat'][1]))):
            if t1 > a and t0 < b:
                for (u0, v0, u1, v1) in UI[shot]:
                    if x0 < u1 and x1 > u0 and y0 < v1 and y1 > v0: coll.append({'cue': cb['cue'], 'shot': shot, 'caption_box': cb['box'], 'ui_rect': [u0, v0, u1, v1]})
    rep['caption_collisions'] = {'count': len(coll), 'items': coll[:10], 'captions_in_sequence_shots': sum(1 for cb in man_r['caption_boxes'] if any(cues_t[cb['cue'] - 1][1] > a and cues_t[cb['cue'] - 1][0] < b for a, b in (rep['shots']['east_oweinat'], rep['shots']['toshka'])))}
    qc = sh([sys.executable, QC, os.path.join(ws, 'dry_run_SIMULATED.mp4'), '--profile', 'long', '--manifest', os.path.join(ws, 'dry_run_SIMULATED.manifest.json')]) if os.path.exists(QC) else None
    try: rep['yt_qc'] = json.loads(qc.stdout) if qc else None
    except Exception: rep['yt_qc'] = {'raw': (qc.stdout + qc.stderr)[:400]} if qc else None
    json.dump(tl, open(os.path.join(HERE, 'timeline_dry_run_SIMULATED.json'), 'w'), indent=1)
    json.dump(rep, open(os.path.join(HERE, 'dry_run_report.json'), 'w'), indent=1)
    print(json.dumps({k: rep[k] for k in ('SIMULATED', 'shots', 'render', 'caption_collisions')}, indent=1)); print('frame accuracy', rep['frame_accuracy']['checked_frames'], rep['frame_accuracy']['all_best_offset_zero'])
if __name__ == '__main__': main(sys.argv[1])
