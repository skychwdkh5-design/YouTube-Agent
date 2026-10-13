"""Class B/C-lite: a REAL geographic camera. Orthographic globe projection of vector geodata (lon/lat in degrees, WGS84 sphere
approximation R = 6371.0088 km), with continuous zoom from whole Earth to a city region.

What this is: exact map-projection mathematics + public-domain vector data (Natural Earth). Everything drawn from the data is placed by
its lon/lat. What it is NOT: no terrain, no satellite imagery, no georeferenced photos, no true 3D perspective; accuracy is that of the
data (Natural Earth 1:10M ≈ 1-2 km at best) and of the sphere approximation (≈0.3 % scale error vs the ellipsoid). Stylised map and
documentary imagery must stay visibly separate (see docs/ORBITALATLAS_VISUAL_MASTER.md).

Data: load with GeoData(dir). Files are fetched by tools/fetch_natural_earth.sh (not committed)."""
import json
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from . import easing as E, text as T, layers as L

R_KM = 6371.0088
DEG = math.pi / 180.0


# ------------------------------------------------------------------ geometry --
def ll_to_vec(lon, lat):
    lon = np.asarray(lon, float) * DEG; lat = np.asarray(lat, float) * DEG
    return np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], -1)


def vec_to_ll(v):
    v = np.asarray(v, float)
    return np.degrees(np.arctan2(v[..., 1], v[..., 0])), np.degrees(np.arcsin(np.clip(v[..., 2], -1, 1)))


def haversine_km(lon1, lat1, lon2, lat2):
    p1, p2 = np.asarray(lat1) * DEG, np.asarray(lat2) * DEG
    dl = (np.asarray(lon2) - np.asarray(lon1)) * DEG; dp = p2 - p1
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def slerp(v0, v1, t):
    v0, v1 = np.asarray(v0, float), np.asarray(v1, float)
    d = float(np.clip(v0 @ v1, -1, 1)); om = math.acos(d)
    if om < 1e-9: return v0
    return (math.sin((1 - t) * om) * v0 + math.sin(t * om) * v1) / math.sin(om)


class GlobeView:
    """orthographic view. span_km = ground distance across the screen HEIGHT at the centre (small-angle). bearing: degrees clockwise,
    the direction that points to the top of the screen (0 = north up)."""
    def __init__(self, lon, lat, span_km, bearing, screen):
        self.lon, self.lat, self.span, self.bearing = float(lon), float(lat), float(span_km), float(bearing)
        self.W, self.H = screen; self.R = self.H * R_KM / self.span                 # px per Earth radius
        c = ll_to_vec(lon, lat); east = np.array([-math.sin(lon * DEG), math.cos(lon * DEG), 0.0])
        north = np.cross(c, east); th = bearing * DEG                                # rotate screen axes by the bearing
        self.c = c; self.ex = east * math.cos(th) - north * math.sin(th); self.ey = north * math.cos(th) + east * math.sin(th)
        self.cx, self.cy = self.W / 2, self.H / 2

    @property
    def km_per_px(self): return R_KM / self.R

    def pt(self, lon, lat):
        """-> (x, y, visible) arrays; visible = on the near hemisphere."""
        v = ll_to_vec(lon, lat); x = v @ self.ex; y = v @ self.ey; z = v @ self.c
        return self.cx + self.R * x, self.cy - self.R * y, z > 0

    def inv(self, X, Y):
        """screen pixel grids -> (lon, lat, valid) where valid = inside the globe disc."""
        x = (X - self.cx) / self.R; y = -(Y - self.cy) / self.R; r2 = x * x + y * y
        ok = r2 <= 1.0; z = np.sqrt(np.clip(1 - r2, 0, 1))
        v = x[..., None] * self.ex + y[..., None] * self.ey + z[..., None] * self.c
        lon, lat = vec_to_ll(v); return lon, lat, ok, z


