"""EP009 B04 'cause -> effect' diorama rebuilt on the continuous engine (v4).

Tree = ONE physical simulation (1 kHz, sampled by Hermite): wind -> canopy clusters (first) -> branches/trunk bend (inertia)
-> root failure (threshold crossing, not a timer) -> rigid fall about a stable root pivot under gravity -> contact (impulse)
-> follow-through of crown/leaves -> settle. Event times (fail, contact, gust thresholds) come out of the simulation and drive
sound and debris, so picture and audio cannot drift apart.

Honest limit: the intact and uprooted PNGs are different drawings, so the uprooted drawing is NOT dissolved in. The intact tree
itself falls (continuous). Roots / soil lip / matching fallen trunk are missing layers (see GEOMETRY_LIMITS_V4.md).
"""
import math, json, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import engine as E
from engine import W, H, Sprite, mat, compose, draw, draw_remap, clamp, seg, lerp, smooth, Hermite, turb, wind, gust_pulse
import motion as M

REPO = "/home/claude/skychwdkh5-design/youtube-agent/productions/ep009-tornado-scars"
AS = f"{REPO}/handoff/assets"


def _clean(im):
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: 0 if v < 24 else min(255, int((v - 24) * 255 / 200)))); return im
def load(n): return _clean(Image.open(f"{AS}/{n}.png").convert("RGBA"))


# ------------------------------------------------------------------ layout (screen px, 1920x1080)
BX, BY, BH = 960.0, 800.0, 600.0                 # land block centre/height
ROOT = (BX - 80.0, BY - BH * 0.17)               # trunk base on the block
TREE_H = 400.0                                    # on-screen height of the tree drawing
PULSES = [(12.9, 0.38, 0.55), (13.55, 0.55, 0.50), (14.15, 1.30, 0.42)]   # (t0, peak, tau): smooth wind pulses
T0, T1 = 11.0, 24.0                               # simulation window

# ------------------------------------------------------------------ tree assets + articulation
_INT = load("P03_tree_intact")
TREE = M.split_tree(_INT, n_clusters=9, ground_frac=0.80)
TW, TH = TREE["size"]; S_T = TREE_H / TH
KREF = 560.0 / TH                                 # pre-shrink factor of tree sprites
BODY = Sprite(Image.alpha_composite(TREE["wood"], TREE["ground"]), ref_h=560)
CL = [Sprite(l, ref_h=560) for l, _ in TREE["clusters"]]
CC = [c for _, c in TREE["clusters"]]            # cluster centroids (orig px)
PIV = (0.60 * TW, 0.955 * TH)                    # leeward root edge: stable pivot of the fall (orig px)
BASE = (0.50 * TW, 0.955 * TH)                   # trunk base centre
V_ROOT, V_TOP = 0.955 * TH, 0.02 * TH


# ------------------------------------------------------------------ physics
THETA_F, THETA_C = 0.19, math.radians(66.0)       # root-failure lean (rad); lying angle (rad)
EV = {}                                           # filled by the simulation: fail / contact times


