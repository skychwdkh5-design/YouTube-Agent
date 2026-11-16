#!/usr/bin/env python3
"""QA gates for renders that use the approved paper-cut character (handoff V3 docs/QA_GATES.md).

Automated part only - it does NOT replace watching the result. Checks:
  SOURCE_MATCH  asset checksums + hero pixels == exact crop of the approved sheet
  ALPHA_CHECK   alpha present; contact sheet on black/white/grey/checker written for visual review
  LAYER_CHECK   no experimental_layers anywhere in this package
  MOTION_BOUNDS roll <= 2 deg, scale <= 3 %, bob <= 10 px @540 (20 px @1080), width 12-24 %
  SCENE_CHECK   hero fully inside frame while holding, never intersects caption box, motion smoothness
  VIDEO_CHECK   1920x1080, 30 fps, H.264, frame count, full decode, black / frozen segments

  python3 -I papercut/qa.py --video test.mp4 --log log.json --report qa.json --sheets outdir/
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from papercut.host import (ASSET_DIR, GATE_BOB_PX_AT_540, GATE_ROLL_DEG, GATE_SCALE_PCT,  # noqa: E402
                           GATE_WIDTH_FRAC, HERO_OFFSET_IN_SOURCE, HERO_PATH, SOURCE_PATH)

PKG = Path(__file__).resolve().parent.parent


def check_assets():
    out = {}
    bad = []
    for line in (ASSET_DIR / "SHA256SUMS.txt").read_text().splitlines():
        digest, name = line.split(None, 1)
        if hashlib.sha256((ASSET_DIR / name.strip()).read_bytes()).hexdigest() != digest:
            bad.append(name)
    out["checksums"] = {"pass": not bad, "mismatch": bad}
    hero = np.asarray(Image.open(HERO_PATH).convert("RGBA")).astype(int)
    src = np.asarray(Image.open(SOURCE_PATH).convert("RGB")).astype(int)
    ox, oy = HERO_OFFSET_IN_SOURCE
    crop = src[oy:oy + hero.shape[0], ox:ox + hero.shape[1]]
    vis = hero[..., 3] > 0
    diff = np.abs(hero[..., :3] - crop)[vis]
    out["source_match"] = {"pass": bool(diff.max() == 0), "visible_px": int(vis.sum()),
                           "max_abs_diff": int(diff.max()), "offset_in_source": [ox, oy]}
    a = hero[..., 3]
    out["alpha"] = {"pass": bool(a.min() == 0 and a.max() == 255),
                    "touches_edges_px": {"left": int((a[:, 0] > 0).sum()), "right": int((a[:, -1] > 0).sum()),
                                         "top": int((a[0] > 0).sum()), "bottom": int((a[-1] > 0).sum())}}
    hits = [str(p.relative_to(PKG)) for p in PKG.rglob("*") if "experimental_layers" in p.name]
    out["layer_check"] = {"pass": not hits, "found": hits}
    return out


def check_log(log):
    W, H = log["size"]
    k = H / 540
    cb = log["caption_box"]
    rows = [r for r in log["log"] if r["host"]]
    viol = {"roll": [], "scale": [], "bob": [], "width": [], "cropped_while_holding": [], "caption_overlap": []}
    for r in rows:
        h, f = r["host"], r["frame"]
        if abs(h["roll_deg"]) > GATE_ROLL_DEG + 1e-6: viol["roll"].append(f)
        if abs(h["scale"] - 1) * 100 > GATE_SCALE_PCT + 1e-6: viol["scale"].append(f)
        if abs(h["bob_px"]) > GATE_BOB_PX_AT_540 * k + 1e-6: viol["bob"].append(f)
        if not (GATE_WIDTH_FRAC[0] - 1e-6 <= h["width"] / W <= GATE_WIDTH_FRAC[1] + 1e-6): viol["width"].append(f)
        b = h["bbox"]
        if b and h["phase"] == "hold" and (b[0] < 0 or b[1] < 0 or b[2] > W or b[3] > H):
            viol["cropped_while_holding"].append(f)
        if b and not (b[2] <= cb[0] or b[0] >= cb[2] or b[3] <= cb[1] or b[1] >= cb[3]):
            viol["caption_overlap"].append(f)
    # smoothness per cue: speed and acceleration of the anchor (sub-pixel), plus bbox-centre jumps
    smooth = {}
    for cue in sorted({r["host"]["cue"] for r in rows}):
        rr = [r for r in rows if r["host"]["cue"] == cue]
        p = np.array([[r["host"]["x"], r["host"]["y"]] for r in rr])
        v = np.linalg.norm(np.diff(p, axis=0), axis=1) if len(p) > 1 else np.zeros(1)
        a = np.linalg.norm(np.diff(p, 2, axis=0), axis=1) if len(p) > 2 else np.zeros(1)
        rolls = np.array([r["host"]["roll_deg"] for r in rr])
        hold = [r for r in rr if r["host"]["phase"] == "hold"]
        ph = np.array([[r["host"]["x"], r["host"]["y"]] for r in hold])
        ah = np.linalg.norm(np.diff(ph, 2, axis=0), axis=1) if len(ph) > 2 else np.zeros(1)
        smooth[cue] = {"frames": len(rr), "max_speed_px_per_frame": round(float(v.max()), 2),
                       "max_accel_px_per_frame2": round(float(a.max()), 3),
                       "max_accel_while_holding": round(float(ah.max()), 3),
                       "max_roll_step_deg": round(float(np.abs(np.diff(rolls)).max()) if len(rolls) > 1 else 0.0, 3),
                       "phases": sorted({r["host"]["phase"] for r in rr})}
    # gate: on-screen hold motion must be gentle (<= 0.5 px/frame^2), entrances/exits are eased (<= 6)
    jerk_ok = all(s["max_accel_while_holding"] <= 0.5 and s["max_accel_px_per_frame2"] <= 6 for s in smooth.values())
    return {"frames_with_host": len(rows), "violations": {k2: v2[:20] for k2, v2 in viol.items()},
            "motion_bounds_pass": not any(viol[x] for x in ("roll", "scale", "bob", "width")),
            "scene_pass": not viol["cropped_while_holding"] and not viol["caption_overlap"],
            "smoothness": smooth, "smoothness_pass": jerk_ok}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def check_video(video: Path, n_expected: int):
    pr = json.loads(run(["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(video)]).stdout)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    res = {"codec": v["codec_name"], "size": [v["width"], v["height"]], "fps": v["r_frame_rate"],
           "pix_fmt": v["pix_fmt"], "frames": int(v["nb_read_frames"]), "duration": float(pr["format"]["duration"]),
           "audio": [s["codec_name"] for s in pr["streams"] if s["codec_type"] == "audio"]}
    dec = run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"])
    res["decode_errors"] = dec.stderr.strip()[:500]
    bd = run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf", "blackdetect=d=0.1:pix_th=0.08", "-an", "-f", "null", "-"]).stderr
    res["black_segments"] = re.findall(r"black_start:[\d.]+ black_end:[\d.]+", bd)
    fz = run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf", "freezedetect=n=0.0005:d=0.5", "-an", "-f", "null", "-"]).stderr
    res["frozen_segments"] = re.findall(r"freeze_start: [\d.]+|freeze_end: [\d.]+", fz)
    res["pass"] = (res["codec"] == "h264" and res["size"] == [1920, 1080] and res["fps"] == "30/1"
                   and res["frames"] == n_expected and not res["decode_errors"] and not res["black_segments"]
                   and not res["frozen_segments"])
    return res


def sheets(video: Path, log, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", "fps=2,scale=480:-1,tile=6x5", "-frames:v", "1",
         str(outdir / "contact_sheet_every_0.5s.jpg")])
    # 1:1 crops of the hero, one row per shot, for edge / artefact review
    crops = []
    for name, a, b in log["shots"]:
        for t in np.linspace(a + 0.4, b - 0.4, 4):
            f = int(round(t * log["fps"]))
            h = log["log"][f]["host"]
            if not h or not h["bbox"]:
                continue
            x0, y0, x1, y1 = h["bbox"]
            x0, y0 = max(0, x0 - 20), max(0, y0 - 20)
            x1, y1 = min(1920, x1 + 20), min(1080, y1 + 20)
            png = outdir / f"_f{f}.png"
            run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", f"select=eq(n\\,{f})", "-vsync", "0",
                 "-frames:v", "1", str(png)])
            crops.append(Image.open(png).convert("RGB").crop((x0, y0, x1, y1)))
            png.unlink()
    if crops:
        hmax = max(c.height for c in crops)
        sheet = Image.new("RGB", (sum(c.width for c in crops[:4]) + 40, hmax * ((len(crops) + 3) // 4)), (40, 40, 40))
        x = y = 0
        for i, c in enumerate(crops):
            if i and i % 4 == 0:
                x, y = 0, y + hmax
            sheet.paste(c, (x, y)); x += c.width + 10
        sheet.save(outdir / "hero_crops_1to1.png")
    hero = Image.open(HERO_PATH).convert("RGBA")
    bg = Image.new("RGB", (hero.width * 4, hero.height))
    for i, col in enumerate([(0, 0, 0), (255, 255, 255), (128, 128, 128), None]):
        tile = Image.new("RGB", hero.size, col or (0, 0, 0))
        if col is None:
            arr = ((np.indices(hero.size[::-1]) // 16).sum(0) % 2 * 110 + 90).astype(np.uint8)
            tile = Image.fromarray(np.dstack([arr] * 3))
        tile.paste(hero, (0, 0), hero)
        bg.paste(tile, (i * hero.width, 0))
    bg.save(outdir / "alpha_check_black_white_grey_checker.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", type=Path, required=True)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--sheets", type=Path)
    a = ap.parse_args()
    log = json.loads(a.log.read_text())
    rep = {"assets": check_assets(), "scene": check_log(log), "video": check_video(a.video, log["frames"])}
    rep["automated_pass"] = (all(v["pass"] for v in rep["assets"].values()) and rep["scene"]["motion_bounds_pass"]
                             and rep["scene"]["scene_pass"] and rep["scene"]["smoothness_pass"] and rep["video"]["pass"])
    rep["note"] = "Automated checks only; visual review of the sheets and real-time playback is still required."
    a.report.write_text(json.dumps(rep, indent=2, ensure_ascii=False))
    if a.sheets:
        sheets(a.video, log, a.sheets)
    print(json.dumps({"automated_pass": rep["automated_pass"], "assets": {k: v["pass"] for k, v in rep["assets"].items()},
                      "motion": rep["scene"]["motion_bounds_pass"], "scene": rep["scene"]["scene_pass"],
                      "smooth": rep["scene"]["smoothness_pass"], "video": rep["video"]["pass"]}, indent=1))
    return 0 if rep["automated_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
