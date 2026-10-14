"""Reusable, parameterised camera moves (VISUAL_REF_001 'camera motion'). Each preset returns Camera KEYS (see camera.Camera) so it plugs into
Scene(camera_keys=...). Class A (image-space) only: these are zooms and pans over one picture, not 3D flyovers.

  smooth_zoom   long eased move between scales (smoother ease)
  snap_zoom     fast in-out zoom with a short hold at the target: 'snap' ~0.30 s
  punch_zoom    very fast push (0.12 s, expo out) then a slow creep: emphasis on a revelation
  whip_to       fast pan/zoom to another point with a small rotation, expo-in-out (pair with camera blur; Scene blurs automatically above its speed threshold)
  pan           constant-height move, eased
  creep         barely perceptible push for long holds (avoids static frames)
  scale_change  world -> region as one move: pull back a little, then dive (the 'transition between geographic scales' of the reference)
Easing names come from easing.py; parameters (durations, heights) are explicit so a preset is data, not magic."""
# effect-reuse-checked: orbitalatlas.camera.Camera is the engine; these are named key generators on top of it (no camera presets existed; transitions.CinematicPush is a 2-frame blend).
from . import easing as E


def _k(t, c, h, ease="smoother", rot=0.0, **kw):
    d = dict(t=float(t), center=tuple(c), height=float(h), ease=ease, rot=rot); d.update(kw); return d


def hold(t0, center, height): return [_k(t0, center, height)]


def smooth_zoom(t0, dur, c0, h0, c1, h1): return [_k(t0, c0, h0, "smoother"), _k(t0 + dur, c1, h1)]


def snap_zoom(t0, c0, h0, c1, h1, dur=0.32, hold_s=0.0):
    ks = [_k(t0, c0, h0, "in_out_expo"), _k(t0 + dur, c1, h1)]
    if hold_s: ks.append(_k(t0 + dur + hold_s, c1, h1))
    return ks


def punch_zoom(t0, c, h, factor=0.82, dur=0.12, creep=0.04, creep_s=1.2):
    return [_k(t0, c, h, "out_expo"), _k(t0 + dur, c, h * factor, "linear"), _k(t0 + dur + creep_s, c, h * factor * (1 - creep))]


def whip_to(t0, c0, h0, c1, h1, dur=0.45, rot=3.0):
    mid = ((c0[0] + c1[0]) / 2, (c0[1] + c1[1]) / 2); hm = max(h0, h1) * 1.08
    return [_k(t0, c0, h0, "in_expo", 0.0), _k(t0 + dur * 0.5, mid, hm, "out_expo", rot), _k(t0 + dur, c1, h1, "smoother", 0.0)]


def pan(t0, dur, c0, c1, h, ease="in_out_cubic"): return [_k(t0, c0, h, ease), _k(t0 + dur, c1, h)]


def creep(t0, dur, c, h, amount=0.05, drift=(0.0, 0.0)): return [_k(t0, c, h, "linear"), _k(t0 + dur, (c[0] + drift[0], c[1] + drift[1]), h * (1 - amount))]


def scale_change(t0, c0, h0, c1, h1, dur=1.4, pullback=1.12):
    """world -> region (or back): a brief pull-back then a fast dive; the pull-back makes the scale change readable."""
    mid = ((c0[0] + c1[0]) / 2, (c0[1] + c1[1]) / 2)
    return [_k(t0, c0, h0, "out_cubic"), _k(t0 + dur * 0.28, mid, max(h0, h1) * pullback, "in_out_expo"), _k(t0 + dur, c1, h1)]


def join(*segments):
    """concatenate key lists; later keys replace earlier ones at the same time; sorted by t."""
    by = {}
    for seg in segments:
        for k in seg: by[round(k["t"], 6)] = k
    return [by[t] for t in sorted(by)]


PRESETS = ("smooth_zoom", "snap_zoom", "punch_zoom", "whip_to", "pan", "creep", "scale_change")
