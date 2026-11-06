"""EP011 opening (0-12 s) built from the owner's new cover (cover_v2.png), used by build.py.

Frame 0 = the cover. The plate then comes alive: drifting smoke, flickering glow and heat shimmer on the fireball, and a
2.5D push toward the epicenter (rows lower in the frame are nearer, so they move faster). The push ends in the fireball's
glow, which dissolves into the existing film at 11.5-12.0 s (the scripted burst at 12.3 s follows).
The cover's inset photograph is replaced by the real May 1929 Kulik expedition photo in the same frame, so no invented
archive image appears in the film."""
import os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from paint import W, H, smooth, seg, fbm, lerp

HERE = os.path.dirname(os.path.abspath(__file__))
COVER = os.path.join(HERE, "..", "thumbs", "cover_v2.png")
ARCHIVE = os.path.join(HERE, "..", "sources", "kulik_1929_nasa_eo.jpg")
SX = W / 1672.0                                   # cover pixels -> film pixels (1672x941 -> 1920x1080)
EPI = (1225 * SX, 405 * SX)                       # base of the fireball, in film pixels
INSET = [(60, 655), (712, 600), (725, 868), (100, 915)]   # inner photo quad of the cover's inset (cover pixels)
T_END, XF0 = 12.0, 11.5


@lru_cache(maxsize=1)
def plate():
    im = Image.open(COVER).convert("RGB")
    # real 1929 photo, toned like the inset, warped into the inset's photo area
    ar = Image.open(ARCHIVE).convert("L")
    ar = ImageOps.colorize(ImageOps.autocontrast(ar, cutoff=2), (28, 20, 14), (232, 214, 182), mid=(118, 96, 74))
    ar = ar.crop((int(ar.width * 0.08), int(ar.height * 0.05), int(ar.width * 0.95), int(ar.height * 0.95)))
    xs = [p[0] for p in INSET]; ys = [p[1] for p in INSET]
    bx0, by0, bx1, by1 = min(xs), min(ys), max(xs), max(ys)
    bw, bh = bx1 - bx0, by1 - by0
    # QUAD maps the output box corners (UL, LL, LR, UR) to source points; we want the inverse: source rect -> quad,
    # so solve with a mesh: output box pixel -> bilinear position in the archive image
    q = [(x - bx0, y - by0) for x, y in INSET]
    yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
    # invert the bilinear quad by Newton iterations (few steps are enough for a near-rectangle)
    u = xx / bw; v = yy / bh
    P = np.array(q, np.float32)
    for _ in range(8):
        x = (1 - u) * (1 - v) * P[0, 0] + u * (1 - v) * P[1, 0] + u * v * P[2, 0] + (1 - u) * v * P[3, 0]
        y = (1 - u) * (1 - v) * P[0, 1] + u * (1 - v) * P[1, 1] + u * v * P[2, 1] + (1 - u) * v * P[3, 1]
        dxu = (1 - v) * (P[1, 0] - P[0, 0]) + v * (P[2, 0] - P[3, 0]); dxv = (1 - u) * (P[3, 0] - P[0, 0]) + u * (P[2, 0] - P[1, 0])
        dyu = (1 - v) * (P[1, 1] - P[0, 1]) + v * (P[2, 1] - P[3, 1]); dyv = (1 - u) * (P[3, 1] - P[0, 1]) + u * (P[2, 1] - P[1, 1])
        det = dxu * dyv - dxv * dyu
        ex, ey = xx - x, yy - y
        u = u + (ex * dyv - ey * dxv) / det; v = v + (ey * dxu - ex * dyu) / det
    a = np.asarray(ar).astype(np.float32)
    sx = np.clip(u, 0, 1) * (ar.width - 1); sy = np.clip(v, 0, 1) * (ar.height - 1)
    patch = a[sy.astype(int), sx.astype(int)]
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).polygon(q, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.5))
    im.paste(Image.fromarray(patch.astype(np.uint8)), (bx0, by0), mask)
    im = im.resize((W, H), Image.LANCZOS)
    return np.asarray(im).astype(np.float32)


