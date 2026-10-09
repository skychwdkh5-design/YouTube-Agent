"""Build scenes from plain dict/JSON specs so the same code serves any episode. Project data (images, anchors, text,
timings) lives in the spec; nothing here is geography-specific.

spec = {
  "name": "shot_a",
  "image": {"path": "..."}  |  {"synthetic": "islands"|"city", "seed": 3, "size": [4000, 2250]},
  "anchors": {"name": [x, y], ...},                # source px; strings "$key" / "$key.sub" read synthetic metadata
  "camera": {"mode": "eased"|"spline", "keys": [{"t": 0, "center": [x, y]|"anchor": "name", "height": 1600, ...}]},
  "overlays": [{"type": "draw_on_polyline", "points": "$outlines.0", "t0": 1.0, ...}, ...]
}"""
import os
import numpy as np
from functools import lru_cache
from PIL import Image
from . import layers as L, text as T, synthetic as S

COLORS = {"cyan": T.THEME.cyan, "amber": T.THEME.amber, "text": T.THEME.text, "muted": T.THEME.muted, "ink": T.THEME.ink}
OVERLAYS = {
    "draw_on_polyline": L.DrawOnPolyline, "pulse_marker": L.PulseMarker, "anchored_text": L.AnchoredText, "screen_text": L.ScreenText,
    "source_chip": L.SourceChip, "year_counter": L.YearCounter, "mask_fill": L.MaskFill, "spotlight": L.Spotlight, "brackets": L.Brackets,
}


def _ref(v, meta):
    """resolve '$a.b.0' references into metadata; other values pass through (colours by name)."""
    if isinstance(v, str) and v.startswith("$"):
        cur = meta
        for part in v[1:].split("."):
            cur = cur[int(part)] if isinstance(cur, (list, tuple, np.ndarray)) else cur[part] if isinstance(cur, dict) else getattr(cur, part)
        return cur
    if isinstance(v, str) and v in COLORS: return COLORS[v]
    if isinstance(v, list) and v and not isinstance(v[0], (list, dict)): return tuple(v) if len(v) <= 3 else v
    return v


def load_image(spec_image):
    """returns (PIL image, metadata). Raises FileNotFoundError for a missing path (surfaced by QA as a missing asset)."""
    if "path" in spec_image:
        if not os.path.exists(spec_image["path"]): raise FileNotFoundError(spec_image["path"])
        return Image.open(spec_image["path"]).convert("RGB"), {}
    return _synthetic(spec_image["synthetic"], tuple(spec_image.get("size", (4000, 2250))), spec_image.get("seed", 3))


@lru_cache(maxsize=8)
def _synthetic(kind, size, seed):
    return {"islands": S.islands, "city": S.city}[kind](size, seed)


def check_assets(spec):
    """list of missing file paths in a spec (no image loading)."""
    miss = []
    im = spec.get("image", {})
    if "path" in im and not os.path.exists(im["path"]): miss.append(im["path"])
    return miss


def scene_from_spec(spec, size=(1920, 1080)):
    img, meta = load_image(spec["image"])
    anchors = {k: np.asarray(_ref(v, meta), float) for k, v in spec.get("anchors", {}).items()}
    cam = spec["camera"]
    keys = []
    for k in cam["keys"]:
        k = dict(k)
        if "center" in k: k["center"] = np.asarray(_ref(k["center"], meta), float)
        keys.append(k)
    overlays = []
    for o in spec.get("overlays", []):
        o = dict(o); typ = o.pop("type")
        if typ not in OVERLAYS: raise ValueError(f"unknown overlay type {typ!r}; known: {sorted(OVERLAYS)}")
        kw = {}
        for k, v in o.items():
            r = _ref(v, meta)
            if k in ("p", "anchor") and isinstance(r, str) and r in anchors: r = anchors[r]
            kw[k] = r
        if typ == "mask_fill" and isinstance(kw.get("mask"), str): kw["mask"] = meta["mask"]
        overlays.append(OVERLAYS[typ](**kw))
    sc = L.Scene(img, keys, size=size, anchors=anchors, overlays=overlays, camera_mode=cam.get("mode", "eased"), name=spec.get("name", "scene"),
                 default_ease=cam.get("ease", "smoother"))
    sc.meta = meta
    return sc
