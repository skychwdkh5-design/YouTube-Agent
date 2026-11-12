import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from fill import pushpull, blur, texture
OUT='/mnt/project-files/voyager/EP013/cover/layers'
import os; os.makedirs(OUT,exist_ok=True)
a=np.asarray(Image.open('v_plate_noatlas.png')).astype(np.float32)
H,W=a.shape[:2]
R,G,B=a[...,0],a[...,1],a[...,2]; lum=a.mean(-1)
def box(x0,y0,x1,y1):
    m=np.zeros((H,W),bool); m[y0:y1,x0:x1]=True; return m
def soft(m,r): return np.asarray(Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32)/255
def dil(m,k): return np.asarray(Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(k)))>127
def save(name,alpha,src=a):
    rgba=np.dstack([src,np.clip(alpha,0,1)*255]).astype(np.uint8)
    Image.fromarray(rgba,'RGBA').save(f'{OUT}/{name}.png')
# text
sig=np.clip((lum-95)/50,0,1)*box(70,0,1340,248)
redness=R-(G+B)/2
lost=np.clip((redness-45)/55,0,1)*box(90,245,1215,525)
# wave (line + warm glow)
wv=box(425,535,1165,750)
wave=np.clip((lum-58)/70,0,1)*wv
wave=np.maximum(wave, np.clip((lum-40)/120,0,1)*wv*0.0)
# probe group: planet disc + probe structures
m=Image.new('L',(W,H),0); d=ImageDraw.Draw(m)
cx,cy,r=1690,730,548
d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=255)
d.polygon([(845,950),(860,1010),(1520,830),(1500,780)],fill=255)
d.polygon([(1260,1080),(1520,860),(1560,880),(1330,1080)],fill=255)
probe=soft(np.asarray(m)>127,6)
probe=np.maximum(probe, np.clip((lum-60)/60,0,1)*box(840,780,1200,1020)*dil(np.asarray(m)>127,25))
# plate: remove text, wave, probe group, then fill dark + grain
hole=dil((sig>0.05)|(lost>0.05)|(wave>0.04)|(probe>0.02),9)
known=(~hole)&(lum<80)&(R<130)
low=blur(pushpull(a,known),5)
tex=texture((H,W),a[0:180,1330:1530],5)
f=low+tex
mm=np.maximum(soft(hole,4),hole*1.0)[...,None]
plate=np.clip(a*(1-mm)+f*mm,0,255)
# keep the corner label on the plate untouched
lab=box(1530,10,1900,150)[...,None]
orig=np.asarray(Image.open('v_cover_1080_src.png')).astype(np.float32)
plate=np.where(lab,orig,plate)
Image.fromarray(plate.astype(np.uint8)).save(f'{OUT}/plate.png')
save('signal',sig); save('lost',lost); save('wave',wave); save('probe',probe)
# check recomposite
comp=plate.copy()
for n in ['probe','lost','signal','wave']:
    L=np.asarray(Image.open(f'{OUT}/{n}.png')).astype(np.float32); al=L[...,3:]/255
    comp=comp*(1-al)+L[...,:3]*al
Image.fromarray(comp.astype(np.uint8)).save('v_recomp.png')
print('max diff vs no-atlas', np.abs(comp-a).max(), np.abs(comp-a).mean())
