"""Reusable paper-projection overlay for Orbital Atlas.

This module draws only diagram cards, not Atlas limbs or source footage.
Projection is independent of any episode, narrator, or hard-coded timestamps.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import cos, pi, sin
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

PAPER = (244, 233, 210)
INK = (28, 43, 57)
ORANGE = (228, 116, 50)
BLUE = (177, 214, 221)
KINDS = {"link", "blocked", "dark", "flash", "view", "label"}


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
            raise ValueError("projection cue must have start >= 0 and end > start")
        if self.kind not in KINDS:
            raise ValueError(f"unknown projection diagram: {self.kind}")
        if not self.title or len(self.title) > 32:
            raise ValueError("title must contain 1..32 characters")


class ProjectionEngine:
    """Draws a cached projection panel anchored to a supplied character hand point.

    Instantiate once per render, then call render(frame, t, hand_xy) on each frame.
    This renders onto the caller's RGBA PIL image and returns the panel bbox, or None.
    The host character is rendered separately. No limb manipulation occurs here.
    """

    def __init__(self, cues, box=(330, 318, 680, 578), open_seconds=0.45,
                 page_seconds=0.30, font_path=None):
        self.cues = tuple(sorted(cues, key=lambda c: c.start))
        if not self.cues:
            raise ValueError("at least one cue is required")
        for a, b in zip(self.cues, self.cues[1:]):
            if b.start < a.end - 1e-9:
                raise ValueError("projection cues must not overlap")
        self.box = tuple(map(int, box))
        x0, y0, x1, y1 = self.box
        if x1 <= x0 or y1 <= y0:
            raise ValueError("projection box has invalid dimensions")
        self.size = (x1-x0, y1-y0)
        if open_seconds <= 0 or page_seconds <= 0:
            raise ValueError("animation durations must be positive")
        self.open_seconds = float(open_seconds)
        self.page_seconds = float(page_seconds)
        try:
            self.font = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
        except OSError:
            self.font = ImageFont.load_default()
        self._panels = {}

    @staticmethod
    def _disc(draw, x, y, r, fill):
        draw.ellipse((x-r, y-r, x+r, y+r), fill=fill, outline=INK, width=3)

    def _panel(self, cue: ProjectionCue) -> Image.Image:
        key = (cue.title, cue.kind)
        if key in self._panels:
            return self._panels[key]
        w, h = self.size
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((1, 1, w-2, h-2), radius=14,
                            fill=BLUE + (244,), outline=PAPER + (255,), width=3)
        d.rectangle((12, 14, 19, 35), fill=ORANGE + (255,))
        d.text((28, 14), cue.title, font=self.font, fill=INK + (255,))
        cy = int(h * .63)
        cx = w // 2
        k = cue.kind
        if k in ("link", "blocked"):
            self._disc(d, 55, cy, 29, (83, 131, 185))
            self._disc(d, cx+30, cy, 42, (180, 180, 178))
            d.rectangle((w-61, cy-11, w-26, cy+11), fill=PAPER, outline=INK, width=3)
            stop = cx-13 if k == "blocked" else w-62
            for x in range(88, stop, 17):
                d.line((x, cy, min(x+9, stop), cy), fill=ORANGE, width=4)
            if k == "blocked":
                d.line((stop-8,cy-8,stop+8,cy+8), fill=(191,52,48),width=5)
                d.line((stop-8,cy+8,stop+8,cy-8), fill=(191,52,48),width=5)
        elif k in ("dark", "flash", "view"):
            self._disc(d, cx, cy, 65, (60, 66, 80) if k != "flash" else (183,181,178))
            if k == "flash":
                for i in range(8):
                    a = i * pi/4
                    d.line((cx+cos(a)*10, cy+sin(a)*10,
                            cx+cos(a)*37, cy+sin(a)*37), fill=(255,240,165),width=4)
            elif k == "view":
                d.arc((cx-64,cy-64,cx+64,cy+64),240,330,fill=PAPER,width=5)
        else:
            d.line((35, cy, w-35, cy), fill=ORANGE, width=5)
            d.ellipse((cx-11,cy-11,cx+11,cy+11), fill=PAPER,outline=INK,width=3)
        self._panels[key] = im
        return im

    def active_cue(self, t: float) -> Optional[ProjectionCue]:
        for cue in self.cues:
            if cue.start <= t < cue.end:
                return cue
        return None

    def render(self, frame: Image.Image, t: float, hand_xy):
        if frame.mode != "RGBA":
            raise ValueError("projection renderer requires RGBA frame")
        cue = self.active_cue(t)
        if cue is None:
            return None
        x0, y0, x1, y1 = self.box
        w, h = self.size
        if x0 < 0 or y0 < 0 or x1 > frame.width or y1 > frame.height:
            raise ValueError("projection box outside frame")
        if len(hand_xy) != 2:
            raise ValueError("hand_xy must contain x,y")
        u = smoothstep((t - cue.start)/self.open_seconds)
        # Single fixed-location panel, opened from the tracked hand point.
        # Avoid allocating a full-frame beam image on every frame.
        cx, cy = (x0+x1)/2, (y0+y1)/2
        hx, hy = map(float, hand_xy)
        px, py = hx + (cx-hx)*u, hy + (cy-hy)*u
        scale = max(0.02, u)
        sw, sh = max(1, round(w*scale)), max(1, round(h*scale))
        panel = self._panel(cue)
        if (sw,sh) != panel.size:
            panel = panel.resize((sw,sh), Image.Resampling.BICUBIC)
        left, top = round(px-sw/2), round(py-sh/2)
        # Clipped alpha-composite handles the opening phase even if hand is off-panel.
        layer = Image.new("RGBA", frame.size, (0,0,0,0))
        layer.paste(panel, (left,top), panel)
        beam = ImageDraw.Draw(layer, "RGBA")
        if u > 0 and u < 1:
            beam.line((hx,hy,px,py), fill=BLUE+(75,), width=6)
        frame.alpha_composite(layer)
        return {"cue": cue.title, "bbox": [left, top, left+sw, top+sh],
                "opening": u < 1, "hand": [hx, hy], "kind": cue.kind}


def cues_from_dict(items):
    """Convert serialized episode projection cues to validated immutable cues."""
    if not isinstance(items, list):
        raise ValueError("projection cues must be a list")
    return [ProjectionCue(float(x["start"]), float(x["end"]), str(x["title"]),
                          str(x.get("kind", "label"))) for x in items]
