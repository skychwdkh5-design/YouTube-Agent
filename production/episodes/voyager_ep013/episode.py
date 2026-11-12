"""EP013 Voyager 1 - full episode. Scenes are keyed to the narration by phrase (Cues), so
the same module renders on the real Adam narration or on the TEMP layout timing.

VOICE_DIR: /mnt/project-files/voyager/EP013/voice (real) or voice_temp (layout only).
ATLAS shots: BIG = cover framing (frame 0 == cover), LEFT / RIGHT = full figure on the
footer line, mirrored on the right. Placement changes only at cuts."""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine_path import *                     # noqa
from host import Host, Shot
from cues import Cues
from gfx import Frame, rng, smooth, lerp, clamp
import opening
import scenes
from scenes import A

VOICE_DIR = os.environ.get('EP013_VOICE', '/mnt/project-files/voyager/EP013/voice')
if not os.path.exists(os.path.join(VOICE_DIR, 'narration.voice.json')):
    VOICE_DIR = '/mnt/project-files/voyager/EP013/voice_temp'
VOICE_WAV = os.path.join(VOICE_DIR, 'narration.wav')
VOICE_JSON = os.path.join(VOICE_DIR, 'narration.voice.json')
TEMP = 'voice_temp' in VOICE_DIR
C = Cues(VOICE_JSON)
DUR = round(C.last_end() + 1.4, 2)

BIG = (263, 1830, 2.9, 1)
LEFT = (300, 985, 1.05, 1)
RIGHT = (1630, 985, 1.05, -1)
FADE_LEN = 3.0


def c(p, after=0.0):
    return C.at(p, after)


# ---------------------------------------------------------------- scene table
S = {}
S['open'] = 0.0
S['reply'] = c('If the spacecraft replies') - 0.15
S['listen'] = c('In October, NASA listened') - 0.15
S['back'] = c('And before engineers') - 0.15
S['dates'] = c('On October eighteenth') - 0.25
S['thr'] = c('Once engineers could see') - 0.25
S['trip'] = c("Here's what makes troubleshooting") - 0.25
S['dist'] = c('On November eighteenth, Voyager will') - 0.25
S['power'] = c('In September, the engineers') - 0.25
S['traj'] = c('Voyager left Earth') - 0.2
S['jup'] = c('It flew past Jupiter') - 0.1
S['pbd'] = c('In nineteen ninety') - 0.15
S['helio'] = c('In twenty twelve') - 0.25
S['fin'] = c('Now look at the timeline') - 0.25
ORDER = ['open', 'reply', 'listen', 'back', 'dates', 'thr', 'trip', 'dist', 'power', 'traj', 'jup', 'pbd', 'helio', 'fin']
PLACE = dict(open=BIG, reply=LEFT, listen=LEFT, back=BIG, dates=LEFT, thr=LEFT, trip=LEFT, dist=LEFT,
             power=LEFT, traj=RIGHT, jup=RIGHT, pbd=RIGHT, helio=LEFT, fin=BIG)


def scene_at(t):
    cur = 'open'
    for k in ORDER:
        if t >= S[k]:
            cur = k
    return cur


def end_of(k):
    i = ORDER.index(k)
    return S[ORDER[i + 1]] if i + 1 < len(ORDER) else DUR


FADE0 = 0.5
WAVE_Y = 640.0


def wave_end(t):
    return opening.cut_x(t, FADE0, FADE0 + FADE_LEN)


# --------------------------------------------------------------- dates geometry (screen px)
def row_xy(i):
    return ((470 + 25) * 1.5 - 20, (190 + 112 * i - 7) * 1.5)


def pbd_xy(t):
    ex, ey = _pbd_dot(smooth((t - S['pbd']) / 6.0))
    return ex * 1.5, ey * 1.5


def _pbd_dot(z):
    zoom = 1.0 + 0.6 * z
    fx, fy = 0.62, 0.52
    iw, ih = 2200, 2177
    sw = min(iw, ih * 1280 / 720) / zoom
    sh = sw * 720 / 1280
    x0, y0 = (iw - sw) * fx, (ih - sh) * fy
    return ((scenes.PB_EARTH[0] - x0) / sw * 1280, (scenes.PB_EARTH[1] - y0) / sh * 720)


