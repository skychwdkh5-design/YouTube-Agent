"""EP001 visual pass 2 renderer (presentation polish). Imagery path unchanged from pass 1: same cached tone-B frames, same crops, same Lanczos resampling.
Review animations (default 1280x720) and stills; the same code at --scale 2 gives 3840x2160 (final, not run).
Upscale policy: Lanczos only (PIL), no sharpening, no AI; the zoom ends at a 960x540 source window (<= 4.0 screen px per source px at 4K)."""
import sys, os, json, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vis_common as c
CACHE = c.VIS + 'cache/'
FD = '/usr/share/fonts/opentype/inter/'
def font(sz, w='Regular'): return ImageFont.truetype(FD + f'Inter-{w}.otf', max(1, int(round(sz))))
EO_LABEL = {'1984': 'August 26, 1984', '2000': 'January 2000', '2010': 'January 2010', '2016': 'January 2016', '2024': 'January 2024'}
EO_SHORT = {'1984': 'Aug 26, 1984', '2000': 'Jan 2000', '2010': 'Jan 2010', '2016': 'Jan 2016', '2024': 'Jan 2024'}
EO_SENSOR = {'1984': 'Landsat 5 TM', '2000': 'Landsat 5 TM', '2010': 'Landsat 5 TM', '2016': 'Landsat 8 OLI', '2024': 'Landsat 9 OLI-2'}
TO_LABEL = {'1999': 'January 1999', '2002': 'January 2002', '2011': 'January 2011', '2021': 'November 2021'}
TO_SHORT = {'1999': 'Jan 1999', '2002': 'Jan 2002', '2011': 'Jan 2011', '2021': 'Nov 2021'}
TO_SENSOR = {'1999': 'Landsat 5 TM', '2002': 'Landsat 5 TM', '2011': 'Landsat 5 TM', '2021': 'Landsat 8 OLI'}
EO_YEARS = ['1984', '2000', '2010', '2016', '2024']; TO_YEARS = ['1999', '2002', '2011', '2021']
BG = (14, 17, 20); FG = (244, 244, 240); ACC = (246, 184, 70); LINE = (170, 176, 180)
ZOOM_SRC = (960, 540)
# ---- shared type scale (design px at 1080p; identical for both sequences). Minimum secondary text 28 px = 18.7 px at 720p.
T = {'kicker': (30, 'Medium'), 'title': (44, 'Medium'), 'date': (64, 'Medium'), 'date2': (44, 'Medium'), 'sub': (32, 'Regular'), 'label': (30, 'Medium'), 'note': (28, 'Regular'), 'chip': (28, 'Medium'), 'scale': (30, 'Medium'), 'cap': (36, 'Medium')}
MX, MT, MB = 96, 72, 72          # safe margins (design px): 5% sides, 6.7% top and bottom (bottom keeps clear of mobile player UI)
DISSOLVE_S = 0.8
FPS = 30                           # fps policy: 30 fps, the yt-render default for the long profile; all sequence times are defined in seconds
CHIP_TEXT = 'Transition between satellite images'
CLARIFY_2011 = 'Narration says "by 2012"; this image is from January 2011.'
def smooth(t): t = min(max(t, 0), 1); return t * t * (3 - 2 * t)
def view(img, box, size): return Image.fromarray(img).resize(size, Image.LANCZOS, box=box)
def grad_shade(im, h, a, top):
    ramp = np.linspace(a, 0, int(h)) if top else np.linspace(0, a, int(h)); arr = np.asarray(im).astype(np.float32)
    sl = slice(0, int(h)) if top else slice(im.size[1] - int(h), im.size[1]); arr[sl] *= (1 - ramp)[:, None, None]; return Image.fromarray(arr.astype(np.uint8))
def nice_bar(km_per_px, lo=110, hi=300):
    for km in (1, 2, 5, 10, 20, 50):
        w = km / km_per_px
        if lo <= w <= hi: return km, w
    return 10, 10 / km_per_px
