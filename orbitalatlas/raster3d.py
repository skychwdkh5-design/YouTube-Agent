"""raster3d - real-time-style RASTER backend for the same true-3-D scenes that orbitalatlas.pbrt3d path-traces.

One scene description, two renderers: pbrt3d.Scene records every mesh / tessellated quadric / material / texture / camera / sun as data;
this module exports a frame as a compact binary bundle and tools/raster3d/render.js draws it with three.js (WebGL2) in headless Chromium
(SwiftShader software GL - no GPU needed): real triangle geometry, perspective camera with lens shift, sun with shadow maps, image-based
light from the same physical sky, PBR (metal/roughness) materials with the same textures, emissive geometry, depth fog, ACES tone map.
Not included (stays with pbrt): global illumination bounces, soft area-light shadows, depth of field, motion blur.
Used for the DRAFT preset (geometry, camera, light direction, composition in minutes instead of an hour).
"""
# effect-reuse-checked: pbrt3d path-traces (minutes per frame); scene3d is a 2.5-D painter without a z-buffer or shadows; tools/cesium_proof
# renders a globe from tiles. Nothing rasterises arbitrary scene meshes with shadows; this reuses the cesium_proof Chromium/SwiftShader setup.
import json, math, os, subprocess
import numpy as np
from . import pbrt3d as P

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RUNNER = os.path.join(ROOT, "tools", "raster3d", "render.js")


def _key(o):
    m = o["mat"]; return json.dumps([m.get("kind"), [round(x, 4) for x in m.get("rgb", [])], m.get("tex"), m.get("roughness"), m.get("metal"),
                                     None if o["emit"] is None else [round(x, 4) for x in o["emit"]]])


def _flat_normals(Pp, idx):
    N = np.zeros_like(Pp); tri = idx.reshape(-1, 3); n = np.cross(Pp[tri[:, 1]] - Pp[tri[:, 0]], Pp[tri[:, 2]] - Pp[tri[:, 0]])
    for k in range(3): np.add.at(N, tri[:, k], n)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def group(objects):
    """merge objects that share a material + emission into one draw (fewer draw calls)."""
    groups = {}
    for o in objects:
        g = groups.setdefault(_key(o), dict(mat=o["mat"], emit=o["emit"], P=[], N=[], uv=[], idx=[], n=0))
        Pp = o["P"]; N = o["N"] if o["N"] is not None else _flat_normals(Pp, o["idx"]).astype(np.float32)
        uv = o["uv"] if o["uv"] is not None else np.zeros((len(Pp), 2), np.float32)
        g["P"].append(Pp); g["N"].append(N); g["uv"].append(uv); g["idx"].append(o["idx"] + g["n"]); g["n"] += len(Pp)
    return [dict(mat=g["mat"], emit=g["emit"], P=np.concatenate(g["P"]).astype(np.float32), N=np.concatenate(g["N"]).astype(np.float32),
                 uv=np.concatenate(g["uv"]).astype(np.float32), idx=np.concatenate(g["idx"]).astype(np.uint32)) for g in groups.values()]


def _write_bundle(groups, bin_path):
    """one binary file (float32 P/N/uv + uint32 indices back to back) + the per-group layout."""
    layout, off = [], 0
    with open(bin_path, "wb") as f:
        for g in groups:
            ent = dict(mat=g["mat"], emit=g["emit"])
            for k in ("P", "N", "uv", "idx"):
                b = g[k].tobytes(); f.write(b); ent[k] = [off, len(b)]; off += len(b)
            layout.append(ent)
    return layout


def save_objects(path_npz, objects):
    """static geometry bundle (written once, loaded once per render session)."""
    gs = group(objects); bin_path = path_npz[:-4] + ".bin"; layout = _write_bundle(gs, bin_path)
    json.dump(dict(bin=os.path.basename(bin_path), groups=layout), open(path_npz[:-4] + ".json", "w")); open(path_npz, "wb").write(b"see .json/.bin")
    return path_npz


def export_frame(scene, out_stem, size):
    """write <out_stem>.json + .bin for one frame of a pbrt3d.Scene (dynamic objects; static bundles referenced by path)."""
    gs = group(scene.objects); layout = _write_bundle(gs, out_stem + ".bin")
    doc = dict(cam=dict(scene.cam, size=list(size)), sun=scene.sun, textures=scene.texpaths, groups=layout, bin=os.path.basename(out_stem + ".bin"),
               static=[p[:-4] + ".json" for p in scene.static_bundles])
    json.dump(doc, open(out_stem + ".json", "w")); return out_stem + ".json"


