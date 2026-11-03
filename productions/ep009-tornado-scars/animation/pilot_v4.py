"""EP009 56 s pilot — v4, every scene on the continuous engine (float affines, sub-frame sampling, C1 camera paths).
Usage: python3 render_v4.py pilot out.mp4 t0 t1 nsub     (scene(t) is a pure function of time)
"""
import math, json, os
import numpy as np, cv2
from PIL import Image
import engine as E
from engine import W, H, Sprite, mat, compose, draw, draw_remap, clamp, seg, lerp, smooth, Hermite, turb
import ground_v4 as G
import sat_v4 as S
import ui_v4 as U
import motion as M

G.PILOT = True
REPO = G.REPO; MO = f"{REPO}/media_original"; AS = G.AS; MK = f"{AS}/markers"
INK, OCHRE = U.INK, U.OCHRE
INKf, OCHf = np.array(INK, np.float32) / 255, np.array(OCHRE, np.float32) / 255
C_MOD = "NASA Terra MODIS · J. Schmaltz, MODIS Rapid Response · NASA Earth Observatory"
C_GOES = "NOAA NESDIS · GOES-13 imagery, April 2011"
e = M.ease

def rd(p): return Image.fromarray(cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB))
DOC_M01 = E.Doc(rd(f"{MO}/nasa_tuscaloosa_EO1_20110502.jpg"))
DOC_B = E.Doc(rd(f"{MO}/nasa_modis_before_20110412.jpg"))
DOC_A = E.Doc(rd(f"{MO}/nasa_modis_after_20110428.jpg"))

def trim(im, thr=24):
    a = im.getchannel("A").point(lambda v: 255 if v > thr else 0); bb = a.getbbox(); return im.crop(bb) if bb else im
def mk(n): return Sprite(trim(G._clean(Image.open(f"{MK}/{n}.png").convert("RGBA"))), ref_h=300)
PIN_R, PIN_O, ARR_W, ARR_O, MEAS = mk("pin_red"), mk("pin_ochre"), mk("arrow_white"), mk("arrow_orange"), mk("measure_double")

TRACK = [(2024, 4248), (2420, 4014), (2780, 3798), (3104, 3618)]
TR_LEN = sum(math.dist(a, b) for a, b in zip(TRACK, TRACK[1:]))
def tr_pt(s):
    d = clamp(s) * TR_LEN
    for a, b in zip(TRACK, TRACK[1:]):
        l = math.dist(a, b)
        if d <= l: return (lerp(a[0], b[0], d / l), lerp(a[1], b[1], d / l))
        d -= l
    return TRACK[-1]

def scr(pt, cx, cy, vw): s = W / vw; return (W / 2 + (pt[0] - cx) * s, H / 2 + (pt[1] - cy) * s)
def tag(c, text, x, y, a=1.0, right=False, bg=(10, 18, 34, 170), font=None):
    if font is None: U.put_tag(c, text, x, y, right, a, bg)
    elif a > 0.004:
        s = U.tag(text, bg=bg, font=font); draw(c, s, mat(x - (s.w * 0.5 if right else 0), y, 0, 0.5, 0.5, 0, 0), alpha=a)
def credit(c, text, a=1.0): tag(c, text, 28, H - 62, a)
def ill(c, a=1.0): tag(c, U.ILL_TXT, W - 28, 28, a, True, (120, 52, 18, 190))

def title(c, words, x, y, t0, t, font=U.F_MID, acc=OCHRE, gap=0.09, out_t=None):
    fade = 1 - smooth(seg(t, out_t, out_t + 0.35)) if out_t else 1.0
    xx = x
    for i, w in enumerate(words):
        u = e("text_rise", t, t0 + i * gap, t0 + i * gap + 0.55)
        if u > 0 and fade > 0:
            spr = U.word(w, font, acc if i == len(words) - 1 else INK); th = font.size * 1.35
            draw(c, spr, mat(xx - 12, y - 6 + (1 - u) * th * 0.55, 0, 0.5, 0.5, 0, 0), alpha=clamp(u * 1.6) * fade)
        xx += U.textlen(w + " ", font)

