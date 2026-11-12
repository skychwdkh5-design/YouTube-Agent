"""Test fragment (12 s): Voyager opening from the approved cover + a cut to the signal
diagram with steps and a pointing gesture. Voice: existing EP012 Adam narration (offset)
used ONLY to test lip-sync; the real Voyager narration replaces it in the episode."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'voyager_ep013'))
from engine_path import *                     # noqa
from host import Host, Shot
from gfx import Frame, rng, smooth, lerp
import opening
import scenes

DUR = 12.0
VOICE_WAV = '/mnt/project-files/bennu/EP012/voice/narration.wav'
VOICE_JSON = '/mnt/project-files/bennu/EP012/voice/narration.voice.json'
OFFSET = 298.89
CUT = 5.2
FADE = (0.6, 3.6)


def build_host(atlas):
    shots = [Shot(-5.0, CUT, 263, 1830, 2.9, 1), Shot(CUT, 99, 300, 985, 1.05, 1)]
    h = Host(atlas, shots, VOICE_WAV, VOICE_JSON, DUR, offset=OFFSET)
    # cover pose: already pointing at the line at frame 0, the finger then follows the fading end
    h.point(-2.0, lambda t: (min(opening.cut_x(t, *FADE) - 40, 900.0), 640.0), 4.5, gaze_lead=0.0)
    h.brow(3.0, 0.8, 1.6)                       # reaction when the line is gone
    # shot 2: two steps toward the diagram, then point at the outbound pulse
    h.walk(CUT + 0.7, 150)
    h.point(CUT + 3.1, lambda t: pulse_xy(t), DUR - 1.0)
    h.auto(emphasis=('signal', 'day', 'hours'))
    return h


def pulse_xy(t):
    p = rng(t, CUT + 0.4, DUR - 0.6)
    x = lerp(scenes.EARTH_X, scenes.PROBE_X, p) * 1.5
    return (x, scenes.LINK_Y * 1.5)


def background(t):
    if t < CUT:
        img, _ = opening.cover_frame(t, fade=FADE)
        return img
    tt = t - CUT
    f = Frame()
    p = rng(t, CUT + 0.4, DUR - 0.6)
    scenes.signal(f, t, 0, p, 'ONE DAY', 'ONE WAY  ·  SIGNAL AT THE SPEED OF LIGHT', title_a=rng(tt, 0.5, 1.1))
    return scenes.retro(f.done())