# ---------------------------------------------------------------- sky ---
def _equal_area_square_to_sphere(u, v):
    """pbrt-v4 EqualAreaSquareToSphere (Clarberg): [0,1]^2 -> unit sphere, z up."""
    u = 2 * u - 1; v = 2 * v - 1; up, vp = np.abs(u), np.abs(v)
    sd = 1 - (up + vp); d = np.abs(sd); r = 1 - d
    phi = np.where(r == 0, 1.0, (vp - up) / np.where(r == 0, 1, r) + 1) * math.pi / 4
    z = np.copysign(1 - r * r, sd); cphi = np.copysign(np.cos(phi), u); sphi = np.copysign(np.sin(phi), v)
    s = r * np.sqrt(np.maximum(2 - r * r, 0)); return np.stack([cphi * s, sphi * s, z], -1)


def sky_equirect(sky_pfm, out_f32, w=512, h=256, wb=(1.0, 1.0, 1.0)):
    """resample pbrt's equal-area octahedral sky (z up) into an equirectangular float32 RGBA map in three.js's convention (y up:
    u = atan2(dir.z, dir.x)/2pi + 0.5, v = asin(dir.y)/pi + 0.5, row 0 = v 0 = nadir). World z-up (x, y, z) is three's (x, z, -y)."""
    oct_ = P.read_pfm(sky_pfm); n = oct_.shape[0]
    c = (np.arange(n) + 0.5) / n; U, Vv = np.meshgrid(c, c); d = _equal_area_square_to_sphere(U, 1 - Vv)       # image row 0 = top (v = 1)
    tx, ty, tz = d[..., 0], d[..., 2], -d[..., 1]                                                                 # to three's y-up frame
    u = np.arctan2(tz, tx) / (2 * math.pi) + 0.5; v = np.arcsin(np.clip(ty, -1, 1)) / math.pi + 0.5
    xx = np.clip((u * w).astype(int), 0, w - 1); yy = np.clip((v * h).astype(int), 0, h - 1)
    acc = np.zeros((h, w, 3)); cnt = np.zeros((h, w, 1)); np.add.at(acc, (yy, xx), oct_); np.add.at(cnt, (yy, xx), 1)
    eq = acc / np.maximum(cnt, 1) * np.asarray(wb)                                     # same white balance as the path-traced grade
    for _ in range(8):                                                   # fill empty texels from neighbours
        empty = cnt[..., 0] == 0
        if not empty.any(): break
        k = (np.roll(cnt, 1, 0) + np.roll(cnt, -1, 0) + np.roll(cnt, 1, 1) + np.roll(cnt, -1, 1))
        nb = (np.roll(eq * cnt, 1, 0) + np.roll(eq * cnt, -1, 0) + np.roll(eq * cnt, 1, 1) + np.roll(eq * cnt, -1, 1)) / np.maximum(k, 1)
        eq[empty] = nb[empty]; cnt[empty] = (k[empty] > 0)
    rgba = np.concatenate([eq, np.ones((h, w, 1))], -1).astype(np.float32); rgba.tofile(out_f32)
    json.dump(dict(w=w, h=h), open(out_f32 + ".json", "w")); return out_f32


def render(frame_jsons, out_dir, size, sky_f32, workdir, shadow=2048, timeout=3600, exposure=0.8, env=1.0, wb=(1.0, 1.0, 1.0), fog=1 / 5000,
           haze=(0.46, 0.44, 0.46), fmt="jpeg", sun=3.0, aa=False, bg=1.0, pcfsoft=True):
    """rasterise a list of exported frames in one Chromium session; images to out_dir. Returns the runner's timing report."""
    os.makedirs(out_dir, exist_ok=True); job = os.path.join(out_dir, "job.json")
    json.dump(dict(frames=frame_jsons, out=out_dir, size=list(size), sky=sky_f32, root=workdir, shadow=shadow, exposure=exposure, env=env, wb=list(wb),
                   fog=fog, haze=list(haze), fmt=fmt, sun=sun, aa=aa, bg=bg, pcfsoft=pcfsoft), open(job, "w"))
    r = subprocess.run(["node", RUNNER, job], capture_output=True, text=True, timeout=timeout)
    if r.returncode: raise RuntimeError("raster3d failed: " + (r.stderr or r.stdout)[-1500:])
    return json.loads(r.stdout.strip().splitlines()[-1])
