#!/usr/bin/env python3
"""EP009 v4 sound: every event time comes from the simulation / scan progress, so sound cannot drift from picture.
 python3 build_audio_v4.py tree|sat out.wav t0 t1 [--voice]"""
import sys, json, wave
import numpy as np
import motion as M
from motion import SR
import ground_v4 as G
import sat_v4 as S

mode, out, T0, T1 = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]); voice = "--voice" in sys.argv
DUR = max(T1 + 1, 24.0)
L = np.zeros(int(SR * DUR) + SR); R = np.zeros_like(L)

def place(x, t, gain_db, pan=0.0, fi=0.004, fo=0.01):
    """Place a sound so its FIRST sample lands at t (sample-accurate); short fades remove clicks."""
    x = np.asarray(x, np.float64); x = x / (np.abs(x).max() + 1e-9) * 10 ** (gain_db / 20)
    k = min(len(x) // 4, int(fi * SR)); x[:k] *= np.linspace(0, 1, k) if k else 1
    k = min(len(x) // 4, int(fo * SR)); x[-k:] *= np.linspace(1, 0, k) if k else 1
    i = int(round(t * SR)); j = min(len(L), i + len(x))
    if i < 0 or j <= i: return
    gl, gr = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan)); L[i:j] += x[: j - i] * gl * 1.414; R[i:j] += x[: j - i] * gr * 1.414

def auto(x, pts):
    tt = np.arange(len(x)) / SR; return x * np.interp(tt, [p[0] for p in pts], [p[1] for p in pts])

def curve_sound(fn, t0, t1, rate=100):
    ts = np.arange(t0, t1, 1.0 / rate); return ts, fn(ts)

if mode == "tree":
    a, b = 11.6, 21.0
    # wind: the audio curve LEADS the picture by 0.35 s (you hear the gust before the crown reacts)
    ts = np.arange(a, b, 0.01); wc = np.array([G.wind(t + 0.35, G.PULSES) for t in ts]) / 1.8
    wind = M.snd_wind(b - a, np.clip(wc, 0, 1.3) * 1.1)
    place(auto(wind, [(0, 0), (0.7, 0.6), (b - a - 3.0, 1.0), (b - a, 0.25)]), a, -20, pan=-0.15, fi=0.2, fo=0.2)
    place(M.lp(M.snd_pressure(b - a), 120), a, -25, fi=0.4, fo=0.4)
    # wood strain: continuous, level/pitch follow the simulated crown load (rises while bending, peaks at the failure)
    ts2 = np.arange(12.6, G.T_FAIL, 0.01); sc_ = G.strain_curve(ts2); load = np.clip(sc_[:, 0] / 60.0, 0, 1) ** 1.4 * (0.35 + np.clip(sc_[:, 1] / 120, 0, 1))
    cre = M.snd_creak(len(ts2) * 0.01, 82)
    cre = auto(cre, [(i * 0.01, float(load[i])) for i in range(0, len(load), 5)])
    place(cre, 12.6, -26, pan=0.1, fi=0.15, fo=0.05)
    # failure: the crack lands exactly on T_FAIL; roots tearing (low debris) follows for ~0.4 s
    place(M.snd_snap(), G.T_FAIL, -14, pan=0.1)
    place(M.lp(M.snd_debris(0.5, 55, 1600), 1800), G.T_FAIL + 0.03, -26, pan=-0.2)
    # fall: air displaced by a heavy mass grows with the simulated angular speed
    ts3 = np.arange(G.T_FAIL, G.T_CONTACT, 0.01); om = np.array([abs(G.SIM(t)[1]) for t in ts3])
    fall = M.lp(M.noise(int((G.T_CONTACT - G.T_FAIL) * SR)), 700); fall = fall * np.interp(np.arange(len(fall)) / SR, ts3 - G.T_FAIL, om / max(om.max(), 1e-6)) ** 1.5
    place(fall, G.T_FAIL, -26, pan=0.2, fi=0.05, fo=0.05)
    # impact: on the contact frame; weight scales with the contact speed
    place(M.snd_thud(42, 1.6, 500), G.T_CONTACT, -12.5, pan=0.2, fi=0.001)
    place(M.snd_debris(1.4, 40, 3000), G.T_CONTACT + 0.01, -25, pan=0.25)
    # soil clods: a tick at every simulated landing
    for tl, sz in G.clod_events():
        place(M.lp(M.snd_thud(110 + 60 * (sz % 7), 0.25, 900), 1200), tl, -27 - 4 * (1 - min(1, (tl - G.T_FAIL) / 1.5)), pan=0.3)
    # settle: rustle follows the real canopy motion after impact (leaves, branches) until it stops
    ts4 = np.arange(G.T_CONTACT, 19.8, 0.01); en = G.canopy_energy(ts4); en = en / (en.max() + 1e-9)
    rustle = M.hp(M.lp(M.noise(int(len(ts4) * 0.01 * SR)), 5000), 900)
    rustle *= np.interp(np.arange(len(rustle)) / SR, ts4 - G.T_CONTACT, en) ** 0.8
    place(rustle, G.T_CONTACT, -29, pan=-0.1, fi=0.1, fo=0.3)
    # thunder after each bolt, delayed by 'distance'
    for tb, s in G.BOLT_T:
        d = 0.7 if s < 0.9 else 0.45; place(M.snd_thunder(2.8, d), tb + 0.25 + 0.9 * d, -24 + 5 * s, pan=-0.4)
    # gust leaves (light ticks) when each leaf is released
    for tl in G.LEAF_T:
        if tl: place(M.hp(M.snd_debris(0.35, 14, 6000), 2500), tl, -38, pan=-0.2 + 0.4 * (tl % 1))
    # post-impact quiet: soft bed re-enters
    place(M.lp(M.snd_bed(5.0, (55, 82.5, 110)), 1200), 16.8, -32, fi=1.5, fo=1.5)
