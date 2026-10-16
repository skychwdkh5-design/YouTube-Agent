"""Shot-level segment cache + stream-copy assembly (FFmpeg only): re-render only the shots whose code or inputs changed.

A film is cut into segments at the shot boundaries of its plan. Each segment is rendered once to an H.264 file at final quality and stored under a
key = SHA-1 of (builder source, previous builder source, shared helper sources, kit + engine sources, narration timings, size, fps, frame range).
Unchanged segments are reused as they are; `assemble` joins them with FFmpeg's concat demuxer (stream copy, no re-encode) and adds the audio.
Measured on EP004 (docs/RENDER_BENCHMARKS.md): the cache turns a 34 min full re-render into the time of the changed shots only.
Rules: the key must change whenever pixels can change (so include engine sources: any orbitalatlas edit invalidates everything, on purpose);
never share a cache between sizes; segments are never edited in place.
"""
import hashlib, inspect, os, subprocess


def sha(*parts):
    h = hashlib.sha1()
    for p in parts: h.update(p if isinstance(p, bytes) else str(p).encode("utf-8")); h.update(b"\x00")
    return h.hexdigest()


def files_hash(paths):
    h = hashlib.sha1()
    for p in sorted(paths):
        with open(p, "rb") as f: h.update(os.path.basename(p).encode()); h.update(f.read())
    return h.hexdigest()


def engine_hash(root):
    d = os.path.join(root, "orbitalatlas")
    return files_hash([os.path.join(d, n) for n in os.listdir(d) if n.endswith(".py") and n != "segcache.py"])


def source(fn):
    try: return inspect.getsource(fn)
    except (OSError, TypeError): return repr(fn)


def segment_path(cache_dir, key): return os.path.join(cache_dir, key + ".mp4")


def have(cache_dir, key):
    p = segment_path(cache_dir, key); return p if os.path.exists(p) and os.path.getsize(p) > 1000 else None


def assemble(paths, out, audio=None, log=print):
    """stream-copy concat of equal-parameter segments (+ AAC audio); the picture length rules (-shortest off)."""
    lst = out + ".list.txt"
    with open(lst, "w") as f:
        for p in paths: f.write("file '%s'\n" % os.path.abspath(p).replace("'", "'\\''"))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst]
    if audio: cmd += ["-i", audio, "-c:a", "aac", "-b:a", "192k", "-af", "apad"]
    cmd += ["-c:v", "copy", "-movflags", "+faststart", "-shortest", out]
    subprocess.run(cmd, check=True); os.remove(lst); return out
