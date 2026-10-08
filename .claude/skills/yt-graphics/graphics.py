#!/usr/bin/env python3
"""graphics.py - original 16:9 documentary graphics (1920x1080 PNG) from a JSON spec.

    python3 graphics.py spec.json --out-dir graphics/            # validate + render every graphic
    python3 graphics.py spec.json --out-dir graphics/ --only bars # one graphic

Types: diagram, flow, circulation, water_cycle (scientific schematics); geo, compare (annotated
Landsat imagery with a scale bar computed from the yt-geo grid); bar, line, callout (data).

Rules: every graphic names its source; chart data must be finite numbers with explicit units; a
geographic scale bar needs the grid's projection and pixel size - it is never guessed; text that
does not fit, or leaves the landscape safe area, is an error rather than silently clipped.
Output is deterministic (same spec and inputs -> same bytes). Prints JSON; exit 0 ok, 2 error.
Pillow + NumPy only. No network.
"""
import hashlib, json, math, os, re, subprocess, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
SS = 2                                   # supersampling: draw at 2x, downsample once (smooth lines)
SAFE = {"top": 0.07, "bottom": 0.13, "left": 0.05, "right": 0.05}   # same as yt-render profile "long"
CAPTION_TOP = 0.74                       # burned-in captions of profile "long" sit below this line
CREDIT_BAND = 44                         # yt-render draws the shot credit just inside the top safe edge
MAX_STEPS = 20                           # build steps per graphic
MIN_TEXT_PX = 24                         # smallest text at 1080p: ~10.5 pt on a phone in landscape fullscreen
STYLES = {
    "documentary_dark": {"bg": (12, 18, 28), "panel": (26, 36, 52), "fg": (240, 244, 248), "muted": (150, 166, 186),
                         "grid": (48, 62, 82), "accent": (255, 210, 63), "accent2": (255, 122, 40),
                         "blue": (72, 160, 255), "green": (92, 200, 122), "red": (236, 84, 72),
                         "sea": (28, 74, 120), "land": (150, 118, 76), "cloud": (225, 232, 240)},
    "documentary_light": {"bg": (246, 244, 239), "panel": (230, 226, 216), "fg": (22, 26, 32), "muted": (96, 104, 116),
                          "grid": (205, 200, 190), "accent": (196, 120, 0), "accent2": (214, 84, 20),
                          "blue": (22, 104, 196), "green": (34, 138, 70), "red": (196, 48, 40),
                          "sea": (120, 170, 214), "land": (196, 168, 120), "cloud": (255, 255, 255)},
}
SERIES = ("accent", "blue", "green", "accent2", "red")
TYPES = ("diagram", "flow", "circulation", "water_cycle", "geo", "compare", "bar", "line", "callout")


class GraphicsError(Exception):
    def __init__(self, message, status="error"):
        super().__init__(message)
        self.status = status


E = GraphicsError


# --- small helpers ------------------------------------------------------------------------------

def _keys(d, allowed, where):
    if not isinstance(d, dict):
        raise E(f"{where} must be an object")
    extra = sorted(set(d) - set(allowed))
    if extra:
        raise E(f"{where}: unknown key(s) {extra}")


def _num(v, where, lo=None, hi=None):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise E(f"{where} must be a finite number, got {v!r}")
    if (lo is not None and v < lo) or (hi is not None and v > hi):
        raise E(f"{where} must be between {lo} and {hi}, got {v}")
    return float(v)


def _text(v, where, maxlen=200, required=True):
    if v is None and not required:
        return None
    if not (isinstance(v, str) and v.strip()):
        raise E(f"{where} must be a non-empty string")
    if len(v) > maxlen:
        raise E(f"{where} is longer than {maxlen} characters")
    return v.strip()


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _resolve(src, root, where):
    if not isinstance(src, str) or not src.strip():
        raise E(f"{where} must be a non-empty path")
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", src):
        raise E(f"{where} must be a local file, not a URL")
    real_root = os.path.realpath(root)
    p = os.path.realpath(os.path.join(real_root, src))
    if os.path.commonpath([p, real_root]) != real_root:
        raise E(f"{where} {src!r} resolves outside the spec folder")
    if not os.path.isfile(p):
        raise E(f"{where} not found: {src!r}")
    return p


