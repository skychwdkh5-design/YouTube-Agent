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
# ------------------------------------------------------------------ HOOK V4 (cold open pull-out, coastline trace, wipe + new-land trace as the main event, triptych, spotlighted plans, title)
# Timing: ESTIMATED (145 wpm inside each scene window, 0.5 s lead); tw(i, n, d) = word i of n. Re-derive from provider word timings once narration exists.
def tw(i, n, d): return 0.5 + i * (d - 1.1) / n
def path(t, d, keys, size):
    """camera path through (time, rect) keys; Catmull-Rom on (cx, cy, log w), 16:9 preserved"""
    t = tm(t); ts = [k[0] for k in keys]; P = [(k[1][0] + k[1][2] / 2, k[1][1] + k[1][3] / 2, math.log(k[1][2])) for k in keys]
    t = min(max(t, ts[0]), ts[-1]); i = max(j for j in range(len(ts) - 1) if ts[j] <= t) if t < ts[-1] else len(ts) - 2
    u = (t - ts[i]) / (ts[i + 1] - ts[i]); n = len(P); p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, n - 1)]
    def cr(a, b, c, e): return 0.5 * ((2 * b) + (-a + c) * u + (2 * a - 5 * b + 4 * c - e) * u * u + (-a + 3 * b - 3 * c + e) * u ** 3)
    cx, cy, lw = (cr(p0[k], p1[k], p2[k], p3[k]) for k in range(3)); w = min(math.exp(lw), size[0], size[1] * 16 / 9); h = w * 9 / 16; return clampr((cx - w / 2, cy - h / 2, w, h), size)
def clampr(r, size):
    x, y, w, h = r; x = min(max(x, 0), size[0] - w); y = min(max(y, 0), size[1] - h); return (x, y, w, h)
def key_rect(c, w, size): return clampr((c[0] - w / 2, c[1] - w * 9 / 32, w, w * 9 / 16), size)
ISS_SZ, P2_SZ, WOC_SZ = (2768, 4928), (3072, 3797), (3000, 3000)
SITE = woc_ring('2003')                                                     # Palm Jumeirah ring in the 2003 grid
# registration of the two ASTER frames, measured (phase correlation, 512 px land patches, 6 places): shift <= 1 px; see HOOK_V3.md
def spot(img, c, r, k):
    if k <= 0.003: return img
    yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32) / SC; m = np.clip((np.hypot(xx - c[0], yy - c[1]) - r) / (r * 0.6), 0, 1); m = m * m * (3 - 2 * m)
    return Image.fromarray((np.asarray(img, np.float32) * (1 - k * m[..., None])).clip(0, 255).astype(np.uint8))
# --- traced layers (TRACED class: computed from the pixels of the frame they are drawn on)
_NL, _CL = {}, {}
def sea_dist(key, x0, y0, w, h):
    a = np.asarray(src(key), np.float32); ref = np.median(a[1250:1400, 0:280].reshape(-1, 3), 0); return np.sqrt(((a[y0:y0 + h, x0:x0 + w] - ref) ** 2).sum(2))
def new_land():
    """land present in 2003 and sea in 2000 inside the palm's site (same grid, registration <= 1 px): fill + outline masks in source pixels"""
    if _NL: return _NL
    cx, cy = SITE[0]; R = SITE[1]; S = 700; x0, y0 = int(cx - S / 2), int(cy - S / 2); new = (sea_dist('2003', x0, y0, S, S) >= 38) & (sea_dist('2000', x0, y0, S, S) < 38)
    yy, xx = np.mgrid[0:S, 0:S]; dist = np.hypot(xx - (cx - x0), yy - (cy - y0)); new &= dist <= R * 1.3
    m = Image.fromarray((new * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5)); fill = np.asarray(m) > 127
    edge = fill & ~(np.asarray(m.filter(ImageFilter.MinFilter(5))) > 127); edge = np.asarray(Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 127
    ang = (np.arctan2(yy - (cy - y0), xx - (cx - x0)) / (2 * math.pi)) % 1.0
    _NL.update(x0=x0, y0=y0, S=S, fill=fill, edge=edge, dist=dist / (R * 1.3), ang=ang); return _NL
def overlay_new_land(cv, r, fill_p, edge_p, fill_a=0.40, edge_a=1.0):
    N = new_land(); S = N['S']; rgba = np.zeros((S, S, 4), np.uint8); col = np.array(AMBER, np.uint8)
    f = N['fill'] & (N['dist'] <= fill_p * 1.02); rgba[f, :3] = col; rgba[f, 3] = int(255 * fill_a)
    e = N['edge'] & (N['ang'] <= edge_p); rgba[e, :3] = col; rgba[e, 3] = int(255 * edge_a)
    k = PW / r[2]; sw = max(int(S * k), 1)
    if sw < 4 or not (f.any() or e.any()): return
    im = Image.fromarray(rgba, 'RGBA').resize((sw, sw), Image.LANCZOS); lay = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); lay.paste(im, (int(round((N['x0'] - r[0]) * k)), int(round((N['y0'] - r[1]) * k))))
    cv.o = Image.alpha_composite(cv.o, lay); cv.d = mkdraw(cv.o)
