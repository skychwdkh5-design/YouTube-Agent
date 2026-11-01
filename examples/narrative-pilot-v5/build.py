"""Narrative v5: original 3D explanation + verified NASA photograph. No paid API."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import subprocess, numpy as np, math, wave, hashlib, urllib.request
R=Path(__file__).resolve().parent;W,H,FPS=1280,720,30
ASSET_URL='https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/pia26/pia26309/PIA26309.jpg'
BEATS=[(0,2.1,'Yellow crystals. On Mars.'),(2.15,3.12,'What exposed them?'),(3.12,4.0,'Rewind.'),(4.1,6.45,'Curiosity drove over a rock.'),(6.6,8.8,'And cracked it open.'),(9.0,11.2,'Inside: elemental sulfur.'),(11.5,15,'This is the actual Mastcam image.')]
def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
def font(n):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',n)
def setup():
 sr=48000;tt=np.arange(sr*15)/sr;audio=np.zeros(sr*15);rng=np.random.default_rng(5)
 for i,(start,end,txt) in enumerate(BEATS):
  p=R/f'line_{i}.txt';p.write_text(txt);wav=R/f'line_{i}.wav'
  subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i',f'flite=textfile={p}:voice=slt','-ar',str(sr),'-ac','1',str(wav)],check=True)
  with wave.open(str(wav)) as w:v=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
  available=int((end-start-.04)*sr)
  if len(v)>available:v=np.interp(np.linspace(0,len(v)-1,available),np.arange(len(v)),v)
  k=int(start*sr);audio[k:k+len(v)]+=v*.82
 noise=rng.normal(0,1,len(tt));air=np.convolve(noise,np.ones(25)/25,mode='same');audio+=air*.014
 for start in [0,2.15,3.12,4,5.6,6.6,7.1,9.0,11.3]:
  q=tt-start;sel=(q>=0)&(q<.5);u=q[sel];audio[sel]+=.14*np.sin(2*np.pi*(100*u-70*u*u))*np.exp(-u*14)
  audio+=air*.14*np.exp(-((tt-start)/.10)**2)
 sel=(tt>=3.12)&(tt<4);q=tt[sel]-3.12;audio[sel]+=.045*np.sin(2*np.pi*(220*q+240*q*q))+.10*air[sel]
 for start in [0.1,7.15,9.15,11.6]:
  q=tt-start;sel=(q>=0)&(q<.6);u=q[sel];audio[sel]+=.028*np.sin(2*np.pi*1318*u)*np.exp(-u*8)
 audio*=np.minimum((15-tt)/.25,1)
 with wave.open(str(R/'mix.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(audio,-.98,.98)*32767).astype('<i2').tobytes())
def photo_frame(photo,t):
 sw,sh=photo.size
 # Preserve original color: only crop/scale, with annotations on a separate layer.
 if t<3.1:
  cw=1450-90*ease(t/3.1);cx=900;cy=820;ch=cw*H/W
  return photo.crop((cx-cw/2,cy-ch/2,cx+cw/2,cy+ch/2)).resize((W,H),Image.Resampling.LANCZOS)
 # Full photograph retreats into a clear evidence frame, revealing context.
 q=ease((t-11.3)/1.3);h=850-(850-560)*q;w=h*sw/sh
 im=Image.new('RGB',(W,H),(15,23,28));p=photo.resize((int(w),int(h)),Image.Resampling.LANCZOS)
 x=int((W-w)/2);y=int((H-h)/2)-12;im.paste(p,(x,y));d=ImageDraw.Draw(im)
 if q>.92:
  d.rectangle((x-1,y-1,x+int(w),y+int(h)),outline=(137,149,148),width=1)
  d.text((65,238),'CURIOSITY',font=font(28),fill='#F3F0E2');d.text((65,278),'MASTCAM',font=font(18),fill='#88C9C4')
  d.text((65,321),'7 JUN 2024',font=font(17),fill='#C4CAC5');d.text((65,355),'PIA26309',font=font(17),fill='#C4CAC5')
 return im
def annotate(im,t):
 ov=Image.new('RGBA',(W,H));d=ImageDraw.Draw(ov)
 for y in range(95):
  a=int(145*(1-y/95)**2);d.line((0,y,W,y),fill=(8,17,22,a));d.line((0,H-y,W,H-y),fill=(8,17,22,a+20))
 d.text((32,25),'ORBITAL ATLAS',font=font(15),fill='#F1EEDC')
 is_photo=t<3.1 or t>=11.3
 label='ACTUAL MASTCAM IMAGE' if is_photo else 'ILLUSTRATION / SIMPLIFIED 3D'
 box=d.textbbox((0,0),label,font=font(13));d.text((W-32-box[2],27),label,font=font(13),fill='#E8E4D8')
 if is_photo:d.text((32,H-27),'NASA/JPL-Caltech/MSSS · PIA26309 · Color adjusted by mission team',font=font(12),fill='#E7E6DD')
 if 2.15<t<3.1:
  p=ease((t-2.15)/.35);d.arc((410,180,850,555),0,int(340*p),fill='#FFE29B',width=3)
 if 3.12<=t<4:
  for j in range(3):d.polygon([(520+j*70,70),(520+j*70,116),(487+j*70,93)],fill='#F4E6C7')
  for y in range(0,H,5):d.line((0,y,W,y),fill=(16,43,54,25))
 if 9<t<11.3:
  p=ease((t-9)/.32);x=int(65-25*(1-p));d.rounded_rectangle((x,112,x+118,228),8,fill=(18,30,34,225),outline='#DCC46A',width=2)
  d.text((x+44,126),'S',font=font(52),fill='#F3D975');d.text((x+17,195),'SULFUR',font=font(15),fill='#EBE9DC')
 for a,b,txt in BEATS:
  if a<=t<b:
   size=29;box=d.textbbox((0,0),txt,font=font(size));tw=box[2];d.text(((W-tw)/2,H-78),txt,font=font(size),fill='white',stroke_width=2,stroke_fill=(9,17,21,200))
 return Image.alpha_composite(im.convert('RGBA'),ov).convert('RGB')
def build():
 if not (R/'PIA26309.jpg').exists():urllib.request.urlretrieve(ASSET_URL,R/'PIA26309.jpg')
 photo=Image.open(R/'PIA26309.jpg').convert('RGB');assert photo.size==(1779,1590)
 setup();subprocess.run(['g++','-O3','-std=c++17',str(R/'render3d.cpp'),'-o',str(R/'render3d')],check=True)
 renderer=subprocess.Popen([str(R/'render3d'),'0','450'],stdout=subprocess.PIPE)
 enc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','30','-i','-','-i',str(R/'mix.wav'),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',str(R/'OA_story_v5_15s.mp4')],stdin=subprocess.PIPE)
 samples=[]
 for i in range(450):
  t=i/30;data=renderer.stdout.read(W*H*3);assert len(data)==W*H*3
  im=photo_frame(photo,t) if t<3.1 or t>=11.3 else Image.frombytes('RGB',(W,H),data)
  out=annotate(im,t);enc.stdin.write(out.tobytes())
  if i in [30,75,105,144,180,219,264,300,396]:samples.append(out)
 renderer.stdout.close();assert renderer.wait()==0;enc.stdin.close();assert enc.wait()==0
 sheet=Image.new('RGB',(W*3,H*3))
 for i,im in enumerate(samples):sheet.paste(im,((i%3)*W,(i//3)*H))
 sheet.resize((1920,1080)).save(R/'qa.jpg')
if __name__=='__main__':build()
