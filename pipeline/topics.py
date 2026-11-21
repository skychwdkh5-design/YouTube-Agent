#!/usr/bin/env python3
"""topics.py - the topic reserve of each channel: candidates, exclusions, gates and the next topic to produce.

    python3 pipeline/topics.py add   --channel oa --file candidates.json     # research results (Claude / scout)
    python3 pipeline/topics.py next  --channel oa [--inventory status.json]  # best topic that passes every gate
    python3 pipeline/topics.py mark  --channel oa --id T --status used|rejected|hold --reason "..."
    python3 pipeline/topics.py list  --channel oa
    python3 pipeline/topics.py gap   --channel oa --what "vidIQ" --detail "0 credits until 2026-11-29"

A candidate: {"id", "title", "angle", "primary_sources": [url...], "media": [{"url", "licence", "credit", "kind"}],
"nasa_involved": bool, "scores": {us_interest, novelty, hook, thumbnail, rights, facts, proof, length_fit} (1-5, as
/yt-plan topic_score.py), "evidence": {criterion: "url or file"}, "outliers": [rows from scout], "found_by": "..."}

Gates (a topic that fails one is skipped and the next one is taken):
  * not a repeat: compared with every title on the channel and every topic already used or rejected;
  * at least 2 primary sources (agency, paper, official data) - no source, no topic;
  * enough licensed footage/stills: >= 6 media items with an allowed licence (OA: NASA/USGS/NOAA/ESA/Wikimedia CC);
  * topic_score gates rights/facts/length_fit >= 3 and never chosen on competitor views alone.
Ranking: US interest first (project rule), then total score; for Orbital Atlas a real NASA role in the story adds a bonus
(the channel's audience responds to NASA) - it is never added to a story where NASA is not actually part of it.
"""
import argparse, json, os, re, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine as E  # noqa: E402

DEFAULT_STATE = os.environ.get("PIPELINE_STATE", os.path.abspath(os.path.join(HERE, "..", "..", "pipeline-data", "pipeline")))
ALLOWED_MEDIA = re.compile(r"public domain|\bPD\b|CC0|CC BY|NASA|USGS|NOAA|Copernicus|ESA", re.I)
FORBIDDEN_MEDIA = re.compile(r"spacex|esri|maxar|airbus|planet labs|google earth|getty|shutterstock|reuters|\bAP\b", re.I)
PRIMARY = re.compile(r"\.(gov|mil|edu|int)(/|$)|nasa\.gov|esa\.int|usgs\.gov|noaa\.gov|nature\.com|science\.org|agu\.org|arxiv\.org|"
                     r"doi\.org|copernicus\.eu|jpl\.nasa|svs\.gsfc|ieee\.org|sciencedirect|springer|wiley", re.I)
CRITERIA = ("us_interest", "novelty", "hook", "thumbnail", "rights", "facts", "proof", "length_fit")


def path(state, ch):
    return os.path.join(state, "topics", f"{ch}.json")


def load(state, ch):
    p = path(state, ch)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"channel": ch, "topics": [], "gaps": []}


def save(state, ch, doc):
    p = path(state, ch)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + ".tmp", "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    os.replace(p + ".tmp", p)


def gates(t, ch, used_titles):
    why = []
    for title in used_titles:
        if E.topic_similar(title, t.get("title", "")):
            why.append(f"repeat of '{title}'")
            break
    prim = [u for u in t.get("primary_sources", []) if PRIMARY.search(u)]
    if len(prim) < 2:
        why.append(f"{len(prim)} primary sources (need 2)")
    ok_media = [m for m in t.get("media", []) if ALLOWED_MEDIA.search(m.get("licence", "") + " " + m.get("credit", ""))
                and not FORBIDDEN_MEDIA.search(m.get("url", "") + " " + m.get("credit", ""))]
    if len(ok_media) < 6:
        why.append(f"{len(ok_media)} licensed media items (need 6)")
    sc = t.get("scores") or {}
    for g in ("rights", "facts", "length_fit"):
        if sc.get(g, 0) < 3:
            why.append(f"{g} score {sc.get(g, 0)} < 3")
    if sc and max((v for k, v in sc.items() if k != "proof"), default=0) < 4 and sc.get("proof", 0) >= 4:
        why.append("competitor views only")
    return why


