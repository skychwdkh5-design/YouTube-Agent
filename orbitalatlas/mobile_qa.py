"""MOBILE_READABILITY_QA - can a viewer read every on-screen text and see every line on a 6.1-inch phone?

    python3 -m orbitalatlas.mobile_qa SLUG [--fps 1] [--start S --end E] [--out FILE.json]

Builds the director programme of a production, renders sampled frames (default 1 per second) with the text recorder on
(orbitalatlas.textrec: every string's font size, box, colour, alpha and the overlay class that drew it) and checks:
  text_size       informational text >= MIN_TEXT_PX at 1080p (6.1-inch phone: portrait inline 390x219 pt, landscape full screen 699x393 pt)
  caption_size    captions >= MIN_CAPTION_PX
  safe_area       every text box inside the title-safe frame (3.5 % x, 4 % y)
  caption_overlap no text box intersects a caption box at the same moment
  text_overlap    no two texts of different overlays intersect
  contrast        text colour vs the median of the box's other pixels on the rendered frame >= MIN_CONTRAST (WCAG ratio)
  line_width      traced outlines (RegionTint thin) measured on a synthetic edge >= MIN_LINE_PX at 1080p, with a dark under-stroke
Checks that need a person (taste, real-device viewing, pronunciation) are listed under `human_checks`, never passed automatically.
Prints/writes JSON with every issue (first time, count, text) and a per-style size table in phone points.
"""
# effect-reuse-checked: QA only; reuses director.build, Program.render, fx.RegionTint and the existing overlay registry conventions
import argparse, json, os, sys
from collections import defaultdict

import numpy as np
from PIL import Image

from . import fx, textrec

PHONE = dict(portrait_pt=219.0, landscape_pt=393.0)          # 6.1-inch phone: video height in points, inline portrait / full-screen landscape
MIN_TEXT_PX, MIN_CAPTION_PX, MIN_LINE_PX, MIN_CONTRAST = 30.0, 48.0, 4.5, 3.0
SAFE_X, SAFE_Y = 0.035, 0.04
CAPTION_TAGS = ("WordCaptions",)
HUMAN_CHECKS = ["watch on a real 6.1-inch phone in portrait and in landscape (sizes here are computed, not seen)",
                "taste: is any overlay distracting, is the hierarchy clear", "pronunciation of names and acronyms (no ASR here)"]


def pt(px, H=1080.0):
    return dict(portrait=round(px / H * PHONE["portrait_pt"], 1), landscape=round(px / H * PHONE["landscape_pt"], 1))


def lum(c):
    c = np.asarray(c, np.float32) / 255.0; c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]) if c.ndim == 1 else 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def contrast(frame, box, color):
    """WCAG ratio between the text colour and the median of the NON-text pixels in the box grown by 6 px (outline, scrim and the ground
    around the glyphs count as background). None when the text is not visible in the final frame (covered by a later layer)."""
    W, H = frame.size; x0, y0, x1, y1 = [int(round(v)) for v in box]
    g = 6; X0, Y0, X1, Y1 = max(0, x0 - g), max(0, y0 - g), min(W, x1 + g), min(H, y1 + g)
    if X1 - X0 < 4 or Y1 - Y0 < 4: return None
    a = np.asarray(frame.crop((X0, Y0, X1, Y1)), np.float32).reshape(-1, 3); dist = np.abs(a - np.asarray(color, np.float32)).sum(1)
    if (dist < 30).mean() < 0.01: return None
    bg = a[dist >= 30]
    if len(bg) < 10: return None
    lt, lb = lum(color), float(np.median(lum(bg)))
    return round((max(lt, lb) + 0.05) / (min(lt, lb) + 0.05), 2)


