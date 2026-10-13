"""EP002 thumbnail 1280x720: the same patch of the Persian Gulf, NASA ASTER 11 Nov 2000 (left) vs 4 Nov 2003 (right), cropped from the SAME pixel box of the shared ASTER grid.
Only real NASA images (colours as published, darkened only by a text scrim) + dated labels. No AI imagery. Output: thumbnail_1280x720.jpg"""
import os, sys
os.environ['EP002_SCALE'] = '1'
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'preview'))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import kit, scenes as S
cx, cy = S.SITE[0]; BW = 1060; BH = int(BW * 720 / 640)
box = (int(cx - BW / 2 - 40), int(cy - BH / 2), int(cx + BW / 2 - 40), int(cy + BH / 2))
def crop(key):
    im = S.src(key).convert('RGB'); x0, y0, x1, y1 = box; x0 = max(0, min(x0, im.width - (x1 - x0))); y0 = max(0, min(y0, im.height - (y1 - y0)))
    return im.crop((x0, y0, x0 + (x1 - x0), y0 + (y1 - y0))).resize((640, 720), Image.LANCZOS)
out = Image.new('RGB', (1280, 720)); out.paste(crop('2000'), (0, 0)); out.paste(crop('2003'), (640, 0))
a = np.asarray(out, np.float32); y = np.linspace(0, 1, 720)[:, None, None]
a *= 1 - np.clip((y - 0.55) / 0.45, 0, 1) ** 1.3 * 0.78 - np.clip(1 - y / 0.2, 0, 1) * 0.45       # text scrims (bottom, top)
out = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(out)
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; AMBER = (255, 190, 60)
def txt(xy, s, px, fill, anchor='mm', stroke=0):
    d.text(xy, s, font=ImageFont.truetype(FB, px), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))
d.line([(640, 0), (640, 720)], fill=AMBER, width=6)
txt((320, 60), 'NOV 2000', 54, (255, 255, 255), stroke=3); txt((960, 60), 'NOV 2003', 54, AMBER, stroke=3)
txt((640, 590), '3 YEARS', 150, (255, 255, 255), stroke=6)
d.rounded_rectangle([14, 688, 560, 714], 6, fill=(8, 14, 22)); txt((24, 701), 'NASA EARTH OBSERVATORY · ASTER · SAME AREA', 17, (255, 255, 255), anchor='lm')
out.save('thumbnail_1280x720.jpg', quality=92, optimize=True); print(out.size, os.path.getsize('thumbnail_1280x720.jpg'))
