#!/usr/bin/env python3
"""scene_templates.py - ready-made animated map scenes. notes.json "scenes": [{"template": "...", "id": ..., "chapter": ..., ...params}] expand into the planner's "maps" entries
(camera move, wipe / flip, pins, arrows, labels that arrive on the narrator's words). Parameters and defaults come from motion_presets.json: no effect is programmed per episode.

Templates: coast_pin, pixel_zoom, timelapse, compare_instruments, measure, callout_zoom.   (a photo scene needs no template: a VERIFIED photo becomes a still with a slow camera move)
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
PRESETS = json.load(open(os.path.join(HERE, "motion_presets.json")))
REQUIRED = {
    "coast_pin": ("asset", "focus", "pin_at", "pin_text", "anchor_text"),
    "pixel_zoom": ("asset", "focus", "anchor_text", "pixel_m"),
    "timelapse": ("flip", "focus", "anchor_text"),
    "compare_instruments": ("wipe", "focus", "anchor_text", "wipe_at", "label_a", "label_b"),
    "measure": ("wipe", "focus", "anchor_text", "arrows"),
    "callout_zoom": ("asset", "focus", "anchor_text", "pin_text"),
}


class TemplateError(ValueError):
    pass


def expand(s):
    t = s.get("template")
    if t not in REQUIRED:
        raise TemplateError(f"unknown template {t!r}; known: {sorted(REQUIRED)}")
    miss = [k for k in REQUIRED[t] if k not in s]
    if miss:
        raise TemplateError(f"scene {s.get('id')}: template {t} needs {miss}")
    P = PRESETS
    base = {"id": s["id"], "chapter": s["chapter"], "claims": s.get("claims", []), "anchor_text": s["anchor_text"], "focus": s["focus"], "min_s": s.get("min_s", P["min_s"].get(t, 6))}
    for k in ("limit", "closes_chapter"):
        if k in s:
            base[k] = s[k]
    plate = {"plate": True}
    if t == "coast_pin":
        base.update(asset=s["asset"], zoom=s.get("zoom", P["camera"]["coast_zoom"]), focus_to=s.get("focus_to", s["focus"]),
                    marks=[{"type": "pin", "at": s["pin_at"], "text": s["pin_text"], "anchor_text": s.get("pin_anchor", s["anchor_text"]), "dur": s.get("pin_dur", 4.5)}])
    elif t == "pixel_zoom":
        z = s.get("zoom", P["camera"]["pixel_zoom"])
        base.update(asset=s["asset"], zoom=z, resample="nearest", label={"text": f"1 PIXEL = {s['pixel_m']} M OF GROUND", "style": "tag", "slot": "upper"})
        if s.get("arrow"):
            base["marks"] = [dict(P["arrow"], type="arrow", **s["arrow"], anchor_text=s.get("arrow_anchor", s["anchor_text"])),
                             {"type": "label", "text": s["arrow"].get("text", "5 PIXELS"), "style": "tag", "slot": "middle", "anchor_text": s.get("arrow_anchor", s["anchor_text"])}]
            base["marks"][0].pop("text", None)
    elif t == "timelapse":
        base.update(flip=s["flip"], step=s.get("step", P["flip_step_s"]), zoom=s.get("zoom", [11, 8]), marks=s.get("marks", []))
    elif t == "compare_instruments":
        base.update(wipe=s["wipe"], wipe_at=s["wipe_at"], zoom=s.get("zoom", P["camera"]["compare_zoom"]), resample="nearest",
                    marks=[{"type": "label", "text": s["label_a"], "style": "tag", "slot": "upper", "t": 0.6, "dur": 2.4},
                           {"type": "label", "text": s["label_b"], "sub": s.get("label_b_sub"), "style": "tag", "slot": "upper", "anchor_text": s["wipe_at"], "dur": None}])
        if not s.get("label_b_sub"):
            base["marks"][1].pop("sub")
    elif t == "measure":
        marks = []
        for a in s["arrows"]:
            marks.append(dict(P["arrow"], type="arrow", **{k: a[k] for k in ("from", "to")}, anchor_text=a["anchor_text"], dur=None))
            marks.append({"type": "label", "text": a["text"], "style": "tag", "slot": a.get("slot", "upper"), "anchor_text": a["anchor_text"], "dur": None})
        base.update(wipe=s["wipe"], wipe_at=s.get("wipe_at", s["arrows"][-1]["anchor_text"]), zoom=s.get("zoom", P["camera"]["measure_zoom"]), marks=marks)
    elif t == "callout_zoom":
        base.update(asset=s["asset"], zoom=s.get("zoom", P["camera"]["callout_zoom"]), marks=[{"type": "pin", "at": s.get("pin_at", s["focus"]), "text": s["pin_text"], "t": 0.6}])
        if s.get("label"):
            base["marks"].append({"type": "label", "text": s["label"], "sub": s.get("label_sub"), "style": "tag", "slot": "upper", "anchor_text": s.get("label_anchor", s["anchor_text"])})
            if not s.get("label_sub"):
                base["marks"][-1].pop("sub")
    return base


def expand_all(scenes):
    return [expand(s) for s in scenes or []]
