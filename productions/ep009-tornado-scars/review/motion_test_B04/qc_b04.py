#!/usr/bin/env python3
"""QC for the B04 motion test. A clean FFmpeg exit is NOT a pass: this measures the result.

Checks
  1. ffprobe: 1920x1080, 30 fps, 150 frames, H.264 yuv420p, 5.0 s.
  2. blackdetect / freezedetect (a held static picture is reported, not hidden).
  3. motion energy per frame (mean |frame - previous frame|) and its peaks.
  4. curve fidelity in pixels: the intact tree layer is re-rendered alone and its silhouette
     angle about the pivot is measured and compared with the angle the named curve prescribes.
  5. native-resolution rule: camera window never below 1920 source px.
  6. review images: 4 fps contact sheets, before/after comparison at key moments, motion chart,
     side-by-side review MP4.
Writes qc_report.json; the visual verdict is written by a person/agent into REVIEW.md.
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
import build_b04 as B  # noqa: E402
import compositor as C  # noqa: E402
import easing as E  # noqa: E402

VIDS = {v: HERE / f"B04_{v}_5s.mp4" for v in ("before", "after")}
KEY_T = [12.3, 13.8, 14.6, 14.95, 15.2, 15.6, 16.8]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(p):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
             "stream=codec_name,width,height,r_frame_rate,pix_fmt,nb_read_frames:format=duration",
             "-of", "json", str(p)])
    d = json.loads(r.stdout)
    s = d["streams"][0]
    num, den = map(int, s["r_frame_rate"].split("/"))
    return {"codec": s["codec_name"], "size": [s["width"], s["height"]], "fps": num / den,
            "pix_fmt": s["pix_fmt"], "frames": int(s["nb_read_frames"]), "duration": float(d["format"]["duration"])}


def detect(p):
    r = run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(p), "-vf",
             "blackdetect=d=0.1:pix_th=0.10,freezedetect=n=0.001:d=0.5", "-an", "-f", "null", "-"])
    black = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)
    fs = re.findall(r"freeze_start: ([\d.]+)", r.stderr)
    fe = re.findall(r"freeze_end: ([\d.]+)", r.stderr)
    freezes = [[float(a), float(b) if i < len(fe) else None] for i, (a, b) in enumerate(zip(fs, fe + [None] * len(fs)))]
    return {"black": [[float(a), float(b)] for a, b in black], "freeze": freezes}


def frames(p, w=480, h=270):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vf", f"scale={w}:{h}", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, h, w, 3)


def full_frame(p, t_local):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t_local:.4f}", "-i", str(p), "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    return Image.frombytes("RGB", (1920, 1080), r.stdout)


def label(im, txt, size=28):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, im.width, size + 14), fill=(0, 0, 0))
    d.text((10, 6), txt, font=C.font(size), fill=(255, 255, 255))
    return im


def contact_sheet(p, out, title):
    fr = frames(p, 384, 216)
    idx = list(range(0, len(fr), 30 // 4))                    # 4 per second
    cols = 5
    rows = math.ceil(len(idx) / cols)
    sheet = Image.new("RGB", (cols * 384, rows * 216 + 44), "black")
    label(sheet, title, 26)
    for k, i in enumerate(idx):
        im = Image.fromarray(fr[i].copy())
        ImageDraw.Draw(im).text((6, 192), f"{B.T0 + i / 30:.2f}s", font=C.font(16), fill=(255, 255, 0))
        sheet.paste(im, ((k % cols) * 384, 44 + (k // cols) * 216))
    sheet.save(out, quality=88)


def comparison(out):
    tiles = []
    for t in KEY_T:
        b = full_frame(VIDS["before"], t - B.T0).resize((640, 360))
        a = full_frame(VIDS["after"], t - B.T0).resize((640, 360))
        col = Image.new("RGB", (640, 720 + 40), "black")
        label(col, f"{t:.2f} s   top: before  /  bottom: after", 20)
        col.paste(b, (0, 40))
        col.paste(a, (0, 400))
        tiles.append(col)
    rows = [tiles[:4], tiles[4:]]
    sheet = Image.new("RGB", (640 * 4, 760 * 2), "black")
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            sheet.paste(im, (c * 640, r * 760))
    sheet.save(out, quality=90)


def energy(fr):
    f = fr.astype(np.float32)
    return [0.0] + [float(np.abs(f[i] - f[i - 1]).mean()) for i in range(1, len(f))]


def silhouette_angle(t):
    """Angle (deg, PIL convention) of the intact tree's pivot->centroid axis, measured on pixels."""
    TI = B.TI
    ang = E.interpolate(TI["angle"], t, "a")
    p, _ = B.tree_layer(B.CLEAN["P03_tree_intact.png"], TI, TI["height_px"], ang, tuple(TI["anchor_screen"]), 1.0, 0, None)
    fr = Image.new("L", (1920, 1080), 0)
    fr.paste(p.image.getchannel("A"), p.xy)
    a = np.asarray(fr, dtype=np.float64)
    yy, xx = np.mgrid[0:1080, 0:1920]
    cx, cy = (a * xx).sum() / a.sum(), (a * yy).sum() / a.sum()
    px, py = TI["anchor_screen"]
    return math.degrees(math.atan2(px - cx, py - cy)), ang     # 0 when centroid straight above pivot


