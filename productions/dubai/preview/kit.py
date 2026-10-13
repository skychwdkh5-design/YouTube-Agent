"""EP002 preview kit: sizes, easing, source loading, drawing helpers. Preview = 960x540 @ 12 fps, silent, ESTIMATED timing."""
import os, sys, math, zipfile, glob, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from orbitalatlas import easing as E

W, H = 960, 540                                      # LOGICAL canvas: every coordinate, font size and line width in the scene code is in these units
FPS = int(os.environ.get('EP002_FPS', '24'))
SC = float(os.environ.get('EP002_SCALE', '1'))        # physical scale: 1 = 960x540 preview, 2 = native 1920x1080 (text/vectors are drawn at physical resolution, not upscaled)
PW, PH = int(round(W * SC)), int(round(H * SC))
K = H / 1080.0
INK, TEXT, AMBER, CYAN, MUTED = (11, 15, 20), (234, 240, 246), (255, 194, 71), (92, 225, 230), (138, 148, 163)
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
_fc = {}
def F(px, bold=True):
    k = (round(px * SC * 8), bold)
    if k not in _fc: _fc[k] = ImageFont.truetype(FB if bold else FR, max(8, round(px * SC)))
    return _fc[k]
class SDraw:
    """ImageDraw proxy taking LOGICAL coordinates (960x540 space) and drawing at physical resolution (SC); textlength returns logical units"""
    def __init__(self, d): self.d = d
    @staticmethod
    def _c(xy):
        if xy and isinstance(xy[0], (tuple, list)): return [(float(p[0]) * SC, float(p[1]) * SC) for p in xy]
        return [float(v) * SC for v in xy]
    def _w(self, w): return max(1, int(round(w * SC))) if w else w
    def line(self, xy, fill=None, width=1, joint=None): self.d.line(self._c(xy), fill=fill, width=self._w(width), joint=joint)
    def ellipse(self, xy, fill=None, outline=None, width=1): self.d.ellipse(self._c(xy), fill=fill, outline=outline, width=self._w(width))
    def rectangle(self, xy, fill=None, outline=None, width=1): self.d.rectangle(self._c(xy), fill=fill, outline=outline, width=self._w(width))
    def rounded_rectangle(self, xy, radius=0, fill=None, outline=None, width=1): self.d.rounded_rectangle(self._c(xy), radius * SC, fill=fill, outline=outline, width=self._w(width))
    def polygon(self, xy, fill=None, outline=None, width=1): self.d.polygon(self._c(xy), fill=fill, outline=outline)
    def arc(self, xy, start, end, fill=None, width=1): self.d.arc(self._c(xy), start, end, fill=fill, width=self._w(width))
    def text(self, xy, s, font=None, fill=None, anchor=None, **kw):
        if kw.get('stroke_width'): kw['stroke_width'] = max(1, int(round(kw['stroke_width'] * SC)))
        self.d.text((xy[0] * SC, xy[1] * SC), s, font=font, fill=fill, anchor=anchor, **kw)
    def textlength(self, s, font=None, **kw): return self.d.textlength(s, font=font, **kw) / SC
def mkdraw(img): return SDraw(ImageDraw.Draw(img))
sm, smr, oc = E.smooth, E.smoother, E.out_cubic
CLK = None            # per-scene smooth clock (word-level estimated time -> smooth estimated time), set by build_final; None in previews
def tm(t): return CLK(t) if CLK else t
def seg(t, a, b):
    """progress of window [a, b]; windows >= 3 s are camera/ease moves and follow the SMOOTH clock, shorter ones are events and follow the word-level clock"""
    if CLK is not None and (b - a) >= 3.0: t = CLK(t)
    return E.clamp((t - a) / max(b - a, 1e-6))

# ------------------------------------------------------------------ sources
HERE = os.path.dirname(os.path.abspath(__file__)); VIS = os.path.join(HERE, '../visuals')
WOC_FILES = {'2000': '20001111', '2002a': '20020202', '2002b': '20021016', '2003': '20031104', '2004': '20041106', '2005': '20051024',
             '2006': '20060918', '2007': '20070304', '2008': '20081117', '2009': '20090205', '2010': '20100208', '2011': '20110425'}
