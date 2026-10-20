#!/usr/bin/env python3
"""yt-research: provenance-first research notes -> claims.json (confidence is DERIVED, never typed in).

The agent (Claude) does the reading and searching with its own tools; this tool makes that work auditable and
machine-usable:
  log    append an entry to research/provenance.jsonl (every search/fetch/read, including failures)
  fetch  try to read a URL from Python (reachability classified: ok | blocked | dns | timeout | http_<code>); never substitutes
  add    validate and append a note to research/notes.json
  build  notes.json -> claims.json (yt-facts/1) + research/report.md (coverage, gaps, factual capacity)
  status coverage report only

Confidence rules (build): primary source read in full -> high; secondary read in full with >= 2 independent outlets -> medium, 1 -> low;
search summary only: >= 2 independent outlets -> medium, else low; unreachable -> low. Observations: two independent checks -> high,
one -> medium, visual only -> low. Hypotheses are always low. A note cannot ask for more than its evidence gives.
"""
import argparse, hashlib, json, os, re, sys, time, urllib.error, urllib.request

KINDS = {"original", "media", "org", "science", "observation", "hypothesis"}
ACCESS = {"read", "summary_only", "unreachable"}
SRC_KIND = {"primary", "secondary", "search_summary", "own_data"}
WORDING = {"media": "reported", "org": "said", "science": "said"}
WORDS_PER_USABLE_CLAIM = 55      # heuristic: spoken words one usable (medium+) claim can honestly carry with context


class ResearchError(Exception):
    pass


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load(path, default):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default


