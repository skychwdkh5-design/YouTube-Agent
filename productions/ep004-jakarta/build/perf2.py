import os, sys, time, io, cProfile, pstats, statistics, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
import numpy as np, review as R
from orbitalatlas import layers as L
size = (1920, 1080)
def stats_for(a, b, N=10):
    prog, info = R.build(size, (a, b)); base = info["t_base"]; ts = [a + (b - a) * (i + .5) / N for i in range(N)]; prog.render(ts[0] - base); out = []
    for t in ts:
        t0 = time.perf_counter(); fr = prog.render(t - base); out.append((time.perf_counter() - t0, fr))
    return out
# 1) motion-blur samples per frame in the map shots (camera speed -> sub-samples)
prog, info = R.build(size, (172, 186)); sc = [s.scene for s in prog.seq.shots][0]
sc = getattr(sc, "s", sc); cam = sc.camera; n_hist = []
for t in np.arange(0.5, 13.5, 0.5):
    spd = cam.speed(t); n = int(min(sc.max_blur_samples, np.ceil(spd * 0.5 / 2.0) + 1)) if spd > sc.blur_threshold else 1; n_hist.append((round(spd, 1), n))
print("b11 camera speed px/frame -> blur samples:", n_hist)
# 2) baseline vs capped blur samples on the same frames (time + SSIM-like error)
base = stats_for(172, 186, 8)
for s in prog.seq.shots: pass
import review as RR
for sh in R.build(size, (172, 186))[0].seq.shots: pass
def patched(thr, mx):
    p, info = R.build(size, (172, 186))
    for sh in p.seq.shots:
        sc = getattr(sh.scene, "s", sh.scene); sc.blur_threshold, sc.max_blur_samples = thr, mx
    base_t = info["t_base"]; ts = [172 + 14 * (i + .5) / 8 for i in range(8)]; p.render(ts[0] - base_t); res = []
    for t in ts:
        t0 = time.perf_counter(); fr = p.render(t - base_t); res.append((time.perf_counter() - t0, fr))
    return res
for thr, mx in ((6, 16), (6, 4), (14, 3), (1e9, 1)):
    r = patched(thr, mx); err = [float(np.abs(np.asarray(a[1], np.float32) - np.asarray(b[1], np.float32)).mean()) for a, b in zip(base, r)]
    print(f"blur thr={thr} max={mx}: {statistics.mean(x[0] for x in r) * 1000:6.0f} ms/frame (baseline {statistics.mean(x[0] for x in base) * 1000:.0f}); mean abs diff vs baseline {statistics.mean(err):.2f}/255, max {max(err):.2f}")
# 3) radar diagram profile
prog, info = R.build(size, (66, 90)); b0 = info["t_base"]; prog.render(70 - b0); pr = cProfile.Profile(); pr.enable()
for t in (70, 74, 78, 82): prog.render(t - b0)
pr.disable(); s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(8); print(s.getvalue()[:2200])
