"""EP004 Jakarta - 2.5-D REVIEW build (Visual Engine V2C components: layers.Scene, captions, sfx, typeset). Narration + provider word times only.

    python3 productions/ep004-jakarta/build/review.py stills OUTDIR t [t ...] [--size 1280x720]
    python3 productions/ep004-jakarta/build/review.py render OUT.mp4 [--start S --end E] [--size 1280x720] [--workers 4] [--no-audio]

Composition only: scenes are orbitalatlas.layers.Scene over our own co-registered Landsat PNGs (assets/geo, tools/autopilot/landsat_color.py), the
Natural Earth locator, orbitalatlas.illustrate / subsidence3d diagrams and the small overlays in ep4kit.py. No ESA frame, no third-party media.
Every shot carries an evidence-class chip: REAL SATELLITE (Landsat, optical context - NOT subsidence), DATA CARD, ILLUSTRATION, STYLISED MAP.
"""
import json, os, re, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); PROD = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(PROD))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, ".claude", "skills", "yt-geo"))
from orbitalatlas import layers as L, sequence as SQ, transitions as TR, captions as C, camera_presets as CP, sfx as SFX, text as T, kinetic as K, geo as G, easing as E
from orbitalatlas import illustrate as IL, subsidence3d as S3D, director as D
import geostack as GS
import ep4kit as X

Image.MAX_IMAGE_PIXELS = None
FPS = 30
VOICE = json.load(open(os.path.join(PROD, "voice", "narration.voice.json")))
WORDS = VOICE["words"]; DUR = float(VOICE["duration"])
GRID = json.load(open(os.path.join(PROD, "assets", "geo", "grid.json")))
IMG = {"2026": os.path.join(PROD, "assets", "geo", "y2026.png"), "1990": os.path.join(PROD, "assets", "geo", "y1990.png")}
BEATS = json.load(open(os.path.join(HERE, "beats.json")))
_cache = {}
CH26 = "LANDSAT 8 · 14 SEP 2026 · OPTICAL, NOT SUBSIDENCE"
CH90 = "LANDSAT 5 · 9 JUL 1990 · OPTICAL, NOT SUBSIDENCE"
SRC = {"2026": "LANDSAT 8 · 14 SEP 2026", "1990": "LANDSAT 5 · 9 JUL 1990"}


def norm(w): return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))


def _beat_slice(n):
    i = sum(b["words"] for b in BEATS if b["n"] < n); return WORDS[i:i + BEATS[n - 1]["words"]]


def tw(n, text, nth=0, end=False):
    """start (or end) time of the nth occurrence of a word (or word sequence) inside beat n; raises if absent (anchors must exist)."""
    toks = [norm(x) for x in text.split()]; ws = _beat_slice(n); hits = []
    for i in range(len(ws) - len(toks) + 1):
        if all(norm(ws[i + j]["text"]) == toks[j] for j in range(len(toks))): hits.append(i)
    if len(hits) <= nth: raise KeyError(f"beat {n}: word {text!r} #{nth} not found")
    i = hits[nth]; return ws[i + len(toks) - 1]["end"] if end else ws[i]["start"]


def geo():
    if "geo" not in _cache: _cache["geo"] = D.Geo(GRID, SIZE)
    return _cache["geo"]


SIZE = (1280, 720)
VIEWS = {"whole": ((106.835, -6.21), 42), "bay": ((106.84, -6.13), 34), "city": ((106.83, -6.17), 22), "west": ((106.76, -6.12), 20), "east": ((106.90, -6.12), 20),
         "nw": ((106.74, -6.09), 22), "north": ((106.82, -6.105), 30), "harbor": ((106.885, -6.115), 15), "south": ((106.83, -6.27), 30), "coast_w": ((106.77, -6.10), 17), "centre": ((106.83, -6.19), 14)}
PINS = {"Tanjung Priok": (106.885, -6.100), "Mutiara Beach": (106.790, -6.107), "Pademangan": (106.840, -6.130), "West Cengkareng": (106.735, -6.150), "Halim airport": (106.891, -6.266), "Jakarta": (106.827, -6.175)}
# compass-direction markers: NOT map measurements; labelled 'general direction'
DIRS = {"west": (106.70, -6.17), "northwest coast": (106.745, -6.105)}


def view(name): c, w = VIEWS[name]; return {"center": list(c), "width_km": w}


