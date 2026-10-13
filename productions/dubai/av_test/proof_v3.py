#!/usr/bin/env python3
"""EP002 Dubai motion proof v3 (14.5 s): real narration slice (rel 23.35-37.85 s of the existing ElevenLabs audio) with
geographic motion graphics. Shots: ISS photograph (2022) -> zoom-through match cut -> ASTER 2006 pull-out -> coast trace.
Run from the repo root:  python3 productions/dubai/av_test/proof_v3.py OUT.mp4 --mastered A.wav --ass S.ass
  --frames 1,5 --png DIR   single frames
Every cue time comes from the provider word timings; every outline is traced from the pixels it is drawn on."""
import sys, os, json, subprocess, argparse, multiprocessing as mp
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "motion")); sys.path.insert(0, os.path.join(HERE, "..", "motion", "engine"))
import math
import numpy as np
import poc_c1_v2 as P
from motionlib import *
import motionlib as M, fx, av
tfont_ = lambda px: fx.tfont(px)
import trace as TR, validate as VA

OFF = 23.35; DUR = 14.5; FPS = 30
AUD = "productions/dubai/visuals/_local_assets/audio/"
voice = json.load(open(AUD+"narration_H1_A1.voice.json")); tr = av.Transcript(voice["words"], -OFF)
T = lambda seq, occ=1: tr.start(seq, occ)              # seconds in proof time
E = lambda seq, occ=1: tr.end(seq, occ)

# ---- ISS photograph (2022), displayed rotated 90 deg clockwise -----------------------------------------------------
ISS_PATH = "productions/dubai/visuals/iss067e003785_lrg.jpg"
iss0 = Image.open(ISS_PATH).convert("RGB"); HI = iss0.size[1]; arr_i = np.asarray(iss0)
iss = iss0.transpose(Image.ROTATE_270); ISZ = iss.size; pyr_i = Pyramid(iss)
def ri(p): p = np.asarray(p, float).reshape(-1, 2); return np.column_stack([HI-p[:, 1], p[:, 0]])
def ri1(x, y): return np.array([HI-y, x], float)
polys_i, _ = TR.trace(ISS_PATH, thresh=80, channel="r", min_len=6, tol=0.6)
BOX_I = {"JU": (1650, 980, 2260, 1560), "JA": (1250, 2430, 2010, 3120), "W": (1150, 60, 1900, 900)}
OUT_I = {}
for k, b in BOX_I.items():
    kept, rep = VA.select_project(arr_i, polys_i, b, channel="r", lo=90, gap=60)
    OUT_I[k] = dict(polys=[ri(p) for p in kept], cums=[cumlen(ri(p)) for p in kept], rep=rep)
land_i = fx.land_mask(arr_i, "r", 85)
def disc_mask(arr_shape, c, r, base): return base & fx.disc(arr_shape[:2], c, r)
C_I = {"JU": ((1955, 1272), 250), "JA": ((1626, 2776), 340)}
ML_I = {k: fx.MaskLayer(fx.rot_mask(disc_mask(arr_i.shape, c, r, land_i)), ISZ) for k, (c, r) in C_I.items()}
SEA_I = fx.MaskLayer(fx.rot_mask(~land_i), ISZ)
AN_I = {"JU": ri1(1955, 1272), "JA": ri1(1626, 2776)}

# ---- ASTER 2006 (palm2), already rotated in poc_c1_v2 ------------------------------------------------------------------
land_a = fx.land_mask(P.arr0, "max", 85)
C_A = {"JA": ((550, 3140), 255), "JU": ((1392, 2180), 195), "W": ((1520, 1360), 300)}
ML_A = {k: fx.MaskLayer(fx.rot_mask(disc_mask(P.arr0.shape, c, r, land_a)), P.SIZE) for k, (c, r) in C_A.items()}
AN_A = {k: P.ANCH[k] for k in ("JA", "JU", "W")}
coast = max(P.polys_all, key=lambda p: cumlen(p)[-1]); coast = P.rot(coast)
if coast[0, 0] > coast[-1, 0]: coast = coast[::-1]
coast_c = cumlen(coast)
def coast_pt(x):  # point of the coast polyline nearest in x'
    return coast[int(np.argmin(np.abs(coast[:, 0]-x)))]