_img = {}
def woc_dir():
    d = os.environ.get('EP002_WOC', '/tmp/ep002_woc')
    if not glob.glob(os.path.join(d, '*.jpg')):
        os.makedirs(d, exist_ok=True); zipfile.ZipFile(os.path.join(VIS, 'OrbitalAtlas_EP002_Dubai_WOC_12_images.zip')).extractall(d)
        for p in glob.glob(os.path.join(d, '**', '*.jpg'), recursive=True):
            if os.path.dirname(p) != d: os.replace(p, os.path.join(d, os.path.basename(p)))
    return d
def src(key):
    if key not in _img:
        if key == 'palm2': p = os.path.join(VIS, 'palm2.jpg')
        elif key == 'iss': p = os.path.join(VIS, 'iss067e003785_lrg.jpg')
        else: p = os.path.join(woc_dir(), f'dubai_ast_{WOC_FILES[key]}_cyl.jpg')
        _img[key] = Image.open(p).convert('RGB')
    return _img[key]

# ------------------------------------------------------------------ views
def lerp_rect(r0, r1, u):
    """16:9-preserving interpolation: width in log space, centre linear."""
    u = E.clamp(u); w = math.exp(math.log(r0[2]) * (1 - u) + math.log(r1[2]) * u); h = w * r0[3] / r0[2]
    cx = r0[0] + r0[2] / 2; cy = r0[1] + r0[3] / 2; nx = r1[0] + r1[2] / 2; ny = r1[1] + r1[3] / 2
    cx, cy = cx + (nx - cx) * u, cy + (ny - cy) * u
    return (cx - w / 2, cy - h / 2, w, h)
REC = None                             # when a list: every on-screen string is appended (audit_labels.py)
USED = []                              # (key, rect) log for the rect/no-data audit (qa_rects.py)
LOG = False
def view(key, rect):
    if LOG: USED.append((key, tuple(float(v) for v in rect)))
    im = src(key); x, y, w, h = rect
    if -2 < x < 0: x = 0.0                                   # float-rounding snap only (<2 px); anything larger still raises
    if -2 < y < 0: y = 0.0
    x = min(x, im.width - w) if 0 < x + w - im.width < 2 else x; y = min(y, im.height - h) if 0 < y + h - im.height < 2 else y
    return im.resize((PW, PH), Image.LANCZOS, box=(x, y, x + w, y + h))
def to_screen(rect, pt): return ((pt[0] - rect[0]) / rect[2] * W, (pt[1] - rect[1]) / rect[3] * H)
def dissolve(a, b, u): return Image.blend(a, b, E.clamp(u))
def dim(im, k):
    return Image.fromarray((np.asarray(im, np.float32) * k).clip(0, 255).astype(np.uint8))

