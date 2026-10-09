"""Procedural test imagery with known geometry. These are NOT maps and carry no geographic meaning; they exist so the
engine can be tested and demonstrated without any episode assets. Every function is deterministic for a given seed and returns
(PIL image, metadata dict) where metadata holds the exact geometry (outlines, masks, anchors) used to build the image."""
import math
import numpy as np
from PIL import Image


def noise(w, h, seed, beta=2.4, down=4):
    """1/f^beta noise, synthesised at 1/down resolution with rfft2 and upsampled (smooth, fast, deterministic)."""
    rng = np.random.default_rng(seed); sw, sh = max(8, w // down), max(8, h // down)
    f = np.fft.rfft2(rng.standard_normal((sh, sw)).astype(np.float32))
    fy = np.fft.fftfreq(sh)[:, None]; fx = np.fft.rfftfreq(sw)[None, :]
    r = np.hypot(fx, fy); r[0, 0] = 1.0
    out = np.fft.irfft2(f / r ** (beta / 2), s=(sh, sw)).astype(np.float32)
    out -= out.mean(); out /= out.std() + 1e-9
    if (sw, sh) != (w, h): out = np.asarray(Image.fromarray(out).resize((w, h), Image.BICUBIC), np.float32)
    return out


def _blob(cx, cy, R, seed, n=64, rough=0.18):
    rng = np.random.default_rng(seed)
    ang = np.linspace(0, 2 * math.pi, n, endpoint=False)
    r = np.ones(n)
    for k in range(2, 7):
        r += rough / k * rng.uniform(0.4, 1.0) * np.cos(k * ang + rng.uniform(0, 2 * math.pi))
    return np.stack([cx + R * r * np.cos(ang), cy + R * r * np.sin(ang)], 1)


def _poly_mask(poly, size):
    from PIL import ImageDraw
    m = Image.new("L", size, 0); ImageDraw.Draw(m).polygon([tuple(p) for p in poly], fill=255)
    return np.asarray(m) > 127


def islands(size=(4000, 2250), seed=3, n_islands=4):
    """sea with several irregular islands. meta: outlines (list of (n,2) closed polylines, exact), centers, mask (bool, source px)."""
    w, h = size; rng = np.random.default_rng(seed)
    centers = [(w * rng.uniform(0.2, 0.8), h * rng.uniform(0.25, 0.75)) for _ in range(n_islands)]
    radii = [h * rng.uniform(0.09, 0.2) for _ in range(n_islands)]
    outlines = [np.vstack([p, p[:1]]) for p in (_blob(c[0], c[1], r, seed * 10 + i) for i, (c, r) in enumerate(zip(centers, radii)))]
    mask = np.zeros((h, w), bool)
    for o in outlines: mask |= _poly_mask(o, size)
    nz = noise(w, h, seed); nz2 = noise(w, h, seed + 99, 1.2)
    # distance to land (cheap): blur of the mask
    m_img = Image.fromarray((mask * 255).astype(np.uint8)).resize((w // 8, h // 8), Image.BILINEAR)
    from PIL import ImageFilter
    near = np.asarray(m_img.filter(ImageFilter.GaussianBlur(14)).resize((w, h), Image.BICUBIC), np.float32) / 255.0
    deep = np.array([8, 40, 70], np.float32); shallow = np.array([40, 140, 150], np.float32)
    sea = deep + (shallow - deep) * np.clip(near * 3.2, 0, 1)[:, :, None] + nz[:, :, None] * 5
    land_t = np.clip(0.5 + 0.25 * nz2, 0, 1)[:, :, None]
    land = np.array([205, 185, 130], np.float32) * (1 - land_t) + np.array([80, 120, 60], np.float32) * land_t
    img = np.where(mask[:, :, None], land + nz[:, :, None] * 6, sea)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), dict(outlines=outlines, centers=[np.array(c) for c in centers], radii=radii, mask=mask)


def city(size=(4000, 2250), seed=7):
    """street grid with a curved river and a few landmark squares. meta: river polyline (exact), landmarks {name: (x, y)}."""
    w, h = size; rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.float32); img[:] = (24, 28, 38)
    step = 70
    xs = np.arange(0, w, step); ys = np.arange(0, h, step)
    blocks = np.zeros((h, w), np.float32)
    for x in xs:
        for y in ys:
            if rng.random() < 0.82: blocks[y + 6:y + step - 6, x + 6:x + step - 6] = rng.uniform(0.35, 1.0)
    nz = noise(w, h, seed, 1.6)
    img += (blocks[:, :, None] * np.array([150, 130, 100], np.float32) * 0.5) + nz[:, :, None] * 3
    t = np.linspace(0, 1, 200)
    river = np.stack([w * (0.05 + 0.9 * t), h * (0.5 + 0.18 * np.sin(t * 7) + 0.05 * np.sin(t * 17))], 1)
    from PIL import ImageDraw
    rm = Image.new("L", (w, h), 0); ImageDraw.Draw(rm).line([tuple(p) for p in river], fill=255, width=int(h * 0.04), joint="curve")
    rmask = np.asarray(rm, np.float32) / 255.0
    img = img * (1 - rmask[:, :, None]) + np.array([20, 70, 110], np.float32) * rmask[:, :, None]
    lm = {"north_square": (w * 0.3, h * 0.2), "east_square": (w * 0.72, h * 0.3), "south_square": (w * 0.55, h * 0.82)}
    for p in lm.values():
        x, y = int(p[0]), int(p[1]); img[y - 40:y + 40, x - 40:x + 40] = (240, 220, 140)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), dict(river=river, landmarks={k: np.array(v) for k, v in lm.items()}, mask=rmask > 0.5)