@lru_cache(maxsize=1)
def masks():
    a = plate()
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1)
    fire = np.clip((r - 150) / 80, 0, 1) * np.clip((r - b - 70) / 80, 0, 1)        # bright orange/yellow pixels
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    region = np.clip(1 - np.hypot((xx - EPI[0]) / 520, (yy - (EPI[1] - 120)) / 420), 0, 1)
    fire = (fire * np.clip(region * 2.2, 0, 1)).astype(np.float32)
    fire = np.asarray(Image.fromarray((fire * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
    depth = np.clip((yy - 470) / 610, 0, 1) ** 1.2                                   # 0 = horizon/sky, 1 = nearest forest
    haze = np.clip(1 - np.abs(yy - 520) / 260, 0, 1) * np.clip(1 - np.abs(xx - EPI[0]) / 1100, 0, 1)
    return fire, depth.astype(np.float32), haze.astype(np.float32)


@lru_cache(maxsize=4)
def smoke_tex(k):
    return fbm(W + 400, H + 200, 700 + k, cells=(260, 110, 45), weights=(0.5, 0.33, 0.17), aniso=2.5)


def camera_state(t):
    u1 = smooth(seg(t, 0.6, 9.0)); u2 = smooth(seg(t, 9.0, 11.9))
    z = 1.0 + 0.62 * u1 + 0.75 * u2
    cx = lerp(W / 2, EPI[0], smooth(seg(t, 0.6, 7.5)))
    cy = lerp(H / 2, EPI[1] + 40, smooth(seg(t, 0.6, 7.5)))
    zmin = 1 + (z - 1) * 0.88                      # the least-zoomed (sky) plane must still cover the frame
    hw, hh = W / 2 / zmin, H / 2 / zmin
    cx = min(max(cx, hw), W - hw); cy = min(max(cy, hh), H - hh)
    return z, cx, cy


def remap(a, sx, sy):
    sx = np.clip(sx, 0, W - 1.001); sy = np.clip(sy, 0, H - 1.001)
    x0 = sx.astype(np.int32); y0 = sy.astype(np.int32); fx = (sx - x0)[..., None]; fy = (sy - y0)[..., None]
    return ((a[y0, x0] * (1 - fx) + a[y0, x0 + 1] * fx) * (1 - fy) + (a[y0 + 1, x0] * (1 - fx) + a[y0 + 1, x0 + 1] * fx) * fy)


@lru_cache(maxsize=1)
def grid():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return xx, yy


def frame(t):
    """RGB PIL image for 0 <= t < 12 (the dissolve into the existing film is done by build.py)."""
    a = plate(); fire, depth, haze = masks()
    xx, yy = grid()
    if t <= 0.0:
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    live = smooth(seg(t, 0.25, 1.6))
    z, cx, cy = camera_state(t)
    # 2.5D push: nearer rows (depth) zoom a little more than the sky/fireball plane
    zl = 1 + (z - 1) * (0.88 + 0.30 * depth)
    sx = cx + (xx - W / 2) / zl; sy = cy + (yy - H / 2) / zl
    # heat shimmer on the fireball
    sh = 2.2 * live * fire
    sx = sx + sh * np.sin(yy / 23.0 + t * 7.0); sy = sy + sh * 0.6 * np.cos(xx / 31.0 + t * 5.3)
    img = remap(a, sx, sy)
    fz = remap(fire[..., None], sx, sy)[..., 0]
    hz = remap(haze[..., None], sx, sy)[..., 0]
    # glow flicker and slow bloom
    flick = 1 + live * (0.06 * np.sin(t * 9.1) + 0.04 * np.sin(t * 15.7 + 1.3))
    img = img * (1 + (flick - 1) * fz[..., None]) + live * 22 * fz[..., None] * np.array((1.0, 0.75, 0.4), np.float32)
    # drifting smoke: two noise layers moving away from the epicenter
    s1 = smoke_tex(0); s2 = smoke_tex(1)
    o1 = int(t * 26) % 380; o2 = int(t * 14) % 180
    sm = 0.6 * s1[100 - o2 // 2:100 - o2 // 2 + H, 200 + o1 // 2 - 100:200 + o1 // 2 - 100 + W] + \
        0.4 * s2[o2:o2 + H, 380 - o1:380 - o1 + W]
    sm = np.clip((sm - 0.48) * 3.0, 0, 1) * hz * live * 0.55
    img = img * (1 - sm[..., None]) + sm[..., None] * np.array((214, 196, 178), np.float32)
    # final bloom toward the fireball's light before the dissolve
    b = smooth(seg(t, 9.6, 11.9))
    if b > 0:
        rr = np.hypot(xx - W / 2, yy - H / 2 + 60) / 900
        k = b * np.clip(1.15 - rr, 0, 1)[..., None]
        img = img + k * (np.array((255, 222, 176), np.float32) - img) * 0.85
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
