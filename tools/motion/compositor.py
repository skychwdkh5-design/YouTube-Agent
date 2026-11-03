"""Layer compositor primitives for Orbital Atlas painted 2.5D scenes (NumPy + Pillow).

This generalises the primitives of examples/painted-collage-v7/build.py (branch
production/dynamic-motion-style-v1) instead of replacing them: same libraries, same
"alpha_composite painted cutouts over a documentary background" model, same FFmpeg rawvideo
pipe. What it adds is what V7 hard-coded or lacked:

* every animated value goes through a named curve from tools/motion/easing.py;
* rotation about a real pivot (e.g. a root plate), not about the bitmap centre;
* a 2.5D bend of a cutout (top moves more than base, with lag) for organic objects;
* a projected ground shadow + contact occlusion that follow the object's pose, instead of
  V7's fixed offset drop shadow (kept as drop_shadow_v7 for parity);
* a virtual camera that never upscales the source image and moves layers by depth (parallax);
* temporal supersampling (motion blur) for fast frames;
* a frame log of the values actually used, so QC can check the curves against pixels.

No new dependencies: Pillow, NumPy and the local FFmpeg only.
"""
from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size)


# --- cutouts --------------------------------------------------------------------------------

def clean_alpha(im: Image.Image, floor: int = 24) -> Image.Image:
    """Drop near-transparent matte noise around generated cutouts (README of the asset pack warns
    about coloured matte contamination). Mild: keeps painted soft edges."""
    im = im.convert("RGBA")
    a = np.asarray(im.getchannel("A"), dtype=np.float32)
    a = np.where(a < floor, 0, (a - floor) * 255.0 / (255 - floor))
    im.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    return im


def resize_to_height(im: Image.Image, h: float) -> Image.Image:
    h = max(2, int(round(h)))
    w = max(2, int(round(im.width * h / im.height)))
    return im.resize((w, h), Image.Resampling.LANCZOS)


def bend(im: Image.Image, base_y: float, amount_px: float, lag: float = 0.0,
         phase: float = 0.0, power: float = 2.0, lean_px: float = 0.0) -> Image.Image:
    """Horizontal 2.5D bend: row at height u (0 at base_y, 1 at the top of the bitmap) shifts by
    lean_px * u**power + amount_px * u**power * cos(phase - lag*u). The base stays planted, the
    crown leads or trails (lag). A deformation of the painted layer, not a rigid move or a zoom."""
    if abs(amount_px) + abs(lean_px) < 0.05:
        im = im.copy()
        im.info["bend_pad"] = 0
        return im
    arr = np.asarray(im.convert("RGBA"), dtype=np.float32)
    h, w, _ = arr.shape
    pad = int(math.ceil(abs(amount_px) + abs(lean_px))) + 2
    arr = np.pad(arr, ((0, 0), (pad, pad), (0, 0)))
    w2 = w + 2 * pad
    ys = np.arange(h, dtype=np.float32)
    u = np.clip((base_y - ys) / max(base_y, 1.0), 0.0, 1.0)
    dx = u ** power * (lean_px + amount_px * np.cos(phase - lag * u))
    xs = np.arange(w2, dtype=np.float32)[None, :] - dx[:, None]   # source x for each output x
    x0 = np.clip(np.floor(xs).astype(np.int32), 0, w2 - 1)
    x1 = np.clip(x0 + 1, 0, w2 - 1)
    fx = np.clip(xs - np.floor(xs), 0, 1)[..., None]
    rows = np.arange(h)[:, None]
    out = arr[rows, x0] * (1 - fx) + arr[rows, x1] * fx
    out = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")
    out.info["bend_pad"] = pad
    return out


@dataclass
class Placed:
    """A cutout already transformed, with its top-left on the frame."""
    image: Image.Image
    xy: tuple[int, int]


def place(im: Image.Image, pivot_px: tuple[float, float], at: tuple[float, float],
          angle_deg: float = 0.0, opacity: float = 1.0, blur: float = 0.0) -> Placed:
    """Rotate `im` about its own pivot (pixel coords inside im) and put that pivot at `at`
    (frame coords). PIL angle convention: positive = counter-clockwise."""
    px, py = pivot_px
    r = int(math.ceil(math.hypot(max(px, im.width - px), max(py, im.height - py)))) + 4
    canvas = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    canvas.alpha_composite(im, (int(round(r - px)), int(round(r - py))))
    if abs(angle_deg) > 0.01:
        canvas = canvas.rotate(angle_deg, Image.Resampling.BICUBIC, center=(r, r))
    if blur > 0.05:
        canvas = canvas.filter(ImageFilter.GaussianBlur(blur))
    if opacity < 0.999:
        a = np.asarray(canvas.getchannel("A"), dtype=np.float32) * max(0.0, opacity)
        canvas.putalpha(Image.fromarray(a.astype(np.uint8)))
    bbox = canvas.getchannel("A").getbbox()
    if not bbox:
        return Placed(Image.new("RGBA", (1, 1)), (0, 0))
    canvas = canvas.crop(bbox)
    return Placed(canvas, (int(round(at[0] - r + bbox[0])), int(round(at[1] - r + bbox[1]))))


