"""temporal QA of a render preset against reference frames of the same shot (same scene, same camera, same frame indices).
Metrics on graded frames at the new resolution (reference downscaled to match):
  quality   - per-frame MAE (0-255) and PSNR new vs reference
  flicker   - high-frequency part of the frame-to-frame difference (|dF - blur(dF)|), new / reference ratio; also on static pixels only
              (pixels whose reference difference is tiny), where any change is noise, not motion
  detail    - Laplacian energy per frame (sharpness) and its frame-to-frame variation (detail stability)
Writes JSON + a side-by-side MP4 (reference | new) and a strip for frame review.
    python3 temporal_qa.py NEW_TAG REF_TAG A B OUTDIR"""
import os, sys, json, subprocess
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_v3 as R


def load(tag, i, size=None):
    p = os.path.join(R.WORK, tag, f"frame_{i:04d}.npz")
    if not os.path.exists(p): return None
    f = np.load(p); img = Image.fromarray(R.grade(f["hdr"].astype(np.float32), f["dist"].astype(np.float32)))
    return np.asarray(img.resize(size, Image.LANCZOS) if size and img.size != size else img, np.float32)


def _box(g, r):
    k = 2 * r + 1; c = np.cumsum(np.pad(g, ((0, 0), (r + 1, r)), mode="edge"), axis=1); g = (c[:, k:] - c[:, :-k]) / k
    c = np.cumsum(np.pad(g, ((r + 1, r), (0, 0)), mode="edge"), axis=0); return (c[k:] - c[:-k]) / k


def hf(x, r=3):
    """high-frequency part of an image/difference (channel mean minus a 3-pass box blur ~ Gaussian sigma ~ r)."""
    g = x.mean(-1).astype(np.float64); b = _box(_box(_box(g, r), r), r); return g - b


def lap_energy(x):
    g = x.mean(-1); l = 4 * g[1:-1, 1:-1] - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]; return float((l ** 2).mean())


def run(new_tag, ref_tag, a, b, out):
    os.makedirs(out, exist_ok=True); idx = [i for i in range(a, b) if load(new_tag, i) is not None and os.path.exists(os.path.join(R.WORK, ref_tag, f"frame_{i:04d}.npz"))]
    size = Image.fromarray(load(new_tag, idx[0]).astype(np.uint8)).size
    N = {i: load(new_tag, i) for i in idx}; F = {i: load(ref_tag, i, size) for i in idx}
    mae = [float(np.abs(N[i] - F[i]).mean()) for i in idx]; psnr = [float(10 * np.log10(255 ** 2 / max(((N[i] - F[i]) ** 2).mean(), 1e-9))) for i in idx]
    fl_new, fl_ref, st_new, st_ref = [], [], [], []
    for i, j in zip(idx[:-1], idx[1:]):
        if j != i + 1: continue
        dn, dr = N[j] - N[i], F[j] - F[i]; hn, hr = np.abs(hf(dn)), np.abs(hf(dr))
        fl_new.append(float(hn.mean())); fl_ref.append(float(hr.mean()))
        static = np.abs(dr).mean(-1) < 1.0                                       # pixels the reference says do not change
        if static.mean() > 0.02: st_new.append(float(np.abs(dn).mean(-1)[static].mean())); st_ref.append(float(np.abs(dr).mean(-1)[static].mean()))
    le_new = [lap_energy(N[i]) for i in idx]; le_ref = [lap_energy(F[i]) for i in idx]
    rep = dict(new=new_tag, ref=ref_tag, frames=[idx[0], idx[-1]], n=len(idx), size=list(size),
               quality=dict(mae_mean=round(float(np.mean(mae)), 2), mae_max=round(float(np.max(mae)), 2), psnr_mean_db=round(float(np.mean(psnr)), 2), psnr_min_db=round(float(np.min(psnr)), 2)),
               flicker=dict(hf_temporal_new=round(float(np.mean(fl_new)), 3), hf_temporal_ref=round(float(np.mean(fl_ref)), 3), ratio=round(float(np.mean(fl_new) / max(np.mean(fl_ref), 1e-9)), 3),
                            static_pixel_change_new=round(float(np.mean(st_new)), 3) if st_new else None, static_pixel_change_ref=round(float(np.mean(st_ref)), 3) if st_ref else None),
               detail=dict(laplacian_new=round(float(np.mean(le_new)), 2), laplacian_ref=round(float(np.mean(le_ref)), 2), ratio=round(float(np.mean(le_new) / max(np.mean(le_ref), 1e-9)), 3),
                           frame_to_frame_cv_new=round(float(np.std(np.diff(le_new)) / max(np.mean(le_new), 1e-9)), 4), frame_to_frame_cv_ref=round(float(np.std(np.diff(le_ref)) / max(np.mean(le_ref), 1e-9)), 4)))
    json.dump(rep, open(os.path.join(out, f"temporal_{new_tag}_vs_{ref_tag}.json"), "w"), indent=1)
    W, H = size; vid = os.path.join(out, f"side_by_side_{new_tag}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W * 2}x{H}", "-r", "30", "-i", "-", "-c:v", "libx264", "-crf", "16",
                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", vid], stdin=subprocess.PIPE)
    for i in idx:
        fr = Image.new("RGB", (W * 2, H)); fr.paste(Image.fromarray(F[i].astype(np.uint8)), (0, 0)); fr.paste(Image.fromarray(N[i].astype(np.uint8)), (W, 0))
        d = ImageDraw.Draw(fr); d.text((12, 10), f"REFERENCE {ref_tag}  frame {i}", fill=(255, 255, 0)); d.text((W + 12, 10), f"NEW {new_tag}  frame {i}", fill=(255, 255, 0))
        p.stdin.write(np.asarray(fr).tobytes())
    p.stdin.close(); p.wait(); return rep


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]), indent=1))
