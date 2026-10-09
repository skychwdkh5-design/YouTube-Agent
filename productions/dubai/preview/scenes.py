"""EP002 scene functions. Each takes (t, dur, ctx) with local time t (s) and returns a Canvas (base frame + overlay), captions added by the driver.
Geography/dates follow SCRIPT_LOCK and visuals/VISUAL_PRODUCTION_PLAN.md. Crops are original-pixel rects (x, y, w, h)."""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from kit import *

R_PALM = (140, 1445, 800, 450)
PS = (350, 1637)                       # Palm Jumeirah site in the WoC frames (2003 frame, read from a 200 px grid; +-30 px)
ASTER = lambda y: f'NASA ASTER · {y} · colours as published'
ISSCHIP = 'NASA ISS astronaut photograph · 2022 · not satellite imagery'
H3A, H3B = (1155, 820, 1600, 900), (826, 2326, 1600, 900)
C1A, C1B, C1C, C1D = (60, 2780, 1280, 720), (915, 1905, 960, 540), (878, 1000, 1280, 720), (1700, 150, 1280, 720)

def still(key, rect, chip, cv_year=None, year_t=0.4):
    return view(key, rect)
def yearlabel(cv, s, t, t0=0.4, xy=None, px=30):
    cv.text((W - 24, 40), s, px, AMBER, oc(seg(t, t0, t0 + 0.7)), anchor='ra', spacing=0.14)

# ------------------------------------------------------------------ HOOK
def H1(t, d, X):
    r = lerp_rect(R_PALM, (170, 1470, 740, 416), t / d); cv = Canvas(view('2000', r)); cv.chip(ASTER('2000')); yearlabel(cv, 'NOVEMBER 2000', t); return cv
def H2(t, d, X):
    r = lerp_rect(R_PALM, (170, 1470, 740, 416), t / d); cv = Canvas(view('2003', r)); cv.chip(ASTER('2003')); yearlabel(cv, 'NOVEMBER 2003', t); return cv
def H3(t, d, X):
    u = smr(seg(t, 0.5, d - 0.5)); cv = Canvas(view('iss', lerp_rect(H3A, H3B, u))); cv.chip(ISSCHIP); yearlabel(cv, 'APRIL 2022', t); return cv
def H4(t, d, X):
    r = lerp_rect((500, 1100, 2368, 1332), (580, 1140, 2200, 1238), t / d); base = view('palm2', r)
    k = sm(seg(t, 2.2, 3.4)); base = dim(base, 1 - 0.55 * k); cv = Canvas(base); cv.chip(ASTER('2006'))
    cv._center = True
    cv.kinetic((W / 2, H * 0.36), 'HOW DUBAI CHANGED', 40, 3.0, t, spacing=0.14, per=0.04, a=k)
    cv.kinetic((W / 2, H * 0.36 + 56), 'THE MAP OF THE EARTH', 40, 3.6, t, spacing=0.14, per=0.04, a=k)
    cv.text((W / 2, H * 0.36 + 120), 'ORBITAL ATLAS · EP002', 16, MUTED, a=k * sm(seg(t, 5.0, 6.0)), anchor='ma', spacing=0.3); return cv

# ------------------------------------------------------------------ ACT 1
A2_START = (550, 600, 2400, 1350)
def clean_swath(img):
    """UI cleanup of the Cesium render: the Landsat WELD layer leaves a blue-grey no-data swath over open water; paint it with deep-sea colour."""
    a = np.asarray(img, np.int16); r, g, b = a[..., 0], a[..., 1], a[..., 2]; luma = a.mean(2)
    m = (abs(r - g) < 19) & ((b - r) >= 3) & ((b - r) <= 48) & (luma > 55) & (luma < 180)
    mi = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.5)); k = (np.asarray(mi, np.float32) / 255)[..., None]
    sea = np.array([19, 50, 66], np.float32); return Image.fromarray((np.asarray(img, np.float32) * (1 - k) + sea * k).clip(0, 255).astype(np.uint8))
def pjson(f): return os.path.join(os.path.dirname(f), 'p' + os.path.basename(f)[1:-4] + '.json')
def tone_match(img, ref):
    a = np.asarray(img, np.float32); r = np.asarray(ref, np.float32).reshape(-1, 3)
    m, s = a.reshape(-1, 3).mean(0), a.reshape(-1, 3).std(0) + 1e-3; t = (a - m) / s * r.std(0) + r.mean(0)
    return t
