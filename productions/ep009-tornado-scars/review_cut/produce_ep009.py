#!/usr/bin/env python3
"""EP009 REVIEW CUT producer (Long 1920x1080 + Shorts 1080x1920). Temporary local voice. Real NASA/NOAA pixels + supplied painted illustrations.
usage: produce_ep009.py long  OUT.mp4 t0 t1   |  produce_ep009.py s1|s2 OUT.mp4 t0 t1   |  thumb"""
import sys, os, math, json, re, subprocess
sys.path.insert(0, "/home/claude/ep009")
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import engine as E
from engine import clamp, seg, lerp, smooth
MODE = sys.argv[1]
SHORT = MODE in ("s1", "s2")
if SHORT: E.W, E.H = 1080, 1920
W, H = E.W, E.H
import ui_v4 as U
REPO = "/home/claude/skychwdkh5-design/youtube-agent/productions/ep009-tornado-scars"; MO = f"{REPO}/media_original"; AS = "/home/claude/ep009/assets_zip/assets"
P = "/home/claude/ep009/prod"; FI = "/usr/share/fonts/opentype/inter/"
INK, OCH = (244, 238, 226), (232, 176, 84); OCHf = np.array(OCH, np.float32) / 255
C_EO1 = "NASA EO-1 ALI · May 2, 2011 · NASA Earth Observatory"
C_MB = "NASA MODIS · Apr 12, 2011 · NASA Earth Observatory"; C_MA = "NASA MODIS · Apr 28, 2011 · NASA Earth Observatory"
C_GOES = "NOAA NESDIS · GOES-13 · April 2011"
def rd(p): return Image.fromarray(cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB))
_docs = {}
def doc(n):
    if n not in _docs: _docs[n] = E.Doc(rd(f"{MO}/{ {'eo':'nasa_tuscaloosa_EO1_20110502','mb':'nasa_modis_before_20110412','ma':'nasa_modis_after_20110428','as':'nasa_aster_birmingham_20110504','lc':'usgs_lcmap_landcover_change_2011'}[n] }.jpg"))
    return _docs[n]
TRACK = [(2024, 4248), (2420, 4014), (2780, 3798), (3104, 3618)]
TRL = sum(math.dist(a, b) for a, b in zip(TRACK, TRACK[1:]))
def tr_pt(s):
    d = clamp(s) * TRL
    for a, b in zip(TRACK, TRACK[1:]):
        l = math.dist(a, b)
        if d <= l: return (lerp(a[0], b[0], d / l), lerp(a[1], b[1], d / l))
        d -= l
    return TRACK[-1]
def scr(pt, cx, cy, vw): s = W / vw; return (W / 2 + (pt[0] - cx) * s, H / 2 + (pt[1] - cy) * s)
def cmask(cx, cy, vw, s0=0.0, s1=1.0, wsrc=95, f=0.55):
    if s1 <= s0 + 1e-3: return np.zeros((H, W), np.float32)
    s = W / vw; return E.corridor([scr(tr_pt(lerp(s0, s1, i / 24)), cx, cy, vw) for i in range(25)], wsrc * s, wsrc * s * f)
def render_doc(n, cx, cy, vw): return doc(n).render(cx, cy, vw, size=(W, H))
# ---------- text / ui
F = lambda n, s: ImageFont.truetype(FI + n, s)
def txt(c, text, x, y, size=44, a=1.0, col=INK, anchor="l", wt="Inter-Bold.otf", dy=0.0, shadow=True):
    if a <= 0.004: return
    key = (text, size, col, wt)
    if key not in _tc:
        f = F(wt, size * 2); d = ImageDraw.Draw(Image.new("RGBA", (4, 4))); l, t, r, b = d.textbbox((0, 0), text, font=f)
        w, h = r - l + 80, b - t + 80; im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((40 - l + 3, 40 - t + 6), text, font=f, fill=(0, 0, 0, 170))
        from PIL import ImageFilter
        sh = sh.filter(ImageFilter.GaussianBlur(7)); ImageDraw.Draw(im).text((40 - l, 40 - t), text, font=f, fill=col + (255,)); sh.alpha_composite(im)
        _tc[key] = E.Sprite(sh)
    s = _tc[key]; k = 0.5; w = s.w * k
    px = x - w / 2 + 20 if anchor == "c" else (x - w + 40 if anchor == "r" else x - 20)
    E.draw(c, s, E.mat(px, y - 20 + dy, 0, k, k, 0, 0), alpha=a)
