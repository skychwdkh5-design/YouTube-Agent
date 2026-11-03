#!/usr/bin/env python3
"""EP009 B04 motion test v2: a separate painted 2.5D scene (no satellite map), 5 s.

0.0-1.0 s  wind builds, the tree resists (crown sways, trunk barely leans)
1.0-2.0 s  the root plate loses grip and lifts on the windward side, the trunk starts to lean
2.0-3.5 s  the tree falls about the lee edge of the root plate; crown and branches trail
3.5-5.0 s  impact: crown compresses, branches whip, leaves burst, bushes recoil, motion decays;
           the tree stays down

Engine: tools/motion (NumPy + Pillow) + FFmpeg. Layers come from cut_layers.py (pixels of the
verified EP009 paintings only). Camera: real pinhole projection over a ground plane, so every
layer moves by its depth (parallax), not a 2D zoom.

  python3 productions/ep009-tornado-scars/review/motion_test_B04_v2/cut_layers.py
  python3 productions/ep009-tornado-scars/review/motion_test_B04_v2/build_b04_v2.py [--still T ...]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools" / "motion"))
import compositor as C  # noqa: E402
import easing as E  # noqa: E402

W, H, FPS, DUR = 1920, 1080, 30, 5.0
L = HERE / "layers"
RIG = json.loads((L / "rig.json").read_text())

# --- camera: pinhole over a flat ground ---------------------------------------------------------
F, HC, YH = 1400.0, 1.0, 500.0          # focal (px), camera height (world units), horizon row
CAM_X = [{"at": 0.0, "v": -0.10, "easing": "camera"}, {"at": 2.0, "v": 0.00, "easing": "move"},
         {"at": 3.7, "v": 0.30, "easing": "settle_soft"}, {"at": 5.0, "v": 0.36}]
CAM_DZ = [{"at": 0.0, "v": 0.0, "easing": "camera"}, {"at": 5.0, "v": 0.32}]
SKY_TOP, SKY_HOR, HAZE = np.array([38, 50, 64.]), np.array([200, 152, 104.]), np.array([176, 146, 112.])


def cam(t):
    return E.interpolate(CAM_X, t, "v"), E.interpolate(CAM_DZ, t, "v")


def project(wx, wz, t, wy=0.0):
    cx, dz = cam(t)
    z = wz - dz
    return 960 + F * (wx - cx) / z, YH + F * (HC - wy) / z, F / z


# --- assets ---------------------------------------------------------------------------------------
def rgba(name):
    return Image.open(L / name).convert("RGBA")


TREE = RIG["tree"]
TW, THh = TREE["size"]
PADX, PADT, PADB = 150, 110, 320
LOCAL = (TW + 2 * PADX, THh + PADT + PADB)
PIV = (TREE["pivot"][0] + PADX, TREE["pivot"][1] + PADT)
BASE = (TREE["base_center"][0] + PADX, TREE["base_center"][1] + PADT)
GROUND_ROW = TREE["ground_row"] + PADT
WOOD, FILL, MOUND = rgba("wood.png"), rgba("canopy_fill.png"), rgba("mound.png")
CLUMPS = []
for i, c in enumerate(TREE["clumps"]):
    im = rgba(c["file"])
    bb = im.getchannel("A").getbbox()
    CLUMPS.append({"im": im.crop(bb), "off": (bb[0] + PADX, bb[1] + PADT),
                   "anchor": (c["anchor"][0] + PADX, c["anchor"][1] + PADT),
                   "r": math.hypot(c["centroid"][0] - TREE["pivot"][0], c["centroid"][1] - TREE["pivot"][1]),
                   "f": 1.3 + 0.37 * i % 1.4, "ph": 1.7 * i, "amp": 3.5 + (i * 7 % 5)})
ROOTS = rgba("roots.png")
ra = np.asarray(ROOTS).copy()                       # keep only the plate below the attach row
ax_r, ay_r = RIG["roots"]["attach_in_file"]
ROOTS_FULL = Image.fromarray(ra.copy(), "RGBA")
ra[: int(ay_r) - 6, :, 3] = 0
ROOTS = Image.fromarray(ra, "RGBA")              # plate only; the stub fades in as the plate lifts
SOIL = rgba("soil.png")
LEAVES = [rgba(lf["file"]) for lf in RIG["leaves"]]
BUSH, FARTREE, STORM = rgba("bushes.png"), rgba("far_tree.png"), rgba("storm.png")
HERO_SMALL = Image.open(ROOT / "productions/ep009-tornado-scars/handoff/assets/P03_tree_intact.png").convert("RGBA").resize((400, 400), Image.Resampling.LANCZOS)

TREE_WX, TREE_WZ = -0.97, 3.70
TREE_S0 = 0.90 * 3.70 / F * (F / 3.70)              # screen scale of the 690 px canvas at t=0 (0.90)
tbase = TREE_S0                                      # scale = 0.90 * (z0 / z) <= 1.0 over the push

# --- wind --------------------------------------------------------------------------------------
WIND = [{"at": 0.0, "v": 0.15, "easing": "move"}, {"at": 1.0, "v": 1.0, "easing": "linear"},
        {"at": 3.5, "v": 1.0, "easing": "exit"}, {"at": 5.0, "v": 0.35}]


def wind(t, x=0.0):
    s = E.interpolate(WIND, t, "v")
    return s * (0.62 + 0.38 * math.sin(2 * math.pi * 0.72 * t - x * 0.004))   # gusts travel left->right


# --- tree angle (degrees fallen to the right; PIL angle = -theta) ------------------------------
PRE = [{"at": 0.0, "v": 0.0, "easing": "move"}, {"at": 1.0, "v": 1.5, "easing": "move"},
       {"at": 1.45, "v": 7.0, "easing": "move"}, {"at": 1.65, "v": 8.0, "easing": "move"},
       {"at": 2.0, "v": 14.0}]
T_IMP = 3.5


def local_tree(th_deg, crown_dx, clump_rot, roots=True):
    """Compose the tree in its upright frame, bend the crown, return the local RGBA image."""
    can = Image.new("RGBA", LOCAL, (0, 0, 0, 0))
    if roots:
        lift = E.segment(th_deg, 4.0, 30.0, "enter")
        r = ROOTS if lift < 0.01 else Image.blend(ROOTS, ROOTS_FULL, lift)
        can.alpha_composite(r, (int(round(BASE[0] - ax_r)), int(round(BASE[1] - ay_r))))
    body = Image.new("RGBA", LOCAL, (0, 0, 0, 0))
    body.alpha_composite(FILL, (PADX, PADT))
    body.alpha_composite(WOOD, (PADX, PADT))
    for c, rot in zip(CLUMPS, clump_rot):
        im = c["im"]
        if abs(rot) > 0.05:
            # rotate the clump about its branch anchor
            ax, ay = c["anchor"][0] - c["off"][0], c["anchor"][1] - c["off"][1]
            p = C.place(im, (ax, ay), c["anchor"], rot)
            C.composite(body, p.image, p.xy)
        else:
            body.alpha_composite(im, c["off"])
    body = C.bend(body, base_y=GROUND_ROW, amount_px=0, lean_px=crown_dx, power=2.2)
    pad = body.info.get("bend_pad", 0)
    can.alpha_composite(body.crop((pad, 0, pad + LOCAL[0], LOCAL[1])))
    return can


def contact_angle():
    """Angle at which the crown first reaches the ground (measured on the composed silhouette)."""
    im = local_tree(0, 0, [0] * len(CLUMPS), roots=False)
    for th in np.arange(55, 95, 0.5):
        p = C.place(im, PIV, PIV, -th)
        a = np.asarray(p.image.getchannel("A")) > 60
        ys, xs = np.nonzero(a)
        ys = ys + p.xy[1]
        xs = xs + p.xy[0]
        far = (xs - PIV[0]) > 260                      # crown, not the root plate
        if far.any() and ys[far].max() >= PIV[1] + 8:
            return float(th)
    return 85.0


TH_IMP = contact_angle()


def theta(t):
    if t <= 2.0:
        return E.interpolate(PRE, t, "v")
    if t <= T_IMP:
        return 14.0 + (TH_IMP - 14.0) * E.segment(t, 2.0, T_IMP, "topple")
    u = t - T_IMP                                  # compresses into the crown, never rises back up
    return TH_IMP + 1.2 * (1 - math.exp(-8 * u)) + 1.6 * math.exp(-7 * u) * math.sin(2 * math.pi * 2.4 * u)


def squash(t):
    """How much the crown is compressed against the ground (0 = none); it never springs back up."""
    if t < T_IMP - 0.04:
        return 0.0
    u = max(0.0, t - T_IMP + 0.04)
    return max(0.0, 0.26 * (1 - math.exp(-14 * u)) + 0.12 * math.exp(-5 * u) * math.sin(2 * math.pi * 2.2 * u))


def omega(t):
    return (theta(t + 1 / 120) - theta(t - 1 / 120)) * 60


def crown_dx(t):
    """Local crown displacement (px, + = toward the fall): wind lean, inertia lag, impact whip."""
    w = wind(t, 0) * 24
    if t < T_IMP:
        lag = -0.34 * omega(t)                      # crown trails the trunk while it rotates
        return w * (1 - E.segment(t, 2.0, 2.4, "move")) + lag
    u = t - T_IMP
    lag_end = -0.34 * omega(T_IMP - 0.02)
    return lag_end * math.exp(-9 * u) + 38 * math.exp(-3.8 * u) * math.sin(2 * math.pi * 1.5 * u) + 4 * wind(t)


def clump_rot(t):
    out = []
    for c in CLUMPS:
        r = c["amp"] * 0.8 * wind(t, c["anchor"][0]) * math.sin(2 * math.pi * c["f"] * t + c["ph"])
        if T_IMP - 1.4 < t < T_IMP:
            r += -0.035 * omega(t) * (c["r"] / 300)  # outer clumps trail more
        if t >= T_IMP:
            u = t - T_IMP
            r += 2.3 * c["amp"] * math.exp(-3.2 * u) * math.sin(2 * math.pi * (c["f"] + 0.6) * u + c["ph"] * 0.3)
        out.append(r)
    return out


# --- background -----------------------------------------------------------------------------------
def make_tile():
    """Grass tile: mirrored left-right (blades stay upright), cross-faded top/bottom so it wraps
    vertically without a seam; plus a blurred pyramid for distant rows."""
    g = Image.open(L / "grass_texture.png").convert("RGB")
    a = np.asarray(g, dtype=np.float32)
    a = np.concatenate([a, a[:, ::-1]], 1)
    n = 46
    top, bot = a[:n].copy(), a[-n:].copy()
    wgt = np.linspace(0, 1, n)[:, None, None]
    a = a[: -n].copy()
    a[:n] = bot * (1 - wgt) + top * wgt
    levels = [a]
    im = Image.fromarray(a.astype(np.uint8))
    for _ in range(5):
        im = im.filter(ImageFilter.GaussianBlur(1.0)).resize((max(2, im.width // 2), max(2, im.height // 2)), Image.Resampling.LANCZOS)
        levels.append(np.asarray(im, dtype=np.float32))
    return levels


TILE = make_tile()
TX, TV = 760.0, 205.0                                  # texture px per world unit (across, depth)
ROWS = np.arange(int(YH) + 2, H)


def ground(t, out):
    cx, dz = cam(t)
    zr = F * HC / (ROWS - YH)
    sx = np.arange(W, dtype=np.float32)
    mins = TX * zr / F
    lvl = np.clip(np.floor(np.log2(np.maximum(mins, 1e-3)) + 0.6), 0, 5).astype(int)
    for k in range(6):
        sel = np.nonzero(lvl == k)[0]
        if not len(sel):
            continue
        tex = TILE[k]
        th, tw = tex.shape[:2]
        z = zr[sel][:, None]
        u = ((cx + (sx[None, :] - 960) * z / F) * TX) / 2 ** k
        v = np.broadcast_to(((z + dz) * TV) / 2 ** k, u.shape)
        def samp(uu, vv):
            u0 = np.floor(uu).astype(np.int64)
            v0 = np.floor(vv).astype(np.int64)
            fu = (uu - u0)[..., None]
            fv = (vv - v0)[..., None]
            u0 %= tw
            v0 %= th
            u1, v1 = (u0 + 1) % tw, (v0 + 1) % th
            return (tex[v0, u0] * (1 - fu) * (1 - fv) + tex[v0, u1] * fu * (1 - fv) +
                    tex[v1, u0] * (1 - fu) * fv + tex[v1, u1] * fu * fv)
        # texture bombing: a second, shifted sampling blended by a smooth world-space mask breaks
        # the visible repeat; low-frequency tone variation adds natural patchiness
        wu, wv = u * 2 ** k / TX, v * 2 ** k / TV
        m = 0.5 + 0.5 * np.sin(wu * 1.9 + 1.1) * np.sin(wv * 0.9 + 0.4) * np.cos(wu * 0.7 - wv * 0.5)
        m = np.clip((m - 0.35) / 0.3, 0, 1)[..., None]
        col = samp(u, v) * (1 - m) + samp(u * 1.0 + 517 / 2 ** k, v + 61 / 2 ** k) * m
        tone = 1 + 0.10 * np.sin(wu * 0.8 + 2.0) * np.sin(wv * 0.6 + 0.3)
        col = col * tone[..., None]
        hz = (1 - np.exp(-z / 9.0))[..., None]
        col = col * 0.86 * (1 - hz) + HAZE * hz          # aerial perspective
        out[ROWS[sel]] = col


SKY = np.zeros((H, W, 3), np.float32)
_y = np.linspace(0, 1, H)[:, None, None]
SKY[:] = SKY_TOP * (1 - np.clip(_y / (YH / H), 0, 1) ** 1.4) + SKY_HOR * np.clip(_y / (YH / H), 0, 1) ** 1.4

rng = np.random.default_rng(5)
FAR = []                                               # background trees: (wx, wz, height, sprite, flip)
for i, wx in enumerate(np.linspace(-6.5, 7.5, 13)):
    wz = 15 + rng.uniform(0, 14)
    hero = i % 3 == 1
    FAR.append((wx + rng.uniform(-0.4, 0.4), wz, rng.uniform(1.1, 1.8) * (1.15 if hero else 1), HERO_SMALL if hero else FARTREE, bool(i % 2)))
FAR.sort(key=lambda f: -f[1])
BUSHES = [(-2.15, 4.9, 1.1, False), (0.95, 4.3, 0.9, True), (0.62, 3.25, 1.0, False), (-1.9, 3.1, 0.8, True)]
FG = [(-1.55, 1.95, 1.5, False), (1.35, 1.9, 1.6, True)]   # foreground framing bushes (defocused)


def sprite_on_ground(frame, im, wx, wz, height_world, t, flip=False, haze=0.0, blur=0.0, bend_px=0.0, anchor_bottom=0.98):
    sx, sy, sc = project(wx, wz, t)
    hpx = height_world * sc
    if hpx < 3:
        return None
    s = C.resize_to_height(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else im, hpx)
    if abs(bend_px) > 0.2:
        s = C.bend(s, base_y=s.height * anchor_bottom, amount_px=0, lean_px=bend_px)
    if haze > 0:
        arr = np.asarray(s, dtype=np.float32)
        arr[..., :3] = arr[..., :3] * (1 - haze) + HAZE * haze
        s = Image.fromarray(arr.astype(np.uint8), "RGBA")
    if blur > 0.1:
        s = s.filter(ImageFilter.GaussianBlur(blur))
    xy = (int(sx - s.width / 2), int(sy - s.height * anchor_bottom))
    C.composite(frame, s, xy)
    return sx, sy, sc


def impact_push(t, sx_obj):
    """Spring recoil of vegetation near the crown's landing point (px of lean)."""
    if t < T_IMP:
        return 0.0
    u = t - T_IMP
    d = sx_obj - IMPACT_SX
    k = 55 * math.exp(-abs(d) / 380)
    return math.copysign(1, d) * k * math.exp(-3.0 * u) * math.sin(2 * math.pi * 1.9 * u + 0.4)