def _geo():
    import importlib.util
    path = os.path.join(HERE, "..", "yt-geo", "geostack.py")
    if not os.path.isfile(path):
        raise E("geographic graphics need the yt-geo skill next to yt-graphics")
    spec = importlib.util.spec_from_file_location("geostack_for_graphics", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def nice_step(span, target=5):
    """A 1/2/5 x 10^n step giving about `target` intervals over span."""
    raw = span / max(target, 1)
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


def fmt_num(v, decimals=None):
    if decimals is None:
        decimals = 0 if abs(v - round(v)) < 1e-9 else (1 if abs(v * 10 - round(v * 10)) < 1e-6 else 2)
    return f"{v:,.{decimals}f}"


# --- canvas with measured text ------------------------------------------------------------------

class Fonts:
    def __init__(self):
        self.files = {}
        for style in ("Black", "Bold", "SemiBold", "Regular"):
            self.files[style] = self._find(f"Inter:style={style}") or self._find("DejaVu Sans:style=Bold")
        if not self.files["Bold"]:
            raise E("no usable font found (Inter or DejaVu Sans)")
        self.cache = {}

    @staticmethod
    def _find(family):
        try:
            r = subprocess.run(["fc-match", "-f", "%{file}", family], capture_output=True, text=True, timeout=20)
            p = r.stdout.strip()
            return p if r.returncode == 0 and os.path.isfile(p) else None
        except (OSError, subprocess.TimeoutExpired):
            return None

    def get(self, weight, size):
        key = (weight, size)
        if key not in self.cache:
            self.cache[key] = ImageFont.truetype(self.files.get(weight) or self.files["Bold"], size * SS)
        return self.cache[key]


class Canvas:
    """Draws in 1920x1080 coordinates on a 2x supersampled image; records every text box so overflow
    and safe-area violations are errors, not surprises."""
    def __init__(self, style, fonts, background=True):
        self.s = STYLES[style]
        self.fonts = fonts
        self.im = Image.new("RGB", (W * SS, H * SS), self.s["bg"])
        self.d = ImageDraw.Draw(self.im, "RGBA")
        self.text_boxes = []
        self.obstacles = []                  # drawn lines/arrows text must not cross: (points, half-width, owner)
        self.safe = (W * SAFE["left"], H * SAFE["top"], W * (1 - SAFE["right"]), H * (1 - SAFE["bottom"]))
        self.content_bottom = H * CAPTION_TOP

    def c(self, name):
        return self.s[name] if isinstance(name, str) else tuple(name)

    def _p(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def line(self, pts, color, width):
        self.d.line(self._p(pts), fill=self.c(color), width=int(width * SS), joint="curve")

    def rect(self, box, fill=None, outline=None, width=2, radius=0):
        b = [v * SS for v in box]
        if radius:
            self.d.rounded_rectangle(b, radius=radius * SS, fill=self.c(fill) if fill else None,
                                     outline=self.c(outline) if outline else None, width=int(width * SS))
        else:
            self.d.rectangle(b, fill=self.c(fill) if fill else None,
                             outline=self.c(outline) if outline else None, width=int(width * SS))

    def ellipse(self, box, fill=None, outline=None, width=2):
        self.d.ellipse([v * SS for v in box], fill=self.c(fill) if fill else None,
                       outline=self.c(outline) if outline else None, width=int(width * SS))

    def polygon(self, pts, fill):
        self.d.polygon(self._p(pts), fill=self.c(fill))

    def obstacle(self, pts, width, owner=None):
        self.obstacles.append(([tuple(p) for p in pts], width / 2 + 2, owner))

    def arrow(self, p0, p1, color, width=6, head=None, owner=None):
        head = head or width * 3.2
        self.obstacle([p0, p1], max(width, head * 0.8), owner)
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        base = (p1[0] - head * 0.85 * math.cos(ang), p1[1] - head * 0.85 * math.sin(ang))
        self.line([p0, base], color, width)
        pts = [p1, (p1[0] - head * math.cos(ang - 0.42), p1[1] - head * math.sin(ang - 0.42)),
               (p1[0] - head * math.cos(ang + 0.42), p1[1] - head * math.sin(ang + 0.42))]
        self.polygon(pts, color)

    def measure(self, text, weight, size):
        f = self.fonts.get(weight, size)
        b = self.d.textbbox((0, 0), text, font=f)
        return (b[2] - b[0]) / SS, (b[3] - b[1]) / SS

    def wrap(self, text, weight, size, max_w):
        words, lines, cur = text.split(), [], ""
        for w_ in words:
            trial = (cur + " " + w_).strip()
            if self.measure(trial, weight, size)[0] <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w_
        if cur:
            lines.append(cur)
        return lines

    def text(self, text, x, y, size=36, weight="Bold", color="fg", anchor="mm", max_w=None, max_lines=1,
             min_size=None, stroke=0, where="text"):
        """Fit text (shrinking to min_size, wrapping to max_lines) into max_w; draw it; record its box.
        Raises if it cannot fit."""
        lay = self.layout(text, x, y, size, weight, anchor, max_w, max_lines, min_size, where)
        return self.draw_layout(lay, color, stroke, where)

    def layout(self, text, x, y, size=36, weight="Bold", anchor="mm", max_w=None, max_lines=1, min_size=None,
               where="text"):
        min_size = max(MIN_TEXT_PX, min_size or int(size * 0.7))
        max_w = max_w or W
        s_ = size
        while True:
            lines = self.wrap(text, weight, s_, max_w)
            widest = max(self.measure(l, weight, s_)[0] for l in lines)
            if len(lines) <= max_lines and widest <= max_w + 0.5:
                break
            if s_ <= min_size:
                raise E(f"{where}: {text!r} does not fit in {max_w:.0f} px on {max_lines} line(s) at >= {min_size} px",
                        status="overflow")
            s_ -= 2
        lh = s_ * 1.18
        total = lh * len(lines)
        top = {"m": y - total / 2, "t": y, "b": y - total}[anchor[1]]
        rows = []
        for i, l in enumerate(lines):
            lw = self.measure(l, weight, s_)[0]
            lx = {"m": x - lw / 2, "l": x, "r": x - lw}[anchor[0]]
            cy = top + lh * (i + 0.5)
            rows.append((l, lx, cy, (lx, cy - s_ * 0.6, lx + lw, cy + s_ * 0.6)))
        box = (min(r[3][0] for r in rows), min(r[3][1] for r in rows), max(r[3][2] for r in rows),
               max(r[3][3] for r in rows))
        return {"text": text, "size": s_, "weight": weight, "rows": rows, "box": box}

    def draw_layout(self, lay, color, stroke, where):
        f = self.fonts.get(lay["weight"], lay["size"])
        for l, lx, cy, _ in lay["rows"]:
            self.d.text((lx * SS, cy * SS), l, font=f, fill=self.c(color), anchor="lm",
                        stroke_width=int(stroke * SS), stroke_fill=self.s["bg"])
        self.text_boxes.append({"where": where, "text": lay["text"], "size": lay["size"],
                                "box": [round(v, 1) for v in lay["box"]]})
        return lay["box"]

    def collides(self, box, pad=4):
        b = (box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad)
        for t in self.text_boxes:
            o = t["box"]
            if b[0] < o[2] and o[0] < b[2] and b[1] < o[3] and o[1] < b[3]:
                return f"text {t['where']!r}"
        for pts, hw, _ in self.obstacles:
            for p0, p1 in zip(pts, pts[1:]):
                if _seg_hits_box(p0, p1, (box[0] - hw, box[1] - hw, box[2] + hw, box[3] + hw)):
                    return "a drawn line or arrow"
        return None

    def place(self, text, candidates, size, weight, color, max_w, max_lines=2, stroke=3, where="label"):
        """Draw text at the first candidate (x, y, anchor) where it touches no other text and no line."""
        last = None
        for x, y, anchor in candidates:
            lay = self.layout(text, x, y, size, weight, anchor, max_w, max_lines, where=where)
            last = self.collides(lay["box"])
            if last is None and self.inside(lay["box"]):
                return self.draw_layout(lay, color, stroke, where)
        raise E(f"{where}: no free place for {text!r} (it would overlap {last or 'the safe-area edge'})",
                status="overflow")

    def inside(self, box):
        x0, y0, x1, y1 = self.safe
        return box[0] >= x0 and box[1] >= y0 and box[2] <= x1 and box[3] <= self.content_bottom

    def check_safe(self, caption_band):
        x0, y0, x1, y1 = self.safe
        small = [t for t in self.text_boxes if t["size"] < MIN_TEXT_PX]
        if small:
            raise E("text below the mobile minimum of %d px: " % MIN_TEXT_PX
                    + ", ".join(f"{t['where']} {t['size']} px" for t in small[:4]), status="overflow")
        tb = self.text_boxes
        for i in range(len(tb)):
            for j in range(i + 1, len(tb)):
                a, b = tb[i]["box"], tb[j]["box"]
                if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                    raise E(f"text overlaps: {tb[i]['where']} {tb[i]['text']!r} and {tb[j]['where']} {tb[j]['text']!r}",
                            status="overflow")
        for t in tb:
            for pts, hw, owner in self.obstacles:
                if owner == (t["where"], t["text"]):
                    continue
                for p0, p1 in zip(pts, pts[1:]):
                    bx = t["box"]
                    if _seg_hits_box(p0, p1, (bx[0] - hw + 2, bx[1] - hw + 2, bx[2] + hw - 2, bx[3] + hw - 2)):
                        raise E(f"{t['where']} {t['text']!r} is drawn across a line or arrow", status="overflow")
        if caption_band:
            y1 = min(y1, H * CAPTION_TOP)
        bad = [t for t in self.text_boxes
               if t["box"][0] < x0 - 0.5 or t["box"][1] < y0 - 0.5 or t["box"][2] > x1 + 0.5 or t["box"][3] > y1 + 0.5]
        if bad:
            raise E(f"text outside the landscape safe area{' / above the caption band' if caption_band else ''}: "
                    + ", ".join(f"{b['where']} {b['box']}" for b in bad[:4]), status="overflow")

    def finish(self):
        return self.im.resize((W, H), Image.LANCZOS)


def _seg_hits_box(p0, p1, box):
    """Liang-Barsky: does the segment p0-p1 pass through the rectangle?"""
    x0, y0, x1, y1 = box
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, p0[0] - x0), (dx, x1 - p0[0]), (-dy, p0[1] - y0), (dy, y1 - p0[1])):
        if p == 0:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return False
    return True


# --- layout -------------------------------------------------------------------------------------

def frame_parts(cv, g):
    """Title, source footer and the content box every type draws into."""
    x0, y0, x1, y1 = cv.safe
    y0 += CREDIT_BAND
    bottom = H * CAPTION_TOP if g["caption_band"] else y1
    top = y0 + 8
    if g.get("title"):
        cv.text(g["title"], x0, y0 + 30, 46, "Black", "fg", anchor="lm", max_w=x1 - x0, where="title")
        if g.get("subtitle"):
            cv.text(g["subtitle"], x0, y0 + 78, 30, "SemiBold", "muted", anchor="lm", max_w=x1 - x0, where="subtitle")
            top = y0 + 108
        else:
            top = y0 + 68
    cv.text(("Source: " if not g["source"].lower().startswith(("source", "data")) else "") + g["source"],
            x0, bottom - 16, 24, "SemiBold", "muted", anchor="lm", max_w=x1 - x0, where="source")
    return (x0, top + 10, x1, bottom - 44)


def nx(box, x):
    return box[0] + x * (box[2] - box[0])


def ny(box, y):
    return box[1] + y * (box[3] - box[1])


