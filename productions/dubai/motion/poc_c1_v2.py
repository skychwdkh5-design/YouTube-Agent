#!/usr/bin/env python3
"""EP002 Dubai motion POC v2: scene C1 'Four projects, south to north' (20 s, silent, 1920x1080, 30 fps).
Source: ASTER (Terra) 18 Sep 2006, productions/dubai/visuals/palm2.jpg, DISPLAYED ROTATED 90 degrees clockwise so the coast
runs left to right (south at left, as listed by NASA). Outlines are traced from that file's own pixels and checked against them.
Run from the repo root:  python3 productions/dubai/motion/poc_c1_v2.py OUT.mp4
  --frames 1,5,9 --png DIR      render single frames        --ui-check   text/plate collision test, no rendering
Cue times = word index / 2.42 words per second of the locked C1 narration (estimate until yt-voice timings exist).
No narration text is drawn; on-screen words are labels and NASA-status chips only."""
import sys, os, json, subprocess, argparse, multiprocessing as mp
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))
import motionlib as M
from motionlib import *
import trace as TR, validate as VA

SRC = "productions/dubai/visuals/palm2.jpg"
DUR, FPS = 20.0, 30
img0 = Image.open(SRC).convert("RGB"); W0, H0 = img0.size; arr0 = np.asarray(img0)
img = img0.transpose(Image.ROTATE_270)                  # 90 degrees clockwise: (x, y) -> (H0 - y, x)
SIZE = img.size; pyr = Pyramid(img)
def rot(p): p = np.asarray(p, float).reshape(-1, 2); return np.column_stack([H0-p[:, 1], p[:, 0]])
def rot1(x, y): return np.array([H0-y, x], float)
def rotbox(b): return (H0-b[3], b[0], H0-b[1], b[2])
CAP = "NASA ASTER (Terra) · 18 Sep 2006 · colours as published · view rotated 90° for display"
CREDIT = "Image: NASA/GSFC/MITI/ERSDAC/JAROS, and U.S./Japan ASTER Science Team · NASA Earth Observatory · view rotated 90° for display"

# ---- traced outlines checked against the source pixels (in ORIGINAL coordinates, then rotated) ----------------------
polys_all, TINFO = TR.trace(SRC)
polys_all = [p for p in polys_all if not (p[:, 0].mean() < 1000 and p[:, 1].mean() < 420)]     # cloud corner excluded
BOXES = {"JA": (290, 2890, 810, 3390), "JU": (1215, 1990, 1590, 2380), "W": (1230, 1100, 1760, 1640)}
PROJ = {}
for k, b in BOXES.items():
    kept, rep = VA.select_project(arr0, polys_all, b)
    lens = np.array([VA.seglen(p) for p in kept]); cen = np.array([p.mean(axis=0) for p in kept])
    anchor = (cen*lens[:, None]).sum(0)/lens.sum(); dist = np.hypot(*(cen-anchor).T); dist = dist/max(dist.max(), 1)
    PROJ[k] = dict(polys=[rot(p) for p in kept], cums=[cumlen(rot(p)) for p in kept], anchor=rot1(*anchor), rank=dist, report=rep,
                   valid=bool(rep["vertex_pass"] >= 0.7 and rep["kept_fraction_len"] >= 0.85), lens=lens)
# The World: selective markers. Thin outlines only for the large landforms; brackets round the three main groups.
W_BIG = [i for i, p in enumerate(PROJ["W"]["polys"]) if PROJ["W"]["lens"][i] >= 380]
W_GROUPS = [rotbox(b) for b in ((1434, 1128, 1653, 1481), (1278, 1344, 1411, 1583), (1463, 1477, 1605, 1581))]   # original bboxes + 14 px, read from the traced big polylines
# Palm Deira: point marker only. Position read on the white reclaimed land and checked by eye on a 1:1 overlay.
DE_ORIG = (2300.0, 430.0); DE = rot1(*DE_ORIG)
ANCH = {"JA": PROJ["JA"]["anchor"], "JU": PROJ["JU"]["anchor"], "W": PROJ["W"]["anchor"], "DE": DE}

