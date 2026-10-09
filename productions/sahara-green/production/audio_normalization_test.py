#!/usr/bin/env python3
"""EP001 audio normalisation TEST (separate file; the locked narration and the approved master are not touched).
Goal: about -16 LUFS integrated without clipping and without changing voice, wording, speed or timing.
Method: ONE constant linear gain (no compression, no EQ, no time change) = target minus measured integrated loudness, then a short look-ahead
peak limiter that acts only on the few samples that would exceed the ceiling (Hann-shaped dip of 6 ms), ceiling chosen so the TRUE peak stays <= -1.5 dBTP.
  python3 audio_normalization_test.py WORKDIR"""
import hashlib, json, os, re, subprocess, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); NAR = os.path.join(os.path.dirname(HERE), 'narration', 'voice'); SRC = os.path.join(NAR, 'narration.wav')
TARGET, TP_CEIL = -16.0, -1.5
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()
def measure(path, extra=''):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', '-i', path, '-af', f'loudnorm=I={TARGET}:TP={TP_CEIL}:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
    j = json.loads(r.stderr[r.stderr.rfind('{'):r.stderr.rfind('}') + 1])
    r2 = subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True)
    sm = r2.stderr[r2.stderr.rfind('Summary:'):]
    g = lambda k: float(re.search(k + r':\s*(-?[\d.]+)', sm).group(1))
    return {'integrated_lufs': float(j['input_i']), 'true_peak_dbtp': float(j['input_tp']), 'lra_lu': float(j['input_lra']), 'ebur128_integrated': g('I'), 'ebur128_lra': g('LRA'), 'ebur128_true_peak_dbfs': g('Peak')}
def read(path):
    w = wave.open(path); n = w.getnframes(); fs = w.getframerate(); ch = w.getnchannels(); assert w.getsampwidth() == 2
    x = np.frombuffer(w.readframes(n), '<i2').astype(np.float64) / 32768; return x.reshape(-1, ch), fs
def write(path, x, fs):
    y = np.clip(np.round(x * 32768), -32768, 32767).astype('<i2')
    with wave.open(path, 'wb') as w: w.setnchannels(x.shape[1]); w.setsampwidth(2); w.setframerate(fs); w.writeframes(y.tobytes())
def limit(y, ceiling, fs, ms=3.0):
    """gain reduction only where |y| > ceiling: a Hann-shaped dip of +-ms around each offending sample (the smoothest way to remove an isolated peak)"""
    a = np.abs(y).max(axis=1); idx = np.nonzero(a > ceiling)[0]; N = int(fs * ms / 1000); g = np.ones(len(y))
    prof = 0.5 * (1 + np.cos(np.linspace(-np.pi, np.pi, 2 * N + 1)))
    for i in idx:
        r = ceiling / a[i]; lo, hi = max(0, i - N), min(len(y), i + N + 1); seg = 1 - (1 - r) * prof[(lo - (i - N)):(hi - (i - N))]
        g[lo:hi] = np.minimum(g[lo:hi], seg)
    return y * g[:, None], g, idx
def main(work):
    os.makedirs(work, exist_ok=True); src_hash = sha(SRC); x, fs = read(SRC)
    before = measure(SRC); gain_db = TARGET - before['integrated_lufs']; lin = 10 ** (gain_db / 20)
    for ceil_db in (-1.8, -2.1, -2.4, -2.8):
        y, g, idx = limit(x * lin, 10 ** (ceil_db / 20), fs); out = os.path.join(work, 'narration_norm16_test.wav'); write(out, y, fs); after = measure(out)
        if after['true_peak_dbtp'] <= TP_CEIL + 0.05: break
    unaffected = g == 1.0
    ratio = np.abs(y[unaffected] - x[unaffected] * lin).max() if unaffected.any() else 0.0
    reduction_db = -20 * np.log10(g.min())
    res = {'schema': 'ep001-audio-normalisation-test/1', 'source': 'productions/sahara-green/narration/voice/narration.wav (locked, untouched)', 'source_sha256': src_hash, 'source_sha256_after_test': sha(SRC),
           'target_lufs': TARGET, 'true_peak_ceiling_dbtp': TP_CEIL,
           'before': before, 'after': after, 'gain_applied_db': round(gain_db, 2), 'limiter': {'ceiling_dbfs': ceil_db, 'samples_over_ceiling': int(len(idx)), 'share_of_samples_touched': round(float((~unaffected).mean()), 6),
           'seconds_touched': round(float((~unaffected).sum() / fs), 2), 'max_gain_reduction_db': round(float(reduction_db), 2), 'window_ms': 6},
           'method_check': {'samples_in': int(len(x)), 'samples_out': int(len(y)), 'sample_rate': fs, 'duration_s_in': round(len(x) / fs, 3), 'duration_s_out': round(len(y) / fs, 3),
                            'max_abs_deviation_from_pure_gain_outside_limiter': float(ratio), 'clipped_samples_out': int((np.abs(y) >= 1.0).sum()), 'sample_peak_out_dbfs': round(float(20 * np.log10(np.abs(y).max())), 2)},
           'current_master_for_comparison': {'renderer_gain_db': -0.8, 'integrated_lufs': -17.8, 'true_peak_dbtp': -4.6, 'why': 'the renderer applies min(target - measured, ceiling - true peak): the raw true peak is -0.7 dBTP, so it cannot raise the level and even lowers it by 0.8 dB'},
           'output': out, 'output_sha256': sha(out)}
    json.dump(res, open(os.path.join(HERE, 'audio_test', 'AUDIO_NORMALIZATION_TEST.json'), 'w'), indent=1); print(json.dumps(res, indent=1))
if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'audio_test'), exist_ok=True); main(sys.argv[1])
