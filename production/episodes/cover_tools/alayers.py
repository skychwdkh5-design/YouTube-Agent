import numpy as np, os
from PIL import Image, ImageDraw, ImageFilter
from fill import pushpull, blur, texture
OUT='/mnt/project-files/artemis/EP014/cover/layers'; os.makedirs(OUT,exist_ok=True)
orig=np.asarray(Image.open('a_cover_1080_src.png')).astype(np.float32)
a=orig.copy(); H,W=a.shape[:2]
R,G,B=a[...,0],a[...,1],a[...,2]; lum=a.mean(-1)
def soft(m,r): return np.asarray(Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32)/255
def dil(m,k): return np.asarray(Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(k)))>127
def box(x0,y0,x1,y1):
    m=np.zeros((H,W),bool); m[y0:y1,x0:x1]=True; return m
# 1) painted ATLAS + held book
m=Image.new('L',(W,H),0); d=ImageDraw.Draw(m)
d.ellipse((-15,440,400,815),fill=255)
d.polygon([(0,760),(420,800),(520,760),(640,700),(790,672),(830,700),(800,770),(770,840),(720,890),(860,900),(880,1080),(0,1080)],fill=255)
d.ellipse((290,680,430,810),fill=255)
hole=dil(np.asarray(m)>127,9)
paper=(lum>150)&(R-B<95)
known=(~hole)&paper&(np.arange(W)[None,:]>120)&(lum>175)
low=blur(pushpull(a,known),6)
tile=a[680:780,1640:1800]
f=low+texture((H,W),tile,7)
mm=np.maximum(soft(hole,4),hole*1.0)[...,None]
out=a*(1-mm)+f*mm
# left page stack / leather strip continues downward
strip=a[330:450,0:75]
for y in range(440,1080):
    k=(y-440)%240; sy=k if k<120 else 239-k
    w=mm[y,0:75]
    out[y,0:75]=out[y,0:75]*(1-w)+strip[sy]*w
# bottom page edge + desk under the removed area (copy from right of the hole)
band=a[1000:1080,880:1000]
for x in range(60,900):
    k=(x-60)%240; sx=k if k<120 else 239-k
    w=mm[1000:1080,x]
    out[1000:1080,x]=out[1000:1080,x]*(1-w)+band[:,sx]*w
# T stem of THIS continues behind the removed helmet
for y in range(440,577):
    sy=440+(y-440)%30
    for x in range(286,384):
        if mm[y,x,0]<=0: continue
        sx=int(round(x+0.06*(y-sy)))
        v=orig[sy,sx] if y<575 else out[y,x]
        out[y,x]=out[y,x]*(1-mm[y,x,0])+v*mm[y,x,0]
noatl=np.clip(out,0,255)
Image.fromarray(noatl.astype(np.uint8)).save('a_plate_noatlas.png')
a=noatl; R,G,B=a[...,0],a[...,1],a[...,2]; lum=a.mean(-1)
# 2) layers
ink=box(180,22,830,588)
title=np.clip((100-lum)/45,0,1)*ink*((R-B)<45)
orange=(R>170)&(G>60)&(G<170)&(B<90)&(R-B>110)
under=soft(orange,0.8)*box(380,520,830,620)
title=np.maximum(title,np.clip(under*1.5,0,1))
marks=np.clip(soft(dil(orange,3),1.0)*1.6,0,1)*box(830,70,1450,920)
mc=Image.new('L',(W,H),0); ImageDraw.Draw(mc).ellipse((1175-492,500-492,1175+492,500+492),fill=255)
moon=soft(np.asarray(mc)>127,2.5)
ship=box(1660,300,1890,520)*np.clip((np.abs(a-np.array([236,222,196])).max(-1)-25)/30,0,1)
ship=soft(dil(ship>0.3,7),2)*box(1660,300,1890,520)
def save(n,al,src=a):
    Image.fromarray(np.dstack([src,np.clip(al,0,1)*255]).astype(np.uint8),'RGBA').save(f'{OUT}/{n}.png')
hole2=dil((title>0.05)|(marks>0.05)|(moon>0.02)|(ship>0.05),9)
known=(~hole2)&(lum>150)&(R-B<95)
low=blur(pushpull(a,known),6)
f=low+texture((H,W),tile,9)
mm2=np.maximum(soft(hole2,4),hole2*1.0)[...,None]
plate=np.clip(a*(1-mm2)+f*mm2,0,255)
plate[:22,:900]=a[:22,:900]
Image.fromarray(plate.astype(np.uint8)).save(f'{OUT}/plate.png')
save('title',title); save('marks',marks); save('moon',np.clip(moon-marks-title,0,1)); save('ship',ship)
comp=plate.copy()
for n in ['moon','marks','ship','title']:
    L=np.asarray(Image.open(f'{OUT}/{n}.png')).astype(np.float32); al=L[...,3:]/255
    comp=comp*(1-al)+L[...,:3]*al
Image.fromarray(comp.astype(np.uint8)).save('a_recomp.png')
print(np.abs(comp-a).mean())