# ---- camera: one continuous spline through the keys -----------------------------------------------------------------
KEYS = [(0.0, 1622, 1399, 470), (1.5, 1622, 1399, 430), (3.2, 1800, 1400, 1250), (4.5, 1898, 1380, 2136), (8.4, 1898, 1380, 2120),
        (9.7, 657, 560, 720), (10.5, 780, 630, 700), (11.5, 1610, 1395, 560), (12.9, 1760, 1425, 545), (13.8, 2437, 1517, 720),
        (15.7, 2650, 1560, 700), (16.7, 3140, 2330, 720), (18.2, 3140, 2350, 690), (19.3, 1898, 1380, 2136), (20.0, 1898, 1380, 2120)]
cam = SplineCam(KEYS, SIZE)
STOPS = {"JA": ("PALM JEBEL ALI", 9.6, 10.9, None), "JU": ("PALM JUMEIRAH", 11.1, 13.1, "LARGELY COMPLETE AS LANDFORMS · 2006"),
         "W": ("THE WORLD", 13.7, 16.0, "UNDER CONSTRUCTION · 2006"), "DE": ("PALM DEIRA", 16.2, 18.4, "EARLIEST STAGES · 2006")}
CHIPS = {"JU": (12.0, 13.5), "W": (14.8, 16.0), "DE": (17.6, 18.5)}
OUT_T = {"JA": (9.9, 10.8), "JU": (11.5, 12.3), "W": (14.0, 15.0)}
PINS = [("JA", "01", "PALM JEBEL ALI", 5.4, (48, -16)), ("JU", "02", "PALM JUMEIRAH", 6.6, (44, -74)),
        ("W", "03", "THE WORLD", 7.4, (46, -14)), ("DE", "04", "PALM DEIRA", 8.7, (-46, -62))]
F_PIN = font(26, True)

def outline(L, v, key, p, width, alpha=1.0, only=None):
    pr = PROJ[key]
    for i, (q, c, rk) in enumerate(zip(pr["polys"], pr["cums"], pr["rank"])):
        if only is not None and i not in only: continue
        f = smoother((p - 0.45*rk)/0.55) if p < 1 else 1.0
        if f <= 0: continue
        pts, head = partial(q, c, f); L.line(v.pts(pts), width, alpha)
        if 0 < f < 1 and c[-1] > 400: L.dot(v.pt(head), 3.0, 0.9)

def pins(ui, amb_g, amb_u, v, t, times, tout=None):
    for (key, num, name, _tp, off), tin in zip(PINS, times):
        sp = v.pt(ANCH[key]); a_in = out_cubic(seg(t, tin, tin+0.5)); fo = 1 - (smooth(seg(t, tout, tout+0.3)) if tout else 0)
        if a_in <= 0 or fo <= 0: continue
        amb_g.ring(sp, lerp(8, 24, out_cubic(seg(t, tin, tin+0.9))), 2.0, 0.9*fo*(1-0.7*seg(t, tin+0.3, tin+0.9))); amb_g.dot(sp, 4.5, fo)
        txt = f"{num}  {name}"; w = text_width(txt, F_PIN) + 36; h = 26 + 18
        x = sp[0]+off[0] if off[0] > 0 else sp[0]+off[0]-w+40*0; y = sp[1]+off[1]
        if off[0] < 0: x = sp[0]-46-w
        tx = x if off[0] > 0 else x+w; ty = y+h/2
        ln = np.array([[sp[0]+(9 if off[0] > 0 else -9), sp[1]], [tx, ty]]); part, _h = partial(ln, cumlen(ln), a_in); amb_u.line(part, 1.8, fo)
        chip(ui, (x, y), txt, F_PIN, t, tin+0.15, out_t=tout, group="pin"+key, pad=12)

def make_base(t):
    v = cam.view(t); b = depth_background(pyr, v, 0.22); return paste_image(b, pyr, v)

