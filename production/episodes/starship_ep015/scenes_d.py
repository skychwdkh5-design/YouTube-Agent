"""EP015 scenes 13-16: not reusable yet (inspection checklist), why it matters (reuse loop,
dream vs data), next milestones, outro at dawn."""
from common import *   # noqa
from host import seq   # noqa: E402

S13 = c('This is where a lot') - 0.2
S13_NOTSAME = c('Catching a spacecraft') - 0.1
S13_INSPECT = c('Engineers still') - 0.1
S13_LIST = c('The heat shield, the') - 0.1
S13_ONE = c('One catch does') - 0.1
S13_BOOST = c('And remember') - 0.1
S14 = c('So why does') - 0.2
S14_BRING = c('Because bringing') - 0.1
S14_AGAIN = c('fly again, instead') - 0.1
S14_NEW = c('building a new one') - 0.1
S14_DREAM = c("That's the dream") - 0.1
S14_NOTDATA = c('But the dream') - 0.1
S14_DATA = c('The data, as') - 0.1
S14_D1 = c('one historic catch') - 0.1
S14_D2 = c('twenty-six satellites deployed,') - 0.1
S14_D3 = c('one lost booster') - 0.1
S15 = c('What comes next') - 0.2
S15_M = [c('inspect this ship') - 0.1, c('fly it again') - 0.1, c('repeat the process') - 0.1, c('both stages') - 0.6]
S15_WATCH = c('Those are the') - 0.1
S16 = c("I'm Atlas") - 0.2
S16_HOME = c('rocket came home') - 0.3
S16_ORD = c('look ordinary') - 0.3
CHECK = ['HEAT SHIELD', 'ENGINES', 'PLUMBING', 'STRUCTURE']
CHECK_T = [c('The heat shield, the') + 0.1, c('the engines,') - 0.05, c('the plumbing') - 0.05, c('the structure') - 0.05]


def headlines(cv, t):
    cv.a[:] = sky('studio')
    # left: the caught ship in the tower (small, scanned)
    def f(c2):
        cam = Cam(1450, 420, 1.0)
        catch_set(c2, t, cam, (None, None), 0.0, 0.5, plume_k=0.0, light=0.5, kind='night', steam=0.3)
    sub = sub_canvas(f, 640, 720)
    a0 = rng(t, S13_INSPECT - 0.2, S13_INSPECT + 0.4)
    if a0 > 0:
        place_rgb(cv, sub, 980, 110, a0)
    v = Vec()
    # over-excited headline, struck out
    h = rng(t, S13, S13 + 0.4) * (1 - rng(t, S13_INSPECT - 0.4, S13_INSPECT))
    if h > 0:
        v.rect(360, 230, 1200, 230, (240, 236, 228), a=h, r=6)
        v.text('"STARSHIP IS NOW', 960, 320, 64, (20, 20, 24), 'b', 'ms', h)
        v.text('FULLY REUSABLE!"', 960, 410, 64, (20, 20, 24), 'b', 'ms', h)
        st = rng(t, S13_NOTSAME, S13_NOTSAME + 0.3)
        v.line([(380, 470), (1540, 220)], RED, 14, h * st)
        tag(v, 'CAUGHT  ≠  READY TO FLY AGAIN', 620, 560, YELLOW, 34, h * st)
    if a0 > 0:
        panel(cv, v, 980, 110, 640, 720, a0)
        scan = (t * 0.6) % 1
        v.line([(990, 120 + 700 * scan), (1610, 120 + 700 * scan)], CYAN, 3, 0.7 * a0)
        v.text('INSPECTION', 1000, 800, 24, CYAN, 'm', a=a0)
    # checklist
    for i, (name, tc) in enumerate(zip(CHECK, CHECK_T)):
        k = rng(t, tc, tc + 0.3)
        if k <= 0:
            continue
        y = 200 + i * 100
        v.rect(420, y, 46, 46, None, (255, 255, 255), 3, a=k, r=6)
        v.text(name, 490, y + 38, 40, (255, 255, 255), 'b', a=k)
        v.text('PENDING', 900, y + 38, 22, YELLOW, 'm', 'rs', a=k)
    one = rng(t, S13_ONE, S13_ONE + 0.4)
    if one > 0:
        v.rect(420, 640, 480, 110, (6, 10, 18, 220), (255, 255, 255, 90), 2, a=one, r=8)
        v.text('SHIP CATCHES FROM ORBIT: 1', 444, 684, 24, (255, 255, 255), 'm', a=one)
        v.text('ROUTINE REUSE: NOT YET', 444, 726, 24, YELLOW, 'm', a=one)
    bo = rng(t, S13_BOOST, S13_BOOST + 0.4)
    if bo > 0:
        v.rect(420, 770, 480, 60, (6, 10, 18, 220), (255, 86, 60, 160), 2, a=bo, r=8)
        v.text('THIS FLIGHT: BOOSTER LOST', 444, 810, 24, RED, 'm', a=bo)
    v.onto(cv)


