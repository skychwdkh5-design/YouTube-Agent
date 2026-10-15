"""pbrt3d - true 3-D rendering for OrbitalAtlas through pbrt-v4 (physically based path tracer, CPU, open source) + Intel Open Image Denoise.

What it is: a small Python scene writer. Real triangle meshes / quadrics, a perspective camera (thin lens: depth of field; start/end camera
transforms: true motion blur), PBR materials (diffuse, coated diffuse, conductor with measured metal spectra, dielectric), image textures and
bump maps, a physical sky (pbrt `imgtool makesky`) plus a sun (distant light), emissive geometry (area lights). Global illumination, soft and
contact shadows and ambient occlusion come from path tracing itself - nothing is faked in screen space.
Per frame: write `frame.pbrt` -> `pbrt` renders a linear-light EXR (gbuffer film: colour + albedo + normal) -> `imgtool` splits PFMs ->
`oidnDenoise` (albedo + normal guided) -> numpy filmic tone map + grade (`finish`).

Toolchain (built from GitHub sources; see docs/production-knowledge/TRUE_3D_PIPELINE.md): env PBRT_BIN (pbrt, imgtool) and OIDN_BIN.
"""
# effect-reuse-checked: scene3d.py is a flat-shaded painter (polygons sorted by depth, no light transport); nothing in the repo path-traces
# real geometry. This module only writes pbrt-v4 scene files and post-processes its HDR output.
import math, os, subprocess
import numpy as np

PBRT_BIN = os.environ.get("PBRT_BIN", "/tmp/claude-0/s3d/pbrt-v4/build")
OIDN_BIN = os.environ.get("OIDN_BIN", "/tmp/claude-0/s3d/oidn-2.3.3.x86_64.linux/bin")


def _f(v): return " ".join(f"{float(x):.5g}" for x in np.ravel(v))


def _i(v): return " ".join(str(int(x)) for x in np.ravel(v))


class Scene:
    """collects pbrt statements for one frame. Coordinates: right-handed, z up, metres (illustration scale)."""
    def __init__(self):
        self.head, self.world, self.textures = [], [], set()

    # ------------------------------------------------------------- camera ---
    def camera(self, eye, target, fov, size=(1920, 1080), spp=32, eye1=None, target1=None, lens=0.0, focus=100.0, maxdepth=5, up=(0, 0, 1),
               film="out.exr", integrator="path", regularize=True):
        """thin-lens perspective camera. eye1/target1 = camera at shutter close: pbrt blurs the motion between the two (true motion blur)."""
        h = self.head
        if eye1 is not None:
            h += ["TransformTimes 0 1", "ActiveTransform StartTime", f"LookAt {_f(eye)} {_f(target)} {_f(up)}",
                  "ActiveTransform EndTime", f"LookAt {_f(eye1)} {_f(target1)} {_f(up)}", "ActiveTransform All"]
        else:
            h.append(f"LookAt {_f(eye)} {_f(target)} {_f(up)}")
        # pbrt's camera space is left-handed, so its image is mirrored left-right; a 'Scale -1 1 1' would fix that but breaks an animated
        # (motion-blurred) camera transform (negative scale cannot be decomposed: blank frames), so the mirror is undone in post (load_frame).
        h.append(f'Camera "perspective" "float fov" [{fov:.4g}] "float lensradius" [{lens:.4g}] "float focaldistance" [{focus:.4g}] '
                 f'"float shutteropen" [0] "float shutterclose" [1]')
        h.append(f'Sampler "zsobol" "integer pixelsamples" [{int(spp)}]')
        h.append(f'Integrator "{integrator}" "integer maxdepth" [{int(maxdepth)}]' + (' "bool regularize" true' if regularize and integrator == "path" else ""))
        h.append(f'Film "gbuffer" "string filename" "{film}" "integer xresolution" [{size[0]}] "integer yresolution" [{size[1]}] "string sensor" "cie1931"')

    # -------------------------------------------------------------- world ---
    def sun_sky(self, sky_exr, sun_dir, sun_kelvin=4800, sun_scale=6.0, sky_scale=1.0):
        w = self.world
        w.append(f'LightSource "infinite" "string filename" "{sky_exr}" "float scale" [{sky_scale:.4g}]')
        d = np.asarray(sun_dir, float); d = d / np.linalg.norm(d)
        w.append(f'LightSource "distant" "point3 from" [{_f(d * 1000)}] "point3 to" [0 0 0] "blackbody L" [{sun_kelvin}] "float scale" [{sun_scale:.4g}]')

    def texture(self, name, path, kind="spectrum", scale=None):
        if name in self.textures: return
        self.textures.add(name)
        self.world.append(f'Texture "{name}" "{kind}" "imagemap" "string filename" "{path}"' + (f' "float scale" [{scale}]' if scale else ""))

    def material(self, kind="diffuse", rgb=(0.5, 0.5, 0.5), tex=None, roughness=None, bump=None, metal=None, eta=None, extra=""):
        """PBR material line. kind: diffuse | coateddiffuse | conductor | dielectric | interface."""
        p = []
        if kind in ("diffuse", "coateddiffuse"):
            p.append(f'"texture reflectance" "{tex}"' if tex else f'"rgb reflectance" [{_f(rgb)}]')
        if kind == "conductor":
            if metal: p.append(f'"spectrum eta" "metal-{metal}-eta" "spectrum k" "metal-{metal}-k"')
            else: p.append(f'"rgb reflectance" [{_f(rgb)}]')
        if kind == "dielectric": p.append(f'"float eta" [{eta or 1.33}]')
        if roughness is not None and kind != "diffuse": p.append(f'"float roughness" [{roughness:.4g}]')
        if bump: p.append(f'"texture displacement" "{bump}"')
        return f'Material "{kind}" ' + " ".join(p) + (" " + extra if extra else "")

    def mesh(self, P, idx, mat, N=None, uv=None, emit=None, twosided=False, alpha=None):
        """triangle mesh. emit = RGB radiance -> area light (emissive surface)."""
        w = self.world; w.append("AttributeBegin"); w.append(mat)
        if emit is not None: w.append(f'AreaLightSource "diffuse" "rgb L" [{_f(emit)}]' + (' "bool twosided" true' if twosided else ""))
        s = f'Shape "trianglemesh" "point3 P" [{_f(P)}] "integer indices" [{_i(idx)}]'
        if N is not None: s += f' "normal N" [{_f(N)}]'
        if uv is not None: s += f' "point2 uv" [{_f(uv)}]'
        if alpha is not None: s += f' "float alpha" [{alpha:.3g}]'
        w.append(s); w.append("AttributeEnd")

    def shape(self, line, mat, transform=None, emit=None, twosided=False):
        """a pbrt quadric (sphere, cylinder, disk) with its own transform list (pbrt statements like 'Translate x y z')."""
        w = self.world; w.append("AttributeBegin"); w += list(transform or []); w.append(mat)
        if emit is not None: w.append(f'AreaLightSource "diffuse" "rgb L" [{_f(emit)}]' + (' "bool twosided" true' if twosided else ""))
        w.append(line); w.append("AttributeEnd")

    def write(self, path):
        with open(path, "w") as f:
            f.write("\n".join(self.head) + "\nWorldBegin\n" + "\n".join(self.world) + "\n")


