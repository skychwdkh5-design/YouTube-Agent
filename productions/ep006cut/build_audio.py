"""EP006 short cut: remove repeated / optional sentences from the EXISTING narration (no new generation). Cuts only at sentence boundaries, keeps every hedge.
Writes voice/narration.wav + voice/narration.voice.json (word timings re-timed) and story/cut_map.json (old -> new time per kept sentence)."""
import json, wave, hashlib, numpy as np, os
SRC = "../ep006/voice/"
DROP = {5, 10, 25, 26, 38, 39, 43, 53, 54, 60, 61}
w = json.load(open(SRC + "narration.voice.json"))
words = w["words"]
sents, cur = [], []
for x in words:
    cur.append(x)
    if x["text"].endswith((".", "?")):
        sents.append(cur); cur = []
wf = wave.open(SRC + "narration.wav"); sr = wf.getframerate(); pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32)
LEAD, TAIL, FADE = 0.20, 0.30, int(0.012 * sr)
keep = [i for i in range(len(sents)) if i not in DROP]
groups, g = [], [keep[0]]
for i in keep[1:]:
    (g.append(i) if i == g[-1] + 1 else (groups.append(g), g := [i]))
groups.append(g)
out, new_words, cmap, t_new = [], [], [], 0.0
for gi, g in enumerate(groups):
    a0 = sents[g[0]][0]["start"]; b0 = sents[g[-1]][-1]["end"]
    prev_end = sents[g[0] - 1][-1]["end"] if g[0] > 0 else 0.0
    next_start = sents[g[-1] + 1][0]["start"] if g[-1] + 1 < len(sents) else len(pcm) / sr
    a = max(prev_end + 0.02, a0 - LEAD) if g[0] > 0 else max(0.0, a0 - 0.05)
    b = min(next_start - 0.02, b0 + TAIL)
    seg = pcm[int(a * sr):int(b * sr)].copy()
    n = len(seg); f = min(FADE, n // 2)
    if gi > 0: seg[:f] *= np.linspace(0, 1, f)
    if gi < len(groups) - 1: seg[-f:] *= np.linspace(1, 0, f)
    for i in g:
        for x in sents[i]:
            new_words.append(dict(x, start=round(x["start"] - a + t_new, 3), end=round(x["end"] - a + t_new, 3)))
        cmap.append({"sentence": i, "old_start": round(sents[i][0]["start"], 3), "new_start": round(sents[i][0]["start"] - a + t_new, 3), "new_end": round(sents[i][-1]["end"] - a + t_new, 3), "text": " ".join(c["text"] for c in sents[i])})
    out.append(seg); t_new += n / sr
audio = np.concatenate(out).astype(np.int16)
with wave.open("voice/narration.wav", "wb") as o:
    o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes(audio.tobytes())
sha = hashlib.sha256(open("voice/narration.wav", "rb").read()).hexdigest()
text = " ".join(x["text"] for x in new_words)
m = dict(w, words=new_words, duration=round(len(audio) / sr, 3), audio="narration.wav", audio_sha256=sha, characters=sum(len(x["text"]) for x in new_words), text=text,
         text_sha256=hashlib.sha256(text.encode()).hexdigest(), edited_from="ep006/voice/narration.wav", edit_note="sentence-level cut of the existing paid narration; no new generation; dropped sentence indexes " + str(sorted(DROP)))
json.dump(m, open("voice/narration.voice.json", "w"), indent=1)
json.dump(cmap, open("story/cut_map.json", "w"), indent=1)
print("old", round(w["duration"], 1), "new", m["duration"], "saved", round(w["duration"] - m["duration"], 1), "groups", len(groups))