# ---------------------------------------------------------------- ATLAS
def build_host(atlas):
    shots = []
    for k in ORDER:
        fx, fy, sc, fc = PLACE[k]
        shots.append(Shot(S[k] if k != 'open' else -5.0, end_of(k), fx, fy, sc, fc))
    h = Host(atlas, shots, VOICE_WAV, VOICE_JSON, DUR, offset=0.0)

    # 1. cover: pointing at the link from frame 0, the finger follows the fading end; reaction at the gap
    e = end_of('open')
    h.point(-2.0, lambda t: (min(wave_end(t) - 40, 900.0), WAVE_Y), e - 0.7, gaze_lead=0.0)
    h.brow(FADE0 + FADE_LEN - 0.4, 0.9, 1.4)
    h.gaze(e - 0.5, None, look=-0.7)
    # 2. reply leg: two steps along the link, then follow the returning pulse
    s0, e = S['reply'], end_of('reply')
    h.walk(s0 + 0.35, 130)
    h.point(s0 + 1.6, lambda t: pulse_reply_xy(t), e - 0.35)
    # 3. listened twice: point at the two NO SIGNAL rows in turn
    s0, e = S['listen'], end_of('listen')
    h.point(s0 + 0.5, lambda t, s0=s0, e=e: row_xy(0) if t < s0 + (e - s0) * 0.55 else row_xy(1), e - 0.3)
    # 4. back on its own: big framing again, line re-forms; he follows it to the probe, relieved
    s0, e = S['back'], end_of('back')
    tb = c('the signal came back', s0)
    h.point(tb - 0.4, lambda t: (min(back_end(t) - 40, 1000.0), WAVE_Y), e - 0.5, gaze_lead=0.2)
    h.brow(tb + 0.3, 0.7, 1.2)
    # 5. dates: three rows as the narration reaches each day
    s0, e = S['dates'], end_of('dates')
    r1, r2 = c('Twenty-four hours later', s0), c('On the twentieth', s0)
    h.walk(s0 + 0.3, 120)
    h.point(s0 + 1.6, lambda t: row_xy(0) if t < r1 else (row_xy(1) if t < r2 else row_xy(2)), e - 0.4)
    # 6. thrusters: group -> backup -> plaque
    s0, e = S['thr'], end_of('thr')
    t_off, t_on, t_why = c('had gone offline', s0), c('its backup had', s0), c('What triggered', s0)
    h.point(t_off - 0.6, lambda t: (1440, 300) if t < t_on else (1702, 300), t_why - 0.3)
    h.point(t_why + 0.2, (1185, 680), e - 0.4)
    # 7. round trip timeline: follow the pulse heads
    s0, e = S['trip'], end_of('trip')
    h.walk(s0 + 0.3, 110)
    h.point(T_SEND0 - 0.3, lambda t: trip_head_xy(t), T_REPLY1 + 0.5)
    h.point(T_BIG - 0.2, (1230, 285), T_BIG + 2.4)
    h.point(T_LOOP - 0.2, lambda t: (lerp(705, 1755, rng(t, T_LOOP, T_LOOP + 2.5)), 459), min(e - 0.4, T_LOOP + 3.0))
    # 8. distance
    s0, e = S['dist'], end_of('dist')
    h.point(c('sixteen billion miles', s0) - 0.4, (1180, 330), c('one light-day', s0) + 1.6)
    h.point(c("There's no marker", s0), (1180, 690), e - 0.4)
    # 9. power swap
    s0, e = S['power'], end_of('power')
    h.walk(s0 + 0.3, 100)
    h.point(c('They switched off', s0) - 0.3, lambda t, tt=c('turned on three', s0): (1000, 330) if t < tt else (1360, 330),
            c('keep the heat', s0))
    h.point(c('Without it', s0) - 0.2, (1180, 840), e - 0.4)
    # 10. history (mirrored, on the right)
    s0, e = S['traj'], end_of('traj')
    h.gaze(s0 + 0.3, ('s', (900, 520)), look=0.7)
    s0, e = S['jup'], end_of('jup')
    h.point(s0 + 0.4, (760, 520), e - 0.5)
    s0, e = S['pbd'], end_of('pbd')
    h.point(c('That little speck', s0) - 0.4, lambda t: pbd_xy(t), c('It had already', s0) + 1.5)
    # 11. heliopause
    s0, e = S['helio'], end_of('helio')
    h.walk(s0 + 0.3, 110)
    h.point(c('crossed the heliopause', s0) - 0.2, lambda t: helio_xy(t), e - 0.5)
    # 12. finale on the cover framing: hour 0 -> 24 -> 48
    s0 = S['fin']
    h.point(H0 - 0.3, lambda t: (fin_pulse_x(t) - 30, WAVE_Y), H48 + 1.4)
    h.brow(H48 + 0.2, 0.6, 1.6)
    h.gaze(DUR - 2.2, None, look=-0.8)
    h.auto(emphasis=('day', 'nothing', 'offline', 'automatically', 'immediately', 'alone', 'light-day',
                     'watt', 'warm', 'jupiter', 'earth', 'heliopause', 'remarkable', 'line'))
    return h


