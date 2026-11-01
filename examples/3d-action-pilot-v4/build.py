"""Build an original 15s 3D motion study. Needs g++, FFmpeg with libass/Flite, numpy."""
from pathlib import Path
import subprocess, wave, numpy as np
R=Path(__file__).resolve().parent
BEATS=[(0,.9,'One wheel.'),(1,2.7,'One ordinary rock.'),(3.6,6.5,'Then, a surprise inside.'),(7.5,9.2,'Wait. Rewind.'),(9.7,11.2,'Watch the wheel.'),(11.25,12.7,'The rock breaks.'),(12.9,15,'The hidden detail appears.')]
def stamp(t):
 h=int(t//3600);m=int(t//60)%60;s=int(t)%60;cs=round((t%1)*100);return f'{h}:{m:02d}:{s:02d}.{cs:02d}'
def setup():
 sr=48000;tt=np.arange(sr*15)/sr;audio=np.zeros(sr*15);rng=np.random.default_rng(4)
 for i,(start,end,txt) in enumerate(BEATS):
  p=R/f'line_{i}.txt';p.write_text(txt);wav=R/f'line_{i}.wav'
  subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i',f'flite=textfile={p}:voice=slt','-ar',str(sr),'-ac','1',str(wav)],check=True)
  with wave.open(str(wav)) as w:v=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
  available=int((end-start-.05)*sr)
  if len(v)>available:v=np.interp(np.linspace(0,len(v)-1,available),np.arange(len(v)),v)
  k=int(start*sr);audio[k:k+len(v)]+=v*.85
 noise=rng.normal(0,1,len(tt));air=np.convolve(noise,np.ones(25)/25,mode='same');audio+=.015*air
 for start in [0,2.2,3.67,4.2,5.7,9.2,10.7,12.5]:
  q=tt-start;sel=(q>=0)&(q<.5);u=q[sel];audio[sel]+=.16*np.sin(2*np.pi*(100*u-75*u*u))*np.exp(-u*14)
  audio+=air*.16*np.exp(-((tt-start)/.12)**2)
 for start in [4.3,5.8,12.8,13.4]:
  q=tt-start;sel=(q>=0)&(q<.6);u=q[sel];audio[sel]+=.025*np.sin(2*np.pi*1568*u)*np.exp(-u*9)
 sel=(tt>=7.7)&(tt<9.2);q=tt[sel]-7.7;audio[sel]+=.04*np.sin(2*np.pi*(150*q+170*q*q))+.10*air[sel]
 audio*=np.minimum((15-tt)/.25,1)
 with wave.open(str(R/'mix.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(audio,-.98,.98)*32767).astype('<i2').tobytes())
 header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,DejaVu Sans,28,&H00FFFFFF,&H00FFFFFF,&H00201A15,&H60000000,-1,0,0,0,100,100,0,0,1,1.4,1,2,40,40,40,1
Style: Label,DejaVu Sans,15,&H00E3EAF0,&H00FFFFFF,&H00201A15,&H60000000,-1,0,0,0,100,100,1,0,1,0.7,0,7,35,35,25,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
 lines=[header]
 for a,b,txt in BEATS:lines.append(f'Dialogue: 2,{stamp(a)},{stamp(b)},Caption,,0,0,0,,{{\\fad(70,70)}}{txt}\n')
 lines.append('Dialogue: 3,0:00:00.00,0:00:15.00,Label,,0,0,0,,ORBITAL ATLAS\n')
 lines.append('Dialogue: 3,0:00:00.00,0:00:15.00,Label,,0,0,0,,{\\an9\\pos(1240,27)\\fs13}ILLUSTRATION / 3D MOTION TEST\n')
 lines.append('Dialogue: 3,0:00:07.70,0:00:09.20,Label,,0,0,0,,{\\an8\\pos(640,80)\\fs22}◀◀◀  REWIND\n')
 (R/'captions.ass').write_text(''.join(lines))
def build():
 setup();subprocess.run(['g++','-O3','-std=c++17',str(R/'render3d.cpp'),'-o',str(R/'render3d')],check=True)
 renderer=subprocess.Popen([str(R/'render3d'),'0','450'],stdout=subprocess.PIPE)
 try:
  subprocess.run(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','30','-i','-','-i',str(R/'mix.wav'),'-vf',f'ass={R}/captions.ass','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',str(R/'OA_3D_action_v4_15s.mp4')],stdin=renderer.stdout,check=True)
 finally:renderer.stdout.close()
 assert renderer.wait()==0
if __name__=='__main__':build()
