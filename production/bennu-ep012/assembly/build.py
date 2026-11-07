#!/usr/bin/env python3
"""EP012 Bennu assembly: shots.py + owner's silent NASA clips + real Adam narration -> 1920x1080 30 fps H.264/AAC.
usage: BENNU_SRC=<silent dir> build.py frames OUTDIR t1 t2 ...   single frames at film times
       BENNU_SRC=... build.py sheet OUT.jpg                     one frame per shot
       BENNU_SRC=... build.py render WORK OUT.mp4 [-j 4] [--t0 S --t1 S]
       build.py audio WORK                                      narration + bed only"""
import json, math, os, subprocess, sys, time, wave
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from paint import W, H, FPS, smooth, seg, lerp, grade, clamp
from timeline import V, END, VOICE, SEGMENTS, _starts, word
import clips as C
import scenes as SC
from shots import SHOTS, EV, CONTACT_FILE_T
FIRST_HUD = min(s["t0"] for s in SHOTS if s.get("hud") is True)

XF = 0.4
ACC = {"y": SC.YEL, "r": (255, 120, 100, 255), None: None}
_R = {}


def reader(key, sid):
    r = _R.get(key)
    if r is None:
        r = _R[key] = C.Reader(sid)
    return r


def gc_readers(i):
    for k in list(_R):
        if k[0] < i - 1:
            _R.pop(k).close()


def shot_at(t):
    k = 0
    for i, s in enumerate(SHOTS):
        if s["t0"] <= t + 1e-9:
            k = i
    return k


def u_of(s, t):
    return (t - s["t0"]) / (s["t1"] - s["t0"])


def src_t(s, t):
    return s["a"] + clamp(u_of(s, t), 0, 1) * (s["b"] - s["a"])


def rate(s):
    return (s["b"] - s["a"]) / (s["t1"] - s["t0"])


def center(s, ts, u):
    if "track" in s:
        tr = s["track"]
        xs = [p[0] for p in tr]
        return float(np.interp(ts, xs, [p[1] for p in tr])), float(np.interp(ts, xs, [p[2] for p in tr]))
    return s.get("fc", (None, None))


def base_clip(i, t, role="m"):
    s = SHOTS[i]
    ts = src_t(s, t)
    arr = reader((i, role), s["src"]).get(ts)
    u = clamp(u_of(s, t))
    z0, z1 = s.get("zoom", (1.0, 1.0))
    z = lerp(z0, z1, smooth(u))
    cx, cy = center(s, ts, u)
    if s.get("fit") == "fit":
        img = C.frame_fit(arr, region=s.get("region"), zoom=z, fcx=cx, fcy=cy)
    else:
        img = C.frame_fill(arr, cx, cy, z, s.get("region"))
    return img.convert("RGBA"), ts


def same_prev(i, key):
    return i > 0 and SHOTS[i - 1].get(key) == SHOTS[i].get(key) and SHOTS[i].get(key) is not None


def overlays(i, t, img, ts=None):
    s = SHOTS[i]
    st = s["t0"]
    lab = s.get("label")
    if lab:
        a = 1.0 if same_prev(i, "label") else SC.fade(t, st + 0.15)
        SC.type_label(img, lab[0], lab[1], a)
    if s.get("credit"):
        SC.credit(img, s["credit"], 1.0 if same_prev(i, "credit") else SC.fade(t, st + 0.3), top=bool(s.get("hud")))
    for c in s.get("callouts", []):
        if c[0] == "ring":
            SC.ring(img, c[1], c[2], c[3], SC.fade(t, c[4]))
    chips = sorted(s.get("chips", []), key=lambda c: c[0])
    for k, c in enumerate(chips):
        tc, text, x, y, size, acc = c[:6]
        nxt = [c2[0] for c2 in chips[k + 1:] if c2[3] == y]
        end = nxt[0] if nxt else s["t1"] + 0.6
        SC.chip(img, text, x, y, SC.fade(t, tc, end, 0.3, 0.25), size, ACC[acc], anchor=c[6] if len(c) > 6 else "c")
    h = s.get("hud")
    if h:
        prev_h = i > 0 and SHOTS[i - 1].get("hud")
        a = 1.0 if prev_h else SC.fade(t, st + 0.1)
        shown = sum(1 for e in EV if t >= e)
        T = None if h == "noclock" or ts is None else ts - CONTACT_FILE_T
        # the "approx. time from contact" note is shown once, in the first timer shot only
        SC.hud(img, T, shown, rate(s), a, playhead=T is not None, note=SC.fade(t, FIRST_HUD + 0.3, FIRST_HUD + 5.0, 0.4, 0.6))


