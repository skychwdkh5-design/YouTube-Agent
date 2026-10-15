"""EP004 S3 V3 "Cutaway Descent" - TRUE 3-D scene (pbrt-v4 path tracing). SCIENTIFIC ILLUSTRATION, not a reconstruction of a real site.

Same physics as V2 (orbitalatlas/subsidence3d.py, unit-tested there): pumping lowers the head in the well (confined aquifer stays saturated),
the clay layers compact (surface lowering == clay thickness loss, shared clay1 0.7 / clay2 0.3), the surface sinks in a bowl, pass 2 reaches
the lowered point, its range is longer than pass 1 by the LOS component = drop * cos(incidence). No rate, depth, distance or angle is printed;
layer thicknesses, the drop and the satellite distance are illustrative and the drop is exaggerated (chips say so).
"""
import math, os
import numpy as np
from orbitalatlas import pbrt3d as P, easing as E
from orbitalatlas.scene3d import CameraPath
from orbitalatlas.subsidence3d import LAYERS, COMPACT

TL = dict(sat1_in=(0.2, 1.6), pulse1=(1.7, 2.3), echo1=(2.3, 2.9), sat1_out=(2.7, 3.9), pump=(4.2, 5.6), sink=(5.3, 7.2),
          sat2_in=(6.4, 7.4), pulse2=(7.5, 8.1), echo2=(8.1, 8.7), extra=(8.6, 9.4), los=(9.9, 10.7), vertical=(10.5, 11.2), fade=(11.9, 12.4))
DUR = 13.5
DROP, R, WELL_X, WELL_R = 8.0, 22.0, -26.0, 1.7
X0, X1, YB = -160.0, 160.0, 220.0                     # block extent (cut face on y = 0)
TOTAL = sum(th for _, th, _ in LAYERS)                 # 36 m of strata in the illustration
SAT = np.array([-150.0, 0.0, 190.0])
P0 = np.array([0.0, 0.0, 0.0]); PEND = P0 + (0, 0, -DROP)
U = (P0 - SAT) / np.linalg.norm(P0 - SAT); LOS = float(np.array([0, 0, -DROP]) @ U); FOOT = P0 + U * LOS
CYAN, AMBER, WHITE = (0.36, 0.88, 0.90), (1.0, 0.76, 0.28), (0.95, 0.96, 0.98)

# camera: (t, eye, target, fov[, lens_shift_y_px]); pchip per coordinate (continuous velocity), whips = short key gaps
KEYS = [(0.0, (165, -255, 98), (-44, 0, 78), 46.0),           # satellite (upper left) and the block (lower right) share the frame
        (1.7, (110, -240, 84), (-44, 28, 80), 46.0),
        (2.9, (52, -128, 40), (-4, 22, 2), 42.0),
        (3.55, (30, -16, 5.5), (-12, 40, 3), 52.0),          # skim the street edge between buildings
        (4.05, (26, -44, -11), (-9, 8, -13), 44.0),          # whip down past the cut edge: under the surface
        (5.0, (4, -31, -12.5), (-22, 8, -16), 40.0),         # track along the face toward the well
        (6.0, (-2, -17, -12.5), (-13, 2, -16), 34.0),        # macro on the compacting clay
        (7.0, (10, -34, -6), (-6, 4, -9), 40.0),
        (7.65, (16, -205, 66), (-60, 20, 104), 50.0),        # whip up to the returning satellite
        (8.4, (14, -130, 26), (-14, 0, -2), 42.0),
        (9.25, (12, -108, 8), (3, 0, -3), 40.0),
        (9.95, (11, -58, 1), (11, 0, 1), 36.0),              # exactly side-on: the plane holding satellite, point and drop
        (11.75, (11, -53, 1), (11, 0, 1), 36.0),
        (12.75, (10, -190, 112), (0, 30, -6), 42.0)]                 # rise to the top view; the placeholder card dissolves in from 12.45