def render(t, ui_only=False):
    ui_reset(); v = cam.view(t)
    if not ui_only:
        spd = cam.speed(t); n = 1 if spd < 6 else min(11, 2 + int((spd-6)/5))
        if n == 1: base = make_base(t)
        else:
            subs = [make_base(t + (i/(n-1)-0.5)*0.4/FPS) for i in range(n)]; base = subs[0]
            for i, s in enumerate(subs[1:], 2): base = Image.blend(base, s, 1/i)
    cyan, thin, amb_g, amb_u = Stroke(CYAN), Stroke(CYAN), Stroke(AMBER), Stroke(AMBER)
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0)); close_fade = 1 - smooth(seg(t, 18.2, 18.8))
    # --- per-project traced outlines (thin glow) and The World's selective markers ---
    for key in ("JA", "JU"):
        t0, t1 = OUT_T[key]
        if t >= t0 and PROJ[key]["valid"]: outline(cyan, v, key, smoother(seg(t, t0, t1)), 2.4, close_fade)
    t0, t1 = OUT_T["W"]
    if t >= t0 and PROJ["W"]["valid"]:
        fw = 1 - smooth(seg(t, 15.8, 16.3)); outline(thin, v, "W", smoother(seg(t, t0, t1)), 2.0, 0.9*fw*close_fade, only=W_BIG)
        for j, g in enumerate(W_GROUPS):
            pr_ = out_cubic(seg(t, 14.3+0.15*j, 14.7+0.15*j))
            if pr_ > 0 and fw > 0:
                a, b = v.pt((g[0], g[1])), v.pt((g[2], g[3])); brackets(thin, (a[0], a[1], b[0], b[1]), 24, 2.0, fw*close_fade, pr_)
    # --- Palm Deira: point marker (no outline) ---
    if t >= 16.5:
        sp = v.pt(DE); a = out_cubic(seg(t, 16.5, 16.9))*close_fade
        crosshair(amb_g, sp, 15, 2.0, a); amb_g.ring(sp, lerp(16, 46, out_cubic(seg(t, 16.5, 17.4))), 1.6, 0.8*a*(1-seg(t, 16.8, 17.4)))
        if t >= 16.9: chip(ui, (sp[0]+34, sp[1]-52), "POINT MARKER · NOT AN OUTLINE", font(16), t, 16.9, out_t=18.2, accent=AMBER, group="demark", pad=10)
    # --- wide establishing phase: title plates, direction chip, pins ---
    if 2.9 <= t < 9.2:
        title_plate(ui, (96, 850), "DUBAI COAST", font(44, True), t, 3.0, out_t=8.3, group="title")
        chip(ui, (96, 930), "UNITED ARAB EMIRATES · PERSIAN GULF · SEPTEMBER 2006", font(22), t, 3.5, out_t=8.3, group="sub")
    if 4.2 <= t < 9.2: chip(ui, (700, 984), "SOUTH → NORTH · AS LISTED BY NASA", font(19), t, 4.2, out_t=8.3, accent=CYAN, group="dir")
    if t < 9.6: pins(ui, amb_g, amb_u, v, t, [p[3] for p in PINS], tout=8.5)
    # --- close-up phase: lower-third plates and NASA-status chips ---
    for key, (name, ti, to, chip_s) in STOPS.items():
        if ti <= t < to+0.4: title_plate(ui, (96, 850), name, font(44, True), t, ti, out_t=to, group="title")
        if chip_s and key in CHIPS and CHIPS[key][0] <= t < CHIPS[key][1]+0.4: chip(ui, (96, 930), chip_s, font(24), t, CHIPS[key][0], out_t=CHIPS[key][1], group="status")
    if 9.8 <= t < 18.3:
        if t < 16.6: chip(ui, (1920-96-452, 1000), "OUTLINE TRACED FROM THIS IMAGE", font(17), t, 9.9, out_t=15.9, accent=CYAN, group="legend", pad=12)
        elif t > 16.9: chip(ui, (1920-96-470, 1000), "POINT POSITION CHECKED BY EYE ON IMAGE", font(17), t, 17.0, out_t=18.0, accent=AMBER, group="legend", pad=12)
    # --- closing wide frame ---
    if t > 18.9:
        pins(ui, amb_g, amb_u, v, t, [19.0, 19.1, 19.2, 19.3])
        anchors = np.array([ANCH[k] for k in ("JA", "JU", "W", "DE")]); curve = chaikin(anchors, 3)
        pp, hd = partial(curve, cumlen(curve), smoother(seg(t, 19.1, 19.8))); cyan.line(v.pts(pp), 2.6, 0.95)
        if seg(t, 19.1, 19.8) < 1: cyan.dot(v.pt(hd), 4.5, 1)
        chip(ui, (700, 984), "PATH JOINS THE ANCHORS IN LISTED ORDER · NOT A DISTANCE", font(17), t, 19.3, accent=CYAN, group="dir", pad=12)
    # --- source line and tag ---
    text_kinetic(ui, (96, 1040), CAP if t < 19.4 else CREDIT, font(16), TEXT, t, 0.9 if t < 19.4 else 19.45, dur=0.5, per=0.004 if t < 19.4 else 0.0015, shadow=True, group="src")
    text_kinetic(ui, (W-40-text_width("MOTION POC v2 · NOT FINAL", font(16)), 18), "MOTION POC v2 · NOT FINAL", font(16), AMBER, t, 0.2, dur=0.3, per=0.004, group="tag")
    if ui_only: return None
    frame = base.convert("RGBA")
    for L, glow in ((cyan, 0.45), (thin, 0.0), (amb_g, 0.35), (amb_u, 0.0)):
        r = L.finish(glow, 6, None)
        if r is not None: frame = Image.alpha_composite(frame, r)
    frame = Image.alpha_composite(frame, ui).convert("RGB")
    a = smooth(seg(t, 0.0, 0.7))
    return frame if a >= 1 else Image.blend(Image.new("RGB", (W, H)), frame, a)

