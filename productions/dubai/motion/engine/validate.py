"""Check traced outlines against the source pixels. For every vertex, sample the brightest-channel value 4 px to each
side along the local normal (nearest pixel, full-resolution edge coordinates). A vertex passes when the dark side is
water-like (max channel <= 75) and the other side is at least 40 levels brighter. Pure numpy; no geography."""
import numpy as np

def vertex_pass(arr, p, off=4.0, lo=75, gap=40, channel="max"):
    if len(p) < 3: return np.zeros(len(p), bool)
    t = np.gradient(p, axis=0); n = np.stack([-t[:, 1], t[:, 0]], 1)
    n /= (np.hypot(n[:, 0], n[:, 1])[:, None] + 1e-9)
    H, W = arr.shape[:2]
    def samp(q):
        x = np.clip(q[:, 0].astype(int), 0, W-1); y = np.clip(q[:, 1].astype(int), 0, H-1)
        return (arr[y, x].max(axis=1) if channel == "max" else arr[y, x][:, {"r": 0, "g": 1, "b": 2}[channel]]).astype(int)
    a, b = samp(p + n*off), samp(p - n*off)
    dark, bright = np.minimum(a, b), np.maximum(a, b)
    return (dark <= lo) & (bright - dark >= gap)

def polyline_score(arr, p, **k): return float(vertex_pass(arr, p, **k).mean()) if len(p) >= 3 else 0.0

def clip_runs(p, box):
    x0, y0, x1, y1 = box
    inside = (p[:, 0] >= x0) & (p[:, 0] <= x1) & (p[:, 1] >= y0) & (p[:, 1] <= y1)
    runs, s = [], None
    for i, v in enumerate(inside):
        if v and s is None: s = i
        if (not v) and s is not None:
            if i - s >= 3: runs.append(p[s:i])
            s = None
    if s is not None and len(p) - s >= 3: runs.append(p[s:])
    return runs

def seglen(p): return float(np.hypot(*np.diff(p, axis=0).T).sum())

def select_project(arr, polys, box, min_len=40.0, min_score=0.7, channel="max", lo=75, gap=40):
    """Clip polylines to box, keep runs whose vertices sit on a real dark/bright edge. Returns (kept, report)."""
    cand = [r for p in polys for r in clip_runs(p, box) if seglen(r) >= min_len]
    kept, rep = [], dict(candidates=len(cand), cand_len=0.0, kept=0, kept_len=0.0, vertex_pass=0.0)
    tot_v = ok_v = 0
    for r in cand:
        ps = vertex_pass(arr, r, lo=lo, gap=gap, channel=channel); sc = float(ps.mean()); L = seglen(r)
        rep["cand_len"] += L; tot_v += len(r); ok_v += int(ps.sum())
        if sc >= min_score: kept.append(r); rep["kept"] += 1; rep["kept_len"] += L
    rep["vertex_pass"] = round(ok_v / max(tot_v, 1), 3)
    rep["kept_fraction_len"] = round(rep["kept_len"] / max(rep["cand_len"], 1), 3)
    return kept, rep
