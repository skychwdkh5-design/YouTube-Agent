"""Sound design for the motion engine: ORIGINAL sound effects synthesised from code (no third-party recordings, so there is no licence to
check or attribute: the sounds are the project's own work and are released CC0 with the code), a cue planner that turns the director's decisions
into timed effects, and a mixer that ducks the effects under the narration.

Library (all deterministic for a given seed, 48 kHz stereo float):
  whoosh(dur)        band-limited noise whose band sweeps up then down, panned across: camera moves, transitions
  sweep(dur)         softer, airy whoosh for gentle transitions (light wipe)
  impact(soft)       low sine thump + short filtered noise transient: impact card landing, punch-ins
  rise(dur)          noise + tone rising in pitch and level into a hit: before an impact card / the opening
  ui_blip(kind)      short two-tone digital accent: pins, panels, number cards, image stamps
  tick()             tiny filtered click: text reveals (rate-limited)

Mixing rules: every effect sits at least `voice_margin_db` (default 12 dB) under the narration while words are spoken (side-chain ducking from
the narration's own envelope), effects never overlap closer than `min_gap` s, and the final mix is normalised to about -16 LUFS by ffmpeg.
The mixer reports the measured margin so QA can prove the effects never mask the voice."""
# effect-reuse-checked: the project had no audio effects at all; yt-render muxes narration only.
import json
import math
import os
import subprocess
import wave

import numpy as np

SR = 48000
LICENSE = ("Original sound effects synthesised by orbitalatlas/sfx.py (code in this repository). No third-party audio is used; no attribution is required. "
           "Released CC0 1.0 by the project owner together with the code; safe for monetised YouTube use.")


def _noise(n, seed):
    return np.random.RandomState(seed).standard_normal(n).astype(np.float32)


def _onepole(x, cut, sr=SR):
    """time-varying one-pole low-pass; `cut` is an array (Hz) or a number."""
    cut = np.broadcast_to(np.asarray(cut, np.float32), x.shape); a = 1 - np.exp(-2 * np.pi * cut / sr); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += a[i] * (x[i] - acc); y[i] = acc
    return y


def _env(n, attack, release, shape=2.0):
    t = np.arange(n) / SR; a = np.clip(t / max(attack, 1e-4), 0, 1) ** 0.6; r = np.clip((n / SR - t) / max(release, 1e-4), 0, 1) ** shape
    return (a * r).astype(np.float32)


def _stereo(mono, pan_from=0.0, pan_to=0.0):
    p = np.linspace(pan_from, pan_to, len(mono)); l = np.cos((p + 1) * np.pi / 4); r = np.sin((p + 1) * np.pi / 4)
    return np.stack([mono * l, mono * r], 1).astype(np.float32)


def _norm(x, peak=0.9): m = np.abs(x).max(); return x * (peak / m) if m > 0 else x


def whoosh(dur=0.6, seed=1, lo=250.0, hi=2800.0, pan=(-0.6, 0.6)):
    n = int(dur * SR); x = _noise(n, seed); t = np.linspace(0, 1, n)
    centre = lo * (hi / lo) ** (np.sin(np.pi * t) ** 1.2)                 # band rises to the middle then falls
    band = _onepole(_onepole(_onepole(x, centre * 1.3), centre * 1.3), centre * 1.3) - _onepole(x, centre * 0.3)   # 3-pole top: soft, not hissy
    band = _onepole(_onepole(band, 5000.0), 5000.0)
    return _stereo(_norm(band * _env(n, dur * 0.45, dur * 0.5, 1.6)), *pan)


def sweep(dur=0.9, seed=2):
    n = int(dur * SR); x = _noise(n, seed); t = np.linspace(0, 1, n); c = 1200 + 2200 * t
    band = _onepole(_onepole(_onepole(x, c), c), c) - _onepole(x, c * 0.3)
    band = _onepole(_onepole(band, 6000.0), 6000.0)
    return _stereo(_norm(band * _env(n, dur * 0.35, dur * 0.6, 2.2)) * 0.8, -0.3, 0.4)