# --- particles ------------------------------------------------------------------------------------
def tree_point(local_xy, t):
    """Screen position of a point given in the tree's local (upright, unbent) frame."""
    sx, sy, sc = project(TREE_WX, TREE_WZ, t)
    s = tbase * (TREE_WZ / (TREE_WZ - cam(t)[1]))
    th = math.radians(theta(t))
    dx, dy = (local_xy[0] - PIV[0]) * s, (local_xy[1] - PIV[1]) * s
    return sx + dx * math.cos(th) - dy * math.sin(th), sy + dx * math.sin(th) + dy * math.cos(th)


def make_leaves():
    r = np.random.default_rng(17)
    out = []
    for k in range(10):                                   # torn off by the wind, 0.5-2.6 s
        c = CLUMPS[r.integers(len(CLUMPS))]
        out.append(dict(t0=0.5 + k * 0.21, src=(c["anchor"][0] + r.uniform(-60, 60), c["anchor"][1] - r.uniform(0, 60)),
                        v=(r.uniform(160, 300), r.uniform(-90, 20)), spr=int(r.integers(len(LEAVES))), sc=r.uniform(0.7, 1.1),
                        spin=r.uniform(-400, 400), life=r.uniform(1.6, 2.6)))
    for k in range(46):                                   # burst at impact from the crown
        c = CLUMPS[r.integers(len(CLUMPS))]
        out.append(dict(t0=T_IMP + r.uniform(-0.03, 0.12), src=(c["anchor"][0] + r.uniform(-90, 90), c["anchor"][1] + r.uniform(-90, 60)),
                        v=(r.uniform(-140, 260), r.uniform(-420, -120)), spr=int(r.integers(len(LEAVES))), sc=r.uniform(0.6, 1.2),
                        spin=r.uniform(-600, 600), life=r.uniform(1.0, 1.5)))
    return out


