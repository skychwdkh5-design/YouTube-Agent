#!/usr/bin/env python3
"""QA for the articulated-rig test: joint coverage (no gaps), constant proportions, motion jumps,
callout placement (inside frame, off the face/hands/objects, no overlaps), video integrity, and
2x close-ups of every joint at its extreme positions taken from the rendered MP4.

  python3 -I papercut/qa_rig.py --video test.mp4 --log log.json --report qa.json --closeups dir/
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from papercut.rig import Pose, Rig, SKELETON  # noqa: E402

JOINT_NAMES = {"head": "neck", "uarm_A": "shoulder A", "uarm_B": "shoulder B", "farm_A": "elbow A", "farm_B": "elbow B",
               "hand_A": "wrist A", "hand_B": "wrist B", "thigh_A": "hip A", "thigh_B": "hip B",
               "shin_A": "knee A", "shin_B": "knee B", "boot_A": "ankle A", "boot_B": "ankle B", "scarf": "scarf"}


def pose_from(d):
    return Pose(lean=d["lean"], head=d["head"], arm_A=tuple(d["arm_A"]), arm_B=tuple(d["arm_B"]),
                leg_A=tuple(d["leg_A"]), leg_B=tuple(d["leg_B"]), hand_B=d["hand_B"], eyes=d["eyes"], scarf=d["scarf"])


def rect_overlap(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def rect_circle(a, c):
    cx, cy, r = c
    nx, ny = min(max(cx, a[0]), a[2]), min(max(cy, a[1]), a[3])
    return math.hypot(nx - cx, ny - cy) < r


def check(log, feet, size):
    L = log["log"]
    W, H = size
    rig = Rig(height_px=log["rig_height"])
    res = {"frames": len(L)}
    # 1) joint coverage: render the puppet alone; every joint disc must be fully opaque (no seam/gap)
    worst = (1.0, None, None)
    for e in L:
        fr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        p = pose_from(e["pose"])
        rig.render(fr, p, feet=feet)
        al = np.asarray(fr.getchannel("A"), np.float32) / 255
        for name, (x, y) in rig.joint_points(p, feet).items():
            if name == "scarf":
                continue
            r = 6
            yy, xx = np.mgrid[int(y) - r:int(y) + r + 1, int(x) - r:int(x) + r + 1]
            m = (xx - x) ** 2 + (yy - y) ** 2 <= r * r
            v = float(al[yy[m], xx[m]].min())
            if v < worst[0]:
                worst = (v, e["frame"], name)
        # silhouette holes: transparent pixels fully enclosed by the puppet
        if e["frame"] % 3 == 0:
            from collections import deque
            solid = al > 0.5
            ys, xs = np.nonzero(solid)
            y0, y1, x0, x1 = ys.min() - 2, ys.max() + 3, xs.min() - 2, xs.max() + 3
            sub = ~solid[y0:y1, x0:x1]
            seen = np.zeros_like(sub)
            q = deque([(0, 0)]); seen[0, 0] = True
            while q:
                cy, cx = q.popleft()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < sub.shape[0] and 0 <= nx < sub.shape[1] and sub[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True; q.append((ny, nx))
            holes = int((sub & ~seen).sum())
            res.setdefault("max_enclosed_hole_px", 0)   # background enclosed by limbs: reviewed by eye, not a seam test
            if holes > res["max_enclosed_hole_px"]:
                res["max_enclosed_hole_px"] = holes
                res["max_hole_frame"] = e["frame"]
    res["joint_min_alpha"] = round(worst[0], 4)
    res["joint_min_alpha_at"] = [worst[1], worst[2]]
    # 2) constant proportions: distances between joints on the same rigid part never change
    pairs = [("thigh_A", "thigh_B"), ("uarm_A", "uarm_B"), ("uarm_A", "thigh_A"), ("uarm_B", "farm_B"),
             ("farm_B", "hand_B"), ("thigh_A", "shin_A"), ("shin_A", "boot_A"), ("uarm_A", "farm_A")]
    spread = {}
    for a, b in pairs:
        ds = [math.dist(e["joints"][a], e["joints"][b]) for e in L]
        spread[f"{a}-{b}"] = round(max(ds) - min(ds), 3)
    res["rigid_length_spread_px"] = spread
    res["rig_scale"] = log["rig_scale"]
    # 3) motion: per-frame joint travel, angle steps
    jumps = []
    for i in range(1, len(L)):
        for k in L[i]["joints"]:
            d = math.dist(L[i]["joints"][k], L[i - 1]["joints"][k])
            jumps.append((d, L[i]["frame"], k))
    jumps.sort(reverse=True)
    res["max_joint_step_px"] = [round(jumps[0][0], 2), jumps[0][1], jumps[0][2]]
    ang = []
    for i in range(1, len(L)):
        a, b = L[i]["pose"], L[i - 1]["pose"]
        for key in ("arm_A", "arm_B", "leg_A", "leg_B"):
            for j in range(3):
                if a[key][j] is None or b[key][j] is None:
                    continue
                ang.append((abs(a[key][j] - b[key][j]), L[i]["frame"], f"{key}[{j}]"))
        for key in ("lean", "head", "scarf"):
            ang.append((abs(a[key] - b[key]), L[i]["frame"], key))
    ang.sort(reverse=True)
    res["max_angle_step_deg"] = [round(ang[0][0], 2), ang[0][1], ang[0][2]]
    # accel: second difference of joint positions (a pop shows as a spike)
    acc = []
    for i in range(2, len(L)):
        for k in L[i]["joints"]:
            p0, p1, p2 = (np.array(L[i - n]["joints"][k]) for n in (2, 1, 0))
            acc.append((float(np.linalg.norm(p2 - 2 * p1 + p0)), L[i]["frame"], k))
    acc.sort(reverse=True)
    res["max_joint_accel_px"] = [round(acc[0][0], 2), acc[0][1], acc[0][2]]
    # 4) callouts
    sc_c, sc_r = log["scope"]
    issues = []
    for e in L:
        cards = e["cards"]
        protect = {k: e["part_boxes"][k] for k in ("head", "hand_A", "hand_B") if k in e["part_boxes"]}
        for text, b in cards.items():
            if b[0] < 24 or b[1] < 24 or b[2] > W - 24 or b[3] > H - 24:
                issues.append((e["frame"], text, "near/over frame edge"))
            for k, pb in protect.items():
                if rect_overlap(b, pb) > 0:
                    issues.append((e["frame"], text, f"overlaps {k}"))
            for nm in ("earth", "moon"):
                if rect_circle(b, e[nm]):
                    issues.append((e["frame"], text, f"overlaps {nm}"))
            if e["scope"] and rect_circle(b, (sc_c[0], sc_c[1], sc_r + 12)):
                issues.append((e["frame"], text, "overlaps telescope window"))
            for t2, b2 in cards.items():
                if t2 > text and rect_overlap(b, b2) > 0:
                    issues.append((e["frame"], text, f"overlaps card {t2}"))
            if rect_overlap(b, e["rig_box"]) > 0:
                # card vs the puppet's overall box is allowed only if it misses every part
                for k, pb in e["part_boxes"].items():
                    if rect_overlap(b, pb) > 0:
                        issues.append((e["frame"], text, f"overlaps puppet part {k}")); break
    res["callout_issues"] = len(issues)
    res["callout_issue_examples"] = issues[:12]
    seen = {}
    for e in L:
        for text in e["cards"]:
            seen.setdefault(text, [e["t"], e["t"]])[1] = e["t"]
    res["callouts_visible"] = seen
    return res


def video(path):
    pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                         "stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,avg_frame_rate,nb_frames,sample_rate,channels"
                         ":format=duration,size,bit_rate", "-of", "default=nw=1", str(path)], capture_output=True, text=True).stdout
    dec = subprocess.run(["ffmpeg", "-v", "info", "-i", str(path), "-vf", "blackdetect=d=0.1,freezedetect=d=0.5", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return {"ffprobe": pr, "black": re.findall(r"black_start:\S+", dec), "freeze": re.findall(r"freeze_start: \S+", dec),
            "decode_errors": [l for l in dec.splitlines() if "error" in l.lower()][:5]}


def closeups(vpath, log, feet, out: Path):
    """For each joint: the frames with its smallest and largest angle, cropped around the joint, 2x."""
    out.mkdir(parents=True, exist_ok=True)
    L = log["log"]
    spec = {"shoulder B": ("arm_B", 0, "uarm_B"), "elbow B": ("arm_B", 1, "farm_B"), "wrist B": ("arm_B", 2, "hand_B"),
            "shoulder A": ("arm_A", 0, "uarm_A"), "elbow A": ("arm_A", 1, "farm_A"),
            "pelvis (lean)": ("lean", None, "thigh_A"), "hip A": ("leg_A", 0, "thigh_A"), "knee A": ("leg_A", 1, "shin_A"),
            "hip B": ("leg_B", 0, "thigh_B"), "knee B": ("leg_B", 1, "shin_B"), "ankle A": ("lean", None, "boot_A"),
            "neck": ("head", None, "head"), "scarf": ("scarf", None, "scarf")}
    tiles = []
    for label, (key, idx, joint) in spec.items():
        vals = [(e["pose"][key] if idx is None else e["pose"][key][idx], e["frame"]) for e in L]
        lo, hi = min(vals), max(vals)
        for tag, (v, f) in (("min", lo), ("max", hi)):
            png = out / f"_f{f:04d}.png"
            if not png.exists():
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(vpath), "-vf", f"select=eq(n\\,{f})", "-frames:v", "1",
                                str(png)], check=True)
            im = Image.open(png).convert("RGB")
            x, y = L[f]["joints"][joint]
            r = 70
            crop = im.crop((int(x - r), int(y - r), int(x + r), int(y + r))).resize((280, 280), Image.Resampling.LANCZOS)
            d = ImageDraw.Draw(crop)
            d.rectangle((0, 0, 280, 22), fill=(20, 20, 20))
            d.text((6, 5), f"{label} {tag} {v:+.1f} deg  f{f}", fill=(255, 255, 255))
            tiles.append(crop)
    cols = 6
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 284, rows * 284), (40, 40, 40))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * 284, (i // cols) * 284))
    sheet.save(out / "joint_extremes.jpg", quality=90)
    for p in out.glob("_f*.png"):
        p.unlink()
    return str(out / "joint_extremes.jpg")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", type=Path, required=True)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--closeups", type=Path)
    ap.add_argument("--feet", default="300,985")
    a = ap.parse_args()
    log = json.loads(a.log.read_text())
    feet = tuple(float(v) for v in a.feet.split(","))
    rep = check(log, feet, tuple(log["size"]))
    rep["video"] = video(a.video)
    if a.closeups:
        rep["closeups"] = closeups(a.video, log, feet, a.closeups)
    ok = (rep["joint_min_alpha"] > 0.98 and rep["callout_issues"] == 0
          and max(rep["rigid_length_spread_px"].values()) < 0.5 and not rep["video"]["black"] and not rep["video"]["decode_errors"])
    rep["pass"] = bool(ok)
    a.report.write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps({k: v for k, v in rep.items() if k != "video"}, indent=1, default=str))
    print(rep["video"]["ffprobe"])
    print("PASS" if ok else "CHECK")


if __name__ == "__main__":
    main()
