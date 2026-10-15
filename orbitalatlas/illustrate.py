"""Original schematic diagrams (evidence class ILLUSTRATION) that explain a measurement, not the measurement itself.

Everything here is drawn from code: no image from any provider, no data. Each diagram says so on screen (chip) and in `manifest()`.
A `Diagram` has the same face as a `layers.Scene` for `sequence.Shot` (size, start, name, render(t)), so it can be joined to other shots
by the existing transitions and rendered by `sequence.render_video`.

Components (all tested in tests/test_illustrate.py):
  geometry   `incidence_deg`, `los_change`         pure functions: how much of a ground drop a radar sees along its line of sight
  drawing    `dashed`, `arc_points`, `arrow`, `satellite`, `bowl_surface`, `wave`   primitives on a 2x supersampled canvas
  diagrams   `RadarGeometryDiagram`                 radar pulses, two passes, phase shift, line of sight vs vertical (EP004 S3)
             `EvidencePending`                      honest placeholder for a measured map whose licence is not cleared

Not built here: 3-D, DEM, real SAR processing, anything that depends on a dataset."""
# effect-reuse-checked: knowledge/effects.json 'graphic_full' is a static yt-graphics PNG; this module animates a geometry over time (pulses, sinking ground,
# phase shift) and shares no code with it. No entry exists for radar geometry, time-parametrised diagrams or an evidence placeholder.
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from . import easing as E
from . import text as T
from . import textrec as TR

SS = 2
INK, CYAN, AMBER, WHITE, MUTED = T.THEME.ink, T.THEME.cyan, T.THEME.amber, T.THEME.text, T.THEME.muted


# ------------------------------------------------------------------ geometry --
def incidence_deg(sat, pt):
    """angle in degrees between the line of sight (point -> satellite) and the local vertical. Screen coordinates: y grows downwards, 'up' is (0, -1)."""
    v = np.asarray(sat, float) - np.asarray(pt, float); n = np.linalg.norm(v)
    return float(np.degrees(np.arccos(np.clip(-v[1] / n, -1, 1))))


def los_change(sat, pt, drop):
    """a ground point `pt` moves by the vector `drop` (screen coordinates). Returns what a radar at `sat` can sense of it.
    range_before/after: distances to the satellite; delta = range_after - range_before (positive = moved away); los_component = displacement projected on the
    line of sight (the quantity a single radar geometry measures); foot = where that projection lands on the extended line of sight (drawing aid)."""
    S, P, d = np.asarray(sat, float), np.asarray(pt, float), np.asarray(drop, float)
    r0 = float(np.linalg.norm(S - P)); r1 = float(np.linalg.norm(S - (P + d))); away = (P - S) / r0
    comp = float(d @ away)
    return dict(range_before=r0, range_after=r1, delta=r1 - r0, los_component=comp, vertical=float(np.linalg.norm(d)),
                ratio=comp / max(float(np.linalg.norm(d)), 1e-9), foot=tuple(P + away * comp), incidence_deg=incidence_deg(sat, pt))


# ------------------------------------------------------------------ drawing ---
def _c(color, a=1.0): return tuple(int(v) for v in color[:3]) + (int(255 * E.clamp(a)),)


