#!/usr/bin/env python3
"""15 s technical test: approved paper-cut ATLAS over three moving environments.

  A  0.0- 2.8 s  real footage (NASA SVS 15110 "Artemis II Earthrise", PD NASA media), slow camera push;
                 hero slides in from the left, stands bottom-left ("listen").
  B  2.8- 9.0 s  paper-cut Earth-Moon map: free-return path draws itself, capsule marker follows it,
                 camera pushes along the outbound leg then pulls back; star parallax; hero floats bottom-right ("explain").
  C  9.0-15.0 s  paper orbit diagram: planets orbit, comet path draws, camera pushes in;
                 hero stands left ("surprise"), then exits left.

Hard cuts between shots (handoff rule: no crossfades between poses). No limbs, no mouth, no lip sync.

  python3 -I scenes/test15.py --earthrise <NASA_ArtemisWow_Earthrise_Final.mp4> --out test.mp4 --log log.json
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from papercut.host import Cue, HostLayer, smoothstep  # noqa: E402
from papercut import paper as P  # noqa: E402

W, H, FPS = 1920, 1080, 30
N = 15 * FPS
SHOTS = [("A_footage", 0.0, 2.8), ("B_map", 2.8, 9.0), ("C_orbits", 9.0, 15.0)]
CAPTION_BOX = (360, 940, 1560, 1020)   # subtitle safe zone the hero must never enter
EARTHRISE_IN = 4.20                    # source seconds: Earth crescent over the lunar limb (no on-screen text)

CUES = [
    Cue(0.0, 2.8, "listen", x=200, y=1035, width=300, enter="left", name="A_bottom_left_enter"),
    Cue(2.8, 9.0, "explain", x=1785, y=945, width=240, drift=((1760, 930), 3.2, 8.6), name="B_float_bottom_right"),
    Cue(9.0, 15.0, "surprise", x=300, y=900, width=300, exit="left", name="C_left_then_exit"),
]


def shot_at(t):
    for name, a, b in SHOTS:
        if a <= t < b:
            return name, t - a
    return SHOTS[-1][0], t - SHOTS[-1][1]


def camera(world: Image.Image, cx, cy, zoom) -> Image.Image:
    """Sub-pixel camera: view centred on world (cx, cy) at `zoom`, output W x H."""
    inv = 1 / zoom
    coeffs = (inv, 0, cx - W / 2 * inv, 0, inv, cy - H / 2 * inv)
    return world.transform((W, H), Image.Transform.AFFINE, coeffs, resample=Image.Resampling.BICUBIC)


def subtitle(frame):
    d = ImageDraw.Draw(frame)
    f = P.font(40)
    text = "[test subtitle - safe area]"
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=f)
    w = x1 - x0 + 48
    bx = (W - w) // 2
    frame.alpha_composite(Image.new("RGBA", (w, 70), (0, 0, 0, 160)), (bx, 945))
    d.text((bx + 24 - x0, 945 + 35 - (y1 - y0) / 2 - y0), text, font=f, fill=(255, 255, 255))


# ------------------------------------------------------------------ shot A
def footage_frames(src: Path, tmp: Path, n: int):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{EARTHRISE_IN}", "-i", str(src), "-frames:v", str(n),
                    "-vf", "scale=1920:1080", str(tmp / "a_%04d.png")], check=True)
    return sorted(tmp.glob("a_*.png"))


def shot_a(frames, tl):
    i = min(int(round(tl * FPS)), len(frames) - 1)
    src = Image.open(frames[i]).convert("RGBA")
    z = 1.0 + 0.05 * smoothstep(tl / 2.8)
    out = camera(src, W / 2 + 20 * tl, H / 2, z)
    P.label(out, "NASA SVS / ARTEMIS II", (48, 40), size=24)
    return out


# ------------------------------------------------------------------ shot B
class MapWorld:
    WW, WH = 2800, 1600
    DY = 200

    def __init__(self):
        WW, WH = self.WW, self.WH
        self.stars = P.paper_sheet(WW, WH, P.NAVY, 11, 0.10)
        d = ImageDraw.Draw(self.stars)
        rng = np.random.default_rng(3)
        for _ in range(260):
            x, y, r = rng.uniform(0, WW), rng.uniform(0, WH), rng.choice([1.2, 1.6, 2.2])
            d.ellipse((x - r, y - r, x + r, y + r), fill=(232, 222, 200, int(rng.uniform(120, 230))))
        for _ in range(14):
            x, y, s = rng.uniform(0, WW), rng.uniform(0, WH), rng.uniform(7, 13)
            d.polygon([(x, y - s), (x + s * .25, y - s * .25), (x + s, y), (x + s * .25, y + s * .25),
                       (x, y + s), (x - s * .25, y + s * .25), (x - s, y), (x - s * .25, y - s * .25)],
                      fill=(245, 196, 92, 230))
        self.main = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
        self.earth = (750, 640 + self.DY, 190)
        self.moon = (2200, 560 + self.DY, 110)
        self._bodies()
        self.path = self._path()
        self._path_layers()

    def _bodies(self):
        ex, ey, er = self.earth
        m = P.ss_mask((self.WW, self.WH), lambda d, s: d.ellipse(((ex - er) * s, (ey - er) * s, (ex + er) * s, (ey + er) * s), fill=255))
        self.main.alpha_composite(P.cutout(m, P.BLUE, 21, border=9))
        land = P.ss_mask((self.WW, self.WH), lambda d, s: [
            d.polygon([((ex + u) * s, (ey + v) * s) for u, v in poly], fill=255) for poly in (
                [(-120, -90), (-40, -140), (30, -110), (10, -40), (-60, -10), (-110, -30)],
                [(40, 10), (120, -20), (150, 60), (90, 130), (30, 90)],
                [(-130, 60), (-70, 50), (-50, 110), (-110, 120)])])
        land = Image.fromarray(np.minimum(np.asarray(land), np.asarray(m)))
        self.main.alpha_composite(P.cutout(land, (122, 158, 104), 23, shadow=True, shadow_offset=(3, 4), shadow_blur=2, shadow_alpha=0.3))
        mx, my, mr = self.moon
        mm = P.ss_mask((self.WW, self.WH), lambda d, s: d.ellipse(((mx - mr) * s, (my - mr) * s, (mx + mr) * s, (my + mr) * s), fill=255))
        self.main.alpha_composite(P.cutout(mm, (200, 196, 186), 31, border=8))
        cr = P.ss_mask((self.WW, self.WH), lambda d, s: [d.ellipse(((mx + u - r) * s, (my + v - r) * s, (mx + u + r) * s, (my + v + r) * s), fill=255)
                                                        for u, v, r in ((-40, -30, 22), (35, 20, 16), (-10, 50, 12), (50, -45, 10))])
        self.main.alpha_composite(P.cutout(cr, (160, 156, 150), 33, shadow=False))
        d = ImageDraw.Draw(self.main)
        for text, (x, y) in (("EARTH", (ex - 70, ey + er + 40)), ("MOON", (mx - 55, my + mr + 36))):
            P.label(self.main, text, (x, y), size=30, fg=P.INK, bg=(*P.CREAM, 255), pad=(16, 8))

    def _path(self):
        ctrl = [(935, 590), (1250, 430), (1750, 400), (2100, 410), (2320, 470), (2360, 590), (2250, 690),
                (2060, 660), (1750, 700), (1300, 770), (945, 700)]
        ctrl = [(x, y + self.DY) for x, y in ctrl]
        pts = []
        c = [ctrl[0]] + ctrl + [ctrl[-1]]
        for i in range(1, len(c) - 2):
            p0, p1, p2, p3 = map(np.array, (c[i - 1], c[i], c[i + 1], c[i + 2]))
            for t in np.linspace(0, 1, 60, endpoint=False):
                pts.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                  + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        pts.append(np.array(ctrl[-1], float))
        pts = np.array(pts)
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        self.arclen = np.concatenate([[0], np.cumsum(seg)]) / seg.sum()
        return pts

    def _path_layers(self):
        """AA dashed path mask + per-pixel reveal parameter (0..1 along the path)."""
        ss = 2
        aa = Image.new("L", (self.WW * ss, self.WH * ss), 0)
        prm = Image.new("F", (self.WW, self.WH), 9.0)
        da, dp = ImageDraw.Draw(aa), ImageDraw.Draw(prm)
        dash, gap = 26 / 1.0, 16
        pos, on = 0.0, True
        total = self.arclen[-1]
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(self.path, axis=0), axis=1))])
        Ltot = L[-1]
        s = 0.0
        while s < Ltot:
            e = min(Ltot, s + dash)
            seg = [tuple(self._pt_at(u / Ltot, L)) for u in np.linspace(s, e, 6)]
            da.line([(x * ss, y * ss) for x, y in seg], fill=255, width=7 * ss, joint="curve")
            dp.line(seg, fill=float(e / Ltot), width=14)
            s = e + gap
        self.path_aa = np.asarray(aa.resize((self.WW, self.WH), Image.Resampling.LANCZOS), np.float32) / 255
        self.path_param = np.asarray(prm, np.float32)
        col = np.array(P.ORANGE, np.float32) / 255
        self.path_rgb = np.ones((self.WH, self.WW, 3), np.float32) * col

    def _pt_at(self, u, L=None):
        idx = np.searchsorted(self.arclen, u)
        idx = int(np.clip(idx, 1, len(self.path) - 1))
        a0, a1 = self.arclen[idx - 1], self.arclen[idx]
        f = 0 if a1 == a0 else (u - a0) / (a1 - a0)
        return self.path[idx - 1] * (1 - f) + self.path[idx] * f

    def frame(self, tl):
        u = smoothstep((tl - 0.3) / 5.6) * 0.999
        tip = self._pt_at(u)
        ahead = self._pt_at(min(1, u + 0.004))
        # camera: push along the outbound leg, then pull back to reveal the whole route
        a1, a2 = smoothstep(tl / 3.2), smoothstep((tl - 3.4) / 2.6)
        cx = 1000 + 640 * a1 + (1400 - 1640) * a2
        cy = 900.0 - 100 * a2
        z = 1.0 + 0.05 * a1 + (0.75 - 1.05) * a2
        # main layer with revealed path
        reveal = self.path_aa * (self.path_param <= u)
        world = self.main.copy()
        pa = (reveal[..., None] * np.concatenate([self.path_rgb, np.ones_like(self.path_rgb[..., :1])], -1) * 255).astype(np.uint8)
        world.alpha_composite(Image.fromarray(pa, "RGBA"))
        # star layer at half parallax
        bg = camera(self.stars, 1000 + (cx - 1000) * 0.5, cy, 1 + (z - 1) * 0.5)
        fg = camera(world, cx, cy, z)
        bg.alpha_composite(fg)
        # capsule marker at the drawing tip (screen space)
        sx, sy = (tip[0] - cx) * z + W / 2, (tip[1] - cy) * z + H / 2
        ang = math.degrees(math.atan2(ahead[1] - tip[1], ahead[0] - tip[0]))
        bg.alpha_composite(*capsule(sx, sy, ang))
        P.label(bg, "ILLUSTRATION - NOT TO SCALE", (W - 470, 40), size=24)
        return bg


_CAPSULE = None


def capsule(sx, sy, ang):
    global _CAPSULE
    if _CAPSULE is None:
        s = 4
        m = Image.new("L", (90 * s, 60 * s), 0)
        d = ImageDraw.Draw(m)
        d.polygon([(20 * s, 12 * s), (62 * s, 22 * s), (62 * s, 38 * s), (20 * s, 48 * s)], fill=255)
        d.rectangle((62 * s, 20 * s, 74 * s, 40 * s), fill=255)
        m = m.resize((90, 60), Image.Resampling.LANCZOS)
        _CAPSULE = P.cutout(m, (236, 232, 222), 41, border=3, border_color=P.ORANGE, shadow_offset=(3, 4), shadow_blur=3)
    im = _CAPSULE.rotate(-ang + 180, resample=Image.Resampling.BICUBIC, expand=True)
    return im, (int(round(sx - im.width / 2)), int(round(sy - im.height / 2)))


# ------------------------------------------------------------------ shot C
class OrbitWorld:
    WW, WH = 2200, 1240
    SUN = (1330, 560)
    ORBITS = [(240, 140, 2.1, 0.3, P.BLUE, 22), (400, 235, 1.25, 2.0, P.PEACH, 26), (560, 330, 0.7, 4.1, (214, 150, 74), 34)]

    def __init__(self):
        WW, WH = self.WW, self.WH
        self.base = P.paper_sheet(WW, WH, P.CREAM, 51, 0.06)
        d = ImageDraw.Draw(self.base)
        sx, sy = self.SUN
        ring = P.ss_mask((WW, WH), lambda dd, s: [dd.ellipse(((sx - a) * s, (sy - b) * s, (sx + a) * s, (sy + b) * s), outline=255, width=5 * s)
                                                  for a, b, *_ in self.ORBITS])
        self.base.alpha_composite(P.cutout(ring, (70, 80, 110), 53, shadow=False))
        sun = P.ss_mask((WW, WH), lambda dd, s: dd.ellipse(((sx - 92) * s, (sy - 92) * s, (sx + 92) * s, (sy + 92) * s), fill=255))
        rays = P.ss_mask((WW, WH), lambda dd, s: [dd.polygon([((sx + math.cos(a) * 112) * s, (sy + math.sin(a) * 112) * s),
                                                               ((sx + math.cos(a + .12) * 150) * s, (sy + math.sin(a + .12) * 150) * s),
                                                               ((sx + math.cos(a + .24) * 112) * s, (sy + math.sin(a + .24) * 112) * s)], fill=255)
                                                   for a in np.linspace(0, 2 * math.pi, 14, endpoint=False)])
        self.rays = P.cutout(rays, (245, 180, 60), 55, shadow_offset=(4, 5), shadow_blur=4)
        self.base.alpha_composite(P.cutout(sun, P.ORANGE, 57, border=8))
        self.sun = P.cutout(sun, P.ORANGE, 57, border=8, shadow=False)   # re-laid over the rotating rays
        self.planets = {}
        for a, b, w, ph, col, r in self.ORBITS:
            m = Image.new("L", (r * 2 * 4, r * 2 * 4), 0)
            ImageDraw.Draw(m).ellipse((0, 0, r * 8 - 1, r * 8 - 1), fill=255)
            m = m.resize((r * 2, r * 2), Image.Resampling.LANCZOS)
            pad = Image.new("L", (r * 2 + 30, r * 2 + 30), 0)
            pad.paste(m, (15, 15))
            self.planets[r] = P.cutout(pad, col, 60 + r, border=5, shadow_offset=(4, 5), shadow_blur=3)
        # comet path (drawn progressively in screen space)
        t = np.linspace(0, 1, 240)[:, None]
        b = [np.array(q, float) for q in ((2150, 60), (1700, 1000), (900, 900), (700, 200))]
        self.comet = ((1 - t) ** 3 * b[0] + 3 * (1 - t) ** 2 * t * b[1] + 3 * (1 - t) * t ** 2 * b[2] + t ** 3 * b[3])

    def frame(self, tl):
        sx, sy = self.SUN
        world = self.base.copy()
        rr = self.rays.rotate(tl * 9, center=self.SUN, resample=Image.Resampling.BICUBIC)
        world.alpha_composite(rr)
        world.alpha_composite(self.sun)
        for a, b, w, ph, col, r in self.ORBITS:
            ang = ph + w * tl
            px, py = sx + a * math.cos(ang), sy + b * math.sin(ang)
            im = self.planets[r]
            world.alpha_composite(im, (int(round(px - im.width / 2)), int(round(py - im.height / 2))))
        z = 1.0 + 0.10 * smoothstep(tl / 6.0)
        cx = 1100 + 120 * smoothstep(tl / 6.0)
        cy = 600
        out = camera(world, cx, cy, z)
        # comet: dashed trail drawn progressively, in screen space with 2x supersampling
        u = smoothstep((tl - 0.5) / 4.5)
        k = max(2, int(u * len(self.comet)))
        pts = [((x - cx) * z + W / 2, (y - cy) * z + H / 2) for x, y in self.comet[:k]]
        ss = 2
        m = Image.new("L", (W * ss, H * ss), 0)
        d = ImageDraw.Draw(m)
        for i in range(0, len(pts) - 1, 6):
            seg = pts[i:i + 4]
            if len(seg) >= 2:
                d.line([(x * ss, y * ss) for x, y in seg], fill=255, width=6 * ss)
        m = m.resize((W, H), Image.Resampling.LANCZOS)
        trail = Image.new("RGBA", (W, H), (*P.ORANGE, 255))
        trail.putalpha(m)
        out.alpha_composite(trail)
        if k > 2:
            hx, hy = pts[-1]
            d2 = ImageDraw.Draw(out)
            d2.ellipse((hx - 13, hy - 13, hx + 13, hy + 13), fill=(*P.CREAM, 255), outline=P.INK, width=4)
        P.label(out, "ILLUSTRATION", (W - 260, 40), size=24)
        return out


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--earthrise", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--log", required=True, type=Path)
    ap.add_argument("--no-host", action="store_true", help="render environment only (for A/B checks)")
    a = ap.parse_args()

    host = HostLayer((W, H), CUES)
    mapw, orbw = MapWorld(), OrbitWorld()
    log = []
    with tempfile.TemporaryDirectory() as td:
        frames = footage_frames(a.earthrise, Path(td), int(2.8 * FPS))
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{N / FPS}",
               "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS),
               "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-shortest", str(a.out)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(N):
            t = i / FPS
            shot, tl = shot_at(t)
            fr = shot_a(frames, tl) if shot == "A_footage" else mapw.frame(tl) if shot == "B_map" else orbw.frame(tl)
            info = None if a.no_host else host.render(fr, t)
            subtitle(fr)
            proc.stdin.write(fr.convert("RGB").tobytes())
            log.append({"frame": i, "t": round(t, 4), "shot": shot, "host": info})
        proc.stdin.close()
        if proc.wait():
            raise SystemExit("ffmpeg failed")
    a.log.write_text(json.dumps({"fps": FPS, "size": [W, H], "frames": N, "shots": SHOTS,
                                 "caption_box": CAPTION_BOX, "log": log}))
    print(f"wrote {a.out} and {a.log}")


if __name__ == "__main__":
    main()