VIEWS.update({"whole2": ((106.84, -6.17), 36), "north2": ((106.80, -6.11), 26), "kota": ((106.82, -6.13), 17), "priok": ((106.885, -6.105), 12), "east2": ((106.93, -6.14), 24), "bay2": ((106.82, -6.12), 30), "bay3": ((106.80, -6.095), 34), "sw": ((106.76, -6.25), 26)})


def camkeys(a, b, dur):
    """a, b = view names, or a, None with a LIST of (t_rel, view) in `a`: an eased path through several views (continuous motion, no hold)."""
    if isinstance(a, (list, tuple)): return camseq(a, dur)
    return D.camera_keys(geo(), {"from": view(a), "to": view(b)}, dur, lambda *_: None)


def camseq(path, dur):
    """[(t_rel, view_name), ...] -> camera keys; every segment eased in/out so the picture is never frozen between moves"""
    g = geo(); keys = []
    for i, (t, name) in enumerate(path):
        c, w = VIEWS[name]; keys.append(dict(t=float(t), center=tuple(g.px(c)), height=g.height(w), ease="in_out_cubic", rot=0.0))
    if keys[-1]["t"] < dur + 0.5: keys.append(dict(keys[-1], t=dur + 0.5, ease="linear"))
    return keys


def src_px(lonlat): return geo().px(lonlat)


def landsat(year, a, b, dur, overlays, name, dim=0.0):
    sc = L.Scene(IMG[year], camkeys(a, b, dur), size=SIZE, overlays=overlays, name=name)
    return X.Backdrop(sc, dim, name) if dim else sc


def chip(kind, text, t0=0.0, t1=None): return X.ClassChip(kind, text, t0, t1)


def hold_keys(a, dur): c, w = VIEWS[a]; return D.camera_keys(geo(), {"from": view(a), "to": view(a)}, dur, lambda *_: None)


# =====================================================================================================  SHOT BUILDERS
# each builder(t0, dur) -> (scene, ) ; overlay times are LOCAL (global time - t0)
def lt(t0): return lambda g: g - t0


def b01a(t0, dur):
    l = lt(t0); five = tw(1, "five"); spots = tw(1, "individual")
    ov = [chip("REAL SATELLITE", CH26), X.Stat("12", "CM / YEAR", "ESA radar: peak at individual spots", "ESA SENTINEL-1 · 2017-2018 · LINE OF SIGHT", l(five - 1.2), l(spots + 0.4), (0.06, 0.20), 0.15, X.AMBER, sub="≈ almost 5 inches · not a citywide average")]
    return landsat("2026", [(0, "whole"), (4.0, "bay"), (dur, "centre")], None, dur, ov, "b01a", 0.12)


def b01b(t0, dur):
    l = lt(t0); along = tw(1, "along"); p = src_px(PINS["Pademangan"])
    ov = [chip("ILLUSTRATION", "LINE OF SIGHT vs VERTICAL · SCHEMATIC"), X.LosView(p, l(along), l(t0 + dur), l(along + 2.0)),
          X.Tag("PEAK AT INDIVIDUAL SPOTS ≠ CITYWIDE AVERAGE", (0.06, 0.15), 0.1, l(along - 0.2), color=X.AMBER)]
    return landsat("2026", [(0, "city"), (4.0, "centre"), (dur, "coast_w")], None, dur, ov, "b01b", 0.28)


def b02(t0, dur):
    return X.OrbitDiagram(SIZE, dur + 0.4, "b02", t_label=(tw(2, "430") - t0 - 0.6, None), t_pass2=(tw(2, "pass", 0) - t0 - 0.2))


def b03(t0, dur):
    l = lt(t0); qs = [("1  Why is the ground falling?", tw(3, "Why", 0)), ("2  Why has one sinking area slowed?", tw(3, "Why", 1)), ("3  Why can't satellites see part of the coast?", tw(3, "Why", 2))]
    ov = [chip("REAL SATELLITE", CH26), X.Lines([(q, l(ts), X.WHITE if i < 2 else X.AMBER) for i, (q, ts) in enumerate(qs)], (0.06, 0.20), l(t0 + dur), px=0.040, head="THREE QUESTIONS")]
    return landsat("2026", [(0, "north"), (4.5, "west"), (dur - 1, "coast_w")], None, dur, ov, "b03", 0.25)