def impact(soft=True, seed=3):
    dur = 0.9; n = int(dur * SR); t = np.arange(n) / SR
    f = 62 * (1 + 0.6 * np.exp(-t * 18)); thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (7 if soft else 4.5))
    tr = _onepole(_onepole(_noise(n, seed), 700), 700) * np.exp(-t * 40) * (0.5 if soft else 0.9)
    return _stereo(_norm(thump + tr), 0.0, 0.0)


def rise(dur=1.4, seed=4):
    n = int(dur * SR); t = np.linspace(0, 1, n); x = _noise(n, seed)
    c = 300 + 3500 * t ** 2; air = _onepole(_onepole(_onepole(x, c), c), c) - _onepole(x, c * 0.25)
    tone = np.sin(2 * np.pi * np.cumsum(110 * 2 ** (2 * t)) / SR) * 0.35
    return _stereo(_norm((air + tone) * (t ** 2.2) * _env(n, 0.01, 0.04, 1.0)), -0.2, 0.2)


def ui_blip(kind="up", seed=5):
    dur = 0.16; n = int(dur * SR); t = np.arange(n) / SR; f1, f2 = (1320, 1760) if kind == "up" else (1760, 1320)
    a = np.sin(2 * np.pi * f1 * t) * (t < dur / 2) + np.sin(2 * np.pi * f2 * t) * (t >= dur / 2)
    return _stereo(_norm(a * _env(n, 0.003, 0.06, 2.0)) * 0.6, 0.1, 0.1)


def tick(seed=6):
    n = int(0.03 * SR); x = _noise(n, seed); y = (_onepole(x, 6000) - _onepole(x, 1500)) * np.exp(-np.arange(n) / SR * 180)
    return _stereo(_norm(y) * 0.5, 0.0, 0.0)


LIBRARY = {"whoosh": whoosh, "sweep": sweep, "impact": impact, "rise": rise, "ui_blip": ui_blip, "tick": tick}
GAIN_DB = {"whoosh": -14, "sweep": -18, "impact": -12, "rise": -16, "ui_blip": -22, "tick": -28}   # before ducking, relative to full scale


def plan_cues(report, min_gap=0.25, max_ticks=6):
    """director report -> cues [{t, kind, why}] (programme time). Deterministic; obeys min_gap with priority impact > rise > whoosh > sweep > ui_blip > tick."""
    pri = {"impact": 6, "rise": 5, "whoosh": 4, "sweep": 3, "ui_blip": 2, "tick": 1}; cues = []
    for f in report.get("focus", []):
        if f["kind"] == "impact": cues += [dict(t=f["t0"] - 1.1, kind="rise", why="before impact card"), dict(t=f["t0"] + 0.02, kind="impact", why="impact card lands")]
        else: cues.append(dict(t=f["t0"] + 0.05, kind="ui_blip", why="number card"))
    for d in report.get("decisions", []):
        k, t = d["kind"], d.get("t")
        if t is None: continue
        if k == "transition":
            w = d.get("why", "")
            if w.startswith("light wipe"): cues.append(dict(t=t - 0.3, kind="sweep", why=w))
            elif w.startswith("flash dip"): cues.append(dict(t=t - 0.05, kind="impact", why=w))
            elif w.startswith("cinematic push"): cues.append(dict(t=t - 0.25, kind="whoosh", why=w))
        elif k == "shot" and any(str(x).startswith(("camera: snap", "camera: scale change")) for x in d.get("decisions", [])):
            held = any(str(x).startswith("camera move held") for x in d.get("decisions", []))
            cues.append(dict(t=t + (1.75 if held else 0.1), kind="whoosh", why="fast camera move"))
        elif k in ("region", "callout", "compare", "route", "image_stamp"): cues.append(dict(t=t, kind="ui_blip", why=k))
        elif k in ("lift",): cues.append(dict(t=t + 0.12, kind="whoosh", why="keyword lift"))
        elif k == "event_year": cues.append(dict(t=t, kind="tick", why="event year"))
        elif k == "punch": cues.append(dict(t=t, kind="impact", why="punch-in on emphasis"))
    if report.get("opening_tilt"): cues.append(dict(t=0.0, kind="rise", why="opening plane tilt"))
    cues.sort(key=lambda c: (c["t"], -pri[c["kind"]])); kept = []
    for c in cues:
        c["t"] = max(0.0, round(c["t"], 3)); clash = [k for k in kept if abs(k["t"] - c["t"]) < min_gap]
        if clash:
            if all(pri[c["kind"]] > pri[k["kind"]] for k in clash):
                for k in clash: kept.remove(k)
            else: continue
        kept.append(c)
    ticks = [c for c in kept if c["kind"] == "tick"][max_ticks:]
    return [c for c in kept if c not in ticks]


