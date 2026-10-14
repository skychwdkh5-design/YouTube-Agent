"""Director: render a production's AUTOMATIC storyboard (timeline v3 from tools/autopilot/storyboard.py) together with its narration plan
(story/motion_plan.json from orbitalatlas.semantic) through the motion engine - camera presets, transitions chosen by purpose, kinetic captions,
impact cards, number cards, year tags, region highlights, routes, comparisons, a focus manager and an opening plane tilt.

    python3 -m orbitalatlas.director render SLUG OUT.mp4 [--start S --end E] [--size 1920x1080] [--workers 4] [--audio WAV] [--report]
    python3 -m orbitalatlas.director stills SLUG OUT_PREFIX --times 1.0,4.2,...

Rules it applies (each decision is written to the report, nothing is hand-timed):
  * shots/cameras/pins/wipes/flips come from timeline.json; times of graphics come from the narration words (plan events), not from code
  * single focus: an impact card (revelation) or a number card owns the screen; captions overlapping it are hidden (no duplicated numbers), the map
    dims behind a number card; at most one focus at a time (impact > number)
  * a storyboard 'stat' label is replaced by the number card built from the same spoken number (never both); an image date label is shown once per
    image change as a HUD stamp, not on every shot
  * transitions by purpose: image date changes -> light wipe; next shot opens on a revelation -> flash dip; big scale jump on the same image ->
    cinematic push; otherwise a cut. Shot timing stays locked to the narration (the outgoing shot is extended under the transition)
  * places with a region definition in the stack get a RegionTint; two pinned places in a 'route' sentence get a RouteArrow with the great-circle
    distance; two pinned places compared ('than') get a CompareLink with the narration's comparative word
  * satellite pixels: grade 'evidence_safe' only; every annotation carries source/validation"""
# effect-reuse-checked: demo/visual_v2.py hand-placed its effects; this is the generic event->overlay mapping for any storyboard timeline.
import argparse
import json
import math
import os
import re
import sys

import numpy as np
from PIL import Image

from . import camera_presets as CP, captions as C, fx, grade, interact as IX, regions, semantic, transitions as TR, typeset as TS
from .layers import Scene, SourceChip
from .plane import PlaneTilt
from .sequence import Program, Sequence, Shot, render_video

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".claude", "skills", "yt-geo"))
import geostack as G  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
UNITS = {"feet": "FEET", "foot": "FEET", "miles": "MILES", "mile": "MILES", "km": "KM", "kilometers": "KM", "kilometres": "KM", "meters": "M", "metres": "M",
         "percent": "%", "acres": "ACRES", "people": "PEOPLE", "million": "MILLION", "billion": "BILLION"}
STOP = {"a", "an", "the", "its", "his", "her", "their", "this", "that", "of"}
TAIL_STOP = {"and", "or", "but", "so", "it", "is", "was", "than", "in", "on", "at", "to", "from", "by", "for", "with", "more", "less", "says", "said", "usgs", "nasa"}   # a number card unit stops before these


def _norm(w): return re.sub(r"[^\w%$.,']", "", w)


def _load(path):
    with open(path, encoding="utf-8") as f: return json.load(f)


def haversine_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


class Geo:
    def __init__(self, grid, size):
        self.g, self.size = grid, size
    def px(self, lonlat):
        x, y = G.lonlat_to_utm(lonlat[0], lonlat[1], self.g["epsg"]); return ((float(x) - self.g["x0"]) / self.g["pixel_m"], (self.g["y_top"] - float(y)) / self.g["pixel_m"])
    def height(self, width_km): return width_km * 1000.0 / self.g["pixel_m"] * self.size[1] / self.size[0]


class Window:
    """a Scene seen over [start, end] of ITS OWN time axis (so two scenes split from one shot share one continuous camera)."""
    def __init__(self, scene, start, end): self.scene, self._s, self._e, self.size, self.name, self.reg = scene, start, end, scene.size, scene.name, scene.reg
    @property
    def start(self): return self._s
    @property
    def end(self): return self._e
    @property
    def camera(self): return self.scene.camera
    def render(self, t, **kw): return self.scene.render(t, **kw)
    def manifest(self): return self.scene.manifest() if hasattr(self.scene, "manifest") else []