def outline_width_px(size=(1920, 1080)):
    """width (px, alpha >= 50 % of peak) of a thin RegionTint line drawn on a straight synthetic edge at this render size"""
    from . import layers as L, text as T
    from .camera import View
    W, H = size; m = np.zeros((H, W), np.uint8); m[:, : W // 2] = 255
    v = View((W / 2, H / 2), H, 0, size); c = L.Ctx(size, v, 5.0, T.THEME, T.Registry())
    fx.RegionTint(Image.fromarray(m), 0.0, settle_alpha=0.0, flash_peak=0.0, thin=True, glint=False, dur=0.5).draw(c)
    a = np.asarray(c.fills, np.float32)[H // 2]; rgb_amber = a[:, :3].mean(1) * (a[:, 3] / 255.0)
    prof = a[:, 3] * (a[:, 0] > 120)                                      # the coloured line, not its dark under-stroke
    return float((prof >= 0.5 * prof.max()).sum()) if prof.max() > 0 else 0.0


def _wrap_overlays(obj, seen, depth=0):
    if depth > 6 or id(obj) in seen: return
    seen.add(id(obj))
    ovs = getattr(obj, "overlays", None)
    if isinstance(ovs, list):
        for o in ovs: _tag(o)
    for k, v in list(getattr(obj, "__dict__", {}).items()):
        if hasattr(v, "__dict__") and type(v).__module__.startswith("orbitalatlas"): _wrap_overlays(v, seen, depth + 1)
        elif isinstance(v, (list, tuple)):
            for x in v:
                if hasattr(x, "__dict__") and type(x).__module__.startswith("orbitalatlas"): _wrap_overlays(x, seen, depth + 1)


def _tag(o):
    if getattr(o, "_mqa", False): return
    f = o.draw
    def draw(ctx, _f=f, _n=type(o).__name__):
        prev = textrec.STATE["tag"]; textrec.STATE["tag"] = _n
        try: return _f(ctx)
        finally: textrec.STATE["tag"] = prev
    o.draw = draw; o._mqa = True


def inter(a, b, tol=2.0):
    return min(a[2], b[2]) - max(a[0], b[0]) > tol and min(a[3], b[3]) - max(a[1], b[1]) > tol


def check_records(recs, frame, size, t, issues):
    W, H = size; k = H / 1080.0; caps = [r for r in recs if r["tag"] in CAPTION_TAGS]
    for r in recs:
        cap = r["tag"] in CAPTION_TAGS; px = r["px"] / k; b = r["box"]
        if cap and px < MIN_CAPTION_PX: issues["caption_size"].append((t, r, f"{px:.0f}px < {MIN_CAPTION_PX:.0f}"))
        if not cap and px < MIN_TEXT_PX: issues["text_size"].append((t, r, f"{px:.0f}px < {MIN_TEXT_PX:.0f} ({pt(px)['portrait']} pt portrait)"))
        if b[0] < SAFE_X * W - 1 or b[1] < SAFE_Y * H - 1 or b[2] > W * (1 - SAFE_X) + 1 or b[3] > H * (1 - SAFE_Y) + 1:
            issues["safe_area"].append((t, r, "box " + ",".join(f"{v:.0f}" for v in b)))
        if not cap and any(inter(b, c["box"]) for c in caps): issues["caption_overlap"].append((t, r, "intersects a caption"))
        if not cap and any(o is not r and o["tag"] != r["tag"] and o["tag"] not in CAPTION_TAGS and inter(b, o["box"], 4.0) for o in recs):
            issues["text_overlap"].append((t, r, "intersects " + ", ".join(sorted({o["tag"] or "?" for o in recs if o is not r and o["tag"] != r["tag"] and o["tag"] not in CAPTION_TAGS and inter(b, o["box"], 4.0)}))))
        if frame is not None:
            c = contrast(frame, b, r["color"])
            if c is not None and c < MIN_CONTRAST: issues["contrast"].append((t, r, f"{c}:1"))


def run(prod, fps=1.0, t_range=None, size=(1920, 1080), log=print):
    from . import director
    prog, rep = director.build(prod, size, t_range=t_range, log=lambda m: None)
    _wrap_overlays(prog, set())
    issues = defaultdict(list); styles = defaultdict(lambda: dict(min_px=1e9, n=0)); n = 0
    t0 = 0.0; t1 = prog.duration; ts = np.arange(t0 + 0.5, t1, 1.0 / fps)
    for t in ts:
        textrec.STATE["rec"] = recs = []
        try: frame = prog.render(float(t))
        finally: textrec.STATE["rec"] = None
        check_records(recs, frame, size, round(float(t) + prog.t_offset, 2), issues); n += 1
        for r in recs:
            s = styles[r["tag"] or "?"]; s["min_px"] = min(s["min_px"], r["px"] * 1080 / size[1]); s["n"] += 1
    lw = outline_width_px(size) * 1080 / size[1]
    thin = [o for o in _all_overlays(prog) if isinstance(o, fx.RegionTint) and getattr(o, "thin", False)]
    line = dict(width_px_1080=round(lw, 1), phone_pt=pt(lw), min_px=MIN_LINE_PX, outlines_in_programme=len(thin), ok=(lw >= MIN_LINE_PX or not thin))
    out = dict(schema="orbitalatlas-mobile-qa/1", device="6.1-inch phone", rules=dict(min_text_px=MIN_TEXT_PX, min_caption_px=MIN_CAPTION_PX, min_line_px=MIN_LINE_PX,
               min_contrast=MIN_CONTRAST, safe_area=[SAFE_X, SAFE_Y]), frames_checked=n, fps=fps, line=line,
               styles={k: dict(min_px=round(v["min_px"], 1), phone_pt=pt(v["min_px"]), draws=v["n"]) for k, v in sorted(styles.items())},
               issues={}, human_checks=HUMAN_CHECKS)
    for kind, lst in issues.items():
        agg = {}
        for t, r, why in lst:
            key = (r["tag"], r["text"][:40])
            if key not in agg: agg[key] = dict(tag=r["tag"], text=r["text"][:60], first_t=t, last_t=t, count=0, why=why)
            agg[key]["last_t"] = t; agg[key]["count"] += 1
        out["issues"][kind] = sorted(agg.values(), key=lambda x: x["first_t"])
    out["ok"] = not any(out["issues"].values()) and line["ok"]
    out["summary"] = {k: len(v) for k, v in out["issues"].items()}
    return out


def _all_overlays(prog):
    found, seen = [], set()
    def walk(obj, d=0):
        if d > 6 or id(obj) in seen: return
        seen.add(id(obj)); ovs = getattr(obj, "overlays", None)
        if isinstance(ovs, list): found.extend(ovs)
        for v in getattr(obj, "__dict__", {}).values():
            if hasattr(v, "__dict__") and type(v).__module__.startswith("orbitalatlas"): walk(v, d + 1)
            elif isinstance(v, (list, tuple)):
                for x in v:
                    if hasattr(x, "__dict__") and type(x).__module__.startswith("orbitalatlas"): walk(x, d + 1)
    walk(prog); return found


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("slug"); ap.add_argument("--fps", type=float, default=1.0)
    ap.add_argument("--start", type=float); ap.add_argument("--end", type=float); ap.add_argument("--out")
    a = ap.parse_args(argv); root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prod = a.slug if os.path.isdir(a.slug) else os.path.join(root, "productions", a.slug)
    res = run(prod, a.fps, (a.start, a.end) if a.start is not None else None)
    s = json.dumps(res, indent=1, ensure_ascii=False)
    if a.out: open(a.out, "w").write(s)
    print(s if not a.out else json.dumps(dict(ok=res["ok"], summary=res["summary"], line=res["line"], out=a.out), indent=1))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
