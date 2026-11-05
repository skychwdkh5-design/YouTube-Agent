"""Cinematic illustrated motion study. Input: cinema.png; original synthetic sound."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np, subprocess, math, wave
from pathlib import Path
R=Path(__file__).resolve().parent
W,H=1920,1080; FPS=30
def e(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
def f(n):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',n)
def shot(src,z,cx,cy):
 sw,sh=src.size; ww=sw/z;hh=ww*H/W
 x=max(0,min(sw-ww,cx*sw-ww/2)); y=max(0,min(sh-hh,cy*sh-hh/2))
 return src.crop((x,y,x+ww,y+hh)).resize((W,H),Image.Resampling.LANCZOS)
def render(t,src):
 # Shot changes are cuts into the subject, not changes of title slide.
 if t<3.4:z=1.06+.12*e(t/3.4);cx=.52;cy=.53
 elif t<6.5:z=1.8+.18*e((t-3.4)/3.1);cx=.63;cy=.55
 elif t<10.6:z=1.38+.08*(t-6.5)/4.1;cx=.59;cy=.55
 elif t<12.5:z=2.35-.16*e((t-10.6)/1.9);cx=.62;cy=.53
 else:z=1.13+.045*(t-12.5);cx=.53;cy=.52
 im=shot(src,z,cx,cy).convert('RGB')
 if 6.5<=t<10.6:
  # Hue-selective highlight follows the actual warm crystal pixels, not a floating box.
  a=np.asarray(im).astype(float); r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
  m=np.clip((g-b-22)/45,0,1)*np.clip((r-b-35)/70,0,1)*np.clip((g-95)/65,0,1)
  yy,xx=np.mgrid[0:H,0:W];roi=np.exp(-(((xx-W*.61)/(W*.30))**4+((yy-H*.55)/(H*.32))**4))
  m=m*roi*e((t-6.5)/.5)*(1-e((t-10.0)/.6))
  a=a*(.66+.34*m[:,:,None]);a+=m[:,:,None]*np.array([15,13,2])
  im=Image.fromarray(np.uint8(np.clip(a,0,255)))
  mask=Image.fromarray(np.uint8(m*255));edge=mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1.2))
  # Spatially growing contour; restrained warm glow attached to the crystals.
  em=np.asarray(edge).copy();em[:,int(W*e((t-6.7)/1.15)):]=0
  glow=Image.new('RGB',(W,H),(250,206,95));im=Image.composite(glow,im,Image.fromarray(em).point(lambda v:int(v*.55)))
 overlay=Image.new('RGBA',(W,H));d=ImageDraw.Draw(overlay)
 # Soft top/bottom grading protects small labels without rectangular panels.
 for y in range(220):
  alpha=int(100*(1-y/220)**2);d.line((0,y,W,y),fill=(0,0,0,alpha));d.line((0,H-y,W,H-y),fill=(0,0,0,int(alpha*1.6)))
 d.text((85,62),'ORBITAL ATLAS',font=f(22),fill=(245,240,226,190))
 d.text((W-410,66),'ILLUSTRATION · STYLE TEST',font=f(17),fill=(245,240,226,180))
 if 1<t<3.4: words='ONE ORDINARY ROCK.'
 elif 3.65<t<6.5:words='AN EXTRAORDINARY DETAIL.'
 elif 7.4<t<10.3:words='LOOK CLOSER.'
 elif 12.8<t:words='FOLLOW THE EVIDENCE.'
 else:words=''
 if words:
  d.text((85,880),words,font=f(55),fill=(255,245,222,255),stroke_width=1)
  d.line((87,858,145,858),fill=(245,203,86,255),width=4)
 if 7.4<t<10.3:
  p=e((t-7.4)/.5);pts=[(W*.70,H*.50),(W*.79,H*.32),(W*.88,H*.32)]
  for i in range(2):
   a,b=pts[i],pts[i+1];q=max(0,min(1,p*2-i));d.line((a[0],a[1],a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q),fill=(250,221,142,220),width=2)
  if p>.95:d.text((W*.79,H*.275),'THE HIDDEN DETAIL',font=f(18),fill=(255,239,202,240))
 im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')
 return im
if __name__=='__main__':
 src=Image.open(R/'cinema.png').convert('RGB');sr=48000;time=np.arange(sr*15)/sr;rng=np.random.default_rng(9)
 # Air bed, low musical pulse, soft transition swells, tiny crystalline accents.
 audio=.024*np.sin(2*np.pi*55*time)+.012*np.sin(2*np.pi*82.41*time)
 noise=rng.normal(0,1,len(time));smooth=np.convolve(noise,np.ones(40)/40,mode='same');audio+=smooth*.025
 for start in [0,3.4,6.5,10.6,12.5]:
  u=time-start;sel=(u>=0)&(u<1);q=u[sel];audio[sel]+=.23*np.sin(2*np.pi*(78*q-26*q*q))*np.exp(-q*8)
  env=np.exp(-((time-start)/.19)**2);audio+=smooth*.18*env
 for start in [3.5,6.9,7.4]:
  u=time-start;sel=(u>=0)&(u<1.2);q=u[sel];audio[sel]+=.033*np.sin(2*np.pi*1318.5*q)*np.exp(-q*5)
 audio*=np.minimum(time/.3,1)*np.minimum((15-time)/.5,1)
 with wave.open(str(R/'cinema_sound.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(audio,-1,1)*32767).astype('<i2').tobytes())
 p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-i',str(R/'cinema_sound.wav'),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',str(R/'OA_cinematic_v2_15s.mp4')],stdin=subprocess.PIPE)
 for i in range(450):p.stdin.write(render(i/30,src).tobytes())
 p.stdin.close();assert p.wait()==0
 sheet=Image.new('RGB',(1920,1080))
 for i,t in enumerate([2,4.5,8.5,13.5]):sheet.paste(render(t,src).resize((960,540)),((i%2)*960,(i//2)*540))
 sheet.save(R/'cinema_contact.jpg')
