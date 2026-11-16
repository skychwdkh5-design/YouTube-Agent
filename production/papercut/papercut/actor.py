"""Pose switching, face layers (blink / mouth) and a glove wave for the approved paper-cut ATLAS.

Everything is built from approved pixels:
- poses / turnaround / emotion heads: tools/extract_sheet.py cut them 1:1 from the approved sheet
  (assets/sheet_cutouts, checksums in MANIFEST.json);
- hero face states: the OPEN eyes and OPEN mouth are the untouched hero pixels. Half-closed eyes and
  the half-open mouth are the hero's own eye / mouth pixels squashed vertically over a skin patch.
  Closed eyes / closed mouth are a skin patch plus one ink stroke in the hero's own ink colour.
  These four derived layers are the only non-original pixels and are listed for owner review;
- glove wave: the hero's own raised glove, rotated a few degrees around the wrist with an overlap
  band so no gap opens at the joint. Other limbs are NOT animated (no source for hidden geometry).

Switching between poses is a hard cut with the feet line kept in place (handoff rule: no crossfades
between different drawings).
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .host import (ASSET_DIR, GATE_BOB_PX_AT_540, GATE_ROLL_DEG, GATE_SCALE_PCT, HostError, _composite,
                   load_hero, load_motion_library, smoothstep)

CUT_DIR = ASSET_DIR / "sheet_cutouts"

# hero face geometry (hero_approved_clean.png pixels), measured on the asset
EYE_L = (208, 239, 236, 291)
EYE_R = (299, 224, 327, 271)
MOUTH = (237, 287, 312, 349)
SKIN_SAMPLE = (246, 250, 292, 284)          # clean cheek / nose skin between the eyes
# glove wave: cut line across the wrist (sleeve side -> glove side), pivot on it
WRIST_A, WRIST_B = (384, 346), (440, 394)
GLOVE_XMIN_ABOVE = (409, 338)                # left of x=409 above y=338 is the helmet: never moved
OVERLAP = 7                                   # px of double coverage across the cut line


def load_cutout(name: str) -> Image.Image:
    man = json.loads((CUT_DIR / "MANIFEST.json").read_text())
    p = CUT_DIR / f"{name}.png"
    if name not in man["items"]:
        raise HostError(f"{name}: not an extracted approved cutout")
    if hashlib.sha256(p.read_bytes()).hexdigest() != man["items"][name]["sha256"]:
        raise HostError(f"{name}: checksum differs from MANIFEST.json")
    return Image.open(p).convert("RGBA")


# --------------------------------------------------------------------------- face layers
def _skin_patch(hero: np.ndarray, box, pad, rng) -> tuple[np.ndarray, np.ndarray]:
    """Skin-coloured textured patch + soft elliptical mask covering `box` (+pad)."""
    sx0, sy0, sx1, sy1 = SKIN_SAMPLE
    sample = hero[sy0:sy1, sx0:sx1, :3].reshape(-1, 3).astype(np.float32)
    mean, std = sample.mean(0), sample.std(0)
    x0, y0, x1, y1 = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    w, h = x1 - x0, y1 - y0
    noise = Image.fromarray((rng.standard_normal((h, w)) * 40 + 128).clip(0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(1.0))
    n = (np.asarray(noise, np.float32) - 128) / 40 * 1.6
    patch = np.clip(mean[None, None] + n[..., None] * std[None, None], 0, 255)
    m = Image.new("L", (w * 4, h * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, w * 4 - 1, h * 4 - 1), fill=255)
    m = m.resize((w, h), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(1.2))
    return patch, np.asarray(m, np.float32) / 255


def _paste(dst: np.ndarray, src_rgb: np.ndarray, mask: np.ndarray, x0: int, y0: int):
    h, w = mask.shape
    reg = dst[y0:y0 + h, x0:x0 + w, :3].astype(np.float32)
    dst[y0:y0 + h, x0:x0 + w, :3] = (src_rgb * mask[..., None] + reg * (1 - mask[..., None])).round().astype(np.uint8)


def _feature_mask(hero: np.ndarray, box, thresh=60.0) -> np.ndarray:
    """Pixels of a facial feature inside box: far from the skin colour."""
    sx0, sy0, sx1, sy1 = SKIN_SAMPLE
    mean = hero[sy0:sy1, sx0:sx1, :3].reshape(-1, 3).astype(np.float32).mean(0)
    x0, y0, x1, y1 = box
    reg = hero[y0:y1, x0:x1, :3].astype(np.float32)
    d = np.linalg.norm(reg - mean, axis=-1)
    m = np.clip((d - thresh * 0.5) / (thresh * 0.5), 0, 1)
    return m


def _ink(hero: np.ndarray, box) -> tuple:
    x0, y0, x1, y1 = box
    reg = hero[y0:y1, x0:x1, :3].reshape(-1, 3)
    lum = reg.sum(1)
    dark = reg[lum <= np.percentile(lum, 10)]
    return tuple(int(v) for v in np.median(dark, 0))


def _stroke(dst: np.ndarray, pts, width: float, color):
    """Anti-aliased ink polyline, 4x supersampled, drawn into an RGBA uint8 array."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0 = int(min(xs) - width - 2), int(min(ys) - width - 2)
    x1, y1 = int(max(xs) + width + 3), int(max(ys) + width + 3)
    s = 4
    m = Image.new("L", ((x1 - x0) * s, (y1 - y0) * s), 0)
    d = ImageDraw.Draw(m)
    sp = [((x - x0) * s, (y - y0) * s) for x, y in pts]
    d.line(sp, fill=255, width=int(width * s), joint="curve")
    r = width * s / 2
    for x, y in (sp[0], sp[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=255)
    m = np.asarray(m.resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS), np.float32) / 255
    col = np.ones((y1 - y0, x1 - x0, 3), np.float32) * np.array(color, np.float32)
    _paste(dst, col, m, x0, y0)