class GeoCamera:
    """keys: dict(t, lon, lat, span_km, bearing=0, ease='smoother', arc=0). The centre moves along the GREAT CIRCLE (slerp), the span in log
    space; `arc` > 0 adds a zoom-out bump mid-segment (fly-over feel for long hops). mode 'spline' = monotone cubic through unit-vector
    components (flowing path, no stops at interior keys)."""
    def __init__(self, keys, screen=(1920, 1080), mode="eased", default_ease="smoother", anchors=None):
        self.anchors = dict(anchors or {}); self.screen, self.mode = tuple(screen), mode; self.keys = sorted(keys, key=lambda k: k["t"]); self.default = E.get(default_ease)
        self.ts = [k["t"] for k in self.keys]; self.vecs = [ll_to_vec(k["lon"], k["lat"]) for k in self.keys]
        self.ease = [E.get(k.get("ease", default_ease)) for k in self.keys]
        if mode == "spline" and len(self.keys) > 2:
            ch = [[v[i] for v in self.vecs] for i in range(3)] + [[math.log(k["span_km"]) for k in self.keys], [k.get("bearing", 0.0) for k in self.keys]]
            self._ch = ch; self._m = [E.pchip_slopes(self.ts, y) for y in ch]
    @property
    def start(self): return self.ts[0]
    @property
    def end(self): return self.ts[-1]

    def view(self, t):
        k = self.keys
        if t <= self.ts[0] or len(k) == 1: kk = k[0]; return GlobeView(kk["lon"], kk["lat"], kk["span_km"], kk.get("bearing", 0.0), self.screen)
        if t >= self.ts[-1]: kk = k[-1]; return GlobeView(kk["lon"], kk["lat"], kk["span_km"], kk.get("bearing", 0.0), self.screen)
        if self.mode == "spline" and hasattr(self, "_ch"):
            q = [E.hermite(t, self.ts, y, m) for y, m in zip(self._ch, self._m)]; v = np.array(q[:3]); v /= np.linalg.norm(v)
            lon, lat = vec_to_ll(v); return GlobeView(lon, lat, math.exp(q[3]), q[4], self.screen)
        i = max(j for j in range(len(k) - 1) if self.ts[j] <= t); a, b = k[i], k[i + 1]; e = self.ease[i](E.seg(t, a["t"], b["t"]))
        v = slerp(self.vecs[i], self.vecs[i + 1], e); lon, lat = vec_to_ll(v)
        span = E.lerp_log(a["span_km"], b["span_km"], e)
        arc = a.get("arc", 0.0)
        if arc: span *= 1 + arc * math.sin(math.pi * e)
        return GlobeView(lon, lat, span, E.lerp(a.get("bearing", 0.0), b.get("bearing", 0.0), e), self.screen)

    def check(self, must_show=None, safe=0.05, step=1 / 15, tmax=None, max_magnification=None, span_limits=(20.0, 40000.0)):
        """same contract as camera.Camera.check: issues as (kind, t, detail). must_show = {anchor_name: (t0, t1)} with anchors = {name: (lon, lat)};
        max_magnification is ignored (vector data has no pixel limit; span_limits bounds the useful zoom range instead)."""
        issues = []; tmax = tmax if tmax is not None else self.ts[-1]; W, H = self.screen
        for i in range(int((tmax - self.ts[0]) / step) + 1):
            t = self.ts[0] + i * step; v = self.view(t)
            if not (span_limits[0] <= v.span <= span_limits[1]): issues.append(("span_out_of_range", round(t, 3), round(v.span, 1)))
            if abs(v.lat) > 85: issues.append(("pole_view", round(t, 3), round(v.lat, 2)))
            for name, (t0, t1) in (must_show or {}).items():
                if t0 <= t <= t1:
                    x, y, vis = v.pt(*self.anchors[name]); m = safe * min(W, H)
                    if not (bool(vis) and m <= x <= W - m and m <= y <= H - m): issues.append(("anchor_outside_safe_frame", round(t, 3), name))
        return issues

    def speed(self, t, dt=1 / 60):
        """apparent speed in screen px per frame (centre travel + zoom)."""
        a, b = self.view(t - dt), self.view(t + dt)
        x, y, vis = b.pt(a.lon, a.lat); move = math.hypot(x - b.cx, y - b.cy)
        return float((move + abs(math.log(b.span / a.span)) * 0.5 * self.screen[1]) / (2 * dt * 30))