def dashed(d, p0, p1, color, width, dash=18, gap=12, scale=SS, alpha=1.0, upto=1.0):
    """dashed line from p0 towards p1; `upto` (0..1) draws only the first part (draw-on)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); L = float(np.linalg.norm(p1 - p0)) * E.clamp(upto)
    if L <= 0: return
    u = (p1 - p0) / max(np.linalg.norm(p1 - p0), 1e-9); s = 0.0
    while s < L:
        a, b = p0 + u * s, p0 + u * min(L, s + dash); d.line([tuple(a * scale), tuple(b * scale)], fill=_c(color, alpha), width=max(1, int(width * scale))); s += dash + gap


def arc_points(center, radius, a0, a1, n=48):
    """points of a circular arc, angles in degrees measured on screen from +x towards +y (so 90 = straight down)."""
    th = np.radians(np.linspace(a0, a1, n)); return np.stack([center[0] + radius * np.cos(th), center[1] + radius * np.sin(th)], 1)


def arrow(d, p0, p1, color, width=6, head=24, scale=SS, alpha=1.0, upto=1.0):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); q = p0 + (p1 - p0) * E.clamp(upto)
    if np.linalg.norm(q - p0) < 1: return
    u = (q - p0) / np.linalg.norm(q - p0); n = np.array([-u[1], u[0]]); tip = q; base = q - u * head
    d.line([tuple(p0 * scale), tuple((base + u * 2) * scale)], fill=_c(color, alpha), width=int(width * scale))
    d.polygon([tuple(tip * scale), tuple((base + n * head * 0.5) * scale), tuple((base - n * head * 0.5) * scale)], fill=_c(color, alpha))


def satellite(d, c, look, scale=SS, alpha=1.0, size=1.0):
    """side-looking radar satellite glyph: body, two solar wings and an antenna pointing along `look` (unit vector)."""
    x, y = c; s = size
    d.rectangle([(x - 34 * s) * scale, (y - 20 * s) * scale, (x + 34 * s) * scale, (y + 20 * s) * scale], fill=_c((205, 214, 226), alpha), outline=_c(INK, alpha), width=2 * scale)
    for sgn in (-1, 1):
        x0 = x + sgn * 38 * s; x1 = x + sgn * 132 * s
        d.rectangle([min(x0, x1) * scale, (y - 12 * s) * scale, max(x0, x1) * scale, (y + 12 * s) * scale], fill=_c((38, 86, 150), alpha), outline=_c(CYAN, alpha * 0.8), width=2 * scale)
        for k in range(1, 4):
            xx = x0 + (x1 - x0) * k / 4; d.line([(xx * scale, (y - 12 * s) * scale), (xx * scale, (y + 12 * s) * scale)], fill=_c(CYAN, alpha * 0.5), width=scale)
    look = np.asarray(look, float); look = look / np.linalg.norm(look); a0 = np.array([x, y + 20 * s]); a1 = a0 + look * 46 * s
    d.line([tuple(a0 * scale), tuple(a1 * scale)], fill=_c(WHITE, alpha), width=int(6 * scale))
    n = np.array([-look[1], look[0]]); d.polygon([tuple((a1 + n * 22 * s) * scale), tuple((a1 - n * 22 * s) * scale), tuple((a1 + look * 14 * s) * scale)], fill=_c(AMBER, alpha))


def bowl_surface(x, base_y, centre, depth, width):
    """ground surface height under a smooth subsidence bowl (Gaussian). `depth` > 0 lowers the surface (screen y grows). Illustrative shape, not a model."""
    return base_y + depth * np.exp(-((np.asarray(x, float) - centre) / width) ** 2)


def wave(x0, x1, y, amp, wavelength, phase, n=240):
    xs = np.linspace(x0, x1, n); return np.stack([xs, y - amp * np.sin(2 * math.pi * (xs - x0) / wavelength + phase)], 1)


def _ui_text(layer, reg, s, xy, px, color, a=1.0, bold=True, group=None, anchor="left"):
    """one text label with a soft dark plate behind it (contrast on any background), logged for the collision and phone-size QA."""
    if a <= 0.02: return
    f = T.font(px, bold); w = T.text_width(s, f); x, y = xy
    x0 = x - {"left": 0, "center": w / 2, "right": w}[anchor]; box = (x0 - px * 0.35, y - px * 0.1, x0 + w + px * 0.35, y + px * 1.28)
    d = ImageDraw.Draw(layer, "RGBA"); d.rounded_rectangle(box, radius=px * 0.25, fill=(6, 9, 14, int(150 * a)))
    d.text((x0 + px * 0.04, y + px * 0.05), s, font=f, fill=(0, 0, 0, int(170 * a))); d.text((x0, y), s, font=f, fill=_c(color, a))
    reg.add(group or s, box, a); TR.note(s, px, box, color, a)


def _chip(layer, reg, s, xy, px, accent, a):
    """top-left chip: dark plate, accent bar, white text (the repo's source-chip look)."""
    if a <= 0.02: return
    f = T.font(px, True); w = T.text_width(s, f) + px * 1.4; h = px * 1.55; x, y = xy; d = ImageDraw.Draw(layer, "RGBA")
    d.rounded_rectangle([x, y, x + w, y + h], radius=px * 0.25, fill=(0, 0, 0, int(165 * a))); d.rectangle([x, y, x + px * 0.22, y + h], fill=_c(accent, a))
    d.text((x + px * 0.65, y + px * 0.25), s, font=f, fill=_c(WHITE, a)); reg.add("chip_" + s, (x, y, x + w, y + h), a); TR.note(s, px, (x, y, x + w, y + h), WHITE, a)


# --------------------------------------------------------------- diagrams -----
class Diagram:
    """base: a self-contained, time-parametrised picture. Looks like a layers.Scene to sequence.Shot."""
    kind = "ILLUSTRATION"

    def __init__(self, size=(1920, 1080), duration=1.0, name="diagram"):
        self.size, self.duration, self.name, self.start = tuple(size), float(duration), name, 0.0
        self.end = float(duration); self.reg = T.Registry()

    def render(self, t): raise NotImplementedError

    def manifest(self): return dict(name=self.name, kind=self.kind, duration=self.duration, size=self.size, evidence_pixels=False)


class RadarGeometryDiagram(Diagram):
    """EP004 S3: why a radar satellite sees ground motion. ILLUSTRATION only (labelled on screen). `tl` is a dict of named time windows in seconds.

    Drawn from `los_change`, so the extra range, the line-of-sight component and the phase shift on the panel come from ONE geometry; the shown drop
    is exaggerated and says so. The phase panel scale is illustrative (labelled). No distance, angle or rate is printed.
    Camera: the diagram is drawn at 2x and cropped, so the push-in on the geometry stays sharp (no upscaling); the HUD panel and text stay in screen space."""
    DEFAULT_TL = dict(sat_in=(0.2, 1.2), beam=(1.0, 1.3), pulse1=(1.3, 2.1), echo1=(2.1, 2.9), wave1=(2.7, 4.0), sink=(4.2, 6.0), pulse2=(6.2, 7.0), echo2=(7.0, 7.8),
                      wave2=(6.9, 8.0), shift=(7.9, 8.5), push=(8.6, 9.4), los=(9.4, 10.3), vertical=(10.2, 11.0))
    CAPTIONS = [(0.9, 2.7, "Radar pulses hit the ground and bounce back."), (2.7, 4.2, "Each echo's phase records the distance to the ground.", ("phase", "distance")),
                (4.2, 6.2, "Later, the ground has sunk.", ("sunk.",)), (6.2, 8.6, "The second echo's phase has shifted.", ("shifted.",)),
                (8.8, 10.4, "Radar sees motion along its line of sight,", ("line", "of", "sight,")), (10.4, 11.9, "not the straight-down drop.", ("straight-down",))]

    def __init__(self, size=(1920, 1080), duration=12.0, name="S3_radar_geometry", tl=None, drop=110.0, sat=(420, 200), pt=(880, 700), captions=None,
                 zoom=2.0, focus=(1000, 760), phase_scale=0.5):
        super().__init__(size, duration, name); self.tl = dict(self.DEFAULT_TL, **(tl or {})); self.drop = float(drop); self.sat, self.pt = sat, pt
        self.captions = captions or self.CAPTIONS; self.geo = los_change(sat, pt, (0, drop)); self.surface_y = pt[1]; self.bowl_w = 230.0; self.bowl_c = float(pt[0])
        self.panel = (1240, 170, 1850, 590); self.zoom, self.focus, self.phase_scale = float(zoom), tuple(focus), float(phase_scale); self.building_x = pt[0] - 330

    def _w(self, key, t): a, b = self.tl[key]; return E.seg(t, a, b)

    def _depth(self, t): return self.drop * E.in_out_cubic(self._w("sink", t))

    def _sat_pos(self, t):
        x = E.lerp(-170, self.sat[0], E.out_cubic(self._w("sat_in", t))); return (x, self.sat[1] + 0.0003 * (x - self.sat[0]) ** 2)

    def _surface(self, x, t): return bowl_surface(x, self.surface_y, self.bowl_c, self._depth(t), self.bowl_w)

    def view(self, t):
        """camera window in diagram coordinates: (x0, y0, zoom). Zoom 1 shows the whole 1920x1080 diagram."""
        e = E.in_out_cubic(self._w("push", t)); z = E.lerp(1.0, self.zoom, e) * (1 + 0.05 * E.seg(t, self.tl["push"][1], self.duration)); w, h = 1920 / z, 1080 / z   # slow creep after the push: no frozen frame
        cx, cy = E.lerp(960, self.focus[0], e), E.lerp(540, self.focus[1], e)
        return float(np.clip(cx - w / 2, 0, 1920 - w)), float(np.clip(cy - h / 2, 0, 1080 - h)), z

    def render(self, t):
        W, H = self.size; k = W / 1920.0; sc = SS * k; g = self.geo; x0, y0, z = self.view(t)
        S = np.array(self._sat_pos(t)); S0 = np.array(self.sat, float); P0 = np.array(self.pt, float); P1 = np.array([P0[0], float(self._surface(P0[0], t))])
        P_end = P0 + (0, self.drop); F = np.array(g["foot"]); M = lambda p: ((p[0] - x0) * z * k, (p[1] - y0) * z * k)
        grad = np.linspace(0, 1, H * SS, dtype=np.float32)[:, None, None]; top = np.array(INK, np.float32); bot = np.array((18, 28, 42), np.float32)
        base = Image.fromarray((top * (1 - grad) + bot * grad).repeat(W * SS, 1).astype(np.uint8)); bd = ImageDraw.Draw(base)
        ov = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); od = ImageDraw.Draw(ov); gl = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
        for gx in range(0, 1921, 120): bd.line([(gx * sc, 0), (gx * sc, H * SS)], fill=(26, 36, 50), width=SS)
        for gy in range(0, 1081, 120): bd.line([(0, gy * sc), (W * SS, gy * sc)], fill=(26, 36, 50), width=SS)

        # orbit + side-looking satellite
        u_los = (P0 - S0) / np.linalg.norm(P0 - S0); xs = np.linspace(0, 1000, 80); orb = np.stack([xs, S0[1] + 0.0003 * (xs - S0[0]) ** 2], 1)
        sf = 1 - E.smooth(E.seg(t, self.tl["push"][0] - 0.3, self.tl["push"][0] - 0.05))                      # satellite and orbit leave the frame with the push
        for i in range(0, len(orb) - 1, 2): od.line([tuple(orb[i] * sc), tuple(orb[i + 1] * sc)], fill=_c(MUTED, 0.55 * sf), width=int(3 * sc))
        sa = E.clamp(self._w("sat_in", t) * 3) * sf
        if sa > 0: satellite(od, S * k, u_los, scale=SS, alpha=sa, size=1.35 * k)

        # ground: the surface follows one Gaussian bowl; the measurement point sits at its centre, a building at its edge
        gx = np.linspace(0, 1920, 400); top_line = np.stack([gx, self._surface(gx, t)], 1)
        bd.polygon([(x * sc, y * sc) for x, y in [(0, 1080)] + [tuple(p) for p in top_line] + [(1920, 1080)]], fill=(44, 36, 31))
        bd.polygon([(x * sc, y * sc) for x, y in [tuple(p) for p in top_line] + [(x, y + 120) for x, y in top_line[::-1]]], fill=(66, 51, 40))
        od.line([tuple(p * sc) for p in top_line], fill=_c((196, 164, 120)), width=int(5 * sc))
        bx = self.building_x; by = float(self._surface(bx + 50, t))
        bd.rectangle([bx * sc, (by - 112) * sc, (bx + 100) * sc, by * sc], fill=(88, 102, 120), outline=(160, 176, 196), width=int(3 * sc))
        for wy in (-88, -52, -16):
            for wx in (14, 56): bd.rectangle([(bx + wx) * sc, (by + wy - 14) * sc, (bx + wx + 26) * sc, (by + wy + 4) * sc], fill=(255, 214, 140))
        sk = self._w("sink", t)
        if sk > 0.02: dashed(od, (P0[0] - 60, P0[1]), (P0[0] + 60, P0[1]), WHITE, 3, dash=10, gap=8, scale=sc, alpha=0.7 * E.clamp(sk * 3))
        od.ellipse([(P1[0] - 11) * sc, (P1[1] - 11) * sc, (P1[0] + 11) * sc, (P1[1] + 11) * sc], fill=_c(AMBER), outline=_c(INK), width=int(3 * sc))

        # line of sight (thin) and travelling wave fronts
        la = self._w("beam", t)
        if la > 0: dashed(od, S0, P0, CYAN, 3, dash=14, gap=12, scale=sc, alpha=0.40, upto=E.out_cubic(la))

        def pulse(key_out, key_back, target, color):
            a, b = self.tl[key_out]; c, e = self.tl[key_back]; v = np.asarray(target, float) - S0; r_t = float(np.linalg.norm(v)); ang = math.degrees(math.atan2(v[1], v[0]))
            if a <= t < b: f = (t - a) / (b - a); rs, al = [f * r_t - 52 * i for i in range(3)], [1.0, 0.65, 0.35]
            elif c <= t < e: f = (t - c) / (e - c); rs, al = [(1 - f) * r_t + 52 * i for i in range(3)], [0.9, 0.55, 0.28]
            else: return
            for r, aa in zip(rs, al):
                if 8 < r < r_t + 2:
                    pts = arc_points(S0, r, ang - 9, ang + 9, 32); gd.line([tuple(p * sc) for p in pts], fill=_c(color, aa), width=int(10 * sc)); od.line([tuple(p * sc) for p in pts], fill=_c(color, aa), width=int(5 * sc))
        pulse("pulse1", "echo1", P0, CYAN); pulse("pulse2", "echo2", P_end, AMBER)
        for key, col, pos in (("pulse1", CYAN, P0), ("pulse2", AMBER, P_end)):
            f = E.seg(t, self.tl[key][1] - 0.05, self.tl[key][1] + 0.45)
            if 0 < f < 1: r = 14 + 46 * f; gd.ellipse([(pos[0] - r) * sc, (pos[1] - r) * sc, (pos[0] + r) * sc, (pos[1] + r) * sc], outline=_c(col, 1 - f), width=int(6 * sc))

        # line of sight vs vertical: the exact projection from los_change
        la2 = self._w("los", t); va = self._w("vertical", t)
        if la2 > 0:
            q = P0 + (F - P0) * E.out_cubic(la2); od.line([tuple(P0 * sc), tuple(q * sc)], fill=_c(CYAN), width=int(11 * sc)); gd.line([tuple(P0 * sc), tuple(q * sc)], fill=_c(CYAN, 0.8 * (0.7 + 0.3 * math.sin(2 * math.pi * 1.1 * t))), width=int(16 * sc))
            if la2 > 0.7:
                dashed(od, P_end, F, WHITE, 3, dash=8, gap=7, scale=sc, alpha=0.85)
                n = (F - P_end) / np.linalg.norm(F - P_end); u = (F - P0) / np.linalg.norm(F - P0); m = 14
                od.line([tuple((F - n * m) * sc), tuple((F - n * m - u * m) * sc), tuple((F - u * m) * sc)], fill=_c(WHITE, 0.85), width=int(3 * sc))
        if va > 0.12: arrow(od, P0 + (-34, 4), P_end + (-34, -6), WHITE, width=7, head=26, scale=sc, upto=E.out_cubic(va))

        # camera: crop the 2x canvas (sharp up to zoom 2), then the screen-space HUD panel
        box = (x0 * sc, y0 * sc, (x0 + 1920 / z) * sc, (y0 + 1080 / z) * sc)
        img = base.resize((W, H), Image.LANCZOS, box=box).convert("RGBA"); ovs = ov.resize((W, H), Image.LANCZOS, box=box); gls = gl.resize((W, H), Image.LANCZOS, box=box)
        glow = gls.filter(ImageFilter.GaussianBlur(7 * k * z)); glow.putalpha(glow.getchannel("A").point(lambda v: int(min(255, v * 1.6)))); img.alpha_composite(glow); img.alpha_composite(ovs)

        px0, py0, px1, py1 = self.panel; pa = E.clamp(self._w("wave1", t) * 4) * (1 - E.smooth(E.seg(t, self.tl["push"][0] - 0.3, self.tl["push"][0])))
        if pa > 0.01:
            hb = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); hd = ImageDraw.Draw(hb); hv = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); hvd = ImageDraw.Draw(hv)
            hg = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); hgd = ImageDraw.Draw(hg); lam, amp = 200.0, 56.0; mid = (py0 + py1) / 2 + 20; xc1 = px0 + 30 + lam * 1.25
            hd.rounded_rectangle([px0 * sc, py0 * sc, px1 * sc, py1 * sc], radius=18 * sc, fill=(10, 16, 24, 235), outline=(60, 76, 96, 255), width=int(3 * sc))
            dashed(hvd, (px0 + 24, mid), (px1 - 24, mid), MUTED, 2, dash=6, gap=8, scale=sc, alpha=0.6)
            drift = -2 * math.pi * 0.35 * (t - 3.0)
            wv = wave(px0 + 30, px1 - 30, mid, amp, lam, drift); n1 = max(2, int(len(wv) * E.linear(self._w("wave1", t))))
            hvd.line([tuple(p * sc) for p in wv[:n1]], fill=_c(CYAN), width=int(7 * sc)); hgd.line([tuple(p * sc) for p in wv[:n1]], fill=_c(CYAN, 0.7), width=int(12 * sc))
            w2 = self._w("wave2", t)
            if w2 > 0:
                shift = (2 * g["los_component"] * self.phase_scale / lam * 2 * math.pi) % (2 * math.pi)
                wv2 = wave(px0 + 30, px1 - 30, mid, amp, lam, shift + drift); n2 = max(2, int(len(wv2) * E.linear(w2)))
                hvd.line([tuple(p * sc) for p in wv2[:n2]], fill=_c(AMBER), width=int(7 * sc)); hgd.line([tuple(p * sc) for p in wv2[:n2]], fill=_c(AMBER, 0.7), width=int(12 * sc))
                sh = self._w("shift", t)
                if sh > 0:
                    xc1 = px0 + 30 + lam * (1.0 + (0.25 - drift / (2 * math.pi)) % 1.0); xc2 = xc1 - shift / (2 * math.pi) * lam; yy = mid - amp - 26; xa, xb = min(xc1, xc2), max(xc1, xc2)
                    for xc in (xc1, xc2): dashed(hvd, (xc, yy), (xc, mid - amp + 2), WHITE, 3, dash=6, gap=5, scale=sc, alpha=0.9 * sh)
                    xe = xa + (xb - xa) * E.out_cubic(sh); hvd.line([(xa * sc, yy * sc), (xe * sc, yy * sc)], fill=_c(WHITE), width=int(7 * sc))
                    for xx in (xa, xe): hvd.line([(xx * sc, (yy - 9) * sc), (xx * sc, (yy + 9) * sc)], fill=_c(WHITE), width=int(7 * sc))
            def sm(layer): im = layer.resize((W, H), Image.LANCZOS); im.putalpha(im.getchannel("A").point(lambda v: int(v * pa))); return im
            hgl = sm(hg).filter(ImageFilter.GaussianBlur(7 * k)); img.alpha_composite(sm(hb)); img.alpha_composite(hgl); img.alpha_composite(sm(hv))

        # text layer (1x): chips, labels, captions
        ui = Image.new("RGBA", (W, H), (0, 0, 0, 0)); self.reg.reset(); px = 34 * k; cpx = 32 * k
        _chip(ui, self.reg, "ILLUSTRATION · NOT TO SCALE", (72 * k, 48 * k), cpx, AMBER, E.out_cubic(E.seg(t, 0.0, 0.5)))
        if sk > 0.05: _chip(ui, self.reg, "GROUND DROP EXAGGERATED", (72 * k, 108 * k), cpx, AMBER, E.out_cubic(E.seg(t, self.tl["sink"][0], self.tl["sink"][0] + 0.5)))
        _ui_text(ui, self.reg, "SENTINEL-1 RADAR", (84 * k, 322 * k), px, CYAN, E.out_cubic(E.seg(t, 1.0, 1.5)) * (1 - E.smooth(E.seg(t, self.tl["push"][0] - 0.3, self.tl["push"][0] - 0.05))), group="sat")
        if pa > 0.02:
            _ui_text(ui, self.reg, "ECHO PHASE · ILLUSTRATIVE", ((px0 + 24) * k, (py0 + 14) * k), px, WHITE, pa, group="panel_title")
            _ui_text(ui, self.reg, "PASS 1", ((px0 + 24) * k, (py1 - 62) * k), px, CYAN, pa, group="pass1")
            w2 = self._w("wave2", t)
            if w2 > 0.02: _ui_text(ui, self.reg, "PASS 2 · LATER", ((px0 + 200) * k, (py1 - 62) * k), px, AMBER, E.clamp(w2 * 4) * pa, group="pass2")
            sh = self._w("shift", t)
            if sh > 0.3: _ui_text(ui, self.reg, "PHASE SHIFT", ((px0 + px1) / 2 * k, (py0 + 86) * k), px, WHITE, E.out_cubic(E.seg(sh, 0.3, 1.0)) * pa, group="shift", anchor="center")
        fx_, fy_ = M(F)
        if la2 > 0.4: _ui_text(ui, self.reg, "SEEN BY RADAR: LINE OF SIGHT", (fx_ + 70 * k, fy_ + 72 * k), px, CYAN, E.out_cubic(E.seg(la2, 0.4, 1.0)), group="los")
        ax, ay = M((P0[0] - 62, P_end[1] + 28))
        if va > 0.4: _ui_text(ui, self.reg, "REAL DROP: VERTICAL", (ax, ay), px, WHITE, E.out_cubic(E.seg(va, 0.4, 1.0)), group="vert", anchor="right")
        self._captions(ui, t, k)
        img.alpha_composite(ui); return img.convert("RGB")

    def _captions(self, ui, t, k):
        """captions: dark scrim + per-glyph kinetic reveal (text.kinetic, the V2C caption motion). 48 px at 1080p = the repo's caption floor (mobile_qa.MIN_CAPTION_PX)."""
        for cap in self.captions:
            t0, t1, s = cap[:3]; emph = set(cap[3]) if len(cap) > 3 else set()
            if not (t0 - 0.01 <= t <= t1 + 0.01): continue
            a = E.out_cubic(E.seg(t, t0, t0 + 0.30)) * (1 - E.smooth(E.seg(t, t1 - 0.25, t1)))
            if a <= 0.02: continue
            px = 48 * k; f = T.font(px, True); w = T.text_width(s, f); x = (ui.width - w) / 2; y = 946 * k; d = ImageDraw.Draw(ui, "RGBA")
            box = (x - px * 0.7, y - px * 0.3, x + w + px * 0.7, y + px * 1.45); d.rounded_rectangle(box, radius=px * 0.3, fill=(0, 0, 0, int(175 * a)))
            cx, n = x, 0                                                          # emphasised words (amber, the OrbitalAtlas emphasis token) share the same per-glyph reveal clock
            for word in s.split(" "):
                T.kinetic(ui, (cx, y), word, px, AMBER if word in emph else WHITE, t, t0 + n * 0.012, per=0.012, dur=0.28, rise=0.25, out_t=t1 - 0.25 + n * 0.0, out_dur=0.2, shadow=True)
                adv = T.text_width(word + " ", f); cx += adv; n += len(word) + 1
            self.reg.add("caption", box, a); prev = TR.STATE["tag"]; TR.STATE["tag"] = "WordCaptions"                   # caption floor (48 px) applies in mobile_qa
            try: TR.note(s, px, box, WHITE, a)
            finally: TR.STATE["tag"] = prev


