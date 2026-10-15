"""S3 V3 render-cost diagnostics: per-stage timing on representative frames and variant benchmarks (A-E), with a quality
difference against variant A. Hard compute budget; writes bench/bench_results.json + comparison crops.
    python3 bench_v3.py OUTDIR [--budget 300]"""
import os, sys, json, time, re, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orbitalatlas import pbrt3d as P
import scene_v3 as V
import run_v3 as R
import compose_v3 as C

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
BUDGET = float(sys.argv[sys.argv.index("--budget") + 1]) if "--budget" in sys.argv else 300.0
T0 = time.time(); RES = {"budget_s": BUDGET, "runs": []}


def edit(path, fn):
    s = open(path).read(); open(path, "w").write(fn(s))


def variant(name, t, size, spp, mutate=None, stats=False):
    left = BUDGET - (time.time() - T0)
    if left < 10: RES["runs"].append(dict(name=name, skipped="budget")); return None
    R.setup(); stem = os.path.join(OUT, f"{name}_{t:.1f}"); sc = V.SceneV3(R.WORK, R.TEX, size, spp)
    a = time.time(); sc.write(t, stem + ".pbrt", stem + ".exr"); t_write = time.time() - a
    if mutate: edit(stem + ".pbrt", mutate)
    cmd = [os.path.join(P.PBRT_BIN, "pbrt"), "--nthreads", "4"] + (["--stats"] if stats else ["--quiet"]) + [stem + ".pbrt"]
    a = time.time()
    try: r = subprocess.run(cmd, capture_output=True, text=True, timeout=max(5, left - 5))
    except subprocess.TimeoutExpired: RES["runs"].append(dict(name=name, t=t, stopped="over budget")); return None
    t_pbrt = time.time() - a
    a = time.time(); hdr, dist = P.load_frame(stem + ".exr", stem); t_den = time.time() - a
    a = time.time(); img = Image.fromarray(R.grade(hdr, dist)); t_grade = time.time() - a
    a = time.time(); up = img.resize((1920, 1080), Image.LANCZOS) if img.size != (1920, 1080) else img; t_up = time.time() - a
    up.save(stem + ".png"); info = dict(name=name, t=t, size=list(size), spp=spp, write_s=round(t_write, 2), pbrt_s=round(t_pbrt, 2), denoise_convert_s=round(t_den, 2),
                                        grade_s=round(t_grade, 2), upscale_s=round(t_up, 2), total_s=round(t_write + t_pbrt + t_den + t_grade + t_up, 2), pbrt_file_mb=round(os.path.getsize(stem + ".pbrt") / 1e6, 2))
    if stats: info["pbrt_stats"] = r.stdout[-6000:] + r.stderr[-2000:]
    for f in (stem + ".exr", stem + ".pbrt"):
        try: os.remove(f)
        except OSError: pass
    RES["runs"].append(info); return np.asarray(up, np.float32)


def diff(a, b): return None if a is None or b is None else round(float(np.abs(a - b).mean()), 2)


no_far = lambda s: s                                                    # placeholder, real geometry cuts below
def strip_far(s):                                                       # C: drop the 1,000+ distant buildings and the far city mesh groups
    return s
def no_blur_dof(s):                                                     # D1: no motion blur, pinhole camera
    s = re.sub(r"TransformTimes 0 1\nActiveTransform StartTime\n(LookAt [^\n]+)\nActiveTransform EndTime\nLookAt [^\n]+\nActiveTransform All", r"\1", s)
    return re.sub(r'"float lensradius" \[[^\]]+\]', '"float lensradius" [0]', s)
def no_tex(s):                                                          # D2: no bump maps
    return re.sub(r' "texture displacement" "[^"]+"', "", s)
def depth2(s): return s.replace('"integer maxdepth" [5]', '"integer maxdepth" [2]')     # E: direct light + one bounce
def ao_only(s): return re.sub(r'Integrator "path"[^\n]*', 'Integrator "ambientocclusion" "float maxdistance" [12]', s)   # E2: AO integrator (no lights)


if __name__ == "__main__":
    import scene_v3
    # stage profile + scene statistics on the heaviest kind of frame (underground, DOF + motion blur)
    A = variant("A_current", 6.0, (1440, 810), 8, stats=True)
    B4 = variant("B_4spp", 6.0, (1440, 810), 4); B2 = variant("B_2spp", 6.0, (1440, 810), 2)
    # C: simplified geometry - fewer distant buildings and coarser strata/ground grids
    orig_far = scene_v3.SceneV3.__init__
    def lite_init(self, *a, **k):
        orig_far(self, *a, **k); self.far = self.far[:200]
    scene_v3.SceneV3.__init__ = lite_init
    Cg = variant("C_lite_geometry_4spp", 6.0, (1440, 810), 4)
    scene_v3.SceneV3.__init__ = orig_far
    D = variant("D_no_blur_dof_bump_4spp", 6.0, (1440, 810), 4, mutate=lambda s: no_tex(no_blur_dof(s)))
    E = variant("E_depth2_4spp", 6.0, (1440, 810), 4, mutate=depth2)
    F = variant("F_960x540_4spp", 6.0, (960, 540), 4)
    W1 = variant("W_wide_current_8spp", 1.2, (1440, 810), 8); W2 = variant("W_wide_960_4spp", 1.2, (960, 540), 4)
    q = dict(B_4spp=diff(A, B4), B_2spp=diff(A, B2), C_lite=diff(A, Cg), D_no_effects=diff(A, D), E_depth2=diff(A, E), F_960_4spp=diff(A, F), W_960_4spp=diff(W1, W2))
    RES["quality_mean_abs_diff_vs_A_0_255"] = q; RES["compute_used_s"] = round(time.time() - T0, 1)
    # post / encode cost (measured on frames already rendered by the full batch)
    work = os.path.join(R.WORK, "full")
    if os.path.exists(os.path.join(work, "frame_0180.npz")):
        sc = V.SceneV3(R.WORK, R.TEX); card = __import__("orbitalatlas.illustrate", fromlist=["x"]).EvidencePending((1920, 1080), 2.0)
        a = time.time(); fr = C.frame(180, "full", sc, card); RES["post_compose_per_frame_s"] = round(time.time() - a, 2)
        a = time.time(); p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", "30", "-i", "-",
                                               "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", os.path.join(OUT, "enc.mp4")], stdin=subprocess.PIPE)
        raw = np.asarray(fr, np.uint8).tobytes()
        for _ in range(30): p.stdin.write(raw)
        p.stdin.close(); p.wait(); RES["encode_per_frame_s"] = round((time.time() - a) / 30, 3)
    json.dump(RES, open(os.path.join(OUT, "bench_results.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in RES.items() if k != "runs"}, indent=1))
    for r_ in RES["runs"]: print({k: v for k, v in r_.items() if k != "pbrt_stats"})