# ----------------------------------------------------------------------- data --
def _polys(geom):
    return geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]


class GeoData:
    """Natural Earth GeoJSON loader. Directory must contain the files listed in tools/fetch_natural_earth.sh."""
    def __init__(self, directory):
        self.dir = directory; self._c = {}
    def _load(self, name):
        if name not in self._c:
            p = os.path.join(self.dir, name + ".geojson")
            if not os.path.exists(p): raise FileNotFoundError(f"{p} (run tools/fetch_natural_earth.sh)")
            with open(p) as fh: self._c[name] = json.load(fh)["features"]
        return self._c[name]
    def land(self, res="10m"): return [poly for f in self._load(f"ne_{res}_land") for poly in _polys(f["geometry"])]
    def country(self, name, res="10m", key="ADMIN"):
        out = []
        for f in self._load(f"ne_{res}_admin_0_countries"):
            if f["properties"].get(key) == name or f["properties"].get("ADM0_A3") == name: out += _polys(f["geometry"])
        if not out: raise KeyError(name)
        return out
    def countries(self, res="50m"): return [(f["properties"]["ADMIN"], _polys(f["geometry"])) for f in self._load(f"ne_{res}_admin_0_countries")]
    def feature(self, fname, key, name):
        for f in self._load(fname):
            if f["properties"].get(key) == name: return f
        raise KeyError(name)
    def place(self, name, country=None):
        for f in self._load("ne_10m_populated_places"):
            p = f["properties"]
            if p["NAME"] == name and (country is None or p.get("ADM0NAME") == country): return tuple(f["geometry"]["coordinates"])
        raise KeyError(name)
    def ring_lines(self, polys, min_pts=3):
        """exterior+interior rings as (n,2) lon/lat arrays."""
        return [np.array(r, float) for poly in polys for r in poly if len(r) >= min_pts]


def polygon_centroid(polys):
    """area-weighted planar centroid in lon/lat. For LABEL anchoring only (not a geodetic centroid)."""
    A = cx = cy = 0.0
    for poly in polys:
        r = np.array(poly[0]); x, y = r[:, 0], r[:, 1]; a = x[:-1] * y[1:] - x[1:] * y[:-1]; s = a.sum() / 2
        if abs(s) < 1e-12: continue
        A += s; cx += ((x[:-1] + x[1:]) * a).sum() / 6; cy += ((y[:-1] + y[1:]) * a).sum() / 6
    return cx / A, cy / A


class GeoRaster:
    """equirectangular coverage masks in several resolution windows; sample() returns the finest available coverage 0..1 at lon/lat arrays.
    Built by rasterising polygons (even-odd holes drawn as 0) with 2x supersampling."""
    def __init__(self): self.levels = []
    def add(self, polys, bbox, res_deg, ss=2):
        lon0, lat0, lon1, lat1 = bbox; w = int(round((lon1 - lon0) / res_deg)); h = int(round((lat1 - lat0) / res_deg))
        im = Image.new("L", (w * ss, h * ss), 0); d = ImageDraw.Draw(im)
        for poly in polys:
            for k, ring in enumerate(poly):
                r = np.asarray(ring, float)
                if r[:, 0].max() < lon0 - 1 or r[:, 0].min() > lon1 + 1 or r[:, 1].max() < lat0 - 1 or r[:, 1].min() > lat1 + 1: continue
                xy = np.stack([(r[:, 0] - lon0) / res_deg * ss, (lat1 - r[:, 1]) / res_deg * ss], 1)
                d.polygon([tuple(p) for p in xy.tolist()], fill=255 if k == 0 else 0)
        arr = np.asarray(im.reduce(ss), np.float32) / 255.0
        self.levels.append((bbox, res_deg, arr)); self.levels.sort(key=lambda L_: -L_[1])      # coarse first
        return self
    def sample(self, lon, lat):
        out = np.zeros(lon.shape, np.float32)
        for (lon0, lat0, lon1, lat1), res, arr in self.levels:
            h, w = arr.shape; fx = (lon - lon0) / res - 0.5; fy = (lat1 - lat) / res - 0.5
            inside = (lon >= lon0) & (lon <= lon1) & (lat >= lat0) & (lat <= lat1)
            if not inside.any(): continue
            x0 = np.clip(np.floor(fx).astype(np.int32), 0, w - 2); y0 = np.clip(np.floor(fy).astype(np.int32), 0, h - 2)
            ax = np.clip(fx - x0, 0, 1); ay = np.clip(fy - y0, 0, 1)
            v = (arr[y0, x0] * (1 - ax) * (1 - ay) + arr[y0, x0 + 1] * ax * (1 - ay) + arr[y0 + 1, x0] * (1 - ax) * ay + arr[y0 + 1, x0 + 1] * ax * ay)
            out = np.where(inside, v, out)
        return out


