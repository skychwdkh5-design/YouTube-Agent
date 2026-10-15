"""Independent-ish QA of the EP004 S3 V2 proof: technical (ffprobe, yt-qc, orbitalatlas.qa, freeze/black/audio), phone readability from recorded text, and
frame extraction for the human/agent review. Writes qa/proof_qa.json. `python3 qa_proof.py VIDEO OUTDIR`"""
import os, sys, json, subprocess, hashlib, re
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
sys.path.insert(0, os.path.dirname(__file__))
from orbitalatlas import qa, mobile_qa, textrec
import build_proof_v2 as B

V, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True); R = {}
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
R["sha256"] = hashlib.sha256(open(V, "rb").read()).hexdigest(); R["bytes"] = os.path.getsize(V)
pr = json.loads(sh("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", V).stdout)
v = next(s for s in pr["streams"] if s["codec_type"] == "video"); a = next(s for s in pr["streams"] if s["codec_type"] == "audio")
R["video"] = dict(codec=v["codec_name"], size=f'{v["width"]}x{v["height"]}', fps=v["r_frame_rate"], frames=int(v["nb_frames"]), duration=float(v["duration"]), pix_fmt=v["pix_fmt"])
R["audio"] = dict(codec=a["codec_name"], rate=a["sample_rate"], channels=a["channels"])
R["decoded_frames"] = int(sh("ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", V).stdout.strip())
R["yt_qc"] = json.loads(sh("python3", ".claude/skills/yt-qc/qc.py", V, "--expected-duration", "13.5").stdout)["result"]
seq = B.program(); r = qa.run_video(V, schedule=seq.schedule(), problems=seq.problems, cuts=[], holds=[(12.9, 13.5)])
R["orbitalatlas_qa"] = dict(ok=r["ok"], issues=r["issues"], stats=r["stats"])
fz = sh("ffmpeg", "-hide_banner", "-nostats", "-i", V, "-vf", "freezedetect=n=0.001:d=0.5", "-an", "-f", "null", "-").stderr
st = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", fz)]; du = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", fz)]
R["freeze_runs_n0.001_d0.5"] = [dict(start=a_, dur=b_) for a_, b_ in zip(st, du)]
R["black_frames"] = len(re.findall(r"black_start", sh("ffmpeg", "-hide_banner", "-nostats", "-i", V, "-vf", "blackdetect=d=0.04:pix_th=0.04", "-an", "-f", "null", "-").stderr))
eb = sh("ffmpeg", "-hide_banner", "-nostats", "-i", V, "-af", "ebur128=peak=true", "-f", "null", "-").stderr
R["audio_loudness"] = dict(integrated_lufs=float(re.findall(r"I:\s+(-?[\d.]+) LUFS", eb)[-1]), true_peak_dbfs=float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", eb)[-1]))
# per-second activity
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", V, "-vf", "scale=320:180,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
g = np.frombuffer(raw, np.uint8).reshape(-1, 180, 320).astype(np.float32); d = np.abs(np.diff(g, axis=0))
R["activity_per_second"] = [dict(s=f"{i}-{i + 1}", mean_abs_diff=round(float(d[i * 30:(i + 1) * 30].mean()), 3), changed_pixels_pct=round(float((d[i * 30:(i + 1) * 30] > 8).mean() * 100), 2)) for i in range(13)]
# phone readability from recorded text (the same checker the director programmes use)
issues = __import__("collections").defaultdict(list); styles = {}
for t in np.arange(0.25, 13.5, 0.25):
    textrec.STATE["rec"] = recs = []
    try: fr = seq.render(float(t))
    finally: textrec.STATE["rec"] = None
    mobile_qa.check_records(recs, fr, (1920, 1080), round(float(t), 2), issues)
    for x in recs: s_ = styles.setdefault(x["tag"] or "label", [1e9, 0]); s_[0] = min(s_[0], x["px"]); s_[1] += 1
R["mobile_readability"] = dict(frames_checked=len(np.arange(0.25, 13.5, 0.25)), min_px_by_style={k: dict(min_px=v[0], phone_pt_landscape=mobile_qa.pt(v[0])["landscape"], phone_pt_portrait=mobile_qa.pt(v[0])["portrait"], draws=v[1]) for k, v in styles.items()},
    issues={k: [dict(t=t, text=x["text"][:50], why=w) for t, x, w in l][:12] for k, l in issues.items()}, n_issues={k: len(l) for k, l in issues.items()})
# frames for review: 2 fps + every frame of the transition window
os.makedirs(f"{OUT}/frames", exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", V, "-vf", "fps=2,scale=960:540", f"{OUT}/frames/f%03d.png"], check=True)
os.makedirs(f"{OUT}/transition", exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "12.1", "-t", "0.8", "-i", V, "-vf", "scale=480:270", f"{OUT}/transition/t%02d.png"], check=True)
json.dump(R, open(f"{OUT}/proof_qa.json", "w"), indent=1); print(json.dumps({k: R[k] for k in ("sha256", "video", "yt_qc", "decoded_frames", "black_frames", "audio_loudness", "freeze_runs_n0.001_d0.5")}, indent=1)); print("orbitalatlas_qa", R["orbitalatlas_qa"]["ok"], R["orbitalatlas_qa"]["issues"]); print("mobile", R["mobile_readability"]["n_issues"], R["mobile_readability"]["min_px_by_style"])