def camera_keys(geo, cam, dur, log):
    c0, h0 = geo.px(cam["from"]["center"]), geo.height(cam["from"]["width_km"]); c1, h1 = geo.px(cam["to"]["center"]), geo.height(cam["to"]["width_km"])
    if abs(h1 / h0 - 1) < 0.05 and math.hypot(c1[0] - c0[0], c1[1] - c0[1]) < 5:
        log("camera: creep (same view)"); return CP.creep(0.0, max(dur, 0.5), c0, h0, 0.05)
    r = h1 / h0
    if r < 0.5:
        log(f"camera: snap zoom in x{1 / r:.1f}"); return CP.join(CP.hold(0.0, c0, h0), CP.snap_zoom(0.15, c0, h0, c1, h1, dur=0.7), CP.creep(0.85, max(0.4, dur - 0.7), c1, h1, 0.04))
    if r > 2.0:
        log(f"camera: scale change out x{r:.1f}"); return CP.join(CP.scale_change(0.0, c0, h0, c1, h1, dur=min(1.4, max(0.6, dur * 0.5)), pullback=1.0), CP.creep(min(1.4, max(0.6, dur * 0.5)), max(0.4, dur - 1.4), c1, h1, 0.03))
    md = min(1.6, max(0.6, dur * 0.55)); log(f"camera: smooth move {md:.1f}s")
    return CP.join(CP.smooth_zoom(0.0, md, c0, h0, c1, h1), CP.creep(md, max(0.4, dur - md), c1, h1, 0.04))


def _direction(words, i):
    nxt = [re.sub(r"[^\w]", "", w["text"]).lower() for w in words[i:i + 7]]
    d = [x for x in ("north", "south", "east", "west") if x in nxt]
    return d[0] if d and "to" in nxt else None


def _words_between(words, t0, t1): return [w for w in words if t0 - 1e-3 <= w["start"] < t1]


