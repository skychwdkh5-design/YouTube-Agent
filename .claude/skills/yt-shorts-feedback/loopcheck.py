#!/usr/bin/env python3
"""loopcheck.py - does the end of a Short flow back into its beginning?

    python3 loopcheck.py --captions captions.json                 # text seam only (list of [start, end, "TEXT"], as in productions/*/final/shorts/*.json)
    python3 loopcheck.py --captions captions.json --video short.mp4 --declared visual_return
    python3 loopcheck.py --srt captions.srt --video short.mp4

A Short that loops plays its last frame and then its first frame again. This tool measures the three seams and prints a JSON report:
  text    the last cue, the first cue and the sentence they make when read back to back (for a person to read), plus mechanical flags:
          the last cue ends on a dangling word, the last cue repeats a content word of the first cue
  visual  distance between the first and the last frame (mean absolute RGB difference and colour-histogram correlation), needs --video
  audio   loudness of the first and last 0.3 s (volumedetect), needs --video and an audio stream; a large jump is a click risk

HONEST LIMITS. The measurements say how close the seam is, not whether viewers will replay: YouTube's published definitions do not tell us which
replays are counted in the Studio figures, and one Short per variant cannot separate a good loop from a good topic. Thresholds are descriptive
labels for a reviewer, never a performance claim. Nothing here edits a timeline; `variants.py loop-close` does that.
"""
import argparse, json, os, re, shutil, subprocess, sys

DANGLING = {"AND", "THE", "A", "AN", "OF", "TO", "WITH", "BUT", "OR", "IN", "ON", "AT", "FOR", "BY", "THAT", "WHICH", "AS", "IS", "WAS", "THAN", "THEN", "SO", "BECAUSE"}
STOP = DANGLING | {"IT", "ITS", "IT'S", "THIS", "THEY", "YOU", "YOUR", "WE", "HE", "SHE", "ARE", "BE", "BEEN", "HAS", "HAVE", "WOULD", "COULD", "CAN", "NOT", "FROM", "INTO"}
DECLARED = ("none", "echo_hook", "question_answer", "visual_return", "cold_cut")

class LoopError(Exception):
    pass

