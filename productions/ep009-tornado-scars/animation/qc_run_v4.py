#!/usr/bin/env python3
"""Run QC for a v4 scene+render: python3 qc_run_v4.py <scene_module> <video> t0 t1 [roi x0,y0,x1,y1 ...]"""
import sys, json, numpy as np
import motion_qc as Q
mod = __import__(sys.argv[1] + "_v4"); video = sys.argv[2]; t0, t1 = float(sys.argv[3]), float(sys.argv[4])
rois = [tuple(int(v) for v in r.split(",")) for r in sys.argv[5:]]
out = dict(file=Q.ffprobe_file(video))
imp = getattr(mod, 'IMPACTS', lambda: [])()
pr = Q.probe_analysis(mod.probe, t0, t1, impacts=imp)
out["probe"] = {k: v for k, v in pr.items()}
out["probe_defects"] = {k: dict(c0=v["c0_jumps"], c1=v["c1_resets"]) for k, v in pr.items() if v["c0_jumps"] or v["c1_resets"]}
fr = Q.read_gray(video, 0, t1 - t0)
dup_d, dup_idx = Q.duplicate_frames(fr); out["near_identical_frames"] = [round(t0 + i / 30, 3) for i in dup_idx]
out["tracks"] = {}
for r in rois:
    d = Q.track_roi(fr, r); out["tracks"][",".join(map(str, r))] = Q.stepping_report(d)
print(json.dumps(out, indent=1))