# ---------------------------------------------------------------- timed geometry helpers
def pulse_reply_xy(t):
    p = rng(t, S['reply'] + 0.3, end_of('reply') - 0.5)
    return (lerp(scenes.PROBE_X, scenes.EARTH_X, p) * 1.5, scenes.LINK_Y * 1.5)


def back_end(t):
    tb = c('the signal came back', S['back'])
    return lerp(720.0, opening.WAVE_X1 + 40, smooth((t - tb + 0.3) / 1.8))


_s = S['trip']
T_SEND0 = c('The first day goes by', _s)
T_SEND1 = c('At the end of that', _s)
T_HEAR = c('finally hears you', _s)
T_REPLY0 = c('If it responds immediately', _s)
T_REPLY1 = c('still on its way home', _s) + 0.8
T_BIG = c("That's forty-eight hours", _s)
T_LOOP = c('the next command', _s)


def trip_head_xy(t):
    if t < T_REPLY0:
        return (lerp(470, 820, rng(t, T_SEND0, T_SEND1 + 0.6)) * 1.5, 280 * 1.5)
    return (lerp(820, 1170, rng(t, T_REPLY0 + 0.6, T_REPLY1)) * 1.5, 280 * 1.5)


def helio_xy(t):
    s0, e = S['helio'], end_of('helio')
    p = lerp(0.35, 1.35, rng(t, s0 + 0.5, e - 1.0))
    a = math.radians(-28)
    r = 190 * 1.15
    return ((820 + r * p * math.cos(a)) * 1.5, (330 + r * 0.82 / 1.15 * p * math.sin(a) * 1.15) * 1.5)


_f = S['fin']
H0, H24, H48 = c('At hour zero', _f), c('At hour twenty-four', _f), c('At hour forty-eight', _f)
T_STILL = c("there's still something", _f)
FIN_X0, FIN_X1 = 470.0, 1150.0


def fin_pulse_x(t):
    if t < H24:
        return lerp(FIN_X0, FIN_X1, rng(t, H0 + 0.2, H24 + 0.3))
    return lerp(FIN_X1, FIN_X0, rng(t, H48 - 0.6, H48 + 0.9))


