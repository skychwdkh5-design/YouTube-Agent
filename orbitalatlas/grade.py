"""Documentary colour grading, kept strictly apart from scientific data (VISUAL_REF_001 'colour grading').

Two classes, never mixed up:
  EVIDENCE   satellite / measured pixels. Default grade is `neutral` (identity). `evidence_safe` is allowed (mild contrast and saturation, hue untouched,
             values stay monotonic) and is written into the manifest as an ENHANCED PRESENTATION: the credit line must not call the picture untouched.
  PRESENTATION  illustrations, basemaps, graphics: any preset.
`apply(img, preset)` is a pure function of the pixels, deterministic. `Graded(scene, preset)` wraps a Scene so a Sequence can use it, and records the grade
in `manifest()` (`evidence_pixels_unmodified` is False whenever anything but `neutral` is applied)."""
# effect-reuse-checked: yt-render has no grading and orbitalatlas had none; text tokens (THEME) are not colour grading.
import numpy as np
from PIL import Image

PRESETS = {
    "neutral": dict(sat=1.0, contrast=1.0, gamma=1.0, lift=0.0, gain=1.0, vignette=0.0, shadows_tint=(0, 0, 0), highlights_tint=(0, 0, 0)),
    "evidence_safe": dict(sat=1.08, contrast=1.06, gamma=1.0, lift=0.0, gain=1.0, vignette=0.0, shadows_tint=(0, 0, 0), highlights_tint=(0, 0, 0)),
    "documentary_map": dict(sat=1.28, contrast=1.14, gamma=0.96, lift=0.01, gain=1.0, vignette=0.12, shadows_tint=(-0.01, 0.0, 0.03), highlights_tint=(0.02, 0.01, -0.01)),
    "deep_ocean": dict(sat=1.35, contrast=1.18, gamma=0.94, lift=0.0, gain=1.02, vignette=0.15, shadows_tint=(-0.02, 0.0, 0.05), highlights_tint=(0.0, 0.01, 0.01)),
}
EVIDENCE_OK = {"neutral", "evidence_safe"}


def apply(img, preset="neutral", strength=1.0, mask=None):
    """return the graded PIL image. `strength` blends with the original; `mask` ('L', same size) limits the grade to a region (localised grading)."""
    p = PRESETS[preset] if isinstance(preset, str) else preset
    a = np.asarray(img.convert("RGB"), np.float32) / 255.0
    if p["sat"] != 1.0 or p["contrast"] != 1.0 or p["gamma"] != 1.0 or p["lift"] or p["gain"] != 1.0 or p["vignette"] or any(p["shadows_tint"]) or any(p["highlights_tint"]):
        luma = (a * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
        b = luma + (a - luma) * p["sat"]
        b = np.clip(b, 0, 1) ** p["gamma"]
        b = np.clip((b - 0.5) * p["contrast"] + 0.5, 0, 1)                      # linear contrast about mid grey
        b = b * p["gain"] + p["lift"]
        L = (b * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
        b = b + (1 - L) * np.array(p["shadows_tint"], np.float32) + L * np.array(p["highlights_tint"], np.float32)
        if p["vignette"]:
            H, W = b.shape[:2]; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); r = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)) / 1.414
            b = b * (1 - p["vignette"] * np.clip(r, 0, 1) ** 2.2)[..., None]
        b = np.clip(b, 0, 1)
    else:
        b = a
    w = float(strength)
    if mask is not None: w = w * (np.asarray(mask.convert("L"), np.float32) / 255.0)[..., None]
    out = a * (1 - w) + b * w
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))


class Graded:
    """Scene wrapper with the Scene interface used by Sequence (render, start, end, size, name, manifest)."""
    def __init__(self, scene, preset="documentary_map", strength=1.0, evidence=False, mask=None):
        if evidence and preset not in EVIDENCE_OK:
            raise ValueError(f"preset {preset!r} is not allowed on EVIDENCE pixels (allowed: {sorted(EVIDENCE_OK)}); grade a PRESENTATION layer instead")
        self.scene, self.preset, self.strength, self.evidence, self.mask = scene, preset, strength, evidence, mask
        self.size = scene.size; self.name = scene.name; self.reg = scene.reg
    @property
    def start(self): return self.scene.start
    @property
    def end(self): return self.scene.end
    @property
    def camera(self): return self.scene.camera
    def render(self, t, **kw): return apply(self.scene.render(t, **kw), self.preset, self.strength, self.mask)
    def manifest(self):
        m = list(self.scene.manifest())
        m.append(dict(type="Grade", cls="EVIDENCE_ENHANCED" if self.evidence and self.preset != "neutral" else ("EVIDENCE" if self.evidence else "PRESENTATION"), preset=self.preset,
                      strength=self.strength, localised=self.mask is not None, evidence_pixels_unmodified=bool(self.evidence and self.preset == "neutral")))
        return m
