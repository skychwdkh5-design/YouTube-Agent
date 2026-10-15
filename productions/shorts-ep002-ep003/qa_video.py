"""technical QA of a rendered Short: exact length and frame count, size, fps, black frames, motion per frame (longest near-static run),
loop seam (last frame vs first), integrated loudness and true peak. Complements .claude/skills/yt-qc/qc.py (run separately).
    python3 qa_video.py VIDEO.mp4 [--sheet OUT.jpg]"""
import json, subprocess, sys
import numpy as np
from PIL import Image

W, H, FPS, DUR = 1080, 1920, 30, 15.0


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=codec_type,width,height,r_frame_rate,nb_read_frames,duration", "-of", "json", path],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)["streams"]


def frames(path, w=270, h=480):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(np.float32)


def loudness(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    tail = r[r.rfind("Summary:"):]; I = TP = None
    for line in tail.splitlines():
        line = line.strip()
        if line.startswith("I:"): I = float(line.split()[1])
        if line.startswith("Peak:"): TP = float(line.split()[1])
    return I, TP


def main(path, sheet=None):
    st = probe(path); v = next(s for s in st if s["codec_type"] == "video"); a = [s for s in st if s["codec_type"] == "audio"]
    F = frames(path); n = len(F); luma = F.mean(axis=(1, 2, 3)); diff = np.abs(np.diff(F, axis=0)).mean(axis=(1, 2, 3))
    static = diff < 0.35; run = best = 0
    for s in static: run = run + 1 if s else 0; best = max(best, run)
    seam = float(np.abs(F[-1] - F[0]).mean()); I, TP = loudness(path)
    num, den = map(int, v["r_frame_rate"].split("/"))
    rep = dict(file=path, size=[v["width"], v["height"]], fps=num / den, frames=int(v["nb_read_frames"]), video_s=float(v["duration"]), audio_s=float(a[0]["duration"]) if a else None,
               black_frames=int((luma < 8).sum()), min_luma=round(float(luma.min()), 1), median_motion=round(float(np.median(diff)), 2),
               longest_static_run_s=round(best / FPS, 2), loop_seam_mad=round(seam, 2), typical_cut_mad=round(float(np.percentile(diff, 99)), 2), lufs=I, true_peak_dbfs=TP)
    checks = dict(size=rep["size"] == [W, H], fps=abs(rep["fps"] - FPS) < 1e-6, frames=rep["frames"] == int(DUR * FPS), duration=abs(rep["video_s"] - DUR) < 0.02,
                  audio=rep["audio_s"] is not None and abs(rep["audio_s"] - DUR) < 0.05, no_black=rep["black_frames"] == 0, no_static_over_1s=rep["longest_static_run_s"] <= 1.0,
                  loop_seam_below_a_cut=rep["loop_seam_mad"] < max(rep["typical_cut_mad"], 6.0), loudness=I is not None and -15.5 <= I <= -12.5, peak=TP is not None and TP <= -1.0)
    rep["checks"] = checks; rep["result"] = "PASS" if all(checks.values()) else "FAIL"
    if sheet:
        idx = [int(i) for i in np.linspace(0, n - 1, 16)]; im = Image.new("RGB", (270 * 8, 480 * 2))
        for k, i in enumerate(idx): im.paste(Image.fromarray(F[i].astype(np.uint8)), ((k % 8) * 270, (k // 8) * 480))
        im.save(sheet, quality=85)
    print(json.dumps(rep, indent=1)); return rep


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[sys.argv.index("--sheet") + 1] if "--sheet" in sys.argv else None)