def _arc(x0, x1, y, sag, n=16):
    return [(x0 + (x1 - x0) * i / (n - 1), y + sag * math.sin(math.pi * i / (n - 1))) for i in range(n)]


def _squash(dst: np.ndarray, hero: np.ndarray, box, factor: float, anchor: str, rng, pad=3):
    """Cover the feature with skin, then re-lay its own pixels squashed vertically."""
    x0, y0, x1, y1 = box
    patch, pm = _skin_patch(hero, box, pad, rng)
    _paste(dst, patch, pm, x0 - pad, y0 - pad)
    fm = _feature_mask(hero, box)
    reg = Image.fromarray(hero[y0:y1, x0:x1, :3])
    h = y1 - y0
    nh = max(2, round(h * factor))
    reg_s = np.asarray(reg.resize((x1 - x0, nh), Image.Resampling.LANCZOS), np.float32)
    m_s = np.asarray(Image.fromarray((fm * 255).astype(np.uint8)).resize((x1 - x0, nh), Image.Resampling.LANCZOS),
                     np.float32) / 255
    ny0 = y0 if anchor == "top" else (y1 - nh if anchor == "bottom" else y0 + (h - nh) // 2)
    _paste(dst, reg_s, m_s, x0, ny0)


def build_face_variants(hero_img: Image.Image) -> dict:
    """Return {(eyes, mouth): RGBA Image}; eyes in open/half/closed, mouth in open/mid/closed."""
    hero = np.asarray(hero_img).copy()
    rng = np.random.default_rng(7)
    ink_eye = _ink(hero, EYE_L)
    ink_mouth = _ink(hero, MOUTH)
    out = {}
    for eyes in ("open", "half", "closed"):
        for mouth in ("open", "mid", "closed"):
            a = hero.copy()
            if eyes == "half":      # eyelid half down: upper half of the eye under skin + lid line
                for box in (EYE_L, EYE_R):
                    x0, y0, x1, y1 = box
                    ym = y0 + (y1 - y0) * 0.52
                    patch, pm = _skin_patch(hero, box, 3, rng)
                    yy = np.arange(pm.shape[0])[:, None] + (y0 - 3)
                    pm = pm * np.clip((ym + 1.5 - yy) / 3.0, 0, 1)
                    _paste(a, patch, pm, x0 - 3, y0 - 3)
                    fm = _feature_mask(hero, box)
                    row = np.nonzero(fm[int(ym) - y0] > 0.5)[0]
                    lx0, lx1 = (x0 + row.min(), x0 + row.max()) if len(row) else (x0 + 5, x1 - 5)
                    _stroke(a, _arc(lx0 - 1, lx1 + 1, ym, 1.0), 4.2, ink_eye)
            elif eyes == "closed":
                for box in (EYE_L, EYE_R):
                    patch, pm = _skin_patch(hero, box, 3, rng)
                    _paste(a, patch, pm, box[0] - 3, box[1] - 3)
                    y = box[1] + (box[3] - box[1]) * 0.70
                    _stroke(a, _arc(box[0] - 1, box[2] + 1, y, 3.0), 4.6, ink_eye)
            if mouth == "mid":
                _squash(a, hero, MOUTH, 0.55, "top", rng)
            elif mouth == "closed":
                patch, pm = _skin_patch(hero, MOUTH, 2, rng)
                _paste(a, patch, pm, MOUTH[0] - 2, MOUTH[1] - 2)
                _stroke(a, _arc(MOUTH[0] + 8, MOUTH[2] - 8, MOUTH[1] + 9, 9.0), 4.8, ink_mouth)
            out[(eyes, mouth)] = Image.fromarray(a, "RGBA")
    return out


# --------------------------------------------------------------------------- glove wave
def _signed(px, py):
    (ax, ay), (bx, by) = WRIST_A, WRIST_B
    nx, ny = (by - ay), -(bx - ax)          # normal pointing to the glove side (up-right)
    ln = math.hypot(nx, ny)
    return ((px - ax) * nx + (py - ay) * ny) / ln


def build_glove_split(hero_img: Image.Image):
    """(static RGBA, glove RGBA, pivot). Glove side of the wrist line, excluding the helmet."""
    a = np.asarray(hero_img).copy()
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = _signed(xx, yy)
    region = (xx >= 384) & (yy <= 400) & (yy >= 240)
    region &= ~((xx < GLOVE_XMIN_ABOVE[0]) & (yy < GLOVE_XMIN_ABOVE[1]))
    glove_m = region & (d > -OVERLAP)
    remove_m = region & (d > OVERLAP)
    glove = a.copy(); glove[..., 3] = np.where(glove_m, a[..., 3], 0)
    static = a.copy(); static[..., 3] = np.where(remove_m, 0, a[..., 3])
    pivot = ((WRIST_A[0] + WRIST_B[0]) / 2, (WRIST_A[1] + WRIST_B[1]) / 2)
    return Image.fromarray(static, "RGBA"), Image.fromarray(glove, "RGBA"), pivot


# --------------------------------------------------------------------------- actor
@dataclass
class ActorCue:
    """One continuous shot of the character in a single drawing.

    drawing : "hero" or a cutout name from assets/sheet_cutouts (pose_*, turn_*, face_*).
    x, y    : feet line (bottom-centre) in output px.  height: on-screen height of the drawing.
    preset  : idle / explain / listen / surprise (whole-cutout motion amplitudes).
    talk    : list of (t0, t1) speech intervals -> mouth flap from `envelope` (hero only).
    blinks  : list of blink start times (hero only).
    wave    : (t0, t1) glove wave (hero only).
    fx      : list of (name, t0, t1, dx, dy, height): sheet effect marks popping beside the figure.
    pop     : True = 4-frame paper "pop" on the cut (scale 0.97 -> 1.0 inside the 3 % gate).
    """
    t0: float
    t1: float
    drawing: str
    x: float
    y: float
    height: float
    preset: str = "idle"
    enter: str | None = None
    exit: str | None = None
    talk: list = field(default_factory=list)
    blinks: list = field(default_factory=list)
    wave: tuple | None = None
    fx: list = field(default_factory=list)
    pop: bool = True
    name: str = ""


class Actor:
    def __init__(self, frame_size, cues, envelope=None, shadow=True):
        self.W, self.H = frame_size
        self.k = self.H / 540
        self.cues = sorted(cues, key=lambda c: c.t0)
        self.motion = load_motion_library()
        self.hero = load_hero()
        self.faces = build_face_variants(self.hero)
        self.envelope = envelope            # callable t -> 0..1 loudness
        self.shadow = shadow
        self._img, self._base = {}, {}
        self._glove = {}
        for c in self.cues:
            if c.drawing != "hero":
                if c.talk or c.blinks or c.wave:
                    raise HostError(f"{c.name}: talk/blink/wave exist only for the hero drawing")
                self._img[c.drawing] = load_cutout(c.drawing)
            for fx in c.fx:
                self._img.setdefault(fx[0], load_cutout(fx[0]))
        self._mouth_state = {}

    # ---- per-frame drawing choice
    def mouth(self, cue, t):
        for a, b in cue.talk:
            if a <= t < b and self.envelope:
                e = self.envelope(t)
                return "open" if e > 0.45 else "mid" if e > 0.15 else "closed"
        return "open" if not cue.talk else "closed"

    def eyes(self, cue, t):
        for b in cue.blinks:
            f = (t - b) * 30
            if 0 <= f < 1.5 or 3.5 <= f < 5:
                return "half"
            if 1.5 <= f < 3.5:
                return "closed"
        return "open"

    def drawing_image(self, cue, t):
        if cue.drawing != "hero":
            return cue.drawing, self._img[cue.drawing]
        key = (self.eyes(cue, t), self.mouth(cue, t))
        return f"hero:{key[0]}:{key[1]}", self.faces[key]

    # ---- motion
    def state(self, t):
        cue = next((c for c in self.cues if c.t0 <= t < c.t1), None)
        if cue is None:
            return None, None
        p = self.motion[cue.preset]
        tau = t - cue.t0
        ph = 2 * math.pi * tau / p["period_s"]
        bob = p["bob_px"] * self.k * math.sin(ph)
        roll = p["roll_deg"] * math.sin(ph * 0.5 + 0.6) * min(1.0, tau / 0.4 + 0.35)
        scale = 1 + p["scale_percent"] / 100 * 0.5 * (1 - math.cos(ph))
        if cue.pop and tau < 4 / 30:
            scale *= 0.97 + 0.03 * smoothstep(tau / (4 / 30))
        scale = min(scale, 1 + GATE_SCALE_PCT / 100)
        x, phase = cue.x, "hold"
        half = cue.height * 0.5
        if cue.enter:
            u = tau / self.motion["entrance"]["duration_s"]
            if u < 1:
                phase = "enter"
                off = (self.W - x + half) if cue.enter == "right" else -(x + half)
                x += off * (1 - smoothstep(u))
        if cue.exit:
            d = self.motion["exit"]["duration_s"]
            u = (t - (cue.t1 - d)) / d
            if u > 0:
                phase = "exit"
                off = (self.W - x + half) if cue.exit == "right" else -(x + half)
                x += off * smoothstep(u)
        assert abs(roll) <= GATE_ROLL_DEG and abs(bob) <= GATE_BOB_PX_AT_540 * self.k + 1e-6
        return cue, {"x": x, "y": cue.y + bob, "roll_deg": roll, "scale": scale, "bob_px": bob, "phase": phase}

    def _premul(self, key, img, height):
        k2 = (key, round(height))
        if k2 not in self._base:
            w = round(img.width * height / img.height)
            im = img.resize((w, round(height)), Image.Resampling.LANCZOS)
            a = np.asarray(im, np.float32) / 255
            a[..., :3] *= a[..., 3:4]
            self._base[k2] = a
        return self._base[k2]

    def _layer(self, base, st, pivot_px=None, extra_rot=0.0):
        """Affine-render premultiplied `base` around its bottom-centre (or `pivot_px` in base px)."""
        bh, bw = base.shape[:2]
        s, r = st["scale"], math.radians(st["roll_deg"])
        px, py = bw / 2, bh
        cs, sn = math.cos(r), math.sin(r)
        # optional local rotation (glove) about pivot_px before the global transform
        if pivot_px is not None and extra_rot:
            ca, sa = math.cos(math.radians(extra_rot)), math.sin(math.radians(extra_rot))
            qx, qy = pivot_px
        else:
            ca, sa, qx, qy = 1.0, 0.0, 0.0, 0.0
        def fwd(u, v):
            u2 = qx + ca * (u - qx) - sa * (v - qy)
            v2 = qy + sa * (u - qx) + ca * (v - qy)
            du, dv = u2 - px, v2 - py
            return st["x"] + s * (cs * du - sn * dv), st["y"] + s * (sn * du + cs * dv)
        pts = [fwd(u, v) for u, v in ((0, 0), (bw, 0), (0, bh), (bw, bh))]
        x0 = math.floor(min(p[0] for p in pts)) - 2; y0 = math.floor(min(p[1] for p in pts)) - 2
        x1 = math.ceil(max(p[0] for p in pts)) + 2; y1 = math.ceil(max(p[1] for p in pts)) + 2
        # inverse of fwd as one affine: out -> in
        ox, oy = fwd(0, 0); ex = fwd(1, 0); ey = fwd(0, 1)
        A = np.array([[ex[0] - ox, ey[0] - ox], [ex[1] - oy, ey[1] - oy]])
        Ai = np.linalg.inv(A)
        tx, ty = -Ai @ np.array([ox - x0, oy - y0])
        coeffs = (Ai[0, 0], Ai[0, 1], tx, Ai[1, 0], Ai[1, 1], ty)
        ch = [np.asarray(Image.fromarray(base[..., c], "F").transform((x1 - x0, y1 - y0), Image.Transform.AFFINE, coeffs,
                                                                      resample=Image.Resampling.BICUBIC), np.float32)
              for c in range(4)]
        layer = np.clip(np.stack(ch, -1), 0, 1)
        layer[..., :3] = np.minimum(layer[..., :3], layer[..., 3:4])
        return layer, x0, y0

    def render(self, frame: Image.Image, t: float):
        cue, st = self.state(t)
        if cue is None:
            return None
        key, img = self.drawing_image(cue, t)
        info = dict(st, cue=cue.name, drawing=key, height=cue.height)
        waving = cue.drawing == "hero" and cue.wave and cue.wave[0] <= t < cue.wave[1]
        if waving:
            if key not in self._glove:
                self._glove[key] = build_glove_split(img)
            static, glove, pivot = self._glove[key]
            sc = cue.height / img.height
            bs = self._premul(key + ":static", static, cue.height)
            bg_ = self._premul(key + ":glove", glove, cue.height)
            a0, a1 = cue.wave
            env = smoothstep((t - a0) / 0.25) * smoothstep((a1 - t) / 0.25)
            ang = -7.0 * env * math.sin(2 * math.pi * 2.0 * (t - a0))
            l1, x0, y0 = self._layer(bs, st)
            l2, x2, y2 = self._layer(bg_, st, (pivot[0] * sc, pivot[1] * sc), ang)
            # merge both into one layer box so the shadow is cast once
            X0, Y0 = min(x0, x2), min(y0, y2)
            X1 = max(x0 + l1.shape[1], x2 + l2.shape[1]); Y1 = max(y0 + l1.shape[0], y2 + l2.shape[0])
            L = np.zeros((Y1 - Y0, X1 - X0, 4), np.float32)
            for l, lx, ly in ((l1, x0, y0), (l2, x2, y2)):
                d = L[ly - Y0:ly - Y0 + l.shape[0], lx - X0:lx - X0 + l.shape[1]]
                al = l[..., 3:4]
                d[...] = l + d * (1 - al)
            layer, lx, ly = L, X0, Y0
            info["glove_deg"] = ang
        else:
            layer, lx, ly = self._layer(self._premul(key, img, cue.height), st)
        info["bbox"] = _composite(frame, layer, lx, ly, self.shadow, self.k)
        # effect marks (original sheet pixels) pop next to the figure, screen-space, no roll
        for name, f0, f1, dx, dy, hh in cue.fx:
            if f0 <= t < f1:
                u = smoothstep((t - f0) / 0.15)
                fx_st = {"x": st["x"] + dx, "y": st["y"] + dy - 6 * self.k * math.sin(min(1, (t - f0) / 0.3) * math.pi),
                         "roll_deg": 0.0, "scale": 0.85 + 0.15 * u}
                fl, fx0, fy0 = self._layer(self._premul(name, self._img[name], hh), fx_st)
                _composite(frame, fl, fx0, fy0, False, self.k)
        return info