def _build():
    n = len(CC); ev = {}
    w0, z0, kap = 2 * math.pi * 0.50, 0.32, 0.215          # rooted sway: 0.5 Hz, lightly damped
    wp, zp = 2 * math.pi * 0.85, 0.30                     # trunk bend (crown deflection) dynamics
    freq = [2.2 + 1.6 * ((i * 0.618) % 1) for i in range(n)]
    zeta = [0.20 + 0.10 * ((i * 0.37) % 1) for i in range(n)]
    delay = [0.03 + 0.17 * (CC[i][0] / TW) for i in range(n)]       # windward side first
    gain = [10.0 + 22.0 * math.hypot(CC[i][0] - BASE[0], CC[i][1] - BASE[1]) / TW for i in range(n)]
    lev = [math.hypot(CC[i][0] - PIV[0], CC[i][1] - PIV[1]) * S_T for i in range(n)]     # lever arm (px)
    # state: theta, om, psi, vpsi, phase, [x_i, vx_i, y_i, vy_i]*n
    s0 = np.zeros(5 + 4 * n)

    def step(s, t, dt):
        th, om, ps, vps, ph = s[:5]; s = s.copy()
        wt = wind(t, PULSES)
        r = smooth((t - ev["fail"]) / 0.12) if "fail" in ev else 0.0       # release ramp: roots let go over ~0.12 s (no force step)
        if ph == 0:
            acc = -w0 * w0 * th - 2 * z0 * w0 * om + w0 * w0 * kap * wt
            if th > THETA_F and om > 0.02 and "fail" not in ev: ev["fail"] = t; ph = 1
        elif ph == 1:
            tear = 4.5 * math.exp(-(t - ev["fail"]) / 0.22)      # roots tearing: brief resistance, then gravity wins
            a_fall = 6.0 * math.sin(th + 0.05) - 0.35 * om - tear + 0.8 * wt
            a_root = -w0 * w0 * th - 2 * z0 * w0 * om + w0 * w0 * kap * wt
            acc = (1 - r) * a_root + r * a_fall
            if th >= THETA_C: ev["contact"] = t; ev["v_contact"] = om; om = -0.07 * om; th = THETA_C; ph = 2
        else:
            acc = -(2 * math.pi * 3.2) ** 2 * (th - THETA_C) - 2 * 0.95 * (2 * math.pi * 3.2) * om
        om += acc * dt; th += om * dt
        # trunk / crown deflection (px at the crown): driven by wind, lags it; inertial term from the rotation
        peq = 48.0 * wt - 4.5 * acc * r
        peq = max(-60.0, min(70.0, peq))
        aps = -wp * wp * (ps - peq) - 2 * zp * wp * vps
        vps += aps * dt; ps += vps * dt
        s[0], s[1], s[2], s[3], s[4] = th, om, ps, vps, ph
        for i in range(n):
            o = 5 + 4 * i; x, vx, y, vy = s[o:o + 4]; wd = wind(t - delay[i], PULSES)
            fl = 5.0 * turb(t, 40 + i, 1.1)
            xeq = gain[i] * wd + fl - 0.9 * lev[i] * acc * r * 0.035
            yeq = -4.0 * wd * (1 + 0.5 * turb(t, 70 + i, 0.8)) + (0.06 * lev[i] * abs(acc) * r) * 0.5
            wi = 2 * math.pi * freq[i]
            ax = -wi * wi * (x - xeq) - 2 * zeta[i] * wi * vx; ay = -wi * wi * (y - yeq) - 2 * zeta[i] * wi * vy
            vx += ax * dt; x += vx * dt; vy += ay * dt; y += vy * dt
            s[o:o + 4] = (x, vx, y, vy)
        return s
    sim = E.Sim(s0, step, T0, T1)
    EV.update(ev); return sim


SIM = _build()
T_FAIL, T_CONTACT = EV["fail"], EV["contact"]

# wind thresholds -> leaf release times (computed, not hand-placed)
_tt = np.arange(T0, T1, 0.002); _ww = np.array([wind(t, PULSES) for t in _tt])
LEAF_T = []
for thr in (0.30, 0.38, 0.47, 0.56, 0.68, 0.80, 0.95):
    k = np.argmax(_ww > thr); LEAF_T.append(float(_tt[k]) if _ww[k] > thr else None)
EV.update(leaf_release=[t for t in LEAF_T if t], wind_peak=float(_ww.max()))


def tree_state(t):
    s = SIM(t); n = len(CC)
    return dict(theta=s[0], psi=s[2], phase=s[4], cl=[(s[5 + 4 * i], s[7 + 4 * i]) for i in range(n)])


def squash_at(t):  # canopy flattens against the ground at contact, then relaxes (inertial, damped)
    if t < T_CONTACT: return 1.0
    x = t - T_CONTACT; return 1.0 - 0.10 * math.exp(-x / 0.18) * (1 - math.exp(-x / 0.03)) - 0.07 * smooth(x / 0.9) * 0 - 0.0


# ------------------------------------------------------------------ camera
CAM = E.Cam([(11.0, (0, 0, 1.0)), (13.2, (-6, -4, 1.018)), (14.9, (14, -2, 1.052)), (16.6, (30, -8, 1.07)), (19.0, (34, -10, 1.075))])
def view(t, par):
    x, y, z = CAM(t); S = z ** par; C = (W / 2, H / 2)
    return S, C, (par * x, par * y)
def to_screen(t, par, wx, wy):
    S, C, c = view(t, par); return C[0] + S * (wx - C[0] - c[0]), C[1] + S * (wy - C[1] - c[1])