LEAF_P = make_leaves()


def draw_leaves(frame, t):
    for lf in LEAF_P:
        u = t - lf["t0"]
        if u < 0 or u > lf["life"]:
            continue
        x0, y0 = tree_point(lf["src"], lf["t0"])
        k = 1.8                                           # air drag on a leaf
        fx = (1 - math.exp(-k * u)) / k
        x = x0 + lf["v"][0] * fx + 70 * wind(t) * u          # wind carries it
        y = y0 + lf["v"][1] * fx + 0.5 * 260 * u * u * 0.55 + 6 * math.sin(7 * u + lf["spin"] * 0.01)
        gy = YH + F * HC / (TREE_WZ - cam(t)[1]) + 20
        if y > gy:                                        # resting in the grass
            y = gy
        spr = LEAVES[lf["spr"]]
        s = spr.resize((max(2, int(spr.width * lf["sc"])), max(2, int(spr.height * lf["sc"] * (0.55 + 0.45 * abs(math.cos(u * 6 + lf['spin'] * 0.02)))))))
        s = s.rotate(lf["spin"] * u, Image.Resampling.BICUBIC, expand=True)
        a = max(0.0, min(1.0, (lf["life"] - u) / 0.35))
        if a < 1:
            s.putalpha(s.getchannel("A").point(lambda v: int(v * a)))
        C.composite(frame, s, (int(x - s.width / 2), int(y - s.height / 2)))


