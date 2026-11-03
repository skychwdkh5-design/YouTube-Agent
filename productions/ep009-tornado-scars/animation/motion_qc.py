#!/usr/bin/env python3
"""Reusable motion QC for Orbital Atlas renders.

Two kinds of checks (never a blind global threshold):
 1. FILE      ffprobe: size, fps, frame count, pts regularity, duplicate/missing frames.
 2. TRACK     per-ROI sub-pixel tracking of the rendered video (phase correlation). A smooth motion gives a smooth
              shift sequence; stepping/freezing shows up as residual vs a local polynomial fit and as 'freeze-jump'
              frames (shift ~0 between frames whose neighbours move). Intentional holds / cuts are passed in and ignored.
 3. PROBE     analytic object trajectories (engine scenes expose probe(t)->{name: dict(x,y,rot,scale,...)}).
              Reports C0 jumps, velocity resets (C1) and acceleration spikes at fine sampling, with declared cuts removed.

CLI:
  python3 motion_qc.py file  video.mp4
  python3 motion_qc.py track video.mp4 t0 t1 x0,y0,x1,y1 [more rois...]
"""
import json, subprocess, sys
import numpy as np


# ------------------------------------------------------------------ 1. FILE
def ffprobe_file(path):
    j = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=width,height,r_frame_rate,avg_frame_rate,codec_name,profile,pix_fmt,nb_frames,duration:format=format_name",
        "-show_entries", "frame=pts_time,pkt_pts_time", "-of", "json", path]))
    st = j["streams"][0]
    pts = sorted(float(f.get("pts_time") or f.get("pkt_pts_time")) for f in j["frames"] if (f.get("pts_time") or f.get("pkt_pts_time")))
    d = np.diff(pts)
    fps = eval(st["r_frame_rate"])
    out = dict(width=st["width"], height=st["height"], fps=fps, codec=f'{st["codec_name"]} {st.get("profile")}', pix_fmt=st["pix_fmt"],
               frames=len(pts), duration=pts[-1] + 1 / fps if pts else 0,
               dt_min=float(d.min()), dt_max=float(d.max()), dt_irregular=int((np.abs(d - 1 / fps) > 1e-4).sum()))
    out["constant_frame_rate"] = out["dt_irregular"] == 0
    return out


def read_gray(path, t0, t1, size=(1920, 1080), fps=30, scale=1.0):
    w, h = size; ow, oh = int(w * scale), int(h * scale)
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t0:.4f}", "-t", f"{t1 - t0:.4f}", "-i", path, "-vf", f"scale={ow}:{oh}:flags=area,format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.check_output(cmd)
    n = len(raw) // (ow * oh)
    return np.frombuffer(raw, np.uint8)[: n * ow * oh].reshape(n, oh, ow)


# ------------------------------------------------------------------ 2. TRACK
def track_roi(frames, roi, up=40):
    """Per-frame displacement (dx, dy) of an ROI between consecutive frames (px, sub-pixel)."""
    from skimage.registration import phase_cross_correlation
    x0, y0, x1, y1 = roi
    win = np.outer(np.hanning(y1 - y0), np.hanning(x1 - x0))
    out = [(0.0, 0.0)]
    for a, b in zip(frames[:-1], frames[1:]):
        A = a[y0:y1, x0:x1].astype(np.float32) * win; B = b[y0:y1, x0:x1].astype(np.float32) * win
        sh, _, _ = phase_cross_correlation(A, B, upsample_factor=up, normalization=None)
        out.append((-float(sh[1]), -float(sh[0])))
    return np.array(out)


def stepping_report(disp, holds=(), fps=30, win=9):
    """disp: (n,2) per-frame shifts. Returns residual RMS vs local poly fit and freeze-jump statistics (px/frame)."""
    from scipy.signal import savgol_filter
    v = np.hypot(disp[:, 0], disp[:, 1]); v[0] = v[1]
    sm = savgol_filter(v, win, 2) if len(v) > win else v
    res = v - sm
    moving = sm > 0.25                                    # only where the motion is intended to be visible
    frozen = moving & (v < 0.35 * sm)                     # near-stop while neighbours move
    rms = float(np.sqrt(np.mean(res[moving] ** 2))) if moving.any() else 0.0
    ratio = rms / (float(np.mean(sm[moving])) + 1e-9) if moving.any() else 0.0
    return dict(n=len(v), moving_frames=int(moving.sum()), freeze_jump_frames=int(frozen.sum()), residual_rms_px=round(rms, 3),
                residual_over_speed=round(ratio, 3), mean_speed_px_frame=round(float(sm[moving].mean()), 3) if moving.any() else 0.0)


