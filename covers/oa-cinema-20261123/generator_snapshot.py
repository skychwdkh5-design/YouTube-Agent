import os, sys, json, hashlib
sys.path.insert(0, '/tmp/claude-0/sc/skill')
from PIL import Image
from cinema_cover import cinema_cover

S = '/tmp/claude-0/sc/'
OUT = S + 'oa-cinema-20261123/'
os.makedirs(OUT, exist_ok=True)

def frame(path, box):
    im = Image.open(path).convert('RGB')
    if im.size != (1920, 1080) and path.endswith('.jpg') and 'prev/' not in path:
        im = im.resize((1920, 1080), Image.LANCZOS)
    return im.crop(box)

def prev(vid, box, patches=()):
    im = Image.open(S + f'prev/{vid}.jpg').convert('RGB')
    for (x0, y0, x1, y1, dx, dy) in patches:
        from PIL import ImageDraw, ImageFilter
        src = im.crop((x0 + dx - 20, y0 + dy - 20, x1 + dx + 20, y1 + dy + 20))
        m = Image.new('L', src.size, 0); ImageDraw.Draw(m).rectangle((12, 12, src.width - 12, src.height - 12), fill=255)
        im.paste(src, (x0 - 20, y0 - 20), m.filter(ImageFilter.GaussianBlur(8)))
    return im.crop(box)

