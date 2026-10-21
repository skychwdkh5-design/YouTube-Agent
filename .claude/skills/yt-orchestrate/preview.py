#!/usr/bin/env python3
"""preview.py - the full film as a light 720p preview, rendered chapter by chapter IN PARALLEL on the real timeline, real narration and real captions, with a render cache and an automatic QC.
Never the final master (that stays behind the owner's --allow-render).

    python3 preview.py --slug neom-line [--jobs 4] [--force]

Cache: a chapter is re-rendered only if its shots, the pictures they use, the narration, the captions or the renderer changed (render/preview_cache.json).
Output: render/<slug>_preview_720p.mp4, render/preview_qc.json, render/preview_report.json (timings per chapter).
"""
import argparse, concurrent.futures as cf, hashlib, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SK = os.path.join(REPO, ".claude", "skills")
PY = sys.executable


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def chapter_key(root, tl, t0, t1):
    shots = [s for s in tl["shots"] if t0 - 1e-6 <= s["start"] < t1 + 0.5]
    def used(L):
        return [L.get("asset")] + ([L.get("from"), L.get("to")] if L.get("type") == "wipe" else []) + (list(L.get("assets") or []) if L.get("type") == "flip" else [])
    assets = sorted({x for s in shots for L in s["layers"] for x in used(L) if isinstance(x, str)})
    files = {a: sha_file(os.path.join(root, tl["assets"][a]["src"])) for a in assets if a in tl["assets"] and os.path.exists(os.path.join(root, tl["assets"][a]["src"]))}
    h = hashlib.sha256()
    h.update(json.dumps([shots, files, tl.get("captions"), tl.get("end")], sort_keys=True).encode())
    for f in ("voice/narration.wav", "captions/captions.srt"):
        h.update(sha_file(os.path.join(root, f)).encode())
    for f in (os.path.join(SK, "yt-render", "compose.py"), os.path.join(SK, "yt-orchestrate", "orchestrate.py")):
        h.update(sha_file(f).encode())
    return h.hexdigest()


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def render_chapter(slug, root, cid, t0, t1, name):
    t = time.time()
    r = run([PY, os.path.join(SK, "yt-orchestrate", "orchestrate.py"), "render-test", "--slug", slug, "--start", f"{t0:.3f}", "--seconds", f"{t1 - t0:.3f}", "--name", name, "--run"], cwd=REPO)
    try:
        d = json.loads(r.stdout)
    except ValueError:
        d = {"status": "error", "error": (r.stderr or r.stdout)[-300:]}
    return cid, d, time.time() - t


def encode_720(src, trim_from, t_len, dst):
    """Re-encode to 720p, starting trim_from seconds into the file (the render begins at a shot boundary at or before the chapter) for t_len seconds."""
    vf = "scale=1280:720,fps=30,format=yuv420p"
    cmd = ["ffmpeg", "-v", "error", "-y"] + (["-ss", f"{trim_from:.3f}"] if trim_from else []) + ["-i", src] + (["-t", f"{t_len:.3f}"] if t_len else []) + ["-vf", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "29", "-c:a", "aac", "-b:a", "96k", "-ar", "44100", "-ac", "2", dst]
    r = run(cmd)
    if r.returncode:
        raise RuntimeError(r.stderr[-300:])


def qc(path, expected_s):
    pr = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_name,codec_type,width,height,r_frame_rate", "-of", "json", path]).stdout)
    v = next((s for s in pr["streams"] if s["codec_type"] == "video"), {}); a = next((s for s in pr["streams"] if s["codec_type"] == "audio"), {})
    dur = float(pr["format"]["duration"])
    dec = [l for l in run(["ffmpeg", "-v", "error", "-i", path, "-f", "null", "-"]).stderr.splitlines() if l.strip()]
    eb = run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", eb); tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", eb)
    bl = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", run(["ffmpeg", "-nostats", "-i", path, "-vf", "blackdetect=d=0.5:pix_th=0.05", "-an", "-f", "null", "-"]).stderr)
    fz = run(["ffmpeg", "-nostats", "-i", path, "-vf", "freezedetect=n=-55dB:d=6", "-an", "-f", "null", "-"]).stderr
    fs_, fd_ = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", fz)], [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", fz)]
    freeze = [(st, fd_[i] if i < len(fd_) else round(dur - st, 2)) for i, st in enumerate(fs_)]       # a freeze that lasts to the end of the file has no duration line
    sil = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", run(["ffmpeg", "-nostats", "-i", path, "-af", "silencedetect=n=-45dB:d=2.5", "-vn", "-f", "null", "-"]).stderr)]
    checks = [
        ("format", v.get("codec_name") == "h264" and (v.get("width"), v.get("height")) == (1280, 720) and a.get("codec_name") == "aac", f"{v.get('codec_name')} {v.get('width')}x{v.get('height')} / {a.get('codec_name')}", "fail"),
        ("duration", expected_s - 0.5 <= dur <= expected_s + 2.5, f"{dur:.2f}s (narration {expected_s:.2f}s + tail)", "fail"),
        ("decode", not dec, "clean" if not dec else dec[:2], "fail"),
        ("loudness", bool(lufs) and -26 <= float(lufs[-1]) <= -10 and bool(tp) and float(tp[-1]) <= -0.1, f"{lufs[-1] if lufs else '?'} LUFS, true peak {tp[-1] if tp else '?'} dBFS", "fail"),
        ("black_frames", not bl, "none" if not bl else bl, "fail"),
        ("freeze_over_6s", not freeze, "none" if not freeze else freeze, "warn"),
        ("silence_over_2_5s", not sil, "none" if not sil else sil, "warn"),
    ]
    res = "FAIL" if any(not ok and lvl == "fail" for _, ok, _, lvl in checks) else "WARN" if any(not ok for _, ok, _, _ in checks) else "PASS"
    return {"result": res, "checks": [{"id": i, "ok": ok, "detail": d, "level": l} for i, ok, d, l in checks], "duration_s": round(dur, 2), "size_mb": round(int(pr["format"]["size"]) / 1e6, 1)}


