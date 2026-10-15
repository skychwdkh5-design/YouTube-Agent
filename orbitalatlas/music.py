"""music - original procedural score for Shorts and promos (numpy only, deterministic, dedicated CC0 like orbitalatlas.sfx).

A loopable electronic bed: kick, clap, hats, sub bass, detuned pad, plucked arpeggio, risers and impacts on given accents; a sidechain pump
from the kick; the tail of the loop is wrapped onto its head so the file repeats seamlessly. `mix_short` places voice excerpts on the timeline,
ducks the bed under the voice and the sound-design cues, and loudness-normalises the result.

No samples from anywhere: every sound is synthesised here, so the licence question cannot arise (see LICENSE below)."""
# effect-reuse-checked: sfx.py makes one-shot effects (whoosh, sweep, impact, ...); nothing in the repository writes music or a loopable bed.
import os, subprocess, wave
import numpy as np
from . import sfx

SR = 48000
LICENSE = "Original music synthesised by orbitalatlas.music (no samples); dedicated to the public domain (CC0 1.0) by the OrbitalAtlas project."
NOTE = {"A1": 55.0, "C2": 65.41, "D2": 73.42, "E2": 82.41, "F1": 43.65, "G1": 49.0, "A2": 110.0}


def _env(n, a, r):
    t = np.arange(n) / SR; return np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))


def kick(dur=0.32, seed=0):
    n = int(dur * SR); t = np.arange(n) / SR; f = 46 + 110 * np.exp(-t * 28); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) + 0.25 * np.sin(ph * 2) * np.exp(-t * 40)


def clap(seed=1):
    rng = np.random.default_rng(seed); n = int(0.22 * SR); x = rng.standard_normal(n)
    env = np.zeros(n);
    for k, d in enumerate((0.0, 0.011, 0.022)): i = int(d * SR); env[i:] += _env(n - i, 0.001, 0.05 if k < 2 else 0.12)
    x = np.diff(np.concatenate([[0], x])) * env; return x / (np.abs(x).max() + 1e-9) * 0.7


def hat(open_=False, seed=2):
    rng = np.random.default_rng(seed); n = int((0.18 if open_ else 0.05) * SR); x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], np.diff(np.concatenate([[0], x]))])); x *= _env(n, 0.0005, 0.06 if open_ else 0.012)
    return x / (np.abs(x).max() + 1e-9) * 0.35


def saw(f, n, detune=(0.0,), phase=0.0):
    t = np.arange(n) / SR; out = np.zeros(n)
    for d in detune: out += 2 * ((t * f * (1 + d) + phase) % 1.0) - 1
    return out / len(detune)


