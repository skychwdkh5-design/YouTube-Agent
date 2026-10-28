"""EP006: writes notes.json -> infographics, maps (scenes from the shared motion presets), skip_graphics, visual_choices. Run from the production root:  python3 research/build_visual_notes.py
Every anchor_text is a phrase of script.md; every number on a card is a number of a claim in notes.json. Nothing here invents a photograph, a satellite frame or a measurement."""
import json
P = "research/notes.json"
n = json.load(open(P))
def N(id, text, x, y, w=0.3, h=0.16, style="default", step=None):
    d = {"id": id, "text": text, "x": x, "y": y, "w": w, "h": h, "style": style}
    if step: d["step"] = step
    return d
SRC_USGS = "USGS Landslide Hazards Program, page updated 28 Aug 2026 (preliminary)"
SRC_ICI = "ICIMOD preliminary analysis, 13 Oct 2026 (page not readable here; via coverage)"
def card(id, ch, claims, anchor, nodes, steps, source, title, min_s=9, exempt=False):
    d = {"id": id, "chapter": ch, "claims": claims, "anchor_text": anchor, "min_s": min_s, "graphic": {"type": "diagram", "title": title, "source": source, "nodes": nodes}, "steps": steps}
    if exempt: d["exempt"] = True
    return d
inf = []
# ---- plan: what was reported
inf.append(card("i_usgs", "plan", ["C1"], "The US Geological Survey said", [N("h", "USGS - 26 AUG 2026, MORNING", 0.5, 0.17, 0.66, 0.13, "plain", 1), N("a", "RAPID SLOPE FAILURE INVOLVING A GLACIER", 0.5, 0.45, 0.86, 0.2, "accent", 1), N("b", "LANGTANG NATIONAL PARK, NEPAL, NEAR THE CHINA BORDER", 0.5, 0.75, 0.86, 0.18, "default", 2)],
    [{"anchor_text": "The US Geological Survey said"}, {"anchor_text": "Langtang National Park in Nepal"}], SRC_USGS, "What was reported", 10))
inf.append(card("i_100km", "plan", ["C2"], "traveled about 100 kilometers", [N("h", "USGS: DEBRIS FLOW AND FLOOD", 0.5, 0.17, 0.66, 0.13, "plain", 1), N("a", "ABOUT 100 KM (62 MI)", 0.5, 0.43, 0.8, 0.22, "accent", 1), N("b", "ALONG THE LENDE KHOLA AND TRISHULI KHOLA", 0.5, 0.74, 0.86, 0.17, "default", 2)],
    [{"anchor_text": "traveled about 100 kilometers"}, {"anchor_text": "along two rivers"}], SRC_USGS, "What was reported", 9))
inf.append(card("i_seismic", "plan", ["C3"], "released seismic energy equal to a magnitude 5.2", [N("a", "ENERGY EQUAL TO A M5.2 EARTHQUAKE", 0.5, 0.2, 0.84, 0.17, "accent", 1), N("b", "A SECOND SIGNAL ~3 HOURS LATER: M4.2", 0.5, 0.47, 0.84, 0.17, "default", 2),
    N("c", "THE FAILURE PRODUCED THE SIGNALS - NOT AN EARTHQUAKE TRIGGER", 0.5, 0.76, 0.9, 0.2, "red", 3)],
    [{"anchor_text": "released seismic energy equal to a magnitude 5.2"}, {"anchor_text": "about three hours later"}, {"anchor_text": "those are energy comparisons"}], SRC_USGS, "What was reported", 15))
inf.append(card("i_cause", "plan", ["C4"], "has not yet determined", [N("a", "CAUSE: NOT YET DETERMINED", 0.5, 0.2, 0.8, 0.16, "red", 1), N("b", "A LANDSLIDE THAT PICKED UP PART OF A GLACIER", 0.5, 0.46, 0.86, 0.16, "default", 2), N("c", "OR A FAILURE OF THE GLACIER ITSELF", 0.5, 0.7, 0.86, 0.16, "default", 2),
    N("d", "ALL INFORMATION PRELIMINARY", 0.5, 0.9, 0.7, 0.1, "plain", 3)],
    [{"anchor_text": "has not yet determined"}, {"anchor_text": "everything it has published is preliminary"}], SRC_USGS, "What was reported", 12))
