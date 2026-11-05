#!/usr/bin/env python3
"""IceCube long-form assembly: shots.py + real Adam narration -> 1920x1080 30 fps H.264/AAC.

Each shot is rendered by its own FFmpeg process on the exact 30 fps frame grid (frame range from
the shot's absolute start/end), text overlays are one transparent PNG per shot (PIL, Inter), then
the segments are joined with the concat demuxer (no re-encode) and the narration + ambience are
muxed once. Timings are written to timings.json so slow stages are visible.

usage: assemble.py --media DIR --voice narration.wav --work DIR --out OUT.mp4 [--t0 S --t1 S] [-j 4]
"""
import argparse, json, os, subprocess, sys, time, hashlib
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shots import SHOTS, END

W, H, FPS = 1920, 1080, 30
FI = "/usr/share/fonts/opentype/inter/"
SRC = {"A01": "A01_cutaway.mp4", "A02": "A02_drill.mp4", "A03": "A03_detection.mp4", "A04": "A04_backtrace.mp4",
       "V01": "V01_antarctic_live_broll.webm", "V02": "V02_blazar.webm", "V03": "V03_particle_journey.webm",
       "V04": "V04_fermi.webm", "P01": "P01_icecube_station.jpg", "P02": "P02_sensor.jpg"}
NAVY = "0x0b1a2b"
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-profile:v", "high",
       "-r", str(FPS), "-g", "60", "-bf", "2", "-video_track_timescale", "15360", "-an"]


def frame(t):
    return int(round(t * FPS))


def shot_table():
    out = []
    for i, (t, kind, src, a, o) in enumerate(SHOTS):
        e = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else END
        out.append(dict(i=i, f0=frame(t), f1=frame(e), kind=kind, src=src, inp=a, o=o))
    return out


# ---------------------------------------------------------------- overlays (one PNG per shot)
def _font(name, size):
    return ImageFont.truetype(FI + name, size)


def _shadow_text(img, xy, text, font, fill, anchor):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0] + 3, xy[1] + 5), text, font=font, fill=(0, 0, 0, 200), anchor=anchor)
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    img.alpha_composite(sh)
    ImageDraw.Draw(img).text(xy, text, font=font, fill=fill, anchor=anchor, stroke_width=2, stroke_fill=(0, 0, 0, 255))


