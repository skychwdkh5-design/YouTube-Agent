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


def hud(img, T, shown, rate=None, alpha=1.0, playhead=True, note=0.0):
    """contact timeline: T = seconds from contact in NASA's reconstruction (None = this view has no clock).
    shown = number of EVENTS reached by the narration. Only the current stage is named; past stages keep a dot,
    later stages only a grey tick. The bar sits low, below the sampler head and the surface."""
    if alpha <= 0.01:
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x0, x1, y = 230, W - 190, 1000
    tmin, tmax = -1.0, 31.0
    X = lambda v: x0 + (x1 - x0) * (v - tmin) / (tmax - tmin)
    d.rounded_rectangle([x0 - 70, y - 66, x1 + 70, y + 46], 16, fill=(6, 12, 24, 150))
    d.line([(x0, y), (x1, y)], fill=(170, 180, 195, 150), width=3)
    if T is not None and playhead:
        d.line([(x0, y), (X(clamp(T, tmin, tmax)), y)], fill=TEAL, width=5)
    fs = font("Inter-SemiBold.otf", 18); fb = font("Inter-Black.otf", 30)
    cur = shown - 1
    for k, (v, name) in enumerate(EVENTS):
        if k < cur:      # past: small dim-yellow dot + seconds
            c = (220, 180, 70, 200); r = 6
        elif k == cur:   # current: big bright dot
            c = YEL; r = 11
        else:            # not reached yet: grey tick only
            c = (130, 138, 150, 150); r = 4
        d.ellipse([X(v) - r, y - r, X(v) + r, y + r], fill=c)
        d.text((X(v), y + 16), f"{v} s", font=fs, fill=c, anchor="ma")
    if cur >= 0:
        v, name = EVENTS[cur]
        anc = "lb" if cur == 0 else ("rb" if cur == len(EVENTS) - 1 else "mb")
        d.text((X(v) + {"lb": -10, "rb": 10, "mb": 0}[anc], y - 20), name, font=fb, fill=YEL, anchor=anc)
    if T is not None and playhead:
        px = X(clamp(T, tmin, tmax))
        d.rectangle([px - 2, y - 14, px + 2, y + 14], fill=TEAL)
    if alpha < 0.999:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(lay)
    if T is not None and playhead:
        sgn = "+" if T >= 0 else "−"
        w_, h_ = _pill(img, W - 40, 36, f"T ≈ {sgn}{abs(T):.1f} s", 40, anchor="r", alpha=alpha, wt="Inter-Black.otf",
                       bg=(6, 12, 24, 190), fg=YEL, pad=(20, 10))
        yy = 36 + h_ + 8
        if rate and rate < 0.95:
            _pill(img, W - 40, yy, f"SLOWED ×{rate:.2f}", 17, anchor="r", alpha=alpha, wt="Inter-SemiBold.otf",
                  bg=(6, 12, 24, 160), pad=(10, 6), radius=8)
            yy += 38
        if note > 0.01:
            _pill(img, W - 40, yy, "APPROX. TIME FROM CONTACT", 17, anchor="r", alpha=alpha * note, wt="Inter-SemiBold.otf",
                  bg=(6, 12, 24, 160), pad=(10, 6), radius=8)


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
    """painted rock/grain: fractal outline, faceted top-left light, speckle, rim light, dark contact edge."""
    S = 3
    s = int(r * 2 * S + 8)
    rng = np.random.default_rng(seed)
    n = int(rng.integers(6, 10))
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.25, 0.25)
        rr = r * S * rng.uniform(0.7, 0.98)
        pts.append((rr * math.cos(a), rr * math.sin(a) * rng.uniform(0.72, 0.95)))
    for lvl in range(2):  # midpoint displacement -> natural, chipped outline
        q = []
        amp = r * S * (0.13 if lvl == 0 else 0.06)
        for i in range(len(pts)):
            x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % len(pts)]
            q.append((x0, y0))
            q.append(((x0 + x1) / 2 + rng.uniform(-amp, amp), (y0 + y1) / 2 + rng.uniform(-amp, amp)))
        pts = q
    c0 = s / 2
    pts = [(c0 + x, c0 + y) for x, y in pts]
    base = np.array([(104, 96, 88), (88, 84, 80), (122, 110, 96), (74, 70, 68)][tone % 4], np.float32)
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # facets: fan from an off-centre apex; each facet lit by how much it faces the upper-left light
    apex = (c0 + rng.uniform(-0.25, 0.1) * r * S, c0 + rng.uniform(-0.25, 0.1) * r * S)
    for i in range(len(pts)):
        p0, p1 = pts[i], pts[(i + 1) % len(pts)]
        mx, my = (p0[0] + p1[0]) / 2 - apex[0], (p0[1] + p1[1]) / 2 - apex[1]
        ang = math.atan2(my, mx)
        lit = 0.78 + 0.36 * math.cos(ang - math.radians(-135)) + rng.uniform(-0.07, 0.07)
        col = tuple(int(np.clip(v * lit, 0, 255)) for v in base) + (255,)
        d.polygon([apex, p0, p1], fill=col)
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(S * 0.6))).astype(np.float32)
    a[..., 3] = np.asarray(im)[..., 3]
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    nx, ny = (x - c0) / (r * S), (y - c0) / (r * S)
    a[..., :3] *= np.clip(1.08 - 0.22 * (nx + ny) - 0.22 * (nx ** 2 + ny ** 2), 0.45, 1.3)[..., None]
    a[..., :3] *= (1 + 0.16 * (rng.random((s, s)).astype(np.float32) - 0.5))[..., None]  # mineral speckle
    alpha = a[..., 3] > 0
    er = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))) > 0
    edge = alpha & ~er
    rim = edge & ((nx + ny) < -0.2)
    a[edge & ~rim, :3] *= 0.42
    a[rim, :3] = a[rim, :3] * 0.55 + np.array([236, 214, 180], np.float32) * 0.45
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").resize((s // S, s // S), Image.LANCZOS)
    return paint_texture(im, seed + 3, 0.16, 1.0)


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
    """painted cross-section backdrop: deep sky, hazy far horizon with boulder silhouettes, textured cut face,
    and a blurred, darker back layer of grains behind the main (moving) layer."""
    g = vgradient(W, H, [(0, (6, 10, 22)), (0.42, (18, 24, 40)), (GROUND_Y / H, (34, 38, 52)),
                         (GROUND_Y / H + 0.001, (40, 34, 30)), (0.75, (26, 22, 20)), (1, (14, 12, 12))])
    a = np.asarray(g).astype(np.float32)
    n = fbm(W, H, 91, cells=(220, 80, 24, 7), weights=(0.4, 0.3, 0.2, 0.1)) - 0.5
    below = (np.arange(H)[:, None] >= GROUND_Y)
    a *= (1 + np.where(below, 0.45, 0.12) * n)[..., None]
    rng = np.random.default_rng(4)
    for _ in range(140):  # faint stars
        x, y = rng.integers(0, W), rng.integers(0, int(GROUND_Y * 0.8))
        a[y, x] = np.maximum(a[y, x], rng.uniform(90, 200))
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    # far horizon: low ridge + boulder silhouettes, hazy
    far = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(far)
    xs = np.arange(0, W + 40, 40)
    ridge = GROUND_Y - 34 + 14 * np.sin(xs / 210.0) + 9 * np.sin(xs / 77.0 + 1.3)
    d.polygon([(0, GROUND_Y + 2)] + [(float(x), float(yv)) for x, yv in zip(xs, ridge)] + [(W, GROUND_Y + 2)], fill=(44, 46, 60, 255))
    for k in range(16):
        bx = rng.uniform(0, W); br = rng.uniform(10, 34)
        spr = rock_sprite(int(br), 300 + k, 3)
        far.alpha_composite(spr, (int(bx - spr.width / 2), int(GROUND_Y - 30 - br * 0.6 + rng.uniform(-6, 6))))
    fa = np.asarray(far.filter(ImageFilter.GaussianBlur(2.2))).astype(np.float32)
    fa[..., :3] = fa[..., :3] * 0.45 + np.array([60, 66, 86], np.float32) * 0.55  # atmospheric fade toward the sky
    img.alpha_composite(Image.fromarray(np.clip(fa, 0, 255).astype(np.uint8), "RGBA"))
    # back grain layer (static, darker, softer)
    back = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for (x, y, r, i) in particles(11, False):
        spr = rock_sprite(max(5, int(r * 0.8)), (i * 7) % 23, (i + 1) % 4)
        back.alpha_composite(spr, (int(x + 9 - spr.width / 2), int(y - 6 - spr.height / 2)))
    ba = np.asarray(back.filter(ImageFilter.GaussianBlur(1.6))).astype(np.float32)
    ba[..., :3] *= 0.42
    img.alpha_composite(Image.fromarray(np.clip(ba, 0, 255).astype(np.uint8), "RGBA"))
    return img


