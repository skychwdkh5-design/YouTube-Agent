"""Story-framing contact sheet: identical geographic windows across dates (no processing beyond crop+resize)."""
import json, sys
sys.path.insert(0, '/home/user/YouTube-Agent/.claude/skills/yt-geo')
import geostack as g
from PIL import Image, ImageDraw, ImageFont
G = json.load(open('stack/grid.json'))
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
def px(lon, lat):
    x, y = g.lonlat_to_utm(lon, lat, G['epsg']); return ((float(x) - G['x0']) / 30, (G['y_top'] - float(y)) / 30)
def row(box, ids, h):
    x0, y1 = px(box[0], box[1]); x1, y0 = px(box[2], box[3]); out = []
    for i in ids:
        im = Image.open(f'stack/{i}.png').crop((round(x0), round(y0), round(x1), round(y1)))
        im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
        d = ImageDraw.Draw(im); lab = i[1:5] + '-' + i[5:7] + '-' + i[7:]
        d.text((10, 8), lab, font=F, fill='white', stroke_width=3, stroke_fill='black'); out.append(im)
    return out
rows = [("EAST RIFT / KAPOHO  (-155.00..-154.80, 19.42..19.56)", row([-155.00, 19.42, -154.80, 19.56],
         ['d20180327', 'd20180514', 'd20180530', 'd20190226', 'd20190720'], 330)),
        ("SUMMIT / HALEMA'UMA'U  (-155.31..-155.24, 19.38..19.44)", row([-155.31, 19.38, -155.24, 19.44],
         ['d20180327', 'd20180514', 'd20190720', 'd20250805'], 330))]
W = max(sum(t.width for t in r) + 8 * (len(r) - 1) for _, r in rows)
H = sum(330 + 44 for _ in rows)
sheet = Image.new('RGB', (W, H), (20, 20, 20)); y = 0; d = ImageDraw.Draw(sheet)
for title, r in rows:
    d.text((10, y + 8), title, font=F, fill='white'); y += 44; x = 0
    for t in r: sheet.paste(t, (x, y)); x += t.width + 8
    y += 330
sheet.save('contact_sheet_story.jpg', quality=90); print(sheet.size)
