#!/usr/bin/env python3
"""Cut the owner's ATLAS parts sheet (2026-11-17) into transparent PNG parts + pivot data.

Every kept pixel is copied 1:1 from the sheet (no redraw, no regeneration). The only edit is removing
the round construction tabs ("pegs") that would otherwise show over a neighbouring part; the tabs that
tuck under a parent are kept. Writes assets/parts_v1/<name>.png and parts.json (boxes, pegs, sha256).

    python3 -I tools/cut_parts.py
"""
from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "parts_v1"
SHEET = OUT / "source" / "atlas_parts_sheet.png"
SHEET_SHA = "833941514b8559b04db6b8529d99c63c3c0120e049080110d9249e53df967e48"

# name: (sheet box x0, y0, x1, y1). A = the limb on the viewer's left, B = viewer's right.
PARTS = {
    "reference": (15, 14, 338, 622),
    "head": (384, 44, 717, 395),
    "torso": (740, 102, 991, 382),
    "scarf": (999, 163, 1252, 323),
    "uarm_A": (1272, 67, 1386, 276), "uarm_B": (1423, 67, 1530, 276),
    "farm_A": (1540, 114, 1627, 321), "farm_B": (1661, 114, 1751, 320),
    "thigh_A": (1279, 348, 1386, 567), "thigh_B": (1398, 350, 1500, 564),
    "shin_A": (1530, 371, 1616, 581), "shin_B": (1649, 373, 1735, 581),
    "fist_A": (394, 434, 501, 589), "fist_B": (542, 436, 649, 590),
    "point_back": (681, 437, 807, 579), "point_B": (827, 438, 955, 581),
    "open_A": (983, 437, 1107, 594), "open_B": (1130, 436, 1252, 591),
    "boot_A": (1409, 619, 1550, 791), "boot_B": (1603, 618, 1756, 786),
    "face_closed": (20, 653, 220, 857),
}
# tabs to remove: (part, which peg) - they would show on top of the child part
REMOVE = {("farm_A", "top"), ("farm_B", "top"),            # forearm sits ON the sleeve cuff, over the elbow tab
          ("fist_A", "top"), ("fist_B", "top"), ("point_back", "top"), ("point_B", "top"),
          ("open_A", "top"), ("open_B", "top"),                 # glove sits over the wrist tab
          ("thigh_A", "bottom"), ("thigh_B", "bottom"), ("shin_A", "bottom"), ("shin_B", "bottom"),
          ("torso", "left"), ("torso", "right")}


def components(m, conn8=True):
    h, w = m.shape
    lab = np.zeros((h, w), np.int32)
    out = []
    nb = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx] if conn8 else [(1, 0), (-1, 0), (0, 1), (0, -1)]
    c = 0
    for sy, sx in zip(*np.nonzero(m)):
        if lab[sy, sx]:
            continue
        c += 1
        q = deque([(sy, sx)]); lab[sy, sx] = c; pts = []
        while q:
            y, x = q.popleft(); pts.append((y, x))
            for dy, dx in nb:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not lab[ny, nx]:
                    lab[ny, nx] = c; q.append((ny, nx))
        out.append((c, np.array(pts)))
    return lab, out


def peg_mask(a):
    r, g, b, al = (a[..., i].astype(int) for i in range(4))
    return (al > 200) & (r > 200) & (r - b > 45) & (g > 150)


def find_pegs(a):
    _, cs = components(peg_mask(a), conn8=False)
    pegs = []
    for _, p in cs:
        if len(p) < 150:
            continue
        x0, x1, y0, y1 = p[:, 1].min(), p[:, 1].max(), p[:, 0].min(), p[:, 0].max()
        r = (x1 - x0 + 1) / 2
        pegs.append({"x0": int(x0), "x1": int(x1), "y0": int(y0), "y1": int(y1), "r": float(r), "n": int(len(p))})
    return pegs


def label_pegs(name, pegs, h):
    """Name each peg top/bottom (limbs, gloves, boots) or left/right (torso) and give a circle centre."""
    out = {}
    for p in pegs:
        cx = (p["x0"] + p["x1"]) / 2
        if name == "torso":
            out["left" if cx < 125 else "right"] = {"c": [cx, (p["y0"] + p["y1"]) / 2], "r": p["r"]}
        elif (p["y0"] + p["y1"]) / 2 < h / 2:
            out["top"] = {"c": [cx, p["y0"] + p["r"]], "r": p["r"]}      # clipped at the bottom by the body
        else:
            out["bottom"] = {"c": [cx, p["y1"] - p["r"]], "r": p["r"]}   # clipped at the top by the cuff/body
    return out


def remove_tab(a, peg, outline=7):
    """Erase a peg: its fill (flood of non-ink pixels from the peg centre) and the ink ring that belongs
    only to it. Ink shared with the body (the junction line) is kept, so the body outline stays closed."""
    h, w = a.shape[:2]
    r, g, b, al = (a[..., i].astype(int) for i in range(4))
    ink = (r + g + b) < 330
    solid = al > 128
    cx, cy = (int(round(v)) for v in peg["c"])
    seen = np.zeros((h, w), bool)
    q = deque([(cy, cx)]); seen[cy, cx] = True
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and solid[ny, nx] and not ink[ny, nx]:
                seen[ny, nx] = True; q.append((ny, nx))
    fill = seen
    other = solid & ~ink & ~fill                                    # body / cuff fills
    def dil(m, k):
        return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(k))) > 0
    near_peg = dil(fill, 2 * outline + 3)
    near_body = dil(other, 2 * outline + 1)
    kill = fill | (near_peg & ~near_body & ~other)
    a = a.copy()
    a[..., 3] = np.where(kill, 0, a[..., 3])
    lab, cs = components(a[..., 3] > 8)
    big = max(cs, key=lambda c: len(c[1]))[0]
    a[..., 3] = np.where(lab == big, a[..., 3], 0)
    return a, int(kill.sum())


def main():
    raw = SHEET.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHEET_SHA:
        raise SystemExit("parts sheet checksum mismatch")
    sheet = np.array(Image.open(SHEET).convert("RGBA"))
    meta = {"source": "source/atlas_parts_sheet.png", "source_sha256": SHEET_SHA, "parts": {}}
    for name, (x0, y0, x1, y1) in PARTS.items():
        a = sheet[y0:y1, x0:x1].copy()
        lab, cs = components(a[..., 3] > 8)
        big = max(cs, key=lambda c: len(c[1]))[0]
        a[..., 3] = np.where(lab == big, a[..., 3], 0)
        pegs = label_pegs(name, find_pegs(a), a.shape[0]) if name not in ("reference", "head", "scarf", "face_closed") else {}
        removed = {}
        for side in list(pegs):
            if (name, side) in REMOVE:
                a, n = remove_tab(a, pegs[side])
                removed[side] = n
        Image.fromarray(a, "RGBA").save(OUT / f"{name}.png")
        sha = hashlib.sha256((OUT / f"{name}.png").read_bytes()).hexdigest()
        meta["parts"][name] = {"sheet_box": [x0, y0, x1, y1], "size": [x1 - x0, y1 - y0], "pegs": pegs,
                               "tabs_removed_px": removed, "sha256": sha}
        print(name, a.shape[1], a.shape[0], {k: [round(v, 1) for v in p["c"]] for k, p in pegs.items()}, removed or "")
    (OUT / "parts.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