def arrow_draw(c, spr, tail, angle, length, u, a=1.0):
    """Arrow draws on from its tail along its own axis: an alpha front moves along the shaft (no stretching, no stepping)."""
    if u <= 0.004: return
    k = length / spr.w; m = mat(tail[0], tail[1], angle, k, k, 0, spr.h / 2)
    Mi = np.linalg.inv(np.vstack([m, [0, 0, 1]]))[:2]
    front = u * spr.w; soft = 0.06 * spr.w
    def inv(X, Y): return Mi[0, 0] * X + Mi[0, 1] * Y + Mi[0, 2], Mi[1, 0] * X + Mi[1, 1] * Y + Mi[1, 2]
    R = length * 1.1 + 40
    bb = (int(tail[0] - R), int(tail[1] - R), int(tail[0] + R), int(tail[1] + R))
    am = lambda Uu, Vv: np.clip((front - Uu) / soft, 0, 1)
    # soft shadow first
    draw(c, spr, np.array([[m[0, 0], m[0, 1], m[0, 2] + 6], [m[1, 0], m[1, 1], m[1, 2] + 9]]), alpha=0.0)
    draw_remap(c, spr, inv, bb, alpha=a, amask=am)

def pin_drop(c, spr, pt, t, t0, h=112):
    if t < t0: return
    f = e("light_drop", t, t0, t0 + 0.34); y = pt[1] - 230 * (1 - f); sx = sy = 1.0
    if t > t0 + 0.34:
        d = M.damped(t - t0 - 0.34, 3.2, 0.32); s = 1 + 0.16 * (1 - d); sx, sy = 2 - s if s > 1 else 1, s if s > 1 else 1
    k = h / spr.h
    draw(c, spr, mat(pt[0], y, 0, k * sx, k * sy, spr.w / 2, spr.h * 0.96), alpha=clamp(seg(t, t0, t0 + 0.12)), shadow=(4, 0.45), shoff=(6, 8))
    if t > t0 + 0.34:
        u = e("camera_settle", t, t0 + 0.34, t0 + 1.0); E.ring(c, pt[0], pt[1], 16 + 70 * u, 0.7 * (1 - u), OCHf, 3)

