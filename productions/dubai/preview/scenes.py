"""EP002 scene functions, V2. Each takes (t, dur, X) with local time t (s) and returns a Canvas (base frame + overlay); captions are added by the driver.
Geography/dates follow SCRIPT_LOCK and visuals/VISUAL_PRODUCTION_PLAN.md. Landmark coordinates come from landmarks.json (deterministic, see landmarks.py);
crops are original-pixel rects (x, y, w, h) clamped inside each source so no pixel outside the real image is ever shown.
Layer rules: satellite pixels are shown as published (never painted or filled); dimming/tone-matching is a labelled UI treatment of the Cesium render only."""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from kit import *

# ------------------------------------------------------------------ labels derived from the asset key (no hand-typed years)
YEAR = {'2000': '2000', '2002a': '2002', '2002b': '2002', '2003': '2003', '2004': '2004', '2005': '2005', '2006': '2006', '2007': '2007', '2008': '2008', '2009': '2009', '2010': '2010', '2011': '2011', 'palm2': '2006'}
DATE = {'2000': 'NOVEMBER 2000', '2002a': 'FEBRUARY 2002', '2002b': 'OCTOBER 2002', '2003': 'NOVEMBER 2003', 'iss': 'APRIL 2022'}   # month only where NASA's captions give it; 2011 = year only
def chip_for(key): return ISSCHIP if key == 'iss' else f'NASA ASTER · {YEAR[key]} · colours as published'
ISSCHIP = 'NASA ISS astronaut photograph · 2022 · not satellite imagery'
def date_for(key): return DATE.get(key, YEAR.get(key, ''))
def yearlabel(cv, s, t, t0=0.4, px=30): cv.text((W - 24, 40), s, px, AMBER, oc(seg(t, t0, t0 + 0.7)), anchor='ra', spacing=0.14)
def stamp(cv, key, t, t0=0.3, px=30):
    cv.chip(chip_for(key)); yearlabel(cv, date_for(key), t, t0, px)

R_PALM = (140, 1445, 800, 450)
H3A, H3B = (1155, 820, 1600, 900), (826, 2326, 1600, 900)
C1A, C1B, C1C, C1D = (60, 2780, 1280, 720), (915, 1905, 960, 540), (878, 1000, 1280, 720), (1700, 150, 1280, 720)
PJ2, PJA2 = lm('palm2', 'palm_jumeirah_ring'), lm('palm2', 'palm_jebel_ali_ring'); WORLD2 = lm('palm2', 'the_world')[0]; DEIRA2 = lm('palm2', 'deira_reclaimed_land')[0]
PJI, PJAI = lm('iss', 'palm_jumeirah_ring'), lm('iss', 'palm_jebel_ali_ring')
FRONDS_2002B = tuple(LMJ['woc']['2002b']['fronds_centroid']['center'])
def zoom_ring(cv, rect, c, r, text, t, t0, dxy, px=18, out=None, pad=1.12):
    """ring around a landmark whose centre/radius come from landmarks.json; radius scales with the crop"""
    cv.callout(to_screen(rect, c), text, t, t0, dxy, r=max(14, r * W / rect[2] * pad), px=px, out=out)

# ------------------------------------------------------------------ HOOK
def H1(t, d, X):
    r = lerp_rect(R_PALM, (170, 1470, 740, 416), t / d); cv = Canvas(view('2000', r)); stamp(cv, '2000', t); return cv
def H2(t, d, X):
    r = lerp_rect(R_PALM, (170, 1470, 740, 416), t / d); cv = Canvas(view('2003', r)); stamp(cv, '2003', t); return cv
def H3(t, d, X):
    u = smr(seg(t, 0.5, d - 0.5)); cv = Canvas(view('iss', lerp_rect(H3A, H3B, u))); stamp(cv, 'iss', t); return cv
def H4(t, d, X):
    r = lerp_rect((500, 1100, 2368, 1332), (580, 1140, 2200, 1238), t / d); base = view('palm2', r)
    k = sm(seg(t, 2.2, 3.4)); cv = Canvas(dim(base, 1 - 0.55 * k)); cv.chip(chip_for('palm2')); cv._center = True
    cv.kinetic((W / 2, H * 0.36), 'HOW DUBAI CHANGED', 40, 3.0, t, spacing=0.14, per=0.04, a=k); cv.kinetic((W / 2, H * 0.36 + 56), 'THE MAP OF THE EARTH', 40, 3.6, t, spacing=0.14, per=0.04, a=k)
    cv.text((W / 2, H * 0.36 + 120), 'ORBITAL ATLAS · EP002', 16, MUTED, a=k * sm(seg(t, 5.0, 6.0)), anchor='ma', spacing=0.3); return cv

# ------------------------------------------------------------------ ACT 1
A2_START = (550, 600, 2400, 1350)
def pjson(f): return os.path.join(os.path.dirname(f), 'p' + os.path.basename(f)[1:-4] + '.json')
def tone_match(img, ref):
    a = np.asarray(img, np.float32); r = np.asarray(ref, np.float32).reshape(-1, 3); m, s = a.reshape(-1, 3).mean(0), a.reshape(-1, 3).std(0) + 1e-3
    return (a - m) / s * r.std(0) + r.mean(0)
def A1(t, d, X):
    fr = X['a1_frames']; n = len(fr); i = min(int(t * FPS), n - 1)
    ces = Image.open(fr[i]).convert('RGB').resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 60, 2)); pj = json.load(open(pjson(fr[i])))
    u = seg(t, 15.8, 19.0)
    if u > 0:                                                  # soft Palm/Dubai-centred dissolve into the ASTER-2000 start crop; the Cesium render is tone-matched (UI treatment), ASTER untouched
        last = json.load(open(pjson(fr[-1]))); ref = view('2000', A2_START)
        k = sm(seg(t, 13.0, 17.0)) * 0.7; ces = Image.fromarray((np.asarray(ces, np.float32) * (1 - k) + tone_match(ces, ref) * k).clip(0, 255).astype(np.uint8))
        c = last['dubai'][:2]; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); D = np.hypot(xx - c[0], yy - c[1]); far = float(np.hypot(max(c[0], W - c[0]), max(c[1], H - c[1])))
        e = smr(u); Rr = (0.02 * H) * (1 - e) + (far + 0.36 * H) * e; v = np.clip((Rr - D) / (0.30 * H), 0, 1); m = (v * v * (3 - 2 * v))[..., None]
        base = Image.fromarray((np.asarray(ces, np.float32) * (1 - m) + np.asarray(ref, np.float32) * m).clip(0, 255).astype(np.uint8))
    else: base = ces
    cv = Canvas(base); ca = 1 - sm(seg(t, 17.0, 18.2))
    if ca > 0: cv.chip('NASA GIBS · Blue Marble + Landsat · 3D globe view (CesiumJS)', ca)
    else: cv.chip(chip_for('2000'), sm(seg(t, 18.2, 19.0)))
    def lab(key, s, t0, t1, px=17):
        x, y, vis = pj[key]; a = oc(seg(t, t0, t0 + 0.6)) * (1 - sm(seg(t, t1, t1 + 0.6))) * vis * ca
        if a > 0.01 and 20 < x < W - 20 and 40 < y < H - 90: cv.text((x, y - 26), s, px, AMBER, a, anchor='ms', spacing=0.2)
    lab('gulf', 'PERSIAN GULF', 2.8, 9.0); lab('uae', 'UNITED ARAB EMIRATES', 4.2, 10.0)
    x, y, vis = pj['dubai']; a = oc(seg(t, 7.0, 7.8)) * vis * ca
    if a > 0.01 and 20 < x < W - 20 and 40 < y < H - 90: cv.ring((x, y), 7, a, 2); cv.text((x + 12, y - 4), 'DUBAI', 18, AMBER, a, anchor='lm', spacing=0.2)
    return cv
