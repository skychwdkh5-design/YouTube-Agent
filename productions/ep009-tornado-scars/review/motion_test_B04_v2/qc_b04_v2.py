#!/usr/bin/env python3
"""QC for B04 v2. Measures the render; a clean FFmpeg exit is not a pass.

Checks: format; black/freeze; the tree never rises back after impact (frame log AND pixels);
crown lag sign measured on pixels (crown trails during the fall, overshoots at impact);
no single-frame pop (motion energy around the impact); camera never upscales the tree layers.
Builds: contact sheet (4 fps), key-frame sheet, motion chart, comparison video v1 | v2.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3] / "tools" / "motion"))
import build_b04_v2 as B  # noqa: E402
import compositor as C  # noqa: E402

V2 = HERE / "B04_v2_5s.mp4"
V1 = HERE.parent / "motion_test_B04" / "B04_after_5s.mp4"
KEY = [0.5, 1.5, 2.3, 2.9, 3.3, 3.6, 4.0, 4.9]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def frames(p, w=480, h=270):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vf", f"scale={w}:{h}", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, h, w, 3)


def full(p, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", str(p), "-frames:v", "1", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    return Image.frombytes("RGB", (1920, 1080), r.stdout)


def head(im, txt, size=24):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, im.width, size + 12), fill=(0, 0, 0))
    d.text((8, 5), txt, font=C.font(size), fill=(255, 255, 255))


def crown_angle(th, dx, rot):
    """Angle of the tree's alpha centroid about the pivot, measured on the composed pixels."""
    loc = B.local_tree(th, dx, rot, roots=False)
    p = C.place(loc, B.PIV, B.PIV, -th)
    a = np.asarray(p.image.getchannel("A"), dtype=np.float64)
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    cx = (a * xx).sum() / a.sum() + p.xy[0] - B.PIV[0]
    cy = (a * yy).sum() / a.sum() + p.xy[1] - B.PIV[1]
    return math.degrees(math.atan2(cx, -cy))


