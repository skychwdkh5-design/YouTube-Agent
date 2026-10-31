#!/usr/bin/env python3
"""TEMPORARY narration for timing and the 20-s test - NOT for release.
Kokoro-82M via kokoro-onnx (Apache-2.0, runs locally, free; model files from the kokoro-onnx GitHub release
model-files-v1.0). Voice am_michael, speed 1.0. Writes voice_temp/lNNN.wav (git-ignored) + voice_temp/lines.json.

    pip install kokoro-onnx soundfile
    python3 voice_temp.py --model /path/kokoro-v1.0.onnx --voices /path/voices-v1.0.bin
"""
import argparse, json, os, re
import soundfile as sf
from kokoro_onnx import Kokoro

HERE = os.path.dirname(os.path.abspath(__file__))
a = argparse.ArgumentParser(); a.add_argument("--model", required=True); a.add_argument("--voices", required=True)
a = a.parse_args()
k = Kokoro(a.model, a.voices)
s = re.sub(r"<!--.*?-->", "", open(os.path.join(HERE, "script.md"), encoding="utf-8").read(), flags=re.S)
lines, scene = [], None
for l in s.splitlines():
    if l.startswith("[SCENE:"): scene = l[7:-1].strip(); continue
    if not l.strip() or l.startswith("#"): continue
    lines.append((scene, re.sub(r"\s*\[\[[^\]]+\]\]", "", l).strip().rstrip(" -")))
os.makedirs(os.path.join(HERE, "voice_temp"), exist_ok=True)
out = []
for i, (sc, txt) in enumerate(lines):
    audio, sr = k.create(txt, voice="am_michael", speed=1.0, lang="en-us")
    f = f"voice_temp/l{i:03d}.wav"; sf.write(os.path.join(HERE, f), audio, sr)
    out.append({"i": i, "scene": sc, "file": f, "dur": round(len(audio) / sr, 3), "text": txt})
json.dump(out, open(os.path.join(HERE, "voice_temp", "lines.json"), "w"), indent=1)
print(json.dumps({"result": "ok", "lines": len(out), "speech_s": round(sum(x["dur"] for x in out), 1), "voice": "TEMPORARY - not for release"}))
