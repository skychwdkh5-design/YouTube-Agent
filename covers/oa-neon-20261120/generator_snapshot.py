"""Orbital Atlas cover style "Neon Contour" (approved by the owner 2026-11-20).

neon_cover(hero, top, big, chip) -> 1280x720 RGB
  hero : PIL RGB image of the real subject (frame from the video / source image)
  top  : 0-2 short white lines above the neon word
  big  : the one neon-lime word or number (the hook)
  chip : source / honesty label shown in the lime pill (keep credits and ILLUSTRATION/RECONSTRUCTION labels)
"""
import sys, os, json, math
sys.path.insert(0, '/tmp/claude-0/s')
from make4 import *

TEXT_W = 540


def fit(s, start, maxw, fname='unb', minsize=40):
    size = start
    while size > minsize and twf(s, F(fname, size)) > maxw:
        size -= 4
    return size


def neon_cover(hero, top, big, chip, seed=1.3, hero_cy=0.5, hero_cx=0.5):
    bg = Image.new('RGBA', (W, H), INKB + (255,))
    bg.alpha_composite(contours(W, H, LIME, seed=seed, alpha=70))
    c, r = (910, 360), 300
    neon_ring(bg, c, r + 18, MAG, 8)
    bg.alpha_composite(disc(fill(hero, 2 * r, 2 * r, cx=hero_cx, cy=hero_cy), 2 * r), (c[0] - r, c[1] - r))
    neon_ring(bg, c, r + 46, LIME, 3)
    d = ImageDraw.Draw(bg)
    for i in range(0, 360, 10):
        a = math.radians(i); r1 = r + 60; r2 = r + (78 if i % 30 == 0 else 68)
        d.line([(c[0] + r1 * math.cos(a), c[1] + r1 * math.sin(a)), (c[0] + r2 * math.cos(a), c[1] + r2 * math.sin(a))], fill=LIME + (200,), width=3)
    streaks(bg, 26, MAG, 420, 700, 3)
    # text block: white lines then the neon word, vertically centred in 40..585
    tsz = min([fit(t, 76, TEXT_W) for t in top] or [76])
    bsz = fit(big, 190 if len(top) >= 2 else 210, 700)
    hs = [tsz * 1.25] * len(top) + [bsz * 1.2]
    y = max(36, (590 - sum(hs)) / 2 - 10)
    for t in top:
        text(bg, (46, y), t, F('unb', tsz), WHITE); y += tsz * 1.25
    fbig = F('unb', bsz)
    L = Image.new('RGBA', bg.size, (0, 0, 0, 0))
    ImageDraw.Draw(L).text((40, y - bsz * 0.05), big, font=fbig, fill=MAG + (255,), stroke_width=6, stroke_fill=MAG + (255,))
    gl = L.filter(ImageFilter.GaussianBlur(22))
    bg.alpha_composite(gl); bg.alpha_composite(gl)
    ImageDraw.Draw(bg).text((40, y - bsz * 0.05), big, font=fbig, fill=LIME, stroke_width=7, stroke_fill=INKB)
    fb = F('unb', 20)
    cw = twf(chip, fb)
    if cw > 500:
        fb = F('unb', fit(chip, 20, 500, minsize=12)); cw = twf(chip, fb)
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((46, 612, 46 + cw + 36, 658), 23, outline=LIME, width=3)
    text(bg, (64, 635), chip, fb, LIME, anchor='lm')
    text(bg, (W - 270, 34), 'ORBITAL ATLAS', F('unb', 20), MAG)
    return bg.convert('RGB')


CUR = S + 'oa_cur/'


def cover_crop(vid, box):
    return Image.open(CUR + vid + '.jpg').convert('RGB').crop(box)


def hero_png(n, box=None):
    im = Image.open(S + f'src/hero_{n}.png').convert('RGB')
    w, h = im.size
    return im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h))) if box else im


def g(im, s=1.5, c=1.2, b=1.05):
    return grade(im, s, c, b)


