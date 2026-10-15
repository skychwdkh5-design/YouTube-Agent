"""OrbitalAtlas Shorts from EP002 (Dubai Islands) and EP003 (Great Salt Lake). 1080x1920, 30 fps, 15.000 s each.

    python3 productions/shorts-ep002-ep003/shorts_build.py stills NAME OUTDIR t1 t2 ...
    python3 productions/shorts-ep002-ep003/shorts_build.py render NAME OUT.mp4 [--workers 4]
NAME: dubai1 | dubai2 | gsl1 | gsl2.   Sources (restored from the media branches, see CONCEPTS.md):
  SRC/dubai/dubai_ast_*.jpg (NASA Earth Observatory World of Change, ASTER/Terra), productions/dubai/visuals/palm2.jpg (ASTER 18 Sep 2006),
  productions/dubai/visuals/iss067e003785_lrg.jpg (ISS astronaut photograph 6 Apr 2022), SRC/gsl/y*.png (calibrated Landsat stack, USGS),
  productions/ep003-great-salt-lake/assets/geo/water_y1986.png / water_y2022.png (EP003 traced water masks), SRC/audio/* (approved narrations).
"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, ROOT)
from orbitalatlas import shorts as SH, easing as E, typeset as TS, sequence as SQ, music, textrec as TR
from orbitalatlas.director import Geo

SRC = os.environ.get("SHORTS_SRC", "/tmp/claude-0/s/src")
DUR, FPS, BPM = 15.0, 30, 128.0
BEAT = 60.0 / BPM
AMBER, CYAN, WHITE, INK = SH.AMBER, SH.CYAN, SH.WHITE, SH.INK


def words(vfile, a, b, at):
    """approved narration words between source times a..b, shifted to programme time `at` (provider timings)."""
    d = json.load(open(os.path.join(SRC, "audio", vfile)))
    return [dict(text=w["text"], start=w["start"] - a + at, end=w["end"] - a + at) for w in d["words"] if a - 0.01 <= w["start"] and w["end"] <= b + 0.01]


def slam0(*a):
    """SH.slam that is invisible (alpha 0) before its start instead of None - for words placed unconditionally."""
    return SH.slam(*a) or (1.0, 0.0, 0.0)


def wt(ws, text, k=0):
    hits = [w for w in ws if w["text"].strip(".,:").lower() == text.lower()]; return hits[k]["start"]


class Short:
    name = "short"; size = (SH.W, SH.H); start = 0.0; duration = DUR

    def __init__(self):
        self.shots = [type("S", (), {"scene": self})()]

    def render(self, t): raise NotImplementedError

    def finish(self, img, ui):
        img = img.convert("RGBA"); img.alpha_composite(ui); return img.convert("RGB")


# ===================================================================== EP002 S1
class Dubai1(Short):
    """JUST SEA. - Nov 2000 open sea -> Feb 2002 -> Oct 2002 -> Nov 2003 palm (beat cuts, same NASA framing, no registered wipe);
    two separate panels 2000 / 2003, each centred on the site; the 2000 panel grows back to the first frame (loop)."""
    name = "EP002_Dubai_Short_01"
    DATES = [("20001111", "NOV 11, 2000"), ("20020202", "FEB 2, 2002"), ("20021016", "OCT 16, 2002"), ("20031104", "NOV 4, 2003")]
    PALM = (0.114, 0.551)
    TOP, BOT = (0, 300, 1080, 860), (0, 1100, 1080, 1660)

    def __init__(self):
        super().__init__(); d = os.path.join(SRC, "dubai"); mp3 = os.path.join(SRC, "audio", "ep002.mp3")
        self.img = {k: SH.ImageView(os.path.join(d, f"dubai_ast_{k}_cyl.jpg")) for k, _ in self.DATES}
        self.v1 = words("ep002.voice.json", 5.05, 7.83, 0.30); self.v2 = words("ep002.voice.json", 8.21, 13.65, 4.85); self.v3 = words("ep002.voice.json", 14.10, 16.58, 11.0)
        self.voice = [(mp3, 5.05, 7.83, 0.30), (mp3, 8.21, 13.65, 4.85), (mp3, 14.10, 16.58, 11.0)]
        self.t_sea = wt(self.v1, "Just"); self.t_nov = wt(self.v2, "November"); self.t_palm = wt(self.v2, "palm"); self.t_fully = wt(self.v2, "fully")
        self.t_three = wt(self.v3, "three"); self.t_between = wt(self.v3, "Between"); self.t_split = self.t_between - 0.1
        self.flip = [(3.30, "20020202"), (3.30 + 2 * BEAT, "20021016"), (self.t_nov - 0.05, "20031104")]
        self.cues = [dict(t=0.02, kind="impact"), dict(t=self.t_sea, kind="impact"), dict(t=3.30, kind="whoosh"), dict(t=3.30 + 2 * BEAT, kind="whoosh"), dict(t=self.t_nov - 0.08, kind="sweep"),
                     dict(t=self.t_palm - 0.25, kind="whoosh"), dict(t=self.t_fully, kind="impact"), dict(t=self.t_split, kind="whoosh"), dict(t=self.t_three, kind="impact"), dict(t=13.85, kind="sweep")]
        self.accents = [3.30, self.t_nov, self.t_fully, self.t_three]

    def frame_at(self, t):
        k = "20001111"
        for t0, key in self.flip:
            if t >= t0: k = key
        return k

    def view(self, t):
        P = self.PALM; tight = (P[0] + 0.03, P[1] + 0.015, 720.0)
        if t < 3.3: return SH.lerp_view((P[0] + 0.03, P[1] + 0.015, 860.0), tight, 0.25 * E.out_cubic(t / 3.3) + 0.75 * t / 3.3)   # steady push, no settle
        if t < self.t_nov: return SH.lerp_view(tight, (P[0] + 0.02, P[1] + 0.01, 650.0), E.smooth(E.seg(t, 3.3, self.t_nov)))
        if t < self.t_palm - 0.25: return SH.lerp_view((P[0] + 0.02, P[1] + 0.01, 650.0), (P[0] + 0.015, P[1] + 0.005, 600.0), E.seg(t, self.t_nov, self.t_palm))
        z = E.in_out_cubic(E.seg(t, self.t_palm - 0.25, self.t_palm + 0.35))
        return SH.lerp_view((P[0] + 0.015, P[1] + 0.005, 600.0), (P[0], P[1] - 0.004, 300.0 * (1 - 0.06 * E.seg(t, self.t_palm + 0.35, 11.0))), z)

    def render(self, t):
        ui = Image.new("RGBA", self.size, (0, 0, 0, 0))
        if t < self.t_split or t >= 14.4:
            cx, cy, w = self.view(t) if t < 14.4 else self.view(0.0)
            img = self.img[self.frame_at(t) if t < 14.4 else "20001111"].view(cx, cy, w)
            if self.t_palm - 0.25 <= t <= self.t_palm + 0.35: img = SH.zoom_blur(img, 0.10 * math.sin(math.pi * E.seg(t, self.t_palm - 0.25, self.t_palm + 0.35)))
            for t0, _ in self.flip:
                if 0 <= t - t0 < 2 / FPS: img = Image.blend(img, Image.new("RGB", self.size, (255, 246, 228)), 0.18)
        else:
            img = self.panels(t)
        img = SH.vignette(img, 0.42)
        self.typography(ui, t)
        return self.finish(img, ui)

    def panels(self, t):
        """'Between these two pictures': two separate crops (2000 above, 2003 below), each centred on the site at the same scale.
        Not a registered wipe - the NASA frames are not re-registered (CONCEPTS.md)."""
        P = self.PALM; w = 700.0; u = E.out_expo(E.seg(t, self.t_split, self.t_split + 0.45)); c = E.in_out_cubic(E.seg(t, 13.85, 14.4))
        bg = self.img["20031104"].view(P[0] + 0.02, P[1], 1400.0).filter(ImageFilter.GaussianBlur(14)); out = Image.blend(bg, Image.new("RGB", self.size, INK), 0.72)
        z0 = self.view(0.0)
        top = [a + (b - a) * c for a, b in zip(self.TOP, (0, 0, SH.W, SH.H))]; tw = w + (z0[2] - w) * c
        tcx, tcy = P[0] + (z0[0] - P[0]) * c, P[1] + (z0[1] - P[1]) * c; dx = int(-SH.W * (1 - u))
        for key, rect, (cx, cy, ww), off in (("20031104", self.BOT, (P[0], P[1], w), -dx + int(SH.W * c)), ("20001111", top, (tcx, tcy, tw), dx)):
            x0, y0, x1, y1 = [int(round(v)) for v in rect]; size = (max(2, x1 - x0), max(2, y1 - y0))
            drift = E.seg(t, self.t_split, 13.85); k = 1 - 0.16 * drift if key == "20031104" else 1 - 0.10 * drift * (1 - c)   # counter-pushes: parallax between panels
            cx = cx + (0.012 * drift if key == "20031104" else -0.010 * drift * (1 - c))
            pan = self.img[key].view(cx, cy, ww * k * size[0] / SH.W, size=size); out.paste(pan, (x0 + off, y0))
            if c < 0.99: ImageDraw.Draw(out).rectangle([x0 + off, y0, x1 - 1 + off, y1 - 1], outline=AMBER, width=4)
        return out

    def typography(self, ui, t):
        k = self.frame_at(t) if t < 14.4 else "20001111"; label = dict(self.DATES)[k]
        in_split = self.t_split <= t < 14.4
        SH.chip(ui, "ASTER · NASA · NOV 2000 / NOV 2003" if in_split else f"ASTER · NASA EARTH OBSERVATORY · {label}", 60, 100, 30)
        SH.chip(ui, "FALSE COLOR: PLANTS APPEAR RED", 60, 152, 30, accent=CYAN)
        # hook: NO ISLAND. is on screen from frame 0 (and fades back in at the end: loop); JUST SEA. lands on the word
        if t < 3.6 or t >= 14.45:
            out = 1 - E.smooth(E.seg(t, 3.25, 3.55)) if t < 14.45 else E.smooth(E.seg(t, 14.45, 14.9))
            SH.place(ui, SH.extrude("NO ISLAND.", 132, 10, WHITE, (90, 100, 115)), SH.W / 2, 640, 1.0 + 0.03 * (1 - E.out_cubic(E.seg(t, 0, 3.3))) if t < 14.45 else 1.03, out, 0, record="NO ISLAND.", px=132)
            s = SH.slam(t, self.t_sea - 0.06) if t < 14.45 else None
            if s: SH.place(ui, SH.extrude("JUST SEA.", 132, 10, AMBER, (120, 90, 40)), SH.W / 2, 810, s[0], s[1] * out, s[2], record="JUST SEA.", px=132, color=AMBER)
        for t0, txt in ((self.flip[0][0], "FIRST STAGE"), (self.flip[1][0], "FRONDS IN A RING")):
            if t0 <= t < min(t0 + 2 * BEAT - 0.03, self.t_nov - 0.08):                       # never overlaps THE SAME PLACE.
                s = slam0(t, t0, 0.25, 1.4); tile, _, _ = SH.word_tile(txt, 86, "black", WHITE)
                SH.place(ui, tile, SH.W / 2, 1180, s[0], s[1], s[2], record=txt, px=86)
        if 3.3 <= t < self.t_split:
            b = SH.Badge(SH.W / 2, 420, 120); yr = label[-4:]
            burst = max(math.sin(math.pi * E.seg(t, self.t_nov - 0.05, self.t_nov + 0.5)), 0.0)
            b.draw(ui, yr, 0.28 * burst, 40 * t, 1.0 + 0.12 * burst, 1.0 - E.smooth(E.seg(t, self.t_split - 0.3, self.t_split)), 62)
        if self.t_nov - 0.05 <= t < self.t_palm - 0.1:
            s = slam0(t, self.t_nov - 0.05, 0.3, 1.4); tile, _, _ = SH.word_tile("THE SAME PLACE.", 84, "black", WHITE)
            SH.place(ui, tile, SH.W / 2, 1180, s[0], s[1] * (1 - E.smooth(E.seg(t, self.t_palm - 0.35, self.t_palm - 0.1))), s[2], record="THE SAME PLACE.", px=84)
        if self.t_palm - 0.1 <= t < self.t_split:
            out = 1 - E.smooth(E.seg(t, self.t_split - 0.3, self.t_split))
            s = slam0(t, self.t_palm - 0.08, 0.28, 1.5); SH.place(ui, SH.extrude("A PALM TREE,", 112, 8, WHITE, (90, 100, 115)), SH.W / 2, 1080, s[0], s[1] * out, s[2], record="A PALM TREE,", px=112)
            s = SH.slam(t, self.t_fully - 0.06, 0.28, 1.8)
            if s: SH.place(ui, SH.extrude("FULLY FORMED.", 100, 12, AMBER, (130, 92, 30)), SH.W / 2 - 8, 1250, s[0], s[1] * out, s[2], record="FULLY FORMED.", px=100, color=AMBER)
        if in_split:
            a = E.smooth(E.seg(t, self.t_split + 0.3, self.t_split + 0.55)) * (1 - E.smooth(E.seg(t, 13.6, 13.85)))
            for y, txt in ((self.TOP[1] + 60, "NOV 2000"), (self.BOT[1] + 60, "NOV 2003")):
                tile, _, _ = SH.word_tile(txt, 64, "black", WHITE); SH.place(ui, tile, 100 + tile.width / 2, y, 1.0, a, 0, record=txt, px=64)
            s = SH.slam(t, self.t_three - 0.05, 0.3, 1.9)
            if s: SH.place(ui, SH.extrude("3 YEARS.", 170, 16, AMBER, (130, 92, 30)), SH.W / 2, 975, s[0], s[1] * (1 - E.smooth(E.seg(t, 13.6, 13.85))), s[2], record="3 YEARS.", px=170, color=AMBER)


# ===================================================================== EP002 S2
class Dubai2(Short):
    """FOUR PROJECTS. ONE PICTURE. - ASTER 18 Sep 2006 on a tilted plane, camera south -> north; anchored labels pop on the spoken names
    (projected through the same tilt); facts on a flat map; ISS photograph 2022; back to the tilted wide (loop)."""
    name = "EP002_Dubai_Short_02"
    PROJ = [("PALM JEBEL ALI", (0.178, 0.816)), ("PALM JUMEIRAH", (0.454, 0.573)), ("THE WORLD", (0.493, 0.355)), ("PALM DEIRA", (0.743, 0.110))]
    WIDE = (0.47, 0.50, 1750.0); TILT = 30.0

    def __init__(self):
        super().__init__(); v = os.path.join(ROOT, "productions", "dubai", "visuals")
        self.a06 = SH.ImageView(os.path.join(v, "palm2.jpg")); self.iss = SH.ImageView(os.path.join(v, "iss067e003785_lrg.jpg"))
        self.vw = words("ep002.voice.json", 222.97, 232.96, 0.30); self.voice = [(os.path.join(SRC, "audio", "ep002.mp3"), 222.97, 232.96, 0.30)]
        self.t_names = [wt(self.vw, "Palm", 0), wt(self.vw, "Palm", 1), wt(self.vw, "World"), wt(self.vw, "Palm", 2)]
        self.t_four = wt(self.vw, "four"); self.t_2006 = wt(self.vw, "2006"); self.t_south = wt(self.vw, "south")
        self.t_sand, self.t_rock, self.t_iss, self.t_back = 10.75, 11.95, 13.0, 14.25
        self.cues = [dict(t=0.02, kind="impact"), dict(t=self.t_2006, kind="tick"), dict(t=self.t_four, kind="impact")] + [dict(t=x - 0.15, kind="whoosh") for x in self.t_names] + \
                    [dict(t=self.t_sand - 0.1, kind="sweep"), dict(t=self.t_rock, kind="impact"), dict(t=self.t_iss - 0.2, kind="whoosh"), dict(t=self.t_back - 0.2, kind="whoosh")]
        self.accents = [self.t_four, self.t_names[0], self.t_sand, self.t_iss]

    def cam(self, t):
        keys = [(0.0, self.WIDE), (self.t_names[0] - 0.6, (0.38, 0.64, 1350.0))]          # intro: steady push south toward the first name
        for (name, p), tn in zip(self.PROJ, self.t_names): keys.append((tn - 0.2, (p[0], p[1], 1050.0))); keys.append((tn + 0.55, (p[0], p[1] + 0.01, 960.0)))
        keys += [(10.4, (0.45, 0.58, 1200.0)), (self.t_iss - 0.25, (0.454, 0.573, 520.0))]
        for (ta, a), (tb, b) in zip(keys, keys[1:]):
            if ta <= t < tb: return SH.lerp_view(a, b, E.in_out_cubic((t - ta) / (tb - ta)))
        return keys[-1][1]

    def tilt_at(self, t):
        if t >= self.t_back: return self.TILT * E.smooth(E.seg(t, self.t_back, 14.85))
        return self.TILT * (1 - E.smooth(E.seg(t, 9.9, 10.6)))

    def render(self, t):
        ui = Image.new("RGBA", self.size, (0, 0, 0, 0))
        if t < self.t_iss or t >= self.t_back:
            view = self.cam(t) if t < self.t_back else SH.lerp_view((0.454, 0.573, 520.0), self.WIDE, E.in_out_cubic(E.seg(t, self.t_back, 14.85)))
            deg = self.tilt_at(t); big = SH.big_size(deg); cx, cy, w = view                   # keep the oversize view inside the picture (no empty edge)
            wb = w * big[0] / SH.W; hx = wb * 0.5 / self.a06.w; hy = wb * big[1] / big[0] * 0.5 / self.a06.h
            cx = min(max(cx, hx), 1 - hx) if hx < 0.5 else 0.5; cy = min(max(cy, hy), 1 - hy) if hy < 0.5 else 0.5
            img, to_scr = SH.tilted_view(self.a06, cx, cy, w, deg, bg=(6, 9, 14))
            for tn in self.t_names:
                if tn - 0.25 <= t < tn + 0.2: img = SH.zoom_blur(img, 0.06 * math.sin(math.pi * E.seg(t, tn - 0.25, tn + 0.2)))
            if t >= self.t_back: img = SH.zoom_blur(img, 0.025 * math.sin(math.pi * E.seg(t, self.t_back, 14.85)))
            self.labels(ui, t, to_scr)
        else:
            u = E.seg(t, self.t_iss, self.t_back); img = self.iss.view(0.70, 0.256 + 0.02 * u, 1300 - 250 * E.out_cubic(u))
            if u < 0.12: img = SH.zoom_blur(img, 0.10 * (1 - u / 0.12))
        img = SH.vignette(img, 0.4); self.type(ui, t)
        return self.finish(img, ui)

    def labels(self, ui, t, to_scr):
        for i, ((name, p), tn) in enumerate(zip(self.PROJ, self.t_names)):
            if not (tn - 0.05 <= t < 10.6): continue
            x, y = to_scr(p)
            a = E.out_cubic(E.seg(t, tn - 0.05, tn + 0.25)) * (1 - E.smooth(E.seg(t, 10.25, 10.6)))
            if not (60 < x < SH.W - 60 and 260 < y < SH.H - 300): continue
            d = ImageDraw.Draw(ui); r = 70 + 12 * math.sin(math.pi * E.seg(t, tn, tn + 0.35))
            d.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8], outline=AMBER + (int(255 * a),), width=6)
            ly = y - 230 if y > 760 else y + 200; d.line([(x, y - r * 0.8 if ly < y else y + r * 0.8), (x, ly + (45 if ly < y else -45))], fill=WHITE + (int(220 * a),), width=4)
            s = slam0(t, tn - 0.05, 0.25, 1.5); tile = SH.extrude(name, 70, 6, WHITE, (90, 100, 115))
            lx = min(max(x, 100 + tile.width / 2), 980 - tile.width / 2 - 20); SH.place(ui, tile, lx, ly, s[0], s[1] * a, s[2], record=name, px=70)

    def type(self, ui, t):
        iss = self.t_iss <= t < self.t_back
        SH.chip(ui, "ISS ASTRONAUT PHOTO · APR 6, 2022" if iss else "ASTER/TERRA · SEP 18, 2006", 60, 100, 30, accent=CYAN if iss else AMBER)
        SH.chip(ui, "NASA JSC · ISS067-E-3785" if iss else "NASA/GSFC/MITI/ERSDAC/JAROS", 60, 152, 30, accent=CYAN if iss else AMBER)
        if t < self.t_names[0] - 0.2 or t >= 14.6:
            out = 1 - E.smooth(E.seg(t, self.t_names[0] - 0.55, self.t_names[0] - 0.2)) if t < 14.6 else E.smooth(E.seg(t, 14.6, 14.95))
            pulse = 1.0 + 0.06 * math.sin(math.pi * E.seg(t, self.t_four - 0.05, self.t_four + 0.3)) if t < 14.6 else 1.0
            SH.place(ui, SH.extrude("4 PROJECTS.", 112, 12, WHITE, (90, 100, 115)), SH.W / 2, 560, pulse, out, 0, record="4 PROJECTS.", px=112)
            s = SH.slam(t, self.t_2006 - 0.05, 0.3, 1.8) if t < 14.6 else None
            if s: SH.place(ui, SH.extrude("ONE PICTURE.", 108, 12, AMBER, (130, 92, 30)), SH.W / 2, 760, s[0], s[1] * out, s[2], record="ONE PICTURE.", px=108, color=AMBER)
            s = SH.slam(t, self.t_south - 0.05, 0.25, 1.3) if t < 14.6 else None
            if s: tile, _, _ = SH.word_tile("SOUTH → NORTH", 70, "black", CYAN); SH.place(ui, tile, SH.W / 2, 1180, s[0], s[1] * out, s[2], record="SOUTH → NORTH", px=70, color=CYAN)
        if self.t_sand - 0.05 <= t < self.t_iss:
            u = E.seg(t, self.t_sand - 0.05, self.t_sand + 0.25)
            hold = 1 - E.smooth(E.seg(t, self.t_rock - 0.3, self.t_rock - 0.05))
            if hold > 0:
                band = Image.new("RGBA", (SH.W, 360), AMBER + (int(235 * hold),)); y0 = int(980 + 400 * (1 - E.out_expo(u))); ui.alpha_composite(band, (0, y0))
                for i, txt in enumerate(("SAND FROM", "THE SEAFLOOR.")):
                    tile, _, _ = SH.word_tile(txt, 96, "black", INK); SH.place(ui, tile, SH.W / 2, y0 + 115 + i * 120, 1.0, hold, 0, record=txt if u > 0.95 else None, px=96, color=INK, shadow=0)
            s = SH.slam(t, self.t_rock - 0.02, 0.28, 1.7)
            if s:
                out = 1 - E.smooth(E.seg(t, self.t_iss - 0.3, self.t_iss - 0.05)); tile, _, _ = SH.word_tile("RINGED BY", 96, "black", WHITE)
                y0 = int(960 + 420 * (1 - E.out_expo(E.seg(t, self.t_rock - 0.02, self.t_rock + 0.3))))
                ui.alpha_composite(Image.new("RGBA", (SH.W, 360), INK + (int(200 * out),)), (0, y0 - 20))
                SH.place(ui, tile, SH.W / 2, y0 + 80, s[0], s[1] * out, s[2], record="RINGED BY", px=96)
                SH.place(ui, SH.extrude("ROCK.", 170, 14, AMBER, (130, 92, 30)), SH.W / 2, y0 + 230, s[0], s[1] * out, s[2], record="ROCK.", px=170, color=AMBER)
        if iss:
            s = slam0(t, self.t_iss, 0.3, 1.6); SH.place(ui, SH.extrude("2022.", 170, 14, AMBER, (130, 92, 30)), SH.W / 2, 560, s[0], s[1], s[2], record="2022.", px=170, color=AMBER)
            s = SH.slam(t, self.t_iss + 0.35, 0.3, 1.4)
            if s: tile, _, _ = SH.word_tile("SEEN FROM THE ISS", 76, "black", WHITE); SH.place(ui, tile, SH.W / 2, 1180, s[0], s[1], s[2], record="SEEN FROM THE ISS", px=76)


# ===================================================================== EP003 common
class GSLBase(Short):
    YEARS = [("1985", "JUNE 1985", "LANDSAT 5"), ("1986", "AUG 1986", "LANDSAT 5"), ("1999", "AUG 1999", "LANDSAT 5"), ("2021", "JULY 2021", "LANDSAT 8"), ("2022", "JULY 2022", "LANDSAT 8, 9")]

    def __init__(self):
        super().__init__(); g = os.path.join(SRC, "gsl")
        self.grid = json.load(open(os.path.join(g, "grid.json"))); self.geo = Geo(self.grid, (SH.W, SH.H))
        self.img = {y: SH.ImageView(os.path.join(g, f"y{y}.png")) for y, _, _ in self.YEARS}
        geo_dir = os.path.join(ROOT, "productions", "ep003-great-salt-lake", "assets", "geo")
        self.m86 = Image.open(os.path.join(geo_dir, "water_y1986.png")).convert("L"); self.m22 = Image.open(os.path.join(geo_dir, "water_y2022.png")).convert("L")

    def mask_view(self, m, cx, cy, w, norm=False):
        key = id(m); cache = self.__dict__.setdefault("_mv", {})
        if key not in cache: cache[key] = SH.ImageView(m.convert("RGB"))
        return cache[key].view(cx, cy, w, norm=norm).convert("L")

    def outline(self, m_view, color, width=7):
        e = m_view.filter(ImageFilter.MaxFilter(width | 1)); d = ImageChops.subtract(e, m_view); a = d.point(lambda v: 255 if v > 100 else 0).filter(ImageFilter.GaussianBlur(1.2))
        lay = Image.new("RGBA", m_view.size, color + (0,)); lay.putalpha(a); return lay


# ===================================================================== EP003 S1
class GSL1(GSLBase):
    """20 FEET. - Aug 1986 (record-high year) -> light wipe to July 2022 with the 1986 shoreline traced; year flip; loops to 1986."""
    name = "EP003_GreatSaltLake_Short_01"
    WIDE = (2150.0, 1450.0, 1150.0)

    def __init__(self):
        super().__init__(); self.vw = words("ep003.voice.json", 14.58, 21.95, 0.35); self.voice = [(os.path.join(SRC, "audio", "ep003.flac"), 14.58, 21.95, 0.35)]
        self.t_record = wt(self.vw, "record"); self.t_1986 = wt(self.vw, "1986"); self.t_num = wt(self.vw, "4,211.6"); self.t_now = wt(self.vw, "Now"); self.t_20 = wt(self.vw, "20")
        self.t_wipe = self.t_now - 0.1; self.flip0 = 8.6
        self.flip = [(self.flip0 + i * 2 * BEAT, y) for i, y in enumerate(("1985", "1986", "1999", "2021", "2022"))]
        self.cues = [dict(t=0.02, kind="impact"), dict(t=self.t_1986, kind="tick"), dict(t=self.t_num, kind="impact"), dict(t=self.t_wipe - 0.2, kind="sweep"),
                     dict(t=self.t_20, kind="impact")] + [dict(t=a, kind="tick") for a, _ in self.flip] + [dict(t=14.2, kind="sweep")]
        self.accents = [self.t_num, self.t_20, self.flip0]

    def year_at(self, t):
        if t < self.t_wipe: return "1986"
        if t < self.flip0: return "2022"
        y = "1985"
        for a, yy in self.flip:
            if t >= a: y = yy
        return "1986" if t >= 14.25 else y

    def view(self, t):
        cx, cy, w = self.WIDE
        if t < 3.0: return (cx, cy, w * (1.12 - 0.12 * E.out_cubic(t / 3.0)))
        if t < self.t_wipe: return (cx + 120 * E.smooth(E.seg(t, 3.0, self.t_wipe)), cy + 80 * E.smooth(E.seg(t, 3.0, self.t_wipe)), w * (1 - 0.15 * E.smooth(E.seg(t, 3.0, self.t_wipe))))
        if t < self.flip0: return (cx + 120, cy + 80, w * 0.85 * (1 + 0.1 * E.smooth(E.seg(t, self.t_wipe, self.flip0))))
        if t < 14.25: return (cx + 120 * (1 - E.smooth(E.seg(t, self.flip0, 14.25))), cy + 80 * (1 - E.smooth(E.seg(t, self.flip0, 14.25))), w * (0.935 + 0.185 * E.smooth(E.seg(t, self.flip0, 14.25))))
        return (cx, cy, w * 1.12)

    def render(self, t):
        cx, cy, w = self.view(t); ui = Image.new("RGBA", self.size, (0, 0, 0, 0))
        yr = self.year_at(t); img = self.img[yr].view(cx, cy, w, norm=False)
        if self.t_wipe <= t < self.t_wipe + 1.1:                                          # light wipe 1986 -> 2022 (same grid: an honest comparison)
            u = E.in_out_cubic(E.seg(t, self.t_wipe, self.t_wipe + 1.0)); a = self.img["1986"].view(cx, cy, w, norm=False); b = self.img["2022"].view(cx, cy, w, norm=False)
            yy = int(SH.H * u); out = a.copy(); out.paste(b.crop((0, 0, SH.W, yy)), (0, 0)); g = ImageDraw.Draw(out); g.rectangle([0, yy - 3, SH.W, yy + 3], fill=(255, 232, 190))
            img = out
        if t >= self.t_wipe + 0.6 and t < 14.25:                                         # 1986 shoreline traced in amber over later years
            a = E.smooth(E.seg(t, self.t_wipe + 0.6, self.t_wipe + 1.1)) * (1 - E.smooth(E.seg(t, 13.9, 14.25)))
            lay = self.outline(self.mask_view(self.m86, cx, cy, w), AMBER, 7); lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
            img = img.convert("RGBA"); img.alpha_composite(lay); img = img.convert("RGB")
        for a0, _ in self.flip:
            if 0 <= t - a0 < 2 / FPS: img = Image.blend(img, Image.new("RGB", self.size, (255, 246, 228)), 0.15)
        img = SH.vignette(img, 0.42); self.type(ui, t, yr)
        return self.finish(img, ui)

    def type(self, ui, t, yr):
        lab = {y: (l, s) for y, l, s in self.YEARS}[yr]
        SH.chip(ui, f"{lab[1]} · USGS · {lab[0]}", 60, 100, 30)
        if self.t_wipe + 0.6 <= t < 14.25: SH.chip(ui, "AMBER LINE: AUG 1986 SHORE, TRACED", 60, 152, 30, accent=AMBER)
        if t < self.t_wipe or t >= 14.6:
            out = 1 - E.smooth(E.seg(t, self.t_wipe - 0.3, self.t_wipe)) if t < 14.6 else E.smooth(E.seg(t, 14.6, 14.95))
            pulse = 1.0 + 0.05 * math.sin(math.pi * E.seg(t, self.t_record - 0.05, self.t_record + 0.3)) if t < 14.6 else 1.0   # on screen from frame 0 (hook + loop)
            tile, _, _ = SH.word_tile("RECORD HIGH", 110, "black", WHITE); SH.place(ui, tile, SH.W / 2, 470, pulse, out, 0, record="RECORD HIGH", px=110)
            if t >= self.t_1986 - 0.05 and t < 14.6: SH.Badge(SH.W / 2, 690, 108).draw(ui, "1986", 0.3 * math.sin(math.pi * E.seg(t, self.t_1986, self.t_1986 + 0.6)), 30 * t, 1.0, out, 60)
            s = SH.slam(t, self.t_num - 0.05, 0.32, 1.9) if t < 14.6 else None
            if s: SH.place(ui, SH.extrude("4,211.6 FT", 150, 16, AMBER, (130, 92, 30)), SH.W / 2, 1180, s[0], s[1] * out, s[2], record="4,211.6 FT", px=150, color=AMBER)
        if self.t_wipe <= t < self.flip0:
            out = 1 - E.smooth(E.seg(t, self.flip0 - 0.35, self.flip0 - 0.05))
            s = SH.slam(t, self.t_20 - 0.05, 0.35, 2.0)
            if s:
                drop = 60 * E.out_cubic(E.seg(t, self.t_20 + 0.3, self.t_20 + 1.2))
                SH.place(ui, SH.extrude("20+ FT", 212, 18, AMBER, (130, 92, 30)), SH.W / 2, 760 + drop, s[0], s[1] * out, s[2], record="20+ FT", px=212, color=AMBER)
                tile, _, _ = SH.word_tile("LOWER.", 150, "black", WHITE); SH.place(ui, tile, SH.W / 2, 1000 + drop * 1.5, s[0], s[1] * out, s[2], record="LOWER.", px=150)
            if t >= self.t_wipe + 0.4 and t < self.t_20 - 0.1:
                tile, _, _ = SH.word_tile("JULY 2022", 96, "black", WHITE); SH.place(ui, tile, SH.W / 2, 560, 1.0, E.smooth(E.seg(t, self.t_wipe + 0.4, self.t_wipe + 0.7)), 0, record="JULY 2022", px=96)
        if self.flip0 <= t < 14.25:
            b = SH.Badge(SH.W / 2, 1160, 118); a0 = max(a for a, y in self.flip if a <= t)
            b.draw(ui, yr, 0.3 * math.sin(math.pi * E.seg(t, a0, a0 + 0.35)), 35 * t, 1.0 + 0.1 * math.sin(math.pi * E.seg(t, a0, a0 + 0.35)), 1.0, 64)
            if yr == "2022" and t >= self.flip[-1][0]:
                s = slam0(t, self.flip[-1][0] + 0.05, 0.3, 1.5); SH.place(ui, SH.extrude("4,190.2 FT", 120, 12, WHITE, (90, 100, 115)), SH.W / 2, 940, s[0], s[1] * (1 - E.smooth(E.seg(t, 13.9, 14.2))), s[2], record="4,190.2 FT", px=120)


# ===================================================================== EP003 S2
class GSL2(GSLBase):
    """WHAT THE WATER LEFT BEHIND. - July 2022 close on the east shore; traced exposed bed (water in Aug 1986, dry in July 2022) revealed;
    USGS dust facts; tilted 2.5D map with an ILLUSTRATED (labelled) dust drift toward Salt Lake City; USGS caveat; loops to frame 0."""
    name = "EP003_GreatSaltLake_Short_02"
    TILT = 26.0

    def __init__(self):
        super().__init__(); flac = os.path.join(SRC, "audio", "ep003.flac")
        self.va = words("ep003.voice.json", 265.52, 268.58, 0.30); self.vb = words("ep003.voice.json", 277.36, 283.14, 7.55)
        self.voice = [(flac, 265.52, 268.58, 0.30), (flac, 277.36, 283.14, 7.55)]
        self.t_bed = wt(self.va, "lake"); self.t_back = wt(self.va, "back"); self.t_dust = wt(self.vb, "dust"); self.t_worse = wt(self.vb, "worsens")
        self.exposed = ImageChops.subtract(self.m86, self.m22).point(lambda v: 255 if v > 128 else 0)
        self.slc = self.geo.px((-111.891, 40.761)); self.t0 = 3.3
        self.cues = [dict(t=0.02, kind="impact"), dict(t=self.t_back, kind="sweep"), dict(t=self.t_bed, kind="impact"), dict(t=self.t0, kind="tick"), dict(t=self.t0 + 2 * BEAT, kind="impact")] + \
                    [dict(t=self.t0 + k * BEAT, kind="tick") for k in (4, 5, 6)] + [dict(t=self.t_dust - 0.3, kind="whoosh"), dict(t=self.t_worse, kind="impact"), dict(t=13.3, kind="impact"), dict(t=14.1, kind="sweep")]
        self.accents = [self.t_bed, self.t0 + 2 * BEAT, self.t_worse, 13.3]

    def view(self, t):
        a = (2470.0, 1720.0, 1050.0); b = (2560.0, 1820.0, 760.0); m = (2540.0, 1800.0, 700.0); c = (2650.0, 1950.0, 1250.0)
        if t < 3.6: return SH.lerp_view(a, b, E.out_cubic(t / 3.6))
        if t < 7.4: return SH.lerp_view(b, m, E.smooth(E.seg(t, 3.6, 7.4)))
        c2 = (2610.0, 1905.0, 1080.0)                                                     # slow push toward the city while the dust drifts
        if t < 9.0: return SH.lerp_view(m, c, E.in_out_cubic(E.seg(t, 7.4, 9.0)))
        if t < 14.0: return SH.lerp_view(c, c2, E.smooth(E.seg(t, 9.0, 14.0)))
        return SH.lerp_view(c2, a, E.in_out_cubic(E.seg(t, 14.0, 14.9)))

    def tilt_at(self, t): return self.TILT * E.smooth(E.seg(t, 7.4, 8.4)) * (1 - E.smooth(E.seg(t, 13.9, 14.7)))

    def render(self, t):
        cx, cy, w = self.view(t); ui = Image.new("RGBA", self.size, (0, 0, 0, 0)); deg = self.tilt_at(t)
        big = SH.big_size(deg); wb = w * big[0] / SH.W
        img = self.img["2022"].view(cx, cy, wb, size=big, norm=False).convert("RGBA")
        reveal = E.in_out_cubic(E.seg(t, self.t_back - 0.1, self.t_bed + 0.3)) * (1 - E.smooth(E.seg(t, 13.6, 14.3)))
        if reveal > 0:                                                                   # traced exposed bed: water in Aug 1986, not water in July 2022
            m = self._mask(cx, cy, wb, big)
            grad = Image.linear_gradient("L").resize(big).transpose(Image.FLIP_TOP_BOTTOM)
            gate = grad.point(lambda v, r=reveal: 255 if v / 255.0 < r * 1.15 else 0); m = ImageChops.multiply(m, gate)
            fill = Image.new("RGBA", big, AMBER + (0,)); fill.putalpha(m.point(lambda v: int(v * 0.30))); img.alpha_composite(fill)
            img.alpha_composite(self.outline(m, AMBER, 5))
        rgb, fwd = SH.cover_tilt(img.convert("RGB"), deg, bg=(8, 12, 18))
        img = SH.vignette(rgb, 0.42).convert("RGBA")
        sx, sy = fwd(*self.img["2022"].to_screen(self.slc, cx, cy, wb, size=big, norm=False))
        if self.t_dust - 0.4 <= t < 13.4:                                                  # ILLUSTRATION: dust drifting east toward the city (labelled on screen)
            a = E.smooth(E.seg(t, self.t_dust - 0.4, self.t_dust + 0.4)) * (1 - E.smooth(E.seg(t, 12.9, 13.4)))
            lay = Image.new("RGBA", self.size, (0, 0, 0, 0)); x1 = int(min(sx, 900))
            SH.dust(lay, t, 260, 5, (236, 214, 176), 0.55 * a, drift=(55, -16), area=(80, 700, x1, 1500), size=4.0)
            SH.dust(lay, t * 1.4, 90, 9, (255, 236, 200), 0.75 * a, drift=(80, -26), area=(120, 800, x1, 1400), size=6.5); img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0.8)))
        self.type(ui, t, (sx, sy), deg)
        return self.finish(img, ui)

    def _mask(self, cx, cy, wb, big):
        key = "_mexp"
        if key not in self.__dict__: self.__dict__[key] = SH.ImageView(self.exposed.convert("RGB"))
        return self.__dict__[key].view(cx, cy, wb, size=big, norm=False).convert("L")

    def type(self, ui, t, slc, deg):
        SH.chip(ui, "JULY 2022 · LANDSAT 8, 9 · USGS", 60, 100, 30)
        if self.t_back <= t < 13.6: SH.chip(ui, "AMBER: LAKE IN 1986, DRY IN 2022 (TRACED)", 60, 152, 30, accent=AMBER)
        if self.t_dust - 0.4 <= t < 13.4: SH.chip(ui, "DUST: ILLUSTRATION, NOT A MEASURED PLUME", 60, 204, 30, accent=CYAN)
        # title: on screen from frame 0 and fading back in at the end (loop)
        if t < self.t_bed - 0.1 or t >= 14.45:
            out = 1 - E.smooth(E.seg(t, self.t_bed - 0.35, self.t_bed - 0.1)) if t < 14.45 else E.smooth(E.seg(t, 14.45, 14.9))
            tile, _, _ = SH.word_tile("WHAT THE WATER", 86, "black", WHITE); SH.place(ui, tile, SH.W / 2, 520, 1.0, out, 0, record="WHAT THE WATER", px=86)
            tile, _, _ = SH.word_tile("LEFT BEHIND", 110, "black", AMBER); SH.place(ui, tile, SH.W / 2, 645, 1.0, out, 0, record="LEFT BEHIND", px=110, color=AMBER)
        if t < self.t0 + 0.05:
            s = SH.slam(t, self.t_bed - 0.05, 0.3, 1.9)
            if s: SH.place(ui, SH.extrude("LAKE BED.", 148, 14, AMBER, (130, 92, 30)), SH.W / 2, 1150, s[0], s[1] * (1 - E.smooth(E.seg(t, self.t0 - 0.25, self.t0))), s[2], record="LAKE BED.", px=148, color=AMBER)
        t0 = self.t0
        if t0 <= t < 7.45:                                                               # USGS facts (C15), one beat each
            out = 1 - E.smooth(E.seg(t, 7.15, 7.45))
            s = slam0(t, t0, 0.3, 1.6); tile, _, _ = SH.word_tile("USGS SAMPLED DUST AT", 64, "black", WHITE); SH.place(ui, tile, SH.W / 2, 430, s[0], s[1] * out, s[2], record="USGS SAMPLED DUST AT", px=64)
            s = SH.slam(t, t0 + 2 * BEAT, 0.3, 1.9)
            if s: SH.place(ui, SH.extrude("17 SITES", 170, 14, AMBER, (130, 92, 30)), SH.W / 2, 600, s[0], s[1] * out, s[2], record="17 SITES", px=170, color=AMBER)
            for i, (sym, nm) in enumerate((("As", "ARSENIC"), ("Pb", "LEAD"), ("Cd", "CADMIUM"))):
                s = SH.slam(t, t0 + (4 + i) * BEAT, 0.25, 1.6)
                if not s: continue
                x = 260 + i * 280; tile = Image.new("RGBA", (220, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(tile)
                d.rounded_rectangle([6, 6, 214, 214], radius=24, fill=(12, 16, 22, 230), outline=CYAN + (255,), width=6)
                st, _, _ = SH.word_tile(sym, 96, "black", CYAN); tile.alpha_composite(st, (110 - st.width // 2, 110 - st.height // 2 - 22)); nt, _, _ = SH.word_tile(nm, 32, "black", WHITE)
                tile.alpha_composite(nt, (110 - nt.width // 2, 168 - nt.height // 2)); SH.place(ui, tile, x, 900, s[0], s[1] * out, s[2], record=nm, px=32)
            s = SH.slam(t, t0 + 7 * BEAT, 0.3, 1.3)
            if s: tile, _, _ = SH.word_tile("FOUND IN THE DUST", 70, "black", WHITE); SH.place(ui, tile, SH.W / 2, 1110, s[0], s[1] * out, s[2], record="FOUND IN THE DUST", px=70)
        if 7.5 <= t < 13.3:
            out = 1 - E.smooth(E.seg(t, 13.0, 13.3))
            s = SH.slam(t, self.t_dust - 0.06, 0.3, 1.5)
            if s: tile, _, _ = SH.word_tile("THE DUST", 130, "black", WHITE); SH.place(ui, tile, SH.W / 2, 420, s[0], s[1] * out, s[2], record="THE DUST", px=130)
            s = SH.slam(t, self.t_worse - 0.06, 0.3, 1.7)
            if s:
                tile, _, _ = SH.word_tile("WORSENS", 96, "black", WHITE); SH.place(ui, tile, SH.W / 2, 560, s[0], s[1] * out, s[2], record="WORSENS", px=96)
                SH.place(ui, SH.extrude("AIR POLLUTION", 104, 12, AMBER, (130, 92, 30)), SH.W / 2, 690, s[0], s[1] * out, s[2], record="AIR POLLUTION", px=104, color=AMBER)
            pin_a = E.smooth(E.seg(t, 9.0, 9.4)) * (1 - E.smooth(E.seg(t, 12.9, 13.2)))
            x, y = slc
            if pin_a > 0 and 120 < x < 960 and 300 < y < 1500:                           # Salt Lake City, projected through the same tilt
                d = ImageDraw.Draw(ui); d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=WHITE + (int(255 * pin_a),), outline=INK + (int(255 * pin_a),), width=4)
                tile, _, _ = SH.word_tile("SALT LAKE CITY", 56, "black", WHITE); lx = min(max(x, 90 + tile.width / 2), 930 - tile.width / 2)
                SH.place(ui, tile, lx, y - 60, 1.0, pin_a, 0, record="SALT LAKE CITY", px=56)
        if 13.3 <= t < 14.5:
            u = E.seg(t, 13.3, 13.6); out = 1 - E.smooth(E.seg(t, 14.25, 14.5)); y0 = int(820 + 300 * (1 - E.out_expo(u)))
            ui.alpha_composite(Image.new("RGBA", (SH.W, 300), AMBER + (int(240 * out),)), (0, y0))
            for i, txt in enumerate(("HEALTH EFFECTS:", "NOT YET FORMALLY", "EVALUATED (USGS)")):
                tile, _, _ = SH.word_tile(txt, 70, "black", INK); SH.place(ui, tile, SH.W / 2, y0 + 70 + i * 80, 1.0, out, 0, record=txt, px=70, color=INK, shadow=0)


SHORTS = dict(dubai1=Dubai1, dubai2=Dubai2, gsl1=GSL1, gsl2=GSL2)


def audio(short, path):
    sc = music.score(DUR, BPM, accents=short.accents, drops=getattr(short, "drops", ()), risers=[a for a in short.accents[1:2]])
    return music.mix_short(path, DUR, sc, voice=short.voice, cues=short.cues)


if __name__ == "__main__":
    cmd, name = sys.argv[1], sys.argv[2]; sh = SHORTS[name]()
    if cmd == "stills":
        out = sys.argv[3]; os.makedirs(out, exist_ok=True)
        for t in [float(x) for x in sys.argv[4:]]: sh.render(t).save(os.path.join(out, f"{name}_t{t:05.2f}.png"))
    elif cmd == "render":
        out = sys.argv[3]; workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
        wav = out + ".wav"; rep = audio(sh, wav); json.dump(rep, open(out + ".audio.json", "w"), indent=1)
        print("frames", SQ.render_video(sh, out, FPS, workers, audio=wav))
