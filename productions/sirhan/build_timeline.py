"""Final timeline: the approved storyboard, re-flowed onto Adam's real word timings.
Same shots, views, imagery and overlays; only times move. Shot starts are word anchors."""
import json
W = json.load(open("voice/narration.voice.json"))["words"]
tl = json.load(open("timeline_storyboard.json"))
# shot -> (first word of its line, offset). S6 starts 0.6 s early so the S5 basin hold stays under 6 s.
FIRST = {"S1_hook": (0, 0), "S2_proof": (10, -0.2), "S3_timelapse": (16, -0.2), "S4_closeup": (20, 0.0),
         "S5_exports": (34, -0.2), "S6_aquifer": (47, -0.6), "S7_policy": (65, -0.2), "S8_alfalfa": (76, -0.2),
         "S9_payoff": (87, -0.2)}
start = {k: (0.0 if i == 0 else W[i]["start"] + o) for k, (i, o) in FIRST.items()}
def rel(shot, word, extra=0.0): return round(W[word]["start"] + extra - start[shot], 2)
for s in tl["shots"]:
    sid = s["id"]; i, o = FIRST[sid]
    s["start"] = 0 if i == 0 else {"word": i, "edge": "start", "offset": o}
    for L in s["layers"]:
        tx = L.get("text")
        if sid == "S4_closeup" and tx == "CENTER-PIVOT IRRIGATION": L["t"] = [rel(sid, 28), None]     # "watered"
        if sid == "S6_aquifer" and tx == "WATER: ~20,000 YEARS OLD": L["t"] = [rel(sid, 52), None]     # "deep aquifers"
        if sid == "S6_aquifer" and tx == "RAIN: 100–200 MM A YEAR": L["t"] = [rel(sid, 60), None]     # "Rain"
        if sid == "S8_alfalfa" and tx == "3× THE WATER": L["t"] = [rel(sid, 81), None]               # "which uses"
        if sid == "S9_payoff" and tx == "~50 MORE YEARS": L["t"] = [rel(sid, 89), rel(sid, 97, -0.1)]
        if sid == "S9_payoff" and tx == "BUILT ON ICE AGE WATER": L["t"] = [rel(sid, 97), None]
tl["voice"] = {"src": "voice/narration.wav", "meta": "voice/narration.voice.json"}
tl["captions"] = {"src": "captions/captions.srt", "preset": "short"}
tl["end"] = {"after_last_word": 1.5, "min_total": 45.0}
tl["meta"] = {"title": "Wadi As-Sirhan - Ice Age water", "claims": "story/claims.json",
              "provenance": "stack/provenance.json", "storyboard": "timeline_storyboard.json (approved)"}
json.dump(tl, open("timeline.json", "w"), indent=1, ensure_ascii=False)
print({k: round(v, 2) for k, v in start.items()})