SHIFT = {9.95: -190.0, 11.75: -190.0}                  # lens shift (px) during the side-on construction, as in V2


def w(k, t): a, b = TL[k]; return E.seg(t, a, b)
def depth(t): return DROP * E.in_out_cubic(w("sink", t))
def subs(x, y, t): return depth(t) * np.exp(-(np.asarray(x, float) ** 2 + (0.8 * np.asarray(y, float)) ** 2) / R ** 2)
def head(t): return E.lerp(-3.0, -12.0, E.in_out_cubic(w("pump", t)))


def boundaries(x, y, t):
    """z of each layer boundary bottom -> top; clay layers lose thickness in proportion to COMPACT (sums to the surface lowering)."""
    s = subs(x, y, t); z = -TOTAL + 0 * s; out = [z]
    for name, th, _ in reversed(LAYERS):
        z = z + th - COMPACT.get(name, 0.0) * s; out.append(z)
    return out


def sat_pos(t):
    if t < TL["sat1_out"][0]: y = E.lerp(-150, 0, E.out_cubic(w("sat1_in", t)))
    elif t < TL["sat2_in"][0]: y = E.lerp(0, 170, E.in_cubic(w("sat1_out", t)))
    else: y = E.lerp(-170, 0, E.out_cubic(w("sat2_in", t)))
    return np.array([SAT[0], y, SAT[2] - 0.0015 * y * y])


_path = None
def cam(t):
    global _path
    if _path is None: _path = CameraPath([k + (SHIFT.get(k[0], 0.0),) for k in KEYS])
    e, g, f = _path.state(min(max(t, 0.0), DUR)); return e, g, f, _path.shift(min(max(t, 0.0), DUR))


def frame_matrix(origin, fwd, up=(0, 0, 1)):
    """4x4 (pbrt ConcatTransform, column-major) mapping local x=right, y=fwd, z=up to world."""
    f = np.asarray(fwd, float); f /= np.linalg.norm(f); r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = r, f, u, origin
    return "ConcatTransform [" + " ".join(f"{v:.6g}" for v in M.T.ravel()) + "]"


def disk_to(origin, normal):
    """transform placing a pbrt disk (in its local xy plane, normal +z) at origin facing `normal`."""
    n = np.asarray(normal, float); n /= np.linalg.norm(n); a = np.cross([0, 0, 1], n); s = np.linalg.norm(a); c = n[2]
    if s < 1e-8: Rm = np.eye(3) if c > 0 else np.diag([1, -1, -1])
    else:
        a /= s; K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]]); Rm = np.eye(3) + s * K + (1 - c) * K @ K
    M = np.eye(4); M[:3, :3] = Rm; M[:3, 3] = origin
    return "ConcatTransform [" + " ".join(f"{v:.6g}" for v in M.T.ravel()) + "]"


def cone(base, tip, r, n=16):
    base, tip = np.asarray(base, float), np.asarray(tip, float); ax = tip - base; ax /= np.linalg.norm(ax)
    t = np.cross(ax, [0, 0, 1] if abs(ax[2]) < 0.9 else [1, 0, 0]); t /= np.linalg.norm(t); s = np.cross(ax, t)
    th = np.linspace(0, 2 * math.pi, n, endpoint=False); ring = base + r * (np.cos(th)[:, None] * t + np.sin(th)[:, None] * s)
    Pp = np.vstack([ring, tip]); I = []
    for k in range(n): I += [k, (k + 1) % n, n]
    Nn = np.vstack([(ring - base) / r * 0.8 + ax * 0.6, ax]); return Pp, np.array(I), Nn