# ------------------------------------------------------------------ canvas (RGBA overlay on a base frame)
class Canvas:
    def __init__(self, base): self.base = base.convert('RGBA') if base.size == (PW, PH) else base.resize((PW, PH), Image.LANCZOS).convert('RGBA'); self.o = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); self.d = mkdraw(self.o)
    def _comp(self, draw_fn):
        """draw on a transparent temporary layer and alpha-composite it (direct drawing on RGBA would overwrite pixels, e.g. erase earlier text under a fading line)"""
        tmp = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); draw_fn(mkdraw(tmp)); bb = tmp.getbbox()
        if bb: self.o.alpha_composite(tmp.crop(bb), dest=(bb[0], bb[1])); self.d = mkdraw(self.o)
    def text(self, xy, s, px, fill=TEXT, a=1.0, bold=True, anchor='la', spacing=0.0, shadow=True):
        if a <= 0.003: return
        if REC is not None: REC.append(s)
        ft = F(px, bold)
        def go(d, xy=xy, a=a, fill=fill):
            if spacing:
                tw = sum(d.textlength(c, font=ft) + px * spacing for c in s) - px * spacing
                x = xy[0] - (tw / 2 if anchor[0] == 'm' else tw if anchor[0] == 'r' else 0)
                for c in s: d.text((x, xy[1]), c, font=ft, fill=fill + (int(255 * a),), anchor='l' + anchor[1]); x += d.textlength(c, font=ft) + px * spacing
            else: d.text(xy, s, font=ft, fill=fill + (int(255 * a),), anchor=anchor)
        if shadow and fill != (11, 15, 20): self._comp(lambda d: go(d, (xy[0] + 1, xy[1] + 1), a * 0.65, (0, 0, 0)))
        self._comp(go)
    def kinetic(self, xy, s, px, t0, t, fill=AMBER, a=1.0, spacing=0.2, per=0.035):
        """letters rise in one after another from t0"""
        if REC is not None and a > 0.003 and t > t0: REC.append(s)
        ft = F(px)
        def go(d):
            tw = sum(d.textlength(c, font=ft) + px * spacing for c in s) - px * spacing; x = xy[0] - tw / 2 if self._center else xy[0]
            for i, c in enumerate(s):
                k = seg(t, t0 + i * per, t0 + i * per + 0.35)
                if k > 0.003: d.text((x, xy[1] + (1 - oc(k)) * px * 0.35), c, font=ft, fill=fill + (int(255 * a * k),))
                x += d.textlength(c, font=ft) + px * spacing
        if a > 0.003: self._comp(go)
    _center = False
    def pill(self, xy, s, px=15, a=1.0, accent=None, anchor='left'):
        if a <= 0.01: return
        if REC is not None: REC.append(s)
        ft = F(px, True); w = self.d.textlength(s, font=ft) + px * 1.4; x = xy[0] - (w if anchor == 'right' else 0)
        self.d.rounded_rectangle([x, xy[1], x + w, xy[1] + px * 1.9], 5, fill=(8, 14, 22, int(205 * a)))
        if accent: self.d.rectangle([x, xy[1] + 3, x + 3, xy[1] + px * 1.9 - 3], fill=accent + (int(255 * a),))
        self.d.text((x + px * 0.7, xy[1] + px * 0.28), s, font=ft, fill=TEXT + (int(255 * a),))
    def chip(self, s, a=1.0): self.pill((22, 20), s, 12, a * 0.85, accent=AMBER)
    def ring(self, c, r, a=1.0, wd=2, col=AMBER):
        if a > 0.01: self.d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=col + (int(255 * a),), width=wd)
    def ping(self, c, t, t0, r=18, col=AMBER, n=2):
        for k in range(n):
            ph = seg(t, t0 + 0.5 * k, t0 + 0.5 * k + 1.1)
            if 0 < ph < 1: self.ring(c, r + 36 * ph, (1 - ph) * 0.8, 2, col)
    def callout(self, pt, text, t, t0, dxy=(-110, -70), r=16, col=AMBER, ring=True, px=17, out=None):
        """ring on pt + leader + label"""
        if not (-30 <= pt[0] <= W + 30 and -30 <= pt[1] <= H + 30): return                              # a label for a landmark outside the frame is meaningless
        k = oc(seg(t, t0, t0 + 0.5)); 
        if out is not None: k *= 1 - sm(seg(t, out, out + 0.4))
        if k <= 0.01: return
        c = pt; e = (pt[0] + dxy[0], pt[1] + dxy[1]); tl_ = self.d.textlength(text, font=F(px))
        e = (min(e[0], W - 28 - tl_), e[1]) if dxy[0] >= 0 else (max(e[0], 28 + tl_), e[1])             # keep the label text inside the frame (24 px margin)
        e = (e[0], min(max(e[1], 96), H - 90))                                                           # ... and below the header/chip band, above the caption band
        if ring: self.ring(c, r * (0.6 + 0.4 * k), k, 2, col)
        q = (c[0] + (e[0] - c[0]) * k, c[1] + (e[1] - c[1]) * k); self.d.line([c, q], fill=col + (int(220 * k),), width=2)
        ft = F(px); w = self.d.textlength(text, font=ft)
        ax = 'l' if dxy[0] >= 0 else 'r'
        bx0 = e[0] + 4 - 7 if dxy[0] >= 0 else e[0] - 4 - w - 7; self.d.rounded_rectangle([bx0, e[1] - px * 0.5 - px * 0.72, bx0 + w + 14, e[1] - px * 0.5 + px * 0.72], 5, fill=(6, 10, 16, int(170 * k)))   # backing pill: contrast on sand/ice imagery
        self.d.text((e[0] + (4 if dxy[0] >= 0 else -4), e[1] - px * 0.5), text, font=ft, fill=col + (int(255 * k),), anchor=ax + 'm', stroke_width=2, stroke_fill=(6, 10, 16, int(200 * k)))
    def finish(self): return Image.alpha_composite(self.base, self.o).convert('RGB')

