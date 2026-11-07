#!/usr/bin/env python3
"""English SRT from the provider word timings (film time = V(narration time)). usage: captions.py OUT.srt"""
import sys
from timeline import WORDS, V

MAXC, MAXD = 84, 6.0


def fmt(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def lines(text):
    if len(text) <= 42:
        return text
    ws = text.split(); best = None
    for k in range(1, len(ws)):
        a, b = " ".join(ws[:k]), " ".join(ws[k:])
        sc = max(len(a), len(b))
        if best is None or sc < best[0]:
            best = (sc, a + "\n" + b)
    return best[1]


cues, cur = [], []
for w in WORDS:
    txt = " ".join(x["text"] for x in cur + [w])
    if cur and (len(txt) > MAXC or w["end"] - cur[0]["start"] > MAXD):
        cues.append(cur); cur = []
    cur.append(w)
    if w["text"].endswith((".", "?", "!")) and len(" ".join(x["text"] for x in cur)) > 20:
        cues.append(cur); cur = []
if cur:
    cues.append(cur)
out = []
for i, c in enumerate(cues):
    a, b = V(c[0]["start"]), V(c[-1]["end"]) + 0.15
    if i + 1 < len(cues):
        b = min(b, V(cues[i + 1][0]["start"]) - 0.02)
    out.append(f"{i + 1}\n{fmt(a)} --> {fmt(b)}\n{lines(' '.join(x['text'] for x in c))}\n")
open(sys.argv[1], "w").write("\n".join(out))
print(len(out), "cues")
