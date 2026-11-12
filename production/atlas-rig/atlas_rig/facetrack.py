"""Face controls from the EXISTING narration (no new audio): jaw/mouth opening from the
loudness envelope gated by provider word timings, closures on m/b/p, irregular blinks."""
import json
import subprocess

import numpy as np


def lip_tracks(wav, words_json, offset, dur, fps=30):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(offset), '-t', str(dur + 0.3), '-i', wav,
                          '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.int16).astype(float)
    hop = 16000 // fps
    n = int(dur * fps) + 3
    rms = np.array([np.sqrt((a[i * hop:(i + 1) * hop] ** 2).mean() + 1e-9) if (i + 1) * hop <= len(a) else 0.0
                    for i in range(n)])
    rms = rms / max(1e-6, np.percentile(rms, 92))
    words = [w for w in json.load(open(words_json))['words']
             if w['end'] > offset - 1 and w['start'] < offset + dur + 1]
    tgt = np.clip((rms - 0.08) / 0.85, 0, 1) ** 0.8
    wid = np.ones(n)
    for i in range(n):
        tn = i / fps + offset + 1 / fps
        w = next((w for w in words if w['start'] - 0.03 <= tn <= w['end']), None)
        if w is None:
            tgt[i] = 0
            continue
        txt = w['text'].lower()
        if txt[:1] in ('m', 'b', 'p') and tn - w['start'] < 0.07:
            tgt[i] = 0
        if any(v in txt for v in ('oo', 'ou', 'ow', 'wo', 'o')) and not txt.startswith('the'):
            wid[i] = 0.82
        elif any(v in txt for v in ('ee', 'ea', 'i')):
            wid[i] = 1.05
    op = np.zeros(n)
    wd = np.ones(n)
    for i in range(1, n):
        k = 0.7 if tgt[i] > op[i - 1] else 0.45
        op[i] = op[i - 1] + (tgt[i] - op[i - 1]) * k
        wd[i] = wd[i - 1] + (wid[i] - wd[i - 1]) * 0.5
    return op, wd


def blink(t, times):
    b = 0.0
    for t0 in times:
        u = t - t0
        if 0 <= u < 0.07:
            b = max(b, u / 0.07)
        elif 0.07 <= u < 0.10:
            b = 1.0
        elif 0.10 <= u < 0.22:
            b = max(b, 1 - (u - 0.10) / 0.12)
    return b
