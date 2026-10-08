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

It renders still images (any size; scaled to cover and cropped) with Ken Burns pan/zoom,
crossfades or hard cuts between them. Optional, in the same timeline:
  audio.voice  one narration track from yt-voice, placed sample-exactly at "start"
               (otherwise the soundtrack is silence)
  subtitles    an SRT from yt-captions, burned into the picture
  credit       an on-screen source credit (e.g. the USGS Landsat credit)
Video clips, music, sound effects and generic overlays are still refused explicitly instead of
being silently dropped. A timeline without the optional keys renders exactly as before.

"version": 3 is a different format - Shorts and 16:9 long-form from geographically aligned imagery - and is
handled by compose.py (see SKILL.md). Versions 1 and 2 never load it.
"""
import hashlib, json, math, os, re, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # compose.py for timeline v3

TIMELINE_VERSION = 1
SUPPORTED_VERSIONS = (1, 2)   # 2 is the same format; docs/production-pipeline.md uses it for voice
DEFAULT_OUTPUT = {"width": 1920, "height": 1080, "fps": 30, "video_codec": "h264",
                  "audio_codec": "aac", "audio_rate": 48000, "audio_channels": 2,
                  "crf": 20, "preset": "medium", "audio_bitrate": "192k"}
ALLOWED_FPS = (24, 25, 30, 50, 60)
PRESETS = ("ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow")
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")
IMAGE_CODECS = ("mjpeg", "png", "webp", "bmp", "tiff")
PANS = ("center", "left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top")
FUTURE_TRACKS = ("voice", "music", "sfx", "subtitles", "overlays")
AUDIO_EXT = (".wav", ".mp3", ".m4a", ".aac", ".flac")
POSITIONS = ("top_left", "top_right", "bottom_left", "bottom_right")
SUB_STYLE = {"font": "Inter", "size": 15, "margin_v": 24}      # libass units (SRT PlayResY 288)
TARGET_LUFS, PEAK_CEILING = -16.0, -1.5   # narration level; a constant gain, never dynamic
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
    _keys(tl, ("version", "output", "clips", "audio", "subtitles", "overlays", "credit", "meta"), "timeline")
    if tl.get("version") not in SUPPORTED_VERSIONS or isinstance(tl.get("version"), bool):
        raise RenderError(f"timeline.version must be one of {SUPPORTED_VERSIONS}, got {tl.get('version')!r}")

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
    for k in ("music", "sfx"):
        if audio.get(k):
            raise RenderError(f"audio.{k} is not supported yet", status="unsupported")
    if tl.get("overlays"):
        raise RenderError("overlays are not supported yet (use \"credit\" for a source credit)",
                          status="unsupported")
    voice = parse_voice(audio.get("voice"), root, limits)
    subtitles = parse_subtitles(tl.get("subtitles"), root)

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
    if voice and voice["end"] > duration + 1e-6:
        raise RenderError(f"the clips end at {duration:.3f}s but the narration runs to {voice['end']:.3f}s; "
                          "lengthen the clips - narration is never cut")
    if subtitles and subtitles["last_end"] > duration + 1e-6:
        raise RenderError(f"subtitles run to {subtitles['last_end']:.3f}s, past the video's {duration:.3f}s")
    credit = parse_credit(tl.get("credit"), clips, out)
    warnings = []
    if any(c["type"] == "landsat" for c in plan) and not credit:
        warnings.append("landsat clips are on screen without a source credit; add \"credit\": {}")
    if voice and not subtitles:
        warnings.append("narration without subtitles")
    return {"output": out, "clips": plan, "total_frames": total_frames,
            "expected_duration": round(duration, 3), "voice": voice, "subtitles": subtitles,
            "credit": credit, "warnings": warnings}


# --- narration, subtitles, credit --------------------------------------------------------------

def parse_voice(v, root, limits=LIMITS):
    """One narration track (yt-voice output). Returns None when absent."""
    if not v:
        return None
    items = v if isinstance(v, list) else [v]
    if len(items) != 1:
        raise RenderError("audio.voice takes exactly one narration track", status="unsupported")
    item = items[0]
    _keys(item, ("src", "start", "meta", "normalize"), "audio.voice[0]")
    src = resolve_src(item.get("src"), root, "audio.voice[0]")
    if not src.lower().endswith(AUDIO_EXT):
        raise RenderError(f"audio.voice[0]: unsupported audio type {os.path.basename(src)!r}; "
                          f"allowed: {', '.join(AUDIO_EXT)}")
    size = os.path.getsize(src)
    if size > limits["max_input_mb"] * 1048576:
        raise RenderError(f"audio.voice[0]: {size / 1048576:.1f} MB is over --max-input-mb {limits['max_input_mb']}")
    d = ffprobe_json(src)
    streams = d.get("streams") or []
    auds = [x for x in streams if x.get("codec_type") == "audio"]
    vids = [x for x in streams if x.get("codec_type") == "video"
            and not (x.get("disposition") or {}).get("attached_pic")]
    if len(auds) != 1 or vids:
        raise RenderError(f"audio.voice[0]: {os.path.basename(src)!r} must hold exactly one audio stream")
    try:
        dur = float((d.get("format") or {}).get("duration") or auds[0].get("duration"))
    except (TypeError, ValueError):
        dur = 0.0
    if not dur > 0:
        raise RenderError(f"audio.voice[0]: {os.path.basename(src)!r} has no readable duration")
    start = _num(item.get("start", 0.0), "audio.voice[0].start", 0, 600)
    norm = item.get("normalize", True)
    if not isinstance(norm, bool):
        raise RenderError("audio.voice[0].normalize must be true or false")
    info = {"src": src, "start": start, "duration": round(dur, 3), "end": round(start + dur, 6),
            "normalize": norm, "gain_db": 0.0, "measured": None, "voice_name": None, "voice_id": None}
    if norm:
        info["measured"] = measure_loudness(src)
        info["gain_db"] = normalize_gain(info["measured"])
    if item.get("meta"):
        meta_path = resolve_src(item["meta"], root, "audio.voice[0].meta")
        try:
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
        except (OSError, ValueError) as e:
            raise RenderError(f"audio.voice[0].meta unreadable: {type(e).__name__}: {e}")
        if not str(meta.get("schema", "")).startswith("yt-voice/"):
            raise RenderError("audio.voice[0].meta is not a yt-voice metadata file")
        if meta.get("audio_sha256") and meta["audio_sha256"] != _sha256(src):
            raise RenderError("audio.voice[0]: the audio file does not match its yt-voice metadata "
                              "(audio_sha256 differs) - the captions would not line up")
        if isinstance(meta.get("duration"), (int, float)) and abs(meta["duration"] - dur) > 0.05:
            raise RenderError(f"audio.voice[0]: audio is {dur:.3f}s but its metadata says {meta['duration']}s")
        info["voice_name"], info["voice_id"] = meta.get("voice_name"), meta.get("voice_id")
    return info


def measure_loudness(path):
    """EBU R128 integrated loudness and true peak of a file (ffmpeg ebur128, analysis only)."""
    r = _run(["ffmpeg", "-hide_banner", "-nostdin", "-i", path, "-map", "0:a", "-af", "ebur128=peak=true",
              "-f", "null", "-"], 600)
    if r.returncode != 0:
        raise RenderError(f"loudness measurement failed: {r.stderr.strip()[-300:]}")
    summary = r.stderr[r.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s*(-?[\d.]+|-inf)\s*LUFS", summary)
    pk = re.search(r"Peak:\s*(-?[\d.]+|-inf)\s*dBFS", summary)
    val = lambda m: float(m.group(1)) if m and m.group(1) != "-inf" else None
    return {"integrated_lufs": val(i), "true_peak_dbfs": val(pk)}


def normalize_gain(m):
    """One constant gain toward TARGET_LUFS that keeps the true peak under PEAK_CEILING. Silence or
    an unmeasurable file gets 0 dB - nothing is invented."""
    if not m or m["integrated_lufs"] is None or m["integrated_lufs"] < -60:
        return 0.0
    gain = TARGET_LUFS - m["integrated_lufs"]
    if m["true_peak_dbfs"] is not None:
        gain = min(gain, PEAK_CEILING - m["true_peak_dbfs"])
    return round(max(-20.0, min(20.0, gain)), 2)


def parse_srt(text):
    """Strict SRT reader: numbered blocks, HH:MM:SS,mmm stamps, increasing, non-overlapping."""
    cues, prev_end = [], 0
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip()):
        lines = block.split("\n")
        m = re.fullmatch(r"(\d+):(\d\d):(\d\d),(\d{3}) --> (\d+):(\d\d):(\d\d),(\d{3})",
                         lines[1].strip()) if len(lines) >= 3 and lines[0].strip().isdigit() else None
        if not m:
            raise RenderError(f"subtitles: bad SRT block {block[:60]!r}")
        g = [int(x) for x in m.groups()]
        a = ((g[0] * 60 + g[1]) * 60 + g[2]) * 1000 + g[3]
        b = ((g[4] * 60 + g[5]) * 60 + g[6]) * 1000 + g[7]
        if b <= a or a < prev_end:
            raise RenderError(f"subtitles: cue {lines[0].strip()} has a broken or overlapping time range")
        cues.append((a, b, " ".join(l.strip() for l in lines[2:])))
        prev_end = b
    return cues


def parse_subtitles(sub, root):
    if not sub:
        return None
    _keys(sub, ("src", "burn_in", "font", "size", "margin_v"), "subtitles")
    src = resolve_src(sub.get("src"), root, "subtitles")
    if not src.lower().endswith(".srt"):
        raise RenderError("subtitles.src must be an .srt file (from yt-captions)")
    if os.path.getsize(src) > 2 * 1048576:
        raise RenderError("subtitles.src is over 2 MB")
    try:
        with open(src, encoding="utf-8") as f:
            cues = parse_srt(f.read())
    except (OSError, UnicodeDecodeError) as e:
        raise RenderError(f"subtitles unreadable: {type(e).__name__}: {e}")
    if not cues:
        raise RenderError("subtitles.src has no cues")
    burn = sub.get("burn_in", True)
    if not isinstance(burn, bool):
        raise RenderError("subtitles.burn_in must be true or false")
    font = sub.get("font", SUB_STYLE["font"])
    if not isinstance(font, str) or not re.fullmatch(r"[A-Za-z0-9 _-]{1,64}", font):
        raise RenderError("subtitles.font must be a plain font family name")
    return {"src": src, "burn_in": burn, "font": font,
            "size": _num(sub.get("size", SUB_STYLE["size"]), "subtitles.size", 6, 60),
            "margin_v": _num(sub.get("margin_v", SUB_STYLE["margin_v"]), "subtitles.margin_v", 0, 200, int),
            "cues": len(cues), "last_end": cues[-1][1] / 1000}


def parse_credit(c, clips, out):
    if c is None or c is False:
        return None
    if c is True:
        c = {}   # {} and true both mean: build the text from the clips' "credit" fields
    _keys(c, ("text", "position", "size", "opacity"), "credit")
    text = c.get("text")
    if text is None:
        seen = []
        for clip in clips:
            t = clip.get("credit")
            if isinstance(t, str) and t.strip() and t.strip() not in seen:
                seen.append(t.strip())
        text = " · ".join(seen)
    if not isinstance(text, str) or not text.strip():
        raise RenderError("credit has no text and no clip carries a \"credit\"")
    if len(text) > 200 or "\n" in text:
        raise RenderError("credit.text must be one line of at most 200 characters")
    pos = c.get("position", "top_left")
    if pos not in POSITIONS:
        raise RenderError(f"credit.position must be one of {POSITIONS}")
    return {"text": text.strip(), "position": pos,
            "size": _num(c.get("size", max(8, round(24 * out["height"] / 1080))), "credit.size", 8, 120, int),
            "opacity": _num(c.get("opacity", 0.85), "credit.opacity", 0.1, 1.0)}


def font_file(family):
    """Resolve a font family to a file with fontconfig, so drawtext does not depend on its build."""
    try:
        r = subprocess.run(["fc-match", "-f", "%{file}", family], capture_output=True, text=True, timeout=20)
        path = r.stdout.strip()
        return path if r.returncode == 0 and os.path.isfile(path) else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def expected_duration(timeline_path, media_root=None):
    """Public helper for yt-qc: the duration a timeline should render to."""
    tl = load_timeline(timeline_path)
    root = media_root or os.path.dirname(os.path.abspath(timeline_path))
    if isinstance(tl, dict) and tl.get("version") == 3 and not isinstance(tl.get("version"), bool):
        sys.modules.setdefault("render", sys.modules[__name__])
        import compose
        return compose.validate(tl, root, LIMITS)["expected_duration"]
    return validate(tl, root)["expected_duration"]


# --- ffprobe / ffmpeg --------------------------------------------------------------------------

def _run(cmd, timeout, cwd=None):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
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


def build_command(plan, out_path, max_output_bytes, workdir=None):
    """The ffmpeg command. Narration, subtitles and credit reference files staged in workdir by
    relative name (ffmpeg runs there), so no user path ever needs filter-graph escaping."""
    o = plan["output"]
    voice, subs, credit = plan.get("voice"), plan.get("subtitles"), plan.get("credit")
    W, H, fps = o["width"], o["height"], o["fps"]
    ww, wh = W * WORK_SCALE, H * WORK_SCALE
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y"]
    for c in plan["clips"]:
        cmd += ["-i", c["src"]]
    duration = plan["total_frames"] / fps
    layout = "stereo" if o["audio_channels"] == 2 else "mono"
    if voice:
        cmd += ["-i", voice["src"]]
    else:
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
    post = ""
    if subs and subs["burn_in"]:
        style = (f"FontName={subs['font']},FontSize={subs['size']:g},PrimaryColour=&H00FFFFFF,"
                 f"OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=1,Outline=1.3,"
                 f"Shadow=0.8,MarginV={subs['margin_v']}")
        post += f",subtitles=subs.srt:force_style='{style}'"
    if credit:
        m = round(44 * H / 1080)
        x = str(m) if credit["position"].endswith("left") else f"w-tw-{m}"
        y = str(m) if credit["position"].startswith("top") else f"h-th-{m}"
        font = "fontfile=credit_font" + os.path.splitext(credit.get("font_file") or ".ttf")[1] \
            if credit.get("font_file") else "font='Inter'"
        sh = max(1, round(2 * H / 1080))
        post += (f",drawtext={font}:textfile=credit.txt:fontsize={credit['size']}:"
                 f"fontcolor=white@{credit['opacity']:g}:shadowcolor=black@0.7:"
                 f"shadowx={sh}:shadowy={sh}:x={x}:y={y}")
    parts.append(f"{acc}settb=1/{fps},setpts=N{post},format=yuv420p[vout]")
    amap = f"{len(plan['clips'])}:a"
    if voice:
        rate = o["audio_rate"]
        chain = f"[{len(plan['clips'])}:a]aformat=sample_fmts=fltp,"
        if voice["gain_db"]:
            chain += f"volume={voice['gain_db']:.2f}dB,"
        chain += f"aresample={rate},aformat=channel_layouts={layout}"
        if voice["start"] > 0:
            chain += f",adelay=delays={round(voice['start'] * rate)}S:all=1"
        parts.append(chain + ",apad[aout]")
        amap = "[aout]"

    cmd += ["-filter_complex", ";".join(parts), "-map", "[vout]", "-map", amap,
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
    sources = [c["src"] for c in plan["clips"]] + [x["src"] for x in (plan.get("voice"), plan.get("subtitles")) if x]
    if os.path.realpath(out_path) in sources:
        raise RenderError("--output would overwrite one of the timeline's source files")

    max_bytes = limits["max_output_mb"] * 1048576
    fd, tmp = tempfile.mkstemp(prefix=".render-", suffix=".partial.mp4", dir=os.path.dirname(out_path))
    os.close(fd)
    work = None
    try:
        voice, subs, credit = plan.get("voice"), plan.get("subtitles"), plan.get("credit")
        if (subs and subs["burn_in"]) or credit:
            work = tempfile.mkdtemp(prefix=".render-work-", dir=os.path.dirname(out_path))
            if subs and subs["burn_in"]:
                shutil.copyfile(subs["src"], os.path.join(work, "subs.srt"))
            if credit:
                with open(os.path.join(work, "credit.txt"), "w", encoding="utf-8") as f:
                    f.write(credit["text"])
                ff = font_file("Inter") or font_file("DejaVu Sans")
                if ff:
                    shutil.copyfile(ff, os.path.join(work, "credit_font" + os.path.splitext(ff)[1]))
                credit = dict(credit, font_file=ff)
        plan_run = dict(plan, credit=credit)
        r = _run(build_command(plan_run, tmp, max_bytes, work), limits["timeout_s"], cwd=work)
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
        if voice:
            a = [x for x in d.get("streams") or [] if x.get("codec_type") == "audio"][0]
            if float(a.get("duration") or 0) + 0.05 < voice["end"]:
                raise RenderError("rendered audio is shorter than the narration - it would be cut")
        umask = os.umask(0); os.umask(umask)
        os.chmod(tmp, 0o666 & ~umask)   # mkstemp creates 0600; give the MP4 normal file permissions
        os.replace(tmp, out_path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    finally:
        if work:
            shutil.rmtree(work, ignore_errors=True)
    result = {"status": "ok", "output": out_path, "bytes": size, "sha256": _sha256(out_path),
              "duration": round(got, 3), "expected_duration": plan["expected_duration"],
              "spec": plan["output"], "clips": len(plan["clips"])}
    result.update(_extras(plan))
    return result


def _extras(plan):
    """Narration / subtitle / credit summary for the JSON output - absent keys stay absent."""
    out = {}
    if plan.get("voice"):
        v = plan["voice"]
        out["narration"] = {k: v[k] for k in ("src", "start", "duration", "end", "normalize", "gain_db",
                                              "measured", "voice_name", "voice_id")}
    if plan.get("subtitles"):
        sb = plan["subtitles"]
        out["subtitles"] = {k: sb[k] for k in ("src", "burn_in", "cues", "last_end", "font")}
    if plan.get("credit"):
        out["credit"] = plan["credit"]["text"]
    if plan.get("warnings"):
        out["warnings"] = plan["warnings"]
    return out


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
    out = {"expected_duration": plan["expected_duration"], "total_frames": plan["total_frames"],
           "output": plan["output"],
           "clips": [{k: c[k] for k in ("index", "type", "src", "frames", "fit", "zoom", "pan",
                                        "transition_frames", "source_size")} for c in plan["clips"]]}
    out.update(_extras(plan))
    return out


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
        tl = load_timeline(tl_path)
        if isinstance(tl, dict) and tl.get("version") == 3 and not isinstance(tl.get("version"), bool):
            sys.modules.setdefault("render", sys.modules[__name__])   # one RenderError class, script or module
            import compose      # timeline v3 (Shorts and long-form); v1/v2 never load it
            plan = compose.validate(tl, root, limits)
            public, do_render = compose.public_plan, compose.render
        else:
            plan = validate(tl, root, limits)
            public, do_render = _public_plan, render
        if "--confirm" not in a:
            raise RenderError("rendering needs --confirm; the timeline is valid, plan attached",
                              status="confirm_required", plan=public(plan))
        out = _flag(a, "--output")
        if not out: raise RenderError("--output is required")
        result = do_render(plan, out, "--overwrite" in a, limits)
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
