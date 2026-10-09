"""EP001 visual pass 1 renderer. Review animations (default 1280x720) and stills; same code at --scale 2 = 3840x2160 (final, not run in this pass).
Upscale policy: Lanczos only (PIL), no sharpening, no AI; the zoom ends at a 960x540 source window (<= 4.0 screen px per source px at 4K)."""
import sys, os, json, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vis_common as c
CACHE = c.VIS + 'cache/'
FD = '/usr/share/fonts/opentype/inter/'
def font(sz, w='Regular'): return ImageFont.truetype(FD + f'Inter-{w}.otf', int(round(sz)))
EO_LABEL = {'1984': 'August 26, 1984', '2000': 'January 2000', '2010': 'January 2010', '2016': 'January 2016', '2024': 'January 2024'}
EO_SENSOR = {'1984': 'Landsat 5 TM', '2000': 'Landsat 5 TM', '2010': 'Landsat 5 TM', '2016': 'Landsat 8 OLI', '2024': 'Landsat 9 OLI-2'}
TO_LABEL = {'1999': 'January 1999', '2002': 'January 2002', '2011': 'January 2011', '2021': 'November 2021'}
TO_SENSOR = {'1999': 'Landsat 5 TM', '2002': 'Landsat 5 TM', '2011': 'Landsat 5 TM', '2021': 'Landsat 8 OLI'}
EO_YEARS = ['1984', '2000', '2010', '2016', '2024']; TO_YEARS = ['1999', '2002', '2011', '2021']
BG = (14, 17, 20); FG = (240, 240, 236); MUTED = (150, 156, 160); ACC = (242, 178, 64)
ZOOM_SRC = (960, 540)    # final zoom window in source pixels (30 m): 28.8 x 16.2 km
def smooth(t): t = min(max(t, 0), 1); return t * t * (3 - 2 * t)
def view(img, box, size):
    """Lanczos resample of the float box (x0,y0,x1,y1; source px) into size (w,h). Pillow resizes only the box; nothing else is added."""
    return Image.fromarray(img).resize(size, Image.LANCZOS, box=box)
def nice_bar(km_per_px, lo=110, hi=300):
    for km in (1, 2, 5, 10, 20, 50):
        w = km / km_per_px
        if lo <= w <= hi: return km, w
    km = 10; return km, km / km_per_px
def draw_scalebar(d, x, y, km, wpx, sc):
    d.rectangle((x, y, x + wpx, y + 6 * sc), fill=FG); d.rectangle((x, y - 6 * sc, x + 2 * sc, y + 6 * sc), fill=FG); d.rectangle((x + wpx - 2 * sc, y - 6 * sc, x + wpx, y + 6 * sc), fill=FG)
    d.text((x, y - 36 * sc), f'{km} km', font=font(24 * sc, 'Medium'), fill=FG)
def shade(im, rect, a):
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(ov).rectangle(rect, fill=(0, 0, 0, int(255 * a))); return Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')
def grad_shade(im, h, a, top):
    w = im.size[0]; ramp = np.linspace(a, 0, int(h)) if top else np.linspace(0, a, int(h)); arr = np.asarray(im).astype(np.float32)
    sl = slice(0, int(h)) if top else slice(im.size[1] - int(h), im.size[1]); arr[sl] *= (1 - ramp)[:, None, None]; return Image.fromarray(arr.astype(np.uint8))