def rank_key(t, ch):
    sc = t.get("scores") or {}
    bonus = 2 if ch == "oa" and t.get("nasa_involved") else 0
    return (sc.get("us_interest", 0), sum(sc.get(k, 0) for k in CRITERIA) + bonus)


def used_titles(state, ch, inventory):
    titles = [v["title"] for v in inventory if v.get("title")]
    titles += [(r.get("topic") or {}).get("title", "") for r in E.all_releases(state) if r["channel"] == ch and not r.get("test")]
    doc = load(state, ch)
    titles += [t["title"] for t in doc["topics"] if t.get("status") in ("used", "rejected")]
    return [t for t in titles if t]


def cmd_add(a):
    doc = load(a.state, a.channel)
    new = json.load(open(a.file, encoding="utf-8"))
    have = {t["id"] for t in doc["topics"]}
    added = 0
    for t in new if isinstance(new, list) else new.get("topics", []):
        if t["id"] in have:
            continue
        t.setdefault("status", "candidate"); t.setdefault("added_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        doc["topics"].append(t); added += 1
    save(a.state, a.channel, doc)
    return {"added": added, "reserve": sum(1 for t in doc["topics"] if t.get("status") == "candidate")}


def cmd_next(a):
    doc = load(a.state, a.channel)
    inv = (json.load(open(a.inventory)).get("videos") or []) if a.inventory else []
    used = used_titles(a.state, a.channel, inv)
    skipped, best = [], None
    for t in sorted([t for t in doc["topics"] if t.get("status") == "candidate"], key=lambda t: rank_key(t, a.channel), reverse=True):
        why = gates(t, a.channel, used)
        if why:
            skipped.append({"id": t["id"], "why": why})
            continue
        best = t
        break
    reserve = sum(1 for t in doc["topics"] if t.get("status") == "candidate")
    return {"next": best, "skipped": skipped, "reserve": reserve, "reserve_low": reserve < 5}


def cmd_mark(a):
    doc = load(a.state, a.channel)
    t = next(t for t in doc["topics"] if t["id"] == a.id)
    t["status"], t["status_reason"] = a.status, a.reason
    save(a.state, a.channel, doc)
    return {"id": a.id, "status": a.status}


def cmd_gap(a):
    doc = load(a.state, a.channel)
    doc["gaps"].append({"at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "what": a.what, "detail": a.detail})
    save(a.state, a.channel, doc)
    return {"logged": a.what}


def cmd_list(a):
    doc = load(a.state, a.channel)
    return {"topics": [{k: t.get(k) for k in ("id", "title", "status", "nasa_involved")} for t in doc["topics"]], "gaps": doc["gaps"][-10:]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", default=DEFAULT_STATE)
    s = ap.add_subparsers(dest="cmd", required=True)
    x = s.add_parser("add"); x.add_argument("--channel", required=True); x.add_argument("--file", required=True)
    x = s.add_parser("next"); x.add_argument("--channel", required=True); x.add_argument("--inventory")
    x = s.add_parser("mark"); x.add_argument("--channel", required=True); x.add_argument("--id", required=True)
    x.add_argument("--status", required=True, choices=["used", "rejected", "hold", "candidate"]); x.add_argument("--reason", default="")
    x = s.add_parser("gap"); x.add_argument("--channel", required=True); x.add_argument("--what", required=True); x.add_argument("--detail", default="")
    x = s.add_parser("list"); x.add_argument("--channel", required=True)
    a = ap.parse_args(argv)
    print(json.dumps(globals()["cmd_" + a.cmd](a), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
