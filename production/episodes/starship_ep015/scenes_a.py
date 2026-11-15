"""EP015 scenes 1-4: hook (cover -> re-entry -> flip -> arms), ship vs booster split,
launch rewind, stage separation."""
from common import *   # noqa

# ------------------------------------------------------------------ 1. HOOK
H_PLASMA = c('It falls through') - 0.15
H_FLIP = c('flips upright') - 0.1
H_AIM = c('aims for') - 0.05
H_NORUN = c('No runway') - 0.05
H_NOLEG = c('No landing legs') - 0.05
H_ARMS = c('Just two enormous') - 0.1
H_END = c('On November fourteenth, twenty') - 0.2

COVER_CAM = (1420.0, 380.0, 2.05)


def cover_ship_y(t):
    """ship height above the arms during the opening tease (world y of its centre)"""
    x, y = ship_catch_xy()
    return x, y - 175 + 70 * rng(t, 0, H_PLASMA) + 5 * math.sin(t * 2.1)


def hook_cover(cv, t):
    """frame 0 = the cover. Movement starts at frame 1: title lifts out, the ship keeps
    descending toward the open arms, the camera pulls back and tilts down."""
    u = rng(t, 0.03, H_PLASMA)
    cam = Cam(lerp(COVER_CAM[0], 1560, u), lerp(COVER_CAM[1], 450, u), lerp(COVER_CAM[2], 1.5, u ** 0.8),
              shake=1.2 * (1 - u) * min(1, t * 8), t=t)
    sx, sy = cover_ship_y(t)
    pp, k, m = catch_set(cv, t, cam, (sx, sy), 0.0, 1.0, plume_k=1.0, light=0.85, kind='night', plume_len=2.4)
    cv.glow(pp[0], pp[1] + 260 * cam.z, 520 * cam.z, (255, 150, 60), 0.35)
    v = Vec()
    # title (cover text): exits upward/fades from frame 1
    a = 1 - smooth(t / 0.55)
    dy = -90 * smooth(t / 0.55)
    if a > 0.003:
        v.text('THEY', 70, 300 + dy, TITLE_BIG, (255, 255, 255), 'b', 'ls', a, 12, (0, 0, 0))
        v.text('CAUGHT IT', 74, 300 + TITLE_GAP + dy, TITLE_SMALL, YELLOW, 'b', 'ls', a, 11, (0, 0, 0))
    v.onto(cv)
    # cover grade (channel thumbnail standard: strong contrast, saturated); eases out with the pull-back
    g = 1 - smooth(u)
    if g > 0.002:
        lum = cv.a.mean(axis=2, keepdims=True)
        cv.a = lum + (cv.a - lum) * (1 + COVER_SAT * g)
        cv.a = COVER_PIV + (cv.a - COVER_PIV) * (1 + COVER_CON * g)


TITLE_BIG, TITLE_SMALL, TITLE_GAP = 245, 136, 172
COVER_SAT, COVER_CON, COVER_PIV = 0.30, 0.70, 70.0


def hook_plasma(cv, t):
    """re-entry close-up: belly first, plasma building, the ship slowing (camera shake fades)"""
    u = (t - H_PLASMA) / (H_FLIP - H_PLASMA)
    cv.a[:] = sky('high') * 0.55
    cv.a += starfield(5) * 0.5
    # curved Earth limb at the bottom
    v = Vec()
    pts = v.arc_pts(960, 2900, 2600, 2000, 200, 340)
    v.poly(pts + [(W, H), (0, H)], (16, 40, 86))
    v.line(pts, (120, 190, 255), 6, 0.8)
    v.onto(cv)
    cv.glow(960, 980, 900, (60, 130, 255), 0.25, 1.2)
    heat = 0.55 + 0.45 * smooth(u * 1.5)
    spr, m = ship_sprite(SHIP_BASE, round(heat, 1))
    x, y = 960 + 30 * math.sin(t * 1.3), 470 + 60 * u
    ang = -78 + 4 * math.sin(t * 2.0)
    # plasma sheath: streaks flowing past the belly (belly faces down-left)
    r = np.random.default_rng(9)
    v = Vec()
    for i in range(46):
        ph = (t * (1.6 + r.random()) + r.random()) % 1
        yy = 300 + r.random() * 420
        xx = 1500 - ph * 1400
        L = 120 + r.random() * 260
        v.line([(xx, yy), (xx + L, yy - 30)], (255, 170 + int(60 * r.random()), 90), 2 + 3 * r.random(), 0.25 + 0.35 * heat * (1 - ph))
    v.onto(cv)
    draw_vehicle(cv, spr, m, x, y, ang, 0.62, 1.0)
    # bow-shock glow in front of the belly (below the ship)
    cv.glow(x - 30, y + 70, 360, (255, 120, 50), 0.55 * heat, 1.4)
    cv.glow(x - 30, y + 40, 200, (255, 220, 160), 0.35 * heat, 2.0)
    v = Vec()
    tag(v, 'BELLY FIRST', 1240, 860, HOT, 24, rng(t, H_PLASMA + 0.4, H_PLASMA + 0.8))
    v.onto(cv)