def coast_line():
    """2000 shoreline: first non-sea pixel (40 px persistence, so clouds over water are ignored) per row, median-smoothed"""
    if _CL: return _CL['p']
    a = np.asarray(src('2000'), np.float32); ref = np.median(a[1250:1400, 0:280].reshape(-1, 3), 0); pts = []
    for y in range(1090, 2300, 8):
        row = (np.sqrt(((a[y] - ref) ** 2).sum(1)) >= 38).astype(np.int32); c = np.convolve(row, np.ones(40, np.int32), 'valid'); idx = np.nonzero(c == 40)[0]
        if len(idx): pts.append([int(idx[0]), y])
    xs = np.array([p[0] for p in pts], float); sm_ = np.array([np.median(xs[max(0, i - 3):i + 4]) for i in range(len(xs))]); _CL['p'] = [(float(x), p[1]) for x, p in zip(sm_, pts)]; return _CL['p']
def draw_coast(cv, r, p, a=1.0):
    pts = coast_line(); n = max(2, int(len(pts) * p)); ss = SS(); pp = [to_screen(r, q) for q in pts[:n]]; ss.line(pp, AMBER + (int(90 * a),), 12); ss.line(pp, AMBER + (int(250 * a),), 5); layer(cv, ss)

CYAN = (96, 200, 230)
def arrow(cv, p0, p1, a, col=AMBER, wd=2.4, head=11):
    """draw-on directional arrow in screen space (UI explanation, not data); a in 0..1 is the draw progress"""
    if a <= 0.01: return
    q = (p0[0] + (p1[0] - p0[0]) * a, p0[1] + (p1[1] - p0[1]) * a); ss = SS(); ss.line([p0, q], col + (235,), wd)
    if a > 0.97:
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); ss.poly([p1, (p1[0] - head * math.cos(ang - 0.45), p1[1] - head * math.sin(ang - 0.45)), (p1[0] - head * math.cos(ang + 0.45), p1[1] - head * math.sin(ang + 0.45))], fill=col + (235,))
    layer(cv, ss)
def sea_tint(cv, r, a, col=CYAN):
    """UI tint over the traced sea side of the 2000 shoreline (rows >= 1090); labelled, evidence pixels underneath are untouched apart from the tint"""
    if a <= 0.01: return
    pts = coast_line(); poly = [to_screen(r, (-400, pts[0][1] - 40))] + [to_screen(r, q) for q in pts] + [to_screen(r, (-400, pts[-1][1] + 40))]; ss = SS(); ss.poly(poly, fill=col + (int(55 * a),)); layer(cv, ss)
def ladder(cv, t, items, active, a, x=None, y0=112):
    """ordered list of the projects; the active row is amber, others muted; right-aligned, rows are pills"""
    for i, name in enumerate(items):
        on = active == i; cv.pill((W - 24 - (cv.d.textlength(f'0{i + 1}  {name}', font=F(13, True)) + 13 * 1.4), y0 + i * 30), f'0{i + 1}  {name}', 13, a=a * (1 if on else 0.8), accent=AMBER if on else None)
def ring_dashed(cv, c, r, a, phase=0.0, frac=1.0, col=AMBER):
    n = max(2, int(90 * frac)); ss = SS(); ss.dashed([(c[0] + r * math.cos(2 * math.pi * k / 90 - math.pi / 2), c[1] + r * math.sin(2 * math.pi * k / 90 - math.pi / 2)) for k in range(n + 1)], col + (int(230 * a),), 1.8, 7, 6, offset=phase); layer(cv, ss)
_MINI = {}
def minimap(cv, r, a):
    if a <= 0.01: return
    if 'im' not in _MINI: _MINI['im'] = src('2000').resize((int(176 * SC), int(176 * SC)), Image.LANCZOS)
    x0, y0 = 22, 58; X0, Y0, Z = int(x0 * SC), int(y0 * SC), int(176 * SC); cv.base.paste(Image.blend(cv.base.crop((X0, Y0, X0 + Z, Y0 + Z)), _MINI['im'].convert('RGBA'), a), (X0, Y0)); s = 176 / 3000; ss = SS()
    ss.rect(x0 - 1, y0 - 1, x0 + 177, y0 + 177, outline=(234, 240, 246, int(200 * a)), width=1); ss.rect(x0 + r[0] * s, y0 + r[1] * s, x0 + (r[0] + r[2]) * s, y0 + (r[1] + r[3]) * s, outline=AMBER + (int(255 * a),), width=1.6); layer(cv, ss)
    cv.text((x0, y0 + 182), 'WHOLE ASTER FRAME · 2000', 12, MUTED, a)
def paste_view(img, key, box, scr):
    sx, sy, sw, sh = (int(round(v * SC)) for v in scr)
    if sw < 2 or sh < 2: return
    bx, by, bw, bh = box; bx = min(max(bx, 0), src(key).width - bw); by = min(max(by, 0), src(key).height - bh); img.paste(src(key).resize((sw, sh), Image.LANCZOS, box=(bx, by, bx + bw, by + bh)), (sx, sy))

