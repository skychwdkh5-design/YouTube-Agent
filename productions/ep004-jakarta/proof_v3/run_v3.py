"""render driver for S3 V3. python3 run_v3.py still T [W H SPP] | batch A B PRESET TAG [--pipeline]   (PRESET: PREVIEW | REVIEW | FINAL)"""
import os, sys, json, time
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orbitalatlas import pbrt3d as P
import scene_v3 as V

WORK = os.environ.get("S3V3_WORK", "/tmp/claude-0/s3d/work")
TEX = os.path.join(WORK, "tex")


def setup():
    if not os.path.exists(os.path.join(WORK, "sky.pfm")): P.make_sky(os.path.join(WORK, "sky.pfm"), 12.0, 2.6, 0.2, 1024)
    if not all(os.path.exists(os.path.join(TEX, n)) for n in ("ground.png", "topsoil.png", "topsoil_bump.png", "clay1.png", "aquifer.png", "panel.png")):
        import textures; textures.make_all(TEX)


HAZE = (0.46, 0.44, 0.46)


def grade(hdr, dist):
    return P.finish(hdr, exposure=0.0, contrast=1.12, saturation=0.95, lift=(0.006, 0.012, 0.026), gain=(1.02, 1.0, 0.97), bloom=0.30, vignette=0.34,
                    dist=dist, haze=HAZE, haze_m=3500.0, wb=(0.86, 1.0, 1.16))


def frame(t, out_png, size=(1920, 1080), spp=32, keep=False):
    setup(); stem = os.path.join(WORK, "f", f"f{t:07.3f}"); os.makedirs(os.path.dirname(stem), exist_ok=True)
    sc = V.SceneV3(WORK, TEX, size, spp); info = sc.write(t, stem + ".pbrt", stem + ".exr")
    t0 = time.time(); P.render(stem + ".pbrt"); tr = time.time() - t0
    hdr, dist = P.load_frame(stem + ".exr", stem); np.save(stem + ".hdr.npy", hdr.astype(np.float16)); np.save(stem + ".dist.npy", np.minimum(dist, 6e4).astype(np.float16))
    if not keep:
        for f in (stem + ".exr", stem + ".pbrt"):
            try: os.remove(f)
            except OSError: pass
    img = grade(hdr, dist)
    Image.fromarray(img).save(out_png); info.update(render_s=round(tr, 1)); return info


# Render presets (docs/production-knowledge/TRUE_3D_PIPELINE.md). All keep the same true-3-D scene: geometry, perspective camera, motion blur,
# depth of field, textures, lighting. Only resolution, samples and frame rate change. OIDN denoises every preset.
PRESETS = {
    "PREVIEW": dict(size=(640, 360), spp=2, step=2, note="geometry / camera check only; 15 fps rendered, frames doubled to 30"),
    "REVIEW": dict(size=(1280, 720), spp=4, step=1, note="owner review; upscaled to 1080p in compose"),
    "FINAL": dict(size=(1920, 1080), spp=4, step=1, note="native 1080p; needs the owner's separate approval"),
}
# per-shot sample overrides (t0, t1, spp), set only from measured temporal tests (perf/TEMPORAL_QA.md); default = preset spp
# measured 2026-10-16 (perf/TEMPORAL_QA.md): with strong depth of field (underground, 4.3-7.2 s) 4 spp leaves blotchy OIDN grain
# (Laplacian energy x2.2 vs 8 spp, static-pixel change x1.3) -> 8 spp there; wide shots and the motion-blurred dive pass at 4 spp;
# 2 spp rejected for wide shots (smeared building edges, -23 % detail, PSNR 32.6 dB vs 8 spp).
SPP_OVERRIDES = {"PREVIEW": [], "REVIEW": [(4.3, 7.2, 8)], "FINAL": [(4.3, 7.2, 8)]}


def spp_for(preset, t):
    for t0, t1, n in SPP_OVERRIDES.get(preset, []):
        if t0 <= t < t1: return n
    return PRESETS[preset]["spp"]