inf.append(card("i_2015", "plan", ["C5"], "In 2015, USGS said", [N("h", "2015 - SAME MOUNTAIN", 0.5, 0.15, 0.6, 0.12, "plain", 1), N("a", "M7.8 EARTHQUAKE SET OFF A DEBRIS AVALANCHE", 0.5, 0.4, 0.88, 0.18, "accent", 1),
    N("b", "FELL NEARLY 1,900 M - BURIED A VILLAGE", 0.5, 0.65, 0.88, 0.15, "default", 2), N("c", "MORE THAN 200 PEOPLE KILLED", 0.5, 0.86, 0.7, 0.13, "red", 3)],
    [{"anchor_text": "In 2015, USGS said"}, {"anchor_text": "nearly 1,900 meters"}, {"anchor_text": "killed more than 200 people"}], SRC_USGS, "What was reported", 14))
inf.append(card("i_toll", "plan", ["C10"], "Now the human cost", [N("h", "NEPAL - MID-OCTOBER, REPORTED", 0.5, 0.16, 0.66, 0.12, "plain", 1), N("a", "MORE THAN 1,400 DEAD", 0.5, 0.4, 0.8, 0.2, "accent", 1),
    N("b", "ROUGHLY 5,000 STILL LISTED AS MISSING", 0.5, 0.65, 0.86, 0.16, "default", 2), N("c", "THE LISTS KEEP CHANGING", 0.5, 0.86, 0.7, 0.12, "red", 3)],
    [{"anchor_text": "Now the human cost"}, {"anchor_text": "roughly five thousand still listed as missing"}, {"anchor_text": "not giving one exact number"}], "Nepali figures as reported (Nepal Police / NDRRMA lists; they differ by source and date)", "Counts in Nepal", 14))
inf.append(card("i_china", "plan", ["C11"], "China counts its own side", [N("h", "CHINA - XINHUA, 5 SEPT", 0.5, 0.16, 0.6, 0.12, "plain", 1), N("a", "GYIRONG PORT: 43 DEAD, 519 MISSING", 0.5, 0.42, 0.86, 0.18, "accent", 1),
    N("b", "COUNTED SEPARATELY FROM NEPAL", 0.5, 0.67, 0.8, 0.14, "default", 2), N("c", "NOT ADDED TO NEPAL'S NUMBERS", 0.5, 0.86, 0.76, 0.12, "red", 3)],
    [{"anchor_text": "China counts its own side"}, {"anchor_text": "do not add the two together"}], "Xinhua (via The Star / NST) and NBC News, early September 2026", "Counts in Tibet", 12))
# ---- method
inf.append(card("i_icimod", "method", ["C7"], "published a preliminary analysis on 13 October", [N("h", "ICIMOD - 13 OCT 2026", 0.5, 0.17, 0.6, 0.12, "plain", 1), N("a", "NOT A CONVENTIONAL GLACIAL LAKE OUTBURST FLOOD", 0.5, 0.45, 0.88, 0.2, "accent", 2),
    N("b", "BEDROCK FAILURE SHEARED AWAY PART OF THE GLACIER ABOVE IT", 0.5, 0.76, 0.9, 0.2, "default", 3)],
    [{"anchor_text": "published a preliminary analysis on 13 October"}, {"anchor_text": "not a conventional glacial lake outburst flood"}, {"anchor_text": "sheared away part of the glacier"}], SRC_ICI, "What was reported", 15))
inf.append(card("i_radar", "method", ["C8"], "radar satellites, Sentinel-1", [N("a", "SENTINEL-1 RADAR: UP TO 40 CM OF MOVEMENT", 0.5, 0.2, 0.88, 0.17, "accent", 1), N("b", "7 JULY - 24 AUGUST (ENDS 2 DAYS BEFORE THE FAILURE)", 0.5, 0.47, 0.9, 0.17, "default", 2),
    N("c", "ALONG THE LINE OF SIGHT - NOT THE FULL MOTION", 0.5, 0.74, 0.86, 0.16, "plain", 3), N("d", "NOT SHOWN TO BE PREDICTABLE", 0.5, 0.92, 0.7, 0.1, "red", 4)],
    [{"anchor_text": "radar satellites, Sentinel-1"}, {"anchor_text": "between 7 July and 24 August"}, {"anchor_text": "along the satellite's line of sight"}, {"anchor_text": "does not show that"}], SRC_ICI, "What the radar measured", 22))
