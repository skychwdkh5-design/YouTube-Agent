#!/usr/bin/env python3
"""EP009 pilot v3 soundscape — locally synthesised, rights-free (motion.py), synced to build_pilot_v3 timings.
Layers: beds (per scene, perspective-filtered), wind/creak/snap/impact/debris for the tree, scan/capture for the
satellite, pressure + delayed thunder for the storm, small settle sounds for dimensional props.
Narration (temporary Flite) stays on top: SFX are ducked ~8 dB under speech. Output: stereo 48 kHz.
Usage: python3 build_audio_v3.py full|test out.wav
"""
import json, sys, wave
import numpy as np
import motion as M
from motion import SR

DUR = 56.0
V = "/home/claude/ep009/voice"
TEST = [(12.0, 18.0), (18.0, 24.0), (30.0, 38.0)]
L = np.zeros(int(SR * DUR) + SR); R = np.zeros_like(L)

def place(x, t, gain_db, pan=0.0, fade_in=0.0, fade_out=0.0):
    x = np.asarray(x, np.float64); x = x / (np.abs(x).max() + 1e-9) * 10 ** (gain_db / 20)
    n = len(x)
    if fade_in: k = int(fade_in * SR); x[:k] *= np.linspace(0, 1, k)
    if fade_out: k = int(fade_out * SR); x[-k:] *= np.linspace(1, 0, k)
    i = int(t * SR); j = min(len(L), i + n)
    if j <= i: return
    gl, gr = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    L[i:j] += x[: j - i] * gl * 1.414; R[i:j] += x[: j - i] * gr * 1.414

def auto(x, pts):
    """Volume automation from (time_rel, gain) points."""
    tt = np.arange(len(x)) / SR; g = np.interp(tt, [p[0] for p in pts], [p[1] for p in pts]); return x * g

# ---------------- beds (background perspective: low-passed, wide, quiet)
place(M.lp(M.snd_bed(7.6, (55, 82.5, 110)), 1400), 0.0, -30, fade_in=0.4, fade_out=0.8)            # EO-1 hook: grounded, warm
place(M.lp(M.snd_bed(5.0, (49, 73.5, 98)), 1100), 7.0, -31, fade_in=0.5, fade_out=0.6)             # MODIS
place(M.hp(M.snd_bed(6.4, (110, 165, 220, 330), 1.6), 120), 17.6, -30, fade_in=0.8, fade_out=0.8) # orbit: thinner, airy
place(M.lp(M.snd_bed(6.0, (55, 82.5, 110)), 1200), 24.0, -32, fade_in=0.5, fade_out=0.7)           # search lens
place(M.lp(M.snd_bed(9.5, (55, 82.5, 123.5)), 1300), 46.6, -30, fade_in=0.6, fade_out=1.2)         # scale reveal

# ---------------- B01-B02: arrow draw-on (soft air, upward), pins (light papery taps), measure (wood/metal hinge)
place(M.snd_air(0.55, True), 0.85, -30, pan=-0.2)
place(M.snd_settle(210), 3.79, -24, pan=-0.35); place(M.snd_settle(190), 5.89, -25, pan=0.35)
place(M.hp(M.snd_creak(0.6, 260), 300), 5.95, -32, pan=0.1)
place(M.snd_air(0.9, False), 6.7, -31)                                                              # pull-back to region
# ---------------- B03: storm front sweep (low, slow, directional L->R) + date ticks
front = M.lp(M.noise(int(2.2 * SR)), 380) * np.sin(np.linspace(0, np.pi, int(2.2 * SR))) ** 2
place(front, 7.7, -27, pan=-0.3); place(front[::-1] * 0.0 + front, 8.6, -30, pan=0.4)
for k in range(8): place(M.snd_settle(1400, 0.05), 7.75 + k * 0.24, -40, pan=-0.5 + k * 0.14)
for tb in (10.05, 10.6): place(M.snd_settle(900, 0.08), tb, -34)                                    # blink comparator clicks

# ---------------- B04 (benchmark): wind builds BEFORE the tree reacts; lull; strain, snap, fall, impact, debris, settle
gusts = [(12.9, 0.35, 0.6, 0.7), (13.55, 0.55, 0.5, 0.5), (14.32, 1.25, 0.18, 0.9)]
tt = np.linspace(11.8, 18.2, 640)
curve = np.array([M.gust(t, gusts, base=0.12) * (1 - 0.55 * M.ease("fade_soft", t, 14.0, 14.3) * (t < 14.32)) for t in tt])
curve = np.clip(curve * np.array([1 - 0.7 * M.ease("fade_soft", t, 16.0, 18.0) for t in tt]), 0, 1.4)
wind = M.snd_wind(6.4, curve * 1.15)          # anticipatory: audio curve leads the visual load (wind arrives first)
place(auto(wind, [(0, 0), (0.6, 0.55), (2.4, 0.9), (2.6, 1.0), (6.0, 0.5), (6.4, 0)]), 11.6, -19, pan=-0.15)
place(M.lp(M.snd_pressure(6.0), 120), 12.2, -24, fade_in=1.0, fade_out=1.5)                        # storm mass (felt)
place(M.snd_creak(0.8, 90), 13.75, -26, pan=0.1)                                                    # strain on second gust
place(M.snd_creak(0.45, 120), 14.36, -22, pan=0.15)                                                 # loading on the hit
place(M.snd_snap(), 14.55, -14, pan=0.1)                                                             # trunk/root snap
place(M.snd_air(0.6, False), 14.62, -28, pan=0.25)                                                   # fall swish (heavy, low)
place(M.snd_thud(42, 1.6, 500), 15.04, -13, pan=0.2)                                                 # impact (weight)
place(M.snd_debris(1.6, 46, 3500), 15.08, -24, pan=0.25)                                             # soil clods & branches
place(M.lp(M.snd_debris(2.0, 18, 1200), 900), 15.4, -31, pan=0.3)                                    # late settling debris
for tb, d in ((13.65, 0.7), (14.38, 0.45), (15.15, 0.6)):                                            # thunder: light first, sound later
    place(M.snd_thunder(2.8, d), tb + 0.25 + 0.9 * d, -24 + 6 * (1 - d), pan=-0.4)