def b04a(t0, dur):                                                       # globe locator -> Java -> Jakarta (stylised map)
    if "globe" not in _cache:
        gd = G.GeoData(os.path.join(ROOT, "data", "natural_earth")); land = gd.land("10m"); ras = G.GeoRaster()
        ras.add(land, (-180, -90, 180, 90), 0.08); ras.add(land, (90, -14, 130, 12), 0.01); ras.add(land, (104.5, -8.5, 116.0, -5.0), 0.004); ras.add(land, (106.3, -6.6, 107.3, -5.7), 0.0008)
        _cache["globe"] = (gd, land, ras, gd.ring_lines(land))
    gd, land, ras, coast = _cache["globe"]; jk = (106.827, -6.175)
    keys = [dict(t=0.0, lon=100.0, lat=-2.0, span_km=9000, arc=0.0), dict(t=1.9, lon=108.0, lat=-6.5, span_km=2300, ease="smoother", arc=0.08), dict(t=3.5, lon=107.0, lat=-6.3, span_km=520, ease="smoother"), dict(t=dur + 0.5, lon=106.84, lat=-6.17, span_km=90, ease="out_cubic")]
    cam = G.GeoCamera(keys, SIZE, anchors={"jakarta": jk}); src = "Natural Earth 1:10M, public domain"
    ov = [G.GeoLabel((110.5, -7.4), "JAVA", 1.7, px_frac=0.05, color=T.THEME.text, out_t=dur - 0.3, source=src), G.GeoMarker(jk, 2.9, "JAKARTA", color=T.THEME.amber, label_offset=(70, -60), source=src + " (populated places)"), G.ScaleBar(1.2, out_t=dur)]
    sc = G.GeoScene(cam, ras, coast, size=SIZE, overlays=ov, name="b04a", max_blur_samples=8)
    sc_ov = [chip("STYLISED MAP", "NATURAL EARTH 1:10M · NOT SATELLITE IMAGERY")]
    sc.overlays = list(sc.overlays) + sc_ov
    return sc


def b04b(t0, dur):
    l = lt(t0); riv = tw(4, "rivers", 0, True); ppl = tw(4, "Almost"); pc = tw(4, "40")
    ov = [chip("REAL SATELLITE", CH26), X.Tag("RIVER DELTA · 13 NATURAL AND ARTIFICIAL RIVERS", (0.06, 0.15), l(tw(4, "built")), l(ppl - 0.2)),
          X.Stat("10.9", "MILLION PEOPLE", "Capital province, DKI Jakarta", "2022 STUDY (C37)", l(ppl + 0.1), l(pc - 1.4), (0.06, 0.20), 0.15, X.CYAN),
          X.Stat("40", "%", "of the city below sea level", "REPORTED 2021", l(pc - 0.6), l(t0 + dur - 0.2), (0.06, 0.20), 0.15, X.AMBER, sub="by some estimates")]
    return landsat("2026", [(0, "bay"), (6.0, "north2"), (dur - 0.5, "kota")], None, dur, ov, "b04b", 0.22)


def b05(t0, dur):
    """radar geometry for beats 5+6 (one continuous diagram; timeline mapped to the narration)"""
    a = lambda n, w, **k: tw(n, w, **k) - t0
    tl = dict(sat_in=(0.2, 1.4), beam=(1.2, 1.6), pulse1=(a(5, "microwave") - 0.3, a(5, "microwave") + 1.6), echo1=(a(5, "microwave") + 1.4, a(5, "microwave") + 3.0),
              wave1=(a(5, "where") - 0.2, a(5, "where") + 2.6), sink=(a(5, "later") - 0.2, a(5, "later") + 2.0), pulse2=(a(5, "compares") - 0.1, a(5, "compares") + 1.0),
              echo2=(a(5, "compares") + 1.0, a(5, "compares") + 2.2), wave2=(a(5, "If"), a(5, "If") + 3.0), shift=(a(5, "phase", nth=1) - 0.2, a(5, "phase", nth=1) + 1.2),
              push=(a(6, "measures") - 0.2, a(6, "measures") + 1.8), los=(a(6, "along") - 0.1, a(6, "along") + 1.6), vertical=(a(6, "not") - 0.1, a(6, "not") + 1.2))
    d = IL.RadarGeometryDiagram(SIZE, dur + 0.4, "b05", tl=tl); d.captions = []
    return d