EL = '/mnt/project-files/cover-style/v1/src/elnino0.png'
EPS = [
 # video_id, slug, hero(), pre, word, loc, credit, latlon, coords, focus
 ('hU-HQOY867Q', 'oa-topaz', lambda: frame(S + 'hi/topaz_99.jpg', (300, 40, 1620, 783)), 'FOUND FROM 65,000 FT', 'TOPAZ',
  'MOJAVE DESERT, CALIFORNIA', 'NASA ER-2 · ARCHIVE FOOTAGE', (34.9, -117.0), '34.9°N  117.0°W', (0.55, 0.45)),
 ('FzB622H_LH0', 'oa-alaska-lake', lambda: frame(S + 'hi/lake_2.5.jpg', (380, 60, 1700, 803)), 'THIS LAKE LEAKS A GAS THAT', 'BURNS',
  'FAIRBANKS, ALASKA', 'NASA ABoVE FOOTAGE', (64.8, -147.7), '64.8°N  147.7°W', (0.6, 0.68)),
 ('dJ7pXdLzB0Q', 'oa-fire', lambda: frame(S + 'h2/fire_39.jpg', (40, 100, 1316, 818)), '1,200 ACRES IN 45 MIN', 'ON PURPOSE',
  'FORT STEWART, GEORGIA', 'NASA FIRESENSE', (31.9, -81.6), '31.9°N  81.6°W', (0.5, 0.5)),
 ('DgvDzvtA08M', 'oa-ice-equator', lambda: frame(S + 'ic/j_0.1.jpg', (300, 30, 1620, 773)), 'ICE NEAR THE EQUATOR', '2% LEFT',
  'PUNCAK JAYA, NEW GUINEA', 'NASA / USGS LANDSAT', (-4.1, 137.2), '4.1°S  137.2°E', (0.55, 0.4)),
 ('sVInlyhIY7c', 'ep-elnino', lambda: Image.open(EL).convert('RGB').crop((900, 230, 1920, 804)), 'THE PACIFIC TURNED', 'RED',
  'EQUATORIAL PACIFIC', 'NASA SVS · SEA SURFACE TEMP.', (0, -120), None, (0.5, 0.5)),
 ('1TAlkxnuDJY', 'ep015-starship', lambda: frame(S + 'h2/star_292.jpg', (300, 190, 1660, 955)), 'THEY CAUGHT', 'STARSHIP',
  'STARBASE, TEXAS', 'ILLUSTRATION · NOT FLIGHT FOOTAGE', (26.0, -97.2), '26.0°N  97.2°W', (0.5, 0.5)),
 ('J6T1JGIUYRI', 'ep014-artemis', lambda: frame(S + 'h2/art_flash.jpg', (0, 0, 1920, 1080)), 'THEY SAW 5 FLASHES ON', 'THE MOON',
  'FAR SIDE OF THE MOON', 'NASA · ARTEMIS II', None, None, (0.5, 0.5)),
 ('OUYNDoW54KQ', 'ep013-voyager', lambda: frame(S + 'h2/voy_dish.jpg', (0, 0, 1920, 1080)), 'VOYAGER 1 SIGNAL', 'LOST',
  'INTERSTELLAR SPACE', 'NASA ANIMATION', None, None, (0.5, 0.5)),
 ('RirYVjOyZq4', 'ep012-bennu', lambda: frame(S + 'h2/bennu_16.jpg', (440, 330, 1480, 915)), 'IT KEPT', 'SINKING',
  'ASTEROID BENNU', 'NASA · OSIRIS-REx SAMCAM', None, 'OCT 20, 2020', (0.5, 0.5)),
 ('iOQne8mgNFk', 'ep011-tunguska', lambda: frame(S + 'h2/tun_221.jpg', (0, 70, 1792, 1078)), 'TUNGUSKA 1908, BUT', 'NO CRATER',
  'TUNGUSKA, SIBERIA', 'PHOTO: KULIK EXPEDITION, 1929', (60.9, 101.9), '60.9°N  101.9°E', (0.5, 0.5)),
 ('ZWYia9XfjMI', 'ep010-icecube', lambda: frame(S + 'h2/icecube_60.jpg', (230, 75, 1690, 896)), 'A TELESCOPE BURIED', '2.5 KM',
  'SOUTH POLE, ANTARCTICA', 'PHOTO: C. MICHEL · CC BY-SA 4.0', (-90, 0), '90°S', (0.5, 0.5)),
 ('dmv8-mG9pvk', 'ep009-tornado', lambda: prev('dmv8-mG9pvk', (770, 44, 1280, 331)), 'SCAR FROM', 'SPACE',
  'ALABAMA, USA', 'STYLIZED ILLUSTRATION · 2011', (33.0, -87.0), None, (0.5, 0.5)),
 ('VQoqReQm9S4', 'ep008-moon', lambda: prev('VQoqReQm9S4', (580, 60, 1280, 454)), 'NO MOON', 'LANDING',
  'THE MOON', 'PHOTO: NASA · ARTEMIS II', None, None, (0.5, 0.5)),
 ('c369ApHh8I8', 'ep007-mars', lambda: prev('c369ApHh8I8', (800, 180, 1280, 450)), 'A MARS ROCK', 'CRACKED',
  'GALE CRATER, MARS', 'NASA · CURIOSITY ROVER', None, None, (0.5, 0.5)),
 ('J1WzDfYsAG0', 'ep005-neom', lambda: prev('J1WzDfYsAG0', (790, 370, 1280, 646), [(1030, 600, 1250, 646, 0, -75)]), 'PROMISED', '170 KM',
  'THE LINE, SAUDI ARABIA', 'COPERNICUS SENTINEL DATA', (28.0, 35.3), None, (0.5, 0.5)),
 ('D9yQ3X8_J1g', 'ep004-jakarta', lambda: prev('D9yQ3X8_J1g', (0, 340, 680, 722)), 'JAKARTA IS', 'SINKING',
  'JAKARTA, INDONESIA', 'ILLUSTRATION', (-6.2, 106.8), '6.2°S  106.8°E', (0.5, 0.5)),
 ('RSZwZyRAEAA', 'ep003-gsl', lambda: prev('RSZwZyRAEAA', (240, 300, 960, 705)), 'GREAT SALT LAKE, 20 FEET', 'LOWER',
  'GREAT SALT LAKE, UTAH', '37 YEARS FROM ORBIT', (41.1, -112.5), '41.1°N  112.5°W', (0.5, 0.5)),
 ('XbhVPSCPKwA', 'ep002-dubai', lambda: prev('XbhVPSCPKwA', (690, 180, 1280, 512)), 'BUILT FROM', 'NOTHING',
  'PALM JUMEIRAH, DUBAI', 'DUBAI · IN 3 YEARS', (25.1, 55.1), '25.1°N  55.1°E', (0.5, 0.5)),
 ('QRc2kPJ3cHE', 'ep001-sahara', lambda: prev('QRc2kPJ3cHE', (380, 230, 1240, 714), [(990, 515, 1155, 590, 0, 75), (495, 430, 745, 515, 0, 90)]), 'THE SAHARA IS', 'CHANGING',
  'SAHARA, NORTH AFRICA', '1984 VS 2024', (23.0, 25.0), None, (0.5, 0.5)),
]

if __name__ == '__main__':
    meta = []
    for vid, slug, hero, pre, word, loc, credit, latlon, coords, focus in EPS:
        im = cinema_cover(hero(), pre, word, loc, credit, latlon, coords, focus)
        p = OUT + f'{slug}.jpg'
        im.save(p, quality=90)
        meta.append(dict(video_id=vid, slug=slug, pre=pre, word=word, loc=loc, credit=credit,
                         sha256=hashlib.sha256(open(p, 'rb').read()).hexdigest(), bytes=os.path.getsize(p)))
    json.dump(meta, open(OUT + 'meta.json', 'w'), indent=1, ensure_ascii=False)
    # contact sheets
    for k in range(0, len(meta), 6):
        sh = Image.new('RGB', (1280 * 2, 720 * 3))
        for i, m in enumerate(meta[k:k + 6]):
            sh.paste(Image.open(OUT + m['slug'] + '.jpg'), ((i % 2) * 1280, (i // 2) * 720))
        sh.resize((1280, 1080)).save(S + f'allsheet_{k // 6}.jpg', quality=85)
    print(len(meta))