class EO:
    def __init__(s): s.f = {k: np.load(f'{CACHE}EO_{k}_base.npy') for k in EO_YEARS}; s.W, s.H = s.f['2024'].shape[1], s.f['2024'].shape[0]
    def target(s):   # zoom centre: densest field area in 2024 (dark = irrigated circles)
        g = (s.f['2024'].astype(np.float32).mean(2) < 110).astype(np.float32); I = g.cumsum(0).cumsum(1); w, h = ZOOM_SRC; best = (0, 0, 0)
        for y in range(0, s.H - h, 20):
            for x in range(0, s.W - w, 20):
                v = I[y + h - 1, x + w - 1] - I[y, x + w - 1] - I[y + h - 1, x] + I[y, x]
                if v > best[0]: best = (v, x, y)
        return best[1] + w / 2, best[2] + h / 2
    def frame(s, sc, years, alpha, zoom, tgt, tick_idx, text_alpha=1.0, note=False):
        CW, CH = int(1920 * sc), int(1080 * sc); z = smooth(zoom)
        dw = (1276 + 644 * z) * sc; dx0 = CW - dw
        # box: aspect = dest aspect; log-interpolated width
        w0 = s.W; w1 = ZOOM_SRC[0]; bw = float(np.exp(np.log(w0) * (1 - z) + np.log(w1) * z)); bh = bw * CH / dw
        cx = (s.W / 2) * (1 - z) + tgt[0] * z; cy = (s.H / 2) * (1 - z) + tgt[1] * z
        cx = min(max(cx, bw / 2), s.W - bw / 2); cy = min(max(cy, bh / 2), s.H - bh / 2)
        if bh > s.H: bh = s.H; bw = bh * dw / CH; cx = s.W / 2
        box = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2); size = (int(round(dw)), CH)
        A = view(s.f[years[0]], box, size)
        if years[1] is not None and alpha > 0: A = Image.blend(A, view(s.f[years[1]], box, size), alpha)
        im = Image.new('RGB', (CW, CH), BG); im.paste(A, (int(round(dx0)), 0))
        cur = years[1] if (years[1] is not None and alpha >= 0.5) else years[0]
        d = ImageDraw.Draw(im)
        # left info panel (slides off with the zoom)
        if dx0 > 2 * sc:
            pn = Image.new('RGB', (int(644 * sc), CH), BG); d = ImageDraw.Draw(pn)
            def fade(col): return tuple(int(BG[i] + (col[i] - BG[i]) * text_alpha) for i in range(3))
            d.text((40 * sc, 54 * sc), 'EAST OWEINAT, EGYPT', font=font(26 * sc, 'Medium'), fill=fade(ACC))
            d.text((40 * sc, 104 * sc), 'Desert to irrigated', font=font(44 * sc, 'Medium'), fill=fade(FG)); d.text((40 * sc, 154 * sc), 'circles, 1984 to 2024', font=font(44 * sc, 'Medium'), fill=fade(FG))
            d.text((40 * sc, 380 * sc), EO_LABEL[cur], font=font(46 * sc, 'Medium'), fill=fade(FG)); d.text((40 * sc, 446 * sc), EO_SENSOR[cur], font=font(26 * sc), fill=fade(MUTED))
            # timeline
            ty0, ty1 = 560 * sc, 940 * sc; xx = 70 * sc; d.line((xx, ty0, xx, ty1), fill=fade((70, 76, 80)), width=int(3 * sc))
            for i, k in enumerate(EO_YEARS):
                yy = ty0 + (ty1 - ty0) * i / 4; on = (k == cur)
                d.ellipse((xx - 9 * sc, yy - 9 * sc, xx + 9 * sc, yy + 9 * sc), fill=fade(ACC if on else (70, 76, 80)))
                d.text((xx + 28 * sc, yy - 16 * sc), EO_LABEL[k] if k == '1984' else EO_LABEL[k].replace('January ', 'Jan '), font=font(26 * sc, 'Medium' if on else 'Regular'), fill=fade(FG if on else MUTED))
            d.text((40 * sc, 1000 * sc), 'Single dates, not a continuous record.', font=font(20 * sc), fill=fade(MUTED))
            d.text((40 * sc, 1028 * sc), 'Landsat / USGS. Same tone curve for every frame.', font=font(20 * sc), fill=fade(MUTED))
            im.paste(pn.crop((0, 0, int(dx0), CH)), (0, 0)); d = ImageDraw.Draw(im)
        # zoom-stage overlays
        if z > 0.85:
            a = min(1, (z - 0.85) / 0.15); im = grad_shade(im, 220 * sc, 0.62 * a, False); d = ImageDraw.Draw(im)
            km, wpx = nice_bar(0.03 / (dw / bw)); draw_scalebar(d, 60 * sc, CH - 70 * sc, km, wpx, sc)
            d.text((CW - 780 * sc, CH - 150 * sc), EO_LABEL[cur] + ' · ' + EO_SENSOR[cur], font=font(34 * sc, 'Medium'), fill=FG)
            if note: d.text((CW - 780 * sc, CH - 100 * sc), 'Center-pivot circles, about half a mile across.', font=font(26 * sc), fill=FG)
        d.text((dx0 + 20 * sc, CH - 36 * sc), '', font=font(10 * sc))
        return im, {'box_src': [round(v, 1) for v in box], 'dest': size, 'screen_px_per_src_px': round(dw / bw, 3), 'label': EO_LABEL[cur]}