def b09(t0, dur):
    a = lambda w, **k: tw(9, w, **k) - t0
    tl = dict(sat1_in=(0.2, 1.6), pulse1=(1.7, 2.3), echo1=(2.3, 2.9), sat1_out=(2.7, 3.9), pump=(a("pumped") - 0.3, a("pumped") + 1.5), sink=(a("compact") - 1.0, a("compact") + 2.4),
              sat2_in=(dur + 5, dur + 6), pulse2=(dur + 6, dur + 7), echo2=(dur + 7, dur + 8), extra=(dur + 8, dur + 9), los=(dur + 9, dur + 10), vertical=(dur + 10, dur + 11), fade=(dur + 12, dur + 13))
    class Cut(S3D.CutawayRadarDiagram):
        LABELS = [(a("pumped") + 0.1, a("pumped") + 3.3, "WATER IS PUMPED OUT", "well"), (a("compact") + 0.2, a("compact") + 3.6, "SOFT LAYERS COMPACT", "clay")]
        CAPTIONS = []
    d = Cut(SIZE, dur + 0.4, "b09", tl=tl)
    return d


def _illus(sc, kind="ILLUSTRATION", text="SCHEMATIC · NOT A MEASUREMENT"):
    sc.overlays = list(getattr(sc, "overlays", [])); return sc


def b09_ov(t0):
    l = lt(t0)
    return [X.HysteresisSketch(l(tw(9, "springs")) - 0.6, l(tw(9, "illustration", 0, True) + 2.2), l(tw(9, "springs") + 0.1), l(tw(9, "squeezed", 0) - 1.4), box=(0.55, 0.20, 0.97, 0.66))]


def b07(t0, dur):
    l = lt(t0)
    ov = [chip("ILLUSTRATION", "THREE SUSPECTS · IAHS STUDY + ESA CAPTION"),
          X.Suspects([("Groundwater pumping", "water taken from under the city", "well"), ("Weight of buildings & roads", "on soft, compressible ground", "build"), ("Settling of young river mud", "natural compaction", "mud")],
                     [l(tw(7, "Groundwater")), l(tw(7, "weight")), l(tw(7, "settling"))], l(t0 + dur), 0, l(tw(7, "ESA's")), box=(0.06, 0.24, 0.94, 0.72))]
    return landsat("2026", [(0, "bay"), (6.5, "whole2"), (13.0, "sw"), (dur, "kota")], None, dur, ov, "b07", 0.30)


def b08(t0, dur):
    l = lt(t0); p_n = src_px((106.84, -6.07)); p_w = src_px((106.70, -6.14)); n0 = tw(8, "north"); n1 = tw(8, "west")
    ov = [chip("REAL SATELLITE", CH26), X.Stat("64", "%", "of the province reached by piped water", "2022 STUDY (C37)", l(tw(8, "64") - 0.4), l(tw(8, "Its") - 0.2), (0.06, 0.20), 0.15, X.CYAN),
          X.Tag("PROPOSAL IN THE 2022 STUDY · NOT POLICY", (0.06, 0.15), l(tw(8, "Its")), l(t0 + dur)),
          X.Arrow(p_n, (0.0, 0.20), l(n0 - 0.1), l(t0 + dur), "north first"), X.Arrow(p_w, (0.20, 0.0), l(n1 - 0.1), l(t0 + dur), "west")]
    return landsat("2026", [(0, "whole"), (7.0, "north2"), (dur, "west")], None, dur, ov, "b08", 0.18)


def b10(t0, dur):
    l = lt(t0); wipe_at = tw(10, "decades") - 0.6
    def ovs(): return [chip("REAL SATELLITE", "LANDSAT 5 · 1990  →  LANDSAT 8 · 2026 · OPTICAL, NOT SUBSIDENCE", 0.75), X.Tag("1990", (0.06, 0.88), 0.0, l(wipe_at), color=X.CYAN, px=0.03), X.Tag("2026", (0.06, 0.88), l(wipe_at + 0.8), None, color=X.AMBER, px=0.03),
                       X.BandTimeline(l(tw(10, "Between") - 0.2), l(t0 + dur), l(tw(10, "1974")), l(tw(10, "three")), (0.06, 0.20, 0.94, 0.44))]
    a = L.Scene(IMG["1990"], camkeys([(0, "whole"), (7.0, "east2"), (dur, "city")], None, dur), size=SIZE, overlays=ovs(), name="b10a"); b = L.Scene(IMG["2026"], camkeys([(0, "whole"), (7.0, "east2"), (dur, "city")], None, dur), size=SIZE, overlays=ovs(), name="b10b")
    return X.Backdrop(X.Wipe(a, b, l(wipe_at), l(wipe_at + 1.6), name="b10"), 0.25, "b10")