def hook_flip(cv, t):
    """flip upright: rotation from belly-first to vertical, engines light mid-flip"""
    u = rng(t, H_FLIP, H_AIM + 0.3)
    cv.a[:] = sky('dusk')
    ground_band(cv, 980, 'dusk', t, 0.6)
    spr, m = ship_sprite(SHIP_BASE)
    ang = lerp(-82, 0, u)
    x, y = 1000 - 40 * u, 430 + 40 * u
    ign = rng(t, H_FLIP + 0.25, H_FLIP + 0.6)
    exhaust(cv, m, x, y, ang, 0.7, t, ign, 1.6)
    sp = spr.copy()
    sp[..., :3] *= 0.85
    draw_vehicle(cv, sp, m, x, y, ang, 0.7)
    v = Vec()
    # rotation arc guide drawn as it happens
    pts = v.arc_pts(x, y, 300, 300, 200, lerp(200, 270, u))
    v.line(pts, CREAM, 4, 0.7 * (1 - rng(t, H_AIM, H_AIM + 0.4)))
    tag(v, 'FLIP + ENGINES', 1280, 860, HOT, 24, rng(t, H_FLIP + 0.5, H_FLIP + 0.9))
    v.onto(cv)


def hook_aim(cv, t):
    """wide: the tower far away, the ship falling toward it on its engines"""
    u = rng(t, H_AIM, H_NORUN + 0.5)
    cam = Cam(1150, 470, lerp(0.62, 0.7, u))
    xs, ys = ship_catch_xy()
    sy = lerp(-260, 60, u)
    catch_set(cv, t, cam, (xs - 260 * (1 - u), sy), lerp(8, 2, u), 1.0, plume_k=1.0, light=0.5, kind='night', plume_len=2.4)


def hook_norun(cv, t):
    """close on the ship's lower half on its engines: NO RUNWAY / NO LANDING LEGS"""
    u = rng(t, H_NORUN, H_ARMS)
    cam = Cam(1420, 330 + 30 * u, 1.9)
    xs, ys = ship_catch_xy()
    catch_set(cv, t, cam, (xs, ys - 230 + 40 * u), 0.0, 1.0, plume_k=1.0, light=0.8, kind='night', plume_len=2.2)
    v = Vec()
    a1 = rng(t, H_NORUN, H_NORUN + 0.25)
    a2 = rng(t, H_NOLEG, H_NOLEG + 0.25)
    # runway icon crossed
    if a1 > 0:
        x0, y0 = 560, 640
        v.poly([(x0, y0 + 120), (x0 + 120, y0), (x0 + 260, y0), (x0 + 380, y0 + 120)], (60, 64, 72), a1)
        for k in range(4):
            v.line([(x0 + 190, y0 + 10 + k * 30), (x0 + 190, y0 + 24 + k * 30)], (230, 230, 230), 6, a1)
        v.line([(x0 + 10, y0 - 10), (x0 + 370, y0 + 130)], RED, 12, a1)
        v.text('NO RUNWAY', x0 + 190, y0 + 190, 54, (255, 255, 255), 'b', 'ms', a1, 6)
    if a2 > 0:
        x0, y0 = 1540, 640
        v.line([(x0, y0), (x0 - 70, y0 + 120)], (190, 196, 206), 14, a2)
        v.line([(x0 + 80, y0), (x0 + 150, y0 + 120)], (190, 196, 206), 14, a2)
        v.line([(x0 - 90, y0 - 20), (x0 + 170, y0 + 140)], RED, 12, a2)
        v.text('NO LANDING LEGS', x0 + 40, y0 + 190, 54, (255, 255, 255), 'b', 'ms', a2, 6)
    v.onto(cv)


