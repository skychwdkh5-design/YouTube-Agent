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
    "DRAFT": dict(size=(960, 540), spp=0, step=1, raster=True, note="RASTER (three.js / WebGL in headless Chromium): same 3-D scene, shadows, sky light; no GI/DOF/motion blur"),
    "PREVIEW": dict(size=(640, 360), spp=2, step=2, note="geometry / camera check only; 15 fps rendered, frames doubled to 30"),
    "REVIEW": dict(size=(1280, 720), spp=4, step=1, note="owner review; upscaled to 1080p in compose"),
    "FINAL": dict(size=(1920, 1080), spp=4, step=1, note="native 1080p; needs the owner's separate approval"),
}
# per-shot sample overrides (t0, t1, spp), set only from measured temporal tests (perf/TEMPORAL_QA.md); default = preset spp
# measured 2026-10-16 (perf/TEMPORAL_QA.md): with strong depth of field (underground, 4.3-7.2 s) 4 spp leaves blotchy OIDN grain
# (Laplacian energy x2.2 vs 8 spp, static-pixel change x1.3) -> 8 spp there; wide shots and the motion-blurred dive pass at 4 spp;
# 2 spp rejected for wide shots (smeared building edges, -23 % detail, PSNR 32.6 dB vs 8 spp).
SPP_OVERRIDES = {"DRAFT": [], "PREVIEW": [], "REVIEW": [], "FINAL": []}      # manual per-shot exceptions (none needed now)
# automatic rule (measured 2026-10-16, perf/ACCELERATION.md): OIDN leaves grain at 4 spp once the depth-of-field blur circle reaches
# ~5 px (1080 lines): Laplacian 4/8 spp = 0.93 at CoC 3-4 px, 1.42 at 7-8 px, 1.21 at 8-11 px, x2.2 at 13-25 px.
COC_8SPP_PX = 5.0
RASTER = dict(exposure=0.9, bg=2.6, shadow=1024, aa=False, wb=(0.86, 1.0, 1.16), fog=1 / 5000, haze=(0.46, 0.44, 0.46))   # matched to grade() by measurement


def spp_for(preset, t):
    for t0, t1, n in SPP_OVERRIDES.get(preset, []):
        if t0 <= t < t1: return n
    base = PRESETS[preset]["spp"]
    if preset in ("REVIEW", "FINAL") and V.coc_px(t) >= COC_8SPP_PX: return max(base, 8)     # adaptive: strong depth of field
    return base


def _post(stem, out, keep_exr=False):
    """EXR -> OIDN -> compressed HDR + distance. Runs in a worker thread when pipelining (its tools are subprocesses: no GIL contention)."""
    t0 = time.time(); hdr, dist = P.load_frame(stem + ".exr", stem)
    hdr = np.nan_to_num(np.minimum(hdr, 6e4), nan=0.0, posinf=6e4)                 # float16 overflows above 65504 (emissive highlights -> inf)
    np.savez_compressed(out, hdr=hdr.astype(np.float16), dist=np.minimum(dist, 6e4).astype(np.float16))
    for f in ((stem + ".pbrt",) if keep_exr else (stem + ".exr", stem + ".pbrt")):
        try: os.remove(f)
        except OSError: pass
    return time.time() - t0


def draft(a, b, tag, frames=None, chunk=60):
    """DRAFT: export each frame's structured scene and rasterise it (orbitalatlas.raster3d) - minutes for a whole proof, no path tracing.
    Writes WORK/<tag>/d_NNNN.jpg + log.txt (export and raster timing)."""
    from orbitalatlas import raster3d as RZ
    setup(); cfg = PRESETS["DRAFT"]; d = os.path.join(WORK, tag); os.makedirs(d, exist_ok=True); log = open(os.path.join(d, "log.txt"), "a")
    sky = os.path.join(WORK, "sky_eq_wb.f32")
    if not os.path.exists(sky): RZ.sky_equirect(os.path.join(WORK, "sky.pfm"), sky, wb=RASTER["wb"])
    sc = V.SceneV3(WORK, TEX, cfg["size"], 1); todo = [i for i in (frames if frames is not None else range(a, b)) if not os.path.exists(os.path.join(d, f"d_{i:04d}.jpg"))]
    w0 = time.time(); t_exp = 0.0; reps = []
    for k in range(0, len(todo), chunk):
        js = []
        for i in todo[k:k + chunk]:
            t0 = time.time(); sc.write(i / 30.0, None, "x.exr"); js.append(RZ.export_frame(sc.last_scene, os.path.join(d, f"d_{i:04d}"), cfg["size"])); t_exp += time.time() - t0
        reps.append(RZ.render(js, d, cfg["size"], sky, WORK, **RASTER))
        for j in js:
            for ext in (".json", ".bin"):
                try: os.remove(j[:-5] + ext)
                except OSError: pass
    rep = dict(done=True, frames=len(todo), wall_s=round(time.time() - w0, 1), export_s=round(t_exp, 1), raster_s=round(sum(r["total_s"] for r in reps), 1))
    log.write(json.dumps(rep) + "\n"); log.flush(); return rep