def text_card_bg(t=0.0, tint=(14, 22, 32)):
    y = np.linspace(0, 1, H)[:, None, None]; x = np.linspace(0, 1, W)[None, :, None]
    a = np.array((22, 31, 44), np.float32) * (1 - y * 0.35) + np.array(tint, np.float32) * y * 0.9              # lifted navy: a mostly empty card must not read as black (yt-qc blackdetect)
    a = np.broadcast_to(a, (H, W, 3)).copy(); a -= 10 * ((x - 0.5) ** 2) * 4
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); return im if SC == 1 else im.resize((PW, PH), Image.LANCZOS)
def wrap(d, s, ft, maxw):
    out, cur = [], ''
    for w in s.split():
        n = (cur + ' ' + w).strip()
        if d.textlength(n, font=ft) <= maxw: cur = n
        else: out.append(cur); cur = w
    return out + [cur]

# ------------------------------------------------------------------ captions (ESTIMATED timing: 145 words/min inside the scene window)
def chunks(vo, maxw=9):
    out = []
    for sent in [s.strip() for s in vo.replace('?', '?|').replace('.', '.|').replace('!', '!|').split('|') if s.strip()]:
        ws = sent.split(); n = max(1, math.ceil(len(ws) / maxw)); step = math.ceil(len(ws) / n)
        out += [' '.join(ws[i:i + step]) for i in range(0, len(ws), step)]
    return out
def caption_track(vo_lines, dur, hold_in=0.5, hold_out=0.6):
    if not vo_lines: return []
    ch = [c for l in vo_lines for c in chunks(l)]; wc = [len(c.split()) for c in ch]; tot = sum(wc)
    avail = max(dur - hold_in - hold_out, 1.0); t = hold_in; track = []
    for c, n in zip(ch, wc):
        d = avail * n / tot; track.append((t, t + d, c)); t += d
    return track
def draw_caption(cv, track, t):
    for a, b, s in track:
        if a <= t < b:
            ft = F(17, True); lines = wrap(cv.d, s, ft, W * 0.78)[:2]; h = 17 * 1.35 * len(lines) + 12
            wmax = max(cv.d.textlength(l, font=ft) for l in lines) + 28; x0 = (W - wmax) / 2; y0 = H - 22 - h
            cv.d.rounded_rectangle([x0, y0, x0 + wmax, y0 + h], 6, fill=(6, 10, 16, 190))
            for i, l in enumerate(lines): cv.d.text((W / 2, y0 + 6 + i * 17 * 1.35 + 11), l, font=ft, fill=TEXT + (255,), anchor='mm')
            return
def badge(cv):
    cv.d.text((W - 14, H - 10), 'PREVIEW · SILENT · TIMING ESTIMATED', font=F(11, True), fill=MUTED + (200,), anchor='rd')

