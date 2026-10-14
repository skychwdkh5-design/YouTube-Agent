"""PlaneTilt: show a rendered map frame as a PLANE seen at an angle (the map lies on a neon floor grid that continues beyond its edges), animate the
tilt to flat. This is the honest version of the 'map in 3D space' look of the references: the picture is one flat image shown on a plane; nothing
pretends to be terrain or a flyover. At tilt 0 the output is the input frame, bit for bit.

PlaneTilt(scene, tilt_keys=[(t, deg)], grid=True) has the Scene interface (start, end, size, name, render, manifest) so a Sequence can use it."""
# effect-reuse-checked: transitions.CinematicPush is a 2D zoom of two frames; kinetic.tilt_25d tilts a word. No plane/floor-grid presentation existed.
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from . import easing as E
from .kinetic import _perspective


def plane_quad(W, H, deg, lift=0.0):
    """screen corners (tl, tr, br, bl) of a frame-sized plane tilted back by `deg` about its bottom edge, seen by a camera above it."""
    a = math.radians(max(0.0, min(80.0, deg))); depth = math.sin(a) * 0.9; shrink = 1.0 / (1.0 + depth)
    top_y = H * (1 - math.cos(a) * shrink) * 0.92 + lift * H; half_top = W / 2 * shrink
    return [(W / 2 - half_top, top_y), (W / 2 + half_top, top_y), (W, H), (0, H)]


class PlaneTilt:
    def __init__(self, scene, tilt_keys, grid=True, grid_color=(92, 225, 230), bg=(6, 9, 14), ease="in_out_cubic", name=None):
        self.scene, self.keys, self.grid, self.grid_color, self.bg, self.ease = scene, sorted(tilt_keys), grid, grid_color, bg, E.get(ease)
        self.size, self.name, self.reg = scene.size, name or scene.name, scene.reg
    @property
    def start(self): return self.scene.start
    @property
    def end(self): return self.scene.end
    @property
    def camera(self): return self.scene.camera
    def tilt(self, t):
        k = self.keys
        if t <= k[0][0]: return k[0][1]
        if t >= k[-1][0]: return k[-1][1]
        for (t0, a0), (t1, a1) in zip(k, k[1:]):
            if t0 <= t <= t1: return E.lerp(a0, a1, self.ease(E.seg(t, t0, t1)))
    def render(self, t, **kw):
        frame = self.scene.render(t, **kw); deg = self.tilt(t)
        if deg <= 0.05: return frame
        W, H = self.size; q = plane_quad(W, H, deg)
        out = Image.new("RGB", (W, H), self.bg)
        if self.grid:                                                      # floor grid in the plane's own coordinates, extending past the map
            g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g, "RGBA"); big = [(-W, -H * 2), (2 * W, -H * 2), (2 * W, H), (-W, H)]
            c = _perspective(q, [(0, 0), (W, 0), (W, H), (0, H)])
            inv = np.linalg.inv(np.array([[c[0], c[1], c[2]], [c[3], c[4], c[5]], [c[6], c[7], 1.0]]))
            def to_screen(px, py):
                v = inv @ np.array([px, py, 1.0]); return (v[0] / v[2], v[1] / v[2])
            n = 12; a = int(150 * min(1.0, deg / 25))
            for i in range(-n, 2 * n + 1):
                x = i * W / n; p0, p1 = to_screen(x, -H * 1.5), to_screen(x, H)
                d.line([p0, p1], fill=tuple(self.grid_color) + (a,), width=1)
            for j in range(-18, 7):
                y = j * H / 6; d.line([to_screen(-W, y), to_screen(2 * W, y)], fill=tuple(self.grid_color) + (a,), width=1)
            g = Image.alpha_composite(g.filter(ImageFilter.GaussianBlur(2)), g); out.paste(g, (0, 0), g)
        warped = frame.transform((W, H), Image.PERSPECTIVE, _perspective(q, [(0, 0), (W, 0), (W, H), (0, H)]), Image.BICUBIC)
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(q, fill=255); out.paste(warped, (0, 0), m)
        ImageDraw.Draw(out).line(q + [q[0]], fill=self.grid_color, width=2)                 # glowing plane edge
        return out
    def manifest(self):
        m = list(self.scene.manifest()) if hasattr(self.scene, "manifest") else []
        return m + [dict(type="PlaneTilt", cls="PRESENTATION", note="one flat picture shown on a tilted plane; not terrain, not a flyover", keys=self.keys)]