def view_m(t, par):
    S, C, c = view(t, par); return np.array([[S, 0, C[0] - S * (C[0] + c[0])], [0, S, C[1] - S * (C[1] + c[1])]], np.float64)
def inv_view(t, par, X, Y):
    S, C, c = view(t, par); return C[0] + c[0] + (X - C[0]) / S, C[1] + c[1] + (Y - C[1]) / S


# ------------------------------------------------------------------ remaining assets
LAND = Sprite(load("P04_land_intact"), ref_h=640)
_ST = load("P02_storm")
BANDS = [Sprite(b, ref_h=640) for b in M.band_split(_ST, 4, 0.22)]
FAR_NEAR = Sprite(_ST.filter(ImageFilter.GaussianBlur(4)), ref_h=640)
_far_h = Sprite(M.atmos(_ST.filter(ImageFilter.GaussianBlur(5)), 0.85), ref_h=640)
_bolt = np.asarray(_ST.convert("RGBA")).astype(np.int32)
_bm = ((_bolt[..., 2] > 170) & (_bolt[..., 0] > 140) & (_bolt[..., 1] < _bolt[..., 2] - 25) & (_bolt[..., 3] > 100))
BOLT = Sprite(Image.merge("RGBA", [Image.fromarray((_bm * c).astype(np.uint8)) for c in (225, 210, 255)] + [Image.fromarray((_bm * 255).astype(np.uint8))]).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(12)), ref_h=640)
_blob = Image.new("RGBA", (256, 256), (0, 0, 0, 0)); ImageDraw.Draw(_blob).ellipse([40, 70, 216, 186], fill=(156, 128, 96, 255)); _blob = _blob.filter(ImageFilter.GaussianBlur(28))
DUST = Sprite(_blob)
_sh = Image.new("RGBA", (256, 96), (0, 0, 0, 0)); ImageDraw.Draw(_sh).ellipse([30, 20, 226, 76], fill=(6, 10, 22, 255)); SHADOW = Sprite(_sh.filter(ImageFilter.GaussianBlur(14)))


def _bits(src, box, n, size, seed, test):
    a = np.asarray(src.convert("RGBA")); out = []
    x0, y0, x1, y1 = [int(v) for v in (box[0] * src.width, box[1] * src.height, box[2] * src.width, box[3] * src.height)]
    for k in range(n * 40):
        x = int(lerp(x0, x1 - size, M.h01(seed + k * 3))); y = int(lerp(y0, y1 - size, M.h01(seed + k * 7)))
        patch = a[y:y + size, x:x + size]
        if patch[..., 3].mean() > 220 and test(patch):
            c = src.crop((x, y, x + size, y + size)); m = Image.new("L", (size, size), 0)
            ImageDraw.Draw(m).polygon([(size * (0.5 + 0.42 * math.cos(q * 1.1 + M.h01(k))), size * (0.5 + 0.38 * math.sin(q * 1.1 + M.h01(k + 1)))) for q in range(6)], fill=255)
            c.putalpha(ImageChops.multiply(c.getchannel("A"), m.filter(ImageFilter.GaussianBlur(1.5)))); out.append(Sprite(c))
            if len(out) >= n: break
    return out
CLODS = _bits(load("P04_land_scared"), (0.2, 0.55, 0.8, 0.85), 14, 38, 11, lambda p: p[..., 0].mean() > p[..., 1].mean() + 8)
LEAVES = _bits(_INT, (0.05, 0.05, 0.95, 0.55), 22, 40, 23, lambda p: p[..., 1].mean() > p[..., 0].mean())


# ------------------------------------------------------------------ analytic debris
def ballistic(tau, x0, y0, vx, vy, g, gy, e=0.28, mu=5.0):
    """Closed-form projectile with one bounce and rolling friction. Smooth in tau; returns (x, y, moving?)."""
    if tau <= 0: return x0, y0, 0.0
    disc = vy * vy + 2 * g * (gy - y0)
    t1 = (-vy + math.sqrt(max(disc, 0.0))) / g if g > 0 else 1e9
    if tau < t1: return x0 + vx * tau, y0 + vy * tau + 0.5 * g * tau * tau, 1.0
    xl = x0 + vx * t1; vyl = -e * (vy + g * t1); d = tau - t1
    t2 = 2 * abs(vyl) / g
    vxr = vx * 0.55
    if d < t2: return xl + vxr * d, gy + vyl * d + 0.5 * g * d * d, 1.0
    xr = xl + vxr * t2; d2 = d - t2
    return xr + vxr * (1 - math.exp(-mu * d2)) / mu, gy, float(math.exp(-mu * d2) > 0.03)


