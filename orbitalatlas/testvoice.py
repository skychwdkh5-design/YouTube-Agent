"""Free TEST narration with REAL word timings (not the channel voice).

ffmpeg's `flite` filter (free, local) speaks each word separately; the word's start/end are the measured positions of that word's audio in the concatenated
file, so the timestamps are exact for THIS audio (source='alignment'). The sound is robotic by design: it exists to test synchronisation, captions and
motion without spending TTS credits. The approved channel voice (ElevenLabs Adam) is never replaced by this; final narration is generated separately with the
provider's own timestamps (`timing.Cues.from_words(..., source='provider')`).

words: [{'text': 'In'}, {'text': '4,190.2', 'say': 'four thousand one hundred ninety point two'}, ...]; `pause_after` maps trailing punctuation to a gap in seconds."""
# effect-reuse-checked: yt-voice is the paid ElevenLabs path; there was no free local test voice with measured word timings.
import hashlib
import os
import re
import subprocess
import wave
import numpy as np

PAUSES = {".": 0.42, "!": 0.42, "?": 0.42, ",": 0.22, ";": 0.3, ":": 0.3}
RATE = 22050


def _speak(text, path, voice="slt", tempo=1.0):
    safe = re.sub(r"[^A-Za-z0-9 .'-]", " ", text)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"flite=text='{safe}':voice={voice}", "-af", f"atempo={tempo}", "-ar", str(RATE), "-ac", "1", "-c:a", "pcm_s16le", path], check=True)


def _read(path):
    with wave.open(path, "rb") as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0


def synth(words, out_wav, workdir, voice="slt", gap=0.04, lead=0.25, tail=0.4, cache=True, tempo=1.0):
    """speak every word, join them and return (words with start/end, info). Identical text -> identical per-word files (cached by hash in workdir)."""
    os.makedirs(workdir, exist_ok=True); chunks = [np.zeros(int(lead * RATE), np.float32)]; t = lead; out = []
    for w in words:
        say = w.get("say") or w["text"]; h = hashlib.sha1(f"{voice}|{tempo}|{say}".encode()).hexdigest()[:12]; p = os.path.join(workdir, f"{h}.wav")
        if not (cache and os.path.exists(p)): _speak(say, p, voice, tempo)
        a = _read(p)
        i0 = np.argmax(np.abs(a) > 0.01) if np.any(np.abs(a) > 0.01) else 0; i1 = len(a) - np.argmax(np.abs(a[::-1]) > 0.01) if np.any(np.abs(a) > 0.01) else len(a)
        a = a[i0:i1]; start = t; end = t + len(a) / RATE; out.append(dict(w, start=round(start, 4), end=round(end, 4)))
        p_after = next((v for k, v in PAUSES.items() if w["text"].endswith(k)), 0.0) + gap
        chunks += [a, np.zeros(int(p_after * RATE), np.float32)]; t = end + p_after
    chunks.append(np.zeros(int(tail * RATE), np.float32)); data = np.concatenate(chunks)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes((np.clip(data, -1, 1) * 32767).astype(np.int16).tobytes())
    return out, dict(source="alignment", voice=f"flite:{voice} tempo {tempo} (test voice, not the channel voice)", duration=len(data) / RATE, rate=RATE)


def envelope(wav, fps=30.0):
    """measured loudness per video frame (0..1) of a wav file, for Waveform(samples=...)."""
    a = _read(wav); n = int(len(a) / RATE * fps); hop = RATE / fps
    e = np.array([np.sqrt(np.mean(a[int(i * hop):int((i + 1) * hop) + 1] ** 2) + 1e-12) for i in range(n)])
    return np.clip(e / max(e.max(), 1e-6), 0, 1)