inf.append(card("i_volume", "method", ["C9"], "estimate of the volume", [N("a", "ICIMOD EARLY ESTIMATE: ~132 MILLION M3", 0.5, 0.22, 0.88, 0.17, "accent", 1), N("b", "ANOTHER EARLY ANALYSIS: MUCH SMALLER", 0.5, 0.5, 0.88, 0.17, "default", 2),
    N("c", "SIZE NOT SETTLED", 0.5, 0.78, 0.6, 0.14, "red", 3)],
    [{"anchor_text": "estimate of the volume"}, {"anchor_text": "much smaller volume"}, {"anchor_text": "the size is not settled"}], SRC_ICI, "How big?", 14))
# ---- obs: own data
inf.append({"id": "i_clouds", "chapter": "obs", "claims": ["C15"], "anchor_text": "First we looked for the clearest view", "min_s": 12,
    "graphic": {"type": "bar", "title": "Sentinel-2 scene cloud cover, clearest pass per date (%)", "source": "Copernicus Sentinel-2 L2A scene catalogue, tiles over Langtang, Aug 2026", "unit": "%", "decimals": 0,
                "bars": [{"label": "12 AUG", "value": 19, "highlight": True}, {"label": "14 AUG", "value": 49}, {"label": "17 AUG", "value": 97}, {"label": "19 AUG", "value": 85}, {"label": "22 AUG", "value": 78}, {"label": "24 AUG", "value": 39}, {"label": "27 AUG", "value": 78}]}})
inf.append({"id": "i_flow_scale", "chapter": "obs", "claims": ["C2", "C14"], "anchor_text": "USGS said the flow traveled about 100 kilometers", "min_s": 11,
    "graphic": {"type": "geo", "title": "Part of ~100 km", "source": "Sentinel-2 12 Aug 2026 (40 m); trace: Landsat 9, 26 Aug", "credit": "Contains modified Copernicus Sentinel data 2026", "show_credit": False, "date": "12 AUG 2026",
                "image": {"stack": "evidence/wide/y2026.png", "grid": "evidence/wide/grid.json", "center": [85.45, 28.26], "width_km": 42},
                "arrows": [{"from": [85.5126, 28.2872], "to": [85.4141, 28.3155], "step": 1}, {"from": [85.4141, 28.3155], "to": [85.3852, 28.2858], "step": 1}, {"from": [85.3852, 28.2858], "to": [85.3586, 28.2268], "step": 1}],
                "callouts": [{"at": [85.3778, 28.2788], "text": "RASUWAGADHI BORDER POST", "step": 2}], "graticule": False, "scale_bar": True},
    "steps": [{"anchor_text": "USGS said the flow traveled about 100 kilometers"}, {"anchor_text": "Our frame cannot show all of it"}]})
inf.append(card("i_official", "obs", ["C6"], "mapping the full extent", [N("a", "USGS: OFFICIAL EXTENT MAP FROM BEFORE/AFTER SATELLITE IMAGES", 0.5, 0.3, 0.9, 0.22, "accent", 1), N("b", "OUR TRACE IS NOT A SUBSTITUTE", 0.5, 0.68, 0.8, 0.16, "red", 2)],
    [{"anchor_text": "mapping the full extent"}, {"anchor_text": "not a substitute"}], SRC_USGS, "What was reported", 10))