elif mode == "sat":
    place(M.lp(M.snd_bed(T1 - T0 + 1, (110, 165, 220, 330), 1.6), 1800), T0 - 0.2, -34, fi=0.6, fo=0.6)          # orbit air
    # scan: a soft tick every 28 scan rows, i.e. tied to the real scanline progress; level follows scan speed
    prev = None
    for k in range(0, 1100, 28):
        # time when the scanline reaches row k (invert the Hermite by bisection)
        lo, hi = 18.2, 22.6
        row_of = lambda t: max(-1e9, S.clamp(S.ROW(t) - 70, 0, 1e9))
        if row_of(hi) < k or row_of(lo) > k: continue
        for _ in range(40):
            mid = (lo + hi) / 2
            if row_of(mid) < k: lo = mid
            else: hi = mid
        tk = (lo + hi) / 2
        if T0 - 0.3 <= tk <= T1: place(np.sin(2 * np.pi * (3900 + 2 * k) * np.arange(int(0.012 * SR)) / SR) * np.exp(-np.arange(int(0.012 * SR)) / SR * 500), tk, -40, pan=0.15)
    # soft sustained scan tone whose pitch rides the scan progress (not a laser)
    t = np.arange(int(3.4 * SR)) / SR; row = np.array([S.ROW(18.9 + x) for x in np.arange(0, 3.4, 0.01)])
    f = 420 + 120 * np.interp(t, np.arange(0, 3.4, 0.01), (row + 120) / 1260)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.sin(2 * np.pi * 2 * np.cumsum(f) / SR) * 0.15
    place(tone * np.sin(np.pi * np.clip(t / t[-1], 0, 1)) ** 1.2, 18.9, -39, pan=0.1, fi=0.3, fo=0.3)
    # capture: one dry shutter click exactly at the exposure pulse (21.30), then the air closes down
    sh = np.concatenate([M.hp(M.noise(int(0.010 * SR)), 2500) * 0.8, np.zeros(int(0.04 * SR)), M.hp(M.noise(int(0.018 * SR)), 1800) * 0.5])
    place(sh, 21.30, -27, pan=0.15); place(M.lp(M.snd_thud(70, 0.5, 1500), 700), 21.30, -34)
    place(M.lp(M.snd_air(1.6, False), 900), 21.55, -33)

if voice:
    V = "/home/claude/ep009/voice"
    beats = json.load(open(f"{V}/voice_durations.json")); vt = np.zeros_like(L)
    for bt in beats:
        s = bt["planned_start"] + (0.15 if bt["planned_start"] == 0 else 0.25)
        with wave.open(f"{V}/{bt['beat']}.wav") as w: x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32768
        i = int(s * SR); j = min(len(vt), i + len(x)); vt[i:j] += x[: j - i]
    env = M.lp(np.abs(vt), 6.0); env = np.clip(env / (env.max() + 1e-9) * 6, 0, 1); duck = 10 ** (-8 * env / 20)
    L *= duck; R *= duck; vt = vt / (np.abs(vt).max() + 1e-9) * 10 ** (-3 / 20); L += vt; R += vt
mix = np.stack([L, R], 1)[int(T0 * SR): int(T1 * SR)]
pk = np.abs(mix).max(); mix *= (0.95 / pk) if pk > 0.95 else 1
with wave.open(out, "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
print("ok", mode, round(len(mix) / SR, 2), "s peak", round(float(np.abs(mix).max()), 3))
