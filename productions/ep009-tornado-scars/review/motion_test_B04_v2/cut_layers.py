#!/usr/bin/env python3
"""Cut the owner-approved EP009 paintings into animation layers for the B04 v2 test.

No new artwork is generated. Every layer is pixels from the verified PNGs in handoff/assets
(checked against handoff/assets.json SHA-256 before use):

  P03_tree_intact.png   -> wood (trunk + branches + grass base), 8 foliage clumps, canopy fill,
                           painted leaf sprites
  P03_tree_uprooted.png -> root plate (soil + roots) re-oriented to the intact tree's frame,
                           soil patch for the pit
  P04_land_intact.png   -> grass ground texture, bush cluster, small background tree
  P02_storm.png         -> distant storm (sky element)

Where pixels are hidden in the original (wood behind leaves), the gap is filled with a
"canopy fill" derived from the painting's own foliage colours (blurred, darkened) - an inner
shadow, not invented detail. Output: layers/*.png + layers/rig.json + layers_preview.jpg.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
SRC = EP / "handoff" / "assets"
OUT = HERE / "layers"
TREE_SCALE = 0.55            # 1254 px painting -> 690 px working canvas (never upscaled later)
FOLIAGE_HUE = (43, 170)      # degrees; measured split between bark (orange-brown) and leaves
BASE_ROW = 0.80              # below this the grass mound belongs to the base, not to the crown
N_CLUMPS = 8


def load(name):
    expected = {a["name"]: a["sha256"] for a in json.loads((EP / "handoff" / "assets.json").read_text())["generated_assets"]}
    p = SRC / name
    if not p.exists():
        sys.exit(f"{p} missing: run productions/ep009-tornado-scars/tools/verify_illustrated_assets.py first")
    if hashlib.sha256(p.read_bytes()).hexdigest() != expected[name]:
        sys.exit(f"{name}: SHA256 mismatch")
    return Image.open(p).convert("RGBA")


def hue_deg(im):
    return np.asarray(im.convert("RGB").convert("HSV"), dtype=np.float32)[..., 0] * 360 / 255


def with_alpha(im, mask):
    arr = np.asarray(im).copy()
    arr[..., 3] = (arr[..., 3].astype(np.float32) * np.clip(mask, 0, 1)).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def clean(mask, size=5):
    m = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(size))
    return np.asarray(m) > 127


def kmeans(pts, k, iters=25, seed=3):
    rng = np.random.default_rng(seed)
    c = pts[rng.choice(len(pts), k, replace=False)].astype(np.float64)
    for _ in range(iters):
        d = ((pts[:, None, :] - c[None]) ** 2).sum(-1)
        lab = d.argmin(1)
        for i in range(k):
            sel = pts[lab == i]
            if len(sel):
                c[i] = sel.mean(0)
    return lab, c


def main():
    OUT.mkdir(exist_ok=True)
    rig = {"tree_scale": TREE_SCALE, "source_assets": ["P03_tree_intact.png", "P03_tree_uprooted.png",
                                                      "P04_land_intact.png", "P02_storm.png"]}

    # --- intact tree ----------------------------------------------------------------------------
    tree = load("P03_tree_intact.png")
    W0 = tree.width
    tree = tree.resize((round(W0 * TREE_SCALE),) * 2, Image.Resampling.LANCZOS)
    w = h = tree.width
    a = np.asarray(tree)[..., 3].astype(np.float32) / 255
    hue = hue_deg(tree)
    yy, xx = np.mgrid[0:h, 0:w]
    foliage = clean((a > 0.16) & (hue >= FOLIAGE_HUE[0]) & (hue < FOLIAGE_HUE[1]) & (yy < BASE_ROW * h)
                    & ~((yy > 0.66 * h) & (xx > 0.34 * w) & (xx < 0.64 * w)))   # moss on the trunk stays on the trunk
    fol_a = np.where(foliage, a, 0)
    # the grass mound is ground, not tree: it stays put while the trunk tips
    grass = (a > 0.05) & (hue >= FOLIAGE_HUE[0]) & (hue < FOLIAGE_HUE[1]) & (yy >= 0.83 * h)
    grass = np.asarray(Image.fromarray((grass * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
    grass &= ~foliage
    mound_a = np.where(grass, a, 0)
    with_alpha(tree, mound_a).save(OUT / "mound.png")
    wood_a = np.where(foliage | grass, 0, a)
    with_alpha(tree, wood_a).save(OUT / "wood.png")

    # canopy fill: the painting's own foliage colours, blurred and darkened, slightly larger than
    # the foliage so small clump movements reveal inner shadow instead of holes
    rgb = np.asarray(tree.convert("RGB"), dtype=np.float32)
    wsum = Image.fromarray((fol_a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10))
    ws = np.asarray(wsum, dtype=np.float32)[..., None] / 255 + 1e-4
    col = np.stack([np.asarray(Image.fromarray((rgb[..., i] * fol_a).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10)),
                               dtype=np.float32) for i in range(3)], -1) / ws
    fill_m = Image.fromarray((foliage * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(3)) \
        .filter(ImageFilter.GaussianBlur(2))
    fill = np.dstack([np.clip(col * 0.42, 0, 255), np.asarray(fill_m, dtype=np.float32) * 0.96]).astype(np.uint8)
    Image.fromarray(fill, "RGBA").save(OUT / "canopy_fill.png")

    # foliage clumps: spatial k-means; each clump hangs from an anchor on its branch
    pts = np.stack([xx[foliage], yy[foliage]], 1).astype(np.float64)
    lab, cent = kmeans(pts, N_CLUMPS)
    labels = -np.ones((h, w), np.int32)
    labels[foliage] = lab
    trunk_x, crotch_y = 0.49 * w, 0.47 * h
    clumps = []
    for i in range(N_CLUMPS):
        m = labels == i
        name = f"clump_{i}.png"
        with_alpha(tree, np.where(m, fol_a, 0)).save(OUT / name)
        cx, cy = cent[i]
        tx, ty = trunk_x, max(cy, crotch_y)
        anchor = (cx + 0.45 * (tx - cx), cy + 0.45 * (ty - cy))
        clumps.append({"file": name, "centroid": [round(cx, 1), round(cy, 1)], "anchor": [round(anchor[0], 1), round(anchor[1], 1)],
                       "pixels": int(m.sum())})
    rig["tree"] = {"size": [w, h], "pivot": [round(0.77 * w, 1), round(0.95 * h, 1)],
                   "pivot_note": "lee (right) edge of the root plate at ground level; wind from the left tips the tree about it",
                   "base_center": [round(0.47 * w, 1), round(0.95 * h, 1)], "ground_row": round(0.95 * h, 1),
                   "trunk_top": [round(trunk_x, 1), round(crotch_y, 1)], "clumps": clumps}

    # painted leaf sprites from the crown's outer edge (real painted pixels, soft round crop)
    rng = np.random.default_rng(11)
    edge = foliage & ~np.asarray(Image.fromarray((foliage * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(15))).astype(bool)
    ey, ex = np.nonzero(edge)
    leaves = []
    r = 13
    disk = np.exp(-((np.mgrid[-r:r, -r:r] ** 2).sum(0)) / (2 * (r * 0.55) ** 2))
    for k in range(28):
        j = rng.integers(len(ex))
        x, y = int(ex[j]), int(ey[j])
        if not (r <= x < w - r and r <= y < h - r):
            continue
        crop = tree.crop((x - r, y - r, x + r, y + r))
        m = np.asarray(crop)[..., 3] / 255 * disk * (labels[y - r:y + r, x - r:x + r] >= 0)
        if m.sum() < 60:
            continue
        name = f"leaf_{k}.png"
        with_alpha(crop, m).save(OUT / name)
        leaves.append({"file": name, "origin": [x, y]})
    rig["leaves"] = leaves

    # --- root plate from the uprooted painting --------------------------------------------------
    up = load("P03_tree_uprooted.png")
    ua = np.asarray(up)[..., 3].astype(np.float32) / 255
    uh = hue_deg(up)
    uy, ux = np.mgrid[0:up.height, 0:up.width]
    # root ball centre and trunk base measured on the 1254 px painting (grid inspection)
    ell = ((ux - 420) / 330.0) ** 2 + ((uy - 880) / 270.0) ** 2
    plate = np.clip((1.15 - ell) / 0.3, 0, 1) * ua * ~((uh >= FOLIAGE_HUE[0]) & (uh < FOLIAGE_HUE[1]))
    plate[(uy < 640)] = 0
    roots = with_alpha(up, plate).crop((40, 560, 820, 1180))
    # uprooted trunk leans ~43 deg right of vertical: rotate CCW so the plate's underside points
    # down when the trunk is upright (pivot = trunk base at crop coords (520, 200))
    roots = roots.rotate(43, Image.Resampling.BICUBIC, center=(520, 200), expand=False)
    s = TREE_SCALE / 1.15            # the uprooted painting is drawn ~15 % larger (silhouette match, v1)
    roots = roots.resize((round(roots.width * s), round(roots.height * s)), Image.Resampling.LANCZOS)
    roots.save(OUT / "roots.png")
    rig["roots"] = {"file": "roots.png", "attach_in_file": [round(520 * s, 1), round(200 * s, 1)],
                    "attach_to_tree": rig["tree"]["base_center"], "note": "hidden below ground until the plate lifts"}
    soil = with_alpha(up, np.clip((1 - (((ux - 330) / 120.0) ** 2 + ((uy - 900) / 90.0) ** 2)), 0, 1) * ua).crop((210, 810, 450, 990))
    soil.resize((round(soil.width * s), round(soil.height * s))).save(OUT / "soil.png")

    # --- ground, bushes, background tree from the land block ------------------------------------
    land = load("P04_land_intact.png")
    grass = land.crop((300, 455, 1010, 640)).convert("RGB")
    # remove flowers and stones (they repeat visibly when tiled): fill those pixels with grass
    # transplanted from shifted copies of the same painting - painted pixels, not synthesis
    g = np.asarray(grass, dtype=np.float32)
    gh = hue_deg(grass)
    gv = g.max(-1)
    sat = (g.max(-1) - g.min(-1)) / np.maximum(gv, 1)
    bad = ~((gh >= 48) & (gh <= 120) & (sat > 0.25)) | (gv > 215)
    bad = np.asarray(Image.fromarray((bad * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0
    filled = g.copy()
    todo = bad.copy()
    for dx, dy in [(97, 0), (-131, 0), (211, 17), (-263, -11), (59, 37), (-41, -29), (311, 5), (-377, 23), (151, -41)]:
        sh_g = np.roll(g, (dy, dx), (0, 1))
        sh_bad = np.roll(bad, (dy, dx), (0, 1))
        use = todo & ~sh_bad
        filled[use] = sh_g[use]
        todo &= ~use
    soft = np.asarray(Image.fromarray((bad * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), dtype=np.float32)[..., None] / 255
    g = g * (1 - soft) + filled * soft
    Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).save(OUT / "grass_texture.png")
    la = np.asarray(land)[..., 3].astype(np.float32) / 255
    ly, lx = np.mgrid[0:land.height, 0:land.width]
    bush = la * np.clip((470 - ly) / 40, 0, 1) * (lx > 280) * (lx < 650) * (ly > 300)
    ramp = np.clip((lx - 280) / 70, 0, 1) * np.clip((650 - lx) / 70, 0, 1)   # no hard crop edges
    with_alpha(land, bush * ramp).crop((280, 300, 650, 470)).save(OUT / "bushes.png")
    small = la * np.clip((418 - ly) / 14, 0, 1) * (lx > 640) * (lx < 1120)
    with_alpha(land, small).crop((640, 95, 1120, 420)).save(OUT / "far_tree.png")

    storm = load("P02_storm.png")
    storm.save(OUT / "storm.png")
    (OUT / "rig.json").write_text(json.dumps(rig, indent=1))

    # preview of every layer on a neutral background
    files = ["wood.png", "mound.png", "canopy_fill.png"] + [c["file"] for c in clumps] + ["roots.png", "soil.png", "bushes.png", "far_tree.png", "grass_texture.png"]
    tiles = []
    for f in files:
        im = Image.open(OUT / f).convert("RGBA")
        im.thumbnail((260, 260))
        t = Image.new("RGBA", (270, 290), (90, 90, 96, 255))
        t.alpha_composite(im, ((270 - im.width) // 2, 5))
        ImageDraw.Draw(t).text((6, 272), f, fill=(255, 255, 255, 255))
        tiles.append(t)
    cols = 5
    sheet = Image.new("RGB", (270 * cols, 290 * ((len(tiles) + cols - 1) // cols)), "black")
    for i, t in enumerate(tiles):
        sheet.paste(t.convert("RGB"), ((i % cols) * 270, (i // cols) * 290))
    sheet.save(HERE / "layers_preview.jpg", quality=88)
    print("layers:", len(files), "leaves:", len(leaves))


if __name__ == "__main__":
    main()