def A1(t, d, X):
    fr = X['a1_frames']; n = len(fr); i = min(int(t * FPS), n - 1)
    ces = Image.open(fr[i]).convert('RGB').resize((W, H), Image.LANCZOS); ces = clean_swath(ces) if 80 <= i <= 172 else ces; ces = Image.fromarray(np.maximum(np.asarray(ces), np.array([12, 28, 40], np.uint8))) if i >= 100 else ces; pj = json.load(open(pjson(fr[i])))
    u = seg(t, 15.8, 19.0)
    if u > 0:
        last = json.load(open(pjson(fr[-1]))); ref = view('2000', A2_START)
        k = sm(seg(t, 13.0, 17.0)) * 0.7; ces = Image.fromarray((np.asarray(ces, np.float32) * (1 - k) + tone_match(ces, ref) * k).clip(0, 255).astype(np.uint8))
        c = last['dubai'][:2]; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); D = np.hypot(xx - c[0], yy - c[1]); far = float(np.hypot(max(c[0], W - c[0]), max(c[1], H - c[1])))
        e = smr(u); Rr = (0.02 * H) * (1 - e) + (far + 0.36 * H) * e; v = np.clip((Rr - D) / (0.30 * H), 0, 1); m = (v * v * (3 - 2 * v))[..., None]
        base = Image.fromarray((np.asarray(ces, np.float32) * (1 - m) + np.asarray(ref, np.float32) * m).clip(0, 255).astype(np.uint8))
    else: base = ces
    cv = Canvas(base)
    ca = 1 - sm(seg(t, 17.0, 18.2)); cv.chip('NASA GIBS · Blue Marble + Landsat · 3D globe view (CesiumJS)', ca) if ca > 0 else cv.chip(ASTER('2000'), sm(seg(t, 18.2, 19.0)))
    def lab(key, s, t0, t1, px=17, off=(0, -26)):
        x, y, vis = pj[key]; a = oc(seg(t, t0, t0 + 0.6)) * (1 - sm(seg(t, t1, t1 + 0.6))) * vis * ca
        if a > 0.01 and 20 < x < W - 20 and 40 < y < H - 90: cv.text((x + off[0], y + off[1]), s, px, AMBER, a, anchor='ms', spacing=0.2)
    lab('gulf', 'PERSIAN GULF', 3.2, 9.5); lab('uae', 'UNITED ARAB EMIRATES', 4.6, 9.0)
    x, y, vis = pj['dubai']; a = oc(seg(t, 9.0, 9.8)) * vis * ca
    if a > 0.01 and 20 < x < W - 20 and 40 < y < H - 90:
        cv.ring((x, y), 7, a, 2); cv.text((x + 12, y - 4), 'DUBAI', 18, AMBER, a, anchor='lm', spacing=0.2)
    return cv
def A2(t, d, X):
    u = smr(seg(t, 0.8, d - 1.0)); r = lerp_rect(A2_START, R_PALM, u); cv = Canvas(view('2000', r)); cv.chip(ASTER('2000')); yearlabel(cv, '2000', t, 0.3)
    s = lambda p: to_screen(r, p)
    cv.callout(s((1150, 1250)), 'CITY HUGS THE SHORE', t, 2.5, (80, -60), out=9.0, ring=False)
    cv.callout(s((1900, 1500)), 'EMPTY DESERT INLAND', t, 4.5, (-70, 60), out=10.5, ring=False)
    cv.callout(s(PS), 'OFFSHORE: NOTHING BUILT YET', t, 14.5, (150, -90), r=60)
    return cv
def card_rows(cv, t, rows, x=70, y0=150, gap=96, t0=0.5, step=0.9, px=34, sub=None):
    for i, (lab, val) in enumerate(rows):
        k = oc(seg(t, t0 + i * step, t0 + i * step + 0.6)); y = y0 + i * gap
        cv.d.line([(x, y - 14), (W - x, y - 14)], fill=MUTED + (int(90 * k),), width=1)
        cv.text((x, y), lab, 14, MUTED, k, anchor='la', spacing=0.2); cv.text((x, y + 24 + (1 - k) * 10), val, px, TEXT, k, anchor='la')
def A3(t, d, X):
    cards = [([('NASA EARTH OBSERVATORY', 'Hundreds of artificial islands'), ('PURPOSE', 'To expand the beachfront for tourism')], 0, 10.5),
             ([('PLANS FROM THE 1990s', 'The World'), ('THE PLAN INCLUDED', 'About 300 small islands')], 10.5, 20.0),
             ([('EARLY 2000s', 'Little built beyond shallow Gulf water'), ('NASA, ON THE SEA HERE', 'The blank page')], 20.0, d)]
    cv = None
    for rows, a, b in cards:
        if a <= t < b + 0.0:
            cv = Canvas(text_card_bg()); k = min(sm(seg(t, a, a + 0.5)), 1 - sm(seg(t, b - 0.5, b)) if b < d else 1)
            sub = Canvas(text_card_bg()); card_rows(sub, t - a, rows, y0=170); sub.o.putalpha(sub.o.getchannel('A').point(lambda v: int(v * k))); cv.o = sub.o; cv.d = ImageDraw.Draw(cv.o); break
    cv.text((70, 56), 'A BLANK PAGE ON THE COAST', 15, AMBER, anchor='la', spacing=0.25); return cv

# ------------------------------------------------------------------ ACT 2
def B1(t, d, X):
    u = smr(seg(t, 1.0, 9.5)); r = lerp_rect(R_PALM, (0, 1422, 480, 270), u); cv = Canvas(view('2002a', r)); cv.chip(ASTER('2002')); yearlabel(cv, 'FEBRUARY 2002', t, 0.3)
    cv.callout(to_screen(r, (230, 1558)), 'FIRST EARLY STAGE', t, 6.0, (120, -80), r=30); return cv
def B2(t, d, X):
    r = lerp_rect(R_PALM, (170, 1470, 740, 416), t / d); cv = Canvas(view('2002b', r)); cv.chip(ASTER('2002')); yearlabel(cv, 'OCTOBER 2002', t, 0.3)
    s = lambda p: to_screen(r, p)
    cv.callout(s((188, 1650)), 'CIRCULAR BREAKWATER', t, 3.0, (60, -120), r=14); cv.callout(s((300, 1590)), 'SANDY FRONDS', t, 7.5, (200, 80), r=14); return cv