def open_frame(i, t):
    """frame 0 = the cover composition; the real SamCam sequence starts moving immediately."""
    s = SHOTS[i]
    ts = src_t(s, t)
    arr = reader((i, "m"), s["src"]).get(ts)
    u = t - s["t0"]
    slide = smooth(seg(u, 0.9, 2.1))
    img = C.frame_fit(arr, cx_out=lerp(1190, 960, slide), zoom=lerp(1.0, 1.08, smooth(seg(u, 0, s["t1"] - s["t0"]))), fcx=500, fcy=600)
    w = 1 - smooth(seg(u, 0.5, 1.7))
    if w > 0.001:
        img = Image.blend(img, duotone(img), w)
    img = img.convert("RGBA")
    ah = 1 - smooth(seg(u, 0.85, 1.35))
    if ah > 0.001:
        cover_text(img, ah, lerp(1190, 960, slide))
    SC.type_label(img, "real", "SAMCAM · STILL PHOTOS, SPED UP", SC.fade(t, 1.2))
    SC.credit(img, s["credit"], SC.fade(t, 1.4))
    return img


def duotone(img):
    a = np.asarray(img.convert("L")).astype(np.float32) / 255.0
    a = np.clip((a - 0.04) * 1.25, 0, 1) ** 0.85
    stops = [(0.0, (6, 14, 44)), (0.28, (100, 50, 20)), (0.6, (230, 138, 36)), (0.85, (255, 204, 100)), (1.0, (255, 240, 196))]
    out = np.zeros(a.shape + (3,), np.float32)
    ps = [p for p, _ in stops]
    for ch in range(3):
        out[..., ch] = np.interp(a, ps, [c[ch] for _, c in stops])
    return Image.fromarray(out.astype(np.uint8), "RGB")


def cover_text(img, alpha, pic_cx):
    from paint import font, shadow_text
    a = int(255 * alpha)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow_text(lay, (64, 50), "STILL", font("Inter-Black.otf", 290), (255, 255, 255, 255), "la", stroke=10, blur=16)
    shadow_text(lay, (64, 350), "SINKING", font("Inter-Black.otf", 222), (255, 204, 40, 255), "la", stroke=10, blur=16)
    hx = pic_cx - 960 + 1146
    SC.arrow(lay, (hx + 175, 300), (hx + 175, 620), 1.0, (229, 50, 45, 255), width=40, head=90)
    SC._pill(lay, 74, 640, "OCT 20, 2020", 64, wt="Inter-Black.otf", bg=(10, 14, 30, 225), pad=(30, 18), radius=18)
    if alpha < 0.999:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(lay)


_BA = {}


def ba_frames():
    if not _BA:
        r = C.Reader("M10")
        _BA["before"] = r.get(0.5).copy(); _BA["after"] = r.get(1.5).copy(); r.close()
    return _BA["before"], _BA["after"]