def b11(t0, dur):
    l = lt(t0); t_pri = tw(11, "fastest") - t0 + 0.4; pins = [("west", DIRS["west"], tw(11, "west")), ("northwest coast", DIRS["northwest coast"], tw(11, "northwest")), ("Tanjung Priok", PINS["Tanjung Priok"], tw(11, "Tanjung"))]
    ov = [chip("REAL SATELLITE", CH26), X.Tag("3 HOTSPOTS · 2016-2024 · LINE OF SIGHT", (0.06, 0.15), l(tw(11, "recent")), l(tw(11, "fastest") - 0.1)),
          X.Stat("30", "MM / YEAR", "Fastest spot · ≈ 1 inch", "SENTINEL-1 ANALYSIS · 2016-2024 · LINE OF SIGHT", l(tw(11, "30") - 0.5), l(t0 + dur - 0.9), (0.06, 0.20), 0.15, X.AMBER)]
    for name, ll, ts in pins:
        named = name == "Tanjung Priok"
        ov.append(X.Ring(src_px(ll), l(ts - 0.1), l(tw(11, "fastest") - 0.1), name, X.AMBER if named else X.CYAN, 24, (0.05, -0.07) if named else (0.05, 0.07), sub=("named place" if named else "direction only")))
    return landsat("2026", [(0, "bay3"), (13.0, "bay2"), (t_pri, "priok"), (dur, "harbor")], None, dur, ov, "b11", 0.10)


def b12_stage(t0, dur):
    l = lt(t0); six = tw(12, "six"); worst = tw(12, "worst")
    ov = [chip("ILLUSTRATION", "SCHEMATIC COUNT · 2 STUDIES, 2 METHODS"), X.Bowls(l(tw(12, "But")), l(six - 0.2), l(worst), l(t0 + dur), box=(0.06, 0.22, 0.94, 0.50)),
          X.Tag("PREPRINT · RADAR + GPS · 2014-2025", (0.06, 0.15), l(tw(12, "preprint") - 0.2), l(t0 + dur), color=X.AMBER),
          X.Stat("7.7", "CM / YEAR", "Worst bowl · up to · ≈ 3 inches", "VERTICAL · PREPRINT (C39)", l(tw(12, "7.7") - 0.5), l(tw(12, "Across") - 0.1), (0.06, 0.54), 0.12, X.AMBER),
          X.Stat("1.1", "CM / YEAR", "Metro area · slow background sinking", "VERTICAL · PREPRINT · ONE CONTINUOUS GPS STATION", l(tw(12, "1.1") - 0.5), l(t0 + dur), (0.06, 0.54), 0.12, X.CYAN)]
    return landsat("2026", [(0, "whole"), (9.0, "city"), (18.0, "south"), (27.0, "bay"), (dur, "east2")], None, dur, ov, "b12", 0.35)


def b13(t0, dur):
    l = lt(t0)
    rows = [("North Jakarta", 4.9, l(tw(13, "North", 0) - 0.2)), ("West Jakarta", 4.8, l(tw(13, "4.8"))), ("Central Jakarta", 3.1, l(tw(13, "3.1"))), ("South", 2.8, l(tw(13, "2.8"))), ("East", 2.5, l(tw(13, "2.5")))]
    ov = [chip("DATA CARD", "RADAR STUDY · 2019-2020 · SENTINEL-1A"), X.Bars(rows, 5.5, "CM PER YEAR", "AVERAGE SINKING RATE BY CITY", "2019-2020 · ONE STUDY", l(tw(13, "average") - 0.3), l(t0 + dur), box=(0.06, 0.16, 0.66, 0.76), colors={"North Jakarta": X.AMBER, "West Jakarta": X.AMBER}, fmt="{:.1f}", note="LINE OF SIGHT OR VERTICAL: NOT STATED"),
          X.Arrow(src_px((106.83, -6.105)), (0.12, -0.10), l(tw(13, "mostly") - 0.1), l(t0 + dur), "coast & river mouths")]
    return landsat("2026", [(0, "whole"), (9.0, "east2"), (18.0, "north2"), (dur, "coast_w")], None, dur, ov, "b13", 0.25)