class Layer:
    """RGBA text/graphics overlay with design-px coordinates; tracks the bounding box of everything drawn."""
    def __init__(s, sc, CW, CH): s.sc = sc; s.im = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.im); s.items = []
    def text(s, x, y, t, role, col=FG, a=1.0, anchor='l', tag=''):
        sz, w = T[role]; f = font(sz * s.sc, w); tw = s.d.textlength(t, font=f) / s.sc
        if anchor == 'r': x = x - tw
        sw = max(1, int(round(2 * s.sc))); s.d.text((x * s.sc, y * s.sc), t, font=f, fill=col + (int(255 * a),), stroke_width=sw, stroke_fill=(0, 0, 0, int(190 * a)))
        s.items.append({'tag': tag or t, 'role': role, 'size': sz, 'bbox': [x, y, x + tw, y + sz * 1.2], 'alpha': a, 'color': col}); return tw
    def pill(s, x0, y0, x1, y1, a=0.58):
        s.d.rounded_rectangle((x0 * s.sc, y0 * s.sc, x1 * s.sc, y1 * s.sc), radius=14 * s.sc, fill=(8, 10, 12, int(255 * a))); s.items.append({'tag': 'pill', 'role': 'pill', 'bbox': [x0, y0, x1, y1], 'alpha': a})
    def bar(s, x, y, km, wpx):
        sc = s.sc; d = s.d; o = 3 * sc
        d.rectangle(((x - o) * sc / sc, (y - 6 * sc - o), x * 1 + wpx * sc / sc * 0 + 0, 0)) if False else None
        X, Y, Wd = x * sc, y * sc, wpx
        d.rectangle((X - o, Y - 8 * sc - o, X + Wd + o, Y + 8 * sc + o), fill=(0, 0, 0, 170)); d.rectangle((X, Y - 8 * sc, X + Wd, Y + 8 * sc), fill=FG + (255,))
        d.rectangle((X + 3 * sc, Y - 5 * sc, X + Wd - 3 * sc, Y + 5 * sc), fill=(8, 10, 12, 255)) if False else None
        s.items.append({'tag': 'scalebar', 'role': 'bar', 'alpha': 1.0, 'bbox': [x, y - 8, x + Wd / sc, y + 8]})
        s.text(x, y - 50, f'{km} km', 'scale', tag='scalebar label')
def date_block(L, x, y, years, alpha, base_a=1.0, big=True):
    """Date + sensor block. Single date outside a dissolve; during a dissolve both dates are listed (outgoing, then incoming) so each stays identifiable."""
    y0, y1 = years
    if y1 is None or alpha <= 0.0 or alpha >= 1.0:
        k = y1 if (y1 is not None and alpha >= 1.0) else y0; return [('single', k, 1.0)] if True else None
    return [('pair', (y0, y1), 1.0)]
class Style:  # per-sequence label tables
    def __init__(s, lab, sensor): s.lab = lab; s.sensor = sensor
EOS, TOS = Style(EO_LABEL, EO_SENSOR), Style(TO_LABEL, TO_SENSOR)
def draw_info(L, x, y, st, years, a, kicker, chip_y_gap=0, text_alpha=1.0, pill=False):
    """Common info block: kicker, date(s), sensor(s), dissolve chip. Returns y of the block end."""
    y0, y1 = years; yy = y + 46
    single = (y1 is None or a <= 0.0 or a >= 1.0)
    if pill: L.pill(x - 22, y - 16, x + 600, (yy + 82 + 44) if single else (yy + 204 - 6), 0.70)
    L.text(x, y, kicker, 'kicker', ACC, text_alpha)
    if y1 is None or a <= 0.0 or a >= 1.0:
        k = y1 if (y1 is not None and a >= 1.0) else y0
        L.text(x, yy, st.lab[k], 'date', FG, text_alpha, tag=f'date:{k}'); L.text(x, yy + 82, st.sensor[k], 'sub', (214, 216, 212), text_alpha, tag=f'sensor:{k}')
        return yy + 82 + 40
    L.text(x, yy, st.lab[y0], 'date2', FG, text_alpha, tag=f'date:{y0}'); L.text(x, yy + 52, '→ ' + st.lab[y1], 'date2', FG, text_alpha, tag=f'date:{y1}')
    s0, s1 = st.sensor[y0], st.sensor[y1]; L.text(x, yy + 108, s0 if s0 == s1 else f'{s0} → {s1}', 'sub', (214, 216, 212), text_alpha, tag='sensors')
    tw = L.d.textlength(CHIP_TEXT, font=font(T['chip'][0] * L.sc, T['chip'][1])) / L.sc
    L.pill(x - 14, yy + 156, x + tw + 14, yy + 156 + 44, 0.62); L.text(x, yy + 160, CHIP_TEXT, 'chip', ACC, text_alpha, tag='chip')
    return yy + 204
