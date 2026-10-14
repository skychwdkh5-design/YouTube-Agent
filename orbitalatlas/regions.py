"""Seeded region masks for annotation layers (RegionTint): smooth, dark-ish areas connected to seed points (typically open water in a satellite picture).

Why seeded: a global threshold on brightness also picks up shaded mountains. Water is smooth (low local contrast); terrain is textured, so the
candidate set is `low local std AND not too bright`, and only the connected components that CONTAIN a seed are kept; an optional box stops leaks.
The result is an annotation mask, labelled TRACED with its method in the overlay (`validation`): it is not a measurement of area. Pure NumPy + Pillow."""
# effect-reuse-checked: yt-geo/watermask.py is a global brightness threshold (used for outline traces); this adds the texture test and seeding. It reuses its morphology helpers.
import os
import sys
from collections import deque
import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".claude", "skills", "yt-geo"))
import watermask as _wm  # noqa: E402


def local_std(lum, radius=3):
    im = lambda a: Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(radius))
    mu = np.asarray(im(lum), np.float32); mu2 = np.asarray(im(lum * lum / 255.0), np.float32) * 255.0
    return np.sqrt(np.maximum(mu2 - mu * mu, 0))


def seeded_region(rgb, seeds, max_luma=135, max_std=9.0, box=None, close=0, fill_holes=True, max_hole_px=None):
    """rgb: HxWx3 uint8; seeds: [(x, y)] in array pixels; box: (x0, y0, x1, y1) limit; close: closing radius (px) to bridge speckle. Returns a bool mask.
    Seeds that fall outside the candidate set are ignored and listed in `seeded_region.last_missed` (never silently dropped)."""
    a = np.asarray(rgb, np.float32); lum = a.mean(2); cand = (local_std(lum) < max_std) & (lum < max_luma)
    if box is not None:
        b = np.zeros_like(cand); x0, y0, x1, y1 = [int(round(v)) for v in box]; b[max(0, y0):y1, max(0, x0):x1] = True; cand &= b
    cand = _wm._dilate(_wm._erode(cand)); H, W = cand.shape; keep = np.zeros_like(cand); missed = []
    for sx, sy in seeds:
        sx, sy = int(round(sx)), int(round(sy))
        if not (0 <= sx < W and 0 <= sy < H) or not cand[sy, sx]: missed.append((sx, sy)); continue
        if keep[sy, sx]: continue
        q = deque([(sy, sx)]); keep[sy, sx] = True
        while q:
            r, c = q.popleft()
            for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= rr < H and 0 <= cc < W and cand[rr, cc] and not keep[rr, cc]: keep[rr, cc] = True; q.append((rr, cc))
    seeded_region.last_missed = missed
    m = keep
    if close:
        im = Image.fromarray((m * 255).astype(np.uint8)); k = 2 * int(close) + 1
        m = np.asarray(im.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MinFilter(k))) > 127
    if max_hole_px: m = _fill_holes(m, max_hole_px)
    elif fill_holes: m = _fill_holes(m)
    return m


seeded_region.last_missed = []


def _fill_holes(m, max_px=None):
    """fill enclosed holes: background connected to the border stays background. With max_px only holes smaller than that many pixels are filled (islands stay)."""
    H, W = m.shape; bg = ~m; seen = np.zeros_like(m); q = deque()
    for r in range(H):
        for c in (0, W - 1):
            if bg[r, c] and not seen[r, c]: seen[r, c] = True; q.append((r, c))
    for c in range(W):
        for r in (0, H - 1):
            if bg[r, c] and not seen[r, c]: seen[r, c] = True; q.append((r, c))
    while q:
        r, c = q.popleft()
        for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= rr < H and 0 <= cc < W and bg[rr, cc] and not seen[rr, cc]: seen[rr, cc] = True; q.append((rr, cc))
    inner = bg & ~seen
    if max_px:
        lab = np.zeros(m.shape, bool); H, W = m.shape
        for r0 in range(H):
            for c0 in range(W):
                if inner[r0, c0] and not lab[r0, c0]:
                    comp = [(r0, c0)]; lab[r0, c0] = True; k = 0
                    while k < len(comp):
                        r, c = comp[k]; k += 1
                        for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                            if 0 <= rr < H and 0 <= cc < W and inner[rr, cc] and not lab[rr, cc]: lab[rr, cc] = True; comp.append((rr, cc))
                    if len(comp) >= max_px:
                        for r, c in comp: inner[r, c] = False
    return m | inner


def to_mask_image(m, scale):
    """bool array -> 'L' image for RegionTint(mask_scale=1/scale): `scale` is how many source px one array px covers."""
    return Image.fromarray((np.asarray(m) * 255).astype(np.uint8), "L")
