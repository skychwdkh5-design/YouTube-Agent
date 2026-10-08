#!/usr/bin/env python3
"""EP001 timing QC: every pre-rendered video shot (sequences, CALIPSO) lands on exactly its frames in the review master.
PSNR between the source clip frame and the master frame at the expected index and at +-1 (rows without captions/labels only);
inside static holds neighbours tie, so first/last frame are also checked against the frame just outside the shot.
  python3 check_frame_accuracy.py WORKSPACE"""
import json, subprocess, sys, os
import numpy as np
FPS = 30
def frame(path, n, w=1920, h=1080):
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{n / FPS + 0.002:.4f}', '-i', path, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)   # input seek to the start of frame n (frame-exact decode)
    return np.frombuffer(r.stdout, np.uint8).reshape(h, w, 3) if len(r.stdout) == w * h * 3 else None
def frame_src(path, n, w=1920, h=1080):
    """frame n of a short source clip by decoded frame count (exact, independent of container time offsets)"""
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', path, '-vf', f'select=eq(n\\,{n})', '-vsync', '0', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(h, w, 3) if len(r.stdout) == w * h * 3 else None
def frames_multi(path, idx, w=1920, h=1080):
    """decoded frames idx of a long file in ONE pass (select by frame count; no seeking)"""
    idx = sorted(set(i for i in idx if i >= 0)); expr = '+'.join(f'eq(n\\,{i})' for i in idx)
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', path, '-vf', f"select='{expr}'", '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)
    n = len(r.stdout) // (w * h * 3); arr = np.frombuffer(r.stdout[:n * w * h * 3], np.uint8).reshape(n, h, w, 3)
    return {i: arr[j] for j, i in enumerate(idx[:n])}
def psnr(a, b, rows):
    if a is None or b is None: return 0.0                       # a missing frame never counts as a match
    a, b = a[rows[0]:rows[1]].astype(np.float64), b[rows[0]:rows[1]].astype(np.float64); m = ((a - b) ** 2).mean()
    return 99.0 if m == 0 else 10 * np.log10(255 ** 2 / m)
def main(ws):
    tl = json.load(open(os.path.join(ws, 'timeline.json'))); master = os.path.join(ws, 'EP001_review_master_1080p30.mp4')
    shots = tl['shots']; ends = [s['start'] for s in shots[1:]] + [tl['end']['seconds']]
    out = []
    for s, e in zip(shots, ends):
        L = s['layers'][0]
        if L['type'] != 'video': continue
        src = os.path.join(ws, tl['assets'][L['asset']]['src']); f0 = round(s['start'] * FPS); n = round(e * FPS) - f0; k0 = round(L.get('trim', 0) * FPS)
        rows = (520, 1000) if L['asset'] == 'calipso' else (0, 700)
        res = {'shot': s['id'], 'asset': L['asset'], 'frames': n, 'checks': []}
        ks = sorted({0, 1, n // 2, n - 2, n - 1})
        M = frames_multi(master, [f0 + k + d for k in ks for d in (-1, 0, 1)] + [f0 - 1, f0 + n])
        for k in ks:
            a = frame_src(src, k0 + k); b = {d: M.get(f0 + k + d) for d in (-1, 0, 1)}
            ps = {d: (psnr(a, b[d], rows) if b[d] is not None and a is not None else 0) for d in (-1, 0, 1)}
            ok = ps[0] > 30 and ps[0] >= max(ps[-1], ps[1]) - 0.1
            res['checks'].append({'k': k, 'psnr0': round(float(ps[0]), 1), 'psnr_prev': round(float(ps[-1]), 1), 'psnr_next': round(float(ps[1]), 1), 'ok': bool(ok)})
        a0, a1 = frame_src(src, k0), frame_src(src, k0 + n - 1)
        pre, post = M.get(f0 - 1), M.get(f0 + n)
        res['source_frames_readable'] = bool(a0 is not None and a1 is not None); res['first_not_previous'] = bool(f0 == 0 or psnr(a0, pre, rows) < 25); res['last_not_next'] = bool(post is None or psnr(a1, post, rows) < 25)
        res['ok'] = res['source_frames_readable'] and all(c['ok'] for c in res['checks']) and res['first_not_previous'] and res['last_not_next']
        out.append(res); print(res['shot'], res['asset'], 'OK' if res['ok'] else 'FAIL', [c['psnr0'] for c in res['checks']], flush=True)
    json.dump({'shots': out, 'all_ok': all(r['ok'] for r in out)}, open(os.path.join(ws, 'frame_accuracy.json'), 'w'), indent=1)
    print('ALL OK' if all(r['ok'] for r in out) else 'SOME FAILED')
if __name__ == '__main__': main(sys.argv[1])
