"""Original score + designed SFX, synthesised here (numpy only), so the channel owns them.

Nothing here imitates a recording of a spacecraft, radio signal, launch or impact: the
sounds are musical / interface accents. An episode provides:
    MUSIC = [(t, intensity 0..1, chord_shift)]   sections of the score
    SFX   = [(t, kind, gain_db)]                 accents on events
mix(ep, out_wav) writes a stereo 48 kHz mix: narration on top, score ducked under speech."""
import subprocess
import wave

import numpy as np

SR = 48000
BPM = 80.0
BEAT = 60.0 / BPM

# D minor world: Dm9, Bbmaj7, Fadd9, C(sus) - as MIDI note lists
CHORDS = [[38, 50, 53, 57, 64], [34, 46, 50, 53, 57], [41, 48, 53, 57, 67], [36, 48, 52, 55, 62]]
ARP = [[62, 65, 69, 72, 69, 65], [58, 62, 65, 69, 65, 62], [60, 65, 69, 72, 69, 65], [60, 64, 67, 71, 67, 64]]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def read_mono(path):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, np.float32).copy()


def write_stereo(path, L, R):
    x = np.clip(np.stack([L, R], 1), -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def env_at(sections, n):
    """per-sample intensity from (t, value) keys, smoothed over 1.5 s"""
    t = np.arange(n) / SR
    ks = sorted(sections)
    v = np.interp(t, [k[0] for k in ks], [k[1] for k in ks])
    k = int(1.5 * SR)
    ker = np.ones(k) / k
    return np.convolve(np.pad(v, (k // 2, k - k // 2 - 1), mode='edge'), ker, mode='valid')


def pad(n, rng, detune=0.0):
    out = np.zeros(n, np.float32)
    t = np.arange(n) / SR
    span = 4 * 4 * BEAT                       # one chord per 4 bars
    for ci in range(int(n / SR / span) + 2):
        a, b = ci * span, (ci + 1) * span
        notes = CHORDS[ci % 4]
        i0, i1 = int(max(0, (a - 1.5)) * SR), int(min(n / SR, b + 1.5) * SR)
        if i0 >= n:
            break
        tt = t[i0:i1]
        e = np.clip((tt - (a - 1.5)) / 2.5, 0, 1) * np.clip(((b + 1.5) - tt) / 2.5, 0, 1)
        e = e * e * (3 - 2 * e)
        seg = np.zeros_like(tt)
        for m in notes:
            f0 = hz(m) * (1 + detune)
            for k, amp in enumerate([1.0, 0.45, 0.22, 0.12, 0.06]):
                ph = rng.uniform(0, 6.28)
                seg += amp / (1 + 0.02 * m) * np.sin(2 * np.pi * f0 * (k + 1) * tt + ph + 0.3 * np.sin(2 * np.pi * 0.11 * tt))
        out[i0:i1] += (seg * e).astype(np.float32)
    return out / 6.0


def pluck(f0, dur, rng, bright=0.5):
    n = int(dur * SR)
    p = max(2, int(SR / f0))
    buf = rng.uniform(-1, 1, p).astype(np.float32)
    out = np.empty(n, np.float32)
    k = 0.5 * (0.993 + 0.006 * bright)
    for i in range(n):
        j = i % p
        out[i] = buf[j]
        buf[j] = k * (buf[j] + buf[(j + 1) % p])
    return out


def arps(n, inten, rng):
    out = np.zeros(n, np.float32)
    step = BEAT / 2
    cache = {}
    i = 0
    while i * step * SR < n:
        t0 = i * step
        s = int(t0 * SR)
        g = inten[min(s, n - 1)]
        if g > 0.35:
            ci = int(t0 / (16 * BEAT)) % 4
            m = ARP[ci][i % 6] + 12
            if m not in cache:
                cache[m] = pluck(hz(m), 1.6, rng)
            x = cache[m]
            e = min(n, s + len(x))
            out[s:e] += x[:e - s] * (g - 0.35) / 0.65 * (0.8 if i % 2 else 1.0)
        i += 1
    return out * 0.5


def pulse_low(n, inten):
    out = np.zeros(n, np.float32)
    d = int(0.5 * SR)
    tt = np.arange(d) / SR
    hit = (np.sin(2 * np.pi * (55 * tt - 12 * tt * tt)) * np.exp(-tt * 7)).astype(np.float32)
    b = 0
    while b * BEAT * SR < n:
        s = int(b * BEAT * SR)
        g = inten[min(s, n - 1)]
        if g > 0.55 and b % 2 == 0:
            e = min(n, s + d)
            out[s:e] += hit[:e - s] * (g - 0.55) / 0.45
        b += 1
    return out * 0.8


def reverb(x, seconds=2.6, seed=3):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n).astype(np.float32) * np.exp(-np.arange(n) / SR * 6.9 / seconds)
    ir[:int(0.012 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum())
    m = 1 << int(np.ceil(np.log2(len(x) + n)))
    y = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[:len(x)]
    return y.astype(np.float32)


# ------------------------------------------------------------------ designed SFX
def sfx(kind, rng):
    def tt(d):
        return np.arange(int(d * SR)) / SR
    if kind == 'send':          # rising interface blip
        t = tt(0.45)
        f = 520 + 1300 * (t / 0.45) ** 1.6
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5) * np.clip(t / 0.01, 0, 1) * 0.7
    if kind == 'arrive':        # soft bell (inharmonic partials)
        t = tt(2.2)
        return sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * dcy) for f, a, dcy in
                   [(880, 0.6, 2.2), (1325, 0.3, 3.0), (2212, 0.18, 4.5), (440, 0.25, 1.6)]) * 0.7
    if kind == 'tick':
        t = tt(0.06)
        return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 90) * 0.5
    if kind == 'stamp':         # low thud + paper slap
        t = tt(0.6)
        body = np.sin(2 * np.pi * (90 * t - 40 * t * t)) * np.exp(-t * 9)
        slap = rng.standard_normal(len(t)) * np.exp(-t * 60) * 0.35
        return (body + slap) * 0.9
    if kind == 'lost':          # filtered noise swell that thins out (designed, not a recording)
        t = tt(2.4)
        x = rng.standard_normal(len(t))
        y = np.zeros_like(x)
        a = 0.0
        for i in range(len(x)):
            a += 0.05 * (x[i] - a)
            y[i] = a
        return y * 2.2 * np.sin(np.pi * t / 2.4) ** 2 * (1 - t / 2.4)
    if kind == 'back':          # rising three-note shimmer
        out = np.zeros(int(1.8 * SR))
        for k, m in enumerate([74, 77, 81]):
            s = int(k * 0.11 * SR)
            t = tt(1.8)[: len(out) - s]
            out[s:] += np.sin(2 * np.pi * hz(m) * t) * np.exp(-t * 2.4) * 0.35
        return out
    if kind == 'whoosh':
        t = tt(0.8)
        x = rng.standard_normal(len(t))
        y = np.zeros_like(x)
        a = 0.0
        for i in range(len(x)):
            c = 0.02 + 0.2 * np.sin(np.pi * i / len(x))
            a += c * (x[i] - a)
            y[i] = a
        return y * np.sin(np.pi * t / 0.8) ** 2 * 1.6
    if kind == 'hit':           # cinematic low accent
        t = tt(2.5)
        return (np.sin(2 * np.pi * (48 * t - 6 * t * t)) * np.exp(-t * 2.0) +
                0.25 * rng.standard_normal(len(t)) * np.exp(-t * 18)) * 0.9
    raise KeyError(kind)


