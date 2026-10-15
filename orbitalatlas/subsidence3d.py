"""EP004 S3 V2 - "Cutaway Descent": a schematic 3-D block of city ground, a radar satellite making two passes, groundwater pumping,
clay compaction and the line-of-sight geometry of the measurement, in one continuous perspective space (class ILLUSTRATION).

Physics the geometry enforces (unit-tested in tests/test_subsidence3d.py):
  * the confined aquifer stays saturated; pumping lowers the water PRESSURE (the level in the well), it does not drain the sand;
  * the clay layers lose thickness; surface lowering == clay1 loss + clay2 loss at every point (no free-floating surface);
  * pass 2's echo goes to the lowered point; the extra range and the line-of-sight component come from illustrate.los_change;
  * in the profile shot the camera looks exactly along +y, perpendicular to the plane that holds the satellite, the point and the drop,
    so the right angle between the drop and the line of sight is shown true (no perspective skew of that construction).
Nothing here is a measurement: no rate, depth, distance or angle is printed; the drop is exaggerated and says so.
"""
# effect-reuse-checked: new scene built on scene3d (perspective renderer) and illustrate (LOS geometry, Diagram face); no existing effect
# renders a cut-away of ground layers, pumping or a two-pass radar geometry in 3-D (knowledge/effects.json searched: radar, cutaway, aquifer).
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from . import easing as E
from . import scene3d as S3
from . import typeset as TS
from . import kinetic as K
from . import textrec as TR
from .illustrate import Diagram, los_change
from . import text as T

AMBER, CYAN, WHITE, INK = T.THEME.amber, T.THEME.cyan, (240, 244, 248), T.THEME.ink
WATER = (70, 150, 220)
LAYERS = [("topsoil", 4.0, (96, 78, 62)), ("clay1", 12.0, (128, 98, 74)), ("aquifer", 9.0, (150, 160, 150)), ("clay2", 8.0, (112, 86, 66)), ("bedrock", 3.0, (72, 72, 80))]
COMPACT = {"clay1": 0.7, "clay2": 0.3}                    # share of the surface lowering taken by each clay layer (sums to 1)


