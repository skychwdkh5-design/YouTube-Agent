"""OrbitalAtlas shared motion-graphics engine (numpy + Pillow + FFmpeg only).

Nothing in this package knows about a specific place, episode, label or claim. Project data (images,
anchors, outlines, text, timings) is passed in by the episode's scene files or spec dicts.

Camera classes: `camera` is class A (image-space crop window over one image's pixels). `geo` is a georeferenced globe
camera driven by lon/lat vector data (class B, orthographic projection; no terrain, no imagery basemap, no perspective
tilt). Neither is a 3D flyover (see docs/CINEMATIC_CAMERA_SYSTEM.md).
"""
from . import easing, camera, text, layers, timing, transitions, sequence, qa, synthetic, spec, geo  # noqa: F401
__version__ = "0.2.0"
