import sys; sys.argv=["x","thumbmode"]
sys.path.insert(0,"/home/claude/ep009")
import numpy as np, cv2, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import engine as E
REPO="/home/claude/skychwdkh5-design/youtube-agent/productions/ep009-tornado-scars"
im=Image.fromarray(cv2.cvtColor(cv2.imread(f"{REPO}/media_original/nasa_tuscaloosa_EO1_20110502.jpg"),cv2.COLOR_BGR2RGB)); d=E.Doc(im)
W,H=1920,1080; cx,cy,vw=2500,3985,1380
c=d.render(cx,cy,vw)
TR=[(2024,4248),(2420,4014),(2780,3798),(3104,3618)]; s=W/vw
pts=[(W/2+(x-cx)*s,H/2+(y-cy)*s) for x,y in TR]
m=E.corridor(pts,95*s,95*s*.55); c=E.spotlight(c,m,0.55,1.25)
img=Image.fromarray(np.clip(c*255,0,255).astype(np.uint8)).convert("RGBA")
ov=Image.new("RGBA",(W,H),(0,0,0,0)); dr=ImageDraw.Draw(ov)
f=ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Black.otf",250)
for t,y,col in (("FROM",560,(244,238,226)),("SPACE",780,(232,176,84))):
    sh=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(sh).text((90,y),t,font=f,fill=(0,0,0,200)); sh=sh.filter(ImageFilter.GaussianBlur(12)); ov.alpha_composite(sh); ImageDraw.Draw(ov).text((80,y-8),t,font=f,fill=col+(255,))
img.alpha_composite(ov); out=img.convert("RGB").resize((1280,720),Image.LANCZOS); out.save("OA_EP009_thumbnail_A.jpg",quality=92)
