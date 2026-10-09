#!/usr/bin/env python3
"""EP001 Shorts: two 1080x1920 30 fps vertical Shorts built from the locked narration.

Audio is sliced from the normalized narration (no TTS). Visuals: Landsat tone-B East Oweinat crops
(cached npy frames), NASA Blue Marble backdrop, PIL cards. Captions are burned in from the word timings.
Usage: build_shorts.py WORKDIR OUTDIR [short1|short2] [--preview N]
"""
import json, os, subprocess, sys, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

W, H, FPS = 1080, 1920, 30
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VOICE = os.path.join(ROOT, 'narration/voice/narration.voice.json')
CACHE = os.environ.get('EP001_VIS_CACHE')
FONT = '/usr/share/fonts/opentype/inter/Inter-%s.otf'
words = json.load(open(VOICE))['words']


def font(w, s):
    p = FONT % w
    return ImageFont.truetype(p if os.path.exists(p) else FONT % 'Bold', s)


def eo(y):
    return Image.fromarray(np.load(os.path.join(CACHE, 'EO_%d_base.npy' % y)))


def kb(img, c0, z0, c1, z1, u):
    """Ken Burns crop: centre (fractions of the image) and zoom (fraction of image height shown)."""
    u = u * u * (3 - 2 * u)
    cx = c0[0] + (c1[0] - c0[0]) * u; cy = c0[1] + (c1[1] - c0[1]) * u; z = z0 + (z1 - z0) * u
    ch = img.height * z; cw = ch * W / H
    if cw > img.width:
        cw = img.width; ch = cw * H / W
    x = min(max(cx * img.width - cw / 2, 0), img.width - cw); y = min(max(cy * img.height - ch / 2, 0), img.height - ch)
    return img.resize((W, H), Image.BILINEAR, box=(x, y, x + cw, y + ch))


def grad(im, top=0.0, bot=0.55):
    a = np.linspace(top, bot, H)[:, None, None] if False else None
    ov = Image.new('L', (1, H))
    ov.putdata([int(255 * (top + (bot - top) * max(0, (i / H - 0.45) / 0.55) ** 1.2 if bot > top else top)) for i in range(H)])
    black = Image.new('RGB', (W, H), (0, 0, 0))
    return Image.composite(black, im, ov.resize((W, H)))


