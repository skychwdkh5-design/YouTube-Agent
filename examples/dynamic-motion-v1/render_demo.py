"""Original schematic style test. Requires Pillow, numpy and ffmpeg. No external assets."""
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import math, subprocess, wave
from pathlib import Path

ROOT=Path(__file__).resolve().parent
W,H,FPS=1280,720,30
YELLOW='#F4D35E'; CYAN='#60E1E0'; WHITE='#F2F4EF'
def font(n): return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',n)
def ease(x):
 x=max(0,min(1,x)); return x*x*(3-2*x)
rng=np.random.default_rng(26)
yy,xx=np.mgrid[0:H,0:W]
v=np.zeros((H,W))
for _ in range(24):
 a,b=rng.uniform(-.025,.025,2); v+=rng.uniform(.3,1)*np.sin(xx*a+yy*b+rng.uniform(0,7))
v=(v-v.min())/(v.max()-v.min())
arr=np.stack([24+v*66,32+v*67,32+v*50],-1).astype('uint8')
base=Image.fromarray(arr)
d=ImageDraw.Draw(base)
for k in range(15):
 pts=[(x,int(100+k*46+30*math.sin(x/150+k*.5))) for x in range(-20,W+30,12)]
 d.line(pts,fill=(87,101,83),width=1)
poly=[(747,235),(870,210),(963,282),(920,366),(811,394),(724,323),(747,235)]
d.polygon(poly,fill=(125,112,65)); d.line(poly,fill=(166,149,84),width=3)
def path(draw,pts,p,color,width):
 p=max(0,min(1,p)); n=(len(pts)-1)*p; i=int(n)
 out=pts[:i+1]
 if i<len(pts)-1:
  a,b=pts[i],pts[i+1]; f=n-i;out=out+[(a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f)]
 if len(out)>1:draw.line(out,fill=color,width=width,joint='curve')
def text(d,xy,s,n=38,color=WHITE):d.text(xy,s,font=font(n),fill=color)
def frame(t):
 im=base.copy(); dr=ImageDraw.Draw(im)
 if t<3:
  z=1+.18*ease(t/3); crop=(int(840-840/z),int(300-300/z),int(840+(W-840)/z),int(300+(H-300)/z));im=im.crop(crop).resize((W,H));dr=ImageDraw.Draw(im)
 elif t<6:
  dark=Image.new('RGB',(W,H),(4,11,15));im=Image.blend(im,dark,.55)
  mask=Image.new('L',(W,H));ImageDraw.Draw(mask).polygon(poly,fill=255);im.paste(base,(0,0),mask);dr=ImageDraw.Draw(im)
  path(dr,poly,ease((t-3)/.65),YELLOW,5)
  path(dr,[(860,300),(1000,190),(1140,190)],ease((t-3.55)/.5),YELLOW,3)
  if t>4.05:text(dr,(988,145),'LOOK HERE',24,YELLOW)
 elif t<10:
  route=[(160,550),(315,490),(445,510),(580,380),(700,410),(835,305)]
  path(dr,route,ease((t-6)/2.2),CYAN,6)
  p=ease((t-6)/2.2)*(len(route)-1);i=min(len(route)-2,int(p));f=min(1,p-i);a,b=route[i],route[i+1];x=a[0]+(b[0]-a[0])*f;y=a[1]+(b[1]-a[1])*f
  dr.ellipse((x-10,y-10,x+10,y+10),fill=WHITE)
  path(dr,poly,1,YELLOW,3)
 elif t<13:
  im=Image.new('RGB',(W,H),(11,23,31));dr=ImageDraw.Draw(im)
  for y in range(180,600,40):dr.line((90,y,1190,y),fill=(23,43,51),width=1)
  for x in range(90,1200,40):dr.line((x,180,x,600),fill=(23,43,51),width=1)
  points=[(170,500),(420,290),(630,410),(920,235),(1100,350)]
  path(dr,points,ease((t-10)/.9),CYAN,5)
  for j,(x,y) in enumerate(points):
   if t-10>j*.17:dr.ellipse((x-13,y-13,x+13,y+13),outline=YELLOW,width=4)
  for j in range(6):
   p=((t-10)*.45+j/6)%1;x=210+p*800;y=580
   dr.polygon([(x,y),(x-13,y-8),(x-13,y+8)],fill=YELLOW)
 else:
  left=base.resize((560,350));right=base.crop((670,165,1010,430)).resize((560,350));im=Image.new('RGB',(W,H),(11,23,31));im.paste(left,(60,240));im.paste(right,(660,240));dr=ImageDraw.Draw(im)
  dr.rectangle((660,240,1220,590),outline=YELLOW,width=4)
  text(dr,(60,615),'CONTEXT',22,CYAN);text(dr,(660,615),'DETAIL',22,YELLOW)
 dr.rectangle((0,0,W,135),fill=(9,18,24))
 text(dr,(60,24),'ORBITAL ATLAS',20,CYAN)
 if t<3: title='WHAT SHOULD YOU NOTICE?'; sub='Start with a visual question.'
 elif t<6:title='ISOLATE THE DETAIL.';sub='Color directs your attention.'
 elif t<10:title='DRAW THE CONNECTION.';sub='Reveal the route as the story unfolds.'
 elif t<13:title='MAKE THE MOTION CLEAR.';sub='Use geometry to explain direction.'
 else:title='THEN SHOW THE BIG PICTURE.';sub='Every effect serves the explanation.'
 text(dr,(60,66),title,40)
 dr.rectangle((40,660,1240,710),fill=(9,18,24));text(dr,(60,672),sub,23)
 text(dr,(825,27),'ILLUSTRATION / STYLE TEST',18,YELLOW)
 dr.rectangle((0,716,int(W*t/15),719),fill=CYAN)
 return im

if __name__=='__main__':
 sr=48000;ts=np.arange(15*sr)/sr;audio=np.zeros(len(ts))
 for start in [0,3,6,10,13]:
  u=ts-start;active=(u>=0)&(u<.35);q=u[active];audio[active]+=.22*np.sin(2*np.pi*(150*q-100*q*q))*np.exp(-q*14)
 for start in [3.5,4,6.5,7,7.5,10.2,10.4,10.6]:
  u=ts-start;active=(u>=0)&(u<.12);q=u[active];audio[active]+=.055*np.sin(2*np.pi*950*q)*np.exp(-q*40)
 with wave.open(str(ROOT/'accents.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((audio*32767).astype('<i2').tobytes())
 p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(ROOT/'accents.wav'),'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart','-shortest',str(ROOT/'OA_motion_style_15s.mp4')],stdin=subprocess.PIPE)
 for i in range(FPS*15):p.stdin.write(frame(i/FPS).tobytes())
 p.stdin.close();assert p.wait()==0
 sheet=Image.new('RGB',(W*2,H*2))
 for n,t in enumerate([1.5,4.8,8,11.8]):sheet.paste(frame(t),((n%2)*W,(n//2)*H))
 sheet.resize((1280,720)).save(ROOT/'contact.jpg')