# ------------------------------------------------------------- geometry ---
def box(p0, p1, uv_scale=1.0):
    """axis-aligned box with per-face normals and uv in metres * uv_scale (for tiling textures). Returns P, idx, N, uv."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    faces = [((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), (0, 0, 1)), ((x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (0, 0, -1)),
             ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), (0, -1, 0)), ((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (0, 1, 0)),
             ((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (-1, 0, 0)), ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1), (1, 0, 0))]
    P, I, N, UV = [], [], [], []
    for a, b, c, d, n in faces:
        k = len(P); P += [a, b, c, d]; N += [n] * 4
        wu = np.linalg.norm(np.subtract(b, a)) * uv_scale; wv = np.linalg.norm(np.subtract(d, a)) * uv_scale
        UV += [(0, 0), (wu, 0), (wu, wv), (0, wv)]; I += [k, k + 1, k + 2, k, k + 2, k + 3]
    return np.array(P), np.array(I), np.array(N, float), np.array(UV)


def grid(xs, ys, zfun, uv_scale=1.0):
    """height-field surface z = zfun(X, Y) on the grid xs x ys, smooth normals. Returns P, idx, N, uv."""
    X, Y = np.meshgrid(xs, ys); Z = zfun(X, Y); ny, nx = Z.shape
    P = np.stack([X, Y, Z], -1).reshape(-1, 3)
    gy, gx = np.gradient(Z, ys, xs); N = np.stack([-gx, -gy, np.ones_like(Z)], -1); N /= np.linalg.norm(N, axis=-1, keepdims=True)
    UV = np.stack([X * uv_scale, Y * uv_scale], -1).reshape(-1, 2)
    i = np.arange(nx * ny).reshape(ny, nx); a, b, c, d = i[:-1, :-1], i[:-1, 1:], i[1:, 1:], i[1:, :-1]
    I = np.stack([a, b, c, a, c, d], -1).reshape(-1)
    return P, I, N.reshape(-1, 3), UV


def strip(xs, z_lo, z_hi, y, normal_y=-1.0, uv_scale=1.0, z_ref=0.0):
    """vertical face on the plane y between two curves z_lo(x) < z_hi(x) (a cut-away face of one layer). uv: (x, z) in metres."""
    n = len(xs); P = np.concatenate([np.stack([xs, np.full(n, y), z_lo], -1), np.stack([xs, np.full(n, y), z_hi], -1)])
    N = np.tile([0.0, normal_y, 0.0], (2 * n, 1)); UV = np.concatenate([np.stack([xs, z_lo - z_ref], -1), np.stack([xs, z_hi - z_ref], -1)]) * uv_scale
    I = []
    for k in range(n - 1):
        a, b, c, d = k, k + 1, n + k + 1, n + k
        I += [a, b, c, a, c, d] if normal_y < 0 else [a, c, b, a, d, c]
    return P, np.array(I), N, UV


def tube(a, b, r=0.15, n=10):
    """open cylinder between points a and b (for beams, vectors, edges). Returns P, idx, N."""
    a, b = np.asarray(a, float), np.asarray(b, float); ax = b - a; L = np.linalg.norm(ax); ax = ax / max(L, 1e-9)
    t = np.cross(ax, [0, 0, 1] if abs(ax[2]) < 0.9 else [1, 0, 0]); t /= np.linalg.norm(t); s = np.cross(ax, t)
    th = np.linspace(0, 2 * math.pi, n, endpoint=False); ring = np.cos(th)[:, None] * t + np.sin(th)[:, None] * s
    P = np.concatenate([a + r * ring, b + r * ring]); N = np.concatenate([ring, ring]); I = []
    for k in range(n):
        k1 = (k + 1) % n; I += [k, k1, n + k1, k, n + k1, n + k]
    return P, np.array(I), N


def merge(parts):
    """concatenate (P, idx, N[, uv]) meshes into one."""
    P, I, N, UV, off, has_uv = [], [], [], [], 0, all(len(p) > 3 for p in parts)
    for p in parts:
        P.append(p[0]); I.append(np.asarray(p[1]) + off); N.append(p[2]); off += len(p[0])
        if has_uv: UV.append(p[3])
    return (np.concatenate(P), np.concatenate(I), np.concatenate(N)) + ((np.concatenate(UV),) if has_uv else ())


# ----------------------------------------------------------------- run ---
def make_sky(out_pfm, elevation_deg=12.0, turbidity=3.0, albedo=0.4, res=1024):
    """physical sky (Hosek-Wilkie, pbrt imgtool makesky) as an equal-area octahedral map. The lower hemisphere (the map's corners, |u|+|v| > 1)
    is black in makesky's output; it is filled with the horizon colour so that no black wedge shows where the ground plane ends."""
    tmp = out_pfm + ".exr"
    subprocess.run([os.path.join(PBRT_BIN, "imgtool"), "makesky", "--elevation", str(elevation_deg), "--turbidity", str(turbidity),
                    "--albedo", str(albedo), "--resolution", str(res), "--outfile", tmp], check=True, capture_output=True)
    subprocess.run([os.path.join(PBRT_BIN, "imgtool"), "convert", "--outfile", out_pfm, tmp], check=True, capture_output=True)
    a = read_pfm(out_pfm).copy(); n = a.shape[0]; c = (np.arange(n) + 0.5) / n * 2 - 1; U, V = np.meshgrid(c, c); L = np.abs(U) + np.abs(V)
    ring = (L > 0.93) & (L < 0.99); hor = np.median(a[ring], axis=0) if ring.any() else np.full(3, 0.1, np.float32)
    a[L >= 0.99] = hor * 0.85; write_pfm(out_pfm, a); os.remove(tmp); return out_pfm


def render(scene_path, nthreads=4, log=None):
    r = subprocess.run([os.path.join(PBRT_BIN, "pbrt"), "--nthreads", str(nthreads), "--quiet", scene_path], cwd=os.path.dirname(os.path.abspath(scene_path)),
                       capture_output=True, text=True)
    if r.returncode: raise RuntimeError("pbrt failed: " + (r.stderr or r.stdout)[-800:])
    return r


def read_pfm(path):
    with open(path, "rb") as f:
        kind = f.readline().strip(); w, h = map(int, f.readline().split()); scale = float(f.readline())
        a = np.frombuffer(f.read(), "<f4" if scale < 0 else ">f4").astype(np.float32)
    c = 3 if kind == b"PF" else 1; return np.flipud(a.reshape(h, w, c))


def write_pfm(path, a):
    a = np.asarray(a, np.float32); h, w = a.shape[:2]; c = 1 if a.ndim == 2 else a.shape[2]
    with open(path, "wb") as f:
        f.write((b"PF\n" if c == 3 else b"Pf\n") + f"{w} {h}\n-1.0\n".encode()); f.write(np.flipud(a).astype("<f4").tobytes())


def exr_to_pfms(exr, stem):
    """split the gbuffer EXR into colour / albedo / normal PFMs with pbrt's imgtool."""
    tool = os.path.join(PBRT_BIN, "imgtool"); out = {}
    for key, ch in (("color", "R,G,B"), ("albedo", "Albedo.R,Albedo.G,Albedo.B"), ("normal", "N.X,N.Y,N.Z"), ("pos", "P.X,P.Y,P.Z")):
        p = f"{stem}.{key}.pfm"; subprocess.run([tool, "convert", "--channels", ch, "--outfile", p, exr], check=True, capture_output=True); out[key] = p
    return out


def load_frame(exr, stem, cleanup=True):
    """gbuffer EXR -> (denoised un-mirrored linear HDR (h, w, 3), camera distance (h, w); 0 where a ray hit nothing (sky))."""
    pf = exr_to_pfms(exr, stem); hdr = np.ascontiguousarray(np.fliplr(denoise(pf, stem + ".den.pfm")))
    dist = np.ascontiguousarray(np.fliplr(np.linalg.norm(read_pfm(pf["pos"]), axis=-1)))
    if cleanup:
        for f in list(pf.values()) + [stem + ".den.pfm"]:
            try: os.remove(f)
            except OSError: pass
    return hdr, dist


def denoise(pfms, out_pfm, threads=4):
    subprocess.run([os.path.join(OIDN_BIN, "oidnDenoise"), "--hdr", pfms["color"], "--alb", pfms["albedo"], "--nrm", pfms["normal"], "-o", out_pfm,
                    "--threads", str(threads)], check=True, capture_output=True)
    return read_pfm(out_pfm)


def finish(hdr, exposure=0.0, contrast=1.08, saturation=1.0, lift=(0.0, 0.0, 0.0), gain=(1.0, 1.0, 1.0), bloom=0.0, vignette=0.25, grain=0.0, seed=0,
           dist=None, haze=None, haze_m=900.0, wb=(1.0, 1.0, 1.0)):
    """linear HDR -> display sRGB uint8: aerial-perspective haze from the camera distance (post, not volumetric scattering), exposure, bloom of
    the brightest highlights, ACES-fitted filmic curve, lift/gain grade, vignette, grain."""
    x = np.maximum(hdr, 0.0) * (2.0 ** exposure) * np.asarray(wb, np.float32)          # white balance against the illuminant
    if dist is not None and haze is not None:
        d = np.where(dist <= 0, np.inf, dist); f = (1 - np.exp(-d / haze_m))[..., None]
        sky = (dist <= 0)[..., None]; x = np.where(sky, x, x * (1 - f) + np.asarray(haze, np.float32) * (2.0 ** exposure) * f)
    if bloom > 0:
        from PIL import Image, ImageFilter
        hi = np.clip(x - 1.0, 0, 8.0); small = Image.fromarray(np.clip(hi / 8 * 255, 0, 255).astype(np.uint8)).resize((x.shape[1] // 4, x.shape[0] // 4), Image.BILINEAR)
        b = sum(np.asarray(small.filter(ImageFilter.GaussianBlur(r)).resize((x.shape[1], x.shape[0]), Image.BILINEAR), np.float32) for r in (3, 9, 24)) / 3 / 255 * 8
        x = x + bloom * b
    a, b_, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    y = np.clip((x * (a * x + b_)) / (x * (c * x + d) + e), 0, 1)                                # ACES (Narkowicz fit)
    m = y.mean(-1, keepdims=True); y = m + (y - m) * saturation; y = 0.5 + (y - 0.5) * contrast
    y = np.clip(y, 0, 1) * np.asarray(gain) + np.asarray(lift) * (1 - y)
    if vignette > 0:
        h, w = y.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)); y *= (1 - vignette * np.clip(r - 0.35, 0, 1) ** 1.6)[..., None]
    y = np.where(y <= 0.0031308, 12.92 * y, 1.055 * np.power(np.clip(y, 0.0031308, 1), 1 / 2.4) - 0.055)
    if grain > 0: y = y + np.random.default_rng(seed).normal(0, grain, y.shape[:2])[..., None]
    return np.clip(y * 255 + 0.5, 0, 255).astype(np.uint8)


def project(p, eye, target, fov, size=(1920, 1080), up=(0, 0, 1)):
    """screen position of a world point under the same camera (for 2-D labels anchored to 3-D features). Returns (x, y, depth)."""
    eye, target = np.asarray(eye, float), np.asarray(target, float); f = target - eye; f /= np.linalg.norm(f)
    r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f); v = np.asarray(p, float) - eye
    z = v @ f; W, H = size; foc = (min(W, H) / 2) / math.tan(math.radians(fov) / 2)
    return W / 2 + foc * (v @ r) / z, H / 2 - foc * (v @ u) / z, z
