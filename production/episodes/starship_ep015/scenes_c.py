"""EP015 scenes 9-12: deorbit + re-entry heating, why the landing is strange (runway /
parachutes / tower), the precision problem (top view), the catch."""
from common import *   # noqa

S9 = c('First came the') - 0.2
S9_FIRE = c('a short engine firing') - 0.1
S9_BEND = c("bends the ship's") - 0.1
S9_AIR = c('Then the air') - 0.15
S9_PILE = c('Air piled up') - 0.1
S9_TEMP = c('Temperatures soared') - 0.1
S9_PLASMA = c('Glowing plasma') - 0.1
S9_TILES = c('Its heat shield') - 0.1
S9_FLAPS = c('steered the fall') - 0.6
S10 = c('And this is where') - 0.2
S10_PLANE = c('An airplane') - 0.1
S10_CAPS = c('A returning capsule') - 0.1
S10_SHIP = c('Starship fell') - 0.1
S10_LIT = c('Then it lit') - 0.1
S10_TARGET = c('The target was') - 0.1
S10_CHOP = c('the chopsticks') - 0.1
S10_WHY = c('Why go to') - 0.1
S10_LEGS = c('Landing legs are') - 0.1
S10_PAY = c("can't be payload") - 0.3
S10_IDEA = c('The idea is') - 0.1
S10_LIGHT = c('fly lighter') - 0.4
S11 = c('Think about how') - 0.2
S11_CHASE = c('The tower cannot') - 0.1
S11_PLACE = c('exactly the right place') - 0.1
S11_SPEED = c('exactly the right speed') - 0.1
S11_END_SEQ = c('the very end') - 0.1
S11_EASY = c('A successful catch') - 0.1
S11_PIECE = c('one crucial piece') - 0.2
S12 = c('And then it happened') - 0.2
S12_HOURS = c('twenty-two and a half') - 0.2
S12_SLOW = c('Its engines slowed') - 0.1
S12_SETTLE = c('It settled') - 0.1
S12_CAUGHT = c('and the tower caught') + 0.25
S12_FIRST = c('For the first time') - 0.1
S13 = c('This is where a lot') - 0.2


# ------------------------------------------------------------------ 9. thermal
def deorbit(cv, t):
    """in orbit: the ship turns tail-first, a short burn, the path bends down into the air"""
    cv.a[:] = sky('space')
    cv.a += starfield(19) * 0.6
    v = Vec()
    R = 1900
    cx, cy = 960, 1080 + R - 220
    pts = v.arc_pts(cx, cy, R, R, 200, 340, 160)
    v.poly(pts + [(W, H), (0, H)], (20, 56, 108))
    v.line(pts, (130, 200, 255), 8, 0.9)
    atm = v.arc_pts(cx, cy, R + 70, R + 70, 200, 340, 160)
    v.line(atm, (120, 180, 255), 2, 0.4, dash=(10, 10))
    v.text('ATMOSPHERE', 1500, 790, 20, (150, 200, 255), 'm', a=0.7)
    v.onto(cv)
    cv.glow(960, 900, 1100, (60, 130, 255), 0.2, 1.2)
    v = Vec()
    turn = rng(t, S9 + 0.3, S9_FIRE)
    burn = rng(t, S9_FIRE, S9_FIRE + 0.3) * (1 - rng(t, S9_FIRE + 2.6, S9_FIRE + 3.0))
    ox, oy = 560 + 120 * rng(t, S9, S9_AIR), 330
    # before the burn: circular path; after: bent path down into the atmosphere
    v.line([(200, 340), (1700, 300)], (210, 230, 240), 3, 0.35 * (1 - rng(t, S9_BEND, S9_BEND + 0.6)), dash=(14, 10))
    bend = bez((ox, oy), (1150, 300), (1560, 760))
    v.line(partial(bend, rng(t, S9_BEND, S9_BEND + 2.2)), YELLOW, 5, 0.9)
    tag(v, 'DEORBIT BURN', ox - 60, oy + 120, HOT, 26, burn)
    tag(v, 'PATH DIPS INTO THE AIR', 1240, 560, YELLOW, 24, rng(t, S9_BEND + 1.6, S9_BEND + 2.2))
    v.onto(cv)
    s, sm = ship_sprite(SHIP_BASE)
    ang = lerp(-90, 90, turn)            # nose forward (+x) -> engines forward
    if burn > 0:
        exhaust(cv, sm, ox, oy, ang, 0.35, t, burn, 1.5, cold=True)
    draw_vehicle(cv, s, sm, ox, oy, ang, 0.35)


