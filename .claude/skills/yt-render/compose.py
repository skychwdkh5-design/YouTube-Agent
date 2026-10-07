"""compose.py - timeline version 3: vertical Shorts built from geographically aligned imagery.

Used by render.py for timelines with "version": 3. Versions 1/2 never reach this file.

Every frame is drawn in Python (Pillow + NumPy) and piped to the installed FFmpeg, which encodes
H.264 and adds the yt-voice narration. The camera is placed in longitude/latitude on the grid that
yt-geo/geostack.py wrote, so every date shares exactly the same framing and a wipe or a year flip
compares like with like. Sub-pixel crops (no zoompan jitter), word-anchored shot timing,
mobile-safe captions and per-shot source credits.

Only what a Short needs today: layers image, flip, wipe, fill, outline, label, arrow, pin.
Profile "short" = 1080x1920, 30 fps.
"""
import json, math, os, re, subprocess, tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import render as r      # RenderError, resolve_src, parse_voice, parse_srt, _sha256, ffprobe_json, font_file

Image.MAX_IMAGE_PIXELS = 400_000_000
PROFILES = {"short": {"width": 1080, "height": 1920, "fps": 30, "min_s": 35.0, "max_s": 60.0,
                      # YouTube Shorts UI: keep text out of the top 8 %, bottom 22 % and right 12 %
                      "safe": {"top": 0.08, "bottom": 0.22, "right": 0.12, "left": 0.06}}}
LAYER_TYPES = ("image", "flip", "wipe", "fill", "outline", "label", "arrow", "pin")
CAPTION = {"size": 68, "stroke": 7, "max_width": 820, "band_lower": 0.645, "band_upper": 0.33,
           "line_gap": 10}
STYLES = {"year": (150, "Black", "#FFFFFF"), "stat": (120, "Black", "#FFD23F"),
          "tag": (58, "Bold", "#FFFFFF"), "sub": (46, "SemiBold", "#FFFFFF"),
          "legend": (44, "Bold", "#FFFFFF")}
SLOTS = {"top": 0.155, "upper": 0.255, "middle": 0.36}
E = r.RenderError


# --- geometry ----------------------------------------------------------------------------------

def _utm():
    import importlib.util
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "yt-geo", "geostack.py")
    spec = importlib.util.spec_from_file_location("geostack", path)
    if not spec or not os.path.isfile(path):
        raise E("timeline v3 needs the yt-geo skill next to yt-render")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Grid:
    def __init__(self, doc):
        for k in ("epsg", "x0", "y_top", "pixel_m", "width", "height"):
            if k not in doc:
                raise E(f"grid is missing '{k}'")
        self.d = doc
        self.geo = _utm()

    def px(self, lon, lat):
        x, y = self.geo.lonlat_to_utm(lon, lat, self.d["epsg"])
        return ((float(x) - self.d["x0"]) / self.d["pixel_m"], (self.d["y_top"] - float(y)) / self.d["pixel_m"])

    def lonlat(self, px, py):
        x = self.d["x0"] + px * self.d["pixel_m"]
        y = self.d["y_top"] - py * self.d["pixel_m"]
        lon, lat = self.geo.utm_to_lonlat(x, y, self.d["epsg"])
        return float(lon), float(lat)


def _ll(v, where):
    if not (isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v)):
        raise E(f"{where} must be [lon, lat]")
    lon, lat = v
    if not (-180 <= lon <= 180 and -85 <= lat <= 85):
        raise E(f"{where} {v} is not a longitude/latitude")
    return float(lon), float(lat)


def _view(v, grid, aspect, where):
    if not isinstance(v, dict) or set(v) - {"center", "width_km"}:
        raise E(f"{where} must be {{center: [lon, lat], width_km}}")
    cx, cy = grid.px(*_ll(v.get("center"), f"{where}.center"))
    wkm = r._num(v.get("width_km"), f"{where}.width_km", 0.3, 5000)
    w = wkm * 1000 / grid.d["pixel_m"]
    h = w * aspect
    x0, y0 = cx - w / 2, cy - h / 2
    if x0 < -0.01 or y0 < -0.01 or x0 + w > grid.d["width"] + 0.01 or y0 + h > grid.d["height"] + 0.01:
        lo0, la0 = grid.lonlat(0, grid.d["height"])
        lo1, la1 = grid.lonlat(grid.d["width"], 0)
        raise E(f"{where}: a {wkm} km wide view at {v['center']} leaves the imagery "
                f"(covers lon {lo0:.3f}..{lo1:.3f}, lat {la0:.3f}..{la1:.3f}); move it or narrow it")
    return (cx, cy, w)


def _ease(t, kind):
    t = min(1.0, max(0.0, t))
    return t if kind == "linear" else t * t * (3 - 2 * t)


def _camera(shot, t):
    """The camera's (centre x, centre y, width) in grid pixels at time t of a shot."""
    (x0, y0, w0), (x1, y1, w1) = shot["views"]
    span = max(shot["end"] - shot["start"], 1e-6)
    k = _ease((t - shot["start"]) / span, shot["ease"])
    w = math.exp(math.log(w0) + (math.log(w1) - math.log(w0)) * k)
    return x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, w


# --- validation --------------------------------------------------------------------------------