def loop_pts(cx, cy, r, n):
    return [(cx + r * math.cos(math.radians(-90 + 360 * i / n)), cy + r * math.sin(math.radians(-90 + 360 * i / n))) for i in range(n)]


def matters(cv, t):
    cv.a[:] = sky('studio')
    v = Vec()
    out = rng(t, S14_NOTDATA - 0.2, S14_NOTDATA + 0.4)
    a = rng(t, S14, S14 + 0.4) * (1 - out)
    if a > 0:
        # old way: build -> launch -> gone (faded, left)
        old = rng(t, S14_NEW, S14_NEW + 0.4)
        for i, s in enumerate(['BUILD', 'LAUNCH', 'DISCARD']):
            v.text(s, 300, 300 + i * 120, 32, (170, 176, 188), 'b', 'ms', a * old * 0.9)
            if i < 2:
                v.line([(300, 316 + i * 120), (300, 384 + i * 120)], (170, 176, 188), 3, a * old)
        v.text('EXPENDABLE', 300, 220, 24, (238, 136, 89), 'm', 'ms', a * old)
        # reuse loop
        nodes = ['BUILD', 'LAUNCH', 'CATCH', 'INSPECT', 'FLY AGAIN']
        P = loop_pts(1060, 480, 280, 5)
        tms = [S14_BRING + 0.3, S14_BRING + 0.9, S14_BRING + 1.5, S14_AGAIN - 0.6, S14_AGAIN]
        for i, (p, s, tm) in enumerate(zip(P, nodes, tms)):
            k = rng(t, tm, tm + 0.4) * a
            if k <= 0:
                continue
            done = i <= 2
            col = (120, 230, 150) if done else YELLOW
            v.circle(p[0], p[1], 70, (10, 16, 26), col, 4, k)
            v.text(s, p[0], p[1] + 10, 24, (255, 255, 255), 'b', 'ms', k)
            q = P[(i + 1) % 5]
            mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            dash = None if i < 2 else (14, 10)
            v.line(partial([p, q], rng(t, tm + 0.2, tm + 0.8)), col, 4, k * 0.8, dash=dash)
        v.text('DONE ONCE', 1450, 300, 24, (120, 230, 150), 'm', a=rng(t, S14_AGAIN, S14_AGAIN + 0.4) * a)
        v.text('THE GOAL', 1450, 340, 24, YELLOW, 'm', a=rng(t, S14_AGAIN, S14_AGAIN + 0.4) * a)
        dr = rng(t, S14_DREAM, S14_DREAM + 0.4) * a
        tag(v, 'THE DREAM: CHEAPER, MORE ROUTINE ACCESS TO ORBIT', 560, 860 - 40, YELLOW, 28, dr)
    if out > 0:
        v.text('DREAM', 560, 220, 70, (170, 176, 188), 'b', 'ms', out * (1 - 0.4 * rng(t, S14_DATA, S14_DATA + 0.5)))
        v.text('≠', 960, 220, 70, (255, 255, 255), 'b', 'ms', out)
        v.text('DATA', 1360, 220, 70, YELLOW, 'b', 'ms', out)
        items = [('1 HISTORIC SHIP CATCH', '✓', (120, 230, 150), S14_D1), ('26 SATELLITES DEPLOYED', '✓', (120, 230, 150), S14_D2),
                 ('1 BOOSTER LOST', '✗', RED, S14_D3)]
        for i, (s, mk, col, tm) in enumerate(items):
            k = rng(t, tm, tm + 0.35) * out
            if k <= 0:
                continue
            y = 380 + i * 130
            v.rect(980, y, 760, 100, (6, 10, 18, 220), col + (150,), 2, a=k, r=10)
            v.text(mk, 1020, y + 68, 54, col, 'b', a=k)
            v.text(s, 1100, y + 64, 40, (255, 255, 255), 'b', a=k)
        v.text('AS OF NOV 15, 2026', 1740, 800, 22, (170, 180, 192), 'm', 'rs', rng(t, S14_DATA, S14_DATA + 0.4))
    v.onto(cv)