def reentry(cv, t):
    """belly-first through the upper air: compression, heating, plasma, flaps steering"""
    u = rng(t, S9_AIR, S10)
    heat = 0.15 + 0.85 * rng(t, S9_PILE, S9_PLASMA + 1.0)
    cv.a[:] = sky('high') * lerp(0.35, 0.7, u)
    cv.a += starfield(23) * 0.4 * (1 - u)
    x, y = 720, 470 + 8 * math.sin(t * 7)
    ang = -80 + 5 * math.sin(t * 1.4)
    # flowing air / plasma streaks (from below-left, pushed around the belly)
    r = np.random.default_rng(29)
    v = Vec()
    for i in range(70):
        ph = (t * (0.9 + r.random()) + r.random()) % 1
        y0 = 620 + r.random() * 440 - ph * 520
        x0 = 120 + r.random() * 1700
        L = 60 + 220 * heat * r.random()
        col = (lerp(160, 255, heat), lerp(200, 150, heat), lerp(255, 80, heat))
        v.line([(x0, y0), (x0 + L * 0.25, y0 - L)], col, 2 + 2 * r.random(), (0.2 + 0.5 * heat) * math.sin(math.pi * ph))
    v.onto(cv)
    spr, m = ship_sprite(SHIP_BASE, round(heat, 1))
    # plasma sheath under the belly
    cv.glow(x + 10, y + 120, 520, (255, 110, 40), 0.55 * heat, 1.3)
    cv.glow(x, y + 70, 300, (255, 200, 140), 0.45 * heat, 1.8)
    cv.glow(x, y + 60, 700, (255, 80, 160), 0.12 * heat, 1.2)
    draw_vehicle(cv, spr, m, x, y, ang, 0.9)
    v = Vec()
    # bow shock arc
    pk = rng(t, S9_PILE, S9_PILE + 0.8)
    arc = v.arc_pts(x, y + 30, 420, 160, 20, 160, 60)
    v.line(arc, (255, 236, 200), 4, 0.6 * pk)
    tag(v, 'AIR PILES UP IN FRONT', 1240, 860, (255, 236, 200), 24, pk * (1 - rng(t, S9_TEMP, S9_TEMP + 0.3)))
    # temperature bar (qualitative)
    tb = rng(t, S9_TEMP, S9_TEMP + 0.4)
    if tb > 0:
        v.rect(1620, 200, 50, 460, (6, 10, 18, 220), (255, 255, 255, 120), 2, a=tb, r=8)
        lvl = rng(t, S9_TEMP, S9_PLASMA + 1.4)
        v.rect(1626, 654 - 448 * lvl, 38, 448 * lvl, (255, int(200 - 120 * lvl), 60), a=tb, r=6)
        v.text('HEAT', 1645, 700, 22, CREAM, 'm', 'ms', a=tb)
    tag(v, 'GLOWING PLASMA', 1180, 300, HOT, 28, rng(t, S9_PLASMA, S9_PLASMA + 0.4) * (1 - rng(t, S9_TILES, S9_TILES + 0.3)))
    # inset: tiles + flaps
    ti = rng(t, S9_TILES, S9_TILES + 0.5)
    if ti > 0:
        bx, by, bw, bh = 1080, 110, 520, 330
        v.rect(bx, by, bw, bh, (10, 12, 18, 235), (255, 255, 255, 110), 2, a=ti, r=10)
        for j in range(6):
            for i in range(10):
                hx = bx + 40 + i * 46 + (23 if j % 2 else 0)
                hy = by + 50 + j * 40
                g = heat * (0.6 + 0.4 * math.sin(t * 3 + i + j))
                pts = [(hx + 20 * math.cos(math.radians(a)), hy + 20 * math.sin(math.radians(a))) for a in range(30, 390, 60)]
                v.poly(pts, (int(30 + 200 * g), int(32 + 70 * g), int(38 + 10 * g)), ti)
        v.text('HEAT-SHIELD TILES', bx + 20, by + bh - 20, 22, CREAM, 'm', a=ti)
    fl = rng(t, S9_FLAPS, S9_FLAPS + 0.5)
    if fl > 0:
        bx, by = 1080, 470
        v.rect(bx, by, 520, 230, (10, 12, 18, 235), (255, 255, 255, 110), 2, a=fl, r=10)
        v.rect(bx + 60, by + 100, 400, 46, (200, 204, 212), a=fl, r=20)
        for k, (fx, sgn) in enumerate(((bx + 110, -1), (bx + 390, -1), (bx + 110, 1), (bx + 390, 1))):
            a = math.radians(25 * math.sin(t * 2.2 + k) * sgn)
            base = (fx, by + 100 if sgn < 0 else by + 146)
            tip = (fx + 60 * math.sin(a), base[1] + sgn * 70 * math.cos(a))
            v.line([base, tip], (50, 54, 64), 22, fl)
        v.text('FLAPS STEER THE FALL', bx + 20, by + 210, 22, CREAM, 'm', a=fl)
    v.onto(cv)