# ---- V6: fewer, larger labels; match-cut and motivated transitions; cross-dissolve 2000 -> 2003 (no wipe); two-panel comparison
def big(cv, text, y, a, px=32):
    """one main label at a time: large, centred, readable on a phone"""
    if a <= 0.01: return
    wt = cv.d.textlength(text, font=F(px, True)) + px * 1.4; cv.pill((W / 2 - wt / 2, y), text, px, a=a, accent=AMBER)
def with_entry(fn, prev, prev_d, kind, tr, center=None):
    """enter a scene through a motivated transition from the last frame of the previous scene (scene durations are unchanged, so narration windows stay valid)"""
    def f(t, d, X):
        cv = fn(t, d, X)
        if t >= tr: return cv
        a = prev(prev_d - 1 / FPS, prev_d, X).finish(); b = cv.finish(); u = sm(t / tr)
        if kind == 'dissolve': out = Image.blend(a, b, u)
        elif kind == 'slide':
            out = Image.new('RGB', (PW, PH)); off = int(PW * oc(t / tr)); out.paste(a, (-off, 0)); out.paste(b, (PW - off, 0))
        else:                                                  # iris: the new scene opens as a circle around a point shared by both shots
            c = center() if callable(center) else center; yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32) / SC; R = oc(t / tr) * float(np.hypot(max(c[0], W - c[0]), max(c[1], H - c[1]))) * 1.05
            m = np.clip((R - np.hypot(xx - c[0], yy - c[1])) / 40.0, 0, 1)[..., None]; out = Image.fromarray((np.asarray(a, np.float32) * (1 - m) + np.asarray(b, np.float32) * m).clip(0, 255).astype(np.uint8))
        return Canvas(out)
    return f
H0_KEYS = lambda: [(0, key_rect(PJI[0], 560, ISS_SZ)), (1.5, key_rect(PJI[0], 1650, ISS_SZ)), (3.0, key_rect(PJI[0], 2150, ISS_SZ))]
def H0(t, d, X):                                                           # silent cold open: the result
    r = path(t, d, H0_KEYS(), ISS_SZ); cv = Canvas(view('iss', r)); cv.chip(ISSCHIP); yearlabel(cv, 'APRIL 2022', t, 0.2)
    cv.ping(to_screen(r, PJI[0]), t, 1.45, r=max(18, PJI[1] * W / r[2] * 0.95), n=1); big(cv, 'THIS WAS OPEN SEA IN 2000', H * 0.80, oc(seg(t, 1.1, 1.6)), 30); return cv
SITE_W0 = SITE[1] * W / (PJI[1] * W / 2150.0)                              # width of the 2000 view whose ring has the same screen radius as the palm at the end of H0 (match cut)
def H1(t, d, X):                                                           # same place, other year: pull out to the shoreline, push back, "no island", ghost outline of what 2003 shows
    keys = [(0, key_rect(SITE[0], SITE_W0, WOC_SZ)), (1.5, key_rect((1500, 1500), 3000, WOC_SZ)), (3.5, key_rect((SITE[0][0] + 450, SITE[0][1] - 100), 1500, WOC_SZ)), (5.2, key_rect(SITE[0], 900, WOC_SZ)), (7.5, key_rect(SITE[0], 860, WOC_SZ)), (d, key_rect(SITE[0], 800, WOC_SZ))]
    r = path(t, d, keys, WOC_SZ); cv = Canvas(view('2000', r)); cv.chip(chip_for('2000')); yearlabel(cv, 'NOVEMBER 2000', t, 0.3)
    pa = oc(seg(t, 0.3, 2.0)); pf = 1 - sm(seg(t, 3.6, 4.4))
    if pf > 0.01: draw_coast(cv, r, pa, pf)
    c = to_screen(r, SITE[0]); rr = SITE[1] * W / r[2]; ring_dashed(cv, c, rr, sm(seg(t, 4.4, 4.8)) * (1 - sm(seg(t, 8.4, 9.0))), phase=t * 14, frac=oc(seg(t, 4.4, 6.0)))
    big(cv, 'NO ISLAND HERE', H * 0.17, sm(seg(t, tw(13, 20, d) - 0.1, tw(13, 20, d) + 0.4)) * (1 - sm(seg(t, 8.6, 9.0))))
    sea_tint(cv, r, sm(seg(t, 6.6, 7.4)))
    overlay_new_land(cv, r, 0.0, oc(seg(t, 8.4, 9.6)), fill_a=0.0, edge_a=0.85); return cv
