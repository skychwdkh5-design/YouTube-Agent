#!/usr/bin/env python3
"""qc.py - check a rendered MP4 with FFprobe/FFmpeg before anyone calls it finished.

    python3 qc.py final.mp4
    python3 qc.py final.mp4 --timeline timeline.json          # expected duration from the timeline
    python3 qc.py final.mp4 --expected-duration 10.5 --quick  # skip the full decode pass

Prints JSON with "result": "PASS" or "FAIL" and one entry per check. Exit code 0 = PASS,
1 = FAIL, 2 = could not run (bad arguments, ffprobe missing).

Defaults match the yt-render v1 spec: 1920x1080, 30 fps, H.264 + AAC in an MP4, under 2000 MB.
Override with --width/--height/--fps/--vcodec/--acodec/--max-mb.

--profile short (vertical Shorts): 1080x1920, 35-60 s (45-55 target, warn), no black frames,
static freezes (warn 1.5 s, fail 2.5 s), loudness (warn outside -16..-12 LUFS), audio within
0.5 s, and - from the render manifest (<video>.manifest.json or --manifest) - >= 5 information
events in the first 10 s, >= 3 distinct compositions in the first 10 s (fail), about 7-10
composition resets and no composition held over 6 s (warn), visual-family novelty when the storyboard
tags visual_family (>= 3 families in the first 10 s, >= 6 transitions, no family over 10 s unless it is
transforming - warn only), captions inside the Shorts safe area
and a source credit on every shot.
--profile long (16:9 documentary, timeline v3 "long"): 1920x1080 30 fps, 60-900 s (480-720 target, warn),
black frames, freezes (warn 2.5 s, fail 5 s), loudness, audio within 1 s, captions inside the 16:9 safe
area, a credit on every shot, composition and visual-family checks as rates (warnings), and for segmented
renders: the segments tile the video frame-exactly and every segment boundary is a keyframe.
--contact-sheet out.jpg writes the first frame plus the middle of every shot.

Each check is one function in CHECKS returning {"id", "status", "expected", "actual", "detail"}
with status pass / fail / warn / skip. Only "fail" fails the file. Later checks (loudness,
black frames, silence, subtitles, licence manifest) are added as more functions in the same list.
"""
import json, math, os, re, subprocess, sys, tempfile

DEFAULTS = {"width": 1920, "height": 1080, "fps": 30.0, "vcodec": "h264", "acodec": "aac",
            "max_mb": 2000.0, "tolerance": 0.25, "timeout": 900}
MP4_FORMAT = "mp4"  # ffprobe reports "mov,mp4,m4a,3gp,3g2,mj2" for MP4


class QCError(Exception):
    pass


def _run(cmd, timeout):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise QCError(f"{cmd[0]} is not installed or not on PATH")
    except subprocess.TimeoutExpired:
        raise QCError(f"{cmd[0]} timed out after {timeout}s")


def _rate(s):
    try:
        n, d = (s or "0/0").split("/")
        return float(n) / float(d) if float(d) else 0.0
    except ValueError:
        return 0.0


