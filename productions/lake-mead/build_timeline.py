#!/usr/bin/env python3
"""Lake Mead Short - storyboard -> timeline v3.

    python3 build_timeline.py predicted   # animatic: word times predicted at 13.6 chars/s, no voice
    python3 build_timeline.py final       # word anchors resolved by yt-render from the real voice.json

The storyboard below is the single source: shot order, word anchors, camera, layers, claims.
"""
import json, re, sys

sys.path.insert(0, "/home/user/YouTube-Agent/.claude/skills/yt-geo")
import geostack as g

GRID = json.load(open("stack/grid.json"))


def ll(px, py):
    lon, lat = g.utm_to_lonlat(GRID["x0"] + px * 30, GRID["y_top"] - py * 30, GRID["epsg"])
    return [round(float(lon), 5), round(float(lat), 5)]


MAIN = [-114.43, 36.30]                     # Overton Arm + Virgin Basin, the iconic V
ARM = [-114.385, 36.455]
BOULDER = [-114.70, 36.20]
RIVER_CAM = ll(2690, 1700)
RIVER_PIN = ll(2780, 1590)
TIP_2000, TIP_2026 = [-114.40402, 36.51408], [-114.36724, 36.3835]
CREDIT = {"y2000": "Landsat 7 · USGS", "y2005": "Landsat 5 · USGS", "y2010": "Landsat 5 · USGS",
          "y2015": "Landsat 8 · USGS", "y2022": "Landsat 9 · USGS", "y2026": "Landsat 9 · USGS"}

ASSETS = {k: {"src": f"stack/{k}.png", "label": k[1:], "credit": v, "prov": f"stack/provenance.json#{k}"}
          for k, v in CREDIT.items()}
ASSETS["water2000"] = {"src": "geo/water_y2000.png", "kind": "mask", "prov": "geo/water_y2000.json"}
ASSETS["water2026"] = {"src": "geo/water_y2026.png", "kind": "mask", "prov": "geo/water_y2026.json"}

LOST = {"type": "fill", "mask": "water2000", "minus": "water2026", "color": "#FF7A28", "opacity": 0.66}
SHORE = {"type": "outline", "mask": "water2000", "color": "#FFFFFF", "width": 4}
CAM = lambda c, w0, w1=None: ({"center": c, "width_km": w0} if w1 is None else
                              {"from": {"center": c, "width_km": w0}, "to": {"center": c, "width_km": w1}})