class SceneV3:
    def __init__(self, work, tex, size=(1920, 1080), spp=32):
        self.work, self.tex, self.size, self.spp = work, tex, size, spp
        rng = np.random.default_rng(11); self.buildings = []
        for x in np.arange(-150, 151, 13.0):
            for y in np.arange(9, 210, 13.0):
                if (abs(x - WELL_X) < 7 and y < 16) or rng.random() < 0.18 or (int((x + 150) // 13) % 5 == 2) or (int(y // 13) % 6 == 3): continue   # streets
                near = math.hypot(x, y) < 60
                h = rng.uniform(8, 26) if near else rng.uniform(10, 46) * (1.25 if rng.random() < 0.12 else 1.0)
                self.buildings.append((x + rng.uniform(-1, 1), y + rng.uniform(-1, 1), rng.uniform(8, 10.5), rng.uniform(8, 10.5), h, int(rng.integers(0, 4))))
        self.far = []
        for x in np.arange(-620, 621, 16.0):
            for y in np.arange(9, 640, 16.0):
                if (abs(x) < 168 and y < 228) or rng.random() < 0.25 or (int((x + 620) // 16) % 6 == 3) or (int(y // 16) % 7 == 3): continue
                self.far.append((x + rng.uniform(-2, 2), y + rng.uniform(-2, 2), rng.uniform(9, 13), rng.uniform(9, 13), rng.uniform(8, 48) * (1.6 if rng.random() < 0.08 else 1.0), int(rng.integers(0, 4))))
        for k in range(500):
            x, y = rng.uniform(-3000, 3000), rng.uniform(600, 4000)
            self.far.append((x, y, rng.uniform(14, 24), rng.uniform(14, 24), rng.uniform(10, 80), int(rng.integers(0, 4))))
        self.drops = rng.uniform(0, 1, (60, 3))

    # ------------------------------------------------------------ helpers ---
    def tx(self, n): return os.path.join(self.tex, n)

    def materials(self, s):
        for name, _, _ in LAYERS:
            s.texture(name, self.tx(f"{name}.png")); s.texture(name + "_b", self.tx(f"{name}_bump.png"), "float", scale=0.06)
        s.texture("ground", self.tx("ground.png")); s.texture("ground_b", self.tx("ground_bump.png"), "float", scale=0.03)
        for k in range(4): s.texture(f"fac{k}", self.tx(f"facade{k}.png"))
        s.texture("panel", self.tx("panel.png"))

    # ---------------------------------------------------------- the block ---
    def block(self, s, t):
        xs_s = np.concatenate([np.linspace(X0, -60, 41), np.linspace(-59, 59, 237), np.linspace(60, X1, 41)])
        ys_s = np.concatenate([np.linspace(0, 60, 61), np.linspace(63, YB, 53)])
        g = P.grid(xs_s, ys_s, lambda X, Y: -subs(X, Y, t), uv_scale=1 / 24.0)
        s.mesh(g[0], g[1], s.material("diffuse", tex="ground", bump="ground_b"), g[2], g[3])
        # cut face on y = 0, one textured strip per layer; a slot is left open where the well is cut in half
        names = [n for n, _, _ in reversed(LAYERS)]; wb = -24.0
        segs = [np.concatenate([np.linspace(X0, -60, 50), np.linspace(-60, WELL_X - WELL_R, 120)]),
                np.concatenate([np.linspace(WELL_X + WELL_R, 60, 300), np.linspace(60, X1, 50)])]
        hole = np.linspace(WELL_X - WELL_R, WELL_X + WELL_R, 8)
        OFF = {"bedrock": -0.45, "clay2": 0.0, "aquifer": 0.55, "clay1": 0.0, "topsoil": 0.15}         # face relief (m): softer sand weathers back
        for i, name in enumerate(names):
            parts = []; yo = OFF[name]
            for xs in segs:
                b = boundaries(xs, 0.0, t); parts.append(P.strip(xs, b[i], b[i + 1], yo, -1.0, 1 / 18.0))
                if i + 1 < len(names) and abs(OFF[names[i + 1]] - yo) > 1e-3:                      # horizontal ledge to the next layer's face
                    y0, y1 = sorted((yo, OFF[names[i + 1]])); n = len(xs); z = b[i + 1]
                    Pl = np.concatenate([np.stack([xs, np.full(n, y0), z], -1), np.stack([xs, np.full(n, y1), z], -1)])
                    up = OFF[names[i + 1]] > yo                                                     # ledge faces up when the upper layer is recessed
                    Il = sum(([k, n + k, n + k + 1, k, n + k + 1, k + 1] if up else [k, n + k + 1, n + k, k, k + 1, n + k + 1] for k in range(n - 1)), [])
                    s.mesh(Pl, Il, s.material("diffuse", tex=names[i + 1]), np.tile([0, 0, 1 if up else -1], (2 * n, 1)), np.concatenate([np.stack([xs, np.full(n, y0)], -1), np.stack([xs, np.full(n, y1)], -1)]) / 18.0)
            bh = boundaries(hole, 0.0, t); lo, hi = bh[i], np.minimum(bh[i + 1], wb)
            if (hi > lo + 0.01).any(): parts.append(P.strip(hole, lo, np.maximum(hi, lo), yo, -1.0, 1 / 18.0))
            m = P.merge(parts); kind = "coateddiffuse" if name == "aquifer" else "diffuse"
            s.mesh(m[0], m[1], s.material(kind, tex=name, roughness=0.25, bump=name + "_b"), m[2], m[3])
        # surroundings: the city continues behind and to both sides as solid ground (boxes, not huge thin planes); in front, the cut drops
        # to a dark floor at the base of the strata
        soil = s.material("diffuse", (0.085, 0.07, 0.058)); asphalt = s.material("diffuse", (0.10, 0.10, 0.105))
        for (x0, x1, y0, y1) in ((-4000, X0, 0, 4000), (X1, 4000, 0, 4000), (X0, X1, YB, 4000)):
            m = P.box((x0, y0, -TOTAL), (x1, y1, 0.0)); s.mesh(m[0][:4], m[1][:6], asphalt, m[2][:4])            # top face
            s.mesh(m[0][8:12], [0, 1, 2, 0, 2, 3], soil, m[2][8:12])                                               # front face (y = y0)
        q = np.array([(-4000, -4000, -TOTAL), (4000, -4000, -TOTAL), (4000, 0, -TOTAL), (-4000, 0, -TOTAL)])
        s.mesh(q, [0, 1, 2, 0, 2, 3], s.material("diffuse", (0.018, 0.02, 0.026)), np.tile([0, 0, 1], (4, 1)))
        far = np.array([(-60000, -60000, -TOTAL - 0.5), (60000, -60000, -TOTAL - 0.5), (60000, 60000, -TOTAL - 0.5), (-60000, 60000, -TOTAL - 0.5)])
        s.mesh(far, [0, 1, 2, 0, 2, 3], s.material("diffuse", (0.03, 0.032, 0.036)), np.tile([0, 0, 1], (4, 1)))        # horizon catcher

    def city(self, s, t):
        groups = {k: [] for k in range(4)}
        for (x, y, bw, bd, h, k) in self.buildings:
            z = float(-subs(x, y, t)); groups[k].append(P.box((x - bw / 2, y - bd / 2, z - 2.0), (x + bw / 2, y + bd / 2, z + h), uv_scale=1 / 10.0))
        for (x, y, bw, bd, h, k) in self.far: groups[k].append(P.box((x - bw / 2, y - bd / 2, 0), (x + bw / 2, y + bd / 2, h), uv_scale=1 / 12.0))
        for k, parts in groups.items():
            if parts: m = P.merge(parts); s.mesh(m[0], m[1], s.material("diffuse", tex=f"fac{k}"), m[2], m[3])

    def well(self, s, t):
        top = float(-subs(WELL_X, 0.0, t))
        steel = s.material("conductor", rgb=(0.62, 0.64, 0.66), roughness=0.28)
        s.shape(f'Shape "cylinder" "float radius" [{WELL_R}] "float zmin" [-24] "float zmax" [{top + 1.2:.3f}] "float phimax" [180]', steel, [f"Translate {WELL_X} 0 0"])
        s.shape(f'Shape "cylinder" "float radius" [{WELL_R * 0.92}] "float zmin" [-24] "float zmax" [{top + 1.2:.3f}] "float phimax" [180]',
                s.material("diffuse", (0.05, 0.05, 0.055)), [f"Translate {WELL_X} 0 0", "ReverseOrientation"])
        hz = head(t); q = np.array([(WELL_X - WELL_R * 0.92, -0.05, -24), (WELL_X + WELL_R * 0.92, -0.05, -24), (WELL_X + WELL_R * 0.92, -0.05, hz), (WELL_X - WELL_R * 0.92, -0.05, hz)])
        s.mesh(q, [0, 2, 1, 0, 3, 2], s.material("coateddiffuse", (0.05, 0.25, 0.42), roughness=0.05), np.tile([0, -1, 0], (4, 1)), emit=(0.10, 0.42, 0.75))
        pump = P.box((WELL_X - 3, 1, top), (WELL_X + 3, 7, top + 3.5)); s.mesh(pump[0], pump[1], s.material("coateddiffuse", (0.55, 0.12, 0.08), roughness=0.3), pump[2])
        pipe = P.tube((WELL_X, 0.4, top + 1.2), (WELL_X, 3.5, top + 2.2), 0.45); s.mesh(pipe[0], pipe[1], steel, pipe[2])

    def satellite(self, s, t):
        S = sat_pos(t); look = P0 - S; vel = np.array([0.0, 1.0, -0.003 * S[1]]); vel /= np.linalg.norm(vel)
        M = frame_matrix(S, vel, up=-look / np.linalg.norm(look))           # local -z (antenna) faces the ground
        gold = s.material("conductor", metal="Au", roughness=0.35); white = s.material("coateddiffuse", (0.85, 0.86, 0.88), roughness=0.2)
        panel = s.material("coateddiffuse", tex="panel", roughness=0.08)
        parts = [("bus", P.box((-3, -4, -3), (3, 4, 3)), gold), ("ant", P.box((-5.5, -7, -4.2), (5.5, 7, -3.4)), white),
                 ("p1", P.box((-1.2, 5, -0.15), (1.2, 7, 0.15)), white), ("p2", P.box((-4, 7, -0.12), (4, 29, 0.12), uv_scale=1 / 4.0), panel),
                 ("p3", P.box((-1.2, -7, -0.15), (1.2, -5, 0.15)), white), ("p4", P.box((-4, -29, -0.12), (4, -7, 0.12), uv_scale=1 / 4.0), panel)]
        for _, mesh, mat in parts:
            s.world += ["AttributeBegin", M]; s.mesh(*mesh[:2], mat, mesh[2], mesh[3]); s.world.append("AttributeEnd")
        return S

    # ------------------------------------------------------- measurement ---
    def glow_tube(self, s, a, b, rgb, r, k=1.0):
        m = P.tube(a, b, r); s.mesh(m[0], m[1], s.material("diffuse", (0, 0, 0)), m[2], emit=tuple(c * k for c in rgb), twosided=True)

    def dashed(self, s, a, b, rgb, r, dash=3.0, gap=2.4, k=1.0):
        a, b = np.asarray(a, float), np.asarray(b, float); L = np.linalg.norm(b - a); u = (b - a) / max(L, 1e-9); p = 0.0; parts = []
        while p < L:
            q = min(L, p + dash); parts.append(P.tube(a + u * p, a + u * q, r, 8)); p += dash + gap
        if parts: m = P.merge(parts); s.mesh(m[0], m[1], s.material("diffuse", (0, 0, 0)), m[2], emit=tuple(c * k for c in rgb), twosided=True)

    def ring(self, s, center, normal, r, width, rgb, k):
        s.shape(f'Shape "disk" "float radius" [{r:.3f}] "float innerradius" [{max(r - width, 0):.3f}]', s.material("diffuse", (0, 0, 0)),
                [disk_to(center, normal)], emit=tuple(c * k for c in rgb), twosided=True)

    def pulses(self, s, t, S, kout, kback, target, rgb):
        v = np.asarray(target) - S; L = float(np.linalg.norm(v)); u = v / L; a, b = TL[kout]; c, e = TL[kback]
        if a <= t < b: f = (t - a) / (b - a); rs = [f * L - 16 * i for i in range(3)]; al = [1, 0.6, 0.3]
        elif c <= t < e: f = (t - c) / (e - c); rs = [(1 - f) * L + 16 * i for i in range(3)]; al = [0.9, 0.5, 0.25]
        else: rs = []; al = []
        for r_, q in zip(rs, al):
            if 6 < r_ < L - 2: self.ring(s, S + u * r_, u, 7.0, 1.4, rgb, 14 * q)
        hit = E.seg(t, b - 0.02, b + 0.6)
        if 0 < hit < 1: self.ring(s, np.asarray(target) + (0, 0, 0.25), (0, 0, 1), 2 + 18 * hit, 1.2, rgb, 18 * (1 - hit))

    def radar(self, s, t, S):
        fo = 1 - E.smooth(w("fade", t))
        on1 = w("pulse1", t) > 0 and t < TL["sat1_out"][0] + 0.2; on2 = TL["pulse2"][0] <= t < TL["los"][1] + 0.6
        if on1: self.dashed(s, S, P0, CYAN, 0.35, 5, 4, 5)
        if on2: self.dashed(s, S, PEND + (0, 0, float(DROP - depth(t))), AMBER, 0.35, 5, 4, 5 * fo)
        self.pulses(s, t, S, "pulse1", "echo1", P0, CYAN); self.pulses(s, t, S, "pulse2", "echo2", PEND, AMBER)
        pz = float(-subs(0.0, 0.0, t)); s.shape('Shape "sphere" "float radius" [0.5]', s.material("diffuse", (0, 0, 0)), [f"Translate 0 -0.6 {pz + 0.3:.3f}"], emit=tuple(c * 6 for c in AMBER))
        if depth(t) > 0.3 and fo > 0: self.dashed(s, (-14, -0.7, 0.0), (14, -0.7, 0.0), WHITE, 0.18, 1.6, 1.2, 4 * fo)      # original ground level
        ex = w("extra", t); fe = fo * (1 - E.smooth(E.seg(t, TL["los"][0] - 0.3, TL["los"][0] + 0.1)))
        if ex > 0 and fe > 0:
            R0 = float(np.linalg.norm(P0 - SAT)); ang0 = math.atan2(P0[2] - SAT[2], P0[0] - SAT[0]); pts = [(SAT[0] + R0 * math.cos(ang0 + d), -0.8, SAT[2] + R0 * math.sin(ang0 + d)) for d in np.linspace(-0.05, 0.05, 24)]
            for a_, b_ in zip(pts[:-1:2], pts[1::2]): self.glow_tube(s, a_, b_, CYAN, 0.16, 6 * ex * fe)                 # pass-1 distance (arc)
            u2 = (PEND - SAT) / np.linalg.norm(PEND - SAT); Q = SAT + u2 * R0; q2 = Q + (PEND - Q) * E.out_cubic(ex)
            if np.linalg.norm(q2 - Q) > 0.05: self.glow_tube(s, Q + (0, -0.9, 0), q2 + (0, -0.9, 0), AMBER, 0.55, 10 * fe)      # the extra range of pass 2
        la, va = w("los", t), w("vertical", t)
        if la > 0 and fo > 0:
            q = P0 + (FOOT - P0) * E.out_cubic(la)
            if np.linalg.norm(q - P0) > 0.05: self.glow_tube(s, P0 + (0, -1.0, 0), q + (0, -1.0, 0), CYAN, 0.6, 12 * fo)
            if la > 0.7:
                self.dashed(s, PEND + (0, -1.0, 0), FOOT + (0, -1.0, 0), WHITE, 0.14, 1.0, 0.8, 5 * fo)
                n = (PEND - FOOT) / np.linalg.norm(PEND - FOOT); m = 0.9
                for a_, b_ in ((FOOT + n * m, FOOT + n * m - U * m), (FOOT + n * m - U * m, FOOT - U * m)): self.glow_tube(s, a_ + (0, -1.0, 0), b_ + (0, -1.0, 0), WHITE, 0.12, 5 * fo)
        if va > 0.1 and fo > 0:
            a0 = P0 + (-1.6, -1.0, -0.2); a1 = a0 + (0, 0, -(DROP - 1.6) * E.out_cubic(va)); self.glow_tube(s, a0, a1, WHITE, 0.4, 6 * fo)
            if va > 0.25: c_ = cone(a1 + (0, 0, 0.2), a1 + (0, 0, -1.5), 0.9); s.mesh(c_[0], c_[1], s.material("diffuse", (0, 0, 0)), c_[2], emit=tuple(x * 6 * fo for x in WHITE), twosided=True)

    def porewater(self, t):
        """droplets squeezed out of the clay into the sand while the clay compacts (illustration of drainage, not a flow rate).
        Returned as 3-D points; they are drawn in post as glows, depth-tested against the rendered distance (they cast no shadows)."""
        k = w("sink", t); out = []
        if not 0 < k < 1: return out
        b = boundaries(0.0, 0.0, 0.0)
        for i, (fx, fz, ph) in enumerate(self.drops):
            x = -44 + 70 * fx; u = (k * 1.6 + ph) % 1.0
            if i % 2 == 0: z0, z1 = b[3] + 1 + fz * 5, b[3] - 1.5        # out of clay1, down into the sand
            else: z0, z1 = b[2] - 1 - fz * 4, b[2] + 1.5                  # out of clay2, up into the sand
            a = math.sin(math.pi * u) * math.sin(math.pi * k)
            if a > 0.05: out.append(((x, -0.25, z0 + (z1 - z0) * u), a))
        return out

    # ------------------------------------------------------------- frame ---
    def write(self, t, path, film, shutter=0.5 / 30):
        s = P.Scene(); e, g, f, sh = cam(t); e1, g1, _, _ = cam(t + shutter)
        lens, focus = 0.0, float(np.linalg.norm(np.subtract(g, e)))
        if 4.3 < t < 7.2: lens = 0.06 + 0.10 * math.sin(math.pi * E.seg(t, 4.3, 7.2))          # shallow depth of field underground
        s.camera(e, g, f, self.size, self.spp, eye1=e1, target1=g1, lens=lens, focus=focus, film=film, maxdepth=5)
        if abs(sh) > 0.5:                                                                     # lens shift = offset screen window (keeps the plane undistorted)
            asp = self.size[0] / self.size[1]; dy = sh / 540.0                                     # shift is given in 1080-line pixels
            s.head[-4] = s.head[-4] + f' "float screenwindow" [{-asp} {asp} {-1 + dy:.4f} {1 + dy:.4f}]'
        s.sun_sky(os.path.join(self.work, "sky.pfm"), (-0.90, -0.30, 0.21), 5000, 7.0, 1.6)        # low raking sun from the left: long shadows, relief on the cut face
        self.materials(s); self.block(s, t); self.city(s, t); self.well(s, t); S = self.satellite(s, t); self.radar(s, t, S)
        s.write(path); return dict(eye=e, target=g, fov=f, shift=sh, sat=S)