def main():
    rep = {"checks": []}

    def check(name, ok, detail=""):
        rep["checks"].append({"name": name, "pass": bool(ok), "detail": detail})

    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
             "stream=codec_name,width,height,r_frame_rate,pix_fmt,nb_read_frames", "-of", "json", str(V2)])
    s = json.loads(r.stdout)["streams"][0]
    rep["probe"] = s
    check("format 1920x1080 30 fps H.264 yuv420p 150 frames",
          s["codec_name"] == "h264" and (s["width"], s["height"]) == (1920, 1080) and s["r_frame_rate"] == "30/1"
          and s["pix_fmt"] == "yuv420p" and int(s["nb_read_frames"]) == 150)
    r = run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(V2), "-vf", "blackdetect=d=0.1:pix_th=0.10,freezedetect=n=0.001:d=0.5",
             "-an", "-f", "null", "-"])
    check("no black frames", not re.findall(r"black_start", r.stderr))
    check("no frozen stretch >= 0.5 s", not re.findall(r"freeze_start", r.stderr))

    log = json.loads((HERE / "B04_v2_framelog.json").read_text())
    th = np.array([row["theta"] for row in log])
    t = np.array([row["t"] for row in log])
    after = th[t >= B.T_IMP]
    check("tree stays down after impact (frame log)", after.min() >= B.TH_IMP - 0.6 and after[-1] >= B.TH_IMP,
          f"impact {B.TH_IMP:.1f} deg, min after {after.min():.2f}, final {after[-1]:.2f}")
    check("camera never upscales the tree layers (scale <= 1)", max(r["tree_scale"] for r in log) <= 1.0001,
          f"max {max(r['tree_scale'] for r in log):.3f}")

    # pixel-measured crown lag vs the rigid pose at the same trunk angle
    lag_rows = []
    for tt in (2.6, 3.0, 3.3, 3.45, 3.6, 3.75, 4.0, 4.6):
        thv, dxv, rot = B.theta(tt), B.crown_dx(tt), B.clump_rot(tt)
        lag = crown_angle(thv, dxv, rot) - crown_angle(thv, 0.0, [0] * len(rot))
        lag_rows.append([tt, round(thv, 2), round(lag, 2)])
    rep["crown_lag_deg"] = {"what": "crown centroid angle minus rigid tree at the same trunk angle (+ = ahead in the fall)",
                            "rows": lag_rows}
    during = [r[2] for r in lag_rows if r[0] < B.T_IMP and B.omega(r[0]) > 40]   # fast part of the fall
    post = [r[2] for r in lag_rows if B.T_IMP < r[0] < 3.9]
    check("crown trails the trunk while falling (pixels)", max(during) < -0.2, f"{during}")
    check("crown overshoots after impact, then settles (pixels)", max(post) > 0.2 and abs(lag_rows[-1][2]) < max(post),
          f"post {post}, end {lag_rows[-1][2]}")

    fr = frames(V2)
    e = np.array([0.0] + [float(np.abs(fr[i].astype(np.float32) - fr[i - 1]).mean()) for i in range(1, len(fr))])
    i_imp = int(round(B.T_IMP * 30))
    win = e[i_imp - 6:i_imp + 7]
    pop = float(win.max() / max(np.median(win), 1e-3))
    rep["energy"] = {"mean": round(float(e.mean()), 3), "max": round(float(e.max()), 3),
                     "max_at_s": round(int(e.argmax()) / 30, 3), "impact_window_peak_to_median": round(pop, 2),
                     "static_frames": int((e[1:] < 0.05).sum())}
    check("no single-frame pop at impact (peak <= 2.5x local median)", pop <= 2.5, f"{pop:.2f}")
    check("no frame without motion", rep["energy"]["static_frames"] == 0)

    # contact sheet
    small = frames(V2, 384, 216)
    idx = list(range(0, 150, 30 // 4))
    sheet = Image.new("RGB", (5 * 384, 4 * 216 + 40), "black")
    head(sheet, "EP009 B04 v2 - painted 2.5D scene, 4 fps contact sheet (0-5 s)")
    for k, i in enumerate(idx):
        im = Image.fromarray(small[i].copy())
        ImageDraw.Draw(im).text((6, 192), f"{i / 30:.2f}s", font=C.font(16), fill=(255, 255, 0))
        sheet.paste(im, ((k % 5) * 384, 40 + (k // 5) * 216))
    sheet.save(HERE / "B04_v2_contact_sheet.jpg", quality=88)
    # key frames
    ks = Image.new("RGB", (4 * 640, 2 * 400), "black")
    for k, tt in enumerate(KEY):
        im = full(V2, tt).resize((640, 360))
        tile = Image.new("RGB", (640, 400), "black")
        tile.paste(im, (0, 40))
        head(tile, f"{tt:.1f} s  theta {B.theta(tt):.0f} deg", 20)
        ks.paste(tile, ((k % 4) * 640, (k // 4) * 400))
    ks.save(HERE / "B04_v2_key_frames.jpg", quality=90)
    # chart
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(3, 1, figsize=(12, 8), dpi=110, sharex=True)
    ax[0].plot(t, th, color="#2a7f8f")
    ax[0].axhline(B.TH_IMP, color="#888", ls=":")
    ax[0].set_ylabel("trunk angle, deg")
    for x0, x1, lab in ((0, 1, "wind"), (1, 2, "roots fail"), (2, B.T_IMP, "fall"), (B.T_IMP, 5, "impact / decay")):
        ax[0].axvspan(x0, x1, alpha=0.06 if lab != "fall" else 0.12, color="#c0563b")
        ax[0].text((x0 + x1) / 2, 5, lab, ha="center", fontsize=9)
    ax[1].plot(t, [r["crown_dx"] for r in log], color="#1d4e5a", label="crown displacement (px, + = ahead)")
    ax[1].plot(t, [r["clump0"] for r in log], color="#7aa64a", label="one foliage clump rotation (deg)")
    ax[1].legend(fontsize=8)
    ax[2].plot(np.arange(len(e)) / 30, e, color="#c0563b")
    ax[2].set_ylabel("motion energy")
    ax[2].set_xlabel("s")
    fig.tight_layout()
    fig.savefig(HERE / "B04_v2_motion_chart.png")
    # comparison video: test 1 (after) | test 2
    r = run(["ffmpeg", "-y", "-v", "error", "-i", str(V1), "-i", str(V2), "-filter_complex",
             "[0:v]scale=960:540,drawtext=fontfile=" + C.FONT + ":text='TEST 1 (map overlay)':x=20:y=20:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.55[a];"
             "[1:v]scale=960:540,drawtext=fontfile=" + C.FONT + ":text='TEST 2 (2.5D scene, layered tree)':x=20:y=20:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.55[b];[a][b]hstack",
             "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(HERE / "B04_test1_vs_test2.mp4")])
    check("comparison video built", r.returncode == 0, r.stderr[-200:])
    rep["technical_pass"] = all(c["pass"] for c in rep["checks"])
    rep["note"] = "measurable checks only; the visual verdict is in REVIEW.md"
    (HERE / "qc_report_v2.json").write_text(json.dumps(rep, indent=1))
    for c in rep["checks"]:
        print("PASS" if c["pass"] else "FAIL", c["name"], c["detail"])
    print(json.dumps(rep["energy"]), rep["crown_lag_deg"]["rows"])


if __name__ == "__main__":
    main()
