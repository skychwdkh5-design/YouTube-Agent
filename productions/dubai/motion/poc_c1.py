#!/usr/bin/env python3
"""EP002 Dubai motion proof of concept: scene C1 'Four projects, south to north' (20 s, silent).
Source: ASTER (Terra) 18 Sep 2006, productions/dubai/visuals/palm2.jpg. Outlines are traced from that file's own pixels.
Run from the repo root:  python3 productions/dubai/motion/poc_c1.py OUT.mp4 [--frames 2,5,9.5 --png DIR]
Cue times = word index / 2.42 words per second of the locked C1 narration (estimate until yt-voice timings exist).
No narration text is rendered; on-screen words are labels and NASA-status chips only."""
import sys, os, json, subprocess, argparse, multiprocessing as mp
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))
from motionlib import *
import trace as TR, validate as VA

SRC = "productions/dubai/visuals/palm2.jpg"
DUR, FPS = 20.0, 30
img = Image.open(SRC).convert("RGB"); SIZE = img.size
pyr = Pyramid(img); arr = np.asarray(img)
CAP = "NASA ASTER (Terra) · 18 Sep 2006 · colours as published"
CREDIT = "Image: NASA/GSFC/MITI/ERSDAC/JAROS, and U.S./Japan ASTER Science Team · NASA Earth Observatory"

# ---- traced outlines, checked against the source pixels ---------------------------------------------------------
polys_all, TINFO = TR.trace(SRC)
polys_all = [p for p in polys_all if not (p[:, 0].mean() < 1000 and p[:, 1].mean() < 420)]     # cloud corner, excluded
BOXES = {"JA": (290, 2890, 810, 3390), "JU": (1215, 1990, 1590, 2380), "W": (1230, 1100, 1760, 1640), "DE": (2200, 300, 2540, 790)}
PROJ = {}
for k, b in BOXES.items():
    kept, rep = VA.select_project(arr, polys_all, b)
    lens = np.array([VA.seglen(p) for p in kept]); cen = np.array([p.mean(axis=0) for p in kept])
    anchor = (cen*lens[:, None]).sum(0)/lens.sum()
    dist = np.hypot(*(cen-anchor).T); dist = dist/max(dist.max(), 1)
    PROJ[k] = dict(polys=kept, cums=[cumlen(p) for p in kept], anchor=anchor, rank=dist, report=rep,
                   valid=bool(rep["vertex_pass"] >= 0.7 and rep["kept_fraction_len"] >= 0.85))
SWEEP = [(p, cumlen(p)) for p in polys_all]
MAIN = [i for i, (p, c) in enumerate(SWEEP) if c[-1] > 2000]

# ---- camera -----------------------------------------------------------------------------------------------------
P_WIN, F_WIN = (150.0, 40.0, 809.0, 1000.0), (0.0, 0.0, 1920.0, 1080.0)
CX, CY = SIZE[0]/2, SIZE[1]/2
def kc(rect): return (rect[0]+rect[2]/2, rect[1]+rect[3]/2, rect[3])
JA, JU, WO, DE = kc((60, 2780, 1280, 720)), kc((915, 1905, 960, 540)), kc((878, 1000, 1280, 720)), kc((1700, 150, 1280, 720))
KEYS = [(0.0, P_WIN, CX, CY, 3797), (8.6, P_WIN, CX, CY, 3650), (9.6, F_WIN, *JA), (10.3, F_WIN, *JA), (11.2, F_WIN, *JU), (12.4, F_WIN, *JU),
        (13.4, F_WIN, *WO), (15.2, F_WIN, *WO), (16.2, F_WIN, *DE), (18.0, F_WIN, *DE), (18.9, P_WIN, CX, CY, 3797), (20.0, P_WIN, CX, CY, 3797)]
STOPS = {  # key: (outline t0, t1, title, title in, title out, status chip, chip in, chip out)
 "JA": (9.9, 10.8, "PALM JEBEL ALI", 9.5, 10.3, None, None, None),
 "JU": (11.2, 12.0, "PALM JUMEIRAH", 10.9, 12.5, "LARGELY COMPLETE AS LANDFORMS · 2006", 12.0, 13.1),
 "W": (13.4, 14.5, "THE WORLD", 13.3, 15.3, "UNDER CONSTRUCTION · 2006", 14.6, 15.4),
 "DE": (16.2, 17.1, "PALM DEIRA", 16.0, 18.0, "EARLIEST STAGES · 2006", 17.2, 18.0)}