def main():
    rep = {"probe": {}, "detect": {}, "energy": {}, "checks": []}
    ok = True
    en = {}
    for v, p in VIDS.items():
        pr = probe(p)
        rep["probe"][v] = pr
        good = pr["codec"] == "h264" and pr["size"] == [1920, 1080] and abs(pr["fps"] - 30) < 1e-6 \
            and pr["pix_fmt"] == "yuv420p" and pr["frames"] == 150 and abs(pr["duration"] - 5) < 0.05
        rep["checks"].append({"name": f"{v}: format 1080p30 H.264 150 frames", "pass": good})
        ok &= good
        rep["detect"][v] = detect(p)
        fr = frames(p)
        en[v] = energy(fr)
        e = np.array(en[v])
        rep["energy"][v] = {"mean": round(float(e.mean()), 3), "max": round(float(e.max()), 3),
                            "max_at_s": round(B.T0 + int(e.argmax()) / 30, 3),
                            "frames_without_motion": int((e[1:] < 0.05).sum()),
                            "max_jump_ratio": round(float(e.max() / max(np.median(e[1:]), 1e-3)), 1)}
        contact_sheet(p, HERE / f"B04_{v}_contact_sheet.jpg", f"EP009 B04 {v.upper()} - 4 fps contact sheet (12.0-17.0 s)")
        blacks = rep["detect"][v]["black"]
        rep["checks"].append({"name": f"{v}: no black frames", "pass": not blacks})
        ok &= not blacks
    # held picture: report, do not fail (a hold can be editorial), but the improved cut should move
    rep["checks"].append({"name": "after: no frame without motion (>=0.05 mean abs diff)",
                          "pass": rep["energy"]["after"]["frames_without_motion"] == 0,
                          "detail": f"before had {rep['energy']['before']['frames_without_motion']} static frames"})
    # curve fidelity
    errs = []
    t = 14.3
    base, _ = silhouette_angle(14.3)
    rows = []
    while t <= 15.15 + 1e-9:
        meas, want = silhouette_angle(t)
        errs.append(abs((meas - base) - (want - 2.0)))              # measured lean vs prescribed rotation
        rows.append([round(t, 3), round(want, 2), round(meas - base, 2)])
        t += 1 / 30
    rep["curve_fidelity"] = {"what": "intact tree, pivot topple 14.30-15.15 s, preset 'topple'",
                             "max_abs_error_deg": round(max(errs), 3), "samples": rows}
    cf = max(errs) < 0.75
    rep["checks"].append({"name": "rendered rotation follows the 'topple' curve within 0.75 deg", "pass": cf})
    ok &= cf
    log = json.loads((HERE / "B04_after_framelog.json").read_text())
    minw = min(r["cam_width"] for r in log)
    rep["checks"].append({"name": "no upscaling of NASA M01 (camera window >= 1920 px)", "pass": minw >= 1920,
                          "detail": f"min window {minw:.1f} px"})
    ok &= minw >= 1920
    # impact moment: motion peak should sit at the impact, not at a random cut
    peak = rep["energy"]["after"]["max_at_s"]
    rep["checks"].append({"name": "after: motion peak at the impact (15.0-15.4 s)", "pass": 15.0 <= peak <= 15.4,
                          "detail": f"peak at {peak}s"})
    # chart
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 1, figsize=(12, 6.5), dpi=110)
    ts = [B.T0 + i / 30 for i in range(150)]
    ax[0].plot(ts, en["before"], label="before (pilot keys, V7 model)", color="#c0563b")
    ax[0].plot(ts, en["after"], label="after (named curves, pivot topple)", color="#2a7f8f")
    ax[0].set_ylabel("motion energy\n(mean |Δ frame|)")
    ax[0].legend(loc="upper left")
    ax[0].axvline(B.IMPACT, color="#888", ls=":")
    bl = json.loads((HERE / "B04_before_framelog.json").read_text())
    ax[1].plot([r["t"] for r in bl], [r["intact_angle"] for r in bl], color="#c0563b", label="before: intact angle")
    ax[1].plot([r["t"] for r in bl], [100 * r["intact_opacity"] for r in bl], color="#c0563b", ls="--", alpha=.6, label="before: intact opacity %")
    ax[1].plot([r["t"] for r in log], [r.get("intact_angle", np.nan) for r in log], color="#2a7f8f", label="after: intact angle")
    ax[1].plot([r["t"] for r in log], [r.get("uprooted_angle", np.nan) for r in log], color="#1d4e5a", ls="-.", label="after: uprooted settle angle")
    ax[1].set_ylabel("degrees / %")
    ax[1].set_xlabel("pilot time, s")
    ax[1].legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "B04_motion_chart.png")
    comparison(HERE / "B04_before_after_frames.jpg")
    r = run(["ffmpeg", "-y", "-v", "error", "-i", str(VIDS["before"]), "-i", str(VIDS["after"]), "-filter_complex",
             "[0:v]scale=960:540,drawtext=fontfile=" + C.FONT + ":text='BEFORE':x=20:y=20:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.5[a];"
             "[1:v]scale=960:540,drawtext=fontfile=" + C.FONT + ":text='AFTER':x=20:y=20:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.5[b];[a][b]hstack",
             "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(HERE / "B04_side_by_side.mp4")])
    rep["checks"].append({"name": "side-by-side review video built", "pass": r.returncode == 0})
    rep["technical_pass"] = bool(ok)
    rep["note"] = "technical_pass covers measurable checks only; the visual verdict is in REVIEW.md"
    (HERE / "qc_report.json").write_text(json.dumps(rep, indent=1))
    for c in rep["checks"]:
        print("PASS" if c["pass"] else "FAIL", c["name"], c.get("detail", ""))
    print("energy", json.dumps(rep["energy"]))
    print("curve max err", rep["curve_fidelity"]["max_abs_error_deg"])
    print("freeze", rep["detect"])


if __name__ == "__main__":
    main()
