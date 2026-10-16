"""dynamics report: per-second picture motion (mean abs diff of 160x90 luma at 6 fps, caption band excluded) -> runs of low motion"""
import subprocess, sys, json, numpy as np
f=sys.argv[1]; out=sys.argv[2] if len(sys.argv)>2 else None
W,H,fps=160,72,6
p=subprocess.run(['ffmpeg','-loglevel','error','-i',f,'-vf',f'crop=iw:ih*0.76:0:0,scale={W}:{H},fps={fps},format=gray','-f','rawvideo','-'],capture_output=True)
a=np.frombuffer(p.stdout,np.uint8).reshape(-1,H,W).astype(np.float32)
d=np.abs(np.diff(a,axis=0)).mean((1,2))           # per 1/6 s
sec=[d[i*fps:(i+1)*fps].mean() for i in range(len(d)//fps)]
thr=0.35
runs=[];s=None
for i,v in enumerate(sec):
    if v<thr and s is None: s=i
    if v>=thr and s is not None:
        if i-s>=4: runs.append((s,i))
        s=None
if s is not None and len(sec)-s>=4: runs.append((s,len(sec)))
print('median motion',round(float(np.median(sec)),2),'mean',round(float(np.mean(sec)),2),'seconds<thr',sum(v<thr for v in sec),'of',len(sec))
print('low-motion runs >=4 s:',[(a_,b_) for a_,b_ in runs])
if out: json.dump(dict(sec=[round(float(x),3) for x in sec],runs=runs),open(out,'w'))