# ------------------------------------------------------------------ deterministic landmarks (landmarks.json, built by landmarks.py)
LMJ = json.load(open(os.path.join(HERE, 'landmarks.json')))
def _med(vals): vals = sorted(vals); return vals[len(vals) // 2]
_rings = [LMJ['woc'][k]['palm_jumeirah_ring'] for k in ('2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011')]
SITE_C = (round(_med([r['center'][0] for r in _rings]), 1), round(_med([r['center'][1] for r in _rings]), 1)); SITE_R = round(_med([r['radius'] for r in _rings]), 1)
def woc_ring(key):
    d = LMJ['woc'].get(key, {}).get('palm_jumeirah_ring')
    return (tuple(d['center']), d['radius']) if d else (SITE_C, SITE_R)
def lm(group, name): d = LMJ[group][name]; return tuple(d['center']), d.get('radius')
def rect_c(c, w, aspect=16 / 9, dx=0, dy=0, size=3000, size_y=None):
    """rect of width w centred (with an offset) on c, clamped inside the image so no pixel outside the source is ever requested"""
    size_y = size_y or size; h = w / aspect; x = min(max(c[0] + dx - w / 2, 0), size - w); y = min(max(c[1] + dy - h / 2, 0), size_y - h); return (x, y, w, h)
def coast_x(key, y, thr=38, ref=(0, 1250, 280, 150)):
    a = np.asarray(src(key), np.float32); x0, y0, w, h = ref; r = np.median(a[y0:y0 + h, x0:x0 + w].reshape(-1, 3), 0)
    row = np.sqrt(((a[int(y)] - r) ** 2).sum(1)) >= thr; xs = np.nonzero(row[600:])[0]; return int(xs[0] + 600) if len(xs) else None

# ------------------------------------------------------------------ supersampled vector drawing for diagrams
class SS:
    def __init__(self, s=3): self.s = s; self.k = s * SC; self.im = Image.new('RGBA', (int(W * self.k), int(H * self.k)), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
    def _p(self, pts): return [(x * self.k, y * self.k) for x, y in pts]
    def line(self, pts, fill, width=2): self.d.line(self._p(pts), fill=fill, width=max(1, round(width * self.k)), joint='curve')
    def poly(self, pts, fill=None, outline=None, width=1): self.d.polygon(self._p(pts), fill=fill, outline=outline)
    def ellipse(self, c, rx, ry=None, fill=None, outline=None, width=1):
        ry = ry if ry is not None else rx; self.d.ellipse([(c[0] - rx) * self.k, (c[1] - ry) * self.k, (c[0] + rx) * self.k, (c[1] + ry) * self.k], fill=fill, outline=outline, width=max(1, round(width * self.k)))
    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1, r=0):
        b = [x0 * self.k, y0 * self.k, x1 * self.k, y1 * self.k]
        (self.d.rounded_rectangle(b, r * self.k, fill=fill, outline=outline, width=max(1, round(width * self.k))) if r else self.d.rectangle(b, fill=fill, outline=outline, width=max(1, round(width * self.k))))
    def arc(self, c, r, a0, a1, fill, width=2): self.d.arc([(c[0] - r) * self.k, (c[1] - r) * self.k, (c[0] + r) * self.k, (c[1] + r) * self.k], a0, a1, fill=fill, width=max(1, round(width * self.k)))
    def dashed(self, pts, fill, width=1.5, dash=8, gap=6, offset=0.0):
        pts = np.asarray(pts, float); seglen = np.hypot(*np.diff(pts, axis=0).T); cum = np.r_[0, np.cumsum(seglen)]; tot = cum[-1]; pos = -offset % (dash + gap) - (dash + gap)
        while pos < tot:
            a, b = max(pos, 0), min(pos + dash, tot)
            if b > a: self.line([tuple(np.array([np.interp(a, cum, pts[:, 0]), np.interp(a, cum, pts[:, 1])])), tuple(np.array([np.interp(b, cum, pts[:, 0]), np.interp(b, cum, pts[:, 1])]))], fill, width)
            pos += dash + gap
    def finish(self): return self.im.resize((PW, PH), Image.LANCZOS)
def layer(cv, ss):
    cv.o = Image.alpha_composite(cv.o, ss.finish()); cv.d = mkdraw(cv.o)