_tc = {}
def tag(c, text, x, y, a=1.0, right=False, ill=False): U.put_tag(c, text, x, y, right, a, (120, 52, 18, 200) if ill else (10, 18, 34, 175))
def credit(c, text, a=1.0): tag(c, text, 28, H - (150 if SHORT else 62) , a) if not SHORT else tag(c, text, 28, H - 330, a)
def ILL(c, a=1.0): tag(c, U.ILL_TXT, W - 28, 28, a, True, True)
def e_(name, t, a, b): import motion as M; return M.ease(name, t, a, b)
def fade(t, a, b, c_, d): return smooth(seg(t, a, b)) * (1 - smooth(seg(t, c_, d)))
def placeholder_note(c, a=1.0): tag(c, "REVIEW CUT PLACEHOLDER · source image pending download", W - 28, H - 250 if not SHORT else 70, a, True, True)
# ---------- captions
def load_srt(p):
    out = []
    for blk in open(p).read().strip().split("\n\n"):
        L = blk.split("\n"); m = re.match(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", L[1])
        g = list(map(int, m.groups())); out.append((g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000, L[2:]))
    return out
CAPF = F("Inter-SemiBold.otf", 44 if not SHORT else 52)
CAPGATE = lambda t: 1.0
def captions(c, t, srt):
    for a, b, lines in srt:
        if a - 0.05 <= t <= b + 0.1:
            u = clamp(seg(t, a - 0.05, a + 0.1) * (1 - seg(t, b, b + 0.1))) * CAPGATE(t)
            base = H - (118 if not SHORT else 360)
            for k, ln in enumerate(lines):
                y = base + (k - (len(lines) - 1)) * (60 if not SHORT else 56)
                txt(c, ln, W / 2, y, 44 if not SHORT else 38, u, INK, "c", "Inter-SemiBold.otf")
            return
# ---------- GOES
UNI = json.load(open("/home/claude/ep009/m3_unique.json"))["unique"]; _fc = {}
def gframe(k):
    k = k % len(UNI)
    if k not in _fc:
        if len(_fc) > 24: _fc.pop(next(iter(_fc)))
        _fc[k] = cv2.cvtColor(cv2.imread(f"/home/claude/ep009/m3/f{UNI[k] + 1:04d}.jpg"), cv2.COLOR_BGR2RGB)
    return _fc[k]
def goes(t, rate, cx, cy, vw, size=None):
    """source cadence: unique real frames only; blend between two real neighbours; loops with crossfade handled by caller."""
    pos = (t * rate) % len(UNI); i = int(pos); fr = pos - i; sw, sh = size or (W, H); s = vw / sw
    m = np.array([[s, 0, cx - s * sw / 2], [0, s, cy - s * sh / 2]], np.float64)
    def v(k): return cv2.warpAffine(gframe(k), m, (sw, sh), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE).astype(np.float32) / 255
    a = v(i); return a if fr < 1e-3 else a * (1 - fr) + v(i + 1) * fr
def lin(t, pts): return E.Hermite([(a, b) for a, b in pts])(t)
def illus(n): return Image.open(f"{AS}/{n}.png").convert("RGBA")
_il = {}
def ill_bg(n, cx, cy, zoom, rot=0.0):
    if n not in _il: _il[n] = E.Sprite(illus(n))
    s = _il[n]; k = max(W / s.w, H / s.h) * zoom
    c = np.zeros((H, W, 3), np.float32); E.draw(c, s, E.mat(W / 2, H / 2, rot, k, k, cx * s.w, cy * s.h)); return c
def grad(c0, c1):
    g = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]; return np.asarray(c0, np.float32) / 255 * (1 - g) + np.asarray(c1, np.float32) / 255 * g + np.zeros((H, W, 3), np.float32)
def chip(c, label, x, y, a, hot=0.0, w=330, h=110):
    if a <= 0.004: return
    cc = c[int(y):int(y + h), int(x):int(x + w)]; cc *= (1 - 0.55 * a); cc += a * (np.array([0.06, 0.1, 0.17]) * (1 - hot) + np.array([0.55, 0.32, 0.08]) * hot) * 0.85
    txt(c, label, x + w / 2, y + 22, 50, a, INK, "c", "Inter-ExtraBold.otf")
