"""EP002 preview QA (TECHNICALLY_VALID checks only), frame-rate-conversion aware.
Why: orbitalatlas.qa resamples to 30 fps before measuring, which turns a 12 fps render into runs of identical frames and makes every move look like a
'discontinuity with local median 0'. This tool decodes at the file's NATIVE rate, collapses exact duplicate frames, and then separates
  - intentional duplication (regular run lengths, e.g. 12 -> 30 fps conversion; reported as info, never a defect),
  - freezes (a unique frame held much longer than the typical hold; flagged unless inside a declared static window),
  - jumps (frame-to-frame change per elapsed frame >> the local median of unique-frame changes; declared cuts are excluded).
Usage: python3 qa_preview.py VIDEO [--expect 960x540@24] [--src-fps 12] [--json OUT.json] [--md OUT.md]"""
import sys, os, json, subprocess, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def probe(path):
    r = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name,profile,width,height,r_frame_rate,avg_frame_rate,nb_frames,duration,pix_fmt,bit_rate:format=size,format_name', '-of', 'json', path]))
    s = r['streams'][0]; n, d = map(int, s['r_frame_rate'].split('/')); s['fps'] = n / d; s['size'] = int(r['format']['size']); return s

def read_gray(path, w=160, h=90):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'scale={w}:{h},format=gray', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE); n = w * h; prev = None; out = []
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        f = np.frombuffer(b, np.uint8).astype(np.float32)
        out.append(0.0 if prev is None else float(np.abs(f - prev).mean()) / 255.0); prev = f
    p.wait(); return np.array(out)

def analyse(diff, fps, eps=3e-5, jump_floor=0.06, jump_ratio=8.0, win=24, cuts=(), static_windows=(), move_windows=(), max_freeze_s=1.0):
    n = len(diff); uniq = np.nonzero(diff > eps)[0]; uniq = np.r_[0, uniq] if len(uniq) == 0 or uniq[0] != 0 else uniq
    gaps = np.diff(np.r_[uniq, n]); med_gap = float(np.median(gaps)) if len(gaps) else 1.0
    dup_runs = gaps[gaps > 1] - 1; dup_ratio = 1 - len(uniq) / n
    regular = bool(len(gaps) > 20 and np.percentile(gaps, 90) <= 3 * max(med_gap, 1) and dup_ratio > 0.2)
    issues = []; cut_frames = set(int(round(c * fps)) + k for c in cuts for k in (-1, 0, 1)); static = lambda i: any(a <= i / fps < b for a, b in static_windows)
    for u, g in zip(uniq, gaps):                                                    # freezes: a unique frame held far longer than the typical hold
        if g / fps > max_freeze_s and g > 3 * med_gap and not static(u): issues.append(dict(check='freeze', t=round(u / fps, 3), detail=f'{g} identical frames ({g / fps:.2f} s)'))
    per = np.zeros(n); per[uniq] = diff[uniq] / np.r_[gaps[:-1], gaps[-1:]][:len(uniq)] if False else 0
    d_u = np.array([diff[u] / max(1, (u - uniq[k - 1])) if k else 0 for k, u in enumerate(uniq)])      # change per elapsed frame
    for k, u in enumerate(uniq):
        if k < 2 or u in cut_frames or any(abs(u - c) <= 1 for c in cut_frames) or any(a <= u / fps < b for a, b in move_windows): continue
        lo, hi = max(0, k - win), min(len(uniq), k + win); ref = np.delete(d_u[lo:hi], k - lo); m = float(np.median(ref[ref > 0])) if (ref > 0).any() else 0.0
        if d_u[k] > max(jump_floor, jump_ratio * m): issues.append(dict(check='jump', t=round(u / fps, 3), detail=f'change {d_u[k]:.3f} per frame vs local median {m:.4f}'))
    return dict(frames=n, unique_frames=int(len(uniq)), duplicate_ratio=round(dup_ratio, 3), regular_duplication=regular, median_hold_frames=med_gap, issues=issues)

def scene_table(diff, fps, scenes, static_windows):
    rows = []
    for sid, start, dur, _, _ in scenes:
        a, b = int(start * fps), min(int((start + dur) * fps), len(diff)); d = diff[a + 1:b]; still = d <= 3e-5; run = best = 0
        for s in still: run = run + 1 if s else 0; best = max(best, run)
        mean = float(d.mean()) if len(d) else 0.0; rows.append(dict(scene=sid, start=start, dur=dur, mean_motion=round(mean, 4), max_change=round(float(d.max()) if len(d) else 0, 3), longest_still_s=round(best / fps, 2),
                                                                  note='WARN still > 3 s' if best / fps > 3 else ('LOW motion (< 0.002)' if mean < 0.002 else 'ok')))
    return rows

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--expect'); ap.add_argument('--src-fps', type=float); ap.add_argument('--json'); ap.add_argument('--md'); a = ap.parse_args()
    import scenes as S
    pr = probe(a.video); res = dict(probe=pr, problems=[])
    if a.expect:
        wh, f = a.expect.split('@'); w, h = map(int, wh.split('x'))
        for k, got, want in (('width', pr['width'], w), ('height', pr['height'], h), ('fps', round(pr['fps'], 3), float(f))):
            if got != want: res['problems'].append(f'{k}: expected {want}, file has {got}')
    dec = subprocess.run(['ffmpeg', '-v', 'error', '-i', a.video, '-f', 'null', '-'], capture_output=True, text=True); res['decode_errors'] = dec.stderr.strip()[:300]
    bl = subprocess.run(['ffmpeg', '-i', a.video, '-vf', 'blackdetect=d=0.15:pix_th=0.06', '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr
    res['black_segments'] = [l.split('black_start:')[1].split()[0] for l in bl.splitlines() if 'black_start' in l]
    diff = read_gray(a.video); fps = pr['fps']
    cuts = [s[1] for s in S.SCENES[1:]] + [s[1] + x for s in S.SCENES for x in getattr(S, 'INTRA_CUTS', {}).get(s[0], [])]
    static = [(s[1] + a0, s[1] + b0) for s in S.SCENES for a0, b0 in getattr(S, 'STATIC_WINDOWS', {}).get(s[0], [])]
    moves = [(s[1] + a0, s[1] + b0) for s in S.SCENES for a0, b0 in getattr(S, 'MOVE_WINDOWS', {}).get(s[0], [])]
    res['analysis'] = analyse(diff, fps, cuts=cuts, static_windows=static, move_windows=moves); res['scenes'] = scene_table(diff, fps, S.SCENES, static)
    res['verdict'] = 'TECHNICALLY_VALID' if not (res['problems'] or res['decode_errors'] or res['black_segments'] or res['analysis']['issues']) else 'ISSUES'
    if a.json: json.dump(res, open(a.json, 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'scenes'}, indent=1)[:2500])
    if a.md:
        L = ['| scene | start s | dur s | mean motion | max change | longest still s | note |', '|---|---|---|---|---|---|---|'] + [f"| {r['scene']} | {r['start']} | {r['dur']} | {r['mean_motion']} | {r['max_change']} | {r['longest_still_s']} | {r['note']} |" for r in res['scenes']]
        open(a.md, 'w').write('\n'.join(L) + '\n')
