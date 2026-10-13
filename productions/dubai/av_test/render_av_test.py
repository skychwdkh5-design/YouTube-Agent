#!/usr/bin/env python3
"""EP002 Dubai 55-second audio-visual test: locked passage H1-A1, real ElevenLabs narration (Adam), provider word timings,
Motion Design v2 components. Video 1920x1080 30 fps H.264, AAC 48 kHz stereo, burned-in English subtitles.
Run from the repo root:
  python3 productions/dubai/av_test/render_av_test.py OUT.mp4 [--frames 3,12 --png DIR] [--ui-check]
Inputs (local, not committed): narration wav and voice.json in productions/dubai/visuals/_local_assets/audio/.
Every visual cue is bound to a spoken word through the provider timings; nothing is estimated."""
import sys, os, json, subprocess, argparse, multiprocessing as mp
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "motion")); sys.path.insert(0, os.path.join(HERE, "..", "motion", "engine"))
import numpy as np
import poc_c1_v2 as P                          # approved v2 scene: rotated palm2, anchors, markers
from motionlib import *
import motionlib as M, av

AUD = "productions/dubai/visuals/_local_assets/audio/"; WOC = "productions/dubai/visuals/_local_assets/woc/dubai_ast_%s_cyl.jpg"
voice = json.load(open(AUD+"narration_H1_A1.voice.json")); words = voice["words"]; DUR = voice["duration"]
T0, TOTAL, FPS = 2.5, 55.2, 30
tr = av.Transcript(words, T0)
def rotimg(p): return Image.open(p).convert("RGB").transpose(Image.ROTATE_270)           # 90 degrees clockwise: (x,y)->(H-y,x)
img00, img03, imgiss = rotimg(WOC % "20001111"), rotimg(WOC % "20031104"), rotimg("productions/dubai/visuals/iss067e003785_lrg.jpg")
pyr00, pyr03, pyri = Pyramid(img00), Pyramid(img03), Pyramid(imgiss); pyr06 = P.pyr
# ---- cue times from the spoken words ----
c1 = tr.start("November", 2)-0.08; c2 = tr.start("More than")-0.08; c3 = tr.start("So how")-0.08; c4 = tr.start("year 2000")-0.10
t_pull = tr.start("And what happened"); t_this = tr.start("This is Dubai"); t_put = tr.start("put that idea")
CAM = [SplineCam([(0, 1370, 390, 560), (c1, 1370, 390, 470)], (3000, 3000)), SplineCam([(c1, 1370, 390, 470), (c2, 1370, 390, 440)], (3000, 3000)),
       SplineCam([(c2, 3656, 1955, 900), (tr.start("stand out"), 3656, 1955, 880), (tr.end("orbit.")+0.1, 2152, 1626, 900), (c3, 2152, 1626, 890)], (4928, 2768)),
       SplineCam([(c3, 1622, 1399, 470), (t_pull, 1622, 1399, 430), (t_pull+1.5, 1800, 1400, 1250), (t_pull+3.5, 1898, 1380, 2136), (c4, 1898, 1380, 2100)], P.SIZE),
       SplineCam([(c4, 1500, 1500, 1688), (TOTAL, 1500, 1500, 1560)], (3000, 3000))]
PYR = [pyr00, pyr03, pyri, pyr06, pyr00]
def shot(t): return 0 if t < c1 else 1 if t < c2 else 2 if t < c3 else 3 if t < c4 else 4
SRC = {0: "NASA ASTER (Terra) · 11 Nov 2000 · colours as published · view rotated 90° for display",
       1: "NASA ASTER (Terra) · 4 Nov 2003 · colours as published · view rotated 90° for display",
       2: "NASA ISS astronaut photograph ISS067-E-3785 · 6 Apr 2022 · Nikon D4 · cropped and contrast-enhanced by NASA · view rotated 90°",
       3: "NASA ASTER (Terra) · 18 Sep 2006 · colours as published · view rotated 90° for display",
       4: "NASA ASTER (Terra) · 11 Nov 2000 · colours as published · view rotated 90° for display"}
CUES = av.build_cues(words); CHK = av.check_cues(CUES, words)
F_TICK, F_CAP = font(96, True), font(20)
BR_JU, BR_JA = (3383, 1675, 3928, 2235), (1823, 1264, 2481, 1988)       # ISS rotated px: palm bboxes read in verified crops, +50 px
def src_line(ui, t, k, t_in):
    s = SRC[k]; text_kinetic(ui, (W-40-text_width(s, font(16)), 38), s, font(16), TEXT, t, t_in, dur=0.5, per=0.003, shadow=True, group="src")

def base_img(k, t):
    v = CAM[k].view(t); return paste_image(depth_background(PYR[k], v, 0.22), PYR[k], v)