def hook_arms(cv, t):
    """the arms swing open and wait; the plume light grows from above"""
    u = rng(t, H_ARMS, H_END)
    cam = Cam(lerp(1180, 1300, u), lerp(470, 430, u), lerp(1.45, 1.25, u))
    open_ = lerp(0.15, 1.0, rng(t, H_ARMS + 0.2, H_ARMS + 2.4))
    xs, ys = ship_catch_xy()
    catch_set(cv, t, cam, (xs, ys - 420 + 90 * u), 0.0, open_, plume_k=1.0, light=0.4 + 0.5 * u, kind='night', plume_len=2.6)
    v = Vec()
    tx, ay = cam.p(TX + TW / 2 + ARML * 0.55, ARMY)
    a = rng(t, H_ARMS + 1.0, H_ARMS + 1.5) * (1 - rng(t, H_END - 0.4, H_END))
    tag(v, 'TWO STEEL ARMS', tx - 90, ay + 150, CREAM, 26, a)
    v.onto(cv)


# ------------------------------------------------------------------ 2. SPLIT: caught / lost
S2 = H_END
S2_TWIST = c("But there's a twist") - 0.1
S2_BOOST = c("The rocket's giant booster")
S2_CONTRAST = c('And that contrast')
S2_END = c("Let's rewind") - 0.2
LP = (70, 120, 820, 600)          # left panel x, y, w, h
RP = (1030, 120, 820, 600)


def _caught_panel(t):
    def f(cv):
        u = rng(t, S2, S3)
        cam = Cam(lerp(1420, 1470, u), lerp(440, 400, u), lerp(1.0, 1.3, u))
        catch_set(cv, t, cam, (None, None), 0.0, 0.55, plume_k=0.0, light=0.55, kind='night', steam=0.8)
    return sub_canvas(f, LP[2], LP[3])


def gulf_map(v, x, y, w, h, a=1.0):
    """schematic Texas Gulf coast (not to scale): land left/top, water right/bottom"""
    v.rect(x, y, w, h, (20, 46, 74), None, a=a, r=10)
    coast = [(x + w * 0.05, y), (x + w * 0.16, y + h * 0.22), (x + w * 0.23, y + h * 0.42), (x + w * 0.26, y + h * 0.6),
             (x + w * 0.24, y + h * 0.82), (x + w * 0.2, y + h)]
    v.poly([(x, y)] + coast + [(x, y + h)], (58, 64, 52), a)
    v.line(coast, (190, 200, 180), 3, a * 0.8)
    v.text('TEXAS', x + 30, y + 60, 26, (210, 214, 196), 'm', a=a * 0.8)
    v.text('GULF OF MEXICO', x + w * 0.62, y + h * 0.84, 26, (150, 196, 230), 'm', 'ms', a=a * 0.85)
    return (x + w * 0.24, y + h * 0.62)            # Starbase (coast, near the border)


def booster_path(sb, x, y, w, h, u_ret, div):
    """return arc from the east toward Starbase; div 0..1 bends it out into the Gulf"""
    start = (x + w * 0.92, y + h * 0.18)
    ctrl = (x + w * 0.62, y + h * 0.05)
    end_tower = sb
    end_gulf = (x + w * 0.52, y + h * 0.66)
    full = bez(start, ctrl, end_tower, 70)
    gulf = bez(start, (x + w * 0.66, y + h * 0.1), end_gulf, 70)
    return partial(full, u_ret), partial(gulf, div)


