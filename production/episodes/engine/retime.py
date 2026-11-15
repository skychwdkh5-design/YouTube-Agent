"""Insert designed pauses into an existing narration (no new TTS): silence is added after
chosen phrases, and every word timing after that point is shifted by the same amount.
The spoken audio itself is untouched (sample-exact copies between the cut points).

    python3 engine/retime.py IN.wav IN.voice.json OUT_DIR "phrase|seconds" ...
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cues import Cues   # noqa: E402

SR = 44100


def read(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).copy()


def retime(wav, js, out_dir, gaps):
    a = read(wav)
    d = json.load(open(js))
    C = Cues(js)
    words = d['words']
    cuts = []                           # (time in the original, seconds of silence)
    for phrase, sec in gaps:
        e = C.end(phrase)
        i = next(k for k, w in enumerate(words) if abs(w['end'] - e) < 1e-6)
        nxt = words[i + 1]['start'] if i + 1 < len(words) else e + 0.05
        cuts.append((e + 0.45 * max(0.0, nxt - e), sec))   # cut in the breath, not on the word tail
    cuts.sort()
    parts, prev = [], 0
    for t, sec in cuts:
        s = int(t * SR)
        parts += [a[prev:s], np.zeros(int(sec * SR), np.int16)]
        prev = s
    parts.append(a[prev:])
    out = np.concatenate(parts)

    def shift(x):
        return x + sum(sec for t, sec in cuts if t <= x)
    for w in words:
        w['start'], w['end'] = round(shift(w['start']), 3), round(shift(w['end']), 3)
    d['duration'] = round(len(out) / SR, 3)
    d['retimed'] = {'source_audio_sha256': d.get('audio_sha256'), 'pauses': [[round(t, 3), s] for t, s in cuts],
                    'note': 'pauses inserted after the generation; spoken audio unchanged'}
    os.makedirs(out_dir, exist_ok=True)
    ow = os.path.join(out_dir, 'narration.wav')
    with wave.open(ow, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(out.tobytes())
    import hashlib
    d['audio_sha256'] = hashlib.sha256(open(ow, 'rb').read()).hexdigest()
    json.dump(d, open(os.path.join(out_dir, 'narration.voice.json'), 'w'), indent=1)
    return ow, d['duration'], cuts


if __name__ == '__main__':
    g = [(x.split('|')[0], float(x.split('|')[1])) for x in sys.argv[4:]]
    print(retime(sys.argv[1], sys.argv[2], sys.argv[3], g)[1:])