def _f(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def _check(cid, ok, expected=None, actual=None, detail=None, warn=False):
    status = "pass" if ok else ("warn" if warn else "fail")
    return {"id": cid, "status": status, "expected": expected, "actual": actual,
            **({"detail": detail} if detail else {})}


def _skip(cid, detail):
    return {"id": cid, "status": "skip", "expected": None, "actual": None, "detail": detail}


# --- checks: ctx -> list of results --------------------------------------------------------------

def check_file(ctx):
    p, spec = ctx["path"], ctx["spec"]
    size = ctx["size"]
    return [_check("file_size", 0 < size <= spec["max_mb"] * 1048576,
                   f"> 0 and <= {spec['max_mb']} MB", size, None if size else "file is empty")]


def check_container(ctx):
    fmt = ctx["probe"].get("format") or {}
    names = (fmt.get("format_name") or "").split(",")
    return [_check("container", MP4_FORMAT in names, "mp4", fmt.get("format_name"))]


def check_streams(ctx):
    v, a = ctx["video"], ctx["audio"]
    spec = ctx["spec"]
    out = [_check("video_stream", v is not None, "1 video stream", len(ctx["videos"])),
           _check("audio_stream", a is not None, "1 audio stream", len(ctx["audios"]))]
    if v is not None:
        fps = _rate(v.get("avg_frame_rate")) or _rate(v.get("r_frame_rate"))
        out += [_check("resolution", (v.get("width"), v.get("height")) == (spec["width"], spec["height"]),
                       f"{spec['width']}x{spec['height']}", f"{v.get('width')}x{v.get('height')}"),
                _check("frame_rate", abs(fps - spec["fps"]) < 0.01, spec["fps"], round(fps, 3)),
                _check("video_codec", v.get("codec_name") == spec["vcodec"], spec["vcodec"],
                       v.get("codec_name")),
                _check("pixel_format", v.get("pix_fmt") == "yuv420p", "yuv420p", v.get("pix_fmt"),
                       "other pixel formats play badly on some devices", warn=True)]
    else:
        out += [_skip(c, "no video stream") for c in ("resolution", "frame_rate", "video_codec", "pixel_format")]
    if a is not None:
        out.append(_check("audio_codec", a.get("codec_name") == spec["acodec"], spec["acodec"],
                          a.get("codec_name")))
    else:
        out.append(_skip("audio_codec", "no audio stream"))
    return out


def check_duration(ctx):
    fmt_d = _f((ctx["probe"].get("format") or {}).get("duration"))
    out = [_check("duration_readable", fmt_d is not None and fmt_d > 0, "> 0 s", fmt_d)]
    exp, tol = ctx["expected_duration"], ctx["spec"]["tolerance"]
    if exp is None:
        out.append(_skip("duration_matches_timeline", "no --timeline or --expected-duration given"))
    elif fmt_d is not None:
        out.append(_check("duration_matches_timeline", abs(fmt_d - exp) <= tol,
                          f"{exp} s ± {tol}", round(fmt_d, 3)))
    # truncation: streams that end well before the container says, or frames missing
    v, a = ctx["video"], ctx["audio"]
    vd = _f(v.get("duration")) if v else None
    ad = _f(a.get("duration")) if a else None
    if fmt_d and vd is not None and ad is not None:
        out.append(_check("streams_aligned", abs(vd - ad) <= max(tol, 0.1) and abs(fmt_d - vd) <= max(tol, 0.1),
                          "video, audio and container end together",
                          {"container": fmt_d, "video": vd, "audio": ad}))
    if v and vd:
        nb, fps = v.get("nb_frames"), _rate(v.get("avg_frame_rate"))
        if nb and fps:
            want = round(vd * fps)
            out.append(_check("frame_count", abs(int(nb) - want) <= 1, want, int(nb)))
    return out


def check_decode(ctx):
    if ctx["quick"]:
        return [_skip("full_decode", "--quick")]
    r = _run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-xerror", "-i", ctx["path"],
              "-map", "0", "-f", "null", "-"], ctx["spec"]["timeout"])
    err = r.stderr.strip()
    return [_check("full_decode", r.returncode == 0 and not err, "decodes with no errors",
                   "ok" if r.returncode == 0 and not err else "errors", err[-400:] or None)]


CHECKS = [check_file, check_container, check_streams, check_duration, check_decode]

