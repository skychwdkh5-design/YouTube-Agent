"""Original layered 2D motion pilot, not scientific reconstruction. Pillow/numpy/FFmpeg."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import numpy as np, math, subprocess, wave, json
R=Path(__file__).resolve().parent;W,H,FPS=1280,720,30
def ease(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
def ft(n):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',n)
def lerp(a,b,t):return a+(b-a)*t
def poly(d,p,c):d.polygon(p,fill=c)
def line(d,p,c,w=3):d.line(p,fill=c,width=w,joint='curve')
# Assets are authored independently: terrain, rover rig, rock halves, crystals, particles.
yy=np.linspace(0,1,H)[:,None,None]
a=np.array([24,36,49])[None,None,:];b=np.array([186,100,66])[None,None,:]
bg=Image.fromarray(np.tile(np.uint8(a*(1-yy)+b*yy),(1,W,1)))
d=ImageDraw.Draw(bg);d.ellipse((1010,65,1090,145),fill='#F9D09B')
for p,c in [([(0,350),(120,315),(240,348),(360,265),(450,310),(600,290),(780,352),(930,280),(1100,325),(1280,285),(1280,720),(0,720)],'#865949'), ([(0,430),(190,370),(340,410),(530,350),(730,402),(900,355),(1080,398),(1280,350),(1280,720),(0,720)],'#A66B50'), ([(0,510),(220,466),(450,510),(720,465),(970,490),(1280,445),(1280,720),(0,720)],'#BC805B')]:poly(d,p,c)
rng=np.random.default_rng(11)
for _ in range(340):
 x=int(rng.integers(0,W));y=int(rng.integers(520,H));q=int(rng.integers(1,5));d.ellipse((x,y,x+q*3,y+q),fill=('#DCA074' if q<3 else '#916346'))
line(d,[(0,585),(250,575),(550,588),(850,578),(1280,590)],'#E0A278',2)
def wheel(d,x,y,angle,lift=0):
 y-=lift;d.ellipse((x-35,y-35,x+35,y+35),fill='#252A30',outline='#111D26',width=4)
 d.ellipse((x-24,y-24,x+24,y+24),fill='#5D6770',outline='#AEB8B7',width=3)
 for k in range(8):
  an=angle+k*math.pi/4;line(d,[(x,y),(x+math.cos(an)*26,y+math.sin(an)*26)],'#CCD0C5',3)
 d.ellipse((x-7,y-7,x+7,y+7),fill='#EEC277')
def rover(im,x,t,shock=0,close=False):
 d=ImageDraw.Draw(im);y=500-10*shock
 d.ellipse((x-170,575,x+165,595),fill='#835843')
 # Suspension and wheels remain independent of chassis/face/mast.
 for off in [-108,0,108]:line(d,[(x+off,y+25),(x+off,548)],'#D1CBB7',10)
 for off in [-108,0,108]:wheel(d,x+off,548,(x-220)/34,shock*15 if off==108 else 0)
 poly(d,[(x-140,y-40),(x+95,y-40),(x+145,y),(x+110,y+30),(x-125,y+30),(x-150,y+10)],'#E9DCC0')
 poly(d,[(x-140,y-40),(x+95,y-40),(x+65,y-62),(x-105,y-62)],'#FFF0CF')
 poly(d,[(x+95,y-40),(x+145,y),(x+110,y+30),(x+105,y-10)],'#ABAA98')
 line(d,[(x-110,y+6),(x+100,y+6)],'#A8987A',3)
 for off in [-92,-55,-18]:d.rounded_rectangle((x+off,y-26,x+off+22,y-7),4,fill='#303D46')
 line(d,[(x+28,y-55),(x+28,y-145)],'#D7D5C6',14)
 d.rounded_rectangle((x-12,y-183,x+93,y-132),12,fill='#E9DDC3',outline='#182C38',width=3)
 for off in [12,65]:
  r=13+shock*4;d.ellipse((x+off-r,y-158-r,x+off+r,y-158+r),fill='#233E4A');d.ellipse((x+off-5,y-166,x+off+2,y-159),fill='#6DE3DB')
 line(d,[(x-75,y-62),(x-92,y-122)],'#DAD1B7',5);d.ellipse((x-98,y-129,x-86,y-117),fill='#F1BD62')
 # Arm opens toward the rock during the discovery.
 arm=ease((t-4.5)/.7);line(d,[(x+116,y),(x+155,y+25-55*arm),(x+186,y+30-70*arm)],'#DDD4BC',9)
 d.ellipse((x+176,y+20-70*arm,x+195,y+39-70*arm),fill='#243B47',outline='#F6CA76',width=3)
def rock(im,s,t):
 d=ImageDraw.Draw(im);x,y=810,565
 d.ellipse((x-80,y+4,x+95,y+27),fill='#8C5D42')
 left=[(-67,0),(-59,-48),(-25,-73),(0,-60),(9,-23),(0,8)]
 right=[(0,-60),(39,-66),(68,-40),(75,0),(0,8),(9,-23)]
 for pts,sign,col in [(left,-1,'#64534A'),(right,1,'#80634F')]:
  out=[(x+px+sign*44*s,y+py+abs(px)/80*12*s) for px,py in pts];poly(d,out,col);line(d,out+[out[0]],'#463E3B',3)
 if s>0:
  for j in range(7):
   cx=x-32+j*11;cy=y-6;hh=(26+(j*17)%28)*s
   pts=[(cx-8,cy),(cx-7,cy-hh*.7),(cx,cy-hh),(cx+8,cy-hh*.7),(cx+9,cy)]
   poly(d,pts,'#EEC743');poly(d,[(cx,cy-hh),(cx+8,cy-hh*.7),(cx+9,cy),(cx,cy)],'#BFA03B');line(d,[pts[1],pts[2],pts[3]],'#FFF1A4',2)
  if t>4:
   for j in range(3):
    q=(t*1.3+j*.33)%1;cx=x-25+j*28;cy=y-35-j%2*18;sz=7*math.sin(q*math.pi)
    line(d,[(cx-sz,cy),(cx+sz,cy)],'#FFF4B6',2);line(d,[(cx,cy-sz),(cx,cy+sz)],'#FFF4B6',2)
def world(t):
 im=bg.copy();x=lerp(205,878,ease(t/5.2));split=ease((t-3.65)/.5)
 shock=max(0,1-abs(t-3.55)/.35)
 # Rover passes over, then leaves the opened rock visible behind it.
 rover(im,x,t,shock);rock(im,split,t)
 d=ImageDraw.Draw(im)
 if 3.6<t<4.9:
  q=(t-3.6)/1.3
  for j in range(18):
   an=j*2.399;vel=45+(j%5)*18;px=810+math.cos(an)*vel*q;py=540-abs(math.sin(an))*85*q+65*q*q
   rad=max(1,int(5*(1-q)));d.ellipse((px-rad,py-rad,px+rad,py+rad),fill='#E3AF7B')
 if t>4.8:
  q=ease((t-4.8)/.35);d.ellipse((x+77,286,x+128,286+q*52),fill='#F7E9C9',outline='#B87A51',width=2)
  d.text((x+92,289),'!',font=ft(34),fill='#594536')
 return im
BEATS=[(0,.9,'One wheel.'),(1.0,2.7,'One ordinary rock.'),(3.6,6.5,'Then, a surprise inside.'),(7.5,9.4,'Wait. Rewind.'),(9.7,11.2,'Watch the wheel.'),(11.25,12.7,'The rock breaks.'),(12.9,15,'The hidden detail appears.')]
def frame(t):
 rewind=7.8<=t<9.5
 if t<7.8:wt=t
 elif rewind:wt=lerp(7.7,1.6,ease((t-7.8)/1.7))
 elif t<12.8:wt=lerp(2.8,4.7,(t-9.5)/3.3)
 else:wt=5.5
 im=world(wt)
 # Scene-space camera follows action; second pass shows contact in close-up.
 if 9.5<=t<12.8:z=1.8;cx=790;cy=470
 elif t>=12.8:z=lerp(1.8,3.25,ease((t-12.8)/1.1));cx=810;cy=525
 else:z=1.04+.07*ease(t/7.8);cx=640+36*ease(t/7.8);cy=360
 cw=W/z;ch=H/z;left=max(0,min(W-cw,cx-cw/2));top=max(0,min(H-ch,cy-ch/2));im=im.crop((left,top,left+cw,top+ch)).resize((W,H),Image.Resampling.LANCZOS)
 ov=Image.new('RGBA',(W,H));d=ImageDraw.Draw(ov)
 for y in range(100):d.line((0,H-y,W,H-y),fill=(13,24,31,int(170*(1-y/100)**2)))
 d.text((40,29),'ORBITAL ATLAS',font=ft(17),fill=(248,236,213,220));d.text((930,31),'ILLUSTRATION / MOTION TEST',font=ft(13),fill=(248,236,213,220))
 if rewind:
  for j in range(3):poly(d,[(510+j*85,270),(510+j*85,330),(465+j*85,300)],(255,239,203,230))
  for y in range(0,H,5):d.line((0,y,W,y),fill=(18,48,62,35))
  d.text((535,350),'REWIND',font=ft(20),fill=(255,239,203,240))
 if t>=13.3:
  # Short target mark points to revealed crystals; does not replace object action.
  p=ease((t-13.3)/.45);line(d,[(680,480),(740,360),(740+int(130*p),360)],(247,224,132,230),2)
  if p>.95:d.text((750,327),'HIDDEN INSIDE',font=ft(16),fill=(255,240,194,240))
 for start,end,txt in BEATS:
  if start<=t<end:
   box=d.textbbox((0,0),txt,font=ft(31));tw=box[2];d.text(((W-tw)/2,650),txt,font=ft(31),fill='white',stroke_width=2,stroke_fill=(16,24,30,180))
 return Image.alpha_composite(im.convert('RGBA'),ov).convert('RGB')
def make_audio():
 sr=48000;audio=np.zeros(sr*15);tt=np.arange(sr*15)/sr;rng=np.random.default_rng(7)
 for i,(start,end,txt) in enumerate(BEATS):
  txtfile=R/f'v3_line_{i}.txt';txtfile.write_text(txt)
  wav=R/f'v3_line_{i}.wav'
  subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',f'flite=textfile={txtfile}:voice=slt','-ar',str(sr),'-ac','1',str(wav)],check=True)
  with wave.open(str(wav)) as w:v=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
  available=int((end-start-.06)*sr)
  if len(v)>available:v=np.interp(np.linspace(0,len(v)-1,available),np.arange(len(v)),v)
  k=int(start*sr);audio[k:k+len(v)]+=v*.8
 for start in [0,3.65,9.5,11.25,12.8]:
  u=tt-start;sel=(u>=0)&(u<.5);q=u[sel];audio[sel]+=.15*np.sin(2*np.pi*(110*q-90*q*q))*np.exp(-q*13)
 noise=rng.normal(0,1,len(tt));filtered=np.convolve(noise,np.ones(30)/30,'same')
 audio+=filtered*.014
 sel=(tt>=7.8)&(tt<9.5);u=tt[sel]-7.8;audio[sel]+=.06*np.sin(2*np.pi*(180*u+160*u*u))+.05*filtered[sel]
 for start in [4.1,4.55,13.0,13.45]:
  u=tt-start;sel=(u>=0)&(u<.5);q=u[sel];audio[sel]+=.035*np.sin(2*np.pi*1320*q)*np.exp(-q*8)
 audio*=np.minimum((15-tt)/.2,1)
 with wave.open(str(R/'v3_mix.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(audio,-.98,.98)*32767).astype('<i2').tobytes())
if __name__=='__main__':
 make_audio()
 p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','30','-i','-','-i',str(R/'v3_mix.wav'),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',str(R/'OA_action_v3_15s.mp4')],stdin=subprocess.PIPE)
 for i in range(450):p.stdin.write(frame(i/30).tobytes())
 p.stdin.close();assert p.wait()==0
 sheet=Image.new('RGB',(1280*3,720*2))
 for i,t in enumerate([1,3.55,5.8,8.5,11.6,14.4]):sheet.paste(frame(t),((i%3)*1280,(i//3)*720))
 sheet.resize((1920,720)).save(R/'action_contact.jpg')