def read_srt(path):
    cues = []
    with open(path, encoding="utf-8-sig") as f: raw = f.read().strip()
    for blk in re.split(r"\n\s*\n", raw):
        lines = [l for l in blk.splitlines() if l.strip()]
        m = next((re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", l) for l in lines if "-->" in l), None)
        if not m: continue
        g = [int(x) for x in m.groups()]; t0 = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000; t1 = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        cues.append([t0, t1, " ".join(l for l in lines if "-->" not in l and not l.strip().isdigit())])
    return cues
def words(t): return re.findall(r"[A-Z0-9'’%.,-]+", t.upper())
def core(w): return w.strip(".,-’'").replace("’", "'")

def text_seam(cues, window=3.0):
    """cues: [[start, end, text], ...] ordered in time. The seam is read over the last/first `window` seconds because caption cues are fragments of 1-4 words."""
    if len(cues) < 2: raise LoopError("need at least two caption cues")
    t0, t1 = cues[0][0], cues[-1][1]
    first_txt = " ".join(c[2] for c in cues if c[0] < t0 + window); last_txt = " ".join(c[2] for c in cues if c[1] > t1 - window)
    lw = [core(w) for w in words(last_txt)]; fw = [core(w) for w in words(first_txt)]
    out = {"first_window": {"start": round(t0, 3), "text": first_txt}, "last_window": {"end": round(t1, 3), "text": last_txt}, "seam_reads_as": f"... {last_txt} | {first_txt} ...", "flags": []}
    if lw and lw[-1] in DANGLING: out["flags"].append({"name": "dangling_last_word", "detail": f"the last cue ends on '{lw[-1]}': the Short stops mid-phrase"})
    shared = sorted((set(lw) & set(fw)) - STOP - {""})
    out["shared_content_words"] = shared
    if not shared: out["flags"].append({"name": "no_shared_content_word", "detail": "the closing and opening seconds share no content word; a loop has to be carried by the idea or the picture (weak mechanical signal only)"})
    return out

def _ffmpeg_ok(): return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except ValueError: raise LoopError("cannot read the video duration with ffprobe")
def has_audio(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", path], capture_output=True, text=True); return "audio" in r.stdout
def frame(path, t, size=(54, 96)):
    import numpy as np
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(t, 0):.3f}", "-i", path, "-frames:v", "1", "-vf", f"scale={size[0]}:{size[1]}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    if len(r.stdout) < size[0] * size[1] * 3: raise LoopError(f"could not decode a frame at {t:.2f} s")
    return np.frombuffer(r.stdout, np.uint8).reshape(size[1], size[0], 3).astype(float)
def last_frame(path, size=(54, 96)):
    """the final decodable frame: decode the last 0.5 s and keep the last frame (seeking to an exact timestamp near the end can return nothing)"""
    import numpy as np
    r = subprocess.run(["ffmpeg", "-v", "error", "-sseof", "-0.5", "-i", path, "-vf", f"scale={size[0]}:{size[1]}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    n = size[0] * size[1] * 3; k = len(r.stdout) // n
    if k < 1: raise LoopError("could not decode the last frame")
    return np.frombuffer(r.stdout[(k - 1) * n:k * n], np.uint8).reshape(size[1], size[0], 3).astype(float)
def visual_seam(path):
    import numpy as np
    dur = probe_duration(path); a = frame(path, 0.0); b = last_frame(path)
    dist = float(np.abs(a - b).mean() / 255.0)                       # mean absolute difference over R, G and B (a grey mean would hide hue changes)
    def hist(x): return np.concatenate([np.histogram(x[..., c], bins=16, range=(0, 256))[0] for c in range(3)]).astype(float)
    ha, hb = hist(a), hist(b); ha -= ha.mean(); hb -= hb.mean(); den = float(np.sqrt((ha ** 2).sum() * (hb ** 2).sum())); corr = float((ha * hb).sum() / den) if den else 1.0
    label = "near_identical" if dist < 0.04 and corr > 0.97 else ("similar_composition" if dist < 0.15 else "different")
    return {"first_vs_last_frame_mean_abs_diff": round(dist, 4), "colour_histogram_correlation": round(corr, 4), "label": label, "duration": round(dur, 3),
            "note": "labels are descriptive thresholds (0.04 / 0.15 mean RGB difference), not performance predictors"}
def audio_seam(path, span=0.3):
    if not has_audio(path): return {"available": False, "detail": "no audio stream"}
    dur = probe_duration(path)
    def mean_db(t0):
        r = subprocess.run(["ffmpeg", "-v", "info", "-ss", f"{t0:.3f}", "-t", f"{span}", "-i", path, "-vn", "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True)
        m = re.search(r"mean_volume: (-?[\d.]+|-inf) dB", r.stderr); return None if not m or m.group(1) == "-inf" else float(m.group(1))
    last, first = mean_db(max(dur - span, 0)), mean_db(0.0)
    out = {"available": True, "first_0_3s_mean_db": first, "last_0_3s_mean_db": last}
    if first is not None and last is not None:
        out["jump_db"] = round(abs(first - last), 1); out["label"] = "smooth" if abs(first - last) <= 6 else "level_jump"
    else: out["label"] = "silent_edge"; out["detail"] = "one end is digital silence: no click, but also no audio continuity"
    return out

def report(cues=None, video=None, declared=None):
    if declared and declared not in DECLARED: raise LoopError(f"declared strategy must be one of {DECLARED}")
    rep = {"declared_strategy": declared or "not_declared", "checks": []}
    if cues: rep["text"] = text_seam(cues)
    if video:
        if not os.path.exists(video): raise LoopError(f"video not found: {video}")
        if not _ffmpeg_ok(): rep["checks"].append({"name": "visual_audio_seam", "status": "skipped", "detail": "ffmpeg/ffprobe not installed"})
        else:
            rep["visual"] = visual_seam(video); rep["audio"] = audio_seam(video)
    notes = []
    if declared in ("visual_return",) and "visual" in rep and rep["visual"]["label"] == "different": notes.append("declared visual_return but the last frame is not close to the first frame")
    if declared in ("echo_hook", "question_answer") and "text" in rep and any(f["name"] == "dangling_last_word" for f in rep["text"]["flags"]): notes.append("declared a spoken loop but the last cue ends mid-phrase")
    if declared in (None, "none") and "visual" in rep and rep["visual"]["label"] == "near_identical": notes.append("the seam is near-identical although no loop was declared: record the strategy so the result can be attributed")
    rep["review_notes"] = notes
    rep["verdict"] = "needs_review" if notes or ("text" in rep and rep["text"]["flags"]) else "seam_ok_by_measurement"
    rep["limits"] = "measures the seam only; says nothing about replay behaviour"
    return rep

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("HONEST LIMITS")[0].strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--captions", help="JSON list of [start, end, text] or an object with a 'captions' list"); ap.add_argument("--srt"); ap.add_argument("--video"); ap.add_argument("--declared", choices=DECLARED)
    try:
        a = ap.parse_args(argv)
        if not (a.captions or a.srt or a.video): print(__doc__); return 0
        cues = None
        if a.captions:
            with open(a.captions, encoding="utf-8") as f: d = json.load(f)
            cues = d["captions"] if isinstance(d, dict) else d
        elif a.srt: cues = read_srt(a.srt)
        print(json.dumps(report(cues, a.video, a.declared), indent=1)); return 0
    except (LoopError, OSError, ValueError, KeyError) as e:
        print(json.dumps({"status": "error", "error": f"{type(e).__name__}: {e}"}, indent=1)); return 2

if __name__ == "__main__":
    sys.exit(main())