# --- profile "short" (vertical YouTube Shorts) ---------------------------------------------------
PROFILES = {"short": {"width": 1080, "height": 1920, "fps": 30.0, "min_s": 35.0, "max_s": 60.0,
                      "target": (45.0, 55.0), "black_s": 0.1, "freeze_warn": 1.5, "freeze_fail": 2.5,
                      "lufs": (-16.0, -12.0), "first_audio_s": 0.5, "events_first_10s": 5,
                      "compositions_first_10s": 3, "composition_resets": (7, 10), "composition_hold_s": 6.0,
                      "families_first_10s": 3, "family_transitions": 6, "family_max_s": 10.0},
            # long-form 16:9 documentary (timeline v3 profile "long"): creative checks are rates and warnings
            "long": {"name": "long", "width": 1920, "height": 1080, "fps": 30.0, "min_s": 60.0, "max_s": 900.0,
                     "target": (480.0, 720.0), "black_s": 0.1, "freeze_warn": 2.5, "freeze_fail": 5.0,
                     "lufs": (-16.0, -12.0), "first_audio_s": 1.0, "events_first_10s": 3, "events_warn": True,
                     "compositions_first_10s": 3, "first10_warn": True, "resets_per_min": 5.0,
                     "composition_hold_s": 8.0, "families_first_10s": 3, "families_per_min": 2.0,
                     "family_max_s": 30.0, "safe_name": "16:9 safe area"}}


def check_short_duration(ctx):
    P, d = ctx["profile"], _f((ctx["probe"].get("format") or {}).get("duration")) or 0
    lo, hi = P["target"]
    name = P.get("name", "short")
    return [_check(f"{name}_duration", P["min_s"] <= d <= P["max_s"], f"{P['min_s']}-{P['max_s']} s", round(d, 3)),
            _check(f"{name}_target_window", lo <= d <= hi, f"{lo}-{hi} s", round(d, 3), warn=True)]


def _filter_log(ctx, args):
    r = _run(["ffmpeg", "-hide_banner", "-nostdin", "-i", ctx["path"], *args, "-f", "null", "-"], ctx["spec"]["timeout"])
    return r.stderr


def check_black(ctx):
    if not ctx["video"]:
        return [_skip("black_frames", "no video stream")]
    log = _filter_log(ctx, ["-an", "-vf", f"blackdetect=d={ctx['profile']['black_s']}:pix_th=0.10"])
    hits = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", log)
    return [_check("black_frames", not hits, "none", [[float(a), float(b)] for a, b in hits] or 0)]


def check_freeze(ctx):
    if not ctx["video"]:
        return [_skip("freezes", "no video stream")]
    P = ctx["profile"]
    log = _filter_log(ctx, ["-an", "-vf", f"freezedetect=n=0.0015:d={P['freeze_warn']}"])
    durs = [float(x) for x in re.findall(r"freeze_duration: ?([\d.]+)", log)]
    worst = max(durs) if durs else 0
    if worst >= P["freeze_fail"]:
        return [_check("freezes", False, f"< {P['freeze_fail']} s static", round(worst, 2))]
    return [_check("freezes", worst < P["freeze_warn"], f"< {P['freeze_warn']} s static", round(worst, 2), warn=True)]


def check_audio(ctx):
    if not ctx["audio"]:
        return [_skip("loudness", "no audio stream"), _skip("audio_starts", "no audio stream")]
    P = ctx["profile"]
    log = _filter_log(ctx, ["-vn", "-af", "ebur128=peak=true"])
    summ = log[log.rfind("Summary:"):]
    m = re.search(r"I:\s*(-?[\d.]+) LUFS", summ)
    lufs = float(m.group(1)) if m else None
    lo, hi = P["lufs"]
    out = []
    if lufs is None or lufs < -40:
        out.append(_check("loudness", False, f"{lo} to {hi} LUFS", lufs, "no programme loudness - silent?"))
    else:
        out.append(_check("loudness", lo <= lufs <= hi, f"{lo} to {hi} LUFS", lufs,
                          "levelling to the Shorts target needs a timing-safe limiter (not built yet)", warn=True))
    log = _filter_log(ctx, ["-vn", "-af", "silencedetect=n=-40dB:d=0.2"])
    first = re.search(r"silence_start: ?(-?[\d.]+)", log)
    start = 0.0
    if first and abs(float(first.group(1))) < 0.05:
        end = re.search(r"silence_end: ?([\d.]+)", log)
        start = float(end.group(1)) if end else ctx["spec"].get("duration_hint", 999)
    out.append(_check("audio_starts", start <= P["first_audio_s"], f"<= {P['first_audio_s']} s", round(start, 3)))
    return out


