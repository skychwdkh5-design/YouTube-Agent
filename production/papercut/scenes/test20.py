#!/usr/bin/env python3
"""20 s character-animation test: ATLAS reacts to and interacts with the graphics.

  S1  0.0- 5.9  hero talks (mouth + blinks) - Orion flies Earth->Moon, radio link pulses
  S2  5.9- 8.4  cut to POINT pose - Orion slips behind the Moon, the link is blocked (turns red)
  S3  8.4-11.2  hero talks - camera pushes in on the blocked line
  S4 11.2-14.5  cut to TELESCOPE pose - a telescope view opens: real Artemis II footage of the dark Moon
  S5 14.5-16.4  cut to SURPRISED pose + "!!" from the sheet - view shows NASA's impact-flash animation
  S6 16.4-20.0  hero talks, blinks - dark Moon view stays

Voice: existing EP014 Adam narration (three sentences, reused, no new paid audio).
Footage: NASA Artemis II (media_v2/cuts/a_darkmoon2.mp4, a_impact_anim.mp4 - labelled ANIMATION by NASA).
No limb rotation, no invented events. Map is an original paper illustration, labelled.

  python3 -I scenes/test20.py --media /mnt/project-files --out test20.mp4 --log log20.json
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from papercut.actor import Actor, ActorCue  # noqa: E402
from papercut.host import smoothstep  # noqa: E402
from papercut import paper as P  # noqa: E402

W, H, FPS, DUR = 1920, 1080, 30, 20.0
N = int(DUR * FPS)
CAPTION_BOX = (300, 935, 1620, 1025)
FEET = (300, 900)
HERO_H, POSE_H = 345, 330

VOICE = [  # (source start, source end, place at, text) from artemis/EP014/voice/narration.wav
    (22.70, 28.06, 0.35, "When Orion moved behind the Moon, the crew knew radio contact with Earth would drop."),
    (28.44, 31.00, 8.55, "The Moon itself blocked the direct path."),
    (39.87, 43.45, 16.40, "This was a rare chance to watch the dark lunar surface."),
]
SHOTS = [("S1_hero_talk", 0.0, 5.9), ("S2_point", 5.9, 8.4), ("S3_hero_talk", 8.4, 11.2),
         ("S4_telescope", 11.2, 14.5), ("S5_surprised", 14.5, 16.4), ("S6_hero_talk", 16.4, 20.0)]


def cues():
    talk = [(a, a + (e - s)) for s, e, a, _ in VOICE]
    fx_h = 62
    return [
        ActorCue(0.0, 5.9, "hero", *FEET, HERO_H, "explain", talk=[talk[0]], blinks=[1.7, 4.4], pop=False, name="S1_hero"),
        ActorCue(5.9, 8.4, "pose_point", *FEET, POSE_H, "surprise", name="S2_point"),
        ActorCue(8.4, 11.2, "hero", *FEET, HERO_H, "explain", talk=[talk[1]], blinks=[9.9], name="S3_hero"),
        ActorCue(11.2, 14.5, "pose_observe", *FEET, POSE_H, "listen", name="S4_telescope"),
        ActorCue(14.5, 16.4, "pose_surprised", *FEET, POSE_H, "surprise",
                 fx=[("fx_exclaim", 14.6, 16.4, 70, -POSE_H - 8, fx_h)], name="S5_surprised"),
        ActorCue(16.4, 20.0, "hero", *FEET, HERO_H, "idle", talk=[talk[2]], blinks=[17.6, 19.3], name="S6_hero"),
    ]


# ------------------------------------------------------------------ audio
def build_audio(media: Path, tmp: Path):
    sr = 48000
    src = media / "artemis/EP014/voice/narration.wav"
    with wave.open(str(src)) as w:
        ch, sw, fr = w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if ch > 1:
        raw = raw.reshape(-1, ch).mean(1)
    if fr != sr:
        idx = np.arange(0, len(raw), fr / sr)
        raw = np.interp(idx, np.arange(len(raw)), raw)
    voice = np.zeros(int(DUR * sr) + sr)
    for s, e, at, _ in VOICE:
        seg = raw[int(s * sr):int(e * sr)]
        fade = np.minimum(1, np.minimum(np.arange(len(seg)), np.arange(len(seg))[::-1]) / (0.01 * sr))
        voice[int(at * sr):int(at * sr) + len(seg)] += seg * fade
    # original SFX: radio pips while the link is alive, a falling tone when it drops, soft pop at cuts
    sfx = np.zeros_like(voice)
    t = np.arange(int(0.07 * sr)) / sr
    pip = np.sin(2 * np.pi * 1320 * t) * np.hanning(len(t)) * 0.10
    for k in np.arange(0.6, 6.1, 0.55):
        i = int(k * sr); sfx[i:i + len(pip)] += pip
    t = np.arange(int(0.6 * sr)) / sr
    drop = np.sin(2 * np.pi * (900 - 700 * t / 0.6) * t) * np.exp(-t * 4) * 0.12
    i = int(6.45 * sr); sfx[i:i + len(drop)] += drop
    t = np.arange(int(0.05 * sr)) / sr
    pop = np.random.default_rng(1).standard_normal(len(t)) * np.exp(-t * 90) * 0.05
    for _, a, _b in SHOTS[1:]:
        i = int(a * sr); sfx[i:i + len(pop)] += pop
    mix = np.clip(voice + sfx, -1, 1)[: int(DUR * sr)]
    out = tmp / "mix.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    # loudness envelope of the VOICE only, per video frame (drives the mouth)
    hop = sr // FPS
    env = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(N)])
    env = env / (np.percentile(env[env > 1e-4], 90) + 1e-9)
    env = np.convolve(env, [0.25, 0.5, 0.25], mode="same")
    return out, env


# ------------------------------------------------------------------ map world
class Map:
    OX, OY = 160, 120
    WW, WH = W + 2 * 160, H + 2 * 120
    EARTH = (700 + 160, 520 + 120, 150)
    MOON = (1450 + 160, 470 + 120, 105)

    def __init__(self):
        self.bg = P.paper_sheet(self.WW, self.WH, P.NAVY, 11, 0.10)
        d = ImageDraw.Draw(self.bg)
        rng = np.random.default_rng(3)
        for _ in range(240):
            x, y, r = rng.uniform(0, self.WW), rng.uniform(0, self.WH), rng.choice([1.2, 1.6, 2.2])
            d.ellipse((x - r, y - r, x + r, y + r), fill=(232, 222, 200, int(rng.uniform(110, 220))))
        ex, ey, er = self.EARTH
        m = P.ss_mask((self.WW, self.WH), lambda dd, s: dd.ellipse(((ex - er) * s, (ey - er) * s, (ex + er) * s, (ey + er) * s), fill=255))
        self.bg.alpha_composite(P.cutout(m, P.BLUE, 21, border=8))
        land = P.ss_mask((self.WW, self.WH), lambda dd, s: [dd.polygon([((ex + u * .8) * s, (ey + v * .8) * s) for u, v in poly], fill=255) for poly in (
            [(-120, -90), (-40, -140), (30, -110), (10, -40), (-60, -10), (-110, -30)],
            [(40, 10), (120, -20), (150, 60), (90, 130), (30, 90)], [(-130, 60), (-70, 50), (-50, 110), (-110, 120)])])
        land = Image.fromarray(np.minimum(np.asarray(land), np.asarray(m)))
        self.bg.alpha_composite(P.cutout(land, (122, 158, 104), 23, shadow_offset=(3, 4), shadow_blur=2, shadow_alpha=0.3))
        P.label(self.bg, "EARTH", (ex - 62, ey + er + 30), size=28, fg=P.INK, bg=(*P.CREAM, 255))
        mx, my, mr = self.MOON
        mm = P.ss_mask((self.WW, self.WH), lambda dd, s: dd.ellipse(((mx - mr) * s, (my - mr) * s, (mx + mr) * s, (my + mr) * s), fill=255))
        self.moon = P.cutout(mm, (200, 196, 186), 31, border=8)
        cr = P.ss_mask((self.WW, self.WH), lambda dd, s: [dd.ellipse(((mx + u - r) * s, (my + v - r) * s, (mx + u + r) * s, (my + v + r) * s), fill=255)
                                                         for u, v, r in ((-38, -28, 20), (32, 18, 15), (-8, 46, 11), (46, -40, 9))])
        self.moon.alpha_composite(P.cutout(cr, (160, 156, 150), 33, shadow=False))
        P.label(self.moon, "MOON", (mx - 50, my + mr + 26), size=28, fg=P.INK, bg=(*P.CREAM, 255))
        # Orion route: Earth -> over the top -> behind the Moon (far side) -> beyond
        t = np.linspace(0, 1, 400)[:, None]
        b = [np.array(q, float) for q in ((ex + 150, ey - 40), (ex + 520, ey - 330), (mx - 120, my - 260), (mx + 175, my + 10))]
        self.route = (1 - t) ** 3 * b[0] + 3 * (1 - t) ** 2 * t * b[1] + 3 * (1 - t) * t ** 2 * b[2] + t ** 3 * b[3]

    def orion_u(self, t):
        if t < 5.9:
            return 0.80 * smoothstep(t / 5.9) ** 0.85
        return 0.80 + 0.20 * smoothstep((t - 5.9) / 1.6)

    def behind_moon(self, p):
        mx, my, mr = self.MOON
        return math.hypot(p[0] - mx, p[1] - my) < mr + 6 and p[0] > mx - 30

    def frame(self, t):
        world = self.bg.copy()
        d = ImageDraw.Draw(world)
        u = self.orion_u(t)
        k = int(u * (len(self.route) - 1))
        for i in range(0, k, 8):              # flown route, dashed
            seg = self.route[i:i + 5]
            if len(seg) > 1:
                d.line([tuple(q) for q in seg], fill=(*P.ORANGE, 255), width=5)
        orion = self.route[k]
        ex, ey, er = self.EARTH
        mx, my, mr = self.MOON
        # radio link Earth -> Orion; blocked once the Moon covers the line of sight
        a = np.array([ex, ey], float)
        dvec = orion - a
        L = np.linalg.norm(dvec)
        dirv = dvec / L
        proj = np.dot(np.array([mx, my]) - a, dirv)
        closest = np.linalg.norm(a + dirv * proj - np.array([mx, my]))
        blocked = closest < mr and 0 < proj < L
        stop = proj - math.sqrt(max(0, mr ** 2 - closest ** 2)) if blocked else L
        col = (255, 92, 70) if blocked else (150, 230, 200)
        n = int(stop // 18)
        for j in range(n):                    # dashes
            p0 = a + dirv * (er + 10 + j * 18); p1 = p0 + dirv * 9
            if np.dot(p1 - a, dirv) > stop:
                break
            d.line([tuple(p0), tuple(p1)], fill=(*col, 230), width=4)
        if not blocked:                       # travelling signal pulses
            for j in range(3):
                f = ((t * 0.9 + j / 3) % 1)
                p = a + dirv * (er + 10 + f * (L - er - 20))
                d.ellipse((p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6), fill=(*col, 255))
        # Orion marker drawn BEFORE the Moon so it really goes behind it
        if not self.behind_moon(orion) or True:
            ahead = self.route[min(len(self.route) - 1, k + 3)]
            ang = math.degrees(math.atan2(ahead[1] - orion[1], ahead[0] - orion[0]))
            cap = capsule()
            im = cap.rotate(-ang + 180, resample=Image.Resampling.BICUBIC, expand=True)
            world.alpha_composite(im, (int(orion[0] - im.width / 2), int(orion[1] - im.height / 2)))
        world.alpha_composite(self.moon)
        if blocked:
            hit = a + dirv * stop
            dd = ImageDraw.Draw(world)
            r = 16 + 3 * math.sin(t * 12)
            dd.line((hit[0] - r, hit[1] - r, hit[0] + r, hit[1] + r), fill=(255, 92, 70, 255), width=7)
            dd.line((hit[0] - r, hit[1] + r, hit[0] + r, hit[1] - r), fill=(255, 92, 70, 255), width=7)
            P.label(world, "LINE OF SIGHT BLOCKED", (hit[0] - 420, hit[1] + 26), size=26, fg=(255, 255, 255), bg=(150, 40, 30, 235))
        # camera: gentle drift; push-in on the blocked line in S3
        # S3 push-in anchored on the Moon, so the Earth slides left but stays clear of ATLAS
        z = 1.0 + 0.07 * smoothstep((t - 8.4) / 2.6) * (t < 11.2)
        mx, my, _ = self.MOON
        cx = mx - (mx - self.OX - W / 2) / z + 8 * math.sin(t * 0.4)
        cy = my - (my - self.OY - H / 2) / z
        inv = 1 / z
        out = world.transform((W, H), Image.Transform.AFFINE, (inv, 0, cx - W / 2 * inv, 0, inv, cy - H / 2 * inv),
                              resample=Image.Resampling.BICUBIC)
        P.label(out, "ILLUSTRATION - NOT TO SCALE", (W - 470, 40), size=24)
        return out, {"orion_u": u, "blocked": bool(blocked)}


_CAP = None


def capsule():
    global _CAP
    if _CAP is None:
        s = 4
        m = Image.new("L", (90 * s, 60 * s), 0)
        dd = ImageDraw.Draw(m)
        dd.polygon([(20 * s, 12 * s), (62 * s, 22 * s), (62 * s, 38 * s), (20 * s, 48 * s)], fill=255)
        dd.rectangle((62 * s, 20 * s, 74 * s, 40 * s), fill=255)
        m = m.resize((90, 60), Image.Resampling.LANCZOS)
        _CAP = P.cutout(m, (236, 232, 222), 41, border=3, border_color=P.ORANGE, shadow_offset=(3, 4), shadow_blur=3)
    return _CAP


# ------------------------------------------------------------------ telescope view (real footage)
class Scope:
    C, R = (1150, 268), 200

    def __init__(self, media: Path, tmp: Path):
        self.dark = self._frames(media / "media_v2/cuts/a_darkmoon2.mp4", 1.10, int(4.7 * FPS), tmp, "d")  # dark-Moon shot only
        self.flash = self._frames(media / "media_v2/cuts/a_impact_anim.mp4", 4.6, int(2.2 * FPS), tmp, "f")
        cx, cy = self.C
        r = self.R
        m = P.ss_mask((W, H), lambda dd, s: dd.ellipse(((cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s), fill=255))
        self.mask = m
        ring = P.ss_mask((W, H), lambda dd, s: dd.ellipse(((cx - r - 12) * s, (cy - r - 12) * s, (cx + r + 12) * s, (cy + r + 12) * s), fill=255))
        self.ring = P.cutout(ring, P.CREAM, 61, border=0, shadow_offset=(8, 10), shadow_blur=8)

    def _frames(self, src, ss, n, tmp, tag):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss}", "-i", str(src), "-frames:v", str(n),
                        "-vf", "scale=760:-2", str(tmp / f"{tag}_%04d.jpg")], check=True)
        return sorted(tmp.glob(f"{tag}_*.jpg"))

    def draw(self, frame: Image.Image, t: float, tip):
        if t < 11.45:
            return None
        u = smoothstep((t - 11.45) / 0.45)
        if t >= 14.5 and t < 16.4:
            src, i, label = self.flash, int((t - 14.5) * FPS), "NASA ANIMATION - IMPACT FLASH"
        else:
            src = self.dark
            i = int((t - 11.45) * FPS) if t < 14.5 else int((t - 16.4 + 0.9) * FPS)
            label = "NASA / ARTEMIS II - DARK MOON"
        im = Image.open(src[min(i, len(src) - 1)]).convert("RGBA")
        cx, cy = self.C
        r = self.R
        side = 2 * r
        z = 1.0 + 0.04 * ((t - 11.45) / 8.5)
        sc = side * z / min(im.width, im.height)
        im = im.resize((round(im.width * sc), round(im.height * sc)), Image.Resampling.LANCZOS)
        view = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        view.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
        a = (np.asarray(self.mask, np.float32) * u).astype(np.uint8)
        view.putalpha(Image.fromarray(a))
        ring = self.ring.copy()
        ring.putalpha(Image.fromarray((np.asarray(ring.getchannel("A"), np.float32) * u).astype(np.uint8)))
        # sight lines from the telescope tip to the view (only while the telescope pose is on screen)
        if tip is not None and 11.2 <= t < 14.5:
            d = ImageDraw.Draw(frame)
            for ang in (-0.62, 0.62):
                px, py = cx - r * math.cos(ang) * 0.92, cy + r * math.sin(ang) * 0.92
                ex = tip[0] + (px - tip[0]) * u; ey = tip[1] + (py - tip[1]) * u
                n = int(math.hypot(ex - tip[0], ey - tip[1]) // 16)
                for j in range(n):
                    f0, f1 = j / max(1, n), (j + 0.5) / max(1, n)
                    d.line((tip[0] + (ex - tip[0]) * f0, tip[1] + (ey - tip[1]) * f0,
                            tip[0] + (ex - tip[0]) * f1, tip[1] + (ey - tip[1]) * f1), fill=(*P.CREAM, 200), width=3)
        frame.alpha_composite(ring)
        frame.alpha_composite(view)
        if u > 0.9:
            P.label(frame, label, (cx - r + 10, cy - r - 52), size=22)
        return label


def quantize_mouth(env, hold=2):
    """Loudness -> mouth level (0 closed / 0.3 mid / 0.8 open), each state held >= `hold` frames."""
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


def captions(frame, t):
    for s, e, at, text in VOICE:
        if at <= t < at + (e - s) + 0.15:
            d = ImageDraw.Draw(frame)
            f = P.font(36)
            words, lines, cur = text.split(), [], ""
            for w in words:
                trial = (cur + " " + w).strip()
                if d.textlength(trial, font=f) > 1180 and cur:
                    lines.append(cur); cur = w
                else:
                    cur = trial
            lines.append(cur)
            lines = lines[-2:]
            lh = 44
            hbox = lh * len(lines) + 20
            y0 = CAPTION_BOX[3] - hbox
            wmax = max(d.textlength(l, font=f) for l in lines) + 40
            frame.alpha_composite(Image.new("RGBA", (int(wmax), hbox), (0, 0, 0, 170)), (int(W / 2 - wmax / 2), int(y0)))
            for i, l in enumerate(lines):
                d.text((W / 2 - d.textlength(l, font=f) / 2, y0 + 10 + i * lh), l, font=f, fill=(255, 255, 255))
            return text
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--media", type=Path, required=True, help="project files root")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--frames", type=str, help="comma list of times: write PNG stills only")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        mix, env = build_audio(a.media, tmp)
        mouth = quantize_mouth(env)
        actor = Actor((W, H), cues(), envelope=lambda t: float(mouth[min(N - 1, int(round(t * FPS)))]))
        mp, scope = Map(), Scope(a.media, tmp)
        times = [float(x) for x in a.frames.split(",")] if a.frames else None
        proc = None
        if not times:
            cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                   "-i", "-", "-i", str(mix), "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                   "-r", str(FPS), "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", str(a.out)]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        log = []
        for i, t in enumerate(times or [i / FPS for i in range(N)]):
            fr, minfo = mp.frame(t)
            cue, st = actor.state(t)
            tip = None
            if cue is not None and cue.drawing == "pose_observe":
                im = actor._img["pose_observe"]
                sc = cue.height / im.height
                tip = (st["x"] - im.width * sc / 2 + 200 * sc, st["y"] - cue.height + 40 * sc)
            scope_label = scope.draw(fr, t, tip)
            info = actor.render(fr, t)
            cap = captions(fr, t)
            if times:
                fr.convert("RGB").save(a.out.parent / f"still_{t:05.2f}.png")
            else:
                proc.stdin.write(fr.convert("RGB").tobytes())
            log.append({"frame": i, "t": round(t, 4), "shot": next(n for n, s0, s1 in SHOTS if s0 <= t < s1 or s1 == DUR),
                        "actor": info, "map": minfo, "scope": scope_label, "caption": cap,
                        "mouth_env": round(float(env[min(N - 1, int(round(t * FPS)))]), 3), "mouth_level": float(mouth[min(N - 1, int(round(t * FPS)))])})
        if proc:
            proc.stdin.close()
            if proc.wait():
                raise SystemExit("ffmpeg failed")
    a.log.write_text(json.dumps({"fps": FPS, "size": [W, H], "frames": N, "shots": SHOTS, "caption_box": CAPTION_BOX,
                                 "voice": VOICE, "log": log}, default=float))
    print("done")


if __name__ == "__main__":
    main()
