#!/usr/bin/env python3
"""render.py - turn a timeline.json into a real MP4 with the installed FFmpeg, nothing else.

    python3 render.py --timeline timeline.json                       # validate + plan only
    python3 render.py --timeline timeline.json --output final.mp4 --confirm
    python3 render.py --timeline timeline.json --output final.mp4 --confirm --overwrite

Every command prints JSON. Nothing renders without --confirm. Every source file is checked with
ffprobe before FFmpeg starts; a missing, unsupported, oversized or out-of-root file stops the run.

The MP4 is written to a hidden temporary file next to the output and only renamed into place after
FFmpeg exits cleanly and the result probes as a valid file under --max-output-mb. A failed render
leaves no final.mp4 behind, and an existing output is never replaced without --overwrite.

Version 1 renders still images (any size; scaled to cover and cropped) with Ken Burns pan/zoom,
crossfades or hard cuts between them, and a silent stereo AAC track. The timeline format already
names the other track kinds (video clips, voice, music, sfx, subtitles, overlays); version 1
rejects them explicitly instead of silently dropping them.
"""
import hashlib, json, math, os, re, subprocess, sys, tempfile

TIMELINE_VERSION = 1
DEFAULT_OUTPUT = {"width": 1920, "height": 1080, "fps": 30, "video_codec": "h264",
                  "audio_codec": "aac", "audio_rate": 48000, "audio_channels": 2,
                  "crf": 20, "preset": "medium", "audio_bitrate": "192k"}
ALLOWED_FPS = (24, 25, 30, 50, 60)
PRESETS = ("ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow")
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")
IMAGE_CODECS = ("mjpeg", "png", "webp", "bmp", "tiff")
PANS = ("center", "left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top")
FUTURE_TRACKS = ("voice", "music", "sfx", "subtitles", "overlays")
MAX_ASPECT_SKEW = 4.0      # cover-cropping a source this far from the output aspect throws most of it away
MIN_SIDE, MAX_PIXELS = 16, 120_000_000
MAX_ZOOM = 2.0
WORK_SCALE = 2             # zoompan works on a 2x canvas so sub-pixel pan steps do not jitter

LIMITS = {"max_input_mb": 200.0, "max_output_mb": 500.0, "max_duration_s": 900.0,
          "max_clips": 200, "timeout_s": 1800}


class RenderError(Exception):
    def __init__(self, message, status="error", **extra):
        super().__init__(message)
        self.status = status
        self.extra = extra


# --- validation --------------------------------------------------------------------------------

def _num(v, name, lo=None, hi=None, kind=float):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise RenderError(f"{name} must be a number, got {v!r}")
    if kind is int and v != int(v):
        raise RenderError(f"{name} must be an integer, got {v!r}")
    if not math.isfinite(v):
        raise RenderError(f"{name} must be finite, got {v!r}")
    if (lo is not None and v < lo) or (hi is not None and v > hi):
        raise RenderError(f"{name} must be between {lo} and {hi}, got {v!r}")
    return kind(v)


def _keys(d, allowed, where):
    if not isinstance(d, dict):
        raise RenderError(f"{where} must be an object")
    extra = sorted(set(d) - set(allowed))
    if extra:
        raise RenderError(f"{where} has unknown key(s) {extra}; allowed: {sorted(allowed)}")