def check_manifest(ctx):
    m = ctx.get("manifest")
    if not m:
        return [_skip("manifest", "no render manifest (pass --manifest or keep <video>.manifest.json)")]
    P, W, H = ctx["profile"], m.get("width"), m.get("height")
    out = []
    ev = [e for e in m.get("info_events") or [] if e["t"] < 10]
    out.append(_check("info_events_first_10s", len(ev) >= P["events_first_10s"], f">= {P['events_first_10s']}", len(ev),
                      warn=P.get("events_warn", False)))
    safe = m.get("safe") or {}
    bad = []
    for c in m.get("caption_boxes") or []:
        x0, y0, x1, y1 = c["box"]
        if (y0 < H * safe.get("top", 0) or y1 > H * (1 - safe.get("bottom", 0)) or
                x1 > W * (1 - safe.get("right", 0)) or x0 < W * safe.get("left", 0)):
            bad.append(c["cue"])
    out.append(_check("captions_in_safe_zone", not bad, f"every caption inside the {P.get('safe_name', 'Shorts safe area')}",
                      "ok" if not bad else {"cues": bad}))
    missing = [s["id"] for s in m.get("shots") or [] if not s.get("credit")]
    out.append(_check("shot_credits", not missing, "a source credit on every shot", "ok" if not missing else missing))
    d = _f((ctx["probe"].get("format") or {}).get("duration")) or 0
    out.append(_check("manifest_matches", abs(d - float(m.get("duration") or 0)) <= 0.1, m.get("duration"), round(d, 3)))
    return out


def check_compositions(ctx):
    """Composition resets from the render manifest: a cut or camera move to a materially different
    view, a full-frame wipe or a timelapse. New text, numbers or overlays on the same view do not
    count. Counted from the manifest's reset list, not from its summary fields."""
    m = ctx.get("manifest")
    c = (m or {}).get("compositions")
    if not c:
        return [_skip("composition_resets", "the render manifest has no 'compositions' block "
                      "(rendered before the composition rule; render.py's plan reports it from the timeline)")]
    P = ctx["profile"]
    resets = [x for x in c.get("resets") or [] if isinstance(x, dict) and _f(x.get("t")) is not None]
    first = 1 + sum(1 for x in resets if _f(x["t"]) < 10)
    holds = [x for x in c.get("segments") or [] if isinstance(x, dict) and _f(x.get("static_hold")) is not None]
    worst = max(holds, key=lambda x: _f(x["static_hold"])) if holds else None
    detail = [f"{x['t']}s {x.get('shot')}: {x.get('kind')}" for x in resets]
    out = [_check("compositions_first_10s", first >= P["compositions_first_10s"],
                  f">= {P['compositions_first_10s']} distinct compositions", first, warn=P.get("first10_warn", False))]
    if "resets_per_min" in P:
        minutes = max((_f((m or {}).get("duration")) or 0) / 60.0, 1e-9)
        rate = round(len(resets) / minutes, 2)
        out.append(_check("composition_resets", rate >= P["resets_per_min"], f">= {P['resets_per_min']} per minute",
                          rate, detail, warn=True))
    else:
        lo, hi = P["composition_resets"]
        out.append(_check("composition_resets", lo <= len(resets) <= hi, f"about {lo}-{hi}", len(resets), detail,
                          warn=True))
    if worst is None:
        out.append(_skip("composition_hold", "no segments in the manifest"))
    else:
        out.append(_check("composition_hold", _f(worst["static_hold"]) <= P["composition_hold_s"],
                          f"<= {P['composition_hold_s']} s on one composition", _f(worst["static_hold"]),
                          f"{worst.get('start')}-{worst.get('end')} s", warn=True))
    return out


