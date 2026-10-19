#!/usr/bin/env python3
# effect-reuse-checked: QA measurement only (no visual effect); generalises the ad-hoc EP003 monotony analysis, no existing tool measured picture runs
"""visual_runs.py - how long does the picture stay practically the same? A free QA check for monotony.

    python3 tools/autopilot/visual_runs.py VIDEO.mp4 [--timeline productions/SLUG/timeline.json] [--fps 2] [--thr 14] [--top 14]

Samples the video at --fps into 64x36 thumbnails (caption band = bottom 25 % ignored), starts a new 'run' whenever a frame differs
from the run's first frame by more than --thr (mean abs RGB difference, 0-255), and prints the longest runs, visual changes per
minute and, with --timeline, the screen time of every base picture and the repeated camera view pairs. A long run is evidence to
look at the scene, not a verdict: a calm explanation may hold on purpose. Prints JSON.
"""
import argparse, collections, json, subprocess, sys

import numpy as np


def runs(video, fps=2, thr=14.0, w=64, h=36):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={fps},scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    F = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(np.float32)[:, :int(h * 0.75)]
    out, s = [], 0
    for i in range(1, len(F)):
        if np.abs(F[i] - F[s]).mean() > thr: out.append((s / fps, i / fps)); s = i
    out.append((s / fps, len(F) / fps)); return out


def timeline_stats(path):
    tl = json.load(open(path)); st = [s["start"] for s in tl["shots"]] + [tl["end"]["seconds"]]; tot = collections.Counter(); pairs = collections.Counter()
    for i, s in enumerate(tl["shots"]):
        L = {l["type"]: l for l in s["layers"]}
        base = (L.get("image") or {}).get("asset") or (L.get("wipe") or {}).get("to") or ("flip" if "flip" in L else "other")
        tot[base] += st[i + 1] - st[i]
        if "camera" in s:
            c = s["camera"]; pairs[(base, round(c["from"]["width_km"]), round(c["to"]["width_km"]))] += 1
    total = st[-1]
    return dict(screen_time={k: dict(seconds=round(v, 1), share=round(v / total, 3)) for k, v in tot.most_common()},
                repeated_views=[dict(base=k[0], from_km=k[1], to_km=k[2], shots=n) for k, n in pairs.most_common() if n > 2])


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--timeline"); ap.add_argument("--fps", type=float, default=2)
    ap.add_argument("--thr", type=float, default=14.0); ap.add_argument("--top", type=int, default=14)
    a = ap.parse_args(argv); r = runs(a.video, a.fps, a.thr)
    fmt = lambda t: f"{int(t // 60)}:{t % 60:04.1f}"
    per_min = collections.Counter(int(x[0] // 60) for x in r)
    out = dict(runs=len(r), median_s=float(np.median([b - x for x, b in r])),
               longest=[dict(start=fmt(x), end=fmt(b), seconds=round(b - x, 1)) for x, b in sorted(sorted(r, key=lambda q: q[0] - q[1])[:a.top])],
               changes_per_minute={str(k): v for k, v in sorted(per_min.items())})
    if a.timeline: out.update(timeline_stats(a.timeline))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