def ba_frame(i, t):
    s = SHOTS[i]
    before, after = ba_frames()
    w = smooth(seg(t, s["t_after"], s["t_after"] + 0.3))  # 0 = before, 1 = after
    if s["t_flip"] <= t < s["t_moved"] + 0.6:
        k = int((t - s["t_flip"]) / 0.7)
        ph = (t - s["t_flip"]) / 0.7 - k
        w = (1 - smooth(seg(ph, 0, 0.2))) if k % 2 == 0 else smooth(seg(ph, 0, 0.2))
    elif t >= s["t_moved"] + 0.6:
        w = smooth(seg(t, s["t_moved"] + 0.6, s["t_moved"] + 0.8)) if int((s["t_moved"] + 0.6 - s["t_flip"]) / 0.7) % 2 == 0 else 1.0
    z = lerp(1.07, 1.0, smooth(seg(t, s["t0"], s["t_ruler"])))
    reg = (74, 0, 1845, 1080)
    fb = C.frame_fit(before, region=reg, zoom=z)
    fa = C.frame_fit(after, region=reg, zoom=z)
    img = Image.blend(fb, fa, w).convert("RGBA")
    SC.chip(img, "BEFORE · MARCH 7, 2019", 960, 120, (1 - w) * SC.fade(t, s["t_before"]), 46, SC.YEL)
    SC.chip(img, "AFTER · APRIL 7, 2021", 960, 120, w * SC.fade(t, s["t_after"]), 46, SC.TEAL)
    SC.chip(img, "MATERIAL MOVED", 960, 230, SC.fade(t, s["t_moved"], s["t_ruler"]), 34)
    a = SC.fade(t, s["t_ruler"] + 0.2)
    if a > 0.01:
        # NASA's 10 m bar sits at x 1473-1776, y ~1012 in the source; at zoom 1 the picture is unshifted
        from PIL import ImageDraw
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        x1 = 1776; px10 = 1776 - 1473; x0 = x1 - px10 * 0.8; y = 918
        c = SC.YEL[:3] + (int(255 * a),)
        d.line([(x0, y), (x1, y)], fill=c, width=10)
        for xx in (x0, x1):
            d.line([(xx, y - 20), (xx, y + 20)], fill=c, width=8)
        img.alpha_composite(lay)
        SC._pill(img, (x0 + x1) / 2, y - 76, "8 m", 34, anchor="c", alpha=a, wt="Inter-Black.otf", fg=SC.YEL)
        SC.chip(img, "NASA: HOLLOW ≈ 8 m WIDE (≈ 26 FT)", 700, 900, a, 40, SC.YEL,
                sub="RULER SET FROM NASA'S 10 m SCALE BAR · SIZE ONLY, NOT POSITION")
    SC.type_label(img, "real", "SAME SITE, ~2 YEARS APART", SC.fade(t, s["t0"] + 0.15))
    SC.credit(img, "NASA/Goddard/University of Arizona", SC.fade(t, s["t0"] + 0.3), top=True)
    return img


def leak_frame(i, t):
    s = SHOTS[i]
    ts = src_t(s, t)
    arr = reader((i, "m"), s["src"]).get(ts)
    base = C.frame_fill(arr, 1290, 560, lerp(1.35, 1.45, smooth(clamp(u_of(s, t)))))
    img = SC.sc_leak(t, s["t0"], s["t1"] - s["t0"], s, base)
    SC.type_label(img, "real", "SPACECRAFT CAMERA · OCT 2020  +  INSET ILLUSTRATION", 1.0)
    SC.credit(img, s.get("credit", "NASA Goddard Space Flight Center"), 1.0)
    return img


SCENE_FN = {"signal": SC.sc_signal, "cross": SC.sc_cross, "release": SC.sc_release, "mass": SC.sc_mass,
            "chem": SC.sc_chem, "end": SC.sc_end}


def shot_frame(i, t, role="m"):
    s = SHOTS[i]
    k = s["kind"]
    if k == "clip":
        img, ts = base_clip(i, t, role)
        overlays(i, t, img, ts)
        return img
    if k == "open":
        return open_frame(i, t)
    if k == "ba":
        return ba_frame(i, t)
    if k == "leak":
        return leak_frame(i, t)
    return SCENE_FN[k](t, s["t0"], s["t1"] - s["t0"], s)


def frame(n):
    t = n / FPS
    i = shot_at(t)
    gc_readers(i)
    img = shot_frame(i, t)
    s = SHOTS[i]
    if i > 0 and t - s["t0"] < XF and not s.get("cut"):
        u = smooth((t - s["t0"]) / XF)
        prev = shot_frame(i - 1, t, "x")
        img = Image.blend(prev.convert("RGB"), img.convert("RGB"), u)
    return grade(img, vignette=0.20, grain_seed=n, grain=2.2)


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
    for k in list(_R):
        _R.pop(k).close()
    return out, n1 - n0, round(time.time() - t, 1)