CITY_PT = (coast_x('2000', 1250) + 140, 1250); DESERT_PT = (coast_x('2000', 1500) + 1000 if coast_x('2000', 1500) else 1900, 1500)
def A2(t, d, X):
    u = smr(seg(t, 0.8, d - 1.0)); r = lerp_rect(A2_START, R_PALM, u); cv = Canvas(view('2000', r)); stamp(cv, '2000', t, 0.3); yearlabel(cv, '2000', t, 0.3); s = lambda p: to_screen(r, p)
    cv.callout(s(CITY_PT), 'CITY HUGS THE SHORE', t, 2.5, (80, -60), out=9.0, ring=False)
    cv.callout(s(DESERT_PT), 'EMPTY DESERT INLAND', t, 4.5, (-70, 60), out=10.5, ring=False)
    zoom_ring(cv, r, SITE_C, SITE_R, 'OFFSHORE: NOTHING BUILT YET', t, 14.5, (150, -90), px=17)
    return cv

def dots_field(ss, rect, n, k, col, seed=7, r=3.0):
    rng = np.random.default_rng(seed); x0, y0, x1, y1 = rect
    for i in range(int(n * k)): ss.ellipse((x0 + rng.random() * (x1 - x0), y0 + rng.random() * (y1 - y0)), r, fill=col)
def card_rows(cv, t, rows, x=70, y0=150, gap=96, t0=0.5, step=0.9, px=34, wmax=None):
    for i, (lab, val) in enumerate(rows):
        k = oc(seg(t, t0 + i * step, t0 + i * step + 0.6)); y = y0 + i * gap
        cv.d.line([(x, y - 14), (x + (wmax or (W - 2 * x)) * k, y - 14)], fill=MUTED + (110,), width=1)
        cv.text((x, y), lab, 14, MUTED, k, anchor='la', spacing=0.2); cv.text((x, y + 24 + (1 - k) * 10), val, px, TEXT, k, anchor='la')
def A3(t, d, X):
    """plan ledger on one continuous layout (no card cuts): timeline strip on top, ledger rows that accumulate on the left, a schematic visual on the right that keeps moving"""
    cv = Canvas(text_card_bg()); ss = SS(); cv.text((70, 52), 'A BLANK PAGE ON THE COAST', 15, AMBER, anchor='la', spacing=0.25)
    x0 = 70; ty = 104; cv.d.line([(x0, ty), (W - x0, ty)], fill=MUTED + (120,), width=1)                  # timeline strip: 1990s -> 2000 -> early 2000s
    for lab, tt in (('1990s', 0.0), ('EARLY 2000s', 1.0)):
        cv.d.ellipse([x0 + tt * (W - 2 * x0) - 4, ty - 4, x0 + tt * (W - 2 * x0) + 4, ty + 4], fill=MUTED + (200,)); cv.text((x0 + tt * (W - 2 * x0), ty + 10), lab, 12, MUTED, anchor='ma' if 0 < tt < 1 else ('la' if tt == 0 else 'ra'), spacing=0.15)
    pos = x0 + (W - 2 * x0) * smr(seg(t, 0.5, d - 1.0)); cv.d.polygon([(pos, ty - 8), (pos - 6, ty - 18), (pos + 6, ty - 18)], fill=AMBER + (255,))
    def row(y, lab, val, t0, px=21):
        k = oc(seg(t, t0, t0 + 0.7)); cv.d.line([(70, y - 8), (70 + 500 * k, y - 8)], fill=MUTED + (110,), width=1); cv.text((70, y), lab, 12, MUTED, k, spacing=0.2); cv.text((70, y + 18 + (1 - k) * 8), val, px, TEXT, k)
    row(150, 'NASA EARTH OBSERVATORY', 'Hundreds of artificial islands', 0.6); row(210, 'PURPOSE', 'To expand the beachfront for tourism', 2.4)
    row(280, 'PLANS FROM THE 1990s', 'One project: The World', 9.9); row(340, 'THE PLAN INCLUDED', 'About 300 small islands', 11.4)
    row(410, 'EARLY 2000s · NASA', 'Little built beyond shallow Gulf water', 19.6)
    rx0, ry0, rx1, ry1 = 610, 140, 900, 390                                                  # right-hand visual: schematic dots (one dot = one planned island, not geography) / the blank page
    ss.rect(rx0, ry0, rx1, ry1, outline=MUTED + (90,), width=1, r=6)
    dots_field(ss, (rx0 + 14, ry0 + 14, rx1 - 14, ry1 - 14), 300, oc(seg(t, 1.0, 9.0)) * (1 - sm(seg(t, 19.0, 21.0))), CYAN + (210,), r=2.6)
    if t >= 9.5:
        n = int(300 * oc(seg(t, 10.0, 17.0))); a = sm(seg(t, 10.0, 11.0)) * (1 - sm(seg(t, 19, 20)))
        cv.text((rx1, ry1 + 30), f'{n}', 30, AMBER, a, anchor='ra'); cv.text((rx1 - 58, ry1 + 20), 'ISLANDS IN THE PLAN (SCHEMATIC)', 11, MUTED, a, anchor='ra', spacing=0.1)
    if t >= 19.0:
        kb = oc(seg(t, 19.5, 21.0)); cv.text(((rx0 + rx1) / 2, (ry0 + ry1) / 2 - 10), 'THE BLANK PAGE', 20, TEXT, kb, anchor='ma', spacing=0.25)
        sx = rx0 + (rx1 - rx0) * ((t - 19.5) % 4.0) / 4.0; ss.line([(sx, ry0 + 6), (sx, ry1 - 6)], CYAN + (int(90 * kb),), 1.2)
    layer(cv, ss); return cv

# ------------------------------------------------------------------ ACT 2
def B1(t, d, X):
    u = smr(seg(t, 0.3, 11.5)); r = lerp_rect(R_PALM, (0, 1422, 480, 270), u); cv = Canvas(view('2002a', r)); stamp(cv, '2002a', t)
    pc = lm('woc', '2002a')[0] if False else tuple(LMJ['woc']['2002a']['early_stage_patch']['center'])
    cv.callout(to_screen(r, pc), 'FIRST EARLY STAGE', t, 6.0, (120, 90), r=30); return cv