CT = coast_pt(2350)
def coast_frame(xq, off, span=700):
    """point on the traced coast near x'=xq moved `off` source px inland (+) or seaward (-); angle = overall coast direction over +/-span px."""
    i = int(np.argmin(np.abs(coast[:, 0]-xq))); a = coast[int(np.argmin(np.abs(coast[:, 0]-(xq-span))))]; b = coast[int(np.argmin(np.abs(coast[:, 0]-(xq+span))))]
    t_ = (b-a)/np.hypot(*(b-a)); n_ = np.array([-t_[1], t_[0]]); return coast[i]+n_*off, -float(np.degrees(np.arctan2(t_[1], t_[0])))
ANG = -float(np.degrees(np.arctan2(coast[-1, 1]-coast[0, 1], coast[-1, 0]-coast[0, 0])))   # screen angle of the coast direction

# ---- timing from the words (proof seconds) --------------------------------------------------------------------------
t_palm, t_islands, t_orbit, t_from = T("palm-shaped"), T("islands stand"), T("orbit."), T("from orbit")
t_so, t_land, t_only, t_sea = T("So how"), T("land where"), T("only sea"), E("only sea")-0.45
t_and, t_plans, t_that = T("And what"), T("plans"), T("that came")
t_this, t_dubai, t_uae, t_shore, t_persian, t_coast = T("This is"), T("Dubai,"), T("United Arab"), T("on the shore"), T("Persian Gulf", 2), T("coastline")
CUT = t_and-0.20                                         # match cut, ISS -> ASTER (just before 'And')
# ---- cameras -------------------------------------------------------------------------------------------------------------
CAM_I = SplineCam([(0, ISZ[0]/2, ISZ[1]/2, ISZ[1]), (t_from-0.05, ISZ[0]/2+60, ISZ[1]/2+80, 2560), (t_so+0.35, 3655, 1955, 1120), (5.12, 3655, 1955, 880), (CUT+0.12, 3655, 1955, 400)], ISZ)
CH_I = math.exp(CAM_I.raw(CUT)[2])
CAM_A = SplineCam([(CUT, 1617, 1395, 0.76*CH_I), (CUT+0.55, 1617, 1395, 0.76*CH_I*1.18), (t_plans+0.15, 1800, 1400, 1300), (t_this+0.1, 1898, 1380, 2136), (t_persian+0.2, 2000, 1400, 2020),
                   (t_coast-0.55, 2050, 1410, 1960), (DUR, CT[0]+80, CT[1]-40, 640)], P.SIZE)
def view_at(t): return (CAM_I if t < CUT else CAM_A).view(t)

SRC_I = "NASA ISS ASTRONAUT PHOTOGRAPH ISS067-E-3785 · 6 APR 2022"
SRC_A = "NASA ASTER (TERRA) · 18 SEP 2006 · COLOURS AS PUBLISHED"
def base_img(t):
    if t < CUT: v = CAM_I.view(t); return paste_image(depth_background(pyr_i, v, 0.2), pyr_i, v)
    v = CAM_A.view(t); return paste_image(depth_background(P.pyr, v, 0.2), P.pyr, v)

def draw_outline(L, v, d, key, p, width, alpha=1.0, stagger=0.4):
    o = d[key]
    for q, c in zip(o["polys"], o["cums"]):
        pts, head = partial(q, c, smoother(p)); L.line(v.pts(pts), width, alpha)

