"""Turn yt-voice/1 metadata (Adam, word timings) into narration.timing.json for build.py / package.py.
Beat boundaries come from counting the words of each approved beat in the provider's word list (no estimates).
python3 adam_timing.py <beats_module> <voice_dir>   (expects <voice_dir>/narration.voice.json + narration.wav)"""
import importlib, json, os, re, sys
mod, vdir = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
B = importlib.import_module(mod).BEATS
meta = json.load(open(os.path.join(vdir, "narration.voice.json")))
words = meta["words"]
counts = [len(t.split()) for t, _ in B]
if sum(counts) != len(words):
    sys.exit(json.dumps({"status": "error", "error": f"word count mismatch: script {sum(counts)} vs timings {len(words)}"}))
beats, i = [], 0
for bi, c in enumerate(counts):
    w0, w1 = words[i], words[i + c - 1]
    beats.append({"index": bi, "start": round(w0["start"], 3), "speech_end": round(w1["end"], 3)})
    i += c
json.dump({"engine": f"{meta['provider']} {meta.get('model_id')} voice {meta.get('voice_name')}", "duration": round(meta["duration"] + 1.0, 3),
           "beats": beats}, open(os.path.join(vdir, "narration.timing.json"), "w"), indent=1)
print(json.dumps({"status": "ok", "beats": len(beats), "duration": round(meta["duration"] + 1.0, 3), "last_word_end": words[-1]["end"]}))
