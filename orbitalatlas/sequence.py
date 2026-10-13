"""Shots joined by transitions on one timeline, and frame-sequence encoding through FFmpeg."""
import os
import subprocess
from multiprocessing import Pool


class Shot:
    def __init__(self, scene, duration, name=None):
        self.scene, self.duration, self.name = scene, float(duration), name or scene.name


class Sequence:
    """shots: [Shot]; transitions: list of len(shots)-1 items, each a Transition or None (hard cut).
    A transition of length d overlaps the last d seconds of shot i with the first d seconds of shot i+1
    (so total = sum(durations) - sum(transition durations)). The scenes are rendered at their own local time."""
    def __init__(self, shots, transitions=None):
        self.shots = list(shots); n = len(self.shots)
        self.transitions = list(transitions) if transitions is not None else [None] * (n - 1)
        if len(self.transitions) != n - 1: raise ValueError("need len(shots)-1 transitions")
        self.starts = []; t = 0.0
        for i, s in enumerate(self.shots):
            self.starts.append(t); d = self.transitions[i].duration if i < n - 1 and self.transitions[i] else 0.0; t += s.duration - d
        self.duration = self.starts[-1] + self.shots[-1].duration
        self.problems = self._validate()

    def _validate(self):
        p = []
        for i, tr in enumerate(self.transitions):
            if tr is None: continue
            a, b = self.shots[i], self.shots[i + 1]
            if tr.duration > a.duration or tr.duration > b.duration: p.append(f"transition {i} ({tr.name}, {tr.duration}s) longer than an adjacent shot")
            prev = self.transitions[i - 1].duration if i > 0 and self.transitions[i - 1] else 0.0
            if prev + tr.duration > a.duration + 1e-9: p.append(f"transitions around shot {i} overlap each other")
        return p

    def schedule(self):
        """machine-readable plan: shots with global times and transition windows (used by QA)."""
        sh = [dict(name=s.name, t0=self.starts[i], t1=self.starts[i] + s.duration) for i, s in enumerate(self.shots)]
        tr = []
        for i, t in enumerate(self.transitions):
            if t is None: tr.append(dict(index=i, kind="cut", t0=self.starts[i + 1], t1=self.starts[i + 1])); continue
            tr.append(dict(index=i, kind=t.name, t0=self.starts[i + 1], t1=self.starts[i] + self.shots[i].duration, declared=t.duration, ease=t.describe()["ease"]))
        return dict(duration=self.duration, shots=sh, transitions=tr)

    def _local(self, i, t): return self.shots[i].scene.start + (t - self.starts[i])

    def render(self, t):
        t = min(max(t, 0.0), self.duration - 1e-6)
        n = len(self.shots)
        for i in range(n - 1):
            tr = self.transitions[i]
            if tr is None: continue
            w0, w1 = self.starts[i + 1], self.starts[i] + self.shots[i].duration
            if w0 <= t < w1:
                a = self.shots[i].scene.render(self._local(i, t)); b = self.shots[i + 1].scene.render(self._local(i + 1, t))
                return tr(a, b, (t - w0) / (w1 - w0))
        for i in range(n - 1, -1, -1):
            if t >= self.starts[i]: return self.shots[i].scene.render(self._local(i, t))
        return self.shots[0].scene.render(self._local(0, t))


_SEQ = None


def _job(t): return _SEQ.render(t).tobytes()


def render_video(seq, path, fps=30, workers=4, audio=None, crf=18, preset="medium", log=print, frames=None):
    """render every frame (multiprocessing, fork) and pipe to ffmpeg -> H.264 (+ AAC if `audio` is a file). Returns frame count."""
    global _SEQ
    _SEQ = seq; W, H = seq.shots[0].scene.size
    n = int(round(seq.duration * fps)); times = [i / fps for i in range(n)] if frames is None else frames
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-"]
    if audio: cmd += ["-i", audio, "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(workers) as pool:
        for i, raw in enumerate(pool.imap(_job, times, chunksize=2)):
            proc.stdin.write(raw)
            if log and i % 60 == 0: log(f"  frame {i}/{len(times)}")
    proc.stdin.close(); rc = proc.wait()
    if rc: raise RuntimeError(f"ffmpeg exited {rc}")
    return len(times)
