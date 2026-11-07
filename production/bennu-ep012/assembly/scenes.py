"""EP012 overlays (labels, credits, chips, contact HUD) and the Orbital Atlas painted 2.5D illustrations.
Everything drawn here is original, generated in code; it is always labelled ILLUSTRATION on screen."""
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from paint import (W, H, clamp, seg, smooth, ease_out, lerp, mix, font, fbm, paint_texture, vgradient,
                   glow_sprite, add_glow, shadow_text)

WHITE = (246, 242, 232, 255)
YEL = (255, 204, 64, 255)
TEAL = (94, 214, 205, 255)
RED = (229, 72, 60, 255)
NAVY = (10, 18, 34)
KIND = {"real": ((96, 220, 130), "REAL IMAGES"), "video": ((96, 220, 130), "NASA VIDEO"),
        "anim": ((255, 176, 64), "NASA ANIMATION"), "model": ((255, 176, 64), "NASA DATA MODEL"),
        "illus": ((150, 170, 255), "ILLUSTRATION")}


# ---------------------------------------------------------------- overlays
def _pill(img, x, y, text, size, fg=WHITE, bg=(8, 14, 28, 200), anchor="l", alpha=1.0, wt="Inter-SemiBold.otf",
          dot=None, pad=(18, 11), radius=12):
    if alpha <= 0.01:
        return (0, 0)
    f = font(wt, size)
    d0 = ImageDraw.Draw(img)
    l, t, r, b = d0.textbbox((0, 0), text, font=f)
    dw = int(size * 0.9) if dot else 0
    w, h = r - l + pad[0] * 2 + dw, b - t + pad[1] * 2
    if anchor == "r":
        x -= w
    elif anchor == "c":
        x -= w / 2
    layer = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius, fill=bg)
    if dot:
        cy = h / 2; rr = size * 0.22
        d.ellipse([pad[0] - 2, cy - rr, pad[0] - 2 + 2 * rr, cy + rr], fill=dot + (255,))
    d.text((pad[0] + dw - l, pad[1] - t), text, font=f, fill=fg)
    if alpha < 0.999:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(layer, (int(x), int(y)))
    return (w, h)


def type_label(img, kind, extra, alpha=1.0):
    col, name = KIND[kind]
    txt = name + (" · " + extra if extra else "")
    _pill(img, 40, 36, txt, 25, dot=col, alpha=alpha, wt="Inter-Bold.otf")


def credit(img, text, alpha=1.0, top=False):
    if alpha <= 0.01 or not text:
        return
    if top:
        _pill(img, 40, 100, text, 19, fg=(225, 225, 225, 235), bg=(0, 0, 0, 120), alpha=alpha,
              wt="Inter-Medium.otf", pad=(12, 7), radius=8)
        return
    _pill(img, W - 36, H - 62, text, 19, fg=(225, 225, 225, 235), bg=(0, 0, 0, 120), anchor="r", alpha=alpha,
          wt="Inter-Medium.otf", pad=(12, 7), radius=8)


def chip(img, text, x, y, alpha=1.0, size=40, accent=None, anchor="c", sub=None):
    """caption chip; accent = colour bar on the left; optional smaller sub line."""
    if alpha <= 0.01:
        return
    yy = y + (1 - ease_out(alpha)) * 14
    w, h = _pill(img, x, yy, text, size, anchor=anchor, alpha=alpha, wt="Inter-Bold.otf", bg=(8, 14, 28, 215),
                 fg=accent or WHITE, pad=(24, 14))
    if sub:
        _pill(img, x, yy + h + 8, sub, int(size * 0.62), anchor=anchor, alpha=alpha, wt="Inter-SemiBold.otf",
              bg=(8, 14, 28, 190), pad=(18, 9))


def fade(t, t0, t1=None, fin=0.35, fout=0.35):
    a = smooth(seg(t, t0, t0 + fin))
    if t1 is not None:
        a *= 1 - smooth(seg(t, t1 - fout, t1))
    return a


EVENTS = [(0, "CONTACT"), (1, "NITROGEN RELEASE"), (6, "BACK-AWAY BURN"), (9, "DESCENT STOPPED"),
          (16, "SAMPLER CLEAR"), (30, "DRIFTING AWAY")]


