"""ATLAS + projection as one layer for any renderer (the yt-render v3 'long' pipeline uses it).

    layer = AtlasLayer.from_spec(spec, words, voice_wav, frame_size=(1920, 1080), voice_start=0.0)
    info = layer.render(frame_rgba, t)          # after footage/diagrams, before text and credits

spec (timeline "atlas" block):
    {"host": {"x": 250, "y": 985, "height": 400, "on": [[0, 21.5]]},
     "projection": {"box": [330, 318, 680, 578],
                    "pages": [{"at": {"phrase": "Orion moved"}, "title": "EARTH TO ORION", "kind": "link"}, ...],
                    "end": {"word": 112, "edge": "end", "offset": 0.4}}}

ATLAS is the approved drawing (hero_approved_clean.png, checksum-verified by papercut.host). He moves only as
a whole cutout (idle preset), blinks, and his mouth follows the narration loudness while words are spoken.
No limbs or joints are animated. The projection opens from his raised glove (papercut.projection).
"""
from __future__ import annotations

import math
import subprocess

import numpy as np

from .actor import Actor, ActorCue
from .projection import DEFAULT_BOX, ProjectionEngine, cues_from_script

HERO_SIZE = (518, 733)
HAND_IN_HERO = (452.0, 318.0)          # open raised glove (palm centre) in hero px (approved test v4)
HEAD_IN_HERO = (40, 60, 400, 400)      # helmet + face: projection, text and callouts stay off it
BLINK_GAPS = (3.0, 2.4, 2.6, 2.5, 4.2, 1.7, 3.3)   # rhythm of the approved test, repeated
FPS = 30


def speech_intervals(words, gap=0.3):
    out = []
    for w in words:
        if out and w["start"] - out[-1][1] <= gap:
            out[-1][1] = w["end"]
        else:
            out.append([w["start"], w["end"]])
    return [tuple(x) for x in out]


def auto_blinks(t0, t1, first=1.4):
    out, t, k = [], t0 + first, 0
    while t < t1 - 0.3:
        out.append(round(t, 3))
        t += BLINK_GAPS[k % len(BLINK_GAPS)]
        k += 1
    return out


def loudness_envelope(wav_path, n_frames, start=0.0, fps=FPS, sr=16000):
    """Per-frame narration loudness 0..~1 on the video timeline (ffmpeg decode, analysis only)."""
    p = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(wav_path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                       capture_output=True, check=True)
    x = np.frombuffer(p.stdout, np.float32)
    pad = int(round(start * sr))
    x = np.concatenate([np.zeros(pad, np.float32), x])
    hop = sr // fps
    need = n_frames * hop
    x = np.pad(x, (0, max(0, need - len(x))))[:need]
    env = np.sqrt((x.reshape(n_frames, hop) ** 2).mean(1) + 1e-12)
    loud = env[env > 1e-4]
    env = env / (np.percentile(loud, 90) + 1e-9) if len(loud) else env * 0
    return np.convolve(env, [0.25, 0.5, 0.25], mode="same")


def quantize_mouth(env, hold=2):
    """3 mouth states with a minimum hold, so the mouth never flickers frame to frame."""
    lv = np.where(env > 0.45, 0.8, np.where(env > 0.15, 0.3, 0.0))
    out = lv.copy()
    i = 0
    while i < len(out):
        j = i
        while j < len(out) and lv[j] == lv[i]:
            j += 1
        if j - i < hold and i > 0:
            out[i:j] = out[i - 1]
        i = j
    return out