def b14(t0, dur):
    l = lt(t0); items = [("Mutiara Beach", tw(14, "Mutiara")), ("West Cengkareng", tw(14, "Cengkareng")), ("Pademangan", tw(14, "Pademangan"))]
    ov = [chip("REAL SATELLITE", CH26), X.Tag("DAMAGED ROADS REPORTED · 2019-2020 STUDY", (0.06, 0.15), l(tw(14, "reported") - 0.1), l(tw(14, "Other") - 0.1))]
    for i, (nm, ts) in enumerate(items): ov.append(X.Ring(src_px(PINS[nm]), l(ts - 0.1), l(tw(14, "Other") - 0.1), nm, X.AMBER, 22, [(0.04, -0.09), (-0.02, 0.09), (0.05, 0.08)][i]))
    ov.append(X.Lines([("Cracked buildings and roads", l(tw(14, "cracked")), X.WHITE), ("Changed river flow", l(tw(14, "changed")), X.WHITE), ("Bigger flooded areas", l(tw(14, "bigger")), X.WHITE), ("Drains that stop working", l(tw(14, "drains")), X.AMBER)],
                      (0.06, 0.20), l(t0 + dur), px=0.036, head="OTHER RESEARCHERS LIST"))
    return landsat("2026", [(0, "north"), (9.5, "bay2"), (dur, "east")], None, dur, ov, "b14", 0.12)


def b15a(t0, dur):
    return X.CoherenceDiagram(SIZE, dur + 0.4, "b15a", t_good=(tw(15, "trust") - t0, tw(15, "trust") - t0 + 1.2), t_bad=(tw(15, "next") - t0 - 0.3, tw(15, "next") - t0 + 0.9), t_thr=(tw(15, "coherence") - t0 - 0.2, tw(15, "coherence") - t0 + 0.8))


def b15b(t0, dur):
    l = lt(t0); p = src_px((106.80, -6.085))
    ov = [chip("REAL SATELLITE", CH26), X.Tag("PIXELS REMOVED ALONG THE NORTHERN COAST · EXTENT NOT SHOWN", (0.06, 0.15), l(tw(15, "removes") - 0.2), l(t0 + dur), color=X.RED),
          X.Arrow(src_px((106.76, -6.085)), (-0.20, 0.0), l(tw(15, "northern") - 0.2), l(t0 + dur), "radar goes blind here", X.RED), X.Arrow(src_px((106.86, -6.095)), (0.20, 0.0), l(tw(15, "northern") - 0.0), l(t0 + dur), "", X.RED)]
    return landsat("2026", "north", "coast_w", dur, ov, "b15b", 0.15)


def b16(t0, dur):
    l = lt(t0)
    ov = [chip("DATA CARD", "2016-2024 ANALYSIS · SENTINEL-1 vs GNSS"), X.Gauge(l(tw(16, "Scientists") - 0.2), l(t0 + dur - 0.9), l(tw(16, "1.64") - 0.3), l(tw(16, "typical") - 0.2), l(tw(16, "station", 1) - 0.1), box=(0.06, 0.18, 0.94, 0.74))]
    return landsat("2026", [(0, "city"), (7.0, "south"), (14.0, "centre"), (dur, "kota")], None, dur, ov, "b16", 0.30)


def b17(t0, dur):
    return X.TrendsDiagram(SIZE, dur + 0.4, "b17", t_west=(tw(17, "western") - t0 - 0.2, tw(17, "significantly", 0, True) - t0 + 0.2), t_others=(tw(17, "northwest") - t0 - 0.2, tw(17, "line", 0, True) - t0 + 0.3))


def b18(t0, dur):
    l = lt(t0)
    ov = [chip("REAL SATELLITE", CH26), X.Tag("2026 STUDY · ABSTRACT ONLY · FULL TEXT NOT READ", (0.06, 0.15), l(tw(18, "2026") - 0.1), l(t0 + dur), color=X.AMBER),
          X.Lines([("Some areas slowing", l(tw(18, "slowing")), X.WHITE), ("A few: localized uplift", l(tw(18, "localized") - 0.2), X.WHITE), ("The coast keeps sinking", l(tw(18, "coast") - 0.1), X.AMBER), ("Slowing ≠ coming back up", l(tw(18, "Slowing", 1) - 0.1), X.CYAN)],
                  (0.06, 0.22), l(t0 + dur), px=0.040, head="WHAT THE ABSTRACT REPORTS")]
    return landsat("2026", [(0, "north"), (6.0, "west"), (12.0, "whole2"), (dur, "bay")], None, dur, ov, "b18", 0.25)


