"""EP015 scenes 5-8: booster abort (schematic map), two stories, orbit + payload (NASA SVS
Earth), why returning from orbit is hard."""
from functools import lru_cache

from common import *   # noqa
from gfx import Video
import scenes_a as A

S5 = c('The booster was supposed') - 0.2
S5_EARLIER = c('Super Heavy boosters had') - 0.1
S5_RETURN = c('But during its return') - 0.1
S5_CALLED = c('the catch was called') - 0.1
S5_RULED = c('Its systems ruled') - 0.1
S5_DIV = c('diverted toward') - 0.2
S5_NOT = c('It did not come') - 0.1
S5_REPORTS = c('Early reports differ') - 0.1
S5_MATTERS = c('That matters') - 0.1
S6 = c('So one half') - 0.2
S6_YET = c('Yet the other') - 0.1
S7 = c('Ship forty-two reached') - 0.2
S7_ALT = c('above Earth') - 0.6
S7_DEPLOY = c('It deployed') - 0.1
S7_CAMS = c('Three of them') - 0.1
S7_CIRCLE = c('Instead of rushing') - 0.1
S7_ORBITS = c('Fourteen orbits') - 0.1
S7_HOURS = c('More than twenty-two') - 0.1
S8 = c('Now the big question') - 0.2
S8_WHETHER = c('It was whether') - 0.1
S8_SPEED = c('In low orbit') - 0.1
S8_KEEP = c('just to keep') - 0.1
S8_DROP = c('At that speed') - 0.1
S8_ENERGY = c('shed an enormous') - 0.2
S9 = c('First came the') - 0.2

MAP = (330, 110, 1260, 700)


def _map_geom():
    x, y, w, h = MAP
    sb = (x + w * 0.24, y + h * 0.62)
    start = (x + w * 0.95, y + h * 0.12)
    ret = bez(start, (x + w * 0.6, y + h * 0.02), sb, 90)
    k = 52                                       # where the abort happens (index on the return arc)
    p_ab = ret[k]
    div = bez(p_ab, (x + w * 0.42, y + h * 0.5), (x + w * 0.52, y + h * 0.8), 60)
    return sb, start, ret, k, p_ab, div