def lowpass(x, cut):
    a = np.exp(-2 * np.pi * cut / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y


def lowpass_fast(x, cut):
    """one-pole low-pass applied in blocks with numpy (approximation good enough for pads)."""
    a = np.exp(-2 * np.pi * cut / SR); k = np.arange(64)[::-1]; kern = (1 - a) * a ** k
    return np.convolve(x, kern[::-1], mode="full")[:len(x)]


def score(duration=15.0, bpm=128.0, key_roots=("A1", "F1", "C2", "G1"), accents=(), drops=(), risers=(), intensity=None, seed=7):
    """returns a stereo float array (n, 2). accents: times of impacts; drops: [(t0, t1)] where drums and bass stop (a held breath);
    risers: times where a 1.2 s riser should PEAK; intensity: f(bar)->0..1 (default rising)."""
    n = int(round(duration * SR)); tail = int(1.0 * SR); N = n + tail; beat = 60.0 / bpm; out = np.zeros((N, 2))
    nb = int(round(duration / beat)); bars = max(1, nb // 4); inten = intensity or (lambda b: 0.55 + 0.45 * min(1.0, b / max(1, bars - 2)))
    in_drop = lambda tt: any(a <= tt < b for a, b in drops)
    def add(x, t0, gain=1.0, pan=0.0):
        i = int(round(t0 * SR));
        if i >= N: return
        x = x[:N - i] * gain; out[i:i + len(x), 0] += x * (1 - max(0, pan)); out[i:i + len(x), 1] += x * (1 + min(0, pan))
    K, C, H, HO = kick(), clap(), hat(), hat(True)
    for b in range(nb):
        t = b * beat; bar = b // 4; it = inten(bar)
        if in_drop(t): continue
        add(K, t, 0.95)
        if b % 4 in (1, 3): add(C, t, 0.45 * it, 0.1)
        for s in range(4 if it > 0.75 else 2):
            tt = t + s * beat / (4 if it > 0.75 else 2)
            if not in_drop(tt): add(HO if (s == 2 and it > 0.75) else H, tt, 0.5 * it, 0.35 if s % 2 else -0.35)
    # sub bass: root per bar, eighth-note pulse, gated in drops
    for bar in range(bars + 1):
        f = NOTE[key_roots[bar % len(key_roots)]]
        for e in range(8):
            t = bar * 4 * beat + e * beat / 2
            if t >= duration or in_drop(t): continue
            m = int(beat / 2 * SR); x = np.sin(2 * np.pi * f * np.arange(m) / SR) * _env(m, 0.004, 0.18)
            add(x, t, 0.55 * inten(bar))
    # pad: minor triads, detuned saws, low-passed, sidechained by the kick
    chord = {"A1": (110.0, 130.81, 164.81), "F1": (87.31, 110.0, 130.81), "C2": (130.81, 164.81, 196.0), "G1": (98.0, 123.47, 146.83)}
    pad = np.zeros(N)
    for bar in range(bars + 1):
        m = int(4 * beat * SR); i0 = int(bar * 4 * beat * SR)
        if i0 >= N: break
        x = sum(saw(f * 2, m, (-0.004, 0.0, 0.005), phase=0.13 * k) for k, f in enumerate(chord[key_roots[bar % len(key_roots)]]))
        x = x * _env(m, 0.25, 9.0); pad[i0:i0 + m] += x[:N - i0] * 0.18
    pad = lowpass_fast(pad, 1600.0)
    pump = np.ones(N)
    for b in range(nb + 2):
        i = int(b * beat * SR); m = min(int(beat * SR), N - i)
        if m > 0: pump[i:i + m] = 0.35 + 0.65 * (1 - np.exp(-np.arange(m) / (0.09 * SR)))
    out[:, 0] += pad * pump; out[:, 1] += pad * pump * 0.96
    # pluck arpeggio from bar 2
    rng = np.random.default_rng(seed)
    for b in range(4, nb):
        bar = b // 4; root = NOTE[key_roots[bar % len(key_roots)]] * 4
        for s in range(2):
            t = b * beat + s * beat / 2
            if in_drop(t): continue
            f = root * (1.0, 1.5, 2.0, 1.2)[(b * 2 + s) % 4]; m = int(0.25 * SR)
            x = (np.sin(2 * np.pi * f * np.arange(m) / SR) + 0.3 * np.sin(4 * np.pi * f * np.arange(m) / SR)) * _env(m, 0.002, 0.07)
            add(x, t, 0.16 * inten(bar), 0.5 if s else -0.5)
    for t in risers:
        x = sfx.rise(1.2); add(x.mean(1) if x.ndim == 2 else x, max(0.0, t - 1.2), 0.32)
    for t in accents:
        x = sfx.impact(True); add(x.mean(1) if x.ndim == 2 else x, t, 0.55)
    # loop: wrap the tail onto the head, so the end flows into the start
    out[:tail] += out[n:n + tail]; out = out[:n]
    return out / (np.abs(out).max() + 1e-9) * 0.9


def _read(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def _write(path, st):
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())


def mix_short(out_wav, duration, music, voice=(), cues=(), duck_db=11.0, target_lufs=-14.0, workdir=None):
    """music: (n,2) array. voice: [(source_audio_path, src_t0, src_t1, place_at)] - exact excerpts of an approved narration.
    cues: [{t, kind}] from orbitalatlas.sfx. Returns a report (placements, measured loudness)."""
    n = int(round(duration * SR)); v = np.zeros(n); placed = []
    for path, a, b, at in voice:
        src = _read(path); seg = src[int(a * SR):int(b * SR)].copy(); f = int(0.012 * SR); seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        i = int(round(at * SR)); m = min(len(seg), n - i); v[i:i + m] += seg[:m]; placed.append(dict(src=os.path.basename(path), src_t0=a, src_t1=b, at=at, dur=round(m / SR, 3)))
    env = np.sqrt(np.convolve(v * v, np.ones(int(0.03 * SR)) / int(0.03 * SR), mode="same")); act = (env > 0.01).astype(float)
    act = np.convolve(act, np.ones(int(0.15 * SR)) / int(0.15 * SR), mode="same"); g = 10 ** (-duck_db * np.clip(act, 0, 1) / 20)
    st = music[:n].copy() * g[:, None] * 0.8 + np.stack([v, v], 1) * 1.15
    for c in cues:
        x = sfx.LIBRARY[c["kind"]](); x = x if x.ndim == 2 else np.stack([x, x], 1); i = int(c["t"] * SR); m = min(len(x), n - i)
        if m > 0: st[i:i + m] += x[:m] * 10 ** (sfx.GAIN_DB[c["kind"]] / 20) * (0.6 if act[min(i, n - 1)] > 0.5 else 1.0)
    tmp = out_wav + ".raw.wav"; _write(tmp, st / max(1.0, np.abs(st).max() / 0.97))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=9", "-ar", str(SR), "-ac", "2", out_wav], check=True); os.remove(tmp)
    return dict(voice=placed, cues=list(cues), duck_db=duck_db, target_lufs=target_lufs, license=LICENSE)