def render(t, ui_only=False):
    ui_reset(); k = shot(t); cam = CAM[k]; v = cam.view(t); ks = [t]
    amb = Stroke(AMBER); amb_g = Stroke(AMBER); ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ui_t = lambda *a, **kw: text_kinetic(ui, *a, **kw)
    ui_t((W-40-text_width("AUDIO-VISUAL TEST · NOT FINAL", font(16)), 14), "AUDIO-VISUAL TEST · NOT FINAL", font(16), AMBER, t, 0.3, dur=0.3, per=0.004, group="tag")
    src_line(ui, t, k, [0.8, c1, c2, c3, c4][k]+0.1)
    if k == 0:
        ui_t((96, 52), "2000", F_TICK, TEXT, t, tr.start("2000"), per=0.06, shadow=True, group="tick", out_t=c1-0.2)
        chip(ui, (96, 176), "SATELLITE: ASTER ON NASA'S TERRA", font(22), t, tr.start("satellite"), out_t=c1-0.25, group="chip")
    elif k == 1:
        ui_t((96, 52), "2003", F_TICK, TEXT, t, c1+0.05, per=0.06, shadow=True, group="tick")
        chip(ui, (96, 176), "2000 → 2003 · THREE YEARS", font(22), t, tr.start("three years"), group="chip")
    elif k == 2:
        ui_t((96, 52), "2022", F_TICK, TEXT, t, tr.start("decades"), per=0.06, shadow=True, group="tick")
        chip(ui, (96, 176), "ASTRONAUT PHOTOGRAPH · NOT SATELLITE IMAGERY", font(22), t, tr.start("astronaut"), group="chip", accent=AMBER)
        for rect, tin in ((BR_JU, tr.start("palm-shaped")), (BR_JA, tr.start("islands stand"))):
            a, b = v.pt((rect[0], rect[1])), v.pt((rect[2], rect[3])); brackets(amb, (a[0], a[1], b[0], b[1]), 64, 4.0, out_cubic(seg(t, tin, tin+0.3)), out_cubic(seg(t, tin, tin+0.5)))
    elif k == 3:
        title_plate(ui, (96, 470), "DUBAI COAST", font(44, True), t, t_this, out_t=c4-0.4, group="title")
        chip(ui, (96, 550), "UNITED ARAB EMIRATES · PERSIAN GULF · SEPTEMBER 2006", font(22), t, t_this+0.4, out_t=c4-0.4, group="sub")
        for j, key in enumerate(("JA", "JU", "W", "DE")):
            tin = t_put+0.18*j; sp = v.pt(P.ANCH[key]); a = out_cubic(seg(t, tin, tin+0.4))
            if a > 0: amb_g.ring(sp, lerp(10, 40, out_cubic(seg(t, tin, tin+1.0))), 2.8, 0.95*a*(1-0.5*seg(t, tin+0.3, tin+1.0))); amb_g.dot(sp, 5.5, a)
    else:
        ui_t((96, 52), "2000", F_TICK, TEXT, t, c4+0.05, per=0.06, shadow=True, group="tick")
        tc = tr.end("year 2000")+0.35
        for i, s in enumerate(("Image credits: NASA Earth Observatory · ASTER on NASA's Terra satellite (World of Change; Palm Islands, Dubai)",
                               "NASA ISS Crew Earth Observations · astronaut photograph ISS067-E-3785")):
            chip(ui, ((W-text_width(s, F_CAP)-40)/2, 960+i*48), s, F_CAP, t, tc+0.2*i, accent=CYAN, group="cred%d" % i, pad=10)
    if any(c["t0"]+T0 <= t <= c["t1"]+T0 for c in CUES): UIREG.append(("subs", 360, 905, 1560, 1035, 1.0))
    if ui_only: return None
    n = 1
    if k == 3:
        spd = cam.speed(t); n = 1 if spd < 6 else min(11, 2+int((spd-6)/5))
    if n == 1: base = base_img(k, t)
    else:
        subs = [base_img(k, t+(i/(n-1)-0.5)*0.4/FPS) for i in range(n)]; base = subs[0]
        for i, s in enumerate(subs[1:], 2): base = Image.blend(base, s, 1/i)
    frame = base.convert("RGBA")
    for L, glow in ((amb_g, 0.35), (amb, 0.3)):
        r = L.finish(glow, 6, None)
        if r is not None: frame = Image.alpha_composite(frame, r)
    frame = Image.alpha_composite(frame, ui).convert("RGB")
    f = smooth(seg(t, 0.0, 1.0))*(1-smooth(seg(t, TOTAL-1.2, TOTAL-0.05)))
    return frame if f >= 1 else Image.blend(Image.new("RGB", (W, H)), frame, f)

def ui_check(step=0.1):
    bad = []
    for i in range(int(TOTAL/step)+1):
        t = i*step; render(t, ui_only=True); R = [r for r in UIREG if r[5] > 0.35]
        for a in range(len(R)):
            for b in range(a+1, len(R)):
                A, B = R[a], R[b]
                if A[0] == B[0]: continue
                ox = min(A[3], B[3])-max(A[1], B[1]); oy = min(A[4], B[4])-max(A[2], B[2])
                if ox > 4 and oy > 4: bad.append((round(t, 2), A[0], B[0], round(ox), round(oy)))
        for g, x0, y0, x1, y1, a in R:
            if g != "subs" and (x0 < 8 or y0 < 8 or x1 > W-8 or y1 > H-8): bad.append((round(t, 2), g, "outside-safe"))
    return bad

def _r(i): return render(i/FPS).tobytes()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("out", nargs="?"); ap.add_argument("--frames"); ap.add_argument("--png"); ap.add_argument("--ui-check", action="store_true"); ap.add_argument("--mastered"); ap.add_argument("--ass")
    a = ap.parse_args()
    if a.ui_check: b = ui_check(); print("collisions:", b if b else "none"); sys.exit(0)
    if a.frames:
        os.makedirs(a.png, exist_ok=True)
        for s in a.frames.split(","): render(float(s)).save(f"{a.png}/f_{float(s):06.2f}.png")
        sys.exit(0)
    N = int(round(TOTAL*FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", a.mastered,
                           "-vf", f"subtitles={a.ass}", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", str(TOTAL), a.out], stdin=subprocess.PIPE)
    with mp.Pool(4) as pool:
        for b in pool.imap(_r, range(N), chunksize=3): ff.stdin.write(b)
    ff.stdin.close(); ff.wait(); print("frames", N, "rc", ff.returncode)