def _clip_to_rect(c, other, half_w, half_h):
    """Point where the segment centre->other leaves a rectangle of half sizes around centre."""
    dx, dy = other[0] - c[0], other[1] - c[1]
    if dx == 0 and dy == 0:
        return c
    t = min(half_w / abs(dx) if dx else 1e9, half_h / abs(dy) if dy else 1e9)
    return (c[0] + dx * t, c[1] + dy * t)


# --- types: schematics --------------------------------------------------------------------------

NODE_STYLES = {"default": ("panel", "fg"), "accent": ("accent", "bg"), "blue": ("blue", "bg"),
               "green": ("green", "bg"), "red": ("red", "bg"), "plain": (None, "fg")}


def v_diagram(g, where):
    _keys(g, ("type", "id", "title", "subtitle", "source", "style", "caption_band", "nodes", "arrows", "notes"), where)
    nodes = g.get("nodes") or []
    if not isinstance(nodes, list) or not nodes:
        raise E(f"{where}.nodes must be a non-empty list")
    ids = set()
    for i, n in enumerate(nodes):
        w = f"{where}.nodes[{i}]"
        _keys(n, ("id", "text", "x", "y", "w", "h", "style", "step", "hl"), w)
        _text(n.get("id"), f"{w}.id", 40)
        if n["id"] in ids:
            raise E(f"{w}.id {n['id']!r} is used twice")
        ids.add(n["id"])
        _text(n.get("text"), f"{w}.text", 80)
        for k in ("x", "y"):
            _num(n.get(k), f"{w}.{k}", 0, 1)
        for k, d in (("w", 0.18), ("h", 0.14)):
            _num(n.get(k, d), f"{w}.{k}", 0.04, 1)
        if n.get("style", "default") not in NODE_STYLES:
            raise E(f"{w}.style must be one of {sorted(NODE_STYLES)}")
        _step(n, w); _hl(n, w)
    for i, a in enumerate(g.get("arrows") or []):
        w = f"{where}.arrows[{i}]"
        _keys(a, ("from", "to", "label", "color", "step"), w)
        for k in ("from", "to"):
            v = a.get(k)
            if isinstance(v, str):
                if v not in ids:
                    raise E(f"{w}.{k}: no node {v!r}")
            elif not (isinstance(v, list) and len(v) == 2):
                raise E(f"{w}.{k} must be a node id or [x, y] (0-1)")
            else:
                _num(v[0], f"{w}.{k}[0]", 0, 1); _num(v[1], f"{w}.{k}[1]", 0, 1)
        _text(a.get("label"), f"{w}.label", 60, required=False)
        if a.get("color", "accent") not in STYLES["documentary_dark"]:
            raise E(f"{w}.color must be a style colour name")
        _step(a, w)
    for i, n in enumerate(g.get("notes") or []):
        w = f"{where}.notes[{i}]"
        _keys(n, ("text", "x", "y", "step", "size", "hl"), w)
        _text(n.get("text"), f"{w}.text", 120)
        _num(n.get("x"), f"{w}.x", 0, 1); _num(n.get("y"), f"{w}.y", 0, 1)
        _num(n.get("size", 30), f"{w}.size", MIN_TEXT_PX, 60)
        _step(n, w); _hl(n, w)


def _step(e, where):
    if "step" in e:
        v = e["step"]
        if isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= MAX_STEPS:
            raise E(f"{where}.step must be an integer 1-{MAX_STEPS}")


def _hl(e, where):
    """`hl`: the build steps at which this node / note is emphasised (a ring around a node, brighter text for a note)"""
    if "hl" in e:
        v = e["hl"]
        if not (isinstance(v, list) and v and all(isinstance(x, int) and not isinstance(x, bool) and 1 <= x <= MAX_STEPS for x in v)):
            raise E(f"{where}.hl must be a list of build steps (1-{MAX_STEPS})")


def d_diagram(cv, g, step):
    box = frame_parts(cv, g)
    nodes = {n["id"]: n for n in g["nodes"]}
    geo = {}
    for n in g["nodes"]:
        cx, cy = nx(box, n["x"]), ny(box, n["y"])
        hw = n.get("w", 0.18) * (box[2] - box[0]) / 2
        hh = n.get("h", 0.14) * (box[3] - box[1]) / 2
        geo[n["id"]] = (cx, cy, hw, hh)

    def pt(v, other):
        if isinstance(v, str):
            cx, cy, hw, hh = geo[v]
            o = other if isinstance(other, tuple) else other
            return _clip_to_rect((cx, cy), o, hw + 10, hh + 10)
        return (nx(box, v[0]), ny(box, v[1]))

    def centre(v):
        return (geo[v][0], geo[v][1]) if isinstance(v, str) else (nx(box, v[0]), ny(box, v[1]))

    labels = []
    for a in g.get("arrows") or []:
        if a.get("step", 1) > step:
            continue
        c0, c1 = centre(a["from"]), centre(a["to"])
        p0, p1 = pt(a["from"], c1), pt(a["to"], c0)
        cv.arrow(p0, p1, a.get("color", "accent"), 7)
        if a.get("label"):
            mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
            ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            off = g.get("_label_offset", 30)
            ox, oy = -math.sin(ang) * off, math.cos(ang) * off
            if oy > 0:
                ox, oy = -ox, -oy
            labels.append((a["label"], (mx, my), (ox, oy), a.get("color", "accent")))
    for n in g["nodes"]:
        if n.get("step", 1) > step:
            continue
        cx, cy, hw, hh = geo[n["id"]]
        fill, fg = NODE_STYLES[n.get("style", "default")]
        if fill:
            cv.rect((cx - hw, cy - hh, cx + hw, cy + hh), fill=fill, radius=14)
        else:
            cv.rect((cx - hw, cy - hh, cx + hw, cy + hh), outline="muted", width=3, radius=14)
        if step in (n.get("hl") or []):
            cv.rect((cx - hw - 9, cy - hh - 9, cx + hw + 9, cy + hh + 9), outline="fg", width=7, radius=20)
        cv.text(n["text"], cx, cy, 34, "Bold", fg, max_w=hw * 2 - 24, max_lines=3, where=f"node {n['id']}")
    for text, (mx, my), (ox, oy), col in labels:        # labels last, so nodes never cover them
        n = math.hypot(ox, oy) or 1
        cands = [(mx + ox / n * d, my + oy / n * d, "mm") for d in (n, n + 24, n + 52)] + \
                [(mx - ox / n * d, my - oy / n * d, "mm") for d in (n, n + 24, n + 52)]
        cv.place(text, cands, 30, "Bold", col, g.get("_label_w", 360), stroke=3, where="arrow label")
    for n in g.get("notes") or []:
        if n.get("step", 1) <= step:
            cv.text(n["text"], nx(box, n["x"]), ny(box, n["y"]), int(n.get("size", 30)), "SemiBold", "fg" if step in (n.get("hl") or []) else "muted",
                    max_w=(box[2] - box[0]) * 0.4, max_lines=3, where="note")


def v_flow(g, where):
    _keys(g, ("type", "id", "title", "subtitle", "source", "style", "caption_band", "steps", "arrow_labels", "build"), where)
    steps = g.get("steps")
    if not isinstance(steps, list) or not 2 <= len(steps) <= 6:
        raise E(f"{where}.steps must list 2-6 steps")
    for i, s in enumerate(steps):
        _text(s, f"{where}.steps[{i}]", 80)
    labels = g.get("arrow_labels") or []
    if not isinstance(labels, list) or len(labels) > len(steps) - 1:
        raise E(f"{where}.arrow_labels must have at most {len(steps) - 1} entries")
    for i, l in enumerate(labels):
        _text(l, f"{where}.arrow_labels[{i}]", 40, required=False)


