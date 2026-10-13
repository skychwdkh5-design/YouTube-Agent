"""Automated visual QA. Passing these checks means TECHNICALLY_VALID only; they cannot tell you whether the result looks good.

Every threshold is in QAConfig and is a heuristic with a stated limitation (see each check). Declare legitimate events
(hard cuts, deliberate fades, holds) instead of loosening thresholds. Video checks decode with FFmpeg at reduced size."""
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field, asdict
import numpy as np


@dataclass
class QAConfig:
    size: tuple = (320, 180)             # analysis resolution
    fps: float = 30.0
    # black frames: mean luma 0..255. Limitation: dark-ocean scenes can be legitimately dark; the default only catches near-pure black.
    black_luma: float = 6.0
    black_min_frames: int = 3
    # blank regions: share of 16x9 blocks that are uniform AND equal to a declared fill colour (missing image / uncovered area).
    blank_colors: tuple = ((0, 0, 0), (11, 15, 20))
    blank_tol: float = 3.0
    blank_block_std: float = 1.5
    blank_max_fraction: float = 0.30
    blank_min_frames: int = 3
    # discontinuity: frame-to-frame mean abs diff (0..1) must not exceed max(floor, ratio * local median). Limitation: fast legitimate
    # motion (whip) needs declared transition windows; hard cuts must be declared in `cuts`.
    jump_floor: float = 0.10
    jump_ratio: float = 6.0
    jump_window: int = 15
    # static: consecutive frames with diff < static_eps. Limitation: documentary holds under animated text still change little;
    # raise max_static_s or declare `holds` instead of disabling.
    static_eps: float = 0.0004
    max_static_s: float = 4.0
    # transitions
    min_transition_s: float = 0.25
    max_transition_s: float = 2.5
    transition_motion_frac: float = 0.8   # share of frames inside a transition window that must differ from the previous frame
    transition_spike_ratio: float = 3.0   # first/last frame diff vs median inside the window
    # overlays / camera
    safe_margin_frac: float = 0.03
    camera_step: float = 1 / 15
    max_magnification: float | None = None


def read_frames(path, size=(320, 180), fps=None):
    cmd = ["ffmpeg", "-loglevel", "error", "-i", path]
    if fps: cmd += ["-r", str(fps)]
    cmd += ["-vf", f"scale={size[0]}:{size[1]}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE); n = size[0] * size[1] * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield np.frombuffer(b, np.uint8).reshape(size[1], size[0], 3)
    p.stdout.close(); p.wait()


def _runs(mask, min_len):
    out = []; i = 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]: j += 1
            if j - i >= min_len: out.append((i, j - 1))
            i = j
        else: i += 1
    return out


def _in_ranges(t, ranges): return any(a <= t <= b for a, b in ranges)


def analyse(frames, cfg=QAConfig()):
    """per-frame statistics from an iterable of RGB uint8 arrays."""
    luma, blank, diff = [], [], []; prev = None
    cols = np.array(cfg.blank_colors, np.float32)
    for f in frames:
        g = f.astype(np.float32); y = 0.299 * g[:, :, 0] + 0.587 * g[:, :, 1] + 0.114 * g[:, :, 2]
        luma.append(float(y.mean()))
        H, W = y.shape; bh, bw = H // 9, W // 16; blocks = g[:bh * 9, :bw * 16].reshape(9, bh, 16, bw, 3).transpose(0, 2, 1, 3, 4).reshape(9, 16, -1, 3)
        std = blocks.std(axis=2).max(axis=2); mean = blocks.mean(axis=2)
        near = (np.abs(mean[:, :, None, :] - cols[None, None]).max(axis=3) <= cfg.blank_tol).any(axis=2)
        blank.append(float(((std <= cfg.blank_block_std) & near).mean()))
        diff.append(0.0 if prev is None else float(np.abs(y - prev).mean() / 255.0)); prev = y
    return dict(luma=np.array(luma), blank=np.array(blank), diff=np.array(diff))