def b19(t0, dur):
    l = lt(t0); f0, f1, f2 = tw(19, "flood"), tw(19, "377") - 0.5, tw(19, "From")
    ov = [chip("DATA CARD", "FLOODS · RAIN · SEA LEVEL"),
          X.Stat("70", "% +", "Of Jakarta submerged · flood of 2007", "REPORTED (C14)", l(tw(19, "70") - 0.6), l(f1 - 0.2), (0.06, 0.20), 0.15, X.CYAN),
          X.Stat("377", "MM", "Rain in one day · 31 Dec 2019 · ≈ 15 inches", "HALIM PERDANAKUSUMA GAUGE (C44)", l(f1), l(f2 - 0.2), (0.06, 0.20), 0.15, X.AMBER),
          X.Compare(l(f2), l(t0 + dur), l(tw(19, "3.1") - 0.3), l(tw(19, "worst") - 0.2), box=(0.06, 0.20, 0.94, 0.72))]
    return landsat("2026", [(0, "north"), (8.0, "harbor"), (17.0, "west"), (26.0, "whole"), (dur, "bay2")], None, dur, ov, "b19", 0.30)


def b20(t0, dur):
    sink0 = tw(20, "model") - t0 - 4.5
    return X.DykeDiagram(SIZE, dur + 0.4, "b20", t_over=(tw(20, "seawater") - t0, tw(20, "seawater") - t0 + 3.5), t_sink=(tw(20, "model") - t0, tw(20, "2040") - t0 + 0.6), t_model=(tw(20, "model") - t0 - 0.2, None))


def b21(t0, dur):
    l = lt(t0)
    cols = [("Satellites prove", X.CYAN, [("Parts of Jakarta are sinking, at different speeds", l(tw(21, "parts") - 0.1)), ("Some of that sinking has slowed", l(tw(21, "slowed", 0) - 1.3))]),
            ("They cannot prove", X.AMBER, [("What happens where the radar goes blind", l(tw(21, "happens") - 0.1)), ("Exactly what drives each bowl", l(tw(21, "exactly") - 0.1))])]
    last = tw(21, "check")
    ov = [chip("REAL SATELLITE", CH26), X.CheckList(cols, l(last - 0.6), box=(0.06, 0.20, 0.94, 0.70)),
          X.Lines([("What was measured", l(tw(21, "What", 2)) if False else l(last + 0.3), X.WHITE), ("When", l(tw(21, "when") - 0.1), X.CYAN), ("In which direction", l(tw(21, "direction") - 0.5), X.AMBER)], (0.06, 0.22), l(t0 + dur + 1), px=0.050, head="CHECK THE LABEL")]
    return landsat("2026", [(0, "whole"), (8.0, "bay"), (16.0, "north2"), (dur, "whole")], None, dur + 0.4, ov, "b21", 0.25)


# =====================================================================================================  PROGRAMME
def shot_plan():
    """[(t_start, builder, transition_into_next (None = cut or (kind, seconds)))] in narration time; t_end of a shot = next start."""
    B = {b["n"]: b for b in BEATS}; S = []
    t = lambda n: B[n]["t0"]
    S.append((0.0, b01a, ("dissolve", 0.5))); S.append((tw(1, "peak") - 0.2, b01b, ("dissolve", 0.5)))
    S.append((B[2]["t0"], b02, ("dissolve", 0.5)))
    S.append((B[3]["t0"], b03, ("dissolve", 0.5)))
    S.append((B[4]["t0"], b04a, ("dissolve", 0.6))); S.append((tw(4, "It") - 0.5, b04b, ("dissolve", 0.6)))
    S.append((B[5]["t0"], b05, ("dissolve", 0.6)))            # beats 5+6 as one diagram
    S.append((B[7]["t0"], b07, ("dissolve", 0.5)))
    S.append((B[8]["t0"], b08, ("dissolve", 0.5)))
    S.append((B[9]["t0"], b09, ("dissolve", 0.6)))
    S.append((B[10]["t0"], b10, ("dissolve", 0.5)))
    S.append((B[11]["t0"], b11, ("dissolve", 0.5)))
    S.append((B[12]["t0"], b12_stage, ("dissolve", 0.5)))
    S.append((B[13]["t0"], b13, ("dissolve", 0.5)))
    S.append((B[14]["t0"], b14, ("dissolve", 0.5)))
    S.append((B[15]["t0"], b15a, ("dissolve", 0.5))); S.append((tw(15, "And") - 0.3, b15b, ("dissolve", 0.5)))
    S.append((B[16]["t0"], b16, ("dissolve", 0.5)))
    S.append((B[17]["t0"], b17, ("dissolve", 0.5)))
    S.append((B[18]["t0"], b18, ("dissolve", 0.5)))
    S.append((B[19]["t0"], b19, ("dissolve", 0.5)))
    S.append((B[20]["t0"], b20, ("dissolve", 0.6)))
    S.append((B[21]["t0"], b21, None))
    return S