def overlay_png(items, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for it in items:
        if "tag" in it:  # credit pill, EP009 style (dark pill, Inter SemiBold)
            f = _font("Inter-SemiBold.otf", 22)
            d = ImageDraw.Draw(img)
            l, t, r, b = d.textbbox((0, 0), it["tag"], font=f)
            x, y = 40, 36
            d.rounded_rectangle([x, y, x + r - l + 28, y + b - t + 18], 10, fill=(10, 18, 34, 185))
            d.text((x + 14 - l, y + 9 - t), it["tag"], font=f, fill=(244, 238, 226, 255))
        if "big" in it:  # headline: channel style, uppercase Inter Black, yellow + white
            lines = it["big"]
            pos = it.get("pos", "tr")
            right = pos.endswith("r")
            x = W - 90 if right else 90
            y0 = 200 if pos.startswith("t") else H - 150 - 92 * (len(lines) - 1) - 40
            for k, (txt, col) in enumerate(lines):
                size = 84 if k == 0 else 50
                y = y0 + (0 if k == 0 else 100 + 66 * (k - 1))
                _shadow_text(img, (x, y), txt, _font("Inter-Black.otf", size), col, "ra" if right else "la")
    img.save(path)


# ---------------------------------------------------------------- per-shot FFmpeg graph
def motion(o, n):
    """zoompan on a 2x upscale: smoothstep zoom/centre, half-pixel steps at output size."""
    z0, z1 = o.get("z", (1.0, 1.0))
    c0 = o.get("c0", (0.5, 0.5)); c1 = o.get("c1", c0)
    if z0 == z1 == 1.0 and c0 == c1 == (0.5, 0.5):
        return ""
    u = f"(on/{max(n - 1, 1)})"; e = f"({u}*{u}*(3-2*{u}))"
    z = f"({z0}+({z1 - z0})*{e})"
    cx = f"({c0[0]}+({c1[0] - c0[0]})*{e})"; cy = f"({c0[1]}+({c1[1] - c0[1]})*{e})"
    x = f"max(0,min(iw-iw/zoom,{cx}*iw-iw/zoom/2))"; y = f"max(0,min(ih-ih/zoom,{cy}*ih-ih/zoom/2))"
    return (f",scale={2 * W}:{2 * H}:flags=lanczos,zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{H}:fps={FPS}")


def cover(label_in, label_out):
    return (f"[{label_in}]scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={W}:{H},setsar=1[{label_out}]")


def shot_cmd(s, media, work, voice_t0=None):
    n = s["f1"] - s["f0"]; dur = n / FPS; o = s["o"]
    src = os.path.join(media, SRC[s["src"]])
    args = ["ffmpeg", "-v", "error", "-y"]
    g = []
    if s["src"].startswith("P"):
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur + 0.5:.3f}", "-i", src]
        if o.get("contain"):  # whole photo, unmodified, on navy; the inset grows, never cropped
            z0, z1 = o.get("z", (1.0, 1.0))
            g.append(f"color=c={NAVY}:s={W}x{H}:r={FPS}:d={dur + 0.5:.3f}[bg]")
            u = f"min(1,t/{dur:.3f})"; e = f"({u}*{u}*(3-2*{u}))"
            hexp = f"trunc(1000*({z0}+({z1 - z0})*{e})/2)*2"
            g.append(f"[0:v]scale=-2:1120:flags=lanczos,fps={FPS},scale=w=-2:h='{hexp}':eval=frame:flags=lanczos[ph]")
            g.append("[bg][ph]overlay=x=(W-w)/2:y=(H-h)/2:eval=frame,setsar=1[v0]")
        else:
            g.append(cover("0:v", "c0")); g.append(f"[c0]fps={FPS}{motion(o, n)}[v0]")
    else:
        if o.get("rev"):
            a = max(0.0, s["inp"] - dur - 0.2)
            args += ["-ss", f"{a:.3f}", "-t", f"{s['inp'] - a:.3f}", "-i", src]
            pre = "reverse,"
        else:
            args += ["-ss", f"{s['inp']:.3f}", "-t", f"{dur + 0.5:.3f}", "-i", src]
            pre = ""
        if "split" in o:
            sb, ib = o["split"]
            args += ["-ss", f"{ib:.3f}", "-t", f"{dur + 0.5:.3f}", "-i", os.path.join(media, SRC[sb])]
            g.append(f"[0:v]fps={FPS},scale={W // 2}:{H}:force_original_aspect_ratio=increase,crop={W // 2}:{H},setsar=1[l]")
            g.append(f"[1:v]fps={FPS},scale={W // 2}:{H}:force_original_aspect_ratio=increase,crop={W // 2}:{H},setsar=1[r]")
            g.append(f"[l][r]hstack,drawbox=x={W // 2 - 2}:y=0:w=4:h={H}:color=0x0b1a2b:t=fill[v0]")
        else:
            conv = (f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" if o.get("mi") else f"fps={FPS}")
            g.append(f"[0:v]{pre}{conv}[r0]"); g.append(cover("r0", "c0")); g.append(f"[c0]null{motion(o, n)}[v0]")
    last = "v0"
    txt = list(o.get("txt", []))
    if "split" in o:
        txt.append({"big": [("NEUTRINO", "#FFD23F")], "pos": "bl"})
        txt.append({"big": [("GAMMA RAYS", "#FFFFFF")], "pos": "br"})
    if txt:
        png = os.path.join(work, f"ov_{s['i']:02d}.png"); overlay_png(txt, png)
        k = len([a for a in args if a == "-i"])
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur + 0.5:.3f}", "-i", png]
        fo = max(0.0, dur - 0.35)
        g.append(f"[{k}:v]format=rgba,fade=t=in:st=0.15:d=0.35:alpha=1,fade=t=out:st={fo:.3f}:d=0.3:alpha=1[t]")
        g.append(f"[{last}][t]overlay=0:0:format=auto[v1]"); last = "v1"
    if s["i"] == 0:  # first frame of the film: no fade-in, hook starts immediately
        pass
    if o.get("fadeout"):
        g.append(f"[{last}]fade=t=out:st={dur - o['fadeout']:.3f}:d={o['fadeout']}[v2]"); last = "v2"
    g.append(f"[{last}]format=yuv420p[out]")
    out = os.path.join(work, f"seg_{s['i']:02d}.mp4")
    args += ["-filter_complex", ";".join(g), "-map", "[out]", "-frames:v", str(n)] + ENC + [out]
    return args, out


