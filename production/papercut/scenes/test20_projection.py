#!/usr/bin/env python3
"""20 s test v4: the approved paper ATLAS (no joints) with a PROJECTION of small topic details.

ATLAS stays the approved drawing (hero_approved_clean.png): whole-cutout idle motion only, blink and mouth
inside the one head. From his raised open glove a paper-style projection opens and shows small details of
the current beat (radio link, blocked path, dark Moon, impact animation, rare view), so the viewer watches him.
On-screen text = short object-anchored callouts + projection tags only; full subtitles in a separate SRT.
Voice: existing EP014 Adam narration. Footage: NASA Artemis II (labelled). No unconfirmed facts or numbers.

  python3 -I scenes/test20_projection.py --media /mnt/project-files --out t.mp4 --log log.json --srt t.srt
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
from papercut.actor import Actor, ActorCue  # noqa: E402
import test20 as T20  # noqa: E402

W, H, FPS, DUR = 1920, 1080, 30, 20.0
N = int(DUR * FPS)
FEET = (250.0, 985.0)
HERO_H = 400
SHIFT = 160          # map drawn 160 px further right than test 2, to make room for the projection
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
        cx = self.OX + W / 2 - SHIFT + 6 * math.sin(t * 0.35)
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


# ------------------------------------------------------------------ ATLAS (approved drawing, no joints)
HAND_IN_HERO = (452.0, 318.0)         # open raised glove (palm centre) in hero_approved_clean.png px (518x733)
BLINKS = [2.9, 5.9, 8.3, 10.9, 13.4, 17.6, 19.3]


def actor_cues():
    talk = [(at, at + (e - s)) for s, e, at, _ in VOICE]
    return [ActorCue(0.0, DUR, "hero", *FEET, HERO_H, "idle", talk=talk, blinks=BLINKS, pop=False, name="hero")]


def hand_point(st):
    """Screen position of the raised glove for the current whole-cutout state (same affine as the actor)."""
    s, r = st["scale"], math.radians(st["roll_deg"])
    k = HERO_H / 733.0
    du, dv = (HAND_IN_HERO[0] - 518 / 2) * k, (HAND_IN_HERO[1] - 733) * k
    return st["x"] + s * (math.cos(r) * du - math.sin(r) * dv), st["y"] + s * (math.sin(r) * du + math.cos(r) * dv)


def quantize_mouth(env, hold=2):
    lv = np.where(env > 0.45, 0.8, np.where(env > 0.15, 0.3, 0.0))
    out = lv.copy(); i = 0
    while i < len(out):
        j = i
        while j < len(out) and lv[j] == lv[i]:
            j += 1
        if j - i < hold and i > 0:
            out[i:j] = out[i - 1]
        i = j
    return out


# ------------------------------------------------------------------ projection
PANEL = (330, 318, 680, 578)          # x0, y0, x1, y1 on screen: above-right of the glove, clear of the face and EARTH
PAGES = [  # (t0, tag, kind) - every tag repeats what the narration says or what the footage label says
    (0.55, "EARTH TO ORION", "link"),
    (6.35, "NO DIRECT PATH", "blocked"),
    (11.35, "DARK MOON", "dark"),
    (14.50, "NASA ANIMATION", "flash"),
    (16.45, "RARE VIEW", "view"),
]
PAGE_TIMES = [p[0] for p in PAGES]
PROJ = (178, 226, 236)                 # pale projection cyan, kept in the paper palette family
PROJ_INK = (24, 52, 72)


class Projection:
    def __init__(self):
        self.tagf = ImageFont.truetype(str(FONT), 26)
        x0, y0, x1, y1 = PANEL
        self.w, self.h = x1 - x0, y1 - y0
        g = P.grain(self.w, self.h, 17, 0.06)[..., None]
        base = np.clip(np.array(PROJ, np.float32)[None, None, :] * g, 0, 255).astype(np.uint8)
        lines = np.ones((self.h, self.w, 1), np.float32)
        lines[::4] = 0.965                                   # faint static scan lines (no flicker)
        base = np.clip(base * lines, 0, 255).astype(np.uint8)
        k = 3
        m = Image.new("L", (self.w * k, self.h * k), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, self.w * k - 1, self.h * k - 1), radius=16 * k, fill=255)
        self.mask = m.resize((self.w, self.h), Image.Resampling.LANCZOS)
        self.bg = Image.fromarray(np.dstack([base, np.asarray(self.mask)]), "RGBA")
        d = ImageDraw.Draw(self.bg)
        d.rounded_rectangle((3, 3, self.w - 4, self.h - 4), radius=14, outline=(*P.CREAM, 255), width=3)
        for cx, cy, sx, sy in ((14, 14, 1, 1), (self.w - 14, 14, -1, 1), (14, self.h - 14, 1, -1), (self.w - 14, self.h - 14, -1, -1)):
            d.line((cx, cy, cx + 18 * sx, cy), fill=(*P.ORANGE, 255), width=4)
            d.line((cx, cy, cx, cy + 18 * sy), fill=(*P.ORANGE, 255), width=4)

    # -- small paper diagrams, drawn into the panel (local px), animated by u = seconds into the page
    def _content(self, kind, tag, u):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        tw = d.textlength(tag, font=self.tagf)
        d.text(((self.w - tw) / 2, 22), tag, font=self.tagf, fill=(*PROJ_INK, 255))
        cy = 150
        ink = (*PROJ_INK, 255)

        def disc(x, y, r, fill, outline=ink, w=4):
            d.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=outline, width=w)

        def earth(x, y, r):
            disc(x, y, r, (70, 120, 190, 255))
            d.polygon([(x - r * .5, y - r * .4), (x - r * .1, y - r * .65), (x + r * .15, y - r * .2), (x - r * .35, y + r * .05)], fill=(120, 165, 100, 255))
            d.polygon([(x + r * .15, y + r * .1), (x + r * .55, y - r * .05), (x + r * .45, y + r * .5), (x + r * .1, y + r * .45)], fill=(120, 165, 100, 255))

        def moon(x, y, r, lit=True):
            disc(x, y, r, (205, 200, 190, 255) if lit else (52, 56, 66, 255))
            for ox, oy, rr in ((-.35, -.25, .2), (.3, .2, .15), (-.05, .45, .1)):
                d.ellipse((x + ox * r - rr * r, y + oy * r - rr * r, x + ox * r + rr * r, y + oy * r + rr * r),
                          fill=(170, 165, 158, 255) if lit else (44, 48, 57, 255))

        def capsule(x, y, s=1.0, flip=False):
            sg = -1 if flip else 1
            pts = [(x - 20 * s * sg, y - 14 * s), (x + 14 * s * sg, y - 8 * s), (x + 14 * s * sg, y + 8 * s), (x - 20 * s * sg, y + 14 * s)]
            d.polygon(pts, fill=(*P.CREAM, 255), outline=ink, width=3)
            d.rectangle((min(x + 14 * s * sg, x + 22 * s * sg), y - 6 * s, max(x + 14 * s * sg, x + 22 * s * sg), y + 6 * s), fill=(*P.ORANGE, 255), outline=ink, width=2)

        if kind == "link":
            earth(70, cy, 42); capsule(self.w - 70, cy - 10, 1.2, flip=True)
            for j in range(3):                                # waves travelling Earth -> Orion
                f = (u * 0.8 + j / 3) % 1
                x = 120 + f * (self.w - 230)
                d.arc((x - 16, cy - 26, x + 16, cy + 6), 300, 60, fill=(*P.ORANGE, 255), width=4)
            for x in range(122, self.w - 104, 16):
                d.line((x, cy - 10, x + 7, cy - 10), fill=ink, width=3)
        elif kind == "blocked":
            earth(55, cy, 32); moon(self.w / 2 + 30, cy, 46); capsule(self.w - 45, cy, 1.0, flip=True)
            stop = self.w / 2 + 30 - 46
            grow = min(1.0, u / 0.6)
            for x in range(90, int(90 + (stop - 92) * grow), 16):
                d.line((x, cy, x + 7, cy), fill=(200, 60, 45, 255), width=4)
            if u > 0.6:
                xx, r = stop - 4, 11
                d.line((xx - r, cy - r, xx + r, cy + r), fill=(200, 60, 45, 255), width=5)
                d.line((xx - r, cy + r, xx + r, cy - r), fill=(200, 60, 45, 255), width=5)
        elif kind == "dark":
            moon(self.w / 2, cy + 6, 70, lit=False)
            d.arc((self.w / 2 - 70, cy - 64, self.w / 2 + 70, cy + 76), 250, 330, fill=(*P.CREAM, 255), width=5)
        elif kind == "flash":
            moon(self.w / 2, cy + 6, 66)
            fx, fy = self.w / 2 + 16, cy - 8
            p = 0.5 + 0.5 * math.sin(min(u, 1.4) * 6)          # a few pulses, then it settles
            rr = 10 + 10 * p if u < 1.4 else 12
            for a in range(0, 360, 45):
                ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
                d.line((fx + ca * 6, fy + sa * 6, fx + ca * rr * 1.6, fy + sa * rr * 1.6), fill=(255, 240, 160, 255), width=4)
            d.ellipse((fx - 6, fy - 6, fx + 6, fy + 6), fill=(255, 250, 220, 255))
        elif kind == "view":
            moon(self.w - 100, cy + 4, 58, lit=False)
            d.arc((self.w - 158, cy - 54, self.w - 42, cy + 62), 250, 320, fill=(*P.CREAM, 255), width=4)
            capsule(85, cy + 10, 1.8)
            d.ellipse((85 - 4, cy + 4, 85 + 8, cy + 16), fill=(90, 150, 200, 255), outline=ink, width=2)   # window
            for k2 in range(3):
                x = 140 + k2 * 22
                d.line((x, cy + 6, x + 10, cy + 6), fill=ink, width=3)
        return im

    def draw(self, frame, t, hand):
        if t < PAGES[0][0]:
            return None
        u_open = ease_out_back((t - PAGES[0][0]) / 0.45)
        a_open = ease_out((t - PAGES[0][0]) / 0.3)
        x0, y0, x1, y1 = PANEL
        # projection beam: two soft cream wedges from the glove to the panel's lower edge (static, no flicker)
        beam = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        bd = ImageDraw.Draw(beam)
        hx, hy = hand
        bx0 = hx + (x0 + 40 - hx) * u_open; bx1 = hx + (x1 - 40 - hx) * u_open; by = hy + (y1 - hy) * u_open
        bd.polygon([(hx - 6, hy), (hx + 6, hy), (bx1, by), (bx0, by)], fill=(*PROJ, int(70 * a_open)))
        beam = beam.filter(ImageFilter.GaussianBlur(3))
        frame.alpha_composite(beam)
        # panel grows out of the glove
        sc = max(0.05, min(1.06, u_open))
        w, h = round(self.w * sc), round(self.h * sc)
        cx = hx + ((x0 + x1) / 2 - hx) * min(1, u_open); cy = hy + ((y0 + y1) / 2 - hy) * min(1, u_open)
        page = max(i for i, p in enumerate(PAGES) if p[0] <= t)
        t0, tag, kind = PAGES[page]
        panel = self.bg.copy()
        u = t - t0
        cur = self._content(kind, tag, u)
        if page > 0 and u < 0.35:                          # page change: old slides up and fades, new slides in
            v = ease_out(u / 0.35)
            pt0, ptag, pkind = PAGES[page - 1]
            old = self._content(pkind, ptag, t - pt0)
            old.putalpha(old.getchannel("A").point(lambda q: int(q * (1 - v))))
            panel.alpha_composite(old, (0, int(-24 * v)) if v < 1 else (0, 0))
            cur.putalpha(cur.getchannel("A").point(lambda q: int(q * v)))
            panel.alpha_composite(cur, (0, int(24 * (1 - v))))
        else:
            panel.alpha_composite(cur)
        panel.putalpha(Image.fromarray(np.minimum(np.asarray(panel.getchannel("A")), np.asarray(self.mask))))
        if (w, h) != panel.size:
            panel = panel.resize((max(1, w), max(1, h)), Image.Resampling.LANCZOS)
        al = 0.93 * a_open
        panel.putalpha(panel.getchannel("A").point(lambda q: int(q * al)))
        sh = Image.new("RGBA", (panel.width + 40, panel.height + 40), (0, 0, 0, 0))
        sa = Image.new("L", sh.size, 0); sa.paste(panel.getchannel("A"), (20, 20))
        sh.putalpha(sa.filter(ImageFilter.GaussianBlur(7)).point(lambda q: int(q * 0.3)))
        frame.alpha_composite(sh, (int(cx - panel.width / 2 - 20 + 5), int(cy - panel.height / 2 - 20 + 8)))
        frame.alpha_composite(panel, (int(round(cx - panel.width / 2)), int(round(cy - panel.height / 2))))
        return {"page": tag, "box": [int(cx - panel.width / 2), int(cy - panel.height / 2), int(cx + panel.width / 2), int(cy + panel.height / 2)]}


def rects_hit(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def rect_circle(a, c):
    cx, cy, r = c
    nx, ny = min(max(cx, a[0]), a[2]), min(max(cy, a[1]), a[3])
    return math.hypot(nx - cx, ny - cy) < r


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
    t = np.arange(int(0.25 * sr)) / sr              # soft rising tone when the projection opens / changes page
    chirp = np.sin(2 * np.pi * (500 + 900 * t / 0.25) * t) * np.hanning(len(t)) * 0.035
    for k in PAGE_TIMES:
        i = int(k * sr); sfx[i:i + len(chirp)] += chirp
    mix = np.clip(voice + sfx, -1, 1)[: int(DUR * sr)]
    out = tmp / "mix.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    hop = sr // FPS
    env = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(N)])
    env = env / (np.percentile(env[env > 1e-4], 90) + 1e-9)
    env = np.convolve(env, [0.25, 0.5, 0.25], mode="same")
    return out, env


def write_srt(path: Path):
    def ts(x):
        ms = int(round(x * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    lines = []
    for i, (s, e, at, text) in enumerate(VOICE, 1):
        lines += [str(i), f"{ts(at)} --> {ts(at + e - s)}", text, ""]
    path.write_text("\n".join(lines), encoding="utf-8")


# ------------------------------------------------------------------ main
HEAD_IN_HERO = (40, 60, 400, 400)       # helmet + face box in hero px: text and projection must stay off it


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--media", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--srt", type=Path)
    ap.add_argument("--frames", type=str, help="comma list of times: PNG stills only")
    a = ap.parse_args()
    mp = Map()
    co = Callouts()
    proj = Projection()
    if a.srt:
        write_srt(a.srt)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        mix, env = build_audio(a.media, tmp)
        mouth = quantize_mouth(env)
        actor = Actor((W, H), actor_cues(), envelope=lambda tt: float(mouth[min(N - 1, int(round(tt * FPS)))]))
        scope = T20.Scope(a.media, tmp)
        times = [float(x) for x in a.frames.split(",")] if a.frames else None
        proc = None
        if not times:
            proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                     "-r", str(FPS), "-i", "-", "-i", str(mix), "-c:v", "libx264", "-preset", "medium",
                                     "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "160k",
                                     "-movflags", "+faststart", "-shortest", str(a.out)], stdin=subprocess.PIPE)
        log, issues, frozen = [], [], {}
        k = HERO_H / 733.0
        for i, t in enumerate(times or [i / FPS for i in range(N)]):
            fr, minfo, geo = mp.frame(t)
            scope_label = scope.draw(fr, t, None)
            cue, st = actor.state(t)
            hand = hand_point(st)
            pj = proj.draw(fr, t, hand)
            info = actor.render(fr, t)
            head = [st["x"] + (HEAD_IN_HERO[0] - 259) * k, st["y"] + (HEAD_IN_HERO[1] - 733) * k,
                    st["x"] + (HEAD_IN_HERO[2] - 259) * k, st["y"] + (HEAD_IN_HERO[3] - 733) * k]
            anc = anchors(geo, T20.Scope.C, T20.Scope.R)
            cards = {}
            for text, t0, t1, key, off in CALLOUTS:
                an, card = anc[key]
                if an is None:
                    continue
                if card is None:
                    if text not in frozen:
                        frozen[text] = (an[0] + off[0], an[1] + off[1])
                    card = frozen[text]
                b = co.draw(fr, text, an, card, t, t0, t1)
                if b:
                    cards[text] = b
            # placement checks on every frame
            boxes = dict(cards)
            if pj and t >= PAGES[0][0] + 0.45:
                boxes["PROJECTION"] = pj["box"]
            for name, b in boxes.items():
                if b[0] < 24 or b[1] < 24 or b[2] > W - 24 or b[3] > H - 24:
                    issues.append((i, name, "frame edge"))
                if rects_hit(b, head):
                    issues.append((i, name, "face/helmet"))
                for nm in ("earth", "moon"):
                    if rect_circle(b, geo[nm]):
                        issues.append((i, name, nm))
                if scope_label and rect_circle(b, (T20.Scope.C[0], T20.Scope.C[1], T20.Scope.R + 12)):
                    issues.append((i, name, "telescope window"))
                for n2, b2 in boxes.items():
                    if n2 > name and rects_hit(b, b2):
                        issues.append((i, name, "overlaps " + n2))
            if times:
                fr.convert("RGB").save(a.out.parent / f"still_{t:05.2f}.png")
            else:
                proc.stdin.write(fr.convert("RGB").tobytes())
            log.append({"frame": i, "t": round(t, 4), "actor": info, "hand": [round(hand[0], 2), round(hand[1], 2)],
                        "head_box": [round(v, 1) for v in head], "projection": pj, "cards": cards, "scope": scope_label,
                        "map": minfo, "mouth": float(mouth[min(N - 1, int(round(t * FPS)))])})
        if proc:
            proc.stdin.close()
            if proc.wait():
                raise SystemExit("ffmpeg failed")
    a.log.write_text(json.dumps({"fps": FPS, "size": [W, H], "frames": N, "voice": VOICE, "pages": PAGES,
                                 "callouts": CALLOUTS, "placement_issues": issues, "log": log},
                                default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o)))
    print("placement issues:", len(issues), issues[:8])
    print("done")


if __name__ == "__main__":
    main()
