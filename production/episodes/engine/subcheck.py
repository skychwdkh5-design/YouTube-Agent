"""Does ATLAS enter the subtitle zone while a subtitle is on screen? Joint-level check, every frame.
usage: python3 subcheck.py EPISODE.py CAPTIONS.srt [--x0 520 --x1 1400 --y0 870]"""
import argparse, os, re, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render import load_episode, FPS
from host import Atlas
from atlas_rig.pose import solve
from atlas_rig.mathx import ap
p = argparse.ArgumentParser(); p.add_argument('ep'); p.add_argument('srt')
p.add_argument('--x0', type=float, default=520); p.add_argument('--x1', type=float, default=1400); p.add_argument('--y0', type=float, default=870)
a = p.parse_args()
def ts(s):
    h, m, x = s.strip().replace(',', '.').split(':'); return int(h) * 3600 + int(m) * 60 + float(x)
cues = []
for b in re.split(r'\n\s*\n', open(a.srt).read().strip()):
    r = b.strip().split('\n'); s, e = r[1].split('-->'); cues.append((ts(s), ts(e)))
ep = load_episode(a.ep); atlas = Atlas(); host = ep.build_host(atlas)
bad = []
for i in range(int(ep.DUR * FPS)):
    t = i / FPS
    if not any(s <= t < e for s, e in cues): continue
    sol = solve(atlas.rig, host.pose(t, i)); M = host.screen(t)
    pts = [ap(M, v) for v in sol.joints.values()]
    if any(a.x0 - 40 <= q[0] <= a.x1 + 40 and q[1] >= a.y0 - 40 for q in pts): bad.append(t)
print(len(bad), 'frames with a joint in the subtitle zone')
if bad:
    runs, s0, pv = [], bad[0], bad[0]
    for t in bad[1:]:
        if t - pv > 0.05: runs.append((s0, pv)); s0 = t
        pv = t
    runs.append((s0, pv)); print([(round(x, 2), round(y, 2)) for x, y in runs])