def H2(t, d, X):                                                           # the event: cross-dissolve 2000 -> 2003 on the shared grid, the changed shoreline and new land light up, pull back, "3 YEARS"
    keys = [(0, key_rect(SITE[0], 800, WOC_SZ)), (2.4, key_rect(SITE[0], 930, WOC_SZ)), (5.0, key_rect((SITE[0][0] + 60, SITE[0][1]), 1650, WOC_SZ)), (d, key_rect((SITE[0][0] + 130, SITE[0][1]), 2150, WOC_SZ))]
    r = path(t, d, keys, WOC_SZ); k = sm(seg(t, 0.9, 2.4)); cv = Canvas(dissolve(view('2000', r), view('2003', r), k)); cv.chip('NASA ASTER · 2000 → 2003 · same grid')
    cv.text((W - 24, 40), 'NOVEMBER 2000', 30, AMBER, 1 - sm(seg(t, 0.9, 1.6)), anchor='ra', spacing=0.14); cv.text((W - 24, 40), 'NOVEMBER 2003', 30, AMBER, sm(seg(t, 1.8, 2.4)), anchor='ra', spacing=0.14)
    overlay_new_land(cv, r, oc(seg(t, 2.4, 4.0)), 1.0, fill_a=0.34 * (1 - 0.65 * sm(seg(t, 5.0, 5.8))), edge_a=0.85 + 0.15 * sm(seg(t, 2.4, 3.0)))
    big(cv, 'NEW LAND', H * 0.17, sm(seg(t, tw(5, 16, d), tw(5, 16, d) + 0.4)) * (1 - sm(seg(t, 4.6, 5.0))))
    tl = sm(seg(t, tw(10, 16, d), tw(10, 16, d) + 0.4)); p = oc(seg(t, tw(10, 16, d) + 0.1, tw(14, 16, d) + 0.4)); n = min(3, 1 + int(p * 3))
    ss = SS(); x0, x1, y = W * 0.2, W * 0.56, H * 0.14 + 52; ss.rect(x0 - 24, y - 12, x1 + 24, y + 34, fill=(8, 14, 22, int(175 * tl)), r=6); ss.line([(x0, y), (x1, y)], (234, 240, 246, int(170 * tl)), 2); ss.line([(x0, y), (x0 + (x1 - x0) * p, y)], AMBER + (int(255 * tl),), 4)
    for xx in (x0, x1): ss.ellipse((xx, y), 5, fill=(234, 240, 246, int(255 * tl)))
    layer(cv, ss); cv.text((x0, y + 10), '2000', 15, TEXT, tl, anchor='ma'); cv.text((x1, y + 10), '2003', 15, TEXT, tl, anchor='ma'); big(cv, f'{n} YEAR' + ('S' if n > 1 else ''), H * 0.14 - 18, tl, 34); return cv
def H3(t, d, X):                                                           # two panels (2000 | 2022), one arrow, one counter; the ISS panel opens to full frame; glide to Palm Jebel Ali
    pw = W / 2; E0, E1 = 3.8, 4.9; e = smr(seg(t, E0, E1)); cx, cy = SITE[0]; z = 1 - 0.07 * min(t / E0, 1)
    box_o = (cx - 350 * z, cy - 394 * z, 700 * z, 788 * z); box_i = (PJI[0][0] - 500 * z, PJI[0][1] - 563 * z, 1000 * z, 1126 * z); big_r = key_rect(PJI[0], 1650, ISS_SZ)
    if e < 1:
        img = Image.new('RGB', (PW, PH), (8, 12, 18)); k1 = oc(seg(t, 0.0, 0.5)); k2 = oc(seg(t, 0.6, 1.3))
        paste_view(img, '2000', box_o, (-pw * e, 0, pw, H))
        scr = (pw * (1 - e) + (1 - k2) * pw, 0, pw + pw * e, H); bx = tuple(box_i[j] + (big_r[j] - box_i[j]) * e for j in range(4))
        if abs(bx[2] / bx[3] - scr[2] / scr[3]) > 0.02: bx = (bx[0], bx[1], bx[2], bx[2] * scr[3] / scr[2])
        paste_view(img, 'iss', bx, scr); cv = Canvas(img); fade = 1 - sm(seg(t, E0, E0 + 0.5))
        ss = SS(); ss.line([(pw, 0), (pw, H)], AMBER + (int(210 * fade),), 1.6); layer(cv, ss)
        cv.pill((10, 12), 'ASTER · NOV 2000', 12, a=0.8 * fade, accent=AMBER); cv.pill((pw + 10, 12), 'ISS PHOTO · APR 2022 · not satellite imagery', 12, a=0.8 * fade * k2, accent=AMBER)
        cv.text((pw / 2, H * 0.68), '2000', 46, AMBER, sm(seg(t, 0.3, 0.8)) * fade, anchor='ma', spacing=0.12); cv.text((pw * 1.5, H * 0.68), '2022', 46, AMBER, sm(seg(t, 1.6, 2.1)) * fade, anchor='ma', spacing=0.12)
        ap = oc(seg(t, 0.6, 3.0)); arrow(cv, (W * 0.22, H * 0.52), (W * 0.78, H * 0.52), ap * (1 if fade > 0.5 else 0), wd=3.2, head=15)
        if ap > 0.05: big(cv, f'{max(1, int(21 * ap))}+ YEARS', H * 0.52 - 64, sm(seg(t, 0.6, 1.0)) * fade, 36)
        if e > 0: cv.chip(ISSCHIP, sm(seg(t, E0 + 0.5, E1)))
        return cv
    keys = [(E1, big_r), (8.0, key_rect((PJAI[0][0] + 80, PJAI[0][1] - 260), 1700, ISS_SZ)), (d, key_rect((PJAI[0][0] + 80, PJAI[0][1] - 360), 2100, ISS_SZ))]
    r = path(t, d, keys, ISS_SZ); cv = Canvas(view('iss', r)); cv.chip(ISSCHIP); yearlabel(cv, 'APRIL 2022', t, E1 + 0.1)
    pj = to_screen(r, PJI[0]); cv.callout(pj, 'PALM JUMEIRAH', t, E1 + 0.2, (-130, -80), r=max(16, PJI[1] * W / r[2] * 1.1), px=24, out=6.2) if 70 < pj[1] < H - 100 and 150 < pj[0] < W - 150 else None
    cv.callout(to_screen(r, PJAI[0]), 'PALM JEBEL ALI', t, tw(20, 25, d), (-150, -100), r=max(16, PJAI[1] * W / r[2] * 1.1), px=24, out=d - 0.3); return cv
