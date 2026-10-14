"""Synchronisation check of a RENDERED video against its plan (not against the code that made it).

    python3 -m orbitalatlas.demo.verify_sync VIDEO.mp4 PLAN.json

1. AUDIO vs WORDS: decode the audio of the file; for every word the loudness just after its start must exceed the loudness just before it (an onset at the stated time, tolerance 60 ms).
   Words that follow another word with no pause cannot show an onset and are reported as 'continuous', not as failures.
2. CAPTIONS vs WORDS (coarse): decode frames at 30 fps; the biggest change of the caption band near every card start must be within +-4 frames (133 ms) of the card's first word. Camera motion also changes the band, so this is an upper bound on the error, not a measurement of it.
Only meaningful when plan.timing_source is 'provider' or 'alignment'; for 'estimated'/'simulated' it says so and does not report a pass."""
import json
import subprocess
import sys
import numpy as np


def audio(path, rate=22050):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0, rate


def band_frames(path, y0, y1, w=480, h=270, fps=30):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-an", "-vf", f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    return a[:, int(y0 * h):int(y1 * h), :]


def rms(a, r, t0, t1):
    i0, i1 = max(0, int(t0 * r)), max(1, int(t1 * r)); seg = a[i0:i1]; return float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0


def check(video, plan):
    src = plan.get("timing_source"); words = plan["words"]; out = dict(timing_source=src, frame_accurate=plan.get("frame_accurate"))
    a, r = audio(video); ok = cont = bad = 0; fails = []
    for i, w in enumerate(words):
        gap = w["start"] - words[i - 1]["end"] if i else 1.0
        if gap < 0.03: cont += 1; continue
        win = min(gap, 0.06); after = rms(a, r, w["start"], w["start"] + 0.06); before = rms(a, r, w["start"] - win * 0.85, w["start"] - win * 0.15)   # the pause itself, not the previous word's tail
        if after > before * 2.0 and after > 0.01: ok += 1
        else: bad += 1; fails.append((w["text"], round(w["start"], 3)))
    out["audio"] = dict(onsets_ok=ok, continuous=cont, failed=bad, failed_words=fails)
    fr = band_frames(video, 0.62, 0.95); d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2)); fps = 30.0
    cards = plan["cards"]; res = []
    for c in cards:
        f0 = int(round(c["t0"] * fps)); win = d[max(0, f0 - 4):f0 + 4]
        peak = (int(np.argmax(win)) + max(0, f0 - 4)) if len(win) else -1
        res.append(dict(card=c["text"][:28], t0=c["t0"], change_frame=peak, offset_frames=peak - f0, ok=abs(peak - f0) <= 4))
    out["captions"] = dict(cards=len(cards), within_tolerance=sum(1 for x in res if x["ok"]), detail=res)
    out["pass"] = bool(src in ("provider", "alignment") and bad == 0 and all(x["ok"] for x in res))
    if src not in ("provider", "alignment"): out["note"] = "timing is not frame accurate; no pass reported"
    return out


if __name__ == "__main__":
    plan = json.load(open(sys.argv[2])); plan = plan.get("plan", plan)
    print(json.dumps(check(sys.argv[1], plan), indent=1))
