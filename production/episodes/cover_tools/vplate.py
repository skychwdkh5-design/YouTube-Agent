import numpy as np
from PIL import Image, ImageDraw
from fill import fill, pushpull, blur, texture
src=Image.open('/mnt/project-files/voyager/EP013/cover/approved_signal_lost_source.png').convert('RGB').resize((1920,1080),Image.LANCZOS)
src.save('v_cover_1080_src.png')
a=np.asarray(src).copy()
m=Image.new('L',(1920,1080),0); d=ImageDraw.Draw(m)
d.ellipse((212-214,670-208,212+214,670+208),fill=255); d.ellipse((-60,450,300,900),fill=255)
d.polygon([(0,700),(330,760),(470,800),(515,760),(560,705),(660,690),(745,715),(755,860),(705,1000),(655,1080),(0,1080)],fill=255)
m=m.filter(__import__('PIL.ImageFilter',fromlist=['x']).MaxFilter(9))
hole=np.asarray(m)>0
lum=a.mean(-1)
dark=(lum<75)&(a[...,0]<120)
known=(~hole)&dark
low=blur(pushpull(a.astype(np.float32),known),4)
tex=texture(hole.shape,a[0:180,1330:1530].astype(np.float32),3)
f=low+tex
from PIL import ImageFilter
mm=np.asarray(m.filter(ImageFilter.GaussianBlur(5))).astype(np.float32)/255
mm=np.maximum(mm,hole*1.0)[...,None]
out=a*(1-mm)+f*mm
# rebuild the hidden bottom of the L (the painted helmet covered it)
for y in range(440,512):
    xl=150-0.29*(y-330); xr=345+0.29*(498-y)
    sy=425+(y-440)%28
    for x in range(int(xl)-2,int(xr)+3):
        cov=min(1,max(0,x-xl+0.5))*min(1,max(0,xr-x+0.5))*min(1,max(0,498.5-y))
        if mm[y,x,0]<=0: continue
        src=a[sy,int(x+0.29*(y-sy))].astype(np.float32)
        out[y,x]=out[y,x]*(1-cov)+src*cov if y>=445 or mm[y,x,0]>0.5 else out[y,x]
out=np.clip(out,0,255).astype(np.uint8)
Image.fromarray(out).save('v_plate_noatlas.png')
np.save('v_hole.npy',hole)