DUSTS = []


def init_dust():
    global IMPACT_SX
    cx, cy = tree_point((PIV[0] + 520, PIV[1] - 40), T_IMP)
    IMPACT_SX = cx
    DUSTS.append(C.Dust((cx, cy + 10), T_IMP - 0.02, (150, 128, 92), 90, 31, 1.1, alpha=95))
    rx, ry = tree_point((BASE[0] - 120, BASE[1] + 20), 2.4)
    DUSTS.append(C.Dust((rx, ry), 1.2, (110, 82, 56), 40, 7, 0.6, alpha=80))


IMPACT_SX = 0.0
init_dust()


# --- frame ----------------------------------------------------------------------------------------
def render(t, log=None):
    sh = C.shake(t, T_IMP, 5.0, 12.0, 8.0)
    img = SKY.copy()
    ground(t, img)
    frame = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    # distant storm (sky depth: barely moves), drifting toward the scene
    sc = 0.42 + 0.02 * t / DUR
    st = STORM.resize((int(STORM.width * sc), int(STORM.height * sc)), Image.Resampling.LANCZOS)
    arr = np.asarray(st, dtype=np.float32)
    arr[..., :3] = arr[..., :3] * 0.62 + np.array([150, 128, 112.]) * 0.38
    st = Image.fromarray(arr.astype(np.uint8), "RGBA")
    C.composite(frame, st, (int(-60 + 10 * t - 8 * cam(t)[0]), int(YH + 6 - st.height * 0.92)))
    # far tree line with haze
    for wx, wz, hw, spr, flip in FAR:
        sx, sy, scl = project(wx, wz, t)
        if -300 < sx < W + 300:
            sprite_on_ground(frame, spr, wx, wz, hw, t, flip, haze=min(0.7, 0.25 + wz / 45), blur=0.6,
                             bend_px=3 * wind(t, sx) * math.sin(2 * math.pi * 0.7 * t + wx))
    # bushes behind the tree
    for wx, wz, hw, flip in BUSHES:
        if wz > TREE_WZ:
            sx = project(wx, wz, t)[0]
            sprite_on_ground(frame, BUSH, wx, wz, hw * 0.45, t, flip, haze=0.08,
                             bend_px=8 * wind(t, sx) + impact_push(t, sx))
    # root pit and soil (revealed as the plate lifts)
    th = theta(t)
    lift = E.segment(th, 3.0, 40.0, "enter")
    gx, gy, gsc = project(TREE_WX, TREE_WZ, t)
    s = tbase * (TREE_WZ / (TREE_WZ - cam(t)[1]))
    # the grass mound is ground: it stays while the trunk and root plate tip
    mz = MOUND.resize((max(2, int(MOUND.width * s)), max(2, int(MOUND.height * s))), Image.Resampling.LANCZOS)
    pm = C.place(mz, ((PIV[0] - PADX) * s, (PIV[1] - PADT) * s), (gx, gy), 0)
    C.composite(frame, pm.image, pm.xy)
    if lift > 0.01:
        pw = int(0.62 * TW * s * lift) + 2
        pit = SOIL.resize((pw, max(2, int(pw * 0.22))))
        pa = np.asarray(pit, dtype=np.float32)
        pa[..., :3] *= 0.42
        pit = Image.fromarray(pa.astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(2))
        C.composite(frame, pit, (int(gx - (PIV[0] - BASE[0]) * s - pw / 2), int(gy - pit.height * 0.6)))
    # the tree
    s = tbase * (TREE_WZ / (TREE_WZ - cam(t)[1]))
    dx = crown_dx(t)
    loc = local_tree(th, dx, clump_rot(t))
    loc = loc.resize((int(loc.width * s), int(loc.height * s)), Image.Resampling.LANCZOS)
    p = C.place(loc, (PIV[0] * s, PIV[1] * s), (gx + sh[0], gy + sh[1]), -th)
    # soil holds whatever is below the ground line at the tree's depth (roots before they lift,
    # the part of the crown pressed into the grass)
    arr = np.asarray(p.image).copy()
    rows = np.arange(arr.shape[0]) + p.xy[1]
    keep = np.clip((gy + sh[1] + 14 - rows) / 10, 0, 1)
    arr[..., 3] = (arr[..., 3] * keep[:, None]).astype(np.uint8)
    # crown pressed against the ground after impact: rows near the ground are compressed
    k = squash(t)
    if k > 0.005:
        band = int(190 * s)
        g_local = min(int(gy + sh[1] - p.xy[1]), arr.shape[0])
        top = max(0, g_local - band)
        if g_local > top:
            d = (g_local - np.arange(top, g_local)).astype(np.float32)
            dsrc = d + k * d * (1 - d / band)
            src = np.clip(np.round(g_local - dsrc).astype(int), 0, arr.shape[0] - 1)
            cols = np.arange(arr.shape[1]) + p.xy[0]
            wcol = np.clip((cols - (gx + 150 * s)) / 90, 0, 1)[None, :, None]
            part = arr[top:g_local].astype(np.float32)
            arr[top:g_local] = (part * (1 - wcol) + arr[src].astype(np.float32) * wcol).astype(np.uint8)
    p = C.Placed(Image.fromarray(arr, "RGBA"), p.xy)
    C.ground_shadow(frame, p, gy + sh[1], lean=1.4, squash=0.16, strength=0.5, blur=10,
                    contact=(gx - 0.3 * (PIV[0] - BASE[0]) * s, 210 * s * (1 - 0.7 * lift), 0.45))
    C.composite(frame, p.image, p.xy)
    for d in DUSTS:
        d.draw(frame, t)
    # bushes in front of the tree, then leaves, then defocused foreground framing
    for wx, wz, hw, flip in BUSHES:
        if wz <= TREE_WZ:
            sx = project(wx, wz, t)[0]
            sprite_on_ground(frame, BUSH, wx, wz, hw * 0.45, t, flip, bend_px=9 * wind(t, sx) + impact_push(t, sx))
    draw_leaves(frame, t)
    for wx, wz, hw, flip in FG:
        sx = project(wx, wz, t)[0]
        sprite_on_ground(frame, BUSH, wx, wz, hw * 0.45, t, flip, blur=5.0,
                         bend_px=14 * wind(t, sx) + 0.4 * impact_push(t, sx), anchor_bottom=0.75)
    # grade + labels
    ov = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(ov)
    for y in range(120):
        a = int(140 * (1 - y / 120) ** 2)
        d.line((0, y, W, y), fill=(7, 20, 29, a))
        d.line((0, H - y, W, H - y), fill=(7, 20, 29, a + 20))
    d.text((42, 30), "ORBITAL ATLAS", font=C.font(19), fill="#F4EDD8")
    lab = "ILLUSTRATION / NOT TO SCALE"
    d.text((W - 42 - d.textbbox((0, 0), lab, font=C.font(19))[2], 31), lab, font=C.font(19), fill="#F4EDD8")
    d.text((42, H - 38), "Painted reconstruction - not a specific tree, place or footage", font=C.font(16), fill="#E3E9E2")
    frame = Image.alpha_composite(frame, ov)
    if log is not None:
        log.add(t=t, theta=th, omega=omega(t), crown_dx=dx, cam_x=cam(t)[0], cam_dz=cam(t)[1], tree_scale=s,
                wind=wind(t), clump0=clump_rot(t)[0], ground_y=gy)
    return frame