def flow_as_diagram(g):
    n = len(g["steps"])
    build = bool(g.get("build"))
    w = min(0.62 / n, 0.2)
    nodes = [{"id": f"s{i}", "text": t, "x": (i + 0.5) / n, "y": 0.5, "w": w, "h": 0.3,
              "style": "accent" if i == n - 1 else "default", "step": (i + 1) if build else 1}
             for i, t in enumerate(g["steps"])]
    labels = g.get("arrow_labels") or []
    arrows = [{"from": f"s{i}", "to": f"s{i + 1}", "label": labels[i] if i < len(labels) else None,
               "step": (i + 2) if build else 1} for i in range(n - 1)]
    return dict(g, type="diagram", nodes=nodes, arrows=[{k: v for k, v in a.items() if v is not None} for a in arrows],
                _label_offset=34, _label_w=(0.38 / n) * (W * 0.9))


def v_circulation(g, where):
    _keys(g, ("type", "id", "title", "subtitle", "source", "style", "caption_band", "labels", "ground_labels",
              "rising_cloud", "build", "step_map", "cloud_step"), where)
    sm = g.get("step_map")
    if sm is not None and not (isinstance(sm, list) and len(sm) == 4 and all(isinstance(x, int) and not isinstance(x, bool) and 1 <= x <= MAX_STEPS for x in sm)):
        raise E(f"{where}.step_map must list the build step of rising, aloft, sinking and surface (four integers)")
    if "cloud_step" in g and (isinstance(g["cloud_step"], bool) or not isinstance(g["cloud_step"], int) or not 1 <= g["cloud_step"] <= MAX_STEPS):
        raise E(f"{where}.cloud_step must be an integer 1-{MAX_STEPS}")
    labels = g.get("labels") or {}
    _keys(labels, ("rising", "aloft", "sinking", "surface"), f"{where}.labels")
    for k, v in labels.items():
        _text(v, f"{where}.labels.{k}", 50)
    gl = g.get("ground_labels") or []
    if not isinstance(gl, list) or len(gl) > 6:
        raise E(f"{where}.ground_labels must be a list of at most 6")
    for i, x in enumerate(gl):
        _keys(x, ("x", "text"), f"{where}.ground_labels[{i}]")
        _num(x.get("x"), f"{where}.ground_labels[{i}].x", 0, 1)
        _text(x.get("text"), f"{where}.ground_labels[{i}].text", 30)


def _cloud(cv, cx, cy, r, color="cloud"):
    for dx, dy, k in ((-1.0, 0.2, 0.75), (-0.35, -0.3, 1.0), (0.4, -0.15, 0.85), (1.0, 0.25, 0.65), (0.0, 0.3, 0.8)):
        rr = r * k
        cv.ellipse((cx + dx * r - rr, cy + dy * r - rr, cx + dx * r + rr, cy + dy * r + rr), fill=color)


def d_circulation(cv, g, step):
    box = frame_parts(cv, g)
    build = bool(g.get("build"))
    L = g.get("labels") or {}
    gx0, gx1 = box[0] + 40, box[2] - 40
    ground = box[3] - 70
    cv.rect((box[0], ground, box[2], box[3] - 20), fill="land", radius=10)
    for x in g.get("ground_labels") or []:
        px = gx0 + x["x"] * (gx1 - gx0)
        cv.line([(px, ground - 12), (px, ground + 4)], "fg", 3)
        cv.text(x["text"], px, ground + 26, 28, "Bold", "bg", max_w=260, where="ground label")
    top, bot = box[1] + 60, ground - 60
    left, right = gx0 + 110, gx1 - 110
    segs = [("rising", (left, bot), (left, top), "accent2", (left + 26, (top + bot) / 2), "lm"),
            ("aloft", (left + 30, top - 10), (right - 30, top - 10), "accent", ((left + right) / 2, top - 52), "mm"),
            ("sinking", (right, top), (right, bot), "blue", (right - 26, (top + bot) / 2), "rm"),
            ("surface", (right - 30, bot + 12), (left + 30, bot + 12), "blue", ((left + right) / 2, bot - 28), "mm")]
    smap = g.get("step_map") or [1, 2, 3, 4]
    if g.get("rising_cloud") and (not build or step >= g.get("cloud_step", 1)):
        _cloud(cv, left, top + 30, 42)
    for k, (name, p0, p1, col, lp, anc) in enumerate(segs):
        if build and smap[k] > step:
            continue
        cv.arrow(p0, p1, col, 12, head=40)
        if L.get(name):
            cv.text(L[name], lp[0], lp[1], 34, "Bold", col, anchor=anc, max_w=(right - left) / 2 - 40, max_lines=2,
                    stroke=3, where=f"label {name}")


def v_water_cycle(g, where):
    _keys(g, ("type", "id", "title", "subtitle", "source", "style", "caption_band", "labels", "build"), where)
    labels = g.get("labels") or {}
    _keys(labels, ("evaporation", "transport", "rainfall", "runoff", "sea", "land"), f"{where}.labels")
    for k, v in labels.items():
        _text(v, f"{where}.labels.{k}", 50)


def d_water_cycle(cv, g, step):
    box = frame_parts(cv, g)
    build = bool(g.get("build"))
    L = g.get("labels") or {}
    bx0, by0, bx1, by1 = box
    split = bx0 + (bx1 - bx0) * 0.45
    surf = by1 - 90
    cv.rect((bx0, surf, split, by1), fill="sea", radius=8)
    cv.polygon([(split, surf + 10), (split + 120, surf - 60), (bx1, surf - 110), (bx1, by1), (split, by1)], "land")
    if L.get("sea"):
        cv.text(L["sea"], (bx0 + split) / 2, (surf + by1) / 2, 32, "Bold", "fg", max_w=split - bx0 - 40, where="sea")
    if L.get("land"):
        cv.text(L["land"], (split + bx1) / 2 + 60, by1 - 40, 32, "Bold", "bg", max_w=bx1 - split - 160, where="land")
    sx, sy = bx0 + 120, by0 + 90                                             # sun
    cv.ellipse((sx - 48, sy - 48, sx + 48, sy + 48), fill="accent")
    for k in range(8):
        a = k * math.pi / 4
        cv.line([(sx + 62 * math.cos(a), sy + 62 * math.sin(a)), (sx + 84 * math.cos(a), sy + 84 * math.sin(a))], "accent", 5)
    c1 = ((bx0 + split) / 2 + 40, by0 + 120)
    c2 = (split + (bx1 - split) * 0.55, by0 + 140)
    stages = []
    stages.append(lambda: [cv.arrow((x, surf - 20), (x + 10 * ((i % 2) * 2 - 1), c1[1] + 90), "blue", 7, 26)
                           for i, x in enumerate(np.linspace(bx0 + 220, split - 120, 4))] and None)
    stages.append(lambda: (_cloud(cv, c1[0], c1[1], 56), _cloud(cv, c2[0], c2[1], 64),
                           cv.arrow((c1[0] + 110, c1[1] - 10), (c2[0] - 120, c2[1] - 10), "fg", 8, 30)))
    stages.append(lambda: [cv.line([(x, c2[1] + 70 + (i % 3) * 14), (x - 18, c2[1] + 150 + (i % 3) * 14)], "blue", 5)
                           for i, x in enumerate(np.linspace(c2[0] - 90, c2[0] + 90, 7))] and None)
    stages.append(lambda: cv.arrow((split + 220, surf - 80), (split - 40, surf + 30), "blue", 9, 32))
    labels = [("evaporation", (split + 10, (surf + c1[1]) / 2 + 40), "blue"),
              ("transport", ((c1[0] + c2[0]) / 2, c1[1] - 80), "fg"),
              ("rainfall", (c2[0] + 200, c2[1] + 120), "blue"),
              ("runoff", (split + 230, surf - 140), "blue")]
    for k, fn in enumerate(stages):
        if build and k + 1 > step:
            continue
        fn()
        name, (lx, ly), col = labels[k]
        if L.get(name):
            cv.text(L[name], lx, ly, 32, "Bold", col, max_w=300, max_lines=2, stroke=3, where=f"label {name}")


# --- types: data --------------------------------------------------------------------------------

