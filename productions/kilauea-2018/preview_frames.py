"""Still frames from the storyboard plan for review (no video, no audio)."""
import sys, json
sys.path.insert(0, '/home/user/YouTube-Agent/.claude/skills/yt-render')
import render as r, compose as c
from PIL import Image, ImageDraw, ImageFont
plan = c.validate(json.load(open('timeline_storyboard.json')), '.', r.LIMITS)
P = c.Painter(plan)
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)
times = [float(x) for x in sys.argv[2:]]
th = []
for t in times:
    im = P.frame(t); im = im if isinstance(im, Image.Image) else Image.fromarray(im)
    im = im.convert('RGB'); d = ImageDraw.Draw(im)
    shot = next(s for s in reversed(plan['shots']) if s['start'] <= t + 1e-9)
    d.rectangle((0, 1840, 1080, 1920), fill='black'); d.text((20, 1850), f"{t:.1f}s {shot['id']}", font=F, fill='white')
    th.append(im.resize((270, 480)))
cols = 7; rows = (len(th) + cols - 1) // cols
S = Image.new('RGB', (cols * 274, rows * 484), (15, 15, 15))
for i, t in enumerate(th): S.paste(t, ((i % cols) * 274, (i // cols) * 484))
S.save(sys.argv[1], quality=88); print(sys.argv[1], S.size)