def _grain_offset(x, y, r, i, hx, hy, hw, push):
    """continuous displacement of a grain by the sampler head (no hard edges in the falloff)."""
    if push <= 0 or hy <= GROUND_Y - 40:
        return 0.0, 0.0
    dx = x - hx
    reach = hw + r + 6
    over = max(0.0, reach - abs(dx))
    sgn = 1 if dx >= 0 else -1
    wv = smooth(clamp((hy + r - y) / 40.0 + 0.5))          # only grains beside/above the head's bottom are shoved sideways
    ox = sgn * over * (1.05 + 0.15 * (i % 3)) * wv
    oy = -over * 0.45 * clamp((hy - y) / 120 + 0.6) * wv
    ddx, ddy = dx, y - hy
    dist = math.hypot(ddx, ddy) + 1e-3
    infl = hw * 1.6
    k = 18 * smooth(clamp(1 - dist / infl))                 # soft radial compression around the head
    return (ox + ddx / dist * k) * push, (oy + ddy / dist * k) * push


DYN_HALF = 330  # grains farther than this from the head centre never move -> cached


@lru_cache(maxsize=8)
def _static_grains(seed, boulders, hx):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for (x, y, r, i) in particles(seed, boulders):
        if abs(x - hx) > DYN_HALF:
            spr = rock_sprite(int(r), i % 23, i % 4)
            lay.alpha_composite(spr, (int(x - spr.width / 2), int(y - spr.height / 2)))
    return lay


