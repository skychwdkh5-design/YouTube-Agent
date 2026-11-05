"""EP009 B05 satellite acquisition on the continuous engine: smooth orbital curve, banking from the path, sub-pixel push-broom reveal."""
import math, cv2, numpy as np
from scipy.ndimage import gaussian_filter1d
import engine as E
from engine import W, H, Sprite, mat, compose, draw, clamp, seg, lerp, smooth, Hermite, turb
import ground_v4 as G
import ui_v4 as U
from PIL import Image

REPO = G.REPO
_m = cv2.cvtColor(cv2.imread(f"{REPO}/media_original/nasa_tuscaloosa_EO1_20110502.jpg"), cv2.COLOR_BGR2RGB)
SH = 1000; FS = SH / _m.shape[0]
STRIP = cv2.resize(_m, (int(_m.shape[1] * FS), SH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
SW = STRIP.shape[1]
_gray = STRIP.mean(2)
FOOT = cv2.GaussianBlur((_gray > 12 / 255).astype(np.float32), (0, 0), 0.7)
GHOST = np.repeat((_gray * 0.28)[..., None], 3, 2)
ROWS = np.arange(SH)
_cen = np.array([(np.nonzero(_gray[r] > 12 / 255)[0][[0, -1]].mean() if (_gray[r] > 12 / 255).any() else SW / 2) for r in ROWS])
ROW_C = gaussian_filter1d(_cen, 14)                       # smoothed footprint centre -> the satellite never jitters with pixel noise
_edges = np.array([(np.nonzero(_gray[r] > 12 / 255)[0][[0, -1]] if (_gray[r] > 12 / 255).any() else [0, SW]) for r in ROWS], float)
EDGE = np.clip(cv2.morphologyEx((FOOT > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32), 0, 1)
EDGE = cv2.GaussianBlur(EDGE, (0, 0), 0.8)
SX0, SY0 = (W - SW) / 2 + 120, (H - SH) / 2 + 40
SAT = Sprite(G.load("P01_satellite"), ref_h=300)
YY = np.arange(SH, dtype=np.float32)[:, None]

# scan progress (ground row under the satellite): near-constant speed, soft ends, C1
ROW = Hermite([(18.2, -120.0), (18.9, 60.0), (21.9, 1060.0), (22.6, 1140.0)])
CAM = E.Cam([(18.0, (0, 0, 1.0)), (20.0, (0, 0, 1.0)), (22.4, (0, 0, 1.0))])   # replaced below (needs scan knowledge)
CAMK = E.Cam([(18.0, (0, -60, 1.00)), (19.6, (-6, 0, 1.025)), (21.4, (-14, 70, 1.06)), (22.6, (-16, 90, 1.07))])

def sat_pos(t):
    r = ROW(t); u = clamp((r + 120) / 1260)
    rc = float(np.interp(clamp(r, 0, SH - 1), ROWS, ROW_C))
    return SX0 + rc + 330 - 40 * u, SY0 + r - 250 - 60 * math.sin(math.pi * u), r, u

def bank(t):  # bank follows the lateral acceleration of the path (no canned wobble)
    e = 0.30; x0, _, _, _ = sat_pos(t - e); x1, _, _, _ = sat_pos(t); x2, _, _, _ = sat_pos(t + e)
    lat = (x2 - 2 * x1 + x0) / (e * e)
    return clamp(-0.0045 * lat, -6, 6) - 4 + 1.6 * turb(t, 8, 0.12)

def strip_array(t, scan):
    band = 26.0
    w = np.clip((scan - YY) / band, 0, 1); w = (w * w * w * (w * (6 * w - 15) + 10))      # continuous development band, 0 at the line
    img = GHOST + (STRIP - GHOST) * w[..., None]
    a = FOOT
    # scanline: 2 px core + soft glow, only across the real footprint (float row coordinate -> sub-pixel exact)
    core = np.exp(-((YY - scan) / 1.1) ** 2); glow = 0.45 * np.exp(-((YY - scan) / 7.0) ** 2)
    on = ((scan > 0) & (scan < SH)) * 1.0
    img = img + on * (core[..., None] * np.array([1.0, 0.96, 0.86], np.float32) * 0.9 + glow[..., None] * np.array([1.0, 0.89, 0.63], np.float32) * 0.6) * a[..., None]
    # footprint guide edges drawn on behind the scan, then fading
    vis = np.clip((scan - YY) / 3.0, 0, 1) * (1 - smooth(seg(t, 22.3, 22.9)))
    img = img + (EDGE * vis * 0.55)[..., None] * np.array([0.91, 0.69, 0.33], np.float32)
    # capture: exposure pulse on the strip only (smooth rise and fall)
    ex = 0.13 * smooth((t - 21.30) / 0.09) * (1 - smooth((t - 21.39) / 0.5))
    img = img * (1 + ex)
    out = np.empty((SH, SW, 4), np.float32); out[..., :3] = np.clip(img, 0, 1.6) * a[..., None]; out[..., 3] = a
    return out

class _A:  # tiny sprite wrapper for a per-frame array
    def __init__(s, a): s.a = a; s.h, s.w = a.shape[:2]

def stars(c, t, cam):
    lay = np.zeros((H, W, 3), np.float32)
    for i in range(170):
        x = (G.M.h01(i) * W - t * 6 * (0.3 + G.M.h01(i + 1)) - 0.2 * cam[0]) % W; y = (G.M.h01(i + 2) * H - 0.2 * cam[1]) % H
        tw = 0.75 + 0.25 * math.sin(t * (1 + 2 * G.M.h01(i + 5)) + i); v = tw * (70 + 140 * G.M.h01(i + 3)) / 255
        cv2.circle(lay, (int(x * 16), int(y * 16)), 16, (v * 0.86, v * 0.9, v), -1, cv2.LINE_AA, 4)
    c += lay

def overlays(c, t, Vm):
    """Satellite + labels, drawn through any world->screen matrix Vm (strip camera or the dive camera)."""
    x, y, r, u = sat_pos(t)
    a = smooth(seg(t, 18.1, 18.7)) * (1 - smooth(seg(t, 22.4, 23.0)))
    k = 220.0 / SAT.h; yaw = 0.93 + 0.07 * math.cos(t * 0.6)
    draw(c, SAT, compose(Vm, mat(x, y, bank(t), k * yaw, k, SAT.w / 2, SAT.h / 2)), alpha=a, shadow=(5, 0.30), shoff=(10, 14))
    fade = lambda a0, a1, b0, b1: smooth(seg(t, a0, a1)) * (1 - smooth(seg(t, b0, b1)))
    U.put_tag(c, "Symbolic satellite, not the EO-1 spacecraft", W - 28, 86, True, a=fade(18.7, 19.1, 21.9, 22.2))
    U.put_tag(c, "Real EO-1 image footprint", SX0 + SW + 30, SY0 + 60, a=fade(19.4, 19.8, 21.9, 22.2))
    U.put_tag(c, "CAPTURED · MAY 2, 2011", SX0 + SW + 30, SY0 + 110, bg=(120, 52, 18, 200), a=fade(21.4, 21.7, 22.6, 23.0))
    U.put_tag(c, U.ILL_TXT, W - 28, 28, True, bg=(120, 52, 18, 190), a=fade(18.4, 18.8, 21.9, 22.2))


def view_matrix(t):
    cx, cy, z = CAMK(t); C = (W / 2, H / 2)
    return np.array([[z, 0, C[0] - z * (C[0] + cx)], [0, z, C[1] - z * (C[1] + cy)]], np.float64)


def scene(t, credit=True):
    c = np.empty((H, W, 3), np.float32); c[:] = np.array([6, 10, 22], np.float32) / 255
    cx, cy, z = CAMK(t); Vm = view_matrix(t)
    stars(c, t, (cx, cy))
    x, y, r, u = sat_pos(t); scan = clamp(r - 70, 0, SH + 5) if t < 22.6 else SH + 5
    draw(c, _A(strip_array(t, scan)), compose(Vm, mat(SX0, SY0, 0, 1, 1, 0, 0)))
    overlays(c, t, Vm)
    if credit: U.put_tag(c, U.C_EO1, 28, H - 62, a=smooth(seg(t, 19.2, 19.6)))
    return c


def probe(t):
    x, y, r, u = sat_pos(t); cx, cy, z = CAMK(t)
    return {"satellite": dict(x=x, y=y, roll=bank(t)), "scanline": dict(row=r), "camera": dict(x=cx, y=cy, zoom=z)}