def H4(t, d, X):                                                           # ASTER 2006 south -> north across the four projects, pings, the plans that came next, accelerating pull-back, title
    mid = ((WORLD2[0] + DEIRA2[0]) / 2, (WORLD2[1] + DEIRA2[1]) / 2 + 80)
    keys = [(0, key_rect(PJA2[0], 1150, P2_SZ)), (2.5, key_rect(PJ2[0], 1250, P2_SZ)), (5.0, key_rect(mid, 2100, P2_SZ)), (6.8, key_rect(mid, 2800, P2_SZ)), (d, key_rect(mid, 3000, P2_SZ))]
    r = path(t, d, keys, P2_SZ); k = sm(seg(t, 6.6, 7.6)); t0 = tw(12, 20, d); base = view('palm2', r)
    sw = sm(seg(t, t0 - 0.2, t0 + 0.4)) * (1 - sm(seg(t, t0 + 1.0, t0 + 1.5))); sd = sm(seg(t, t0 + 1.0, t0 + 1.5)) * (1 - sm(seg(t, 6.3, 6.8)))
    base = spot(base, to_screen(r, WORLD2), max(60, 190 * W / r[2]), 0.62 * sw); base = spot(base, to_screen(r, DEIRA2), max(55, 150 * W / r[2]), 0.62 * sd)
    cv = Canvas(dim(base, 1 - 0.55 * k)); cv.chip(chip_for('palm2')); yearlabel(cv, '2006', t, 0.3)
    cv.ping(to_screen(r, PJA2[0]), t, 0.5, r=max(18, 160 * W / r[2]), n=1); cv.ping(to_screen(r, PJ2[0]), t, 2.7, r=max(18, 160 * W / r[2]), n=1)
    cv.callout(to_screen(r, WORLD2), 'THE WORLD', t, t0 - 0.1, (90, -80), r=max(18, 160 * W / r[2]), px=26, out=t0 + 1.2)
    cv.callout(to_screen(r, DEIRA2), 'PALM DEIRA', t, t0 + 1.0, (-100, 60), r=max(16, 110 * W / r[2]), px=26, out=6.4)
    cv._center = True; cv.kinetic((W / 2, H * 0.34), 'HOW DUBAI CHANGED', 46, 6.8, t, spacing=0.12, per=0.04, a=k); cv.kinetic((W / 2, H * 0.34 + 62), 'THE MAP OF THE EARTH', 46, 7.2, t, spacing=0.12, per=0.04, a=k)
    u = oc(seg(t, 7.7, 8.5)); ss = SS(); ss.line([(W / 2 - 210 * u, H * 0.34 + 124), (W / 2 + 210 * u, H * 0.34 + 124)], AMBER + (230,), 2); layer(cv, ss)
    cv.text((W / 2, H * 0.34 + 138), 'ORBITAL ATLAS · EP002', 16, MUTED, a=k * sm(seg(t, 8.0, 8.6)), anchor='ma', spacing=0.3); return cv

# ------------------------------------------------------------------ ACT 1
A2_START = (550, 600, 2400, 1350)
def pjson(f): return os.path.join(os.path.dirname(f), 'p' + os.path.basename(f)[1:-4] + '.json')
def tone_match(img, ref):
    a = np.asarray(img, np.float32); r = np.asarray(ref, np.float32).reshape(-1, 3); m, s = a.reshape(-1, 3).mean(0), a.reshape(-1, 3).std(0) + 1e-3
    return (a - m) / s * r.std(0) + r.mean(0)