def _post(stem, out, keep_exr=False):
    """EXR -> OIDN -> compressed HDR + distance. Runs in a worker thread when pipelining (its tools are subprocesses: no GIL contention)."""
    t0 = time.time(); hdr, dist = P.load_frame(stem + ".exr", stem)
    np.savez_compressed(out, hdr=hdr.astype(np.float16), dist=np.minimum(dist, 6e4).astype(np.float16))
    for f in ((stem + ".pbrt",) if keep_exr else (stem + ".exr", stem + ".pbrt")):
        try: os.remove(f)
        except OSError: pass
    return time.time() - t0


def batch(a, b, preset, tag, pipeline=False, frames=None):
    """render frames a..b-1 (30 fps grid) with a preset to WORK/<tag>/frame_NNNN.npz; restartable (skips finished frames).
    pipeline=True overlaps the denoise/encode of frame i with the path tracing of frame i+1 (one frame in flight, bounded RAM).
    Logs per-frame stage times and peak RSS (self + children) to WORK/<tag>/log.txt."""
    import resource
    from concurrent.futures import ThreadPoolExecutor
    setup(); cfg = PRESETS[preset]; d = os.path.join(WORK, tag); os.makedirs(d, exist_ok=True); log = open(os.path.join(d, "log.txt"), "a")
    sc = V.SceneV3(WORK, TEX, cfg["size"], cfg["spp"]); ex = ThreadPoolExecutor(1) if pipeline else None; pending = None; wall0 = time.time()
    import threading
    mem = {"peak_used_mb": 0, "stop": False}

    def sample():                                                           # system-wide used RAM (all processes), every 0.5 s
        while not mem["stop"]:
            info = dict(l.split(":", 1) for l in open("/proc/meminfo"))
            used = (int(info["MemTotal"].split()[0]) - int(info["MemAvailable"].split()[0])) / 1024; mem["peak_used_mb"] = max(mem["peak_used_mb"], round(used))
            time.sleep(0.5)
    threading.Thread(target=sample, daemon=True).start()
    todo = frames if frames is not None else range(a, b, cfg["step"])
    for i in todo:
        out = os.path.join(d, f"frame_{i:04d}.npz")
        if os.path.exists(out): continue
        t = i / 30.0; sc.spp = spp_for(preset, t); stem = os.path.join(d, f"tmp_{i:04d}")
        t0 = time.time(); sc.write(t, stem + ".pbrt", stem + ".exr"); tw = time.time() - t0
        t0 = time.time(); P.render(stem + ".pbrt"); tr = time.time() - t0
        if pipeline:
            if pending is not None: pending.result()
            pending = ex.submit(_post, stem, out); tp = None
        else:
            tp = _post(stem, out)
        ru_s = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024; ru_c = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024
        log.write(json.dumps(dict(i=i, t=round(t, 3), preset=preset, spp=sc.spp, write_s=round(tw, 2), pbrt_s=round(tr, 1), post_s=None if tp is None else round(tp, 2),
                                  wall_s=round(time.time() - wall0, 1), peak_rss_self_mb=round(ru_s), peak_rss_child_mb=round(ru_c), pipeline=pipeline)) + "\n"); log.flush()
    if pending is not None: pending.result()
    if ex: ex.shutdown()
    mem["stop"] = True
    log.write(json.dumps(dict(done=True, frames=len(list(todo)), wall_s=round(time.time() - wall0, 1), peak_system_used_mb=mem["peak_used_mb"], pipeline=pipeline)) + "\n"); log.flush()


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "batch":                                                     # batch A B PRESET TAG [--pipeline]
        batch(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5], pipeline="--pipeline" in sys.argv)
    if cmd == "still":
        t = float(sys.argv[2]); W, H, spp = (int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (960, 540, 16)
        info = frame(t, os.path.join(WORK, f"still_{t:05.2f}.png"), (W, H), spp, keep="--keep" in sys.argv)
        print(json.dumps({k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in info.items()}))