def v_bar(g, where):
    _keys(g, ("type", "id", "title", "subtitle", "source", "style", "caption_band", "unit", "bars", "decimals"), where)
    _text(g.get("unit"), f"{where}.unit", 40)
    bars = g.get("bars")
    if not isinstance(bars, list) or not 1 <= len(bars) <= 12:
        raise E(f"{where}.bars must list 1-12 bars")
    for i, b in enumerate(bars):
        _keys(b, ("label", "value", "highlight"), f"{where}.bars[{i}]")
        _text(b.get("label"), f"{where}.bars[{i}].label", 40)
        _num(b.get("value"), f"{where}.bars[{i}].value")
    if all(b["value"] == 0 for b in bars):
        raise E(f"{where}.bars are all zero - nothing to chart")
    if "decimals" in g:
        _num(g["decimals"], f"{where}.decimals", 0, 4)


def d_bar(cv, g, step):
    box = frame_parts(cv, g)
    bars = g["bars"]
    vals = [b["value"] for b in bars]
    lo, hi = min(0.0, min(vals)), max(0.0, max(vals))
    st = nice_step(hi - lo, 5)
    lo, hi = math.floor(lo / st) * st, math.ceil(hi / st) * st
    x0, y0, x1, y1 = box[0] + 120, box[1] + 40, box[2] - 20, box[3] - 70

    def ty(v):
        return y1 - (v - lo) / (hi - lo) * (y1 - y0)

    dec = int(g["decimals"]) if "decimals" in g else None
    v = lo
    while v <= hi + st * 1e-6:
        cv.line([(x0, ty(v)), (x1, ty(v))], "grid", 2)
        cv.text(fmt_num(v, dec), x0 - 16, ty(v), 26, "SemiBold", "muted", anchor="rm", max_w=110, where="axis")
        v += st
    cv.text(g["unit"], x0, y0 - 28, 28, "Bold", "muted", anchor="lm", max_w=500, where="unit")
    n = len(bars)
    slot = (x1 - x0) / n
    bw = slot * 0.62
    for i, b in enumerate(bars):
        cx = x0 + slot * (i + 0.5)
        top, base = ty(max(b["value"], 0)), ty(min(b["value"], 0))
        cv.rect((cx - bw / 2, top, cx + bw / 2, base), fill="accent" if b.get("highlight") else "blue")
        lab_y = top - 26 if b["value"] >= 0 else base + 26
        cv.text(fmt_num(b["value"], dec), cx, lab_y, 30, "Black", "fg", max_w=slot - 10, where="value")
        cv.text(b["label"], cx, y1 + 36, 26, "Bold", "fg", max_w=slot - 12, max_lines=2, where="bar label")
    cv.line([(x0, ty(0)), (x1, ty(0))], "fg", 3)


def v_line(g, where):
    _keys(g, ("type", "id", "title", "subtitle", "source", "style", "caption_band", "x_label", "x_unit", "y_unit",
              "series", "annotations", "decimals"), where)
    _text(g.get("y_unit"), f"{where}.y_unit", 40)
    _text(g.get("x_unit"), f"{where}.x_unit", 40)
    _text(g.get("x_label"), f"{where}.x_label", 60, required=False)
    series = g.get("series")
    if not isinstance(series, list) or not 1 <= len(series) <= len(SERIES):
        raise E(f"{where}.series must list 1-{len(SERIES)} series")
    for i, s in enumerate(series):
        w = f"{where}.series[{i}]"
        _keys(s, ("name", "points"), w)
        _text(s.get("name"), f"{w}.name", 40)
        pts = s.get("points")
        if not isinstance(pts, list) or len(pts) < 2:
            raise E(f"{w}.points needs at least two [x, y] points")
        prev = None
        for j, p in enumerate(pts):
            if not (isinstance(p, list) and len(p) == 2):
                raise E(f"{w}.points[{j}] must be [x, y]")
            x = _num(p[0], f"{w}.points[{j}][0]"); _num(p[1], f"{w}.points[{j}][1]")
            if prev is not None and x <= prev:
                raise E(f"{w}.points: x must increase ({x} after {prev})")
            prev = x
    for i, a in enumerate(g.get("annotations") or []):
        _keys(a, ("x", "y", "text"), f"{where}.annotations[{i}]")
        _num(a.get("x"), f"{where}.annotations[{i}].x"); _num(a.get("y"), f"{where}.annotations[{i}].y")
        _text(a.get("text"), f"{where}.annotations[{i}].text", 60)


def d_line(cv, g, step):
    box = frame_parts(cv, g)
    xs = [p[0] for s in g["series"] for p in s["points"]]
    ys = [p[1] for s in g["series"] for p in s["points"]]
    xlo, xhi = min(xs), max(xs)
    ylo, yhi = min(0.0, min(ys)) if min(ys) >= 0 and min(ys) < 0.25 * max(ys) else min(ys), max(ys)
    if yhi == ylo:
        yhi = ylo + 1
    st = nice_step(yhi - ylo, 5)
    ylo, yhi = math.floor(ylo / st) * st, math.ceil(yhi / st) * st
    x0, y0, x1, y1 = box[0] + 120, box[1] + 40, box[2] - 40, box[3] - 96
    if len(g["series"]) > 1:
        y0 += 56
    years = g["x_unit"].lower() in ("year", "years") or all(float(x).is_integer() and 1000 <= x <= 3000 for x in xs)

    def px(x):
        return x0 + (x - xlo) / (xhi - xlo) * (x1 - x0)

    def py(y):
        return y1 - (y - ylo) / (yhi - ylo) * (y1 - y0)

    dec = int(g["decimals"]) if "decimals" in g else None
    v = ylo
    while v <= yhi + st * 1e-6:
        cv.line([(x0, py(v)), (x1, py(v))], "grid", 2)
        cv.text(fmt_num(v, dec), x0 - 16, py(v), 26, "SemiBold", "muted", anchor="rm", max_w=110, where="axis")
        v += st
    xst = nice_step(xhi - xlo, 6)
    v = math.ceil(xlo / xst) * xst
    while v <= xhi + xst * 1e-6:
        cv.line([(px(v), y1), (px(v), y1 + 10)], "muted", 2)
        cv.text(str(int(round(v))) if years else fmt_num(v), px(v), y1 + 32, 26, "SemiBold", "muted", max_w=160,
                where="x axis")
        v += xst
    cv.text(g["y_unit"], x0, y0 - 28, 28, "Bold", "muted", anchor="lm", max_w=600, where="y unit")
    xl = g.get("x_label") or ""
    if xl.strip().lower() != g["x_unit"].strip().lower():              # no "Year (year)"
        xl = (xl + " " if xl else "") + f"({g['x_unit']})"
    cv.text(xl, x1, y1 + 72, 26, "Bold", "muted", anchor="rm", max_w=400, where="x unit")
    for k, s in enumerate(g["series"]):
        col = SERIES[k]
        pts = [(px(x), py(y)) for x, y in s["points"]]
        cv.line(pts, col, 6)
        cv.obstacle(pts, 6, f"series {k}")
        for p in pts:
            cv.ellipse((p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6), fill=col)
        if len(g["series"]) > 1:
            lx = x0 + k * 360
            cv.rect((lx, box[1] + 18, lx + 30, box[1] + 30), fill=col)
            cv.text(s["name"], lx + 42, box[1] + 24, 28, "Bold", "fg", anchor="lm", max_w=300, where="legend")
    for a in g.get("annotations") or []:
        p = (px(a["x"]), py(a["y"]))
        cv.ellipse((p[0] - 10, p[1] - 10, p[0] + 10, p[1] + 10), outline="accent", width=4)
        cv.place(a["text"], [(p[0], p[1] - 44, "mm"), (p[0], p[1] + 48, "mm"), (p[0] - 24, p[1] - 44, "rm"),
                             (p[0] + 24, p[1] + 44, "lm"), (p[0], p[1] - 90, "mm"), (p[0], p[1] + 92, "mm")],
                 30, "Bold", "accent", 420, where="annotation")