# video_id, slug, hero (callable), top lines, neon word, chip
EPS = [
    ('sVInlyhIY7c', 'ep-elnino', lambda: elnino_hero(), ['THE PACIFIC', 'TURNED'], 'RED', 'NASA SVS · SEA SURFACE TEMP'),
    ('1TAlkxnuDJY', 'ep015-starship', lambda: g(hero_png('star', (0.3, 0.2, 0.76, 1.0))), ['THEY CAUGHT'], 'STARSHIP', 'FLIGHT 15 · BOOSTER LOST'),
    ('J6T1JGIUYRI', 'ep014-artemis', lambda: g(hero_png('art', (0.42, 0.04, 0.98, 0.82)), 1.2, 1.3, 1.25), ['THEY SAW', '5 FLASHES ON'], 'THE MOON', 'NASA · ARTEMIS II'),
    ('OUYNDoW54KQ', 'ep013-voyager', lambda: g(hero_png('voy', (0.2, 0.11, 0.74, 0.78))), ['VOYAGER 1', 'SIGNAL'], 'LOST', 'NASA DEEP SPACE NETWORK'),
    ('RirYVjOyZq4', 'ep012-bennu', lambda: duo(samcam_raw(), (40, 0, 60), (255, 120, 235), 0.9), ['IT KEPT'], 'SINKING', 'OSIRIS-REx · OCT 20, 2020'),
    ('iOQne8mgNFk', 'ep011-tunguska', lambda: g(hero_png('tun', (0.38, 0.1, 0.92, 1.0)), 1.6, 1.3, 1.2), ['TUNGUSKA 1908', 'BUT'], 'NO CRATER', 'RECONSTRUCTION'),
    ('ZWYia9XfjMI', 'ep010-icecube', lambda: g(hero_png('ice', (0.18, 0.1, 0.82, 0.97))), ['A TELESCOPE', 'BURIED'], '2.5 KM', 'PHOTO: C. MICHEL · CC BY-SA 4.0'),
    ('dmv8-mG9pvk', 'ep009-tornado', lambda: g(cover_crop('dmv8-mG9pvk', (760, 20, 1240, 360)), 1.2), ['SCAR FROM'], 'SPACE', 'STYLIZED ILLUSTRATION · 2011'),
    ('VQoqReQm9S4', 'ep008-moon', lambda: g(cover_crop('VQoqReQm9S4', (700, 60, 1280, 640)), 1.2), ['NO MOON'], 'LANDING', 'PHOTO: NASA · ARTEMIS II'),
    ('c369ApHh8I8', 'ep007-mars', lambda: g(cover_crop('c369ApHh8I8', (870, 180, 1280, 590)), 1.2), ['A MARS ROCK'], 'CRACKED', 'NASA · CURIOSITY ROVER'),
    ('J1WzDfYsAG0', 'ep005-neom', lambda: g(cover_crop('J1WzDfYsAG0', (880, 230, 1280, 600)), 1.3), ['PROMISED'], '170 KM', 'COPERNICUS SENTINEL DATA'),
    ('D9yQ3X8_J1g', 'ep004-jakarta', lambda: g(cover_crop('D9yQ3X8_J1g', (840, 330, 1280, 720)), 1.2), ['JAKARTA IS'], 'SINKING', 'ILLUSTRATION'),
    ('RSZwZyRAEAA', 'ep003-gsl', lambda: g(cover_crop('RSZwZyRAEAA', (740, 220, 1240, 720)), 1.2), ['GREAT SALT LAKE', '20 FEET'], 'LOWER', '37 YEARS FROM ORBIT'),
    ('XbhVPSCPKwA', 'ep002-dubai', lambda: g(cover_crop('XbhVPSCPKwA', (820, 130, 1280, 590)), 1.2), ['BUILT FROM'], 'NOTHING', 'DUBAI · IN 3 YEARS'),
    ('QRc2kPJ3cHE', 'ep001-sahara', lambda: g(cover_crop('QRc2kPJ3cHE', (730, 300, 1010, 580)), 1.2), ['THE SAHARA', 'IS'], 'CHANGING', '1984 VS 2024'),
]

if __name__ == '__main__':
    out = S + 'oaneon/'
    os.makedirs(out, exist_ok=True)
    meta = []
    for i, (vid, slug, hero, top, big, chip) in enumerate(EPS):
        im = neon_cover(hero(), top, big, chip, seed=1.1 + i * 0.37)
        im.save(out + f'{slug}.jpg', quality=92)
        meta.append({'video_id': vid, 'slug': slug, 'top': top, 'big': big, 'chip': chip})
    json.dump(meta, open(out + 'meta.json', 'w'), indent=1)
    print('ok', len(meta))