def composite(frame: Image.Image, im: Image.Image, xy: tuple[int, int]) -> None:
    """alpha_composite that accepts positions partly or fully outside the frame."""
    x, y = int(xy[0]), int(xy[1])
    sx, sy = max(0, -x), max(0, -y)
    if sx >= im.width or sy >= im.height or x >= frame.width or y >= frame.height:
        return
    frame.alpha_composite(im, (max(0, x), max(0, y)), (sx, sy))


def place_centered_v7(im: Image.Image, center: tuple[float, float], height: float,
                      angle_deg: float = 0.0, opacity: float = 1.0) -> Placed:
    """V7 paste_prop geometry: scale to size, rotate about the bitmap centre, centre on point."""
    s = resize_to_height(im, height)
    if abs(angle_deg) > 0.05:
        s = s.rotate(angle_deg, Image.Resampling.BICUBIC, expand=True)
    if opacity < 0.999:
        s = s.copy()
        s.putalpha(s.getchannel("A").point(lambda v: int(v * max(0.0, opacity))))
    return Placed(s, (int(center[0] - s.width / 2), int(center[1] - s.height / 2)))


def drop_shadow_v7(frame: Image.Image, p: Placed) -> None:
    """Exactly V7's shadow: alpha*0.38, blur 9, fixed offset (12, 20)."""
    sh = Image.new("RGBA", p.image.size, (0, 0, 0, 0))
    sh.putalpha(p.image.getchannel("A").point(lambda v: int(v * .38)).filter(ImageFilter.GaussianBlur(9)))
    frame.alpha_composite(sh, (p.xy[0] + 12, p.xy[1] + 20))


def ground_shadow(frame: Image.Image, p: Placed, ground_y: float, lean: float = 0.9,
                  squash: float = 0.22, strength: float = 0.42, blur: float = 7.0,
                  contact: tuple[float, float, float] | None = None) -> None:
    """Project the object's silhouette onto a ground plane at ground_y with light from the
    upper-left (shadow falls right and slightly toward camera), so the shadow changes shape with
    the pose. `contact` = (x, width, darkness) adds a tight occlusion where the object meets the
    ground."""
    W, H = frame.size
    layer = Image.new("L", (W, H), 0)
    layer.paste(p.image.getchannel("A"), p.xy)
    gy = ground_y
    sx, sy = lean * squash, squash
    # inverse affine: output (x', y') -> source (x, y) on the object layer
    coeffs = (1, -sx / sy, sx / sy * gy, 0, -1 / sy, gy + gy / sy)
    proj = layer.transform((W, H), Image.Transform.AFFINE, coeffs, Image.Resampling.BILINEAR)
    proj = proj.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(proj, dtype=np.float32) * strength
    if contact:
        cx, cw, dark = contact
        x0, x1 = max(0, int(cx - cw)), min(W, int(cx + cw))
        y0, y1 = max(0, int(gy - cw * 0.3)), min(H, int(gy + cw * 0.3))
        if x1 > x0 and y1 > y0:
            yy, xx = np.mgrid[y0:y1, x0:x1]
            a[y0:y1, x0:x1] += 255 * dark * np.exp(-(((xx - cx) / (cw / 2)) ** 2 + ((yy - gy) / (cw * 0.08)) ** 2))
    sh = Image.new("RGBA", (W, H), (10, 18, 22, 0))
    sh.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    frame.alpha_composite(sh)


# --- background and camera --------------------------------------------------------------------

