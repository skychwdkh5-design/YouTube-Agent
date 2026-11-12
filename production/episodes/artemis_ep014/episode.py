"""EP014 Artemis II - five flashes. Scenes keyed to the narration by phrase (Cues).
The cover notebook (moon sketch, orange marks, capsule) is a CONCEPT ILLUSTRATION; the
science is told with NASA's own annotated simulation, photo and flyby material."""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine_path import *                     # noqa
from host import Host, Shot
from cues import Cues
from gfx import Frame, rng, smooth, lerp, Video
import scenes
from scenes import A, MARKS

VOICE_DIR = os.environ.get('EP014_VOICE', '/mnt/project-files/artemis/EP014/voice')
if not os.path.exists(os.path.join(VOICE_DIR, 'narration.voice.json')):
    VOICE_DIR = '/mnt/project-files/artemis/EP014/voice_temp'
VOICE_WAV = os.path.join(VOICE_DIR, 'narration.wav')
VOICE_JSON = os.path.join(VOICE_DIR, 'narration.voice.json')
TEMP = 'voice_temp' in VOICE_DIR
C = Cues(VOICE_JSON)
DUR = round(C.last_end() + 1.4, 2)

BIG = (250, 1800, 2.9, 1)
LEFT = (255, 985, 1.05, 1)


def c(p, after=0.0):
    return C.at(p, after)


S = {}
S['open'] = 0.0
S['notes1'] = c('Three astronauts aboard') - 0.2
S['geo1'] = c('And at that point') - 0.2
S['ecl'] = c("Here's what the crew") - 0.2
S['geo2'] = c('When Orion moved') - 0.25
S['mc'] = c('For a while') - 0.2
S['dark'] = c('This was a rare') - 0.25
S['impact'] = c('Picture a small') - 0.25
S['pin'] = c('From Orion, that flash') - 0.25
S['notes2'] = c('Now look at the annotations') - 0.2
S['views'] = c('An astronaut seeing') - 0.25
S['notes3'] = c('including cases where') - 0.2
S['mc2'] = c('Once communications came') - 0.25
S['dark2'] = c('This is why scientists') - 0.25
S['notes4'] = c('An observer who records') - 0.2
S['fin'] = c('That makes these little') - 0.25
ORDER = list(S.keys())
PLACE = {k: (BIG if k in ('open', 'fin') else LEFT) for k in ORDER}


def scene_at(t):
    cur = 'open'
    for k in ORDER:
        if t >= S[k]:
            cur = k
    return cur


def end_of(k):
    i = ORDER.index(k)
    return S[ORDER[i + 1]] if i + 1 < len(ORDER) else DUR


PUSH = (1.3, S['notes1'] - 0.2)
NOTE_Z = {'notes1': (1.0, 1.06), 'notes2': (1.0, 1.0), 'notes3': (1.25, 1.55), 'notes4': (1.0, 1.08)}


def note_z(k, t):
    a, b = NOTE_Z[k]
    return lerp(a, b, smooth((t - S[k]) / max(0.5, end_of(k) - S[k])))


def note_xy(key, k):
    return lambda t: scenes.notes_to_screen(scenes.NOTE[key], note_z(k, t))