# ---------------- B05 (benchmark): orbit — tilt-up air, scan tone + data ticks, capture shutter, dive
place(M.hp(M.snd_air(1.2, True), 200), 17.2, -30)
place(M.snd_scan(2.9), 18.55, -29, pan=0.15, fade_in=0.2, fade_out=0.3)
shutter = np.concatenate([M.hp(M.noise(int(0.012 * SR)), 2500) * 0.8, np.zeros(int(0.05 * SR)), M.hp(M.noise(int(0.02 * SR)), 1800) * 0.5])
place(shutter, 21.35, -25, pan=0.15); place(M.lp(M.snd_thud(70, 0.6, 1500), 700), 21.36, -33)
place(M.lp(M.snd_air(2.2, False), 900), 21.9, -31)                                                   # descent (filter closes)

# ---------------- B06: lens (glass) moves + blink ticks
for t0 in (25.1, 25.9, 27.9, 29.0): place(M.lp(M.snd_air(0.7, True), 1400), t0, -36, pan=-0.3 + 0.2 * (t0 - 25))
for tb in (26.15, 26.7, 28.15, 28.7): place(M.snd_settle(1200, 0.06), tb, -36)

# ---------------- B07 (benchmark): storm — rising pressure, distant thunder delayed after each flash, wind gusts, rain hiss
place(auto(M.lp(M.snd_pressure(8.6), 110), [(0, 0), (1.5, 0.6), (6.0, 1.0), (7.8, 0.7), (8.6, 0)]), 29.6, -20)
rain = M.hp(M.lp(M.noise(int(6.0 * SR)), 6000), 1500)
place(auto(rain, [(0, 0), (1.2, 0.5), (4.5, 0.7), (6.0, 0)]), 31.6, -36, pan=0.2)
for tb, s in ((32.1, 1.0), (33.85, 0.7), (35.25, 1.0), (36.55, 0.6)):
    d = 0.65 if s < 0.8 else 0.45
    place(M.snd_thunder(3.2, d), tb + 0.35 + 1.1 * d, -22 + 3 * s, pan=-0.25 + 0.3 * (tb - 32) / 4)
place(M.lp(M.snd_wind(4.5, np.linspace(0.2, 0.7, 50)), 1500), 33.4, -30, pan=0.3, fade_in=0.6, fade_out=1.2)

# ---------------- B08: orbital pass, acquisition lock, arrow, front rolls into aftermath
place(M.snd_scan(1.4), 40.1, -32, pan=-0.3, fade_out=0.3)
place(M.snd_settle(1600, 0.08), 40.8, -32); place(M.snd_air(0.6, True), 40.85, -33, pan=-0.2)
place(auto(M.lp(M.snd_wind(2.2, np.linspace(0.5, 1.1, 40)), 2200), [(0, 0), (0.8, 1), (1.8, 0.6), (2.2, 0)]), 43.0, -22, pan=-0.6)
place(M.lp(M.snd_thunder(3.0, 0.5), 300), 43.6, -25, pan=0.5)
# ---------------- B09: block rises (low air + soft weight), damage propagates (debris), sinks (thud), pins & measure
place(M.lp(M.snd_air(1.2, True), 700), 47.4, -28)
place(M.snd_debris(1.7, 30, 2500), 49.3, -27, pan=0.1); place(M.lp(M.snd_creak(1.2, 70), 900), 49.2, -31)
place(M.snd_thud(46, 1.2, 700), 52.95, -19)
place(M.snd_settle(210), 53.94, -25, pan=-0.3); place(M.snd_settle(190), 54.29, -25, pan=0.3)
place(M.hp(M.snd_creak(0.7, 260), 300), 54.25, -33)

# ---------------- voice (temporary Flite), centre, with SFX ducking under it
beats = json.load(open(f"{V}/voice_durations.json")); vt = np.zeros_like(L); placed = {}
for b in beats:
    s = b["planned_start"] + (0.15 if b["planned_start"] == 0 else 0.25)
    with wave.open(f"{V}/{b['beat']}.wav") as w: x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32768
    i = int(s * SR); vt[i:i + len(x)] += x; placed[b["beat"]] = (round(s, 2), round(s + len(x) / SR, 2))
env = M.lp(np.abs(vt), 6.0); env = np.clip(env / (env.max() + 1e-9) * 6, 0, 1)
duck = 10 ** (-8 * env / 20)
L *= duck; R *= duck
vt = vt / (np.abs(vt).max() + 1e-9) * 10 ** (-3 / 20)
L += vt; R += vt
mix = np.stack([L, R], 1)[: int(DUR * SR)]
if sys.argv[1] == "test":
    mix = np.concatenate([mix[int(a * SR):int(b * SR)] for a, b in TEST])
peak = np.abs(mix).max()
if peak > 0.95: mix *= 0.95 / peak
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
print("ok", sys.argv[1], round(len(mix) / SR, 2), "s; voice", placed)