# ------------------------------------------------------------------ 10. why the landing is strange
LANES = [(150, 'AIRPLANE'), (430, 'CAPSULE'), (710, 'STARSHIP')]


def strange(cv, t):
    cv.a[:] = sky('studio')
    v = Vec()
    out = rng(t, S10_TARGET - 0.3, S10_TARGET + 0.3)
    a_l = 1 - out
    if a_l > 0:
        for i, (y, name) in enumerate(LANES):
            st = (S10_PLANE, S10_CAPS, S10_SHIP)[i]
            a = rng(t, st, st + 0.4) * a_l
            if a <= 0:
                continue
            v.rect(380, y, 1460, 250, (14, 20, 32, 220), (255, 255, 255, 50), 2, a=a, r=10)
            v.text(name, 410, y + 44, 26, CREAM, 'm', a=a)
            u = rng(t, st + 0.2, st + 3.2)
            if i == 0:          # airplane glides to a runway
                v.rect(1100, y + 200, 600, 22, (70, 74, 84), a=a)
                for k in range(8):
                    v.rect(1120 + k * 72, y + 208, 36, 6, (230, 230, 230), a=a)
                px, py = lerp(520, 1300, u), lerp(y + 90, y + 186, u)
                v.poly([(px - 70, py), (px + 70, py - 6), (px + 80, py + 4), (px - 70, py + 10)], (220, 224, 230), a)
                v.poly([(px - 10, py), (px + 20, py), (px - 30, py + 40)], (190, 196, 206), a)
                v.poly([(px - 70, py), (px - 56, py - 26), (px - 46, py)], (190, 196, 206), a)
                v.text('NEEDS A RUNWAY', 1700, y + 44, 24, (255, 255, 255), 'b', 'rs', a=a)
            elif i == 1:        # capsule under parachutes into the ocean
                wy = y + 210
                pts = [(380 + k * 20, wy + 6 * math.sin(k * 0.6 + t * 3)) for k in range(74)]
                v.line(pts, (90, 160, 220), 5, a)
                px, py = lerp(1100, 1150, u), lerp(y + 80, wy - 30, u)
                for dx in (-60, 0, 60):
                    v.line([(px, py - 10), (px + dx, py - 70)], (220, 220, 220), 2, a)
                v.poly(v.arc_pts(px, py - 70, 90, 40, 180, 360, 30), (240, 120, 60), a)
                v.poly([(px - 26, py + 24), (px + 26, py + 24), (px + 12, py - 12), (px - 12, py - 12)], (200, 204, 212), a)
                v.text('PARACHUTES → OCEAN', 1700, y + 44, 24, (255, 255, 255), 'b', 'rs', a=a)
            else:               # belly flop, flip, engines
                v.text('BELLY-FIRST, FLAPS, FLIP, ENGINES', 1700, y + 44, 24, (255, 255, 255), 'b', 'rs', a=a)
        v.onto(cv)
        # lane 3 ship (raster)
        a3 = rng(t, S10_SHIP, S10_SHIP + 0.4) * a_l
        if a3 > 0:
            y = LANES[2][0]
            fl = rng(t, S10_LIT, S10_LIT + 2.0)
            px = lerp(700, 1450, rng(t, S10_SHIP, S10_TARGET))
            py = y + 140 + 20 * fl
            spr, m = ship_sprite(SHIP_BASE, 0.3 if fl < 0.5 else 0.0)
            ang = lerp(-80, 0, fl)
            ign = rng(t, S10_LIT + 0.3, S10_LIT + 0.7)
            if ign > 0:
                exhaust(cv, m, px, py, ang, 0.3, t, ign * a3, 1.6)
            draw_vehicle(cv, spr, m, px, py, ang, 0.3, a3)
        v = Vec()
    # target: the gap between the arms (top view)
    if out > 0:
        tg = 1 - rng(t, S10_WHY - 0.2, S10_WHY + 0.3)
        if tg > 0:
            a = out * tg
            v.rect(300, 120, 1320, 700, (16, 30, 42), (79, 119, 138), 3, a=a, r=16)
            v.rect(420, 380, 240, 220, (84, 107, 114), a=a)
            op = 1.0
            v.line([(660, 430), (1040, 460), (1290, 400)], (162, 184, 188), 56, a)
            v.line([(660, 560), (1040, 535), (1290, 590)], (162, 184, 188), 56, a)
            pulse = 0.5 + 0.5 * math.sin(t * 4)
            v.circle(1080, 498, 52, (212, 228, 228), (100, 125, 130), 6, a)
            v.circle(1080, 498, 80 + 10 * pulse, None, YELLOW, 4, a)
            v.text('THE GAP', 1080, 360, 34, YELLOW, 'b', 'ms', a)
            v.text('TOWER', 540, 650, 26, CREAM, 'm', 'ms', a)
            v.text('TOP VIEW · NOT TO SCALE', 1580, 800, 20, (170, 180, 192), 'm', 'rs', a)
            ch = rng(t, S10_CHOP, S10_CHOP + 0.4)
            tag(v, '"CHOPSTICKS"', 760, 300, (255, 255, 255), 34, a * ch)
        # why: legs are heavy -> leave them in the tower
        w2 = rng(t, S10_WHY - 0.1, S10_WHY + 0.4)
        if w2 > 0:
            # balance: legs vs payload
            tilt = rng(t, S10_LEGS + 0.4, S10_LEGS + 1.4) * (1 - rng(t, S10_IDEA + 0.3, S10_LIGHT))
            cx, cy = 700, 420
            ang = math.radians(-12 * tilt)
            L = 300
            p1 = (cx - L * math.cos(ang), cy - L * math.sin(ang))
            p2 = (cx + L * math.cos(ang), cy + L * math.sin(ang))
            v.poly([(cx - 30, 720), (cx + 30, 720), (cx, cy)], (120, 126, 140), w2)
            v.line([p1, p2], (200, 206, 216), 10, w2)
            for p, lab, col in ((p1, 'LANDING LEGS', (238, 136, 89)), (p2, 'PAYLOAD', CYAN)):
                v.line([p, (p[0], p[1] + 100)], (200, 206, 216), 3, w2)
                v.rect(p[0] - 120, p[1] + 100, 240, 26, (200, 206, 216), a=w2, r=6)
                v.text(lab, p[0], p[1] + 170, 26, col, 'b', 'ms', w2)
            lg = rng(t, S10_LEGS, S10_LEGS + 0.4) * (1 - rng(t, S10_IDEA + 0.3, S10_IDEA + 1.6))
            if lg > 0:
                for k in range(3):
                    v.rect(p1[0] - 90 + k * 60, p1[1] + 40, 40, 60, (238, 136, 89), a=lg, r=4)
            pg = rng(t, S10_PAY, S10_PAY + 0.4)
            if pg > 0:
                v.rect(p2[0] - 50, p2[1] + 50, 100, 50, CYAN, a=pg, r=4)
            # tower takes the hardware
            tw_ = rng(t, S10_IDEA, S10_IDEA + 0.4)
            if tw_ > 0:
                v.rect(1380, 240, 70, 480, (60, 66, 78), a=tw_)
                v.rect(1450, 380, 220, 26, (150, 156, 168), a=tw_)
                v.rect(1450, 430, 220, 26, (150, 156, 168), a=tw_)
                mv = rng(t, S10_IDEA + 0.3, S10_IDEA + 1.6)
                for k in range(3):
                    sx = lerp(p1[0] - 90 + k * 60, 1390 + k * 18, mv)
                    sy = lerp(p1[1] + 40, 520 + k * 50, mv)
                    v.rect(sx, sy, 40, 40, (238, 136, 89), a=tw_ * (1 if mv < 1 else 0.85), r=4)
                v.text('HEAVY HARDWARE STAYS ON THE GROUND', 1300, 200, 26, (255, 255, 255), 'b', 'ms', tw_)
            lt = rng(t, S10_LIGHT, S10_LIGHT + 0.5)
            tag(v, 'LIGHTER ROCKET → MORE PAYLOAD', 420, 200, YELLOW, 30, lt)
    v.onto(cv)


