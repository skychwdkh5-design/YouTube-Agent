"""quality of a fast mode vs the REVIEW path-traced frames on the same frame indices: PSNR, block SSIM (luma, 8x8), mean colour shift.
    python3 quality_cmp.py TAG A B [--size 1280 720]"""
import os, sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_v3 as R


def img(tag, i, size):
    d = os.path.join(R.WORK, tag); j = os.path.join(d, f"d_{i:04d}.jpg"); z = os.path.join(d, f"frame_{i:04d}.npz")
    if os.path.exists(j): im = Image.open(j).convert("RGB")
    elif os.path.exists(z): f = np.load(z); im = Image.fromarray(R.grade(f["hdr"].astype(np.float32), f["dist"].astype(np.float32)))
    else: return None
    return np.asarray(im.resize(size, Image.LANCZOS) if im.size != size else im, np.float64)


def ssim(a, b, k=8):
    ya = a @ [0.299, 0.587, 0.114]; yb = b @ [0.299, 0.587, 0.114]; h, w = ya.shape; h, w = h // k * k, w // k * k
    A = ya[:h, :w].reshape(h // k, k, w // k, k); Bb = yb[:h, :w].reshape(h // k, k, w // k, k)
    ma, mb = A.mean((1, 3)), Bb.mean((1, 3)); va, vb = A.var((1, 3)), Bb.var((1, 3)); cov = ((A - ma[:, None, :, None]) * (Bb - mb[:, None, :, None])).mean((1, 3))
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2; return float((((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma ** 2 + mb ** 2 + c1) * (va + vb + c2))).mean())


def run(tag, a, b, ref="review", size=(1280, 720)):
    ps, ss, sh = [], [], []
    for i in range(a, b):
        x, y = img(tag, i, size), img(ref, i, size)
        if x is None or y is None: continue
        ps.append(10 * np.log10(255 ** 2 / max(((x - y) ** 2).mean(), 1e-9))); ss.append(ssim(x, y)); sh.append((x.mean((0, 1)) - y.mean((0, 1))).tolist())
    return dict(tag=tag, ref=ref, frames=len(ps), psnr_db=round(float(np.mean(ps)), 2), ssim=round(float(np.mean(ss)), 3), mean_rgb_shift=[round(float(v), 1) for v in np.mean(sh, 0)])


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))))