def v_callout(g, where):
    _keys(g, ("type", "id", "title", "subtitle", "source", "style", "caption_band", "value", "unit", "label",
              "context", "decimals", "build"), where)
    _num(g.get("value"), f"{where}.value")
    _text(g.get("unit"), f"{where}.unit", 30)
    _text(g.get("label"), f"{where}.label", 80)
    _text(g.get("context"), f"{where}.context", 160, required=False)
    if "decimals" in g:
        _num(g["decimals"], f"{where}.decimals", 0, 4)


def _callout_first(g):
    """build steps of a callout: [title alone,] number and unit, label, context (the title step exists only for a titled callout)"""
    return 2 if (g.get("build") and g.get("title")) else 1


def d_callout(cv, g, step):
    box = frame_parts(cv, g)
    first = _callout_first(g)
    if step < first:                       # build: the title (and source line) alone
        return
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 - 40
    dec = int(g["decimals"]) if "decimals" in g else None
    val = fmt_num(g["value"], dec)
    vw, _ = cv.measure(val, "Black", 190)
    uw, _ = cv.measure(g["unit"], "Black", 90)
    total = vw + 24 + uw
    cv.text(val, cx - total / 2, cy, 190, "Black", "accent", anchor="lm", max_w=box[2] - box[0] - uw - 40, min_size=90,
            where="value")
    cv.text(g["unit"], cx - total / 2 + vw + 24, cy + 30, 90, "Black", "accent", anchor="lm", max_w=uw + 4, where="unit")
    if not g.get("build") or step >= first + 1:
        cv.text(g["label"], cx, cy + 150, 44, "Bold", "fg", max_w=box[2] - box[0] - 80, max_lines=2, where="label")
    if g.get("context") and (not g.get("build") or step >= first + 2):
        cv.text(g["context"], cx, cy + 240, 30, "SemiBold", "muted", max_w=box[2] - box[0] - 200, max_lines=2,
                where="context")


# --- types: geographic --------------------------------------------------------------------------

class GeoView:
    """A 16:9 view of a yt-geo stack PNG, placed by lon/lat with a width in km. The scale comes only
    from the grid's projection (EPSG) and pixel size - it is never assumed."""
    def __init__(self, spec, root, where, size):
        _keys(spec, ("stack", "grid", "center", "width_km"), where)
        gpath = _resolve(spec.get("grid"), root, f"{where}.grid")
        try:
            with open(gpath) as f:
                grid = json.load(f)
        except (OSError, ValueError) as e:
            raise E(f"{where}.grid unreadable: {type(e).__name__}: {e}")
        missing = [k for k in ("epsg", "x0", "y_top", "pixel_m", "width", "height") if k not in grid]
        if missing:
            raise E(f"{where}.grid has no {missing} - a scale bar needs real geospatial metadata", status="no_scale")
        _num(grid["pixel_m"], f"{where}.grid.pixel_m", 0.01, 10000)
        if not (isinstance(grid["epsg"], int) and (32601 <= grid["epsg"] <= 32660 or 32701 <= grid["epsg"] <= 32760)):
            raise E(f"{where}.grid.epsg must be a UTM zone (326xx/327xx) to measure distances", status="no_scale")
        self.grid = grid
        self.geo = _geo()
        src = _resolve(spec.get("stack"), root, f"{where}.stack")
        im = Image.open(src).convert("RGB")
        if im.size != (grid["width"], grid["height"]):
            raise E(f"{where}.stack is {im.size[0]}x{im.size[1]} but the grid is {grid['width']}x{grid['height']}")
        c = spec.get("center")
        if not (isinstance(c, list) and len(c) == 2):
            raise E(f"{where}.center must be [lon, lat]")
        lon, lat = _num(c[0], f"{where}.center[0]", -180, 180), _num(c[1], f"{where}.center[1]", -85, 85)
        self.width_km = _num(spec.get("width_km"), f"{where}.width_km", 0.3, 5000)
        self.size = size
        cx, cy = self.px(lon, lat)
        w = self.width_km * 1000 / grid["pixel_m"]
        h = w * size[1] / size[0]
        self.box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        if self.box[0] < -0.01 or self.box[1] < -0.01 or self.box[2] > grid["width"] + 0.01 or self.box[3] > grid["height"] + 0.01:
            raise E(f"{where}: a {self.width_km} km view at {c} leaves the imagery")
        self.image = im.resize(size, Image.BILINEAR, box=self.box)
        self.m_per_px = self.width_km * 1000 / size[0]          # metres per output pixel (projected grid)

    def px(self, lon, lat):
        x, y = self.geo.lonlat_to_utm(lon, lat, self.grid["epsg"])
        return ((float(x) - self.grid["x0"]) / self.grid["pixel_m"], (self.grid["y_top"] - float(y)) / self.grid["pixel_m"])

    def screen(self, lon, lat, origin=(0, 0)):
        gx, gy = self.px(lon, lat)
        return (origin[0] + (gx - self.box[0]) / (self.box[2] - self.box[0]) * self.size[0],
                origin[1] + (gy - self.box[1]) / (self.box[3] - self.box[1]) * self.size[1])

    def lonlat(self, sx, sy):
        gx = self.box[0] + sx / self.size[0] * (self.box[2] - self.box[0])
        gy = self.box[1] + sy / self.size[1] * (self.box[3] - self.box[1])
        x = self.grid["x0"] + gx * self.grid["pixel_m"]
        y = self.grid["y_top"] - gy * self.grid["pixel_m"]
        lon, lat = self.geo.utm_to_lonlat(x, y, self.grid["epsg"])
        return float(lon), float(lat)


def scale_bar(m_per_px, max_px):
    """The longest 1/2/5 x 10^n km (or m) length that fits in max_px, from the real metres per pixel."""
    best = None
    for exp in range(-1, 5):
        for m in (1, 2, 5):
            km = m * 10 ** exp
            if km < 0.1:
                continue
            px = km * 1000 / m_per_px
            if px <= max_px:
                best = (km, px)
    if not best:
        raise E("no scale bar length fits the frame")
    km, px = best
    label = f"{fmt_num(km)} km" if km >= 1 else f"{int(round(km * 1000))} m"
    return {"km": km, "px": round(px, 2), "label": label, "m_per_px": round(m_per_px, 4)}


def _draw_scale(cv, sb, x, y):
    cv.rect((x - 8, y - 46, x + sb["px"] + 8, y + 16), fill=(0, 0, 0, 150), radius=6)
    cv.rect((x, y - 6, x + sb["px"], y + 6), fill="fg")
    cv.rect((x, y - 6, x + sb["px"] / 2, y + 6), fill=(0, 0, 0))
    cv.rect((x, y - 6, x + sb["px"], y + 6), outline="fg", width=2)
    cv.text(sb["label"], x + sb["px"] / 2, y - 26, 28, "Bold", "fg", max_w=max(sb["px"], 140), where="scale bar")


def v_geo(g, where, root):
    _keys(g, ("type", "id", "title", "subtitle", "source", "style", "caption_band", "image", "credit", "date",
              "callouts", "arrows", "graticule", "scale_bar"), where)
    _text(g.get("credit"), f"{where}.credit", 80)
    _text(g.get("date"), f"{where}.date", 40, required=False)
    for i, c in enumerate(g.get("callouts") or []):
        _keys(c, ("at", "text", "step"), f"{where}.callouts[{i}]")
        if not (isinstance(c.get("at"), list) and len(c["at"]) == 2):
            raise E(f"{where}.callouts[{i}].at must be [lon, lat]")
        _num(c["at"][0], f"{where}.callouts[{i}].at[0]", -180, 180); _num(c["at"][1], f"{where}.callouts[{i}].at[1]", -85, 85)
        _text(c.get("text"), f"{where}.callouts[{i}].text", 40)
        _step(c, f"{where}.callouts[{i}]")
    for i, a in enumerate(g.get("arrows") or []):
        _keys(a, ("from", "to", "label", "step"), f"{where}.arrows[{i}]")
        for k in ("from", "to"):
            if not (isinstance(a.get(k), list) and len(a[k]) == 2):
                raise E(f"{where}.arrows[{i}].{k} must be [lon, lat]")
        _text(a.get("label"), f"{where}.arrows[{i}].label", 40, required=False)
        _step(a, f"{where}.arrows[{i}]")