def build_host(atlas):
    shots = [Shot(S[k] if k != 'open' else -5.0, end_of(k), *PLACE[k]) for k in ORDER]
    h = Host(atlas, shots, VOICE_WAV, VOICE_JSON, DUR, offset=0.0)
    mark = MARKS[2]
    # cover: pointing at the sketched mark from frame 0; glance to the viewer, back to the mark,
    # the camera then moves in on it
    h.point(-2.0, mark, PUSH[1] - 0.3, gaze_lead=0.0)
    h.gaze(0.45, None, look=-0.7)
    h.gaze(1.25, ('s', mark), look=0.9)
    h.brow(1.3, 0.7, 1.3)
    # NASA notes: the five marked pinpricks, then the distance
    s0, e = S['notes1'], end_of('notes1')
    h.point(s0 + 0.6, note_xy('m2', 'notes1'), c('forty-six thousand', s0) - 0.3)
    h.gaze(c('forty-six thousand', s0) - 0.1, ('s', (200, 380)), look=0.6)
    # geometry: the Moon between Orion and Earth
    s0, e = S['geo1'], end_of('geo1')
    h.walk(s0 + 0.3, 110)
    h.point(s0 + 1.5, lambda t: orion_xy(t), e - 0.3)
    # photo
    s0, e = S['ecl'], end_of('ecl')
    h.gaze(s0 + 0.2, ('s', (1350, 520)), look=0.8)
    # radio path blocked
    s0, e = S['geo2'], end_of('geo2')
    h.point(s0 + 0.5, lambda t: orion_xy(t), c('The Moon itself', s0) + 0.2)
    h.point(c('The Moon itself', s0) + 0.9, (1290, 450), e - 0.3)
    s0, e = S['mc'], end_of('mc')
    h.gaze(s0 + 0.3, ('s', (1000, 520)), look=0.7)
    s0, e = S['dark'], end_of('dark')
    h.point(s0 + 0.8, (980, 470), s0 + 3.2)
    # impact schematic: follow the rock, react to the flash
    s0, e = S['impact'], end_of('impact')
    h.walk(s0 + 0.3, 120)
    h.point(c('It can hit', s0) - 0.6, lambda t: rock_xy(t), c('A little of the', s0) + 1.6)
    h.brow(c('brief flash', s0), 0.8, 1.0)
    s0, e = S['pin'], end_of('pin')
    h.point(s0 + 0.3, (1200, 450), e - 0.3)
    # the crew's colours, one by one
    s0, e = S['notes2'], end_of('notes2')
    seq = [(c('Reid Wiseman', s0), 'reid'), (c('Victor Glover', s0), 'ike'), (c('Jeremy Hansen', s0), 'jeremy'),
           (c('General annotations', s0), 'purple')]

    def legend(t, seq=seq):
        key = seq[0][1]
        for tk, kk in seq:
            if t >= tk - 0.2:
                key = kk
        return scenes.notes_to_screen(scenes.NOTE[key], note_z('notes2', t))
    h.point(seq[0][0] - 0.6, legend, c('The drawing is', s0) + 0.6)
    h.point(c('compare across', s0) - 0.4, note_xy('m1', 'notes2'), e - 0.3)
    # images vs notes
    s0, e = S['views'], end_of('views')
    h.walk(s0 + 0.3, 100)
    h.point(c('The images give', s0) - 0.2, lambda t, tn=c('Their notes tell', s0), tp=c('Put those together', s0):
            (960, 410) if t < tn else ((1560, 400) if t < tp else (1260, 730)), e - 0.3)
    # same event, circled
    s0, e = S['notes3'], end_of('notes3')
    h.point(s0 + 0.4, note_xy('m4', 'notes3'), e - 0.3)
    s0, e = S['mc2'], end_of('mc2')
    h.gaze(s0 + 0.3, ('s', (1000, 480)), look=0.7)
    s0, e = S['dark2'], end_of('dark2')
    h.gaze(s0 + 0.3, ('s', (1300, 520)), look=0.7)
    s0, e = S['notes4'], end_of('notes4')
    h.point(s0 + 0.5, note_xy('m2', 'notes4'), e - 0.3)
    # finale on the cover: point at the sketch mark, then look at the viewer
    s0 = S['fin']
    h.point(s0 + 0.6, mark, DUR - 2.4)
    h.gaze(DUR - 2.0, None, look=-0.8)
    h.auto(emphasis=('five', 'dark', 'drop', 'blocked', 'rare', 'flash', 'pinprick', 'blue', 'green', 'red',
                     'purple', 'evidence', 'darkness', 'trace', 'marks'))
    return h


# ---------------------------------------------------------------- moving targets
def geo_p(t):
    k = scene_at(t)
    if k == 'geo1':
        return rng(t, S['geo1'] + 0.4, end_of('geo1') - 0.4) * 0.5
    return lerp(0.25, 0.9, rng(t, S['geo2'] + 0.3, end_of('geo2') - 0.6))


def orion_xy(t):
    p = geo_p(t)
    a = lerp(-1.1, 1.04, p)
    return ((860 + 230 * math.cos(a)) * 1.5, (300 + 230 * math.sin(a)) * 1.5)


def rock_p(t):
    s0 = S['impact']
    return rng(t, c('Picture a small', s0) + 0.3, c('It can hit', s0) + 0.9)


def rock_xy(t):
    p = rock_p(t)
    return (lerp(1240, 930, p) * 1.5, lerp(120, 1180 - 640 + 8, p) * 1.5)


# ---------------------------------------------------------------- frames
_FLY = None


def fly(ts):
    global _FLY
    if _FLY is None:
        _FLY = Video(A('flyby_12s.mp4'))
    return _FLY.at(ts)