def text(d, xy, s, f, fill=(255, 255, 255), anchor='mm', stroke=8):
    d.text(xy, s, font=f, fill=(0, 0, 0), anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def wrap(d, s, f, maxw):
    out, cur = [], ''
    for w in s.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: out.append(cur); cur = w
    return out + [cur]


def block(im, lines, y, f, fill=(255, 255, 255), gap=12):
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        text(d, (W // 2, y + i * (f.size + gap)), ln, f, fill)
    return im


def darken(im, a):
    return Image.blend(im, Image.new('RGB', im.size, (6, 12, 22)), a)


def credit(im, s):
    d = ImageDraw.Draw(im, 'RGBA'); f = font('Bold', 28)
    w = d.textlength(s, font=f) + 36
    d.rounded_rectangle([W - w - 135, 170, W - 135, 220], 12, fill=(0, 0, 0, 150))
    d.text((W - 153, 195), s, font=f, fill=(235, 235, 235), anchor='rm')
    return im


def sentence_times(a, b):
    ws = words[a:b + 1]
    return ws[0]['start'], ws[-1]['end']


def build(name, ranges, shots, pad=0.35, tail=0.6):
    """ranges: list of (first_word, last_word). Returns timeline dict mapping output time to narration slices."""
    t = 0.0; slices = []; omap = []
    for a, b in ranges:
        s, e = sentence_times(a, b); s = max(0, s - 0.08); e = e + 0.12
        slices.append((s, e, t)); omap.append((a, b, s, t)); t += e - s + pad
    return slices, t - pad + tail


def out_time(wi, slices):
    w = words[wi]
    for s, e, t0 in slices:
        if s - 0.2 <= w['start'] <= e:
            return t0 + (w['start'] - s) + 0.08
    raise ValueError(wi)


def caption_chunks(ranges, slices):
    chunks = []
    for a, b in ranges:
        grp = []
        for i in range(a, b + 1):
            grp.append(i)
            end = words[i]['text'][-1] in ',.?!;:'
            if len(grp) >= 4 or end or (len(grp) >= 3 and len(words[i]['text']) > 7):
                chunks.append(grp); grp = []
        if grp: chunks.append(grp)
    res = []
    for g in chunks:
        res.append((out_time(g[0], slices), out_time(g[-1], slices) + (words[g[-1]]['end'] - words[g[-1]]['start']) + 0.1,
                    ' '.join(words[i]['text'] for i in g).upper().rstrip('.,;:')))
    # close gaps (hold caption until next starts within 0.25 s)
    for i in range(len(res) - 1):
        if res[i + 1][0] - res[i][1] < 0.25: res[i] = (res[i][0], res[i + 1][0], res[i][2])
    return res


def draw_caption(im, s):
    d = ImageDraw.Draw(im, 'RGBA'); f = font('Black', 78)
    lines = wrap(d, s, f, 920)
    h = len(lines) * 92 + 30
    y0 = 1380 - (h - 120) // 2
    d.rounded_rectangle([60, y0 - 20, W - 60, y0 + h - 20], 24, fill=(0, 0, 0, 120))
    for i, ln in enumerate(lines):
        text(d, (W // 2, y0 + 50 + i * 92), ln, f, (255, 255, 255), stroke=7)
    return im


# ------------------------------------------------------------------ Short 1: East Oweinat
def short1():
    ranges = [(631, 725), (807, 827)]
    slices, total = build('s1', ranges, None)
    cap = caption_chunks(ranges, slices)
    e84, e24 = eo(1984), eo(2024)
    T = lambda wi: out_time(wi, slices)
    t_today = T(649); t_water = T(666); t_aq = T(671); t_when = T(691); t_yes = T(807); t_one = T(814)
    bounds = [0, t_today, t_water, t_aq, t_when, t_yes, t_one, total]
    names = ['barren', 'green', 'below', 'aquifer', 'when', 'yes', 'one']

    def frame(t):
        k = max(i for i in range(7) if t >= bounds[i]); u = (t - bounds[k]) / max(bounds[k + 1] - bounds[k], 1e-6)
        if k == 0:
            im = kb(e84, (0.40, 0.45), 0.60, (0.50, 0.55), 0.30, u)
            lab = 'Landsat 5 · USGS · 1984'
            if t < 2.0:  # hook: the 2024 fields wiped away to the barren 1984 view
                new = ImageEnhance.Color(kb(e24, (0.40, 0.45), 0.60, (0.40, 0.45), 0.57, t / 2.0)).enhance(1.3)
                x = int(W * min(max((t - 0.6) / 1.2, 0), 1))
                if x < W: new.paste(im.crop((0, 0, x, H)), (0, 0)); im = new
                lab = 'Landsat 9 · 2024 / Landsat 5 · 1984'
            credit(im, lab)
            top = ('THE SAHARA IS', 'TURNING GREEN?')
            block(im, top, 330, font('Black', 100), (255, 214, 0))
            block(im, ['EAST OWEINAT, EGYPT'], 590, font('Bold', 50))
            if t > 4: block(im, ['1984: ALMOST ENTIRELY BARREN'], 700, font('Bold', 46), (255, 214, 0))
            return im
        if k == 1:
            # wipe from 1984 to 2024 over the first 0.9 s, then push in on the circles
            base = kb(e24, (0.42, 0.40), 0.55, (0.50, 0.32), 0.30, u)
            old = kb(e84, (0.40, 0.45), 0.50, (0.50, 0.32), 0.30, u)
            wp = min((t - bounds[1]) / 0.9, 1)
            x = int(W * wp); im = base.copy(); im.paste(old.crop((x, 0, W, H)), (x, 0))
            if wp < 1: ImageDraw.Draw(im).line([(x, 0), (x, H)], fill=(255, 255, 255), width=6)
            im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.3)).enhance(1.15)
            credit(im, 'Landsat 9 · USGS · 2024')
            block(im, ['1984 → 2024'], 330, font('Black', 96), (255, 214, 0))
            block(im, ['EACH CIRCLE ≈ HALF A MILE'], 450, font('Bold', 46))
            return im
        if k in (2, 3, 4):
            im = darken(kb(e24, (0.20 + 0.05 * k, 0.30), 0.30, (0.25 + 0.05 * k, 0.36), 0.38, u), 0.55)
            credit(im, 'Landsat 9 · USGS · 2024')
            if k == 2:
                block(im, ['THE WATER'], 380, font('Black', 120), (255, 255, 255))
                block(im, ['COMES FROM BELOW'], 520, font('Black', 100), (255, 214, 0))
            elif k == 3:
                block(im, ['NUBIAN SANDSTONE', 'AQUIFER'], 330, font('Black', 96), (255, 214, 0))
                block(im, ['Fossil groundwater shared by', 'Egypt · Libya · Sudan · Chad'], 600, font('Bold', 48))
            else:
                block(im, ['SOAKED IN'], 330, font('Black', 90))
                block(im, ['10,000 TO'], 460, font('Black', 130), (255, 214, 0))
                block(im, ['1,000,000 YEARS AGO'], 610, font('Black', 78), (255, 214, 0))
                block(im, ['NASA: recharges slowly; considered', 'a non-renewable resource today'], 740, font('Bold', 44))
            return im
        im = kb(e24, (0.50, 0.30), 0.34, (0.55, 0.26), 0.20, u) if k == 5 else kb(e24, (0.55, 0.26), 0.20, (0.62, 0.20), 0.28, u)
        im = ImageEnhance.Color(im).enhance(1.25)
        credit(im, 'Landsat 9 · USGS · 2024')
        if k == 5:
            block(im, ['SO YES,', 'WE CAN GREEN', 'THE DESERT'], 330, font('Black', 112), (255, 255, 255))
        else:
            block(im, ['ONE FIELD AT A TIME'], 330, font('Black', 78), (255, 214, 0))
            block(im, ['WATER STORED LONG AGO,', 'ONLY SLOWLY REPLACED'], 470, font('Bold', 56))
        return im
    return slices, total, cap, frame


# ------------------------------------------------------------------ Short 2: can humans turn it green
def short2():
    ranges = [(0, 5), (828, 850), (920, 1005)]
    slices, total = build('s2', ranges, None)
    cap = caption_chunks(ranges, slices)
    africa = Image.open(os.path.join(ROOT, 'production/stills/africa.0700.jpg')).convert('RGB')
    gil = Image.open(os.path.join(ROOT, 'production/stills/gilf_toneB.png')).convert('RGB')
    tas = Image.open(os.path.join(ROOT, 'production/stills/tassili_toneB.png')).convert('RGB')
    T = lambda wi: out_time(wi, slices)
    b = [0, T(828), T(838), T(920), T(930) if False else T(930), T(950), T(970), total]
    # 922 'rain?' 949 'Sahara.' -> 1,000 mm card until the second model begins (word 950+)
    b = [0, T(828), T(838), T(922), T(931), T(950), T(970), total]

    def frame(t):
        k = max(i for i in range(7) if t >= b[i]); u = (t - b[k]) / max(b[k + 1] - b[k], 1e-6)
        if k == 0:
            im = darken(kb(tas, (0.5, 0.5), 0.9, (0.5, 0.5), 0.7, u), 0.15)
            credit(im, 'Landsat 8 · USGS')
            block(im, ['CAN HUMANS', 'TURN THE', 'SAHARA GREEN?'], 330, font('Black', 104), (255, 214, 0))
            return im
        if k == 1:
            im = darken(kb(africa, (0.50, 0.38), 0.78, (0.48, 0.40), 0.60, u), 0.50)
            credit(im, 'NASA Blue Marble (SVS 3539)')
            block(im, ['2009 PROPOSAL'], 330, font('Black', 104), (255, 214, 0))
            block(im, ['Fast-growing forests across', 'the Sahara and the Outback,', 'watered with desalinated', 'seawater'], 470, font('Bold', 56))
            return im
        if k == 2:
            im = darken(kb(africa, (0.48, 0.40), 0.60, (0.48, 0.42), 0.50, u), 0.62)
            credit(im, 'NASA Blue Marble (SVS 3539)')
            block(im, ['SEAWATER →', 'DESALINATION →', 'PIPELINES →', 'FOREST'], 340, font('Black', 92), (255, 255, 255), gap=26)
            block(im, ['A proposal, not an existing system'], 840, font('Bold', 46), (255, 214, 0))
            return im
        if k == 3:
            im = darken(kb(gil, (0.5, 0.5), 0.9, (0.5, 0.5), 0.8, u), 0.55)
            credit(im, 'Landsat 7 · USGS')
            block(im, ['WOULD IT RAIN?'], 380, font('Black', 112), (255, 214, 0))
            block(im, ['Authors’ own simulation', 'One climate model'], 560, font('Bold', 52))
            return im
        if k == 4:
            im = darken(kb(gil, (0.5, 0.5), 0.8, (0.5, 0.5), 0.7, u), 0.6)
            credit(im, 'Landsat 7 · USGS')
            block(im, ['1,000+', 'mm / year'], 330, font('Black', 150), (255, 214, 0), gap=20)
            block(im, ['(about 40 in) over roughly', 'half of the irrigated Sahara'], 700, font('Bold', 52))
            block(im, ['2009 model result'], 880, font('Bold', 42), (210, 210, 210))
            return im
        if k == 5:
            im = darken(kb(africa, (0.50, 0.40), 0.55, (0.50, 0.42), 0.50, u), 0.62)
            credit(im, 'NASA Blue Marble (SVS 3539)')
            block(im, ['A LATER MODEL'], 330, font('Black', 96), (255, 255, 255))
            block(im, ['+267', 'mm / year'], 470, font('Black', 140), (255, 214, 0), gap=20)
            block(im, ['(about 10 in) across the', 'whole Sahara'], 830, font('Bold', 52))
            return im
        im = darken(kb(africa, (0.50, 0.42), 0.50, (0.50, 0.40), 0.62, u), 0.62)
        credit(im, 'NASA Blue Marble (SVS 3539)')
        block(im, ['THE AUTHORS', 'CALLED THAT', 'A WEAK INCREASE'], 340, font('Black', 96), (255, 214, 0))
        block(im, ['Model results, not forecasts'], 700, font('Bold', 48))
        return im
    return slices, total, cap, frame


def render(name, spec, outdir, work, preview=None):
    slices, total, cap, frame = spec
    n = int(round(total * FPS))
    wav = os.path.join(work, name + '.wav')
    src = os.path.join(work, 'narration_norm16.wav')
    fl = []; inputs = []
    for i, (s, e, t0) in enumerate(slices):
        fl.append('[0:a]atrim=%.4f:%.4f,asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st=%.4f:d=0.06,adelay=%d|%d[a%d]'
                  % (s, e, e - s - 0.06, int(t0 * 1000), int(t0 * 1000), i))
    fl.append(''.join('[a%d]' % i for i in range(len(slices))) + 'amix=inputs=%d:normalize=0,apad=whole_dur=%.4f,atrim=0:%.4f[a]' % (len(slices), total, total))
    subprocess.check_call(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-filter_complex', ';'.join(fl), '-map', '[a]', '-ar', '48000', wav])
    mp4 = os.path.join(outdir, name + '.mp4')
    tmp = mp4 + '.tmp.mp4'
    if preview: n = preview
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS),
                          '-i', '-', '-i', wav, '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-r', str(FPS),
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', tmp], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        im = frame(t)
        for a, b, s in cap:
            if a <= t < b: im = draw_caption(im, s); break
        p.stdin.write(im.convert('RGB').tobytes())
    p.stdin.close(); assert p.wait() == 0
    os.replace(tmp, mp4)
    return mp4, total, cap


if __name__ == '__main__':
    work, outdir = sys.argv[1], sys.argv[2]
    which = [a for a in sys.argv[3:] if a.startswith('short')] or ['short1', 'short2']
    prev = int(sys.argv[sys.argv.index('--preview') + 1]) if '--preview' in sys.argv else None
    CACHE = CACHE or os.path.join(work, 'vis_cache')
    os.makedirs(outdir, exist_ok=True)
    names = {'short1': ('SHORT1_The_Sahara_Is_Turning_Green', short1), 'short2': ('SHORT2_Can_Humans_Turn_The_Sahara_Green', short2)}
    for k in which:
        nm, fn = names[k]
        mp4, total, cap = render(nm, fn(), outdir, work, prev)
        sha = hashlib.sha256(open(mp4, 'rb').read()).hexdigest()
        json.dump({'file': os.path.basename(mp4), 'duration_s': round(total, 3), 'sha256': sha, 'captions': cap}, open(mp4[:-4] + '.json', 'w'), indent=1)
        print(k, mp4, round(total, 2), sha)
