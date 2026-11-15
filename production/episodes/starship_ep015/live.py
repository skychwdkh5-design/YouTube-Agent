"""EP015 v2: live-footage plates.

Each SEG is a piece of real, rights-cleared footage (see docs/RIGHTS_AND_FACTS_LEDGER.md) cut to a
narration beat. `build_plates()` decodes the source range once with ffmpeg (static crop, Lanczos
scale to a 1.25x oversized plate, 30 fps) into a JPEG sequence; `plate(seg, t)` returns the frame
for episode time t with a slow, eased push-in, so the shot keeps moving without re-sampling twice.
"""
import math
import os
import subprocess
from functools import lru_cache

import numpy as np
from PIL import Image, ImageFilter

FPS, W, H = 30, 1920, 1080
OVER = 1.25                                   # plates are 2400x1350: room for the push-in
PW, PH = int(W * OVER), int(H * OVER)
SRC = '/mnt/project-files/starship/EP015/live/src'
PLATES = '/mnt/project-files/starship/EP015/live/plates'


class Seg:
    def __init__(self, name, t0, t1, src, s0, crop=None, push=(1.0, 1.12), focus=(0.5, 0.5),
                 label='', credit='', mode='full', grade=1.0, speed=1.0):
        self.name, self.t0, self.t1, self.src, self.s0 = name, t0, t1, src, s0
        self.crop, self.push, self.focus = crop, push, focus
        self.label, self.credit, self.mode, self.grade, self.speed = label, credit, mode, grade, speed

    @property
    def n(self):
        return int(math.ceil((self.t1 - self.t0) * FPS)) + 2

    def dir(self):
        return os.path.join(PLATES, self.name)


def build_plates(segs, force=False):
    for s in segs:
        d = s.dir()
        if not force and os.path.isdir(d) and len(os.listdir(d)) >= s.n:
            continue
        os.makedirs(d, exist_ok=True)
        dur = (s.t1 - s.t0) * s.speed + 0.2
        vf = []
        if s.crop:
            x, y, w, h = s.crop
            vf.append(f'crop={w}:{h}:{x}:{y}')
        if s.mode == 'portrait':
            vf.append('scale=-2:%d:flags=lanczos' % PH)
        else:
            vf.append(f'scale={PW}:{PH}:flags=lanczos')
        if s.speed != 1.0:
            vf.append(f'setpts=PTS/{s.speed}')
        vf.append(f'fps={FPS}')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(s.s0), '-t', str(dur), '-i', os.path.join(SRC, s.src),
                        '-vf', ','.join(vf), '-q:v', '2', '-frames:v', str(s.n), os.path.join(d, '%05d.jpg')], check=True)


@lru_cache(maxsize=48)
def _frame(d, i):
    fs = sorted(os.listdir(d))
    i = max(0, min(i, len(fs) - 1))
    return np.asarray(Image.open(os.path.join(d, fs[i])).convert('RGB'), np.float32)


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def plate(s, t):
    """float RGB 1080x1920 for episode time t inside segment s"""
    i = int(round((t - s.t0) * FPS))
    im = _frame(s.dir(), i)
    u = ease((t - s.t0) / max(0.1, s.t1 - s.t0))
    z = s.push[0] + (s.push[1] - s.push[0]) * u          # 1.0 = whole oversized plate
    if s.mode == 'portrait':
        return _portrait(im, z)
    h, w = im.shape[:2]
    cw, ch = w / z, h / z
    fx, fy = s.focus
    x0 = (w - cw) * fx
    y0 = (h - ch) * fy
    img = Image.fromarray(im.astype(np.uint8)).resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    a = np.asarray(img, np.float32)
    return _grade(a, s.grade)


def _portrait(im, z):
    """vertical phone footage: blurred, darkened fill + the real frame centred with a soft frame"""
    h, w = im.shape[:2]
    base = Image.fromarray(im.astype(np.uint8))
    bg = base.resize((W, int(W * h / w)), Image.BILINEAR)
    top = (bg.height - H) // 2
    bg = bg.crop((0, top, W, top + H)).filter(ImageFilter.GaussianBlur(28))
    out = np.asarray(bg, np.float32) * 0.42
    fh = int(H * 0.94 * z / 1.0)
    fh = min(fh, int(H * 1.0))
    fw = int(fh * w / h)
    fr = np.asarray(base.resize((fw, fh), Image.LANCZOS), np.float32)
    x0, y0 = (W - fw) // 2 + 180, (H - fh) // 2
    out[y0:y0 + fh, x0:x0 + fw] = fr
    # thin frame
    out[y0:y0 + 3, x0:x0 + fw] = 235
    out[y0 + fh - 3:y0 + fh, x0:x0 + fw] = 235
    out[y0:y0 + fh, x0:x0 + 3] = 235
    out[y0:y0 + fh, x0 + fw - 3:x0 + fw] = 235
    return _grade(out, 1.0)


def _grade(a, k):
    """light, consistent grade: a touch more contrast and warmth (k = strength)"""
    if k <= 0:
        return a
    lum = a.mean(axis=2, keepdims=True)
    a = lum + (a - lum) * (1 + 0.12 * k)
    a = 118 + (a - 118) * (1 + 0.10 * k)
    a[..., 0] *= 1 + 0.025 * k
    a[..., 2] *= 1 - 0.03 * k
    return np.clip(a, 0, 255)