def build(slug, jobs=4, force=False):
    root = os.path.join(REPO, "productions", slug)
    t_all = time.time()
    tl = json.load(open(os.path.join(root, "timeline.json")))
    sb = json.load(open(os.path.join(root, "story", "storyboard.json")))
    voice = json.load(open(os.path.join(root, "voice", "narration.voice.json")))["duration"]
    cp = os.path.join(root, "render", "preview_cache.json")
    cache = json.load(open(cp)) if os.path.exists(cp) and not force else {}
    firsts = {}
    for s in sb["shots"]:
        firsts.setdefault(s["chapter"], s["start"])           # exact chapter boundaries = the first shot of each chapter (the rounded chapter times would drift by a few ms per seam)
    ids = list(sb["chapters"].keys())
    chapters = [(c, firsts[c], firsts[ids[i + 1]] if i + 1 < len(ids) else sb["chapters"][c][1]) for i, c in enumerate(ids)]
    todo, report = [], {}
    for cid, t0, t1 in chapters:
        key = chapter_key(root, tl, t0, t1)
        name = f"pvc_{cid}"
        f720 = os.path.join(root, "render", name, "seg720.mp4")
        if cache.get(cid, {}).get("key") == key and os.path.exists(f720):
            report[cid] = {"cached": True, "seconds": 0.0}
        else:
            todo.append((cid, t0, t1, name, key))
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        futs = [ex.submit(render_chapter, slug, root, cid, t0, t1, name) for cid, t0, t1, name, _ in todo]
        for f in cf.as_completed(futs):
            cid, d, secs = f.result()
            report[cid] = {"cached": False, "seconds": round(secs, 1), "status": d.get("status"), "error": d.get("error")}
    for cid, t0, t1, name, key in todo:
        if report[cid].get("status") != "ok":
            raise SystemExit(f"chapter {cid} failed: {report[cid]}")
    # trim to the chapter and re-encode to 720p (parallel); the last chapter keeps its natural tail
    def enc(item):
        cid, t0, t1, name, key = item
        src = os.path.join(root, "render", name, f"{name}.mp4")
        last = cid == chapters[-1][0]
        voice_meta = json.load(open(os.path.join(root, "render", name, f"narration.{name}.voice.json")))
        encode_720(src, max(t0 - voice_meta.get("excerpt_from", 0.0), 0.0), None if last else t1 - t0, os.path.join(root, "render", name, "seg720.mp4"))
        return cid, key
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        for cid, key in ex.map(enc, todo):
            cache[cid] = {"key": key}
    json.dump(cache, open(cp, "w"), indent=1)
    lst = os.path.join(root, "render", "preview_list.txt")
    open(lst, "w").write("".join(f"file '{os.path.join(root, 'render', f'pvc_{c}', 'seg720.mp4')}'\n" for c, _, _ in chapters))
    out = os.path.join(root, "render", f"{slug}_preview_720p.mp4")
    r = run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out])
    if r.returncode:
        raise SystemExit(r.stderr[-300:])
    t_render = time.time() - t_all
    q = qc(out, voice)
    json.dump(q, open(os.path.join(root, "render", "preview_qc.json"), "w"), indent=1)
    rep = {"slug": slug, "output": os.path.relpath(out, root), "jobs": jobs, "chapters": report, "render_wall_s": round(t_render, 1), "qc_wall_s": round(time.time() - t_all - t_render, 1), "qc": q["result"]}
    json.dump(rep, open(os.path.join(root, "render", "preview_report.json"), "w"), indent=1)
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--slug", required=True); ap.add_argument("--jobs", type=int, default=4); ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    print(json.dumps(build(a.slug, a.jobs, a.force)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
