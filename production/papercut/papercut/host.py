"""Approved paper-cut ATLAS character as a host layer for Orbital Atlas renders.

Production-safe by construction (handoff V3 rules, see ../handoff_docs/):
- the only character pixels are assets/hero_approved_clean.png, verified by SHA-256 on load;
- the cutout is moved ONLY as a whole: translation, small roll, gentle scale (no limbs, no mouth);
- experimental_layers are refused; mirroring is not offered (it would change the design);
- motion amplitudes come from assets/MOTION_LIBRARY.json and are clamped to the QA gates
  (roll <= 2 deg, scale <= 3 %, bob <= 10 px at 960x540 == 20 px at 1920x1080).

Usage inside any episode renderer that composes PIL RGBA frames:

    host = HostLayer((1920, 1080), [Cue(0, 5, "listen", x=1720, y=1040, width=300, enter="right")])
    info = host.render(frame_rgba, t)      # composites in place, returns per-frame QA info
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
HERO_PATH = ASSET_DIR / "hero_approved_clean.png"
SOURCE_PATH = ASSET_DIR / "APPROVED_CONCEPT_UNMODIFIED.png"
MOTION_PATH = ASSET_DIR / "MOTION_LIBRARY.json"
HERO_SHA256 = "c313b8ade1d4c6db3e739bb979630d19be9e6d8f6220ce17f0292d12470def40"
SOURCE_SHA256 = "a0a68a20ed4c16a6e57589919a1ba8afca48484d870aa234079d348f04c9cbfe"
# The hero is an exact pixel crop of the approved sheet at this offset (verified by qa.source_match).
HERO_OFFSET_IN_SOURCE = (0, 18)

PRESET_REF_HEIGHT = 540          # presets and QA gates are authored at 960x540
GATE_ROLL_DEG = 2.0
GATE_SCALE_PCT = 3.0
GATE_BOB_PX_AT_540 = 10.0
GATE_WIDTH_FRAC = (0.12, 0.24)   # character width as a share of frame width
LOOP_PRESETS = ("idle", "explain", "listen", "surprise")


class HostError(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_hero(path: Path = HERO_PATH) -> Image.Image:
    path = Path(path)
    if "experimental_layers" in path.parts:
        raise HostError("experimental_layers are forbidden in release builds (not an articulated rig)")
    digest = sha256(path)
    if digest != HERO_SHA256:
        raise HostError(f"{path.name}: sha256 {digest[:12]}... is not the approved hero {HERO_SHA256[:12]}...")
    return Image.open(path).convert("RGBA")


def load_motion_library(path: Path = MOTION_PATH) -> dict:
    lib = json.loads(Path(path).read_text())
    for name in LOOP_PRESETS:
        p = lib[name]
        if p["roll_deg"] > GATE_ROLL_DEG or p["scale_percent"] > GATE_SCALE_PCT or p["bob_px"] > GATE_BOB_PX_AT_540:
            raise HostError(f"preset {name} exceeds the QA motion gate: {p}")
    return lib


def smoothstep(u: float) -> float:
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


@dataclass
class Cue:
    """One continuous appearance of the character.

    x, y   : frame position of the cutout's bottom-centre (feet line) in output pixels.
    width  : on-screen width of the cutout in output pixels (12-24 % of frame width).
    enter / exit : None, "left" or "right" - slide fully in from / out to that frame edge using the
                   preset duration and easing ("entrance" / "exit" in MOTION_LIBRARY.json).
    drift  : optional ((x2, y2), t_start, t_end) - a whole-body float to a new position (eased).
    """
    t0: float
    t1: float
    preset: str
    x: float
    y: float
    width: float
    enter: str | None = None
    exit: str | None = None
    drift: tuple | None = None
    name: str = ""


@dataclass
class HostLayer:
    frame_size: tuple
    cues: list
    shadow: bool = True
    hero: Image.Image | None = None
    motion: dict | None = None
    _cache: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self.hero = self.hero or load_hero()
        self.motion = self.motion or load_motion_library()
        W, H = self.frame_size
        self.k = H / PRESET_REF_HEIGHT   # preset px -> output px
        last = -1e9
        for c in sorted(self.cues, key=lambda c: c.t0):
            if c.preset not in LOOP_PRESETS:
                raise HostError(f"unknown preset {c.preset!r}; allowed: {LOOP_PRESETS}")
            frac = c.width / W
            if not (GATE_WIDTH_FRAC[0] - 1e-6 <= frac <= GATE_WIDTH_FRAC[1] + 1e-6):
                raise HostError(f"cue {c.name or c.t0}: width {frac:.1%} of frame is outside 12-24 %")
            if c.t0 < last:
                raise HostError("cues overlap; one hero on screen at a time")
            last = c.t1

    # ----------------------------------------------------------------- motion
    def _base(self, width: float) -> np.ndarray:
        """Premultiplied float RGBA of the hero, resized once per cue size (LANCZOS, downscale)."""
        key = round(width)
        if key not in self._cache:
            h = round(self.hero.height * key / self.hero.width)
            im = self.hero.resize((key, h), Image.Resampling.LANCZOS)
            a = np.asarray(im, dtype=np.float32) / 255.0
            a[..., :3] *= a[..., 3:4]
            self._cache[key] = a
        return self._cache[key]

    def state(self, t: float) -> dict | None:
        cue = next((c for c in self.cues if c.t0 <= t < c.t1), None)
        if cue is None:
            return None
        W, _ = self.frame_size
        p = self.motion[cue.preset]
        tau = t - cue.t0
        ph = 2 * math.pi * tau / p["period_s"]
        bob = p["bob_px"] * self.k * math.sin(ph)
        roll = p["roll_deg"] * math.sin(ph * 0.5 + 0.6) * min(1.0, tau / 0.4 + 0.35)
        scale = 1 + p["scale_percent"] / 100 * 0.5 * (1 - math.cos(ph))
        x, y = cue.x, cue.y
        if cue.drift:
            (x2, y2), ta, tb = cue.drift
            u = smoothstep((t - ta) / (tb - ta))
            x, y = x + (x2 - x) * u, y + (y2 - y) * u
        phase = "hold"
        half = cue.width * 0.62  # half-diagonal margin so the cutout is fully off-frame at the edge
        if cue.enter:
            e = self.motion["entrance"]
            u = (t - cue.t0) / e["duration_s"]
            if u < 1:
                phase = "enter"
                off = (W - x + half) if cue.enter == "right" else -(x + half)
                x += off * (1 - smoothstep(u))
        if cue.exit:
            e = self.motion["exit"]
            u = (t - (cue.t1 - e["duration_s"])) / e["duration_s"]
            if u > 0:
                phase = "exit"
                off = (W - x + half) if cue.exit == "right" else -(x + half)
                x += off * smoothstep(u)
        return {"cue": cue.name, "preset": cue.preset, "x": x, "y": y + bob, "roll_deg": roll,
                "scale": scale, "bob_px": bob, "width": cue.width, "phase": phase}

    # ---------------------------------------------------------------- render
    def render(self, frame: Image.Image, t: float) -> dict | None:
        st = self.state(t)
        if st is None:
            return None
        base = self._base(st["width"])
        bh, bw = base.shape[:2]
        s, r = st["scale"], math.radians(st["roll_deg"])
        # forward: out = A + s*R*(in - pivot); pivot = bottom-centre of the cutout
        px, py = bw / 2, bh
        cs, sn = math.cos(r), math.sin(r)
        corners = [(-px, -py), (bw - px, -py), (-px, bh - py), (bw - px, bh - py)]
        pts = [(st["x"] + s * (cs * u - sn * v), st["y"] + s * (sn * u + cs * v)) for u, v in corners]
        x0 = math.floor(min(p[0] for p in pts)) - 2
        y0 = math.floor(min(p[1] for p in pts)) - 2
        x1 = math.ceil(max(p[0] for p in pts)) + 2
        y1 = math.ceil(max(p[1] for p in pts)) + 2
        ow, oh = x1 - x0, y1 - y0
        # inverse map for PIL: in = pivot + (1/s) R^-1 (out + (x0,y0) - A)
        ax, ay = st["x"] - x0, st["y"] - y0
        a_, b_ = cs / s, sn / s
        c_, d_ = -sn / s, cs / s
        coeffs = (a_, b_, px - a_ * ax - b_ * ay, c_, d_, py - c_ * ax - d_ * ay)
        chans = []
        for ch in range(4):
            im = Image.fromarray(base[..., ch], mode="F")
            chans.append(np.asarray(im.transform((ow, oh), Image.Transform.AFFINE, coeffs,
                                                 resample=Image.Resampling.BICUBIC), dtype=np.float32))
        layer = np.clip(np.stack(chans, -1), 0.0, 1.0)
        layer[..., :3] = np.minimum(layer[..., :3], layer[..., 3:4])
        info = dict(st)
        info["bbox"] = _composite(frame, layer, x0, y0, self.shadow, self.k)
        return info


def _composite(frame: Image.Image, layer: np.ndarray, x0: int, y0: int, shadow: bool, k: float):
    """Premultiplied over-composite of `layer` into `frame` (RGBA, in place). Returns visible bbox."""
    W, H = frame.size
    alpha = layer[..., 3]
    lh, lw = alpha.shape
    sx, sy = x0 + round(6 * k / 2), y0 + round(8 * k / 2)
    # Work only inside the region the layer and its shadow can touch (the rest of the frame is unchanged:
    # the old full-frame float round trip gave back the same bytes there, at ~20x the cost).
    rx0, ry0 = max(0, min(x0, sx)), max(0, min(y0, sy))
    rx1, ry1 = min(W, max(x0, sx) + lw), min(H, max(y0, sy) + lh)
    if rx0 >= rx1 or ry0 >= ry1:
        return None
    dst = np.asarray(frame.crop((rx0, ry0, rx1, ry1)), dtype=np.float32) / 255.0
    RW, RH = rx1 - rx0, ry1 - ry0
    if shadow:   # soft paper drop shadow (scene element; does not touch character pixels)
        sh = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5 * k / 2))
        sa = np.asarray(sh, dtype=np.float32) / 255.0 * 0.38
        col = np.array([0.05, 0.07, 0.12], np.float32)
        shadow_px = np.dstack([sa * col[0], sa * col[1], sa * col[2], sa])
        _over(dst, shadow_px, sx - rx0, sy - ry0, RW, RH)
    _over(dst, layer, x0 - rx0, y0 - ry0, RW, RH)
    frame.paste(Image.fromarray((np.clip(dst, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA"), (rx0, ry0))
    ys, xs = np.nonzero(alpha > 0.03)
    if len(xs) == 0:
        return None
    return [int(x0 + xs.min()), int(y0 + ys.min()), int(x0 + xs.max() + 1), int(y0 + ys.max() + 1)]


def _over(dst, src, x0, y0, W, H):
    h, w = src.shape[:2]
    fx0, fy0, fx1, fy1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if fx0 >= fx1 or fy0 >= fy1:
        return
    s = src[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0]
    d = dst[fy0:fy1, fx0:fx1]
    a = s[..., 3:4]
    d[..., :3] = s[..., :3] + d[..., :3] * (1 - a)
    d[..., 3:4] = a + d[..., 3:4] * (1 - a)