def ui_check(step=0.1):
    bad = []
    for i in range(int(DUR/step)+1):
        t = i*step; render(t, ui_only=True); R = [r for r in UIREG if r[5] > 0.35]
        for a in range(len(R)):
            for b in range(a+1, len(R)):
                A, B = R[a], R[b]
                if A[0] == B[0]: continue
                ox = min(A[3], B[3]) - max(A[1], B[1]); oy = min(A[4], B[4]) - max(A[2], B[2])
                if ox > 4 and oy > 4: bad.append((round(t, 2), A[0], B[0], round(ox), round(oy)))
        for g, x0, y0, x1, y1, a in R:
            if x0 < 8 or y0 < 8 or x1 > W-8 or y1 > H-8: bad.append((round(t, 2), g, "outside-safe", round(x0), round(y0)))
    return bad

def _r(i): return render(i/FPS).tobytes()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("out", nargs="?"); ap.add_argument("--frames"); ap.add_argument("--png"); ap.add_argument("--report"); ap.add_argument("--ui-check", action="store_true")
    a = ap.parse_args()
    rep = {k: dict(valid=v["valid"], anchor_rot=[round(float(x), 1) for x in v["anchor"]], **v["report"]) for k, v in PROJ.items()}
    rep["DE"] = dict(point_orig=DE_ORIG, point_rot=[float(x) for x in DE], method="read on the white reclaimed land, checked by eye on a 1:1 overlay; no outline drawn")
    rep["W"]["selective"] = dict(thin_outlines=len(W_BIG), bracket_groups=len(W_GROUPS)); rep["_trace"] = dict(TINFO, polylines=len(polys_all))
    if a.report: json.dump(rep, open(a.report, "w"), indent=1)
    if a.ui_check:
        bad = ui_check(); print("collisions:", bad if bad else "none"); sys.exit(0)
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