def timeline(L, pts, cur, a, years, horizontal, x0, y0, x1, y1, lab, ta=1.0):
    """pts: ordered years; cur highlighted; during a dissolve both endpoints are highlighted and joined."""
    act = {years[0]} if (years[1] is None or a <= 0 or a >= 1) else {years[0], years[1]}
    if years[1] is not None and a >= 1: act = {years[1]}
    n = len(pts); pos = {}
    for i, k in enumerate(pts): pos[k] = (x0 + (x1 - x0) * i / (n - 1), y0 + (y1 - y0) * i / (n - 1))
    sc = L.sc; d = L.d
    d.line((pos[pts[0]][0] * sc, pos[pts[0]][1] * sc, pos[pts[-1]][0] * sc, pos[pts[-1]][1] * sc), fill=LINE + (int(255 * ta),), width=int(3 * sc))
    if len(act) == 2:
        p = [pos[k] for k in sorted(act, key=pts.index)]; d.line((p[0][0] * sc, p[0][1] * sc, p[1][0] * sc, p[1][1] * sc), fill=ACC + (int(255 * ta),), width=int(7 * sc))
    for k in pts:
        x, y = pos[k]; on = k in act; r = 11 if on else 8
        d.ellipse(((x - r) * sc, (y - r) * sc, (x + r) * sc, (y + r) * sc), fill=(ACC if on else (226, 228, 224)) + (int(255 * ta),), outline=(0, 0, 0, int(200 * ta)), width=int(2 * sc))
        if horizontal:
            tw = d.textlength(lab[k], font=font(T['label'][0] * sc, T['label'][1])) / sc; L.text(x - tw / 2, y + 26, lab[k], 'label', FG if on else (226, 228, 224), ta, tag=f'tl:{k}')
        else:
            L.text(x + 34, y - 18, lab[k], 'label', FG if on else (226, 228, 224), ta, tag=f'tl:{k}')
class EO:
    def __init__(s): s.f = {k: np.load(f'{CACHE}EO_{k}_base.npy') for k in EO_YEARS}; s.W, s.H = s.f['2024'].shape[1], s.f['2024'].shape[0]
    def target(s): return json.load(open(c.VIS + 'eo_target.json'))['zoom_target_src_px']
    def frame(s, sc, years, alpha, zoom, tgt, text_alpha=1.0, note=False, parts=False):
        CW, CH = int(1920 * sc), int(1080 * sc); z = smooth(zoom)
        dw = (1276 + 644 * z) * sc; dx0 = CW - dw
        bw = float(np.exp(np.log(s.W) * (1 - z) + np.log(ZOOM_SRC[0]) * z)); bh = bw * CH / dw
        cx = (s.W / 2) * (1 - z) + tgt[0] * z; cy = (s.H / 2) * (1 - z) + tgt[1] * z
        cx = min(max(cx, bw / 2), s.W - bw / 2); cy = min(max(cy, bh / 2), s.H - bh / 2)
        if bh > s.H: bh = s.H; bw = bh * dw / CH; cx = s.W / 2
        box = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2); size = (int(round(dw)), CH)
        A = view(s.f[years[0]], box, size)
        if years[1] is not None and alpha > 0: A = Image.blend(A, view(s.f[years[1]], box, size), alpha)
        base = Image.new('RGB', (CW, CH), BG); base.paste(A, (int(round(dx0)), 0))
        cur = years[1] if (years[1] is not None and alpha >= 0.5) else years[0]
        L = Layer(sc, CW, CH)
        if dx0 > 2 * sc:
            ta = text_alpha
            end = draw_info(L, MX, MT, EOS, years, alpha, 'EAST OWEINAT, EGYPT', text_alpha=ta)
            # (title lines sit above the date block in pass 1; pass 2 keeps one shared info block for both sequences)
            timeline(L, EO_YEARS, cur, alpha, years, False, 110, 590, 110, 840, EO_SHORT, ta)
            for i, line in enumerate(('Single dates, not a continuous record.', 'Landsat / USGS · same tone', 'curve for every frame.')): L.text(MX, 892 + i * 34, line, 'note', (214, 216, 212), ta, tag='footnote')
            keep = Image.new('L', (CW, CH), 0); ImageDraw.Draw(keep).rectangle((0, 0, int(dx0), CH), fill=255)
            a_ch = L.im.getchannel('A'); L.im.putalpha(Image.fromarray(np.minimum(np.asarray(a_ch), np.asarray(keep))))
        if z > 0.85:
            a = min(1, (z - 0.85) / 0.15); base = grad_shade(base, 230 * sc, 0.55 * a, False)
            km, wpx = nice_bar(0.03 / (dw / bw)); L.pill(MX - 14, 1080 - MB - 84, MX + wpx + 18, 1080 - MB + 2, 0.70 * a); L.bar(MX, 1080 - MB - 16, km, wpx)
            L.pill(CW / sc - MX - 740, 1080 - MB - 112, CW / sc - MX + 14, 1080 - MB + 2, 0.70 * a)
            L.text(CW / sc - MX, 1080 - MB - 100, EO_LABEL[cur] + ' · ' + EO_SENSOR[cur], 'cap', FG, a, anchor='r', tag=f'date:{cur}')
            if note: L.text(CW / sc - MX, 1080 - MB - 52, 'Center-pivot circles, about half a mile across.', 'sub', FG, a, anchor='r', tag='zoom note')
        im = Image.alpha_composite(base.convert('RGBA'), L.im).convert('RGB')
        m = {'box_src': [round(v, 1) for v in box], 'dest': size, 'screen_px_per_src_px': round(dw / bw, 3), 'label': EO_LABEL[cur]}
        return (im, m, base, L) if parts else (im, m)
