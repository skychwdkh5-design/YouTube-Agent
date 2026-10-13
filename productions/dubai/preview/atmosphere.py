"""EP002 hook atmosphere: a locally synthesised low drone under the silent cold open (no music, no stock audio, no API). Deterministic (fixed seed).
    python3 atmosphere.py NORMALISED_NARRATION.wav OUT.wav [--peak-lufs -28]
The narration file is NOT modified: OUT = narration + atmosphere, and the script asserts that OUT - atmosphere equals the narration sample for sample.
Design: two detuned pairs of low partials (E1 41.2, B1 61.7, E2 82.4, B2 123.5 Hz, +/-0.35 Hz between channels), low-passed noise bed (<= 160 Hz), a slow 0.12 Hz breathing,
raised-cosine swell from silence (peak at 2.9 s), still audible when the voice starts (3.35 s), then a long raised-cosine release to silence by 6.2 s (no hit, no riser noise)."""
import sys, subprocess, re, wave, numpy as np
SR = 48000
def synth(dur=8.0, seed=2026, peak_t=2.9, end_t=6.2):
    n = int(dur * SR); t = np.arange(n) / SR; rng = np.random.default_rng(seed); out = np.zeros((2, n))
    for ch, sgn in enumerate((-1, 1)):
        for f, a in ((41.2, 1.0), (61.7, 0.55), (82.4, 0.45), (123.5, 0.22), (164.8, 0.08)):
            ph = rng.uniform(0, 2 * np.pi); out[ch] += a * np.sin(2 * np.pi * (f + sgn * 0.35 * (f / 82.4)) * t + ph)
        nz = rng.standard_normal(n); F = np.fft.rfft(nz); fr = np.fft.rfftfreq(n, 1 / SR); F *= 1 / np.sqrt(np.maximum(fr, 20)) * (fr < 160)
        bed = np.fft.irfft(F, n); out[ch] += 0.55 * bed / np.std(bed)
    out *= (1 + 0.12 * np.sin(2 * np.pi * 0.12 * t))[None]                                    # slow breathing
    env = np.zeros(n); up = t <= peak_t; env[up] = np.sin(0.5 * np.pi * (t[up] / peak_t)) ** 2   # swell from silence
    dn = t > peak_t; u = np.clip((t[dn] - peak_t) / (end_t - peak_t), 0, 1); env[dn] = 0.5 * (1 + np.cos(np.pi * u)) ** 2.4   # release: about -6 dB one second into the speech, -26 dB two seconds later
    out *= env[None]; return out / np.abs(out).max() * 0.5                                 # normalised to half scale; the final level is set by loudness below
def momentary_peak_lufs(x):
    """highest momentary (400 ms) loudness of the atmosphere alone, measured with ffmpeg ebur128"""
    pcm = (np.clip(x, -1, 1).T * 32767).astype('<i2').tobytes()
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-loglevel', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '2', '-i', '-', '-af', 'ebur128=metadata=1,ametadata=print:key=lavfi.r128.M:file=-', '-f', 'null', '-'], input=pcm, capture_output=True)
    vals = [float(m) for m in re.findall(r'lavfi\.r128\.M=(-?\d+\.?\d*)', r.stdout.decode()) if float(m) > -70]
    return max(vals)
def main(argv):
    src, dst = argv[0], argv[1]; target = float(argv[argv.index('--peak-lufs') + 1]) if '--peak-lufs' in argv else -28.0
    with wave.open(src, 'rb') as f: assert f.getframerate() == SR and f.getnchannels() == 2 and f.getsampwidth() == 2; nar_int = np.frombuffer(f.readframes(f.getnframes()), '<i2').reshape(-1, 2).T.astype(np.int32)
    a = synth(); g = 10 ** ((target - momentary_peak_lufs(a)) / 20); a *= g
    q = lambda x: np.round(np.clip(x, -1, 1) * 32767).astype(np.int32)
    nar_q, a_q = nar_int, q(a); n = min(a_q.shape[1], nar_q.shape[1]); mix_q = nar_q.copy(); mix_q[:, :n] += a_q[:, :n]
    clipped = int((np.abs(mix_q) > 32767).sum()); mix_q = np.clip(mix_q, -32768, 32767)
    exact = bool(((mix_q[:, :n] - a_q[:, :n]) == nar_q[:, :n]).all() and (mix_q[:, n:] == nar_q[:, n:]).all())     # integer sum: narration = mix - atmosphere, sample for sample
    with wave.open(dst, 'wb') as f: f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes(mix_q.astype('<i2').T.tobytes())
    print({'atmosphere_gain_db': round(float(20 * np.log10(g)), 2), 'atmosphere_peak_momentary_lufs': target, 'mix_sample_peak_dbfs': round(float(20 * np.log10(np.abs(mix_q).max() / 32768)), 2), 'clipped_samples': clipped, 'narration_recoverable_exactly': exact})
if __name__ == '__main__': main(sys.argv[1:])
