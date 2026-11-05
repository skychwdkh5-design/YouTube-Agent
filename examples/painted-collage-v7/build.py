"""Suez painted editorial collage, selected style 3; generated illustrations over a NASA map."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance
import numpy as np, math, subprocess, wave, json, urllib.request, hashlib
R=Path(__file__).resolve().parent;W,H=1920,1080;OUT=(1280,720);FPS=30
def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
def pop(x):
 x=max(0,min(1,x));return 1+(2.3)*(x-1)**3+1.3*(x-1)**2
def ft(n):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',n)
if not (R/'suez_original.jpg').exists():
 urllib.request.urlretrieve('https://assets.science.nasa.gov/content/dam/science/esd/eo/images/imagerecords/148000/148114/suezcanal_oli_202170_lrg.jpg',R/'suez_original.jpg')
assert hashlib.sha256((R/'suez_original.jpg').read_bytes()).hexdigest()=='46caf0253cf64157f7911ce4663578ca9857b2a338e781fd503ae481855565bf'
atlas=Image.open(R/'atlas.webp').convert('RGBA')
# Actual atlas is 1254 square; bounds selected after visual inspection, not assumed grid halves.
def asset(rect):
 im=atlas.crop(rect);a=im.getchannel('A').filter(ImageFilter.MinFilter(3));a=a.point(lambda v:0 if v<80 else v);im.putalpha(a);return im.crop(a.getbbox())
SHIP=asset((130,0,610,770)).rotate(90,expand=True)
CAPTAIN=asset((745,0,1160,735));MONEY=asset((25,773,755,1254));CLOCK=asset((785,738,1215,1230))
rawmap=Image.open(R/'suez_original.jpg').convert('RGB').rotate(270,expand=True)
rawmap=rawmap.resize((W,round(rawmap.height*W/rawmap.width)),Image.Resampling.LANCZOS)
MAP=rawmap.crop((0,135,W,135+H)).convert('RGBA')
# Slight restrained grade preserves image texture; map is a context layer, not evidence of prop positions.
MAP=ImageEnhance.Color(MAP).enhance(.82)
sprite_cache={}
def paste_prop(canvas,im,center,width,angle=0,alpha=1):
 if width<2 or alpha<=.001:return
 width=int(width);angle=round(angle,1);key=(id(im),width,angle)
 if key not in sprite_cache:
  h=int(im.height*width/im.width);s=im.resize((width,h),Image.Resampling.LANCZOS)
  if abs(angle)>.05:s=s.rotate(angle,Image.Resampling.BICUBIC,expand=True)
  # Avoid holding all animation frames in RAM.
  if len(sprite_cache)>140:sprite_cache.clear()
  sprite_cache[key]=s
 s=sprite_cache[key];x=int(center[0]-s.width/2);y=int(center[1]-s.height/2)
 if alpha<.999:s=s.copy();s.putalpha(s.getchannel('A').point(lambda v:int(v*alpha)))
 shadow=Image.new('RGBA',s.size,(0,0,0,0));shadow.putalpha(s.getchannel('A').point(lambda v:int(v*.38)).filter(ImageFilter.GaussianBlur(9)))
 canvas.alpha_composite(shadow,(x+12,y+20));canvas.alpha_composite(s,(x,y))
def route(draw,pts,p,color,width=6):
 p=max(0,min(1,p));num=(len(pts)-1)*p;k=int(num);out=pts[:k+1]
 if k<len(pts)-1:
  a,b=pts[k],pts[k+1];q=num-k;out=out+[(a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q)]
 if len(out)>1:draw.line(out,fill=color,width=width,joint='curve')
def text(d,p,s,size=32,color='#F7E9CD',stroke=0):d.text(p,s,font=ft(size),fill=color,stroke_width=stroke,stroke_fill='#102934')
def scene_time(t):
 if t<8.7:return t
 if t<10:return 8.65*(1-ease((t-8.7)/1.3))
 return min(4.5,(t-10)*1.6)
def scene(t):
 s=scene_time(t);im=MAP.copy();d=ImageDraw.Draw(im)
 path=[(100,520),(420,500),(730,465),(1030,440),(1310,430),(1610,430),(1850,440)]
 route(d,path,ease(s/.8),(85,220,213,230),10)
 # Direction markers physically travel along the same route, then halt behind the obstruction.
 blocked=ease((s-1.8)/1.1)
 for j in range(10):
  x=140+((s*180+j*174)%1710)
  if blocked>.7 and 1060<x<1510:continue
  y=500-(x-300)*.045;d.polygon([(x+15,y),(x-10,y-10),(x-10,y+10)],fill=(225,244,231,180))
 hero_x=370+740*ease(s/2.4);hero_y=465-15*ease(s/2.4)
 # Queue enters as independent symbols with staggered timing; count is illustrative.
 for j in range(12):
  q=pop((s-3.0-j*.085)/.44)
  if q<=0:continue
  lane=j//6;idx=j%6;x=170+idx*142;y=600+lane*110
  paste_prop(im,SHIP,(x+25*(1-ease((s-3.0)/1.7)),y),133*q,0,min(1,max(0,q)))
 # Main prop turns and stops. This is symbolic staging, not actual vessel dynamics or coordinates.
 paste_prop(im,SHIP,(hero_x,hero_y),610+40*blocked,-37*blocked)
 d=ImageDraw.Draw(im)
 if s>2.3:
  q=ease((s-2.3)/.35);a=int(255*q)
  d.arc((940,200,1375,690),10,350,fill=(240,100,76,a),width=7)
  text(d,(1190,663),'EVER GIVEN',25,'#FFE3AA',1)
  # Clear stop marker instead of a fabricated physical barrier.
  d.line((1355,367,1405,417),fill=(250,112,85,a),width=12);d.line((1405,367,1355,417),fill=(250,112,85,a),width=12)
 if s>3.15:
  q=pop((s-3.15)/.52);paste_prop(im,CAPTAIN,(1640,720-10*math.sin(s*3)),360*q,2*math.sin(s*2))
  if s>3.8:
   d=ImageDraw.Draw(im);text(d,(1770,425),'!',65,'#F4C55D',2)
  if s>4.05:
   d=ImageDraw.Draw(im);text(d,(130,805),'HUNDREDS WAITING',30,'#FFF1D1',1)
 if s>5.05:
  q=pop((s-5.05)/.65);paste_prop(im,MONEY,(520,270),385*q,-4)
  d=ImageDraw.Draw(im)
  if q>.8:text(d,(350,420),'CARGO ON HOLD',25,'#F6EAD1',1)
 if s>6.3:
  q=pop((s-6.3)/.7);paste_prop(im,CLOCK,(965,235),340*q,0)
  d=ImageDraw.Draw(im)
  if s>6.8:
   text(d,(1170,105),'6',132,'#FFDB86',2);text(d,(1179,245),'DAYS',32,'#FFF0D6',1)
  # Authored indicator sweeps around the dial, separate from the generated hands.
  if q>.8:
   an=(s-6.3)*3.4;cx,cy=965,260
   d.line((cx,cy,cx+math.sin(an)*68,cy-math.cos(an)*68),fill='#BC4D30',width=4)
 # Camera re-composes a coherent shared map, never cuts to a separate slide background.
 if s<3.1:z=1.48;cx=hero_x;cy=465
 elif s<4.8:
  q=ease((s-3.1)/.75);z=1.48-.44*q;cx=1100-140*q;cy=465+45*q
 elif s<6.3:
  q=ease((s-4.8)/.8);z=1.04+.31*q;cx=960-200*q;cy=510-120*q
 else:
  q=ease((s-6.3)/.7);z=1.35+.15*q;cx=760+205*q;cy=390-60*q
 if t>=10:z=1.04;cx=960;cy=510
 cw=W/z;ch=H/z;x=max(0,min(W-cw,cx-cw/2));y=max(0,min(H-ch,cy-ch/2));im=im.crop((x,y,x+cw,y+ch)).resize((W,H),Image.Resampling.LANCZOS)
 d=ImageDraw.Draw(im)
 if 8.7<=t<10:
  for j in range(3):d.polygon([(780+j*95,140),(780+j*95,205),(730+j*95,172)],fill='#F7EDD6')
  for y in range(0,H,6):d.line((0,y,W,y),fill=(15,35,45,30))
 if t>10.2:
  q=ease((t-10.2)/.45);text(d,(65,105),'MARCH 2021',int(42*q)+1,'#F9EBCB',1)
  text(d,(65,165),'SUEZ CANAL · EGYPT',24,'#95DFD9',1)
 return im.convert('RGB')
BEATS=[(0,1.65,'One ship.'),(1.8,3.0,'One blocked canal.'),(3.2,5.1,'Hundreds of ships waiting.'),(5.2,6.55,'Cargo going nowhere.'),(6.6,8.55,'For six days.'),(8.7,9.95,"Let's rewind."),(10.1,12.0,'March twenty twenty-one.'),(12.1,15,'The Suez Canal. One ship. One bottleneck.')]
def finish(im,t):
 ov=Image.new('RGBA',(W,H));d=ImageDraw.Draw(ov)
 for y in range(120):
  a=int(145*(1-y/120)**2);d.line((0,y,W,y),fill=(7,20,29,a));d.line((0,H-y,W,H-y),fill=(7,20,29,a+25))
 text(d,(42,30),'ORBITAL ATLAS',19,'#F4EDD8');text(d,(1390,31),'ILLUSTRATION · NOT TO SCALE',17,'#F4EDD8')
 text(d,(42,H-35),'Map: NASA Earth Observatory / Landsat · Objects and movement illustrative',15,'#E3E9E2')
 for a,b,txt in BEATS:
  if a<=t<b:
   box=d.textbbox((0,0),txt,font=ft(39));tw=box[2];text(d,((W-tw)/2,H-107),txt,39,'#FFFFFF',2)
 return Image.alpha_composite(im.convert('RGBA'),ov).convert('RGB').resize(OUT,Image.Resampling.LANCZOS)
def audio():
 sr=48000;tt=np.arange(sr*15)/sr;mix=np.zeros(len(tt));rng=np.random.default_rng(6)
 for i,(start,end,txt) in enumerate(BEATS):
  f=R/f'line_{i}.txt';f.write_text(txt);p=R/f'line_{i}.wav'
  subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i',f'flite=textfile={f}:voice=slt','-ar',str(sr),'-ac','1',str(p)],check=True)
  with wave.open(str(p)) as w:v=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
  limit=int((end-start-.04)*sr)
  if len(v)>limit:v=np.interp(np.linspace(0,len(v)-1,limit),np.arange(len(v)),v)
  k=int(start*sr);mix[k:k+len(v)]+=v*.8
 air=np.convolve(rng.normal(0,1,len(tt)),np.ones(40)/40,'same');mix+=air*.018
 for start in [0,1.8,2.8,3.2,5.05,6.3,8.7,10]:
  q=tt-start;sel=(q>=0)&(q<.5);u=q[sel];mix[sel]+=.18*np.sin(2*np.pi*(95*u-65*u*u))*np.exp(-u*14);mix+=air*.18*np.exp(-((tt-start)/.12)**2)
 for start in np.arange(6.4,8.7,.3):
  q=tt-start;sel=(q>=0)&(q<.05);u=q[sel];mix[sel]+=.05*np.sin(2*np.pi*1600*u)*np.exp(-u*90)
 sel=(tt>=8.7)&(tt<10);q=tt[sel]-8.7;mix[sel]+=.05*np.sin(2*np.pi*(190*q+160*q*q))+.08*air[sel]
 mix*=np.minimum((15-tt)/.25,1)
 with wave.open(str(R/'mix.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(mix,-.98,.98)*32767).astype('<i2').tobytes())
def build():
 audio();p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','30','-i','-','-i',str(R/'mix.wav'),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',str(R/'OA_suez_painted_v7_15s.mp4')],stdin=subprocess.PIPE)
 for i in range(450):p.stdin.write(finish(scene(i/30),i/30).tobytes())
 p.stdin.close();assert p.wait()==0
if __name__=='__main__':build()