class TO:
    def __init__(s): s.f = {k: np.load(f'{CACHE}TOSH_{k}_base.npy') for k in TO_YEARS}
    def frame(s, sc, years, alpha, parts=False, clarify=False):
        CW, CH = int(1920 * sc), int(1080 * sc)
        A = view(s.f[years[0]], (0, 0, 3840, 2160), (CW, CH))
        if years[1] is not None and alpha > 0: A = Image.blend(A, view(s.f[years[1]], (0, 0, 3840, 2160), (CW, CH)), alpha)
        cur = years[1] if (years[1] is not None and alpha >= 0.5) else years[0]
        base = grad_shade(A, 340 * sc, 0.48, True); base = grad_shade(base, 210 * sc, 0.45, False)
        L = Layer(sc, CW, CH)
        end_y = draw_info(L, MX, MT, TOS, years, alpha, 'TOSHKA LAKES, EGYPT', pill=True)
        if clarify and years[1] is None and years[0] == '2011':      # narration says "By 2012"; the image date stays January 2011
            tw = L.d.textlength(CLARIFY_2011, font=font(T['note'][0] * sc, T['note'][1])) / sc
            L.pill(MX - 22, end_y + 10, MX + tw + 14, end_y + 10 + 46, 0.70); L.text(MX, end_y + 16, CLARIFY_2011, 'note', FG, tag='clarify 2011')
        tl0, tl1 = CW / sc - MX - 110 - 700, CW / sc - MX - 110; L.pill(tl0 - 72, MT - 16, tl1 + 72, MT + 124, 0.70)
        timeline(L, TO_YEARS, cur, alpha, years, True, tl0, MT + 38, tl1, MT + 38, TO_SHORT)
        km = 20; wpx = 20 / (0.03 / (CW / 3840)); L.pill(MX - 14, 1080 - MB - 84, MX + wpx + 18, 1080 - MB + 2, 0.70); L.bar(MX, 1080 - MB - 16, km, wpx)
        L.pill(CW / sc - MX - 724, 1080 - MB - 88, CW / sc - MX + 14, 1080 - MB + 2, 0.70)
        L.text(CW / sc - MX, 1080 - MB - 72, 'Single dates, not a continuous record.', 'note', FG, anchor='r', tag='footnote'); L.text(CW / sc - MX, 1080 - MB - 36, 'Landsat / USGS · same tone curve for every frame', 'note', (214, 216, 212), anchor='r', tag='footnote')
        im = Image.alpha_composite(base.convert('RGBA'), L.im).convert('RGB')
        m = {'label': TO_LABEL[cur], 'screen_px_per_src_px': round(CW / 3840, 3)}
        return (im, m, base, L) if parts else (im, m)
def encode(frames_iter, out, w, h, fps=30, crf=24):
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    n = 0
    for im in frames_iter: p.stdin.write(np.asarray(im).tobytes()); n += 1
    p.stdin.close(); p.wait(); return n
