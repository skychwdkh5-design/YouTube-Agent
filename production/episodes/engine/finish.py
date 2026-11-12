"""Finish an episode: SFX bed + narration mix (-14 LUFS), burned English subtitles from the
yt-captions SRT (separate libass layer, readable box, frame 0 left clean = cover), final MP4.

usage: python3 finish.py EPISODE.py RAW_VIDEO.mp4 CAPTIONS.srt OUT.mp4 [--sub-margin-l PX --sub-margin-r PX]

SFX are synthetic and temporary (soft transition whoosh at scene cuts, quiet low bed). They are
never meant as recordings of a radio signal, launch or impact; the narrator stays on top."""
import argparse
import os
import re
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from render import load_episode  # noqa: E402

SR = 48000
FPS = 30


def read_wav(path):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, np.float32).copy()


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def whoosh(rng, dur=0.6):
    n = int(dur * SR)
    noise = rng.standard_normal(n).astype(np.float32)
    # one-pole low-pass sweeping down: soft air, no click
    out, y = np.empty(n, np.float32), 0.0
    for i in range(n):
        a = 0.02 + 0.18 * (1 - i / n) ** 2
        y += a * (noise[i] - y)
        out[i] = y
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return out * env / (np.abs(out).max() + 1e-9)


def bed(n, seed):
    t = np.arange(n) / SR
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t + seed)
    x = (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 82.4 * t + 1) + 0.25 * np.sin(2 * np.pi * 110 * t + 2)) * trem
    fade = np.minimum(1, np.minimum(t / 2.0, (t[-1] - t) / 2.5))
    return (x / 1.75 * fade).astype(np.float32)


def mix(ep, out_wav):
    voice = read_wav(ep.VOICE_WAV)
    n = int(ep.DUR * SR) + SR
    v = np.zeros(n, np.float32)
    off = int(getattr(ep, 'OFFSET', 0.0) * SR)
    v[off:off + len(voice)] = voice[:max(0, n - off)]
    rng = np.random.default_rng(13)
    sfx = np.zeros(n, np.float32)
    for name, t in sorted(ep.S.items(), key=lambda kv: kv[1]):
        if t <= 0.05:
            continue
        w = whoosh(rng)
        a = max(0, int((t - 0.35) * SR))
        b = min(n, a + len(w))
        sfx[a:b] += w[:b - a]
    peak_v = np.abs(voice).max() + 1e-9
    out = v + sfx * peak_v * 10 ** (-24 / 20) + bed(n, 1.0) * peak_v * 10 ** (-34 / 20)
    write_wav(out_wav, out[:int(ep.DUR * SR)])


def integrated_lufs(path):
    err = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[0-9.]+) LUFS', err)[-1])


def ts(s):
    h, m, sec = s.replace(',', '.').split(':')
    return int(h) * 3600 + int(m) * 60 + float(sec)


def ass_time(t):
    cs = int(round(t * 100))
    return f'{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}'


def srt_to_ass(srt, ass, ml, mr, mv):
    blocks = [b for b in re.split(r'\n\s*\n', open(srt, encoding='utf-8').read().strip()) if b.strip()]
    first_ok = 1.0 / FPS + 0.01            # frame 0 must stay identical to the cover
    lines = []
    for b in blocks:
        rows = b.strip().split('\n')
        a, z = [ts(x.strip()) for x in rows[1].split('-->')]
        a = max(a, first_ok)
        if z <= a:
            continue
        text = r'\N'.join(r.strip() for r in rows[2:]).replace('{', '(').replace('}', ')')
        lines.append(f'Dialogue: 0,{ass_time(a)},{ass_time(z)},Sub,,0,0,0,,{text}')
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter SemiBold,46,&H00FFFFFF,&H00FFFFFF,&H50000000,&H50000000,0,0,0,0,100,100,0,0,3,10,0,2,{ml},{mr},{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    open(ass, 'w', encoding='utf-8').write(head + '\n'.join(lines) + '\n')
    return len(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('episode')
    p.add_argument('video')
    p.add_argument('srt')
    p.add_argument('out')
    p.add_argument('--sub-margin-l', type=int, default=640)
    p.add_argument('--sub-margin-r', type=int, default=400)
    p.add_argument('--sub-margin-v', type=int, default=96)
    a = p.parse_args()
    ep = load_episode(a.episode)
    work = a.out + '_finish'
    os.makedirs(work, exist_ok=True)
    wav, ass = os.path.join(work, 'mix.wav'), os.path.join(work, 'subs.ass')
    mix(ep, wav)
    n = srt_to_ass(a.srt, ass, a.sub_margin_l, a.sub_margin_r, a.sub_margin_v)
    gain = -13.3 - integrated_lufs(wav)   # limiter costs ~0.7 LU; lands near -14
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a.video, '-i', wav,
                    '-filter_complex', f"[0:v]ass={ass}[v];[1:a]volume={gain:.2f}dB,alimiter=limit=0.82:level=false,aresample={SR}[a]",
                    '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
                    '-pix_fmt', 'yuv420p', '-r', str(FPS), '-c:a', 'aac', '-b:a', '192k', '-ar', str(SR),
                    '-t', f'{ep.DUR:.3f}', '-movflags', '+faststart', a.out], check=True)
    print(f'{n} subtitle cues, mix {wav} -> {a.out}')


if __name__ == '__main__':
    main()