def visible_runs(x, y, vis, W, H, margin=60):
    """split a projected polyline into runs that are on the near hemisphere and (nearly) on screen; each run keeps one neighbour point so
    lines reach the frame edge. Returns a list of (n,2) arrays."""
    inside = vis & (x > -margin) & (x < W + margin) & (y > -margin) & (y < H + margin)
    idx = np.nonzero(inside)[0]
    if len(idx) < 1: return []
    cuts = np.nonzero(np.diff(idx) > 1)[0] + 1; out = []
    for grp in np.split(idx, cuts):
        a, b = max(grp[0] - 1, 0), min(grp[-1] + 2, len(x))
        sel = slice(a, b); keep = vis[sel]
        if keep.all() and b - a > 1: out.append(np.stack([x[sel], y[sel]], 1))
        elif len(grp) > 1: out.append(np.stack([x[grp[0]:grp[-1] + 1], y[grp[0]:grp[-1] + 1]], 1))
    return out


# ------------------------------------------------------------------- scene -----
class GeoStyle:
    """stylised map look. All colours are tokens, override per episode."""
    def __init__(self, space=(5, 8, 14), ocean_deep=(8, 30, 52), ocean_shallow=(16, 58, 88), land=(52, 62, 66), land_hi=(86, 96, 90), border=(205, 215, 225),
                 coast=(150, 205, 215), graticule=(120, 160, 190), glow=(70, 140, 220)):
        self.space, self.ocean_deep, self.ocean_shallow, self.land, self.land_hi = space, ocean_deep, ocean_shallow, land, land_hi
        self.border, self.coast, self.graticule, self.glow = border, coast, graticule, glow