def _read_wav(path):
    with wave.open(path, "rb") as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes(); a = np.frombuffer(w.readframes(n), np.int16).astype(np.float32) / 32768
    a = a.reshape(-1, ch).mean(1) if ch > 1 else a
    if sr != SR: a = np.interp(np.arange(int(len(a) * SR / sr)) / SR, np.arange(len(a)) / sr, a).astype(np.float32)
    return a


def _write_wav(path, st):
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())


def envelope(x, win=0.03):
    n = int(win * SR); k = np.ones(n, np.float32) / n; return np.sqrt(np.convolve(x * x, k, mode="same") + 1e-12)


def mix(voice_wav, cues, duration, out_wav, voice_margin_db=12.0, duck_db=8.0, workdir=None, normalise=True):
    """voice + cues -> stereo mix wav. Returns a report with the measured effects-to-voice margin while the voice is active."""
    v = _read_wav(voice_wav); n = int(duration * SR); v = np.pad(v, (0, max(0, n - len(v))))[:n]
    fx = np.zeros((n, 2), np.float32); placed = []
    for c in cues:
        snd = LIBRARY[c["kind"]](); g = 10 ** (GAIN_DB[c["kind"]] / 20); i0 = int(c["t"] * SR); i1 = min(n, i0 + len(snd))
        if i0 >= n: continue
        fx[i0:i1] += snd[:i1 - i0] * g; placed.append(dict(c, gain_db=GAIN_DB[c["kind"]]))
    env = envelope(v); active = env > max(0.02, env.max() * 0.08)
    act_s = np.convolve(active.astype(np.float32), np.ones(int(0.12 * SR)) / int(0.12 * SR), mode="same")
    duck = 10 ** (-duck_db * np.clip(act_s, 0, 1) / 20); fx *= duck[:, None]
    # hard guarantee: inside speech the effects stay voice_margin_db under the local voice level
    fe = envelope(fx.mean(1)); lim = env * 10 ** (-voice_margin_db / 20); over = active & (fe > lim)
    scale = np.ones(n, np.float32); scale[over] = (lim[over] / np.maximum(fe[over], 1e-9))
    scale = np.convolve(scale, np.ones(int(0.01 * SR)) / int(0.01 * SR), mode="same"); fx *= scale[:, None]
    out = np.stack([v, v], 1) + fx
    tmp = out_wav if not normalise else out_wav + ".raw.wav"; _write_wav(tmp, out / max(1.0, np.abs(out).max() / 0.98))
    if normalise:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(SR), out_wav], check=True); os.remove(tmp)
    fe2 = envelope(fx.mean(1)); m = active & (fe2 > 1e-4)
    margin = float(np.percentile(20 * np.log10(env[m] / np.maximum(fe2[m], 1e-9)), 5)) if m.any() else None
    return dict(cues=placed, voice_active_s=round(float(active.mean() * duration), 2), margin_db_p5=None if margin is None else round(margin, 1), license=LICENSE)


def export_library(folder):
    """write every effect as a wav + LICENSE.txt + SHA list (for the media branch / review)."""
    import hashlib
    os.makedirs(folder, exist_ok=True); sums = []
    for k, f in LIBRARY.items():
        p = os.path.join(folder, f"{k}.wav"); _write_wav(p, f()); sums.append(f"{hashlib.sha256(open(p, 'rb').read()).hexdigest()}  {k}.wav")
    open(os.path.join(folder, "LICENSE.txt"), "w").write(LICENSE + "\n"); open(os.path.join(folder, "SHA256SUMS"), "w").write("\n".join(sums) + "\n")
    return sums
