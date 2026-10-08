#!/usr/bin/env python3
"""Builds ASSET_AUDIT.json / ASSET_AUDIT.md from scene_plan.json plus the hand-classified need per scene.
Kinds: seq = pre-rendered Landsat sequence (visuals/scripts/render.py), landsat_loc = new Landsat location shot,
nasa = NASA still/video (external_still / video), graphic = original yt-graphics image."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
plan = json.load(open(os.path.join(HERE, "scene_plan.json")))

NEED = {  # scene: (kind, asset, status)
 "1": ("landsat_loc", "Tassili n'Ajjer plateau, LC08 browse 2025-10-24 (path/row 183/048)", "browse_downloaded_unframed"),
 "2": ("graphic", "callout 230+ (claims.md)", "to_build"),
 "3": ("landsat_loc", "Bodele depression, browse LC09 2025-12-20 (190/042)", "browse_downloaded_unframed"),
 "4": ("nasa", "NASA SVS 3539 Blue Marble Next Generation, africa.0700.jpg", "downloaded_provenance_recorded"),
 "5": ("graphic", "callout 'a few inches of rain a year'", "to_build"),
 "6": ("seq", "East Oweinat wipe 1984->2024 with 1984 push-in <=3 percent", "sequence_code_ready_render_pending"),
 "7": ("graphic", "timeline 15,000 y to today, band 11,000-6,000", "to_build"),
 "8": ("landsat_loc", "Bodele wide, 'floor of Lake Mega-Chad' callout", "browse_downloaded_unframed"),
 "9": ("landsat_loc", "Tassili canyons + callout ~200 burials", "browse_downloaded_unframed"),
 "10": ("graphic", "rainfall card ~100 / ~450 mm per year", "to_build"),
 "11": ("landsat_loc", "Ounianga lakes, wide and close (LC09 2025-12-30, 180/043)", "browse_downloaded_unframed"),
 "12": ("graphic", "3-step orbital/monsoon diagram", "to_build"),
 "13": ("graphic", "model-vs-geology flow", "to_build"),
 "14": ("graphic", "schematic green episodes on a time axis", "to_build"),
 "15": ("landsat_loc", "Ounianga + N->S arrow insert", "browse_downloaded_unframed"),
 "16": ("graphic", "circulation diagram (yt-graphics circulation)", "to_build"),
 "17": ("landsat_loc", "Gilf Kebir slow pull-out (LC09 2025-11-21, 179/044)", "browse_downloaded_unframed"),
 "18": ("seq", "East Oweinat timelapse 1984/2000/2010/2016/2024", "sequence_code_ready_render_pending"),
 "19": ("seq", "East Oweinat zoom to centre-pivot field; starts <=2.2 s late", "sequence_code_ready_render_pending"),
 "20": ("landsat_loc", "Kufra push-in with pin (LC09 2025-12-21, 181/047)", "browse_downloaded_unframed"),
 "21": ("seq", "Toshka wipe chain 1999/2002/2011-12/2021", "sequence_code_ready_render_pending"),
 "22": ("seq", "East Oweinat close-up 2024", "sequence_code_ready_render_pending"),
 "23": ("graphic", "desalination-pipeline flow, footer PROPOSAL (2009)", "to_build"),
 "24": ("graphic", "text card multi-trillion-dollar projects", "to_build"),
 "24b": ("graphic", "callout >1,000 mm/yr (2009 simulation)", "to_build"),
 "25": ("graphic", "water-budget stacked bar (MODEL)", "to_build"),
 "25b": ("nasa", "pull-out Sahara -> Africa/Atlantic: Blue Marble africa.0700.jpg as a still zoom", "downloaded_provenance_recorded"),
 "29": ("nasa", "NASA SVS 4362 Dust in the Wind (CALIPSO), webm 60 fps -> 30 fps", "downloaded_needs_decimation"),
 "30": ("landsat_loc", "Bodele 100-150 km, white diatomite flats", "browse_downloaded_unframed"),
 "31": ("graphic", "text card HYPOTHESIS - NO STUDY FOUND", "to_build"),
 "32": ("graphic", "simulation diagram ~6,000 y ago", "to_build"),
 "33": ("graphic", "callouts only; optional Lake Chad wipe dropped", "to_build"),
 "34": ("graphic", "three separate labelled bars (COP21, PA-GGW...)", "to_build"),
 "35": ("seq", "East Oweinat widest view wipe 1984->2024", "sequence_code_ready_render_pending"),
 "36": ("graphic", "closing text card (uncertainty statement)", "to_build"),
 "37": ("landsat_loc", "Ounianga or Tassili slow pull-out", "browse_downloaded_unframed"),
}
PROV = {
 "svs3539": {"title": "Blue Marble Next Generation images from Terra/MODIS", "url": "https://svs.gsfc.nasa.gov/3539",
             "file": "africa.0700.jpg", "credit": "NASA Goddard Space Flight Center Scientific Visualization Studio; Blue Marble data: Reto Stockli, NASA Earth Observatory",
             "data_date": "2004 monthly composites", "released": "2008-08-29", "licence": "NASA media usage guidelines: public domain unless noted; credit NASA",
             "acquired": "2026-10-08"},
 "svs4362": {"title": "Dust in the Wind (CALIPSO)", "url": "https://svs.gsfc.nasa.gov/4362", "file": "SaharanDust_1080p_60fps.webm",
             "credit": "NASA Goddard Space Flight Center Scientific Visualization Studio; visualizer Kel Elkins (USRA); CALIPSO data", "released": "2015-09-28",
             "licence": "NASA media usage guidelines: public domain unless noted; credit NASA", "acquired": "2026-10-08",
             "note": "VP8 1920x1080, 60 fps, 104.25 s; must be decimated to 30 fps (every 2nd frame) before use"},
 "landsat_browse": {"url": "https://m2m.cr.usgs.gov/ (USGS EarthExplorer browse images)", "credit": "U.S. Geological Survey / NASA Landsat",
             "licence": "USGS Landsat data are public domain; credit requested", "acquired": "2026-10-08",
             "scenes": ["LC08_L1TP_183048_20251024", "LC09_L1TP_179044_20251121", "LC09_L1TP_180043_20251230", "LC09_L1TP_181047_20251221", "LC09_L1TP_190042_20251220"],
             "note": "8-bit natural colour browse at 30 m; not tone-B comparable to the locked sequences, used for location shots only; framing unchecked"},
}
rows = []
for s in plan["scenes"]:
    if s.get("status") != "ok":
        continue
    k, a, st = NEED[s["scene"]]
    rows.append({"scene": s["scene"], "start": round(s["start"], 2), "end": round(s["end"], 2), "duration": round(s["duration"], 2),
                 "kind": k, "asset": a, "status": st, "storyboard_visual": s["visual"][:160]})
assert len(rows) == 36, len(rows)
tally = {}
for r in rows:
    tally[r["status"]] = tally.get(r["status"], 0) + 1
out = {"schema": "ep001-asset-audit/1", "date": "2026-10-08", "scenes": rows, "status_tally": tally, "provenance": PROV}
json.dump(out, open(os.path.join(HERE, "ASSET_AUDIT.json"), "w"), indent=1, ensure_ascii=False)
md = ["# EP001 asset audit (36 active scenes)", "", f"Status tally: {json.dumps(tally)}", "",
      "| scene | time | kind | asset | status |", "|---|---|---|---|---|"]
md += [f"| {r['scene']} | {r['start']}-{r['end']} | {r['kind']} | {r['asset']} | {r['status']} |" for r in rows]
md += ["", "## Provenance (acquired 2026-10-08)", ""]
for k, v in PROV.items():
    md.append(f"- **{k}**: " + "; ".join(f"{a}: {b}" for a, b in v.items()))
md += ["", "No invented imagery stands in for scientific evidence. Every graphic carries only claims from `story/claims.md`."]
open(os.path.join(HERE, "ASSET_AUDIT.md"), "w").write("\n".join(md) + "\n")
print(tally, len(rows))