def d_geo(cv, g, step, root, where):
    view = GeoView(g["image"], root, f"{where}.image", (W, H))
    cv.im.paste(view.image.resize((W * SS, H * SS), Image.LANCZOS), (0, 0))
    x0, y0, x1, y1 = cv.safe
    bottom = H * CAPTION_TOP if g["caption_band"] else y1
    cv.rect((0, 0, W, y0 + CREDIT_BAND + 120), fill=(0, 0, 0, 110))
    ty = y0 + CREDIT_BAND
    if g.get("title"):
        cv.text(g["title"], x0, ty + 30, 46, "Black", "fg", anchor="lm", max_w=x1 - x0, stroke=3, where="title")
    meta = g["credit"] + (f" · {g['date']}" if g.get("date") else "")
    cv.text(meta, x0, ty + 78, 26, "SemiBold", "fg", anchor="lm", max_w=x1 - x0, stroke=3, where="credit")
    info = {}
    sb = scale_bar(view.m_per_px, (x1 - x0) * 0.22) if g.get("scale_bar", True) else None
    tick_x1 = x1 - sb["px"] - 20 - 90 if sb else x1 - 60    # longitude labels stay clear of the scale bar
    if g.get("graticule", True):
        lon0, lat0 = view.lonlat(0, 0)
        lon1, lat1 = view.lonlat(W, H)
        st = nice_step(abs(lon1 - lon0), 4)
        v = math.ceil(min(lon0, lon1) / st) * st
        ticks = []
        while v <= max(lon0, lon1):
            sx, _ = view.screen(v, (lat0 + lat1) / 2)
            if x0 + 60 < sx < tick_x1:
                cv.line([(sx, bottom - 30), (sx, bottom - 12)], "fg", 3)
                cv.text(f"{abs(v):.{max(0, -int(math.floor(math.log10(st))))}f}°{'E' if v >= 0 else 'W'}", sx, bottom - 50,
                        26, "Bold", "fg", stroke=3, max_w=220, where="graticule")
                ticks.append(round(v, 6))
            v += st
        st2 = nice_step(abs(lat0 - lat1), 3)
        v = math.ceil(min(lat0, lat1) / st2) * st2
        while v <= max(lat0, lat1):
            _, sy = view.screen((lon0 + lon1) / 2, v)
            if y0 + CREDIT_BAND + 170 < sy < bottom - 90:
                cv.line([(x0 - 30, sy), (x0 - 12, sy)], "fg", 3)
                cv.text(f"{abs(v):.{max(0, -int(math.floor(math.log10(st2))))}f}°{'N' if v >= 0 else 'S'}", x0, sy,
                        26, "Bold", "fg", anchor="lm", stroke=3, max_w=220, where="graticule")
            v += st2
        info["graticule_lon"] = ticks
    pending_arrow_labels = []
    for a in g.get("arrows") or []:
        if a.get("step", 1) > step:
            continue
        p0, p1 = view.screen(*a["from"]), view.screen(*a["to"])
        cv.arrow(p0, p1, (0, 0, 0), 14, 48)
        cv.arrow(p0, p1, "accent", 8, 40)
        if a.get("label"):
            pending_arrow_labels.append((a["label"], p0, p1))
    for c in g.get("callouts") or []:
        if c.get("step", 1) > step:
            continue
        p = view.screen(*c["at"])
        if not (0 <= p[0] <= W and 0 <= p[1] <= H):
            raise E(f"{where}: callout {c['text']!r} at {c['at']} is outside the view")
        cv.ellipse((p[0] - 12, p[1] - 12, p[0] + 12, p[1] + 12), fill="accent", outline=(0, 0, 0), width=3)
        placed = None
        for dx, dy in ((150, -100), (-150, -100), (150, 100), (-150, 100), (0, -130), (0, 130)):
            tx, ty = p[0] + dx, p[1] + dy
            lay = cv.layout(c["text"], tx, ty, 34, "Black", "mm", 320, 2, where="callout")
            end = (tx, ty + (26 if dy < 0 else -26))
            hit = cv.collides(lay["box"]) or any(_seg_hits_box(p, end, tb["box"]) for tb in cv.text_boxes)
            if not hit and cv.inside(lay["box"]):
                placed = (lay, end)
                break
        if placed is None:
            raise E(f"{where}: no free place for callout {c['text']!r}", status="overflow")
        lay, end = placed
        cv.line([p, end], (0, 0, 0), 6)
        cv.line([p, end], "accent", 3)
        cv.obstacle([p, end], 6, ("callout", c["text"]))   # its own leader may touch it
        cv.draw_layout(lay, "accent", 4, "callout")
    for text, p0, p1 in pending_arrow_labels:            # after callouts: arrow labels find a free side
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        nxv, nyv = -math.sin(ang), math.cos(ang)
        cands = [(mx + nxv * d * sg, my + nyv * d * sg, "mm") for d in (52, 80, 112) for sg in (-1, 1)]
        cv.place(text, cands, 32, "Bold", "accent", 420, stroke=4, where="arrow label")
    if sb:
        _draw_scale(cv, sb, x1 - sb["px"] - 20, bottom - 30)
        info["scale_bar"] = sb
    cv.text(("Source: " if not g["source"].lower().startswith(("source", "data")) else "") + g["source"],
            x0, bottom - 16, 24, "SemiBold", "fg", anchor="lm", max_w=(x1 - x0) * 0.6, stroke=3,
            where="source")
    return info


def v_compare(g, where, root):
    _keys(g, ("type", "id", "title", "subtitle", "source", "style", "caption_band", "left", "right", "metric"), where)
    for side in ("left", "right"):
        s = g.get(side)
        _keys(s, ("geo", "file", "label", "credit"), f"{where}.{side}")
        _text(s.get("label"), f"{where}.{side}.label", 40)
        _text(s.get("credit"), f"{where}.{side}.credit", 80)
        if ("geo" in s) == ("file" in s):
            raise E(f"{where}.{side} needs exactly one of 'geo' or 'file'")
    m = g.get("metric")
    if m is not None:
        _keys(m, ("left", "right", "unit", "decimals"), f"{where}.metric")
        _num(m.get("left"), f"{where}.metric.left"); _num(m.get("right"), f"{where}.metric.right")
        _text(m.get("unit"), f"{where}.metric.unit", 30)


