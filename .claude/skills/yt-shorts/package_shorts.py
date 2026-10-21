#!/usr/bin/env python3
"""Measure every Short in productions/shorts/out and write productions/shorts/SHORTS_PACKAGE.md + shorts_manifest.json (sizes, durations, sha256, loudness from the files themselves)."""
import hashlib, json, os, re, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "productions", "shorts"))
META = json.load(open(os.path.join(ROOT, "shorts_meta.json"), encoding="utf-8"))


def probe(p):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate:format=duration,size", "-of", "json", p], capture_output=True, text=True).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p, "-af", "loudnorm=print_format=summary", "-vn", "-f", "null", "-"], capture_output=True, text=True).stderr
    lufs = float(re.search(r"Input Integrated:\s+(-?[0-9.]+)", r).group(1))
    bl = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p, "-vf", "blackdetect=d=0.1:pix_th=0.05", "-an", "-f", "null", "-"], capture_output=True, text=True).stderr.count("black_start")
    dec = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "null", "-"], capture_output=True, text=True).returncode == 0
    return {"w": v["width"], "h": v["height"], "fps": v["r_frame_rate"], "seconds": round(float(j["format"]["duration"]), 2), "bytes": int(j["format"]["size"]), "lufs": lufs, "black_segments": bl, "decodes": dec}


rows, md = [], ["# OrbitalAtlas Shorts - package for owner review", "", "Nothing is published. Status of every file: REVIEW_READY, USER_APPROVED: NO. Titles are English, written for a US viewer.", ""]
for m in META:
    p = os.path.join(ROOT, "out", m["file"])
    pr = probe(p)
    sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
    rows.append(dict(m, **pr, sha256=sha))
    md += [f"## {m['file']}", f"- Origin: {m['origin']}", f"- Measured: {pr['w']}x{pr['h']} {pr['fps']} fps, {pr['seconds']} s, {pr['bytes'] / 1e6:.1f} MB, {pr['lufs']} LUFS, black segments {pr['black_segments']}, full decode {'clean' if pr['decodes'] else 'ERRORS'}",
           f"- sha256: `{sha}`" + (f" (matches the sha recorded on 2026-10-15: byte-identical)" if m.get("expected_sha") and m["expected_sha"] == sha else (f" (does NOT match the 2026-10-15 record `{m['expected_sha']}`)" if m.get("expected_sha") else "")),
           f"- YouTube Shorts title: {m['title']}", f"- Instagram Reels caption: {m['reel']}", "", "YouTube description:", "```", m["description"], "```", f"- Claims used: {m['claims']}", f"- Limits: {m['limits']}", ""]
open(os.path.join(ROOT, "SHORTS_PACKAGE.md"), "w", encoding="utf-8").write("\n".join(md))
json.dump(rows, open(os.path.join(ROOT, "shorts_manifest.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps([{k: r[k] for k in ("file", "seconds", "lufs", "black_segments", "decodes", "sha256")} for r in rows], indent=1))