def sea_bg(horizon=0.30):
    y = np.linspace(0, 1, H)[:, None, None]
    sky = np.array([210, 226, 238], np.float32); water = np.array([30, 92, 128], np.float32) * (1 - y * 0.0) ; deep = np.array([12, 40, 62], np.float32)
    a = np.where(y < horizon, sky * (1 - y / horizon * 0.15), water * (1 - (y - horizon) / (1 - horizon)) + deep * ((y - horizon) / (1 - horizon)))
    return Image.fromarray(np.broadcast_to(a, (H, W, 3)).clip(0, 255).astype(np.uint8))
def ship(d, x, y, s=1.0, col=(40, 46, 56)):
    d.polygon([(x - 60 * s, y), (x + 70 * s, y), (x + 52 * s, y + 20 * s), (x - 48 * s, y + 20 * s)], fill=col)
    d.rectangle([x - 20 * s, y - 24 * s, x + 12 * s, y], fill=(220, 224, 230)); d.rectangle([x - 10 * s, y - 36 * s, x + 4 * s, y - 24 * s], fill=(200, 60, 50))
def B3(t, d, X):
    base = sea_bg(0.30); cv = Canvas(base); dd = cv.d; hz = int(H * 0.30); sea_floor = int(H * 0.80)
    dd.rectangle([0, sea_floor, W, H], fill=(194, 164, 112, 255)); dd.rectangle([0, sea_floor + 60, W, H], fill=(160, 134, 92, 255))
    rng = np.random.default_rng(3)
    for _ in range(160): x, y = rng.integers(0, W), rng.integers(sea_floor, H); dd.ellipse([x, y, x + 2, y + 2], fill=(120, 98, 66, 255))
    sx = 250 + 10 * math.sin(t * 1.2); ship(dd, sx, hz - 10); dd.line([(sx - 30, hz + 10), (sx - 40, sea_floor)], fill=(60, 66, 76, 255), width=5)
    k1 = seg(t, 4.0, 8.0)
    if k1 > 0:
        for i in range(12): yy = hz + 20 + (sea_floor - hz - 40) * ((i / 12 + t * 0.7) % 1); dd.ellipse([sx - 44 - 3 * math.sin(i), yy, sx - 36, yy + 6], fill=(214, 184, 126, int(220 * k1)))
    k2 = seg(t, 8.5, 12.0)
    if k2 > 0:                                                       # spray arc and the new island pile
        pts = [(sx + 55 + (520 - 55) * s, hz - 28 - 70 * math.sin(math.pi * s)) for s in np.linspace(0, k2, 40)]
        dd.line(pts, fill=(226, 200, 142, 255), width=6)
    pile = seg(t, 10.0, 17.5)
    if pile > 0: hh = 28 * pile; dd.polygon([(520, hz + 2), (900, hz + 2), (880, hz - hh), (560, hz - hh)], fill=(214, 186, 128, 255))
    k3 = seg(t, 14.0, 17.0)
    if k3 > 0:
        for i in range(7): x = 495 + i * 15; dd.polygon([(x, hz + 22), (x + 14, hz + 22), (x + 12, hz - 6 - 22 * k3), (x + 2, hz - 6 - 22 * k3)], fill=(96, 98, 104, int(255 * k3)))
        cv.callout((505, hz - 12), 'ROCK BREAKWATER', t, 14.2, (-30, -62), ring=False, col=(30, 40, 52), px=15)
    cv.callout((W - 330, sea_floor + 30), 'SAND ON THE SEA FLOOR', t, 1.0, (0, 0), ring=False, col=(40, 30, 16), px=16)
    cv.callout((sx - 40, sea_floor - 80), 'DREDGED FROM THE GULF FLOOR', t, 4.5, (140, 40), ring=False, col=(235, 240, 246), px=15)
    cv.callout((700, hz - 40), 'PLACED WHERE THE ISLAND WILL BE', t, 10.5, (0, -50), ring=False, col=(30, 40, 52), px=15)
    cv.pill((22, 20), 'ILLUSTRATION · not to scale · method as described by NASA Earth Observatory', 14, 1.0, accent=CYAN); return cv
