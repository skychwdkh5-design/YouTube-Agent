#!/usr/bin/env python3
"""EP011 assembly: shots.py + real Adam narration -> 1920x1080 30 fps H.264/AAC.
usage: build.py sheet OUT.jpg            one frame per shot (contact sheet)
       build.py frames OUTDIR t1 t2 ...  single frames at absolute times
       build.py render WORK OUT.mp4 [-j 4] [--t0 S --t1 S]
       build.py thumb OUTDIR             three cover variants (A = frame 0 composition)"""
import json, math, os, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from paint import W, H, FPS, smooth, seg, grade
from shots import SHOTS, END
from scenes import SCENES
import cover_intro as CI

XF = 0.4  # crossfade into each shot (s); the first frame is never a blend
ROOT = os.path.join(HERE, "..")
VOICE = os.path.join(ROOT, "voice", "narration.wav")
BURSTS = [12.3, 266.7, 459.5]   # rumble cues (forest blast, section burst, final recap)


def shot_at(t):
    k = 0
    for i, s in enumerate(SHOTS):
        if s[0] <= t:
            k = i
    return k


def dur(i):
    return (SHOTS[i + 1][0] if i + 1 < len(SHOTS) else END) - SHOTS[i][0]


def scene_frame(i, t):
    st, name, p = SHOTS[i]
    return SCENES[name](t - st, dur(i), p)


def frame(n):
    t = n / FPS
    if t < CI.T_END:  # opening from the owner's cover v2; dissolves into the existing film at 11.5-12.0 s
        img = CI.frame(t)
        if t >= CI.XF0:
            img = Image.blend(img, film_frame(n), smooth((t - CI.XF0) / (CI.T_END - CI.XF0)))
        g = grade(img, vignette=0.28, grain_seed=n, grain=3.0)
        return Image.blend(img, g, smooth(seg(t, 0.6, 2.0)))  # frame 0 is the cover itself
    return film_frame(n)


def film_frame(n):
    t = n / FPS
    i = shot_at(t)
    img = scene_frame(i, t)
    if i > 0 and t - SHOTS[i][0] < XF and not SHOTS[i][2].get("cut"):
        u = smooth((t - SHOTS[i][0]) / XF)
        prev = scene_frame(i - 1, t)
        img = Image.blend(prev, img, u)
    return grade(img, vignette=0.28, grain_seed=n, grain=3.0)


def render_chunk(args):
    n0, n1, out = args
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
                          "-g", "60", "-bf", "2", "-video_track_timescale", "15360", out], stdin=subprocess.PIPE)
    t = time.time()
    for n in range(n0, n1):
        p.stdin.write(frame(n).tobytes())
    p.stdin.close()
    assert p.wait() == 0, out
    return out, n1 - n0, round(time.time() - t, 1)


def build_audio(work, t0, t1):
    """narration (constant gain toward -15 LUFS integrated) + quiet original wind bed + low rumble at the blasts. No music."""
    d = t1 - t0
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", VOICE, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    li = float(r.rsplit("I:", 1)[1].split("LUFS")[0])
    g = -15.0 - (li + 3.0)
    rumble = "".join(f"+0.9*exp(-((t-{b}-1.2)/1.6)^2)" for b in BURSTS if t0 <= b <= t1)
    amb = (f"anoisesrc=color=brown:amplitude=0.6:seed=11:r=48000:d={d + 1:.3f},lowpass=f=420,highpass=f=40,"
           f"volume='0.5+0.2*sin(2*PI*t/13)+0.12*sin(2*PI*t/5.1)':eval=frame,volume=-24dB,afade=t=in:d=1.0,afade=t=out:st={max(0, d - 2):.3f}:d=2[amb]")
    rum = (f"anoisesrc=color=brown:amplitude=0.9:seed=5:r=48000:d={d + 1:.3f},lowpass=f=110,"
           f"volume='0{rumble}':eval=frame,volume=-8dB[rum]")
    vo = (f"[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,atrim=start={t0:.3f},asetpts=PTS-STARTPTS,volume={g:.2f}dB,"
          f"alimiter=limit=0.79:attack=2:release=60:level=false,apad=whole_dur={d:.3f}[vo]")
    out = os.path.join(work, "mix.m4a")
    graph = ";".join([vo, amb, rum, f"[vo][amb][rum]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.8:level=false,atrim=0:{d:.3f}[a]"])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VOICE, "-filter_complex", graph, "-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out], check=True)
    return out, li, g


def render(work, out, j=4, t0=0.0, t1=END):
    os.makedirs(work, exist_ok=True)
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    step = 300
    chunks = [(a, min(a + step, n1), os.path.join(work, f"c_{a:06d}.mp4")) for a in range(n0, n1, step)]
    t = time.time()
    with ProcessPoolExecutor(j) as ex:
        res = list(ex.map(render_chunk, chunks))
    lst = os.path.join(work, "concat.txt")
    open(lst, "w").write("".join(f"file '{os.path.basename(c[2])}'\n" for c in chunks))
    vid = os.path.join(work, "video.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    mix, li, g = build_audio(work, n0 / FPS, n1 / FPS)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", mix, "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", "-shortest", out], check=True)
    info = dict(frames=n1 - n0, wall_s=round(time.time() - t, 1), voice_lufs_in=li, voice_gain_db=round(g, 2), chunks=len(chunks))
    json.dump(info, open(os.path.splitext(out)[0] + ".timings.json", "w"), indent=1)
    print(json.dumps(info))


def sheet(out):
    tiles = []
    for i, s in enumerate(SHOTS):
        t = s[0] + min(dur(i) * 0.6, dur(i) - 0.1)
        tiles.append(frame(int(t * FPS)).resize((384, 216)))
    cols = 6; rows = math.ceil(len(tiles) / cols)
    o = Image.new("RGB", (384 * cols, 216 * rows))
    for k, im in enumerate(tiles):
        o.paste(im, ((k % cols) * 384, (k // cols) * 216))
    o.save(out, quality=88)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "sheet":
        sheet(a[1])
    elif a[0] == "frames":
        os.makedirs(a[1], exist_ok=True)
        for x in a[2:]:
            frame(int(round(float(x) * FPS))).save(os.path.join(a[1], f"f_{float(x):07.2f}.jpg"), quality=90)
    elif a[0] == "render":
        kw = dict(j=4)
        if "-j" in a: kw["j"] = int(a[a.index("-j") + 1])
        if "--t0" in a: kw["t0"] = float(a[a.index("--t0") + 1])
        if "--t1" in a: kw["t1"] = float(a[a.index("--t1") + 1])
        render(a[1], a[2], **kw)