# ------------------------------------------------------------------ 11. precision (top view)
def precision(cv, t):
    cv.a[:] = sky('studio')
    v = Vec()
    a = rng(t, S11, S11 + 0.5)
    v.rect(140, 110, 1640, 720, (16, 30, 42), (79, 119, 138), 3, a=a, r=16)
    v.text('TOP VIEW · NOT TO SCALE', 1750, 810, 20, (170, 180, 192), 'm', 'rs', a)
    # tower + arms
    v.rect(260, 370, 260, 240, (84, 107, 114), a=a)
    lock = rng(t, S11_CHASE, S11_CHASE + 0.4)
    if lock > 0:
        tag(v, 'TOWER: FIXED IN PLACE', 540, 660, CREAM, 24, lock)
    close = rng(t, S11_END_SEQ, S11_END_SEQ + 1.2)
    gap = lerp(70, 54, close)
    v.line([(520, 420), (900, 490 - gap + 70), (1140, 490 - gap)], (162, 184, 188), 50, a)
    v.line([(520, 560), (900, 490 + gap - 70), (1140, 490 + gap)], (162, 184, 188), 50, a)
    # the ship's footprint wandering in and settling; error ellipse shrinking
    u = rng(t, S11 + 0.3, S11_SPEED + 1.5)
    wob = (1 - u)
    sx = 1000 + 380 * wob * math.cos(t * 0.9) + 60 * wob
    sy = 490 + 240 * wob * math.sin(t * 1.3)
    er = lerp(330, 62, u)
    v.circle(1000, 490, er, None, YELLOW, 3, a * 0.8)
    v.circle(sx, sy, 50, (212, 228, 228), (100, 125, 130), 5, a)
    tag(v, 'ALLOWED ERROR', 1000 + er * 0.72 + 20, 490 - er * 0.72 - 10, YELLOW, 22, a * (1 - close))
    # gauges: position + speed
    for k, (lab, st) in enumerate((('POSITION', S11_PLACE), ('SPEED', S11_SPEED))):
        g = rng(t, st, st + 0.4)
        if g <= 0:
            continue
        gx, gy = 1380, 200 + k * 140
        v.rect(gx, gy, 360, 100, (6, 10, 18, 220), (255, 255, 255, 100), 2, a=g, r=8)
        v.text(lab, gx + 20, gy + 38, 22, CREAM, 'm', a=g)
        lvl = 1 - rng(t, st + 0.2, st + 2.0)
        v.rect(gx + 20, gy + 56, 320 * max(0.06, lvl), 22, (255, int(120 + 100 * (1 - lvl)), 70) if lvl > 0.1 else (120, 230, 150), a=g, r=4)
        if lvl <= 0.1:
            v.text('✓', gx + 330, gy + 42, 34, (120, 230, 150), 'b', a=g)
    e = rng(t, S11_EASY, S11_EASY + 0.5)
    if e > 0:
        v.rect(420, 860 - 20, 1080, 0.1, None, a=0)
        tag(v, 'NOT "EASY" — ONE CRUCIAL PIECE, PROVEN IN REAL FLIGHT', 450, 760, (255, 255, 255), 28,
            rng(t, S11_PIECE, S11_PIECE + 0.5))
    v.onto(cv)