def duplicate_frames(frames, roi=None, eps=0.35):
    """Near-identical consecutive frames (mean abs diff below eps grey levels) inside an ROI."""
    x0, y0, x1, y1 = roi or (0, 0, frames.shape[2], frames.shape[1])
    d = np.abs(frames[1:, y0:y1, x0:x1].astype(np.float32) - frames[:-1, y0:y1, x0:x1].astype(np.float32)).mean((1, 2))
    return d, np.where(d < eps)[0] + 1


# ------------------------------------------------------------------ 3. PROBE
def probe_analysis(probe, t0, t1, cuts=(), impacts=(), holds=(), fps=30, sub=16):
    """Sample probe(t) at fps*sub Hz. Detect C0 jumps, velocity resets and acceleration spikes per object/property.
    cuts: times of intentional editorial discontinuities (ignored +-1 fine sample). holds: (a,b,name|None) intervals where
    stillness is intended. impacts: times of physical collisions (velocity may jump, position must not). A defect is reported only when the discontinuity is large relative to the object's own local
    dynamics (robust MAD of the derivative), not against a global number."""
    dt = 1.0 / (fps * sub); ts = np.arange(t0, t1, dt)
    samples = [probe(t) for t in ts]
    rep = {}
    for obj in samples[0]:
        for prop in samples[0][obj]:
            x = np.array([s[obj][prop] for s in samples], float)
            v = np.gradient(x, dt); a = np.gradient(v, dt)
            keep = np.ones(len(ts), bool)
            for c in cuts: keep &= np.abs(ts - c) > 2 * dt
            dx = np.abs(np.diff(x)); dv = np.abs(np.diff(v))
            kk = keep[1:] & keep[:-1]
            rng = float(np.ptp(x)) + 1e-12; vmax = float(np.abs(v[keep]).max()) + 1e-12
            def local_med(d, w=24):
                from scipy.ndimage import median_filter
                return median_filter(d, size=2 * w + 1, mode="nearest")
            lm_x, lm_v = local_med(dx), local_med(dv)
            # a defect must beat (a) the object's OWN local dynamics and (b) an absolute floor tied to its range / peak speed,
            # so near-static signals and ordinary fast-but-smooth motion are not flagged
            floor_x = 0.02 * rng * (2 / (fps * sub)) * fps * 1.0       # 2% of range per second at the fine rate
            floor_v = 0.5 * vmax / (0.05 * fps * sub)                   # velocity may not change by half its peak in 1/20 frame
            c0 = np.where(kk & (dx > 8 * lm_x + 1e-12) & (dx > floor_x * 0 + 0.05 * rng) )[0]
            c1 = np.where(kk & (dv > 8 * lm_v + 1e-12) & (dv > 0.15 * vmax))[0]
            c1 = np.array([i for i in c1 if all(abs(ts[i] - ti) > 3 * dt for ti in impacts)], int)
            rep[f"{obj}.{prop}"] = dict(c0_jumps=[round(float(ts[i]), 4) for i in c0[:8]], c1_resets=[round(float(ts[i]), 4) for i in c1[:8]],
                                       peak_speed=float(np.abs(v[keep]).max()), peak_accel=float(np.abs(a[keep]).max()))
    return rep


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "file":
        print(json.dumps(ffprobe_file(sys.argv[2]), indent=1))
    elif cmd == "track":
        path, t0, t1 = sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
        fr = read_gray(path, t0, t1)
        for r in sys.argv[5:]:
            roi = tuple(int(v) for v in r.split(","))
            d = track_roi(fr, roi)
            print(r, json.dumps(stepping_report(d)))