def check_visual_novelty(ctx):
    """Visual-family transitions from the storyboard tags in the manifest. A new composition of the same
    visual idea is not new. Creative warnings only; recounted from the manifest's runs."""
    v = (ctx.get("manifest") or {}).get("visual_novelty")
    if not v:
        return [_skip("visual_novelty", "no visual_family tags in the storyboard/manifest")]
    P = ctx["profile"]
    runs = [x for x in v.get("runs") or [] if isinstance(x, dict) and _f(x.get("start")) is not None and x.get("family")]
    if not runs:
        return [_skip("visual_novelty", "the manifest's visual_novelty block has no runs")]
    first = len({x["family"] for x in runs if _f(x["start"]) < 10})
    longest = max(runs, key=lambda x: _f(x.get("untransformed")) or 0)
    held = _f(longest.get("untransformed")) or 0
    trans = [f"{x['start']}s {x['family']}" for x in runs]
    if "families_per_min" in P:
        minutes = max((_f((ctx.get("manifest") or {}).get("duration")) or 0) / 60.0, 1e-9)
        rate = round((len(runs) - 1) / minutes, 2)
        tcheck = _check("visual_family_transitions", rate >= P["families_per_min"], f">= {P['families_per_min']} per minute",
                        rate, trans, warn=True)
    else:
        tcheck = _check("visual_family_transitions", len(runs) - 1 >= P["family_transitions"],
                        f">= {P['family_transitions']}", len(runs) - 1, trans, warn=True)
    return [_check("visual_families_first_10s", first >= P["families_first_10s"], f">= {P['families_first_10s']}", first,
                   warn=True),
            tcheck,
            _check("visual_family_dominance", held <= P["family_max_s"], f"<= {P['family_max_s']} s of one family "
                   "unless it is transforming", held, f"{longest['family']} {longest.get('start')}-{longest.get('end')} s",
                   warn=True)]


def check_segments(ctx):
    """Segmented long renders: the manifest's segments must tile the video frame-exactly, and every
    segment boundary must be a keyframe in the joined file (proof the concat did not re-encode or shift)."""
    m = ctx.get("manifest") or {}
    segs = m.get("segments")
    if not segs:
        return [_skip("segments", "no segments in the manifest (rendered in one pass)")]
    fps = _f(m.get("fps")) or 30.0
    total = round((_f(m.get("duration")) or 0) * fps)
    pos, gaps = 0, []
    for sgm in segs:
        if sgm.get("start_frame") != pos:
            gaps.append(sgm.get("index"))
        pos = (sgm.get("start_frame") or 0) + (sgm.get("frames") or 0)
    out = [_check("segments_tile_video", not gaps and pos == total, f"{total} frames, contiguous",
                  {"frames": pos, "gaps_at": gaps} if gaps or pos != total else pos)]
    r = _run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-skip_frame", "nokey", "-show_entries",
              "frame=pts_time", "-of", "csv=p=0", ctx["path"]], ctx["spec"]["timeout"])
    keys = [_f(x.split(",")[0]) for x in r.stdout.split() if _f(x.split(",")[0]) is not None]
    missing = [sgm["index"] for sgm in segs
               if not any(abs(k - sgm["start_frame"] / fps) < 0.5 / fps for k in keys)]
    out.append(_check("segment_boundaries_keyframes", not missing, "a keyframe at every segment start",
                      "ok" if not missing else {"segments": missing}))
    return out


SHORT_CHECKS = [check_short_duration, check_black, check_freeze, check_audio, check_manifest, check_compositions,
                check_visual_novelty]
LONG_CHECKS = SHORT_CHECKS + [check_segments]