def check_stats(st, cfg=QAConfig(), cuts=(), allowed_dark=(), holds=(), transitions=()):
    """cuts: times (s) of declared hard cuts. allowed_dark/holds: [(t0, t1)] declared ranges. transitions: schedule transition dicts."""
    fps = cfg.fps; n = len(st["luma"]); t = np.arange(n) / fps; issues = []
    # 1 black frames
    dark = np.array([(st["luma"][i] < cfg.black_luma) and not _in_ranges(t[i], allowed_dark) for i in range(n)])
    for a, b in _runs(dark, cfg.black_min_frames): issues.append(dict(check="black_frames", t0=round(a / fps, 3), t1=round(b / fps, 3), detail=f"mean luma<{cfg.black_luma}"))
    # 2 blank regions
    bl = np.array([(st["blank"][i] > cfg.blank_max_fraction) and not _in_ranges(t[i], allowed_dark) for i in range(n)])
    for a, b in _runs(bl, cfg.blank_min_frames): issues.append(dict(check="blank_region", t0=round(a / fps, 3), t1=round(b / fps, 3), detail=f"{st['blank'][a:b+1].max():.2f} of blocks are uniform fill colour"))
    # 3 discontinuities
    d = st["diff"]; cutf = {int(round(c * fps)) + k for c in cuts for k in (-1, 0, 1)}
    win = {int(round(tr["t0"] * fps)) + k for tr in transitions if tr.get("kind") != "cut" for k in range(0, int(round((tr["t1"] - tr["t0"]) * fps)) + 1)}
    for i in range(1, n):
        if i in cutf or i in win: continue
        lo, hi = max(1, i - cfg.jump_window), min(n, i + cfg.jump_window + 1)
        neigh = np.concatenate([d[lo:i], d[i + 1:hi]]); med = float(np.median(neigh)) if len(neigh) else 0.0
        if d[i] > max(cfg.jump_floor, cfg.jump_ratio * med): issues.append(dict(check="discontinuity", t0=round(i / fps, 3), t1=round(i / fps, 3), detail=f"diff {d[i]:.3f} vs local median {med:.4f}"))
    # 4 static sequences
    stat = np.array([d[i] < cfg.static_eps and not _in_ranges(t[i], holds) for i in range(n)]); stat[0] = False
    for a, b in _runs(stat, int(cfg.max_static_s * fps)): issues.append(dict(check="static_sequence", t0=round(a / fps, 3), t1=round(b / fps, 3), detail=f"{(b-a+1)/fps:.1f}s with frame diff<{cfg.static_eps}"))
    # 5 transitions measured in the video
    for tr in transitions:
        if tr.get("kind") == "cut": continue
        a, b = int(round(tr["t0"] * fps)), int(round(tr["t1"] * fps))
        if b <= a + 1 or b >= n: continue
        inside = d[a + 1:b + 1]
        if len(inside) and (inside > cfg.static_eps).mean() < cfg.transition_motion_frac:
            issues.append(dict(check="transition_no_motion", t0=tr["t0"], t1=tr["t1"], detail=f"{tr['kind']}: only {(inside > cfg.static_eps).mean():.2f} of frames change"))
        med = float(np.median(inside)) if len(inside) else 0.0
        for j in (a + 1, b):
            if j < n and med > 0 and d[j] > cfg.transition_spike_ratio * max(inside.max(initial=0.0) * 0.0 + med, 1e-9) * 2.2 and d[j] > cfg.jump_floor * 0.5:
                issues.append(dict(check="transition_boundary_pop", t0=round(j / fps, 3), t1=round(j / fps, 3), detail=f"{tr['kind']}: boundary diff {d[j]:.3f} vs median {med:.3f}"))
    return issues