PINS = [("JA", "01", "PALM JEBEL ALI", 5.4), ("JU", "02", "PALM JUMEIRAH", 6.6), ("W", "03", "THE WORLD", 7.4), ("DE", "04", "PALM DEIRA", 8.7)]
SWEEP_T = (1.7, 4.0); FLY_OUT = (8.4, 9.2); BACK = (18.0, 18.9)

def outline(cy_, view, key, p, width, alpha=1.0):
    pr = PROJ[key]
    for q, c, rk in zip(pr["polys"], pr["cums"], pr["rank"]):
        f = smoother((p - 0.45*rk)/0.55) if p < 1 else 1.0
        if f <= 0: continue
        pts, head = partial(q, c, f)
        cy_.line(view.pts(pts), width, alpha)
        if 0 < f < 1 and c[-1] > 400: cy_.dot(view.pt(head), 3.2, 0.95)

def render(t):
    v = camera_at(t, KEYS, SIZE); win = v.win
    base = depth_background(pyr, v); base = ImageChops.multiply(base, Image.merge("RGB", [vignette()]*3))
    fullness = (win[2]*win[3])/(W*H)
    if fullness < 0.9: base = window_shadow(base, win, 0.7*(1-clamp((fullness-0.4)/0.5)))
    sw, sh = int(round(win[2])), int(round(win[3]))
    base.paste(pyr.render(v.crop, (sw, sh)), (int(round(win[0])), int(round(win[1]))))
    cyan, amb_g, amb_u = Stroke(CYAN), Stroke(AMBER), Stroke(AMBER)
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    panel = clamp(1 - smooth(seg(t, *FLY_OUT)) + smooth(seg(t, *BACK)))      # 1 while the framed panel is on screen
    # --- traced coast sweep (south -> north) ---
    if t >= SWEEP_T[0]:
        ys = lerp(SIZE[1]+40, -40, smoother(seg(t, *SWEEP_T))); a = 1 - smooth(seg(t, *FLY_OUT))
        for (p, c) in SWEEP:
            ok = np.minimum(p[:-1, 1], p[1:, 1]) >= ys
            if not ok.any(): continue
            idx = np.flatnonzero(ok); br = np.flatnonzero(np.diff(idx) > 1)+1
            for run in np.split(idx, br): cyan.line(v.pts(p[run[0]:run[-1]+2]), 2.2, a*0.95)
        if t < SWEEP_T[1]+0.05:
            for i in MAIN:
                p = SWEEP[i][0]; y = p[:, 1]; cr = np.flatnonzero((y[:-1]-ys)*(y[1:]-ys) <= 0)
                for j in cr[:2]: cyan.dot(v.pt(p[j]), 4.0, 0.95)
    # --- per-project traced outlines in the stops ---
    for key, (t0, t1, *_r) in STOPS.items():
        if t >= t0 and PROJ[key]["valid"]:
            fade = 1.0 if t < 18.0 else 1 - 0.35*smooth(seg(t, 18.0, 18.7))
            outline(cyan, v, key, smoother(seg(t, t0, t1)), 2.6 if panel < 0.5 else 2.0, fade)
    # --- panel stage: titles, pins, leaders ---
    pa = panel
    if pa > 0.01:
        tt = lambda s, xy, f, col, t0, **k: text_kinetic(ui, xy, s, f, col, t, t0, **k)
        g = 1 - smooth(seg(t, *FLY_OUT)) if t < 10 else smooth(seg(t, 18.8, 19.3))
        if t < 10 or t > 18.7:
            ti = 0.5 if t < 10 else 18.8
            tt("DUBAI COAST", (1040, 30), font(54, True), TEXT, ti, track=2, out_t=8.4 if t < 10 else None)
            tt("SEPTEMBER 2006 · NASA ASTER", (1040, 96), font(24), MUTED, ti+0.3, per=0.012, track=2, out_t=8.4 if t < 10 else None)
        if t >= 2.0 and t < 10:
            chip(ui, (1040, 972), "OUTLINE TRACED FROM THIS IMAGE · DARK WATER VS BRIGHT GROUND", font(17), t, 2.0, out_t=8.4, accent=CYAN)
        if t >= 4.2 and t < 10:
            text_kinetic(ui, (1040, 262), "↑  LISTED SOUTH TO NORTH (NASA)", font(20), MUTED, t, 4.2, out_t=8.4, track=1.5)
        for key, num, name, tp in PINS:
            ap = PROJ[key]["anchor"]; sp = v.pt(ap)
            if t < 10:
                tin, tout = tp, 8.4
                pr_ = out_cubic(seg(t, tin, tin+0.5)); fo = 1 - smooth(seg(t, tout, tout+0.5))
            else:
                tin, tout = 18.7 + 0.1*[p[0] for p in PINS].index(key), 99
                pr_ = out_cubic(seg(t, tin, tin+0.5)); fo = 1.0
            if pr_ <= 0 or fo <= 0: continue
            amb_g.ring(sp, lerp(9, 22, out_cubic(seg(t, tin, tin+0.8))) , 2.0, 0.9*fo*(1-seg(t, tin+0.3, tin+0.9)*0.7)); amb_g.dot(sp, 4.5, fo)
            lx = 1030.0; pts = np.array([sp, [lx-40, sp[1]], [lx, sp[1]]])
            part, _h = partial(pts, cumlen(pts), pr_); amb_u.line(part, 2.0, fo)
            text_kinetic(ui, (1040, sp[1]-34), num, font(18, True), AMBER, t, tin+0.25, track=2, out_t=tout if tout < 99 else None)
            text_kinetic(ui, (1040, sp[1]-12), name, font(30, True), TEXT, t, tin+0.3, per=0.02, track=1, out_t=tout if tout < 99 else None)
        if t > 18.9:   # closing path S -> N through the four anchors, image-space only
            anchors = np.array([PROJ[k]["anchor"] for k in ("JA", "JU", "W", "DE")]); curve = chaikin(anchors, 3)
            pp, hd = partial(curve, cumlen(curve), smoother(seg(t, 18.9, 19.6)))
            cyan.line(v.pts(pp), 3.0, 0.95)
            if seg(t, 18.9, 19.6) < 1: cyan.dot(v.pt(hd), 4.5, 1)
            chip(ui, (1040, 228), "PATH JOINS THE ANCHORS IN LISTED ORDER · NOT A DISTANCE", font(16), t, 19.1, accent=CYAN)
        # source line (panel position)
        if t < 19.3: text_kinetic(ui, (1040, 1034), CAP, font(18), MUTED, t, 0.7, dur=0.5, per=0.006)
        else: text_kinetic(ui, (1040, 1034), CREDIT, font(14), MUTED, t, 19.4, dur=0.4, per=0.003)
    # --- full-bleed stage: lower-third titles and NASA status chips ---
    if panel < 0.99:
        for key, (t0, t1, title, ti, to, chip_s, ci, co) in STOPS.items():
            if ti <= t < to+0.5:
                text_kinetic(ui, (96, 836), title, font(54, True), TEXT, t, ti, per=0.03, track=3, out_t=to, shadow=True)
            if chip_s and ci <= t < co+0.4: chip(ui, (96, 930), chip_s, font(24), t, ci, out_t=co)
        text_kinetic(ui, (96, 1036), CAP, font(18), TEXT, t, 9.0, dur=0.5, per=0.006, out_t=17.9, shadow=True)
        if 10 <= t < 18.0 and any(PROJ[k]["valid"] for k in PROJ):
            chip(ui, (1330, 1024), "OUTLINE TRACED FROM THIS IMAGE", font(16), t, 10.0, out_t=17.7, accent=CYAN)
    text_kinetic(ui, (40, 18), "MOTION POC · NOT FINAL", font(16), AMBER, t, 0.2, dur=0.3, per=0.004)
    # --- composite ---
    frame = base.convert("RGBA")
    gm = window_mask(win)
    for L, glow, mask in ((cyan, 0.5, gm), (amb_g, 0.35, gm), (amb_u, 0.0, None)):
        r = L.finish(glow, 6, mask)
        if r is not None: frame = Image.alpha_composite(frame, r)
    frame = Image.alpha_composite(frame, ui).convert("RGB")
    a = smooth(seg(t, 0.0, 0.9))
    return frame if a >= 1 else Image.blend(Image.new("RGB", (W, H)), frame, a)

def _r(i): return render(i/FPS).tobytes()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("out", nargs="?"); ap.add_argument("--frames"); ap.add_argument("--png"); ap.add_argument("--report")
    a = ap.parse_args()
    rep = {k: dict(valid=v["valid"], anchor=[round(float(x), 1) for x in v["anchor"]], **v["report"]) for k, v in PROJ.items()}
    rep["_trace"] = dict(TINFO, polylines=len(polys_all)); 
    if a.report: json.dump(rep, open(a.report, "w"), indent=1)
    print(json.dumps(rep, indent=None)[:900])
    if a.frames:
        os.makedirs(a.png, exist_ok=True)
        for s in a.frames.split(","): render(float(s)).save(f"{a.png}/f_{float(s):05.2f}.png")
        sys.exit(0)
    N = int(DUR*FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
                           "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    with mp.Pool(4) as pool:
        for b in pool.imap(_r, range(N), chunksize=3): ff.stdin.write(b)
    ff.stdin.close(); ff.wait(); print("frames", N, "rc", ff.returncode)
