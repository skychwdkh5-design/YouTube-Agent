"""Taiga hero scene: painted layered forest at dawn, bolide streak, airburst, pressure wave, staggered tree fall.
The state is a pure function of the event time e (seconds after the burst), so shots can hold, play and rewind
the same scene (actual scene-state rewind, not a reversed clip). Illustration / reconstruction, not to scale."""
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from paint import (W, H, clamp, seg, smooth, ease_in, ease_out, lerp, mix, noise, fbm, paint_texture, vgradient,
                   glow_sprite, tree_sprite, stamp, add_glow, camera)

WW, WH = 2400, 1350           # world size (camera can zoom 1.25x without upscaling)
GZ = (1660, 300)              # burst point in world px (upper right, matches the thumbnail)
GROUND_Y = 900                # horizon of the near forest floor
V = 260.0                     # wave speed in world px per second (illustrative)
HAZE = (214, 150, 112)


@lru_cache(maxsize=1)
def sky():
    im = vgradient(WW, WH, [(0, (16, 30, 58)), (0.32, (52, 62, 96)), (0.55, (176, 112, 96)), (0.66, (238, 168, 112)), (1, (120, 84, 70))])
    im = paint_texture(im, 11, 0.06, 3.0)
    # painted cloud bands
    a = fbm(WW, WH, 21, cells=(300, 120, 40), weights=(0.5, 0.35, 0.15), aniso=5.0)
    band = np.clip((a - 0.52) * 4, 0, 1) * np.clip(1 - np.abs(np.linspace(-1, 1, WH)[:, None] + 0.25) * 2.2, 0, 1)
    arr = np.asarray(im).astype(np.float32)
    cloud = np.array((236, 170, 138), np.float32)
    arr = arr * (1 - 0.45 * band[..., None]) + cloud * 0.45 * band[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


def _ridge(seed, y0, amp, col, haze_u, rough=1.0):
    rng = np.random.default_rng(seed)
    xs = np.arange(WW)
    prof = y0 + amp * (np.sin(xs / 380 + seed) * 0.5 + np.sin(xs / 150 + seed * 2) * 0.25) + \
        rough * 18 * (noise(WW, 1, 40, seed)[0] - 0.5)
    im = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(0, WH)] + [(x, prof[x]) for x in range(0, WW, 4)] + [(WW, WH)], fill=mix(col, HAZE, haze_u) + (255,))
    return paint_texture(im, seed + 1, 0.08, 3.0), prof


@lru_cache(maxsize=1)
def far_layers():
    r1, _ = _ridge(3, 700, 30, (40, 52, 60), 0.55)
    r2, p2 = _ridge(5, 760, 22, (26, 44, 44), 0.35)
    # tiny tree serrations on the second ridge
    d = ImageDraw.Draw(r2)
    rng = np.random.default_rng(9)
    for x in range(0, WW, 7):
        h = rng.uniform(10, 26)
        y = p2[x] + 2
        d.polygon([(x - 4, y + 2), (x, y - h), (x + 4, y + 2)], fill=mix((26, 44, 44), HAZE, 0.35) + (255,))
    return r1, r2


TREE_VARIANTS = 10


@lru_cache(maxsize=None)
def tree(var, h, stripped=False, haze=0.0):
    base = mix((22, 56, 44), HAZE, haze)
    shade = mix((10, 26, 26), HAZE, haze * 0.8)
    return tree_sprite(h, 100 + var, base=base, shade=shade, lit_amt=0.35 * (1 - haze), stripped=stripped)