def hud(img, T, shown, rate=None, alpha=1.0, playhead=True):
    """contact timeline: T = seconds from contact in NASA's reconstruction (None = this view has no clock).
    shown = number of EVENTS revealed so far (synced to the narration)."""
    if alpha <= 0.01:
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x0, x1, y = 200, W - 150, 985
    tmin, tmax = -1.0, 31.0
    X = lambda v: x0 + (x1 - x0) * (v - tmin) / (tmax - tmin)
    d.rounded_rectangle([x0 - 110, y - 84, x1 + 40, y + 52], 16, fill=(6, 12, 24, 170))
    d.line([(x0, y), (x1, y)], fill=(200, 210, 225, 200), width=4)
    if T is not None and playhead:
        d.line([(x0, y), (X(clamp(T, tmin, tmax)), y)], fill=TEAL, width=6)
    fs = font("Inter-SemiBold.otf", 19); fb = font("Inter-Bold.otf", 21)
    for k, (v, name) in enumerate(EVENTS):
        on = k < shown
        c = YEL if on else (150, 160, 175, 220)
        d.ellipse([X(v) - 8, y - 8, X(v) + 8, y + 8], fill=c)
        d.text((X(v), y + 16), f"{v} s", font=fs, fill=c, anchor="ma")
        if on:
            anc = {0: "rb", 1: "lb", 2: "rb", 3: "lb", 4: "mb", 5: "rb"}[k]
            d.text((X(v) + {"rb": 6, "lb": -6, "mb": 0}[anc], y - (50 if k in (1, 3) else 22)), name, font=fb, fill=WHITE, anchor=anc)
    if T is not None and playhead:
        px = X(clamp(T, tmin, tmax))
        d.polygon([(px - 11, y - 30), (px + 11, y - 30), (px, y - 12)], fill=TEAL)
    if alpha < 0.999:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(lay)
    if T is not None and playhead:
        sgn = "+" if T >= 0 else "−"
        f = font("Inter-Black.otf", 64)
        txt = f"T {sgn} {abs(T):04.1f} s"
        _pill(img, W - 40, 36, txt, 46, anchor="r", alpha=alpha, wt="Inter-Black.otf", bg=(6, 12, 24, 200), fg=YEL)
        sub = "TIME FROM CONTACT · APPROX."
        if rate and rate < 0.95:
            sub += f" · SLOWED ×{rate:.2f}"
        _pill(img, W - 40, 120, sub, 18, anchor="r", alpha=alpha, wt="Inter-SemiBold.otf", bg=(6, 12, 24, 170), pad=(12, 7))


def ring(img, x, y, r, alpha=1.0, color=YEL, width=6):
    if alpha <= 0.01:
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = color[:3] + (int(255 * alpha),)
    d.ellipse([x - r, y - r, x + r, y + r], outline=c, width=width)
    img.alpha_composite(lay)


def arrow(img, p0, p1, alpha=1.0, color=YEL, width=7, head=22):
    if alpha <= 0.01:
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = color[:3] + (int(255 * alpha),)
    d.line([p0, p1], fill=c, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    a1 = (p1[0] - head * math.cos(ang - 0.45), p1[1] - head * math.sin(ang - 0.45))
    a2 = (p1[0] - head * math.cos(ang + 0.45), p1[1] - head * math.sin(ang + 0.45))
    d.polygon([p1, a1, a2], fill=c)
    img.alpha_composite(lay)


# ---------------------------------------------------------------- painted primitives
@lru_cache(maxsize=None)
def space_bg(seed=3, tone=(10, 18, 36)):
    g = vgradient(W, H, [(0, (6, 10, 22)), (0.55, tone), (1, (14, 22, 40))]).convert("RGB")
    a = np.asarray(g).astype(np.float32)
    n = fbm(W, H, seed, cells=(420, 160, 60, 20), weights=(0.45, 0.3, 0.15, 0.1), aniso=1.8)
    neb = np.clip((n - 0.45) * 2.2, 0, 1)
    a += neb[..., None] * np.array([18, 34, 46], np.float32)
    rng = np.random.default_rng(seed)
    for _ in range(900):
        x, y = rng.integers(0, W), rng.integers(0, H)
        v = rng.random() ** 3 * 170 + 40
        a[y, x] = np.minimum(255, a[y, x] + v)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    return paint_texture(img, seed + 1, 0.06, 2.4).convert("RGBA")


@lru_cache(maxsize=None)
def sphere(size, kind, seed=1):
    S = 2; s = size * S
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    nx, ny = (x - s / 2) / (s / 2), (y - s / 2) / (s / 2)
    if kind == "bennu":  # spinning-top outline: slightly diamond-shaped
        rr = np.abs(nx) ** 1.75 + np.abs(ny) ** 1.75
        inside = rr <= 1.0
        nz = np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0, 1))
    else:
        rr = nx ** 2 + ny ** 2
        inside = rr <= 1.0
        nz = np.sqrt(np.clip(1 - rr, 0, 1))
    L = np.array([-0.55, -0.45, 0.70]); L /= np.linalg.norm(L)
    lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    n = fbm(s, s, seed, cells=(s / 4, s / 10, s / 26, s / 70), weights=(0.35, 0.3, 0.2, 0.15))
    rgb = np.zeros((s, s, 3), np.float32)
    if kind == "earth":
        land = n > 0.53
        ocean = np.array([28, 78, 150], np.float32); landc = np.array([176, 150, 96], np.float32)
        green = np.array([70, 120, 74], np.float32)
        base = np.where(land[..., None], np.where((n > 0.6)[..., None], landc, green), ocean)
        cloud = np.clip((fbm(s, s, seed + 9, cells=(s / 8, s / 20, s / 50), weights=(0.5, 0.3, 0.2), aniso=2.5) - 0.58) * 4, 0, 1)
        base = base * (1 - cloud[..., None] * 0.8) + 240 * cloud[..., None] * 0.8
        rgb = base * (0.12 + 0.95 * lam[..., None])
        rim = np.clip((rr - 0.82) / 0.18, 0, 1) * (lam > 0.05)
        rgb += rim[..., None] * np.array([60, 120, 200], np.float32) * 0.6
    else:
        rock = 70 + 90 * n
        boulders = np.clip((fbm(s, s, seed + 4, cells=(s / 30, s / 60), weights=(0.6, 0.4)) - 0.62) * 6, 0, 1)
        v = rock * (1 - 0.35 * boulders) + 30 * boulders
        rgb = np.stack([v * 1.0, v * 0.97, v * 0.92], -1) * (0.08 + 1.05 * lam[..., None])
    alpha = inside.astype(np.float32) * 255
    out = np.dstack([np.clip(rgb, 0, 255), alpha]).astype(np.uint8)
    im = Image.fromarray(out, "RGBA").resize((size, size), Image.LANCZOS)
    return paint_texture(im, seed + 2, 0.10, 1.6)