SHOTS = [
 dict(id="hook", beat="hook", word=0, info="2026 lake with 2000 water shown in orange", claims=["C1"],
      camera=CAM(MAIN, 38, 35),
      layers=[{"type": "image", "asset": "y2026"}, LOST,
              {"type": "label", "text": "2026", "style": "year", "slot": "top"},
              {"type": "label", "text": "ORANGE = WATER IN 2000", "style": "tag", "slot": "upper",
               "t": [0.5, None], "info": "legend: orange = water in 2000"},
              dict(SHORE, t=[1.6, None], info="2000 shoreline drawn")]),
 dict(id="wipe2000", beat="proof", word=7, info="wipe back to the full lake of 2000", claims=["C2", "M1"],
      camera=CAM(MAIN, 35),
      layers=[{"type": "wipe", "from": "y2026", "to": "y2000", "t": [0.0, 0.8]},
              {"type": "label", "text": "LAKE MEAD", "style": "tag", "slot": "upper", "t": [0.3, None],
               "sub": "AMERICA'S LARGEST RESERVOIR", "info": "name + largest reservoir"}]),
 dict(id="flip", beat="proof", word=12, offset=-0.9, info=None, claims=["M1"], camera=CAM(MAIN, 36, 33),
      layers=[{"type": "flip", "assets": ["y2000", "y2005", "y2010", "y2015", "y2022", "y2026"], "step": 0.42}]),
 dict(id="drop", beat="escalation", word=15, info="-160 ft since 2000", claims=["C3"], camera=CAM(MAIN, 33, 31),
      layers=[{"type": "image", "asset": "y2026"}, SHORE,
              {"type": "label", "text": "-160 FT", "style": "stat", "slot": "top", "sub": "≈ 49 M LOWER SINCE 2000"}]),
 dict(id="arm", beat="escalation", word=25, info="zoom to the northern arm", claims=["C4"], camera=CAM(ARM, 19, 17),
      layers=[{"type": "wipe", "from": "y2000", "to": "y2026", "t": [0.15, 1.1], "info": "2000 -> 2026 wipe on the arm"},
              {"type": "arrow", "from": TIP_2000, "to": TIP_2026, "t": [1.1, None], "info": "retreat arrow"},
              {"type": "label", "text": "≈ 9 MILES", "style": "stat", "slot": "top", "sub": "≈ 14 KM OF ARM GONE",
               "t": [1.3, None]}]),
 dict(id="half", beat="escalation", word=33, info="about half the water surface gone", claims=["C11"],
      camera=CAM(MAIN, 31, 38),
      layers=[{"type": "image", "asset": "y2026"}, LOST, SHORE,
              {"type": "label", "text": "≈ HALF THE WATER", "style": "stat", "slot": "top", "sub": "SURFACE GONE SINCE 2000"}]),
 dict(id="record2022", beat="escalation", word=41, info="2022 record low near Hoover Dam basin", claims=["C5"],
      camera=CAM(BOULDER, 27, 24),
      layers=[{"type": "image", "asset": "y2022"}, SHORE,
              {"type": "label", "text": "2022", "style": "year", "slot": "top"},
              {"type": "label", "text": "RECORD LOW", "style": "tag", "slot": "upper", "sub": "LOWEST SINCE THE 1930s",
               "color": "#FF6B6B", "t": [0.4, None], "info": "record low tag"}]),
 dict(id="river", beat="explanation", word=56, info="the Colorado River flowing in", claims=["C6"],
      camera={"from": {"center": ll(2600, 1700), "width_km": 24}, "to": {"center": RIVER_CAM, "width_km": 21}},
      layers=[{"type": "image", "asset": "y2026"},
              {"type": "pin", "at": RIVER_PIN, "text": "COLORADO RIVER", "t": [0.3, None], "info": "river pinned"},
              {"type": "label", "text": "DROUGHT", "style": "tag", "slot": "top", "sub": "SINCE 2000", "t": [0.9, None]}]),
 dict(id="budget", beat="explanation", word=64, info="out > in", claims=["C7"], camera=CAM(ll(2560, 1690), 21),
      layers=[{"type": "flip", "assets": ["y2000", "y2010", "y2022"], "step": 0.9},
              {"type": "label", "text": "OUT > IN", "style": "stat", "slot": "upper", "sub": "OUTFLOW + EVAPORATION > INFLOW",
               "t": [0.5, None], "info": "water budget"}]),
 dict(id="people", beat="explanation", word=75, info="40 million people", claims=["C8"], camera=CAM(MAIN, 30, 37),
      layers=[{"type": "image", "asset": "y2026"}, SHORE,
              {"type": "label", "text": "40 MILLION", "style": "stat", "slot": "top", "sub": "PEOPLE ON THIS RIVER SYSTEM"}]),
 dict(id="record2026", beat="payoff", word=85, info="August 2026 new record low", claims=["C9"], camera=CAM(MAIN, 37, 33),
      layers=[{"type": "image", "asset": "y2026"}, LOST,
              {"type": "label", "text": "AUG 2026", "style": "year", "slot": "top"},
              {"type": "label", "text": "NEW RECORD LOW", "style": "tag", "slot": "upper", "color": "#FF6B6B",
               "t": [0.3, None], "info": "new record"}]),
 dict(id="line", beat="payoff", word=97, info="the white line = 2000 shoreline", claims=["C10"], camera=CAM(MAIN, 30, 38),
      layers=[{"type": "image", "asset": "y2026"}, dict(SHORE, width=6),
              {"type": "label", "text": "2000 SHORELINE", "style": "tag", "slot": "upper", "t": [0.4, None]}]),
]


def predicted_words(text, cps=13.6):
    words, t = [], 0.0
    for m in re.finditer(r"\S+", text):
        w = m.group()
        d = (len(w) + 1) / cps
        pause = 0.35 if w[-1] in ".?!" else (0.15 if w[-1] == "," else 0)
        words.append({"text": w, "start": round(t, 3), "end": round(t + d, 3)})
        t += d + pause
    return words


def build(mode):
    shots = []
    for s in SHOTS:
        s = dict(s)
        anchor = {"word": s.pop("word")}
        if "offset" in s:
            anchor["offset"] = s.pop("offset")
        s["start"] = 0 if anchor["word"] == 0 else anchor
        shots.append(s)
    tl = {"version": 3, "profile": "short", "grid": "stack/grid.json", "assets": ASSETS,
          "meta": {"title": "Lake Mead - Everything in orange", "claims": "story/claims.json",
                   "provenance": "stack/provenance.json"},
          "shots": shots}
    if mode == "final":
        tl["voice"] = {"src": "voice/narration.wav", "meta": "voice/narration.voice.json"}
        tl["captions"] = {"src": "captions/captions.srt", "preset": "short"}
        tl["end"] = {"after_last_word": 1.6, "min_total": 45.5}
        out = "timeline.json"
    else:
        text = open("voice/predicted_text.txt").read()
        words = predicted_words(text)
        for s in shots:
            if isinstance(s["start"], dict):
                a = s["start"]
                s["start"] = round(max(0.0, words[a["word"]]["start"] + a.get("offset", 0)), 3)
        tl["end"] = {"seconds": round(max(words[-1]["end"] + 1.6, 45.5), 3)}
        out = "timeline_animatic.json"
    json.dump(tl, open(out, "w"), indent=1, ensure_ascii=False)
    print(out, len(shots), "shots")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "predicted")
