#!/usr/bin/env python3
"""topics.py - rank candidate topics by the CLAUDE.md audience strategy (a decision aid, not an oracle).

    python3 tools/autopilot/topics.py score candidates.json [--out ranked.json]

candidates.json: {"candidates": [{"id", "title", "scores": {"us", "sweden", "norway", "denmark",
"international", "visual", "curiosity", "evidence", "satellite" (or null), "monetization"}, "evidence_urls": [...]}]}
Scores are 1-5 and are the agent's judgement - the tool only applies the project's rules consistently:
 - the US score dominates (weight 0.30); Sweden/Norway/Denmark are small tie-breakers and never gate a topic;
 - evidence is a hard gate: a topic with evidence <= 2 or no evidence URL loses to any topic with evidence;
 - near-ties on the US score (within 0.5) are broken by international + Scandinavian potential.
"""
import json, sys

WEIGHTS = {"us": 0.30, "sweden": 0.03, "norway": 0.03, "denmark": 0.03, "international": 0.08, "visual": 0.12,
           "curiosity": 0.12, "evidence": 0.14, "satellite": 0.05, "monetization": 0.10}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def _val(s, k):
    v = s.get(k)
    if v is None and k == "satellite": return None
    if not isinstance(v, (int, float)) or not 1 <= v <= 5:
        raise ValueError(f"score {k!r} must be a number 1-5, got {v!r}")
    return float(v)


def weighted(s):
    """Weighted score 1-5. A null satellite score (imagery not relevant) is dropped and the rest renormalised."""
    use = {k: w for k, w in WEIGHTS.items() if _val(s, k) is not None}
    tot = sum(use.values())
    return sum(_val(s, k) * w for k, w in use.items()) / tot


def reach(s):
    return (_val(s, "international") + _val(s, "sweden") + _val(s, "norway") + _val(s, "denmark")) / 4


def rank(cands):
    rows = []
    for c in cands:
        s = c["scores"]
        gated = _val(s, "evidence") <= 2 or not c.get("evidence_urls")
        rows.append({"id": c["id"], "title": c.get("title", c["id"]), "score": round(weighted(s), 3), "us": _val(s, "us"),
                     "reach": round(reach(s), 3), "evidence_gate_failed": gated})
    # evidence gate first, then weighted score; near-ties on US decided by reach
    rows.sort(key=lambda r: (r["evidence_gate_failed"], -r["score"]))
    for i in range(len(rows) - 1):                 # bubble pass for US near-ties inside the same gate class
        a, b = rows[i], rows[i + 1]
        if a["evidence_gate_failed"] == b["evidence_gate_failed"] and abs(a["us"] - b["us"]) <= 0.5 \
                and abs(a["score"] - b["score"]) <= 0.15 and b["reach"] > a["reach"]:
            rows[i], rows[i + 1] = b, a
    for n, r in enumerate(rows, 1): r["rank"] = n
    return rows


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) < 2 or a[0] != "score":
        print(__doc__); return 2
    try:
        data = json.load(open(a[1], encoding="utf-8"))
        rows = rank(data["candidates"])
    except (OSError, ValueError, KeyError) as x:
        print(json.dumps({"ok": False, "error": str(x)})); return 2
    out = {"ok": True, "ranking": rows, "rule": "evidence gate, then US-dominant weighted score, near-ties by international+Scandinavian reach"}
    if "--out" in a:
        with open(a[a.index("--out") + 1], "w", encoding="utf-8") as f: json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1)); return 0


if __name__ == "__main__":
    sys.exit(main())