# ------------------------------------------------------------------ the scene
def sky(t, k):
    top = np.array([lerp(a, b, k) for a, b in zip((44, 66, 98), (18, 22, 36))], np.float32) / 255
    bot = np.array([lerp(a, b, k) for a, b in zip((196, 150, 98), (70, 60, 58))], np.float32) / 255
    g = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    return np.repeat(top[None, None] * (1 - g) + bot[None, None] * g, W, 1)


def storm_draw(c, t, h_scr, pos, haze, light, bolt, drift_t):
    """4 independently rolling bands + hazed far layer. Continuous smooth deformation on separate time scales; one resample each."""
    k = h_scr / BANDS[0].h; ws, hs = BANDS[0].w * k, BANDS[0].h * k
    mix = (FAR_NEAR.a * (1 - haze) + _far_h.a * haze)
    far_px = pos[0] - 0.4 * drift_t * 0.0, pos[1]
    layers = [(mix, 1.18, 0.0, 0.55)]
    speeds = [0.050, 0.030, 0.012, -0.010]; amps = [10.0, 8.0, 7.0, 6.0]; freqs = [0.13, 0.09, 0.07, 0.05]
    for pass_i in range(5):
        if pass_i == 0: arr, sc, spd, alpha = mix, 1.18, 0.0, 0.55
        else:
            i = pass_i - 1; arr, sc, spd, alpha = BANDS[i].a, 1.0, speeds[i], 1.0
        i = max(0, pass_i - 1)
        cx = pos[0] + spd * drift_t * ws + amps[i] * turb(t, 20 + i, freqs[i]); cy = pos[1] + 4 * turb(t, 40 + i, 0.07)
        sw, sh_ = ws * sc, hs * sc
        def inv(X, Y, cx=cx, cy=cy, sw=sw, sh_=sh_, i=i, pass_i=pass_i):
            # slow internal churn (continuous field; different spatial / temporal scale per band)
            ph = 2 * math.pi * (0.045 + 0.02 * i) * t + i * 1.7
            dxm = (6.0 + 3 * i) * np.sin(Y * (0.011 + 0.003 * i) + ph) * (1 if pass_i else 0.4)
            dym = (3.0 + 1.5 * i) * np.sin(X * (0.008 + 0.002 * i) - ph * 0.8) * (1 if pass_i else 0.4)
            wx, wy = X, Y
            return ((wx - dxm - cx) / sw + 0.5) * arr.shape[1], ((wy - dym - cy) / sh_ + 0.5) * arr.shape[0]
        bb = (int(cx - sw / 2) - 20, int(cy - sh_ / 2) - 20, int(cx + sw / 2) + 20, int(cy + sh_ / 2) + 20)
        draw_remap(c, None if False else BANDS[0], inv, bb, alpha=alpha, tint=(light, light, light), arr=arr)
    if bolt > 0.003:
        def inv_b(X, Y): return ((X - pos[0]) / ws + 0.5) * BOLT.w, ((Y - pos[1]) / hs + 0.5) * BOLT.h
        draw_remap(c, BOLT, inv_b, (int(pos[0] - ws / 2), int(pos[1] - hs / 2), int(pos[0] + ws / 2), int(pos[1] + hs / 2)), alpha=min(1.0, 2.2 * bolt), add=True)


BOLT_T = [(13.65, 1.0), (14.38, 0.8), (15.15, 0.6), (15.72, 0.35)]
def bolt_at(t):
    b = 0.0
    for tb, a in BOLT_T:                          # fast but continuous rise (0.025 s), exponential decay
        if t > tb - 0.025:
            r = smooth((t - (tb - 0.025)) / 0.025) * math.exp(-max(0.0, t - tb) / 0.09); b = max(b, a * r)
    return b