# ------------------------------------------------------------------ 12. the catch
def catch(cv, t):
    """wide night shot: the ship comes down on its engines, settles between the arms, the arms
    take its weight, engines off, steam. Narration pauses for ~6 s at the contact."""
    xs, ys = ship_catch_xy()
    t_contact = S12_CAUGHT - 0.9
    # descent: from high above to the catch point (eases in, slowing at the end)
    d = rng(t, S12, t_contact)
    d = 1 - (1 - d) ** 2.2
    sy = lerp(ys - 1150, ys, d)
    sx = xs + 40 * (1 - d) * math.sin(t * 0.7)
    close = rng(t, t_contact - 0.4, t_contact + 0.8)
    open_ = lerp(1.0, 0.5, close)
    cut = rng(t, t_contact + 0.15, t_contact + 0.7)
    plume_k = (1 - cut) * (0.75 + 0.25 * (1 - rng(t, S12_SLOW, t_contact)))
    cz = lerp(0.72, 0.95, rng(t, S12, S12_FIRST))
    cy = lerp(sy + 60, 420, rng(t, S12, t_contact))
    cam = Cam(lerp(1150, 1260, rng(t, S12, S12_FIRST)), cy, cz, shake=1.6 * plume_k * (1 - close * 0.5), t=t)
    steam = rng(t, t_contact + 0.2, t_contact + 2.5) * (1 - 0.6 * rng(t, S12_FIRST + 2, S13))
    settle = 4 * math.exp(-max(0, t - t_contact) * 3) * math.sin(max(0, t - t_contact) * 14) if t > t_contact else 0
    catch_set(cv, t, cam, (sx, sy + settle), 0.0, open_, plume_k=plume_k, light=0.55 + 0.4 * plume_k, kind='night',
              steam=steam, plume_len=2.2)
    v = Vec()
    tag(v, 'NOV 14, 2026 · STARBASE, TEXAS', 1240, 120, CREAM, 24, rng(t, S12 + 0.4, S12 + 0.9) * (1 - rng(t, S12_SETTLE, S12_SETTLE + 0.5)))
    tag(v, '~22.5 HOURS AFTER LIFTOFF', 1240, 172, (255, 255, 255), 24, rng(t, S12_HOURS, S12_HOURS + 0.4) * (1 - rng(t, S12_SETTLE, S12_SETTLE + 0.5)))
    f = rng(t, S12_FIRST, S12_FIRST + 0.6)
    if f > 0:
        v.text('FIRST STARSHIP UPPER STAGE', 120, 180, 54, (255, 255, 255), 'b', 'ls', f, 5)
        v.text('CAUGHT AFTER ORBIT', 120, 250, 54, YELLOW, 'b', 'ls', f, 5)
    v.onto(cv)