def A1(t, d, X):
    fr = X['a1_frames']; n = len(fr); i = min(int(tm(t) * 24), n - 1)                      # Cesium frames are 24 per estimated second whatever the output fps
    ces = Image.open(fr[i]).convert('RGB').resize((PW, PH), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2 * SC, 60, 2)); pj = json.load(open(pjson(fr[i])))
    u = seg(t, 15.8, 19.0)
    if u > 0:                                                  # soft Palm/Dubai-centred dissolve into the ASTER-2000 start crop; the Cesium render is tone-matched (UI treatment), ASTER untouched
        last = json.load(open(pjson(fr[-1]))); ref = view('2000', A2_START)
        k = sm(seg(t, 13.0, 17.0)) * 0.7; ces = Image.fromarray((np.asarray(ces, np.float32) * (1 - k) + tone_match(ces, ref) * k).clip(0, 255).astype(np.uint8))
        c = last['dubai'][:2]; yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32) / SC; D = np.hypot(xx - c[0], yy - c[1]); far = float(np.hypot(max(c[0], W - c[0]), max(c[1], H - c[1])))
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
    c, rad = woc_ring('2002b'); r = lerp_rect(rect_c(c, 1050, dx=210), rect_c(c, 640, dx=60), smr(tm(t) / d)); cv = Canvas(view('2002b', r)); stamp(cv, '2002b', t)
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
    cv.callout((ex - 40, SURF - 50), 'PLACED WHERE THE ISLAND WILL BE', t, 10.5, (-40, -64), ring=False, px=15, col=TEXT)
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
    c, _ = woc_ring('2003'); r = lerp_rect(rect_c(c, 900, dx=150), rect_c(c, 760, dx=110), tm(t) / d)
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
    c, rad = PJ2; r = lerp_rect(C1B, (965, 1930, 860, 484), tm(t) / d); cv = Canvas(view('palm2', r)); cv.chip(chip_for('palm2'))
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
    u = sm(seg(t, 8.0, 10.5)); im = dissolve(view('palm2', lerp_rect(C1D, (1760, 190, 1180, 664), tm(t) / d)), view('palm2', lerp_rect(C1C, (940, 1040, 1180, 664), seg(t, 6.0, d))), u); k = sm(seg(t, 2.0, 3.0))
    cv = Canvas(dim(im, 1 - 0.5 * k)); cv.chip(chip_for('palm2'))
    cv.text((60, 150), '2007 – 2008', 44, AMBER, oc(seg(t, 3.0, 4.0)), anchor='la'); cv.text((60, 212), 'THE GLOBAL RECESSION', 28, TEXT, oc(seg(t, 4.0, 5.0)), anchor='la')
    cv.text((60, 258), 'NASA: it delayed these projects', 20, MUTED, oc(seg(t, 5.0, 6.0)), anchor='la', bold=False)
    cv.text((60, 330), 'In the 2006 image: Palm Deira barely begun,', 17, TEXT, oc(seg(t, 12.0, 13.0)), anchor='la', bold=False); cv.text((60, 356), 'The World still under construction.', 17, TEXT, oc(seg(t, 12.6, 13.6)), anchor='la', bold=False); return cv
def C4(t, d, X):
    r = lerp_rect(C1C, (940, 1040, 1180, 664), tm(t) / d); cv = Canvas(dim(view('palm2', r), 0.32)); cv.chip('Background: NASA ASTER · 2006 · colours as published (not 2022)')
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
    u = sm(seg(t, 8.0, 10.0)); r1 = lerp_rect(C1A, (100, 2810, 1180, 664), tm(t) / d); r2 = lerp_rect(C1B, (950, 1930, 880, 495), tm(t) / d)
    cv = Canvas(dissolve(view('palm2', r1), view('palm2', r2), u)); cv.chip(chip_for('palm2'))
    if u < 0.5: zoom_ring(cv, r1, PJA2[0], PJA2[1], 'CIRCULAR STORM BARRIER', t, 1.5, (-30, -200), px=17, out=8.0)
    else: zoom_ring(cv, r2, PJ2[0], PJ2[1], 'PALM JUMEIRAH · THE SAME DESIGN', t, 10.3, (-190, -170), px=17)
    k = oc(seg(t, 5.0, 6.0))
    if k > 0:
        x0, y0, w, h = 700, 330, 230, 100; cv.d.rounded_rectangle([x0 - 8, y0 - 24, x0 + w + 8, y0 + h + 24], 6, fill=(8, 14, 22, int(215 * k)))
        cv.d.rectangle([x0, y0, x0 + w, y0 + h], fill=(30, 80, 120, int(255 * k))); cv.d.rectangle([x0 + 90, y0 + 20, x0 + w, y0 + h], fill=(190, 160, 110, int(255 * k)))
        for i in range(4): cv.d.rectangle([x0 + 62 + (i % 2) * 14, y0 + 28 + i * 18, x0 + 90 + (i % 2) * 6, y0 + 44 + i * 18], fill=(110, 112, 118, int(255 * k)))
        cv.text((x0 + 46, y0 - 16), 'ROCK', 12, TEXT, k, anchor='ma'); cv.text((x0 + 160, y0 - 16), 'SAND', 12, TEXT, k, anchor='ma'); cv.text((x0, y0 + h + 6), 'ILLUSTRATION · cross-section', 12, MUTED, k)
    return cv