def B4(t, d, X):
    cv = Canvas(text_card_bg((10, 26, 40))); dd = cv.d
    cv.pill((22, 20), 'ILLUSTRATION · schematic · method as described by NASA Earth Observatory', 14, 1.0, accent=CYAN)
    pw = W / 2 - 50
    for j, (title, x0, t0) in enumerate((('1 · SHIPS GUIDED BY GPS PLACE THE SAND', 30, 0.5), ('2 · A VIBROFLOT COMPACTS IT WITH STONE', W / 2 + 20, 8.0))):
        k = oc(seg(t, t0, t0 + 0.6)); dd.rounded_rectangle([x0, 80, x0 + pw, 400], 8, outline=MUTED + (int(120 * k),), width=1)
        cv.text((x0 + 16, 94), title, 15, AMBER, k)
    k = oc(seg(t, 0.8, 1.6))                                                       # panel 1
    sat = (130, 130 + 10 * math.sin(t)); dd.rectangle([sat[0] - 14, sat[1] - 6, sat[0] + 14, sat[1] + 6], fill=CYAN + (int(255 * k),)); dd.rectangle([sat[0] - 36, sat[1] - 3, sat[0] - 16, sat[1] + 3], fill=MUTED + (int(255 * k),)); dd.rectangle([sat[0] + 16, sat[1] - 3, sat[0] + 36, sat[1] + 3], fill=MUTED + (int(255 * k),))
    cv.text((sat[0] + 46, sat[1] - 8), 'GPS', 14, CYAN, k)
    sx, sy = 260, 330; dd.rectangle([30, 360, 30 + pw, 396], fill=(30, 70, 100, int(255 * k))); ship(dd, sx, sy, 0.8, col=(90, 100, 114))
    for i in range(5): a = seg(t, 2.0 + i * 0.5, 2.5 + i * 0.5); dd.line([(sat[0], sat[1] + 8), (sx - 10 + i * 6 - 12, sy - 34)], fill=CYAN + (int(110 * a),), width=1)
    if seg(t, 4.0, 6.0) > 0:
        for i in range(10): yy = sy + 8 + (60 * ((i / 10 + t * 0.6) % 1)); dd.ellipse([sx + 40 + 4 * math.sin(i * 2), yy, sx + 46, yy + 5], fill=(214, 184, 126, 255))
    cv.text((30 + 16, 372), 'TARGET AREA', 12, MUTED, seg(t, 3, 4))
    k = oc(seg(t, 8.3, 9.0)); x0 = W / 2 + 20                                         # panel 2 (loose sand -> packed)
    dd.rectangle([x0 + 30, 160, x0 + pw - 30, 390], fill=(168, 140, 96, int(255 * k)))
    rng = np.random.default_rng(5); pk = seg(t, 11.5, 15.0)
    for i in range(140):
        px_, py_ = rng.uniform(x0 + 36, x0 + pw - 36), rng.uniform(170, 384); cx = x0 + pw / 2; pull = pk * 0.5 * (1 if px_ > cx else -1) * min(1, abs(px_ - cx) / 80)
        dd.ellipse([px_ - pull * 40 - 3, py_ - 3, px_ - pull * 40 + 3, py_ + 3], fill=(104, 82, 52, int(255 * k)))
    if seg(t, 9.5, 11.5) > 0:
        dep = 160 + 200 * sm(seg(t, 9.5, 12.0)); dd.rectangle([x0 + pw / 2 - 7, 130, x0 + pw / 2 + 7, dep], fill=(150, 156, 164, 255)); dd.polygon([(x0 + pw / 2 - 7, dep), (x0 + pw / 2 + 7, dep), (x0 + pw / 2, dep + 14)], fill=(120, 126, 134, 255))
        cv.text((x0 + pw / 2 + 16, 140), 'VIBROFLOT', 14, TEXT, 1.0)
    if pk > 0.5: cv.text((x0 + pw / 2, 410), 'SOLIDIFIED LAND', 15, CYAN, oc(seg(t, 13.5, 14.5)), anchor='ma')
    return cv
def B5(t, d, X):
    r = lerp_rect(R_PALM, (170, 1470, 740, 416), t / d)
    a, b = view('2002b', r), view('2003', r); u = sm(seg(t, 11.5, 14.5)); cv = Canvas(dissolve(a, b, u))
    cv.chip(ASTER('2002') if u < 0.5 else ASTER('2003')); yearlabel(cv, 'OCTOBER 2002' if u < 0.5 else 'NOVEMBER 2003', t, 0.3)
    s = lambda p: to_screen(r, p)
    cv.callout(s((188, 1650)), 'RING ALREADY IN PLACE', t, 4.5, (60, -120), r=14, out=11.2)
    cv.callout(s((300, 1590)), 'FRONDS STILL SAND', t, 7.5, (200, 80), r=14, out=11.2)
    cv.callout(s((300, 1590)), 'A COMPLETE PALM', t, 17.0, (200, 80), r=14, out=24.0)
    cv.pill((W / 2, 74), 'SEPARATE IMAGES · NOT REGISTERED · NO WIPE', 13, sm(seg(t, 12.0, 13.0)) * (1 - sm(seg(t, 22, 23))), accent=CYAN, anchor='left')
    k = sm(seg(t, 24.5, 25.5)); cv.pill((24, 98), 'BUILDINGS AND VEGETATION COME LATER · 2004–2008', 14, k, accent=AMBER); return cv
