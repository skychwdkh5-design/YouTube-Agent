#!/usr/bin/env python3
"""Temporary LOCAL narration (ffmpeg flite, voice slt) for EP009 Long + 2 Shorts. No paid TTS.
Outputs prod/<name>/voice.wav, prod/<name>/timeline.json (sentence start/end, section), prod/<name>/captions.srt"""
import re, json, subprocess, sys, os, wave
import numpy as np
REPO = "/home/claude/skychwdkh5-design/youtube-agent/productions/ep009-tornado-scars"; OUT = "/home/claude/ep009/prod"; SR = 48000
TEMPO = 0.93                                   # mild slow-down of the (fast) flite voice; review voice only
FIX = {"the day after the devastating outbreak": "the day after the April twenty-seventh tornadoes"}   # QC FACT-1 (Apr 28 is the last outbreak day)

def sents(t): return [s.strip() for s in re.split(r"(?<=[.?!])\s+", t.strip()) if s.strip()]
def tts(text, path):
    open(f"{OUT}/_t.txt", "w").write(text)
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"flite=textfile={OUT}/_t.txt:voice=slt", "-af", f"atempo={TEMPO},aresample={SR}", "-ac", "1", path])
def wav(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768

def build(name, items, gaps):
    """items: [(section, paragraph_id, sentence)]"""
    d = f"{OUT}/{name}"; os.makedirs(d, exist_ok=True); t = 0.4; tl = []; chunks = []; prev = None
    for i, (sec, para, s) in enumerate(items):
        for a, b in FIX.items(): s = s.replace(a, b)
        p = f"{d}/s{i:03d}.wav"; tts(s, p); x = wav(p)
        if prev is not None: t += gaps["sec"] if sec != prev[0] else gaps["para"] if para != prev[1] else gaps["sent"]
        tl.append(dict(i=i, section=sec, text=s, start=round(t, 3), end=round(t + len(x) / SR, 3))); chunks.append((t, x)); t += len(x) / SR; prev = (sec, para)
    total = t + 1.2; mix = np.zeros(int(total * SR) + SR, np.float32)
    for st, x in chunks: i0 = int(st * SR); mix[i0:i0 + len(x)] += x
    mix = mix[:int(total * SR)]; mix = mix / (np.abs(mix).max() + 1e-9) * 0.7
    with wave.open(f"{d}/voice.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype("<i2").tobytes())
    json.dump(dict(duration=round(total, 2), cues=tl), open(f"{d}/timeline.json", "w"), indent=1)
    # SRT: <=2 lines of <=42 chars
    def ts(x): h, r = divmod(x, 3600); m, s = divmod(r, 60); return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    srt = []; n = 0
    for c in tl:
        words = c["text"].split(); lines = []; cur = ""
        for w_ in words:
            if len(cur) + len(w_) + 1 > 42 and cur: lines.append(cur); cur = w_
            else: cur = (cur + " " + w_).strip()
        lines.append(cur); pages = [lines[k:k + 2] for k in range(0, len(lines), 2)]
        dur = c["end"] - c["start"]; tot = sum(len(" ".join(p_)) for p_ in pages); a = c["start"]
        for p_ in pages:
            b = a + dur * len(" ".join(p_)) / tot; n += 1; srt.append(f"{n}\n{ts(a)} --> {ts(b)}\n" + "\n".join(p_) + "\n"); a = b
    open(f"{d}/captions.srt", "w").write("\n".join(srt))
    print(name, "duration", round(total, 1), "s,", len(tl), "sentences,", sum(len(i[2].split()) for i in items), "words")

# ---- Long
txt = open(f"{REPO}/script_en.md").read().split("## Editorial fact-check")[0]; items = []; sec = None; pid = 0
for line in txt.splitlines():
    line = line.strip()
    m = re.match(r"\[(\d\d:\d\d) ([A-Z0-9 \-]+)\]", line)
    if m: sec = m.group(2).strip(); continue
    if not line or line.startswith("#") or line.startswith("Target"): continue
    pid += 1
    for s in sents(line): items.append((sec, pid, s))
build("long", items, dict(sent=0.55, para=0.95, sec=1.7))
# ---- Shorts
for n, f in ((1, "short_01"), (2, "short_02")):
    t = open(f"{REPO}/shorts/{f}.md").read(); vo = re.search(r'VO: "(.*?)"\s*\n', t, re.S).group(1)
    build(f"s{n}", [("S", 1, s) for s in sents(vo)], dict(sent=0.3, para=0.3, sec=0.3))