def draw_ground(img, hx, hy, hw, push=1.0, balls=0.0, wobble_t=0.0, boulders=False, seed=5):
    """draw the grain field; grains near the sampler head (centre hx, bottom hy, half-width hw) are pushed aside."""
    P = particles(seed, boulders)
    static = not wobble_t and balls <= 0.01
    if static:
        img.alpha_composite(_static_grains(seed, boulders, int(hx)))
    for (x, y, r, i) in P:
        if static and abs(x - hx) > DYN_HALF:
            continue
        ox, oy = _grain_offset(x, y, r, i, hx, hy, hw, push)
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
    a = np.asarray(im).astype(np.float32); a[..., :3] *= 0.88
    return paint_texture(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"), 31, 0.2, 1.6)


@lru_cache(maxsize=None)
def _arm_profile(w=30):
    """one row of a painted metal tube: light from the left, rim on the right."""
    x = np.linspace(-1, 1, w, dtype=np.float32)
    lam = np.clip(0.55 - 0.45 * x + 0.35 * np.sqrt(np.clip(1 - x ** 2, 0, 1)), 0.15, 1.2)
    rgb = np.array([186, 190, 198], np.float32)[None] * lam[:, None]
    rgb[-3:] = rgb[-3:] * 0.6 + 60
    return np.dstack([np.clip(rgb, 0, 255)[None], np.full((1, w, 1), 255, np.float32)])[0].astype(np.uint8)


def draw_sampler(img, hx, hy, w=240, ghost=False, arm_top=-40):
    head = head_sprite(w)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    y1 = hy - head.height + 6
    if y1 > arm_top:
        prof = _arm_profile()
        strip = Image.fromarray(np.repeat(prof[None], int(y1 - arm_top), axis=0), "RGBA")
        lay.alpha_composite(strip, (int(hx - 15), int(arm_top)))
        jy = y1 - 70
        if jy > arm_top + 10:  # wrist joint collar
            d.rounded_rectangle([hx - 21, jy, hx + 21, jy + 26], 6, fill=(150, 152, 160, 255))
            d.line([(hx - 19, jy + 4), (hx + 19, jy + 4)], fill=(214, 216, 222, 255), width=3)
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
    # the arm leaves the frame at the top (the spacecraft body is above, out of view); a soft contact shadow
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([hx - hw * 1.5, hy - 24, hx + hw * 1.5, hy + 30], fill=(0, 0, 0, 110))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    draw_sampler(img, hx, hy, 2 * hw)
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


# ---------------------------------------------------------------- chemistry epilogue (symbolic icons only)
def _sphere(r, col, S=3):
    s_ = int(r * 2 * S + 4)
    y, x = np.mgrid[0:s_, 0:s_].astype(np.float32)
    nx, ny = (x - s_ / 2) / (r * S), (y - s_ / 2) / (r * S)
    rr = nx ** 2 + ny ** 2
    nz = np.sqrt(np.clip(1 - rr, 0, 1))
    lam = np.clip(-0.45 * nx - 0.55 * ny + 0.7 * nz, 0, 1)
    rgb = np.array(col, np.float32) * (0.3 + 0.8 * lam[..., None]) + 255 * (lam[..., None] ** 16) * 0.55
    out = np.dstack([np.clip(rgb, 0, 255), (rr <= 1) * 255.0]).astype(np.uint8)
    return Image.fromarray(out, "RGBA").resize((s_ // S, s_ // S), Image.LANCZOS)


ATOM_COLS = [(200, 204, 210), (90, 96, 108), (220, 90, 80), (90, 140, 230)]


@lru_cache(maxsize=None)
def stick_icon(seed, size=136):
    """symbolic ball-and-stick cluster (NOT a real structure): a short random zig-zag chain with one side branch."""
    rng = np.random.default_rng(seed)
    S = size
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    n = int(rng.integers(4, 6))
    pts = []
    x, y, ang = S * 0.2, S * 0.55, rng.uniform(-0.4, 0.4)
    for k in range(n):
        pts.append((x, y))
        ang += (0.9 if k % 2 else -0.9) + rng.uniform(-0.2, 0.2)
        x += S * 0.17 * math.cos(ang); y += S * 0.17 * math.sin(ang)
    j = int(rng.integers(1, n - 1))
    br = (pts[j][0] + S * 0.04, pts[j][1] - S * 0.2)
    d = ImageDraw.Draw(im)
    bonds = [(pts[k], pts[k + 1]) for k in range(n - 1)] + [(pts[j], br)]
    for p0, p1 in bonds:
        d.line([p0, p1], fill=(150, 156, 168, 255), width=max(3, S // 22))
    for k, q in enumerate(pts + [br]):
        r = S * (0.075 if k < n else 0.06)
        spr = _sphere(r, ATOM_COLS[int(rng.integers(0, 4))])
        im.alpha_composite(spr, (int(q[0] - spr.width / 2), int(q[1] - spr.height / 2)))
    return im


@lru_cache(maxsize=None)
def ring_icon(nsides, fused=False, size=130, col=(110, 200, 196)):
    """symbolic ring icon (generic polygon with atom dots). Ring size only; atoms are not identified."""
    S = size
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy, R = S * (0.4 if fused else 0.5), S * 0.5, S * 0.27
    polys = [[(cx + R * math.cos(math.pi / 2 + 2 * math.pi * k / nsides), cy + R * math.sin(math.pi / 2 + 2 * math.pi * k / nsides))
              for k in range(nsides)]]
    if fused:
        a0, a1 = polys[0][4], polys[0][5]
        mx, my = (a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2
        ox, oy = mx - cx, my - cy; L = math.hypot(ox, oy)
        c2 = (mx + ox / L * R * 0.68, my + oy / L * R * 0.68)
        polys.append([a0, (c2[0] + (a0[0] - mx) * 0.2 + ox / L * R * 0.25, c2[1] + (a0[1] - my) * 0.2 + oy / L * R * 0.25 - R * 0.5),
                      (c2[0] + ox / L * R * 0.55, c2[1] + oy / L * R * 0.55),
                      (c2[0] + (a1[0] - mx) * 0.2 + ox / L * R * 0.25, c2[1] + (a1[1] - my) * 0.2 + oy / L * R * 0.25 + R * 0.5), a1])
    for poly in polys:
        d.line(poly + [poly[0]], fill=col + (255,), width=max(4, S // 18), joint="curve")
    for poly in polys:
        for q in poly:
            spr = _sphere(S * 0.06, (210, 214, 220))
            im.alpha_composite(spr, (int(q[0] - spr.width / 2), int(q[1] - spr.height / 2)))
    return im


@lru_cache(maxsize=None)
def _tinted(kind, key, mode):
    im = stick_icon(key) if kind == "a" else ring_icon(*key)
    a = np.asarray(im).astype(np.float32)
    if mode == "lit":
        a[..., :3] = a[..., :3] * 0.6 + np.array([255, 208, 90], np.float32) * 0.4
    elif mode == "dim":
        g = a[..., :3].mean(axis=2, keepdims=True)
        a[..., :3] = g * 0.55
        a[..., 3] *= 0.55
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


@lru_cache(maxsize=None)
def dish_sprite(w=620):
    """painted sample tray seen at an angle, heaped with dark grains."""
    h = int(w * 0.62)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([0, h * 0.30, w - 1, h - 1], fill=(64, 68, 76, 255))
    d.ellipse([w * 0.03, h * 0.31, w * 0.97, h * 0.93], fill=(150, 156, 166, 255))
    d.ellipse([w * 0.07, h * 0.36, w * 0.93, h * 0.88], fill=(34, 30, 28, 255))
    rng = np.random.default_rng(9)
    for i in range(420):
        ang = rng.uniform(0, 2 * math.pi); rr = math.sqrt(rng.uniform(0, 1))
        x = w / 2 + rr * w * 0.40 * math.cos(ang)
        y = h * 0.62 + rr * h * 0.22 * math.sin(ang) - (1 - rr) * h * 0.18
        spr = rock_sprite(int(rng.choice([4, 5, 6, 8, 10, 12])), i % 23, i % 4)
        im.alpha_composite(spr, (int(x - spr.width / 2), int(y - spr.height / 2)))
    a = np.asarray(im).astype(np.float32)
    xs = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    a[..., :3] *= np.clip(1.1 - 0.3 * xs, 0.6, 1.3)[..., None]
    return paint_texture(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"), 61, 0.14, 1.4)


@lru_cache(maxsize=None)
def bowl_sprite(w=560):
    h = int(w * 0.5)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.chord([0, -h * 0.9, w - 1, h - 1], 0, 180, fill=(120, 96, 64, 255))
    d.ellipse([0, 0, w - 1, h * 0.22], fill=(70, 54, 40, 255))
    a = np.asarray(im).astype(np.float32)
    xs = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    a[..., :3] *= np.clip(1.2 - 0.45 * xs - 0.25 * xs ** 2, 0.5, 1.4)[..., None]
    return paint_texture(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"), 63, 0.16, 1.2)


@lru_cache(maxsize=None)
def no_icon(kind, size=200):
    """symbolic organism (cell) or DNA icon, crossed out."""
    S = size
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if kind == "cell":
        d.ellipse([S * 0.14, S * 0.22, S * 0.86, S * 0.78], fill=(70, 150, 120, 255), outline=(150, 230, 190, 255), width=5)
        d.ellipse([S * 0.40, S * 0.38, S * 0.58, S * 0.56], fill=(40, 90, 80, 255))
    else:
        for k in range(2):
            ph = k * math.pi
            pts = [(S * 0.5 + S * 0.22 * math.sin(y / S * 4 * math.pi + ph), y) for y in np.linspace(S * 0.1, S * 0.9, 40)]
            d.line(pts, fill=(120, 170, 240, 255), width=7)
        for y in np.linspace(S * 0.16, S * 0.84, 9):
            x0 = S * 0.5 + S * 0.22 * math.sin(y / S * 4 * math.pi); x1 = S * 0.5 + S * 0.22 * math.sin(y / S * 4 * math.pi + math.pi)
            d.line([(x0, y), (x1, y)], fill=(200, 210, 230, 255), width=4)
    im = paint_texture(im, 64, 0.12, 1.2)
    d = ImageDraw.Draw(im)
    d.ellipse([S * 0.04, S * 0.04, S * 0.96, S * 0.96], outline=RED, width=12)
    d.line([(S * 0.18, S * 0.82), (S * 0.82, S * 0.18)], fill=RED, width=12)
    return im


def _chem_layout():
    """home positions: 20 amino-acid icons (5x4 grid), 5 nucleobase rings (row), 2 sugar rings."""
    am = [(740 + 200 * (k % 5), 240 + 140 * (k // 5)) for k in range(20)]
    nb = [(740 + 200 * k, 820) for k in range(5)]
    sg = [(980, 720), (1340, 720)]
    return am, nb, sg


def sc_chem(t, s, d, p):
    """sample -> symbolic molecule icons -> one short dated caption at a time. Icons are symbolic, never structures."""
    u = t - s
    bg = grains_bg(17)
    ox = int(100 + 60 * u / d); oy = int(30 + 30 * math.sin(u * 0.1))
    img = bg.crop((ox, oy, ox + W, oy + H)).copy()
    img.alpha_composite(Image.new("RGBA", (W, H), (6, 10, 20, 170)))
    T = lambda key: p[key] - s
    tj, t14, tn, td, ts_, tr, tg, tnot, tno, ti = (T(k) for k in ("t_jan", "t_14", "t_nuc", "t_dec", "t_sug", "t_rib",
                                                                   "t_glu", "t_not", "t_noorg", "t_ingr"))
    # 1. the sample dish: push-in, then it slides left and stays as the source of everything
    mv = smooth(seg(u, tj - 0.2, tj + 0.9))
    back = smooth(seg(u, ti - 0.2, ti + 0.8))
    sc = lerp(lerp(lerp(1.15, 1.3, smooth(seg(u, 0, tj))), 0.62, mv), 0.95, back)
    dish = dish_sprite()
    ds = dish.resize((int(dish.width * sc), int(dish.height * sc)), Image.LANCZOS)
    dx, dy = lerp(lerp(960, 330, mv), 960, back), lerp(560, 640, back)
    img.alpha_composite(ds, (int(dx - ds.width / 2), int(dy - ds.height / 2)))
    # 2. icons
    am, nb, sg = _chem_layout()
    bowl = (960, 660)  # the sample dish, back in the centre at the end
    focus_dec = smooth(seg(u, td, td + 0.6))           # older icons dim while the sugars are introduced
    focus_not = smooth(seg(u, tnot, tnot + 0.5))
    gather = [smooth(seg(u, ti + 0.1 + 0.02 * k, ti + 1.1 + 0.02 * k)) for k in range(27)]
    items = []
    for k, (x, y) in enumerate(am):
        a_in = smooth(seg(u, tj + 0.3 + 0.05 * k, tj + 0.7 + 0.05 * k))
        lit = k < 14 and u >= t14 + 0.06 * k
        mode = "lit" if lit else "dim" if u >= t14 + 0.9 else "n"
        items.append(("a", 300 + k, mode, x, y, a_in, 92, k))
    for k, (x, y) in enumerate(nb):
        a_in = smooth(seg(u, tn + 0.1 * k, tn + 0.45 + 0.1 * k))
        items.append(("r", (6, k % 2 == 0, 130, (110, 200, 196)), "n", x, y, a_in, 130, 20 + k))
    for k, ((x, y), tt) in enumerate(zip(sg, (tr, tg))):
        a_in = smooth(seg(u, ts_ - 0.3 + 0.2 * k, ts_ + 0.2 + 0.2 * k))
        items.append(("r", ((5, False, 190, (255, 196, 90)), (6, False, 190, (255, 196, 90)))[k], "n", x, y, a_in, 190, 25 + k))
    for kind, key, mode, x, y, a_in, size, k in items:
        if a_in <= 0.01:
            continue
        older = k < 25
        g = gather[k]
        alpha = a_in * lerp((1 - 0.45 * focus_dec * older) * (1 - 0.85 * focus_not), 1.0, g)
        scale = 1.0
        if older:  # earlier finds tuck up and shrink while the sugars are introduced
            cx, cy = 1140, 535
            x, y = lerp(x, cx + (x - cx) * 0.55, focus_dec), lerp(y, cy + (y - cy) * 0.55 - 170, focus_dec)
            scale = lerp(1.0, 0.6, focus_dec)
        bx = bowl[0] + ((k * 37) % 9 - 4) * 40; by = bowl[1] - 10 - (k % 3) * 22
        X, Y = lerp(x, bx, g), lerp(y, by, g) - 160 * math.sin(math.pi * g)
        scale = lerp(scale, 0.5 if size > 120 else 0.7, g)
        if a_in < 1:
            scale *= lerp(0.7, 1.0, a_in)
        im = _tinted(kind, key, mode)
        if scale != 1.0:
            im = im.resize((max(2, int(im.width * scale)), max(2, int(im.height * scale))), Image.BILINEAR)
        if alpha < 0.999:
            im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
        img.alpha_composite(im, (int(X - im.width / 2), int(Y - im.height / 2)))
    # sugar names on the word
    for (x, y), tt, name in zip(sg, (tr, tg), ("RIBOSE", "GLUCOSE")):
        chip(img, name, x, y + 108, alpha=fade(u, tt, tnot, 0.25, 0.35), size=30, accent=YEL)
    # 3. no organisms / no DNA
    a_no = fade(u, tno, ti + 0.4, 0.3, 0.4)
    for k, kind in enumerate(("cell", "dna")):
        if a_no > 0.01:
            ic = no_icon(kind).copy()
            ic.putalpha(ic.getchannel("A").point(lambda v, a_=a_no * smooth(seg(u, tno + 0.6 * k, tno + 0.6 * k + 0.3)): int(v * a_)))
            img.alpha_composite(ic, (int(960 + (k * 2 - 1) * 180 - 100), 420))
    # one caption at a time (bottom centre)
    caps = [(tj + 0.2, "JAN 2025 · 14 OF 20 AMINO ACIDS", YEL), (tn, "+ 5 NUCLEOBASES", TEAL),
            (td, "DEC 2025 · SUGARS", YEL), (tnot, "NOT EVIDENCE OF LIFE", (255, 120, 100, 255)),
            (tno, "NO ORGANISMS · NO DNA", (255, 120, 100, 255)), (ti, "CHEMICAL INGREDIENTS", YEL)]
    for k, (tc, text, acc) in enumerate(caps):
        end = caps[k + 1][0] if k + 1 < len(caps) else d + 1
        chip(img, text, W / 2, 960, alpha=fade(u, tc, end, 0.3, 0.2), size=46, accent=acc)
    _pill(img, W - 40, 36, "SYMBOLIC ICONS · NOT CHEMICAL STRUCTURES", 19, anchor="r", alpha=fade(u, tj + 0.3),
          wt="Inter-SemiBold.otf", bg=(6, 12, 24, 170), pad=(12, 7), radius=8)
    credit(img, "Findings reported by NASA, Jan and Dec 2025", fade(u, tj + 0.5))
    type_label(img, "illus", "SYMBOLIC", fade(u, 0.1))
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