def split(cv, t):
    cv.a[:] = sky('studio')
    v = Vec()
    aL = rng(t, S2, S2 + 0.5)
    aR = rng(t, S2_TWIST, S2_TWIST + 0.5)
    # left: the caught ship
    if aL > 0:
        place_rgb(cv, _caught_panel(t), LP[0] - 60 * (1 - aL), LP[1], aL)
    if aR > 0:
        x, y, w, h = RP
        vm = Vec()
        sb = gulf_map(vm, x + 60 * (1 - aR), y, w, h, aR)
        sb_s = sb
        u = rng(t, S2_BOOST, S2_BOOST + 2.4)
        _, g = booster_path(sb_s, x, y, w, h, 0, u)
        vm.circle(sb_s[0], sb_s[1], 9, (255, 220, 140), a=aR)
        vm.text('STARBASE', sb_s[0] + 18, sb_s[1] + 8, 22, CREAM, 'm', a=aR)
        if len(g) > 1:
            vm.line(g, RED, 6, aR)
            bx, by = g[-1]
            vm.circle(bx, by, 10, RED, a=aR)
            if u >= 1:
                rr = 18 + 30 * rng(t, S2_BOOST + 2.4, S2_BOOST + 3.2)
                vm.circle(bx, by, rr, None, RED, 4, aR * (1 - 0.5 * rng(t, S2_BOOST + 3.2, S2_BOOST + 4)))
        vm.onto(cv)
    panel(cv, v, *LP, aL)
    panel(cv, v, *RP, aR)
    v.text('NOV 14, 2026', LP[0] + 24, LP[1] + 48, 26, CREAM, 'm', a=aL)
    v.text('SHIP 42', LP[0] + 24, LP[1] + 84, 30, (255, 255, 255), 'b', a=aL)
    v.text('SUPER HEAVY BOOSTER', RP[0] + RP[2] - 24, RP[1] + 48, 26, CREAM, 'm', 'rs', a=aR)
    k = rng(t, S2_CONTRAST, S2_CONTRAST + 0.35)
    stamp(v, 'CAUGHT', LP[0] + LP[2] / 2, LP[1] + LP[3] + 92, (120, 230, 150), 70, k)
    stamp(v, 'LOST', RP[0] + RP[2] / 2, RP[1] + RP[3] + 92, RED, 70, k)
    v.onto(cv)


# ------------------------------------------------------------------ 3. REWIND + LAUNCH
S3 = S2_END
S3_LIFT = c('lifted off on') + 0.15
S3_BOT = c('At the bottom') - 0.1
S3_TOP = c('On top was') - 0.1
S3_PLAN = c('And the plan') - 0.1
S3_END = c('A few minutes') - 0.2
STACK_GAP = 2


def stack_draw(cv, t, x, y_base, z, plume_k=0.0, ang=0.0, labels=None):
    """booster + ship stacked; y_base = screen y of the booster engines"""
    b, bm = booster_sprite(SHIP_BASE)
    s, sm = ship_sprite(SHIP_BASE)
    kb = 71.0 / 50.0 * SHIP_H / bm['h'] * z
    ks = SHIP_H / sm['h'] * z
    bh, sh = bm['h'] * kb, sm['h'] * ks
    th = math.radians(ang)
    ux, uy = -math.sin(th), -math.cos(th)                      # up along the axis
    bcx, bcy = x + ux * bh / 2, y_base + uy * bh / 2
    scx, scy = x + ux * (bh + sh / 2 - STACK_GAP), y_base + uy * (bh + sh / 2 - STACK_GAP)
    if plume_k > 0:
        exhaust(cv, bm, bcx, bcy, ang, kb, t, plume_k, 1.8)
    draw_vehicle(cv, b, bm, bcx, bcy, ang, kb)
    draw_vehicle(cv, s, sm, scx, scy, ang, ks)
    return (bcx, bcy, bh), (scx, scy, sh)


def rewind(cv, t):
    u = rng(t, S3, S3_LIFT - 4.0)
    cv.a[:] = sky('dusk') * (0.6 + 0.4 * u)
    v = Vec()
    # tape-rewind streaks + calendar flip
    r = np.random.default_rng(2)
    for i in range(40):
        y = r.uniform(0, H)
        ph = (t * 3.5 + r.random()) % 1
        x = W * (1 - ph) * 1.3 - 200
        v.line([(x, y), (x + 300, y)], (255, 255, 255), 2, 0.25 * (1 - u))
    day = '14' if u < 0.5 else '13'
    v.text('NOV', 960, 470, 60, CREAM, 'm', 'ms', 1 - rng(t, S3_LIFT - 4.4, S3_LIFT - 3.9))
    v.text(day, 960, 620, 170, YELLOW, 'b', 'ms', 1 - rng(t, S3_LIFT - 4.4, S3_LIFT - 3.9))
    v.text('◀◀ REWIND', 960, 720, 30, (255, 255, 255), 'm', 'ms', (1 - u) * (0.6 + 0.4 * math.sin(t * 9)))
    v.onto(cv)