def run_shot(s, media, work):
    args, out = shot_cmd(s, media, work)
    key = hashlib.sha256(json.dumps([args, s["f0"], s["f1"]]).encode()).hexdigest()
    keyf = out + ".key"
    if os.path.exists(out) and os.path.exists(keyf) and open(keyf).read() == key:
        return s["i"], 0.0, out  # unchanged shot: reuse the rendered segment
    t = time.time()
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"shot {s['i']}: {r.stderr[-1500:]}")
    got = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                              "stream=nb_read_frames", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip())
    if got != s["f1"] - s["f0"]:
        raise RuntimeError(f"shot {s['i']}: {got} frames, expected {s['f1'] - s['f0']}")
    open(keyf, "w").write(key)
    return s["i"], round(time.time() - t, 2), out


# ---------------------------------------------------------------- audio
def build_audio(voice, work, t0, t1, gain_db):
    """Narration (one constant gain) + quiet synthetic wind/low hum, original, no music."""
    dur = t1 - t0
    out = os.path.join(work, "mix.m4a")
    amb = (f"anoisesrc=color=brown:amplitude=0.6:seed=7:r=48000:d={dur + 1:.3f},lowpass=f=380,highpass=f=45,"
           f"volume='0.55+0.25*sin(2*PI*t/11)+0.15*sin(2*PI*t/4.3)':eval=frame,volume=-22dB,"
           f"afade=t=in:d=1.2,afade=t=out:st={max(0, dur - 1.5):.3f}:d=1.5[amb]")
    hum = f"sine=f=55:r=48000:d={dur + 1:.3f},volume=-44dB[hum]"
    vo = (f"[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,atrim=start={t0:.3f},asetpts=PTS-STARTPTS,"
          f"volume={gain_db:.2f}dB,alimiter=limit=0.79:attack=2:release=60:level=false,apad=whole_dur={dur:.3f}[vo]")
    g = ";".join([vo, amb, hum, "[vo][amb][hum]amix=inputs=3:normalize=0:duration=first,"
                  f"alimiter=limit=0.8:level=false,atrim=0:{dur:.3f}[a]"])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", voice, "-filter_complex", g, "-map", "[a]",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out], check=True)
    return out


def voice_gain(voice, target=-15.0):
    """gain toward target LUFS; peaks are held by the limiter in build_audio (ceiling -2 dBFS)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", voice, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    i = float(r.rsplit("I:", 1)[1].split("LUFS")[0]); tp = float(r.rsplit("Peak:", 1)[1].split("dBFS")[0])
    g = target - (i + 3.0)  # mono narration is played dual-mono: +3 LU when measured as stereo
    return g, i, tp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--media", required=True); ap.add_argument("--voice", required=True)
    ap.add_argument("--work", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--t0", type=float, default=0.0); ap.add_argument("--t1", type=float, default=END)
    ap.add_argument("-j", type=int, default=4)
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)
    T = {}; t = time.time()
    shots = [s for s in shot_table() if s["f1"] > frame(a.t0) and s["f0"] < frame(a.t1)]
    # a preview always uses whole shots, so the segment grid is identical to the full render
    t0, t1 = shots[0]["f0"] / FPS, shots[-1]["f1"] / FPS
    per = {}
    with ThreadPoolExecutor(a.j) as ex:
        heavy = sorted(shots, key=lambda s: (not s["o"].get("mi"), -(s["f1"] - s["f0"])))  # slow shots first
        for i, sec, _ in ex.map(lambda s: run_shot(s, a.media, a.work), heavy):
            per[i] = sec
    T["shots_wall_s"] = round(time.time() - t, 1); T["per_shot_s"] = per
    t = time.time()
    lst = os.path.join(a.work, "concat.txt")
    with open(lst, "w") as f:
        for s in shots:
            f.write(f"file 'seg_{s['i']:02d}.mp4'\n")
    vid = os.path.join(a.work, "video.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    T["concat_s"] = round(time.time() - t, 1); t = time.time()
    g, li, tp = voice_gain(a.voice)
    mix = build_audio(a.voice, a.work, t0, t1, g)
    T["audio_s"] = round(time.time() - t, 1); t = time.time()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", mix, "-map", "0:v", "-map", "1:a", "-c", "copy",
                    "-movflags", "+faststart", "-shortest", a.out], check=True)
    T["mux_s"] = round(time.time() - t, 1)
    T.update(range=[t0, t1], shots=len(shots), voice_lufs_in=li, voice_tp_in=tp, voice_gain_db=round(g, 2))
    json.dump(T, open(os.path.splitext(a.out)[0] + ".timings.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in T.items() if k != "per_shot_s"}, indent=1))
    slow = sorted(per.items(), key=lambda kv: -kv[1])[:5]
    print("slowest shots:", slow)


if __name__ == "__main__":
    main()
