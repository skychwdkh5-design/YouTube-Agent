#!/usr/bin/env python3
"""EP009 pilot audio: temporary Flite SLT voice (free, local) placed at storyboard beat starts, plus quiet
self-synthesised transition whooshes (no third-party SFX, so no clearance needed). Voice is NOT time-stretched."""
import json, wave, numpy as np, subprocess
SR, DUR = 48000, 56.0
V = "/home/claude/ep009/voice"
beats = json.load(open(f"{V}/voice_durations.json"))
bed = np.zeros(int(SR * DUR))
rng = np.random.default_rng(9)

def read(p):
    with wave.open(p) as w: x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32768
    return x

def whoosh(n=int(SR * 0.6)):
    t = np.linspace(0, 1, n); x = rng.standard_normal(n); y = np.zeros(n); acc = 0.0
    k = 1 - np.exp(-2 * np.pi * (300 + 3000 * t ** 1.5) / SR)
    for i in range(n): acc += k[i] * (x[i] - acc); y[i] = acc
    return y * np.sin(np.pi * t) ** 2

def boom(n=int(SR * 1.2)):
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-t * 12)) / SR) * np.exp(-t * 3.5)

def put(x, t, gain):
    i = int(t * SR); j = min(len(bed), i + len(x)); bed[i:j] += x[: j - i] * gain

starts = {}
for b in beats:
    s = b["planned_start"] + (0.15 if b["planned_start"] == 0 else 0.25)
    starts[b["beat"]] = (round(s, 2), round(s + b["dur"], 2))
    put(read(f"{V}/{b['beat']}.wav"), s, 1.0)
w = whoosh()
for t in (2.85, 6.85, 11.85, 17.85, 23.85, 29.85, 37.85, 46.85): put(w / np.abs(w).max(), t, 0.06)
b0 = boom(); put(b0 / np.abs(b0).max(), 0.0, 0.12)
pcm = (np.clip(bed, -1, 1) * 32767).astype("<i2")
with wave.open("/home/claude/ep009/audio_raw.wav", "wb") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes(pcm.tobytes())
json.dump(starts, open("/home/claude/ep009/voice_placement.json", "w"), indent=1)
print(starts)