def load_timeline(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise RenderError(f"timeline not found: {path}")
    except (OSError, ValueError) as e:
        raise RenderError(f"cannot read timeline {path}: {type(e).__name__}: {e}")


def resolve_src(src, root, where):
    """Resolve a source path inside root. URLs and anything escaping root (.., symlinks) fail."""
    if not isinstance(src, str) or not src.strip():
        raise RenderError(f"{where}.src must be a non-empty path")
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", src) and not re.match(r"^[a-zA-Z]:[\\/]", src):
        raise RenderError(f"{where}.src must be a local file, not a URL: {src!r}")
    real_root = os.path.realpath(root)
    p = os.path.realpath(os.path.join(real_root, src))
    if os.path.commonpath([p, real_root]) != real_root:
        raise RenderError(f"{where}.src {src!r} resolves outside the media root {real_root}")
    if not os.path.isfile(p):
        raise RenderError(f"{where}.src not found: {src!r}")
    return p


def validate(tl, root, limits=LIMITS):
    """Check the whole timeline and return a normalised plan. Touches no media except ffprobe."""
    _keys(tl, ("version", "output", "clips", "audio", "subtitles", "overlays", "meta"), "timeline")
    if tl.get("version") != TIMELINE_VERSION:
        raise RenderError(f"timeline.version must be {TIMELINE_VERSION}, got {tl.get('version')!r}")

    out = dict(DEFAULT_OUTPUT)
    spec = tl.get("output") or {}
    _keys(spec, DEFAULT_OUTPUT, "output")
    out.update(spec)
    out["width"] = _num(out["width"], "output.width", 16, 3840, int)
    out["height"] = _num(out["height"], "output.height", 16, 2160, int)
    if out["width"] % 2 or out["height"] % 2:
        raise RenderError("output.width and output.height must be even (yuv420p)")
    out["fps"] = _num(out["fps"], "output.fps", kind=int)
    if out["fps"] not in ALLOWED_FPS:
        raise RenderError(f"output.fps must be one of {ALLOWED_FPS}")
    if out["video_codec"] != "h264": raise RenderError("output.video_codec: only h264 is supported")
    if out["audio_codec"] != "aac": raise RenderError("output.audio_codec: only aac is supported")
    out["audio_rate"] = _num(out["audio_rate"], "output.audio_rate", kind=int)
    if out["audio_rate"] not in (44100, 48000): raise RenderError("output.audio_rate must be 44100 or 48000")
    out["audio_channels"] = _num(out["audio_channels"], "output.audio_channels", 1, 2, int)
    out["crf"] = _num(out["crf"], "output.crf", 0, 51, int)
    if out["preset"] not in PRESETS: raise RenderError(f"output.preset must be one of {PRESETS}")
    if not re.fullmatch(r"\d{2,3}k", str(out["audio_bitrate"])):
        raise RenderError("output.audio_bitrate must look like '192k'")

    audio = tl.get("audio") or {}
    _keys(audio, FUTURE_TRACKS[:3], "audio")
    for k in FUTURE_TRACKS[:3]:
        if audio.get(k):
            raise RenderError(f"audio.{k} is not supported in timeline version 1 yet", status="unsupported")
    for k in ("subtitles", "overlays"):
        if tl.get(k):
            raise RenderError(f"{k} are not supported in timeline version 1 yet", status="unsupported")

    clips = tl.get("clips")
    if not isinstance(clips, list) or not clips:
        raise RenderError("timeline.clips must be a non-empty list")
    if len(clips) > limits["max_clips"]:
        raise RenderError(f"{len(clips)} clips is over the limit of {limits['max_clips']}")

    fps, plan = out["fps"], []
    for i, c in enumerate(clips):
        where = f"clips[{i}]"
        _keys(c, ("type", "src", "duration", "fit", "motion", "transition", "source", "credit", "note"), where)
        kind = c.get("type")
        if kind == "video":
            raise RenderError(f"{where}: video clips are not supported in timeline version 1 yet",
                              status="unsupported")
        if kind not in ("image", "landsat"):
            raise RenderError(f"{where}.type must be 'image' or 'landsat', got {kind!r}")
        dur = _num(c.get("duration"), f"{where}.duration", 0.2, 600)
        frames = max(1, round(dur * fps))
        fit = c.get("fit", "cover")
        if fit not in ("cover", "contain"):
            raise RenderError(f"{where}.fit must be 'cover' or 'contain'")

        m = c.get("motion") or {"type": "kenburns"}
        _keys(m, ("type", "zoom", "pan"), f"{where}.motion")
        if m.get("type", "kenburns") == "static":
            zoom, pan = (1.0, 1.0), "center"
        elif m.get("type", "kenburns") == "kenburns":
            z = m.get("zoom", [1.0, 1.1])
            if not (isinstance(z, list) and len(z) == 2):
                raise RenderError(f"{where}.motion.zoom must be [start, end]")
            zoom = tuple(_num(v, f"{where}.motion.zoom", 1.0, MAX_ZOOM) for v in z)
            pan = m.get("pan", "center")
            if pan not in PANS: raise RenderError(f"{where}.motion.pan must be one of {PANS}")
        else:
            raise RenderError(f"{where}.motion.type must be 'kenburns' or 'static'")

        t = c.get("transition") or {"type": "none"}
        _keys(t, ("type", "duration"), f"{where}.transition")
        if t.get("type") not in ("none", "crossfade"):
            raise RenderError(f"{where}.transition.type must be 'none' or 'crossfade'")
        t_frames = 0
        if t["type"] == "crossfade" and i < len(clips) - 1:
            td = _num(t.get("duration", 0.5), f"{where}.transition.duration", 0.1, 5)
            t_frames = max(1, round(td * fps))

        src = resolve_src(c.get("src"), root, where)
        info = probe_image(src, where, limits)
        if fit == "cover":
            skew = max(info["width"] / info["height"] / (out["width"] / out["height"]),
                       (out["width"] / out["height"]) / (info["width"] / info["height"]))
            if skew > MAX_ASPECT_SKEW:
                raise RenderError(f"{where}: {info['width']}x{info['height']} is too far from "
                                  f"{out['width']}x{out['height']} to crop; set \"fit\": \"contain\"")
        plan.append({"index": i, "type": kind, "src": src, "frames": frames, "fit": fit,
                     "zoom": zoom, "pan": pan, "transition_frames": t_frames,
                     "source_size": [info["width"], info["height"]], "bytes": info["bytes"]})

    for a, b in zip(plan, plan[1:]):
        if a["transition_frames"] and a["transition_frames"] >= min(a["frames"], b["frames"]):
            raise RenderError(f"clips[{a['index']}].transition is longer than one of the clips it joins")

    total_frames = sum(p["frames"] for p in plan) - sum(p["transition_frames"] for p in plan)
    duration = total_frames / fps
    if duration > limits["max_duration_s"]:
        raise RenderError(f"timeline is {duration:.1f}s, over --max-duration {limits['max_duration_s']}")
    return {"output": out, "clips": plan, "total_frames": total_frames,
            "expected_duration": round(duration, 3)}


def expected_duration(timeline_path, media_root=None):
    """Public helper for yt-qc: the duration a timeline should render to."""
    tl = load_timeline(timeline_path)
    return validate(tl, media_root or os.path.dirname(os.path.abspath(timeline_path)))["expected_duration"]


# --- ffprobe / ffmpeg --------------------------------------------------------------------------

def _run(cmd, timeout):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise RenderError(f"{cmd[0]} is not installed or not on PATH")
    except subprocess.TimeoutExpired:
        raise RenderError(f"{cmd[0]} timed out after {timeout}s")


def ffprobe_json(path, timeout=60):
    r = _run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", path], timeout)
    if r.returncode != 0:
        raise RenderError(f"ffprobe cannot read {os.path.basename(path)}: {r.stderr.strip()[-300:]}")
    try:
        return json.loads(r.stdout or "{}")
    except ValueError:
        raise RenderError(f"ffprobe returned unreadable output for {os.path.basename(path)}")


def probe_image(path, where, limits=LIMITS):
    if not path.lower().endswith(IMAGE_EXT):
        raise RenderError(f"{where}: unsupported file type {os.path.basename(path)!r}; "
                          f"allowed: {', '.join(IMAGE_EXT)}")
    size = os.path.getsize(path)
    if size > limits["max_input_mb"] * 1048576:
        raise RenderError(f"{where}: {size / 1048576:.1f} MB is over --max-input-mb {limits['max_input_mb']}")
    d = ffprobe_json(path)
    vs = [s for s in d.get("streams") or [] if s.get("codec_type") == "video"]
    if len(vs) != 1 or vs[0].get("codec_name") not in IMAGE_CODECS:
        raise RenderError(f"{where}: {os.path.basename(path)!r} is not a supported still image "
                          f"(got {[s.get('codec_name') for s in vs]})")
    w, h = int(vs[0].get("width") or 0), int(vs[0].get("height") or 0)
    if not w or not h:
        raise RenderError(f"{where}: {os.path.basename(path)!r} is not a readable image (no dimensions)")
    if w < MIN_SIDE or h < MIN_SIDE:
        raise RenderError(f"{where}: {w}x{h} is too small (min {MIN_SIDE}px a side)")
    if w * h > MAX_PIXELS:
        raise RenderError(f"{where}: {w}x{h} is over {MAX_PIXELS // 1_000_000} megapixels")
    return {"width": w, "height": h, "codec": vs[0]["codec_name"], "bytes": size}


def build_command(plan, out_path, max_output_bytes):
    o = plan["output"]
    W, H, fps = o["width"], o["height"], o["fps"]
    ww, wh = W * WORK_SCALE, H * WORK_SCALE
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y"]
    for c in plan["clips"]:
        cmd += ["-i", c["src"]]
    duration = plan["total_frames"] / fps
    layout = "stereo" if o["audio_channels"] == 2 else "mono"
    cmd += ["-f", "lavfi", "-i", f"anullsrc=r={o['audio_rate']}:cl={layout}"]

    parts = []
    for i, c in enumerate(plan["clips"]):
        n, (zs, ze) = c["frames"], c["zoom"]
        step = f"{ze - zs:.6f}*on/{max(n - 1, 1)}"
        frac = f"on/{max(n - 1, 1)}"
        cx, cy = "(iw-iw/zoom)/2", "(ih-ih/zoom)/2"
        x, y = {"center": (cx, cy),
                "left_to_right": (f"(iw-iw/zoom)*{frac}", cy),
                "right_to_left": (f"(iw-iw/zoom)*(1-{frac})", cy),
                "top_to_bottom": (cx, f"(ih-ih/zoom)*{frac}"),
                "bottom_to_top": (cx, f"(ih-ih/zoom)*(1-{frac})")}[c["pan"]]
        if c["fit"] == "cover":
            fit = (f"scale={ww}:{wh}:force_original_aspect_ratio=increase:flags=lanczos,"
                   f"crop={ww}:{wh}")
        else:
            fit = (f"scale={ww}:{wh}:force_original_aspect_ratio=decrease:flags=lanczos,"
                   f"pad={ww}:{wh}:(ow-iw)/2:(oh-ih)/2:color=black")
        parts.append(f"[{i}:v]format=yuv444p,{fit},setsar=1,"
                     f"zoompan=z='{zs:.6f}+{step}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={fps},"
                     f"trim=end_frame={n},setpts=PTS-STARTPTS,format=yuv420p[c{i}]")

    acc, acc_frames = "[c0]", plan["clips"][0]["frames"]
    for i in range(1, len(plan["clips"])):
        prev, cur = plan["clips"][i - 1], plan["clips"][i]
        label = f"[j{i}]"
        if prev["transition_frames"]:
            tf = prev["transition_frames"]
            offset = (acc_frames - tf) / fps
            parts.append(f"{acc}[c{i}]xfade=transition=fade:duration={tf / fps:.6f}:"
                         f"offset={offset:.6f}{label}")
            acc_frames += cur["frames"] - tf
        else:
            parts.append(f"{acc}[c{i}]concat=n=2:v=1:a=0{label}")
            acc_frames += cur["frames"]
        acc = label
    # fps= here would drop the last frame (it cannot know its duration); renumber instead
    parts.append(f"{acc}settb=1/{fps},setpts=N,format=yuv420p[vout]")

    cmd += ["-filter_complex", ";".join(parts), "-map", "[vout]", "-map", f"{len(plan['clips'])}:a",
            "-c:v", "libx264", "-preset", o["preset"], "-crf", str(o["crf"]), "-pix_fmt", "yuv420p",
            "-profile:v", "high", "-r", str(fps), "-g", str(fps * 2),
            "-c:a", "aac", "-b:a", o["audio_bitrate"], "-ar", str(o["audio_rate"]),
            "-ac", str(o["audio_channels"]),
            "-frames:v", str(plan["total_frames"]), "-t", f"{duration:.6f}",
            "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:v", "+bitexact",
            "-flags:a", "+bitexact", "-movflags", "+faststart",
            "-fs", str(int(max_output_bytes)), "-f", "mp4", out_path]
    return cmd


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def render(plan, out_path, overwrite=False, limits=LIMITS):
    out_path = os.path.abspath(out_path)
    if not out_path.lower().endswith(".mp4"):
        raise RenderError("--output must end in .mp4")
    if not os.path.isdir(os.path.dirname(out_path)):
        raise RenderError(f"output directory does not exist: {os.path.dirname(out_path)}")
    if os.path.lexists(out_path) and not overwrite:
        raise RenderError(f"{out_path} already exists; pass --overwrite to replace it", status="exists")
    if os.path.isdir(out_path):
        raise RenderError(f"{out_path} is a directory")
    if any(os.path.realpath(out_path) == c["src"] for c in plan["clips"]):
        raise RenderError("--output would overwrite one of the timeline's source images")

    max_bytes = limits["max_output_mb"] * 1048576
    fd, tmp = tempfile.mkstemp(prefix=".render-", suffix=".partial.mp4", dir=os.path.dirname(out_path))
    os.close(fd)
    try:
        r = _run(build_command(plan, tmp, max_bytes), limits["timeout_s"])
        if r.returncode != 0:
            raise RenderError("ffmpeg failed: " + (r.stderr.strip()[-600:] or f"exit {r.returncode}"))
        size = os.path.getsize(tmp)
        if size >= max_bytes:
            raise RenderError(f"output reached --max-output-mb {limits['max_output_mb']}; "
                              "it would be truncated, so it was discarded")
        d = ffprobe_json(tmp)
        kinds = sorted(s.get("codec_type") for s in d.get("streams") or [])
        if kinds != ["audio", "video"]:
            raise RenderError(f"rendered file has streams {kinds}, expected one video and one audio")
        got = float((d.get("format") or {}).get("duration") or 0)
        if abs(got - plan["expected_duration"]) > max(0.25, 2 / plan["output"]["fps"]):
            raise RenderError(f"rendered duration {got:.3f}s does not match the timeline's "
                              f"{plan['expected_duration']:.3f}s")
        umask = os.umask(0); os.umask(umask)
        os.chmod(tmp, 0o666 & ~umask)   # mkstemp creates 0600; give the MP4 normal file permissions
        os.replace(tmp, out_path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    return {"status": "ok", "output": out_path, "bytes": size, "sha256": _sha256(out_path),
            "duration": round(got, 3), "expected_duration": plan["expected_duration"],
            "spec": plan["output"], "clips": len(plan["clips"])}


# --- CLI ---------------------------------------------------------------------------------------

def _flag(a, name, default=None):
    if name not in a: return default
    i = a.index(name)
    if i + 1 >= len(a) or a[i + 1].startswith("--"):
        raise RenderError(f"{name} needs a value")
    return a[i + 1]


def _limit(a, name, key, lo, kind=float):
    raw = _flag(a, name)
    if raw is None: return LIMITS[key]
    try:
        v = kind(raw)
    except ValueError:
        raise RenderError(f"{name} expects a number, got {raw!r}")
    if not math.isfinite(v) or v < lo:
        raise RenderError(f"{name} must be a finite number >= {lo}, got {raw!r}")
    return v


def _public_plan(plan):
    return {"expected_duration": plan["expected_duration"], "total_frames": plan["total_frames"],
            "output": plan["output"],
            "clips": [{k: c[k] for k in ("index", "type", "src", "frames", "fit", "zoom", "pan",
                                         "transition_frames", "source_size")} for c in plan["clips"]]}


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or "-h" in a or "--help" in a:
        print(__doc__); return 0
    try:
        known = {"--timeline", "--output", "--media-root", "--max-input-mb", "--max-output-mb",
                 "--max-duration", "--timeout", "--confirm", "--overwrite"}
        unknown = [x for x in a if x.startswith("--") and x not in known]
        if unknown: raise RenderError(f"unknown option(s): {unknown}")
        limits = dict(LIMITS,
                      max_input_mb=_limit(a, "--max-input-mb", "max_input_mb", 0.001),
                      max_output_mb=_limit(a, "--max-output-mb", "max_output_mb", 0.01),
                      max_duration_s=_limit(a, "--max-duration", "max_duration_s", 0.1),
                      timeout_s=_limit(a, "--timeout", "timeout_s", 1, int))
        tl_path = _flag(a, "--timeline")
        if not tl_path: raise RenderError("--timeline is required")
        root = _flag(a, "--media-root") or os.path.dirname(os.path.abspath(tl_path))
        plan = validate(load_timeline(tl_path), root, limits)
        if "--confirm" not in a:
            raise RenderError("rendering needs --confirm; the timeline is valid, plan attached",
                              status="confirm_required", plan=_public_plan(plan))
        out = _flag(a, "--output")
        if not out: raise RenderError("--output is required")
        result = render(plan, out, "--overwrite" in a, limits)
        print(json.dumps(result, indent=1))
        return 0
    except RenderError as e:
        print(json.dumps({"status": e.status, "error": str(e), **e.extra}, indent=1, default=str))
        return 2
    except Exception as e:  # never a traceback
        print(json.dumps({"status": "error", "error": f"unexpected {type(e).__name__}: {e}"}, indent=1))
        return 2


if __name__ == "__main__":
    sys.exit(main())