class CutawayRadarDiagram(Diagram):
    DEFAULT_TL = dict(sat1_in=(0.2, 1.6), pulse1=(1.7, 2.3), echo1=(2.3, 2.9), sat1_out=(2.7, 3.9), pump=(4.2, 5.6), sink=(5.3, 7.2),
                      sat2_in=(6.4, 7.4), pulse2=(7.5, 8.1), echo2=(8.1, 8.7), extra=(8.6, 9.4), los=(9.9, 10.7), vertical=(10.5, 11.2), fade=(11.75, 12.2))
    CAPTIONS = [(0.5, 2.4, "A radar satellite pings the same patch of ground", ("same",)),
                (2.4, 4.2, "and records exactly how far away it is.", ("far",)),
                (4.2, 5.8, "Pump out groundwater and the pressure drops,", ("pressure",)),
                (5.8, 7.4, "the clay squeezes, and the ground sinks.", ("sinks.",)),
                (7.4, 9.6, "On the next pass, the echo travels farther.", ("farther.",))]
    LABELS = [(4.5, 5.75, "WATER PRESSURE DROPS", "well"), (5.95, 7.3, "CLAY COMPACTS", "clay"), (8.75, 9.6, "EXTRA PATH", "extra")]

    def __init__(self, size=(1920, 1080), duration=12.8, name="S3v2_cutaway_radar", drop=8.0, sat=(-150.0, 0.0, 190.0), tl=None, keys=None):
        super().__init__(size, duration, name); self.tl = dict(self.DEFAULT_TL, **(tl or {})); self.drop = float(drop); self.sat = np.array(sat, float)
        self.P0 = np.array([0.0, 0.0, 0.0]); self.Pend = self.P0 + (0, 0, -self.drop)
        u = (self.P0 - self.sat) / np.linalg.norm(self.P0 - self.sat); self.u_away = u
        self.los_comp = float(np.array([0, 0, -self.drop]) @ u); self.F = self.P0 + u * self.los_comp
        self.X0, self.X1, self.Y1, self.R = -70.0, 70.0, 45.0, 22.0
        self.well_x = -26.0
        rng = np.random.default_rng(11); self.buildings = []
        for x in (-58, -44, -30, -14, 2, 16, 32, 48, 62):
            for y in (9, 22, 35):
                if rng.random() < 0.22 or (abs(x) < 9 and y < 15): continue
                self.buildings.append((x + rng.uniform(-2, 2), y + rng.uniform(-2, 2), rng.uniform(7, 10), rng.uniform(7, 10), rng.uniform(6, 24), rng.integers(0, 1 << 30)))
        self.dust = np.column_stack([rng.uniform(-160, 160, 140), rng.uniform(-90, 160, 140), rng.uniform(-30, 140, 140)])
        self.keys = keys or [
            (0.0, (80, -380, 80), (-60, 10, 55), 52.0),
            (1.9, (62, -345, 74), (-56, 8, 52), 50.0),
            (3.3, (30, -190, 45), (-8, 5, 4), 44.0),
            (4.6, (40, -100, 10), (-4, 10, -14), 40.0),
            (7.1, (31, -82, 5), (-5, 8, -14), 40.0),
            (8.1, (10, -250, 60), (-50, 0, 62), 48.0),
            (9.1, (12, -112, 9), (2, 0, -3), 40.0, 0.0),
            (10.0, (11, -58, 1), (11, 0, 1), 36.0, -190.0),          # shifted lens: geometry raised to the frame centre, plane stays undistorted
            (11.7, (11, -53, 1), (11, 0, 1), 36.0, -190.0),
            (12.8, (0, -32, 175), (0, 22, -5), 40.0, 0.0)]
        self.path = S3.CameraPath(self.keys, size)

    # ---------------------------------------------------------------- state ----
    def _w(self, k, t): a, b = self.tl[k]; return E.seg(t, a, b)

    def depth(self, t): return self.drop * E.in_out_cubic(self._w("sink", t))

    def subs(self, x, y, t): return self.depth(t) * np.exp(-((np.asarray(x, float)) ** 2 + (0.8 * np.asarray(y, float)) ** 2) / self.R ** 2)

    def boundaries(self, x, y, t):
        """z of every layer boundary (bottom -> top) at (x, y): bedrock bottom, then the top of each layer in LAYERS order reversed."""
        s = self.subs(x, y, t); z = -sum(th for _, th, _ in LAYERS) + 0 * s; out = [z]
        for name, th, _ in reversed(LAYERS):
            z = z + th - COMPACT.get(name, 0.0) * s; out.append(z)
        return out                                                                      # out[-1] is the surface = -s

    def head(self, t):
        """water level in the well (piezometric head): near the surface before pumping, lower after."""
        return E.lerp(-3.0, -12.0, E.in_out_cubic(self._w("pump", t)))     # confined aquifer: the head stays above the aquifer top

    def sat_pos(self, t):
        y = 0.0
        if t < self.tl["sat1_out"][0]: y = E.lerp(-150, 0, E.out_cubic(self._w("sat1_in", t)))
        elif t < self.tl["sat2_in"][0]: y = E.lerp(0, 170, E.in_cubic(self._w("sat1_out", t)))
        else: y = E.lerp(-170, 0, E.out_cubic(self._w("sat2_in", t)))
        return np.array([self.sat[0], y, self.sat[2] - 0.0015 * y * y])

    def camera(self, t): return self.path.camera(t)

    # --------------------------------------------------------------- render ----
    def render(self, t):
        W, H = self.size; k = W / 1920.0; cam = self.camera(t)
        fz = E.smooth(E.seg(t, 9.2, 9.9)) * (1 - E.smooth(E.seg(t, 11.8, 12.4)))           # depth focus on the cut plane during the profile
        pa = S3.Painter(cam, fog=(12, 19, 30), fog_near=E.lerp(140, 71, fz), fog_far=E.lerp(560, 80, fz), fog_max=E.lerp(0.8, 0.94, fz))
        self._focus = fz
        pa.stage = 0; self._floor(pa); pa.stage = 1; self._block(pa, t); self._buildings(pa, t); self._well(pa, t); self._satellite(pa, t); self._radar(pa, t); self._dust(pa, t)
        base = S3.sky(self.size)
        img = pa.render(base, glow_radius=7 * k)
        img = self._grade(img, cam, t)
        ui = Image.new("RGBA", (W, H), (0, 0, 0, 0)); self.reg.reset()
        self._labels(ui, cam, t, k); self._captions(ui, t, k); self._lockup(ui, t, k); self._chips(ui, t, k)
        img.alpha_composite(ui); return img.convert("RGB")

    def _floor(self, pa):
        z = -36.2
        for x in range(-400, 400, 40):
            for y in range(-200, 800, 40):
                pa.poly([(x, y, z), (x + 40, y, z), (x + 40, y + 40, z), (x, y + 40, z)], (13, 19, 29), None, cull=False, bias=60)
        for x in range(-400, 401, 40): pa.line([(x, -200, z + 0.05), (x, 800, z + 0.05)], (30, 46, 66), 1.4, 0.8, sort_bias=55)
        for y in range(-200, 801, 40): pa.line([(-400, y, z + 0.05), (400, y, z + 0.05)], (30, 46, 66), 1.4, 0.8, sort_bias=55)

    def _block(self, pa, t):
        xs = np.linspace(self.X0, self.X1, 71); ys = np.linspace(0.0, self.Y1, 19)
        # front cut face (y = 0): one polygon per layer, boundaries follow the compaction
        bnd = self.boundaries(xs, 0.0, t); sk = self.depth(t) / self.drop
        for i, (name, th, col) in enumerate(reversed(LAYERS)):
            lo, hi = bnd[i], bnd[i + 1]; pts = [(x, 0.0, z) for x, z in zip(xs, hi)] + [(x, 0.0, z) for x, z in zip(xs[::-1], lo[::-1])]
            c = col
            if name == "aquifer": c = tuple(int(a * 0.55 + b * 0.45) for a, b in zip(col, WATER))      # saturated sand: stays blue (pressure drop, not drained)
            pa.stage = 2; pa.poly(pts, c, (0, -1, 0), cull=True, light=(-0.3, -0.85, 0.45), bias=-0.2); pa.stage = 3
            if name.startswith("clay"):                                                       # laminations: squeeze together as the clay compacts
                for f in (0.25, 0.5, 0.75):
                    zz = lo + (hi - lo) * f; pa.line([(x, -0.05, z) for x, z in zip(xs, zz)], tuple(int(v * 0.72) for v in c), 1.6, 0.9, sort_bias=-0.4)
        # pore water squeezed out of clay1 into the aquifer while it compacts
        if 0 < sk < 1:
            rng = np.random.default_rng(5)
            for j in range(26):
                x = rng.uniform(-16, 16); ph = (t * 0.9 + rng.uniform(0, 1)) % 1.0
                b = self.boundaries(x, 0.0, t); ztop, zbot = b[4] - 1.0, b[3] - 1.5           # from inside clay1 down into the top of the aquifer
                pa.dot((x, -0.12, ztop + (zbot - ztop) * ph), 3.2, WATER, alpha=0.9 * math.sin(math.pi * ph), top=False)
        pa.stage = 1
        # top surface: shaded grid, amber where it sinks
        Z = np.array([[float(-self.subs(x, y, t)) for x in xs] for y in ys])
        for j in range(len(ys) - 1):
            for i in range(len(xs) - 1):
                p = [(xs[i], ys[j], Z[j, i]), (xs[i + 1], ys[j], Z[j, i + 1]), (xs[i + 1], ys[j + 1], Z[j + 1, i + 1]), (xs[i], ys[j + 1], Z[j + 1, i])]
                n = np.cross(np.subtract(p[1], p[0]), np.subtract(p[3], p[0])); f = float(-Z[j:j + 2, i:i + 2].mean()) / self.drop
                col = tuple(int(a * (1 - 0.6 * f) + b * 0.6 * f) for a, b in zip((62, 70, 82), AMBER))
                pa.poly(p, col, n, emissive=0.35 * f, cull=False)
        # surface edge on the cut face (bright line) and side faces
        pa.stage = 3; pa.line([(x, -0.1, z) for x, z in zip(xs, bnd[-1])], (220, 190, 140), 3.0, 1.0, sort_bias=-0.6)
        for x0, nx in ((self.X0, -1), (self.X1, 1)):
            b = self.boundaries(np.full(len(ys), x0), ys, t)
            for i, (name, th, col) in enumerate(reversed(LAYERS)):
                pts = [(x0, y, z) for y, z in zip(ys, b[i + 1])] + [(x0, y, z) for y, z in zip(ys[::-1], b[i][::-1])]
                pa.stage = 1; pa.poly(pts, col, (nx, 0, 0), cull=True)

    def _buildings(self, pa, t):
        fz = getattr(self, "_focus", 0.0); mix = lambda c: tuple(int(a * (1 - 0.88 * fz) + b * 0.88 * fz) for a, b in zip(c, pa.fog))   # profile: city recedes
        for (x, y, w, d, h, seed) in self.buildings:
            z0 = float(-self.subs(x, y, t)); rng = np.random.default_rng(int(seed))
            for quad, n in S3.box((x - w / 2, y - d / 2, z0 - 2.0), (x + w / 2, y + d / 2, z0 + h)):
                pa.poly(quad, mix((74, 86, 104)), n)
            rows = max(1, int(h // 4))
            for r in range(rows):
                for c in (-0.25, 0.25):
                    if rng.random() < 0.45: continue
                    zz = z0 + 2 + r * 4; xx = x + c * w
                    pa.poly([(xx - 0.9, y - d / 2 - 0.05, zz), (xx + 0.9, y - d / 2 - 0.05, zz), (xx + 0.9, y - d / 2 - 0.05, zz + 1.6), (xx - 0.9, y - d / 2 - 0.05, zz + 1.6)],
                            mix((255, 206, 140)), (0, -1, 0), emissive=0.6 * (1 - fz))

    def _well(self, pa, t):
        pa.stage = 3; x = self.well_x; wa = int(255 * (1 - 0.9 * getattr(self, "_focus", 0.0))); b = self.boundaries(x, 0.0, t); top = float(b[-1]) + 3.0; bottom = float(b[2] + 0.5 * (b[3] - b[2]))   # wa: the well steps back in the profile shot
        pa.poly([(x - 1.8, -0.2, bottom), (x + 1.8, -0.2, bottom), (x + 1.8, -0.2, top), (x - 1.8, -0.2, top)], (36, 42, 52), (0, -1, 0), bias=-1, alpha=wa)
        h = max(bottom, self.head(t)); pa.poly([(x - 1.2, -0.3, bottom), (x + 1.2, -0.3, bottom), (x + 1.2, -0.3, h), (x - 1.2, -0.3, h)], (90, 175, 245), (0, -1, 0), emissive=0.55, bias=-6.0, alpha=wa)
        pa.line([(x - 2.6, -0.35, h), (x + 2.6, -0.35, h)], (170, 225, 255), 3.0, wa / 255, sort_bias=-2)                     # water level mark
        pa.stage = 1
        for quad, n in S3.box((x - 2.4, -2.0, top - 0.5), (x + 2.4, 2.0, top + 2.2)): pa.poly(quad, (150, 156, 168), n)
        pa.stage = 3
        pu = self._w("pump", t)
        if 0 < pu < 1:                                                                         # water drawn up the pipe
            for j in range(6):
                ph = (t * 1.6 + j / 6) % 1.0; pa.dot((x, -0.4, h + (top - h) * ph), 3.0, (150, 210, 255), alpha=0.9, top=False)
        if self._w("pump", t) > 0:
            pa.line([(x + 1.6, -0.35, -3.0), (x + 4.5, -0.35, -3.0)], WHITE, 1.6, 0.55 * (1 - pu * 0.3), dash=(6, 5), sort_bias=-2)  # starting level

    def _satellite(self, pa, t):
        pa.stage = 1; S = self.sat_pos(t); x, y, z = S; g = 2.2                                                  # glyph scale (not to scale)
        orb = [(self.sat[0], yy, self.sat[2] - 0.0015 * yy * yy) for yy in np.linspace(-260, 260, 60)]
        pa.line(orb, (120, 140, 170), 1.6, 0.5 * (1 - E.smooth(E.seg(t, 8.6, 9.4))), dash=(8, 8))
        for quad, n in S3.box((x - 4 * g, y - 2.5 * g, z - 2.5 * g), (x + 4 * g, y + 2.5 * g, z + 2.5 * g)): pa.poly(quad, (214, 220, 230), n, emissive=0.15)
        for sgn in (-1, 1):
            for quad, n in S3.box((x - 3.5 * g, y + sgn * 3.5 * g - (sgn < 0) * 18 * g, z - 0.3 * g), (x + 3.5 * g, y + sgn * 3.5 * g + (sgn > 0) * 18 * g, z + 0.3 * g)):
                pa.poly(quad, (52, 104, 176), n, emissive=0.25)
        u = (self.P0 - S) / np.linalg.norm(self.P0 - S); a = S + u * 3.0 * g
        pa.line([a, a + u * 5.0 * g], AMBER, 5.0, 1.0, glow=0.8)

    def _pulse(self, pa, t, k_out, k_back, target, color):
        S = self.sat_pos(t); v = np.asarray(target) - S; L = float(np.linalg.norm(v)); u = v / L
        a, b = self.tl[k_out]; c, e = self.tl[k_back]
        if a <= t < b: f = (t - a) / (b - a); rs = [f * L - 14 * i for i in range(3)]; al = [1, 0.65, 0.35]
        elif c <= t < e: f = (t - c) / (e - c); rs = [(1 - f) * L + 14 * i for i in range(3)]; al = [0.9, 0.55, 0.3]
        else: return
        for r, q in zip(rs, al):
            if 4 < r < L:
                pa.ring(S + u * r, u, 8.0, color, 5.0, q, glow=1.0); pa.dot(S + u * r, 6.0 * q, WHITE, q, glow=0.6)
        hit = E.seg(t, b - 0.02, b + 0.55)
        if 0 < hit < 1: pa.ring(np.asarray(target) + (0, 0, 0.2), (0, 0, 1), 2 + 14 * hit, color, 4.0, 1 - hit, glow=1.0)

    def _radar(self, pa, t):
        S = self.sat_pos(t)
        on1 = self._w("pulse1", t) > 0 and t < self.tl["sat1_out"][0] + 0.2
        on2 = t >= self.tl["pulse2"][0] and t < self.tl["los"][1] + 0.6
        fo = 1 - E.smooth(self._w("fade", t))
        if on1: pa.line([S, self.P0], CYAN, 2.0, 0.45, top=True, dash=(10, 9))
        if on2: pa.line([S, self.Pend], AMBER, 2.0, 0.45 * fo, top=True, dash=(10, 9))
        self._pulse(pa, t, "pulse1", "echo1", self.P0, CYAN); self._pulse(pa, t, "pulse2", "echo2", self.Pend, AMBER)
        # measurement point: rides on the surface
        pz = float(-self.subs(0.0, 0.0, t)); pa.dot((0, -0.3, pz), 7.0, AMBER, 1.0, glow=0.8)
        if self.depth(t) > 0.3: pa.line([(-9, -0.3, 0.0), (9, -0.3, 0.0)], WHITE, 2.2, 0.75 * fo, top=True, dash=(7, 6))     # original level
        ex = self._w("extra", t); fe = fo * (1 - E.smooth(E.seg(t, self.tl["los"][0] - 0.3, self.tl["los"][0] + 0.1)))
        if ex > 0 and fe > 0:
            R0 = float(np.linalg.norm(self.P0 - self.sat)); u2 = (self.Pend - self.sat) / np.linalg.norm(self.Pend - self.sat)
            ang0 = math.atan2(self.P0[2] - self.sat[2], self.P0[0] - self.sat[0]); arc = []
            for d in np.linspace(-0.05, 0.05, 30):
                q = ang0 + d; arc.append((self.sat[0] + R0 * math.cos(q), -0.35, self.sat[2] + R0 * math.sin(q)))
            pa.line(arc, CYAN, 2.4, 0.85 * ex * fe, top=True, dash=(7, 6))                              # pass-1 distance
            Q = self.sat + u2 * R0; q2 = Q + (self.Pend - Q) * E.out_cubic(ex)
            pa.line([Q + (0, -0.4, 0), q2 + (0, -0.4, 0)], AMBER, 9.0, fe, top=True, glow=0.9)            # the extra range of pass 2
        la, va = self._w("los", t), self._w("vertical", t)
        if la > 0 and fo > 0:
            q = self.P0 + (self.F - self.P0) * E.out_cubic(la)
            pa.line([self.P0 + (0, -0.5, 0), q + (0, -0.5, 0)], CYAN, 12.0, fo, top=True, glow=1.0)
            if la > 0.7:
                pa.line([self.Pend + (0, -0.5, 0), self.F + (0, -0.5, 0)], WHITE, 2.4, 0.9 * fo, top=True, dash=(6, 5))
                n = (self.Pend - self.F) / np.linalg.norm(self.Pend - self.F); u = self.u_away; m = 0.9
                pa.line([self.F + n * m + (0, -0.5, 0), self.F + n * m - u * m + (0, -0.5, 0), self.F - u * m + (0, -0.5, 0)], WHITE, 2.4, 0.9 * fo, top=True)
        if va > 0.1 and fo > 0:
            a0 = self.P0 + (-1.4, -0.5, -0.2); a1 = a0 + (0, 0, -(self.drop - 1.2) * E.out_cubic(va))
            pa.line([a0, a1], WHITE, 7.0, fo, top=True)
            if va > 0.25:                                                                                   # arrow head as a small triangle of lines
                pa.line([a1 + (-0.9, 0, 1.3), a1, a1 + (0.9, 0, 1.3)], WHITE, 7.0, fo, top=True)

    def _dust(self, pa, t):
        for i, p in enumerate(self.dust):
            q = p + np.array([math.sin(t * 0.3 + i) * 1.5, t * 1.2, math.cos(t * 0.25 + i * 0.7) * 1.2])
            pa.stage = 1 if q[1] > 0 else 3; pa.dot(q, 1.6, (190, 210, 240), 0.35, top=False)

    def _grade(self, img, cam, t):
        """vignette + a warm light on the sinking point during the hero shot (presentation grade of an illustration, no evidence pixels)."""
        W, H = self.size; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot((xx - W / 2) / (W * 0.62), (yy - H / 2) / (H * 0.62)); v = np.clip(1 - 0.38 * np.clip(r - 0.55, 0, 1) ** 1.4, 0, 1)
        a = np.asarray(img, np.float32); a[..., :3] *= v[..., None]
        hero = E.smooth(E.seg(t, 4.3, 5.0)) * (1 - E.smooth(E.seg(t, 7.3, 7.9)))
        if hero > 0:
            sp, z = cam.project([(0, 0, -self.depth(t))])
            if z[0] > 0:
                g = np.exp(-(((xx - sp[0, 0]) / (W * 0.22)) ** 2 + ((yy - sp[0, 1]) / (H * 0.30)) ** 2)) * 0.22 * hero
                a[..., :3] += g[..., None] * np.array([255, 196, 120], np.float32)
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")

    # ------------------------------------------------------------------ text ---
    def _anchor(self, cam, which, t):
        if which == "well":
            b = self.boundaries(self.well_x, 0.0, t); p = (self.well_x, -0.3, max(float(b[2] + 0.5 * (b[3] - b[2])), self.head(t)))
        elif which == "clay":
            b = self.boundaries(9.0, 0.0, t); p = (9.0, -0.1, float(b[3] + 0.5 * (b[4] - b[3])))
        else:
            R0 = float(np.linalg.norm(self.P0 - self.sat)); u2 = (self.Pend - self.sat) / np.linalg.norm(self.Pend - self.sat); Q = self.sat + u2 * R0
            p = tuple((Q + self.Pend) / 2)
        sp, z = cam.project([p]); return (float(sp[0, 0]), float(sp[0, 1])) if z[0] > 0 else None

    def _labels(self, ui, cam, t, k):
        d = ImageDraw.Draw(ui, "RGBA")
        for t0, t1, s, which in self.LABELS:
            if not (t0 <= t <= t1): continue
            a = E.out_cubic(E.seg(t, t0, t0 + 0.3)) * (1 - E.smooth(E.seg(t, t1 - 0.25, t1))); p = self._anchor(cam, which, t)
            if p is None or a < 0.02: continue
            px = 36 * k; w = K.width(s, px, "black"); lx = min(max(p[0] + 70 * k, 80 * k), ui.width - 80 * k - w); ly = p[1] - 120 * k
            ly = min(max(ly, 200 * k), 800 * k)
            q = (lx - 10 * k, ly + px * 0.62); e = E.out_cubic(E.seg(t, t0, t0 + 0.35))
            d.line([p, (p[0] + (q[0] - p[0]) * e, p[1] + (q[1] - p[1]) * e)], fill=(255, 255, 255, int(220 * a)), width=max(2, int(3 * k)))
            d.ellipse([p[0] - 6 * k, p[1] - 6 * k, p[0] + 6 * k, p[1] + 6 * k], outline=(255, 255, 255, int(230 * a)), width=max(2, int(3 * k)))
            pad = px * 0.35; d.rounded_rectangle([lx - pad, ly - pad * 0.6, lx + w + pad, ly + px * 1.3], radius=px * 0.2, fill=(6, 10, 16, int(170 * a)))
            TS.animate_word(ui, s, lx, ly, px, t, t0, preset="slide", weight="black", color=WHITE, dur=0.35)
            self.reg.add("label", (lx - pad, ly - pad * 0.6, lx + w + pad, ly + px * 1.3), a)

    def _captions(self, ui, t, k):
        """lower-third narration stand-in: one line, words rise in sequence (typeset 'rise'), 1-2 amber emphasis words, soft scrim (no box)."""
        for t0, t1, s, emph in self.CAPTIONS:
            if not (t0 <= t <= t1): continue
            a = E.smooth(E.seg(t, t0, t0 + 0.25)) * (1 - E.smooth(E.seg(t, t1 - 0.2, t1)))
            if a > 0.01:
                band = Image.new("L", (1, 300), 0); bd = np.clip((np.arange(300) - 40) / 260.0, 0, 1) ** 1.2 * 175 * a
                band = Image.fromarray(bd.astype(np.uint8)[:, None]).resize((ui.width, int(300 * k)))
                sh = Image.new("RGBA", (ui.width, int(300 * k)), (0, 0, 0, 0)); sh.putalpha(band); ui.alpha_composite(sh, (0, ui.height - int(300 * k)))
            px = 52 * k; words = s.split(" "); pos, lines = TS.layout(words, px, "bold", 1700 * k, align="center", x0=ui.width / 2, y0=905 * k)
            prev = TR.STATE["tag"]; TR.STATE["tag"] = "WordCaptions"
            try:
                for i, w in enumerate(words):
                    TS.animate_word(ui, w, pos[i][0], pos[i][1], px, t, t0 + i * 0.045, preset="rise", weight="bold", color=WHITE, emph=w in emph, accent=AMBER, dur=0.3,
                                    exit_t=t1 - 0.22, exit="up", hold_glint=False)
            finally: TR.STATE["tag"] = prev
            self.reg.add("caption", (300 * k, 875 * k, ui.width - 300 * k, 990 * k), a)

    def _lockup(self, ui, t, k):
        """VR2-style weight contrast: heavy 'LINE OF SIGHT' (cyan = the cyan segment) over thin outline 'NOT THE VERTICAL DROP' (white = the white arrow)."""
        t0, t1 = 9.95, 11.75
        if not (t0 <= t <= t1): return
        x = 960 * k; y = 190 * k; px1, px2 = 100 * k, 50 * k
        words = ["LINE", "OF", "SIGHT"]; xx = x
        for i, w in enumerate(words):
            TS.animate_word(ui, w, xx, y, px1, t, t0 + i * 0.09, preset="depth_in", weight="black", color=CYAN, dur=0.45, exit_t=t1 - 0.3, exit="up")
            xx += K.width(w, px1, "black") + px1 * 0.32
        TS.animate_word(ui, "NOT THE VERTICAL DROP", x + 6 * k, y + 140 * k, px2, t, t0 + 0.55, preset="outline_fill", weight="black", color=WHITE, dur=0.5, exit_t=t1 - 0.3, exit="up")
        self.reg.add("lockup", (x, y, xx, y + 140 * k + px2 * 1.3), 1.0)

    def _chips(self, ui, t, k):
        d = ImageDraw.Draw(ui, "RGBA"); a_all = 1 - E.smooth(self._w("fade", t))
        chips = [("ILLUSTRATION · NOT TO SCALE", 0.0)] + ([("DROP EXAGGERATED", self.tl["sink"][0])] if t >= self.tl["sink"][0] else [])
        for i, (s, t0) in enumerate(chips):
            a = E.out_cubic(E.seg(t, t0, t0 + 0.4)) * a_all
            if a < 0.02: continue
            px = 30 * k; f = K.face(px, "bold"); w = f.getlength(s); x, y = 72 * k, (50 + i * 54) * k
            d.rounded_rectangle([x, y, x + w + px * 1.2, y + px * 1.45], radius=px * 0.25, fill=(0, 0, 0, int(150 * a)))
            d.rectangle([x, y, x + px * 0.18, y + px * 1.45], fill=AMBER + (int(255 * a),))
            d.text((x + px * 0.6, y + px * 0.18), s, font=f, fill=(235, 240, 246, int(255 * a)))
            self.reg.add("chip_" + s, (x, y, x + w + px * 1.2, y + px * 1.45), a); TR.note(s, px, (x, y, x + w + px * 1.2, y + px * 1.45), (235, 240, 246), a)

    def manifest(self): return dict(super().manifest(), camera="schematic perspective (illustration), not georeferenced", los_component=self.los_comp, drop=self.drop)