def measure_unfold(c, p1, p2, u, lift=58, h=100):
    if u <= 0.004: return
    ln = math.dist(p1, p2) * 0.9; nat = h * MEAS.w / MEAS.h; k = h / MEAS.h
    ang = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
    draw(c, MEAS, mat((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 - lift, ang, k * max(0.02, u) * ln / nat, k, MEAS.w / 2, MEAS.h / 2), alpha=clamp(u * 3), shadow=(3, 0.4), shoff=(5, 8))

def corridor_mask(cx, cy, vw, s0=0.0, s1=1.0, width_src=95, feather=0.55):
    if s1 <= s0 + 1e-3: return np.zeros((H, W), np.float32)
    s = W / vw; pts = [scr(tr_pt(lerp(s0, s1, i / 24)), cx, cy, vw) for i in range(25)]
    return E.corridor(pts, width_src * s, width_src * s * feather)

# ------------------------------------------------------------------ B01-B02  0 - 7.4
CAM_HOOK = E.Cam([(0.0, (2500, 3985, 1380)), (0.9, (2512, 3975, 1560)), (6.5, (2564, 3940, 1640)), (7.9, (2564, 3940, 2650))])
def sc_hook(t):
    cx, cy, vw = CAM_HOOK(t); c = DOC_M01.render(cx, cy, vw)
    if t < 3.0: m = corridor_mask(cx, cy, vw); amt = e("fade_soft", t, 0.25, 1.1)
    else: m = corridor_mask(cx, cy, vw, 0, lerp(0.03, 1, e("draw_on", t, 3.5, 5.7))); amt = 1.0
    amt *= 1 - e("fade_soft", t, 6.6, 7.3)
    c = E.spotlight(c, m, dim=lerp(1, 0.58, amt), lift=lerp(1, 1.26, amt))
    p1, p2 = scr(TRACK[0], cx, cy, vw), scr(TRACK[-1], cx, cy, vw)
    if t < 3.4:
        mid = scr(tr_pt(0.40), cx, cy, vw); ang = 32
        tail = (mid[0] - 330 * math.cos(math.radians(ang)), mid[1] + 330 * math.sin(math.radians(ang)) + 40)
        arrow_draw(c, ARR_O, tail, -ang, 300, e("draw_on", t, 0.85, 1.5) * (1 - e("fade_soft", t, 2.8, 3.3)))
    pin_drop(c, PIN_R, p1, t, 3.45); pin_drop(c, PIN_O, p2, t, 5.55)
    measure_unfold(c, p1, p2, e("unfold_rigid", t, 5.95, 6.75) * (1 - e("fade_soft", t, 6.7, 7.2)))
    if t < 3.05: title(c, ["NOT", "A", "ROAD."], 118, 140, 0.1, t, U.F_HOOK, out_t=2.75)
    else: title(c, ["NOT", "A", "RIVER."], 118, 140, 3.2, t, U.F_HOOK, out_t=6.5)
    if t > 3.4: ill(c, seg(t, 3.4, 3.8) * (1 - seg(t, 6.8, 7.2)))
    credit(c, U.C_EO1)
    return c

# ------------------------------------------------------------------ B03 7 - 12
M2CEN = (1500.0, 2250.0)
def modis_vw(t): return lerp(2950, 2700, e("camera_settle", t, 6.8, 8.2)) if t < 8.2 else lerp(2700, 2350, e("camera_glide", t, 8.2, 12.3))
def sc_modis(t, vw=None):
    vw = vw or modis_vw(t)
    b, a = DOC_B.render(*M2CEN, vw), DOC_A.render(*M2CEN, vw)
    f = e("terrain_wave", t, 7.75, 9.7)
    yy = np.arange(H, dtype=np.float32); X = np.arange(W, dtype=np.float32)[None, :]
    edge = lerp(-0.5, 1.1, f) * W + 0.62 * H * (1 - yy / H) + 34 * np.array([turb(v / H * 3 + t * 0.8, 7, 0.5) for v in yy[::6]]).repeat(6)[:H]
    mask = np.clip((edge[:, None] - X) / 28 + 0.5, 0, 1); mask = mask * mask * (3 - 2 * mask)
    c = b + (a - b) * mask[..., None]
    live = 1 - e("fade_soft", t, 9.5, 9.9)
    if live > 0 and f > 0:
        sm = cv2.resize(cv2.GaussianBlur(cv2.resize(mask, (W // 4, H // 4)), (0, 0), 20), (W, H))
        band = np.clip(sm - mask, 0, 1) * 2.0 * live; c = c * (1 - 0.5 * band[..., None])
        ed = np.clip(np.abs(cv2.GaussianBlur(mask, (0, 0), 4) - mask) * 2.6 * live, 0, 1)[..., None]; c = c + (np.array([1.0, 0.84, 0.59], np.float32) - c) * ed
    blink = (10.05 <= t < 10.3) or (10.6 <= t < 10.85)
    if t >= 9.7: c = b if blink else a
    day = (12 + int(round(16 * f))) if t < 9.9 else (12 if blink else 28)
    ta = seg(t, 7.3, 7.7)
    tag(c, f"APR {day}, 2011", 70, 70, ta, bg=(10, 18, 34, 190), font=U.F_DATE)
    tag(c, "BEFORE → AFTER" if t < 9.9 else ("BEFORE" if blink else "AFTER"), 70, 150, ta, bg=(120, 52, 18, 200) if (t < 9.9 or blink) else (32, 70, 110, 200))
    credit(c, C_MOD)
    return c

# ------------------------------------------------------------------ B04 12 - 18.3 (ground_v4) + tilt-up into orbit
G.CAM = E.Cam([(11.0, (0, 0, 1.0)), (13.2, (-6, -4, 1.018)), (14.9, (14, -2, 1.052)), (16.6, (30, -8, 1.07)), (17.3, (34, -10, 1.075)), (18.5, (34, -1000, 1.075))])
def sc_ground(t):
    c = G.scene(t)
    up = smooth(seg(t, 17.4, 18.5))
    if up > 0:
        c *= (1 - up); c += up * (np.array([6, 10, 22], np.float32) / 255); S.stars(c, t, (0, 0))
    if t > 12.4: ill(c, seg(t, 12.4, 12.8) * (1 - seg(t, 17.6, 18.0)))
    title(c, ["CARVED", "BY", "A", "TORNADO"], 640, 96, 15.55, t, out_t=17.2)
    return c

# ------------------------------------------------------------------ B05 18 - 24 (orbit scan + dive into the real swath)
def dive_cam(t):
    cs = S.CAMK(22.0); C = (W / 2, H / 2)
    cx0, cy0 = (C[0] + cs[0] - S.SX0) / S.FS, (C[1] + cs[1] - S.SY0) / S.FS; vw0 = W / (S.FS * cs[2])
    k = Hermite([(22.0, 0.0), (24.2, 1.0)])(t)
    return lerp(cx0, 2560, k), lerp(cy0, 3930, k), math.exp(lerp(math.log(vw0), math.log(1560), k))
def sc_orbit(t):
    if t < 22.0: return S.scene(t, credit=True)
    cx, cy, vw = dive_cam(t); c = DOC_M01.render(cx, cy, vw)
    k = e("fade_soft", t, 23.2, 24.0)
    if k > 0: c = E.spotlight(c, corridor_mask(cx, cy, vw), lerp(1, 0.6, k), lerp(1, 1.2, k))
    kd = W / (S.FS * vw); Vm = np.array([[kd, 0, W / 2 - kd * (S.SX0 + S.FS * cx)], [0, kd, H / 2 - kd * (S.SY0 + S.FS * cy)]], np.float64)
    S.overlays(c, t, Vm)
    credit(c, U.C_EO1)
    return c

# ------------------------------------------------------------------ B06 24 - 29.6 honest search lens
M2FULL = (2048.0, 1592.0)
def sc_search(t):
    if t < 24.9:
        k = e("camera_glide", t, 24.0, 24.9)
        a_ = DOC_M01.render(2560, 3930, lerp(1560, 3200, k)); b_ = DOC_A.render(*M2FULL, lerp(1800, 4000, k)); m = M.EASE["fade_soft"](k)
        c = a_ + (b_ - a_) * m; credit(c, U.C_EO1 if k < 0.5 else C_MOD); return c
    vw = lerp(4000, 3600, e("camera_glide", t, 24.9, 30))
    a, b = DOC_A.render(*M2FULL, vw), DOC_B.render(*M2FULL, vw); c = a * 0.8
    P = Hermite([(25.1, (420.0, 820.0)), (25.9, (780.0, 620.0), (0.0, 0.0)), (27.0, (780.0, 620.0), (0.0, 0.0)), (27.9, (1240.0, 440.0), (0.0, 0.0)),
                 (29.0, (1240.0, 440.0), (0.0, 0.0)), (29.8, (1580.0, 330.0))])
    x, y = P(t); r = 200 * e("camera_settle", t, 25.0, 25.6) * (1 - e("fade_soft", t, 29.4, 29.9))
    if r > 4:
        blink = (26.15 <= t < 26.45) or (26.7 <= t < 26.95) or (28.15 <= t < 28.45) or (28.7 <= t < 28.95)
        pad = r + 30; x0, y0, x1, y1 = int(max(0, x - pad)), int(max(0, y - pad)), int(min(W, x + pad)), int(min(H, y + pad))
        X, Y = np.meshgrid(np.arange(x0, x1, dtype=np.float32) + 0.5, np.arange(y0, y1, dtype=np.float32) + 0.5); d = np.hypot(X - x, Y - y)
        m = np.clip(r - d + 0.5, 0, 1)[..., None]; roi = c[y0:y1, x0:x1]; roi += ((b if blink else a)[y0:y1, x0:x1] - roi) * m
        sh = np.clip(7 - np.abs(d - (r + 6)) + 0.5, 0, 1)[..., None] * 0.47; roi *= (1 - sh) * 1.0
        E.ring(c, x, y, r, 1.0, OCHf, 5); tag(c, "APR 12" if blink else "APR 28", x - 46, y + r + 18, 1.0, bg=(120, 52, 18, 210) if blink else (32, 70, 110, 210))
    title(c, ["NOT", "THE", "ONLY", "LINE"], 118, 110, 24.4, t, out_t=29.3)
    tag(c, "Lens compares the same NASA frame: Apr 28 vs Apr 12. Track positions not annotated.", 28, H - 116, seg(t, 25.3, 25.8))
    credit(c, C_MOD)
    return c

# ------------------------------------------------------------------ B07-B08 29.6 - 46.4 GOES storm
_U = json.load(open("/home/claude/ep009/m3_unique.json"))["unique"]; _UN = len(_U)
UPS = _UN / (590 * 1001 / 30000)                         # unique real frames per second of source time
_cen = [c for c in json.load(open("/home/claude/ep009/m3_centroids.json")) if c[1] is not None]
CEN_X = Hermite([(c[0] * 1001 / 30000, c[1]) for c in _cen[::4]]); CEN_Y = Hermite([(c[0] * 1001 / 30000, c[2]) for c in _cen[::4]])
_fc = {}
def goes(ts):
    """Real GOES frames. The clip repeats ~half its frames at irregular gaps, so we sample UNIQUE frames at an even cadence and
    blend only the two real neighbours (no flow, no synthesised content)."""
    u = clamp(ts * UPS, 0, _UN - 1.001); i = int(u); f = u - i
    def L(k):
        if k not in _fc:
            if len(_fc) > 6: _fc.pop(next(iter(_fc)))
            _fc[k] = cv2.cvtColor(cv2.imread(f"/home/claude/ep009/m3/f{_U[k] + 1:04d}.jpg"), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
        return _fc[k]
    return L(i) if f < 1e-3 else L(i) * (1 - f) + L(i + 1) * f

def goes_cam(img, fx, fy, z):
    """Zoom z about the point (fx, fy) given in screen px, float affine."""
    m = np.array([[z, 0, fx - z * fx], [0, z, fy - z * fy]], np.float64)
    return cv2.warpAffine(img, m, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

CAM_S = E.Cam([(29.6, (0, 0, 1.0)), (30.6, (0, 0, 1.0)), (36.6, (1, 1, 1.20)), (38.0, (1, 1, 1.20)), (40.2, (0, 0, 1.0))])
THUNDER = [(32.1, 1.0), (33.85, 0.7), (35.25, 1.0), (36.55, 0.6)]
_ST = G._ST
SCUD = Sprite(G._clean(_ST).crop((int(_ST.width * 0.55), int(_ST.height * 0.55), _ST.width, _ST.height)), ref_h=420)
def sc_storm(t):
    ts = t - 30.0; _, _, z = CAM_S(t); follow = clamp((z - 1) / 0.2)
    ccx, ccy = CEN_X(ts), CEN_Y(ts)
    fx, fy = lerp(W / 2, ccx, 0.55 * follow), lerp(H / 2, ccy, 0.55 * follow)
    if t < 30.4:
        k = e("fade_soft", t, 29.6, 30.4); g = goes(0); mod = DOC_A.render(*M2FULL, 4000); ms = lerp(1.0, 0.55, k)
        m = np.array([[ms, 0, (W - W * ms) / 2], [0, ms, (H - H * ms) / 2]], np.float64)
        small = cv2.warpAffine(mod, m, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
        sm = cv2.warpAffine(np.ones((H, W), np.float32), m, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)[..., None]
        bg = g * (1 - sm) + small * sm; kk = M.EASE["fade_soft"]
        c = mod + (bg - mod) * kk(clamp(k * 2)) if k < 0.5 else bg + (g - bg) * kk((k - 0.5) * 2)
    else:
        c = goes_cam(goes(ts), fx, fy, z)
    pcx, pcy = fx + z * (ccx - fx), fy + z * (ccy - fy)
    bolt = 0.0
    for tb, s in THUNDER:
        if tb <= t < tb + 0.26: bolt = max(bolt, s * (1 - (t - tb) / 0.26) ** 1.6)
    grow = e("camera_settle", t, 30.9, 33.2); leave = e("fade_soft", t, 37.0, 38.4)
    if grow > 0 and t < 38.4:
        hz = lerp(0.9, 0.12, grow) + 0.6 * leave
        G.storm_draw(c, t, lerp(300, 420, grow), (pcx - 150 + 260 * leave, pcy - 70 - lerp(40, 0, grow) - 50 * leave), min(hz, 1.0), 0.95, bolt * (1 - leave), t - 30.9)
        # (alpha envelope for the whole painted storm is applied by blending against the plain GOES view)
        al = clamp(grow * 1.3) * (1 - leave)
        tag(c, "Illustration, not the observed storm cell", pcx - 350, pcy + 140, clamp(grow * 1.6) * (1 - leave))
        sk = e("fade_soft", t, 33.6, 34.4) * (1 - e("fade_soft", t, 36.8, 37.6))
        if sk > 0:
            kk2 = 1.9 * 420 / SCUD.h * 0 + 1.9 * (SCUD.h and 1)
            draw(c, SCUD, mat(lerp(-200, W + 300, seg(t, 33.4, 37.8)), 840, 0, 1.9 * 420 / 420, 1.9 * 420 / 420, SCUD.w / 2, SCUD.h / 2), alpha=0.42 * sk)
    if t < 38: title(c, ["APRIL", "2011"], 118, 110, 30.35, t, out_t=37.6)
    if t >= 38:
        u = M.EASE["orbit"](seg(t, 38.1, 43.6)); sx, sy = lerp(-160, 760, u), 210 - 70 * math.sin(math.pi * u)
        a = e("fade_soft", t, 38.1, 38.7) * (1 - e("fade_soft", t, 43.0, 43.5)); lock = e("draw_on", t, 40.1, 40.8) * (1 - e("fade_soft", t, 42.9, 43.4))
        if lock > 0:
            for ex in (pcx - 80, pcx + 80): E.aa_line(c, (sx + 30, sy + 60), (lerp(sx + 30, ex, lock), lerp(sy + 60, pcy, lock)), (1.0, 0.93, 0.75), 0.6, 2)
            E.ring(c, pcx, pcy, 80, 0.85 * lock, OCHf, 3)
        k = 180.0 / S.SAT.h
        draw(c, S.SAT, mat(sx, sy, -5 + 4 * math.sin(t * 0.7), k * (0.94 + 0.06 * math.cos(t * 0.5)), k, S.SAT.w / 2, S.SAT.h / 2), alpha=a, shadow=(5, 0.3), shoff=(8, 10))
        au = e("draw_on", t, 40.85, 41.5) * (1 - e("fade_soft", t, 42.9, 43.4))
        arrow_draw(c, ARR_W, (pcx - 470, pcy + 150), 18, 330, au)
        tag(c, "STORMS · APR 27, 2011", pcx - 520, pcy + 190, au); ill(c, a)
    roll = e("terrain_wave", t, 43.2, 45.0)
    if roll > 0:
        after = DOC_A.render(*M2FULL, lerp(4000, 3600, seg(t, 43.2, 47)))
        xw = lerp(-500, W + 500, roll); X = np.arange(W, dtype=np.float32)[None, :]; Y = np.arange(H, dtype=np.float32)[:, None]
        edge = xw + 220 - 440 * Y / H; m = np.clip((edge - X) / 120 + 0.5, 0, 1); m = (m * m * (3 - 2 * m))[..., None]
        c = c + (after - c) * m
        if roll < 1:
            G.storm_draw(c, t, 760, (xw + 160, H * 0.48), 0.05, 0.9, 0.0, roll * 0.0 + (t - 43.2) * 0.2)
        if t > 44.9: tag(c, "AFTERMATH · APR 28, 2011", 70, 70, seg(t, 44.9, 45.4), bg=(10, 18, 34, 190), font=U.F_DATE)
    credit(c, C_GOES if t < 44.3 else C_MOD)
    return c

# ------------------------------------------------------------------ B09 46.4 - 56 scale reveal
CAM_E = E.Cam([(46.4, (2560, 3930, 3000)), (47.6, (2560, 3930, 1560)), (53.2, (2540, 3925, 1600)), (56.0, (2330, 3890, 2300))])
T_BSWAP = 49.55
def sc_scale(t):
    cx, cy, vw = CAM_E(t); c = DOC_M01.render(cx, cy, vw)
    if t < 47.3:
        k = e("fade_soft", t, 46.4, 47.3); c = DOC_A.render(*M2FULL, lerp(3600, 2600, k)) * (1 - k) + c * k
    c = E.spotlight(c, corridor_mask(cx, cy, vw), 0.58, 1.18)
    mid = scr(tr_pt(0.5), cx, cy, vw)
    rise = e("camera_settle", t, 47.5, 48.8); sink = e("heavy_fall", t, 52.2, 53.0); k = rise * (1 - sink)
    if k > 0.01:
        bx, by = lerp(mid[0], 960, k), lerp(mid[1], 640, k); bh = 560 * k; yaw = 2.0 * math.sin((t - 47.5) * 0.7)
        spr, kk = (G.LAND_SC, 0.98) if t >= T_BSWAP else (G.LAND, 1.0); s = bh * kk / spr.h
        draw(c, spr, mat(bx, by, yaw, s, s, spr.w / 2, spr.h / 2), alpha=clamp(k * 1.5), shadow=(8, 0.55), shoff=(0.05 * bh, 0.11 * bh))
        cov = smooth(seg(t, T_BSWAP - 0.55, T_BSWAP - 0.05)) * (1 - smooth(seg(t, T_BSWAP + 0.08, T_BSWAP + 1.3)))
        if cov > 0.004:
            for i in range(10):    # dust front rolls along the swath direction and covers the whole block while the state changes
                gx, gy = (i % 5 - 2) * bh * 0.30, (i // 5 - 0.5) * bh * 0.42
                r = bh * (0.32 + 0.08 * M.h01(i + 400))
                draw(c, G.DUST, mat(bx + gx + 20 * (t - T_BSWAP), by + gy - 0.05 * bh, 0, r * 2 / G.DUST.w, r * 1.6 / G.DUST.h, G.DUST.w / 2, G.DUST.h / 2), alpha=min(1.0, 1.15 * cov))
        for i, cl in enumerate(G.CLODS[:9]):
            t0 = T_BSWAP + 0.15 + 0.9 * M.h01(i + 70)
            if t > t0:
                dt = t - t0; x = bx - bh * 0.5 + bh * 1.0 * M.h01(i + 71) + 60 * dt; y = by - bh * 0.25 - 180 * dt + 420 * dt * dt
                if dt < 0.9: sz = (16 + 10 * M.h01(i)) / cl.h; draw(c, cl, mat(x, y, dt * 260, sz, sz, cl.w / 2, cl.h / 2), alpha=1 - seg(dt, 0.6, 0.9), shadow=(2, 0.25), shoff=(3, 4))
        dmg = smooth(seg(t, T_BSWAP, T_BSWAP + 0.3))
        tag(c, "INTACT", bx - bh * 0.6, by + bh * 0.45, clamp(k * 2) * (1 - dmg)); tag(c, "DAMAGE CORRIDOR", bx - bh * 0.3, by + bh * 0.45, clamp(k * 2) * dmg); ill(c, clamp(k * 2))
    if t > 53.0:
        u = e("camera_settle", t, 53.0, 54.2); E.ring(c, mid[0], mid[1], 30 + 150 * u, 0.6 * (1 - u), OCHf, 3)
    p1, p2 = scr(TRACK[0], cx, cy, vw), scr(TRACK[-1], cx, cy, vw)
    pin_drop(c, PIN_R, p1, t, 53.6, 92); pin_drop(c, PIN_O, p2, t, 53.95, 92)
    mu = e("unfold_rigid", t, 54.25, 55.0)
    if mu > 0: measure_unfold(c, p1, p2, mu, 48, 86); ill(c, clamp(mu * 3))
    title(c, ["THE", "SCALE", "OF", "DESTRUCTION"], 118, 110, 54.3, t)
    credit(c, U.C_EO1)
    return c

# ------------------------------------------------------------------ dispatcher (overlaps are scale-continuous dissolves / focus pulls)
def mixc(a, b, k): return a + (b - a) * k
def scene(t):
    if t < 7.0: return sc_hook(t)
    if t < 7.6: return mixc(sc_hook(t), sc_modis(t), e("fade_soft", t, 7.0, 7.6))
    if t < 11.6: return sc_modis(t)
    if t < 12.4:
        k = e("fade_soft", t, 11.6, 12.4); g = sc_ground(t); m = sc_modis(t, vw=modis_vw(min(t, 12.3)))
        return mixc(E.blur(m, 10 * k), E.blur(g, 10 * (1 - k)), k)
    if t < 18.0: return sc_ground(t)
    if t < 18.5: return mixc(sc_ground(t), sc_orbit(t), e("fade_soft", t, 18.0, 18.5))
    if t < 24.0: return sc_orbit(t)
    if t < 29.6: return sc_search(t)
    if t < 46.4: return sc_storm(t)
    return sc_scale(t)

def probe(t):
    out = {}
    cx, cy, vw = CAM_HOOK(t); out["hook_cam"] = dict(x=cx, y=cy, vw=vw)
    cx, cy, vw = CAM_E(t); out["scale_cam"] = dict(x=cx, y=cy, vw=vw)
    cx, cy, z = G.CAM(t); out["ground_cam"] = dict(x=cx, y=cy, z=z)
    out["modis_cam"] = dict(vw=modis_vw(t))
    return out
