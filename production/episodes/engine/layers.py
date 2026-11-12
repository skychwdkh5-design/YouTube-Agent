"""Layered cover compositions (1920x1080). The approved cover is split into RGBA layers
(plate, text, graphics); each layer can move independently (parallax, slides, fades,
partial reveal masks), so the opening is animated by layers, not a zoom of a flat picture.
At the cover's own parameters the layers recombine into the cover exactly."""
import os
from functools import lru_cache

import numpy as np
from PIL import Image

W, H = 1920, 1080


@lru_cache(maxsize=32)
def load(path):
    im = Image.open(path)
    return im.convert('RGBA') if im.mode != 'RGBA' else im


def _affine(im, dx=0.0, dy=0.0, s=1.0, cx=W / 2, cy=H / 2):
    if abs(dx) < 1e-3 and abs(dy) < 1e-3 and abs(s - 1) < 1e-5:
        return im
    # output (x, y) samples input at ((x - cx - dx) / s + cx, ...)
    a = 1 / s
    c = cx - (cx + dx) * a
    f = cy - (cy + dy) * a
    return im.transform((W, H), Image.AFFINE, (a, 0, c, 0, a, f), resample=Image.BICUBIC)


class Stack:
    """Composite named layers from a folder with per-layer transforms.
    cam: (dx, dy, s, cx, cy) applied to every layer after its own transform."""

    def __init__(self, folder):
        self.folder = folder

    def path(self, name):
        return os.path.join(self.folder, name + '.png')

    def render(self, spec, cam=(0.0, 0.0, 1.0, W / 2, H / 2)):
        """spec: list of (name, dict(dx, dy, s, cx, cy, alpha, mask)) bottom -> top.
        mask: optional HxW float array multiplied into the layer alpha (screen space,
        before the camera)."""
        out = None
        for name, o in spec:
            a = o.get('alpha', 1.0)
            if a <= 0.002:
                continue
            im = load(self.path(name))
            im = _affine(im, o.get('dx', 0.0), o.get('dy', 0.0), o.get('s', 1.0), o.get('cx', W / 2), o.get('cy', H / 2))
            m = o.get('mask')
            if a < 0.999 or m is not None:
                arr = np.asarray(im).astype(np.float32)
                al = arr[..., 3] * a
                if m is not None:
                    al = al * m
                im = Image.fromarray(np.dstack([arr[..., :3], al]).astype(np.uint8), 'RGBA')
            if out is None:
                out = Image.new('RGBA', (W, H), (0, 0, 0, 255))
                out.alpha_composite(im if im.mode == 'RGBA' else im.convert('RGBA'))
            else:
                out.alpha_composite(im)
        dx, dy, s, cx, cy = cam
        out = _affine(out, dx, dy, s, cx, cy)
        return out.convert('RGB')


def ramp_x(x0, x1, soft=60.0, invert=False):
    """Horizontal reveal mask: 1 left of x0..x1 edge (soft), 0 right of it."""
    xs = np.arange(W, dtype=np.float32)
    m = np.clip((x1 - xs) / max(soft, 1e-3), 0, 1)
    if invert:
        m = 1 - m
    return np.broadcast_to(m[None, :], (H, W))
