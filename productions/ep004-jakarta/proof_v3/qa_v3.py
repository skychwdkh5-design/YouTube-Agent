"""QA of the S3 V3 REVIEW video: ffprobe, full decode, yt-qc, black / freeze detection, loudness, activity per second, phone readability
of every text element (recorded through orbitalatlas.textrec while re-composing frames every 0.25 s), review frames.
    python3 qa_v3.py VIDEO TAG OUTDIR"""
import os, sys, json, subprocess, hashlib, re, collections
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orbitalatlas import mobile_qa, textrec, illustrate as I
import compose_v3 as C, scene_v3 as V, run_v3 as R

VID, TAG, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(OUT, exist_ok=True); Q = {}
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
Q["sha256"] = hashlib.sha256(open(VID, "rb").read()).hexdigest(); Q["bytes"] = os.path.getsize(VID)
pr = json.loads(sh("ffprobe", "-v", "error", "-show_streams", "-of", "json", VID).stdout)
v = next(s for s in pr["streams"] if s["codec_type"] == "video"); a = next(s for s in pr["streams"] if s["codec_type"] == "audio")
Q["video"] = dict(codec=v["codec_name"], profile=v.get("profile"), size=f'{v["width"]}x{v["height"]}', fps=v["r_frame_rate"], frames=int(v["nb_frames"]), duration=float(v["duration"]), pix_fmt=v["pix_fmt"])
Q["audio"] = dict(codec=a["codec_name"], rate=a["sample_rate"], channels=a["channels"], duration=float(a["duration"]))
Q["decoded_frames"] = int(sh("ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", VID).stdout.strip())
Q["yt_qc"] = json.loads(sh("python3", "/home/user/YouTube-Agent/.claude/skills/yt-qc/qc.py", VID, "--expected-duration", "13.5").stdout)["result"]
fz = sh("ffmpeg", "-hide_banner", "-nostats", "-i", VID, "-vf", "freezedetect=n=0.001:d=0.5", "-an", "-f", "null", "-").stderr
Q["freeze_runs"] = [dict(start=float(s_), dur=float(d_)) for s_, d_ in zip(re.findall(r"freeze_start: ([\d.]+)", fz), re.findall(r"freeze_duration: ([\d.]+)", fz))]
Q["black_runs"] = len(re.findall(r"black_start", sh("ffmpeg", "-hide_banner", "-nostats", "-i", VID, "-vf", "blackdetect=d=0.04:pix_th=0.04", "-an", "-f", "null", "-").stderr))
eb = sh("ffmpeg", "-hide_banner", "-nostats", "-i", VID, "-af", "ebur128=peak=true", "-f", "null", "-").stderr
Q["loudness"] = dict(integrated_lufs=float(re.findall(r"I:\s+(-?[\d.]+) LUFS", eb)[-1]), true_peak_dbfs=float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", eb)[-1]))
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", VID, "-vf", "scale=320:180,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
g = np.frombuffer(raw, np.uint8).reshape(-1, 180, 320).astype(np.float32); d = np.abs(np.diff(g, axis=0))
Q["activity_per_second"] = [round(float(d[i * 30:(i + 1) * 30].mean()), 3) for i in range(13)]
issues = collections.defaultdict(list); styles = {}; sc = V.SceneV3(R.WORK, R.TEX); card = I.EvidencePending((1920, 1080), 2.0)
for t in np.arange(0.25, 13.5, 0.25):
    textrec.STATE["rec"] = recs = []
    try: fr = C.frame(int(round(t * 30)), TAG, sc, card)
    finally: textrec.STATE["rec"] = None
    mobile_qa.check_records(recs, fr, (1920, 1080), round(float(t), 2), issues)
    for x in recs: s_ = styles.setdefault(x["tag"] or "label", [1e9, 0]); s_[0] = min(s_[0], x["px"]); s_[1] += 1
Q["mobile_readability"] = dict(min_px_by_style={k: v_[0] for k, v_ in styles.items()}, n_issues={k: len(l) for k, l in issues.items()},
                               issues={k: [dict(t=t, text=x["text"][:40], why=w) for t, x, w in l][:8] for k, l in issues.items()})
os.makedirs(f"{OUT}/frames", exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", VID, "-vf", "fps=4,scale=480:270,tile=8x7", "-frames:v", "1", f"{OUT}/contact_4fps.jpg"], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", VID, "-vf", "fps=2,scale=960:540", f"{OUT}/frames/f%03d.png"], check=True)
json.dump(Q, open(f"{OUT}/qa_v3.json", "w"), indent=1)
print(json.dumps({k: Q[k] for k in ("sha256", "bytes", "video", "audio", "decoded_frames", "yt_qc", "freeze_runs", "black_runs", "loudness", "activity_per_second")}, indent=1))
print("mobile", Q["mobile_readability"]["n_issues"], Q["mobile_readability"]["min_px_by_style"])
