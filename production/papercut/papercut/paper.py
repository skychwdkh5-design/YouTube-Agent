"""Paper-craft helpers for environments that sit with the approved paper-cut character.

Everything here is original procedural art (noise + shapes); nothing is traced from third-party media.
Palette taken from the approved sheet: cream, slate blue, navy, orange, peach.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

CREAM = (243, 233, 214)
BLUE = (79, 116, 160)
NAVY = (31, 40, 62)
ORANGE = (240, 132, 38)
PEACH = (246, 196, 160)
INK = (45, 34, 38)
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"


def font(size: int):
    try:
        return ImageFont.truetype(FONT_BOLD, size)
    except OSError:
        return ImageFont.load_default()


def grain(w: int, h: int, seed: int, strength: float = 0.05) -> np.ndarray:
    """Multiplicative paper grain (h, w) around 1.0: fine fibre noise + soft blotches."""
    rng = np.random.default_rng(seed)
    fine = Image.fromarray((rng.random((h, w)) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    coarse = Image.fromarray((rng.random((h // 16 + 1, w // 16 + 1)) * 255).astype(np.uint8)).resize(
        (w, h), Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(6))
    f = np.asarray(fine, np.float32) / 255 - 0.5
    c = np.asarray(coarse, np.float32) / 255 - 0.5
    return 1 + strength * (0.9 * f + 1.4 * c)


def paper_sheet(w: int, h: int, color, seed: int, strength=0.05) -> Image.Image:
    g = grain(w, h, seed, strength)[..., None]
    arr = np.clip(np.array(color, np.float32)[None, None] * g, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def cutout(mask: Image.Image, color, seed: int, border=0, border_color=CREAM, shadow=True,
           shadow_offset=(7, 9), shadow_blur=6, shadow_alpha=0.45) -> Image.Image:
    """Turn an 'L' mask into a textured paper piece with optional cream border and drop shadow."""
    w, h = mask.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    big = mask.filter(ImageFilter.MaxFilter(2 * border + 1)) if border else mask
    if shadow:
        sa = np.asarray(big.filter(ImageFilter.GaussianBlur(shadow_blur)), np.float32) * shadow_alpha
        sh = Image.new("RGBA", (w, h), (10, 12, 22, 0))
        sh.putalpha(Image.fromarray(sa.astype(np.uint8)))
        out.alpha_composite(sh, shadow_offset)
    if border:
        b = paper_sheet(w, h, border_color, seed + 7, 0.04)
        b.putalpha(big)
        out.alpha_composite(b)
    f = paper_sheet(w, h, color, seed, 0.07)
    f.putalpha(mask)
    out.alpha_composite(f)
    return out


def ss_mask(size, draw_fn, ss=3) -> Image.Image:
    """Supersampled antialiased mask: draw_fn(ImageDraw, scale) at ss x, downsample."""
    w, h = size
    m = Image.new("L", (w * ss, h * ss), 0)
    draw_fn(ImageDraw.Draw(m), ss)
    return m.resize((w, h), Image.Resampling.LANCZOS)


def label(frame: Image.Image, text: str, xy, size=26, fg=(255, 255, 255), bg=(0, 0, 0, 150), pad=(14, 8)):
    d = ImageDraw.Draw(frame)
    f = font(size)
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=f)
    w, h = x1 - x0 + 2 * pad[0], y1 - y0 + 2 * pad[1]
    box = Image.new("RGBA", (w, h), bg)
    frame.alpha_composite(box, (int(xy[0]), int(xy[1])))
    d.text((xy[0] + pad[0] - x0, xy[1] + pad[1] - y0), text, font=f, fill=fg)
    return (int(xy[0]), int(xy[1]), int(xy[0] + w), int(xy[1] + h))