def rain(c, t, st, w):
    lay = np.zeros((H, W, 4), np.uint8); n = int(110 * st)
    for i in range(n):
        x = (M.h01(i) * W * 1.4 + t * 700 * (0.4 + w)) % (W * 1.3) - W * 0.15
        y = (M.h01(i + 7) * H + t * 1400 * (0.8 + 0.4 * M.h01(i + 11))) % (H + 80) - 40
        p0 = (int(round(x * 16)), int(round(y * 16))); p1 = (int(round((x - 34 * (0.3 + w)) * 16)), int(round((y - 46) * 16)))
        cv2.line(lay, p0, p1, (200, 210, 232, int(60 * st)), 2, cv2.LINE_AA, 4)
    a = lay.astype(np.float32) / 255; a[..., :3] *= a[..., 3:4]
    c *= (1 - a[..., 3:4]); c += a[..., :3]


PILOT = False                                    # pilot mode: terrain state change hidden behind an impact-dust occluder
T_SWAP = T_CONTACT + 0.62
LAND_SC = Sprite(load("P04_land_scared"), ref_h=640)


def cover(c, t, Vm):
    """Dense impact-dust cloud over the whole block; the intact->scarred swap happens at its opaque peak (no open crossfade)."""
    a = smooth(seg(t, T_SWAP - 0.50, T_SWAP - 0.05)) * (1 - smooth(seg(t, T_SWAP + 0.08, T_SWAP + 1.35)))
    if a <= 0.004: return
    for i in range(12):
        gx, gy = (i % 4 - 1.5) * 190 + 22 * math.sin(i * 2.1 + 0.8 * t), (i // 4 - 1.0) * 215 + 18 * math.cos(i * 1.7 + 0.7 * t)
        r = 215 + 40 * M.h01(i + 300) + 25 * a
        draw(c, DUST, compose(Vm, mat(BX + gx + 14 * (t - T_SWAP), BY - 90 + gy, 0, r * 2 / DUST.w, r * 1.7 / DUST.h, DUST.w / 2, DUST.h / 2)), alpha=min(1.0, 1.15 * a))


def scene(t):
    """Canvas (float RGB 0..1) for time t. Pure function of t."""
    st = lerp(0.0, 1.0, E.smooth(seg(t, 12.2, 14.3))) * (1 - 0.55 * smooth(seg(t, 15.8, 17.6)))
    c = sky(t, st)
    # far storm (parallax .35)
    sx = Hermite([(11.0, 260.0), (13.5, 560.0), (17.8, 1150.0), (24.0, 1180.0)])(t)
    hz = lerp(0.85, 0.15, smooth(seg(t, 12.0, 14.4)))
    hs = Hermite([(11.0, 380.0), (14.6, 600.0), (24.0, 610.0)])(t)
    px, py = to_screen(t, 0.35, sx, 300.0)
    storm_draw(c, t, hs * view(t, 0.35)[0], (px, py), hz, lerp(1.0, 0.85, st), bolt_at(t), t - 12.0)
    # block (parallax 1)
    Vm = view_m(t, 1.0)
    tint = (1 - 0.30 * st, 1 - 0.28 * st, 1 - 0.18 * st)
    kk = BH / LAND.h
    swapped = PILOT and t >= T_SWAP
    if swapped: draw(c, LAND_SC, compose(Vm, mat(BX + 6, BY + 4, 0, kk * 0.98, kk * 0.98, LAND_SC.w / 2, LAND_SC.h / 2)), shadow=(8, 0.5), shoff=(26, 34), tint=tint)
    else: draw(c, LAND, compose(Vm, mat(BX, BY, 0, kk, kk, LAND.w / 2, LAND.h / 2)), shadow=(8, 0.5), shoff=(26, 34), tint=tint)
    # tree
    ts = tree_state(t); th = ts["theta"]; ps = ts["psi"]
    # contact shadow grows/skews as the tree lowers
    sh_w = 190 * (1 + 0.9 * math.sin(max(0.0, th))); sh_a = 0.55 * (1 - 0.2 * smooth(th / THETA_C))
    if not swapped: draw(c, SHADOW, compose(Vm, mat(ROOT[0] + 40 * math.sin(max(0.0, th)) * 2.0, ROOT[1] + 22, 0, sh_w / SHADOW.w, 36 * (1 + 0.5 * math.sin(max(0.0, th))) / SHADOW.h * 2.2, SHADOW.w / 2, SHADOW.h / 2)), alpha=sh_a)
    if not swapped: draw_tree(c, t, ts, st)
    # debris, leaves, dust
    draw_debris(c, t, Vm, st)
    if PILOT: cover(c, t, Vm)
    if st > 0.05: rain(c, t, st, clamp(wind(t, PULSES)))
    return c


def draw_tree(c, t, ts, st):
    th, ps = ts["theta"], ts["psi"]; S, C, cv = view(t, 1.0)
    s = S_T * S                                                # orig px -> screen px at this zoom
    pv_w = (ROOT[0] + (PIV[0] - BASE[0]) * S_T, ROOT[1] + (PIV[1] - BASE[1]) * S_T)    # pivot in world px
    Px, Py = to_screen(t, 1.0, *pv_w)
    sq = squash_at(t); ct, sn = math.cos(th), math.sin(th)
    shade = (1 - 0.30 * st, 1 - 0.27 * st, 1 - 0.16 * st)
    R = 0.78 * TH * s * 1.12 + 40
    bb = (int(Px - R), int(Py - R * 1.05), int(Px + R), int(Py + R * 0.7))
    span = V_ROOT - V_TOP

    def inv_factory(ox, oy):
        def inv(X, Y):
            dx = X - Px; dy = (Y - Py) / sq
            a = ct * dx + sn * dy; b = -sn * dx + ct * dy            # rotate by -theta
            u1 = PIV[0] + a / s - ox / s; v1 = PIV[1] + b / s - oy / s
            hh = np.clip((V_ROOT - v1) / span, 0, 1)
            u = u1 - ps * hh ** 1.9 / S_T                            # undo row-shear bend (exactly invertible)
            return u * KREF, v1 * KREF
        return inv
    draw_remap(c, BODY, inv_factory(0, 0), bb, tint=shade)
    for i, spr in enumerate(CL):
        ox, oy = ts["cl"][i]
        draw_remap(c, spr, inv_factory(ox, oy), bb, tint=shade)


def clod_params(i):
    t0 = T_FAIL + 0.04 + 0.07 * M.h01(i)
    vx = (110 + 280 * M.h01(i + 1)) * (1 if i % 3 else -0.45); vy = -(250 + 300 * M.h01(i + 2))
    return dict(t0=t0, x0=ROOT[0] - 40.0 + (M.h01(i + 5) - 0.5) * 40, y0=ROOT[1] + 20, vx=vx, vy=vy, gy=ROOT[1] + 46.0 + 18 * M.h01(i + 6))


def draw_debris(c, t, Vm, st):
    gy = ROOT[1] + 46.0; S = view(t, 1.0)[0]
    rootx = ROOT[0] - 40.0
    for i, spr in enumerate(CLODS):                              # soil clods: thrown at the root failure
        cp = clod_params(i); t0 = cp["t0"]
        if t <= t0: continue
        x, y, mv = ballistic(t - t0, cp["x0"], cp["y0"], cp["vx"], cp["vy"], 1500.0, cp["gy"])
        sz = (16 + 16 * M.h01(i + 3)) / spr.h; rot = 300 * (t - t0) * (M.h01(i + 4) - 0.5) * (1 if mv > 0 else 0.0)
        a = 1.0 - seg(t - t0, 3.4, 4.6)
        draw(c, spr, compose(Vm, mat(x, y, rot, sz, sz, spr.w / 2, spr.h / 2)), alpha=a, shadow=(2, 0.35), shoff=(3, 4))
    for i, spr in enumerate(LEAVES):                             # loose leaves: released when the wind crosses their threshold
        if i < len(LEAF_T) and LEAF_T[i]: t0 = LEAF_T[i]
        elif i >= 7: t0 = T_FAIL + 0.35 * M.h01(i)
        else: continue
        if t <= t0: continue
        tau = t - t0; h = M.h01(i + 2)
        U = (260 + 420 * h) * min(1.0, 0.45 + wind(t0, PULSES)); T1_, T2_ = 0.45, 0.6
        x0 = ROOT[0] - 120 + (M.h01(i) - 0.3) * 300; y0 = ROOT[1] - 330 + (M.h01(i + 1) - 0.5) * 160
        x = x0 + U * (tau - T1_ * (1 - math.exp(-tau / T1_))) + 26 * math.sin(tau * 4 + i) * (1 - math.exp(-tau))
        y = y0 + 95 * (tau - T2_ * (1 - math.exp(-tau / T2_))) - 60 * (1 - math.exp(-tau / 0.4)) + 16 * math.sin(tau * 5 + i) * (1 - math.exp(-tau))
        sz = (26 + 14 * M.h01(i + 3)) / spr.h; rot = 200 * (M.h01(i + 4) - 0.5) * tau + 25 * math.sin(tau * 5 + i)
        draw(c, spr, compose(Vm, mat(x, y, rot, sz, sz, spr.w / 2, spr.h / 2)), alpha=1 - seg(tau, 1.9, 2.9), shadow=(1.5, 0.2), shoff=(3, 4))
    # dust: root tearing (small) and ground impact (large); light, drifts slowly with the residual wind
    def puff(t0, x, y, r0, a0, n, seed, rise=40.0):
        if t <= t0 - 0.02: return
        for j in range(n):
            tau = t - t0; p = M.h01(j + seed)
            r = (r0 * (0.6 + 0.8 * M.h01(j + seed + 5))) * (0.45 + 1.3 * (1 - math.exp(-tau / 0.7)))
            xx = x + (p - 0.4) * 320 * (1 - math.exp(-tau / 0.5)) + 40 * tau; yy = y - rise * tau * (0.4 + M.h01(j + seed + 9)) + 4 * turb(t, seed + j, 0.4) * tau
            al = a0 * smooth(tau / 0.08) * math.exp(-max(0.0, tau - 0.15) / 1.1) * (0.6 + 0.4 * M.h01(j + seed + 3))
            draw(c, DUST, compose(Vm, mat(xx, yy, 0, r * 2 / DUST.w, r * 1.3 / DUST.h, DUST.w / 2, DUST.h / 2)), alpha=al)
    puff(T_FAIL + 0.03, ROOT[0] - 50, ROOT[1] + 30, 36, 0.28, 5, 100, 25.0)
    puff(T_CONTACT - 0.02, ROOT[0] + 190, ROOT[1] + 48, 56, 0.40, 9, 200, 38.0)


# ------------------------------------------------------------------ probes for motion QC (analytic, same state the renderer uses)
def probe(t):
    ts = tree_state(t); S = view(t, 1.0)[0]; cx, cy, z = CAM(t)
    out = {"tree": dict(theta_deg=math.degrees(ts["theta"]), crown_bend_px=ts["psi"]),
           "camera": dict(x=cx, y=cy, zoom=z)}
    for i in (0, 4, 8): out[f"canopy{i}"] = dict(dx=ts["cl"][i][0], dy=ts["cl"][i][1])
    for i in (0, 5):
        cp = clod_params(i); x, y, _ = ballistic(t - cp["t0"], cp["x0"], cp["y0"], cp["vx"], cp["vy"], 1500.0, cp["gy"]) if t > cp["t0"] else (cp["x0"], cp["y0"], 0)
        out[f"clod{i}"] = dict(x=x, y=y)
    return out


def export_events(path):
    ev = dict(EV); ev.update(T_FAIL=T_FAIL, T_CONTACT=T_CONTACT, pulses=PULSES, bolts=BOLT_T)
    json.dump(ev, open(path, "w"), indent=1)


# ------------------------------------------------------------------ physics-derived events for sound
def clod_events():
    out = []
    for i in range(len(CLODS)):
        cp = clod_params(i); vy, y0, gy = cp["vy"], cp["y0"], cp["gy"]
        t1 = (-vy + math.sqrt(max(vy * vy + 2 * 1500.0 * (gy - y0), 0))) / 1500.0
        out.append((cp["t0"] + t1, 16 + 16 * M.h01(i + 3)))
    return sorted(out)

def canopy_energy(ts):
    """Smoothed |velocity| of all canopy clusters + trunk bend (drives rustle / strain sound from the same simulation)."""
    n = len(CC); e = []
    for t in ts:
        s = SIM(t); e.append(sum(abs(s[6 + 4 * i]) for i in range(n)) / n)
    return np.array(e)

def strain_curve(ts):
    """Trunk load for wood-strain sound: crown deflection and its rate (pre-failure only)."""
    return np.array([(abs(SIM(t)[2]), abs(SIM(t)[3]), SIM(t)[4]) for t in ts])


def IMPACTS():  # physical collisions: velocity jumps allowed (position continuity still enforced)
    ts = [clod_params(i)["t0"] for i in range(len(CLODS))]            # launches (a throw is an impulse)
    return [T_CONTACT] + ts + [t for t, _ in clod_events()] + [t + 0.02 for t, _ in clod_events()]