def _save(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".part"
    json.dump(obj, open(tmp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def log_entry(root, **e):
    e = {"at": now(), **e}
    os.makedirs(os.path.join(root, "research"), exist_ok=True)
    with open(os.path.join(root, "research", "provenance.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return e


def fetch(root, url, timeout=20):
    """Read a URL; the outcome is logged whatever happens. Returns the log entry (with 'text' only in memory)."""
    status, body, err = "ok", b"", None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 OrbitalAtlas-research"})
        body = urllib.request.urlopen(req, timeout=timeout).read(2_000_000)
    except urllib.error.HTTPError as e:
        status, err = f"http_{e.code}", str(e)
    except urllib.error.URLError as e:
        r = str(e.reason)
        status = "blocked" if "403" in r or "Tunnel" in r else "dns" if "Name or service" in r or "ENOTFOUND" in r or "getaddrinfo" in r else "timeout" if "timed out" in r else "error"
        err = r
    except (OSError, ValueError) as e:
        status, err = "error", str(e)
    ent = log_entry(root, tool="fetch", url=url, status=status, bytes=len(body), sha256=hashlib.sha256(body).hexdigest() if body else None, error=err)
    ent["text"] = body.decode("utf8", "replace") if body else ""
    return ent


def validate_note(n):
    p = []
    for k in ("id", "kind", "statement", "short"):
        if not n.get(k):
            p.append(f"missing {k}")
    if n.get("kind") not in KINDS:
        p.append(f"kind must be one of {sorted(KINDS)}")
    if n.get("short") and len(n["short"]) > 44:
        p.append("short must be <= 44 characters (it is drawn on screen)")
    if n.get("kind") == "observation":
        if not n.get("evidence"):
            p.append("observation needs an evidence file")
        if n.get("basis") not in ("two_checks", "one_check", "visual_only"):
            p.append("observation needs basis: two_checks | one_check | visual_only")
    elif n.get("kind") == "hypothesis":
        pass
    else:
        s = n.get("source") or {}
        if not (s.get("outlet") and s.get("url") and s.get("date")):
            p.append("source needs outlet, url, date")
        if s.get("access") not in ACCESS:
            p.append(f"source.access must be one of {sorted(ACCESS)}")
        if s.get("kind") not in SRC_KIND - {"own_data"}:
            p.append("source.kind must be primary | secondary | search_summary")
        if not isinstance(n.get("independent_outlets"), int) or n["independent_outlets"] < 1:
            p.append("independent_outlets: integer >= 1 (outlets that independently report it, not retellings of one)")
    return p


def derive(n):
    """(confidence, reason)"""
    k = n["kind"]
    if k == "hypothesis":
        return "low", "hypothesis"
    if k == "observation":
        return {"two_checks": "high", "one_check": "medium", "visual_only": "low"}[n["basis"]], f"observation basis {n['basis']}"
    s, m = n["source"], n["independent_outlets"]
    if s["access"] == "unreachable":
        return "low", "source unreachable"
    if s["access"] == "read" and s["kind"] == "primary":
        return "high", "primary read"
    if s["access"] == "read":
        return ("medium", f"secondary read, {m} independent outlets") if m >= 2 else ("low", "secondary read, one outlet")
    return ("medium", f"search summary, {m} independent outlets") if m >= 2 else ("low", "search summary, one outlet")


def build(root):
    d = _load(os.path.join(root, "research", "notes.json"), None)
    if not d:
        raise ResearchError("research/notes.json missing")
    claims, seen, probs, rows = [], set(), [], []
    for i, n in enumerate(d["notes"], 1):
        pr = validate_note(n)
        if n.get("id") in seen:
            pr.append("duplicate id")
        seen.add(n.get("id"))
        if pr:
            probs.append(f"{n.get('id')}: " + "; ".join(pr))
            continue
        conf, why = derive(n)
        c = {"id": n["id"], "tier": n["kind"], "text": n["statement"], "short": n["short"], "confidence": conf, "confidence_reason": why}
        if n["kind"] in WORDING:
            c["wording"] = n.get("wording") or WORDING[n["kind"]]
        if n["kind"] == "original" and n.get("source"):
            c["wording"] = n.get("wording")      # originals need no attribution word
        if n.get("source"):
            s = n["source"]
            c.update(attribution=s["outlet"], date=s["date"], url=s["url"], source_access=s["access"], source_kind=s["kind"])
        for k in ("evidence", "forbid", "allow", "years", "focus", "check", "scale_km", "group", "must_cover", "callouts", "anchor", "visual", "compare_km", "hero_km"):
            if k in n:
                c[k] = n[k]
        claims.append(c)
        rows.append((c["id"], c["tier"], conf, why, c.get("source_access", "own data")))
    if probs:
        raise ResearchError("invalid notes: " + " | ".join(probs))
    out = {"schema": "yt-facts/1", "derived_from": "research/notes.json", "claims": claims}
    _save(os.path.join(root, "claims.json"), out)
    usable = [c for c in claims if c["confidence"] in ("medium", "high")]
    cap = len(usable) * WORDS_PER_USABLE_CLAIM
    gaps = [f"{c['id']} ({c.get('attribution') or c['tier']}): {c['confidence_reason']}" for c in claims if c["confidence"] == "low" and c["tier"] != "hypothesis"]
    unreachable = sorted({(n.get("source") or {}).get("url") for n in d["notes"] if (n.get("source") or {}).get("access") == "unreachable"} - {None})
    rep = ["# Research report", "", f"Built {now()} from {len(d['notes'])} notes.", "", "| id | tier | confidence | why | access |", "|---|---|---|---|---|"]
    rep += [f"| {a} | {b} | {c} | {w} | {x} |" for a, b, c, w, x in rows]
    rep += ["", f"Usable claims (medium+): {len(usable)} of {len(claims)}. Heuristic factual capacity: about {cap} spoken words (~{cap / 2.45 / 60:.1f} min) at {WORDS_PER_USABLE_CLAIM} words per usable claim.",
            "Unusable (low) claims, not for the script: " + (", ".join(gaps) or "none"), "Unreachable sources (not substituted): " + (", ".join(unreachable) or "none")]
    if cap / 2.45 < 360:
        rep.append("**INSUFFICIENT_FOR_6_MIN**: the verified facts carry less than 6 minutes; the video should be shorter or the research deepened. Do not pad.")
    open(os.path.join(root, "research", "report.md"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
    return {"status": "ok", "claims": len(claims), "usable": len(usable), "capacity_words": cap, "capacity_minutes": round(cap / 2.45 / 60, 1),
            "low_claims": gaps, "unreachable": unreachable, "insufficient_for_6_min": cap / 2.45 < 360}


def add_note(root, note):
    pr = validate_note(note)
    if pr:
        raise ResearchError("; ".join(pr))
    p = os.path.join(root, "research", "notes.json")
    d = _load(p, {"schema": "yt-research/1", "notes": []})
    if any(n["id"] == note["id"] for n in d["notes"]):
        raise ResearchError(f"note {note['id']} exists")
    d["notes"].append(note)
    _save(p, d)
    return {"status": "ok", "notes": len(d["notes"])}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=".", help="episode folder")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("log"); p.add_argument("--tool", required=True); p.add_argument("--query"); p.add_argument("--url"); p.add_argument("--status", required=True); p.add_argument("--note")
    p = sub.add_parser("fetch"); p.add_argument("url")
    p = sub.add_parser("add"); p.add_argument("--json", required=True, help="a note as JSON")
    sub.add_parser("build"); sub.add_parser("status")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "log":
            r = log_entry(a.root, tool=a.tool, query=a.query, url=a.url, status=a.status, note=a.note)
        elif a.cmd == "fetch":
            r = fetch(a.root, a.url); r.pop("text", None)
        elif a.cmd == "add":
            r = add_note(a.root, json.loads(a.json))
        else:
            r = build(a.root)
        print(json.dumps(r, indent=1, ensure_ascii=False))
        return 0
    except (ResearchError, ValueError, OSError) as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