def build(prod, size=(1920, 1080), t_range=None, log=print, opening_tilt=True, min_focus_gap=5.0, max_focus_per_min=4):
    tl = _load(os.path.join(prod, "timeline.json")); mp_path = os.path.join(prod, (tl.get("meta") or {}).get("motion_plan", "story/motion_plan.json"))
    plan = _load(mp_path); words = plan["words"]; report = dict(decisions=[], skipped=[], focus=[], intended_changes=[])
    note = lambda kind, **kw: report["decisions"].append(dict(kind=kind, **kw))
    grid = _load(os.path.join(prod, tl["grid"])); geo = Geo(grid, size)
    manifest = _load(os.path.join(prod, "assets", "manifest.json")); stack = (manifest.get("stacks") or [{}])[0]
    pins = {k: tuple(v) for k, v in (stack.get("pins") or {}).items()}; regdef = stack.get("regions") or {}
    imgs = {}
    def image(aid):
        if aid not in imgs: imgs[aid] = Image.open(os.path.join(prod, tl["assets"][aid]["src"])).convert("RGB")
        return imgs[aid]
    shots = tl["shots"]; end = tl["end"]["seconds"]
    starts = [s["start"] for s in shots] + [end]
    # ---- focus manager: impact (revelation) and number cards, from the plan
    cards = C.make_cards(words); focus = []
    for e in plan["events"]:
        if e["kind"] == "revelation":
            sent = [w for w in words[e["word"]:] ]; j = next((k for k, w in enumerate(sent) if re.search(r"[.!?]$", w["text"])), len(sent) - 1); sent = sent[:j + 1]
            col = next((k for k, w in enumerate(sent) if w["text"].endswith(":")), None)
            body = sent[col + 1:] if col is not None and col + 1 < len(sent) else sent[-min(4, len(sent)):]
            kicker = " ".join(re.sub(r"[:,]$", "", w["text"]) for w in sent[:col + 1][-4:]) if col is not None else None
            if len(body) > 5:                                 # a long statement is not a card: it stays a (rate-limited) style C caption
                report["skipped"].append(dict(kind="impact", t0=round(body[0]["start"], 2), why=f"{len(body)} words; cards hold at most 5")); continue
            focus.append(dict(kind="impact", t0=body[0]["start"] - 0.12, t1=body[-1]["end"] + 0.45, words=body, kicker=kicker, word=e["word"]))
        elif e["kind"] == "number":
            i = e["word"]; val = _norm(words[i]["text"]).rstrip(".,"); nxt = _norm(words[i + 1]["text"]).lower().rstrip(".,") if i + 1 < len(words) else ""
            unit = UNITS.get(nxt, "")
            card = next(c for c in cards if any(w is words[i] or (w["start"] == words[i]["start"] and w["text"] == words[i]["text"]) for w in c["words"]))
            s0 = max((k + 1 for k in range(0, i) if re.search(r"[.!?]$", words[k]["text"])), default=0)      # the number's own sentence, up to the number
            pre = [w["text"] for w in words[s0:i]]
            if pre and pre[0].lower() in ("and", "but", "so", "then"): pre = pre[1:]
            colon = max((k + 1 for k, x in enumerate(pre) if x.endswith(":")), default=0); pre = pre[colon:]      # 'the measurements are plain: IN JULY 2022, ...'
            kicker = " ".join(pre[-9:]).strip().rstrip(",") or "measured"
            tail = []                                                                         # content words after the unit inside the clause ('HIGHER', 'CUBIC YARDS')
            ends = re.search(r"[.!?,;:]$", words[i + 1]["text"] if unit else words[i]["text"])   # the unit (or number) closes the clause: no tail
            for w in ([] if ends else words[i + (2 if unit else 1):i + 5]):
                x = re.sub(r"[^\w%$']", "", w["text"])
                if not x or x.lower() in STOP or x.lower() in TAIL_STOP or re.search(r"\d", x): break
                tail.append(x.upper())
                if re.search(r"[.!?,;:]$", w["text"]): break
            unit = " ".join([unit] + tail[:3]).strip()
            focus.append(dict(kind="number", t0=words[i]["start"] - 0.15, t1=max(words[i]["end"] + 1.4, card["t1"] + 0.4), value=val, unit=unit, kicker=kicker, word=i))
    focus.sort(key=lambda f: f["t0"]); kept = []
    for f in focus:
        near = [k for k in kept if f["t0"] - k["t1"] < min_focus_gap and f["t0"] >= k["t0"]]
        per_min = [k for k in kept if f["t0"] - k["t0"] < 60.0]
        if f["kind"] == "number" and (near or len(per_min) >= max_focus_per_min):          # pacing: the number stays in the caption (style D) instead
            report["skipped"].append(dict(kind="number", t0=round(f["t0"], 2), why="focus pacing (gap/limit); shown in the caption")); continue
        clash = [k for k in kept if not (f["t1"] <= k["t0"] or f["t0"] >= k["t1"])]
        if clash:
            if f["kind"] == "impact" and all(k["kind"] == "number" for k in clash):
                for k in clash: kept.remove(k); report["skipped"].append(dict(kind=k["kind"], t0=k["t0"], why="overlaps a revelation card"))
            else:
                report["skipped"].append(dict(kind=f["kind"], t0=f["t0"], why="another focus element is on screen")); continue
        kept.append(f)
    focus = kept; report["focus"] = [dict(kind=f["kind"], t0=round(f["t0"], 2), t1=round(f["t1"], 2)) for f in focus]
    hidden = {ci for ci, c in enumerate(cards) for f in focus if min(c["t1"], f["t1"]) - max(c["t0"], f["t0"]) > 0.25 * (c["t1"] - c["t0"])}
    styles = list(plan["cards"][i]["style"] if i < len(plan["cards"]) else "A" for i in range(len(cards)))
    for ci, c in enumerate(cards):                                  # an impact card carries that revelation: its caption must not be a second style C
        if styles[ci] == "C" and any(f["kind"] == "impact" and c["t0"] <= f["t1"] and c["t1"] >= f["t0"] - 3.0 for f in focus):
            styles[ci] = "B"; note("captions", t=c["t0"], why="style C handed to the impact card")
    inten = plan.get("intensity") or semantic.intensity(words, plan["events"])
    def level(t):
        for it in inten:
            if it["t0"] - 0.3 <= t <= it["t1"] + 0.3: return it["label"]
        return "normal"
    for ci, c in enumerate(cards):                                  # calm explanations: restrained captions (A), no kinetic word pops
        if level(c["t0"]) == "calm" and styles[ci] in ("B", "C"): styles[ci] = "A"
    caps = C.WordCaptions(cards, styles, source=plan.get("timing_source", "provider"), hidden=hidden)
    in_focus = lambda t: any(f["t0"] - 0.05 <= t <= f["t1"] for f in focus)
    lifted, last_punch, dates = set(), -9.0, []
    report["intensity"] = inten; report["opening_tilt"] = bool(opening_tilt)
    # ---- shots
    seq_shots, trans = [], []; prev_img = None; region_cache = {}
    for si, sh in enumerate(shots):
        t_s, t_e = starts[si], starts[si + 1]; dur = t_e - t_s
        if t_range and (t_e <= t_range[0] or t_s >= t_range[1]): continue
        L = {l["type"]: l for l in sh["layers"]}; decisions = []
        base = (L.get("image") or {}).get("asset") or (L.get("wipe") or {}).get("from") or ((L.get("flip") or {}).get("assets") or [None])[0]
        if not base or "camera" not in sh: report["skipped"].append(dict(kind="shot", id=sh["id"], why="not a geo shot (stills/video are not rendered by the director yet)")); continue
        keys = camera_keys(geo, sh["camera"], dur + 0.8, decisions.append)
        if si == 0 and opening_tilt and len(keys) > 1:                 # the plane lands first, THEN the camera moves (no smear inside the tilted plane)
            keys = [dict(keys[0], t=0.0)] + [dict(k, t=k["t"] + 1.6) for k in keys]; keys = CP.join(keys); decisions.append("camera move held until the plane has landed")
        if any(d_.startswith(("camera: snap", "camera: scale change")) for d_ in decisions):        # deliberate fast moves: declared to QA
            sh_ = 1.6 if any(d_.startswith("camera move held") for d_ in decisions) else 0.0
            report["intended_changes"] += [round(t_s + sh_ + k / 30, 3) for k in range(0, 45)]
        overlays = [IX.ParallaxDust((0, 0, grid["width"], grid["height"]), 0.0, dur + 1.0, alpha=0.22, seed=si + 3)]
        lift_here = {}                                                # place -> event: the caption word flies to the pin (energetic/normal, first mention, no focus card)
        for e in plan["events"]:
            if e["kind"] == "place" and t_s <= e["t"] < t_e and e.get("place") in pins and e["place"] not in lifted and not in_focus(e["t"]):
                if any(l["type"] == "pin" and (l.get("info") or "").lower() == e["place"].lower() for l in sh["layers"]): lift_here[e["place"]] = e
        for l in sh["layers"]:
            if l["type"] == "pin":
                name = l.get("info") or l["text"].title(); p = geo.px(l["at"])
                overlays.append(fx.MarkerPin(p, l["t"][0], label=None, source=f"stack pin {l['at']}", group=f"pin_{name}"))
                has_callout = any(e["kind"] == "place" and e.get("place") == name and t_s <= e["t"] < t_e and _direction(words, e["word"]) for e in plan["events"])
                if name not in lift_here and not has_callout: overlays.append(IX.FloatingLabel(p, name, l["t"][0] + 0.2, dur + 1.0, depth=0.06))   # one name label per place
        for name, e in lift_here.items():
            lifted.add(name); overlays.append(IX.KeywordLift(caps, e["t"], words[e["word"]]["text"], geo.px(pins[name]), t_s, t_e + 0.5, label=name))
            note("lift", t=e["t"], place=name)
        # semantic events that fall inside this shot
        for e in plan["events"]:
            if not (t_s <= e["t"] < t_e): continue
            lt = e["t"] - t_s
            if e["kind"] == "place" and e.get("place") in regdef:
                rd = regdef[e["place"]]; aid = base if not L.get("wipe") else L["wipe"]["to"]; key = (aid, e["place"])
                if key not in region_cache:
                    im = image(aid); f = 4; small = np.asarray(im.resize((im.width // f, im.height // f), Image.LANCZOS))
                    seeds = [(geo.px(s)[0] / f, geo.px(s)[1] / f) for s in rd["seeds"]]; (a, b), (c, d) = geo.px(rd["box"][:2]), geo.px(rd["box"][2:])
                    m = regions.seeded_region(small, seeds, box=(a / f, b / f, c / f, d / f), close=2, fill_holes=False, max_hole_px=700)
                    region_cache[key] = regions.to_mask_image(m, f)
                col = {"amber": fx.AMBER, "cyan": fx.CYAN, "violet": fx.PURPLE}.get(rd.get("color", "amber"), fx.AMBER)
                overlays.append(fx.RegionTint(region_cache[key], lt, color=col, settle_alpha=0.12, mask_scale=0.25, out_t=min(dur - 0.2, lt + 3.0),
                                              source=f"seeded water mask on {aid}", validation="annotation only; display shape, not a measurement"))
                note("region", t=e["t"], place=e["place"])
            if e["kind"] == "place" and e.get("place") in pins:
                nxt = [re.sub(r"[^\w]", "", w["text"]).lower() for w in words[e["word"]:e["word"] + 7]]
                dirs = [d for d in ("north", "south", "east", "west") if d in nxt]
                if dirs and "to" in nxt:
                    lifted_now = e["place"] in lift_here
                    overlays.append(fx.CalloutPanel(geo.px(pins[e["place"]]), lt + (0.8 if lifted_now else 0.1), min(dur - 0.15, lt + 2.6),
                                                    f"TO THE {dirs[0].upper()}" if lifted_now else e["place"], [] if lifted_now else [f"TO THE {dirs[0].upper()}"],
                                                    offset=(0.09, -0.2) if dirs[0] == "north" else (0.09, 0.05)))
                    note("callout", t=e["t"], place=e["place"], row=dirs[0])
            if e["kind"] == "route" and e.get("frm") in pins and e.get("to") in pins:
                km = haversine_km(pins[e["frm"]], pins[e["to"]]); lab = f"{round(km / 5) * 5:.0f} KM"
                arr = fx.RouteArrow(geo.px(pins[e["frm"]]), geo.px(pins[e["to"]]), lt, dur=1.2, bend=-0.2, label=lab, out_t=dur - 0.2,
                                    validation=f"presentation arrow; {km:.1f} km great-circle between the stack pins")
                overlays += [arr, fx.RouteLabel(arr, lt + 0.8, px=60, out_t=dur - 0.25)]; note("route", t=e["t"], frm=e["frm"], to=e["to"], km=round(km, 1))
            elif e["kind"] == "comparison":
                sent_end = next((k for k in range(e["word"], len(words)) if re.search(r"[.!?]$", words[k]["text"])), len(words) - 1)
                sent_start = max((k + 1 for k in range(0, e["word"]) if re.search(r"[.!?]$", words[k]["text"])), default=0)
                pl = []
                for k in range(sent_start, sent_end + 1):
                    p = words[k].get("place")
                    if p and p in pins and p not in pl: pl.append(p)
                wtxt = re.sub(r"[^\w]", "", words[e["word"]]["text"]).lower(); comp = re.sub(r"[^\w]", "", words[e["word"] - 1]["text"]) if wtxt == "than" and e["word"] > 0 else None
                if len(pl) >= 2 and comp:
                    overlays.append(fx.CompareLink(geo.px(pins[pl[0]]), geo.px(pins[pl[1]]), lt - 0.3, min(dur - 0.1, lt + 2.6), comp, validation="connector between two stack pins; the word is the narration's"))
                    note("compare", t=e["t"], places=pl[:2], word=comp)
                else: report["skipped"].append(dict(kind="comparison", t=e["t"], why="needs two pinned places and an adjective before 'than'"))
        # image change -> HUD date stamp once
        img_now = base
        def stamp_txt(aid): a = tl["assets"][aid]; return f"{a.get('credit', '')} · {a.get('label', '')}"
        def chip(aid): return SourceChip((0.03, 0.935), f"{tl['assets'][aid].get('credit', '').upper()} · {tl['assets'][aid].get('label', '').upper()} · DISPLAY GRADE", 0.1)
        def stamp(aid, a0, a1, why=None, type_s=0.5):                            # every picture on screen carries ITS date (wipes and flips included)
            txt = stamp_txt(aid); note("image_stamp", t=t_s + a0, text=txt.upper(), asset=aid, **({"why": why} if why else {}))
            dates.append(dict(kind="image", t=round(t_s + a0, 2), text=txt.upper(), asset_label=tl["assets"][aid].get("label", ""), prov=tl["assets"][aid].get("prov") or tl["assets"][aid].get("date")))
            return IX.ImageStamp(txt, a0, a1, type_s=type_s)
        first = []
        if img_now != prev_img and not L.get("flip") and not any(f["kind"] == "impact" and f["t0"] <= t_s + 0.3 <= f["t1"] for f in focus):
            first.append(stamp(img_now, 0.15, min(dur, 3.0)))
        prev_img = (L.get("wipe") or {}).get("to") or ((L.get("flip") or {}).get("assets") or [img_now])[-1]
        sc = Scene(image(base), keys, size, overlays=overlays + first + [chip(base)], name=sh["id"], clamp=True, max_blur_samples=6, blur_threshold=10.0)
        parts = [(grade.Graded(sc, "evidence_safe", evidence=True), 0.0, dur)]
        if L.get("wipe"):
            w = L["wipe"]; tw = (w["t"][0] + w["t"][1]) / 2
            sc = Scene(image(base), keys, size, overlays=overlays + [x for x in first if x.t1 <= tw] + [IX.ImageStamp(stamp_txt(base), x.t0, min(x.t1, tw - 0.3)) for x in first if x.t1 > tw] + [chip(base)], name=sh["id"], clamp=True, max_blur_samples=6, blur_threshold=10.0)
            sc2 = Scene(image(w["to"]), keys, size, overlays=overlays + [stamp(w["to"], tw + 0.1, min(dur, tw + 2.8), "wipe to another date"), chip(w["to"])], name=sh["id"] + "_b", clamp=True, max_blur_samples=6, blur_threshold=10.0)
            parts = [(grade.Graded(sc, "evidence_safe", evidence=True), 0.0, tw + 0.3), (grade.Graded(sc2, "evidence_safe", evidence=True), tw - 0.3, dur)]
            decisions.append(f"wipe {w['from']}->{w['to']} at {tw:.2f}s")
        elif L.get("flip"):
            fl = L["flip"]; stp = fl["step"]; parts = []
            for k, aid in enumerate(fl["assets"]):
                s0 = k * stp; s1 = (k + 1) * stp if k < len(fl["assets"]) - 1 else dur
                ov = overlays + [stamp(aid, s0, min(s1, s0 + 3.0) if k == len(fl["assets"]) - 1 else s1, "flip image", type_s=0.0 if k else 0.5), chip(aid)]
                parts.append((grade.Graded(Scene(image(aid), keys, size, overlays=ov, name=f"{sh['id']}_{aid}", clamp=True, max_blur_samples=6, blur_threshold=10.0), "evidence_safe", evidence=True), s0, s1))
            decisions.append(f"flip {len(fl['assets'])} images, step {stp}s")
        hits = []
        for e in plan["events"]:
            if e["kind"] == "emphasis" and t_s + 0.4 <= e["t"] < t_e - 0.3 and level(e["t"]) == "energetic" and not in_focus(e["t"]) and e["t"] - last_punch > 2.5:
                hits.append((e["t"] - t_s, 0.045)); last_punch = e["t"]; note("punch", t=e["t"], word=e["text"])
        if hits: parts = [(IX.Punch(scn, hits), a0, a1) for scn, a0, a1 in parts]
        for k, (scn, a0, a1) in enumerate(parts):
            tr = None
            if k == 0 and seq_shots:                       # transition INTO this storyboard shot, chosen by purpose
                prev = shots[si - 1]; pl_ = {l["type"]: l for l in prev["layers"]}
                prev_last = (pl_.get("wipe") or {}).get("to") or ((pl_.get("flip") or {}).get("assets") or [None])[-1] or (pl_.get("image") or {}).get("asset")
                opens_reveal = any(f["kind"] == "impact" and t_s - 0.1 <= f["t0"] <= t_s + 0.8 for f in focus)
                ratio = geo.height(sh["camera"]["from"]["width_km"]) / geo.height(prev["camera"]["to"]["width_km"]) if "camera" in prev else 1.0
                why = "cut"
                if opens_reveal: tr, why = TR.FlashDip(0.3, peak=0.75), "flash dip: shot opens on a revelation"
                elif prev_last and prev_last != base: tr, why = TR.LightWipe(0.6), "light wipe: image date changes"
                elif ratio < 0.45 or ratio > 2.2: tr, why = TR.CinematicPush(duration=0.5), "cinematic push: scale jump"
                if tr is not None:
                    pd = seq_shots[-1].duration; tr.duration = min(tr.duration, pd * 0.45, (a1 - a0) * 0.45)
                    seq_shots[-1] = Shot(seq_shots[-1].scene, pd + tr.duration, seq_shots[-1].name)   # the outgoing shot plays on under the transition
                note("transition", t=t_s, why=why)
                if tr is None:
                    report["intended_changes"].append(round(t_s, 3))
                    if level(t_s) == "energetic": report.setdefault("_accents", []).append(t_s); note("accent", t=t_s, why="light sweep on an energetic cut")
            elif k > 0:
                tr = TR.LightWipe(0.6) if L.get("wipe") else None     # parts of a wipe overlap by 0.6 s already (window times); flips cut
            if seq_shots: trans.append(tr)
            win = Window(scn, a0, a1)
            if si == 0 and k == 0 and opening_tilt:
                win = Window(PlaneTilt(scn, [(0.0, 42.0), (1.7, 0.0)]), a0, a1); decisions.append("opening plane tilt 42 -> 0 deg")
            seq_shots.append(Shot(win, a1 - a0, f"{sh['id']}:{k}"))
        note("shot", id=sh["id"], t=t_s, dur=round(dur, 2), base=base, decisions=decisions)
    if not seq_shots: raise ValueError("no renderable geo shots in the requested range")
    seq = Sequence(seq_shots, trans)
    # ---- global overlays
    over = []
    for f in focus:
        if f["kind"] == "number":
            over += [TS.Dim(f["t0"], f["t1"], 0.42), TS.NumberCard(f["value"], f["unit"], f["kicker"], f["t0"], f["t1"])]
        else:
            over.append(TS.ImpactCard([dict(text=w["text"], start=w["start"]) for w in f["words"]], f["t0"], f["t1"], kicker=f["kicker"]))
    for e in plan["events"]:
        if e["kind"] == "year" and not any(f["t0"] - 0.3 <= e["t"] <= f["t1"] for f in focus):
            i = e["word"]; s0 = max((k + 1 for k in range(0, i) if re.search(r"[.!?]$", words[k]["text"])), default=0)
            s1 = next((k for k in range(i, len(words)) if re.search(r"[.!?]$", words[k]["text"])), len(words) - 1)
            if any(f["kind"] == "number" and s0 <= f.get("word", -1) <= s1 for f in focus):
                report["skipped"].append(dict(kind="event_year", t=e["t"], why="the number card of this sentence carries the date")); continue
            bare = lambda k: re.sub(r"[^\w]", "", words[k]["text"]).lower() if 0 <= k < len(words) else ""
            yi = i + 1 if bare(i) in semantic.MONTHS else i
            if bare(yi - 1) in ("from", "to") or bare(yi + 1) == "to" or bare(yi - 2) == "from":   # a range ('from 1985 to 2022'): the image stamps carry it
                report["skipped"].append(dict(kind="event_year", t=e["t"], why="year range; image stamps show the dates")); continue
            j = i - 1 if i > 0 and bare(i - 1) in semantic.MONTHS else i
            if j > s0 + 1 and re.fullmatch(r"\d{1,2}", bare(j - 1)) and bare(j - 2) in semantic.MONTHS: j -= 2        # 'on July 3, 2022'
            prep = j - 1 if j > s0 and bare(j - 1) in ("in", "by", "since", "until", "after", "before", "on") else j
            raw = words[s0:prep]
            cut = max((k + 1 for k, w in enumerate(raw) if re.search(r"[,;:]$", w["text"]) and k < len(raw) - 1), default=0); raw = raw[cut:]   # last clause only
            clause = [re.sub(r"[^\w']", "", w["text"]) for w in raw] or [re.sub(r"[^\w']", "", w["text"]) for w in words[yi + 1:s1 + 1]]
            keep = [x for x in clause if x and not re.search(r"\d", x) and x.lower() not in STOP and x.lower() not in ("and", "but", "so", "then")]
            lab = " ".join(keep[-4:])
            yr = re.sub(r"[^\d]", "", words[i + 1]["text"]) if re.sub(r"[^\w]", "", words[i]["text"]).lower() in semantic.MONTHS else re.sub(r"[^\d]", "", words[i]["text"])
            t1 = min([e["t"] + 1.8] + [f["t0"] - 0.05 for f in focus if f["t0"] > e["t"]])
            if yr and t1 - e["t"] > 0.6:
                over.append(IX.EventYear(yr, lab, e["t"], t1)); note("event_year", t=e["t"], year=yr, words=lab)
                img = next((d_ for d_ in reversed(dates) if d_["kind"] == "image" and d_["t"] <= e["t"]), None); img_label = img["asset_label"] if img else None
                if img and yr not in img_label:                       # an event year never stands alone over a picture of another date
                    over.append(IX.ImageStamp(img["text"], e["t"], t1, group="image_stamp_ctx")); note("image_stamp", t=e["t"], text=img["text"], why="shown with an event year of another date")
                dates.append(dict(kind="event", t=round(e["t"], 2), year=yr, words=lab, image_on_screen=img_label, differs=bool(img_label and yr not in img_label)))
    for ta in report.pop("_accents", []): over.append(fx.LightSweep(ta - 0.05, 0.45, strength=0.16))
    over.append(caps)
    t_off = min(starts[i] for i, sh in enumerate(shots) if not (t_range and (starts[i + 1] <= t_range[0] or starts[i] >= t_range[1])) and "camera" in sh) if t_range else 0.0
    prog = Program(seq, over, t_offset=t_off)
    for f in focus:                                              # card entrances/exits are deliberate hard changes
        report["intended_changes"] += [round(f["t0"] + k / 30, 3) for k in range(-1, 10)] + [round(f["t1"] + k / 30, 3) for k in range(-1, 12)]
    report["intended_changes"] = sorted(set(report["intended_changes"]))
    report["dates"] = dates
    ev_t = sorted({round(d["t"], 2) for d in report["decisions"] if d.get("t") is not None and d["kind"] != "captions"} | {round(f["t0"], 2) for f in focus} |
                  {round(f["t1"], 2) for f in focus} | {round(c["t0"], 2) for c in cards})
    pacing = []
    for it in inten:
        pts = [it["t0"]] + [x for x in ev_t if it["t0"] < x < it["t1"]] + [it["t1"]]; gap = max(b_ - a_ for a_, b_ in zip(pts, pts[1:]))
        limit = {"energetic": 3.0, "normal": 4.0, "calm": 6.0}[it["label"]]
        pacing.append(dict(t0=it["t0"], t1=it["t1"], label=it["label"], visual_events=len(pts) - 2, max_gap=round(gap, 2), limit=limit, ok=gap <= limit))
    report["pacing"] = pacing
    report.update(t_offset=t_off, timing_source=plan.get("timing_source"), hidden_cards=sorted(hidden), shots=len(seq_shots), duration=round(seq.duration, 3))
    return prog, report


class _LocalYearTag(TS.YearTag):
    """date stamp for the IMAGE (not the narration): '<label>' + credit, top-left, in shot time."""
    def __init__(self, year, label, credit, t0, t1): super().__init__(year, f"{label} · {credit}", t0, t1, xy=(0.04, 0.07), px=0.07, group="imagedate")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0]); ap.add_argument("cmd", choices=("render", "stills")); ap.add_argument("slug"); ap.add_argument("out")
    ap.add_argument("--start", type=float, default=None); ap.add_argument("--end", type=float, default=None); ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--workers", type=int, default=4); ap.add_argument("--audio", default=None); ap.add_argument("--sfx", action="store_true", help="add the synthesised sound design, ducked under --audio"); ap.add_argument("--times", default=""); ap.add_argument("--report", action="store_true")
    a = ap.parse_args(argv); size = tuple(int(x) for x in a.size.split("x"))
    prod = a.slug if os.path.isdir(a.slug) else os.path.join(ROOT, "productions", a.slug)
    rng = (a.start or 0.0, a.end or 1e9) if (a.start is not None or a.end is not None) else None
    prog, rep = build(prod, size, rng, log=lambda m: None)
    if a.report: print(json.dumps(rep, indent=1, default=str)[:6000])
    if a.cmd == "stills":
        for ts in a.times.split(","):
            prog.render(float(ts)).save(f"{a.out}_{float(ts):06.2f}.png")
        return 0
    audio = a.audio
    if a.sfx:
        from . import sfx as SFX
        if not a.audio: raise SystemExit("--sfx needs --audio (the narration the effects are ducked under)")
        cues = SFX.plan_cues(rep); mix_path = os.path.splitext(a.out)[0] + ".mix.wav"
        mrep = SFX.mix(a.audio, cues, prog.duration + 0.05, mix_path); rep["sfx"] = mrep; audio = mix_path
        print(f"sound design: {len(mrep['cues'])} cues, effects at least {mrep['margin_db_p5']} dB under the voice (5th percentile, while speaking)")
    n = render_video(prog, a.out, 30, a.workers, audio=audio)
    json.dump(rep, open(os.path.splitext(a.out)[0] + ".director.json", "w"), indent=1, default=str)
    print(f"{n} frames -> {a.out} ({prog.duration:.2f}s, timing {rep['timing_source']})"); return 0


if __name__ == "__main__":
    sys.exit(main())
