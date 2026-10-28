"""Temporary draft narration with Kokoro (local, free, Apache-2.0). NOT the channel narrator.
Each caption-sized phrase is synthesized separately, so every caption cue has exact audio timing.
Usage: python3 tts_draft.py beats_module out_dir [voice]"""
import importlib, json, re, sys, os
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

MOD, OUT = sys.argv[1], sys.argv[2]
VOICE = sys.argv[3] if len(sys.argv) > 3 else "am_michael"
SPEED = float(os.environ.get("TTS_SPEED", "1.0"))
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.getcwd())
BEATS = importlib.import_module(MOD).BEATS
K = Kokoro("/home/claude/tts/kokoro-v1.0.onnx", "/home/claude/tts/voices-v1.0.bin")
SR = 24000
GAP_PHRASE, GAP_BEAT, LEAD = 0.14, 0.38, 0.25


def phrases(text, limit=78):
    sents = re.split(r"(?<=[.?!:])\s+", text.strip())
    out = []
    for s in sents:
        while len(s) > limit:
            cut = None
            for m in re.finditer(r"[,;]\s|\s(and|but|so|which|where|when)\s", s):
                if 20 < m.start() < limit:
                    cut = m.start() + (1 if s[m.start()] in ",;" else 0)
            if cut is None:
                sp = s.rfind(" ", 0, limit); cut = sp
            out.append(s[:cut].strip()); s = s[cut:].strip()
        if s:
            out.append(s)
    return out


audio = [np.zeros(int(LEAD * SR), dtype=np.float32)]
t = LEAD
beats_out, cues = [], []
for bi, (text, _shots) in enumerate(BEATS):
    b0 = t
    for pi, ph in enumerate(phrases(text)):
        s, sr = K.create(ph, voice=VOICE, speed=SPEED, lang="en-us")
        assert sr == SR
        s = s.astype(np.float32)
        # trim leading/trailing near-silence so cue edges sit on speech
        nz = np.where(np.abs(s) > 0.004)[0]
        if len(nz):
            s = s[max(0, nz[0] - 240): nz[-1] + 480]
        cues.append({"start": round(t, 3), "end": round(t + len(s) / SR, 3), "text": ph})
        audio.append(s); t += len(s) / SR
        gap = GAP_PHRASE
        audio.append(np.zeros(int(gap * SR), dtype=np.float32)); t += gap
    beats_out.append({"index": bi, "start": round(b0, 3), "speech_end": round(t - GAP_PHRASE, 3)})
    audio.append(np.zeros(int(GAP_BEAT * SR), dtype=np.float32)); t += GAP_BEAT
audio.append(np.zeros(int(0.8 * SR), dtype=np.float32)); t += 0.8
wav = np.concatenate(audio)
sf.write(f"{OUT}/narration.wav", wav, SR, subtype="PCM_16")


def ts(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def wrap(txt, width=42):
    if len(txt) <= width:
        return txt
    mid = len(txt) // 2
    sp = min((i for i, c in enumerate(txt) if c == " "), key=lambda i: abs(i - mid))
    return txt[:sp] + "\n" + txt[sp + 1:]


with open(f"{OUT}/captions.srt", "w") as f:
    for i, c in enumerate(cues, 1):
        f.write(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{wrap(c['text'])}\n\n")
json.dump({"engine": "kokoro-onnx v1.0 (Apache-2.0), TEMPORARY draft voice", "voice": VOICE, "speed": SPEED,
           "duration": round(len(wav) / SR, 3), "beats": beats_out, "cues": cues},
          open(f"{OUT}/narration.timing.json", "w"), indent=1)
print(json.dumps({"duration": round(len(wav) / SR, 2), "beats": len(beats_out), "cues": len(cues)}))