def render(t, ui_only=False):
    ui_reset(); v = view_at(t); iss_on = t < CUT
    cy, am = Stroke(CYAN), Stroke(AMBER); ui = Image.new("RGBA", (W, H), (0, 0, 0, 0)); hl = []     # hl: queued highlights
    # ---------- ticker, source chips ----------
    if True:
        fx.year_roll(ui, (W-64-340, 36), 2022, 2006, t, CUT-0.32, dur=0.5, px=118, stagger=0.07, group="year") if t >= CUT-0.32 else fx.year_roll(ui, (W-64-340, 36), 2022, 2022, t, 0.0, px=118, group="year")
        for j, (txt, tin, tout, acc) in enumerate(((SRC_I, 0.35, CUT-0.35, CYAN), ("PHOTOGRAPH, NOT SATELLITE IMAGERY · VIEW ROTATED 90°", 0.55, CUT-0.35, AMBER)) if iss_on else
                                                   ((SRC_A, CUT+0.02, None, CYAN), ("VIEW ROTATED 90° FOR DISPLAY", CUT+0.15, t_this+1.5, AMBER))):
            f_ = font(24 if j == 0 else 22); wchip = text_width(txt, f_)+2*12+8
            chip(ui, (W-68-wchip, 194+58*j), txt, f_, t, tin, out_t=tout, group=f"src{j}", accent=acc, pad=12)
    # ---------- shot A: ISS hook ----------
    if iss_on:
        for key, t0, t1 in (("JU", t_palm, t_palm+0.75), ("JA", t_islands, t_islands+0.75)):
            if t >= t0:
                p = smoother(seg(t, t0, t1)); draw_outline(cy, v, OUT_I, key, p, 3.6, 1.0)
                sp = v.pt(AN_I[key]); R = (C_I[key][1]*1.15)*v.k*out_cubic(seg(t, t0, t1+0.3))
                hl.append((ML_I[key].at(v), (92, 225, 230), 0.34*(1-0.35*seg(t, t1+0.4, t1+1.2)), sp, R))
        if t_from-0.05 <= t:      # kinetic: from orbit
            fx.screen_text(ui, (64, 56), "FROM ORBIT", 96, t, t_from, color=TEXT, track=0.3, per=0.055, out_t=t_so+0.1, glow=1.0, group="fromorbit")
        # land / sea beat
        sp = v.pt(AN_I["JU"]); Rp = C_I["JU"][1]*1.1*v.k
        if t_land-0.2 <= t:
            e = out_cubic(seg(t, t_land-0.1, t_land+0.45)); fl = 1-smooth(seg(t, t_only-0.05, t_only+0.3))
            hl.append((ML_I["JU"].at(v), (255, 194, 71), 0.62*e*fl, sp, 1.4*Rp*e))
            fx.anchored_text(ui, v, (AN_I["JU"][0]-(Rp/v.k+40/v.k), AN_I["JU"][1]+10), "LAND", 150/v.k, t, t_land-0.02, color=AMBER, track=0.16, per=0.06, out_t=t_land+0.95, glow=1.2, min_px=60, max_px=150, anchor="right")
        if t_sea-0.1 <= t:
            e = smoother(seg(t, t_sea-0.1, t_sea+0.75))
            hl.append((SEA_I.at(v), (92, 225, 230), 0.34*e*(1-smooth(seg(t, CUT-0.4, CUT-0.1))), sp, (0.2+2.6*e)*Rp*3))
            fx.anchored_text(ui, v, (AN_I["JU"][0]+(Rp/v.k+40/v.k), AN_I["JU"][1]+10), "SEA", 150/v.k, t, t_sea, color=CYAN, track=0.16, per=0.06, out_t=CUT-0.1, out_dur=0.2, glow=1.2, min_px=60, max_px=150, anchor="left")
    # ---------- shot B: ASTER 2006 ----------
    else:
        if t >= CUT+0.05:
            p = smoother(seg(t, CUT+0.05, CUT+0.7)); draw_outline(cy, v, {"JU": dict(polys=P.PROJ["JU"]["polys"], cums=P.PROJ["JU"]["cums"])}, "JU", p, 3.2, 1-smooth(seg(t, t_plans+0.9, t_plans+1.6))*0.0)
        for key, t0 in (("JA", t_plans+0.45), ("W", t_that+0.35)):
            if t >= t0 and P.PROJ[key]["valid"]:
                pr = P.PROJ[key]; p = smoother(seg(t, t0, t0+0.8))
                for qi, (q, c) in enumerate(zip(pr["polys"], pr["cums"])):
                    if key == "W" and pr["lens"][qi] < 380: continue
                    pts, head = partial(q, c, p); cy.line(v.pts(pts), 3.2 if key == "JA" else 2.2, 1.0)
                sp = v.pt(AN_A[key]); hl.append((ML_A[key].at(v), (92, 225, 230), 0.30*out_cubic(seg(t, t0, t0+0.6)), sp, C_A[key][1]*1.15*v.k*out_cubic(seg(t, t0, t0+0.8))))
        # geographic names, anchored on the image and set parallel to the traced coast
        cp, ang = coast_frame(1600, 200)
        if t >= t_dubai: fx.anchored_text(ui, v, cp, "DUBAI", 250, t, t_dubai-0.05, color=TEXT, track=0.18, angle=ang, per=0.075, dur=0.55, out_t=t_persian+1.0, glow=0.8, min_px=60, max_px=230)
        cp2, ang2 = coast_frame(1380, 380)
        if t >= t_uae: fx.anchored_text(ui, v, cp2, "UNITED ARAB EMIRATES", 80, t, t_uae, color=AMBER, track=0.16, angle=ang2, per=0.032, out_t=t_persian+1.0, glow=0.8, min_px=30, max_px=90)
        cp3, ang3 = np.array([2650.0, 1250.0]), coast_frame(1600, 0)[1]
        if t >= t_persian-0.05: fx.anchored_text(ui, v, cp3, "PERSIAN GULF", 150, t, t_persian-0.05, color=CYAN, track=0.22, angle=ang3, per=0.065, dur=0.6, out_t=t_coast-0.25, glow=1.1, min_px=50, max_px=130)
        # coast trace, then the dive along it
        if t >= t_shore-0.1:
            head = fx.trail(cy, v.pts(coast), smoother(seg(t, t_shore-0.1, t_persian+0.55)), 0.22, 4.0, 1.0)
            if seg(t, t_shore-0.1, t_persian+0.55) < 1: cy.dot(head, 6.0, 1.0)
        if t >= t_coast-0.05 and t < DUR:
            cp4, ang4 = coast_frame(CT[0]+60, -170); fx.anchored_text(ui, v, cp4, "COASTLINE", 62, t, t_coast-0.05, color=TEXT, track=0.26, angle=ang4, per=0.05, glow=1.0, min_px=60, max_px=150)
    if ui_only: return None
    n = 1
    cam = CAM_I if iss_on else CAM_A; spd = cam.speed(t); n = 1 if spd < 5 else min(13, 2+int((spd-5)/4))
    if n == 1: base = base_img(t)
    else:
        subs = [base_img(min(t+(i/(n-1)-0.5)*0.5/FPS, CUT-0.001 if iss_on else DUR)) for i in range(n)]; base = subs[0]
        for i, s in enumerate(subs[1:], 2): base = Image.blend(base, s, 1/i)
    if iss_on and t_land-0.2 <= t < t_only+0.2:
        sp = v.pt(AN_I["JU"]); base = fx.spotlight(base, sp, C_I["JU"][1]*1.3*v.k, 0.5*out_cubic(seg(t, t_land-0.2, t_land+0.3))*(1-smooth(seg(t, t_only-0.1, t_only+0.2))))
    frame = base.convert("RGBA")
    for m, col, a, sp_, R in hl: frame = fx.highlight(frame, m, col, a, anchor_px=sp_, radius_px=R)
    for L, glow in ((cy, 0.55), (am, 0.4)):
        r = L.finish(glow, 7, None)
        if r is not None: frame = Image.alpha_composite(frame, r)
    frame = Image.alpha_composite(frame, ui).convert("RGB")
    f = smooth(seg(t, 0.0, 0.35))*(1-smooth(seg(t, DUR-0.12, DUR)))
    return frame if f >= 1 else Image.blend(Image.new("RGB", (W, H)), frame, f)

def _r(i): return render(i/FPS).tobytes()
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("out", nargs="?"); ap.add_argument("--frames"); ap.add_argument("--png"); ap.add_argument("--mastered"); ap.add_argument("--ass")
    a = ap.parse_args()
    if a.frames:
        os.makedirs(a.png, exist_ok=True)
        for s in a.frames.split(","): render(float(s)).save(f"{a.png}/f_{float(s):05.2f}.png")
        sys.exit(0)
    N = int(round(DUR*FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", a.mastered,
                           "-vf", f"subtitles={a.ass}", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", str(DUR), a.out], stdin=subprocess.PIPE)
    with mp.Pool(4) as pool:
        for b in pool.imap(_r, range(N), chunksize=2): ff.stdin.write(b)
    ff.stdin.close(); ff.wait(); print("frames", N, "rc", ff.returncode)
