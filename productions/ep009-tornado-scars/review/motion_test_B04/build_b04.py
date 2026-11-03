#!/usr/bin/env python3
"""EP009 B04 motion test: the same 5 s of the pilot (12.0-17.0 s) rendered twice.

  before  - pilot_keyframes.json B04 taken literally, rendered the way V7 renders props
            (centre-scaled cutouts, V7 smoothstep between keys, fixed-offset drop shadow,
            crossfade between the intact and the uprooted painting).
  after   - b04_improved_keyframes.json: named curves from tools/motion/easing.py, pivot
            topple with physical 'topple' curve, 2.5D wind bend with crown lag, projected ground
            shadow, depth-of-field background, parallax camera, impact handoff with motion blur,
            dust and shake.

Usage (from the repository root, after productions/ep009-tornado-scars/tools/verify_illustrated_assets.py):
  python3 productions/ep009-tornado-scars/review/motion_test_B04/build_b04.py [before|after|all] [--still T ...]
Outputs go to the review folder; MP4s are git-ignored by repository policy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools" / "motion"))
import compositor as C  # noqa: E402
import easing as E  # noqa: E402

W, H, FPS = 1920, 1080, 30
M01 = EP / "media_original" / "nasa_tuscaloosa_EO1_20110502.jpg"
M01_SHA = "44b95e31d1392f74eb4c62fabe984871809e7e167ec02b30a61b059d3760f21a"
ASSETS = EP / "handoff" / "assets"
SPEC = json.loads((HERE / "b04_improved_keyframes.json").read_text())
PILOT = next(s for s in json.loads((EP / "handoff" / "pilot_keyframes.json").read_text())["scenes"] if s["id"] == "B04")
T0, T1 = SPEC["window_s"]


def load_inputs():
    if hashlib.sha256(M01.read_bytes()).hexdigest() != M01_SHA:
        sys.exit("M01 SHA256 mismatch - do not render")
    expected = {a["name"]: a["sha256"] for a in json.loads((EP / "handoff" / "assets.json").read_text())["generated_assets"]}
    out = {}
    for name in ("P03_tree_intact.png", "P03_tree_uprooted.png"):
        p = ASSETS / name
        if not p.exists():
            sys.exit(f"{p} missing: run productions/ep009-tornado-scars/tools/verify_illustrated_assets.py first")
        if hashlib.sha256(p.read_bytes()).hexdigest() != expected[name]:
            sys.exit(f"{name} SHA256 mismatch - do not render")
        out[name] = p
    return out


Image.MAX_IMAGE_PIXELS = 40_000_000
PATHS = load_inputs()
SOURCE = Image.open(M01).convert("RGB")
CAM = C.Camera(SOURCE, (W, H))
RAW = {n: Image.open(p).convert("RGBA") for n, p in PATHS.items()}            # V7 used raw cutouts
CLEAN = {n: C.clean_alpha(im) for n, im in RAW.items()}                       # matte noise removed


# --- shared finish (same on both versions, so only the motion differs) --------------------------

def finish(im: Image.Image, label_alpha: float = 1.0) -> Image.Image:
    ov = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(ov)
    for y in range(120):                                   # V7 top/bottom grade bars
        a = int(145 * (1 - y / 120) ** 2)
        d.line((0, y, W, y), fill=(7, 20, 29, a))
        d.line((0, H - y, W, H - y), fill=(7, 20, 29, a + 25))
    f = C.font
    d.text((42, 30), "ORBITAL ATLAS", font=f(19), fill="#F4EDD8")
    lab = SPEC["labels"]["illustration"]
    tw = d.textbbox((0, 0), lab, font=f(19))[2]
    d.text((W - 42 - tw, 31), lab, font=f(19), fill=(244, 237, 216, int(255 * label_alpha)))
    d.text((42, H - 38), SPEC["labels"]["credit"], font=f(16), fill="#E3E9E2")
    return Image.alpha_composite(im, ov)


# --- BEFORE: literal pilot keyframes, V7 rendering model -----------------------------------------

def render_before(t: float, log: C.FrameLog | None = None) -> Image.Image:
    cam = SPEC["camera"]["keys"][0]
    frame, _ = CAM.frame(cam["cx"], cam["cy"], cam["width"])
    state = {}
    for layer in PILOT["layers"]:
        ks = layer["keyframes"]
        op = E.interpolate(ks, t, "opacity")            # no easing in pilot file -> V7 smoothstep
        pos = E.interpolate(ks, t, "position")
        sc = E.interpolate(ks, t, "scale")
        rot = E.interpolate(ks, t, "rotation")
        state[layer["asset"]] = (op, rot, pos)
        if op <= 0.001:
            continue
        p = C.place_centered_v7(RAW[layer["asset"]], (pos[0] * W, pos[1] * H), sc * H, rot, op)
        C.drop_shadow_v7(frame, p)
        frame.alpha_composite(p.image, p.xy)
    if log is not None:
        i = state["P03_tree_intact.png"]
        u = state["P03_tree_uprooted.png"]
        log.add(t=t, intact_opacity=i[0], intact_angle=i[1], intact_x=i[2][0] * W, intact_y=i[2][1] * H,
                uprooted_opacity=u[0], uprooted_angle=u[1])
    return finish(frame)


# --- AFTER: named curves, pivot physics, depth --------------------------------------------------

TI, TU = SPEC["tree_intact"], SPEC["tree_uprooted"]
IMPACT, HAND = SPEC["handoff"]["start_s"], SPEC["handoff"]["dur_s"]
DUSTS = [C.Dust(tuple(d["origin_screen"]), d["at"], tuple(d["color"]), d["n"], d["seed"], d["spread"], alpha=d["alpha"])
         for d in SPEC["dust"]]
CAM0 = SPEC["camera"]["keys"][0]


def tree_layer(img, spec, height, angle, at, opacity, blur, bend_kw):
    s = C.resize_to_height(img, height)
    pv = (spec["pivot_in_asset"][0] * s.width, spec["pivot_in_asset"][1] * s.height)
    if bend_kw:
        s = C.bend(s, base_y=pv[1], **bend_kw)
        pv = (pv[0] + s.info.get("bend_pad", 0), pv[1])
    return C.place(s, pv, at, angle, opacity, blur), s.width


def render_after_raw(t: float, log: C.FrameLog | None = None) -> Image.Image:
    ck = SPEC["camera"]["keys"]
    cx, cy, cw = (E.interpolate(ck, t, k) for k in ("cx", "cy", "width"))
    sh = SPEC["shake"]
    sx, sy = C.shake(t, sh["at"], sh["amp_px"], sh["freq_hz"], sh["decay"])
    bd = SPEC["background_depth"]["keys"]
    frame, scale = CAM.frame(cx - sx / (W / cw), cy - sy / (W / cw), cw, E.interpolate(bd, t, "blur"))
    dim = E.interpolate(bd, t, "dim")
    if dim > 0.001:                                     # recede the background, most around the subject
        yy, xx = np.mgrid[0:H:4, 0:W:4]
        m = dim * (0.55 + 0.45 * np.exp(-(((xx - 650) / 700.0) ** 2 + ((yy - 720) / 520.0) ** 2)))
        m = Image.fromarray((m * 255).astype(np.uint8)).resize((W, H), Image.Resampling.BILINEAR)
        tint = Image.new("RGBA", (W, H), (8, 20, 28, 0))
        tint.putalpha(m)
        frame.alpha_composite(tint)
    shift = ((cx - CAM0["cx"]) * scale, (cy - CAM0["cy"]) * scale)
    zrel = CAM0["width"] / cw

    def anchor(a, depth):
        x, y = C.parallax(tuple(a), shift, zrel, depth)
        return x + sx * (depth - 1), y + sy * (depth - 1)   # near layers shake a bit more

    row = {"t": t}
    # intact tree: entry, wind bend, anticipation + topple about the root-plate pivot
    if t < IMPACT + HAND:
        en = TI["entry"]
        rise, sc, bl, op = (E.interpolate(en, t, k) for k in ("rise", "scale", "blur", "opacity"))
        hand = 1.0 if t < IMPACT else 1 - E.segment(t, IMPACT, IMPACT + HAND, SPEC["handoff"]["easing"])
        ang = E.interpolate(TI["angle"], t, "a")
        amp, lean = E.interpolate(TI["wind"], t, "amp"), E.interpolate(TI["wind"], t, "lean")
        wp = TI["wind_px"]
        z = 1 + (zrel - 1) * TI["depth"]
        bend_kw = dict(amount_px=amp * wp["gust_amp"] * z, lean_px=lean * wp["lean"] * z,
                       phase=2 * math.pi * wp["freq_hz"] * t, lag=wp["crown_lag_rad"])
        ax, ay = anchor(TI["anchor_screen"], TI["depth"])
        p, sw = tree_layer(CLEAN["P03_tree_intact.png"], TI, TI["height_px"] * sc * z, ang,
                           (ax, ay + rise), op * hand, bl + 3.0 * (1 - hand), bend_kw)   # blur masks the dissolve
        if op * hand > 0.01:
            cwid = sw * 0.42
            C.ground_shadow(frame, p, ay, strength=0.55 * op * hand, blur=8,
                            contact=(ax - 0.13 * sw * math.cos(math.radians(ang)), cwid, 0.55 * op * hand * max(0, math.cos(math.radians(ang * 1.6)))))
            frame.alpha_composite(p.image, p.xy)
        row.update(intact_opacity=op * hand, intact_angle=ang, intact_rise=rise, bend_amp=bend_kw["amount_px"],
                   bend_lean=bend_kw["lean_px"], anchor_x=ax, anchor_y=ay)
    # uprooted tree: appears inside the impact, settles with a spring
    if t >= IMPACT:
        q = E.segment(t, IMPACT, IMPACT + HAND, SPEC["handoff"]["easing"])
        a = E.interpolate(TU["settle"], t, "a")
        dy = E.interpolate(TU["settle"], t, "dy")
        aw = TU["after_wind_px"]
        z = 1 + (zrel - 1) * TU["depth"]
        ax, ay = anchor(TU["anchor_screen"], TU["depth"])
        bend_kw = dict(amount_px=aw["gust_amp"] * z, phase=2 * math.pi * aw["freq_hz"] * t, lag=aw["crown_lag_rad"])
        p, sw = tree_layer(CLEAN["P03_tree_uprooted.png"], TU, TU["height_px"] * z, a, (ax, ay + dy), q,
                           3.0 * (1 - q), bend_kw)
        C.ground_shadow(frame, p, ay, lean=0.6, strength=0.45 * q, blur=9, contact=(ax + 0.12 * sw, sw * 0.7, 0.55 * q))
        frame.alpha_composite(p.image, p.xy)
        row.update(uprooted_opacity=q, uprooted_angle=a, uprooted_dy=dy)
    for dust in DUSTS:
        dust.draw(frame, t)
    lab = E.segment(t, 12.2, 12.9, "enter")
    if log is not None:
        row.update(cam_cx=cx, cam_width=cw, shake_x=sx, bg_blur=E.interpolate(bd, t, "blur"), bg_dim=dim)
        log.add(**row)
    return finish(frame, lab)


def render_after(t: float, log: C.FrameLog | None = None) -> Image.Image:
    mb = SPEC["motion_blur"]
    if mb["from"] <= t <= mb["to"]:
        im = C.supersample(lambda u: render_after_raw(u).convert("RGB"), t, FPS, mb["samples"], mb["shutter"])
        render_after_raw(t, log)                         # log the centre-of-shutter values
        return im.convert("RGBA")
    return render_after_raw(t, log)


VERSIONS = {"before": render_before, "after": render_after}


def build(which: str):
    fn = VERSIONS[which]
    log = C.FrameLog()
    n = int(round((T1 - T0) * FPS))
    frames = (fn(T0 + i / FPS, log) for i in range(n))
    out = HERE / f"B04_{which}_5s.mp4"
    C.encode(frames, out, (W, H), FPS)
    log.write(HERE / f"B04_{which}_framelog.json")
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("which", nargs="?", default="all", choices=["before", "after", "all"])
    ap.add_argument("--still", type=float, nargs="*", help="render stills at these pilot times instead of video")
    a = ap.parse_args()
    todo = ["before", "after"] if a.which == "all" else [a.which]
    for w in todo:
        if a.still:
            for t in a.still:
                VERSIONS[w](t).convert("RGB").save(HERE / f"_still_{w}_{t:05.2f}.jpg", quality=90)
        else:
            build(w)