def B2(t, d, X):
    c, rad = woc_ring('2002b'); r = lerp_rect(rect_c(c, 1050, dx=210), rect_c(c, 640, dx=60), smr(t / d)); cv = Canvas(view('2002b', r)); stamp(cv, '2002b', t)
    cv.callout(to_screen(r, (c[0] - rad, c[1])), 'CIRCULAR BREAKWATER', t, 3.0, (60, -120), r=14); cv.callout(to_screen(r, FRONDS_2002B), 'SANDY FRONDS', t, 7.5, (200, 100), r=14); return cv

def sea_gradient():
    y = np.linspace(0, 1, H)[:, None, None]; a = np.array([8, 14, 22], np.float32) * (1 - y) + np.array([6, 18, 30], np.float32) * y
    return np.broadcast_to(a, (H, W, 3)).astype(np.uint8)
SURF = 205
def water_bg(t):
    img = np.array(sea_gradient()); y = np.arange(H)[:, None, None]; wat = (y >= SURF)
    c = np.array([18, 70, 104], np.float32) * (1 - np.clip((y - SURF) / (H - SURF), 0, 1) * 0.72) + 0
    img = np.where(wat, np.broadcast_to(c, (H, W, 3)), img).astype(np.uint8); return Image.fromarray(img)
def seabed_pts(): return [(x, 440 + 9 * math.sin(x / 70.0) + 5 * math.sin(x / 23.0)) for x in range(-5, W + 6, 5)]
def dredger(ss, x, y, col=(52, 64, 80)):
    ss.poly([(x - 92, y - 6), (x + 92, y - 6), (x + 74, y + 16), (x - 80, y + 16)], fill=col + (255,), outline=CYAN + (255,))
    ss.rect(x - 78, y - 36, x - 34, y - 6, fill=(214, 222, 232, 255)); ss.rect(x - 70, y - 50, x - 46, y - 36, fill=(214, 222, 232, 255)); ss.rect(x - 62, y - 62, x - 54, y - 50, fill=AMBER + (255,))
    ss.rect(x - 24, y - 20, x + 62, y - 6, fill=(36, 44, 56, 255)); ss.line([(x + 70, y - 8), (x + 100, y - 26)], (214, 222, 232, 255), 2.4)
def B3(t, d, X):
    """cross-section: sand is dredged from the Gulf floor, sprayed to the island site and protected by rock breakwaters (method as described by NASA Earth Observatory; no volumes)"""
    cv = Canvas(water_bg(t)); ss = SS(); sx = 250 + 6 * math.sin(t * 0.9); sb = seabed_pts()
    ss.poly(sb + [(W + 5, H + 5), (-5, H + 5)], fill=(150, 124, 86, 255)); ss.poly([(x, y + 38) for x, y in sb] + [(W + 5, H + 5), (-5, H + 5)], fill=(116, 94, 64, 255))
    ss.line([(x, SURF + 2.2 * math.sin(x / 26.0 - t * 2.4)) for x in range(0, W + 1, 8)], (190, 232, 240, 170), 1.4)
    rngp = np.random.default_rng(21)
    for i in range(46): px_ = (rngp.random() * W + t * (6 + 10 * rngp.random())) % W; py_ = SURF + 14 + rngp.random() * 220 + 3 * math.sin(t * 0.8 + i); ss.ellipse((px_, py_), 1.3, fill=(170, 220, 235, 80))
    kd = seg(t, 3.0, 8.0)                                              # suction pipe from the drag head on the sea floor up to the vessel; sand rises along it
    hx, hy = 150.0, 440 + 9 * math.sin(150 / 70.0) + 5 * math.sin(150 / 23.0)
    ss.ellipse((hx, hy + 12 + 10 * kd), 26 * kd, 7 * kd, fill=(98, 78, 52, 255)) if kd > 0 else None      # a dip in the floor where the sand is taken
    ss.line([(sx - 60, SURF + 12), (hx + 6, hy - 6)], (150, 160, 172, 255), 5.0); ss.rect(hx - 14, hy - 10, hx + 14, hy + 2, fill=(110, 118, 130, 255), r=2)
    dredger(ss, sx, SURF - 8)
    if kd > 0:
        for i in range(14):
            ph = (i / 14 + t * 0.5) % 1; px_, py_ = hx + 6 + (sx - 60 - hx - 6) * ph, hy - 6 + (SURF + 12 - hy + 6) * ph; ss.ellipse((px_, py_), 2.6, fill=(238, 208, 150, int(255 * kd)))
    ka = seg(t, 8.5, 12.5); bx, by = sx + 100, SURF - 34; ex = 640.0                                  # rainbowing arc: a plume of sand thrown to the island site
    if ka > 0:
        pts = [(bx + (ex - bx) * s, by - 78 * math.sin(math.pi * s) + (SURF - by) * s * s) for s in np.linspace(0, 1, 60)]; vis = max(2, int(60 * ka)); ss.line(pts[:vis], (238, 208, 150, 255), 5.0)
        for i in range(10): s = ((i / 10 + t * 0.7) % 1) * ka; p = (bx + (ex - bx) * s, by - 78 * math.sin(math.pi * s) + (SURF - by) * s * s); ss.ellipse(p, 2.4, fill=(255, 236, 190, 230))
    km = seg(t, 9.5, 16.0)                                                                             # the island pile grows from the sea floor to above the surface
    if km > 0:
        top = 440 - (440 - (SURF - 26)) * oc(km); l, r_ = 570.0, 800.0
        ss.poly([(l - 70, 452), (l + 34, top), (r_ - 34, top), (r_ + 70, 452)], fill=(190, 160, 108, 255))
    kr = seg(t, 13.5, 16.5)
    if kr > 0:
        for side, x_top, x_base in ((-1, 604.0, 500.0), (1, 766.0, 870.0)):
            for i in range(8):
                f = i / 7.0; px_ = x_top + (x_base - x_top) * f; py_ = (SURF - 26) + (452 - (SURF - 26)) * f; a = int(255 * min(1, kr * 2 - f))
                if a > 0: ss.poly([(px_ - 12, py_ - 7), (px_ + 12, py_ - 9), (px_ + 13, py_ + 8), (px_ - 11, py_ + 9)], fill=(104, 108, 116, a), outline=(30, 36, 44, a))
    kp = seg(t, 16.5, 19.5)
    if kp > 0: ss.rect(0, 452, W, H, outline=None, fill=(255, 214, 120, int(45 * math.sin(math.pi * kp))))
    layer(cv, ss)
    cv.callout((40, 478), 'SEA FLOOR · SAND', t, 1.0, (0, 0), ring=False, px=15, col=(250, 232, 190))
    cv.callout((hx + 18, 330), 'DREDGED FROM THE GULF FLOOR', t, 4.5, (30, -30), ring=False, px=15, col=TEXT)
    cv.callout((ex - 40, SURF - 50), 'PLACED WHERE THE ISLAND WILL BE', t, 10.5, (40, -64), ring=False, px=15, col=TEXT)
    cv.callout((528, 396), 'ROCK BREAKWATER', t, 14.2, (-60, -40), ring=False, px=15, col=(210, 214, 222))
    cv.pill((W / 2 - 190, 486), 'THE MATERIAL WAS ALREADY THERE, UNDERWATER', 15, oc(seg(t, 16.8, 17.8)), accent=AMBER)
    cv.pill((22, 20), 'ILLUSTRATION · not to scale · method as described by NASA Earth Observatory', 14, 1.0, accent=CYAN); return cv