CACHE = os.path.join(WORK, "framecache")


def scene_hash(pbrt_path):
    """content hash of a frame: the whole pbrt scene text (geometry, camera, lights, materials, samples, resolution) with the per-frame
    film / temp file names removed. Same hash = same picture (deterministic sampler), so the frame can be reused."""
    import hashlib, re
    txt = open(pbrt_path).read(); txt = re.sub(r'"string filename" "[^"]*\.exr"', '"string filename" "F.exr"', txt)
    return hashlib.sha1(txt.encode()).hexdigest()


def _cache_put(h, npz):
    os.makedirs(CACHE, exist_ok=True); dst = os.path.join(CACHE, h + ".npz")
    if not os.path.exists(dst):
        try: os.link(npz, dst)
        except OSError: import shutil; shutil.copy(npz, dst)


def _cache_get(h, out):
    src = os.path.join(CACHE, h + ".npz")
    if not os.path.exists(src): return False
    try: os.link(src, out)
    except OSError: import shutil; shutil.copy(src, out)
    return True


def seed_cache(tag, preset, frames):
    """register already rendered frames of WORK/<tag> under their current scene hash (after checking equivalence once)."""
    cfg = PRESETS[preset]; sc = V.SceneV3(WORK, TEX, cfg["size"], cfg["spp"]); d = os.path.join(WORK, tag); n = 0
    for i in frames:
        npz = os.path.join(d, f"frame_{i:04d}.npz")
        if not os.path.exists(npz): continue
        sc.spp = spp_for(preset, i / 30.0); tmp = os.path.join(d, "hash_tmp.pbrt"); sc.write(i / 30.0, tmp, "F.exr"); _cache_put(scene_hash(tmp), npz); n += 1
    return n


def batch(a, b, preset, tag, pipeline=False, frames=None, cache=True):
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
        h = scene_hash(stem + ".pbrt") if cache else None
        if cache and _cache_get(h, out):                                       # unchanged frame: reuse, no render
            os.remove(stem + ".pbrt"); log.write(json.dumps(dict(i=i, t=round(t, 3), cached=True, write_s=round(tw, 2), wall_s=round(time.time() - wall0, 1))) + "\n"); log.flush(); continue
        t0 = time.time(); P.render(stem + ".pbrt"); tr = time.time() - t0
        if pipeline:
            if pending is not None: pending.result()
            pending = ex.submit(lambda st=stem, o=out, hh=h: (_post(st, o), hh and _cache_put(hh, o))); tp = None
        else:
            tp = _post(stem, out)
            if h: _cache_put(h, out)
        ru_s = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024; ru_c = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024
        log.write(json.dumps(dict(i=i, t=round(t, 3), preset=preset, spp=sc.spp, write_s=round(tw, 2), pbrt_s=round(tr, 1), post_s=None if tp is None else round(tp, 2),
                                  wall_s=round(time.time() - wall0, 1), peak_rss_self_mb=round(ru_s), peak_rss_child_mb=round(ru_c), pipeline=pipeline)) + "\n"); log.flush()
    if pending is not None: pending.result()
    if ex: ex.shutdown()
    mem["stop"] = True
    log.write(json.dumps(dict(done=True, frames=len(list(todo)), wall_s=round(time.time() - wall0, 1), peak_system_used_mb=mem["peak_used_mb"], pipeline=pipeline)) + "\n"); log.flush()


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "draft":                                                     # draft A B TAG
        print(json.dumps(draft(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])))
    if cmd == "batch":                                                     # batch A B PRESET TAG [--pipeline]
        batch(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5], pipeline="--pipeline" in sys.argv)
    if cmd == "still":
        t = float(sys.argv[2]); W, H, spp = (int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (960, 540, 16)
        info = frame(t, os.path.join(WORK, f"still_{t:05.2f}.png"), (W, H), spp, keep="--keep" in sys.argv)
        print(json.dumps({k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in info.items()}))