def abort(cv, t):
    cv.a[:] = sky('studio')
    v = Vec()
    x, y, w, h = MAP
    a = rng(t, S5, S5 + 0.5)
    sb = gulf_map_big(v, a)
    _, start, ret, k, p_ab, div = _map_geom()
    # tower icon at Starbase
    v.rect(sb[0] - 8, sb[1] - 70, 16, 70, (180, 186, 196), a=a)
    v.line([(sb[0] + 8, sb[1] - 50), (sb[0] + 46, sb[1] - 50)], (180, 186, 196), 5, a)
    # return path: planned (dashed cream) to the tower
    u_plan = rng(t, S5 + 0.3, S5 + 2.4)
    v.line(partial(ret, u_plan), CREAM, 4, a * (1 - 0.6 * rng(t, S5_RULED, S5_RULED + 1)), dash=(18, 12))
    # actual: booster moving along the return until the abort point
    u_go = rng(t, S5_RETURN, S5_CALLED + 0.2)
    cur = partial(ret[:k + 1], u_go)
    if u_go > 0:
        v.line(cur, (238, 136, 89), 7, a)
    bx, by = cur[-1] if u_go > 0 else start
    called = rng(t, S5_CALLED, S5_CALLED + 0.3)
    if called > 0:
        pulse = 0.5 + 0.5 * math.sin((t - S5_CALLED) * 8)
        v.circle(p_ab[0], p_ab[1], 30 + 14 * pulse, None, YELLOW, 4, called * (1 - rng(t, S5_DIV, S5_DIV + 1)))
        tag(v, 'TOWER CATCH CALLED OFF', p_ab[0] - 150, p_ab[1] - 56, YELLOW, 26, called)
    # the planned remainder to the tower is crossed out
    rx = rng(t, S5_RULED + 0.6, S5_RULED + 1.2)
    if rx > 0:
        mid = ret[(k + len(ret)) // 2]
        v.line([(mid[0] - 22, mid[1] - 22), (mid[0] + 22, mid[1] + 22)], RED, 7, rx)
        v.line([(mid[0] - 22, mid[1] + 22), (mid[0] + 22, mid[1] - 22)], RED, 7, rx)
    u_div = rng(t, S5_DIV, S5_DIV + 2.6)
    if u_div > 0:
        dv = partial(div, u_div)
        v.line(dv, RED, 7, a)
        bx, by = dv[-1]
        tag(v, 'DIVERTED INTO THE GULF', div[-1][0] + 30, div[-1][1] - 10, RED, 26, rng(t, S5_DIV + 1.6, S5_DIV + 2.2) * (1 - rng(t, S5_REPORTS - 0.3, S5_REPORTS)))
    nr = rng(t, S5_NOT, S5_NOT + 0.4)
    fade = 1 - 0.8 * nr
    v.circle(bx, by, 13, (238, 136, 89), a=a * fade)
    if nr > 0:
        v.circle(bx, by, 24 + 26 * nr, None, RED, 4, nr)
        tag(v, 'NOT RECOVERED', bx + 46, by + 60, RED, 28, nr * (1 - rng(t, S5_REPORTS - 0.3, S5_REPORTS)))
    # earlier flights: booster catches had happened before
    e = rng(t, S5_EARLIER, S5_EARLIER + 0.5) * (1 - rng(t, S5_RETURN - 0.3, S5_RETURN + 0.2))
    if e > 0:
        v.rect(x + 40, y + h - 170, 560, 140, (8, 12, 20, 220), (120, 230, 150, 140), 2, a=e, r=8)
        v.text('EARLIER FLIGHTS', x + 64, y + h - 128, 22, (180, 230, 190), 'm', a=e)
        for i in range(3):
            xx = x + 90 + i * 160
            v.rect(xx, y + h - 106, 12, 64, (180, 186, 196), a=e)
            v.line([(xx + 12, y + h - 90), (xx + 48, y + h - 90)], (180, 186, 196), 4, e)
            v.rect(xx + 26, y + h - 96, 14, 54, (226, 230, 236), a=e)
            v.text('✓', xx + 66, y + h - 50, 34, (120, 230, 150), 'b', a=e)
        v.text('BOOSTER CAUGHT BY THE TOWER', x + 64, y + h - 8, 20, (180, 230, 190), 'm', a=e)
    # why? cause not confirmed
    q = rng(t, S5_REPORTS, S5_REPORTS + 0.5)
    if q > 0:
        bx0 = x + w - 520
        v.rect(bx0, y + h - 250, 490, 220, (8, 12, 20, 230), (255, 255, 255, 90), 2, a=q, r=10)
        v.text('WHY?', bx0 + 26, y + h - 196, 40, YELLOW, 'b', a=q)
        v.text('Early reports differ.', bx0 + 26, y + h - 146, 26, (230, 234, 240), 'r', a=q)
        v.text('Root cause: NOT CONFIRMED', bx0 + 26, y + h - 104, 26, (255, 255, 255), 'b', a=q)
        v.text('as of Nov 15, 2026', bx0 + 26, y + h - 62, 22, (170, 180, 192), 'm', a=q)
    m2 = rng(t, S5_MATTERS, S5_MATTERS + 0.5)
    if m2 > 0:
        v.rect(x + 40, y + 30, 520, 150, (8, 12, 20, 230), None, a=m2, r=10)
        v.text('REPORTED  ✓  catch off, diverted', x + 64, y + 86, 25, (190, 236, 200), 'm', a=m2)
        v.text('UNKNOWN   ?  the final reason', x + 64, y + 140, 25, YELLOW, 'm', a=m2)
    v.onto(cv)


def gulf_map_big(v, a):
    x, y, w, h = MAP
    v.rect(x, y, w, h, (20, 46, 74), (255, 255, 255, 70), 2, a=a, r=12)
    coast = [(x + w * 0.05, y), (x + w * 0.15, y + h * 0.2), (x + w * 0.21, y + h * 0.4), (x + w * 0.245, y + h * 0.62),
             (x + w * 0.22, y + h * 0.84), (x + w * 0.18, y + h)]
    v.poly([(x + 2, y + 2)] + coast + [(x + 2, y + h - 2)], (58, 64, 52), a)
    v.line(coast, (190, 200, 180), 3, a * 0.8)
    v.text('TEXAS', x + 34, y + 70, 30, (210, 214, 196), 'm', a=a * 0.85)
    v.text('GULF OF MEXICO', x + w * 0.66, y + h * 0.9, 30, (150, 196, 230), 'm', 'ms', a=a * 0.85)
    sb = (x + w * 0.24, y + h * 0.62)
    v.circle(sb[0], sb[1], 10, (255, 220, 140), a=a)
    v.text('STARBASE', sb[0] - 24, sb[1] + 42, 24, CREAM, 'm', 'rs', a=a)
    return sb


# ------------------------------------------------------------------ 6. two stories
def two_stories(cv, t):
    """camera climbs from the lower atmosphere to the edge of space; the booster's trail fades,
    the ship keeps climbing toward orbit"""
    u = rng(t, S6, S7 + 0.2)
    sk = sky('high') * (1 - u) + sky('space') * u
    cv.a[:] = sk
    cv.a += starfield(11) * 0.8 * u
    v = Vec()
    # Earth limb rising into view
    cy = lerp(2400, 1700, u)
    pts = v.arc_pts(960, cy, 2300, 1100, 200, 340, 120)
    v.poly(pts + [(W, H), (0, H)], (18, 52, 100), 1.0)
    v.line(pts, (130, 200, 255), 7, 0.85)
    v.onto(cv)
    cv.glow(960, cy - 1100, 1300, (70, 140, 255), 0.18 * u, 1.3)
    # booster trail: grey, fading
    fade = 1 - rng(t, S6 + 0.8, S6_YET + 0.6)
    v = Vec()
    v.line(bez((300, 900), (520, 640), (760, 860)), (238, 136, 89), 6, 0.6 * fade, dash=(14, 10))
    tag(v, 'BOOSTER: LOST', 420, 960 - 80, (238, 136, 89), 24, fade * rng(t, S6, S6 + 0.5))
    trail = bez((700, 980), (1000, 600), (1500, 260))
    k = rng(t, S6 + 0.2, S7 + 0.2)
    v.line(partial(trail, k), CYAN, 6, 0.9)
    v.onto(cv)
    sx, sy = partial(trail, k)[-1]
    s, sm = ship_sprite(SHIP_BASE)
    p0, p1 = partial(trail, max(0, k - 0.02))[-1], (sx, sy)
    ang = -math.degrees(math.atan2(p1[0] - p0[0], -(p1[1] - p0[1]))) if k > 0.02 else -30
    exhaust(cv, sm, sx, sy, ang, 0.32, t, 1.0, 2.0, cold=True)
    draw_vehicle(cv, s, sm, sx, sy, ang, 0.32)
    v = Vec()
    tag(v, 'SHIP 42: STILL CLIMBING', sx + 60, sy + 40, CYAN, 24, rng(t, S6_YET, S6_YET + 0.5))
    v.onto(cv)


# ------------------------------------------------------------------ 7. orbit + payload (NASA SVS Earth)
@lru_cache(maxsize=1)
def earth_video():
    return Video(os.path.join(MEDIA, 'svs5570', 'Earth_wAtmos_spin_02_1080p60.mp4'))


EC, ER = (985, 535), 445            # Earth disc centre / radius in the SVS frame (measured)
ORB = (720, 300, -14)              # orbit ellipse rx, ry, tilt (deg)


def orbit_pt(th):
    rx, ry, tilt = ORB
    x, y = rx * math.cos(th), ry * math.sin(th)
    a = math.radians(tilt)
    return EC[0] + x * math.cos(a) - y * math.sin(a), EC[1] + x * math.sin(a) + y * math.cos(a)


def ship_theta(t):
    return 0.35 * (t - S7) + 0.4


def orbit(cv, t):
    fr = earth_video().at(8.0 + (t - S7) * 0.8)
    cv.a[:] = np.asarray(fr, np.float32)
    cv.a += starfield(13) * 0.25
    v = Vec()
    # orbit path: back half drawn before Earth occlusion is implied by dimming
    rx, ry, tilt = ORB
    pts = [orbit_pt(th) for th in np.linspace(0, 2 * math.pi, 240)]
    a0 = rng(t, S7, S7 + 1.0)
    for i in range(len(pts) - 1):
        th = 2 * math.pi * i / 239
        behind = math.sin(th) < 0 and math.hypot(pts[i][0] - EC[0], pts[i][1] - EC[1]) < ER
        v.line([pts[i], pts[i + 1]], (210, 230, 240), 3, a0 * (0.15 if behind else 0.7))
    # ground tracks accumulating (orbit counter)
    n_orb = int(1 + 13 * rng(t, S7_ORBITS - 0.2, S7_HOURS + 0.6)) if t >= S7_ORBITS - 0.2 else 1
    for j in range(n_orb if t >= S7_ORBITS - 0.2 else 0):
        off = j * 0.42
        tr = []
        for xx in np.linspace(-1, 1, 60):
            lon = xx * 1.4
            yy = 0.45 * math.sin(lon * 1.0 + off)
            px, py = EC[0] + ER * 0.98 * math.sin(lon) * 0.9 + 0, EC[1] + ER * yy * 0.9
            if abs(lon) < 1.3:
                tr.append((px, py))
        v.line(tr, YELLOW, 2, 0.35)
    v.onto(cv)
    th = ship_theta(t)
    sx, sy = orbit_pt(th)
    s, sm = ship_sprite(SHIP_BASE)
    nx_, ny_ = orbit_pt(th + 0.01)
    ang = math.degrees(math.atan2(-(nx_ - sx), -(ny_ - sy)))
    draw_vehicle(cv, s, sm, sx, sy, ang, 0.17)
    v = Vec()
    # altitude tag
    tag(v, '~275 km UP (MISSION PLAN)', sx + 40, sy - 50, CREAM, 24, rng(t, S7_ALT, S7_ALT + 0.4) * (1 - rng(t, S7_DEPLOY, S7_DEPLOY + 0.4)))
    # satellites leaving the ship
    nsat = int(26 * rng(t, S7_DEPLOY + 0.4, S7_CAMS - 0.2)) if t > S7_DEPLOY + 0.4 else 0
    for i in range(nsat):
        ti = S7_DEPLOY + 0.4 + (S7_CAMS - 0.6 - S7_DEPLOY) * i / 26
        age = max(0.0, t - ti)
        thi = ship_theta(ti) - 0.02 * age
        bx, by = orbit_pt(thi)
        dx, dy = (bx - EC[0]), (by - EC[1])
        dd = math.hypot(dx, dy)
        px, py = bx + dx / dd * (10 + 9 * age), by + dy / dd * (10 + 9 * age) + (i % 5 - 2) * 3 * age
        cam_sat = i in (5, 13, 21) and t >= S7_CAMS
        col = YELLOW if cam_sat else (220, 226, 236)
        v.rect(px - 7, py - 3, 14, 6, col, a=1.0)
        if cam_sat:
            k = rng(t, S7_CAMS + 0.3 + 0.3 * (i // 8), S7_CAMS + 0.9 + 0.3 * (i // 8)) * (1 - rng(t, S7_CIRCLE + 2.0, S7_CIRCLE + 2.6))
            v.line([(px, py), (sx, sy)], YELLOW, 2, k, dash=(8, 6))
            v.circle(px, py, 12, None, YELLOW, 2, k)
    cnt = rng(t, S7_DEPLOY, S7_DEPLOY + 0.4)
    if cnt > 0:
        v.rect(1380, 120, 470, 120, (6, 10, 18, 210), None, a=cnt, r=8)
        v.text('STARLINK V3 DEPLOYED', 1404, 166, 22, CREAM, 'm', a=cnt)
        v.text(f'{nsat:2d} / 26', 1404, 222, 48, (255, 255, 255), 'b', a=cnt)
    ck = rng(t, S7_CAMS + 0.4, S7_CAMS + 0.8) * (1 - rng(t, S7_CIRCLE + 2.0, S7_CIRCLE + 2.6))
    tag(v, '3 WITH HEAT-SHIELD CAMERAS (PLANNED)', 1380, 300, YELLOW, 22, ck)
    oc = rng(t, S7_ORBITS - 0.3, S7_ORBITS + 0.1)
    if oc > 0:
        v.rect(70, 120, 420, 230, (6, 10, 18, 210), None, a=oc, r=8)
        v.text('ORBIT', 96, 168, 24, CREAM, 'm', a=oc)
        v.text(f'{n_orb:2d}', 96, 280, 110, YELLOW, 'b', a=oc)
        v.text('/ 14', 270, 280, 50, (255, 255, 255), 'b', a=oc)
    hc = rng(t, S7_HOURS, S7_HOURS + 0.4)
    if hc > 0:
        v.text('22+ HOURS IN SPACE', 96, 330, 26, (255, 255, 255), 'b', a=hc)
    v.onto(cv)


# ------------------------------------------------------------------ 8. why returning from orbit is hard
def why_hard(cv, t):
    cv.a[:] = sky('space')
    cv.a += starfield(17) * 0.6
    v = Vec()
    # big Earth arc
    R = 1700
    cx, cy = 960, 1080 + R - 300
    pts = v.arc_pts(cx, cy, R, R, 200, 340, 160)
    v.poly(pts + [(W, H), (0, H)], (20, 56, 108))
    v.line(pts, (130, 200, 255), 8, 0.9)
    v.onto(cv)
    cv.glow(960, 860, 1100, (60, 130, 255), 0.22, 1.2)
    v = Vec()
    # orbit arc above
    Ro = R + 230
    orb = v.arc_pts(cx, cy, Ro, Ro, 205, 335, 160)
    v.line(orb, (210, 230, 240), 3, 0.5, dash=(14, 10))
    th = math.radians(228 + 22 * rng(t, S8, S9))
    sx, sy = cx + Ro * math.cos(th), cy + Ro * math.sin(th)
    tang = (-math.sin(th), math.cos(th))
    tang = (-tang[0], -tang[1]) if tang[0] < 0 else tang
    q = rng(t, S8_WHETHER, S8_WHETHER + 0.6) * (1 - rng(t, S8_SPEED - 0.4, S8_SPEED))
    if q > 0:
        tag(v, 'ORBIT  →  BACK TO A STEEL TOWER?', 640, 180, YELLOW, 30, q)
    vk = rng(t, S8_SPEED, S8_SPEED + 1.0)
    if vk > 0:
        L = 380 * vk
        ex, ey = sx + tang[0] * L, sy + tang[1] * L
        v.line([(sx, sy), (ex, ey)], YELLOW, 8, vk)
        v.poly([(ex + tang[0] * 26, ey + tang[1] * 26), (ex - tang[1] * 16, ey + tang[0] * 16), (ex + tang[1] * 16, ey - tang[0] * 16)], YELLOW, vk)
        sp = rng(t, c('seventeen thousand') - 0.2, c('seventeen thousand') + 0.4)
        tag(v, '~17,000 MPH  ·  ~28,000 KM/H', 1100, 180, (255, 255, 255), 32, sp)
    g = rng(t, S8_KEEP, S8_KEEP + 0.5)
    if g > 0:
        v.line([(sx, sy), (sx, sy + 160 * g)], (238, 136, 89), 6, g)
        v.text('GRAVITY', sx + 16, sy + 150, 22, (238, 136, 89), 'm', a=g)
        v.text('= FALLING AROUND EARTH', sx - 140, sy - 60, 24, (220, 228, 236), 'm', a=g * (1 - rng(t, S8_DROP, S8_DROP + 0.4)))
    d = rng(t, S8_DROP, S8_DROP + 0.6)
    if d > 0:
        v.line([(sx, sy), (sx, sy + 320)], (255, 255, 255), 4, 0.5 * d, dash=(10, 10))
        v.line([(sx - 26, sy + 140), (sx + 26, sy + 190)], RED, 7, d)
        v.line([(sx - 26, sy + 190), (sx + 26, sy + 140)], RED, 7, d)
        spiral = []
        for k in range(80):
            a = th + math.radians(k * 1.2)
            r = Ro - 260 * (k / 79) ** 1.6
            spiral.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        v.line(partial(spiral, rng(t, S8_DROP + 0.6, S8_DROP + 3.0)), CYAN, 5, d)
    e = rng(t, S8_ENERGY, S8_ENERGY + 0.5)
    if e > 0:
        drain = rng(t, S8_ENERGY + 0.6, S9 - 0.2)
        v.rect(1430, 300, 380, 60, (6, 10, 18, 220), (255, 255, 255, 120), 2, a=e, r=6)
        v.rect(1436, 306, 368 * (1 - 0.9 * drain), 48, (255, 170, 70), a=e, r=4)
        v.text('ENERGY TO SHED', 1430, 290, 22, CREAM, 'm', a=e)
    v.onto(cv)
    s, sm = ship_sprite(SHIP_BASE)
    ang = -math.degrees(math.atan2(tang[0], -tang[1]))
    draw_vehicle(cv, s, sm, sx, sy, ang, 0.2)


TIMELINE = [
    (S5, abort, 'SCHEMATIC MAP · NOT TO SCALE'),
    (S6, two_stories, 'ILLUSTRATION'),
    (S7, orbit, 'EARTH: NASA SVS VISUALIZATION · SHIP, ORBIT, SATELLITES: ILLUSTRATION'),
    (S8, why_hard, 'SCHEMATIC · NOT TO SCALE'),
]

SHOTS = [
    (S5, S6, 140, FLOOR, 0.72, 1),
    (S6, S7, 1700, FLOOR, 0.6, -1),
    (S7, S8, 230, FLOOR, 0.62, 1),
    (S8, S9, 1700, FLOOR, 0.74, -1),
]


def host(h):
    sb, start, ret, k, p_ab, div = _map_geom()
    # abort: walks in, follows the booster with his hand, stop-palm at the abort, points at "?"
    h.walk(S5 + 0.3, 90)
    h.point(S5_EARLIER + 0.4, (520, 690), S5_RETURN - 0.4, arm='n')
    h.point(S5_RETURN + 0.2, lambda t: partial(ret[:k + 1], rng(t, S5_RETURN, S5_CALLED + 0.2))[-1], S5_CALLED + 0.6, gaze_lead=0.1)
    h.support(S5_CALLED + 0.3, S5_RULED + 1.2, 'n', offset=(18.0, -30.0))
    h.brow(S5_CALLED + 0.2, -0.6, 1.4)
    h.point(S5_DIV + 0.2, lambda t: partial(div, rng(t, S5_DIV, S5_DIV + 2.6))[-1], S5_NOT + 1.0, gaze_lead=0.1)
    h.walk(S5_NOT + 1.3, 40)
    h.point(S5_REPORTS + 0.5, (1180, 600), S5_MATTERS - 0.2, arm='f')
    h.point(S5_MATTERS + 0.3, (640, 260), S6 - 0.4, arm='n')
    # two stories: watches the ship climb, walks a few steps
    h.gaze(S6 + 0.2, ('s', (1100, 500)), look=0.8)
    h.walk(S6 + 0.8, 80)
    h.point(S6_YET + 0.3, (1300, 380), S7 - 0.4, arm='f')
    # orbit: points at the ship (follows it), at the counter, at the orbits
    h.point(S7 + 0.4, lambda t: orbit_pt(ship_theta(t)), S7_DEPLOY - 0.2, gaze_lead=0.1)
    h.point(S7_DEPLOY + 0.3, (1500, 200), S7_CAMS + 1.8, arm='n')
    h.walk(S7_CIRCLE + 0.2, 70)
    h.point(S7_ORBITS + 0.1, (300, 250), S8 - 0.4, arm='f')
    # why hard: two steps, traces the velocity arrow, then the fall-around spiral
    h.walk(S8 + 0.5, 100)
    h.point(S8_SPEED + 0.4, (1150, 300), S8_KEEP - 0.1, arm='f')
    h.point(S8_KEEP + 0.2, (700, 520), S8_ENERGY - 0.3, arm='n')
    h.point(S8_ENERGY + 0.3, (1600, 330), S9 - 0.4, arm='f')