def B4(t, d, X):
    """two-step schematic: (1) GPS-guided placement (plan view), (2) vibroflot compaction with stone (cross-section)"""
    cv = Canvas(text_card_bg((10, 26, 40))); ss = SS(); pw = 430; xa, xb = 30, W - 30 - pw; ya, yb = 84, 470
    for x0, ttl, t0 in ((xa, '1', 0.4), (xb, '2', 8.0)):
        k = oc(seg(t, t0, t0 + 0.6)); ss.rect(x0, ya, x0 + pw, yb, outline=CYAN + (int(110 * k),), width=1, r=8); cv.text((x0 + 16, ya + 12), ttl, 22, AMBER, k)
    cv.text((xa + 44, ya + 17), 'SHIPS GUIDED BY GPS PLACE THE SAND', 15, TEXT, oc(seg(t, 0.6, 1.4))); cv.text((xb + 44, ya + 17), 'A VIBROFLOT COMPACTS IT WITH STONE', 15, TEXT, oc(seg(t, 8.2, 9.0)))
    # panel 1: plan view of a placement grid, satellite signal, ship lanes
    gx0, gy0, cw, ch, nx, ny = xa + 50, ya + 120, 54, 40, 7, 6; k1 = oc(seg(t, 0.8, 1.8))
    for j in range(ny):
        for i in range(nx):
            x, y = gx0 + i * cw, gy0 + j * ch; ss.rect(x, y, x + cw - 3, y + ch - 3, outline=MUTED + (int(120 * k1),), width=0.8)
    prog = seg(t, 2.5, 7.5) * nx * ny; sat = (xa + pw - 70, ya + 62 + 4 * math.sin(t * 1.5))
    for n in range(int(prog) + 1):                                                    # boustrophedon lanes: cells fill with sand as the ship passes
        j, i = divmod(n, nx); i = i if j % 2 == 0 else nx - 1 - i
        if n < nx * ny:
            f = 1.0 if n < int(prog) else prog - int(prog); x, y = gx0 + i * cw, gy0 + j * ch; ss.rect(x, y, x + cw - 3, y + ch - 3, fill=(214, 184, 126, int(235 * f)))
    n = min(int(prog), nx * ny - 1); j, i = divmod(n, nx); i = i if j % 2 == 0 else nx - 1 - i; shx, shy = gx0 + i * cw + cw / 2, gy0 + j * ch + ch / 2
    if seg(t, 2.0, 2.5) > 0:
        ss.poly([(shx - 20, shy - 8), (shx + 14, shy - 8), (shx + 22, shy), (shx + 14, shy + 8), (shx - 20, shy + 8)], fill=(214, 222, 232, 255), outline=CYAN + (255,))
        for a in (18, 30, 42): ss.arc(sat, a, 100, 180, CYAN + (int(180 * (1 - a / 60)),), 1.4)
        ss.dashed([sat, (shx, shy)], CYAN + (160,), 1.2, 6, 5, offset=t * 30)
    ss.rect(sat[0] - 10, sat[1] - 5, sat[0] + 10, sat[1] + 5, fill=CYAN + (255,)); ss.rect(sat[0] - 28, sat[1] - 2, sat[0] - 12, sat[1] + 2, fill=MUTED + (255,)); ss.rect(sat[0] + 12, sat[1] - 2, sat[0] + 28, sat[1] + 2, fill=MUTED + (255,))
    cv.text((sat[0], sat[1] - 24), 'GPS', 13, CYAN, oc(seg(t, 1.0, 1.6)), anchor='ma', spacing=0.2); cv.text((gx0, gy0 + ny * ch + 6), 'PLACEMENT AREA · PLAN VIEW', 12, MUTED, k1, spacing=0.15)
    # panel 2: cross-section, loose sand packs down around a vibrating probe, stone column forms
    sx0, sy0, sx1, sy1 = xb + 40, ya + 90, xb + pw - 40, yb - 56; k2 = oc(seg(t, 8.3, 9.0)); ss.rect(sx0, sy0, sx1, sy1, fill=(168, 140, 96, int(255 * k2)))
    rng = np.random.default_rng(5); n_g = 160; gx = rng.uniform(sx0 + 8, sx1 - 8, n_g); gy = rng.uniform(sy0 + 8, sy1 - 8, n_g); cx = (sx0 + sx1) / 2; pk = sm(seg(t, 11.5, 15.0))
    for i in range(n_g):
        pull = pk * 0.6 * (cx - gx[i]) / max(abs(gx[i] - cx), 1) * min(1, abs(gx[i] - cx) / 80) * 30; dn = pk * 14 * (1 - (gy[i] - sy0) / (sy1 - sy0))
        ss.ellipse((gx[i] + pull, gy[i] + dn), 3.2, fill=(96, 74, 48, int(255 * k2)))
    kp = seg(t, 9.5, 11.5); dep = sy0 - 40 + (sy1 - sy0 + 20) * sm(kp) if kp > 0 else None
    if dep is not None:
        jit = 2.2 * math.sin(t * 40) * (1 if t > 11.5 else 0); stone = seg(t, 12.0, 15.5)
        ss.rect(cx - 9 + jit, sy0 - 60, cx + 9 + jit, dep, fill=(156, 164, 174, 255)); ss.poly([(cx - 9 + jit, dep), (cx + 9 + jit, dep), (cx + jit, dep + 14)], fill=(120, 128, 138, 255))
        for r_ in (16, 28, 40): ss.arc((cx + jit, dep), r_, 0, 360, CYAN + (int(150 * (1 - r_ / 48) * (1 if t > 11.5 else 0)),), 1.2)
        for q in range(int(10 * stone)): ss.ellipse((cx + (-13 + 26 * ((q * 37) % 10) / 9.0), sy1 - 12 - q * (sy1 - sy0 - 20) / 10), 6.5, fill=(112, 116, 124, 255), outline=(40, 46, 56, 255))
    layer(cv, ss)
    cv.text((xb + 44, sy0 - 28), 'VIBROFLOT', 13, TEXT, oc(seg(t, 9.8, 10.6)), spacing=0.12); cv.text((cx, sy1 + 12), 'STONE COLUMN · SOLIDIFIED LAND', 14, CYAN, oc(seg(t, 14.0, 15.0)), anchor='ma', spacing=0.1)
    cv.pill((22, 20), 'ILLUSTRATION · schematic, not to scale · method as described by NASA Earth Observatory', 14, 1.0, accent=CYAN); return cv