def eo_timeline(fps):
    seq = []; hold, dis = int(2.0 * fps), int(DISSOLVE_S * fps)
    for i, k in enumerate(EO_YEARS):
        for _ in range(hold): seq.append(((k, None), 0, 0, 1, False))
        if i < 4:
            for j in range(dis): seq.append(((k, EO_YEARS[i + 1]), (j + 1) / (dis + 1), 0, 1, False))   # strictly inside (0,1): the outgoing and incoming dates are both shown
    zf = int(6.0 * fps)
    for j in range(zf): t = (j + 1) / zf; seq.append((('2024', None), 0, t, max(0, 1 - t * 5), t > 0.95))
    for _ in range(int(2.5 * fps)): seq.append((('2024', None), 0, 1, 0, True))
    return seq
def to_timeline(fps):
    seq = []; hold, dis = int(3.0 * fps), int(DISSOLVE_S * fps)
    for i, k in enumerate(TO_YEARS):
        for _ in range(hold): seq.append(((k, None), 0))
        if i < 3:
            for j in range(dis): seq.append(((k, TO_YEARS[i + 1]), (j + 1) / (dis + 1)))
    for _ in range(int(1.5 * fps)): seq.append((('2021', None), 0))
    return seq
def _alpha(tt, a, b, fps):
    return min(max((tt - a) / (b - a), 0.5 / (fps * (b - a))), 1 - 0.5 / (fps * (b - a)))      # strictly inside (0, 1): every dissolve frame shows both dates
def eo_states_from_schedule(sched, fps):
    """frames of the East Oweinat sequence for a cues.fit_eo schedule (absolute seconds); the zoom end is held to ."""
    steps = sched['schedule']; t0, end = steps[0]['start'], sched['clip_end']; n = int(round((end - t0) * fps)); out = []; prev = '1984'
    for i in range(n):
        tt = t0 + i / fps
        st = next((x for x in steps if x['start'] <= tt + 1e-9 < x['end']), None)
        if st is None:
            out.append((('2024', None), 0, 1, 0, True)); continue
        name = st['step']
        if name == '1984 hold': out.append((('1984', None), 0, 0, 1, False)); prev = '1984'
        elif name.startswith('dissolve to'):
            y = name.split()[-1]; out.append(((prev, y), _alpha(tt, st['start'], st['end'], fps), 0, 1, False))
            if tt + 1 / fps >= st['end'] - 1e-9: prev = y
        elif name.endswith(' hold'): y = name.split()[0]; out.append(((y, None), 0, 0, 1, False)); prev = y
        elif name == 'zoom into circles':
            z = (tt - st['start']) / (st['end'] - st['start']); out.append((('2024', None), 0, z, max(0, 1 - z * 5), z > 0.95))
    return out
def to_states_from_schedule(sched, fps):
    steps = sched['schedule']; t0, end = steps[0]['start'], sched['clip_end']; n = int(round((end - t0) * fps)); out = []; cur = '1999'
    for i in range(n):
        tt = t0 + i / fps
        st = next((x for x in steps if x['start'] <= tt + 1e-9 < x['end']), steps[-1])
        if st['step'].startswith('dissolve to'):
            y = st['step'].split()[-1]; out.append(((cur, y), _alpha(tt, st['start'], st['end'], fps)))
            if tt + 1 / fps >= st['end'] - 1e-9: cur = y
        else: out.append(((cur, None), 0))
    return out
if __name__ == '__main__':
    what = sys.argv[1]; sc = float(sys.argv[2]) if len(sys.argv) > 2 else 2 / 3; out = sys.argv[3] if len(sys.argv) > 3 else None; fps = int(sys.argv[4]) if len(sys.argv) > 4 else FPS
    CW, CH = int(1920 * sc), int(1080 * sc)
    if what == 'eo':
        e = EO(); tgt = e.target()
        print(encode((e.frame(sc, y, a, z, tgt, ta, nt)[0] for (y, a, z, ta, nt) in eo_timeline(fps)), out, CW, CH, fps), 'frames')
    elif what == 'to':
        t = TO(); print(encode((t.frame(sc, y, a)[0] for (y, a) in to_timeline(fps)), out, CW, CH, fps), 'frames')
    elif what == 'eo-sched':
        e = EO(); tgt = e.target(); sched = json.load(open(sys.argv[5])); print(encode((e.frame(sc, y, a, z, tgt, ta, nt)[0] for (y, a, z, ta, nt) in eo_states_from_schedule(sched, fps)), out, CW, CH, fps), 'frames')
    elif what == 'to-sched':
        t = TO(); sched = json.load(open(sys.argv[5])); print(encode((t.frame(sc, y, a, clarify=True)[0] for (y, a) in to_states_from_schedule(sched, fps)), out, CW, CH, fps), 'frames')
