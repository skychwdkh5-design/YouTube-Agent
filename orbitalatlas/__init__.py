"""OrbitalAtlas shared motion-graphics engine (numpy + Pillow + FFmpeg only).

Nothing in this package knows about a specific place, episode, label or claim. Project data (images,
anchors, outlines, text, timings) is passed in by the episode's scene files or spec dicts.

Camera classes: this package implements class A only (image-space camera: a crop window over the pixels of
one image). It is not a georeferenced map camera and not a 3D flyover (see docs/CINEMATIC_CAMERA_SYSTEM.md).
"""
from . import easing, camera, text, layers, timing, transitions, sequence, qa, synthetic, spec  # noqa: F401
__version__ = "0.1.0"