class GeoScene:
    """one geographic shot. layers: raster land/ocean shading (by inverse projection), graticule, coast + borders (projected lines), overlays.
    render(t) -> PIL RGB. Camera motion blur by temporal sub-sampling when moving fast."""
    def __init__(self, camera, land_raster, coast_lines, border_lines=(), size=(1920, 1080), overlays=(), style=None, name="geo", graticule=True,
                 max_blur_samples=8, blur_threshold=10.0, stars_seed=5, base_scale=None):
        self.camera, self.land, self.coast, self.borders = camera, land_raster, coast_lines, border_lines
        self.size, self.overlays, self.style, self.name, self.graticule = tuple(size), list(overlays), style or GeoStyle(), name, graticule
        self.max_blur_samples, self.blur_threshold = max_blur_samples, blur_threshold; self.reg = T.Registry()
        W, H = self.size; rng = np.random.default_rng(stars_seed); bg = np.zeros((H, W, 3), np.float32); bg[:] = self.style.space
        for _ in range(int(W * H / 3500)):
            x, y = rng.integers(0, W), rng.integers(0, H); bg[y, x] += rng.uniform(40, 150)
        self._bg = bg; Y, X = np.mgrid[0:H, 0:W].astype(np.float32); self._X, self._Y = X, Y
        self.base_scale = base_scale if base_scale else (0.5 if W > 1280 else 1.0); sc = self.base_scale
        Ys, Xs = np.mgrid[0:int(H * sc), 0:int(W * sc)].astype(np.float32); self._Xs, self._Ys = (Xs + 0.5) / sc - 0.5, (Ys + 0.5) / sc - 0.5
        self._coastbbox = [(l[:, 0].min(), l[:, 1].min(), l[:, 0].max(), l[:, 1].max()) for l in coast_lines]
    @property
    def start(self): return self.camera.start
    @property
    def end(self): return self.camera.end

    def _base(self, view):
        """sphere shading + land by inverse projection at `base_scale` resolution (upsampled; coast/border lines are drawn crisp at full
        resolution afterwards), atmosphere + stars at full resolution."""
        W, H = self.size; st = self.style; sc = self.base_scale; w, h = int(W * sc), int(H * sc)
        lon, lat, ok, z = view.inv(self._Xs, self._Ys)
        land = np.where(ok, self.land.sample(lon, lat), 0.0).astype(np.float32)
        light = np.clip(0.55 + 0.45 * z ** 0.55, 0, 1)                                    # limb darkening (z = cos of angle from the view centre)
        deep, shal = np.array(st.ocean_deep, np.float32), np.array(st.ocean_shallow, np.float32)
        ocean = deep + (shal - deep) * (0.25 + 0.75 * z[..., None] ** 2)
        # stylistic shoreline glow (NOT bathymetry): water near land is lighter
        blur = np.asarray(Image.fromarray((land * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(2, 14 * sc * H / 1080))), np.float32) / 255.0
        ocean = ocean + (np.array(st.ocean_shallow, np.float32) * 0.55) * np.clip(blur * 1.6, 0, 1)[..., None] * (1 - land[..., None])
        landc = np.array(st.land, np.float32) * (0.8 + 0.2 * z[..., None] ** 2)
        col = (ocean * (1 - land[..., None]) + landc * land[..., None]) * light[..., None]
        rim = np.clip(1 - z, 0, 1) ** 3 * 0.55; col = col + rim[..., None] * np.array(st.glow, np.float32)
        col_full = np.asarray(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) if sc != 1.0 else col
        r = np.hypot(self._X - view.cx, self._Y - view.cy) / view.R
        inside = np.clip((1.0 - r) * view.R, 0, 1)[..., None]                              # 1-px antialiased limb
        outside = np.where(r > 1.0, np.exp(-(r - 1.0) * 26.0) * 0.9, 0.0)
        img = col_full * inside + (self._bg + outside[..., None] * np.array(st.glow, np.float32)) * (1 - inside)
        return img, land, (lon, lat, ok, z)

    def _lines(self, view, span_alpha):
        """graticule + coast + borders as projected polylines on a 2x supersampled layer; hidden (far-side) points break the lines."""
        W, H = self.size; k = H / 1080.0; layer = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(layer, "RGBA")
        def draw(lons, lats, color, alpha, width):
            x, y, vis = view.pt(lons, lats)
            for run in visible_runs(x, y, vis, W, H):
                d.line([tuple(q) for q in (run * 2).tolist()], fill=tuple(color) + (int(255 * alpha),), width=max(1, int(width * k * 2)), joint="curve")
        st = self.style
        if self.graticule:
            step = 30 if view.span > 8000 else 10 if view.span > 2500 else 5 if view.span > 900 else 1 if view.span > 90 else 0.5
            a = 0.16 * span_alpha
            for lo in np.arange(-180, 180.01, step): draw(np.full(181, lo), np.linspace(-85, 85, 181), st.graticule, a, 1.0)
            for la in np.arange(-80, 80.01, step): draw(np.linspace(-180, 180, 721), np.full(721, la), st.graticule, a, 1.0)
        lim = view.span / R_KM * 1.6 / DEG                                                 # degrees of arc worth drawing around the centre
        def near(bb): return not (bb[0] > view.lon + lim / max(math.cos(view.lat * DEG), 0.2) or bb[2] < view.lon - lim / max(math.cos(view.lat * DEG), 0.2) or bb[1] > view.lat + lim or bb[3] < view.lat - lim)
        step_pts = 1 if view.span < 1500 else 2 if view.span < 4000 else 4
        for ln, bb in zip(self.coast, self._coastbbox):
            if view.span < 20000 and near(bb) or view.span >= 20000: draw(ln[::step_pts, 0], ln[::step_pts, 1], st.coast, 0.85, 1.4)
        return layer.reduce(2)

    def _world(self, t, view):
        img, land, geo = self._base(view)
        ctx = L.Ctx(self.size, view, t)
        ctx.geo = geo; ctx.land = land
        frame = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
        for o in self.overlays:
            if o.layer == "world": o.draw(ctx)
        frame.alpha_composite(ctx.fills)
        lines = self._lines(view, 1.0); frame.alpha_composite(lines)
        for s in ctx.strokes(): frame.alpha_composite(s)
        return frame.convert("RGB")

    def render(self, t, blur=True, overlays=True):
        view = self.camera.view(t); self.last_view = view
        speed = self.camera.speed(t) if blur else 0.0
        n = int(min(self.max_blur_samples, math.ceil(speed * 0.35 / 2.0) + 1)) if speed > self.blur_threshold else 1
        acc = None
        for i in range(n):
            tt = t + (0 if n == 1 else (i / (n - 1) - 0.5) / 85)
            v = view if n == 1 else self.camera.view(tt)
            a = np.asarray(self._world(tt, v), np.float32); acc = a if acc is None else acc + a
        frame = Image.fromarray((acc / n + 0.5).astype(np.uint8))
        if overlays:
            self.reg.reset(); uctx = L.Ctx(self.size, view, t, reg=self.reg); uctx.geo = None
            for o in self.overlays:
                if o.layer == "ui": o.draw(uctx)
            base = frame.convert("RGBA"); base.alpha_composite(uctx.fills)
            for st in uctx.strokes(): base.alpha_composite(st)
            base.alpha_composite(uctx.ui); frame = base.convert("RGB")
        return frame

    def manifest(self): return [o.describe() for o in self.overlays]


