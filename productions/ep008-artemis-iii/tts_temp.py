#!/usr/bin/env python3
"""TEMPORARY narration for EP008 drafts - NOT for release (same approach as EP007 tts_draft.py / NEXORA voice_temp.py).
Kokoro-82M via kokoro-onnx (Apache-2.0, local, free). Voice am_michael. Reads scene text from script/edit_map.json.

    python3 tts_temp.py --model kokoro-v1.0.onnx --voices voices-v1.0.bin [--scenes s01,s02] [--out voice_temp]

Writes <out>/<scene>.wav (24 kHz mono, git-ignored) and <out>/timing.json:
{scene: {"dur": s, "sentences": [{"text", "start", "end"}]}} - sentence times are relative to the scene start.
"""
import argparse, json, os, re
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

HERE = os.path.dirname(os.path.abspath(__file__))
a = argparse.ArgumentParser()
a.add_argument("--model", required=True); a.add_argument("--voices", required=True)
a.add_argument("--scenes", default=""); a.add_argument("--out", default=os.path.join(HERE, "voice_temp"))
a.add_argument("--speed", type=float, default=1.0)
a = a.parse_args()
k = Kokoro(a.model, a.voices)
scenes = json.load(open(os.path.join(HERE, "script", "edit_map.json")))["scenes"]
want = set(filter(None, a.scenes.split(",")))
os.makedirs(a.out, exist_ok=True)
tp = os.path.join(a.out, "timing.json")
timing = json.load(open(tp)) if os.path.exists(tp) else {}
GAP = 0.18                                   # pause between sentences
for s in scenes:
    if want and s["id"] not in want:
        continue
    parts, sent, t = [], [], 0.0
    for txt in re.split(r"(?<=[.?!:])\s+", s["vo"].strip()):
        if not txt:
            continue
        audio, sr = k.create(txt, voice="am_michael", speed=a.speed, lang="en-us")
        audio = np.asarray(audio, dtype=np.float32)
        sent.append({"text": txt, "start": round(t, 3), "end": round(t + len(audio) / sr, 3)})
        parts += [audio, np.zeros(int(GAP * sr), np.float32)]
        t += len(audio) / sr + GAP
    sf.write(os.path.join(a.out, s["id"] + ".wav"), np.concatenate(parts), sr)
    timing[s["id"]] = {"dur": round(t, 3), "sentences": sent}
json.dump(timing, open(tp, "w"), indent=1)
print(json.dumps({"result": "ok", "scenes": sorted(timing), "voice": "TEMPORARY Kokoro am_michael - not for release"}))
