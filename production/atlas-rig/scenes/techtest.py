"""ATLAS rig technical test: calm stance -> two steps -> stop with weight shift ->
pointing gesture -> arm back to rest. Plain background with a floor line.

usage: python3 scenes/techtest.py OUT.mp4 [--debug] [--frames a:b] [--png DIR]
Narration: the existing EP012 voice (read only; never regenerated).
"""
import argparse
import os
import subprocess
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from atlas_rig.character import Atlas, Performance, draw_debug          # noqa: E402
from atlas_rig.mathx import T, S, ap, smoothstep                       # noqa: E402
from atlas_rig.facetrack import lip_tracks, blink                      # noqa: E402

FPS, W, H = 30, 1920, 1080
DUR = 7.6
WAV = os.environ.get('ATLAS_WAV', '/mnt/project-files/bennu/EP012/voice/narration.wav')
WORDS = WAV.replace('narration.wav', 'narration.voice.json')
NAR_OFFSET = 298.89

SCALE = 2.0
FLOOR_Y = 1010


def build():
    return build_with(Atlas())


def build_with(atlas):
    rig = atlas.rig
    screen = T(560, FLOOR_Y) @ S(SCALE) @ T(-rig.J['pelvis'][0], -rig.ground)
    inv = np.linalg.inv(screen)
    bar = (1440, 1700, 360)                      # x0, x1, top (screen px) of the reference bar
    bar_top = ap(inv, ((bar[0] + bar[1]) / 2 - 40, bar[2] + 10))
    perf = Performance(atlas, root0=(0.0, 0.0))
    perf.walk(t0=1.15, distance=92.0, lead='n')
    perf.shift_weight(2.95, 3.9, 3.0)
    perf.shift_weight(6.3, 7.4, -2.0)
    perf.gaze([(0.0, None), (3.28, bar_top), (5.8, None)])
    perf.point('f', t0=3.62, target=bar_top, hold_until=5.35)
    perf.support('n', 4.3, 5.3)
    perf.blinks = [0.72, 2.55, 6.7]
    return atlas, perf, screen, bar


def background(bar):
    y = np.linspace(0, 1, H)[:, None, None]
    top = np.array([22, 26, 36], np.float32)
    bot = np.array([40, 44, 56], np.float32)
    bg = np.broadcast_to(top + (bot - top) * y, (H, W, 3)).copy()
    bg[FLOOR_Y:] = np.array([30, 32, 40], np.float32)
    bg[FLOOR_Y - 2:FLOOR_Y + 2] = np.array([175, 180, 190], np.float32)
    bg[bar[2]:FLOOR_Y - 2, bar[0]:bar[1]] = np.array([232, 190, 60], np.float32)
    out = np.dstack([bg / 255, np.ones((H, W, 1), np.float32)])
    return out.astype(np.float32)


def brow(t):
    return 0.7 * min(smoothstep((t - 4.2) / 0.2), 1 - smoothstep((t - 4.9) / 0.6)) + \
        0.25 * min(smoothstep((t - 1.6) / 0.3), 1 - smoothstep((t - 2.4) / 0.4))


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument('out')
    ap_.add_argument('--debug', action='store_true')
    ap_.add_argument('--frames', default=None)
    ap_.add_argument('--png', default=None)
    a = ap_.parse_args()
    atlas, perf, screen, bar = build()
    bg = background(bar)
    op, wd = lip_tracks(WAV, WORDS, NAR_OFFSET, DUR, FPS)
    blinks = perf.blink_times()
    n = int(DUR * FPS)
    f0, f1 = (0, n) if not a.frames else map(int, a.frames.split(':'))
    ff = None
    if not a.png:
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                               '-r', str(FPS), '-i', '-', '-ss', str(NAR_OFFSET + f0 / FPS), '-t', str((f1 - f0) / FPS),
                               '-i', WAV, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '17',
                               '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', a.out],
                              stdin=subprocess.PIPE)
    for i in range(f0, f1):
        t = i / FPS
        pose = perf.pose(t)
        sol = atlas.solve(pose)
        can = bg.copy()
        face = dict(open_=float(op[i]), width=float(wd[i]), blink=blink(t, blinks), brow=brow(t))
        atlas.draw(can, sol, screen, face)
        img = Image.fromarray((np.clip(can[..., :3], 0, 1) * 255).astype(np.uint8), 'RGB')
        if a.debug:
            draw_debug(img, sol, screen, pose, perf.contacts(t), atlas.rig, t, 'ATLAS rig tech test - debug')
        if a.png:
            os.makedirs(a.png, exist_ok=True)
            img.save(os.path.join(a.png, f'f{i:04d}.png'))
        else:
            ff.stdin.write(img.tobytes())
    if ff:
        ff.stdin.close()
        ff.wait()


if __name__ == '__main__':
    main()