# ------------------------------------------------------------------- overlays --
class GeoFill(L.Overlay):
    """tint inside polygons given in lon/lat (Natural Earth country, etc.), optionally grown by a geodesic radial wipe from (lon, lat)."""
    layer = "world"; cls = "MAP"
    def __init__(self, polys, bbox, color, t0, dur=1.0, alpha=0.4, anchor=None, max_km=None, res_deg=0.01, out_t=None, source=None, water_only=False):
        self.ras = GeoRaster().add(polys, bbox, res_deg); self.color, self.t0, self.dur, self.alpha, self.anchor, self.max_km, self.out_t = color, t0, dur, alpha, anchor, max_km, out_t
        self.source, self.water_only = source, water_only; self.validation = "polygons from the cited dataset; fill follows the data"
    def draw(self, ctx):
        e = E.smoother(E.seg(ctx.t, self.t0, self.t0 + self.dur)); a = self.alpha * e
        if self.out_t is not None: a *= 1 - E.smooth(E.seg(ctx.t, self.out_t, self.out_t + 0.5))
        if a <= 0.003 or ctx.geo is None: return
        lon, lat, ok, z = ctx.geo; m = self.ras.sample(lon, lat) * ok
        if self.water_only: m = m * (1 - ctx.land)
        if self.anchor is not None and self.max_km:
            dist = haversine_km(self.anchor[0], self.anchor[1], lon, lat); r = self.max_km * e; fe = max(10.0, ctx.view.km_per_px * 40)
            u = np.clip((r - dist) / fe, 0, 1); m = m * (u * u * (3 - 2 * u))
        al = Image.fromarray((np.clip(m * a, 0, 1) * 255).astype(np.uint8))
        if al.size != ctx.size: al = al.resize(ctx.size, Image.BICUBIC)
        ov = Image.new("RGBA", ctx.size, tuple(self.color) + (0,)); ov.putalpha(al); ctx.fills.alpha_composite(ov)