# ---------------------------------------------------------------- background per scene
def background(t):
    k = scene_at(t)
    loc = t - S[k]
    e = end_of(k)
    if k == 'open':
        img, _ = opening.cover_frame(t, fade=(FADE0, FADE0 + FADE_LEN))
        return img
    if k == 'back':
        img, _ = opening.cover_frame(2.0 + 0.4 * loc, fade=(-10, -9), back_t=None, text_out=(-2, -1), cam_push=0.001,
                                     back_end=back_end(t))
        f = Frame(base=img)
        a = rng(t, c('the signal came back', S['back']) + 0.6, c('the signal came back', S['back']) + 1.1)
        if a > 0:
            stamp(f, 'SIGNAL BACK  ·  OCT 20, 2026', 60, 150, a)
        return f.done()
    if k == 'fin':
        img, _ = opening.cover_frame(2.0 + 0.4 * loc, fade=(-10, -9), text_out=(-2, -1), back_end=opening.WAVE_X1 + 40, cam_push=0.001)
        f = Frame(base=img)
        finale_marks(f, t)
        return f.done()
    f = Frame()
    if k == 'reply':
        p = rng(t, S['reply'] + 0.3, e - 0.5)
        scenes.signal(f, t, 1, p, '+1 DAY BACK', 'THE REPLY TRAVELS AS FAR AGAIN', title_a=rng(loc, 0.3, 0.8))
    elif k == 'listen':
        h = rng(loc, 0.2, 0.7), rng(t, S['listen'] + (e - S['listen']) * 0.45, S['listen'] + (e - S['listen']) * 0.55)
        scenes.dates(f, t, A('dish.jpg'), loc / 8, [h[0], h[1], 0], [0, 0, 0],
                     'NASA / CANBERRA DEEP SPACE COMMUNICATION COMPLEX', kick='DSN ANTENNA (EXAMPLE)  /  OCTOBER 2026')
    elif k == 'dates':
        r1, r2 = c('Twenty-four hours later', S['dates']), c('On the twentieth', S['dates'])
        scenes.dates(f, t, A('dish.jpg'), loc / 12, [rng(loc, 0.3, 0.8), rng(t, r1, r1 + 0.4), rng(t, r2, r2 + 0.4)],
                     [0, 0, 1], 'NASA / CANBERRA DEEP SPACE COMMUNICATION COMPLEX',
                     kick='DSN ANTENNA (EXAMPLE)  /  OCTOBER 2026')
    elif k == 'thr':
        s0 = S['thr']
        t_off, t_on = c('had gone offline', s0), c('its backup had', s0)
        t_auto, t_why = c('automatically', s0), c('What triggered', s0)
        scenes.thrusters(f, t, rng(t, t_off, t_off + 0.5), rng(t, t_on + 0.2, t_on + 0.7), rng(t, t_auto, t_auto + 0.5),
                         rng(t, t_why, t_why + 0.5))
    elif k == 'trip':
        marks = [rng(t, T_SEND0 - 0.3, T_SEND0), rng(t, T_HEAR - 0.2, T_HEAR + 0.2), rng(t, T_REPLY1 - 0.3, T_REPLY1 + 0.1)]
        scenes.round_trip(f, t, rng(t, T_SEND0, T_SEND1 + 0.6), rng(t, T_REPLY0 + 0.6, T_REPLY1), marks,
                          rng(t, T_BIG, T_BIG + 0.5), rng(t, T_LOOP, T_LOOP + 2.5))
    elif k == 'dist':
        s0 = S['dist']
        scenes.distance(f, t, rng(loc, 0.2, 3.0), rng(t, c('sixteen billion miles', s0) - 0.2, c('sixteen billion miles', s0) + 0.3),
                        rng(t, c('one light-day', s0), c('one light-day', s0) + 0.4),
                        rng(t, c("There's no marker", s0), c("There's no marker", s0) + 0.4))
    elif k == 'power':
        s0 = S['power']
        g = lambda p, d=0.5: rng(t, c(p, s0), c(p, s0) + d)
        scenes.power(f, t, g('They switched off'), g('turned on three'), g('Those devices help'), g('all three swaps'),
                     g('The change bought'), g('Without it'))
    elif k == 'traj':
        scenes.trajectory(f, t, min(11.9, 1.0 + loc * 1.6))
    elif k == 'jup':
        scenes.jupiter(f, t, min(3.7, loc * min(1.0, 3.6 / max(0.1, e - S['jup']))))
    elif k == 'pbd':
        s0 = S['pbd']
        scenes.paleblue(f, t, smooth(loc / 6.0), rng(t, c('That little speck', s0) - 0.2, c('That little speck', s0) + 0.3),
                        rng(loc, 0.4, 0.9))
    elif k == 'helio':
        s0 = S['helio']
        scenes.heliopause(f, t, rng(t, s0 + 0.5, e - 1.0), rng(t, c('the heliopause', s0), c('the heliopause', s0) + 0.4),
                          rng(t, c('interstellar space', s0), c('interstellar space', s0) + 0.5))
    return scenes.retro(f.done())


def stamp(f, s, x, y, a, color='ice', n=30):
    f.group(a)
    w = f.text_w(s, n, 'sans') + 40
    f.rect(x, y - 40, w, 56, (20, 12, 10, 225), scenes.PAL['ice'] + (160,), 2)
    f.text(s, x + 20, y - 2, n, color, 'sans')
    f.end()


def finale_marks(f, t):
    y = WAVE_Y / 1.5
    xs = [FIN_X0 / 1.5, FIN_X1 / 1.5, FIN_X0 / 1.5]
    hs = [H0, H24, H48]
    lab = ['HOUR 0', 'HOUR 24', 'HOUR 48']
    sub = ['SIGNAL LEAVES EARTH', 'VOYAGER HEARS IT', 'EARTH HEARS BACK']
    for k in range(3):
        a = rng(t, hs[k] - 0.1, hs[k] + 0.4)
        if a <= 0:
            continue
        yy = y - 85 if k != 2 else y + 128
        xx = xs[k] if k != 1 else xs[k] - 70
        f.text(lab[k], xx, yy, 30, 'amber' if k == 2 else 'ice', 'sans', 'center', alpha=a)
        f.text(sub[k], xx, yy + 24, 14, 'paper', 'mono', 'center', alpha=a)
    if t >= H0:
        px = fin_pulse_x(t) / 1.5
        col = scenes.PAL['amber'] if t >= H48 - 0.6 else scenes.PAL['ice']
        f.glow(px, y, 46, col)
        f.circle(px, y, 6, col)
    a = rng(t, T_STILL, T_STILL + 0.6)
    if a > 0:
        f.text('STILL SOMETHING ON THE', 300, 130, 40, 'paper', 'sans', alpha=a)
        f.text('OTHER END OF THE LINE', 300, 182, 40, 'amber', 'sans', alpha=a)