@lru_cache(maxsize=None)
def craft_sprite(scale=1.0, arm=1.0):
    """OSIRIS-REx-like silhouette, painted: gold-foil body, two grey panels, TAGSAM arm with round head.
    Origin = head bottom centre is returned too. Symbolic, not a measured model."""
    S = 2
    w, h = int(520 * scale * S), int((300 + 260 * arm) * scale * S)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = scale * S
    cx = w / 2
    by = 40 * k
    # panels
    for sgn in (-1, 1):
        x0 = cx + sgn * 70 * k; x1 = cx + sgn * 250 * k
        d.polygon([(x0, by + 30 * k), (x1, by + 6 * k), (x1, by + 86 * k), (x0, by + 96 * k)], fill=(70, 80, 96, 255))
        for j in range(1, 6):
            xx = lerp(x0, x1, j / 6)
            d.line([(xx, by + lerp(30, 6, j / 6) * k), (xx, by + lerp(96, 86, j / 6) * k)], fill=(40, 46, 58, 255), width=int(2 * k))
    # body
    d.rounded_rectangle([cx - 72 * k, by, cx + 72 * k, by + 150 * k], int(10 * k), fill=(196, 150, 70, 255))
    d.rectangle([cx - 72 * k, by + 110 * k, cx + 72 * k, by + 150 * k], fill=(150, 112, 52, 255))
    d.ellipse([cx - 40 * k, by - 30 * k, cx + 40 * k, by + 20 * k], fill=(214, 214, 210, 255))  # antenna dish
    # arm + head
    ay0 = by + 150 * k; ay1 = ay0 + 240 * arm * k
    d.rectangle([cx + 30 * k - 6 * k, ay0, cx + 30 * k + 6 * k, ay1], fill=(200, 200, 205, 255))
    hx = cx + 30 * k
    d.rounded_rectangle([hx - 34 * k, ay1, hx + 34 * k, ay1 + 26 * k], int(6 * k), fill=(226, 226, 230, 255))
    # light: warm from upper left
    a = np.asarray(im).astype(np.float32)
    xs = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    ys = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
    a[..., :3] *= np.clip(1.12 - 0.28 * (xs + ys), 0.6, 1.3)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").resize((w // S, h // S), Image.LANCZOS)
    im = paint_texture(im, 21, 0.14, 1.4)
    return im, (hx / S, (ay1 + 26 * k) / S)


@lru_cache(maxsize=None)
def rock_sprite(r, seed, tone=0):
    """painted rock/grain: irregular polygon, top-left light, dark rim, brush texture. r = radius px."""
    S = 3
    s = int(r * 2 * S + 6)
    rng = np.random.default_rng(seed)
    n = rng.integers(7, 12)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.2, 0.2)
        rr = r * S * rng.uniform(0.72, 1.0)
        pts.append((s / 2 + rr * math.cos(a), s / 2 + rr * math.sin(a) * rng.uniform(0.8, 1.0)))
    base = [(104, 96, 88), (88, 84, 80), (122, 110, 96), (74, 70, 68)][tone % 4]
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(im).polygon(pts, fill=base + (255,))
    a = np.asarray(im).astype(np.float32)
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    nx, ny = (x - s / 2) / (r * S), (y - s / 2) / (r * S)
    shade = np.clip(1.15 - 0.55 * (nx + ny) * 0.7 - 0.35 * (nx ** 2 + ny ** 2), 0.35, 1.35)
    a[..., :3] *= shade[..., None]
    alpha = a[..., 3] > 0
    er = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))) > 0
    edge = alpha & ~er
    a[edge, :3] *= 0.45
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").resize((s // S, s // S), Image.LANCZOS)
    return paint_texture(im, seed + 3, 0.18, 1.0)


BALL_COLS = [(226, 60, 52), (250, 196, 50), (60, 120, 222), (70, 176, 90), (238, 120, 40)]