def render_mb(t, log=None):
    w = abs(omega(t))
    fast = w > 25 or (T_IMP - 0.05 <= t <= T_IMP + 0.35)
    if fast:
        im = C.supersample(lambda u: render(u).convert("RGB"), t, FPS, 5, 0.5)
        render(t, log)
        return im.convert("RGBA")
    return render(t, log)


def _work(i):
    lg = C.FrameLog()
    im = render_mb(i / FPS, lg)
    return im.convert("RGB").tobytes(), lg.rows[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", type=float, nargs="*")
    a = ap.parse_args()
    print(f"contact angle {TH_IMP:.1f} deg")
    if a.still:
        for t in a.still:
            render_mb(t).convert("RGB").save(HERE / f"_still_{t:04.2f}.jpg", quality=90)
        return
    import multiprocessing as mp
    n = int(DUR * FPS)
    log = C.FrameLog()
    with mp.get_context("fork").Pool(max(1, mp.cpu_count())) as pool:   # frames are independent
        def frames():
            for data, row in pool.imap(_work, range(n), chunksize=2):
                log.rows.append(row)
                yield Image.frombytes("RGB", (W, H), data)
        C.encode(frames(), HERE / "B04_v2_5s.mp4", (W, H), FPS)
    log.write(HERE / "B04_v2_framelog.json")
    print("wrote", HERE / "B04_v2_5s.mp4")


if __name__ == "__main__":
    main()