def check_schedule(sched, cfg=QAConfig(), problems=()):
    """declared transition durations: inside [min, max], consistent with the realised window, no overlap problems."""
    issues = [dict(check="schedule", t0=0, t1=0, detail=p) for p in problems]
    for tr in sched["transitions"]:
        if tr["kind"] == "cut": continue
        real = tr["t1"] - tr["t0"]
        if not (cfg.min_transition_s <= tr["declared"] <= cfg.max_transition_s): issues.append(dict(check="transition_duration", t0=tr["t0"], t1=tr["t1"], detail=f"{tr['kind']} declared {tr['declared']}s outside [{cfg.min_transition_s},{cfg.max_transition_s}]"))
        if abs(real - tr["declared"]) > 1 / cfg.fps: issues.append(dict(check="transition_duration", t0=tr["t0"], t1=tr["t1"], detail=f"{tr['kind']} declared {tr['declared']}s but schedule gives {real:.3f}s"))
    kinds = [t["kind"] for t in sched["transitions"] if t["kind"] != "cut"]
    for i in range(len(kinds) - 2):
        if kinds[i] == kinds[i + 1] == kinds[i + 2]: issues.append(dict(check="repetitive_transitions", t0=0, t1=0, detail=f"{kinds[i]} three times in a row"))
    return issues


def check_camera(scene, cfg=QAConfig(), must_show=None):
    """crop validity along the camera path (window leaves image, magnification, anchors outside the safe frame)."""
    iss = scene.camera.check(must_show=must_show, safe=cfg.safe_margin_frac, step=cfg.camera_step, max_magnification=cfg.max_magnification)
    return [dict(check="camera_" + i[0], t0=i[1], t1=i[1], detail=str(i[2]), scene=scene.name) for i in iss]


def check_overlays(scene, cfg=QAConfig(), step=1 / 10):
    """text/plate boxes recorded by the scene: outside the safe frame or colliding. Samples the scene's own timeline."""
    issues = []; W, H = scene.size; m = cfg.safe_margin_frac * H; t = scene.start
    while t <= scene.end:
        scene.render(t, blur=False)
        for g in scene.reg.outside(scene.size, margin=m): issues.append(dict(check="overlay_outside_safe_frame", t0=round(t, 3), t1=round(t, 3), detail=str(g), scene=scene.name))
        for a, b in scene.reg.collisions(): issues.append(dict(check="overlay_collision", t0=round(t, 3), t1=round(t, 3), detail=f"{a} x {b}", scene=scene.name))
        t += step
    return _merge(issues)


def _merge(issues):
    """collapse identical consecutive findings into ranges."""
    out = []
    for i in issues:
        if out and all(out[-1].get(k) == i.get(k) for k in ("check", "detail", "scene")) and i["t0"] - out[-1]["t1"] <= 0.25: out[-1]["t1"] = i["t1"]
        else: out.append(dict(i))
    return out


def check_assets(paths):
    return [dict(check="missing_asset", t0=0, t1=0, detail=p) for p in paths if not os.path.exists(p)]


def run_video(path, cfg=QAConfig(), cuts=(), allowed_dark=(), holds=(), schedule=None, problems=()):
    """decode a rendered file and run all video-level checks; returns {'ok': bool, 'issues': [...], 'stats': {...}}."""
    if not os.path.exists(path): return dict(ok=False, issues=check_assets([path]), stats={})
    st = analyse(read_frames(path, cfg.size, cfg.fps), cfg)
    issues = check_stats(st, cfg, cuts, allowed_dark, holds, schedule["transitions"] if schedule else ())
    if schedule: issues += check_schedule(schedule, cfg, problems)
    stats = dict(frames=len(st["luma"]), mean_luma=round(float(st["luma"].mean()), 2), max_diff=round(float(st["diff"].max()), 4), median_diff=round(float(np.median(st["diff"])), 4))
    return dict(ok=not issues, issues=issues, stats=stats)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="visual QA for a rendered video (TECHNICALLY_VALID checks only)")
    ap.add_argument("video"); ap.add_argument("--cuts", default=""); ap.add_argument("--holds", default=""); ap.add_argument("--dark", default="")
    ap.add_argument("--json"); a = ap.parse_args()
    parse = lambda s: [tuple(map(float, x.split("-"))) for x in s.split(",") if x]
    r = run_video(a.video, cuts=[float(x) for x in a.cuts.split(",") if x], holds=parse(a.holds), allowed_dark=parse(a.dark))
    print(json.dumps(r, indent=1)); (a.json and open(a.json, "w").write(json.dumps(r, indent=1))); sys.exit(0 if r["ok"] else 1)
