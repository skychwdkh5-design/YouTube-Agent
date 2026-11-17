#!/usr/bin/env python3
"""20 s test v3: the articulated paper ATLAS (parts sheet 2026-11-17) + object-anchored callouts.

One continuous take, no pose cuts. ATLAS points at EARTH, the MOON and the RADIO LINK, returns to rest,
leans toward the Moon when the SIGNAL is BLOCKED, returns, points at the telescope window and leans in at
the IMPACT FLASH, returns. Blinks and a lagging scarf throughout. No walking.

Text: no burned-in subtitles, no black boxes, no bottom line. Only short English callouts anchored to
objects, appearing with the explaining action. Full subtitles go to a separate SRT.
Voice: existing EP014 Adam narration (three lines, no new audio). Footage: NASA Artemis II (labelled).

  python3 -I scenes/test20_rig.py --media /mnt/project-files --out test.mp4 --log log.json --srt test.srt
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import tempfile
import wave
from dataclasses import replace
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scenes"))
from papercut import paper as P  # noqa: E402
from papercut.host import smoothstep  # noqa: E402
from papercut.rig import Pose, Rig  # noqa: E402
import test20 as T20  # noqa: E402

W, H, FPS, DUR = 1920, 1080, 30, 20.0
N = int(DUR * FPS)
FEET = (300.0, 985.0)
RIG_H = 430
FONT = ROOT.parent / "kinetic_captions" / "fonts" / "unbounded-latin-800-normal.woff"
MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"

VOICE = [  # (source start, source end, place at, text) from artemis/EP014/voice/narration.wav
    (22.70, 28.06, 0.35, "When Orion moved behind the Moon, the crew knew radio contact with Earth would drop."),
    (28.44, 31.00, 6.90, "The Moon itself blocked the direct path."),
    (39.87, 43.45, 16.40, "This was a rare chance to watch the dark lunar surface."),
]

# ------------------------------------------------------------------ source labels: paper tags, no black boxes
_label = P.label
SKIP = {"EARTH", "MOON", "LINE OF SIGHT BLOCKED"}          # replaced by the anchored callouts
RENAME = {"NASA ANIMATION - IMPACT FLASH": "NASA ANIMATION", "NASA / ARTEMIS II - DARK MOON": "NASA / ARTEMIS II FOOTAGE"}


def _paper_label(frame, text, xy, size=26, fg=None, bg=None, pad=(14, 8)):
    if text in SKIP:
        return None
    text = RENAME.get(text, text)
    return _label(frame, text, xy, size=min(size, 22), fg=P.INK, bg=(*P.CREAM, 235), pad=pad)


P.label = _paper_label
T20.P.label = _paper_label


# ------------------------------------------------------------------ world (map) with a known camera
class Map(T20.Map):
    def cam(self, t):
        """world -> screen: calm slow drift only (no push-ins, no shake)."""
        mx, my, _ = self.MOON
        cx = self.OX + W / 2 + 6 * math.sin(t * 0.35)
        cy = self.OY + H / 2
        return lambda p: (p[0] - (cx - W / 2), p[1] - (cy - H / 2)), (cx, cy)

    def frame(self, t):
        world = self.bg.copy()
        d = ImageDraw.Draw(world)
        u = self.orion_u(t)
        k = int(u * (len(self.route) - 1))
        for i in range(0, k, 8):
            seg = self.route[i:i + 5]
            if len(seg) > 1:
                d.line([tuple(q) for q in seg], fill=(*P.ORANGE, 255), width=5)
        orion = self.route[k]
        ex, ey, er = self.EARTH
        mx, my, mr = self.MOON
        a = np.array([ex, ey], float)
        dvec = orion - a
        L = np.linalg.norm(dvec)
        dirv = dvec / L
        proj = np.dot(np.array([mx, my]) - a, dirv)
        closest = np.linalg.norm(a + dirv * proj - np.array([mx, my]))
        blocked = closest < mr and 0 < proj < L
        stop = proj - math.sqrt(max(0, mr ** 2 - closest ** 2)) if blocked else L
        col = (255, 92, 70) if blocked else (150, 230, 200)
        for j in range(int(stop // 18)):
            p0 = a + dirv * (er + 10 + j * 18); p1 = p0 + dirv * 9
            if np.dot(p1 - a, dirv) > stop:
                break
            d.line([tuple(p0), tuple(p1)], fill=(*col, 230), width=4)
        if not blocked:
            for j in range(3):
                f = ((t * 0.9 + j / 3) % 1)
                p = a + dirv * (er + 10 + f * (L - er - 20))
                d.ellipse((p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6), fill=(*col, 255))
        ahead = self.route[min(len(self.route) - 1, k + 3)]
        ang = math.degrees(math.atan2(ahead[1] - orion[1], ahead[0] - orion[0]))
        im = T20.capsule().rotate(-ang + 180, resample=Image.Resampling.BICUBIC, expand=True)
        world.alpha_composite(im, (int(orion[0] - im.width / 2), int(orion[1] - im.height / 2)))
        world.alpha_composite(self.moon)
        hit = None
        if blocked:
            hit = a + dirv * stop
            r = 16
            d2 = ImageDraw.Draw(world)
            d2.line((hit[0] - r, hit[1] - r, hit[0] + r, hit[1] + r), fill=(255, 92, 70, 255), width=7)
            d2.line((hit[0] - r, hit[1] + r, hit[0] + r, hit[1] - r), fill=(255, 92, 70, 255), width=7)
        to_screen, (cx, cy) = self.cam(t)
        out = world.crop((int(round(cx - W / 2)), int(round(cy - H / 2)), int(round(cx - W / 2)) + W, int(round(cy - H / 2)) + H))
        dx = (cx - W / 2) - int(round(cx - W / 2))
        if abs(dx) > 1e-3:   # sub-pixel drift
            out = out.transform((W, H), Image.Transform.AFFINE, (1, 0, dx, 0, 1, 0), resample=Image.Resampling.BICUBIC)
        P.label(out, "ILLUSTRATION - NOT TO SCALE", (W - 430, 40), size=22)
        link_mid = a + dirv * (er + 10 + 0.5 * (min(stop, L) - er - 10))
        geo = {"earth": to_screen((ex, ey)) + (er,), "moon": to_screen((mx, my)) + (mr,),
               "link_mid": to_screen(link_mid), "hit": to_screen(hit) if hit is not None else None,
               "link_dir": math.degrees(math.atan2(dirv[1], dirv[0]))}
        return out, {"orion_u": u, "blocked": bool(blocked)}, geo


# ------------------------------------------------------------------ callouts (paper cards anchored to objects)
def ease_out(u):
    u = min(1.0, max(0.0, u)); return 1 - (1 - u) ** 3


def ease_out_back(u, s=1.2):
    u = min(1.0, max(0.0, u)) - 1; return 1 + u * u * ((s + 1) * u + s)


class Callouts:
    SIZE = 40

    def __init__(self):
        self.f = ImageFont.truetype(str(FONT), self.SIZE)
        self.cache = {}

    def card(self, text):
        if text in self.cache:
            return self.cache[text]
        x0, y0, x1, y1 = self.f.getbbox(text)
        pw, ph, bar = 24, 16, 9
        w, h = x1 - x0 + 2 * pw + bar, y1 - y0 + 2 * ph
        k = 3
        m = Image.new("L", (w * k, h * k), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w * k - 1, h * k - 1), radius=8 * k, fill=255)
        m = m.resize((w, h), Image.Resampling.LANCZOS)
        g = P.grain(w, h, 7, 0.05)[..., None]
        base = np.clip(np.array(P.CREAM, np.float32)[None, None, :] * g, 0, 255).astype(np.uint8)
        im = Image.fromarray(np.dstack([base, np.full((h, w), 255, np.uint8)]), "RGBA")
        ImageDraw.Draw(im).rectangle((0, 0, bar - 1, h), fill=(*P.ORANGE, 255))
        ImageDraw.Draw(im).text((bar + pw - x0, ph - y0), text, font=self.f, fill=(*P.INK, 255))
        im.putalpha(m)
        sh = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
        sa = Image.new("L", (w + 40, h + 40), 0)
        sa.paste(m, (20, 20))
        sa = sa.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.35))
        sh.putalpha(sa)
        self.cache[text] = (im, sh)
        return self.cache[text]

    def draw(self, frame, text, anchor, card_xy, t, t0, t1):
        """card_xy = card centre. Returns the card box on screen, or None when hidden."""
        if t < t0 or t >= t1:
            return None
        u = (t - t0) / 0.32
        a_in = ease_out(u)
        a_out = 1 - ease_out((t - (t1 - 0.25)) / 0.25) if t > t1 - 0.25 else 1.0
        al = a_in * a_out
        if al <= 0.01:
            return None
        im, sh = self.card(text)
        sc = 0.92 + 0.08 * ease_out_back(u)
        rise = (1 - ease_out(u)) * 12
        w, h = im.width * sc, im.height * sc
        cx, cy = card_xy[0], card_xy[1] + rise
        x0, y0 = cx - w / 2, cy - h / 2
        # leader: anchor dot -> nearest card edge point, drawn as the card arrives
        d = ImageDraw.Draw(frame)
        ex = min(max(anchor[0], x0 + 10), x0 + w - 10)
        ey = min(max(anchor[1], y0), y0 + h)
        lu = ease_out((t - t0 - 0.05) / 0.3)
        lx, ly = anchor[0] + (ex - anchor[0]) * lu, anchor[1] + (ey - anchor[1]) * lu
        d.line((anchor[0], anchor[1], lx, ly), fill=(*P.CREAM, int(235 * al)), width=4)
        r = 7
        d.ellipse((anchor[0] - r, anchor[1] - r, anchor[0] + r, anchor[1] + r), fill=(*P.ORANGE, int(255 * al)),
                  outline=(*P.CREAM, int(255 * al)), width=2)
        ims = im.resize((round(w), round(h)), Image.Resampling.LANCZOS) if sc != 1 else im
        shs = sh.resize((round(sh.width * sc), round(sh.height * sc)), Image.Resampling.LANCZOS) if sc != 1 else sh
        if al < 1:
            ims = ims.copy(); ims.putalpha(ims.getchannel("A").point(lambda v: int(v * al)))
            shs = shs.copy(); shs.putalpha(shs.getchannel("A").point(lambda v: int(v * al)))
        frame.alpha_composite(shs, (int(round(x0 - 20 * sc + 4)), int(round(y0 - 20 * sc + 7))))
        frame.alpha_composite(ims, (int(round(x0)), int(round(y0))))
        return [round(x0), round(y0), round(x0 + w), round(y0 + h)]


# (text, t0, t1, anchor key, card offset from anchor)
CALLOUTS = [
    ("EARTH", 1.15, 20.0, "earth_label", (0, 0)),
    ("MOON", 2.55, 20.0, "moon_label", (0, 0)),
    ("RADIO LINK", 3.80, 6.40, "link_mid", (-150, -110)),
    ("SIGNAL BLOCKED", 6.55, 11.0, "hit", (-260, 125)),
    ("IMPACT FLASH", 14.65, 16.6, "flash", (-280, -150)),
]


def anchors(geo, scope_c, scope_r):
    ex, ey, er = geo["earth"]
    mx, my, mr = geo["moon"]
    out = {"earth": (ex, ey), "moon": (mx, my),
           "earth_label": ((ex, ey + er - 6), (ex, ey + er + 78)),
           "moon_label": ((mx, my + mr - 6), (mx, my + mr + 78)),
           "link_mid": (geo["link_mid"], (ex + 280, ey - 255)),
           "hit": (geo["hit"], (mx - 330, my - 150)) if geo["hit"] else (None, None),
           "flash": ((scope_c[0] - scope_r - 6, scope_c[1] + 40), None)}
    return out


# ------------------------------------------------------------------ choreography
def solve_point(rig, base: Pose, target, feet, arm="B", elbow=-12.0):
    """Shoulder angle so the arm aims at `target`; wrist turns the pointing glove onto the target."""
    best = None
    for s in np.arange(-150, 21, 1.0):
        p = replace(base, arm_B=(s, elbow, 0.0)) if arm == "B" else replace(base, arm_A=(s, elbow, 0.0))
        j = rig.joint_points(p, feet)
        sh, wr = np.array(j["uarm_" + arm]), np.array(j["hand_" + arm])
        want = math.atan2(target[1] - sh[1], target[0] - sh[0])
        got = math.atan2(wr[1] - sh[1], wr[0] - sh[0])
        err = abs((want - got + math.pi) % (2 * math.pi) - math.pi)
        if best is None or err < best[0]:
            best = (err, s, math.degrees(want))
    _, s, want = best
    w = want - (base.lean + s + elbow)        # glove finger is drawn along +x
    w = (w + 180) % 360 - 180
    return (float(s), elbow, float(w))


class Choreo:
    """Key poses on a timeline; joints blend with smootherstep, so every move eases in and out."""

    def __init__(self, rig, geo_at):
        self.rig = rig
        rest = Pose()
        self.rest = rest
        g = geo_at
        aim = lambda tt, key, **kw: solve_point(rig, rest, key(g(tt)), FEET, **kw)
        earth = lambda geo: (geo["earth"][0] - 40, geo["earth"][1] - 30)
        moon = lambda geo: (geo["moon"][0] - 60, geo["moon"][1])
        link = lambda geo: geo["link_mid"]
        scope = lambda geo: (T20.Scope.C[0] - 150, T20.Scope.C[1] + 120)
        lean_in = Pose(lean=7.0, head=4.0, leg_A=(-7.0, 3.0, None), leg_B=(-7.0, 3.0, None),
                       arm_A=(5.0, 6.0, 0.0), arm_B=(-14.0, -24.0, 12.0), hand_B="open_B")
        point = lambda tt, f: replace(rest, arm_B=aim(tt, f), hand_B="point_B", head=-3.0)
        lean_scope = replace(lean_in, lean=5.0, head=-6.0, arm_B=(-60.0, -40.0, 20.0), hand_B="open_B")
        # (t_start, t_end, target pose)  - holds between moves
        self.keys = [
            (0.70, 1.70, point(1.2, earth)),
            (2.00, 2.80, point(2.6, moon)),
            (3.20, 4.00, point(3.9, link)),
            (4.70, 5.50, rest),
            (6.15, 6.95, lean_in),
            (9.40, 10.30, rest),
            (11.40, 12.40, point(12.3, scope)),
            (14.45, 14.95, lean_scope),
            (15.90, 16.80, rest),
        ]
        self.blinks = [2.9, 5.9, 8.3, 10.9, 13.4, 17.6, 19.3]
        self._scarf = self._simulate_scarf()

    @staticmethod
    def ease(u):
        u = min(1.0, max(0.0, u)); return u * u * u * (u * (u * 6 - 15) + 10)

    def body(self, t):
        cur = self.rest
        for t0, t1, tgt in self.keys:
            if t < t0:
                break
            u = self.ease((t - t0) / (t1 - t0))
            nxt = cur.mix(tgt, u)
            # glove drawing changes while the hand is moving, never on a still frame
            hand = tgt.hand_B if u >= 0.35 else cur.hand_B
            if tgt.hand_B == cur.hand_B:
                hand = cur.hand_B
            cur = replace(nxt, hand_B=hand) if t < t1 else tgt
        return cur

    def _simulate_scarf(self):
        """Scarf tip = damped spring that follows the torso lean and arm swings with a short delay."""
        dt = 1 / FPS / 4
        y, v = 0.0, 0.0
        w0, zeta = 2 * math.pi * 1.4, 0.45
        out = []
        prev_arm = self.body(0).arm_B[0]
        for i in range(N * 4 + 4):
            t = i * dt
            p = self.body(t)
            arm_v = (p.arm_B[0] - prev_arm) / dt
            prev_arm = p.arm_B[0]
            target = p.lean - 0.004 * arm_v
            a = w0 * w0 * (target - y) - 2 * zeta * w0 * v
            v += a * dt; y += v * dt
            if i % 4 == 0:
                out.append((y, p.lean))
        return out

    def eyes(self, t):
        for b in self.blinks:
            f = (t - b) * FPS
            if 0 <= f < 1.5 or 3.5 <= f < 5:
                return "half"
            if 1.5 <= f < 3.5:
                return "closed"
        return "open"

    def pose(self, t):
        p = self.body(t)
        i = min(len(self._scarf) - 1, int(round(t * FPS)))
        y, lean = self._scarf[i]
        # transforms() already turns the scarf by -0.6*lean; the lag adds (spring - lean)
        return replace(p, eyes=self.eyes(t), scarf=float(y - lean) * 1.6)


# ------------------------------------------------------------------ audio
def build_audio(media: Path, tmp: Path):
    sr = 48000
    with wave.open(str(media / "artemis/EP014/voice/narration.wav")) as w:
        ch, fr = w.getnchannels(), w.getframerate()
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if ch > 1:
        raw = raw.reshape(-1, ch).mean(1)
    if fr != sr:
        raw = np.interp(np.arange(0, len(raw), fr / sr), np.arange(len(raw)), raw)
    voice = np.zeros(int(DUR * sr) + sr)
    for s, e, at, _ in VOICE:
        seg = raw[int(s * sr):int(e * sr)]
        fade = np.minimum(1, np.minimum(np.arange(len(seg)), np.arange(len(seg))[::-1]) / (0.01 * sr))
        voice[int(at * sr):int(at * sr) + len(seg)] += seg * fade
    sfx = np.zeros_like(voice)
    t = np.arange(int(0.07 * sr)) / sr
    pip = np.sin(2 * np.pi * 1320 * t) * np.hanning(len(t)) * 0.08
    for k in np.arange(0.6, 6.1, 0.55):
        i = int(k * sr); sfx[i:i + len(pip)] += pip
    t = np.arange(int(0.6 * sr)) / sr
    drop = np.sin(2 * np.pi * (900 - 700 * t / 0.6) * t) * np.exp(-t * 4) * 0.10
    i = int(6.45 * sr); sfx[i:i + len(drop)] += drop
    mix = np.clip(voice + sfx, -1, 1)[: int(DUR * sr)]
    out = tmp / "mix.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    return out


def write_srt(path: Path):
    def ts(x):
        ms = int(round(x * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    lines = []
    for i, (s, e, at, text) in enumerate(VOICE, 1):
        lines += [str(i), f"{ts(at)} --> {ts(at + e - s)}", text, ""]
    path.write_text("\n".join(lines), encoding="utf-8")


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--media", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--srt", type=Path)
    ap.add_argument("--frames", type=str, help="comma list of times: PNG stills only")
    a = ap.parse_args()
    rig = Rig(height_px=RIG_H)
    mp = Map()
    geo_at = lambda tt: mp.frame(tt)[2]
    choreo = Choreo(rig, geo_at)
    co = Callouts()
    if a.srt:
        write_srt(a.srt)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        scope = T20.Scope(a.media, tmp)
        times = [float(x) for x in a.frames.split(",")] if a.frames else None
        proc = None
        if not times:
            mix = build_audio(a.media, tmp)
            proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                     "-r", str(FPS), "-i", "-", "-i", str(mix), "-c:v", "libx264", "-preset", "medium",
                                     "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "160k",
                                     "-movflags", "+faststart", "-shortest", str(a.out)], stdin=subprocess.PIPE)
        log = []
        frozen = {}
        for i, t in enumerate(times or [i / FPS for i in range(N)]):
            fr, minfo, geo = mp.frame(t)
            scope_label = scope.draw(fr, t, None)
            pose = choreo.pose(t)
            box, parts = rig.render(fr, pose, feet=FEET, return_boxes=True)
            anc = anchors(geo, T20.Scope.C, T20.Scope.R)
            cards = {}
            for text, t0, t1, key, off in CALLOUTS:
                an, card = anc[key]
                if an is None:
                    continue
                if card is None:       # card holds still for reading: placed from the anchor at its first frame
                    if text not in frozen:
                        frozen[text] = (an[0] + off[0], an[1] + off[1])
                    card = frozen[text]
                b = co.draw(fr, text, an, card, t, t0, t1)
                if b:
                    cards[text] = b
            if times:
                fr.convert("RGB").save(a.out.parent / f"still_{t:05.2f}.png")
            else:
                proc.stdin.write(fr.convert("RGB").tobytes())
            joints = {k: [round(v[0], 2), round(v[1], 2)] for k, v in rig.joint_points(pose, FEET).items()}
            log.append({"frame": i, "t": round(t, 4), "pose": {"lean": pose.lean, "head": pose.head, "arm_A": pose.arm_A,
                        "arm_B": pose.arm_B, "leg_A": pose.leg_A, "leg_B": pose.leg_B, "hand_B": pose.hand_B,
                        "eyes": pose.eyes, "scarf": round(pose.scarf, 3)},
                        "joints": joints, "rig_box": box, "part_boxes": parts, "cards": cards, "scope": scope_label,
                        "map": minfo, "earth": geo["earth"], "moon": geo["moon"]})
        if proc:
            proc.stdin.close()
            if proc.wait():
                raise SystemExit("ffmpeg failed")
    a.log.write_text(json.dumps({"fps": FPS, "size": [W, H], "frames": N, "rig_height": RIG_H, "rig_scale": rig.k,
                                 "voice": VOICE, "callouts": CALLOUTS, "scope": [T20.Scope.C, T20.Scope.R], "log": log},
                                default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o)))
    print("done")


if __name__ == "__main__":
    main()