def contact_sheet(path, manifest, out, timeout=300):
    """First frame + the middle of every shot, labelled - for the human review step."""
    from PIL import Image, ImageDraw
    times = [(0.0, "first frame")] + [(round((s["start"] + s["end"]) / 2, 2), s["id"]) for s in manifest["shots"]]
    landscape = (manifest.get("width") or 0) > (manifest.get("height") or 0)
    size, per_row = ((480, 270), 4) if landscape else ((270, 480), 7)
    tiles = []
    with tempfile.TemporaryDirectory() as tmp:
        for k, (t, name) in enumerate(times):
            p = os.path.join(tmp, f"{k}.png")
            r = _run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", path, "-frames:v", "1", p], timeout)
            if r.returncode != 0 or not os.path.exists(p):
                raise QCError(f"contact sheet: cannot read a frame at {t}s")
            tiles.append((Image.open(p).convert("RGB").resize(size), f"{name}  {t:.1f}s"))
    cols = min(per_row, len(tiles))
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * size[0], rows * (size[1] + 30)), "black")
    d = ImageDraw.Draw(sheet)
    for i, (im, label) in enumerate(tiles):
        x, y = (i % cols) * size[0], (i // cols) * (size[1] + 30)
        sheet.paste(im, (x, y))
        d.text((x + 6, y + size[1] + 8), label, fill="white")
    sheet.save(out, quality=90)
    return out


# --- driver ------------------------------------------------------------------------------------

def run_qc(path, spec=None, expected_duration=None, quick=False, profile=None, manifest=None):
    prof = PROFILES.get(profile) if profile else None
    base = dict(DEFAULTS, **({k: prof[k] for k in ("width", "height", "fps")} if prof else {}))
    spec = dict(base, **(spec or {}))
    path = os.path.abspath(path)
    if not os.path.exists(path):
        return {"result": "FAIL", "file": path,
                "checks": [_check("file_exists", False, "exists", "missing")]}
    if not os.path.isfile(path):
        return {"result": "FAIL", "file": path,
                "checks": [_check("file_exists", False, "regular file", "not a regular file")]}
    checks = [_check("file_exists", True, "exists", "exists")]
    r = _run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", path], 60)
    probe = None
    if r.returncode == 0:
        try:
            probe = json.loads(r.stdout or "{}")
        except ValueError:
            pass
    checks.append(_check("container_readable", probe is not None, "ffprobe reads the file",
                         "ok" if probe is not None else "unreadable",
                         None if probe is not None else (r.stderr.strip()[-300:] or None)))
    if probe is None:
        return {"result": "FAIL", "file": path, "checks": checks}
    streams = probe.get("streams") or []
    videos = [s for s in streams if s.get("codec_type") == "video"
              and not (s.get("disposition") or {}).get("attached_pic")]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    ctx = {"path": path, "spec": spec, "probe": probe, "size": os.path.getsize(path),
           "videos": videos, "audios": audios,
           "video": videos[0] if len(videos) == 1 else None,
           "audio": audios[0] if len(audios) == 1 else None,
           "expected_duration": expected_duration, "quick": quick, "profile": prof, "manifest": manifest}
    for fn in CHECKS + ((LONG_CHECKS if prof.get("name") == "long" else SHORT_CHECKS) if prof else []):
        checks += fn(ctx)
    fmt = probe.get("format") or {}
    v, a = ctx["video"] or {}, ctx["audio"] or {}
    return {"result": "FAIL" if any(c["status"] == "fail" for c in checks) else "PASS",
            "file": path,
            "summary": {"bytes": ctx["size"], "duration": _f(fmt.get("duration")),
                        "resolution": f"{v.get('width')}x{v.get('height')}" if v else None,
                        "fps": round(_rate(v.get("avg_frame_rate")), 3) if v else None,
                        "video_codec": v.get("codec_name"), "audio_codec": a.get("codec_name"),
                        "expected_duration": expected_duration, "profile": profile},
            "checks": checks}


def _timeline_duration(path, media_root=None):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "yt-render"))
    try:
        import render
    except ImportError:
        raise QCError("--timeline needs the yt-render skill next to yt-qc")
    try:
        return render.expected_duration(path, media_root)
    except render.RenderError as e:
        raise QCError(f"timeline: {e}")


