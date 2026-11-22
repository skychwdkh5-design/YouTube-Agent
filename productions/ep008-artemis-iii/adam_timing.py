#!/usr/bin/env python3
"""Adam word timings (ElevenLabs alignment, adam/timing/adam_sNN.voice.json) -> voice_adam/timing.json in the same shape as
tts_temp.py ({scene: {dur, sentences: [{text, start, end}]}}), sentences split exactly as tts_temp.py splits them.
Also copies/links the per-scene wav as voice_adam/sNN.wav. Fails loudly if words and script do not line up."""
import json, os, re, sys, glob, shutil
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); media = sys.argv[1]
out = os.path.join(HERE, "voice_adam"); os.makedirs(out, exist_ok=True)
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
res = {}
for vj in sorted(glob.glob(os.path.join(HERE, "adam", "timing", "adam_s*.voice.json"))):
    sid = os.path.basename(vj)[5:8]; meta = json.load(open(vj)); words = meta.get("words") or []
    assert words, f"{sid}: no word timings"
    vo = open(os.path.join(HERE, "adam", sid + ".md")).read().strip()
    sents = [s for s in re.split(r"(?<=[.?!:])\s+", vo) if s]
    k = 0; out_s = []
    for s in sents:
        n = len([w for w in s.split() if norm(w)])
        ws = [w for w in words[k:k + n]]
        assert [norm(w["text"]) for w in ws] == [norm(w) for w in s.split() if norm(w)], f"{sid}: alignment mismatch at '{s[:40]}'"
        out_s.append({"text": s, "start": round(ws[0]["start"], 3), "end": round(ws[-1]["end"], 3)}); k += n
    wav = os.path.join(media, f"adam_{sid}.wav"); a, sr = sf.read(wav)
    shutil.copy(wav, os.path.join(out, sid + ".wav"))
    res[sid] = {"dur": round(len(a) / sr, 3), "sentences": out_s, "last_word_end": round(words[-1]["end"], 3)}
json.dump(res, open(os.path.join(out, "timing.json"), "w"), indent=1)
print(json.dumps({sid: [v["dur"], len(v["sentences"])] for sid, v in res.items()}))
