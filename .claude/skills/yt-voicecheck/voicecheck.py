#!/usr/bin/env python3
"""Check a generated narration against its script: file, duration, word coverage, timing order, silence, loudness, risky pronunciations. No network, no cost."""
import argparse, json, os, re, subprocess, sys

# words a TTS commonly mispronounces; listed with timestamps so the owner can listen to exactly those moments
RISKY = {"neom": "NEOM (say: NEE-om)", "sentinel": "Sentinel-2 (the '-2' must read 'two')", "landsat": "Landsat", "tabuk": "Tabuk", "ndwi": "NDWI (should be avoided aloud or spelled)",
         "copernicus": "Copernicus", "ghayyal": "proper noun", "kilometers": "unit", "km": "unit (km must read 'kilometers')"}


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,sample_rate,channels", "-of", "json", path], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    j = json.loads(r.stdout or "{}")
    s = (j.get("streams") or [{}])[0]
    return {"duration": float(j.get("format", {}).get("duration", 0) or 0), "codec": s.get("codec_name"), "sample_rate": s.get("sample_rate"), "channels": s.get("channels")}


def run(root, spoken, meta_path, wav):
    checks, risky = [], []

    def add(i, status, detail):
        checks.append({"id": i, "status": status, "detail": detail})
    if not os.path.exists(wav) or not os.path.exists(meta_path):
        add("files", "fail", f"missing {wav if not os.path.exists(wav) else meta_path}")
        return {"result": "FAIL", "checks": checks, "risky": risky}
    meta = json.load(open(meta_path, encoding="utf-8"))
    pr = probe(wav)
    if not pr or pr["duration"] <= 0:
        add("audio", "fail", "ffprobe cannot read the audio file or it has no duration")
        return {"result": "FAIL", "checks": checks, "risky": risky}
    add("audio", "pass", f"{pr['codec']} {pr['sample_rate']} Hz, {pr['channels']} ch, {pr['duration']:.1f}s")
    words = meta.get("words") or []
    text = open(spoken, encoding="utf-8").read()
    sw = [w for w in text.split() if norm(w)]
    # duration: 2.0-3.2 words/s is normal narration; far outside means truncation or a runaway generation
    wps = len(sw) / pr["duration"]
    add("duration", "pass" if 2.0 <= wps <= 3.2 else "fail", f"{len(sw)} script words / {pr['duration']:.1f}s = {wps:.2f} words/s (accepted 2.0-3.2)")
    if abs(meta.get("duration", pr["duration"]) - pr["duration"]) > 1.5:
        add("meta_duration", "fail", f"voice.json says {meta.get('duration')}s, file is {pr['duration']:.1f}s")
    # sync: every script word must have a timing, in order, inside the audio
    mw = [norm(w["text"]) for w in words if norm(w["text"])]
    sn = [norm(w) for w in sw]
    if not words:
        add("timings", "fail", "no word timings in voice.json: captions and sync impossible")
    else:
        miss = abs(len(mw) - len(sn))
        add("coverage", "pass" if miss <= max(3, int(0.01 * len(sn))) else "fail", f"{len(mw)} timed words vs {len(sn)} script words (diff {miss})")
        back = [i for i in range(1, len(words)) if words[i]["start"] < words[i - 1]["start"] - 0.001]
        over = [i for i, w in enumerate(words) if w["end"] > pr["duration"] + 0.5 or w["end"] < w["start"]]
        add("order", "pass" if not back and not over else "fail", f"{len(back)} out-of-order, {len(over)} out-of-range timings")
        end_gap = pr["duration"] - words[-1]["end"]
        add("tail", "pass" if -0.5 <= end_gap <= 6 else "fail", f"last word ends {end_gap:.1f}s before the end of the file")
        gaps = [(words[i]["start"] - words[i - 1]["end"], i) for i in range(1, len(words))]
        big = [(round(g, 1), round(words[i]["start"], 1)) for g, i in gaps if g > 2.5]
        add("pauses", "pass" if not big else "warn", "no pause over 2.5s" if not big else f"{len(big)} pauses over 2.5s at {[t for _, t in big][:8]}")
        for w in words:
            k = norm(w["text"])
            if k in RISKY:
                risky.append({"at": round(w["start"], 2), "word": w["text"], "note": RISKY[k]})
    # silence and loudness from the real audio
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", wav, "-af", "silencedetect=n=-45dB:d=3,volumedetect", "-f", "null", "-"], capture_output=True, text=True)
    sil = re.findall(r"silence_duration: ([0-9.]+)", r.stderr)
    mv = re.search(r"mean_volume: (-?[0-9.]+) dB", r.stderr)
    mx = re.search(r"max_volume: (-?[0-9.]+) dB", r.stderr)
    add("silence", "pass" if not sil else "fail", "no silence of 3s or more" if not sil else f"{len(sil)} silent stretches of 3s or more (longest {max(map(float, sil)):.1f}s): speech may be missing")
    if mv and mx:
        m, x = float(mv.group(1)), float(mx.group(1))
        add("loudness", "pass" if m > -40 and x < -0.1 else "fail", f"mean {m} dB, peak {x} dB (silent file or clipping would fail)")
    else:
        add("loudness", "fail", "could not measure")
    fails = [c for c in checks if c["status"] == "fail"]
    # pronunciation cannot be judged by a script: the risky moments are listed for a human ear, never marked as passed
    return {"result": "FAIL" if fails else "NEEDS_HUMAN_LISTEN", "checks": checks, "risky": risky,
            "listen": "Automatic checks cannot hear mispronunciation. Listen to the moments in `risky` (and the first 30 seconds) before the paid render.",
            "words": len(sn), "duration": round(pr["duration"], 2)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default="."); ap.add_argument("--spoken", default="voice/spoken.md"); ap.add_argument("--meta", default="voice/narration.voice.json")
    ap.add_argument("--audio", default="voice/narration.wav"); ap.add_argument("--out", default="voice/voicecheck.json")
    a = ap.parse_args()
    j = lambda p: p if os.path.isabs(p) else os.path.join(a.root, p)
    res = run(a.root, j(a.spoken), j(a.meta), j(a.audio))
    os.makedirs(os.path.dirname(j(a.out)), exist_ok=True)
    json.dump(res, open(j(a.out), "w"), indent=1)
    print(json.dumps(res, indent=1))
    return 1 if res["result"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
