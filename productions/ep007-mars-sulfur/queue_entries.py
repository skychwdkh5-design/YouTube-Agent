"""Append EP007 entries to publish/queue.json and set publish/media.json (bundle ep007-v1) in a publish checkout.
Owner approval: chat 2026-10-28 15:59 ICT (script, edit, title #1, cover B, schedule) - recorded verbatim below.
python3 queue_entries.py <publish_checkout> <manifest.json: {asset: {sha256, size, seconds}}> [long_video_id]"""
import json, os, sys
root, man = sys.argv[1], json.load(open(sys.argv[2]))
long_id = None
CHAT = "--chat" in sys.argv   # publish-data: the approval record replaces owner_approval
texts = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "package", "texts.json")))
desc_long = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "package", "description_long.txt")).read()
APPROVAL_NOTE = "Owner in chat 2026-10-28 15:59 ICT: script and edit approved; title #1; cover B; schedule 29.10 08:00, 29.10 12:00, 30.10 12:00 (Asia/Ho_Chi_Minh)."
SCHED = {"ep007": "2026-10-29T01:00:00Z", "short-07-ep007": "2026-10-29T05:00:00Z", "short-08-ep007": "2026-10-30T05:00:00Z"}
ASSET = {"ep007": "EP007_final_long.mp4", "short-07-ep007": "EP007_final_short1.mp4", "short-08-ep007": "EP007_final_short2.mp4"}
TAGS = ["Mars", "Curiosity rover", "NASA", "sulfur", "Gediz Vallis", "Gale crater", "Mount Sharp", "space", "planetary science", "OrbitalAtlas"]
BASIS = "Narration is a stock text-to-speech voice (ElevenLabs Adam), not a real person's voice; imagery is real NASA rover/orbiter data with labelled schematic graphics. No realistic fabricated people or events, so YouTube's altered-or-synthetic label is not required. The description states the voice."


def entry(i, kind, title, desc, extra):
    a = ASSET[i]; m = man[a]
    e = {"id": i, "mode": "approval" if kind == "long" else "autopilot", "kind": kind,
         "media": {"asset": a, "sha256": m["sha256"], "seconds": m["seconds"]}, "title": title, "title_status": "final",
         "description": desc, "tags": TAGS, "category_id": "27", "default_language": "en", "made_for_kids": False,
         "contains_synthetic_media": False, "disclosure_basis": BASIS, "thumbnail": None, "captions": None,
         "publish_at": SCHED[i], "related": None,
         "owner_approval": ({"approved": False, "sha256": None, "publish_at": None} if CHAT else
                            {"approved": True, "sha256": m["sha256"], "publish_at": SCHED[i], "note": APPROVAL_NOTE})}
    e.update(extra)
    return e


q = json.load(open(os.path.join(root, "publish", "queue.json")))
q["items"] = [x for x in q["items"] if not x["id"].endswith("ep007") and x["id"] != "ep007"]
thumb = "publish/assets/ep007/thumbnail_B.jpg"
import hashlib
tsha = hashlib.sha256(open(os.path.join(root, thumb), "rb").read()).hexdigest()
items = [entry("ep007", "long", texts["long"]["title"], desc_long, {
    "thumbnail": thumb, "captions": {"file": "publish/assets/ep007/captions.srt", "language": "en", "name": "English"},
    "thumbnail_review": {"result": "PASS", "sha256": tsha, "note": "Cover B 'CRACKED OPEN': thumbcheck objective PASS; checked full size and at 168x94 against the four published covers by Claude.",
                         "owner_approved": True, "owner_approved_note": "Owner chose cover B in chat 2026-10-28 15:59 ICT; applies to this exact file."}})]
for sid, key in (("short-07-ep007", "short1"), ("short-08-ep007", "short2")):
    d = texts[key]["description"]
    d = d.replace("\n\nImages:", "\n\nFull episode on OrbitalAtlas: \u201c" + texts["long"]["title"] + "\u201d\n\nImages:")
    items.append(entry(sid, "short", texts[key]["title"], d, {}))
q["items"] += items
q["_note_ep007"] = "EP007: long 29.10 08:00 ICT = 01:00Z; Shorts 29.10 and 30.10 12:00 ICT = 05:00Z."
json.dump(q, open(os.path.join(root, "publish", "queue.json"), "w"), indent=1, ensure_ascii=False)
json.dump({"bundle": "ep007-v1", "files": [{"asset": a, "sha256": man[a]["sha256"], "size": man[a]["size"],
           "source": {"release": "ep007-v1"}} for a in ASSET.values()]},
          open(os.path.join(root, "publish", "media.json"), "w"), indent=1)
print(json.dumps({i["id"]: [i["publish_at"], i["media"]["sha256"][:12]] for i in items}))
