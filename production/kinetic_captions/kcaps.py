"""Kinetic motion-graphics captions for Orbital Atlas (word-timed, keyword boxes, hero numbers, HUD).

Look: heavy wide uppercase (Unbounded 900, OFL), words pop in on their spoken time, key words get an
accent box that wipes in behind them, big numbers count up in a slammed box, thin HUD frame with a
countdown ring. Timing comes from the yt-voice word timings, so captions always match the voice.

    caps = Captions(words, keywords={"FIVE", "PINPRICKS"}, heroes=[Hero(...)], style=Style())
    caps.render(frame_rgba, t)          # after footage / graphics, last layer
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIR = Path(__file__).resolve().parent / "fonts"
MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"


@dataclass
class Style:
    accent: tuple = (255, 210, 31)        # Orbital Atlas yellow (thumbnail standard). Lime alt: (198, 255, 0)
    text: tuple = (255, 255, 255)
    ink: tuple = (12, 12, 14)
    size: int = 58
    y: int = 880                           # baseline centre of the caption line
    max_chars: int = 24                    # per phrase
    max_width: int = 1560
    hud: bool = True
    channel_tag: str = "ORBITAL ATLAS"


@dataclass
class Hero:
    """A big moment that replaces the caption line: e.g. a count-up number."""
    t0: float
    t1: float
    big: str                               # "46,000" (digits count up) or a word
    above: str = ""
    below: str = ""
    count_up: bool = True


def ease_out_back(u, s=1.7):
    u = min(1.0, max(0.0, u)) - 1
    return 1 + u * u * ((s + 1) * u + s)


def ease_out(u):
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


def font(weight=900, size=58):
    return ImageFont.truetype(str(FONT_DIR / f"unbounded-latin-{weight}-normal.woff"), size)


@dataclass
class Word:
    text: str
    start: float
    end: float
    key: bool = False


class Captions:
    def __init__(self, words: list, keywords=(), heroes=(), replace=None, style: Style | None = None, duration=None):
        self.st = style or Style()
        self.heroes = list(heroes)
        replace = replace or {}
        ws = []
        for w in words:
            raw = w["text"]
            if any(h.t0 - 0.02 <= w["start"] < h.t1 for h in self.heroes):
                continue                   # spoken inside a hero moment: shown by the hero instead
            txt = replace.get(raw, raw).upper()
            core = re.sub(r"[^\w'’-]", "", txt)
            ws.append(Word(txt, w["start"], w["end"], core in {k.upper() for k in keywords}))
        self.phrases = self._phrases(ws)
        self.duration = duration or (max(w["end"] for w in words) + 0.5)
        self.f = font(900, self.st.size)
        self._glyph = {}

    # -------------------------------------------------------------- layout
    def _phrases(self, ws):
        out, cur = [], []
        for w in ws:
            n = sum(len(x.text) + 1 for x in cur) + len(w.text)
            gap = cur and w.start - cur[-1].end > 0.45
            glue = re.fullmatch(r"[IVX]+[.,!?]?", w.text) is not None      # keep "ARTEMIS II" together
            if cur and (n > self.st.max_chars or gap) and not glue:
                out.append(cur); cur = []
            cur.append(w)
            if re.search(r"[.!?]$", w.text):
                out.append(cur); cur = []
        if cur:
            out.append(cur)
        res = []
        for i, p in enumerate(out):
            t0 = p[0].start - 0.06
            nxt = out[i + 1][0].start - 0.06 if i + 1 < len(out) else p[-1].end + 0.6
            t1 = min(nxt, p[-1].end + 0.7)
            res.append({"words": p, "t0": t0, "t1": t1})
        return res

    def glyph(self, text, color, size=None, weight=900):
        key = (text, color, size, weight)
        if key not in self._glyph:
            f = self.f if size is None else font(weight, size)
            x0, y0, x1, y1 = f.getbbox(text)
            im = Image.new("RGBA", (x1 + 4, y1 + 4), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((2, 2), text, font=f, fill=(*color, 255))
            self._glyph[key] = (im, f.getbbox(text))
        return self._glyph[key]

    # -------------------------------------------------------------- drawing
    def render(self, frame: Image.Image, t: float):
        layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        hero = next((h for h in self.heroes if h.t0 <= t < h.t1), None)
        shown = None
        if hero:
            self._hero(layer, hero, t)
            shown = hero.big
        else:
            ph = next((p for p in self.phrases if p["t0"] <= t < p["t1"]), None)
            if ph:
                self._phrase(layer, ph, t)
                shown = " ".join(w.text for w in ph["words"])
        # legibility: soft dark glow under everything drawn on this layer
        a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(9))
        glow = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        glow.putalpha(a.point(lambda v: int(v * 0.55)))
        frame.alpha_composite(glow)
        frame.alpha_composite(layer)
        if self.st.hud:
            self._hud(frame, t)
        return shown

    def _phrase(self, layer, ph, t):
        st = self.st
        sp = st.size * 0.34
        items = [self.glyph(w.text, st.text) for w in ph["words"]]
        widths = [g[0].width for g in items]
        total = sum(widths) + sp * (len(items) - 1)
        x = 960 - total / 2
        out_u = ease_out((t - (ph["t1"] - 0.12)) / 0.12) if t > ph["t1"] - 0.12 else 0.0
        for w, (img, bb), wd in zip(ph["words"], items, widths):
            u = (t - (w.start - 0.05)) / 0.18
            if u <= 0:
                x += wd + sp
                continue
            p = ease_out_back(u)
            alpha = min(1.0, u * 1.8) * (1 - out_u)
            sc = 0.86 + 0.14 * p
            dy = (1 - p) * 26 - out_u * 18
            cy = st.y + dy
            if w.key:                       # accent box wipes in left -> right, text turns ink colour
                bu = ease_out((t - w.start) / 0.16)
                pad_x, pad_y = 14, 10
                bx0, by0 = x - pad_x, cy - st.size * 0.62 - pad_y
                bx1, by1 = x + wd + pad_x, cy + st.size * 0.42 + pad_y
                if bu > 0:
                    box = Image.new("RGBA", (int(bx1 - bx0), int(by1 - by0)), (*st.accent, int(255 * alpha)))
                    wv = max(1, int(box.width * bu))
                    layer.alpha_composite(box.crop((0, 0, wv, box.height)), (int(bx0), int(by0)))
                self._put(layer, img, x, cy, sc, alpha * (1 - bu))
                ink, _ = self.glyph(w.text, st.ink)
                if bu > 0:
                    self._put(layer, ink, x, cy, sc, alpha, clip_w=bu)
            else:
                self._put(layer, img, x, cy, sc, alpha)
            x += wd + sp

    def _put(self, layer, img, x, cy, sc, alpha, clip_w=1.0):
        if alpha <= 0.01:
            return
        w, h = max(1, round(img.width * sc)), max(1, round(img.height * sc))
        im = img.resize((w, h), Image.Resampling.LANCZOS) if sc != 1 else img.copy()
        if clip_w < 1:
            im = im.crop((0, 0, max(1, int(w * clip_w)), h))
        if alpha < 1:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
        ox = x + (img.width - w) / 2
        oy = cy - self.st.size * 0.80 + (img.height - h) / 2
        layer.alpha_composite(im, (int(round(ox)), int(round(oy))))

    def _hero(self, layer, h: Hero, t):
        st = self.st
        u = (t - h.t0)
        big = h.big
        if h.count_up and re.fullmatch(r"[\d,]+", big):
            target = int(big.replace(",", ""))
            val = int(target * ease_out(u / 0.75))
            big = f"{val:,}"
        out_u = ease_out((t - (h.t1 - 0.15)) / 0.15) if t > h.t1 - 0.15 else 0.0
        a = 1 - out_u
        size = 168
        img, bb = self.glyph(big, st.ink, size)
        full, _ = self.glyph(h.big, st.ink, size)            # box sized to the final number: no jitter
        p = ease_out_back(u / 0.28, 2.2)
        sc = 1.18 - 0.18 * p
        bw, bh = (full.width + 70) * sc, (size * 1.22) * sc
        cx, cy = 960, 520 - out_u * 30
        box = Image.new("RGBA", (int(bw), int(bh)), (*st.accent, int(255 * a)))
        rot = (1 - p) * -4
        box = box.rotate(rot, expand=True, resample=Image.Resampling.BICUBIC)
        layer.alpha_composite(box, (int(cx - box.width / 2), int(cy - box.height / 2)))
        w = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.Resampling.LANCZOS)
        if a < 1:
            w.putalpha(w.getchannel("A").point(lambda v: int(v * a)))
        layer.alpha_composite(w, (int(cx - w.width / 2), int(cy - w.height / 2 - 14 * sc)))
        for txt, dy, delay in ((h.above, -170, 0.0), (h.below, 160, 0.25)):
            if not txt:
                continue
            g, _ = self.glyph(txt, st.text, 64)
            q = ease_out_back((u - delay) / 0.22)
            if u - delay <= 0:
                continue
            al = min(1, (u - delay) * 5) * a
            gg = g.copy()
            gg.putalpha(gg.getchannel("A").point(lambda v: int(v * al)))
            layer.alpha_composite(gg, (int(cx - g.width / 2), int(cy + dy - g.height / 2 + (1 - q) * 24)))

    def _hud(self, frame, t):
        st = self.st
        d = ImageDraw.Draw(frame)
        W, H = frame.size
        c = (255, 255, 255, 150)
        m, L = 44, 46
        for (x, y, sx, sy) in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
            d.line((x, y, x + sx * L, y), fill=c, width=3)
            d.line((x, y, x, y + sy * L), fill=c, width=3)
        # countdown ring, top-right
        cx, cy, r = W - 120, 112, 34
        rem = max(0.0, self.duration - t)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, 70), width=3)
        frac = 1 - t / self.duration
        d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * frac, fill=(*st.accent, 255), width=4)
        mf = ImageFont.truetype(MONO, 18)
        s = f"00:{int(math.ceil(rem)):02d}"
        tw = d.textlength(s, font=mf)
        d.text((cx - tw / 2, cy - 11), s, font=mf, fill=(255, 255, 255, 230))
        # channel tag, top-left
        tf = font(800, 22)
        d.text((m + 18, m + 14), st.channel_tag, font=tf, fill=(255, 255, 255, 220))
        d.rectangle((m + 18, m + 46, m + 18 + 36, m + 50), fill=(*st.accent, 255))