def _time(v, words, where):
    """A time in seconds, or a word anchor {"word": i, "edge": "start"|"end", "offset": s}."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return r._num(v, where, 0, 3600)
    if isinstance(v, dict):
        r._keys(v, ("word", "edge", "offset"), where)
        if not words:
            raise E(f"{where} anchors to a word but the narration has no word timings")
        i = r._num(v.get("word"), f"{where}.word", 0, len(words) - 1, int)
        edge = v.get("edge", "start")
        if edge not in ("start", "end"):
            raise E(f"{where}.edge must be 'start' or 'end'")
        off = r._num(v.get("offset", 0.0), f"{where}.offset", -5, 5)
        return max(0.0, words[i][edge] + off)
    raise E(f"{where} must be seconds or a word anchor")


def _color(c, where):
    if not (isinstance(c, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", c)):
        raise E(f"{where} must be a #RRGGBB colour")
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def validate(tl, root, limits):
    r._keys(tl, ("version", "profile", "grid", "assets", "voice", "captions", "end", "shots", "meta"), "timeline")
    prof = PROFILES.get(tl.get("profile"))
    if not prof:
        raise E(f"timeline.profile must be one of {sorted(PROFILES)}")
    W, H, fps = prof["width"], prof["height"], prof["fps"]
    gpath = r.resolve_src(tl.get("grid"), root, "grid")
    try:
        with open(gpath) as f:
            grid = Grid(json.load(f))
    except (OSError, ValueError) as e:
        raise E(f"grid unreadable: {type(e).__name__}: {e}")

    assets = {}
    for aid, a in (tl.get("assets") or {}).items():
        where = f"assets.{aid}"
        r._keys(a, ("src", "kind", "label", "credit", "prov"), where)
        kind = a.get("kind", "image")
        if kind not in ("image", "mask"):
            raise E(f"{where}.kind must be 'image' or 'mask'")
        src = r.resolve_src(a.get("src"), root, where)
        if not src.lower().endswith(".png"):
            raise E(f"{where}: grid assets must be PNG (from yt-geo)")
        with Image.open(src) as im:
            size = im.size
        if size != (grid.d["width"], grid.d["height"]):
            raise E(f"{where} is {size[0]}x{size[1]} but the grid is {grid.d['width']}x{grid.d['height']}")
        if kind == "image" and not (isinstance(a.get("credit"), str) and a["credit"].strip()):
            raise E(f"{where}: every image needs an on-screen 'credit' (its provenance)")
        assets[aid] = {"src": src, "kind": kind, "label": a.get("label", aid), "credit": a.get("credit"),
                       "prov": a.get("prov")}
    if not assets:
        raise E("timeline.assets is empty")

    voice = r.parse_voice([tl["voice"]] if tl.get("voice") else None, root, limits)
    words = []
    if voice and tl["voice"].get("meta"):
        with open(r.resolve_src(tl["voice"]["meta"], root, "voice.meta"), encoding="utf-8") as f:
            words = [{"text": w["text"], "start": float(w["start"]) + voice["start"],
                      "end": float(w["end"]) + voice["start"]} for w in json.load(f).get("words") or []]

    end = tl.get("end") or {}
    r._keys(end, ("after_last_word", "min_total", "max_total", "seconds"), "end")
    if "seconds" in end:
        duration = r._num(end["seconds"], "end.seconds", 1, prof["max_s"])
    else:
        if not voice:
            raise E("end needs 'seconds' when there is no narration")
        duration = voice["end"] + r._num(end.get("after_last_word", 1.5), "end.after_last_word", 0, 10)
        duration = max(duration, r._num(end.get("min_total", 0), "end.min_total", 0, prof["max_s"]))
    if voice and voice["end"] > duration + 1e-6:
        raise E(f"the video ends at {duration:.2f}s but the narration runs to {voice['end']:.2f}s")
    if duration > prof["max_s"]:
        raise E(f"{duration:.1f}s is over the {prof['max_s']:.0f}s limit of profile {tl['profile']}")
    total_frames = int(round(duration * fps))

    captions = None
    if tl.get("captions"):
        c = tl["captions"]
        r._keys(c, ("src", "preset"), "captions")
        if c.get("preset", "short") != "short":
            raise E("captions.preset must be 'short'")
        src = r.resolve_src(c.get("src"), root, "captions")
        with open(src, encoding="utf-8") as f:
            cues = r.parse_srt(f.read())
        if cues and cues[-1][1] / 1000 > duration + 1e-6:
            raise E("captions run past the end of the video")
        captions = {"src": src, "cues": [(a / 1000, b / 1000, t) for a, b, t in cues]}

    shots_in = tl.get("shots")
    if not isinstance(shots_in, list) or not shots_in:
        raise E("timeline.shots must be a non-empty list")
    shots = []
    for i, s in enumerate(shots_in):
        where = f"shots[{i}]"
        r._keys(s, ("id", "beat", "start", "camera", "layers", "info", "focus", "claims", "visual_family"), where)
        start = _time(s.get("start", 0), words, f"{where}.start")
        if i == 0 and start != 0:
            raise E("the first shot must start at 0 - the first frame is the hook")
        cam = s.get("camera")
        if not isinstance(cam, dict):
            raise E(f"{where}.camera is required")
        r._keys(cam, ("from", "to", "center", "width_km", "ease"), f"{where}.camera")
        if "from" in cam:
            v0 = _view(cam["from"], grid, H / W, f"{where}.camera.from")
            v1 = _view(cam.get("to", cam["from"]), grid, H / W, f"{where}.camera.to")
        else:
            v0 = v1 = _view({"center": cam.get("center"), "width_km": cam.get("width_km")}, grid, H / W, f"{where}.camera")
        ease = cam.get("ease", "in_out")
        if ease not in ("in_out", "linear"):
            raise E(f"{where}.camera.ease must be 'in_out' or 'linear'")
        layers = [_layer(L, assets, grid, f"{where}.layers[{j}]") for j, L in enumerate(s.get("layers") or [])]
        if not any(L["type"] in ("image", "flip", "wipe") for L in layers):
            raise E(f"{where} needs an image, flip or wipe layer")
        focus = None
        if s.get("focus") is not None:
            f_ = s["focus"]
            if not (isinstance(f_, list) and len(f_) == 4):
                raise E(f"{where}.focus must be [lon_min, lat_min, lon_max, lat_max]")
            focus = f_
        family = _family(s.get("visual_family"), f"{where}.visual_family")
        shots.append({"id": str(s.get("id", f"s{i + 1}")), "beat": s.get("beat"), "start": start, "views": (v0, v1),
                      "ease": ease, "layers": layers, "info": s.get("info"), "focus": focus,
                      "claims": s.get("claims") or [], "family": family})
    tagged = [s["family"] is not None for s in shots]
    if any(tagged) and not all(tagged):
        raise E("visual_family is set on some shots but not on " +
                ", ".join(s["id"] for s in shots if s["family"] is None) + " - tag every shot or none")
    for a, b in zip(shots, shots[1:]):
        if b["start"] <= a["start"]:
            raise E(f"shot {b['id']} starts at or before shot {a['id']}")
    if shots[-1]["start"] >= duration:
        raise E(f"shot {shots[-1]['id']} starts after the end of the video")
    for a, b in zip(shots, shots[1:] + [None]):
        a["end"] = b["start"] if b else duration

    plan = {"version": 3, "profile": tl["profile"], "output": dict(prof, width=W, height=H, fps=fps,
            video_codec="h264", audio_codec="aac", audio_rate=48000, audio_channels=2, crf=18,
            preset="medium", audio_bitrate="192k"),
            "grid": grid, "assets": assets, "voice": voice, "words": words, "captions": captions,
            "shots": shots, "total_frames": total_frames, "expected_duration": round(total_frames / fps, 3)}
    plan["events"] = info_events(plan)
    plan["compositions"] = compositions(plan)
    plan["novelty"] = visual_novelty(plan)
    plan["warnings"] = lint(plan)
    return plan


def _layer(L, assets, grid, where):
    if not isinstance(L, dict) or L.get("type") not in LAYER_TYPES:
        raise E(f"{where}.type must be one of {LAYER_TYPES}")
    t = L["type"]
    allowed = {"image": ("asset",), "flip": ("assets", "step"), "wipe": ("from", "to"),
               "fill": ("mask", "minus", "color", "opacity"), "outline": ("mask", "color", "width"),
               "label": ("text", "sub", "slot", "style", "color"), "arrow": ("from", "to", "color", "width"),
               "pin": ("at", "text", "color")}[t]
    r._keys(L, ("type", "t", "info") + allowed + (("visual_family",) if t in ("image", "flip", "wipe") else ()), where)
    out = {"type": t, "info": L.get("info"), "family": _family(L.get("visual_family"), f"{where}.visual_family")}
    tw = L.get("t", [0, None])
    if not (isinstance(tw, list) and len(tw) == 2):
        raise E(f"{where}.t must be [start, end] in seconds from the shot start (end may be null)")
    out["t0"] = r._num(tw[0], f"{where}.t[0]", 0, 600)
    out["t1"] = None if tw[1] is None else r._num(tw[1], f"{where}.t[1]", out["t0"], 600)

    def asset(aid, kind, w):
        if aid not in assets or assets[aid]["kind"] != kind:
            raise E(f"{w}: '{aid}' is not a {kind} asset")
        return aid
    if t == "image":
        out["asset"] = asset(L.get("asset"), "image", f"{where}.asset")
    elif t == "flip":
        ids = L.get("assets")
        if not (isinstance(ids, list) and len(ids) >= 2):
            raise E(f"{where}.assets needs at least two images")
        out["assets"] = [asset(a, "image", f"{where}.assets") for a in ids]
        out["step"] = r._num(L.get("step", 0.6), f"{where}.step", 0.2, 5)
    elif t == "wipe":
        out["from"], out["to"] = asset(L.get("from"), "image", f"{where}.from"), asset(L.get("to"), "image", f"{where}.to")
        if out["t1"] is None:
            out["t1"] = out["t0"] + 1.0
    elif t in ("fill", "outline"):
        out["mask"] = asset(L.get("mask"), "mask", f"{where}.mask")
        out["minus"] = asset(L["minus"], "mask", f"{where}.minus") if L.get("minus") else None
        out["color"] = _color(L.get("color", "#FF7A28" if t == "fill" else "#FFFFFF"), f"{where}.color")
        out["opacity"] = r._num(L.get("opacity", 0.62), f"{where}.opacity", 0.05, 1)
        out["width"] = r._num(L.get("width", 4), f"{where}.width", 1, 20, int)
    elif t == "label":
        if not (isinstance(L.get("text"), str) and 0 < len(L["text"]) <= 40):
            raise E(f"{where}.text must be 1-40 characters")
        out["text"], out["sub"] = L["text"], L.get("sub")
        if out["sub"] is not None and not (isinstance(out["sub"], str) and len(out["sub"]) <= 48):
            raise E(f"{where}.sub must be at most 48 characters")
        out["slot"] = L.get("slot", "top")
        out["style"] = L.get("style", "year")
        if out["slot"] not in SLOTS or out["style"] not in STYLES:
            raise E(f"{where}: slot must be one of {sorted(SLOTS)}, style one of {sorted(STYLES)}")
        out["color"] = _color(L["color"], f"{where}.color") if L.get("color") else None
    elif t == "arrow":
        out["from"], out["to"] = grid.px(*_ll(L.get("from"), f"{where}.from")), grid.px(*_ll(L.get("to"), f"{where}.to"))
        out["color"] = _color(L.get("color", "#FFD23F"), f"{where}.color")
        out["width"] = r._num(L.get("width", 9), f"{where}.width", 2, 30, int)
    elif t == "pin":
        out["at"] = grid.px(*_ll(L.get("at"), f"{where}.at"))
        if not (isinstance(L.get("text"), str) and 0 < len(L["text"]) <= 32):
            raise E(f"{where}.text must be 1-32 characters")
        out["text"] = L["text"]
        out["color"] = _color(L.get("color", "#FFD23F"), f"{where}.color")
    return out


def info_events(plan):
    """Moments that put NEW information on screen (not decorative motion)."""
    ev = []
    for s in plan["shots"]:
        if s["info"]:
            ev.append({"t": round(s["start"], 3), "shot": s["id"], "what": s["info"]})
        for L in s["layers"]:
            t0 = s["start"] + L["t0"]
            if L["type"] == "flip":
                n = len(L["assets"])
                for k in range(1, n):
                    tk = t0 + k * L["step"]
                    if tk < s["end"]:
                        ev.append({"t": round(tk, 3), "shot": s["id"], "what": f"flip to {L['assets'][k]}"})
            elif L.get("info") and t0 < s["end"]:
                ev.append({"t": round(t0, 3), "shot": s["id"], "what": L["info"]})
    return sorted(ev, key=lambda e: e["t"])


# A composition is what the frame is built on - where the camera looks and how wide - plus the
# full-frame visual events that replace the whole picture. Text, year labels, numbers, captions,
# outlines, fills, arrows and pins are overlays: new information, never a new composition.
COMPOSITION = {"zoom_ratio": 1.5,      # a framing this much wider/narrower is a new view
               "shift": 0.35,          # ... or its centre moved this share of the wider view's width
               "merge_s": 0.75,        # resets closer than this read as one change
               "timelapse_min": 3, "timelapse_max_step": 1.0,   # a flip that counts as a timelapse
               "sample_s": 0.1,
               "first_10s_min": 3, "resets": (7, 10), "max_hold_s": 6.0}


def _same_view(a, b):
    C = COMPOSITION
    if abs(math.log(a[2] / b[2])) >= math.log(C["zoom_ratio"]):
        return False
    return math.hypot(a[0] - b[0], a[1] - b[1]) < C["shift"] * max(a[2], b[2])


def compositions(plan):
    """Composition resets: the moments the picture itself changes, not just what is drawn on it.

    A reset is a cut or camera move to a materially different view (zoom >= 1.5x or a relocation
    of >= 35 % of the frame), a full-frame wipe, or a multi-year timelapse (a flip of >= 3 dates).
    A continuous camera move counts once, however far it goes.
    Pure arithmetic on the timeline - no image analysis.
    """
    C = COMPOSITION
    resets, moving = [], []

    def add(t, shot, kind, what):
        if resets and t - resets[-1]["t"] < C["merge_s"]:
            resets[-1].setdefault("also", []).append(kind)
            return
        if t > 0:
            resets.append({"t": round(t, 3), "shot": shot["id"], "kind": kind, "what": what})

    anchor = None
    for s in plan["shots"]:
        events = []
        for L in s["layers"]:
            t0 = s["start"] + L["t0"]
            if t0 >= s["end"]:
                continue
            if L["type"] == "wipe":
                events.append((t0, "wipe", f"wipe {L['from']} -> {L['to']}"))
                moving.append((t0, min(s["start"] + L["t1"], s["end"])))
            elif (L["type"] == "flip" and len(L["assets"]) >= C["timelapse_min"]
                  and L["step"] <= C["timelapse_max_step"]):
                events.append((t0, "timelapse", f"timelapse of {len(L['assets'])} dates"))
                moving.append((t0, min(t0 + len(L["assets"]) * L["step"], s["end"])))
        events.sort(key=lambda e: e[0])
        if not _same_view(*s["views"]):
            moving.append((s["start"], s["end"]))
        moved = False
        n = max(1, int(math.ceil((s["end"] - s["start"]) / C["sample_s"])))
        for i in range(n + 1):
            t = min(s["start"] + i * C["sample_s"], s["end"])
            if i == n and s is not plan["shots"][-1]:
                break                       # the next shot's first frame takes over
            while events and events[0][0] <= t:
                e = events.pop(0)
                add(e[0], s, e[1], e[2])
            view = _camera(s, t)
            if anchor is None or moved:
                anchor = view       # one continuous move is one reset, however far it travels
            elif not _same_view(anchor, view):
                ratio = view[2] / anchor[2]
                what = (f"zoom {'in' if ratio < 1 else 'out'} x{max(ratio, 1 / ratio):.1f}"
                        if math.hypot(view[0] - anchor[0], view[1] - anchor[1]) < C["shift"] * max(view[2], anchor[2])
                        else "camera relocation")
                add(t, s, "cut" if i == 0 else "camera_move", what)
                anchor, moved = view, i > 0
        for e in events:
            add(e[0], s, e[1], e[2])

    duration = plan["expected_duration"]
    bounds = [0.0] + [x["t"] for x in resets] + [duration]
    segments = []
    for a, b in zip(bounds, bounds[1:]):
        free, cur = [], a          # longest stretch of the segment with nothing transforming
        for m0, m1 in sorted((max(a, m0), min(b, m1)) for m0, m1 in moving if m1 > a and m0 < b):
            if m0 > cur:
                free.append(m0 - cur)
            cur = max(cur, m1)
        free.append(b - cur)
        segments.append({"start": round(a, 3), "end": round(b, 3), "seconds": round(b - a, 3),
                         "static_hold": round(max(free), 3)})
    longest = max(segments, key=lambda x: x["static_hold"])
    return {"rule": "composition-reset/1", "thresholds": dict(COMPOSITION, resets=list(C["resets"])),
            "composition_resets": len(resets),
            "distinct_first_10s": 1 + sum(1 for x in resets if x["t"] < 10),
            "longest_static_hold": {"seconds": longest["static_hold"], "start": longest["start"], "end": longest["end"]},
            "resets": resets, "segments": segments}


def _family(v, where):
    if v is None:
        return None
    if not (isinstance(v, str) and re.fullmatch(r"[a-z0-9][a-z0-9_]{0,47}", v)):
        raise E(f"{where} must be a short snake_case name (a-z, 0-9, _; at most 48 characters)")
    return v


# A visual family is the visual idea on screen (empty_desert, lava_infrared, coastline_change), assigned
# by hand in the storyboard. A composition reset is a new picture; a visual novelty reset is a new idea.
# Zoom, relocation, crop, year, text or overlays on the same idea stay in the same family.
NOVELTY = {"first_10s_min": 3, "transitions_min": 6, "max_family_s": 10.0}


def visual_novelty(plan):
    """Visual-family transitions from the storyboard tags (shot `visual_family`, or a wipe/flip/image layer's
    own `visual_family` from its start). None when the timeline has no tags - the check is then skipped.
    Time inside a flip or wipe whose family is on screen is that family transforming, not dominating."""
    if plan["shots"][0]["family"] is None:
        return None
    marks, moving = [], []
    for s in plan["shots"]:
        marks.append((s["start"], 0, s["family"], s["id"]))
        for L in s["layers"]:
            t0 = s["start"] + L["t0"]
            if t0 >= s["end"]:
                continue
            if L["family"]:
                marks.append((t0, 1, L["family"], s["id"]))
            if L["type"] == "wipe":
                moving.append((t0, min(s["start"] + L["t1"], s["end"])))
            elif L["type"] == "flip":
                moving.append((t0, min(t0 + len(L["assets"]) * L["step"], s["end"])))
    marks.sort(key=lambda m: (m[0], m[1]))
    duration = plan["expected_duration"]
    runs = []
    for t, _, fam, sid in marks:
        if runs and runs[-1]["family"] == fam:
            continue
        if runs and t <= runs[-1]["start"] + 1e-9:
            runs[-1].update(family=fam, shot=sid)       # a layer family at the shot's own start wins
            continue
        runs.append({"start": t, "family": fam, "shot": sid})
    merged = []
    for r_ in runs:                                     # a family again after an override collapses back
        if merged and merged[-1]["family"] == r_["family"]:
            continue
        merged.append(r_)
    for a, b in zip(merged, merged[1:] + [None]):
        a["end"] = b["start"] if b else duration
    out = []
    for r_ in merged:
        free, cur = [], r_["start"]
        for m0, m1 in sorted((max(r_["start"], m0), min(r_["end"], m1)) for m0, m1 in moving
                             if m1 > r_["start"] and m0 < r_["end"]):
            if m0 > cur:
                free.append(m0 - cur)
            cur = max(cur, m1)
        free.append(r_["end"] - cur)
        out.append({"family": r_["family"], "start": round(r_["start"], 3), "end": round(r_["end"], 3),
                    "seconds": round(r_["end"] - r_["start"], 3), "untransformed": round(max(free), 3),
                    "shot": r_["shot"]})
    longest = max(out, key=lambda x: x["untransformed"])
    return {"rule": "visual-novelty/1", "thresholds": dict(NOVELTY),
            "transitions": len(out) - 1,
            "families": sorted({x["family"] for x in out}),
            "families_first_10s": len({x["family"] for x in out if x["start"] < 10}),
            "longest_family_run": {k: longest[k] for k in ("family", "start", "end", "untransformed")},
            "runs": out}


def lint(plan):
    w = []
    first10 = [e for e in plan["events"] if e["t"] < 10]
    if len(first10) < 5:
        w.append(f"only {len(first10)} information events in the first 10 s (target >= 5)")
    c, C = plan["compositions"], COMPOSITION
    if c["distinct_first_10s"] < C["first_10s_min"]:
        w.append(f"only {c['distinct_first_10s']} distinct compositions in the first 10 s "
                 f"(target >= {C['first_10s_min']}; new text or overlays on the same view do not count)")
    lo, hi = C["resets"]
    if not lo <= c["composition_resets"] <= hi:
        w.append(f"{c['composition_resets']} composition resets (target about {lo}-{hi})")
    v = plan.get("novelty")
    if v:
        N = NOVELTY
        if v["families_first_10s"] < N["first_10s_min"]:
            w.append(f"only {v['families_first_10s']} visual families in the first 10 s (target >= {N['first_10s_min']}; "
                     "a new view of the same visual idea is not new)")
        if v["transitions"] < N["transitions_min"]:
            w.append(f"{v['transitions']} visual-family transitions (target >= {N['transitions_min']})")
        lf = v["longest_family_run"]
        if lf["untransformed"] > N["max_family_s"]:
            w.append(f"visual family '{lf['family']}' holds {lf['untransformed']:.1f}s ({lf['start']:.1f}-{lf['end']:.1f}s, "
                     f"target <= {N['max_family_s']:.0f}s unless it is transforming)")
    h = c["longest_static_hold"]
    if h["seconds"] > C["max_hold_s"]:
        w.append(f"one composition holds {h['seconds']:.1f}s without a reset ({h['start']:.1f}-{h['end']:.1f}s, "
                 f"target <= {C['max_hold_s']:.0f}s)")
    if plan["words"] and plan["words"][0]["start"] > 0.5:
        w.append(f"narration starts at {plan['words'][0]['start']:.2f}s (target <= 0.5 s)")
    if plan["words"]:
        opener = " ".join(x["text"] for x in plan["words"][:4]).lower()
        if re.match(r"(this is|here we can see|landsat captured|welcome|in this video)", opener):
            w.append(f"banned opener: '{opener}'")
    prof = PROFILES[plan["profile"]]
    if not prof["min_s"] <= plan["expected_duration"] <= prof["max_s"]:
        w.append(f"duration {plan['expected_duration']}s outside {prof['min_s']}-{prof['max_s']} s")
    return w


# --- drawing -----------------------------------------------------------------------------------

class Fonts:
    def __init__(self):
        self.files = {}
        for style in ("Black", "Bold", "SemiBold", "Regular"):
            self.files[style] = r.font_file(f"Inter:style={style}") or r.font_file("DejaVu Sans:style=Bold")
        if not self.files["Bold"]:
            raise E("no usable font found (Inter or DejaVu Sans)")
        self.cache = {}

    def get(self, style, size):
        key = (style, size)
        if key not in self.cache:
            self.cache[key] = ImageFont.truetype(self.files.get(style) or self.files["Bold"], size)
        return self.cache[key]


class Painter:
    def __init__(self, plan):
        self.p = plan
        self.W, self.H = plan["output"]["width"], plan["output"]["height"]
        self.safe = plan["output"]["safe"]
        self.img = {}
        self.mask = {}
        for aid, a in plan["assets"].items():
            if a["kind"] == "image":
                self.img[aid] = Image.open(a["src"]).convert("RGB")
            else:
                self.mask[aid] = Image.open(a["src"]).convert("L")
        self.fonts = Fonts()
        self.caption_boxes = {}

    # camera ------------------------------------------------------------------------------------
    def box(self, shot, t):
        cx, cy, w = _camera(shot, t)
        h = w * self.H / self.W
        return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)

    def crop(self, aid, box):
        return np.asarray(self.img[aid].resize((self.W, self.H), Image.BILINEAR, box=box))

    def crop_mask(self, aid, box):
        return np.asarray(self.mask[aid].resize((self.W, self.H), Image.NEAREST, box=box)) > 127

    def to_screen(self, px, box):
        return ((px[0] - box[0]) / (box[2] - box[0]) * self.W, (px[1] - box[1]) / (box[3] - box[1]) * self.H)

    # frame -------------------------------------------------------------------------------------
    def frame(self, t):
        shot = next(s for s in reversed(self.p["shots"]) if s["start"] <= t + 1e-9)
        box = self.box(shot, t)
        lt = t - shot["start"]
        base, overlays, credits = None, [], []

        def active(L):
            return L["t0"] <= lt and (L["t1"] is None or lt < L["t1"])

        for L in shot["layers"]:
            if L["type"] == "image" and active(L):
                base = self.crop(L["asset"], box); credits.append(L["asset"])
            elif L["type"] == "flip":
                k = min(max(0, int((lt - L["t0"]) / L["step"])), len(L["assets"]) - 1)
                aid = L["assets"][k]
                base = self.crop(aid, box); credits.append(aid)
                overlays.append(("label", {"text": self.p["assets"][aid]["label"], "sub": None, "slot": "top",
                                           "style": "year", "color": None}, 1.0))
            elif L["type"] == "wipe":
                a, b = self.crop(L["from"], box), self.crop(L["to"], box)
                k = _ease((lt - L["t0"]) / max(L["t1"] - L["t0"], 1e-6), "in_out")   # 0 before t0: "from"
                xw = int(round(k * self.W))
                base = a.copy()
                base[:, :xw] = b[:, :xw]
                credits += [L["from"], L["to"]]
                if 0 < xw < self.W:
                    overlays.append(("divider", xw, 1.0))
                if lt < L["t1"] + 0.6:          # year labels while the comparison is happening
                    overlays.append(("wipe_labels", (L["to"], L["from"], xw), 1.0))
        if base is None:
            raise E(f"shot {shot['id']} has no visible image at {t:.2f}s")
        base = base.copy()
        for L in shot["layers"]:
            if L["type"] in ("fill", "outline") and lt >= L["t0"] and (L["t1"] is None or lt < L["t1"]):
                fade = 1.0 if L["t0"] == 0 else min(1.0, (lt - L["t0"]) / 0.35)   # t0 = 0: there from frame one
                m = self.crop_mask(L["mask"], box)
                if L["minus"]:
                    m = m & ~self.crop_mask(L["minus"], box)
                if L["type"] == "outline":
                    inner = m.copy()
                    inner[1:, :] &= m[:-1, :]; inner[:-1, :] &= m[1:, :]
                    inner[:, 1:] &= m[:, :-1]; inner[:, :-1] &= m[:, 1:]
                    m = m & ~inner
                    for _ in range(max(0, L["width"] // 2)):
                        g = m.copy()
                        g[1:, :] |= m[:-1, :]; g[:-1, :] |= m[1:, :]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
                        m = g
                    alpha = fade
                else:
                    alpha = L["opacity"] * fade
                col = np.array(L["color"], dtype=np.float32)
                base[m] = (base[m] * (1 - alpha) + col * alpha).astype(np.uint8)
            elif L["type"] in ("label", "arrow", "pin") and lt >= L["t0"] and (L["t1"] is None or lt < L["t1"]):
                overlays.append((L["type"], L, 1.0 if L["t0"] == 0 else min(1.0, (lt - L["t0"]) / 0.25)))

        im = Image.fromarray(base)
        d = ImageDraw.Draw(im, "RGBA")
        for kind, L, a in overlays:
            if kind == "divider":
                d.rectangle([L - 3, 0, L + 3, self.H], fill=(255, 255, 255, 230))
            elif kind == "wipe_labels":
                to_id, from_id, xw = L
                f = self.fonts.get("Black", 84)
                top = int(self.H * SLOTS["top"])
                if xw > 260:
                    self._text(d, self.p["assets"][to_id]["label"], f, (min(xw, self.W) // 2, top), (255, 255, 255))
                if self.W - xw > 260:
                    self._text(d, self.p["assets"][from_id]["label"], f, ((xw + self.W) // 2, top), (255, 255, 255))
            elif kind == "label":
                self._label(d, L, a)
            elif kind == "arrow":
                self._arrow(d, self.to_screen(L["from"], box), self.to_screen(L["to"], box), L, a)
            elif kind == "pin":
                self._pin(d, self.to_screen(L["at"], box), L, a)
        self._caption(d, shot, box, t)
        self._credit(d, credits)
        return im

    def _text(self, d, text, font, center, color, alpha=1.0, stroke=6):
        d.text(center, text, font=font, fill=color + (int(255 * alpha),), anchor="mm",
               stroke_width=stroke, stroke_fill=(0, 0, 0, int(220 * alpha)))

    def _label(self, d, L, a):
        size, style, color = STYLES[L["style"]]
        col = L["color"] or tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
        y = int(self.H * SLOTS[L["slot"]])
        font = self.fonts.get(style, size)
        while d.textlength(L["text"], font=font) > self.W * 0.82 and size > 30:
            size -= 6
            font = self.fonts.get(style, size)
        self._text(d, L["text"], font, (self.W // 2, y), col, a, stroke=max(4, size // 14))
        if L.get("sub"):
            sz, st, _ = STYLES["sub"]
            self._text(d, L["sub"], self.fonts.get(st, sz), (self.W // 2, y + size // 2 + 40), (255, 255, 255), a, 5)

    def _arrow(self, d, p0, p1, L, a):
        col = L["color"] + (int(255 * a),)
        k = min(1.0, a)
        tip = (p0[0] + (p1[0] - p0[0]) * k, p0[1] + (p1[1] - p0[1]) * k)
        d.line([p0, tip], fill=(0, 0, 0, int(160 * a)), width=L["width"] + 6)
        d.line([p0, tip], fill=col, width=L["width"])
        ang = math.atan2(tip[1] - p0[1], tip[0] - p0[0])
        hl = L["width"] * 4
        pts = [tip, (tip[0] - hl * math.cos(ang - 0.45), tip[1] - hl * math.sin(ang - 0.45)),
               (tip[0] - hl * math.cos(ang + 0.45), tip[1] - hl * math.sin(ang + 0.45))]
        d.polygon(pts, fill=col)

    def _pin(self, d, p, L, a):
        col = L["color"] + (int(255 * a),)
        x, y = p
        d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=col, outline=(0, 0, 0, int(200 * a)), width=4)
        font = self.fonts.get("Black", 52)
        tw = d.textlength(L["text"], font=font)
        tx = min(max(x, tw / 2 + 70), self.W * (1 - self.safe["right"]) - tw / 2 - 10)
        ty = y - 70 if y > self.H * 0.3 else y + 70
        self._text(d, L["text"], font, (int(tx), int(ty)), L["color"], a)

    def _caption(self, d, shot, box, t):
        cap = self.p["captions"]
        if not cap:
            return
        cue = next(((i, c) for i, c in enumerate(cap["cues"]) if c[0] <= t < c[1]), None)
        if cue is None:
            return
        idx = cue[0]
        src_lines = self._srt_lines(idx)
        size = CAPTION["size"]
        font = self.fonts.get("Black", size)
        while max(d.textlength(l, font=font) for l in src_lines) > CAPTION["max_width"] and size > 40:
            size -= 4
            font = self.fonts.get("Black", size)
        band = CAPTION["band_lower"]
        if shot["focus"]:
            g = self.p["grid"]
            x0, y0 = self.to_screen(g.px(shot["focus"][0], shot["focus"][3]), box)
            x1, y1 = self.to_screen(g.px(shot["focus"][2], shot["focus"][1]), box)
            lh = len(src_lines) * (size + CAPTION["line_gap"])
            cy = self.H * band
            if y0 < cy + lh / 2 and y1 > cy - lh / 2:
                band = CAPTION["band_upper"]
        lh = size + CAPTION["line_gap"]
        cy = self.H * band - (len(src_lines) - 1) * lh / 2
        for k, line in enumerate(src_lines):
            self._text(d, line, font, (self.W // 2, int(cy + k * lh)), (255, 255, 255), 1.0, CAPTION["stroke"])
        bw = max(d.textlength(l, font=font) for l in src_lines)
        self.caption_boxes.setdefault(idx, {"cue": idx + 1, "band": band,
            "box": [round(self.W / 2 - bw / 2), round(cy - size / 2), round(self.W / 2 + bw / 2),
                    round(cy + (len(src_lines) - 1) * lh + size / 2)], "font_size": size})

    def _srt_lines(self, idx):
        if not hasattr(self, "_lines"):
            with open(self.p["captions"]["src"], encoding="utf-8") as f:
                blocks = re.split(r"\n\s*\n", f.read().replace("\r\n", "\n").strip())
            self._lines = [b.split("\n")[2:] for b in blocks]
        return self._lines[idx]

    def _credit(self, d, ids):
        seen = []
        for aid in ids:
            c = self.p["assets"][aid]["credit"]
            if c and c not in seen:
                seen.append(c)
        if not seen:
            return
        text = " / ".join(seen)
        font = self.fonts.get("SemiBold", 30)
        x, y = int(self.W * self.safe["left"]), int(self.H * self.safe["top"]) + 6
        d.text((x, y), text, font=font, fill=(255, 255, 255, 215), stroke_width=3, stroke_fill=(0, 0, 0, 170))
        self.last_credit = text


# --- render ------------------------------------------------------------------------------------

def render(plan, out_path, overwrite=False, limits=None):
    limits = limits or r.LIMITS
    out_path = os.path.abspath(out_path)
    if not out_path.lower().endswith(".mp4"):
        raise E("--output must end in .mp4")
    if not os.path.isdir(os.path.dirname(out_path)):
        raise E(f"output directory does not exist: {os.path.dirname(out_path)}")
    if os.path.lexists(out_path) and not overwrite:
        raise E(f"{out_path} already exists; pass --overwrite to replace it", status="exists")
    o, voice, fps = plan["output"], plan["voice"], plan["output"]["fps"]
    W, H, n = o["width"], o["height"], plan["total_frames"]
    duration = n / fps
    max_bytes = limits["max_output_mb"] * 1048576
    painter = Painter(plan)          # fonts and imagery load before any file exists, so a failure here leaves nothing
    fd, tmp = tempfile.mkstemp(prefix=".render-", suffix=".partial.mp4", dir=os.path.dirname(out_path))
    os.close(fd)
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-"]
    if voice:
        cmd += ["-i", voice["src"]]
        chain = "[1:a]aformat=sample_fmts=fltp,"
        if voice["gain_db"]:
            chain += f"volume={voice['gain_db']:.2f}dB,"
        chain += "aresample=48000,aformat=channel_layouts=stereo"
        if voice["start"] > 0:
            chain += f",adelay=delays={round(voice['start'] * 48000)}S:all=1"
        cmd += ["-filter_complex", chain + ",apad[aout]", "-map", "0:v", "-map", "[aout]"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-preset", o["preset"], "-crf", str(o["crf"]), "-pix_fmt", "yuv420p",
            "-profile:v", "high", "-r", str(fps), "-g", str(fps * 2), "-c:a", "aac", "-b:a", "192k",
            "-ar", "48000", "-ac", "2", "-frames:v", str(n), "-t", f"{duration:.6f}", "-map_metadata", "-1",
            "-fflags", "+bitexact", "-flags:v", "+bitexact", "-flags:a", "+bitexact",
            "-movflags", "+faststart", "-fs", str(int(max_bytes)), "-f", "mp4", tmp]
    shot_credits = {}
    err = tempfile.TemporaryFile()
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=err)
    except FileNotFoundError:
        os.remove(tmp)
        raise E("ffmpeg is not installed or not on PATH")
    try:
        for i in range(n):
            t = i / fps
            im = painter.frame(t)
            sid = next(s["id"] for s in reversed(plan["shots"]) if s["start"] <= t + 1e-9)
            shot_credits.setdefault(sid, getattr(painter, "last_credit", None))
            proc.stdin.write(im.tobytes())
        proc.stdin.close()
        rc = proc.wait(timeout=limits["timeout_s"])
        if rc != 0:
            err.seek(0)
            raise E("ffmpeg failed: " + err.read().decode(errors="replace").strip()[-600:])
        size = os.path.getsize(tmp)
        if size >= max_bytes:
            raise E(f"output reached --max-output-mb {limits['max_output_mb']}; discarded")
        d = r.ffprobe_json(tmp)
        got = float((d.get("format") or {}).get("duration") or 0)
        if abs(got - duration) > max(0.25, 2 / fps):
            raise E(f"rendered duration {got:.3f}s does not match the plan's {duration:.3f}s")
        umask = os.umask(0); os.umask(umask)
        os.chmod(tmp, 0o666 & ~umask)
        manifest = _manifest(plan, painter, shot_credits, out_path)
        man_path = out_path[:-4] + ".manifest.json"
        with open(man_path + ".tmp", "w") as f:
            json.dump(manifest, f, indent=1, ensure_ascii=False)
        os.replace(tmp, out_path)
        os.replace(man_path + ".tmp", man_path)
    except BaseException:
        try:
            proc.kill()
        except Exception:
            pass
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    finally:
        err.close()
    return {"status": "ok", "output": out_path, "manifest": man_path, "bytes": size, "sha256": r._sha256(out_path),
            "duration": round(got, 3), "expected_duration": plan["expected_duration"], "profile": plan["profile"],
            "shots": len(plan["shots"]), "info_events_first_10s": sum(1 for e in plan["events"] if e["t"] < 10),
            "composition_resets": plan["compositions"]["composition_resets"],
            "distinct_compositions_first_10s": plan["compositions"]["distinct_first_10s"],
            **({"visual_family_transitions": plan["novelty"]["transitions"]} if plan.get("novelty") else {}),
            "warnings": plan["warnings"]}


def _manifest(plan, painter, shot_credits, out_path):
    return {"schema": "yt-render-manifest/1", "profile": plan["profile"], "output": os.path.basename(out_path),
            "width": plan["output"]["width"], "height": plan["output"]["height"], "fps": plan["output"]["fps"],
            "duration": plan["expected_duration"], "safe": plan["output"]["safe"],
            "first_word_start": plan["words"][0]["start"] if plan["words"] else None,
            "narration": ({k: plan["voice"][k] for k in ("start", "duration", "end", "gain_db", "voice_name", "voice_id")}
                          if plan["voice"] else None),
            "shots": [{"id": s["id"], "beat": s["beat"], "start": round(s["start"], 3), "end": round(s["end"], 3),
                       "info": s["info"], "claims": s["claims"], "layers": [L["type"] for L in s["layers"]],
                       "credit": shot_credits.get(s["id"]),
                       **({"visual_family": s["family"]} if s["family"] else {})} for s in plan["shots"]],
            "info_events": plan["events"],
            "compositions": plan["compositions"],
            **({"visual_novelty": plan["novelty"]} if plan.get("novelty") else {}),
            "caption_boxes": [painter.caption_boxes[k] for k in sorted(painter.caption_boxes)],
            "assets": {k: {"label": a["label"], "credit": a["credit"], "prov": a["prov"], "kind": a["kind"]}
                       for k, a in plan["assets"].items()},
            "warnings": plan["warnings"]}


def public_plan(plan):
    return {"version": 3, "profile": plan["profile"], "expected_duration": plan["expected_duration"],
            "total_frames": plan["total_frames"],
            "shots": [{"id": s["id"], "beat": s["beat"], "start": round(s["start"], 3), "end": round(s["end"], 3),
                       "layers": [L["type"] for L in s["layers"]]} for s in plan["shots"]],
            "info_events": plan["events"], "info_events_first_10s": sum(1 for e in plan["events"] if e["t"] < 10),
            "compositions": plan["compositions"],
            **({"visual_novelty": plan["novelty"]} if plan.get("novelty") else {}),
            "narration": ({k: plan["voice"][k] for k in ("duration", "end", "gain_db", "voice_name")}
                          if plan["voice"] else None),
            "warnings": plan["warnings"]}
