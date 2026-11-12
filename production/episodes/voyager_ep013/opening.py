"""Voyager opening: the approved SIGNAL LOST cover, animated by its layers.
Frame 0 == cover. Then the link line fades from the far end (signal lost), a gap opens,
and later the line re-forms all the way to the probe (signal back)."""
import math
import numpy as np
from engine_path import *            # noqa
from layers import Stack, W, H
from gfx import smooth, rng, lerp

LAYERS = '/mnt/project-files/voyager/EP013/cover/layers'
STACK = Stack(LAYERS)
WAVE_X0, WAVE_X1 = 430.0, 1165.0       # painted waveform + dashes, screen px


def wave_mask(cut, back=0.0, flicker_t=None):
    """cut: x where the line now ends (signal fading from the far end).
    back: 0..1, line re-forms from the cut to the far end."""
    xs = np.arange(W, dtype=np.float32)
    end = lerp(cut, WAVE_X1 + 40, smooth(back))
    m = np.clip((end - xs) / 70.0, 0, 1)
    if flicker_t is not None:
        # a weak, irregular flicker near the end of the line while it fades
        f = 0.75 + 0.25 * math.sin(flicker_t * 23.0) * math.sin(flicker_t * 7.3)
        near = np.clip((xs - (end - 260)) / 260, 0, 1)
        m = m * (1 - near * (1 - f))
    return np.broadcast_to(m[None, :], (H, W))


def cut_x(t, t_fade0, t_fade1):
    return lerp(WAVE_X1 + 40, 720.0, smooth((t - t_fade0) / (t_fade1 - t_fade0)))


def cover_frame(t, fade=(0.5, 3.4), back_t=None, text_out=None, cam_push=0.006, back_end=None):
    """t: seconds since frame 0. back_t: (t0, t1) when the signal re-forms.
    text_out: (t0, t1) the title slides up and fades (for the cut to the story)."""
    c = cut_x(t, *fade)
    back = rng(t, *back_t) if back_t else 0.0
    to = rng(t, *text_out) if text_out else 0.0
    probe_s = 1 + 0.010 * t
    spec = [
        ('plate', {}),
        ('probe', dict(s=probe_s, cx=1690, cy=730, dx=-3.0 * t, dy=-1.0 * t)),
        ('lost', dict(dy=-1.2 * t - 60 * to, alpha=1 - to)),
        ('signal', dict(dy=-1.8 * t - 80 * to, alpha=1 - to)),
        ('wave', dict(mask=(wave_mask(back_end, 0.0, None) if back_end is not None else
                            (None if t <= 1e-6 else wave_mask(c, back, t if back < 0.99 else None))))),
    ]
    return STACK.render(spec, cam=(0.0, 0.0, 1 + cam_push * t, 760, 640)), c