TIMELINE = [
    (S9, deorbit, 'SCHEMATIC · NOT TO SCALE'),
    (S9_AIR, reentry, 'VISUALIZATION · NOT FLIGHT FOOTAGE'),
    (S10, strange, 'SCHEMATIC · NOT TO SCALE'),
    (S11, precision, 'SCHEMATIC · NOT TO SCALE'),
    (S12, catch, 'ILLUSTRATION · NOT FLIGHT FOOTAGE'),
]

SHOTS = [
    (S9, S9_AIR, 1680, FLOOR, 0.62, -1),
    (S9_AIR, S10, 150, FLOOR, 0.6, 1),
    (S10, S10_TARGET - 0.3, 120, FLOOR, 0.66, 1),
    (S10_TARGET - 0.3, S11, 1640, FLOOR, 0.72, -1),
    (S11, S12, 120, FLOOR, 0.66, 1),
    (S12, S13, 170, FLOOR, 0.56, 1),
]


def host(h):
    # deorbit: watches the turn, points at the burn, traces the bent path
    h.gaze(S9 + 0.2, ('s', (600, 330)), look=0.8)
    h.point(S9_FIRE + 0.1, (620, 380), S9_BEND + 0.2, arm='f')
    h.point(S9_BEND + 0.5, lambda t: partial(bez((680, 330), (1150, 300), (1560, 760)), rng(t, S9_BEND, S9_BEND + 2.2))[-1],
            S9_AIR - 0.4, arm='n', gaze_lead=0.1)
    # re-entry: shields himself (near palm up), points at plasma, tiles, flaps
    h.support(S9_PILE + 0.2, S9_TEMP + 1.2, 'n', offset=(18.0, -34.0))
    h.point(S9_TEMP + 0.2, (1640, 400), S9_PLASMA + 0.8, arm='f')
    h.walk(S9_PLASMA + 1.0, 60)
    h.point(S9_TILES + 0.3, (1300, 300), S9_FLAPS - 0.2, arm='f')
    h.point(S9_FLAPS + 0.2, (1300, 600), S10 - 0.4, arm='n')
    # strange: walks along the lanes, points at each as it is named
    h.point(S10_PLANE + 0.2, (1300, 300), S10_CAPS - 0.25, arm='f')
    h.walk(S10_CAPS - 0.1, 70)
    h.point(S10_CAPS + 0.3, (1130, 540), S10_SHIP - 0.25, arm='f')
    h.point(S10_SHIP + 0.3, lambda t: (lerp(700, 1450, rng(t, S10_SHIP, S10_TARGET)), 840), S10_TARGET - 0.5, arm='n', gaze_lead=0.1)
    # target / legs: points at the gap, then at legs vs payload
    h.walk(S10_TARGET + 0.2, 60)
    h.point(S10_TARGET + 0.7, (1080, 498), S10_WHY - 0.3, arm='f')
    h.point(S10_LEGS + 0.3, (420, 600), S10_PAY - 0.3, arm='f')
    h.point(S10_PAY + 0.2, (1000, 520), S10_IDEA - 0.2, arm='n')
    h.point(S10_IDEA + 0.6, (1415, 480), S11 - 0.4, arm='f')
    # precision: walks in, points at the error circle, both hands frame the gap
    h.walk(S11 + 0.3, 90)
    h.point(S11_CHASE + 0.2, (390, 490), S11_PLACE - 0.3, arm='f')
    h.point(S11_PLACE + 0.2, (1000, 490), S11_SPEED + 1.0, arm='f')
    h.support(S11_SPEED + 0.4, S11_EASY - 0.3, 'n', offset=(16.0, -24.0))
    h.point(S11_PIECE, (900, 740), S12 - 0.4, arm='n')
    # catch: small, follows the ship down with his gaze, reacts at contact, no big gesture
    h.gaze(S12 + 0.3, ('s', (1150, 300)), look=0.85)
    h.gaze(S12_SETTLE, ('s', (1250, 480)), look=0.85)
    h.brow(S12_CAUGHT - 0.6, 0.9, 2.6)
    h.walk(S12_CAUGHT + 1.5, 50)
    h.point(S12_FIRST + 0.6, (1270, 470), S13 - 0.5, arm='f')
