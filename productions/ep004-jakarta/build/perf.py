"""performance probe (short fragments, one process): where does a 1080p frame spend its time?
    python3 productions/ep004-jakarta/build/perf.py [--size 1920x1080] [--n 12]"""
import os, sys, time, cProfile, pstats, io, statistics
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
import review as R
from orbitalatlas import layers as L
size = tuple(int(v) for v in sys.argv[sys.argv.index("--size") + 1].split("x")) if "--size" in sys.argv else (1920, 1080); N = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 12
SEG = [("map+cards (b11 hotspots)", 172, 186), ("map+bars (b13 districts)", 228, 240), ("2-D radar diagram (b05)", 66, 90), ("cut-away 3-D-style scene (b09)", 136, 148), ("globe locator (b04a)", 41, 44), ("2-D schematic (b17 trends)", 318, 328), ("dyke schematic (b20)", 386, 398)]
rows = []
for name, a, b in SEG:
    prog, info = R.build(size, (a, b)); base = info["t_base"]; ts = [a + (b - a) * (i + 0.5) / N for i in range(N)]
    prog.render(ts[0] - base)                                   # warm caches (fonts, pyramids)
    t_seq, t_all = [], []
    for t in ts:
        t0 = time.perf_counter(); prog.seq.render(t - base); t1 = time.perf_counter(); fr = prog.render(t - base); t2 = time.perf_counter(); fr.tobytes(); t3 = time.perf_counter()
        t_seq.append(t1 - t0); t_all.append(t2 - t1 + (t3 - t2))
    rows.append((name, statistics.mean(t_seq) * 1000, statistics.mean(t_all) * 1000, (statistics.mean(t_all) - statistics.mean(t_seq)) * 1000))
    print(f"{name:34s} scene {rows[-1][1]:7.0f} ms | full frame (scene+captions+composite) {rows[-1][2]:7.0f} ms | captions+composite {rows[-1][3]:6.0f} ms", flush=True)
# profile one map+cards fragment
prog, info = R.build(size, (172, 186)); base = info["t_base"]; pr = cProfile.Profile(); pr.enable()
for i in range(8): prog.render(172 + 1.5 * i - base)
pr.disable(); s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(22); print(s.getvalue()[:3800])
