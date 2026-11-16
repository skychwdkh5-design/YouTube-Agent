#!/usr/bin/env python3
"""Cut clean poses / turnaround views / emotion heads out of the approved concept sheet.

Non-generative: every visible pixel of an output is an original pixel of
assets/APPROVED_CONCEPT_UNMODIFIED.png. Method per cell:
  1. flood-fill the paper background from the cell border (stops at ink lines);
  2. keep the largest connected figure (drops sparkles, "!!", "?", motion lines, labels);
  3. add a ring of the sheet's own paper around it (paper-cut sticker edge, like the hero);
  4. soft 1-px alpha edge.
Writes PNGs + a manifest with the source box of every cutout, so provenance can be re-checked.

  python3 -I tools/extract_sheet.py --out assets/sheet_cutouts
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "APPROVED_CONCEPT_UNMODIFIED.png"

# name: (x0, y0, x1, y1) in sheet pixels, generous boxes; label text below each figure is excluded
CELLS = {
    "pose_point":      (370, 495, 570, 735),
    "pose_explain":    (565, 495, 760, 725),
    "pose_starmap":    (750, 495, 950, 725),
    "pose_observe":    (372, 785, 590, 1010),
    "pose_surprised":  (585, 770, 772, 1010),
    "pose_proud":      (780, 765, 985, 1012),
    "turn_front":      (968, 535, 1100, 735),
    "turn_34":         (1088, 535, 1214, 735),
    "turn_side":       (1208, 535, 1318, 735),
    "turn_back":       (1308, 535, 1445, 735),
    "face_happy":      (938, 65, 1102, 232),
    "face_curious":    (1104, 65, 1266, 232),
    "face_amazed":     (1268, 65, 1432, 232),
    "face_thinking":   (938, 258, 1102, 426),
    "face_excited":    (1104, 258, 1266, 426),
    "face_content":    (1268, 258, 1432, 426),
}
# effect marks drawn on the sheet next to figures: keep ALL non-paper pixels in the box
FX_CELLS = {
    "fx_exclaim":      (655, 764, 714, 809),   # "!!" above the surprised pose
}
BORDER_PX = 4


def background_mask(rgb: np.ndarray) -> np.ndarray:
    """Pixels that look like the cream paper: light, low saturation."""
    r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    return (mn > 200) & (mx - mn < 40) & (r >= b)


def flood_from_border(bgish: np.ndarray) -> np.ndarray:
    h, w = bgish.shape
    seen = np.zeros_like(bgish)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if bgish[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if bgish[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and bgish[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; q.append((ny, nx))
    return seen


def largest_component(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32)
    best, best_n, cur = 0, 0, 0
    for sy in range(h):
        for sx in range(w):
            if mask[sy, sx] and not lab[sy, sx]:
                cur += 1; n = 0
                q = deque([(sy, sx)]); lab[sy, sx] = cur
                while q:
                    y, x = q.popleft(); n += 1
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                                lab[ny, nx] = cur; q.append((ny, nx))
                if n > best_n:
                    best, best_n = cur, n
    return lab == best


def cut(sheet: np.ndarray, box, keep_all=False) -> tuple[Image.Image, dict]:
    x0, y0, x1, y1 = box
    rgb = sheet[y0:y1, x0:x1]
    bg = background_mask(rgb)
    outside = flood_from_border(bg)
    fig = ~outside if keep_all else largest_component(~outside)
    ring_src = Image.fromarray((fig * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * BORDER_PX + 1))
    ring = (np.asarray(ring_src) > 0) & ~fig
    ring &= bg            # the sticker edge may only take plain paper pixels, never marks or text
    alpha = (fig | ring).astype(np.uint8) * 255
    a = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.6))
    a = np.minimum(np.asarray(a), alpha)          # soften outward only; never adds pixels
    a = np.where(fig, 255, a).astype(np.uint8)    # figure pixels stay fully opaque
    ys, xs = np.nonzero(a)
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    out = np.dstack([rgb, a])[by0:by1, bx0:bx1]
    info = {"source_box": [int(x0 + bx0), int(y0 + by0), int(x0 + bx1), int(y0 + by1)],
            "size": [int(bx1 - bx0), int(by1 - by0)],
            "touches_cell_edge": bool(fig[0].any() or fig[-1].any() or fig[:, 0].any() or fig[:, -1].any())}
    return Image.fromarray(out, "RGBA"), info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    sheet = np.asarray(Image.open(SRC).convert("RGB"))
    manifest = {"source": SRC.name, "source_sha256": hashlib.sha256(SRC.read_bytes()).hexdigest(),
                "method": "flood-fill background + largest component + paper ring; pixels copied 1:1", "items": {}}
    for name, box in list(CELLS.items()) + list(FX_CELLS.items()):
        im, info = cut(sheet, box, keep_all=name in FX_CELLS)
        p = a.out / f"{name}.png"
        im.save(p)
        info["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        manifest["items"][name] = info
        print(name, info["size"], "EDGE!" if info["touches_cell_edge"] else "")
    (a.out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    sys.exit(main())
