#!/usr/bin/env python3
"""qc.py - check a rendered MP4 with FFprobe/FFmpeg before anyone calls it finished.

    python3 qc.py final.mp4
    python3 qc.py final.mp4 --timeline timeline.json          # expected duration from the timeline
    python3 qc.py final.mp4 --expected-duration 10.5 --quick  # skip the full decode pass

Prints JSON with "result": "PASS" or "FAIL" and one entry per check. Exit code 0 = PASS,
1 = FAIL, 2 = could not run (bad arguments, ffprobe missing).

Defaults match the yt-render v1 spec: 1920x1080, 30 fps, H.264 + AAC in an MP4, under 2000 MB.
Override with --width/--height/--fps/--vcodec/--acodec/--max-mb.

Each check is one function in CHECKS returning {"id", "status", "expected", "actual", "detail"}
with status pass / fail / warn / skip. Only "fail" fails the file. Later checks (loudness,
black frames, silence, subtitles, licence manifest) are added as more functions in the same list.
"""
import json, math, os, subprocess, sys

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


# --- driver ------------------------------------------------------------------------------------

def run_qc(path, spec=None, expected_duration=None, quick=False):
    spec = dict(DEFAULTS, **(spec or {}))
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
           "expected_duration": expected_duration, "quick": quick}
    for fn in CHECKS:
        checks += fn(ctx)
    fmt = probe.get("format") or {}
    v, a = ctx["video"] or {}, ctx["audio"] or {}
    return {"result": "FAIL" if any(c["status"] == "fail" for c in checks) else "PASS",
            "file": path,
            "summary": {"bytes": ctx["size"], "duration": _f(fmt.get("duration")),
                        "resolution": f"{v.get('width')}x{v.get('height')}" if v else None,
                        "fps": round(_rate(v.get("avg_frame_rate")), 3) if v else None,
                        "video_codec": v.get("codec_name"), "audio_codec": a.get("codec_name"),
                        "expected_duration": expected_duration},
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
                  "--vcodec", "--acodec", "--max-mb", "--tolerance", "--timeout"}
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
        report = run_qc(files[0], spec, exp, "--quick" in a)
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