def background(t):
    k = scene_at(t)
    s0, e = S[k], end_of(k)
    loc = t - s0
    if k == 'open':
        push = rng(t, *PUSH)
        img = scenes.cover(t, push=push, title_out=0.0, mark_pulse=rng(t, 1.3, 1.8))
        f = Frame(base=img)
        a = rng(t, PUSH[0] + 0.6, PUSH[0] + 1.2)
        if a > 0:
            f.pill('CONCEPT ILLUSTRATION  ·  MARKS ARE NOT OBSERVED LOCATIONS', 470, 690, 'paper', 15)
        return f.done()
    if k == 'fin':
        img = scenes.cover(2.0 + 0.5 * loc, push=0.0, title_out=0.0, mark_pulse=rng(t, s0 + 0.6, s0 + 1.2))
        return img
    f = Frame()
    if k.startswith('notes'):
        hi, hi_a, big_a = None, 0.0, 0.0
        if k == 'notes1':
            big_a = rng(t, c('forty-six thousand', s0) - 0.2, c('forty-six thousand', s0) + 0.3)
            hi, hi_a = 'm2', rng(loc, 0.6, 1.2) * (1 - rng(t, c('forty-six thousand', s0) - 0.3, c('forty-six thousand', s0)))
        elif k == 'notes2':
            seq = [(c('Reid Wiseman', s0), 'reid'), (c('Victor Glover', s0), 'ike'), (c('Jeremy Hansen', s0), 'jeremy'),
                   (c('General annotations', s0), 'purple')]
            for tk, kk in seq:
                if t >= tk - 0.2:
                    hi = kk
            hi_a = 1.0 if hi else 0.0
        elif k == 'notes3':
            hi, hi_a = 'purple', rng(loc, 0.5, 1.0)
        scenes.notes(f, t, note_z(k, t), hi, hi_a, big_a)
    elif k in ('geo1', 'geo2'):
        ba = rng(t, c('radio contact', S['geo2']), c('radio contact', S['geo2']) + 0.5) if k == 'geo2' else 0.0
        scenes.geometry(f, t, geo_p(t), ba)
    elif k == 'ecl':
        scenes.photo(f, t, 1.05 + 0.05 * smooth(loc / 6), 'ARTEMIS II  /  THE MOON FROM ORION', 'ARCHIVE PHOTO  ·  ART002E012278',
                     'NASA', path=A('eclipse.jpg'))
    elif k == 'dark2':
        scenes.photo(f, t, 1.12 + 0.08 * smooth(loc / 10), 'STARING INTO DARKNESS', 'ARCHIVE PHOTO  ·  ART002E012278',
                     'NASA', path=A('eclipse.jpg'))
    elif k in ('mc', 'mc2'):
        ts = lerp(4.15, 6.95, smooth(loc / max(0.5, e - s0))) if k == 'mc' else lerp(4.15, 5.9, smooth(loc / max(0.5, e - s0)))
        scenes.photo(f, t, 1.02, 'MISSION CONTROL' if k == 'mc' else 'CONTACT RESTORED', 'NASA FLYBY MATERIAL',
                     'NASA / SCIENTIFIC VISUALIZATION STUDIO', frame=fly(ts), fy=0.5)
    elif k == 'dark':
        ts = lerp(7.05, 11.9, smooth(loc / max(0.5, e - s0)))
        scenes.photo(f, t, 1.0, 'THE DARK LUNAR SURFACE', 'NASA FLYBY MATERIAL', 'NASA / SCIENTIFIC VISUALIZATION STUDIO',
                     frame=fly(ts), fy=0.5)
    elif k == 'impact':
        tf = c('brief flash', s0) if True else 0
        fl = rng(t, tf - 0.05, tf + 0.05) * (1 - rng(t, tf + 0.25, tf + 0.9))
        if rock_p(t) >= 1 and t < tf - 0.05:
            fl = max(fl, 0.6 * (1 - rng(t, c('It can hit', s0) + 0.9, c('It can hit', s0) + 1.3)))
        scenes.impact(f, t, rock_p(t), rng(t, c('no thick atmosphere', s0), c('no thick atmosphere', s0) + 0.4),
                      rng(t, c('high speed', s0), c('high speed', s0) + 0.4), fl, rng(t, tf, tf + 0.4))
    elif k == 'pin':
        scenes.pinprick(f, t, rng(loc, 0.5, 1.0))
    elif k == 'views':
        g = lambda p, d=0.5: rng(t, c(p, s0) - 0.1, c(p, s0) + d)
        scenes.views(f, t, g('The images give'), g('Their notes tell'), g('Put those together'), rng(loc, 0.3, 0.8))
    return scenes.retro(f.done())