def _flag(a, name, kind=str, lo=None):
    if name not in a: return None
    i = a.index(name)
    if i + 1 >= len(a) or a[i + 1].startswith("--"):
        raise QCError(f"{name} needs a value")
    raw = a[i + 1]
    if kind is str: return raw
    try:
        v = kind(raw)
    except ValueError:
        raise QCError(f"{name} expects a number, got {raw!r}")
    if not math.isfinite(v) or (lo is not None and v < lo):
        raise QCError(f"{name} must be a finite number >= {lo}, got {raw!r}")
    return v


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or "-h" in a or "--help" in a:
        print(__doc__); return 0
    try:
        valued = {"--timeline", "--media-root", "--expected-duration", "--width", "--height", "--fps",
                  "--vcodec", "--acodec", "--max-mb", "--tolerance", "--timeout", "--profile", "--manifest",
                  "--contact-sheet"}
        unknown = [x for x in a if x.startswith("--") and x not in valued | {"--quick"}]
        if unknown: raise QCError(f"unknown option(s): {unknown}")
        values = {a[i + 1] for i, x in enumerate(a[:-1]) if x in valued}
        files = [x for x in a if not x.startswith("--") and x not in values]
        if len(files) != 1: raise QCError("give exactly one MP4 to check")
        spec = {}
        for name, key, kind, lo in (("--width", "width", int, 16), ("--height", "height", int, 16),
                                    ("--fps", "fps", float, 1), ("--max-mb", "max_mb", float, 0.001),
                                    ("--tolerance", "tolerance", float, 0), ("--timeout", "timeout", int, 1)):
            v = _flag(a, name, kind, lo)
            if v is not None: spec[key] = v
        for name, key in (("--vcodec", "vcodec"), ("--acodec", "acodec")):
            if _flag(a, name): spec[key] = _flag(a, name)
        exp = _flag(a, "--expected-duration", float, 0)
        if _flag(a, "--timeline"):
            if exp is not None: raise QCError("use --timeline or --expected-duration, not both")
            exp = _timeline_duration(_flag(a, "--timeline"), _flag(a, "--media-root"))
        profile = _flag(a, "--profile")
        if profile is not None and profile not in PROFILES:
            raise QCError(f"--profile must be one of {sorted(PROFILES)}")
        manifest, mpath = None, _flag(a, "--manifest")
        if mpath is None and profile:
            guess = os.path.splitext(files[0])[0] + ".manifest.json"
            mpath = guess if os.path.isfile(guess) else None
        if mpath:
            try:
                with open(mpath, encoding="utf-8") as f:
                    manifest = json.load(f)
            except (OSError, ValueError) as e:
                raise QCError(f"manifest unreadable: {type(e).__name__}: {e}")
        report = run_qc(files[0], spec, exp, "--quick" in a, profile, manifest)
        sheet = _flag(a, "--contact-sheet")
        if sheet:
            if not manifest:
                raise QCError("--contact-sheet needs the render manifest")
            report["contact_sheet"] = contact_sheet(files[0], manifest, sheet)
        print(json.dumps(report, indent=1, default=str))
        return 0 if report["result"] == "PASS" else 1
    except QCError as e:
        print(json.dumps({"result": "ERROR", "status": "error", "error": str(e)}, indent=1))
        return 2
    except Exception as e:  # never a traceback
        print(json.dumps({"result": "ERROR", "status": "error",
                          "error": f"unexpected {type(e).__name__}: {e}"}, indent=1))
        return 2


if __name__ == "__main__":
    sys.exit(main())