T = lambda c: json.load(open(f"{P}/{c}/timeline.json"))
# ======================================================================= LONG
if MODE == "long":
    TL = T("long"); CU = [c["start"] for c in TL["cues"]]; END = TL["duration"]; SRT = load_srt(f"{P}/long/captions.srt")
    def hook_eo(t):                      # 0 - 28.7  EO-1 real image, corridor, then Apr12/28 comparison, then multiple scars
        if True:
            cam = E.Cam([(0, (2500, 3985, 1380)), (CU[1], (2512, 3975, 1560)), (CU[3], (2540, 3950, 1620)), (CU[4], (2800, 3790, 2300)), (CU[5], (2300, 3520, 4300))])
            cx, cy, vw = cam(t); c = render_doc("eo", cx, cy, vw)
            if t < CU[3]: m = cmask(cx, cy, vw); amt = e_("fade_soft", t, 0.25, 1.1)
            else: m = cmask(cx, cy, vw, 0, lerp(0.03, 1, e_("draw_on", t, CU[3] + 0.4, CU[3] + 4.5))); amt = 1.0
            bump = smooth(seg(t, CU[3] - 0.4, CU[3])) * (1 - smooth(seg(t, CU[3], CU[3] + 0.3))) if t < CU[3] + 0.3 else 0.0
            amt = amt * (1 - bump) if t >= CU[3] - 0.4 else amt; amt = amt if t < CU[3] else amt * smooth(seg(t, CU[3], CU[3] + 0.4))
            c = E.spotlight(c, m, lerp(1, 0.62, amt), lerp(1, 1.2, amt))
            txt(c, "THIS ISN'T A ROAD.", 120, 140, 100, fade(t, 0.2, 0.6, CU[1] - 0.2, CU[1] + 0.1), INK, "l", "Inter-Black.otf")
            txt(c, "NOR A RIVER.", 120, 140, 100, fade(t, CU[1], CU[1] + 0.35, CU[2] - 0.1, CU[2] + 0.2), OCH, "l", "Inter-Black.otf")
            txt(c, "IT WASN'T THERE BEFORE THE STORM.", 120, 140, 66, fade(t, CU[2] + 0.1, CU[2] + 0.5, CU[3] - 0.3, CU[3] + 0.1), INK, "l", "Inter-Black.otf")
            txt(c, "CARVED BY A TORNADO", 120, 140, 74, fade(t, CU[3] + 0.3, CU[3] + 0.8, CU[4] - 0.3, CU[4] + 0.1), OCH, "l", "Inter-Black.otf")
            txt(c, "MAY 2, 2011 · FROM SPACE", 120, 140, 66, fade(t, CU[4] + 0.2, CU[4] + 0.7, CU[5] - 0.4, CU[5] - 0.1), INK, "l", "Inter-Black.otf")
            credit(c, C_EO1, smooth(seg(t, 0.8, 1.4))); return c
    def hook_ma(t):
        u = max(0.0, t - CU[5]); cam = E.Cam([(0, (2300, 1750, 3800)), (CU[7] - CU[5], (2100, 1700, 3100))]); cx, cy, vw = cam(u)
        c = render_doc("ma", cx, cy, vw); w = smooth(seg(t, CU[5] + 0.4, CU[5] + 1.6)) ; txt(c, "MANY LINES · APRIL 2011", 120, 140, 74, fade(t, CU[5] + 0.3, CU[5] + 0.9, CU[7] - 0.4, CU[7]), INK, "l", "Inter-Black.otf")
        credit(c, C_MA, w); return c
    TH_PATH = f"{REPO}/review_cut/thumbnail/OA_EP009_thumbnail_SCAR_FROM_SPACE_original.png"; _th = {}
    CAPGATE = lambda t: smooth(seg(t, 1.0, 1.3))
    C_AS = "NASA Earth Observatory · ASTER (Terra) · May 4, 2011 · FALSE COLOR · J. Allen; data NASA/GSFC/METI/ERSDAC/JAROS, U.S./Japan ASTER Science Team"
    def hook_open(t):
        if "t" not in _th:
            im = cv2.cvtColor(cv2.imread(TH_PATH), cv2.COLOR_BGR2RGB); im = cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC); _th["t"] = im.astype(np.float32) / 255
        TH = _th["t"]
        if t < 1.0: c = TH.copy()
        elif t < 2.0: w = smooth(seg(t, 1.0, 2.0)); c = E.blur(TH, 1.0 + 28 * w) * (1 - 0.45 * w)
        else: c = E.blur(TH, 29.0) * 0.55
        cam = E.Cam([(2.0, (2560, 3350, 3100)), (6.0, (2560, 3350, 2500))]); cx, cy, vw = cam(max(2.0, t))
        if t >= 2.0:
            u = smooth(seg(t, 2.0, 3.0)); A = render_doc("as", cx, cy, vw)
            ASTR = [(1230, 4030), (1980, 3720), (2730, 3280), (3550, 2700)]; sc_ = W / vw
            m = E.corridor([(W / 2 + (x - cx) * sc_, H / 2 + (y - cy) * sc_) for x, y in ASTR], 85 * sc_, 85 * sc_ * 0.6); k = smooth(seg(t, 3.0, 3.9))
            A = E.spotlight(A, m, lerp(1, 0.62, k), 1.0); A = E.blur(A, 16.0 * (1 - u)); c = c * (1 - u) + A * u
        tag(c, "STYLIZED ILLUSTRATION", W - 28, 28, (1 - smooth(seg(t, 1.2, 2.2))) , True, True)
        tag(c, "NASA SATELLITE IMAGE · ASTER (TERRA) · FALSE COLOR", 28, 28, smooth(seg(t, 2.5, 3.1)) * (1 - smooth(seg(t, 5.2, 5.7))))
        credit(c, C_AS, smooth(seg(t, 2.7, 3.3)) * (1 - smooth(seg(t, 5.2, 5.7)))); return c
    def sc_hook(t):
        if t < 5.2: return hook_open(t)
        if t < 5.9: w = smooth(seg(t, 5.2, 5.9)); return hook_open(t) * (1 - w) + hook_eo(t) * w
        if t < CU[5] - 0.6: return hook_eo(t)
        if t < CU[5] - 0.1: w = smooth(seg(t, CU[5] - 0.6, CU[5] - 0.1)); return hook_eo(CU[5] - 0.61) * (1 - w) + hook_ma(t) * w
        return hook_ma(t)
    def goes_scene(t, t0, t1, rate, cam, label=None, lab_t=None):
        cx, cy, vw = cam(t - t0); c = goes(t - t0, rate, cx, cy, vw); c = c * 0.92
        credit(c, C_GOES, smooth(seg(t, t0 + 0.6, t0 + 1.2)));
        tag(c, "Weather-satellite view: cloud systems, not individual funnels", W - 28, 28, smooth(seg(t, t0 + 1, t0 + 1.6)), True); return c
    def sc_promise(t):
        c = goes_scene(t, CU[7], CU[9], 3.2, E.Cam([(0, (700, 380, 900)), (CU[9] - CU[7], (760, 330, 700))]))
        txt(c, "FOLLOW THE SATELLITE EVIDENCE", 120, 150, 70, fade(t, CU[7] + 0.4, CU[7] + 0.9, CU[8] - 0.2, CU[8] + 0.2), INK, "l", "Inter-Black.otf")
        txt(c, "CLOUDS BEFORE  →  SCARS AFTER", 120, 150, 70, fade(t, CU[8] + 0.2, CU[8] + 0.7, CU[9] - 0.5, CU[9] - 0.1), OCH, "l", "Inter-Black.otf"); return c
    def sc_context(t):
        z = 1.05 + 0.05 * seg(t, CU[9], CU[14]); c = ill_bg("P02_storm", 0.5, 0.5, z) * 0.7; c = c + 0.0
        ILL(c, 1); u = lambda a: smooth(seg(t, a, a + 0.5))
        days = ["APR 25", "APR 26", "APR 27", "APR 28"]; s0 = CU[9] + 3.0
        for i, d in enumerate(days): chip(c, d, 300 + i * 360, 190, u(s0 + i * 1.5), hot=smooth(seg(t, s0 + i * 1.5 + 1.0, s0 + i * 1.5 + 1.4)) * (1 if i == 2 else 0.5))
        txt(c, "OUTBREAK · APRIL 25–28, 2011", W / 2, 120, 50, u(CU[9] + 0.3), INK, "c", "Inter-ExtraBold.otf")
        kk = 1 - smooth(seg(t, CU[12] - 0.3, CU[12] + 0.5)); u0 = u; u = lambda a: u0(a) * kk
        n1 = int(362 * e_("camera_settle", t, CU[10] + 0.5, CU[10] + 3.2)); n2 = int(321 * e_("camera_settle", t, CU[11] + 0.3, CU[11] + 2.6))
        if t > CU[10] + 0.3: txt(c, f"{n1}", 560, 470, 190, u(CU[10] + 0.3), INK, "c", "Inter-Black.otf"); txt(c, "CONFIRMED TORNADOES", 560, 690, 38, u(CU[10] + 0.6), OCH, "c", "Inter-ExtraBold.otf")
        if t > CU[11] + 0.3: txt(c, f"{n2}", 1360, 470, 190, u(CU[11] + 0.3), INK, "c", "Inter-Black.otf"); txt(c, "ESTIMATED DEATHS", 1360, 690, 38, u(CU[11] + 0.6), OCH, "c", "Inter-ExtraBold.otf")
        if t > CU[10] + 0.3: tag(c, "Source: NOAA NCEI retrospective count", W / 2 - 230, 800, u(CU[10] + 1.5))
        k = smooth(seg(t, CU[12], CU[12] + 1.0)); c *= (1 - 0.45 * k)
        txt(c, "A HUMAN DISASTER, NOT A SPECTACLE", W / 2, 470, 58, fade(t, CU[12] + 0.5, CU[12] + 1.1, CU[14] - 0.5, CU[14] - 0.1), INK, "c", "Inter-Black.otf"); return c
    def sc_storms(t):
        cams = E.Cam([(CU[14], (640, 360, 1100)), (CU[16], (560, 300, 760)), (CU[18], (700, 340, 900)), (CU[19] + 2, (820, 300, 640)), (CU[21], (650, 380, 1000)), (CU[22], (640, 360, 1280))])
        cx, cy, vw = cams(t); c = goes(t - CU[14], 3.2, cx, cy, vw) * 0.92
        credit(c, C_GOES, smooth(seg(t, CU[14] + 0.5, CU[14] + 1.2)))
        tag(c, "Funnels are too small to see at this scale · the satellite records the cloud systems", W - 28, 28, smooth(seg(t, CU[16] + 0.3, CU[16] + 1.0)) * (1 - smooth(seg(t, CU[18], CU[18] + 0.5))), True)
        txt(c, "CLOUD TOWERS", 120, 150, 70, fade(t, CU[18] + 0.2, CU[18] + 0.7, CU[19] + 2.5, CU[19] + 3.0), OCH, "l", "Inter-Black.otf")
        txt(c, "HOURS · MANY STATES", 120, 150, 70, fade(t, CU[20] + 0.3, CU[20] + 0.8, CU[21] + 2.5, CU[21] + 3.0), INK, "l", "Inter-Black.otf"); return c
    def sc_ba(t):
        cam = E.Cam([(CU[22], (2200, 1700, 4096)), (CU[23] + 2, (2200, 1700, 3800)), (CU[27], (2100, 1750, 3300)), (CU[31] + 3, (2120, 1760, 2400)), (CU[32] + 0.5, (2140, 1770, 2250))]); cx, cy, vw = cam(t)
        b, a = render_doc("mb", cx, cy, vw), render_doc("ma", cx, cy, vw)
        w = smooth(seg(t, CU[27] + 0.3, CU[27] + 3.4)); xw = W * 1.06 * w - 0.03 * W; soft = 70
        X = np.arange(W, dtype=np.float32)[None, :, None]; m = np.clip((xw - X) / soft + 0.5, 0, 1)
        c = a * m + b * (1 - m)
        for s in (-1, 1): pass
        la = smooth(seg(t, CU[27] + 0.4, CU[27] + 1.2))
        txt(c, "APRIL 12 · BEFORE", 120, 120, 62, fade(t, CU[23] + 0.3, CU[23] + 0.9, CU[27] + 2.0, CU[27] + 2.6), INK, "l", "Inter-Black.otf")
        txt(c, "APRIL 28 · AFTER", 120, 120, 62, smooth(seg(t, CU[27] + 2.6, CU[27] + 3.2)), OCH, "l", "Inter-Black.otf")
        credit(c, C_MB if w < 0.5 else C_MA, smooth(seg(t, CU[22] + 1, CU[22] + 1.6)))
        txt(c, "NOT CLOUDS · EXPOSED, DISTURBED GROUND", 120, 190, 44, fade(t, CU[29] + 0.3, CU[29] + 0.8, CU[30] + 3.0, CU[30] + 3.5), INK, "l", "Inter-ExtraBold.otf"); return c
    def sc_tusc(t):
        s0, s1 = CU[32], CU[47]
        cam = E.Cam([(s0, (2048, 3000, 5400)), (CU[33], (2300, 3800, 3600)), (CU[35], (2564, 3950, 2400)), (CU[38], (2564, 3940, 2000)), (CU[38] + 3, (2700, 3880, 1250)), (CU[42], (2600, 3900, 1700)), (CU[45] + 2, (2700, 3860, 1500)), (s1, (2700, 3860, 1600))]); cx, cy, vw = cam(t)
        c = render_doc("eo", cx, cy, vw); k = smooth(seg(t, CU[34] - 0.3, CU[34] + 1.2)) * (1 - 0.25 * smooth(seg(t, CU[42], CU[42] + 1.0)))
        m = cmask(cx, cy, vw, 0, lerp(0.03, 1, e_("draw_on", t, CU[34] + 0.2, CU[34] + 3.6))); c = E.spotlight(c, m, lerp(1, 0.6, k), lerp(1, 1.2, k))
        p1, p2 = scr(TRACK[0], cx, cy, vw), scr(TRACK[-1], cx, cy, vw)
        txt(c, "TUSCALOOSA, ALABAMA", 120, 120, 60, fade(t, CU[32] + 0.2, CU[32] + 0.8, CU[34] - 0.2, CU[34] + 0.2), INK, "l", "Inter-Black.otf")
        txt(c, "MAY 2, 2011 · NATURAL COLOR", 120, 195, 54, fade(t, CU[33] + 0.2, CU[33] + 0.8, CU[34] - 0.2, CU[34] + 0.2), OCH, "l", "Inter-Black.otf")
        txt(c, "SOUTHWEST → NORTHEAST", 120, 120, 60, fade(t, CU[34] + 0.4, CU[34] + 1.0, CU[35] - 0.3, CU[35] + 0.1), INK, "l", "Inter-Black.otf")
        txt(c, "NWS: ~80-MILE PATH · UP TO 1.5 MI WIDE", 120, 120, 54, fade(t, CU[35] + 0.4, CU[35] + 1.0, CU[36] - 0.3, CU[36] + 0.1), OCH, "l", "Inter-Black.otf")
        txt(c, "THIS FRAME SHOWS ONE SECTION", 120, 120, 54, fade(t, CU[36] + 0.6, CU[36] + 1.2, CU[37] + 3, CU[37] + 3.5), INK, "l", "Inter-Black.otf")
        txt(c, "A LINE THROUGH A LIVING CITY", 120, 120, 60, fade(t, CU[40] + 0.3, CU[40] + 0.9, CU[42] - 0.3, CU[42] + 0.1), OCH, "l", "Inter-Black.otf")
        txt(c, "CONTRAIL: IN THE ATMOSPHERE · SCAR: ON THE GROUND", 120, 120, 44, fade(t, CU[43] + 0.5, CU[43] + 1.1, CU[46] + 3, CU[46] + 3.6), INK, "l", "Inter-Black.otf")
        credit(c, C_EO1, smooth(seg(t, s0 + 0.8, s0 + 1.4))); return c
    C_AS = "NASA Earth Observatory · ASTER (Terra) · May 4, 2011 · FALSE COLOR · J. Allen; data NASA/GSFC/METI/ERSDAC/JAROS, U.S./Japan ASTER Science Team"
    C_LC = "USGS · LCMAP land-cover change, 2011 (Landsat-based) · public domain"
    def sc_sensors(t):
        s0, a1, a2, a3, a4, a5, a6, e1 = CU[47], CU[48], CU[49], CU[50], CU[51], CU[52], CU[53], CU[54]
        if t < a4 - 0.4 or True:
            cam = E.Cam([(s0, (2048, 3073, 10925)), (a1 + 0.5, (2048, 3073, 9800)), (a1 + 5.0, (2560, 3350, 3300)), (a2 + 4.0, (2560, 3350, 2600)), (a3 + 0.5, (2500, 3400, 3600)), (a4 - 0.4, (2048, 3073, 10925)), (a4 + 3, (2048, 3073, 10925))])
            cx, cy, vw = cam(t); A = render_doc("as", cx, cy, vw)
            camL = E.Cam([(a4 - 0.4, (1600, 1600, 5689)), (a4 + 3.0, (1500, 1350, 2600)), (a5, (1450, 1250, 2000)), (a6, (1500, 1400, 2500)), (e1 - 1.0, (1600, 1600, 5689)), (e1 + 1, (1600, 1600, 5689))])
            cx2, cy2, vw2 = camL(t); L = render_doc("lc", cx2, cy2, vw2)
        k = smooth(seg(t, a4 - 0.4, a4 + 0.4)); c = A * (1 - k) + L * k if 0 < k < 1 else (L if k >= 1 else A)
        ka = 1 - k
        txt(c, "ASTER · TERRA · MAY 4, 2011", 120, 120, 54, fade(t, s0 + 0.3, s0 + 0.9, a1 - 0.1, a1 + 0.3) * ka, INK, "l", "Inter-Black.otf")
        txt(c, "FALSE COLOR", 120, 195, 54, fade(t, s0 + 0.6, s0 + 1.2, a1 - 0.1, a1 + 0.3) * ka, OCH, "l", "Inter-Black.otf")
        txt(c, "ANOTHER SECTION · NEAR BIRMINGHAM", 120, 120, 54, fade(t, a1 + 0.4, a1 + 1.0, a2 - 0.3, a2 + 0.1) * ka, INK, "l", "Inter-Black.otf")
        txt(c, "FALSE COLOR: HEALTHY VEGETATION = RED", 120, 120, 50, fade(t, a2 + 0.3, a2 + 0.9, a3 - 0.3, a3 + 0.1) * ka, INK, "l", "Inter-Black.otf")
        txt(c, "TORNADO TRACK = PALE BEIGE STRIPE", 120, 190, 50, fade(t, a2 + 2.2, a2 + 2.8, a3 - 0.3, a3 + 0.1) * ka, OCH, "l", "Inter-Black.otf")
        txt(c, "NEW SENSOR · NEW COLORS · SAME EVIDENCE", 120, 120, 50, fade(t, a3 + 0.3, a3 + 0.9, a4 - 0.5, a4 - 0.1) * ka, OCH, "l", "Inter-Black.otf")
        kl = k
        txt(c, "USGS LAND-COVER CHANGE (LANDSAT-BASED)", 120, 120, 50, fade(t, a4 + 0.2, a4 + 0.8, a5 - 0.3, a5 + 0.1) * kl, INK, "l", "Inter-Black.otf")
        txt(c, "PURPLE = LAND-COVER CHANGE IN 2011", 120, 190, 50, fade(t, a4 + 1.4, a4 + 2.0, a5 - 0.3, a5 + 0.1) * kl, (200, 120, 255), "l", "Inter-Black.otf")
        txt(c, "MEASUREMENTS OF CHANGE · NOT PHOTOS OF A TORNADO", 120, 120, 46, fade(t, a5 + 0.3, a5 + 0.9, e1 - 0.6, e1 - 0.1) * kl, INK, "l", "Inter-Black.otf")
        credit(c, C_AS, smooth(seg(t, s0 + 0.8, s0 + 1.4)) * ka); credit(c, C_LC, smooth(seg(t, a4, a4 + 0.6)) * kl); return c
    def sc_limits(t):
        a = CU[54]; cam = E.Cam([(a, (2564, 3940, 3200)), (CU[56], (2700, 3860, 1000)), (CU[58], (2900, 3700, 420)), (CU[60], (2800, 3760, 900)), (CU[61], (2564, 3940, 2800))]); cx, cy, vw = cam(t)
        c = render_doc("eo", cx, cy, vw); m = cmask(cx, cy, vw); c = E.spotlight(c, m, 0.72, 1.12)
        txt(c, "ONE WITNESS · NOT THE WHOLE INVESTIGATION", 120, 120, 50, fade(t, CU[54] + 0.3, CU[54] + 0.9, CU[55] - 0.2, CU[55] + 0.1), INK, "l", "Inter-Black.otf")
        txt(c, "ON THE GROUND: ISOLATED SCENES", 120, 120, 54, fade(t, CU[55] + 0.5, CU[55] + 1.1, CU[56] - 0.2, CU[56] + 0.1), INK, "l", "Inter-Black.otf")
        txt(c, "FROM ABOVE: LONG CORRIDORS", 120, 120, 54, fade(t, CU[56] + 0.2, CU[56] + 0.8, CU[57] - 0.2, CU[57] + 0.1), OCH, "l", "Inter-Black.otf")
        for i, lab in enumerate(["WIND SPEED", "INJURIES", "WHAT HAPPENED AT EACH ADDRESS"]):
            txt(c, f"✕ {lab}", 120, 120 + 0 + 0, 50, 0, INK)
        for i, lab in enumerate(["EXACT WIND SPEED", "EVERY INJURY", "EACH ADDRESS"]):
            a_ = fade(t, CU[58] + 0.6 + i * 1.6, CU[58] + 1.2 + i * 1.6, CU[59] - 0.1, CU[59] + 0.3); txt(c, "NOT SHOWN: " + lab, 120, 120 + 0, 48, a_ * 0 , INK)
        for i, lab in enumerate(["WIND SPEED", "INJURIES", "EACH ADDRESS"]):
            chip(c, lab, 120 + i * 360, 120, fade(t, CU[58] + 0.5 + i * 1.5, CU[58] + 1.0 + i * 1.5, CU[59] - 0.2, CU[59] + 0.3), 0.0, 330, 100)
        txt(c, "SURVEYS · RADAR · PEOPLE ON THE GROUND", 120, 250, 46, fade(t, CU[59] + 0.4, CU[59] + 1.0, CU[60] - 0.2, CU[60] + 0.1), OCH, "l", "Inter-Black.otf")
        txt(c, "NOT SHOWN BY A SATELLITE:", 120, 70, 36, fade(t, CU[58] + 0.3, CU[58] + 0.8, CU[59] - 0.2, CU[59] + 0.3), OCH, "l", "Inter-ExtraBold.otf")
        credit(c, C_EO1, 1.0); return c
    def sc_return(t):
        a = CU[61]; cam = E.Cam([(a, (2564, 3940, 2800)), (CU[63], (2564, 3940, 1900)), (CU[65], (2400, 3860, 3600)), (CU[67], (2048, 3000, 6000))]); cx, cy, vw = cam(t)
        c = render_doc("eo", cx, cy, vw); k = smooth(seg(t, a + 0.3, a + 1.6)); c = E.spotlight(c, cmask(cx, cy, vw), lerp(1, 0.62, k), lerp(1, 1.2, k))
        txt(c, "A FEW TERRIFYING MINUTES · SEEN DAYS LATER", 120, 120, 54, fade(t, CU[63] + 0.3, CU[63] + 0.9, CU[64] - 0.3, CU[64] + 0.1), INK, "l", "Inter-Black.otf")
        txt(c, "THE LIVES ALONG THE PATH ARE NOT IN THE PICTURE", 120, 120, 50, fade(t, CU[65] + 0.2, CU[65] + 0.8, CU[66] - 0.2, CU[66] + 0.2), OCH, "l", "Inter-Black.otf")
        txt(c, "BUT THEY SHOW HOW FAR IT WENT", 120, 120, 54, fade(t, CU[66] + 0.3, CU[66] + 0.9, CU[67] - 0.2, CU[67] + 0.2), INK, "l", "Inter-Black.otf")
        credit(c, C_EO1, 1.0); return c
    def sc_close(t):
        a = CU[67]; u = t - a; parts = [(CU[67], CU[67] + 4.7, "goes"), (CU[67] + 4.7, CU[68] + 1.2, "ma"), (CU[68] + 1.2, CU[69] - 0.3, "eo"), (CU[69] - 0.3, 1e9, "end")]
        def part(kind, t0):
            if kind == "goes": return goes(t - a, 3.2, 700, 380, 1000 - 25 * (t - a))
            if kind == "ma": return render_doc("ma", 2200 - 20 * (t - t0), 1750, 3600 - 120 * (t - t0))
            if kind == "eo": return render_doc("eo", 2564, 3940, 2800 - 140 * (t - t0))
            return None
        c = None
        for i, (p0, p1, kind) in enumerate(parts):
            if p0 - 0.6 <= t <= p1 + 0.6 and kind != "end":
                x = part(kind, p0); w = smooth(seg(t, p0 - 0.6, p0 + 0.6)) * (1 - smooth(seg(t, p1 - 0.6, p1 + 0.6)))
                c = x * w if c is None else c + x * w
        if c is None: c = np.zeros((H, W, 3), np.float32)
        e_ = smooth(seg(t, CU[69] - 0.3, CU[69] + 0.8)); c = c * (1 - 0.9 * e_) + e_ * grad((8, 14, 28), (20, 32, 56)) * 0.9
        cr = [("goes", C_GOES), ("ma", C_MA), ("eo", C_EO1)]
        for (p0, p1, kind), (_, cs) in zip(parts[:3], cr): credit(c, cs, smooth(seg(t, p0, p0 + 0.5)) * (1 - smooth(seg(t, p1 - 0.5, p1))) * (1 - e_))
        txt(c, "ORBITAL ATLAS", W / 2, 440, 120, e_, INK, "c", "Inter-Black.otf"); txt(c, "THE STORY IS WRITTEN ON THE PLANET ITSELF", W / 2, 620, 40, smooth(seg(t, CU[70] - 0.2, CU[70] + 0.8)), OCH, "c", "Inter-ExtraBold.otf"); return c
    SECS = [(CU[7], sc_hook), (CU[9], sc_promise), (CU[14], sc_context), (CU[22], sc_storms), (CU[32], sc_ba), (CU[47], sc_tusc), (CU[54], sc_sensors), (CU[61], sc_limits), (CU[67], sc_return), (1e9, sc_close)]
    # scene boundaries: hook<CU[7]; promise<CU[9]; context<CU[14]; storms<CU[22]; before/after<CU[32]; tusc<CU[47]; sensors<CU[54]; limits<CU[61]; return<CU[67]; close
    SC = [(0, sc_hook), (CU[7], sc_promise), (CU[9], sc_context), (CU[14], sc_storms), (CU[22], sc_ba), (CU[32], sc_tusc), (CU[47], sc_sensors), (CU[54], sc_limits), (CU[61], sc_return), (CU[67], sc_close)]
    XF = 0.5
    def scene(t):
        k = max(i for i, (s, _) in enumerate(SC) if s <= t + 1e-9); c = SC[k][1](t)
        if k + 1 < len(SC) and SC[k + 1][0] - t < XF:        # soft dip-free crossfade into next scene (real, continuous)
            u = smooth(1 - (SC[k + 1][0] - t) / XF * 1.0); c = c * (1 - u * 0) ; n = SC[k + 1][1](t); c = c * (1 - u) + n * u
        elif k > 0 and t - SC[k][0] < 0 : pass
        captions(c, t, SRT); return c
    DUR = END