# ---------------------------------------------------------------- audio
def build_audio(work, t0=0.0, t1=END):
    """narration in SEGMENTS order with silences inserted (no word is stretched or cut) + a quiet generated bed + two soft low hits.
    No music. The hits are sound design, never presented as a recording from Bennu."""
    sr = 48000
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", VOICE, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"], capture_output=True, check=True).stdout
    v = np.frombuffer(raw, np.float32)
    total = int(round(END * sr))
    out = np.zeros(total, np.float32)
    for (a_, b_, _g), f0 in zip(SEGMENTS, _starts):
        a, b = int(round(a_ * sr)), min(len(v), int(round(b_ * sr)))
        dst = int(round(f0 * sr))
        seg_ = v[a:b]
        out[dst:dst + len(seg_)] += seg_[: max(0, total - dst)]
    vo_path = os.path.join(work, "vo_timed.wav")
    _wav(vo_path, out, sr)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", vo_path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    li = float(r.rsplit("I:", 1)[1].split("LUFS")[0])
    g = -15.0 - (li + 2.6)
    hits = [V(word("touch the surface,")) + 0.25, V(word("touches Nightingale.")) + 0.3]
    hit = "".join(f"+1.0*exp(-((t-{h:.3f})/0.35)^2)" for h in hits)
    d = END
    graph = ";".join([
        f"[0:a]aresample={sr},pan=stereo|c0=c0|c1=c0,volume={g:.2f}dB,alimiter=limit=0.89:attack=2:release=60:level=false[vo]",
        f"anoisesrc=color=brown:amplitude=0.5:seed=7:r={sr}:d={d + 1:.3f},lowpass=f=300,highpass=f=35,"
        f"volume='0.55+0.25*sin(2*PI*t/17)+0.1*sin(2*PI*t/6.3)':eval=frame,volume=-31dB,afade=t=in:d=1.5,afade=t=out:st={d - 3:.3f}:d=3,pan=stereo|c0=c0|c1=c0[bed]",
        f"anoisesrc=color=brown:amplitude=0.9:seed=3:r={sr}:d={d + 1:.3f},lowpass=f=90,volume='0{hit}':eval=frame,volume=-12dB,pan=stereo|c0=c0|c1=c0[hit]",
        f"[vo][bed][hit]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.89:level=false,atrim={t0:.3f}:{t1:.3f},asetpts=PTS-STARTPTS[a]"])
    mix = os.path.join(work, "mix.m4a")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vo_path, "-filter_complex", graph, "-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-ar", str(sr), mix], check=True)
    return mix, li, g


def _wav(path, x, sr):
    y = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())


def render(work, out, j=4, t0=0.0, t1=END):
    os.makedirs(work, exist_ok=True)
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    step = 240
    chunks = [(a, min(a + step, n1), os.path.join(work, f"c_{a:06d}.mp4")) for a in range(n0, n1, step)]
    todo = [c for c in chunks if not os.path.exists(c[2])]
    t = time.time()
    with ProcessPoolExecutor(j) as ex:
        for r in ex.map(render_chunk, todo):
            print(r, flush=True)
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
        t = s["t0"] + min((s["t1"] - s["t0"]) * 0.6, s["t1"] - s["t0"] - 0.1)
        tiles.append(frame(int(t * FPS)).resize((384, 216)))
    cols = 6; rows = math.ceil(len(tiles) / cols)
    sh = Image.new("RGB", (cols * 384, rows * 216))
    for k, im in enumerate(tiles):
        sh.paste(im, ((k % cols) * 384, (k // cols) * 216))
    sh.save(out, quality=88)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "frames":
        od = sys.argv[2]; os.makedirs(od, exist_ok=True)
        for x in sys.argv[3:]:
            tt = float(x)
            frame(int(round(tt * FPS))).save(os.path.join(od, f"f_{tt:07.2f}.jpg"), quality=90)
            for k in list(_R):
                _R.pop(k).close()
    elif cmd == "sheet":
        sheet(sys.argv[2])
    elif cmd == "render":
        args = sys.argv[2:]
        j = int(args[args.index("-j") + 1]) if "-j" in args else 4
        t0 = float(args[args.index("--t0") + 1]) if "--t0" in args else 0.0
        t1 = float(args[args.index("--t1") + 1]) if "--t1" in args else END
        render(args[0], args[1], j, t0, t1)
    elif cmd == "audio":
        os.makedirs(sys.argv[2], exist_ok=True)
        print(build_audio(sys.argv[2]))