# ---- limits / close (no claims: exempt)
inf.append(card("i_cannot", "limits", [], "What can we not say", [N("a", "SPEED OR DEPTH OF THE FLOW: NOT SHOWN", 0.5, 0.18, 0.88, 0.14, "red", 1), N("b", "WHY THE SLOPE FAILED: NOT FINISHED", 0.5, 0.4, 0.88, 0.14, "red", 2),
    N("c", "A WARNING IN TIME: NOT SHOWN", 0.5, 0.62, 0.88, 0.14, "red", 3), N("d", "HOW MANY DIED: LISTS NOT FINAL", 0.5, 0.84, 0.88, 0.14, "red", 4)],
    [{"anchor_text": "how high the water rose"}, {"anchor_text": "why the slope failed"}, {"anchor_text": "anyone could have been warned"}, {"anchor_text": "how many people died"}], "Limitations listed in the script (L)", "What we cannot say", 22, True))
inf.append(card("i_watch", "close", [], "Two things will settle more", [N("a", "FINAL USGS + ICIMOD FINDINGS: TYPE AND SIZE", 0.5, 0.3, 0.9, 0.2, "accent", 1), N("b", "OFFICIAL COUNTS ON BOTH SIDES OF THE BORDER", 0.5, 0.68, 0.9, 0.2, "accent", 2)],
    [{"anchor_text": "The final findings from USGS and ICIMOD"}, {"anchor_text": "official counts of the dead and missing"}], "Limitations listed in the script (L)", "What to watch", 14, True))