def d_compare(cv, g, step, root, where):
    box = frame_parts(cv, g)
    gap = 30
    pw = (box[2] - box[0] - gap) / 2
    ph = pw * 9 / 16
    if g.get("metric"):
        ph = min(ph, box[3] - box[1] - 150)
    else:
        ph = min(ph, box[3] - box[1] - 70)
    pw = ph * 16 / 9
    left0 = (box[0] + box[2]) / 2 - pw - gap / 2
    info = {}
    for k, side in enumerate(("left", "right")):
        s = g[side]
        ox = left0 + k * (pw + gap)
        oy = box[1] + 50
        size = (int(round(pw * SS)), int(round(ph * SS)))
        if "geo" in s:
            view = GeoView(s["geo"], root, f"{where}.{side}.geo", size)
            img = view.image
            sb = scale_bar(view.m_per_px * SS, pw * 0.3)
            info[f"{side}_scale_bar"] = sb
        else:
            img = Image.open(_resolve(s["file"], root, f"{where}.{side}.file")).convert("RGB")
            src_ar, dst_ar = img.size[0] / img.size[1], size[0] / size[1]
            if src_ar > dst_ar:
                cw = img.size[1] * dst_ar
                img = img.resize(size, Image.LANCZOS, box=((img.size[0] - cw) / 2, 0, (img.size[0] + cw) / 2, img.size[1]))
            else:
                ch = img.size[0] / dst_ar
                img = img.resize(size, Image.LANCZOS, box=(0, (img.size[1] - ch) / 2, img.size[0], (img.size[1] + ch) / 2))
            sb = None
        cv.im.paste(img, (int(round(ox * SS)), int(round(oy * SS))))
        cv.rect((ox, oy, ox + pw, oy + ph), outline="fg", width=2)
        cv.text(s["label"], ox + 16, oy - 24, 32, "Black", "fg", anchor="lm", max_w=pw - 32, where=f"{side} label")
        cv.text(s["credit"], ox + 14, oy + ph - 22, 24, "SemiBold", "fg", anchor="lm", max_w=pw * 0.55,
                stroke=3, where=f"{side} credit")
        if sb:
            _draw_scale(cv, sb, ox + pw - sb["px"] - 20, oy + ph - 24)
        if g.get("metric"):
            m = g["metric"]
            dec = int(m["decimals"]) if "decimals" in m else None
            cv.text(f"{fmt_num(m[side], dec)} {m['unit']}", ox + pw / 2, oy + ph + 52, 48, "Black", "accent",
                    max_w=pw - 20, where=f"{side} metric")
    return info


# --- driver -------------------------------------------------------------------------------------

VALIDATE = {"diagram": v_diagram, "flow": v_flow, "circulation": v_circulation, "water_cycle": v_water_cycle,
            "bar": v_bar, "line": v_line, "callout": v_callout}


def validate_graphic(g, where, root):
    if not isinstance(g, dict) or g.get("type") not in TYPES:
        raise E(f"{where}.type must be one of {list(TYPES)}")
    gid = g.get("id")
    if not (isinstance(gid, str) and re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,47}", gid)):
        raise E(f"{where}.id must be a short lowercase name (a-z, 0-9, _ or -)")
    _text(g.get("source"), f"{where}.source", 160)          # provenance is mandatory for every graphic
    _text(g.get("title"), f"{where}.title", 90, required=False)
    _text(g.get("subtitle"), f"{where}.subtitle", 120, required=False)
    if g.get("style", "documentary_dark") not in STYLES:
        raise E(f"{where}.style must be one of {sorted(STYLES)}")
    if g["type"] in ("geo", "compare"):
        (v_geo if g["type"] == "geo" else v_compare)(g, where, root)
    else:
        VALIDATE[g["type"]](g, where)


def steps_of(g):
    if g["type"] == "flow":
        return len(g["steps"]) * 2 - 1 if g.get("build") else 1
    if g["type"] == "circulation":
        return max((g.get("step_map") or [1, 2, 3, 4]) + [g.get("cloud_step", 1)]) if g.get("build") else 1
    if g["type"] == "water_cycle":
        return 4 if g.get("build") else 1
    if g["type"] == "callout":
        return (_callout_first(g) + 1 + (1 if g.get("context") else 0)) if g.get("build") else 1
    if g["type"] in ("diagram", "geo"):
        items = list(g.get("nodes") or []) + list(g.get("arrows") or []) + list(g.get("notes") or []) + list(g.get("callouts") or [])
        return max([1] + [x.get("step", 1) for x in items] + [h for x in items for h in (x.get("hl") or [])])
    return 1


def draw(g, step, fonts, root, where):
    g = dict(g, caption_band=g.get("caption_band", True))
    if g["type"] == "flow":
        g = flow_as_diagram(g)
    cv = Canvas(g.get("style", "documentary_dark"), fonts)
    info = {}
    if g["type"] == "diagram":
        d_diagram(cv, g, step)
    elif g["type"] == "circulation":
        d_circulation(cv, g, step)
    elif g["type"] == "water_cycle":
        d_water_cycle(cv, g, step)
    elif g["type"] == "bar":
        d_bar(cv, g, step)
    elif g["type"] == "line":
        d_line(cv, g, step)
    elif g["type"] == "callout":
        d_callout(cv, g, step)
    elif g["type"] == "geo":
        info = d_geo(cv, g, step, root, where)
    elif g["type"] == "compare":
        info = d_compare(cv, g, step, root, where)
    cv.check_safe(g["caption_band"])
    return cv.finish(), cv.text_boxes, info


def render_spec(spec, root, out_dir, only=None):
    _keys(spec, ("schema", "graphics", "meta"), "spec")
    gs = spec.get("graphics")
    if not isinstance(gs, list) or not gs:
        raise E("spec.graphics must be a non-empty list")
    ids = set()
    for i, g in enumerate(gs):
        validate_graphic(g, f"graphics[{i}]", root)
        if g["id"] in ids:
            raise E(f"graphics[{i}].id {g['id']!r} is used twice")
        ids.add(g["id"])
    if only and only not in ids:
        raise E(f"--only {only!r}: no such graphic")
    if not os.path.isdir(out_dir):
        raise E(f"output directory does not exist: {out_dir}")
    fonts = Fonts()
    results = []
    for i, g in enumerate(gs):
        if only and g["id"] != only:
            continue
        n = steps_of(g)
        files, boxes, info = [], [], {}
        rendered = []
        for st in range(1, n + 1):                         # everything is drawn and checked before writing
            im, tb, info = draw(g, st, fonts, root, f"graphics[{i}]")
            rendered.append(im)
            boxes = tb
        for st, im in enumerate(rendered, 1):
            name = f"{g['id']}.png" if st == n else f"{g['id']}.step{st}.png"
            path = os.path.join(out_dir, name)
            tmp = path + ".tmp"
            im.save(tmp, format="PNG", compress_level=6)
            os.replace(tmp, path)
            files.append(name)
        side = {"schema": "yt-graphics/1", "id": g["id"], "type": g["type"], "style": g.get("style", "documentary_dark"),
                "size": [W, H], "source": g["source"], "credit": g.get("credit"), "steps": files,
                "sha256": {f: _sha256(os.path.join(out_dir, f)) for f in files},
                "safe_area": SAFE, "caption_band_reserved": g.get("caption_band", True),
                "text_boxes": boxes, **info}
        with open(os.path.join(out_dir, f"{g['id']}.json"), "w") as f:
            json.dump(side, f, indent=1, ensure_ascii=False)
        results.append({"id": g["id"], "type": g["type"], "files": files, **({"scale_bar": info["scale_bar"]}
                                                                            if "scale_bar" in info else {})})
    return {"status": "ok", "out_dir": os.path.abspath(out_dir), "graphics": results}


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or "-h" in a or "--help" in a:
        print(__doc__); return 0
    try:
        known = {"--out-dir", "--only"}
        opts, pos, i = {}, [], 0
        while i < len(a):
            if a[i].startswith("--"):
                if a[i] not in known:
                    raise E(f"unknown option {a[i]}")
                if i + 1 >= len(a):
                    raise E(f"{a[i]} needs a value")
                opts[a[i]] = a[i + 1]; i += 2
            else:
                pos.append(a[i]); i += 1
        if len(pos) != 1:
            raise E("give exactly one spec.json")
        if "--out-dir" not in opts:
            raise E("--out-dir is required")
        try:
            with open(pos[0], encoding="utf-8") as f:
                spec = json.load(f)
        except (OSError, ValueError) as e:
            raise E(f"spec unreadable: {type(e).__name__}: {e}")
        root = os.path.dirname(os.path.abspath(pos[0]))
        print(json.dumps(render_spec(spec, root, opts["--out-dir"], opts.get("--only")), indent=1, ensure_ascii=False))
        return 0
    except GraphicsError as e:
        print(json.dumps({"status": e.status, "error": str(e)}, indent=1, ensure_ascii=False))
        return 2
    except Exception as e:  # never a traceback
        print(json.dumps({"status": "error", "error": f"unexpected {type(e).__name__}: {e}"}, indent=1))
        return 2


if __name__ == "__main__":
    sys.exit(main())
