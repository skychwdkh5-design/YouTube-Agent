#!/usr/bin/env python3
"""motion.py - the motion-graphics finishing pass for pipeline releases.

Why: on 2026-11-21 the owner rejected the El Nino and Ice releases as a "slideshow": zoom in, zoom out, hard cuts and
plain labels. He asked for designed transitions, more motion graphics and the motion-graphics subtitles he approved on
2026-11-16 (production/kinetic_captions). This pass runs on the rendered base video (yt-render, labels and burned credits
off) and adds, frame by frame:

  * kinetic captions from the narration word timings: words pop in on their spoken time, key words get the yellow
    accent box, big numbers count up in a slammed "hero" box (kcaps.Captions / kcaps.Hero, approved style);
  * a thin HUD (corner brackets, channel tag, a running-time ring) and a per-shot source line
    ("ARCHIVE // NASA OPERATION ICEBRIDGE // FILMED IN ALASKA") so other-place footage is always labelled on screen;
  * designed transitions on every cut: whip pan with motion blur, zoom punch with zoom blur, light-leak flash and an
    RGB-split glitch, each with a matching whoosh;
  * a sound layer: original synthesised ambient pad (no third-party music, no licence needed), whooshes on the cuts and
    a low hit on every hero number. Mixed UNDER the narration (owner 2026-11-22: transition sounds must never be louder
    than the voice): effects peak about 20 dB below full scale and the whole effects bed is side-chain ducked by the
    narration, then the mix is loudness-normalised to -16 LUFS.

The cover frame (everything before the first shot after the cover) is passed through untouched, so the cover = frame 0
check still holds. Captions and HUD stop before the end-screen tail so YouTube's end-screen elements sit on a clean
picture.

    python3 pipeline/motion.py --base base.mp4 --timeline timeline.json --rights rights.json \
        --voice voice.json --spec motion.json --out final.mp4 [--start 0 --dur 30] [--frames 3,12.5]

motion.json:
  {"keywords": ["EQUATOR", ...], "replace": {"Two": "II"},
   "heroes": [{"at": "sixteen thousand", "dur": 2.4, "big": "16,000", "above": "SUMMIT", "below": "FEET HIGH"}],
   "transitions": {"<shot id>": "whip_l|whip_r|zoom|flash|glitch|none"},
   "channel_tag": "NEXORA",                   # HUD tag, default ORBITAL ATLAS
   "labels": {"<asset src>": "ARCHIVE // ..."}, "no_captions": ["<shot id>"], "music": true,
   "text_mode": "kinetic" | "callouts",        # callouts = owner rule 2026-11-17: only 2-4 word paper callouts
   "callouts": [{"t": [t0, t1], "text": "BREAKING APART", "pos": [x, y], "accent": false}]}
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "production" / "kinetic_captions"))
from kcaps import MONO, Captions, Hero, Style, font as kfont  # noqa: E402

W, H, FPS, SR = 1920, 1080, 30, 48000
WIN = 0.24                      # half-length of a transition, seconds
CYCLE = ("whip_l", "zoom", "flash", "whip_r", "glitch", "zoom")
KINDS = CYCLE + ("none",)


# ------------------------------------------------------------------ timeline helpers
def shot_list(tl):
    return sorted(tl.get("shots", []), key=lambda s: s["start"])


def first_picture(tl):
    """Start of the first shot after the cover frame."""
    for s in shot_list(tl):
        if s["start"] > 0:
            return float(s["start"])
    return 0.0


def cuts(tl, spec):
    shots = shot_list(tl)
    f0 = first_picture(tl)
    out, k = [], 0
    for prev, s in zip(shots, shots[1:]):
        T = float(s["start"])
        if T <= f0 + 1e-6:
            continue
        kind = (spec.get("transitions") or {}).get(s.get("id"))
        if kind is None:
            kind = CYCLE[k % len(CYCLE)]
            k += 1
        if kind not in KINDS:
            raise SystemExit(f"motion: unknown transition {kind!r} on shot {s.get('id')}")
        out.append({"t": T, "shot": s.get("id"), "kind": kind})
    return out


def shot_at(tl, t):
    cur = None
    for s in shot_list(tl):
        if s["start"] <= t:
            cur = s
    return cur


# ------------------------------------------------------------------ picture effects
def _blur1d(a, k, axis):
    k = int(k)
    if k < 2:
        return a
    h = k // 2
    n = a.shape[axis]
    pad = [(0, 0)] * a.ndim
    pad[axis] = (h + 1, h)
    p = np.pad(a, pad, mode="edge")
    c = np.cumsum(p, axis=axis, dtype=np.float32)
    hi = np.take(c, np.arange(2 * h + 1, 2 * h + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return (hi - lo) / (2 * h + 1)


def _scale(img: Image.Image, z):
    if abs(z - 1) < 1e-3:
        return img
    w, h = int(W * z), int(H * z)
    big = img.resize((w, h), Image.Resampling.BILINEAR)
    x0, y0 = (w - W) // 2, (h - H) // 2
    return big.crop((x0, y0, x0 + W, y0 + H))


_LEAK = None


def _leak():
    global _LEAK
    if _LEAK is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W * 0.85) / W) ** 2 + ((yy - H * 0.15) / H) ** 2)
        g = np.clip(1.2 - r * 1.3, 0, 1) ** 1.6
        col = np.array([255, 196, 120], np.float32)
        _LEAK = g[..., None] * col
    return _LEAK


def transition(img: Image.Image, t, cut, idx):
    d = t - cut["t"]
    if abs(d) >= WIN or cut["kind"] == "none":
        return img
    s = 1 - abs(d) / WIN
    e = s * s
    kind = cut["kind"]
    if kind in ("whip_l", "whip_r"):
        sgn = -1 if kind == "whip_l" else 1
        a = np.asarray(img, np.float32)
        a = _blur1d(a, 6 + 220 * e, axis=1)
        shift = int(sgn * 1100 * e) if d < 0 else int(-sgn * 1100 * e)
        a = np.roll(a, shift, axis=1) * (1 + 0.18 * e)
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if kind == "zoom":
        z = 1 + 0.55 * e
        layers = [np.asarray(_scale(img, z * f), np.float32) for f in (1.0, 0.94, 0.88)]
        a = (layers[0] * 0.45 + layers[1] * 0.33 + layers[2] * 0.22) * (1 + 0.15 * e)
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if kind == "flash":
        a = np.asarray(img, np.float32)
        L = s ** 1.4
        a = a + _leak() * (1.1 * L) + 255 * 0.55 * L ** 2.2
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if kind == "glitch":
        a = np.asarray(img, np.float32).copy()
        k = int(48 * e)
        a[..., 0] = np.roll(a[..., 0], k, axis=1)
        a[..., 2] = np.roll(a[..., 2], -k, axis=1)
        rng = np.random.default_rng(idx)
        for _ in range(int(10 * e) + 1):
            y0 = int(rng.integers(0, H - 40)); hh = int(rng.integers(12, 90))
            a[y0:y0 + hh] = np.roll(a[y0:y0 + hh], int(rng.integers(-1, 2) * 160 * e), axis=1)
        a = a * (1 + 0.2 * e)
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return img


# ------------------------------------------------------------------ captions, HUD, source line
class LongCaptions(Captions):
    """Approved kinetic captions; the HUD ring shows the running time m:ss for long videos."""

    def __init__(self, *a, hud_until=None, **k):
        super().__init__(*a, **k)
        self.hud_until = hud_until

    def _hud(self, frame, t):
        if self.hud_until is not None and t > self.hud_until:
            return
        st = self.st
        d = ImageDraw.Draw(frame)
        c = (255, 255, 255, 150)
        m, L = 44, 46
        for (x, y, sx, sy) in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
            d.line((x, y, x + sx * L, y), fill=c, width=3)
            d.line((x, y, x, y + sy * L), fill=c, width=3)
        cx, cy, r = W - 120, 112, 34
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, 70), width=3)
        frac = min(1.0, t / self.duration)
        d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * frac, fill=(*st.accent, 255), width=4)
        mf = ImageFont.truetype(MONO, 18)
        s = f"{int(t) // 60}:{int(t) % 60:02d}"
        tw = d.textlength(s, font=mf)
        d.text((cx - tw / 2, cy - 11), s, font=mf, fill=(255, 255, 255, 230))
        tf = kfont(800, 22)
        d.text((m + 18, m + 14), st.channel_tag, font=tf, fill=(255, 255, 255, 220))
        d.rectangle((m + 18, m + 46, m + 18 + 36, m + 50), fill=(*st.accent, 255))


def find_phrase(words, phrase, after=0.0):
    toks = [re.sub(r"[^\w]", "", x).lower() for x in phrase.split()]
    core = [re.sub(r"[^\w]", "", w["text"]).lower() for w in words]
    for i in range(len(words) - len(toks) + 1):
        if words[i]["start"] >= after and core[i:i + len(toks)] == toks:
            return words[i]["start"]
    raise SystemExit(f"motion: hero phrase not in narration: {phrase!r}")


def build_heroes(spec, words):
    out = []
    for h in spec.get("heroes", []):
        t0 = find_phrase(words, h["at"], h.get("after", 0.0)) - 0.05
        out.append(Hero(t0, t0 + float(h.get("dur", 2.4)), h["big"], h.get("above", ""), h.get("below", ""),
                        h.get("count_up", True)))
    return out


def source_line(tl, rights, spec, shot):
    if not shot or not shot.get("layers"):
        return ""
    L = shot["layers"][0]
    src = ((tl.get("assets") or {}).get(L.get("asset")) or {}).get("src", "")
    lab = (spec.get("labels") or {}).get(src)
    if lab is not None:
        return lab
    r = next((a for a in rights.get("assets", []) if a["src"] == src), {})
    credit = (r.get("credit") or "").upper()
    if not credit:
        return ""
    head = "ARCHIVE" if r.get("footage") in ("live", "animation") else "SOURCE"
    return f"{head}  //  {credit}"


# ------------------------------------------------------------------ paper callouts (owner rule 2026-11-17)
CREAM, ORANGE, INK = (250, 241, 224), (255, 138, 61), (24, 20, 18)


class Callouts:
    """Short 2-4 word paper callouts next to the object, cream card + orange accent, smooth entrance, calm hold.

    spec "callouts": [{"t": [t0, t1], "text": "BREAKING APART", "pos": [x, y], "accent": false}]
    """

    def __init__(self, items):
        self.items = []
        for c in items:
            words = c["text"].split()
            if not 1 <= len(words) <= 5:
                raise SystemExit(f"motion: callout must be short: {c['text']!r}")
            self.items.append({"t0": float(c["t"][0]), "t1": float(c["t"][1]), "text": c["text"].upper(),
                               "pos": tuple(c.get("pos") or (120, 150)), "accent": bool(c.get("accent"))})
        self.f = kfont(800, 50)

    def render(self, frame, t):
        for c in self.items:
            if not (c["t0"] <= t < c["t1"]):
                continue
            u_in = min(1.0, (t - c["t0"]) / 0.35)
            u_in = 1 - (1 - u_in) ** 3
            u_out = max(0.0, min(1.0, (t - (c["t1"] - 0.3)) / 0.3))
            a = u_in * (1 - u_out)
            if a <= 0.01:
                continue
            x, y = c["pos"]
            y += (1 - u_in) * 24
            tw = int(self.f.getlength(c["text"]))
            pad_x, h = 26, 78
            card = Image.new("RGBA", (tw + pad_x * 2 + 12, h + 8), (0, 0, 0, 0))
            d = ImageDraw.Draw(card)
            d.rounded_rectangle((4, 6, tw + pad_x * 2 + 8, h + 6), 10, fill=(0, 0, 0, 90))          # soft paper shadow
            bg = ORANGE if c["accent"] else CREAM
            d.rounded_rectangle((0, 0, tw + pad_x * 2, h), 10, fill=(*bg, 255))
            d.rectangle((0, 10, 8, h - 10), fill=(*(INK if c["accent"] else ORANGE), 255))
            d.text((pad_x + 4, h / 2), c["text"], font=self.f, fill=(*INK, 255), anchor="lm")
            if a < 1:
                card.putalpha(card.getchannel("A").point(lambda v: int(v * a)))
            frame.alpha_composite(card, (int(x), int(y)))


# ------------------------------------------------------------------ sound
def _env(n, peak):
    x = np.arange(n, dtype=np.float32)
    up = np.clip(x / max(1, peak), 0, 1) ** 2
    down = np.clip(1 - (x - peak) / max(1, n - peak), 0, 1) ** 1.5
    return np.where(x < peak, up, down)


def whoosh(rng, dur=0.62, bright=1.0):
    n = int(dur * SR)
    noise = rng.standard_normal(n).astype(np.float32)
    out = np.empty(n, np.float32)
    y = 0.0
    cut = _env(n, int(n * 0.52))
    for i in range(n):                     # one-pole low-pass whose cutoff sweeps with the envelope
        a = 0.015 + 0.25 * bright * cut[i]
        y += a * (noise[i] - y)
        out[i] = y
    out *= _env(n, int(n * 0.52))
    return out / (np.abs(out).max() + 1e-6)


def hit(rng, dur=0.9):
    n = int(dur * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (52 + 30 * np.exp(-t * 18)) * t) * np.exp(-t * 4.5)
    click = rng.standard_normal(n) * np.exp(-t * 60) * 0.25
    s = (body + click).astype(np.float32)
    return s / (np.abs(s).max() + 1e-6)


def ambient_pad(dur):
    """Original synthesised pad: slow Dm - Bb - F - C changes, soft partials, gentle movement."""
    n = int(dur * SR)
    chords = [(73.42, 146.83, 220.0, 293.66, 349.23), (58.27, 116.54, 174.61, 233.08, 293.66),
              (87.31, 174.61, 220.0, 261.63, 349.23), (65.41, 130.81, 196.0, 261.63, 329.63)]
    seg = 9.0
    out = np.zeros((n, 2), np.float32)
    step = SR * 4
    for c0 in range(0, n, step):
        c1 = min(n, c0 + step)
        t = np.arange(c0, c1, dtype=np.float64) / SR
        acc = np.zeros((c1 - c0, 2))
        for ci, ch in enumerate(chords):
            pos = (t / seg) % len(chords)
            dd = np.abs(pos - (ci + 0.5))
            dd = np.minimum(dd, len(chords) - dd)             # circular distance to this chord's segment centre
            w = np.clip((0.65 - dd) / 0.3, 0, 1)              # full inside the segment, 0.3-segment crossfades
            w = np.sin(w * np.pi / 2) ** 2
            if not w.any():
                continue
            for j, f in enumerate(ch):
                lfo = 0.75 + 0.25 * np.sin(2 * np.pi * (0.05 + 0.013 * j) * t + j)
                v = (np.sin(2 * np.pi * f * t) + 0.22 * np.sin(2 * np.pi * 2 * f * t + 0.4)) * lfo / (1 + 0.35 * j)
                vr = np.sin(2 * np.pi * f * 1.004 * t + 1.1) * lfo / (1 + 0.35 * j)
                acc[:, 0] += w * (0.6 * v + 0.4 * vr)
                acc[:, 1] += w * (0.4 * v + 0.6 * vr)
        out[c0:c1] = acc
    fade = np.minimum(1, np.minimum(np.arange(n) / (SR * 3), (n - np.arange(n)) / (SR * 4)))
    out *= fade[:, None]
    return out / (np.abs(out).max() + 1e-6)


# Effects levels (linear, before ducking). 2026-11-22 owner review ("звуки переходов громче голоса"): the old bed measured
# about -17 LUFS against a -23 LUFS narration. Now a whoosh peaks near -17 dBFS, a hero hit near -18 dBFS and the pad sits
# far below (bed about -32 LUFS, roughly 9 dB under the voice), and while the narrator speaks the side-chain compressor
# pushes the bed down a further ~8 dB. pipeline/tests/test_motion_mix.py keeps these limits.
WHOOSH_GAIN, HIT_GAIN, PAD_GAIN = 0.07, 0.13, 0.08
DUCK = "sidechaincompress=threshold=0.015:ratio=4:attack=8:release=350:makeup=1"


def sound_layer(path, dur, cuts_, heroes, music=True, t_from=0.0):
    rng = np.random.default_rng(7)
    n = int(dur * SR)
    mix = np.zeros((n, 2), np.float32)
    if music:
        mix += ambient_pad(dur + t_from)[int(t_from * SR):int(t_from * SR) + n] * PAD_GAIN
    for c in cuts_:
        if c["kind"] == "none":
            continue
        w = whoosh(rng, bright=1.3 if c["kind"] in ("whip_l", "whip_r") else 0.9)
        if c["kind"] == "flash":
            w *= 0.55
        start = int((c["t"] - t_from - 0.52 * len(w) / SR) * SR)
        pan = 0.25 if c["kind"] == "whip_l" else 0.75 if c["kind"] == "whip_r" else 0.5
        for ch, g in ((0, 1 - pan), (1, pan)):
            a, b = max(0, start), min(n, start + len(w))
            if b > a:
                mix[a:b, ch] += w[a - start:b - start] * WHOOSH_GAIN * g * 2
    for h in heroes:
        s = hit(rng)
        start = int((h.t0 + 0.05 - t_from) * SR)
        a, b = max(0, start), min(n, start + len(s))
        if b > a:
            mix[a:b] += (s[a - start:b - start] * HIT_GAIN)[:, None]
    pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
    import wave
    with wave.open(path, "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes(pcm.tobytes())


# ------------------------------------------------------------------ main pass
def run(a):
    tl = json.load(open(a.timeline))
    rights = json.load(open(a.rights))
    vj = json.load(open(a.voice))
    spec = json.load(open(a.spec)) if a.spec else {}
    words = vj["words"]
    voice_end = float(vj.get("duration") or words[-1]["end"])
    mode = spec.get("text_mode", "kinetic")
    heroes = build_heroes(spec, words) if mode == "kinetic" else []
    callouts = Callouts(spec.get("callouts", [])) if mode == "callouts" else None
    caps = LongCaptions(words, keywords=set(spec.get("keywords", [])), heroes=heroes, replace=spec.get("replace"),
                        style=Style(channel_tag=spec.get("channel_tag", "ORBITAL ATLAS")), duration=voice_end, hud_until=voice_end + 0.6)
    cl = cuts(tl, spec)
    f0 = first_picture(tl)
    no_caps = set(spec.get("no_captions", []))
    mf = ImageFont.truetype(MONO, 20)
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  a.base], capture_output=True, text=True).stdout.strip())
    t_from = a.start
    dur = min(a.dur or total, total - t_from)

    def frame_at(img, t, idx):
        if t < f0 - 1e-6:
            return img                       # cover frame: untouched
        c = min(cl, key=lambda c: abs(c["t"] - t)) if cl else None
        if c:
            img = transition(img, t, c, idx)
        im = img.convert("RGBA")
        sh = shot_at(tl, t)
        if t <= voice_end + 0.6:
            line = source_line(tl, rights, spec, sh)
            if line:
                ImageDraw.Draw(im).text((84, H - 96), line, font=mf, fill=(255, 255, 255, 190))
            if callouts is not None:
                callouts.render(im, t)
            elif not (sh and sh.get("id") in no_caps):
                caps.render(im, t)
            else:
                caps._hud(im, t)
        return im.convert("RGB")

    if a.frames:
        for t in (float(x) for x in a.frames.split(",")):
            p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", a.base, "-frames:v", "1", "-f", "rawvideo",
                                "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
            img = Image.frombytes("RGB", (W, H), p.stdout[: W * H * 3])
            out = Path(a.out).with_name(f"{Path(a.out).stem}_{t:06.2f}.png")
            frame_at(img, t, int(t * FPS)).save(out)
            print(out)
        return

    with tempfile.TemporaryDirectory() as td:
        sfx = os.path.join(td, "sfx.wav")
        sound_layer(sfx, dur, [c for c in cl if t_from - 1 <= c["t"] <= t_from + dur + 1],
                    [h for h in heroes if t_from - 1 <= h.t0 <= t_from + dur], music=spec.get("music", True), t_from=t_from)
        dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t_from:.3f}", "-t", f"{dur:.3f}", "-i", a.base,
                                "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-ss", f"{t_from:.3f}", "-t", f"{dur:.3f}", "-i", a.base,
                                "-i", sfx, "-filter_complex",
                                "[1:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[v][key];"
                                "[2:a]aresample=48000,aformat=channel_layouts=stereo[fx];"
                                f"[fx][key]{DUCK}[fxd];"
                                "[v][fxd]amix=inputs=2:normalize=0:duration=first,"
                                "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]",
                                "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                                "-force_key_frames", f"expr:gte(t,n_forced*{a.segment_s:g})",   # yt-render segment boundaries
                                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                                "-shortest", a.out], stdin=subprocess.PIPE)
        size = W * H * 3
        idx = 0
        while True:
            buf = dec.stdout.read(size)
            if len(buf) < size:
                break
            t = t_from + idx / FPS
            img = Image.frombytes("RGB", (W, H), buf)
            enc.stdin.write(frame_at(img, t, idx).tobytes())
            idx += 1
            if idx % 300 == 0:
                print(f"motion: {t:.1f}s", flush=True)
        enc.stdin.close()
        dec.wait()
        if enc.wait():
            raise SystemExit("motion: ffmpeg encode failed")
    print(json.dumps({"out": a.out, "frames": idx, "cuts": len(cl), "heroes": len(heroes)}))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True)
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--rights", required=True)
    ap.add_argument("--voice", required=True)
    ap.add_argument("--spec")
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--dur", type=float, default=0.0)
    ap.add_argument("--frames", help="comma list of times: write PNG stills only")
    ap.add_argument("--segment-s", type=float, default=60.0, help="keyframe every N s (yt-render long segments)")
    run(ap.parse_args())


if __name__ == "__main__":
    main()