class EvidencePending(Diagram):
    """placeholder for a measured map whose licence or period is not cleared. Shows NO data: only a hatched field, the words and a reason.
    It must never look like a measurement (no colour scale, no map shapes)."""
    def __init__(self, size=(1920, 1080), duration=2.0, name="evidence_map_pending", reason="Measured map goes here once its licence and period are confirmed"):
        super().__init__(size, duration, name); self.reason = reason

    def render(self, t):
        W, H = self.size; k = W / 1920.0; self.reg.reset()
        im = Image.new("RGB", (W, H), (14, 20, 30)); d = ImageDraw.Draw(im)
        x0, y0, x1, y1 = 160 * k, 190 * k, 1760 * k, 890 * k
        d.rounded_rectangle([x0, y0, x1, y1], radius=22 * k, fill=(18, 27, 40), outline=(70, 88, 110), width=max(2, int(3 * k)))
        hatch = Image.new("L", (W, H), 0); hd = ImageDraw.Draw(hatch); step = 46 * k
        for i in range(-int(H / step), int((W + H) / step)): hd.line([(i * step, y1), (i * step + (y1 - y0), y0)], fill=255, width=max(1, int(3 * k)))
        mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).rounded_rectangle([x0 + 6, y0 + 6, x1 - 6, y1 - 6], radius=18 * k, fill=255)
        hm = Image.fromarray((np.asarray(hatch, np.float32) * np.asarray(mask, np.float32) / 255 * 0.22).astype(np.uint8))
        im.paste(Image.new("RGB", (W, H), (120, 140, 165)), (0, 0), hm)
        ui = Image.new("RGBA", (W, H), (0, 0, 0, 0)); a = E.out_cubic(E.seg(t, 0.35, 0.9))
        _ui_text(ui, self.reg, "EVIDENCE MAP PENDING", (W / 2, 450 * k), 72 * k, WHITE, a, group="title", anchor="center")
        _ui_text(ui, self.reg, self.reason, (W / 2, 570 * k), 36 * k, MUTED, a, bold=False, group="reason", anchor="center")
        _chip(ui, self.reg, "PLACEHOLDER · NO DATA SHOWN", (72 * k, 48 * k), 32 * k, AMBER, a)
        out = im.convert("RGBA"); out.alpha_composite(ui); return out.convert("RGB")

    def manifest(self): return dict(super().manifest(), shows_data=False, reason=self.reason)