def launch(cv, t):
    """Starbase at dusk: the full stack on the pad, liftoff, then the climb with labels."""
    lift = rng(t, S3_LIFT, S3_LIFT + 7.0) ** 1.8
    rise = 1500 * lift
    zoom = lerp(0.95, 0.62, rng(t, S3_LIFT + 1.5, S3_BOT + 2))
    cam_y = 520 - rise * 0.75
    cam = Cam(1000, cam_y, zoom)
    cv.a[:] = sky('dusk')
    hy = cam.p(0, GROUND)[1]
    ground_band(cv, hy, 'dusk', t, 0.8)
    tx, gy = cam.p(TX, GROUND)
    _, ty = cam.p(TX, TOP)
    _, ay = cam.p(TX, ARMY)
    v = Vec()
    tower(v, tx, gy, ty, ay, open_=1.0, light=0.3, arm_len=ARML * 0.45 * cam.z, w=TW * cam.z, scale=cam.z)
    v.onto(cv)
    px, py = cam.p(TX + 230, GROUND - 60 - rise)
    ign = rng(t, S3_LIFT - 0.6, S3_LIFT)
    (bx, by, bh), (sx, sy, sh) = stack_draw(cv, t, px, py, cam.z, plume_k=ign, ang=0.0)
    # launch mount + smoke
    v = Vec()
    mx, my = cam.p(TX + 230, GROUND)
    v.rect(mx - 80 * cam.z, my - 60 * cam.z, 160 * cam.z, 60 * cam.z, (40, 42, 48))
    v.onto(cv)
    if ign > 0:
        r = np.random.default_rng(3)
        for i in range(26):
            k = (t - S3_LIFT + 0.6) * (0.4 + r.random() * 0.6)
            ox = r.uniform(-1, 1) * (120 + 260 * k) * cam.z
            cv.glow(mx + ox, my - 40 * cam.z - r.random() * 60 * cam.z, (110 + 120 * min(k, 3)) * cam.z,
                    (230, 196, 170), 0.22 * ign * max(0.2, 1 - 0.12 * k), 1.2)
        cv.glow(mx, my - 40, 420 * cam.z, (255, 170, 90), 0.5 * ign)
    v = Vec()
    a_b = rng(t, S3_BOT, S3_BOT + 0.5) * (1 - rng(t, S3_PLAN + 4, S3_PLAN + 4.6))
    a_s = rng(t, S3_TOP, S3_TOP + 0.5) * (1 - rng(t, S3_PLAN + 4, S3_PLAN + 4.6))
    if a_b > 0:
        p = (bx + 40 * cam.z, by)
        v.line([p, (p[0] + 160, p[1]), (p[0] + 200, p[1] - 40)], CREAM, 3, a_b)
        tag(v, 'SUPER HEAVY  ·  BOOSTER', p[0] + 210, p[1] - 30, CREAM, 26, a_b)
    if a_s > 0:
        p = (sx + 34 * cam.z, sy)
        v.line([p, (p[0] + 160, p[1]), (p[0] + 200, p[1] - 40)], CYAN, 3, a_s)
        tag(v, 'SHIP 42  ·  SPACECRAFT', p[0] + 210, p[1] - 30, CYAN, 26, a_s)
    a_p = rng(t, S3_PLAN + 1.2, S3_PLAN + 1.8) * (1 - rng(t, S3_END - 0.4, S3_END))
    if a_p > 0:
        # the plan: both stages back to the tower (dashed return arrows)
        gx, gy2 = tx + 30, ay
        u = rng(t, S3_PLAN + 1.2, S3_PLAN + 3.2)
        v.line(partial(bez((bx, by), (bx - 350, by + 120), (gx, gy2)), u), CREAM, 5, a_p, dash=(22, 14))
        v.line(partial(bez((sx, sy), (sx - 700, sy + 80), (gx, gy2 - 40)), u), CYAN, 5, a_p, dash=(22, 14))
        tag(v, 'THE PLAN: CATCH BOTH', 740, 160, YELLOW, 30, a_p)
    v.onto(cv)


# ------------------------------------------------------------------ 4. STAGING
S4 = S3_END
S4_SEP = c('the stages parted') - 0.3
S4_SPLIT = c('Super Heavy turned') - 0.2
S4_SHIP = c('Ship forty-two kept')
S4_END = c('The booster was supposed') - 0.2