def B5(t, d, X):
    c, _ = woc_ring('2003'); r = lerp_rect(rect_c(c, 900, dx=150), rect_c(c, 760, dx=110), t / d)
    a, b = view('2002b', r), view('2003', r); u = sm(seg(t, 11.5, 14.5)); cv = Canvas(dissolve(a, b, u)); key = '2002b' if u < 0.5 else '2003'; stamp(cv, key, t if u < 0.5 else t - 11.5, 0.3)
    c2, r2 = woc_ring('2002b'); c3, r3 = woc_ring('2003')
    cv.callout(to_screen(r, (c2[0] - r2, c2[1])), 'RING ALREADY IN PLACE', t, 4.5, (60, -120), r=14, out=11.2); cv.callout(to_screen(r, FRONDS_2002B), 'FRONDS STILL SAND', t, 7.5, (200, 90), r=14, out=11.2)
    cv.callout(to_screen(r, c3), 'A COMPLETE PALM', t, 17.0, (200, 100), r=14, out=24.0)
    cv.pill((W - 24, 84), 'SEPARATE IMAGES · NOT REGISTERED · NO WIPE', 13, sm(seg(t, 12.0, 13.0)) * (1 - sm(seg(t, 22, 23))), accent=CYAN, anchor='right')
    cv.pill((24, 98), 'BUILDINGS AND VEGETATION COME LATER · 2004–2008', 14, sm(seg(t, 24.5, 25.5)), accent=AMBER); return cv