def mix(ep, out_wav, dur=None):
    rng = np.random.default_rng(11)
    dur = dur or ep.DUR
    n = int(dur * SR)
    voice = np.zeros(n, np.float32)
    v = read_mono(ep.VOICE_WAV)
    off = int(getattr(ep, 'OFFSET', 0.0) * SR)
    voice[:max(0, min(n, len(v) - off))] = v[off:off + n]
    inten = env_at(ep.MUSIC, n)
    # score
    pl, pr = pad(n, np.random.default_rng(1), -0.0015), pad(n, np.random.default_rng(2), 0.0015)
    ar = arps(n, inten, rng)
    lo = pulse_low(n, inten)
    pad_g = 0.35 + 0.65 * inten
    musL = pl * pad_g + ar * 0.9 + lo
    musR = pr * pad_g + np.roll(ar, int(0.012 * SR)) * 0.9 + lo
    musL = musL + 0.35 * reverb(musL, seed=3)
    musR = musR + 0.35 * reverb(musR, seed=4)
    # fade in/out
    fade = np.minimum(1, np.minimum(np.arange(n) / (0.8 * SR), (n - np.arange(n)) / (2.5 * SR)))
    musL *= fade
    musR *= fade
    # duck under speech (smoothed voice envelope)
    hop = int(0.02 * SR)
    env = np.sqrt(np.convolve(voice ** 2, np.ones(hop) / hop, mode='same'))
    env = np.convolve(env, np.ones(int(0.25 * SR)) / int(0.25 * SR), mode='same')
    duck = 1 - 0.55 * np.clip(env / (env.max() * 0.25 + 1e-9), 0, 1)
    peak_v = np.abs(voice).max() + 1e-9
    mg = peak_v * 10 ** (-17 / 20) / (np.abs(musL).max() + 1e-9)
    L = voice + musL * mg * duck
    R = voice + musR * mg * duck
    # SFX
    for t, kind, gdb in getattr(ep, 'SFX', []):
        x = sfx(kind, rng).astype(np.float32)
        x *= peak_v * 10 ** (gdb / 20) / (np.abs(x).max() + 1e-9)
        s = int(t * SR)
        if s >= n:
            continue
        e = min(n, s + len(x))
        wet = x[:e - s] + 0.3 * reverb(np.pad(x[:e - s], (0, 0)), 1.6, 5)[:e - s]
        L[s:e] += wet
        R[s:e] += wet
    write_stereo(out_wav, L, R)
    return out_wav