def B6(t, d, X):
    keys = ['2004', '2005', '2006', '2007', '2008']; n = len(keys); seg_len = d / n; i = min(int(t // seg_len), n - 1); lt = t - i * seg_len
    r = lerp_rect(R_PALM, (170, 1470, 740, 416), lt / seg_len); im = view(keys[i], r)
    if lt > seg_len - 0.5 and i < n - 1: im = dissolve(im, view(keys[i + 1], R_PALM), (lt - (seg_len - 0.5)) / 0.5)
    cv = Canvas(im); cv.chip(ASTER(keys[i])); yearlabel(cv, keys[i], lt, 0.1, px=44); return cv
def B7(t, d, X):
    r = lerp_rect(C1B, (965, 1930, 860, 484), t / d); cv = Canvas(view('palm2', r)); cv.chip(ASTER('2006'))
    cv.callout(to_screen(r, (1365, 2205)), 'PALM JUMEIRAH', t, 1.5, (-190, -150), r=150, px=20)
    cv.text((24, 66), 'THE FIRST OF SEVERAL', 22, TEXT, oc(seg(t, 5.5, 6.5)), anchor='la', spacing=0.12); return cv

# ------------------------------------------------------------------ ACT 3
def C1(t, d, X):
    stops = [(C1A, 'PALM JEBEL ALI'), (C1B, 'PALM JUMEIRAH'), (C1C, 'THE WORLD'), (C1D, 'PALM DEIRA · EARLY STAGE')]; L = d / 4; i = min(int(t // L), 3); lt = t - i * L
    ctr = [(552, 3140), (1365, 2205), (1517, 1360), (2277, 525)]; rr = [175, 150, 170, 90]
    if i > 0 and lt < 1.6: r = lerp_rect(stops[i - 1][0], stops[i][0], smr(lt / 1.6))
    else: r = lerp_rect(stops[i][0], tuple(v * f for v, f in zip(stops[i][0], (1, 1, 0.94, 0.94))), (lt - 1.6) / (L - 1.6)) if lt >= 1.6 else stops[i][0]
    cv = Canvas(view('palm2', r)); cv.chip(ASTER('2006'))
    cv.callout(to_screen(r, ctr[i]), stops[i][1], lt, 1.0 if i else 0.4, (-60, -190) if i != 1 else (-190, -150), r=rr[i], px=19, out=L - 0.5)
    cv.text((W - 24, 66), f'{i + 1} / 4 · SOUTH TO NORTH', 13, MUTED, anchor='ra', spacing=0.2); return cv

def palm_glyph(dd, cx, cy, s, col, a=255, lw=3):
    dd.arc([cx - 78 * s, cy - 78 * s, cx + 78 * s, cy + 78 * s], 130, 410, fill=col + (a,), width=lw)
    dd.line([(cx, cy + 62 * s), (cx, cy - 40 * s)], fill=col + (a,), width=lw)
    for k in range(-6, 7):
        ang = math.radians(-90 + k * 12); dd.line([(cx, cy - 28 * s + abs(k) * 2 * s), (cx + 58 * s * math.sin(ang + math.radians(90)) * 0 + 52 * s * math.sin(math.radians(k * 12)), cy - 28 * s - 52 * s * math.cos(math.radians(k * 12)) + abs(k) * 2 * s)], fill=col + (a,), width=max(1, lw - 1))
def world_glyph(dd, cx, cy, s, col, a=255, n=300):
    rng = np.random.default_rng(11); blobs = [(-0.45, -0.1, 0.30, 0.34), (-0.40, 0.45, 0.14, 0.28), (0.05, -0.2, 0.18, 0.26), (0.12, 0.28, 0.14, 0.26), (0.48, -0.15, 0.30, 0.28), (0.62, 0.50, 0.12, 0.10)]
    dd.ellipse([cx - 78 * s, cy - 78 * s, cx + 78 * s, cy + 78 * s], outline=col + (int(a * 0.6),), width=1)
    for i in range(n):
        b = blobs[i % len(blobs)]; px_, py_ = rng.normal(b[0], b[2] * 0.45), rng.normal(b[1], b[3] * 0.45)
        if px_ ** 2 + py_ ** 2 < 0.95: dd.ellipse([cx + px_ * 70 * s - 1.5, cy + py_ * 70 * s - 1.5, cx + px_ * 70 * s + 1.5, cy + py_ * 70 * s + 1.5], fill=col + (a,))
def C2(t, d, X):
    cv = Canvas(text_card_bg((10, 22, 36))); dd = cv.d
    cv.pill((22, 20), 'ILLUSTRATION · stylised layouts, not traced from imagery', 14, 1.0, accent=CYAN)
    k1 = oc(seg(t, 1.0, 2.2)); k2 = oc(seg(t, 8.0, 9.2))
    palm_glyph(dd, W * 0.27, H * 0.45, 1.6, AMBER, int(255 * k1), 3); cv.text((W * 0.27, H * 0.74), 'A PALM TREE', 20, AMBER, k1, anchor='ma', spacing=0.2)
    world_glyph(dd, W * 0.73, H * 0.45, 1.6, CYAN, int(255 * k2)); cv.text((W * 0.73, H * 0.74), 'A MAP OF EARTH', 20, CYAN, k2, anchor='ma', spacing=0.2)
    cv.text((W * 0.73, H * 0.80), 'about 300 small islands planned', 14, MUTED, k2 * seg(t, 10, 11), anchor='ma', bold=False)
    cv.text((W / 2, 66), 'THREE PROJECTS · TWO DESIGNS · ONE COAST', 15, MUTED, 1.0, anchor='ma', spacing=0.25); return cv
def C3(t, d, X):
    u = sm(seg(t, 8.0, 10.5)); im = dissolve(view('palm2', C1D), view('palm2', C1C), u); k = sm(seg(t, 2.0, 3.0))
    cv = Canvas(dim(im, 1 - 0.5 * k)); cv.chip(ASTER('2006'))
    cv.text((60, 150), '2007 – 2008', 44, AMBER, oc(seg(t, 3.0, 4.0)), anchor='la'); cv.text((60, 212), 'THE GLOBAL RECESSION', 28, TEXT, oc(seg(t, 4.0, 5.0)), anchor='la')
    cv.text((60, 258), 'NASA: it delayed these projects', 20, MUTED, oc(seg(t, 5.0, 6.0)), anchor='la', bold=False)
    cv.text((60, 330), 'In the 2006 image: Palm Deira barely begun,', 17, TEXT, oc(seg(t, 12.0, 13.0)), anchor='la', bold=False); cv.text((60, 356), 'The World still under construction.', 17, TEXT, oc(seg(t, 12.6, 13.6)), anchor='la', bold=False); return cv
def C4(t, d, X):
    r = lerp_rect(C1C, (940, 1040, 1180, 664), t / d); cv = Canvas(dim(view('palm2', r), 0.32)); cv.chip('Background: NASA ASTER · 2006 · colours as published (not 2022)')
    cv.text((60, 120), '2022', 90, AMBER, oc(seg(t, 0.8, 1.8)), anchor='la')
    cv.text((60, 236), 'Only a handful of The World\'s roughly 300 islands', 26, TEXT, oc(seg(t, 3.0, 4.0)), anchor='la'); cv.text((60, 272), 'had seen development.', 26, TEXT, oc(seg(t, 3.6, 4.6)), anchor='la')
    cv.text((60, 330), 'NASA\'s caption for the astronaut\'s photograph', 17, MUTED, oc(seg(t, 6.0, 7.0)), anchor='la', bold=False)
    cv.text((60, 372), 'A statement about 2022. Nothing is assumed since.', 19, CYAN, oc(seg(t, 14.0, 15.0)), anchor='la'); return cv
def C5(t, d, X):
    r = lerp_rect((704, 0, 2368, 1332), (1500, 60, 1280, 720), smr(seg(t, 0.5, d - 0.5))); cv = Canvas(dim(view('palm2', r), 1 - 0.28 * sm(seg(t, 2, 3)))); cv.chip(ASTER('2006'))
    cv.d.rectangle([W - 400, 112, W, 452], fill=(6, 10, 16, int(150 * sm(seg(t, 2.5, 3.5)))))
    def row(y, a, b, t0, col=TEXT, px=22, bold=True): cv.text((W - 40, y), a, px, col, oc(seg(t, t0, t0 + 0.8)), anchor='ra', bold=bold);
    row(150, 'PALM DEIRA', 0, 3.0, AMBER, 30); row(190, 'scaled back and renamed', 0, 4.0, TEXT, 20, False); row(222, 'THE DEIRA ISLANDS', 0, 5.0, TEXT, 24)
    row(290, 'THE UNIVERSE', 0, 9.5, AMBER, 30); row(330, 'another planned archipelago: put on hold', 0, 10.5, TEXT, 20, False)
    row(400, 'DELAYED · SCALED BACK · ON HOLD', 0, 15.0, CYAN, 22); row(430, 'words about plans, not the condition of the land', 0, 16.0, MUTED, 17, False); return cv
def C6(t, d, X):
    cv = Canvas(text_card_bg((10, 22, 36))); dd = cv.d; cv.pill((22, 20), 'ILLUSTRATION · stylised; facts per NASA Earth Observatory', 14, 1.0, accent=CYAN)
    cv.text((W / 2, 70), 'SAME METHOD: DREDGED SAND, PROTECTED BY ROCK', 15, MUTED, oc(seg(t, 0.5, 1.5)), anchor='ma', spacing=0.2)
    k1 = oc(seg(t, 2.0, 3.0)); k2 = oc(seg(t, 12.0, 13.0)); dd.line([(W / 2, 110), (W / 2, 440)], fill=MUTED + (80,), width=1)
    palm_glyph(dd, W * 0.25, H * 0.40, 1.1, AMBER, int(255 * k1)); cv.text((W * 0.25, 290), 'PALM JUMEIRAH', 20, AMBER, k1, anchor='ma', spacing=0.16)
    cv.text((W * 0.25, 322), 'By 2011: vegetation covered most', 15, TEXT, seg(t, 5, 6), anchor='ma', bold=False); cv.text((W * 0.25, 344), 'of the fronds; many buildings on the trunk', 15, TEXT, seg(t, 5.5, 6.5), anchor='ma', bold=False)
    world_glyph(dd, W * 0.75, H * 0.40, 1.1, CYAN, int(255 * k2)); cv.text((W * 0.75, 290), 'THE WORLD', 20, CYAN, k2, anchor='ma', spacing=0.16)
    cv.text((W * 0.75, 322), 'In 2022: only a handful of roughly', 15, TEXT, seg(t, 15, 16), anchor='ma', bold=False); cv.text((W * 0.75, 344), '300 islands had seen development', 15, TEXT, seg(t, 15.5, 16.5), anchor='ma', bold=False)
    cv.text((W / 2, 420), 'SIMILAR METHOD · VERY DIFFERENT OUTCOMES', 24, AMBER, oc(seg(t, 20, 21)), anchor='ma', spacing=0.12); return cv

# ------------------------------------------------------------------ ACT 4
def D1(t, d, X):
    u = sm(seg(t, 8.0, 10.0)); r1 = lerp_rect(C1A, (100, 2810, 1180, 664), t / d); r2 = lerp_rect(C1B, (950, 1930, 880, 495), t / d)
    cv = Canvas(dissolve(view('palm2', r1), view('palm2', r2), u)); cv.chip(ASTER('2006'))
    if u < 0.5: cv.callout(to_screen(r1, (552, 3140)), 'CIRCULAR STORM BARRIER', t, 1.5, (-30, -200), r=170, out=8.0)
    else: cv.callout(to_screen(r2, (1365, 2205)), 'PALM JUMEIRAH · THE SAME DESIGN', t, 10.3, (-190, -170), r=165)
    k = oc(seg(t, 5.0, 6.0))
    if k > 0:
        x0, y0, w, h = 700, 330, 230, 100; cv.d.rounded_rectangle([x0 - 8, y0 - 24, x0 + w + 8, y0 + h + 24], 6, fill=(8, 14, 22, int(215 * k)))
        cv.d.rectangle([x0, y0, x0 + w, y0 + h], fill=(30, 80, 120, int(255 * k))); cv.d.rectangle([x0 + 90, y0 + 20, x0 + w, y0 + h], fill=(190, 160, 110, int(255 * k)))
        for i in range(4): cv.d.rectangle([x0 + 62 + (i % 2) * 14, y0 + 28 + i * 18, x0 + 90 + (i % 2) * 6, y0 + 44 + i * 18], fill=(110, 112, 118, int(255 * k)))
        cv.text((x0 + 46, y0 - 16), 'ROCK', 12, TEXT, k, anchor='ma'); cv.text((x0 + 160, y0 - 16), 'SAND', 12, TEXT, k, anchor='ma'); cv.text((x0, y0 + h + 6), 'ILLUSTRATION · cross-section', 11, MUTED, k)
    return cv
def D2(t, d, X):
    rect = (600, 1000, 1600, 900); cut = 8.0; key = '2000' if t < cut else '2011'; cv = Canvas(view(key, rect)); cv.chip(ASTER(key))
    yearlabel(cv, key, t if t < cut else t - cut, 0.2, px=54); cv.pill((24, 128), 'LABELLED CUT · separate days · not registered', 13, 1.0 if abs(t - cut) < 1.5 else 0.0, accent=CYAN)
    if t < cut: cv.text((W - 30, 80), 'MOSTLY EMPTY DESERT', 20, TEXT, oc(seg(t, 2, 3)), anchor='ra')
    else: cv.text((W - 30, 80), 'ROADS, BUILDINGS, IRRIGATED LAND', 20, TEXT, oc(seg(t, cut + 2, cut + 3)), anchor='ra'); cv.text((W - 30, 108), 'cover almost all of this area (NASA)', 15, MUTED, oc(seg(t, cut + 3, cut + 4)), anchor='ra', bold=False)
    return cv
def D5(t, d, X):
    cv = Canvas(text_card_bg()); cv.text((70, 56), 'A NOTE ON METHOD', 15, AMBER, anchor='la', spacing=0.25)
    card_rows(cv, t, [('EVERY IMAGE CARRIES', 'Its source, its instrument and its year'), ('MOST COME FROM', 'ASTER, an instrument on a satellite'), ('ONE IS A PHOTOGRAPH', 'Taken by an astronaut with a Nikon camera'),
                      ('NEVER', 'Moving footage · never overlaid on each other'), ('ONE IMAGE', 'Year only: NASA\'s text and caption disagree on the month')], y0=110, gap=76, t0=1.0, step=3.6, px=26); return cv
def E1(t, d, X):
    cv = Canvas(text_card_bg()); keys = ['2000', '2002a', '2002b', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011']
    labs = ['2000', 'FEB 2002', 'OCT 2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011']
    tw, th, gx, gy = 220, 124, 14, 14; x0 = (W - (4 * tw + 3 * gx)) / 2; y0 = 66
    for i, (kk, lab) in enumerate(zip(keys, labs)):
        k = oc(seg(t, 0.6 + i * 1.45, 1.1 + i * 1.45))
        if k <= 0: continue
        x = x0 + (i % 4) * (tw + gx); y = y0 + (i // 4) * (th + gy + 14); tile = view(kk, R_PALM).resize((tw, th), Image.LANCZOS)
        cv.o.paste(tile.convert('RGBA'), (int(x), int(y + (1 - k) * 8)), Image.new('L', (tw, th), int(255 * k)))
        cv.text((x + 6, y + th + 3), lab, 13, AMBER, k, anchor='la')
    cv.pill((22, 20), 'NASA ASTER · 12 images, 2000–2011 · colours as published · same crop of each', 13, 1.0, accent=AMBER); return cv
def E2(t, d, X):
    cut = 15.5
    if t < cut: r = lerp_rect((1475, 1002, 960, 540), (1500, 1020, 900, 506), t / cut); lab = 'PALM JUMEIRAH'; note = 'NASA CAPTION: ringed by a circular storm barrier'; c = (1840, 1290)
    else: r = lerp_rect((1066, 2461, 1120, 630), (1090, 2480, 1060, 596), (t - cut) / (d - cut)); lab = 'PALM JEBEL ALI'; note = 'NASA CAPTION: mostly undeveloped in 2022'; c = (1626, 2776)
    cv = Canvas(view('iss', r)); cv.chip(ISSCHIP); lt = t if t < cut else t - cut
    cv.callout(to_screen(r, c), lab, lt, 1.5, (-170, -170), r=185 if lab == 'PALM JUMEIRAH' else 200, px=19); cv.text((24, 66), note, 14, MUTED, oc(seg(lt, 6, 7)), anchor='la', bold=False)
    cv.text((W - 24, 66), 'APRIL 2022', 18, AMBER, anchor='ra', spacing=0.2); return cv
def E4(t, d, X):
    u = sm(seg(t, 11.0, 14.0)); r = lerp_rect(R_PALM, (170, 1470, 740, 416), t / d); im = dissolve(view('2000', r), view('2003', r), u); cv = Canvas(dim(im, 1 - 0.38 * sm(seg(t, 1.0, 2.0))))
    cv.chip(ASTER('2000') if u < 0.5 else ASTER('2003')); yearlabel(cv, '2000' if u < 0.5 else '2003', t if u < 0.5 else t - 11, 0.2, px=44)
    cv.text((60, 330), 'A map drawn in 2000 would show open water here.', 22, TEXT, oc(seg(t, 3.0, 4.0)) * (1 - sm(seg(t, 10.0, 11.0))), anchor='la')
    cv.text((60, 330), 'By November 2003, that map would be wrong.', 22, TEXT, oc(seg(t, 14.5, 15.5)), anchor='la')
    cv.text((60, 380), 'Sand from the sea floor · a ring of rock', 20, AMBER, oc(seg(t, 18.0, 19.0)), anchor='la'); cv.text((60, 410), 'A coastline stops being a fixed line.', 20, AMBER, oc(seg(t, 21.0, 22.0)), anchor='la'); return cv
def E5(t, d, X):
    if t < 8.0: key, r, chip, lab = '2000', lerp_rect(R_PALM, (170, 1470, 740, 416), t / 8.0), ASTER('2000'), 'NOVEMBER 2000: OPEN SEA'
    elif t < 16.0: key, r, chip, lab = '2003', lerp_rect(R_PALM, (170, 1470, 740, 416), (t - 8) / 8.0), ASTER('2003'), 'NOVEMBER 2003: A PALM INSIDE ITS RING'
    else: key, r, chip, lab = 'iss', lerp_rect(H3A, H3B, smr(seg(t, 20.0, 26.0))), ISSCHIP, 'APRIL 2022: THE PALM ISLANDS FROM ORBIT'
    cv = Canvas(view(key, r)); cv.chip(chip); lt = t if t < 8 else (t - 8 if t < 16 else t - 16); cv.text((24, 62), lab, 20, AMBER, oc(seg(lt, 0.3, 1.2)), anchor='la', spacing=0.1)
    s = lambda p: to_screen(r, p)
    if key == '2003': cv.callout(s((188, 1650)), 'THE RING', lt, 2.5, (80, 110), r=14)
    if key == 'iss': cv.callout(s((1840, 1290)), 'PALM JUMEIRAH · RING', lt, 2.0, (-170, -170), r=165, px=18); cv.callout(s((1626, 2776)), 'PALM JEBEL ALI · RING', lt, 9.0, (-170, -150), r=180, px=18)
    return cv
def E6(t, d, X):
    cv = Canvas(text_card_bg()); k = oc(seg(t, 0.4, 1.4)) * (1 - sm(seg(t, d - 1.5, d)))
    cv.text((W / 2, 150), 'IMAGERY', 14, AMBER, k, anchor='ma', spacing=0.3); cv.text((W / 2, 190), 'NASA Earth Observatory', 30, TEXT, k, anchor='ma')
    cv.text((W / 2, 250), 'ASTER on the Terra satellite', 24, TEXT, k, anchor='ma', bold=False); cv.text((W / 2, 300), 'Astronaut photograph ISS067-E-3785', 24, TEXT, k, anchor='ma', bold=False)
    cv.text((W / 2, 336), 'ISS Crew Earth Observations', 20, MUTED, k, anchor='ma', bold=False)
    cv.text((W / 2, 420), 'Orbital Atlas · EP002', 15, MUTED, k, anchor='ma', spacing=0.3); return cv

# id, start s, duration s, VO line numbers (1-based among VO lines), function
SCENES = [('H1', 0, 10, [1], H1), ('H2', 10, 8, [2], H2), ('H3', 18, 11, [3], H3), ('H4', 29, 9, [4], H4), ('A1', 38, 20, [5], A1), ('A2', 58, 23, [6, 7], A2), ('A3', 81, 27, [8, 9], A3),
          ('B1', 108, 13, [10], B1), ('B2', 121, 15, [11], B2), ('B3', 136, 20, [12], B3), ('B4', 156, 17, [13], B4), ('B5', 173, 30, [14], B5), ('B6', 203, 15, [15], B6), ('B7', 218, 14, [16], B7),
          ('C1', 232, 20, [17], C1), ('C2', 252, 20, [18], C2), ('C3', 272, 18, [19], C3), ('C4', 290, 23, [20], C4), ('C5', 313, 21, [21], C5), ('C6', 334, 25, [22], C6),
          ('D1', 359, 17, [23], D1), ('D2', 376, 17, [24], D2), ('D5', 393, 30, [25], D5), ('E1', 423, 20, [26], E1), ('E2', 443, 32, [27], E2), ('E4', 475, 27, [28], E4), ('E5', 502, 27, [29], E5), ('E6', 529, 9, [30], E6)]
