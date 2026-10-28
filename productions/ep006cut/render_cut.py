"""Render the cut preview in 4 parallel segments (render-test on the cut narration), trim to exact shot boundaries, encode 720p/15 fps, concat."""
import json, subprocess, sys, os, concurrent.futures as cf, time
R = "/home/user/YouTube-Agent"; slug = "ep006cut"; root = f"{R}/productions/{slug}"
tl = json.load(open(f"{root}/timeline.json")); end = json.load(open(f"{root}/voice/narration.voice.json"))["duration"]
cuts = [0.0, 93.682, 203.665, 296.166]; starts = [s["start"] for s in tl["shots"]]
assert all(any(abs(c - s) < 0.02 for s in starts) for c in cuts)
def run(i):
    t0 = cuts[i]; t1 = cuts[i + 1] if i + 1 < len(cuts) else None
    secs = (t1 - t0) if t1 else (end - t0 + 1)
    r = subprocess.run(["python3", f"{R}/.claude/skills/yt-orchestrate/orchestrate.py", "render-test", "--slug", slug, "--start", f"{t0:.3f}", "--seconds", f"{secs:.3f}", "--name", f"seg{i}", "--timeline", "timeline.json", "--fps", "15", "--run"], capture_output=True, text=True, cwd=R)
    d = json.loads(r.stdout)
    if d.get("status") != "ok": raise SystemExit(f"seg{i}: {d}")
    meta = json.load(open(f"{root}/render/seg{i}/narration.seg{i}.voice.json"))
    off = max(t0 - meta.get("excerpt_from", 0.0), 0.0)
    dst = f"{root}/render/seg{i}/seg720.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y"] + (["-ss", f"{off:.3f}"] if off else []) + ["-i", f"{root}/render/seg{i}/seg{i}.mp4"] + (["-t", f"{t1 - t0:.3f}"] if t1 else []) + ["-vf", "scale=1280:720,fps=15,format=yuv420p", "-c:v", "libx264", "-preset", "fast", "-crf", "25", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2", dst]
    subprocess.run(cmd, check=True)
    return i
t = time.time()
segs = [int(x) for x in os.environ.get("SEGS", "0,1,2,3").split(",")]
with cf.ThreadPoolExecutor(3) as ex: list(ex.map(run, segs))
open(f"{root}/render/list.txt", "w").write("".join(f"file '{root}/render/seg{i}/seg720.mp4'\n" for i in range(len(cuts))))
out = f"{root}/render/EP006_cut_preview_720p15.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{root}/render/list.txt", "-c", "copy", "-movflags", "+faststart", out], check=True)
print("done", round(time.time() - t), out)
