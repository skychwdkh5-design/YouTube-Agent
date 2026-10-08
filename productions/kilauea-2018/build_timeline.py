"""Final timeline: the approved storyboard v2, re-flowed onto Adam's real word timings.
Same shots, views, imagery and overlays; only times move. Shot starts are word anchors."""
import json
W = json.load(open("voice/narration.voice.json"))["words"]
tl = json.load(open("timeline_storyboard.json"))
# line -> first word index (from the approved script, in order)
FIRST = {"S1_hook": 0, "S2_proof": 9, "S3_eruption": 13, "S4_heat": 26, "S5_flow": 34, "S6_bay": 44,
         "S7_scale": 58, "S8_rift": 69, "S9_collapse": 77, "S10_newland": 86, "S11_owner": 95}
OFF = -0.2                                      # cut a beat before the line starts
start = {k: (0.0 if i == 0 else max(0.0, W[i]["start"] + OFF)) for k, i in FIRST.items()}
def rel(shot, word, extra=0.0):                 # word time relative to the shot start
    return round(W[word]["start"] + extra - start[shot], 2)
for s in tl["shots"]:
    sid = s["id"]; i = FIRST[sid]
    s["start"] = 0 if i == 0 else {"word": i, "edge": "start", "offset": OFF}
    for L in s["layers"]:
        tx = L.get("text")
        if sid == "S3_eruption" and tx == "ERUPTION BEGINS": L["t"] = [0.2, rel(sid, 24, -0.3)]
        if sid == "S3_eruption" and tx == "24 FISSURES":    L["t"] = [rel(sid, 24), None]
        if sid == "S6_bay":
            w0 = rel(sid, 51, -0.1)                              # "By June 7th"
            if L["type"] == "wipe": L["t"] = [w0, w0 + 0.8]
            if tx == "JUNE 3: LAVA ARRIVES": L["t"] = [0.0, w0]
            if tx == "JUNE 7: BAY GONE": L["t"] = [round(w0 + 1.4, 2), None]
        if sid == "S7_scale" and tx == "1,839 STRUCTURES": L["t"] = [rel(sid, 64), None]
        if sid == "S9_collapse" and tx == "−1,600 FT": L["t"] = [max(1.8, rel(sid, 80)), None]
        if sid == "S10_newland" and tx == "+875 ACRES": L["t"] = [rel(sid, 87), None]
        if sid == "S11_owner" and tx == "WHO OWNS IT?": L["t"] = [0.0, rel(sid, 106)]
        if sid == "S11_owner" and tx == "THE STATE OF HAWAII": L["t"] = [rel(sid, 106), None]
tl["voice"] = {"src": "voice/narration.wav", "meta": "voice/narration.voice.json"}
tl["captions"] = {"src": "captions/captions.srt", "preset": "short"}
tl["end"] = {"after_last_word": 1.5, "min_total": 45.0}
tl["meta"] = {"title": "Kilauea 2018 - A bay disappeared", "claims": "story/claims.json",
              "provenance": "stack/provenance.json", "storyboard": "timeline_storyboard.json (approved v2)"}
json.dump(tl, open("timeline.json", "w"), indent=1, ensure_ascii=False)
print({k: round(v, 2) for k, v in start.items()})