@lru_cache(maxsize=None)
def ball_sprite(r, ci):
    S = 3; s = int(r * 2 * S + 4)
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    nx, ny = (x - s / 2) / (r * S), (y - s / 2) / (r * S)
    rr = nx ** 2 + ny ** 2
    inside = rr <= 1
    nz = np.sqrt(np.clip(1 - rr, 0, 1))
    lam = np.clip(-0.5 * nx - 0.5 * ny + 0.7 * nz, 0, 1)
    c = np.array(BALL_COLS[ci % len(BALL_COLS)], np.float32)
    rgb = c * (0.35 + 0.8 * lam[..., None]) + 255 * (lam[..., None] ** 18) * 0.7
    out = np.dstack([np.clip(rgb, 0, 255), inside * 255.0]).astype(np.uint8)
    return Image.fromarray(out, "RGBA").resize((s // S, s // S), Image.LANCZOS)


# ---------------------------------------------------------------- cross-section ground (loose particles)
GROUND_Y = 560


@lru_cache(maxsize=None)
def particles(seed=5, boulders=False):
    """loosely packed grains under the surface line: poisson-ish placement with deliberate gaps."""
    rng = np.random.default_rng(seed)
    pts = []
    grid = {}
    cs = 60

    def ok(x, y, r):
        gx, gy = int(x // cs), int(y // cs)
        for i in range(gx - 1, gx + 2):
            for j in range(gy - 1, gy + 2):
                for (px, py, pr) in grid.get((i, j), ()):
                    if (px - x) ** 2 + (py - y) ** 2 < (pr + r + 5) ** 2:
                        return False
        return True

    if boulders:
        for (bx, br) in ((300, 70), (560, 52), (1380, 64), (1640, 80), (1180, 40)):
            by = GROUND_Y - br * 0.35
            pts.append((bx, by, br)); grid.setdefault((int(bx // cs), int(by // cs)), []).append((bx, by, br))
    for _ in range(26000):
        r = float(rng.choice([7, 9, 11, 13, 16, 19, 23, 27], p=[.17, .17, .16, .14, .12, .10, .08, .06]))
        x = rng.uniform(-30, W + 30)
        y = rng.uniform(GROUND_Y + r * 0.2, H + 30)
        if ok(x, y, r):
            pts.append((x, y, r)); grid.setdefault((int(x // cs), int(y // cs)), []).append((x, y, r))
    return [(x, y, r, i) for i, (x, y, r) in enumerate(pts)]


@lru_cache(maxsize=None)
def ground_bg():
    g = vgradient(W, H, [(0, (8, 12, 24)), (GROUND_Y / H, (20, 26, 40)), (GROUND_Y / H + 0.001, (30, 26, 24)), (1, (16, 14, 14))])
    return paint_texture(g.convert("RGB"), 77, 0.10, 2.0).convert("RGBA")


def draw_ground(img, hx, hy, hw, push=1.0, balls=0.0, wobble_t=0.0, boulders=False, seed=5):
    """draw the grain field; grains near the sampler head (centre hx, bottom hy, half-width hw) are pushed aside."""
    P = particles(seed, boulders)
    for (x, y, r, i) in P:
        dx = x - hx
        ox, oy = 0.0, 0.0
        if push > 0 and hy > GROUND_Y - 40:
            reach = hw + r + 6
            if abs(dx) < reach and y < hy + r:
                s = 1 if dx >= 0 else -1
                over = reach - abs(dx)
                ox = s * over * (1.05 + 0.3 * (i % 3) / 2)
                oy = -over * 0.45 * clamp((hy - y) / 120 + 0.6)
            else:
                ddx, ddy = dx, y - hy
                dist = math.hypot(ddx, ddy) + 1e-3
                infl = hw * 1.25
                if dist < infl:
                    k = (infl - dist) / infl * 18
                    ox, oy = ddx / dist * k, ddy / dist * k
            ox *= push; oy *= push
        if wobble_t:
            ox += 2.0 * math.sin(wobble_t * 2.1 + i * 0.7); oy += 1.5 * math.cos(wobble_t * 1.7 + i * 1.3)
        X, Y = x + ox, y + oy
        if X < -40 or X > W + 40 or Y > H + 40:
            continue
        ri = int(r)
        spr = rock_sprite(ri, i % 23, i % 4)
        if balls > 0.01 and r < 40:
            b = ball_sprite(ri, i)
            if balls < 0.99:
                spr = Image.blend(spr, b, balls) if spr.size == b.size else b
            else:
                spr = b
        img.alpha_composite(spr, (int(X - spr.width / 2), int(Y - spr.height / 2)))


@lru_cache(maxsize=None)
def head_sprite(w=240):
    """TAGSAM head, side view: short wide metal drum with ribbing, painted. Bottom centre = anchor."""
    S = 2; ww, hh = int(w * S), int(w * 0.38 * S)
    im = Image.new("RGBA", (ww, hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, hh * 0.18, ww - 1, hh - 1], int(10 * S), fill=(206, 208, 214, 255))
    d.rectangle([ww * 0.04, hh * 0.32, ww * 0.96, hh * 0.80], fill=(160, 164, 172, 255))
    for j in range(1, 16):
        x = ww * (0.04 + 0.92 * j / 16)
        d.line([(x, hh * 0.32), (x, hh * 0.80)], fill=(120, 124, 134, 255), width=int(2 * S))
    d.rectangle([ww * 0.38, 0, ww * 0.62, hh * 0.2], fill=(186, 188, 194, 255))
    a = np.asarray(im).astype(np.float32)
    xs = np.linspace(-1, 1, ww, dtype=np.float32)[None, :]
    a[..., :3] *= np.clip(1.15 - 0.35 * xs - 0.25 * xs ** 2, 0.5, 1.4)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").resize((ww // S, hh // S), Image.LANCZOS)
    return paint_texture(im, 31, 0.12, 2.0)


def draw_sampler(img, hx, hy, w=240, ghost=False, arm_top=-40):
    head = head_sprite(w)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    if hy - head.height + 6 > arm_top:
        d.rectangle([hx - 13, arm_top, hx + 13, hy - head.height + 6], fill=(196, 198, 204, 255))
        d.rectangle([hx - 13, arm_top, hx - 5, hy - head.height + 6], fill=(150, 152, 160, 255))
    lay.alpha_composite(head, (int(hx - head.width / 2), int(hy - head.height)))
    if ghost:
        a = np.asarray(lay).astype(np.float32)
        a[..., 3] *= 0.35
        a[..., :3] = a[..., :3] * 0.3 + np.array([150, 170, 255]) * 0.7
        lay = Image.fromarray(a.astype(np.uint8), "RGBA")
    img.alpha_composite(lay)


def ground_label(img, t, start):
    type_label(img, "illus", "NOT TO SCALE", fade(t, start, None, 0.3))


# ---------------------------------------------------------------- scenes  (t = film time, s = shot start, d = shot length, p = params)
def sc_signal(t, s, d, p):
    """Earth -> Bennu signal delay, then the autonomous sequence. Symbolic distances."""
    u = t - s
    img = space_bg(3).copy()
    zoom = lerp(1.0, 1.0, 0)
    ex, ey = 300, 600
    bx, by = 1560, 520
    img.alpha_composite(sphere(300, "earth", 4), (ex - 150, ey - 150))
    img = add_glow(img, glow_sprite(256, (60, 120, 220)), ex, ey, 520, 0.35)
    img.alpha_composite(sphere(230, "bennu", 8), (bx - 115, by - 115))
    craft, (hxo, hyo) = craft_sprite(0.32, 0.8)
    cyo = by - 260 + 8 * math.sin(u * 0.8)
    t_up = p["t_auto"] - s
    if u > t_up:  # autonomous descent toward the surface
        k = smooth(seg(u, t_up + 0.6, d - 0.4))
        cyo = lerp(cyo, by - 185, k)
    img.alpha_composite(craft, (int(bx + 40 - hxo), int(cyo - hyo + craft.height * 0.0)))
    d0 = ImageDraw.Draw(img)
    # dashed path
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    pts = [(lerp(ex + 160, bx - 130, v), ey - 40 - math.sin(v * math.pi) * 120 - (ey - by) * v) for v in np.linspace(0, 1, 60)]
    for i in range(0, 59, 2):
        dl.line([pts[i], pts[i + 1]], fill=(150, 200, 220, 140), width=4)
    img.alpha_composite(lay)
    # travelling pulse
    tp0, tp1 = p["t_delay"] - s - 0.3, p["t_delay"] - s + 6.0
    if tp0 <= u <= tp1 + 3.5:
        v = smooth(seg(u, tp0, tp1))
        i = min(59, int(v * 59))
        img = add_glow(img, glow_sprite(128, (90, 230, 220), core=(240, 255, 255)), pts[i][0], pts[i][1], 90, 1.0)
        mins = 18.5 * v
        chip(img, f"{mins:4.1f} MIN", pts[i][0], pts[i][1] - 110, alpha=fade(u, tp0, tp1 + 3.5), size=44, accent=YEL)
    chip(img, "SIGNAL DELAY ≈ 18.5 MINUTES, ONE WAY", W / 2, 120, alpha=fade(u, p["t_delay"] - s + 0.3, p["t_slow"] - s + 2.2),
         size=40, sub="NASA ESTIMATE BEFORE THE EVENT")
    chip(img, "TOO SLOW TO STEER BY HAND", W / 2, 120, alpha=fade(u, p["t_slow"] - s + 2.3, t_up), size=44, accent=RED)
    chip(img, "AUTONOMOUS: COMMANDS UPLOADED IN ADVANCE", W / 2, 120, alpha=fade(u, t_up + 0.1, d + 1), size=42, accent=TEAL)
    shadow_text(img, (ex, ey + 190), "EARTH", font("Inter-Bold.otf", 34), WHITE, "ma", stroke=2, blur=6)
    shadow_text(img, (bx, by + 150), "BENNU", font("Inter-Bold.otf", 34), WHITE, "ma", stroke=2, blur=6)
    ground_label(img, u, 0.2)
    return img


def sc_cross(t, s, d, p):
    """cross-section of the loose surface with the sampler head. modes: depth / pit / notsolid."""
    u = t - s
    mode = p["mode"]
    img = ground_bg().copy()
    boulders = mode == "notsolid"
    hw = 120
    hx = 960
    if mode == "depth":
        hy = GROUND_Y + lerp(0, 230, smooth(seg(u, 0.2, 2.6)))
    elif mode == "pit":
        hy = GROUND_Y + lerp(-60, 200, smooth(seg(u, 1.0, 9.0)))
    else:
        hy = GROUND_Y + 200
    balls = 0.0
    if mode == "pit" and "t_balls" in p:
        tb = p["t_balls"] - s
        balls = smooth(seg(u, tb, tb + 0.9)) * (1 - smooth(seg(u, d - 1.0, d)))
    wob = u if mode in ("pit",) else 0.0
    draw_ground(img, hx, hy, hw, push=1.0, balls=balls, wobble_t=wob, boulders=boulders)
    draw_sampler(img, hx, hy, 2 * hw)
    # spacecraft body hint at the top
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    top = hy - 560
    dl.rounded_rectangle([hx - 240, top - 160, hx + 200, top], 14, fill=(170, 130, 62, 255))
    lay = paint_texture(lay, 41, 0.15, 1.4)
    img.alpha_composite(lay)
    f = font("Inter-SemiBold.otf", 26)
    shadow_text(img, (60, GROUND_Y - 44), "SURFACE", f, (220, 220, 220, 255), "lb", stroke=2, blur=5)
    if mode == "depth":
        a = smooth(seg(u, 2.0, 2.6))
        if a > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            c = YEL[:3] + (int(255 * a),)
            x = hx + hw + 90
            dl.line([(x, GROUND_Y), (x, hy)], fill=c, width=6)
            for yy in (GROUND_Y, hy):
                dl.line([(x - 22, yy), (x + 22, yy)], fill=c, width=6)
            dl.line([(0, GROUND_Y), (W, GROUND_Y)], fill=(255, 255, 255, int(90 * a)), width=2)
            img.alpha_composite(lay)
            chip(img, "NEARLY HALF A METER", x + 40, (GROUND_Y + hy) / 2 - 50, alpha=a, size=40, accent=YEL, anchor="l",
                 sub="≈ 1.5 FT · SAMPLER ARM DEPTH")
    if mode == "pit":
        chip(img, "LOOSELY PACKED", 470, 170, alpha=fade(u, p["t_loose"] - s, None), size=40, accent=YEL)
        chip(img, "WEAKLY BOUND", 1450, 170, alpha=fade(u, p["t_weak"] - s, None), size=40, accent=YEL)
        if balls > 0.02:
            chip(img, "LIKE A BALL PIT", W / 2, 290, alpha=balls, size=44, accent=WHITE)
    if mode == "notsolid":
        chip(img, "BOULDERS ON TOP ≠ SOLID ROCK BELOW", W / 2, 250, alpha=fade(u, 0.2, p["t_ghost"] - s), size=40, accent=YEL)
        tg = p["t_ghost"] - s
        if u > tg:
            k = smooth(seg(u, tg + 0.3, tg + 4.0))
            draw_sampler(img, hx, hy + 330 * k, 2 * hw, ghost=True, arm_top=hy - 40)
            chip(img, "WITHOUT THE BACK-AWAY BURN: KEPT SINKING", W / 2, 250, alpha=fade(u, tg + 0.2, None), size=38, accent=TEAL,
                 sub="NASA ANALYSIS · CONDITIONAL RESULT, NOT WHAT HAPPENED")
    ground_label(img, u, 0.2)
    return img


def sc_leak(t, s, d, p, real_frame):
    """left: real head image (passed in); right: painted inset diagram of the half-open flap."""
    u = t - s
    img = real_frame.convert("RGBA")
    # inset panel
    px0, py0, pw, ph = 1130, 170, 740, 700
    a = smooth(seg(u, 0.3, 1.0))
    panel = Image.new("RGBA", (pw, ph), (12, 20, 36, 235))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([0, 0, pw - 1, ph - 1], 22, outline=(150, 170, 255, 255), width=3)
    # collector ring cross-section
    cx, cy = pw / 2, ph / 2 + 40
    pd.rounded_rectangle([cx - 250, cy - 120, cx + 250, cy + 120], 30, fill=(170, 174, 182, 255))
    pd.rounded_rectangle([cx - 200, cy - 80, cx + 200, cy + 80], 20, fill=(40, 40, 46, 255))
    # sample inside
    rng = np.random.default_rng(3)
    for _ in range(160):
        x = rng.uniform(cx - 190, cx + 190); y = rng.uniform(cy - 70, cy + 72); r = rng.uniform(3, 8)
        pd.ellipse([x - r, y - r, x + r, y + r], fill=(int(rng.uniform(80, 120)),) * 3 + (255,))
    # flap (mylar) at the top opening, held slightly open by a wedged rock
    open_k = smooth(seg(u, 1.0, 2.5))
    ang = math.radians(16 * open_k)
    fx0, fy0 = cx - 120, cy - 80
    L = 240
    fx1, fy1 = fx0 + L * math.cos(ang), fy0 - L * math.sin(ang)
    pd.line([(fx0, fy0), (fx1, fy1)], fill=(230, 200, 120, 255), width=10)
    if u > p["t_rock"] - s:
        ka = smooth(seg(u, p["t_rock"] - s, p["t_rock"] - s + 0.6))
        rx, ry = fx0 + L * 0.82, fy0 - L * 0.82 * math.sin(ang) + 18
        r = rock_sprite(26, 7, 2)
        r2 = r.copy(); r2.putalpha(r.getchannel("A").point(lambda v: int(v * ka)))
        panel.alpha_composite(r2, (int(rx - r.width / 2), int(ry - r.height / 2)))
    # escaping particles through the gap
    for i in range(40):
        ph_ = (u * 0.35 + i / 40) % 1.0
        x = fx0 + L * (0.3 + 0.6 * ((i * 37) % 100) / 100) + 40 * ph_
        y = fy0 - 10 - 260 * ph_
        rr = 3 + (i % 3)
        al = int(255 * open_k * (1 - ph_))
        pd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(200, 200, 200, al))
    panel = paint_texture(panel, 51, 0.08, 2.0)
    fb = font("Inter-Bold.otf", 30); fs = font("Inter-SemiBold.otf", 24)
    pd = ImageDraw.Draw(panel)
    pd.text((30, 26), "SAMPLER HEAD · CUTAWAY", font=fb, fill=WHITE)
    pd.text((30, 66), "ILLUSTRATION · SIMPLIFIED", font=fs, fill=(170, 185, 255, 255))
    if open_k > 0.3:
        pd.text((fx1 + 20, fy1 - 10), "FLAP SLIGHTLY OPEN", font=fs, fill=YEL)
        pd.text((30, ph - 70), "PARTICLES ESCAPING THROUGH THE GAPS", font=fs, fill=WHITE)
    panel.putalpha(panel.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(panel, (px0, py0 + int((1 - a) * 20)))
    chip(img, "TEAM'S INTERPRETATION: LARGER ROCKS WEDGED IT OPEN", W / 2, 940, alpha=fade(u, p["t_rock"] - s, None), size=34, accent=YEL)
    return img


def sc_release(t, s, d, p):
    u = t - s
    img = space_bg(9, (12, 20, 40)).copy()
    # Earth limb lower left
    e = sphere(1300, "earth", 6)
    img.alpha_composite(e, (-700, 560))
    img = add_glow(img, glow_sprite(256, (70, 130, 230)), -50, 1210, 1500, 0.30)
    craft, (hxo, hyo) = craft_sprite(0.42, 0.25)
    k = smooth(seg(u, 0.3, d))
    cx, cy = lerp(1100, 1500, k), lerp(330, 210, k)
    img.alpha_composite(craft, (int(cx - craft.width / 2), int(cy - craft.height / 2)))
    # capsule: small rounded cone heading to Earth
    cap = Image.new("RGBA", (90, 70), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap)
    cd.polygon([(10, 60), (80, 60), (60, 10), (30, 10)], fill=(214, 206, 186, 255)); cd.ellipse([8, 52, 82, 68], fill=(150, 120, 80, 255))
    cap = paint_texture(cap, 61, 0.12, 1.2)
    kc = smooth(seg(u, 0.8, d))
    capx, capy = lerp(1050, 520, kc), lerp(420, 760, kc)
    img.alpha_composite(cap, (int(capx - 45), int(capy - 35)))
    chip(img, "SPACECRAFT: DID NOT RETURN", 1480, 470, alpha=fade(u, 0.4, None), size=32)
    chip(img, "CAPSULE ONLY → EARTH", 640, 600, alpha=fade(u, 1.2, None), size=34, accent=YEL)
    type_label(img, "illus", "NOT TO SCALE", fade(u, 0.1))
    return img


@lru_cache(maxsize=None)
def grains_bg(seed=13):
    img = Image.new("RGBA", (W + 200, H + 120), (22, 18, 16, 255))
    rng = np.random.default_rng(seed)
    for i in range(2600):
        r = int(rng.choice([6, 9, 12, 16, 22, 30]))
        x, y = rng.uniform(0, W + 200), rng.uniform(0, H + 120)
        spr = rock_sprite(r, i % 23, i % 4)
        img.alpha_composite(spr, (int(x - spr.width / 2), int(y - spr.height / 2)))
    a = np.asarray(img).astype(np.float32)
    yy = np.linspace(0, 1, a.shape[0])[:, None]
    a[..., :3] *= (0.55 + 0.25 * yy)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(1.2))


def sc_mass(t, s, d, p):
    u = t - s
    bg = grains_bg()
    ox = int(60 + 60 * math.sin(u * 0.15)); oy = int(40 + 20 * u / d)
    img = bg.crop((ox, oy, ox + W, oy + H)).copy()
    img.alpha_composite(Image.new("RGBA", (W, H), (6, 10, 20, 150)))
    base = 900; scale = 4.4
    bars = [("MINIMUM NEEDED", 60.0, p["t_min"] - s, (150, 160, 180)), ("DELIVERED", 121.6, 0.4, YEL[:3])]
    xs = [700, 1220]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    for (name, g, t0, col), x in zip(bars, xs):
        k = smooth(seg(u, t0, t0 + 1.6))
        hgt = g * scale * k
        if k > 0:
            dl.rounded_rectangle([x - 120, base - hgt, x + 120, base], 14, fill=col + (255,))
    lay = paint_texture(lay, 71, 0.16, 1.0)
    img.alpha_composite(lay)
    fb = font("Inter-Black.otf", 64); fm = font("Inter-Bold.otf", 30)
    for (name, g, t0, col), x in zip(bars, xs):
        k = smooth(seg(u, t0, t0 + 1.6))
        if k > 0.02:
            val = f"{g * k:.1f} g" if g != 60 else f"{60 * k:.0f} g"
            shadow_text(img, (x, base - g * scale * k - 20), val, fb, WHITE, "mb", stroke=3, blur=8)
            shadow_text(img, (x, base + 24), name, fm, WHITE, "ma", stroke=2, blur=6)
    chip(img, "≈ 4.3 OZ", 1220 + 170, base - 121.6 * scale + 40, alpha=fade(u, p["t_oz"] - s, None), size=34, anchor="l")
    chip(img, "ABOUT TWICE THE MINIMUM", W / 2, 120, alpha=fade(u, p["t_twice"] - s, None), size=44, accent=YEL,
         sub="121.6 g ÷ 60 g ≈ 2.03 · NASA-REPORTED MASS")
    type_label(img, "illus", "CHART", fade(u, 0.1))
    return img


def sc_chem(t, s, d, p):
    u = t - s
    bg = grains_bg(17)
    ox = int(100 + 80 * u / d); oy = int(30 + 40 * math.sin(u * 0.1))
    img = bg.crop((ox, oy, ox + W, oy + H)).copy()
    img.alpha_composite(Image.new("RGBA", (W, H), (6, 10, 20, 135)))
    y0 = 220
    cards = [("JANUARY 2025", "14 of the 20 amino acids life on Earth uses", "+ five nucleobases", p["t_jan"], p["t_nuc"]),
             ("DECEMBER 2025", "Sugars, including ribose and glucose", None, p["t_dec"], None)]
    for k, (hdr, l1, l2, ta, tb) in enumerate(cards):
        a = fade(t, ta)
        if a <= 0.01:
            continue
        x = 180 + (1 - ease_out(a)) * -60
        y = y0 + k * 270
        pw, ph = 1200, 220
        panel = Image.new("RGBA", (pw, ph), (10, 18, 34, 225))
        pd = ImageDraw.Draw(panel)
        pd.rounded_rectangle([0, 0, pw - 1, ph - 1], 20, outline=YEL[:3] + (255,), width=3)
        pd.text((36, 26), hdr, font=font("Inter-Black.otf", 38), fill=YEL)
        pd.text((36, 86), l1, font=font("Inter-Bold.otf", 44), fill=WHITE)
        if l2 and t >= tb:
            pd.text((36, 146), l2, font=font("Inter-Bold.otf", 40), fill=(200, 230, 230, 255))
        panel = paint_texture(panel, 81 + k, 0.06, 2.0)
        panel.putalpha(panel.getchannel("A").point(lambda v: int(v * a)))
        img.alpha_composite(panel, (int(x), int(y)))
    chip(img, "WHAT SCIENTISTS FOUND IN THE SAMPLE", W / 2, 90, alpha=fade(u, 0.2), size=40, accent=YEL)
    a = fade(t, p["t_not"])
    if a > 0.01:
        chip(img, "NOT EVIDENCE OF LIFE", W / 2, 780, alpha=a, size=50, accent=(255, 120, 100, 255))
    chip(img, "NO ORGANISMS · NO DNA", W / 2, 880, alpha=fade(t, p["t_noorg"], p["t_ingr"]), size=36)
    chip(img, "CHEMICAL INGREDIENTS", W / 2, 880, alpha=fade(t, p["t_ingr"]), size=36, accent=YEL)
    credit(img, "Findings reported by NASA, Jan 2025 and Dec 2025", fade(u, 0.5))
    type_label(img, "illus", "SUMMARY OF REPORTED FINDINGS", fade(u, 0.1))
    return img


def sc_end(t, s, d, p):
    u = t - s
    img = space_bg(21).copy()
    img = add_glow(img, glow_sprite(256, (40, 90, 160)), W / 2, 420, 900, 0.35)
    a = fade(u, 0.2)
    shadow_text(img, (W / 2, 300), "ORBITAL ATLAS", font("Inter-Black.otf", 110), WHITE[:3] + (int(255 * a),), "ma", stroke=4, blur=12)
    lines = ["Imagery & animations: NASA / Goddard / University of Arizona · NASA Goddard CI Lab",
             "NASA Scientific Visualization Studio (data: NASA/UA/CSA/York University/Open University/MDA)",
             "Illustrations: Orbital Atlas · Narration: synthetic voice (ElevenLabs)",
             "No NASA endorsement implied."]
    f = font("Inter-Medium.otf", 30)
    for i, l in enumerate(lines):
        aa = fade(u, 0.6 + 0.25 * i)
        shadow_text(img, (W / 2, 520 + 56 * i), l, f, (220, 226, 236, int(255 * aa)), "ma", stroke=1, blur=4)
    return img
