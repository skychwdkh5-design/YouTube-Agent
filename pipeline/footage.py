#!/usr/bin/env python3
"""footage.py - the live-footage gate (owner rule; enforced after the 2026-11-21 "slideshow" review).

Owner rule: a pipeline episode is MAINLY real footage - more than 60 % of the narrated picture must be live video
(camera-filmed: mission footage, launches, aircraft / drone / ground shots, lab and field work). Satellite stills with
zoom, Landsat year-by-year sequences, data visualisations, CGI animations and our own graphics are support, not footage.

How it is measured (no trust in labels alone):
  * every timeline asset carries "footage" in rights.json: live | animation | still | graphic (missing = not live);
  * only video layers declared "live" can count, and only the part of their shown segment that actually moves:
    the segment is sampled at 2 fps, and a sample whose picture barely changes from the previous one (mean absolute
    difference < STATIC_DIFF on a 96x54 grey thumbnail) counts as static - a still sequence or a hold;
  * share = live moving seconds / narrated seconds (from the first shot after the cover to the end of the narration);
    the end-screen tail is outside the denominator.

    python3 pipeline/footage.py --timeline timeline.json --rights rights.json --voice-meta voice.json [--min 0.60]
"""
import argparse, json, os, subprocess

import numpy as np

MIN_LIVE = 0.60
STATIC_DIFF = 1.2
CLASSES = ("live", "animation", "still", "graphic")


def shot_spans(tl, end):
    shots = sorted(tl.get("shots", []), key=lambda s: s["start"])
    out = []
    for i, s in enumerate(shots):
        e = shots[i + 1]["start"] if i + 1 < len(shots) else end
        out.append((s, s["start"], e))
    return out


def _frames(path, t0, dur, fps=2, w=96, h=54):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", path, "-vf",
                        f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8)
    n = a.size // (w * h)
    return a[: n * w * h].reshape(n, h, w).astype(np.float32)


def moving_fraction(path, t0, dur):
    f = _frames(path, t0, dur)
    if len(f) < 2:
        return 0.0, []
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    return float((d >= STATIC_DIFF).mean()), [round(float(x), 2) for x in d]


def measure(tl, rights, voice_end, base_dir=".", min_live=MIN_LIVE):
    assets = tl.get("assets") or {}
    by_src = {r["src"]: r for r in rights.get("assets", [])}
    spans = shot_spans(tl, float((tl.get("end") or {}).get("seconds") or voice_end))
    first = next((st for s, st, e in spans if st > 0.0 or (s["layers"] and s["layers"][0].get("type") != "graphic")), 0.0)
    denom = max(0.1, voice_end - first)
    rows, live, by_class = [], 0.0, {c: 0.0 for c in CLASSES + ("unknown",)}
    for s, st, e in spans:
        a0, b0 = max(st, first), min(e, voice_end)
        if b0 <= a0 or not s.get("layers"):
            continue
        L = s["layers"][0]
        asset = assets.get(L.get("asset"), {})
        src = asset.get("src", "")
        cls = (by_src.get(src) or {}).get("footage")
        cls = cls if cls in CLASSES else "unknown"
        if L.get("type") == "still":
            cls = "still" if cls in ("live", "unknown") else cls          # a still is never footage
        if L.get("type") == "graphic":
            cls = "graphic"
        sec = b0 - a0
        by_class[cls] += sec
        row = {"shot": s.get("id"), "from": round(a0, 2), "to": round(b0, 2), "src": src, "class": cls}
        if cls == "live" and L.get("type") == "video":
            t0 = float(L.get("trim") or 0) + (a0 - st)
            mv, _ = moving_fraction(os.path.join(base_dir, src), t0, sec)
            row["moving"] = round(mv, 2)
            live += sec * mv
        rows.append(row)
    share = round(live / denom, 3)
    return {"live_share": share, "need": min_live, "ok": share >= min_live, "narrated_s": round(denom, 1),
            "live_moving_s": round(live, 1), "seconds_by_class": {k: round(v, 1) for k, v in by_class.items() if v},
            "shots": rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--timeline", required=True); ap.add_argument("--rights", required=True)
    ap.add_argument("--voice-meta", required=True); ap.add_argument("--min", type=float, default=MIN_LIVE)
    a = ap.parse_args()
    tl = json.load(open(a.timeline))
    vend = float(json.load(open(a.voice_meta)).get("duration") or 0)
    out = measure(tl, json.load(open(a.rights)), vend, os.path.dirname(os.path.abspath(a.timeline)), a.min)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