# ---- maps (scenes): camera, wipe, pins, arrows; presets are shared (motion_presets.json)
VALLEY = [85.445, 28.325]; SCAR = [85.5126, 28.2872]; JUNC = [85.3778, 28.2788]; BEND = [85.4456, 28.3379]
MAPS = [
 {"id": "m_hook", "chapter": "plan", "claims": ["C13"], "anchor_text": "On 12 August 2026", "min_s": 10, "wipe": ["y2026", "l2026"], "zoom": [26, 15], "focus": VALLEY, "wipe_at": "a dark swath runs through", "resample": "nearest",
  "marks": [{"type": "label", "text": "12 AUG 2026 - SENTINEL-2 (10 M)", "style": "tag", "slot": "upper", "t": 0.5, "dur": 4.2, "plate": True},
            {"type": "label", "text": "26 AUG 2026 - LANDSAT 9 (30 M)", "sub": "NOT SHARPENED", "style": "tag", "slot": "upper", "anchor_text": "a dark swath runs through", "dur": None, "plate": True}]},
 {"id": "m_rivers", "chapter": "plan", "claims": ["C2"], "anchor_text": "along two rivers", "min_s": 9, "asset": "y2026", "zoom": [20, 15], "focus": [85.43, 28.32], "focus_to": [85.37, 28.23],
  "marks": [{"type": "pin", "at": [85.4456, 28.3379], "text": "LENDE KHOLA", "anchor_text": "the Lende Khola", "dur": 4.0, "plate": True}, {"type": "pin", "at": [85.3592, 28.2404], "text": "TRISHULI KHOLA", "anchor_text": "the Trishuli Khola", "dur": None, "plate": True}]},
 {"id": "m_border", "chapter": "plan", "claims": ["C2"], "anchor_text": "including the Rasuwagadhi border post", "min_s": 7, "asset": "y2026", "zoom": [9, 5], "focus": JUNC,
  "marks": [{"type": "pin", "at": JUNC, "text": "RASUWAGADHI BORDER POST", "t": 0.8, "dur": None, "plate": True}]},
 {"id": "m_stop", "chapter": "plan", "claims": [], "limit": True, "anchor_text": "does not say where along that route", "min_s": 5, "asset": "y2026", "zoom": [16, 20], "focus": JUNC, "focus_to": [85.36, 28.20],
  "label": {"text": "STOP POINT: NOT IN USGS TEXT", "style": "tag", "slot": "upper", "plate": True}},
 {"id": "m_before", "chapter": "obs", "claims": ["C13"], "anchor_text": "In the 12 August image", "min_s": 7, "asset": "y2026", "zoom": [12, 7], "focus": [85.43, 28.335], "focus_to": [85.39, 28.30],
  "marks": [{"type": "pin", "at": [85.4253, 28.3314], "text": "NARROW PALE RIVER BED", "t": 1.0, "dur": None, "plate": True},
            {"type": "label", "text": "12 AUG 2026 - SENTINEL-2, 10 M", "style": "tag", "slot": "upper", "t": 0.3, "plate": True}]},
 {"id": "m_after", "chapter": "obs", "claims": ["C13"], "anchor_text": "In the 26 August image", "min_s": 9, "wipe": ["y2026", "l2026"], "zoom": [12, 7], "focus": [85.43, 28.335], "focus_to": [85.39, 28.30], "wipe_at": "a dark grey-brown swath", "resample": "nearest",
  "marks": [{"type": "label", "text": "12 AUG 2026 - SENTINEL-2 (10 M)", "style": "tag", "slot": "upper", "t": 0.4, "dur": 3.0, "plate": True},
            {"type": "label", "text": "26 AUG 2026 - LANDSAT 9 (30 M)", "sub": "NOT SHARPENED", "style": "tag", "slot": "upper", "anchor_text": "a dark grey-brown swath", "dur": None, "plate": True}]},
 {"id": "m_pixel", "chapter": "obs", "claims": ["C16"], "anchor_text": "Its pixels are 30 meters wide", "min_s": 5, "asset": "l2026", "zoom": [1.5, 0.5], "focus": BEND, "resample": "nearest",
  "label": {"text": "1 PIXEL = 30 M OF GROUND", "style": "tag", "slot": "upper", "plate": True}},
 {"id": "m_trace", "chapter": "obs", "claims": ["C14"], "anchor_text": "We traced it by eye", "min_s": 15, "wipe": ["y2026", "l2026"], "zoom": [32, 26], "focus": [85.43, 28.30], "wipe_at": "We traced it by eye", "resample": "nearest",
  "marks": [{"type": "arrow", "from": SCAR, "to": BEND, "color": "#FFD23F", "width": 9, "anchor_text": "We traced it by eye", "dur": None},
            {"type": "arrow", "from": BEND, "to": [85.3852, 28.2858], "color": "#FFD23F", "width": 9, "anchor_text": "On our grid it runs about 30 kilometers", "dur": None},
            {"type": "arrow", "from": [85.3852, 28.2858], "to": [85.3522, 28.1974], "color": "#FFD23F", "width": 9, "anchor_text": "On our grid it runs about 30 kilometers", "dur": None},
            {"type": "label", "text": "TRACED BY EYE: ~30 KM", "style": "tag", "slot": "upper", "anchor_text": "On our grid it runs about 30 kilometers", "dur": None, "plate": True},
            {"type": "pin", "at": JUNC, "text": "RASUWAGADHI BORDER POST", "anchor_text": "near the Rasuwagadhi border post", "dur": None, "plate": True},
            {"type": "label", "text": "~20 KM FROM GLACIER FOOT TO HERE", "style": "tag", "slot": "middle", "anchor_text": "About 20 of them", "dur": None, "plate": True}]},
 {"id": "m_clouds_hide", "chapter": "obs", "claims": [], "limit": True, "anchor_text": "Clouds hide other stretches", "min_s": 5, "asset": "l2026", "zoom": [20, 14], "focus": [85.5, 28.30], "focus_to": [85.45, 28.32],
  "label": {"text": "CLOUDS HIDE PARTS OF THE VALLEY", "style": "tag", "slot": "upper", "plate": True}},
]
n["infographics"] = inf
n["maps"] = MAPS
n["skip_graphics"] = {"g_reports": ["plan", "method", "obs", "limits", "close"]}
n["max_map_beats"] = {"obs": 5, "plan": 4}
n["visual_choices"] = {
 "hook": "The strongest real material is our own before/after pair: Sentinel-2 on 12 Aug (clear) against Landsat 9 on 26 Aug. It is shown first, with both sensors and pixel sizes named.",
 "obs": "Satellite frames are the evidence for this chapter: the claim is about what the ground looked like on two dates. No verified ground photograph of the flood exists in the ledger (see media/exceptions.json).",
 "plan": "Reported facts are shown as source cards (USGS / ICIMOD / Nepali and Chinese counts); satellite scenes only place the rivers and the border post, never a casualty.",
 "method": "Radar is not shown: no Sentinel-1 image was obtained, so the radar claim is a labelled card, not a picture."}
json.dump(n, open(P, "w"), indent=1, ensure_ascii=False)
print(len(inf), len(MAPS))