def staging(cv, t):
    u = (t - S4) / (S4_SPLIT - S4)
    cv.a[:] = sky('high')
    cv.a += starfield(7) * 0.5 * smooth(u)
    # high altitude: cloud deck far below drifting down
    v = Vec()
    yc = 1000 + 200 * u
    v.poly([(0, yc), (W, yc - 60), (W, H), (0, H)], (180, 196, 214), 0.5)
    v.onto(cv)
    sep = rng(t, S4_SEP, S4_SEP + 3.0)
    x0, yb = 900, 820 - 40 * smooth(u)
    b, bm = booster_sprite(SHIP_BASE)
    s, sm = ship_sprite(SHIP_BASE)
    z = 0.9
    kb = 71.0 / 50.0 * SHIP_H / bm['h'] * z
    ks = SHIP_H / sm['h'] * z
    bh, sh = bm['h'] * kb, sm['h'] * ks
    # booster: falls back, turns around (flip) and starts its boostback
    b_ang = 0 + 160 * rng(t, S4_SEP + 0.8, S4_SEP + 4.0)
    bcx, bcy = x0 - 120 * sep, yb - bh / 2 + 220 * sep
    s_y = yb - bh - sh / 2 - 330 * sep ** 1.3
    s_x = x0 + 180 * sep
    ship_ign = 1.0 if t < S4_SEP else rng(t, S4_SEP + 0.25, S4_SEP + 0.7)
    boost_ign = 1.0 if t < S4_SEP else 0.0 + 0.9 * rng(t, S4_SEP + 3.6, S4_SEP + 4.2)
    if t < S4_SEP:
        stack_draw(cv, t, x0, yb, z, plume_k=1.0)
    else:
        if boost_ign > 0:
            exhaust(cv, bm, bcx, bcy, b_ang, kb, t, boost_ign, 1.2)
        draw_vehicle(cv, b, bm, bcx, bcy, b_ang, kb)
        exhaust(cv, sm, s_x, s_y, 0, ks, t, ship_ign, 2.2, seed=3, cold=False)
        draw_vehicle(cv, s, sm, s_x, s_y, 0, ks)
        flash = math.exp(-max(0, t - S4_SEP) * 3.0)
        cv.glow(x0, yb - bh, 260, (255, 200, 120), 0.9 * flash)
    v = Vec()
    tag(v, 'HOT STAGING: STAGES SEPARATE', 1180, 300, HOT, 26, rng(t, S4_SEP + 0.3, S4_SEP + 0.7) * (1 - rng(t, S4_SPLIT - 0.5, S4_SPLIT)))
    v.onto(cv)


def two_outcomes(cv, t):
    """diagram: one launch, two outcomes (builds with the narration)"""
    cv.a[:] = sky('studio')
    v = Vec()
    u1 = rng(t, S4_SPLIT, S4_SPLIT + 2.2)
    u2 = rng(t, S4_SHIP, S4_SHIP + 2.2)
    base = (1000, 900)
    stg = (1000, 560)
    v.line([(0, 940), (W, 940)], (60, 74, 84), 4)
    v.line(partial([base, stg], rng(t, S4_SPLIT - 0.2, S4_SPLIT + 0.4)), (210, 220, 228), 6, dash=(20, 18))
    bp = bez(stg, (760, 420), (420, 820))
    sp = bez(stg, (1180, 330), (1620, 150))
    v.line(partial(bp, u1), (238, 136, 89), 9)
    v.line(partial(sp, u2), (111, 201, 222), 9)
    if u1 > 0:
        x, y = partial(bp, u1)[-1]
        v.circle(x, y, 12, (238, 136, 89))
        v.text('BOOSTER: BACK TOWARD THE COAST', 300, 880, 32, (238, 136, 89), 'b', a=rng(t, S4_SPLIT + 1, S4_SPLIT + 1.5))
    if u2 > 0:
        x, y = partial(sp, u2)[-1]
        v.circle(x, y, 12, (111, 201, 222))
        v.text('SHIP 42: TOWARD ORBIT', 1180, 120, 32, (111, 201, 222), 'b', a=rng(t, S4_SHIP + 1, S4_SHIP + 1.5))
    v.circle(*stg, 16, (255, 255, 255))
    v.text('ONE LAUNCH. TWO OUTCOMES.', 960, 1000 - 960 + 120, 52, (255, 255, 255), 'b', 'ms', rng(t, S4_SPLIT + 0.3, S4_SPLIT + 0.9))
    v.onto(cv)
