"""Reusable paper projection for the approved paper-cut ATLAS (owner-approved format, 2026-11-17).

The approved test (scenes/test20_projection.py, PR #56) drew the projection inside the scene script. This
module is the same look as an engine any renderer can use, so every future episode gets it from one place:

- a pale-cyan paper panel (grain, faint static scan lines, cream border, orange corner brackets) that opens
  out of ATLAS's raised glove with a soft light beam, holds, and turns pages as the narration moves on;
- each page = a short English tag (2-4 words) + a small animated paper diagram (`kind`);
- page change: the old page slides up and fades while the new one slides in (0.35 s);
- a gap between cues closes the panel back into the glove; the next cue opens it again.

Only the projection animates. ATLAS himself is drawn by papercut.actor (approved drawing, whole-cutout
motion, blink + mouth inside the one head): no limbs, joints or arms are touched here.

Speed: the panel background, its drop shadow, every static page and every phase of the looping page
animations are rendered once and cached; the beam is drawn in a small local box instead of a full-frame
layer with a full-frame blur. Steady-state frames are two small alpha composites.

Timing: `cues_from_script()` turns script pages anchored to narration words or phrases (yt-voice word
timings) into validated cues, so pages change on the spoken words without hand-typed timestamps.
"""
from __future__ import annotations

import math
import re
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import paper as P

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FONT = ROOT.parent / "kinetic_captions" / "fonts" / "unbounded-latin-800-normal.woff"

PROJ = (178, 226, 236)          # pale projection cyan (approved test v4)
PROJ_INK = (24, 52, 72)
RED = (200, 60, 45)
DESIGN = (350, 260)             # approved panel size at 1920x1080; diagrams are drawn in this space
DEFAULT_BOX = (330, 318, 680, 578)
KINDS = ("link", "blocked", "dark", "flash", "view", "wait", "label")
MAX_WORDS = 4                   # owner rule: short tags, usually 2-4 words
MAX_CHARS = 24
TAG_SIZE, TAG_MIN = 26, 22          # below 22 px at 1080p a tag is hard to read on a phone
CACHE_LIMIT = 512               # cached panel images per engine (all small: 350x260 RGBA)


def ease_out(u: float) -> float:
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


def ease_out_back(u: float, s: float = 1.2) -> float:
    u = min(1.0, max(0.0, u)) - 1
    return 1 + u * u * ((s + 1) * u + s)


def smoothstep(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


@dataclass(frozen=True)
class ProjectionCue:
    start: float
    end: float
    title: str
    kind: str = "label"

    def __post_init__(self):
        if not (0 <= self.start < self.end):
            raise ValueError(f"projection cue {self.title!r}: needs start >= 0 and end > start")
        if self.kind not in KINDS:
            raise ValueError(f"projection cue {self.title!r}: unknown diagram {self.kind!r} (one of {', '.join(KINDS)})")
        t = self.title.strip()
        if not t or len(t) > MAX_CHARS or len(t.split()) > MAX_WORDS or t != self.title:
            raise ValueError(f"projection tag {self.title!r}: 1-{MAX_WORDS} words, at most {MAX_CHARS} characters, "
                             "no leading/trailing spaces")


def _over(frame: Image.Image, im: Image.Image, x: int, y: int):
    """alpha_composite `im` at (x, y), clipped to the frame (PIL refuses negative offsets)."""
    W, H = frame.size
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(im.width, W - x), min(im.height, H - y)
    if sx0 >= sx1 or sy0 >= sy1:
        return
    frame.alpha_composite(im, (x + sx0, y + sy0), (sx0, sy0, sx1, sy1))


def _scale_alpha(im: Image.Image, a: float) -> Image.Image:
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda q: int(q * a)))
    return im