def rects_hit(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


class AtlasLayer:
    def __init__(self, frame_size, host, cues, box=DEFAULT_BOX, mouth=None, fps=FPS):
        self.W, self.H = frame_size
        self.fps = fps
        x, y, height = float(host["x"]), float(host["y"]), float(host.get("height", 400 * self.H / 1080))
        self.height = height
        on = host["on"]
        speech = host.get("talk", [])
        self.mouth = mouth
        acues = []
        for a, b in on:
            talk = [(max(a, s), min(b, e)) for s, e in speech if e > a and s < b]
            acues.append(ActorCue(a, b, "hero", x, y, height, host.get("preset", "idle"), talk=talk,
                                  blinks=auto_blinks(a, b), pop=False, enter=host.get("enter"), exit=host.get("exit"),
                                  name=f"atlas@{a:g}"))
        env = (lambda t: float(mouth[min(len(mouth) - 1, int(round(t * fps)))])) if mouth is not None else None
        self.actor = Actor(frame_size, acues, envelope=env)
        self.on = [tuple(x) for x in on]
        self.projection = ProjectionEngine(cues, box=box, frame_size=frame_size) if cues else None
        # the projection may only be open while ATLAS is on screen (it comes out of his glove)
        for c in (cues or []):
            if not any(a - 1e-6 <= c.start and c.end <= b + 1e-6 for a, b in self.on):
                raise ValueError(f"projection page {c.title!r} ({c.start:.2f}-{c.end:.2f}s) is not inside an ATLAS window")
        k = height / HERO_SIZE[1]
        self.head = [x + (HEAD_IN_HERO[0] - HERO_SIZE[0] / 2) * k, y + (HEAD_IN_HERO[1] - HERO_SIZE[1]) * k,
                     x + (HEAD_IN_HERO[2] - HERO_SIZE[0] / 2) * k, y + (HEAD_IN_HERO[3] - HERO_SIZE[1]) * k]
        if self.projection and rects_hit(self.projection.box, [v + d for v, d in zip(self.head, (-12, -12, 12, 12))]):
            raise ValueError(f"projection box {self.projection.box} covers ATLAS's face/helmet {[round(v) for v in self.head]}")

    @classmethod
    def from_spec(cls, spec, words, voice_wav, frame_size=(1920, 1080), duration=None, voice_start=0.0, fps=FPS):
        if not isinstance(spec, dict) or set(spec) - {"host", "projection"} or "host" not in spec:
            raise ValueError("atlas must be {host: {...}, projection: {...}}")
        h = spec["host"]
        if not isinstance(h, dict) or set(h) - {"x", "y", "height", "on", "preset", "enter", "exit"}:
            raise ValueError("atlas.host takes x, y (feet line), height, on [[t0, t1], ...], preset, enter, exit")
        if duration is None:
            raise ValueError("duration is required")
        on = h.get("on", [[0.0, duration]])
        if not isinstance(on, list) or not on or any(not (isinstance(w, list) and len(w) == 2 and 0 <= w[0] < w[1] <= duration + 1e-6) for w in on):
            raise ValueError("atlas.host.on must be [[t0, t1], ...] inside the video")
        if h.get("preset", "idle") not in ("idle", "explain", "listen", "surprise"):
            raise ValueError("atlas.host.preset must be idle, explain, listen or surprise")
        host = dict(h, on=[(float(a), float(b)) for a, b in on], talk=speech_intervals(words or []))
        cues, box = [], DEFAULT_BOX
        pj = spec.get("projection")
        if pj:
            if not isinstance(pj, dict) or set(pj) - {"box", "pages", "end", "lead"}:
                raise ValueError("atlas.projection takes box, pages, end, lead")
            box = tuple(pj.get("box", DEFAULT_BOX))
            cues = cues_from_script(pj.get("pages"), words or [], end=pj.get("end"), lead=float(pj.get("lead", 0.15)))
        n = int(round(duration * fps))
        mouth = quantize_mouth(loudness_envelope(voice_wav, n, voice_start, fps)) if voice_wav else None
        return cls(frame_size, host, cues, box=box, mouth=mouth, fps=fps)

    def hand_point(self, st):
        """Screen position of the raised glove for the current whole-cutout state (same affine as the actor)."""
        s, r = st["scale"], math.radians(st["roll_deg"])
        k = self.height / HERO_SIZE[1]
        du, dv = (HAND_IN_HERO[0] - HERO_SIZE[0] / 2) * k, (HAND_IN_HERO[1] - HERO_SIZE[1]) * k
        return st["x"] + s * (math.cos(r) * du - math.sin(r) * dv), st["y"] + s * (math.sin(r) * du + math.cos(r) * dv)

    def screen_share(self, duration):
        return sum(min(b, duration) - a for a, b in self.on) / duration

    def pages(self):
        return [] if not self.projection else [
            {"start": c.start, "end": c.end, "title": c.title, "kind": c.kind} for c in self.projection.cues]

    def render(self, frame, t):
        cue, st = self.actor.state(t)
        if cue is None:
            return None
        hand = self.hand_point(st)
        pj = self.projection.render(frame, t, hand) if self.projection else None     # behind ATLAS, like the approved test
        info = self.actor.render(frame, t)
        return {"t": round(t, 4), "hand": [round(hand[0], 2), round(hand[1], 2)], "head": [round(v, 1) for v in self.head],
                "bbox": info.get("bbox") if info else None, "drawing": info.get("drawing") if info else None,
                "projection": pj}