# ======================================================================= SHORTS
if SHORT:
    TL = T(MODE); CU = [c["start"] for c in TL["cues"]]; END = TL["duration"]; SRT = load_srt(f"{P}/{MODE}/captions.srt"); DUR = END
    def hl(c, text, y, a, col=INK, size=88): txt(c, text, W / 2, y, size, a, col, "c", "Inter-Black.otf")
    def ctab(c, text, a=1.0): tag(c, text, 28, H - 200, a)
    def s1(t):
        if t < CU[3] - 0.2:
            cam = E.Cam([(0, (2640, 3920, 1300)), (CU[2], (2700, 3890, 1450)), (CU[3], (2800, 3820, 1800))]); cx, cy, vw = cam(t); c = doc("eo").render(cx, cy, vw, size=(W, H))
            def sc2(pt): s = W / vw; return (W / 2 + (pt[0] - cx) * s, H / 2 + (pt[1] - cy) * s)
            m = E.corridor([sc2(tr_pt(i / 24)) for i in range(25)], 95 * W / vw, 95 * W / vw * 0.55); amt = e_("fade_soft", t, 0.2, 1.0); c = E.spotlight(c, m, lerp(1, 0.62, amt), lerp(1, 1.2, amt))
            hl(c, "THIS ISN'T A ROAD.", 230, fade(t, 0.15, 0.5, CU[1] + 1.5, CU[1] + 2.0), INK, 76)
            hl(c, "A TORNADO SCAR.", 230, fade(t, CU[2] + 0.1, CU[2] + 0.6, CU[3] - 0.3, CU[3] + 0.1), OCH, 76); ctab(c, C_EO1, smooth(seg(t, 0.6, 1.2))); return c
        def eo_end(t):
            cx_, cy_, vw_ = E.Cam([(0, (2450, 3880, 1500)), (END - CU[5], (2450, 3880, 1700))])(max(0.0, t - CU[5])); return doc("eo").render(cx_, cy_, vw_, size=(W, H))
        if t < CU[5] + 1.4:
            xw = None; cx, cy, vw = 2150, 1750, lin(t, [(CU[3], 1750), (CU[5] + 1.4, 1450)]); a = doc("ma").render(cx, cy, vw, size=(W, H)); b = doc("mb").render(cx, cy, vw, size=(W, H))
            w = smooth(seg(t, CU[3] + 1.5, CU[3] + 4.2)); X = np.arange(W, dtype=np.float32)[None, :, None]; m = np.clip((W * 1.1 * w - 0.05 * W - X) / 60 + 0.5, 0, 1); c = a * m + b * (1 - m)
            hl(c, "APR 12 → APR 28", 230, fade(t, CU[3] + 0.2, CU[3] + 0.7, CU[5], CU[5] + 0.5), INK, 84); ctab(c, "NASA MODIS · Apr 12 / Apr 28, 2011 · NASA Earth Observatory", 1.0)
            u = smooth(seg(t, CU[3], CU[3] + 0.5)); c = c * u + (1 - u) * s1(CU[3] - 0.3); w2 = smooth(seg(t, CU[5] + 0.4, CU[5] + 1.4)); return c * (1 - w2) + w2 * eo_end(t) if w2 > 0 else c
        c = eo_end(t)
        hl(c, "SEEN FROM ORBIT", 230, smooth(seg(t, CU[5] + 1.4, CU[5] + 2.0)), INK, 96); hl(c, "FULL STORY · ORBITAL ATLAS", H - 560, smooth(seg(t, END - 6, END - 5.4)), OCH, 52); ctab(c, C_EO1, 1.0); return c
    def s2(t):
        if t < CU[3] - 0.1:
            c = goes(t, 3.2, 1050 + 30 * math.sin(t * 0.4), 540, 600 - 8 * t, size=(W, H)) * 0.92
            hl(c, "CAN SATELLITES SEE TORNADOES?", 230, fade(t, 0.2, 0.7, CU[1] - 0.2, CU[1] + 0.2), INK, 50)
            hl(c, "THE CLOUDS", 230, fade(t, CU[1] + 0.3, CU[1] + 0.8, CU[3] - 0.3, CU[3] + 0.1), OCH, 100); ctab(c, C_GOES, 1.0)
            tag(c, "Funnels: too small at this scale", W - 28, 70, smooth(seg(t, CU[1] + 1, CU[1] + 1.6)), True); return c
        if t < CU[4] + 0.6:
            c = goes(t, 3.2, 1050 + 30 * math.sin(t * 0.4), 540, 600 - 8 * t, size=(W, H)) * 0.92; hl(c, "STORM SYSTEMS · APRIL 2011", 230, fade(t, CU[3] + 0.2, CU[3] + 0.8, CU[4] - 0.2, CU[4] + 0.3), INK, 52); ctab(c, C_GOES, 1.0)
            u = smooth(seg(t, CU[4] - 0.4, CU[4] + 0.6)); return c * (1 - u) + u * doc("mb").render(2150, 1600, 1750, size=(W, H))
        if t < CU[5] + 1.0: pass
        k = t - CU[4]; w = smooth(seg(t, CU[4] + 2.5, CU[4] + 5.5)); cx, cy, vw = 2150, 1600, lin(t, [(CU[4], 1750), (END, 1500)])
        a = doc("ma").render(cx, cy, vw, size=(W, H)); b = doc("mb").render(cx, cy, vw, size=(W, H)); X = np.arange(W, dtype=np.float32)[None, :, None]; m = np.clip((W * 1.1 * w - 0.05 * W - X) / 60 + 0.5, 0, 1)
        c = a * m + b * (1 - m)
        if t > CU[5] + 0.5:
            u = smooth(seg(t, CU[5] + 0.5, CU[5] + 1.6)); e_cam = E.Cam([(0, (2450, 3880, 1500)), (END - CU[5], (2450, 3880, 1700))]); cx2, cy2, vw2 = e_cam(t - CU[5]); c = c * (1 - u) + u * doc("eo").render(cx2, cy2, vw2, size=(W, H))
        hl(c, "THE SCARS STAYED", 230, smooth(seg(t, CU[5] + 0.4, CU[5] + 1.0)), OCH, 96); hl(c, "FULL STORY · ORBITAL ATLAS", H - 560, smooth(seg(t, END - 6, END - 5.4)), INK, 52)
        ctab(c, "NASA MODIS / EO-1 · NASA Earth Observatory", 1.0); return c
    def scene(t):
        c = (s1 if MODE == "s1" else s2)(t); captions(c, t, SRT); return c
# ======================================================================= render loop
def main():
    out, t0, t1 = sys.argv[2], float(sys.argv[3]), float(sys.argv[4]); i0, i1 = int(round(t0 * 30)), int(round(min(t1, DUR) * 30))
    vg = E.vignette_map(0.28); G = np.random.default_rng(5).normal(0, 1, (4, H, W)).astype(np.float32)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "30", out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        c = E.render_frame(scene, i / 30, 1) * vg[..., None] + G[i % 4][..., None] * 0.010
        ff.stdin.write(np.clip(c * 255 + 0.5, 0, 255).astype(np.uint8).tobytes())
        if (i - i0) % 150 == 0: print(MODE, i, "/", i1, flush=True)
    ff.stdin.close(); ff.wait()
def stills():
    vg = E.vignette_map(0.28)
    for t in map(float, os.environ["STILLS"].split(",")):
        c = scene(t) * vg[..., None]; cv2.imwrite(f"{P}/still_{MODE}_{t:07.2f}.jpg", cv2.cvtColor(np.clip(c * 255, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
if os.environ.get("STILLS"): stills()
elif MODE != "thumb": main()