def nextm(cv, t):
    cv.a[:] = sky('studio')
    v = Vec()
    labels = ['INSPECT SHIP 42', 'FLY IT AGAIN', 'REPEAT RELIABLY', 'CATCH BOTH STAGES, SAME FLIGHT']
    for i, (s, tm) in enumerate(zip(labels, S15_M)):
        k = rng(t, tm, tm + 0.4)
        x, y = 560 + i * 300, 760 - i * 150
        v.rect(x, y, 280, 18, (90, 100, 116), a=rng(t, S15, S15 + 0.5), r=4)
        if k > 0:
            v.circle(x + 140, y - 46, 30, (10, 16, 26), YELLOW, 4, k)
            v.text('?', x + 140, y - 32, 36, YELLOW, 'b', 'ms', k)
            v.text(s, x + 140, y + 60, 24 if i < 3 else 21, (255, 255, 255), 'b', 'ms', k)
    w = rng(t, S15_WATCH, S15_WATCH + 0.5)
    v.text('MILESTONES TO WATCH', 960, 180, 56, YELLOW, 'b', 'ms', w, 5)
    v.onto(cv)


def outro(cv, t):
    u = rng(t, S16, DUR_GUESS)
    cam = Cam(lerp(1150, 1220, u), lerp(470, 380, u), lerp(0.78, 0.86, u))
    catch_set(cv, t, cam, (None, None), 0.0, 0.5, plume_k=0.0, light=0.35, kind='dawn', steam=0.4, stars=0.2)
    cv.glow(1700, 760, 700, (255, 200, 140), 0.25)
    fade = rng(t, DUR_GUESS - 1.6, DUR_GUESS - 0.1)
    if fade > 0:
        cv.a *= (1 - fade)


DUR_GUESS = C.duration

TIMELINE = [
    (S13, headlines, 'ILLUSTRATION'),
    (S14, matters, 'SCHEMATIC'),
    (S15, nextm, ''),
    (S16, outro, 'ILLUSTRATION'),
]

SHOTS = [
    (S13, S14, 160, FLOOR, 0.68, 1),
    (S14, S14_NOTDATA - 0.2, 1700, FLOOR, 0.72, -1),
    (S14_NOTDATA - 0.2, S15, 300, FLOOR, 0.72, 1),
    (S15, S16, 160, FLOOR, 0.74, 1),
    (S16, C.duration + 1, 420, FLOOR, 1.05, 1),
]


def host(h):
    # headlines: points at the struck headline, counts the checklist items with the near hand
    h.point(S13_NOTSAME + 0.2, (900, 330), S13_INSPECT - 0.3, arm='f')
    h.gaze(S13_INSPECT + 0.1, ('s', (1300, 450)), look=0.8)
    # one arm sweeps down the list (no alternating flicks between arms)
    h.point(CHECK_T[0] + 0.05, seq([(CHECK_T[i] + 0.05, (470, 220 + i * 100)) for i in range(4)], blend=0.4),
            CHECK_T[3] + 1.1, arm='n')
    h.walk(S13_ONE + 0.2, 50)
    h.point(S13_BOOST + 0.3, (660, 800), S14 - 0.4, arm='f')
    # matters: loop builds; points at catch, then at the dashed goal
    h.point(S14_BRING + 1.0, (1300, 600), S14_AGAIN - 0.4, arm='f')
    h.point(S14_AGAIN + 0.3, (880, 600), S14_DREAM + 1.4, arm='n')
    h.walk(S14_DREAM + 1.6, 60)
    # dream vs data: turns to the viewer, then ticks off the data
    h.gaze(S14_NOTDATA, None, look=-0.9)
    h.point(S14_D1, (1100, 430), S14_D3 + 1.0, arm='f')
    h.support(S14_D2 - 0.2, S15 - 0.6, 'n')
    # next: steps forward up the ladder, points at each milestone
    h.walk(S15 + 0.3, 110)
    h.point(S15_M[0] + 0.05, seq([(S15_M[i] + 0.05, (700 + i * 300, 714 - i * 150)) for i in range(4)], blend=0.5),
            S15_WATCH + 0.8, arm='f')
    # outro: to camera, open palm, small step
    h.gaze(S16, None, look=-0.95)
    h.support(S16 + 0.4, S16 + 2.6, 'n', offset=(14.0, -20.0))
    h.walk(S16_HOME - 0.8, 50)
    h.support(S16_ORD - 0.6, S16_ORD + 1.4, 'f', offset=(12.0, -16.0))