class GeoPolyline(L.Overlay):
    """draw-on polyline in lon/lat (arc length by great-circle distance); breaks at the horizon."""
    layer = "world"; cls = "MAP"
    def __init__(self, lonlat, t0, dur=1.2, color=T.THEME.amber, width=3.0, glow=1.0, ease="smoother", closed=False, fade_out=None, source=None):
        p = np.asarray(lonlat, float); self.p = np.vstack([p, p[:1]]) if closed else p
        seg = haversine_km(self.p[:-1, 0], self.p[:-1, 1], self.p[1:, 0], self.p[1:, 1]); self.cum = np.concatenate([[0], np.cumsum(seg)])
        self.t0, self.dur, self.color, self.width, self.glow, self.ease, self.fade_out, self.source = t0, dur, color, width, glow, E.get(ease), fade_out, source
        self.validation = "geometry from the cited dataset"
    def draw(self, ctx):
        f = self.ease(E.seg(ctx.t, self.t0, self.t0 + self.dur))
        if f <= 0: return
        a = 1.0 if self.fade_out is None else 1 - E.smooth(E.seg(ctx.t, self.fade_out[0], self.fade_out[0] + self.fade_out[1]))
        if a <= 0: return
        n = int(np.searchsorted(self.cum, self.cum[-1] * f, side="right")); pts = self.p[:max(n, 2)]
        x, y, vis = ctx.view.pt(pts[:, 0], pts[:, 1]); s = ctx.stroke(self.color, self.glow); k = ctx.size[1] / 1080
        for run in visible_runs(x, y, vis, *ctx.size): s.line(run, self.width * k, a)


class GeoMarker(L.Overlay):
    """pulse marker at a lon/lat with an optional label plate (screen px offset). Hidden when the point is on the far side."""
    layer = "ui"; cls = "MAP"
    def __init__(self, lonlat, t0, label=None, color=T.THEME.amber, r=14.0, label_offset=(70, -60), out_t=None, group=None, source=None):
        self.ll, self.t0, self.label, self.color, self.r, self.off, self.out_t, self.group, self.source = lonlat, t0, label, color, r, label_offset, out_t, group, source
        self.validation = "position = lon/lat of the cited place point"
    def draw(self, ctx):
        k = ctx.size[1] / 1080; a = E.out_cubic(E.seg(ctx.t, self.t0, self.t0 + 0.4))
        if self.out_t is not None: a *= 1 - E.smooth(E.seg(ctx.t, self.out_t, self.out_t + 0.3))
        x, y, vis = ctx.view.pt(self.ll[0], self.ll[1])
        if a <= 0.003 or not bool(vis): return
        c = np.array([float(x), float(y)]); s = ctx.stroke(self.color, 0.9)
        s.ring(c, self.r * k * (0.6 + 0.4 * E.out_cubic(E.seg(ctx.t, self.t0, self.t0 + 0.4))), 3 * k, a); s.dot(c, 4 * k, a)
        ph = ((ctx.t - self.t0) % 1.4) / 1.4; s.ring(c, self.r * k * (1 + 2.2 * ph), 1.8 * k, a * (1 - ph) * 0.8)
        if self.label:
            e = c + np.array(self.off) * k; s.line([c, e], 2 * k, a * 0.85)
            T.plate(ctx.ui, (e[0] + 4 * k, e[1] - 18 * k), self.label, 30 * k, ctx.t, self.t0 + 0.25, out_t=self.out_t, accent=self.color, reg=ctx.reg, group=self.group or self.label, bold=True)