class ProjectionEngine:
    """Paper projection opened from ATLAS's glove. One instance per render; call render() once per frame.

    cues        : ProjectionCue list (non-overlapping). Touching cues are pages of one open panel;
                  a gap closes the panel and the next cue opens it again.
    box         : (x0, y0, x1, y1) panel rectangle in output pixels (approved: 330,318,680,578 at 1080p).
    frame_size  : output size; the box must sit inside it with `margin` px to spare.
    """

    def __init__(self, cues, box=DEFAULT_BOX, frame_size=(1920, 1080), font_path=None, open_s=0.45, page_s=0.35,
                 close_s=0.35, margin=24, min_page_s=1.0, alpha=0.93):
        self.cues = tuple(sorted(cues, key=lambda c: c.start))
        if not self.cues:
            raise ValueError("at least one projection cue is required")
        for a, b in zip(self.cues, self.cues[1:]):
            if b.start < a.end - 1e-9:
                raise ValueError(f"projection cues overlap: {a.title!r} ends {a.end:.2f}s, {b.title!r} starts {b.start:.2f}s")
        for c in self.cues:
            if c.end - c.start < min_page_s - 1e-9:
                raise ValueError(f"projection page {c.title!r} lasts {c.end - c.start:.2f}s; at least {min_page_s}s "
                                 "so it can be read")
        if min(open_s, page_s, close_s) <= 0:
            raise ValueError("animation durations must be positive")
        self.box = tuple(int(round(v)) for v in box)
        x0, y0, x1, y1 = self.box
        W, H = frame_size
        if x1 - x0 < 200 or y1 - y0 < 150:
            raise ValueError("projection box must be at least 200x150 px")
        if x0 < margin or y0 < margin or x1 > W - margin or y1 > H - margin:
            raise ValueError(f"projection box {self.box} is outside the {W}x{H} frame minus a {margin}px margin")
        self.frame_size = (W, H)
        self.w, self.h = x1 - x0, y1 - y0
        self.open_s, self.page_s, self.close_s, self.alpha = float(open_s), float(page_s), float(close_s), float(alpha)
        # sessions: runs of touching cues = one opening ... one closing
        self.sessions = []
        for c in self.cues:
            if self.sessions and abs(c.start - self.sessions[-1][-1].end) < 1e-6:
                self.sessions[-1].append(c)
            else:
                self.sessions.append([c])
        for s in self.sessions:
            if s[-1].end - s[0].start < open_s + close_s + 0.5:
                raise ValueError(f"projection from {s[0].start:.2f}s is open for under {open_s + close_s + 0.5:.2f}s")
        fp = Path(font_path) if font_path else DEFAULT_FONT
        self._font_path = str(fp)
        self._fonts = {}
        self._tag_font = {}
        for c in self.cues:              # fail at build time, not mid-render, if a tag cannot fit
            self._fit(c.title)
        self._build_static()
        self._cache = OrderedDict()
        self.stats = {"hits": 0, "misses": 0}

    # ------------------------------------------------------------------ static parts (built once)
    def _font(self, size):
        if size not in self._fonts:
            try:
                self._fonts[size] = ImageFont.truetype(self._font_path, size)
            except OSError as e:
                raise ValueError(f"projection font {self._font_path} unusable: {e}")
        return self._fonts[size]

    def _fit(self, title):
        if title not in self._tag_font:
            dw = DESIGN[0] - 40
            size = TAG_SIZE
            while size >= TAG_MIN:
                f = self._font(size)
                if f.getlength(title) <= dw:
                    self._tag_font[title] = f
                    break
                size -= 1
            else:
                raise ValueError(f"projection tag {title!r} does not fit the panel even at {TAG_MIN}px; shorten it")
        return self._tag_font[title]

    def _build_static(self):
        w, h = DESIGN
        g = P.grain(w, h, 17, 0.06)[..., None]
        base = np.clip(np.array(PROJ, np.float32)[None, None, :] * g, 0, 255)
        lines = np.ones((h, w, 1), np.float32)
        lines[::4] = 0.965                                   # faint static scan lines (no flicker)
        base = np.clip(base * lines, 0, 255).astype(np.uint8)
        k = 3
        m = Image.new("L", (w * k, h * k), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w * k - 1, h * k - 1), radius=16 * k, fill=255)
        mask = m.resize((w, h), Image.Resampling.LANCZOS)
        bg = Image.fromarray(np.dstack([base, np.asarray(mask)]), "RGBA")
        d = ImageDraw.Draw(bg)
        d.rounded_rectangle((3, 3, w - 4, h - 4), radius=14, outline=(*P.CREAM, 255), width=3)
        for cx, cy, sx, sy in ((14, 14, 1, 1), (w - 14, 14, -1, 1), (14, h - 14, 1, -1), (w - 14, h - 14, -1, -1)):
            d.line((cx, cy, cx + 18 * sx, cy), fill=(*P.ORANGE, 255), width=4)
            d.line((cx, cy, cx, cy + 18 * sy), fill=(*P.ORANGE, 255), width=4)
        if (self.w, self.h) != DESIGN:
            bg = bg.resize((self.w, self.h), Image.Resampling.LANCZOS)
            mask = mask.resize((self.w, self.h), Image.Resampling.LANCZOS)
        self._bg, self._mask = bg, mask
        # the panel's alpha is always mask * alpha (content is clipped to the mask), so its shadow is constant
        pa = mask.point(lambda q: int(q * self.alpha))
        sa = Image.new("L", (self.w + 40, self.h + 40), 0)
        sa.paste(pa, (20, 20))
        sh = Image.new("RGBA", sa.size, (0, 0, 0, 0))
        sh.putalpha(sa.filter(ImageFilter.GaussianBlur(7)).point(lambda q: int(q * 0.3)))
        self._shadow = sh

    # ------------------------------------------------------------------ page content (cached per animation phase)
    @staticmethod
    def _phase(kind, u):
        """Cache key of a page's animation state at u seconds into the page; None = still frame."""
        if kind == "link":
            return round((u * 0.8) % 1.0 * 240) / 240           # looping waves, 1.25 s cycle
        if kind == "wait":
            return round((u / 3.0) % 1.0 * 360) / 360           # clock hand, 3 s per turn
        if kind == "blocked" and u < 0.6:
            return round(u * 120) / 120
        if kind == "flash" and u < 1.4:
            return round(u * 120) / 120
        return None

    def _content(self, cue, u):
        ph = self._phase(cue.kind, u)
        key = ("c", cue.title, cue.kind, ph)
        im = self._get(key)
        if im is None:
            im = self._draw_content(cue, ph)
            self._put(key, im)
        return im

    def _get(self, key):
        im = self._cache.get(key)
        if im is not None:
            self._cache.move_to_end(key)
            self.stats["hits"] += 1
        else:
            self.stats["misses"] += 1
        return im

    def _put(self, key, im):
        self._cache[key] = im
        if len(self._cache) > CACHE_LIMIT:
            self._cache.popitem(last=False)

    def _draw_content(self, cue, ph):
        """One page in design space (350x260), transparent outside the drawings. ph = animation phase or None."""
        w, h = DESIGN
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        font = self._fit(cue.title)
        tw = d.textlength(cue.title, font=font)
        d.text(((w - tw) / 2, 22 + (TAG_SIZE - font.size) * 0.6), cue.title, font=font, fill=(*PROJ_INK, 255))
        cy = 150
        ink = (*PROJ_INK, 255)

        def disc(x, y, r, fill, outline=ink, wd=4):
            d.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=outline, width=wd)

        def earth(x, y, r):
            disc(x, y, r, (70, 120, 190, 255))
            d.polygon([(x - r * .5, y - r * .4), (x - r * .1, y - r * .65), (x + r * .15, y - r * .2), (x - r * .35, y + r * .05)],
                      fill=(120, 165, 100, 255))
            d.polygon([(x + r * .15, y + r * .1), (x + r * .55, y - r * .05), (x + r * .45, y + r * .5), (x + r * .1, y + r * .45)],
                      fill=(120, 165, 100, 255))

        def moon(x, y, r, lit=True):
            disc(x, y, r, (205, 200, 190, 255) if lit else (52, 56, 66, 255))
            for ox, oy, rr in ((-.35, -.25, .2), (.3, .2, .15), (-.05, .45, .1)):
                d.ellipse((x + ox * r - rr * r, y + oy * r - rr * r, x + ox * r + rr * r, y + oy * r + rr * r),
                          fill=(170, 165, 158, 255) if lit else (44, 48, 57, 255))

        def capsule(x, y, s=1.0, flip=False):
            sg = -1 if flip else 1
            pts = [(x - 20 * s * sg, y - 14 * s), (x + 14 * s * sg, y - 8 * s), (x + 14 * s * sg, y + 8 * s), (x - 20 * s * sg, y + 14 * s)]
            d.polygon(pts, fill=(*P.CREAM, 255), outline=ink, width=3)
            d.rectangle((min(x + 14 * s * sg, x + 22 * s * sg), y - 6 * s, max(x + 14 * s * sg, x + 22 * s * sg), y + 6 * s),
                        fill=(*P.ORANGE, 255), outline=ink, width=2)

        k = cue.kind
        if k == "link":
            earth(70, cy, 42); capsule(w - 70, cy - 10, 1.2, flip=True)
            for j in range(3):                                # waves travelling Earth -> Orion
                f = (ph + j / 3) % 1
                x = 120 + f * (w - 230)
                d.arc((x - 16, cy - 26, x + 16, cy + 6), 300, 60, fill=(*P.ORANGE, 255), width=4)
            for x in range(122, w - 104, 16):
                d.line((x, cy - 10, x + 7, cy - 10), fill=ink, width=3)
        elif k == "blocked":
            u = 1.0 if ph is None else ph
            earth(55, cy, 32); moon(w / 2 + 30, cy, 46); capsule(w - 45, cy, 1.0, flip=True)
            stop = w / 2 + 30 - 46
            grow = min(1.0, u / 0.6)
            for x in range(90, int(90 + (stop - 92) * grow), 16):
                d.line((x, cy, x + 7, cy), fill=(*RED, 255), width=4)
            if u > 0.6 or ph is None:
                xx, r = stop - 4, 11
                d.line((xx - r, cy - r, xx + r, cy + r), fill=(*RED, 255), width=5)
                d.line((xx - r, cy + r, xx + r, cy - r), fill=(*RED, 255), width=5)
        elif k == "dark":
            moon(w / 2, cy + 6, 70, lit=False)
            d.arc((w / 2 - 70, cy - 64, w / 2 + 70, cy + 76), 250, 330, fill=(*P.CREAM, 255), width=5)
        elif k == "flash":
            u = 1.4 if ph is None else ph
            moon(w / 2, cy + 6, 66)
            fx, fy = w / 2 + 16, cy - 8
            p = 0.5 + 0.5 * math.sin(min(u, 1.4) * 6)          # a few pulses, then it settles
            rr = 10 + 10 * p if u < 1.4 else 12
            for a in range(0, 360, 45):
                ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
                d.line((fx + ca * 6, fy + sa * 6, fx + ca * rr * 1.6, fy + sa * rr * 1.6), fill=(255, 240, 160, 255), width=4)
            d.ellipse((fx - 6, fy - 6, fx + 6, fy + 6), fill=(255, 250, 220, 255))
        elif k == "view":
            moon(w - 100, cy + 4, 58, lit=False)
            d.arc((w - 158, cy - 54, w - 42, cy + 62), 250, 320, fill=(*P.CREAM, 255), width=4)
            capsule(85, cy + 10, 1.8)
            d.ellipse((85 - 4, cy + 4, 85 + 8, cy + 16), fill=(90, 150, 200, 255), outline=ink, width=2)   # window
            for k2 in range(3):
                x = 140 + k2 * 22
                d.line((x, cy + 6, x + 10, cy + 6), fill=ink, width=3)
        elif k == "wait":                                     # ground waits: Earth, broken link, turning clock hand
            earth(62, cy + 4, 36)
            for x in range(108, 196, 16):
                d.line((x, cy + 4, x + 7, cy + 4), fill=ink, width=3)
            cx_, r = w - 92, 52
            disc(cx_, cy + 4, r, (*P.CREAM, 255))
            for i in range(12):
                a = i * math.pi / 6
                r0 = r - (10 if i % 3 == 0 else 6)
                d.line((cx_ + math.cos(a) * r0, cy + 4 + math.sin(a) * r0, cx_ + math.cos(a) * (r - 3),
                        cy + 4 + math.sin(a) * (r - 3)), fill=ink, width=3 if i % 3 == 0 else 2)
            a = 2 * math.pi * (ph or 0.0) - math.pi / 2
            d.line((cx_, cy + 4, cx_ + math.cos(a) * (r - 14), cy + 4 + math.sin(a) * (r - 14)), fill=(*P.ORANGE, 255), width=5)
            d.line((cx_, cy + 4, cx_, cy + 4 - (r - 26)), fill=ink, width=5)
            disc(cx_, cy + 4, 5, (*P.ORANGE, 255), wd=2)
        else:                                                 # "label": tag + a calm ruled line
            d.line((35, cy, w - 35, cy), fill=(*P.ORANGE, 255), width=5)
            d.ellipse((w / 2 - 11, cy - 11, w / 2 + 11, cy + 11), fill=(*P.CREAM, 255), outline=ink, width=3)
        if (self.w, self.h) != DESIGN:
            im = im.resize((self.w, self.h), Image.Resampling.LANCZOS)
        return im

    def _panel(self, cue, u, prev=None, pu=0.0):
        """Full panel (background + page, clipped to the rounded mask, alpha applied). Cached unless turning."""
        turning = prev is not None and u < self.page_s
        if not turning:
            key = ("p", cue.title, cue.kind, self._phase(cue.kind, u))
            im = self._get(key)
            if im is not None:
                return im
        panel = self._bg.copy()
        cur = self._content(cue, u)
        if turning:
            # old page slides up and fades out first, then the new page slides in and fades up (only a short
            # overlap, so two diagrams are never shown on top of each other at half strength)
            v = ease_out(u / self.page_s)
            v_old = ease_out(u / (0.5 * self.page_s))
            v_new = smoothstep((u - 0.35 * self.page_s) / (0.65 * self.page_s))
            off = round(24 * self.h / DESIGN[1])
            if v_old < 1:
                panel.alpha_composite(_scale_alpha(self._content(prev, pu), 1 - v_old), (0, 0),
                                      (0, int(off * v_old), self.w, self.h))
            new = _scale_alpha(cur, v_new)
            dy = int(off * (1 - v))
            panel.alpha_composite(new, (0, dy), (0, 0, self.w, self.h - dy))
        else:
            panel.alpha_composite(cur)
        a = np.minimum(np.asarray(panel.getchannel("A")), np.asarray(self._mask))
        panel.putalpha(Image.fromarray((a.astype(np.float32) * self.alpha).astype(np.uint8)))
        if not turning:
            self._put(key, panel)
        return panel

    # ------------------------------------------------------------------ per frame
    def active(self, t: float):
        """(session, cue index in session) at time t, or (None, None)."""
        for s in self.sessions:
            if s[0].start <= t < s[-1].end:
                for i, c in enumerate(s):
                    if c.start <= t < c.end:
                        return s, i
        return None, None

    def active_cue(self, t: float) -> Optional[ProjectionCue]:
        s, i = self.active(t)
        return None if s is None else s[i]

    def render(self, frame: Image.Image, t: float, hand_xy):
        """Draw the projection for time t into `frame` (RGBA, in place). hand_xy = ATLAS's glove on screen.
        Returns {"page", "kind", "box", "state", "beam"} or None when the projection is closed."""
        if frame.mode != "RGBA":
            raise ValueError("projection renderer requires an RGBA frame")
        if frame.size != self.frame_size:
            raise ValueError(f"frame is {frame.size}, engine was built for {self.frame_size}")
        if len(hand_xy) != 2:
            raise ValueError("hand_xy must contain x, y")
        s, i = self.active(t)
        if s is None:
            return None
        cue = s[i]
        hx, hy = map(float, hand_xy)
        t_open, t_close = s[0].start, s[-1].end
        if t < t_open + self.open_s:
            state = "opening"
            u_pos = ease_out_back((t - t_open) / self.open_s)
            a_open = ease_out((t - t_open) / 0.3)
        elif t >= t_close - self.close_s:
            state = "closing"
            v = smoothstep((t_close - t) / self.close_s)        # 1 -> 0 as the panel folds back into the glove
            u_pos, a_open = v, smoothstep((v - 0.2) / 0.6)     # fully gone before it shrinks to a dot
        else:
            state, u_pos, a_open = "open", 1.0, 1.0
        x0, y0, x1, y1 = self.box
        # beam: a soft cream-cyan wedge from the glove to the panel's lower edge, drawn in a small local box
        bx0 = hx + (x0 + 40 - hx) * u_pos
        bx1 = hx + (x1 - 40 - hx) * u_pos
        by = hy + (y1 - hy) * u_pos
        beam_box = None
        if a_open > 0.01:
            pad = 8
            lx0 = math.floor(min(hx - 6, bx0, bx1)) - pad; ly0 = math.floor(min(hy, by)) - pad
            lx1 = math.ceil(max(hx + 6, bx0, bx1)) + pad; ly1 = math.ceil(max(hy, by)) + pad
            beam = Image.new("RGBA", (lx1 - lx0, ly1 - ly0), (0, 0, 0, 0))
            ImageDraw.Draw(beam).polygon([(hx - 6 - lx0, hy - ly0), (hx + 6 - lx0, hy - ly0), (bx1 - lx0, by - ly0),
                                          (bx0 - lx0, by - ly0)], fill=(*PROJ, int(70 * a_open)))
            _over(frame, beam.filter(ImageFilter.GaussianBlur(3)), lx0, ly0)
            beam_box = [lx0, ly0, lx1, ly1]
        # panel
        u = t - cue.start
        prev = s[i - 1] if i > 0 and u < self.page_s else None
        panel = self._panel(cue, u, prev, (t - prev.start) if prev else 0.0)
        sc = max(0.05, min(1.06, u_pos))
        cx = hx + ((x0 + x1) / 2 - hx) * min(1.0, u_pos)
        cy = hy + ((y0 + y1) / 2 - hy) * min(1.0, u_pos)
        shadow = self._shadow
        if abs(sc - 1) > 1e-6:
            pw, ph_ = max(1, round(self.w * sc)), max(1, round(self.h * sc))
            panel = panel.resize((pw, ph_), Image.Resampling.LANCZOS)
            shadow = shadow.resize((max(1, round(shadow.width * sc)), max(1, round(shadow.height * sc))),
                                   Image.Resampling.BILINEAR)
        if a_open < 0.999:
            panel = _scale_alpha(panel, a_open)
            shadow = _scale_alpha(shadow, a_open)
        left, top = int(round(cx - panel.width / 2)), int(round(cy - panel.height / 2))
        _over(frame, shadow, int(cx - shadow.width / 2 + 5), int(cy - shadow.height / 2 + 8))
        _over(frame, panel, left, top)
        if prev is not None and state == "open":
            state = "turning"
        return {"page": cue.title, "kind": cue.kind, "box": [left, top, left + panel.width, top + panel.height],
                "state": state, "beam": beam_box}


