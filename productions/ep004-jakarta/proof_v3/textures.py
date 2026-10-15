"""procedural PBR textures for the S3 V3 true-3D scene (original, generated here; CC0 like the rest of the illustration).
Albedo maps are sRGB PNGs; bump maps are 8-bit greyscale PNGs (pbrt 'texture displacement'). Deterministic (fixed seeds)."""
import os
import numpy as np
from PIL import Image, ImageFilter


def noise(h, w, scales=(4, 16, 64), weights=(0.5, 0.3, 0.2), seed=0):
    rng = np.random.default_rng(seed); out = np.zeros((h, w), np.float32)
    for s, k in zip(scales, weights):
        small = rng.random((max(2, h // s), max(2, w // s))).astype(np.float32)
        out += k * np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    return (out - out.min()) / (np.ptp(out) + 1e-6)


def save(a, path, mode="RGB"):
    Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8), mode if mode == "L" else None).save(path)


def strata(base, band_freq, band_amp, grain, seed, h=512, w=1024, wavy=0.0):
    """layered sediment: base colour, horizontal laminations, grain speckle. returns albedo (h,w,3), bump (h,w)."""
    y = np.arange(h)[:, None] / h; x = np.arange(w)[None, :] / w
    n = noise(h, w, (8, 32, 128), (0.45, 0.35, 0.2), seed)
    warp = wavy * np.sin(x * 2 * np.pi * 1.5 + n * 3)
    n2 = noise(h, w, (64, 256), (0.6, 0.4), seed + 3)                                   # irregular bed thickness, not a regular sine
    bands = 0.5 + 0.5 * np.sin((y + warp * 0.012 + 0.03 * n2) * band_freq * 2 * np.pi + n * 1.2) * (0.6 + 0.4 * n2)
    rng = np.random.default_rng(seed + 7); g = rng.random((h, w)).astype(np.float32)
    lum = 1 + band_amp * (bands - 0.5) + 0.26 * (n - 0.5) + grain * (g - 0.5)
    alb = np.clip(np.asarray(base, np.float32)[None, None, :] / 255 * lum[..., None], 0, 1)
    bump = np.clip(0.5 + 0.35 * (bands - 0.5) + 0.4 * grain * (g - 0.5) + 0.2 * (n - 0.5), 0, 1)
    return alb, bump


def facade(seed, w=512, h=1024, cols=8, rows=18, lit=0.18, tint=(0.62, 0.64, 0.66)):
    """concrete facade with a window grid: albedo (glass darker, frames lighter) and an emission mask for lit windows."""
    rng = np.random.default_rng(seed); n = noise(h, w, (8, 32), (0.6, 0.4), seed)
    alb = np.ones((h, w, 3), np.float32) * np.asarray(tint, np.float32) * (0.85 + 0.15 * n[..., None]); em = np.zeros((h, w), np.float32)
    cw, rh = w / cols, h / rows
    for r in range(rows):
        for c in range(cols):
            x0, x1 = int(c * cw + cw * 0.18), int((c + 1) * cw - cw * 0.18); y0, y1 = int(r * rh + rh * 0.22), int((r + 1) * rh - rh * 0.18)
            glass = np.asarray((0.10, 0.13, 0.17), np.float32) * (0.8 + 0.4 * rng.random())
            alb[y0:y1, x0:x1] = glass
            if rng.random() < lit: em[y0:y1, x0:x1] = 0.6 + 0.4 * rng.random()
    return alb, em


def make_all(out_dir):
    os.makedirs(out_dir, exist_ok=True); p = lambda n: os.path.join(out_dir, n)
    specs = {"topsoil": ((86, 70, 54), 5, 0.14, 0.45, 1, 0.3), "clay1": ((96, 86, 78), 11, 0.12, 0.10, 2, 0.25), "aquifer": ((156, 146, 120), 6, 0.08, 0.70, 3, 0.2),
             "clay2": ((82, 74, 70), 13, 0.12, 0.10, 4, 0.25), "bedrock": ((58, 60, 66), 3, 0.14, 0.35, 5, 0.1)}
    for name, (base, bf, ba, gr, sd, wv) in specs.items():
        a, b = strata(base, bf, ba, gr, sd, wavy=wv); save(a, p(f"{name}.png")); save(b, p(f"{name}_bump.png"), "L")
    # city ground: concrete / asphalt mosaic with faint joints
    n = noise(1024, 1024, (8, 32, 128), (0.4, 0.4, 0.2), 9); a = np.stack([0.30 + 0.10 * n] * 3, -1) * np.asarray((1.0, 0.98, 0.95))
    j = (np.arange(1024) % 128 < 2); a[j, :] *= 0.6; a[:, j] *= 0.6; save(a, p("ground.png")); save(0.5 + 0.3 * (n - 0.5), p("ground_bump.png"), "L")
    for k in range(4):
        a, e = facade(20 + k, tint=[(0.66, 0.67, 0.68), (0.72, 0.68, 0.62), (0.55, 0.60, 0.66), (0.78, 0.78, 0.76)][k], lit=0.22)
        save(a, p(f"facade{k}.png")); save(np.stack([e * 1.0, e * 0.78, e * 0.5], -1), p(f"facade{k}_em.png"))
    # solar panel cells
    h, w = 256, 512; a = np.ones((h, w, 3), np.float32) * np.asarray((0.05, 0.08, 0.18)); a[(np.arange(h) % 32) < 2, :] = (0.5, 0.5, 0.55); a[:, (np.arange(w) % 32) < 2] = (0.5, 0.5, 0.55)
    save(a, p("panel.png"))
    return out_dir


if __name__ == "__main__":
    import sys; print(make_all(sys.argv[1]))
