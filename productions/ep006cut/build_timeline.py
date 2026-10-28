"""EP006 short cut: hand-authored shot list (style of start_v3) on the cut narration timings (story/cut_map.json). No planner involved."""
import json, math
tl = json.load(open("../ep006/timeline.json"))
A = {k: v for k, v in tl["assets"].items() if k in ("y2026", "l2026") or k.startswith(("i_seismic", "i_2015", "i_toll", "i_clouds", "i_cause"))}
A["y2026"]["label"] = "12 AUG"; A["l2026"]["label"] = "26 AUG"
S2C = "Contains modified Copernicus Sentinel data 2026"
A["d0827"] = {"src": "evidence/s2post/d0827.png", "label": "27 AUG", "credit": S2C}
A["d0908"] = {"src": "evidence/s2post/d0908.png", "label": "8 SEP", "credit": S2C}
A["esa_l9"] = {"src": "evidence/esa_landsat9_after_1280.jpg", "kind": "external_still", "label": "ESA LANDSAT-9 26 AUG", "credit": "ESA - Landsat-9 (USGS), 26 Aug 2026, CC BY 4.0",
               "source_url": "https://commons.wikimedia.org/wiki/File:Nepal_glacier_collapse_and_flood_(after)_(55504451912).jpg", "license": "CC BY 4.0", "retrieved": "2026-10-28", "image_date": "2026-08-26"}
SCAR = [85.5126, 28.2872]; BEND = [85.4456, 28.3379]; P1 = [85.4141, 28.3155]; P2 = [85.3852, 28.2858]; P3 = [85.3586, 28.2268]; JUNC = [85.3778, 28.2788]; C = [85.46, 28.31]
KM_LON = 98.1; KM_LAT = 111.2
def fit(c, w):
    hl = w / 2 / KM_LON + 0.001; ha = w * 9 / 16 / 2 / KM_LAT + 0.001
    return [round(min(max(c[0], 85.30 + hl), 85.62 - hl), 4), round(min(max(c[1], 28.196 + ha), 28.424 - ha), 4)]
def cam(c0, w0, c1, w1): return {"from": {"center": fit(c0, w0), "width_km": w0}, "to": {"center": fit(c1, w1), "width_km": w1}}
def lab(text, t, slot="upper", sub=None, dur=None):
    d = {"type": "label", "text": text, "style": "tag", "slot": slot, "plate": True, "t": [t, dur]}
    if sub: d["sub"] = sub
    return d
def pin(at, text, t, dur=None): return {"type": "pin", "at": at, "text": text, "plate": True, "t": [t, dur]}
def arr(a, b, t): return {"type": "arrow", "from": a, "to": b, "color": "#FFD23F", "width": 9, "t": [t, None]}
img = lambda a: {"type": "image", "asset": a}
gfx = lambda a, t=0: {"type": "graphic", "asset": a, "t": [t, None], "push": 0.04}
wipe = lambda a, b, t0, t1: {"type": "wipe", "from": a, "to": b, "t": [t0, t1]}
S = []
def shot(start, layers, camera=None, nearest=False):
    d = {"id": f"v4_{len(S):03d}", "start": start, "visual_family": f"v4_{len(S):03d}", "layers": layers}
    if camera: d["camera"] = camera
    if nearest: d["resample"] = "nearest"
    S.append(d)
