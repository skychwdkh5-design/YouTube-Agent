"""scene3d - a small perspective renderer for schematic 3-D illustrations (numpy + Pillow, no GPU, no 3-D package).

What it is: a pinhole camera (`Camera3D`) with a smooth keyframed path (`CameraPath`, monotone cubic per coordinate), and a painter
(`Painter`) that shades flat polygons (Lambert + ambient), fades them into fog by depth, sorts them back to front and draws them on a 2x
supersampled canvas; lines/rings/points can be depth-sorted or drawn on top with glow. Near-plane clipping for lines; polygons that cross
the near plane are dropped (scenes keep geometry in front of the camera).

What it is not: a georeferenced camera (no CRS, no terrain data) and not a photoreal renderer. Use it for ILLUSTRATION scenes only
(class shown on screen); evidence imagery keeps its own camera classes (docs/ORBITALATLAS_VISUAL_MASTER.md s.4).
"""
# effect-reuse-checked: plane.PlaneTilt is a 2-D quad tilt of one image and geo.GlobeView an orthographic globe of vector data; neither renders
# 3-D polygons with a perspective camera, depth sorting, shading or fog. tools/cesium_proof needs a browser/WebGL and a token (registry).
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from . import easing as E

SS = 2


def _n(v): v = np.asarray(v, float); return v / max(float(np.linalg.norm(v)), 1e-12)


class Camera3D:
    """pinhole camera. World: right-handed, z up. Screen: x right, y down (pixels of `size`)."""
    def __init__(self, pos, target, fov_deg=40.0, size=(1920, 1080), up=(0, 0, 1), near=0.5, shift=(0.0, 0.0)):
        """shift: principal-point offset in pixels (a shifted lens, like a tilt-shift view camera): moves the picture without turning the camera,
        so a plane parallel to the image stays undistorted (angles preserved)."""
        self.pos = np.asarray(pos, float); self.size = size; self.near = near; self.fov = fov_deg; self.shift = (float(shift[0]), float(shift[1]))
        f = _n(np.asarray(target, float) - self.pos); upv = np.asarray(up, float)
        if abs(float(f @ _n(upv))) > 0.999: upv = np.array([0.0, 1.0, 0.0])          # looking straight down: use +y as up
        r = _n(np.cross(f, upv)); u = np.cross(r, f)
        self.R = np.stack([r, u, f]); self.focal = (size[1] / 2) / math.tan(math.radians(fov_deg) / 2)

    def to_cam(self, P): return (np.atleast_2d(np.asarray(P, float)) - self.pos) @ self.R.T

    def project(self, P):
        """world points (N,3) -> screen (N,2) and depth (N,) along the view axis (negative = behind the camera)."""
        c = self.to_cam(P); z = c[:, 2]; zz = np.where(np.abs(z) < 1e-9, 1e-9, z)
        W, H = self.size; return np.stack([W / 2 + self.shift[0] + self.focal * c[:, 0] / zz, H / 2 + self.shift[1] - self.focal * c[:, 1] / zz], 1), z

    def forward(self): return self.R[2]


class CameraPath:
    """keys: [(t, pos, target, fov[, shift_y_px])]; each coordinate follows a monotone cubic through the keys (continuous velocity, no overshoot),
    so the camera never stops dead between keys unless two keys repeat the same value."""
    def __init__(self, keys, size=(1920, 1080)):
        self.keys = sorted(keys, key=lambda k: k[0]); self.size = size; self.ts = [k[0] for k in self.keys]
        self._ch = []; rows = [list(k[1]) + list(k[2]) + [k[3], (k[4] if len(k) > 4 else 0.0)] for k in self.keys]
        for comp in range(8):
            ys = [r[comp] for r in rows]; self._ch.append((ys, E.pchip_slopes(self.ts, ys)))

    def state(self, t):
        v = [E.hermite(t, self.ts, ys, ms) for ys, ms in self._ch] if len(self.ts) > 1 else [ys[0] for ys, _ in self._ch]
        return np.array(v[:3]), np.array(v[3:6]), float(v[6])

    def shift(self, t): ys, ms = self._ch[7]; return float(E.hermite(t, self.ts, ys, ms)) if len(self.ts) > 1 else ys[0]

    def camera(self, t):
        p, q, f = self.state(t); return Camera3D(p, q, f, self.size, shift=(0.0, self.shift(t)))