@dataclass
class Camera:
    """Window onto a large source image, in source pixels. The window is never smaller than the
    output, so the documentary image is never upscaled beyond its native pixels."""
    source: Image.Image
    out: tuple[int, int] = (1920, 1080)

    def frame(self, cx: float, cy: float, width: float, blur: float = 0.0) -> tuple[Image.Image, float]:
        W, H = self.out
        if width < W - 0.5:
            raise ValueError(f"camera window {width:.0f}px < output {W}px would upscale the source")
        h = width * H / W
        x0 = min(max(cx - width / 2, 0), self.source.width - width)
        y0 = min(max(cy - h / 2, 0), self.source.height - h)
        im = self.source.resize((W, H), Image.Resampling.LANCZOS, box=(x0, y0, x0 + width, y0 + h))
        if blur > 0.05:
            im = im.filter(ImageFilter.GaussianBlur(blur))
        return im.convert("RGBA"), W / width


def parallax(at: tuple[float, float], cam_shift: tuple[float, float], zoom_rel: float,
             depth: float, origin: tuple[float, float] = (960, 540)) -> tuple[float, float]:
    """Screen position of a foreground anchor when the camera moved by cam_shift (screen px of the
    background) and zoomed by zoom_rel; depth > 1 = closer to camera, so it moves more."""
    z = 1 + (zoom_rel - 1) * depth
    return (origin[0] + (at[0] - origin[0]) * z - cam_shift[0] * depth,
            origin[1] + (at[1] - origin[1]) * z - cam_shift[1] * depth)


# --- particles ------------------------------------------------------------------------------------

@dataclass
class Dust:
    """Soft soil/dust puff with gravity and drag, deterministic per seed."""
    origin: tuple[float, float]
    t0: float
    color: tuple[int, int, int] = (120, 92, 60)
    n: int = 60
    seed: int = 9
    spread: float = 1.0
    alpha: int = 150
    parts: list = field(default_factory=list)

    def __post_init__(self):
        rng = np.random.default_rng(self.seed)
        for _ in range(self.n):
            ang = rng.uniform(math.radians(200), math.radians(340))   # mostly upward fan
            sp = rng.uniform(60, 260) * self.spread
            self.parts.append((sp * math.cos(ang), sp * math.sin(ang) * 0.9,
                               rng.uniform(16, 44), rng.uniform(0.9, 2.0), rng.uniform(-40, 40)))

    def draw(self, frame: Image.Image, t: float) -> None:
        dt = t - self.t0
        if dt <= 0:
            return
        layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for vx, vy, size, life, off in self.parts:
            if dt > life:
                continue
            k = 2.2                                      # air drag
            fx = (1 - math.exp(-k * dt)) / k
            x = self.origin[0] + off + vx * fx
            y = self.origin[1] + vy * fx + 18 * dt * dt   # dust barely falls back
            r = size * (0.6 + 1.4 * dt / life)
            a = int(self.alpha * (1 - dt / life) ** 1.6)
            d.ellipse((x - r, y - r * 0.8, x + r, y + r * 0.8), fill=self.color + (a,))
        frame.alpha_composite(layer.filter(ImageFilter.GaussianBlur(14)))


# --- output ---------------------------------------------------------------------------------------

def shake(t: float, t0: float, amp: float = 6.0, freq: float = 13.0, decay: float = 9.0) -> tuple[float, float]:
    """Damped impact shake (screen px); zero before t0."""
    if t < t0:
        return 0.0, 0.0
    e = math.exp(-decay * (t - t0))
    return (amp * e * math.sin(2 * math.pi * freq * (t - t0)),
            0.6 * amp * e * math.sin(2 * math.pi * freq * 1.3 * (t - t0) + 1.1))


def supersample(render, t: float, fps: int, samples: int, shutter: float = 0.5) -> Image.Image:
    """Average `samples` renders across `shutter` of the frame interval (180 degree shutter)."""
    if samples <= 1:
        return render(t)
    acc = None
    for i in range(samples):
        im = render(t + shutter / fps * (i / (samples - 1) - 0.5))
        a = np.asarray(im.convert("RGB"), dtype=np.float32)
        acc = a if acc is None else acc + a
    return Image.fromarray((acc / samples).round().astype(np.uint8))


def encode(frames, out: Path, size=(1920, 1080), fps: int = 30, crf: int = 16) -> None:
    """Pipe RGB frames to the local FFmpeg (libx264, yuv420p), like V7's build()."""
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{size[0]}x{size[1]}", "-r", str(fps), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for im in frames:
        p.stdin.write(im.convert("RGB").tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError(f"ffmpeg failed for {out}")


class FrameLog:
    """Values actually used per frame, written next to the render for QC."""
    def __init__(self):
        self.rows: list[dict] = []

    def add(self, **kv):
        self.rows.append({k: (round(v, 4) if isinstance(v, float) else v) for k, v in kv.items()})

    def write(self, path: Path):
        path.write_text(json.dumps(self.rows, indent=0))