B = "12 AUG 2026 - SENTINEL-2"
shot(0.0, [img("y2026"), lab(B, 0.4, sub="BEFORE - 10 M")], cam(C, 27, [85.47, 28.32], 14))
shot(3.76, [img("y2026")], cam([85.47, 28.32], 14, [85.50, 28.295], 9))
shot(7.523, [img("y2026"), wipe("y2026", "l2026", 0.2, 2.6), lab("26 AUG 2026 - LANDSAT 9", 2.0, sub="30 M, SHOWN WIDE, NOT SHARPENED")], cam(C, 26, C, 24), True)
shot(12.411, [img("y2026"), lab("RADAR 7 JUL - 24 AUG", 2.0, sub="UP TO 40 CM, LINE OF SIGHT (ICIMOD)")], cam([85.50, 28.29], 10, [85.47, 28.31], 8))
shot(20.016, [img("d0908"), lab("8 SEP 2026 - SENTINEL-2", 0.3, sub="13 DAYS AFTER THE EVENT, 10 M")], cam([85.47, 28.32], 14, [85.45, 28.325], 10))
shot(24.463, [{"type": "still", "asset": "esa_l9", "view": {"from": {"center": [0.5, 0.77], "width": 1.0}, "to": {"center": [0.5, 0.56], "width": 1.0}, "ease": "linear"}}, lab("ESA - LANDSAT-9, 26 AUG 2026", 3.5, dur=9.0)])
shot(37.965, [img("l2026"), arr(SCAR, P1, 1.2), arr(P1, P2, 3.0), lab("USGS: ABOUT 100 KM (62 MI)", 2.3), lab("OUR TRACE (APPROX.): ~30 KM", 4.6, slot="middle")], cam([85.45, 28.29], 24, [85.43, 28.29], 22), True)
shot(44.16, [img("y2026"), lab("12 AUG 2026 - BEFORE", 0.2, dur=1.2), arr(P2, P3, 1.0), pin(BEND, "LENDE KHOLA", 1.4, dur=1.4), pin(P3, "TRISHULI KHOLA", 2.6)], cam([85.43, 28.32], 16, [85.38, 28.24], 14))
shot(48.937, [img("y2026"), wipe("y2026", "d0827", 1.8, 3.6), lab("USGS: FLOOD HIT POPULATED AREAS", 0.4, dur=3.0), lab("27 AUG 2026 - PARTLY CLOUDED", 3.2), pin(JUNC, "RASUWAGADHI (APPROX.)", 4.2)], cam([85.395, 28.29], 14, JUNC, 8))
shot(55.531, [img("l2026"), lab("STOP POINT: NOT IN USGS TEXT", 0.4)], cam([85.42, 28.28], 22, C, 26), True)
shot(59.746, [gfx("i_seismic_s1"), gfx("i_seismic_s2", 6.7)])
shot(73.272, [img("y2026"), lab("USGS: ENERGY COMPARISON ONLY", 0.6)], cam([85.50, 28.30], 14, [85.49, 28.30], 10))
shot(80.319, [img("d0908"), lab("8 SEP 2026 - SENTINEL-2", 0.3, sub="CAUSE: NOT YET DETERMINED (USGS)")], cam([85.48, 28.32], 11, [85.50, 28.30], 8))
shot(93.682, [img("y2026"), lab("2015: SAME MOUNTAIN (USGS)", 3.2)], cam([85.50, 28.30], 16, [85.49, 28.29], 9))
shot(104.968, [gfx("i_2015")])
shot(112.084, [gfx("i_toll_s1"), gfx("i_toll_s2", 8.5)])
shot(124.0, [img("l2026")], cam(C, 26, [85.45, 28.31], 24), True)
shot(130.881, [img("y2026"), pin(JUNC, "GYIRONG PORT (APPROX.)", 4.0)], cam([85.40, 28.29], 12, JUNC, 8))
shot(140.958, [img("d0827")], cam([85.43, 28.32], 16, [85.40, 28.30], 12))
shot(147.101, [img("y2026"), lab("ICIMOD - 13 OCT 2026", 0.5)], cam(C, 27, [85.46, 28.31], 20))
shot(153.649, [img("d0908"), lab("ICIMOD: NOT A LAKE OUTBURST", 0.6, sub="8 SEP 2026 IMAGE, 10 M")], cam([85.48, 28.32], 11, [85.50, 28.30], 8))
shot(162.902, [img("y2026"), lab("RADAR 7 JUL - 24 AUG", 2.0, sub="UP TO 40 CM, LINE OF SIGHT (ICIMOD)")], cam([85.50, 28.29], 10, [85.47, 28.31], 8))
shot(173.328, [img("y2026"), lab("LINE OF SIGHT, NOT FULL MOTION", 0.8)], cam([85.52, 28.30], 8, [85.50, 28.29], 12))
shot(181.965, [img("y2026"), lab("NOT SHOWN TO BE PREDICTABLE", 0.5)], cam([85.47, 28.32], 18, C, 27))
shot(187.805, [img("l2026"), lab("ICIMOD: ~132 MILLION M3", 0.8, sub="EARLY ESTIMATE; OTHERS SMALLER")], cam(C, 26, [85.46, 28.31], 22), True)
shot(199.067, [img("y2026")], cam([85.46, 28.31], 22, [85.47, 28.32], 14))
shot(203.665, [img("y2026"), lab("12 AUG: 19% SCENE CLOUD", 0.5)], cam(C, 26, [85.47, 28.32], 14))
shot(211.734, [gfx("i_clouds")])
shot(220.024, [img("l2026"), lab("26 AUG 2026 - LANDSAT 9", 0.4, sub="30 M PIXELS, NOT SHARPENED")], cam(C, 26, [85.45, 28.31], 22), True)
shot(232.958, [img("y2026"), lab("12 AUG 2026 - BEFORE", 0.3)], cam([85.43, 28.335], 9, [85.40, 28.31], 8))
shot(237.382, [img("l2026"), lab("26 AUG 2026 - LANDSAT 9", 0.3)], cam([85.44, 28.31], 22, [85.45, 28.32], 24), True)
shot(243.071, [img("d0908"), lab("COMPOSITION: CANNOT TELL", 0.5, sub="SHOWN: 8 SEP 2026 IMAGE, 10 M")], cam([85.48, 28.32], 12, [85.50, 28.30], 9))
shot(247.041, [img("l2026"), arr(SCAR, P1, 0.3), arr(P1, P2, 1.9), arr(P2, P3, 4.0), lab("TRACED BY EYE, APPROX. 30 KM", 1.4), lab("~20 KM TO RIVER TURN", 7.2, slot="middle"), pin(JUNC, "RASUWAGADHI (APPROX.)", 8.6)], cam([85.45, 28.30], 26, [85.44, 28.29], 22), True)
shot(259.325, [img("d0827"), lab("CLOUDS HIDE PARTS OF THE VALLEY", 0.4, sub="27 AUG 2026, SENTINEL-2")], cam([85.43, 28.32], 16, [85.42, 28.31], 20))
shot(265.27, [{"type": "still", "asset": "esa_l9", "view": {"from": {"center": [0.5, 0.50], "width": 1.0}, "to": {"center": [0.5, 0.30], "width": 1.0}, "ease": "linear"}}, lab("ESA - LANDSAT-9, 26 AUG 2026", 0.5)])
shot(274.709, [img("y2026"), wipe("y2026", "l2026", 1.2, 3.8), lab("TWO DAYS: 12 AUG AND 26 AUG", 0.5)], cam(C, 26, C, 24), True)
shot(282.988, [img("y2026")], cam([85.50, 28.30], 16, [85.48, 28.30], 10))
shot(291.22, [img("l2026")], cam([85.45, 28.31], 22, C, 26), True)
shot(296.166, [img("y2026")], cam(C, 27, [85.47, 28.32], 16))
shot(305.569, [img("y2026"), lab("12 AUG 2026 - BEFORE", 0.5)], cam([85.43, 28.32], 18, [85.41, 28.31], 12))
shot(311.339, [img("y2026"), lab("SENTINEL-2 - LANDSAT 9 - ESA", 0.8)], cam([85.47, 28.32], 14, C, 27))
t = dict(tl, assets=A, shots=S, end={"seconds": 318.9})
json.dump(t, open("timeline.json", "w"), indent=1)
print(len(S), "shots")
