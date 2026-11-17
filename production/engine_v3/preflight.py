#!/usr/bin/env python3
"""Offline, dependency-free episode preflight. Never publishes or renders."""
import argparse
import json
import math
import sys
from pathlib import Path

ALLOWED_FAMILIES = {"live_footage", "experiment", "archive", "diagram", "paper_animation", "motion_graphics"}
LIVE_FAMILIES = {"live_footage", "experiment", "archive"}

def check(plan):
    errors, warnings = [], []
    def err(s): errors.append(s)
    shots = plan.get("shots")
    if not isinstance(shots, list) or not shots:
        return {"pass": False, "errors": ["shots must be a nonempty array"], "warnings": [], "metrics": {}}
    episode = plan.get("episode", "")
    if not isinstance(episode, str) or not episode.strip():
        err("episode identifier is required")
    approved = plan.get("approved_assets", {})
    if not isinstance(approved, dict) or not approved.get("atlas_hero_sha256"):
        err("approved_assets.atlas_hero_sha256 is required")
    else:
        value = approved["atlas_hero_sha256"]
        if value != "c313b8ade1d4c6db3e739bb979630d19be9e6d8f6220ce17f0292d12470def40":
            err("atlas_hero_sha256 does not match the approved paper-cut asset")
    if plan.get("plain_burned_subtitles") is not False:
        err("plain_burned_subtitles must be false (kinetic captions only)")
    if plan.get("kinetic_captions") is not True:
        err("kinetic_captions must be true")
    if plan.get("publish") is not False:
        err("publish must be false until owner approval")
    thumb = plan.get("thumbnail", {})
    if not isinstance(thumb, dict) or not thumb.get("sha256") or not thumb.get("first_frame_reference_sha256"):
        err("thumbnail.sha256 and thumbnail.first_frame_reference_sha256 are required")
    elif thumb["sha256"] != thumb["first_frame_reference_sha256"]:
        err("thumbnail reference and first-frame reference hashes differ; visual equality still needs QC")
    intervals = []
    prev_end = 0.0
    for i, shot in enumerate(shots):
        tag = f"shots[{i}]"
        if not isinstance(shot, dict):
            err(f"{tag} must be an object"); continue
        start, end, family = shot.get("start"), shot.get("end"), shot.get("family")
        if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in (start, end)):
            err(f"{tag} start/end must be finite numeric seconds"); continue
        if start < 0 or end <= start:
            err(f"{tag} invalid interval"); continue
        if abs(start - prev_end) > 0.001:
            err(f"{tag} gap or overlap after previous shot at {prev_end:.3f}s")
        prev_end = end
        if family not in ALLOWED_FAMILIES:
            err(f"{tag} unknown family: {family}"); continue
        if family in LIVE_FAMILIES:
            source = shot.get("source")
            if not isinstance(source, dict) or not all(source.get(k) for k in ("url", "license", "credit")):
                err(f"{tag} live/archive footage needs source url, license and credit")
        intervals.append((start, end, family))
    total = sum(b-a for a,b,_ in intervals)
    live = sum(b-a for a,b,f in intervals if f in LIVE_FAMILIES)
    ratio = live/total if total else 0
    if total <= 0: err("total planned duration must be positive")
    if ratio < 0.70 - 1e-9: err(f"live/experiment/archive footage share {ratio:.1%} is below 70%")
    if intervals and abs(intervals[0][0]) > 0.001: err("first shot must begin at t=0")
    if not plan.get("owner_approval_required", False):
        err("owner_approval_required must be true")
    warnings.append("Preflight checks metadata, not footage authenticity, movement quality, license validity or pixel equality.")
    return {"pass": not errors, "errors": errors, "warnings": warnings, "metrics": {"duration_s": round(total,3), "live_s": round(live,3), "live_share": round(ratio,4), "shot_count": len(shots)}}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("plan",type=Path)
    ap.add_argument("--report",type=Path)
    args=ap.parse_args()
    try: report=check(json.loads(args.plan.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError) as e:
        report={"pass":False,"errors":[str(e)],"warnings":[],"metrics":{}}
    output=json.dumps(report,ensure_ascii=False,indent=2)
    if args.report: args.report.write_text(output+"\n",encoding="utf-8")
    print(output)
    return 0 if report["pass"] else 1

if __name__=="__main__": sys.exit(main())
