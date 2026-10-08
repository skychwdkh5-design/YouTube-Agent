"""Storyboard for the Wadi As-Sirhan Short - timeline v3 with PREDICTED times (no narration yet).
Line starts from story/predicted_timing.json (Adam's actual Kilauea rate, 2.21 words/s).
After TTS, starts become word anchors."""
import json
T = json.load(open("story/predicted_timing.json"))["starts"]
CR = {"y1987": "Landsat 5 · USGS", "y2000": "Landsat 5 · USGS", "y2008": "Landsat 5 · USGS",
      "y2015": "Landsat 8 · USGS", "y2025": "Landsat 8 · USGS"}
A = {k: {"src": f"stack/{k}.png", "label": k[1:], "credit": c} for k, c in CR.items()}
def cam(c0, w0, c1=None, w1=None, ease="in_out"):
    if c1 is None: return {"center": c0, "width_km": w0}
    return {"from": {"center": c0, "width_km": w0}, "to": {"center": c1, "width_km": w1}, "ease": ease}
def lab(text, style="tag", slot="top", sub=None, t0=0.0, t1=None, info=None):
    L = {"type": "label", "text": text, "style": style, "slot": slot, "t": [t0, t1]}
    if sub: L["sub"] = sub
    if info: L["info"] = info
    return L
CORE, CLOSE, WIDE, NE, EDGE = [38.30, 30.15], [38.33, 30.20], [38.44, 30.165], [38.70, 30.40], [38.47, 30.17]
def st(i, off=-0.2): return 0.0 if i == 0 else round(T[i] + off, 2)
shots = [
 {"id": "S1_hook", "beat": "hook", "start": st(0), "info": "thousands of green circles in sand (2015)",
  "camera": cam(EDGE, 14.0, EDGE, 13.0),
  "layers": [{"type": "image", "asset": "y2015"},
             lab("WATER FROM THE ICE AGE", "stat", "top", info="hook claim"),
             lab("SAUDI ARABIA", "tag", "upper", sub="Wadi As-Sirhan Basin", t0=1.0, info="place"),
             lab("2015", "tag", "middle", t0=2.0, info="image date")]},
 {"id": "S2_proof", "beat": "proof", "start": st(1), "info": "same view, 1987: empty desert",
  "camera": cam(EDGE, 13.0),
  "layers": [{"type": "wipe", "from": "y2015", "to": "y1987", "t": [0.0, 0.9]},
             lab("EMPTY DESERT", "stat", "upper", t0=1.6, info="empty")]},
 {"id": "S3_timelapse", "beat": "proof", "start": st(2), "info": "zoom out: 1987-2015 timelapse",
  "camera": cam([38.35, 30.12], 24.0, [38.35, 30.12], 22.0),
  "layers": [{"type": "flip", "assets": ["y1987", "y2000", "y2008", "y2015"], "step": 0.5}]},
 {"id": "S4_closeup", "beat": "proof", "start": st(3, 0.0), "info": "close-up: individual circles",
  "camera": cam(CLOSE, 7.0, CLOSE, 6.3),
  "layers": [{"type": "image", "asset": "y2015"},
             lab("≈1 KM WIDE", "stat", "top", sub="each circle is one farm", info="size"),
             lab("CENTER-PIVOT IRRIGATION", "tag", "upper", t0=2.6, info="mechanism")]},
 {"id": "S5_exports", "beat": "escalation", "start": st(4), "info": "whole basin, 2000",
  "camera": cam(WIDE, 46.0),
  "layers": [{"type": "image", "asset": "y2000"},
             lab("1992: 2,000,000+ TONS", "stat", "top", sub="of wheat exported (net)", t0=0.3, info="exports"),
             lab("2000 IMAGE", "tag", "upper", t0=1.2, info="image date")]},
 {"id": "S6_aquifer", "beat": "explanation", "start": st(5), "info": "fly to the northeastern fields",
  "camera": cam(WIDE, 46.0, NE, 14.0, "linear"),
  "layers": [{"type": "image", "asset": "y2015"},
             lab("WATER: ~20,000 YEARS OLD", "stat", "top", t0=0.3, info="fossil water"),
             lab("RAIN: 100–200 MM A YEAR", "tag", "upper", sub="about 4–8 inches · no recharge", t0=round(T[6] - T[5], 2), info="no recharge")]},
 {"id": "S7_policy", "beat": "explanation", "start": st(7), "info": "core fields, 2015 image",
  "camera": cam([38.35, 30.10], 20.0, [38.35, 30.10], 18.5),
  "layers": [{"type": "image", "asset": "y2015"},
             lab("2016: WHEAT PROGRAM ENDS", "stat", "top", sub="to save water (USDA)", t0=0.2, info="policy"),
             lab("2015 IMAGE", "tag", "upper", t0=1.0, info="image date")]},
 {"id": "S8_alfalfa", "beat": "payoff", "start": st(8), "info": "close-up 2025",
  "camera": cam([38.30, 30.20], 7.0, [38.30, 30.20], 6.3),
  "layers": [{"type": "image", "asset": "y2025"},
             lab("ALFALFA", "tag", "top", sub="2025 image", info="crop switch"),
             lab("3× THE WATER", "stat", "upper", sub="of wheat (USDA)", t0=2.2, info="3x")]},
 {"id": "S9_payoff", "beat": "payoff", "start": st(9), "info": "widest view: 1987 -> 2025, push in",
  "camera": cam(WIDE, 46.0, [38.35, 30.13], 28.0, "linear"),
  "layers": [{"type": "wipe", "from": "y1987", "to": "y2025", "t": [0.3, 1.5]},
             lab("~50 MORE YEARS", "stat", "upper", sub="of pumping (2016 estimate)", t0=2.0, t1=round(T[10] - T[9] + 0.1, 2), info="50 years"),
             lab("BUILT ON ICE AGE WATER", "stat", "upper", sub="it doesn't come back", t0=round(T[10] - T[9] + 0.2, 2), info="non-renewable")]},
]
tl = {"version": 3, "profile": "short", "grid": "stack/grid.json", "assets": A, "shots": shots,
      "end": {"seconds": round(json.load(open("story/predicted_timing.json"))["speech_end"] + 1.5, 2)},
      "meta": {"note": "storyboard, predicted times; no narration yet"}}
json.dump(tl, open("timeline_storyboard.json", "w"), indent=1, ensure_ascii=False)
