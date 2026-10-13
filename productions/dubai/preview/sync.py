"""EP002 audio sync: real scene windows, smooth time warp (real -> estimated scene time) and captions from provider word timings.
The scene functions keep their ESTIMATED timeline (tw() cues at 145 wpm); a monotone cubic warp built from sentence-start anchors maps real time to that timeline,
so every cue lands on the real speech (error = within-sentence rate variation) and camera speed changes stay smooth. Nothing here calls any API."""
import os, json, re, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
VOICE = os.path.join(ROOT, 'narration', 'voice', 'narration.voice.json'); SCRIPT = os.path.join(ROOT, 'script_draft_v1_2.md')
LEAD, TAIL, PREROLL = 0.35, 2.4, 3.0
EXTRA = {'H4': 1.8}                                                                    # seconds of held final frame (silence inserted in the audio) so the title is readable
def vo_lines(): return [l[4:].strip() for l in open(SCRIPT, encoding='utf-8') if l.startswith('VO: ')]
def load():
    m = json.load(open(VOICE, encoding='utf-8')); words = m['words']; lines = vo_lines(); counts = [len(l.split()) for l in lines]
    assert sum(counts) == len(words), (sum(counts), len(words)); starts = np.cumsum([0] + counts)
    return m, words, [(int(starts[i]), int(starts[i + 1])) for i in range(len(lines))]
def pchip(x, y):
    """monotone cubic (Fritsch-Carlson) through increasing x, increasing y; returns f(t)"""
    x = np.asarray(x, float); y = np.asarray(y, float); h = np.diff(x); d = np.diff(y) / h; m = np.zeros_like(y)
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, len(x) - 1): m[i] = 0.0 if d[i - 1] * d[i] <= 0 else 2 * d[i - 1] * d[i] / (d[i - 1] + d[i])
    for i in range(len(d)):
        if d[i] == 0: m[i] = m[i + 1] = 0.0
        else:
            a, b = m[i] / d[i], m[i + 1] / d[i]; s = a * a + b * b
            if s > 9: tau = 3 / np.sqrt(s); m[i], m[i + 1] = tau * a * d[i], tau * b * d[i]
    def f(t):
        t = min(max(t, x[0]), x[-1]); i = min(max(np.searchsorted(x, t) - 1, 0), len(x) - 2); u = (t - x[i]) / h[i]
        return float((2 * u ** 3 - 3 * u * u + 1) * y[i] + (u ** 3 - 2 * u * u + u) * h[i] * m[i] + (-2 * u ** 3 + 3 * u * u) * y[i + 1] + (u ** 3 - u * u) * h[i] * m[i + 1])
    return f
def plan(scenes, extra=None):
    """scenes: [(id, est_start, est_dur, [vo line numbers])] -> ({id: window}, offset). window: start/end/dur on the FINAL timeline (extras included), warp(t_real_local) -> est local time,
    words (local, spoken times), audio = (a0, a1, delay) narration slice [a0, a1) (seconds of the original file) played at final time start (+ delay)."""
    extra = EXTRA if extra is None else extra
    m, words, lw = load(); offset = PREROLL + LEAD - words[0]['start']; rows = []
    for sid, st, d_est, vos in scenes:
        if not vos: rows.append([sid, 0.0, PREROLL, d_est, None, None]); continue
        a, b = lw[vos[0] - 1][0], lw[vos[-1] - 1][1]; rows.append([sid, words[a]['start'] + offset - LEAD, None, d_est, a, b])
    for i, r in enumerate(rows):
        if r[2] is None: r[2] = rows[i + 1][1] if i + 1 < len(rows) else words[r[5] - 1]['end'] + offset + TAIL
    out, shift = {}, 0.0
    for sid, s0, e0, d_est, a, b in rows:
        ex = extra.get(sid, 0.0)
        if a is None: out[sid] = dict(start=s0 + shift, end=e0 + shift, dur=e0 - s0, warp=lambda t: t, words=[], audio=None, anchors=[]); shift += ex; continue
        n = b - a; tw = lambda k: 0.5 + k * (d_est - 1.1) / n; ax, ay = [0.0], [0.0]
        for k in range(n):                                                                    # sentence starts only (smooth warp)
            prev = words[a + k - 1]['text'] if k else ''
            if k == 0 or re.search(r'[.?!]["\')]?$', prev):
                r_ = words[a + k]['start'] + offset - s0
                if r_ > ax[-1] + 0.2 and tw(k) > ay[-1] + 0.05: ax.append(r_); ay.append(tw(k))
        sp = e0 - s0
        if sp > ax[-1] + 0.2 and d_est > ay[-1] + 0.05: ax.append(sp); ay.append(d_est)
        else: ax[-1], ay[-1] = sp, d_est
        a0 = s0 - offset; delay = max(0.0, -a0); a0 = max(a0, 0.0)
        out[sid] = dict(start=s0 + shift, end=e0 + shift + ex, dur=sp + ex, speech_dur=sp, warp=pchip(ax, ay) if len(ax) > 1 else (lambda t, k=d_est / sp: t * k), anchors=list(zip(ax, ay)),
                        words=[dict(text=w['text'], start=w['start'] + offset - s0, end=w['end'] + offset - s0) for w in words[a:b]], audio=(a0, e0 - offset, delay)); shift += ex
    return out, offset
def assemble_audio(win, out_wav, narration=None, rate=44100):
    """place the narration slices on the final timeline (silence elsewhere) -> mono 16-bit wav"""
    import subprocess, wave
    narration = narration or os.path.join(ROOT, 'narration', 'voice', 'narration.mp3')
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', narration, '-f', 's16le', '-ac', '1', '-ar', str(rate), '-'], capture_output=True, check=True).stdout
    nar = np.frombuffer(raw, np.int16); total = int(round(max(w['end'] for w in win.values()) * rate)) + rate; buf = np.zeros(total, np.int16)
    for sid, w in win.items():
        if not w['audio']: continue
        a0, a1, delay = w['audio']; seg = nar[int(a0 * rate):int(min(a1, len(nar) / rate) * rate)].astype(np.float32); f = int(0.02 * rate)
        if len(seg) > 2 * f: seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        p = int(round((w['start'] + delay) * rate)); buf[p:p + len(seg)] = np.clip(seg, -32768, 32767).astype(np.int16)[:max(0, total - p)]
    with wave.open(out_wav, 'wb') as f: f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate); f.writeframes(buf.tobytes())
    return total / rate
def cues(words, maxw=8, maxc=70, maxd=4.2):
    """caption cues from word timings: phrase-sized, break after punctuation once >= 3 words, cap words/chars/duration; times = spoken times (no estimation)"""
    out, cur = [], []
    def flush():
        if cur: out.append([cur[0]['start'], cur[-1]['end'], ' '.join(w['text'] for w in cur)])
    for w in words:
        cur.append(w); txt = ' '.join(x['text'] for x in cur); brk = (re.search(r'[.?!]$', w['text']) and len(cur) >= 2) or (re.search(r'[,;:]$', w['text']) and len(cur) >= 3)
        if brk or len(cur) >= maxw or len(txt) >= maxc or (w['end'] - cur[0]['start']) >= maxd: flush(); cur = []
    flush()
    for i in range(len(out) - 1):
        if 0 < out[i + 1][0] - out[i][1] < 0.35: out[i][1] = out[i + 1][0]                      # close tiny gaps; never overlap
    return out