class GeoLabel(L.Overlay):
    """place-name text anchored at a lon/lat (letters rise in). Size is a screen height fraction; `angle` in screen degrees (ccw)."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, lonlat, text, t0, px_frac=0.05, color=T.THEME.text, angle=0.0, track=0.28, per=0.045, out_t=None, out_dur=0.4, glow=0.8, group=None, source=None, offset_px=(0, 0)):
        self.ll, self.text, self.t0, self.px, self.color, self.angle, self.track, self.per, self.out_t, self.out_dur, self.glow = lonlat, text, t0, px_frac, color, angle, track, per, out_t, out_dur, glow
        self.group, self.source, self.offset = group or text, source, offset_px; self.validation = "anchor = lon/lat from the cited dataset (label position, not a boundary)"
    def draw(self, ctx):
        x, y, vis = ctx.view.pt(self.ll[0], self.ll[1])
        if not bool(vis): return
        T.reveal_label(ctx.ui, (float(x) + self.offset[0], float(y) + self.offset[1]), self.text, self.px * ctx.size[1], self.color, ctx.t, self.t0, angle=self.angle, track=self.track,
                       per=self.per, out_t=self.out_t, out_dur=self.out_dur, glow=self.glow, reg=ctx.reg, group=self.group)


class ScaleBar(L.Overlay):
    """km scale at the screen centre (true there; orthographic scale falls off toward the limb)."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, t0=0.0, xy_frac=(0.04, 0.93), out_t=None): self.t0, self.xy, self.out_t = t0, xy_frac, out_t; self.validation = "length = km_per_px at the screen centre"
    def draw(self, ctx):
        a = E.smooth(E.seg(ctx.t, self.t0, self.t0 + 0.6)) * (1 - (E.smooth(E.seg(ctx.t, self.out_t, self.out_t + 0.4)) if self.out_t else 0))
        if a <= 0.01: return
        W, H = ctx.size; kpp = ctx.view.km_per_px; target = W * 0.12 * kpp; mag = 10 ** math.floor(math.log10(target)); n = max(c for c in (1, 2, 5, 10) if c * mag <= target)
        km = n * mag; px = km / kpp; x, y = self.xy[0] * W, self.xy[1] * H; k = H / 1080; d = ImageDraw.Draw(ctx.ui, "RGBA"); col = (234, 240, 246, int(230 * a))
        d.line([(x, y), (x + px, y)], fill=col, width=max(2, int(3 * k))); d.line([(x, y - 8 * k), (x, y + 8 * k)], fill=col, width=max(2, int(3 * k))); d.line([(x + px, y - 8 * k), (x + px, y + 8 * k)], fill=col, width=max(2, int(3 * k)))
        f = T.font(22 * k, True); lab = f"{km:g} km"; d.text((x, y - 36 * k), lab, font=f, fill=col)
        ctx.reg.add("scalebar", (x, y - 36 * k, x + max(px, f.getlength(lab)), y + 10 * k), a)


class Breadcrumb(L.Overlay):
    """vertical location ladder (e.g. EARTH > ARABIAN PENINSULA > ...) with the active step highlighted at its time."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, steps, xy_frac=(0.04, 0.06), px_frac=0.021, out_t=None):
        self.steps, self.xy, self.px, self.out_t = steps, xy_frac, px_frac, out_t; self.validation = "labels only"      # steps: [(label, t_on, t_next)]
    def draw(self, ctx):
        W, H = ctx.size; px = self.px * H; x, y = self.xy[0] * W, self.xy[1] * H; d = ImageDraw.Draw(ctx.ui, "RGBA"); f = T.font(px, True)
        g = 1 - (E.smooth(E.seg(ctx.t, self.out_t, self.out_t + 0.4)) if self.out_t else 0)
        for i, (name, t_on, t_off) in enumerate(self.steps):
            a_in = E.out_cubic(E.seg(ctx.t, t_on - 0.2, t_on + 0.35)) * g
            if a_in <= 0.01: continue
            act = E.smooth(E.seg(ctx.t, t_on, t_on + 0.3)) * (1 - E.smooth(E.seg(ctx.t, t_off - 0.1, t_off + 0.3)) if t_off else 1.0)
            yy = y + i * px * 1.9; col = tuple(int(c0 + (c1 - c0) * act) for c0, c1 in zip((120, 135, 150), T.THEME.amber)); al = int(255 * a_in * (0.55 + 0.45 * act))
            d.rectangle([x, yy + px * 0.1, x + px * 0.45, yy + px * 0.1 + px * 0.9], fill=col + (al,)); d.text((x + px * 0.9, yy), name, font=f, fill=col + (al,))
            ctx.reg.add("crumb%d" % i, (x, yy, x + px * 0.9 + f.getlength(name), yy + px * 1.2), a_in)