def D2(t, d, X):
    rect = (600, 1000, 1600, 900); cut = 8.0; key = '2000' if t < cut else '2011'; lt = t if t < cut else t - cut
    r = lerp_rect(rect, (700, 1060, 1400, 788), lt / (cut if t < cut else d - cut)); cv = Canvas(view(key, r)); stamp(cv, key, lt, 0.2, 54)
    cv.pill((24, 128), 'LABELLED CUT · separate days · not registered', 13, 1.0 if abs(t - cut) < 1.5 else 0.0, accent=CYAN)
    if t < cut: cv.pill((W - 30, 92), 'MOSTLY EMPTY DESERT', 20, oc(seg(t, 2, 3)), accent=AMBER, anchor='right')
    else: cv.pill((W - 30, 92), 'ROADS, BUILDINGS, IRRIGATED LAND', 20, oc(seg(t, cut + 2, cut + 3)), accent=AMBER, anchor='right'); cv.pill((W - 30, 138), 'cover almost all of this area (NASA)', 15, oc(seg(t, cut + 3, cut + 4)), anchor='right')
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
        w = 760 + 40 * (tm(t) / d); h = w * ph / pw; x = min(max(c[0] + 120 - w / 2, 0), 3000 - w); y = min(max(c[1] - h / 2, 0), 3000 - h)
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
    cv = Canvas(view(key, r)); cv.chip(chip_for(key)); lt = t if t < 8 else (t - 8 if t < 16 else t - 16); cv.text((24, 62 if key != 'iss' else H - 112), lab, 20, AMBER, oc(seg(lt, 0.3, 1.2)), anchor='la', spacing=0.1)   # on the ISS frame the Jumeirah ring sits top-left: header moves above the captions
    if key == '2003': c, rad = woc_ring('2003'); cv.callout(to_screen(r, (c[0] - rad, c[1])), 'THE RING', lt, 2.5, (80, 110), r=14)
    if key == 'iss': zoom_ring(cv, r, PJI[0], PJI[1], 'PALM JUMEIRAH · RING', lt, 2.0, (170, 130), px=18); zoom_ring(cv, r, PJAI[0], PJAI[1], 'PALM JEBEL ALI · RING', lt, 9.0, (-170, -150), px=18)
    return cv
def E6(t, d, X):
    cv = Canvas(text_card_bg()); k = oc(seg(t, 0.4, 1.4))                      # credits stay to the last frame (no fade to black)
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

