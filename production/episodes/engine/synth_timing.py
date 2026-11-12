"""TEMP word timings estimated from the script text (Adam's measured pace on EP012,
~14.45 chars/s incl. pauses) plus a silent WAV of the same length. Used ONLY to lay out
and preview scenes before the real narration exists. Never ship a render made on it.

usage: python3 synth_timing.py SCRIPT.txt OUT_DIR
writes OUT_DIR/narration.voice.json (schema yt-voice/1, provider 'TEMP-estimate') and
OUT_DIR/narration.wav (silence)."""
import json
import os
import re
import subprocess
import sys

CPS = 15.6          # speech chars/s without pauses (fits 14.45 overall with the pauses below)
PAUSE = {',': 0.22, ';': 0.3, ':': 0.3, '.': 0.42, '?': 0.45, '!': 0.42}
PARA = 0.75


def build(text):
    words, t = [], 0.25
    for pi, para in enumerate([p for p in text.split('\n') if p.strip()]):
        for tok in para.split():
            d = (len(tok) + 1) / CPS
            words.append({'text': tok, 'start': round(t, 3), 'end': round(t + d * 0.92, 3)})
            t += d
            if tok[-1] in PAUSE:
                t += PAUSE[tok[-1]]
        t += PARA
    return words, t + 0.4


if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    text = open(src).read().strip()
    words, dur = build(text)
    json.dump({'schema': 'yt-voice/1', 'provider': 'TEMP-estimate', 'voice_name': 'NONE (silent layout track)',
               'audio': 'narration.wav', 'duration': round(dur, 3), 'text': text, 'words': words,
               'warnings': ['TEMP timing estimate - not a voice recording']}, open(os.path.join(out, 'narration.voice.json'), 'w'), indent=1)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', str(dur),
                    os.path.join(out, 'narration.wav')], check=True)
    print(f'{len(words)} words, {dur:.1f}s')