def B6(t, d, X):
    """five dated stills with DIFFERENT framings on the same palm (crown, trunk, shore, wide) instead of five identical crops"""
    spec = [('2004', rect_c(SITE_C, 760, dx=20), rect_c(SITE_C, 660, dx=0)), ('2005', rect_c(SITE_C, 560, dx=190, dy=70), rect_c(SITE_C, 520, dx=230, dy=60)),
            ('2006', rect_c(SITE_C, 640, dx=-10), rect_c(SITE_C, 520, dx=-10, dy=-10)), ('2007', rect_c(SITE_C, 520, dx=250, dy=100), rect_c(SITE_C, 600, dx=210, dy=80)), ('2008', rect_c(SITE_C, 1250, dx=420, dy=-60), rect_c(SITE_C, 1100, dx=390, dy=-40))]
    n = len(spec); L = d / n; i = min(int(t // L), n - 1); lt = t - i * L; key, r0, r1 = spec[i]; r = lerp_rect(r0, r1, lt / L); im = view(key, r)
    if lt > L - 0.5 and i < n - 1: nk, nr0, _ = spec[i + 1]; im = dissolve(im, view(nk, nr0), (lt - (L - 0.5)) / 0.5)
    cv = Canvas(im); cv.chip(chip_for(key)); yearlabel(cv, YEAR[key], lt, 0.1, px=44); return cv
def B7(t, d, X):
    c, rad = PJ2; r = lerp_rect(C1B, (965, 1930, 860, 484), t / d); cv = Canvas(view('palm2', r)); cv.chip(chip_for('palm2'))
    zoom_ring(cv, r, c, rad, 'PALM JUMEIRAH', t, 1.5, (-190, -150), px=20)
    cv.text((24, 66), 'THE FIRST OF SEVERAL', 22, TEXT, oc(seg(t, 5.5, 6.5)), anchor='la', spacing=0.12); return cv

# ------------------------------------------------------------------ ACT 3
def C1(t, d, X):
    stops = [(C1A, 'PALM JEBEL ALI', PJA2), (C1B, 'PALM JUMEIRAH', PJ2), (C1C, 'THE WORLD', (WORLD2, 190)), (C1D, 'PALM DEIRA · EARLY STAGE (NASA CAPTION ORDER)', (DEIRA2, 110))]
    L = d / 4; i = min(int(t // L), 3); lt = t - i * L
    if i > 0 and lt < 1.6: r = lerp_rect(stops[i - 1][0], stops[i][0], smr(lt / 1.6))
    else: r = lerp_rect(stops[i][0], tuple(v * f for v, f in zip(stops[i][0], (1, 1, 0.94, 0.94))), (lt - 1.6) / (L - 1.6)) if lt >= 1.6 else stops[i][0]
    cv = Canvas(view('palm2', r)); cv.chip(chip_for('palm2')); c, rad = stops[i][2]
    zoom_ring(cv, r, c, rad, stops[i][1], lt, 1.0 if i else 0.4, (-60, -190) if i != 1 else (-190, -150), px=19, out=L - 0.5)
    cv.text((W - 24, 40), f'{i + 1} / 4 · SOUTH TO NORTH', 13, MUTED, anchor='ra', spacing=0.2); return cv

def palm_glyph(ss, cx, cy, s, col, p=1.0, lw=2.6):
    """stylised palm (crescent barrier + trunk + 17 fronds), drawn on progressively; an ILLUSTRATION, not a traced plan"""
    a = 190 + 160 * min(1, p * 2.0); ss.arc((cx, cy), 80 * s, 180 - 150 * 0 - 0, 180 + 360 * min(1, p * 1.4) - 0 if False else 180 + 360 * min(1, p * 1.4), col, lw) if False else None
    ss.arc((cx, cy), 82 * s, 150, 150 + 240 * min(1, p * 1.6), col, lw)
    ss.line([(cx, cy + 64 * s), (cx, cy + 64 * s - 100 * s * min(1, p * 1.6))], col, lw + 0.8)
    for k in range(-8, 9):
        f = min(1, max(0, p * 2.0 - 0.4 - abs(k) * 0.03)); ang = math.radians(k * 9.5); L = (54 - abs(k) * 1.6) * s * f
        x0, y0 = cx, cy - 28 * s + abs(k) * 1.8 * s; ss.line([(x0, y0), (x0 + L * math.sin(ang), y0 - L * math.cos(ang))], col, max(1.2, lw - 0.6))
def world_glyph(ss, cx, cy, s, col, p=1.0, n=300):
    rng = np.random.default_rng(11); blobs = [(-0.45, -0.1, 0.30, 0.34), (-0.40, 0.45, 0.14, 0.28), (0.05, -0.2, 0.18, 0.26), (0.12, 0.28, 0.14, 0.26), (0.48, -0.15, 0.30, 0.28), (0.62, 0.50, 0.12, 0.10)]
    ss.ellipse((cx, cy), 82 * s, fill=None, outline=col[:3] + (int(col[3] * 0.6) if len(col) > 3 else 150,), width=1)
    pts = []
    for i in range(n):
        b = blobs[i % len(blobs)]; px_, py_ = rng.normal(b[0], b[2] * 0.45), rng.normal(b[1], b[3] * 0.45)
        if px_ ** 2 + py_ ** 2 < 0.95: pts.append((cx + px_ * 70 * s, cy + py_ * 70 * s))
    for q in pts[:int(len(pts) * p)]: ss.ellipse(q, 1.7, fill=col)
def C2(t, d, X):
    cv = Canvas(text_card_bg((10, 22, 36))); ss = SS(); cv.pill((22, 20), 'ILLUSTRATION · stylised layouts, not traced from imagery', 14, 1.0, accent=CYAN)
    palm_glyph(ss, W * 0.27, H * 0.46, 1.6, AMBER + (255,), seg(t, 1.0, 6.0)); world_glyph(ss, W * 0.73, H * 0.46, 1.6, CYAN + (255,), seg(t, 8.5, 16.0))
    cv.text((W * 0.27, H * 0.76), 'A PALM TREE', 20, AMBER, oc(seg(t, 5.0, 6.0)), anchor='ma', spacing=0.2); cv.text((W * 0.73, H * 0.76), 'A MAP OF EARTH', 20, CYAN, oc(seg(t, 15.0, 16.0)), anchor='ma', spacing=0.2)
    cv.text((W * 0.73, H * 0.82), 'about 300 small islands planned', 14, MUTED, oc(seg(t, 16.5, 17.5)), anchor='ma', bold=False)
    cv.text((W / 2, 66), 'THREE PROJECTS · TWO DESIGNS · ONE COAST', 15, MUTED, 1.0, anchor='ma', spacing=0.25); layer(cv, ss); return cv
def C3(t, d, X):
    u = sm(seg(t, 8.0, 10.5)); im = dissolve(view('palm2', lerp_rect(C1D, (1760, 190, 1180, 664), t / d)), view('palm2', lerp_rect(C1C, (940, 1040, 1180, 664), seg(t, 6.0, d))), u); k = sm(seg(t, 2.0, 3.0))
    cv = Canvas(dim(im, 1 - 0.5 * k)); cv.chip(chip_for('palm2'))
    cv.text((60, 150), '2007 – 2008', 44, AMBER, oc(seg(t, 3.0, 4.0)), anchor='la'); cv.text((60, 212), 'THE GLOBAL RECESSION', 28, TEXT, oc(seg(t, 4.0, 5.0)), anchor='la')
    cv.text((60, 258), 'NASA: it delayed these projects', 20, MUTED, oc(seg(t, 5.0, 6.0)), anchor='la', bold=False)
    cv.text((60, 330), 'In the 2006 image: Palm Deira barely begun,', 17, TEXT, oc(seg(t, 12.0, 13.0)), anchor='la', bold=False); cv.text((60, 356), 'The World still under construction.', 17, TEXT, oc(seg(t, 12.6, 13.6)), anchor='la', bold=False); return cv
def C4(t, d, X):
    r = lerp_rect(C1C, (940, 1040, 1180, 664), t / d); cv = Canvas(dim(view('palm2', r), 0.32)); cv.chip('Background: NASA ASTER · 2006 · colours as published (not 2022)')
    cv.text((60, 120), '2022', 90, AMBER, oc(seg(t, 0.8, 1.8)), anchor='la')
    cv.text((60, 236), "Only a handful of The World's roughly 300 islands", 26, TEXT, oc(seg(t, 3.0, 4.0)), anchor='la'); cv.text((60, 272), 'had seen development.', 26, TEXT, oc(seg(t, 3.6, 4.6)), anchor='la')
    cv.text((60, 330), "NASA's caption for the astronaut's photograph", 17, MUTED, oc(seg(t, 6.0, 7.0)), anchor='la', bold=False)
    cv.text((60, 372), 'A statement about 2022. Nothing is assumed since.', 19, CYAN, oc(seg(t, 14.0, 15.0)), anchor='la'); return cv
def C5(t, d, X):
    r = lerp_rect((704, 0, 2368, 1332), (1500, 60, 1280, 720), smr(seg(t, 0.5, d - 0.5))); cv = Canvas(dim(view('palm2', r), 1 - 0.28 * sm(seg(t, 2, 3)))); cv.chip(chip_for('palm2'))
    cv.d.rectangle([W - 400, 112, W, 452], fill=(6, 10, 16, int(150 * sm(seg(t, 2.5, 3.5)))))
    def row(y, a, t0, col=TEXT, px=22, bold=True): cv.text((W - 40, y), a, px, col, oc(seg(t, t0, t0 + 0.8)), anchor='ra', bold=bold)
    row(150, 'PALM DEIRA', 3.0, AMBER, 30); row(190, 'scaled back and renamed', 4.0, TEXT, 20, False); row(222, 'THE DEIRA ISLANDS', 5.0, TEXT, 24)
    row(290, 'THE UNIVERSE', 9.5, AMBER, 30); row(330, 'another planned archipelago: put on hold', 10.5, TEXT, 20, False)
    row(400, 'DELAYED · SCALED BACK · ON HOLD', 15.0, CYAN, 22); row(430, 'words about plans, not the condition of the land', 16.0, MUTED, 17, False); return cv
def C6(t, d, X):
    cv = Canvas(text_card_bg((10, 22, 36))); ss = SS(); cv.pill((22, 20), 'ILLUSTRATION · stylised; facts per NASA Earth Observatory', 14, 1.0, accent=CYAN)
    cv.text((W / 2, 70), 'SAME METHOD: DREDGED SAND, PROTECTED BY ROCK', 15, MUTED, oc(seg(t, 0.5, 1.5)), anchor='ma', spacing=0.2)
    ss.line([(W / 2, 110), (W / 2, 440)], MUTED + (80,), 1)
    palm_glyph(ss, W * 0.25, H * 0.40, 1.1, AMBER + (255,), seg(t, 2.0, 6.0)); world_glyph(ss, W * 0.75, H * 0.40, 1.1, CYAN + (255,), seg(t, 12.0, 17.0))
    cv.text((W * 0.25, 290), 'PALM JUMEIRAH', 20, AMBER, oc(seg(t, 4.5, 5.5)), anchor='ma', spacing=0.16)
    cv.text((W * 0.25, 322), 'By 2011: vegetation covered most', 15, TEXT, seg(t, 6, 7), anchor='ma', bold=False); cv.text((W * 0.25, 344), 'of the fronds; many buildings on the trunk', 15, TEXT, seg(t, 6.6, 7.6), anchor='ma', bold=False)
    cv.text((W * 0.75, 290), 'THE WORLD', 20, CYAN, oc(seg(t, 14.5, 15.5)), anchor='ma', spacing=0.16)
    cv.text((W * 0.75, 322), 'In 2022: only a handful of roughly', 15, TEXT, seg(t, 16, 17), anchor='ma', bold=False); cv.text((W * 0.75, 344), '300 islands had seen development', 15, TEXT, seg(t, 16.6, 17.6), anchor='ma', bold=False)
    cv.text((W / 2, 420), 'SIMILAR METHOD · VERY DIFFERENT OUTCOMES', 24, AMBER, oc(seg(t, 20, 21)), anchor='ma', spacing=0.12); layer(cv, ss); return cv

# ------------------------------------------------------------------ ACT 4
def D1(t, d, X):
    u = sm(seg(t, 8.0, 10.0)); r1 = lerp_rect(C1A, (100, 2810, 1180, 664), t / d); r2 = lerp_rect(C1B, (950, 1930, 880, 495), t / d)
    cv = Canvas(dissolve(view('palm2', r1), view('palm2', r2), u)); cv.chip(chip_for('palm2'))
    if u < 0.5: zoom_ring(cv, r1, PJA2[0], PJA2[1], 'CIRCULAR STORM BARRIER', t, 1.5, (-30, -200), px=17, out=8.0)
    else: zoom_ring(cv, r2, PJ2[0], PJ2[1], 'PALM JUMEIRAH · THE SAME DESIGN', t, 10.3, (-190, -170), px=17)
    k = oc(seg(t, 5.0, 6.0))
    if k > 0:
        x0, y0, w, h = 700, 330, 230, 100; cv.d.rounded_rectangle([x0 - 8, y0 - 24, x0 + w + 8, y0 + h + 24], 6, fill=(8, 14, 22, int(215 * k)))
        cv.d.rectangle([x0, y0, x0 + w, y0 + h], fill=(30, 80, 120, int(255 * k))); cv.d.rectangle([x0 + 90, y0 + 20, x0 + w, y0 + h], fill=(190, 160, 110, int(255 * k)))
        for i in range(4): cv.d.rectangle([x0 + 62 + (i % 2) * 14, y0 + 28 + i * 18, x0 + 90 + (i % 2) * 6, y0 + 44 + i * 18], fill=(110, 112, 118, int(255 * k)))
        cv.text((x0 + 46, y0 - 16), 'ROCK', 12, TEXT, k, anchor='ma'); cv.text((x0 + 160, y0 - 16), 'SAND', 12, TEXT, k, anchor='ma'); cv.text((x0, y0 + h + 6), 'ILLUSTRATION · cross-section', 11, MUTED, k)
    return cv
def D2(t, d, X):
    rect = (600, 1000, 1600, 900); cut = 8.0; key = '2000' if t < cut else '2011'; lt = t if t < cut else t - cut
    r = lerp_rect(rect, (700, 1060, 1400, 788), lt / (cut if t < cut else d - cut)); cv = Canvas(view(key, r)); stamp(cv, key, lt, 0.2, 54)
    cv.pill((24, 128), 'LABELLED CUT · separate days · not registered', 13, 1.0 if abs(t - cut) < 1.5 else 0.0, accent=CYAN)
    if t < cut: cv.text((W - 30, 100), 'MOSTLY EMPTY DESERT', 20, TEXT, oc(seg(t, 2, 3)), anchor='ra')
    else: cv.text((W - 30, 100), 'ROADS, BUILDINGS, IRRIGATED LAND', 20, TEXT, oc(seg(t, cut + 2, cut + 3)), anchor='ra'); cv.text((W - 30, 128), 'cover almost all of this area (NASA)', 15, MUTED, oc(seg(t, cut + 3, cut + 4)), anchor='ra', bold=False)
    return cv
def sat_icon(ss, x, y, col): ss.rect(x - 9, y - 5, x + 9, y + 5, fill=col); ss.rect(x - 26, y - 2, x - 11, y + 2, fill=MUTED + (255,)); ss.rect(x + 11, y - 2, x + 26, y + 2, fill=MUTED + (255,))
def cam_icon(ss, x, y, col): ss.rect(x - 22, y - 11, x + 22, y + 13, fill=col, r=3); ss.rect(x - 8, y - 17, x + 8, y - 11, fill=col); ss.ellipse((x, y + 1), 8, fill=(11, 15, 20, 255), outline=(234, 240, 246, 255), width=1.5)
def D5(t, d, X):
    cv = Canvas(text_card_bg()); ss = SS(); cv.text((70, 56), 'A NOTE ON METHOD', 15, AMBER, anchor='la', spacing=0.25)
    rows = [('EVERY IMAGE CARRIES', 'Its source, its instrument and its year'), ('MOST COME FROM', 'ASTER, an instrument on a satellite'), ('ONE IS A PHOTOGRAPH', 'Taken by an astronaut with a Nikon camera'),
            ('NEVER', 'Moving footage · never overlaid on each other'), ('ONE IMAGE', "Year only: NASA's text and caption disagree on the month")]
    card_rows(cv, t, rows, y0=110, gap=76, t0=1.0, step=4.8, px=21, wmax=620)
    k = [oc(seg(t, 1.0 + i * 4.8, 1.6 + i * 4.8)) for i in range(5)]; vx = 800
    if k[0] > 0: cv.pill((vx - 70, 118), 'NASA ASTER · 2006', 12, k[0], accent=AMBER)
    if k[1] > 0: sat_icon(ss, vx + 20, 205 + 3 * math.sin(t * 2), CYAN + (int(255 * k[1]),)); ss.dashed([(vx + 20, 214), (vx + 20, 238)], CYAN + (int(200 * k[1]),), 1.3, 4, 4, offset=t * 20)
    if k[2] > 0: cam_icon(ss, vx + 20, 292, (214, 222, 232, int(255 * k[2])))
    if k[3] > 0:
        ss.rect(vx - 40, 350, vx + 10, 392, outline=MUTED + (int(255 * k[3]),), width=1.4, r=3); ss.rect(vx + 30, 350, vx + 80, 392, outline=MUTED + (int(255 * k[3]),), width=1.4, r=3)
        cv.text((vx + 20, 361), '≠', 22, AMBER, k[3], anchor='ma')
    if k[4] > 0: cv.pill((vx - 6, 424), '2011', 16, k[4], accent=AMBER)
    layer(cv, ss); return cv
def E1(t, d, X):
    cv = Canvas(text_card_bg()); keys = ['2000', '2002a', '2002b', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011']
    labs = ['2000', 'FEB 2002', 'OCT 2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011']
    tw, th, gx, gy = 220, 124, 14, 14; x0 = (W - (4 * tw + 3 * gx)) / 2; y0 = 66
    for i, (kk, lab) in enumerate(zip(keys, labs)):
        k = oc(seg(t, 0.6 + i * 1.45, 1.1 + i * 1.45))
        if k <= 0: continue
        x = x0 + (i % 4) * (tw + gx); y = y0 + (i // 4) * (th + gy + 14); c, _ = woc_ring(kk); tile = view(kk, rect_c(c, 760, dx=150)).resize((tw, th), Image.LANCZOS)
        cv.o.paste(tile.convert('RGBA'), (int(x), int(y + (1 - k) * 8)), Image.new('L', (tw, th), int(255 * k))); cv.text((x + 6, y + th + 3), lab, 13, AMBER, k, anchor='la')
    cv.pill((22, 20), 'NASA ASTER · 12 images, 2000–2011 · colours as published · crop centred on the palm site', 13, 1.0, accent=AMBER); return cv
def E2(t, d, X):
    cut = 15.5
    if t < cut: r = lerp_rect((1475, 1002, 960, 540), (1500, 1020, 900, 506), t / cut); lab = 'PALM JUMEIRAH'; note = 'NASA CAPTION: ringed by a circular storm barrier'; c, rad = PJI
    else: r = lerp_rect((1066, 2461, 1120, 630), (1090, 2480, 1060, 596), (t - cut) / (d - cut)); lab = 'PALM JEBEL ALI'; note = 'NASA CAPTION: mostly undeveloped in 2022'; c, rad = PJAI
    cv = Canvas(view('iss', r)); cv.chip(ISSCHIP); lt = t if t < cut else t - cut
    zoom_ring(cv, r, c, rad, lab, lt, 1.5, (-170, -170), px=19); cv.text((24, 66), note, 14, MUTED, oc(seg(lt, 6, 7)), anchor='la', bold=False); cv.text((W - 24, 40), 'APRIL 2022', 18, AMBER, anchor='ra', spacing=0.2); return cv
def E4(t, d, X):
    """split screen (both dated stills fully visible, no overlay or wipe): 2000 | 2003, then synthesis text on a lower strip"""
    c0, _ = woc_ring('2000'); c3, _ = woc_ring('2003'); pw, ph = W // 2, H; sl = oc(seg(t, 0.4, 2.0))
    def panel(key, c):
        w = 760 + 40 * (t / d); h = w * ph / pw; x = min(max(c[0] + 120 - w / 2, 0), 3000 - w); y = min(max(c[1] - h / 2, 0), 3000 - h)
        return view_panel(key, (x, y, w, h))
    a, b = panel('2000', c0), panel('2003', c3); base = Image.new('RGB', (W, H), INK); base.paste(a, (-int((1 - sl) * pw * 0.2), 0)); base.paste(b, (pw + int((1 - sl) * pw * 0.2), 0))
    cv = Canvas(dim(base, 1 - 0.0)); cv.d.rectangle([pw - 2, 0, pw + 2, H], fill=INK + (255,))
    cv.chip('NASA ASTER · 2000 | 2003 · colours as published · separate days, not registered'); cv.text((24, 70), '2000', 44, AMBER, sl, anchor='la'); cv.text((pw + 24, 70), '2003', 44, AMBER, sl, anchor='la')
    cv.d.rectangle([0, H - 190, W, H], fill=(6, 10, 16, int(170 * sm(seg(t, 1.5, 2.5)))))
    cv.text((W / 2, H - 170), 'A map drawn in 2000 would show open water here.', 22, TEXT, oc(seg(t, 3.0, 4.0)) * (1 - sm(seg(t, 10.0, 11.0))), anchor='ma')
    cv.text((W / 2, H - 170), 'By November 2003, that map would be wrong.', 22, TEXT, oc(seg(t, 14.5, 15.5)), anchor='ma')
    cv.text((W / 2, H - 132), 'Sand from the sea floor · a ring of rock', 20, AMBER, oc(seg(t, 18.0, 19.0)), anchor='ma'); cv.text((W / 2, H - 100), 'A coastline stops being a fixed line.', 20, AMBER, oc(seg(t, 21.0, 22.0)), anchor='ma'); return cv
def view_panel(key, rect):
    im = src(key); x, y, w, h = rect
    if LOG: USED.append((key, (x, y, w, h)))
    return im.resize((W // 2, H), Image.LANCZOS, box=(x, y, x + w, y + h))
def E5(t, d, X):
    if t < 8.0: key, r = '2000', lerp_rect(rect_c(SITE_C, 1400, dx=300), rect_c(SITE_C, 1250, dx=250), t / 8.0)
    elif t < 16.0: key, r = '2003', lerp_rect(rect_c(woc_ring('2003')[0], 1400, dx=300), rect_c(woc_ring('2003')[0], 1250, dx=250), (t - 8) / 8.0)
    else: key, r = 'iss', lerp_rect(H3A, H3B, smr(seg(t, 16.5, 26.5)))
    lab = {'2000': 'NOVEMBER 2000: OPEN SEA', '2003': 'NOVEMBER 2003: A PALM INSIDE ITS RING', 'iss': 'APRIL 2022: THE PALM ISLANDS FROM ORBIT'}[key]
    cv = Canvas(view(key, r)); cv.chip(chip_for(key)); lt = t if t < 8 else (t - 8 if t < 16 else t - 16); cv.text((24, 62), lab, 20, AMBER, oc(seg(lt, 0.3, 1.2)), anchor='la', spacing=0.1)
    if key == '2003': c, rad = woc_ring('2003'); cv.callout(to_screen(r, (c[0] - rad, c[1])), 'THE RING', lt, 2.5, (80, 110), r=14)
    if key == 'iss': zoom_ring(cv, r, PJI[0], PJI[1], 'PALM JUMEIRAH · RING', lt, 2.0, (-170, -170), px=18); zoom_ring(cv, r, PJAI[0], PJAI[1], 'PALM JEBEL ALI · RING', lt, 9.0, (-170, -150), px=18)
    return cv
def E6(t, d, X):
    cv = Canvas(text_card_bg()); k = oc(seg(t, 0.4, 1.4)) * (1 - sm(seg(t, d - 1.5, d)))
    cv.text((W / 2, 150), 'IMAGERY', 14, AMBER, k, anchor='ma', spacing=0.3); cv.text((W / 2, 190), 'NASA Earth Observatory', 30, TEXT, k, anchor='ma')
    cv.text((W / 2, 250), 'ASTER on the Terra satellite', 24, TEXT, k, anchor='ma', bold=False); cv.text((W / 2, 300), 'Astronaut photograph ISS067-E-3785', 24, TEXT, k, anchor='ma', bold=False)
    cv.text((W / 2, 336), 'ISS Crew Earth Observations', 20, MUTED, k, anchor='ma', bold=False)
    cv.text((W / 2, 392), 'Globe sequence: NASA GIBS (Blue Marble, Landsat) rendered with CesiumJS', 13, MUTED, k, anchor='ma', bold=False)
    cv.text((W / 2, 440), 'Orbital Atlas · EP002', 15, MUTED, k, anchor='ma', spacing=0.3); return cv

PUSH = {'A3': 0.035, 'B4': 0.03, 'C2': 0.04, 'C4': 0.03, 'C6': 0.04, 'D5': 0.035, 'E1': 0.03, 'E6': 0.03}      # whole-frame slow push (fraction), text/graphic scenes only
MOVE_WINDOWS = {'C1': [(5.0, 6.8), (10.0, 11.8), (15.0, 16.8)]}   # declared fast camera moves (stop to stop), excluded from jump detection
EXTRA_YEARS = {'D5': ({'2006', '2011'}, 'example chips on the method card: 2006 = palm2.jpg (ASTER 18 Sep 2006), 2011 = the year-only WoC frame (SCRIPT_LOCK: 2011 = year only)')}
INTRA_CUTS = {'D2': [8.0], 'E2': [15.5], 'E5': [8.0, 16.0]}      # declared hard cuts inside a scene (seconds from scene start), used by qa_preview.py
STATIC_WINDOWS = {}                                                  # declared intentional holds (none: every text card keeps at least one animated element)
# id, start s, duration s, VO line numbers (1-based among VO lines), function
SCENES = [('H1', 0, 10, [1], H1), ('H2', 10, 8, [2], H2), ('H3', 18, 11, [3], H3), ('H4', 29, 9, [4], H4), ('A1', 38, 20, [5], A1), ('A2', 58, 23, [6, 7], A2), ('A3', 81, 27, [8, 9], A3),
          ('B1', 108, 13, [10], B1), ('B2', 121, 15, [11], B2), ('B3', 136, 20, [12], B3), ('B4', 156, 17, [13], B4), ('B5', 173, 30, [14], B5), ('B6', 203, 15, [15], B6), ('B7', 218, 14, [16], B7),
          ('C1', 232, 20, [17], C1), ('C2', 252, 20, [18], C2), ('C3', 272, 18, [19], C3), ('C4', 290, 23, [20], C4), ('C5', 313, 21, [21], C5), ('C6', 334, 25, [22], C6),
          ('D1', 359, 17, [23], D1), ('D2', 376, 17, [24], D2), ('D5', 393, 30, [25], D5), ('E1', 423, 20, [26], E1), ('E2', 443, 32, [27], E2), ('E4', 475, 27, [28], E4), ('E5', 502, 27, [29], E5), ('E6', 529, 9, [30], E6)]