# ---- V4 hook: the voice starts at 0 s; opening = real NASA GIBS globe descent (frames 60..end, compressed to ~4.5 s) on "A satellite looks down at a patch of the Persian Gulf", dissolve into ASTER 2000
def HV1(t, d, X):
    fr = X['a1_frames']; n = len(fr); T1 = tw(12, 20, d) + 0.25; u = min(tm(t) / T1, 1.0); i = min(int(60 + (n - 1 - 60) * (1 - (1 - u) ** 1.6)), n - 1)
    ces = Image.open(fr[i]).convert('RGB').resize((PW, PH), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2 * SC, 60, 2)); pj = json.load(open(pjson(fr[i])))
    r2 = path(t, d, [(0, key_rect((1500, 1500), 3000, WOC_SZ)), (4.5, key_rect((1500, 1500), 3000, WOC_SZ)), (5.7, key_rect((SITE[0][0] + 450, SITE[0][1] - 100), 1500, WOC_SZ)), (6.9, key_rect(SITE[0], 900, WOC_SZ)), (7.5, key_rect(SITE[0], 860, WOC_SZ)), (d, key_rect(SITE[0], 800, WOC_SZ))], WOC_SZ)
    ref = view('2000', r2); ku = seg(t, tw(10, 20, d), tw(12, 20, d) + 0.8)
    if ku > 0:
        last = json.load(open(pjson(fr[-1]))); k = sm(ku) * 0.8; ces = Image.fromarray((np.asarray(ces, np.float32) * (1 - k) + tone_match(ces, ref) * k).clip(0, 255).astype(np.uint8))
        c = last['dubai'][:2]; yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32) / SC; D = np.hypot(xx - c[0], yy - c[1]); far = float(np.hypot(max(c[0], W - c[0]), max(c[1], H - c[1])))
        e = smr(ku); Rr = (0.02 * H) * (1 - e) + (far + 0.36 * H) * e; v = np.clip((Rr - D) / (0.30 * H), 0, 1); m = (v * v * (3 - 2 * v))[..., None]
        base = Image.fromarray((np.asarray(ces, np.float32) * (1 - m) + np.asarray(ref, np.float32) * m).clip(0, 255).astype(np.uint8))
    else: base = ces
    ca = 1 - sm(seg(t, tw(12, 20, d) + 0.2, tw(12, 20, d) + 0.9))
    if ca > 0.01:                                                                  # soft top scrim so the spoken date reads on bright desert
        g = (np.clip(1 - np.linspace(0, 1, PH) / 0.42, 0, 1) ** 1.5 * 0.62 * ca)[:, None, None]; base = Image.fromarray((np.asarray(base, np.float32) * (1 - g)).astype(np.uint8))
    cv = Canvas(base)
    if ca > 0.01: cv.chip('NASA GIBS · Blue Marble + Landsat · 3D globe (CesiumJS) · orientation only', ca)
    if ku > 0.5: cv.chip(chip_for('2000'), sm(seg(t, tw(12, 20, d) + 0.5, tw(12, 20, d) + 1.1)))
    cv._center = True; cv.kinetic((W / 2, H * 0.16), 'NOVEMBER 2000', 54, 0.02, t, spacing=0.14, per=0.035, a=ca * (1 - sm(seg(t, 2.0, 2.6))))
    def lab(key, s, t0, t1, px=22):
        x, y, vis = pj[key]; a = oc(seg(t, t0, t0 + 0.5)) * (1 - sm(seg(t, t1, t1 + 0.5))) * vis * ca
        if a > 0.01 and 20 < x < W - 20 and 40 < y < H - 90: cv.text((x, y - 26), s, px, AMBER, a, anchor='ms', spacing=0.2)
    lab('gulf', 'PERSIAN GULF', tw(11, 20, d) - 0.2, 4.4)
    x, y, vis = pj['dubai']; a = oc(seg(t, 1.9, 2.5)) * vis * ca * (1 - sm(seg(t, 4.4, 4.9)))
    if a > 0.01 and 20 < x < W - 20 and 40 < y < H - 90: cv.ring((x, y), 7, a, 2); cv.text((x + 12, y - 4), 'DUBAI', 20, AMBER, a, anchor='lm', spacing=0.2)
    if ku > 0.55: yearlabel(cv, 'NOVEMBER 2000', t, tw(12, 20, d) + 0.6)
    pa = oc(seg(t, tw(12, 20, d) + 0.5, tw(12, 20, d) + 1.6)); pf = 1 - sm(seg(t, 5.9, 6.6))
    if pa > 0.01 and pf > 0.01: draw_coast(cv, r2, pa, pf)
    c = to_screen(r2, SITE[0]); rr = SITE[1] * W / r2[2]; ring_dashed(cv, c, rr, sm(seg(t, 5.6, 6.0)) * (1 - sm(seg(t, 7.3, 7.8))), phase=t * 14, frac=oc(seg(t, 5.6, 6.8)))
    big(cv, 'NO ISLAND HERE', H * 0.17, sm(seg(t, tw(13, 20, d) - 0.1, tw(13, 20, d) + 0.4)) * (1 - sm(seg(t, 7.0, 7.4))))
    sea_tint(cv, r2, sm(seg(t, tw(18, 20, d) - 0.2, tw(18, 20, d) + 0.5)))
    overlay_new_land(cv, r2, 0.0, oc(seg(t, 7.2, 7.9)), fill_a=0.0, edge_a=0.85); return cv

H1E = with_entry(H1, H0, 3.0, 'iris', 0.6, center=lambda: to_screen(path(3.0, 3.0, H0_KEYS(), ISS_SZ), PJI[0])); H3E = with_entry(H3, H2, 8.0, 'slide', 0.5); H4E = with_entry(H4, H3, 11.0, 'dissolve', 0.6); A1E = with_entry(A1, H4, 9.0, 'dissolve', 0.7)
SCENES = [('H0', 0, 3, [], H0), ('H1', 3, 10, [1], H1E), ('H2', 13, 8, [2], H2), ('H3', 21, 11, [3], H3E), ('H4', 32, 9, [4], H4E), ('A1', 41, 20, [5], A1E), ('A2', 61, 23, [6, 7], A2), ('A3', 84, 27, [8, 9], A3),
          ('B1', 111, 13, [10], B1), ('B2', 124, 15, [11], B2), ('B3', 139, 20, [12], B3), ('B4', 159, 17, [13], B4), ('B5', 176, 30, [14], B5), ('B6', 206, 15, [15], B6), ('B7', 221, 14, [16], B7),
          ('C1', 235, 20, [17], C1), ('C2', 255, 20, [18], C2), ('C3', 275, 18, [19], C3), ('C4', 293, 23, [20], C4), ('C5', 316, 21, [21], C5), ('C6', 337, 25, [22], C6),
          ('D1', 362, 17, [23], D1), ('D2', 379, 17, [24], D2), ('D5', 396, 30, [25], D5), ('E1', 426, 20, [26], E1), ('E2', 446, 32, [27], E2), ('E4', 478, 27, [28], E4), ('E5', 505, 27, [29], E5), ('E6', 532, 9, [30], E6)]

import scenes_v6 as _v6                       # V6 visual standard for A3, C2, C4, C6, D5, E1, E4, B7 (must stay the last statement: replaces entries of SCENES)
_v6.install(sys.modules[__name__])
SCENES_V4 = [('H1', 0, 8, [1], HV1), ('H2', 8, 8, [2], H2), ('H3', 16, 11, [3], H3E), ('H4', 27, 9, [4], H4E)]