def shade(color, normal, light=(-0.35, -0.55, 0.76), ambient=0.42, diffuse=0.62, emissive=0.0):
    k = ambient + diffuse * max(0.0, float(_n(normal) @ _n(light)))
    return tuple(int(min(255, c * k + 255 * emissive * (c / 255.0))) for c in color[:3])


class Painter:
    """collects primitives for one frame, then draws them back to front on a 2x canvas. All coordinates are world coordinates."""
    def __init__(self, cam, fog=(14, 22, 34), fog_near=120.0, fog_far=520.0, fog_max=0.85):
        self.cam = cam; self.items = []; self.top = []; self.glow = []; self.stage = 1      # set .stage before adding: lower stages are drawn first (floor 0, world 1, ...)
        self.fog, self.fog_near, self.fog_far, self.fog_max = fog, fog_near, fog_far, fog_max

    def _fog(self, rgb, depth, alpha=255):
        f = self.fog_max * E.clamp((depth - self.fog_near) / max(self.fog_far - self.fog_near, 1e-9))
        return tuple(int(c * (1 - f) + g * f) for c, g in zip(rgb[:3], self.fog)) + (alpha,)

    def poly(self, pts, color, normal=None, outline=None, cull=True, emissive=0.0, alpha=255, light=None, bias=0.0):
        P = np.asarray(pts, float); scr, z = self.cam.project(P)
        if (z < self.cam.near).any(): return
        if normal is not None:
            if cull and float((P.mean(0) - self.cam.pos) @ np.asarray(normal, float)) > 0: return
            rgb = shade(color, normal, emissive=emissive, **({} if light is None else dict(light=light)))
        else: rgb = tuple(color[:3])
        d = float(z.mean()) + bias; self.items.append((d, "poly", scr, self._fog(rgb, d, alpha), outline, self.stage))

    def line(self, pts, color, width=2.0, alpha=1.0, top=False, glow=0.0, dash=None, sort_bias=0.0):
        """3-D polyline; segments behind the near plane are clipped. width in output pixels (1x)."""
        P = np.asarray(pts, float); c = self.cam.to_cam(P); near = self.cam.near; segs = []
        for a, b in zip(c[:-1], c[1:]):
            if a[2] < near and b[2] < near: continue
            if a[2] < near: a = a + (b - a) * (near - a[2]) / (b[2] - a[2])
            if b[2] < near: b = b + (a - b) * (near - b[2]) / (a[2] - b[2])
            segs.append((a, b))
        if not segs: return
        W, H = self.cam.size; F = self.cam.focal
        sx, sy = self.cam.shift; sp = lambda q: (W / 2 + sx + F * q[0] / q[2], H / 2 + sy - F * q[1] / q[2])
        scr = [(sp(a), sp(b)) for a, b in segs]; d = float(np.mean([s[0][2] for s in segs])) + sort_bias
        item = (d, "line", scr, tuple(color[:3]) + (int(255 * E.clamp(alpha)),), (width, dash), self.stage)
        (self.top if top else self.items).append(item)
        if glow > 0: self.glow.append((d, "line", scr, tuple(color[:3]) + (int(255 * E.clamp(alpha * glow)),), (width * 2.6, None), 0))

    def ring(self, center, axis, radius, color, width=3.0, alpha=1.0, top=True, glow=0.0, n=48, arc=(0.0, 360.0)):
        """circle of `radius` around `center`, perpendicular to `axis` (projected -> ellipse)."""
        ax = _n(axis); a = _n(np.cross(ax, [0, 0, 1] if abs(ax[2]) < 0.9 else [1, 0, 0])); b = np.cross(ax, a)
        th = np.radians(np.linspace(arc[0], arc[1], n)); pts = [np.asarray(center) + radius * (math.cos(q) * a + math.sin(q) * b) for q in th]
        self.line(pts, color, width, alpha, top, glow)

    def dot(self, p, r_px, color, alpha=1.0, top=True, glow=0.0):
        scr, z = self.cam.project([p])
        if z[0] < self.cam.near: return
        item = (float(z[0]), "dot", scr[0], tuple(color[:3]) + (int(255 * E.clamp(alpha)),), r_px, self.stage)
        (self.top if top else self.items).append(item)
        if glow > 0: self.glow.append((float(z[0]), "dot", scr[0], tuple(color[:3]) + (int(255 * E.clamp(alpha * glow)),), r_px * 2.4, 0))

    def _draw(self, d, items, k):
        for _, kind, scr, col, extra, _st in items:
            if kind == "poly":
                d.polygon([(x * k, y * k) for x, y in scr], fill=col, outline=None if extra is None else tuple(extra))
            elif kind == "line":
                width, dash = extra
                for (x0, y0), (x1, y1) in scr:
                    if dash:
                        L = math.hypot(x1 - x0, y1 - y0); s = 0.0
                        while s < L:
                            e = min(L, s + dash[0]); f0, f1 = s / max(L, 1e-9), e / max(L, 1e-9)
                            d.line([((x0 + (x1 - x0) * f0) * k, (y0 + (y1 - y0) * f0) * k), ((x0 + (x1 - x0) * f1) * k, (y0 + (y1 - y0) * f1) * k)], fill=col, width=max(1, int(width * k)))
                            s += dash[0] + dash[1]
                    else: d.line([(x0 * k, y0 * k), (x1 * k, y1 * k)], fill=col, width=max(1, int(width * k)), joint="curve")
            elif kind == "dot":
                x, y = scr; r = extra * k; d.ellipse([x * k - r, y * k - r, x * k + r, y * k + r], fill=col)

    def render(self, base_rgb, glow_radius=8.0):
        """draw onto `base_rgb` (an RGB image of size*SS) and return an RGBA image at 1x."""
        W, H = self.cam.size; k = SS
        canvas = base_rgb.convert("RGBA"); d = ImageDraw.Draw(canvas, "RGBA")
        self._draw(d, sorted(self.items, key=lambda it: (it[5], -it[0])), k)
        top = Image.new("RGBA", canvas.size, (0, 0, 0, 0)); self._draw(ImageDraw.Draw(top, "RGBA"), sorted(self.top, key=lambda it: -it[0]), k)
        out = canvas.resize((W, H), Image.LANCZOS)
        if self.glow:
            g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); self._draw(ImageDraw.Draw(g, "RGBA"), self.glow, 1)
            g = g.filter(ImageFilter.GaussianBlur(glow_radius)); g.putalpha(g.getchannel("A").point(lambda v: int(min(255, v * 1.7)))); out.alpha_composite(g)
        out.alpha_composite(top.resize((W, H), Image.LANCZOS)); return out


def box(p0, p1):
    """axis-aligned box -> list of (quad, outward normal)."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    return [([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1)), ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
            ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], (0, 1, 0)), ([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], (-1, 0, 0)),
            ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0))]


def sky(size, top=(5, 8, 16), horizon=(20, 32, 50), horizon_y=0.62):
    """vertical gradient backdrop at 2x (RGB)."""
    W, H = size; h = H * SS; y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    m = np.clip(y / horizon_y, 0, 1) ** 1.6; c = np.array(top, np.float32) * (1 - m) + np.array(horizon, np.float32) * m
    return Image.fromarray(np.ascontiguousarray(np.broadcast_to(c, (h, W * SS, 3))).astype(np.uint8))
