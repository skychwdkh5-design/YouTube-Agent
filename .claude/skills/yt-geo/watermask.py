#!/usr/bin/env python3
"""watermask.py - a water mask from one date of a geostack, for outlines and "lost area" fills.

    python3 watermask.py stack/y2000.png --out geo/water_y2000.png
    python3 watermask.py stack/y2000.png --out geo/water_y2000.png --max-brightness 75 --min-area-px 400

Classifies water in a natural-colour image as pixels that are dark (brightest channel below
--max-brightness) and not reddish (blue >= red - --blue-margin), removes one-pixel speckle with a
morphological opening and drops connected regions smaller than --min-area-px. Writes an 8-bit
mask (255 = water) on the same grid as the input, plus <out>.json with the method, thresholds,
pixel count and the share of the frame classified as water.

This is a display aid traced from real imagery, not a survey: the JSON says so, and anything
spoken about the area it outlines needs its own source. Prints JSON; no network.
"""
import json, os, sys
from collections import deque

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = 400_000_000


class MaskError(Exception):
    pass


def _erode(m):
    out = m.copy()
    out[1:, :] &= m[:-1, :]; out[:-1, :] &= m[1:, :]
    out[:, 1:] &= m[:, :-1]; out[:, :-1] &= m[:, 1:]
    return out


def _dilate(m):
    out = m.copy()
    out[1:, :] |= m[:-1, :]; out[:-1, :] |= m[1:, :]
    out[:, 1:] |= m[:, :-1]; out[:, :-1] |= m[:, 1:]
    return out


def drop_small(mask, min_px):
    """Keep 4-connected regions of at least min_px pixels (breadth-first labelling)."""
    h, w = mask.shape
    seen = np.zeros_like(mask)
    keep = np.zeros_like(mask)
    ys, xs = np.nonzero(mask)
    flat = mask.ravel()
    seenf = seen.ravel()
    for start in (ys * w + xs):
        if seenf[start]:
            continue
        comp, q = [], deque([start])
        seenf[start] = True
        while q:
            p = q.popleft()
            comp.append(p)
            y, x = divmod(p, w)
            for n in ((p - w) if y else -1, (p + w) if y < h - 1 else -1,
                      (p - 1) if x else -1, (p + 1) if x < w - 1 else -1):
                if n >= 0 and flat[n] and not seenf[n]:
                    seenf[n] = True
                    q.append(n)
        if len(comp) >= min_px:
            keep.ravel()[comp] = True
    return keep


def water_mask(rgb, max_brightness=75, blue_margin=5, min_area_px=400):
    a = rgb.astype(np.int16)
    m = (a.max(axis=2) < max_brightness) & (a[..., 2] >= a[..., 0] - blue_margin)
    m = _dilate(_erode(m))                 # opening: removes isolated dark pixels
    return drop_small(m, min_area_px)


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or "-h" in a or "--help" in a:
        print(__doc__); return 0
    try:
        def flag(name, default, kind):
            if name not in a: return default
            i = a.index(name)
            try:
                return kind(a[i + 1])
            except (IndexError, ValueError):
                raise MaskError(f"{name} needs a {kind.__name__}")
        out = flag("--out", None, str)
        mb, bm, mn = flag("--max-brightness", 75, int), flag("--blue-margin", 5, int), flag("--min-area-px", 400, int)
        if not (1 <= mb <= 255 and 0 <= bm <= 255 and 1 <= mn <= 10_000_000):
            raise MaskError("thresholds out of range")
        valued = {"--out", "--max-brightness", "--blue-margin", "--min-area-px"}
        files = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in valued)]
        if len(files) != 1 or not out:
            raise MaskError("give one input image and --out")
        if not os.path.isfile(files[0]):
            raise MaskError(f"not found: {files[0]}")
        if not out.lower().endswith(".png"):
            raise MaskError("--out must be a .png")
        rgb = np.asarray(Image.open(files[0]).convert("RGB"))
        m = water_mask(rgb, mb, bm, mn)
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        Image.fromarray((m * 255).astype(np.uint8), "L").save(out)
        meta = {"schema": "yt-geo-watermask/1", "source": files[0], "mask": out, "size": [rgb.shape[1], rgb.shape[0]],
                "method": "dark & non-red pixels, 3x3 cross opening, connected regions >= min_area_px",
                "params": {"max_brightness": mb, "blue_margin": bm, "min_area_px": mn},
                "water_pixels": int(m.sum()), "water_fraction": round(float(m.mean()), 5),
                "note": "display aid traced from imagery; not a survey measurement"}
        with open(out[:-4] + ".json", "w") as f:
            json.dump(meta, f, indent=1)
        print(json.dumps(dict(meta, status="ok"), indent=1)); return 0
    except MaskError as e:
        print(json.dumps({"status": "error", "error": str(e)}, indent=1)); return 2
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"unexpected {type(e).__name__}: {e}"}, indent=1)); return 2


if __name__ == "__main__":
    sys.exit(main())