def build(size=(1280, 720), t_range=None, log=print):
    """-> (Program, info). Shots are built only when they intersect t_range; the Sequence starts at the first kept shot's boundary (info['t_base'])."""
    global SIZE; SIZE = tuple(size); _cache.pop("geo", None)
    plan = shot_plan(); bounds = [p[0] for p in plan] + [DUR + 0.2]; keep = []
    for i, (t0, bld, tr) in enumerate(plan):
        d = tr[1] if tr else 0.0
        if t_range and (bounds[i + 1] + d <= t_range[0] or t0 >= t_range[1]): continue
        keep.append(i)
    shots, trs = [], []
    for i in keep:
        t0, bld, tr = plan[i]; d = tr[1] if tr else 0.0; dur = (bounds[i + 1] - t0) + (d if i != len(plan) - 1 else 0.0)
        sc = bld(t0, dur); shots.append(SQ.Shot(sc, dur, getattr(sc, "name", bld.__name__))); trs.append(TR.Dissolve(d) if tr and i != len(plan) - 1 else None)
    seq = SQ.Sequence(shots, trs[:-1]); base = plan[keep[0]][0]
    cards = C.make_cards(WORDS); styles = C.plan_styles(cards, "long"); caps = C.WordCaptions(cards, styles, source="provider")
    prog = SQ.Program(seq, [caps], t_offset=base)
    return prog, dict(t_base=base, plan=[(p[0], p[1].__name__) for p in plan], keep=keep)


def sfx_cues(plan):
    cues = []
    for i, (t0, bld, tr) in enumerate(plan):
        if i and tr is not None or i: cues.append(dict(t=max(0.0, t0 - 0.15), kind="sweep", why=f"shot {bld.__name__}"))
    return cues


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=("stills", "render", "plan")); ap.add_argument("out", nargs="?"); ap.add_argument("times", nargs="*", type=float)
    ap.add_argument("--size", default="1280x720"); ap.add_argument("--start", type=float, default=None); ap.add_argument("--end", type=float, default=None); ap.add_argument("--workers", type=int, default=4); ap.add_argument("--no-audio", action="store_true"); ap.add_argument("--crf", type=int, default=18); ap.add_argument("--preset", default="medium")
    a = ap.parse_args(argv); size = tuple(int(x) for x in a.size.split("x"))
    if a.cmd == "plan":
        for t0, bld, tr in shot_plan(): print(f"{t0:8.2f}  {bld.__name__:12s} {tr}")
        return
    rng = (a.start, a.end) if a.start is not None else None
    if a.cmd == "stills":
        os.makedirs(a.out, exist_ok=True); times = a.times
        for t in times:
            prog, info = build(size, (t - 0.01, t + 0.01)); prog.render(t - info["t_base"]).save(os.path.join(a.out, f"t{t:07.2f}.png"))
        return
    prog, info = build(size, rng); t_s = a.start if a.start is not None else 0.0; t_e = a.end if a.end is not None else DUR
    # a Program's time base is the first kept shot; render only [t_s, t_e]
    times = [i / FPS for i in range(int(round((t_s - info["t_base"]) * FPS)), int(round((t_e - info["t_base"]) * FPS)))]
    audio = None
    if not a.no_audio:
        mix_path = a.out + ".mix.wav"; voice = os.path.join(PROD, "voice", "narration.wav")
        rep = SFX.mix(voice, sfx_cues(shot_plan()), DUR + 0.05, mix_path); json.dump(rep, open(a.out + ".sfx.json", "w"), indent=1)
        audio = a.out + ".cut.wav"
        import subprocess
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t_s}", "-t", f"{t_e - t_s}", "-i", mix_path, audio], check=True)
    n = SQ.render_video(prog, a.out, FPS, a.workers, audio=audio, crf=a.crf, preset=a.preset, frames=times); print("frames", n)


if __name__ == "__main__":
    main()