@lru_cache(maxsize=None)
def fallen_log(var, L):
    rng = np.random.default_rng(300 + var)
    im = Image.new("RGBA", (int(L) + 20, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line([(10, 22), (L, 20 + rng.uniform(-4, 4))], fill=(92, 64, 46, 255), width=max(3, int(L / 30)))
    for k in range(6):
        x = 10 + L * rng.uniform(0.1, 0.9)
        d.line([(x, 21), (x + rng.uniform(-14, 14), 21 - rng.uniform(5, 15))], fill=(70, 50, 36, 255), width=2)
    return paint_texture(im, 400 + var, 0.2, 1.0)


def _trees(seed, n, y0, y1, hmin, hmax, haze):
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        x = rng.uniform(-60, WW + 60)
        y = rng.uniform(y0, y1)
        u = (y - y0) / max(1, (y1 - y0))
        h = int(lerp(hmin, hmax, u) * rng.uniform(0.85, 1.15))
        out.append((y, x, h, int(rng.integers(TREE_VARIANTS)), haze * (1 - 0.6 * u)))
    out.sort()
    return out


@lru_cache(maxsize=1)
def mid_layer_pair():
    """mid forest band, standing and flattened versions (crossfaded behind the wave front)."""
    stand = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
    flat = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
    floor = vgradient(WW, WH - 780, [(0, mix((30, 52, 44), HAZE, 0.3)), (1, (18, 32, 26))]).convert("RGBA")
    floor = paint_texture(floor, 41, 0.12, 4.0)
    stand.alpha_composite(floor, (0, 780)); flat.alpha_composite(floor, (0, 780))
    df = ImageDraw.Draw(flat)
    for (y, x, h, var, hz) in _trees(7, 900, 770, 880, 40, 110, 0.32):
        stamp(stand, tree(var, h, False, round(hz, 2)), x, y)
        # flattened: log pointing away from ground zero, plus a few stripped survivors right under it
        if abs(x - GZ[0]) < 120:
            if var % 3 == 0:
                stamp(flat, tree(var, int(h * 0.7), True, round(hz, 2)), x, y)
        else:
            sgn = 1 if x > GZ[0] else -1
            L = h * 0.9
            log = fallen_log(var, int(L))
            if sgn < 0:
                log = log.transpose(Image.FLIP_LEFT_RIGHT)
            flat.alpha_composite(log, (int(x - (0 if sgn > 0 else L)), int(y - 22)))
    stand = paint_texture(stand, 51, 0.06, 2.0)
    flat = paint_texture(flat, 52, 0.06, 2.0)
    return stand, flat


@lru_cache(maxsize=1)
def hero_trees():
    rng = np.random.default_rng(77)
    trees = []
    for i in range(95):
        x = rng.uniform(-80, WW + 80)
        y = 905 + 435 * rng.random() ** 1.6
        u = (y - 905) / 435
        h = int(lerp(120, 520, u) * rng.uniform(0.85, 1.15))
        trees.append((y, x, h, int(rng.integers(TREE_VARIANTS))))
    trees.sort()
    return trees


@lru_cache(maxsize=1)
def ground_near():
    g = vgradient(WW, WH - 890, [(0, (58, 70, 50)), (0.4, (34, 50, 36)), (1, (14, 24, 18))]).convert("RGBA")
    g = paint_texture(g, 61, 0.28, 6.0)
    d = ImageDraw.Draw(g)
    rng = np.random.default_rng(62)
    for i in range(1400):  # moss, shrubs and dead grass strokes
        x = rng.uniform(0, WW); y = rng.uniform(0, WH - 890); L = 6 + y * 0.05
        c = [(86, 98, 58), (120, 96, 60), (40, 66, 44), (150, 120, 80)][i % 4]
        d.line([(x, y), (x + L * rng.uniform(1, 3), y - rng.uniform(0, 3))], fill=c + (int(90 + y * 0.2),), width=int(1 + y / 120))
    im = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
    im.alpha_composite(g, (0, 890))
    return im


FIRE = glow_sprite(512, (255, 150, 60), power=1.25, core=(255, 248, 225), seed=4, turb=0.35)
HALO = glow_sprite(512, (255, 180, 110), power=2.6)
SUN = glow_sprite(256, (255, 214, 150), power=2.0, core=(255, 250, 235))
STREAK_HEAD = glow_sprite(128, (255, 230, 190), power=1.5, core=(255, 255, 255))


def state(e):
    """everything visible as a function of event time e (s after the burst)."""
    s = {}
    s["streak"] = seg(e, -3.7, 0.0)                      # bolide path progress
    s["fire"] = smooth(seg(e, -0.05, 0.9)) * (1 - 0.35 * smooth(seg(e, 3.0, 9.0)))
    s["fire_size"] = lerp(60, 620, ease_out(seg(e, -0.05, 1.6))) + 50 * seg(e, 1.6, 9)
    s["flash"] = smooth(seg(e, -0.1, 0.35)) * (1 - smooth(seg(e, 0.35, 3.0)))
    s["wave_r"] = max(0.0, (e - 0.25) * V * 1.6)
    s["e"] = e
    return s


def fall_angle(x, y, e):
    """tree rotation (deg, ccw positive) when the pressure wave reaches it; away from ground zero."""
    dx = x - GZ[0]
    dist = math.hypot(dx, (y - GROUND_Y) * 2.2) + 520     # slant distance from the burst (burst is above ground)
    t_hit = (dist - 520) / V + 1.0
    u = ease_in(seg(e, t_hit, t_hit + 0.55))
    sgn = -1 if dx > 0 else 1                             # dx>0 -> falls to the right (clockwise, negative angle)
    if abs(dx) < 110:
        return 0.0, seg(e, t_hit, t_hit + 0.2)            # stripped, still standing
    return sgn * 84 * u, 0.0


def render(e, cam=(1200, 675, 1.0), shake=True, sun=True):
    """compose the world for event time e and return the camera view (RGB, W x H)."""
    s = state(e)
    cx, cy, z = cam
    if shake and 1.2 < e < 7:
        k = (1 - seg(e, 1.2, 7)) * 6
        cx += k * math.sin(e * 23.0) + k * 0.6 * math.sin(e * 41.0)
        cy += k * 0.7 * math.cos(e * 29.0)
    world = sky().copy()
    if sun:
        world = add_glow(world, SUN, 420, 720, 300, 0.85 * (1 - 0.5 * s["flash"]))
    # bolide streak (behind the far ridges' top edge, in the sky)
    if 0 < s["streak"] < 1.0 or (s["streak"] >= 1 and e < 0.4):
        p0 = (-200, -120); p1 = GZ
        u = s["streak"]
        hx, hy = lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u)
        lay = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        tail = 0.35
        tx, ty = lerp(p0[0], p1[0], max(0, u - tail)), lerp(p0[1], p1[1], max(0, u - tail))
        for wdt, a in ((26, 40), (14, 90), (6, 200)):
            d.line([(tx, ty), (hx, hy)], fill=(255, 214, 160, a), width=wdt)
        lay = lay.filter(ImageFilter.GaussianBlur(4))
        world.alpha_composite(lay)
        world = add_glow(world, STREAK_HEAD, hx, hy, 180 + 160 * u, 1.0)
    # fireball + halo
    if s["fire"] > 0.01:
        world = add_glow(world, HALO, GZ[0], GZ[1], s["fire_size"] * 3.0, 0.55 * s["fire"])
        world = add_glow(world, FIRE, GZ[0], GZ[1], s["fire_size"], 1.0 * s["fire"])
    # expanding pressure shell (sky part)
    if 0 < s["wave_r"] < 3200:
        r = s["wave_r"]
        lay = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        a = int(150 * (1 - seg(r, 0, 3200)))
        d.ellipse([GZ[0] - r, GZ[1] - r * 0.8, GZ[0] + r, GZ[1] + r * 0.8], outline=(255, 226, 180, a), width=int(10 + r / 90))
        lay = lay.filter(ImageFilter.GaussianBlur(6 + r / 200))
        world.alpha_composite(lay)
    r1, r2 = far_layers()
    stand, flat = mid_layer_pair()
    near = ground_near()
    # wave-front mask for the mid band: flattened where the wave has passed
    reach = max(0.0, (e - 1.0) * V) if e > 1.0 else -1
    layers = [(r1, 0.35), (r2, 0.55)]
    view = None
    out = None
    # composite with parallax: far layers move less than the camera
    def cam_for(p):
        return (WW / 2 + (cx - WW / 2) * p, WH / 2 + (cy - WH / 2) * p, 1 + (z - 1) * p)
    base = camera(world, *cam_for(0.15)).convert("RGBA")
    for lay, p in layers:
        base.alpha_composite(camera(lay, *cam_for(p)))
    if reach < 0:
        mid = stand
    else:
        m = np.zeros((1, WW), np.float32)
        xs = np.arange(WW)
        m[0] = np.clip(1 - (np.abs(xs - GZ[0]) - reach) / 140.0, 0, 1)
        mask = Image.fromarray((m * 255).astype(np.uint8), "L").resize((WW, WH))
        mid = Image.composite(flat, stand, mask)
    base.alpha_composite(camera(mid, *cam_for(0.8)))
    # dust band at the wave front (ground level)
    if 1.0 < e < 9:
        dl = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
        d = ImageDraw.Draw(dl)
        a = int(110 * (1 - seg(e, 5, 9)))
        for sgn in (-1, 1):
            x = GZ[0] + sgn * reach
            d.ellipse([x - 160, 760, x + 160, 900], fill=(214, 170, 130, a))
        dl = dl.filter(ImageFilter.GaussianBlur(30))
        base.alpha_composite(camera(dl, *cam_for(0.8)))
    # near ground + individual hero trees (rotate about their base when the wave arrives)
    nl = near.copy()
    for (y, x, h, var) in hero_trees():
        ang, strip = fall_angle(x, y, e)
        spr = tree(var, h, strip > 0.5, 0.0)
        stamp(nl, spr, x, y, angle=ang)
    base.alpha_composite(camera(nl, *cam_for(1.0)))
    img = base.convert("RGB")
    if s["flash"] > 0.01:  # exposure ramp, no hard strobe
        a = np.asarray(img).astype(np.float32)
        a = a + s["flash"] * (np.array((255, 214, 170), np.float32) - a) * 0.55
        img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return img