class TO:
    def __init__(s): s.f = {k: np.load(f'{CACHE}TOSH_{k}_base.npy') for k in TO_YEARS}
    def frame(s, sc, years, alpha):
        CW, CH = int(1920 * sc), int(1080 * sc)
        A = view(s.f[years[0]], (0, 0, 3840, 2160), (CW, CH))
        if years[1] is not None and alpha > 0: A = Image.blend(A, view(s.f[years[1]], (0, 0, 3840, 2160), (CW, CH)), alpha)
        cur = years[1] if (years[1] is not None and alpha >= 0.5) else years[0]
        im = grad_shade(A, 270 * sc, 0.62, True); im = grad_shade(im, 170 * sc, 0.62, False); d = ImageDraw.Draw(im)
        d.text((50 * sc, 36 * sc), 'TOSHKA LAKES, EGYPT', font=font(26 * sc, 'Medium'), fill=ACC)
        d.text((50 * sc, 78 * sc), TO_LABEL[cur], font=font(58 * sc, 'Medium'), fill=FG); d.text((50 * sc, 156 * sc), TO_SENSOR[cur], font=font(26 * sc), fill=(210, 212, 208))
        # timeline top right
        x0 = CW - 760 * sc; d.line((x0, 96 * sc, x0 + 680 * sc, 96 * sc), fill=(120, 124, 126), width=int(3 * sc))
        for i, k in enumerate(TO_YEARS):
            xx = x0 + 680 * sc * i / 3; on = (k == cur)
            d.ellipse((xx - 9 * sc, 96 * sc - 9 * sc, xx + 9 * sc, 96 * sc + 9 * sc), fill=ACC if on else (120, 124, 126))
            t = TO_LABEL[k].replace('January ', 'Jan ').replace('November ', 'Nov '); tw = d.textlength(t, font=font(22 * sc)); d.text((xx - tw / 2, 120 * sc), t, font=font(22 * sc, 'Medium' if on else 'Regular'), fill=FG if on else (200, 202, 198))
        km, wpx = nice_bar(0.03 / (CW / 3840), 140, 320); km = 20; wpx = 20 / (0.03 / (CW / 3840))
        draw_scalebar(d, 60 * sc, CH - 62 * sc, km, wpx, sc)
        d.text((CW - 880 * sc, CH - 92 * sc), 'Single dates, not a continuous record.', font=font(24 * sc), fill=FG)
        d.text((CW - 880 * sc, CH - 56 * sc), 'Landsat / USGS · same tone curve for every frame', font=font(20 * sc), fill=(210, 212, 208))
        return im, {'label': TO_LABEL[cur], 'screen_px_per_src_px': round(CW / 3840, 3)}
def encode(frames_iter, out, w, h, fps=24, crf=26):
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    n = 0
    for im in frames_iter: p.stdin.write(np.asarray(im).tobytes()); n += 1
    p.stdin.close(); p.wait(); return n
def eo_timeline(fps):
    seq = []   # (years, alpha, zoom, text_alpha, note)
    hold, dis = int(2.0 * fps), int(1.0 * fps)
    for i, k in enumerate(EO_YEARS):
        for _ in range(hold): seq.append(((k, None), 0, 0, 1, False))
        if i < 4:
            for j in range(dis): seq.append(((k, EO_YEARS[i + 1]), smooth((j + 1) / dis), 0, 1, False))
    zf = int(6.0 * fps)
    for j in range(zf): t = (j + 1) / zf; seq.append((('2024', None), 0, t, max(0, 1 - t * 3), t > 0.95))
    for _ in range(int(2.5 * fps)): seq.append((('2024', None), 0, 1, 0, True))
    return seq
def to_timeline(fps):
    seq = []; hold, dis = int(3.0 * fps), int(1.2 * fps)
    for i, k in enumerate(TO_YEARS):
        for _ in range(hold): seq.append(((k, None), 0))
        if i < 3:
            for j in range(dis): seq.append(((k, TO_YEARS[i + 1]), smooth((j + 1) / dis)))
    for _ in range(int(1.5 * fps)): seq.append((('2021', None), 0))
    return seq
if __name__ == '__main__':
    what = sys.argv[1]; sc = float(sys.argv[2]) if len(sys.argv) > 2 else 2 / 3; out = sys.argv[3] if len(sys.argv) > 3 else None; fps = 24
    CW, CH = int(1920 * sc), int(1080 * sc)
    if what == 'eo':
        e = EO(); tgt = e.target(); print('zoom target', tgt, flush=True); json.dump({'zoom_target_src_px': tgt}, open(c.VIS + 'eo_target.json', 'w'))
        enc = lambda: (e.frame(sc, y, a, z, tgt, 0, ta, nt)[0] for (y, a, z, ta, nt) in eo_timeline(fps))
        print(encode(enc(), out, CW, CH, fps), 'frames')
    elif what == 'to':
        t = TO(); print(encode((t.frame(sc, y, a)[0] for (y, a) in to_timeline(fps)), out, CW, CH, fps), 'frames')
