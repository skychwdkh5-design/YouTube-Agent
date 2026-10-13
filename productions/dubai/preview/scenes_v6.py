"""EP002 V6 visual standard applied to the text-heavy scenes (A3, C2, C4, C6, D5, E1, E4, B7). Imported at the bottom of scenes.py (install()).
Rules: real imagery as the base, outlines TRACED from that image's pixels (thresholded sea mask), one main label at a time (big), arrows/pings are UI explanations,
no scale bars or distances (no georeference, claim 32), no wipes, 2000/2003/2011 share one ASTER grid (registration <= 1 px measured for 2000 vs 2003).
Timing ESTIMATED (145 wpm inside the scene window): cue = tw(i, n, d); re-derive from provider word timings after TTS."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter
from kit import *
import scenes as S
from scenes import chip_for, date_for, yearlabel, ISSCHIP, big, arrow, path, key_rect, clampr, tw, sea_tint, coast_line, draw_coast, ring_dashed, P2_SZ, WOC_SZ, ISS_SZ, PJ2, PJA2, WORLD2, DEIRA2, PJI, SITE, CYAN, paste_view

SEA_REF = {'palm2': (400, 600, 300, 300), '2000': (0, 1250, 280, 150), '2003': (0, 1250, 280, 150), '2011': (0, 1250, 280, 150), 'iss': (0, 2400, 300, 300)}
_TR = {}
def trace(key, c, R, thr, rad=1.25):
    """land mask = pixels far (colour distance >= thr) from the median colour of a sea-only patch, inside rad*R of c; fill + outline + polar angle for draw-on"""
    k = (key, round(c[0]), round(c[1]), R, thr)
    if k in _TR: return _TR[k]
    a = np.asarray(src(key), np.float32); rx, ry, rw, rh = SEA_REF[key]; ref = np.median(a[ry:ry + rh, rx:rx + rw].reshape(-1, 3), 0); Sz = int(R * 2.7)
    x0 = int(min(max(c[0] - Sz / 2, 0), a.shape[1] - Sz)); y0 = int(min(max(c[1] - Sz / 2, 0), a.shape[0] - Sz)); d = np.sqrt(((a[y0:y0 + Sz, x0:x0 + Sz] - ref) ** 2).sum(2))
    yy, xx = np.mgrid[0:Sz, 0:Sz]; cx, cy = c[0] - x0, c[1] - y0; dist = np.hypot(xx - cx, yy - cy); land = (d >= thr) & (dist <= R * rad)
    m = Image.fromarray((land * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(3)); fill = np.asarray(m) > 127
    edge = fill & ~(np.asarray(m.filter(ImageFilter.MinFilter(5))) > 127); edge = np.asarray(Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 127
    _TR[k] = dict(x0=x0, y0=y0, S=Sz, fill=fill, edge=edge, dist=dist / (R * rad), ang=(np.arctan2(yy - cy, xx - cx) / (2 * math.pi)) % 1.0); return _TR[k]
def overlay(cv, tr, box, scr, fill_p=0.0, edge_p=0.0, col=AMBER, fill_a=0.3, edge_a=1.0):
    """draw a traced region (source pixels) into the screen rect scr = (x, y, w, h) that shows source box = (x, y, w, h)"""
    Sz = tr['S']; rgba = np.zeros((Sz, Sz, 4), np.uint8); c = np.array(col, np.uint8)
    f = tr['fill'] & (tr['dist'] <= fill_p * 1.02) if fill_p > 0 else np.zeros_like(tr['fill']); e = tr['edge'] & (tr['ang'] <= edge_p) if edge_p > 0 else np.zeros_like(tr['edge'])
    if not (f.any() or e.any()): return
    rgba[f, :3] = c; rgba[f, 3] = int(255 * fill_a); rgba[e, :3] = c; rgba[e, 3] = int(255 * edge_a)
    k = scr[2] * SC / box[2]; sw = max(int(Sz * k), 1)
    if sw < 4: return
    im = Image.fromarray(rgba, 'RGBA').resize((sw, sw), Image.LANCZOS); pan = Image.new('RGBA', (int(round(scr[2] * SC)), int(round(scr[3] * SC))), (0, 0, 0, 0)); pan.paste(im, (int(round((tr['x0'] - box[0]) * k)), int(round((tr['y0'] - box[1]) * k))))
    lay = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); lay.paste(pan, (int(round(scr[0] * SC)), int(round(scr[1] * SC)))); cv.o = Image.alpha_composite(cv.o, lay); cv.d = mkdraw(cv.o)
FULL = (0, 0, W, H)
_TH = {}
def thumb(kk, w, h, wide=700):
    k = (kk, w, h, wide)
    if k not in _TH:
        c, _ = woc_ring(kk); x, y, bw, bh = rect_c(c, wide, aspect=w / h, dx=130 if wide == 700 else 150); _TH[k] = src(kk).resize((int(round(w * SC)), int(round(h * SC))), Image.LANCZOS, box=(x, y, x + bw, y + bh)).convert('RGBA')
    return _TH[k]
def put(cv, tile, x, y, a=1.0):
    """paste a physical-size tile at LOGICAL (x, y) with opacity a"""
    cv.o.paste(tile, (int(round(x * SC)), int(round(y * SC))), Image.new('L', tile.size, int(255 * min(1, max(0, a)))))
def tiny(cv, s, a=1.0, y=20): cv.pill((22, y), s, 12, a * 0.85, accent=AMBER)
def strip(cv, t, labels, pos, a=1.0, y=58):
    """thin timeline strip with labelled ticks and a moving marker (pos 0..1)"""
    x0, x1 = 90, W - 90; cv.d.line([(x0, y), (x1, y)], fill=MUTED + (int(150 * a),), width=2)
    for i, lab in enumerate(labels):
        x = x0 + (x1 - x0) * i / (len(labels) - 1); cv.d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=MUTED + (int(220 * a),)); cv.text((x, y + 10), lab, 13, MUTED, a, anchor='ma', spacing=0.12)
    px = x0 + (x1 - x0) * pos; cv.d.polygon([(px, y - 5), (px - 7, y - 17), (px + 7, y - 17)], fill=AMBER + (int(255 * a),))

# ---------------------------------------------------------------- A3 (27 s): real 2000 coast; arrows outward; The World plan as a schematic counter; the blank page
def A3(t, d, X):
    keys = [(0, key_rect((1500, 1500), 3000, WOC_SZ)), (10, key_rect((1050, 1450), 1900, WOC_SZ)), (19, key_rect((900, 1550), 1500, WOC_SZ)), (d, key_rect(SITE[0], 1150, WOC_SZ))]
    r = path(t, d, keys, WOC_SZ); lift = sm(seg(t, 23.5, 25.0)); cv = Canvas(dim(view('2000', r), 0.58 + 0.42 * lift)); tiny(cv, 'NASA ASTER · 2000 · colours as published · dimmed for legibility', 1 - lift)
    cp = oc(seg(t, 1.0, 4.8)); pf = 1 - sm(seg(t, 12.0, 13.0))
    if pf > 0.01: draw_coast(cv, r, cp, pf)
    pts = coast_line(); ar = oc(seg(t, 7.8, 10.0)) * (1 - sm(seg(t, 12.0, 13.0)))
    for j in (4, 22, 40, 58, 76, 92):
        j = min(j, len(pts) - 2); p, q = pts[j - 2], pts[j + 2]; tx, ty = q[0] - p[0], q[1] - p[1]; n = math.hypot(tx, ty) or 1; nx, ny = ty / n, -tx / n
        if nx > 0: nx, ny = -nx, -ny                                                       # point toward the sea (smaller x)
        a0 = to_screen(r, pts[j]); a1 = to_screen(r, (pts[j][0] + nx * 230, pts[j][1] + ny * 230)); arrow(cv, a0, a1, ar * oc(seg(t, 7.8 + 0.12 * (j % 5), 9.4 + 0.12 * (j % 5))), wd=3, head=12)
    if t > 10.0: strip(cv, t, ['1990s · PLANS', 'EARLY 2000s'], oc(seg(t, 10.6, 19.2)) , sm(seg(t, 10.0, 10.6)) * (1 - sm(seg(t, 25, 26))))
    for txt, a0, a1 in (('HUNDREDS OF ARTIFICIAL ISLANDS', 5.2, 8.0), ('MORE BEACHFRONT FOR TOURISM', 8.3, 11.4), ('THE WORLD · ABOUT 300 SMALL ISLANDS', 13.4, 19.0), ('LITTLE BUILT BEYOND SHALLOW WATER', 19.4, 24.2), ('THE BLANK PAGE', 24.6, 27.0)):
        big(cv, txt, H * 0.21 if t > 10 else H * 0.13, sm(seg(t, a0, a0 + 0.4)) * (1 - sm(seg(t, a1 - 0.3, a1))), 28)
    if 12.6 < t < 19.6:                                                                     # schematic panel: one dot = one planned island, NOT a location
        k = sm(seg(t, 12.6, 13.4)) * (1 - sm(seg(t, 18.8, 19.6))); ss = SS(); rx0, ry0, rx1, ry1 = 560, 190, 900, 410; ss.rect(rx0, ry0, rx1, ry1, fill=(8, 14, 22, int(215 * k)), outline=CYAN + (int(160 * k),), width=1.2, r=6)
        S.dots_field(ss, (rx0 + 14, ry0 + 14, rx1 - 14, ry1 - 14), 300, oc(seg(t, 14.0, 17.5)), CYAN + (int(220 * k),), r=2.6); layer(cv, ss)
        cv.text((rx1 - 16, ry1 - 46), f'{int(300 * oc(seg(t, 14.0, 17.5)))}', 34, AMBER, k, anchor='ra'); cv.text((rx0 + 14, ry0 + 8), 'SCHEMATIC · one dot = one planned island, not a position', 11, MUTED, k)
    sea_tint(cv, r, sm(seg(t, 24.2, 25.2))); c = to_screen(r, SITE[0]); ring_dashed(cv, c, SITE[1] * W / r[2], sm(seg(t, 24.6, 25.2)), phase=t * 14, frac=oc(seg(t, 24.6, 26.0))); return cv

# ---------------------------------------------------------------- C2 (20 s): the three designs on the real 2006 frame, outlines traced
def C2(t, d, X):
    keys = [(0, key_rect(PJA2[0], 1150, P2_SZ)), (2.8, key_rect(PJ2[0], 1250, P2_SZ)), (6.0, key_rect(WORLD2, 1700, P2_SZ)), (12.0, key_rect(WORLD2, 1000, P2_SZ)), (d, key_rect(WORLD2, 1300, P2_SZ))]
    r = path(t, d, keys, P2_SZ); cv = Canvas(view('palm2', r)); tiny(cv, chip_for('palm2') + ' · outlines traced from this image (UI)')
    for tr, col, e0, e1, f0, f1 in ((trace('palm2', PJA2[0], PJA2[1] * 1.0, 110, 1.12), AMBER, 0.8, 2.4, 0, 0), (trace('palm2', PJ2[0], PJ2[1] * 1.0, 110, 1.12), AMBER, 2.9, 4.5, 0, 0), (trace('palm2', WORLD2, 330, 110, 1.0), CYAN, 7.7, 10.0, 12.8, 15.0)):
        overlay(cv, tr, r, FULL, fill_p=oc(seg(t, f0, f1)) if f1 else 0, edge_p=oc(seg(t, e0, e1)), col=col, fill_a=0.28)
    for txt, a0, a1 in (('SHAPED AS PALMS', 3.3, 5.3), ('NOT A PALM', 5.6, 7.7), ('A MAP OF EARTH', 8.0, 12.4), ('ABOUT 300 SMALL ISLANDS', 12.8, 15.6), ('THE PLANET, DRAWN IN THE SEA', 15.9, 20.0)):
        big(cv, txt, H * 0.14, sm(seg(t, a0, a0 + 0.4)) * (1 - sm(seg(t, a1 - 0.3, a1))), 30)
    cv.ping(to_screen(r, PJA2[0]), t, 0.7, r=max(18, 150 * W / r[2]), n=1); cv.ping(to_screen(r, PJ2[0]), t, 2.9, r=max(18, 150 * W / r[2]), n=1); cv.ping(to_screen(r, WORLD2), t, 7.8, r=max(20, 190 * W / r[2]), n=1, col=CYAN); return cv

# ---------------------------------------------------------------- C4 (23 s): jump ahead to 2022 (year counter), The World traced, only what NASA's caption says
def C4(t, d, X):
    r = path(t, d, [(0, key_rect(WORLD2, 1750, P2_SZ)), (d, key_rect(WORLD2, 1150, P2_SZ))], P2_SZ); cv = Canvas(dim(view('palm2', r), 0.42)); tiny(cv, 'Background: NASA ASTER · 2006 · colours as published (not 2022)')
    overlay(cv, trace('palm2', WORLD2, 330, 110, 1.0), r, FULL, edge_p=oc(seg(t, 3.0, 6.0)), col=CYAN, edge_a=0.9)
    u = oc(seg(t, 1.6, 3.2)); yr = int(round(2006 + 16 * u)); cv.text((50, 70), f'{yr}', 96, AMBER if u > 0.98 else TEXT, 1.0, anchor='la')
    big(cv, 'ONLY A HANDFUL', H * 0.40, sm(seg(t, 6.2, 6.7)) * (1 - sm(seg(t, 10.8, 11.2))), 40); cv.text((W / 2, H * 0.40 + 92), "of The World's roughly 300 islands had seen development", 20, TEXT, sm(seg(t, 7.2, 7.8)) * (1 - sm(seg(t, 10.8, 11.2))), anchor='ma')
    cv.text((W / 2, H * 0.40 + 124), "NASA's caption for the astronaut's photograph", 15, MUTED, sm(seg(t, 8.2, 8.8)) * (1 - sm(seg(t, 10.8, 11.2))), anchor='ma', bold=False)
    for txt, a0, a1 in (('A STATEMENT ABOUT 2022', 11.2, 15.6), ('NO RELIABLE SOURCE SINCE', 16.0, 20.3), ('SO WE WILL NOT GUESS', 20.6, 23.0)): big(cv, txt, H * 0.40, sm(seg(t, a0, a0 + 0.4)) * (1 - sm(seg(t, a1 - 0.3, a1))), 36)
    return cv

# ---------------------------------------------------------------- C6 (25 s): one method, two outcomes: Palm Jumeirah 2003 -> 2011 | The World 2006
def fit(c, w, scr, size):
    h = w * scr[3] / scr[2]
    if h > size[1] * 0.98: h = size[1] * 0.98; w = h * scr[2] / scr[3]
    if w > size[0] * 0.98: w = size[0] * 0.98; h = w * scr[3] / scr[2]
    x = min(max(c[0] - w / 2, 0), size[0] - w); y = min(max(c[1] - h / 2, 0), size[1] - h); return (x, y, w, h)
def C6(t, d, X):
    sp = smr(seg(t, 7.0, 8.4)); lw = W - (W / 2) * sp; scrL = (0, 0, lw, H); scrR = (lw, 0, W - lw, H); z = 1 - 0.06 * tm(t) / d; img = Image.new('RGB', (PW, PH), INK); LW = int(round(lw * SC))
    cs = SITE[0]; wL = 760 * z if sp > 0.5 else 1100 * z; boxL = fit((cs[0] + 40, cs[1]), wL, scrL, WOC_SZ) if lw > 1 else None; k = sm(seg(t, 10.7, 12.0))
    if lw > 2:
        a = src('2003').resize((LW, PH), Image.LANCZOS, box=(boxL[0], boxL[1], boxL[0] + boxL[2], boxL[1] + boxL[3])); b = src('2011').resize((LW, PH), Image.LANCZOS, box=(boxL[0], boxL[1], boxL[0] + boxL[2], boxL[1] + boxL[3])); img.paste(Image.blend(a, b, k), (0, 0))
    if W - lw > 2:
        boxR = fit(WORLD2, 1050 * z, scrR, P2_SZ); img.paste(src('palm2').resize((PW - LW, PH), Image.LANCZOS, box=(boxR[0], boxR[1], boxR[0] + boxR[2], boxR[1] + boxR[3])), (LW, 0))
    cv = Canvas(img)
    if lw > 2: overlay(cv, S.new_land(), boxL, scrL, edge_p=oc(seg(t, 1.0, 3.5)), col=AMBER, edge_a=0.9)
    if W - lw > 2: overlay(cv, trace('palm2', WORLD2, 330, 110, 1.0), boxR, scrR, edge_p=oc(seg(t, 9.0, 11.0)), col=CYAN, edge_a=0.9)
    if sp > 0.02: cv.d.rectangle([lw - 1.5, 0, lw + 1.5, H], fill=INK + (255,))
    tiny(cv, 'NASA ASTER · Palm Jumeirah 2003 → 2011 | The World 2006 image · outlines traced (UI)')
    big(cv, 'DREDGED SAND · PROTECTED BY ROCK', H * 0.15, sm(seg(t, 3.6, 4.0)) * (1 - sm(seg(t, 6.6, 7.0))), 28)
    big(cv, '2011', H * 0.68, sm(seg(t, 10.8, 11.3)) * (1 - sm(seg(t, 17.0, 17.4))), 44) if False else None
    if sp > 0.9: cv.pill((14, 44), 'PALM JUMEIRAH', 13, a=sm(seg(t, 8.4, 9.0)), accent=AMBER); cv.pill((W / 2 + 14, 44), 'THE WORLD', 13, a=sm(seg(t, 8.6, 9.2)), accent=CYAN)
    cv.text((W * 0.25, H * 0.68), '2011', 44, AMBER, sm(seg(t, 10.8, 11.3)), anchor='ma'); cv.text((W * 0.75, H * 0.68), '2022', 44, CYAN, sm(seg(t, 17.0, 17.5)), anchor='ma')
    cv.text((W * 0.25, H * 0.68 + 54), 'green fronds · buildings on the trunk', 16, TEXT, sm(seg(t, 13.0, 13.8)), anchor='ma', bold=False); cv.text((W * 0.75, H * 0.68 + 54), 'only a handful of islands developed', 16, TEXT, sm(seg(t, 18.5, 19.3)), anchor='ma', bold=False)
    big(cv, 'SIMILAR METHOD · VERY DIFFERENT OUTCOMES', H * 0.14, sm(seg(t, 22.0, 22.5)), 28); return cv

# ---------------------------------------------------------------- D5 (30 s): sources as a dated timeline of real thumbnails
def D5(t, d, X):
    cv = Canvas(text_card_bg()); keys = ['2000', '2002a', '2002b', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011']; yrs = [2000, 2002.1, 2002.8, 2003.85, 2004.85, 2005.8, 2006.7, 2007.2, 2008.85, 2009.1, 2010.1, 2011.3]
    x0, x1, yl = 60, W - 60, H * 0.70; X_ = lambda y: x0 + (x1 - x0 - 150) * (y - 2000) / 11.5 if y < 2020 else x1 - 40
    cv.d.line([(x0, yl), (x1, yl)], fill=MUTED + (170,), width=2)
    for y in (2000, 2003, 2006, 2009, 2011):
        cv.d.line([(X_(y), yl - 5), (X_(y), yl + 5)], fill=MUTED + (200,), width=1); cv.text((X_(y), yl + 12), str(y), 13, MUTED, anchor='ma')
    cv.d.line([(x1 - 110, yl - 6), (x1 - 100, yl + 6)], fill=MUTED + (200,), width=2); cv.d.line([(x1 - 100, yl - 6), (x1 - 90, yl + 6)], fill=MUTED + (200,), width=2); cv.text((x1 - 40, yl + 12), '2022', 13, MUTED, anchor='ma')
    tb = sm(seg(t, 13.4, 14.2)); tw_, th_ = 92, 92
    for i, (kk, yy) in enumerate(zip(keys, yrs)):
        k = oc(seg(t, 8.0 + i * 0.22, 8.6 + i * 0.22)); tile = thumb(kk, tw_, th_); xx = X_(yy); ov = i % 2
        put(cv, tile, xx - tw_ / 2, yl - 20 - th_ - ov * (th_ + 14) + (1 - k) * 10, k)
        cv.d.line([(xx, yl - 18 - ov * (th_ + 14)), (xx, yl)], fill=AMBER + (int(150 * k),), width=1)
    if tb > 0:
        iss = src('iss').resize((int(130 * SC), int(130 * SC)), Image.LANCZOS, box=(PJI[0][0] - 700, PJI[0][1] - 700, PJI[0][0] + 700, PJI[0][1] + 700)).convert('RGBA'); xx = X_(2022); put(cv, iss, xx - 65, yl - 20 - 130 + (1 - tb) * 10, tb)
        cv.d.line([(xx, yl - 18), (xx, yl)], fill=CYAN + (int(180 * tb),), width=1)
    ka = sm(seg(t, 0.3, 1.0)) * (1 - sm(seg(t, 8.2, 8.9)))
    if ka > 0.01:                                                                          # anatomy of one caption: source, instrument, year (real ASTER 2006 crop)
        bx_, by_, bw_, bh_ = key_rect(PJ2[0], 900 - 70 * min(max(t / 8.0, 0), 1), P2_SZ); card = src('palm2').resize((int(300 * SC), int(169 * SC)), Image.LANCZOS, box=(bx_, by_, bx_ + bw_, by_ + bw_ * 169 / 300)).convert('RGBA'); cx0, cy0 = 150, H * 0.30; put(cv, card, cx0, cy0, ka)
        for j, (lab, a0_) in enumerate((('SOURCE · NASA', 4.4), ('INSTRUMENT · ASTER', 5.4), ('YEAR · 2006', 6.4))):
            kk_ = sm(seg(t, a0_, a0_ + 0.5)) * ka; y_ = cy0 + 20 + j * 52; xl = cx0 + 300 + 30; cv.d.line([(cx0 + 300, y_ + 14), (xl, y_ + 14)], fill=AMBER + (int(255 * kk_),), width=2); cv.text((xl + 8, y_), lab, 24, AMBER, kk_, anchor='la', spacing=0.08)
    for txt, a0, a1, px in (('EVERY IMAGE: SOURCE · INSTRUMENT · YEAR', 0.3, 7.6, 28), ('MOST: ASTER, AN INSTRUMENT ON A SATELLITE', 8.0, 12.8, 26), ('ONE: AN ASTRONAUT PHOTO · NIKON CAMERA', 13.2, 16.0, 26), ('SEPARATE DAYS · NEVER OVERLAID', 16.2, 26.0, 28), ('ONE IMAGE: YEAR ONLY', 27.0, 30.0, 30)):
        big(cv, txt, H * 0.15, sm(seg(t, a0, a0 + 0.4)) * (1 - sm(seg(t, a1 - 0.3, a1))), px)
    if t > 20.0:                                                                           # "never overlay one on another": two frames with a crossed overlay mark
        k = sm(seg(t, 20.2, 21.0)) * (1 - sm(seg(t, 25.0, 26.0))); ss = SS(); cx, cy = W / 2, H * 0.40
        ss.rect(cx - 150, cy - 45, cx - 40, cy + 45, outline=AMBER + (int(255 * k),), width=2.4, r=4); ss.rect(cx + 40, cy - 45, cx + 150, cy + 45, outline=CYAN + (int(255 * k),), width=2.4, r=4)
        ss.ellipse((cx, cy), 26, outline=(234, 90, 90, int(255 * k)), width=3); ss.line([(cx - 18, cy + 18), (cx + 18, cy - 18)], (234, 90, 90, int(255 * k)), 3); layer(cv, ss)
    if t > 27.0:
        k = sm(seg(t, 27.2, 28.0)); xx = X_(2011.3); cv.ring((xx, yl - 20 - th_ / 2 - (th_ + 14)), 62, k, 2); cv.text((xx, yl + 34), 'YEAR ONLY', 14, AMBER, k, anchor='ma', spacing=0.12)
    tiny(cv, 'Thumbnails: the real ASTER frames (colours as published) and the ISS photograph, placed by year · not to be compared pixel for pixel'); return cv

# ---------------------------------------------------------------- E1 (20 s): the record as a scrolling filmstrip with a dated playhead
def E1(t, d, X):
    cv = Canvas(text_card_bg()); keys = ['2000', '2002a', '2002b', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011']; tt = [1.4 + i * 1.3 for i in range(12)]; speed = 215; tw_, th_ = 250, 140; yc = H * 0.47
    te = min(t, tt[-1] + 0.2); m = sm(seg(t, 16.2, 17.4)); cw, chh = 72, 40
    for i, kk in enumerate(keys):
        xs = W / 2 + (tt[i] - te) * speed; xcmp = 60 + cw / 2 + i * (W - 120 - cw) / 11; xc = xs + (xcmp - xs) * m
        if xc < -tw_ or xc > W + tw_: continue
        near = (1 - min(abs(tt[i] - te) / 0.9, 1)) * (1 - m); sc = 1 + 0.38 * near * near; w_ = int(round((tw_ * sc + (cw - tw_ * sc) * m) / 4) * 4); h_ = int(round((th_ * sc + (chh - th_ * sc) * m) / 4) * 4)
        yy = yc + (H * 0.58 - yc) * m; tile = thumb(kk, w_, h_, 760); a = min(1, oc(seg(t, tt[i] - 2.8, tt[i] - 2.0)) * 0.55 + 0.45 * near + m)
        put(cv, tile, xc - w_ / 2, yy - h_ / 2, a); cv.d.rectangle([xc - w_ / 2, yy - h_ / 2, xc + w_ / 2, yy + h_ / 2], outline=AMBER + (int(255 * max(near, 0.5 * m)),), width=2)
        lab = date_for(kk) if m < 0.5 else date_for(kk)[-4:]; edge = sm(min(max((min(xc, W - xc) - 60) / 90.0, 0), 1)); cv.text((xc, yy + h_ / 2 + 8), lab, int(22 if near > 0.5 else 15 - 3 * m), AMBER if near > 0.5 or m > 0.5 else MUTED, (0.5 + 0.5 * max(near, m)) * edge, anchor='ma', spacing=0.08)    # labels fade before they reach the frame edge (no cut-off text)
    ss = SS(); ss.line([(W / 2, yc - 112), (W / 2, yc - 92)], AMBER + (int(255 * (1 - m)),), 2.4); ss.poly([(W / 2, yc - 88), (W / 2 - 8, yc - 100), (W / 2 + 8, yc - 100)], fill=AMBER + (int(255 * (1 - m)),)); layer(cv, ss)
    x0, x1, yb = 120, W - 120, H - 52; cv.d.line([(x0, yb), (x1, yb)], fill=MUTED + (int(150 * (1 - m)),), width=2); cv.d.line([(x0, yb), (x0 + (x1 - x0) * oc(seg(t, 1.4, 14.7)), yb)], fill=AMBER + (int(255 * (1 - m)),), width=4)
    cv.text((x0, yb + 8), '2000', 13, MUTED, 1 - m, anchor='ma'); cv.text((x1, yb + 8), '2011', 13, MUTED, 1 - m, anchor='ma')
    for txt, a0, a1 in (('12 ASTER IMAGES · 2000–2011', 0.2, 5.2), ('EMPTY SEA → FIRST STAGE → FRONDS → A FINISHED PALM', 5.4, 11.6), ('YEARS OF BUILDINGS AND VEGETATION', 11.8, 15.0), ('EACH ONE A DATED FACT', 15.2, 17.4), ('A TIMELINE YOU CAN CHECK', 17.6, 20.0)):
        big(cv, txt, H * 0.13, sm(seg(t, a0, a0 + 0.4)) * (1 - sm(seg(t, a1 - 0.3, a1))), 26)
    tiny(cv, 'NASA ASTER · 12 images, 2000–2011 · colours as published · crop centred on the palm site'); return cv

# ---------------------------------------------------------------- E4 (27 s): the 2000 coastline stays drawn while the 2003 palm dissolves in
def E4(t, d, X):
    r = path(t, d, [(0, key_rect(SITE[0], 1250, WOC_SZ)), (13, key_rect(SITE[0], 950, WOC_SZ)), (23.4, key_rect(SITE[0], 1100, WOC_SZ))], WOC_SZ)
    k = sm(seg(t, 6.6, 8.0)); u = sm(seg(t, 23.4, 24.2)); base = dissolve(view('2000', r), view('2003', r), k)
    if u > 0:
        r2 = path(t, d, [(23.4, key_rect(WORLD2, 1500, P2_SZ)), (d, key_rect(WORLD2, 1150, P2_SZ))], P2_SZ); base = dissolve(base, view('palm2', r2), u)
    cv = Canvas(base)
    if u < 0.99:
        c = coast_line(); n = len(c); cp = oc(seg(t, 1.5, 4.0)); pts = [to_screen(r, q) for q in c[:max(2, int(n * cp))]]; ss = SS(); ss.line(pts, AMBER + (int(90 * (1 - u)),), 12); ss.line(pts, AMBER + (int(250 * (1 - u)),), 4.4); layer(cv, ss)
        overlay(cv, S.new_land() | {}, r, FULL, fill_p=oc(seg(t, 8.0, 10.0)), edge_p=1.0 if k > 0.5 else 0.0, col=AMBER, fill_a=0.30 * (1 - 0.5 * sm(seg(t, 13, 15))), edge_a=0.9 * (1 - u)) if False else None
        tr = S.new_land(); overlay(cv, tr, r, FULL, fill_p=oc(seg(t, 8.0, 10.0)) * (1 - u), edge_p=oc(seg(t, 8.0, 9.5)) * (1 - u), col=AMBER, fill_a=0.30, edge_a=0.9)
    else: overlay(cv, trace('palm2', WORLD2, 330, 110, 1.0), r2, FULL, edge_p=oc(seg(t, 24.5, 26.5)), col=CYAN, edge_a=0.9)
    tiny(cv, 'NASA ASTER · 2000 → 2003 · same grid · the line is the 2000 shoreline traced from the 2000 image' if u < 0.5 else chip_for('palm2'))
    cv.text((W - 24, 40), 'NOVEMBER 2000', 30, AMBER, (1 - sm(seg(t, 6.4, 7.2))) * (1 - u), anchor='ra', spacing=0.14); cv.text((W - 24, 40), 'NOVEMBER 2003', 30, AMBER, sm(seg(t, 7.4, 8.0)) * (1 - u), anchor='ra', spacing=0.14)
    for txt, a0, a1 in (('A MAP DRAWN IN 2000: OPEN WATER HERE', 3.8, 6.8), ('BY 2003, THAT MAP IS WRONG', 7.8, 12.2), ('SAND FROM THE SEA FLOOR', 12.6, 15.2), ('A RING OF ROCK', 15.4, 17.4), ('A COASTLINE IS NOT A FIXED LINE', 17.6, 20.2), ('IT GAVE DUBAI A PALM', 20.4, 22.6), ('AND A PLAN FOR A MAP OF EARTH', 22.8, 27.0)):
        big(cv, txt, H * 0.16, sm(seg(t, a0, a0 + 0.4)) * (1 - sm(seg(t, a1 - 0.3, a1))), 28)
    c = to_screen(r, SITE[0]); ring_dashed(cv, c, SITE[1] * W / r[2], sm(seg(t, 15.4, 15.9)) * (1 - sm(seg(t, 17.2, 17.6))) * (1 - u), phase=t * 14); return cv

# ---------------------------------------------------------------- B7 (14 s): the first of several, then all four still under construction
def B7(t, d, X):
    keys = [(0, key_rect(PJ2[0], 900, P2_SZ)), (4.8, key_rect(PJ2[0], 1250, P2_SZ)), (8.8, key_rect((1500, 1900), 2900, P2_SZ)), (d, key_rect((1500, 1900), 3070, P2_SZ))]
    r = path(t, d, keys, P2_SZ); cv = Canvas(view('palm2', r)); cv.chip(chip_for('palm2')); yearlabel(cv, '2006', t, 0.3)
    overlay(cv, trace('palm2', PJ2[0], PJ2[1] * 1.0, 110, 1.12), r, FULL, edge_p=oc(seg(t, 0.8, 2.8)), col=AMBER, edge_a=0.95)
    big(cv, 'THE FIRST OF SEVERAL', H * 0.15, sm(seg(t, 3.0, 3.4)) * (1 - sm(seg(t, 6.8, 7.2))), 30)
    big(cv, 'ALL STILL UNDER CONSTRUCTION', H * 0.15, sm(seg(t, 9.0, 9.4)), 28)
    for j, (c, rad, t0) in enumerate(((PJA2[0], 150, 8.8), (WORLD2, 190, 9.3), (DEIRA2, 120, 9.8))): cv.ping(to_screen(r, c), t, t0, r=max(18, rad * W / r[2]), n=1)
    return cv

def install(mod):
    fns = {'A3': A3, 'C2': C2, 'C4': C4, 'C6': C6, 'D5': D5, 'E1': E1, 'E4': E4, 'B7': B7}; ent = {'D5': 'D2', 'E1': 'D5', 'B4': 'B3', 'E6': 'E5'}   # card scenes enter by a 0.6 s dissolve from the previous scene (no blank start)
    cur = {sid: fns.get(sid, fn) for sid, st, d, vos, fn in mod.SCENES}; dur = {sid: d for sid, st, d, vos, fn in mod.SCENES}
    out = []
    for sid, st, d, vos, fn in mod.SCENES:
        f = fns.get(sid, fn)
        if sid in ent: f = mod.with_entry(f, cur[ent[sid]], dur[ent[sid]], 'dissolve', 0.6)
        out.append((sid, st, d, vos, f))
    mod.SCENES = out; mod.PUSH = {k: v for k, v in mod.PUSH.items() if k not in fns}; mod.PUSH.update({'B3': 0.05, 'B4': 0.055, 'D5': 0.03})
