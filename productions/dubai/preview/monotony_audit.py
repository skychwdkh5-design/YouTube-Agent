"""Cheap monotony audit of every scene (no video render): samples N frames per scene, reports mean frame-to-frame change (motion), the share of near-static
samples and the number of distinct compositions. Flags: LOW_MOTION (mean change < 3.0) and CARD (text-card base). Usage: python3 monotony_audit.py [--n 14] [--skip A1]"""
import sys, os, json, argparse, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenes as S
from PIL import Image
ap = argparse.ArgumentParser(); ap.add_argument('--n', type=int, default=14); ap.add_argument('--skip', default='A1'); ap.add_argument('--out'); a = ap.parse_args(); rows = []
for sid, start, d, vos, fn in S.SCENES:
    if sid in a.skip.split(','): continue
    fr = [np.asarray(fn(d * (i + 0.5) / a.n, d, {}).finish().convert('L').resize((96, 54)), np.float32) for i in range(a.n)]
    diffs = [float(np.abs(fr[i + 1] - fr[i]).mean()) for i in range(a.n - 1)]; mean = float(np.mean(diffs)); static = sum(x < 1.0 for x in diffs)
    rows.append({'id': sid, 'start': start, 'dur': d, 'mean_change': round(mean, 2), 'static_samples': static, 'flag': 'LOW_MOTION' if mean < 3.0 else ''})
    print(f"{sid:3s} {start:4d}s {d:3d}s  motion {mean:5.2f}  static {static:2d}/{a.n - 1}  {rows[-1]['flag']}", flush=True)
if a.out: json.dump(rows, open(a.out, 'w'), indent=1)
