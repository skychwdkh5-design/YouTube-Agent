"""Storyboard v2 for the Kilauea 2018 Short - timeline v3 with PREDICTED times (no narration yet).
Shot starts come from story/predicted_timing.json (Adam's measured 2.395 words/s from Lake Mead).
After TTS, starts become word anchors from Adam's real timings."""
import json
T = json.load(open("story/predicted_timing.json"))["starts"]
CR = "Landsat 8 · USGS"
A = {d: {"src": f"stack/{d}.png", "label": lab, "credit": CR} for d, lab in
     [("d20180327", "MAR 2018"), ("d20180514", "MAY 14, 2018"), ("d20180530", "MAY 30, 2018"),
      ("d20190226", "FEB 2019"), ("d20190720", "JUL 2019")]}
BAY, SUMMIT, NEWLAND = [-154.826, 19.503], [-155.281, 19.4055], [-154.815, 19.488]
def cam(c0, w0, c1=None, w1=None, ease="in_out"):
    if c1 is None: return {"center": c0, "width_km": w0}
    return {"from": {"center": c0, "width_km": w0}, "to": {"center": c1, "width_km": w1}, "ease": ease}
def lab(text, style="tag", slot="top", sub=None, t0=0.0, t1=None, info=None):
    L = {"type": "label", "text": text, "style": style, "slot": slot, "t": [t0, t1]}
    if sub: L["sub"] = sub
    if info: L["info"] = info
    return L
def pin(at, text, t0=0.0, t1=None, info=None):
    P = {"type": "pin", "at": at, "text": text, "t": [t0, t1]}
    if info: P["info"] = info
    return P
shots = [
 {"id": "S1_hook", "beat": "hook", "start": 0.0, "info": "after-image: black lava where Kapoho Bay was",
  "camera": cam([-154.845, 19.49], 7.0, [-154.842, 19.492], 6.3),
  "layers": [{"type": "image", "asset": "d20190226"},
             lab("A BAY — GONE", "stat", info="hook claim"),
             pin(BAY, "KAPOHO BAY", 0.5, info="where the bay was"),
             lab("FEB 2019", "tag", "upper", t0=1.2, info="image date")]},
 {"id": "S2_proof", "beat": "proof", "start": T[1], "info": "wipe back to the bay before the eruption",
  "camera": cam([-154.842, 19.492], 6.3),
  "layers": [{"type": "wipe", "from": "d20190226", "to": "d20180327", "t": [0.0, 0.8]},
             pin(BAY, "KAPOHO BAY", 0.9)]},
 {"id": "S3_eruption", "beat": "proof", "start": T[2], "info": "zoom out: four-date timelapse of the eruption",
  "camera": cam([-154.88, 19.465], 12.0, [-154.88, 19.468], 11.0),
  "layers": [{"type": "flip", "assets": ["d20180327", "d20180514", "d20180530", "d20190226"], "step": 0.9},
             lab("ERUPTION BEGINS", "tag", "middle", sub="May 3, 2018", t0=0.2, t1=3.6, info="start date"),
             lab("24 FISSURES", "stat", "middle", t0=3.8, info="24 fissures")]},
 {"id": "S4_heat", "beat": "escalation", "start": T[3], "info": "zoom in 2x: eruption zone, heat in infrared",
  "camera": cam([-154.885, 19.485], 6.0, [-154.885, 19.485], 5.5),
  "layers": [{"type": "image", "asset": "d20180530"},
             lab("HEAT SEEN IN INFRARED", "tag", "top", sub="Landsat 8 · May 30, 2018", info="infrared heat")]},
 {"id": "S5_flow", "beat": "escalation", "start": T[4], "info": "camera follows the lava path east to the sea",
  "camera": cam([-154.89, 19.478], 6.5, [-154.845, 19.492], 7.5, "linear"),
  "layers": [{"type": "image", "asset": "d20190226"},
             {"type": "arrow", "from": [-154.872, 19.482], "to": [-154.832, 19.499], "t": [0.8, None], "info": "path to the ocean"},
             lab("TO THE OCEAN", "tag", "top", sub="Landsat 8 · Feb 2019", t0=0.3, info="flow reached the sea")]},
 {"id": "S6_bay", "beat": "escalation", "start": T[5], "info": "tight on the bay: before -> after",
  "camera": cam([-154.84, 19.497], 5.5),
  "layers": [{"type": "wipe", "from": "d20180327", "to": "d20190226", "t": [2.5, 3.3]},
             lab("JUNE 3: LAVA ARRIVES", "tag", "upper", t0=0.0, t1=2.5, info="june 3"),
             lab("JUNE 7: BAY GONE", "stat", "upper", t0=3.9, info="june 7"),
             pin(BAY, "KAPOHO BAY")]},
 {"id": "S7_scale", "beat": "escalation", "start": T[6], "info": "pull back: the whole lava field",
  "camera": cam([-154.93, 19.41], 18.0, [-154.93, 19.41], 16.5),
  "layers": [{"type": "image", "asset": "d20190226"},
             lab("13.7 SQ MI OF LAVA", "stat", "top", sub="35.5 km²", info="area"),
             lab("1,839 STRUCTURES", "stat", "upper", sub="destroyed", t0=2.2, info="structures")]},
 {"id": "S8_rift", "beat": "explanation", "start": T[7], "info": "travel 30 km up the rift to the summit",
  "camera": cam([-154.95, 19.405], 18.0, [-155.245, 19.405], 12.0, "in_out"),
  "layers": [{"type": "image", "asset": "d20190720"},
             lab("MEANWHILE, AT THE SUMMIT", "tag", "top", t0=1.5, info="summit")]},
 {"id": "S9_collapse", "beat": "explanation", "start": T[8], "info": "summit crater before/after",
  "camera": cam([-155.278, 19.405], 6.0, [-155.278, 19.405], 5.4),
  "layers": [{"type": "wipe", "from": "d20180327", "to": "d20190720", "t": [0.3, 1.2]},
             pin(SUMMIT, "HALEMAʻUMAʻU", 0.0, 1.2),
             lab("−1,600 FT", "stat", "top", sub="caldera floor dropped (500+ m)", t0=1.8, info="collapse depth")]},
 {"id": "S10_newland", "beat": "payoff", "start": T[9], "info": "the new coastline",
  "camera": cam([-154.83, 19.482], 6.0, [-154.832, 19.481], 5.6),
  "layers": [{"type": "image", "asset": "d20190226"},
             lab("+875 ACRES", "stat", "top", sub="brand-new land", info="new land"),
             pin(NEWLAND, "NEW LAND", 0.4, info="where")]},
 {"id": "S11_owner", "beat": "payoff", "start": T[10], "info": "pull back over the new coast",
  "camera": cam([-154.835, 19.48], 6.5, [-154.88, 19.46], 13.0, "linear"),
  "layers": [{"type": "image", "asset": "d20190226"},
             lab("WHO OWNS IT?", "tag", "upper", t0=0.0, t1=3.6, info="question"),
             lab("THE STATE OF HAWAII", "stat", "upper", sub="1977 court ruling", t0=3.6, info="answer")]},
]
tl = {"version": 3, "profile": "short", "grid": "stack/grid.json", "assets": A, "shots": shots,
      "end": {"seconds": 48.6}, "meta": {"note": "storyboard v2, predicted times; no narration yet"}}
json.dump(tl, open("timeline_storyboard.json", "w"), indent=1, ensure_ascii=False)
