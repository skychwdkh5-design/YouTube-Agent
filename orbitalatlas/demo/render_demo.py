"""Demonstration render: seven synthetic shots built from specs (two different synthetic images through one spec format),
six different transitions, camera motion, anchored overlays. Output is a local test MP4 (git-ignored). Usage:
  python3 -m orbitalatlas.demo.render_demo OUT.mp4 [--size 1280x720] [--fps 30] [--frames t1,t2 --png DIR]"""
import argparse, json, os, sys
import numpy as np
from orbitalatlas import spec as SP, transitions as TR, sequence as SQ, qa as QA

HERE = os.path.dirname(os.path.abspath(__file__))


def build(size=(1280, 720)):
    specs = json.load(open(os.path.join(HERE, "demo_specs.json")))
    sc = {k: SP.scene_from_spec(v, size) for k, v in specs.items()}
    W, H = size
    # ScaleMatch: island B in 'islands_wide2' (end of shot) must land on island B in 'islands_closeup' (start of shot).
    va = sc["islands_wide2"].camera.view(sc["islands_wide2"].end); vb = sc["islands_closeup"].camera.view(sc["islands_closeup"].start)
    c = sc["islands_closeup"].meta["centers"][1]; r = sc["islands_closeup"].meta["radii"][1] * 1.0
    pa, pb = va.pt(c) / [W, H], vb.pt(c) / [W, H]; sa, sb = 2 * r * va.k / H, 2 * r * vb.k / H
    # GeoFocus: focus = the coast marker at the end of the close-up.
    ve = sc["islands_closeup"].camera.view(sc["islands_closeup"].end); focus = ve.pt(sc["islands_closeup"].camera.anchors["coast"]) / [W, H]
    trs = [
        TR.Push("left", a_rate=1.0, duration=0.8, ease="in_out_cubic", shutter=1 / 45, samples=16),
        TR.DateTransition("2010", "2020", mode="sweep", duration=1.2),
        TR.ScaleMatch(tuple(pa), tuple(pb), float(sa), float(sb), duration=1.2),
        TR.GeoFocus(tuple(focus), radius=0.14, duration=1.2),
        TR.CinematicPush((0.5, 0.5), duration=1.0),
        TR.MaskReveal("linear", angle=-20, feather=0.1, edge_color=(92, 225, 230), duration=1.0),
    ]
    order = [("islands_wide", 4.0), ("city_river", 4.0), ("islands_wide2", 3.5), ("islands_closeup", 3.0), ("city_landmark", 3.0), ("islands_pair", 3.0), ("city_end", 2.5)]
    return SQ.Sequence([SQ.Shot(sc[k], d) for k, d in order], trs), sc


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--size", default="1280x720"); ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--frames"); ap.add_argument("--png"); ap.add_argument("--qa", action="store_true"); a = ap.parse_args()
    size = tuple(int(x) for x in a.size.split("x")); seq, sc = build(size)
    print("duration", round(seq.duration, 2), "problems", seq.problems)
    if a.frames:
        os.makedirs(a.png, exist_ok=True)
        for t in [float(x) for x in a.frames.split(",")]: seq.render(t).save(os.path.join(a.png, f"f_{t:05.2f}.png"))
        sys.exit(0)
    n = SQ.render_video(seq, a.out, fps=a.fps); print("frames", n)
    if a.qa:
        sched = seq.schedule(); cuts = [t["t0"] for t in sched["transitions"] if t["kind"] == "cut"]
        r = QA.run_video(a.out, QA.QAConfig(fps=a.fps), cuts=cuts, schedule=sched, problems=seq.problems)
        print(json.dumps(r, indent=1))