# ---------------------------------------------------------------------- loading cues
def cues_from_dict(items):
    """Serialized cues [{"start", "end", "title", "kind"}] -> validated ProjectionCue list."""
    if not isinstance(items, list):
        raise ValueError("projection cues must be a list")
    return [ProjectionCue(float(x["start"]), float(x["end"]), str(x["title"]), str(x.get("kind", "label"))) for x in items]


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9']+", "", s.lower().replace("’", "'"))


def resolve_anchor(v, words, where="anchor"):
    """Seconds, {"word": i, "edge", "offset"} or {"phrase": "...", "occurrence": n, "edge", "offset"} -> seconds.
    words = yt-voice word timings [{"text", "start", "end"}] already placed on the video timeline."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if v < 0:
            raise ValueError(f"{where}: negative time")
        return float(v)
    if not isinstance(v, dict):
        raise ValueError(f"{where} must be seconds, a word anchor or a phrase anchor")
    extra = set(v) - {"word", "phrase", "occurrence", "edge", "offset"}
    if extra:
        raise ValueError(f"{where}: unknown keys {sorted(extra)}")
    edge = v.get("edge", "start")
    if edge not in ("start", "end"):
        raise ValueError(f"{where}.edge must be 'start' or 'end'")
    off = float(v.get("offset", 0.0))
    if not words:
        raise ValueError(f"{where} anchors to the narration but it has no word timings")
    if "word" in v:
        i = v["word"]
        if not isinstance(i, int) or not 0 <= i < len(words):
            raise ValueError(f"{where}.word must be 0..{len(words) - 1}")
        return max(0.0, words[i][edge] + off)
    toks = [_norm(x) for x in str(v.get("phrase", "")).split()]
    toks = [x for x in toks if x]
    if not toks:
        raise ValueError(f"{where}: needs 'word' or a non-empty 'phrase'")
    norm = [_norm(w["text"]) for w in words]
    hits = [i for i in range(len(norm) - len(toks) + 1) if norm[i:i + len(toks)] == toks]
    n = int(v.get("occurrence", 1))
    if len(hits) < n or n < 1:
        raise ValueError(f"{where}: phrase {v['phrase']!r} found {len(hits)} time(s) in the narration, "
                         f"occurrence {n} requested")
    i = hits[n - 1]
    return max(0.0, (words[i]["start"] if edge == "start" else words[i + len(toks) - 1]["end"]) + off)


def cues_from_script(pages, words, end=None, lead=0.15, tail=0.6):
    """Script pages -> cues on the spoken words.

    pages: [{"at": <anchor>, "title": "NO DIRECT PATH", "kind": "blocked", "until": <anchor, optional>}, ...]
      at    - when the page appears; anchors are resolved against the narration's word timings and moved
              `lead` seconds earlier, so the page has landed when the word is heard;
      until - optional: close the projection there (a gap before the next page); default = next page.
    end: anchor for the last page's end (default: last spoken word + `tail`).
    """
    if not isinstance(pages, list) or not pages:
        raise ValueError("projection pages must be a non-empty list")
    starts = []
    for k, p in enumerate(pages):
        if not isinstance(p, dict) or set(p) - {"at", "title", "kind", "until"}:
            raise ValueError(f"projection.pages[{k}] must have at, title, kind (and optional until)")
        starts.append(max(0.0, resolve_anchor(p.get("at"), words, f"projection.pages[{k}].at") - lead))
    for k in range(1, len(starts)):
        if starts[k] <= starts[k - 1]:
            raise ValueError(f"projection.pages[{k}] starts at {starts[k]:.2f}s, not after page {k - 1}")
    if end is not None:
        t_end = resolve_anchor(end, words, "projection.end")
    elif words:
        t_end = words[-1]["end"] + tail
    else:
        raise ValueError("projection.end is required when the narration has no word timings")
    cues = []
    for k, p in enumerate(pages):
        nxt = starts[k + 1] if k + 1 < len(starts) else t_end
        e = nxt
        if p.get("until") is not None:
            e = resolve_anchor(p["until"], words, f"projection.pages[{k}].until")
            if e > nxt + 1e-9:
                raise ValueError(f"projection.pages[{k}].until runs past the next page")
        cues.append(ProjectionCue(round(starts[k], 4), round(e, 4), str(p.get("title", "")), str(p.get("kind", "label"))))
    return cues
