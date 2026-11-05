import sys, subprocess, json, numpy as np
f = sys.argv[1]; w, h = int(sys.argv[2]), int(sys.argv[3])
pts = sorted(float(x) for x in subprocess.check_output(["ffprobe","-v","error","-select_streams","v","-show_entries","packet=pts_time","-of","csv=p=0",f]).split())
dp = np.diff(pts); r = {"frames": len(pts), "pts_dt_min": round(float(dp.min()),4), "pts_dt_max": round(float(dp.max()),4), "pts_irregular": int((np.abs(dp-1/30)>0.002).sum())}
p = subprocess.Popen(["ffmpeg","-v","error","-i",f,"-vf",f"scale={w//6}:{h//6},format=gray","-f","rawvideo","-"], stdout=subprocess.PIPE)
n = (w//6)*(h//6); prev = None; d = []
while True:
    b = p.stdout.read(n)
    if len(b) < n: break
    a = np.frombuffer(b, np.uint8).astype(np.float32)
    if prev is not None: d.append(float(np.abs(a-prev).mean()))
    prev = a
d = np.array(d); med = float(np.median(d)); r.update(zero_diff_frames=[round(i/30,2) for i in np.where(d<0.02)[0]][:30], n_zero=int((d<0.02).sum()), median_diff=round(med,3),
  max_jump=round(float(d.max()),2), max_jump_at=round(float(d.argmax())/30,2), big_jumps=[round(i/30,2) for i in np.where(d>med*5+2)[0]][:40])
print(json.dumps(r))
