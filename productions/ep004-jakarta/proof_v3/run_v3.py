"""render driver for S3 V3: stills / frame ranges / post. python3 run_v3.py still T [W H SPP] | frames A B | post"""
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


def batch(a, b, size, spp, tag):
    """render frames a..b-1 (30 fps) to WORK/<tag>/hdr_NNNN.npy (+ dist); skips frames already done (restartable)."""
    setup(); d = os.path.join(WORK, tag); os.makedirs(d, exist_ok=True); log = open(os.path.join(d, "log.txt"), "a")
    sc = V.SceneV3(WORK, TEX, size, spp)
    for i in range(a, b):
        out = os.path.join(d, f"frame_{i:04d}.npz")
        if os.path.exists(out) or os.path.exists(os.path.join(d, f"hdr_{i:04d}.npy")): continue
        t = i / 30.0; stem = os.path.join(d, f"tmp_{i:04d}"); info = sc.write(t, stem + ".pbrt", stem + ".exr")
        t0 = time.time(); P.render(stem + ".pbrt"); tr = time.time() - t0
        hdr, dist = P.load_frame(stem + ".exr", stem)
        np.savez_compressed(out, hdr=hdr.astype(np.float16), dist=np.minimum(dist, 6e4).astype(np.float16))
        for f in (stem + ".exr", stem + ".pbrt"):
            try: os.remove(f)
            except OSError: pass
        log.write(json.dumps(dict(i=i, t=round(t, 3), render_s=round(tr, 1), total_s=round(time.time() - t0, 1))) + "\n"); log.flush()


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "batch":
        batch(int(sys.argv[2]), int(sys.argv[3]), (int(sys.argv[4]), int(sys.argv[5])), int(sys.argv[6]), sys.argv[7])
    if cmd == "still":
        t = float(sys.argv[2]); W, H, spp = (int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (960, 540, 16)
        info = frame(t, os.path.join(WORK, f"still_{t:05.2f}.png"), (W, H), spp, keep="--keep" in sys.argv)
        print(json.dumps({k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in info.items()}))
