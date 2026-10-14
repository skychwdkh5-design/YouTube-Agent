#!/usr/bin/env python3
"""topics.py - choose the best topic by a fixed scoring system, decide alone when the advantage is provable, and document why.

    python3 tools/autopilot/topics.py score CANDIDATES.json [--out research/topic_decision.json]

CANDIDATES.json: {"candidates": [{"id", "title", "scores": {...}, "rationale": {criterion: "why this score"},
                                  "evidence_urls": [...], "audience_signals": [{"metric", "value", "url", "retrieved"}],
                                  "assets": {"free_imagery": [...], "checked": "YYYY-MM-DD"}}]}
Scores are 1-5 integers/floats chosen by the agent WITH a rationale; the tool applies the rules identically every time:

  criterion         weight  what it measures
  us                 .16    US audience potential (CLAUDE.md: dominant single audience criterion)
  audience_evidence  .12    confirmed demand: 5 needs measured public signals (view counts, search interest, comments) with URL+date.
                            Without a measured signal the score is capped at 3 - a metric is never invented.
  sources            .14    reliable primary/scientific sources reachable now (GATE: <= 2 or no https URL = out)
  visual             .12    strong visual material that is legally usable
  originality        .08    documentary angle not already covered the same way
  zero_cost          .12    the whole video can be made with free tools and free, licence-clean imagery (GATE: <= 2 = out)
  fit                .06    fits OrbitalAtlas: the story is visible from orbit / real geography + satellite evidence
  curiosity          .08    click and retention pull
  monetization       .04    advertiser-friendly, licence allows monetisation
  international      .04    other English-speaking markets
  sweden/norway/denmark .0133 each  never a gate, never forced (CLAUDE.md)

Decision: gated-out candidates lose to any candidate that passes. Among the rest, if the leader beats the runner-up by >= MARGIN
(0.25 on the 1-5 scale) the decision is `auto` (provable advantage). Otherwise it is a `tie_break`, decided by the fixed order
audience_evidence, us, zero_cost, originality, reach, then id - never by asking the owner - and the reason names the rule that decided.
"""
import json, sys

WEIGHTS = {"us": 0.16, "audience_evidence": 0.12, "sources": 0.14, "visual": 0.12, "originality": 0.08, "zero_cost": 0.12, "fit": 0.06,
           "curiosity": 0.08, "monetization": 0.04, "international": 0.04, "sweden": 0.0133, "norway": 0.0133, "denmark": 0.0134}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, sum(WEIGHTS.values())
GATES = {"sources": 2, "zero_cost": 2}                  # score <= this value = gated out
MARGIN = 0.25
EVIDENCE_CAP_WITHOUT_MEASUREMENT = 3
TIE_ORDER = ("audience_evidence", "us", "zero_cost", "originality")


def _num(s, k):
    v = s.get(k)
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not 1 <= v <= 5:
        raise ValueError(f"score {k!r} must be a number 1-5, got {v!r}")
    return float(v)


def _measured(c):
    return [x for x in c.get("audience_signals", []) if isinstance(x, dict) and x.get("metric") and x.get("value") is not None
            and str(x.get("url", "")).startswith("https://") and x.get("retrieved")]


def evaluate(c):
    """-> row with the weighted score, gate results and any caps applied (with their reasons)."""
    s = {k: _num(c["scores"], k) for k in WEIGHTS}
    notes = []
    if s["audience_evidence"] > EVIDENCE_CAP_WITHOUT_MEASUREMENT and not _measured(c):
        s["audience_evidence"] = float(EVIDENCE_CAP_WITHOUT_MEASUREMENT)
        notes.append(f"audience_evidence capped at {EVIDENCE_CAP_WITHOUT_MEASUREMENT}: no measured public signal (metric, value, https url, date) given")
    for k in c["scores"]:
        if k in WEIGHTS and not str((c.get("rationale") or {}).get(k, "")).strip():
            notes.append(f"no rationale for {k}")
    gates = []
    if s["sources"] <= GATES["sources"] or not [u for u in c.get("evidence_urls", []) if str(u).startswith("https://")]:
        gates.append("sources: no reliable reachable source")
    if s["zero_cost"] <= GATES["zero_cost"]:
        gates.append("zero_cost: cannot be produced with free licence-clean material")
    score = sum(s[k] * w for k, w in WEIGHTS.items())
    reach = (s["international"] + s["sweden"] + s["norway"] + s["denmark"]) / 4
    return {"id": c["id"], "title": c.get("title", c["id"]), "score": round(score, 3), "scores": s, "reach": round(reach, 3),
            "gated_out": gates, "notes": notes, "measured_signals": len(_measured(c))}


def rank(cands):
    rows = [evaluate(c) for c in cands]
    rows.sort(key=lambda r: (bool(r["gated_out"]), -r["score"], r["id"]))
    for n, r in enumerate(rows, 1): r["rank"] = n
    return rows


def decide(rows):
    """Pick the winner and say why. Returns {chosen_id, mode, margin, reason}."""
    live = [r for r in rows if not r["gated_out"]]
    if not live: raise ValueError("every candidate is gated out (no reliable source or no zero-cost path); research more topics")
    if len(live) == 1:
        return {"chosen_id": live[0]["id"], "mode": "auto", "margin": None, "reason": f"the only candidate passing the gates (others: " + "; ".join(f"{r['id']} {r['gated_out'][0]}" for r in rows if r["gated_out"]) + ")"}
    a, b = live[0], live[1]
    margin = round(a["score"] - b["score"], 3)
    if margin >= MARGIN:
        deltas = sorted(((a["scores"][k] - b["scores"][k]) * w, k) for k, w in WEIGHTS.items())
        top = [f"{k} {a['scores'][k]:g} vs {b['scores'][k]:g}" for d, k in reversed(deltas[-3:]) if d > 0]
        return {"chosen_id": a["id"], "mode": "auto", "margin": margin,
                "reason": f"provable advantage: {a['score']} vs {b['score']} (margin {margin} >= {MARGIN}); largest contributions: " + ", ".join(top)}
    tied = [r for r in live if a["score"] - r["score"] < MARGIN]
    for k in TIE_ORDER + ("reach",):
        key = (lambda r: r["reach"]) if k == "reach" else (lambda r, k=k: r["scores"][k])
        best = max(key(r) for r in tied)
        tied2 = [r for r in tied if key(r) == best]
        if len(tied2) < len(tied):
            tied = tied2
            if len(tied) == 1:
                return {"chosen_id": tied[0]["id"], "mode": "tie_break", "margin": margin,
                        "reason": f"scores within {MARGIN} (leader margin {margin}); decided by the fixed tie-break rule '{k}' ({best:g})"}
    tied.sort(key=lambda r: r["id"])
    return {"chosen_id": tied[0]["id"], "mode": "tie_break", "margin": margin, "reason": "exact tie on every rule; alphabetical id (documented, harmless)"}


def run(data):
    cands = data["candidates"]
    if len(cands) < 5: raise ValueError(f"research needs at least 5 candidates, got {len(cands)}")
    rows = rank(cands)
    d = decide(rows)
    chosen = next(c for c in cands if c["id"] == d["chosen_id"])
    return {"ok": True, "chosen_id": d["chosen_id"], "mode": d["mode"], "margin": d["margin"], "reason": d["reason"],
            "evidence_urls": chosen.get("evidence_urls", []), "us_hook": chosen.get("us_hook", ""), "ranking": rows,
            "rule": "gates (sources, zero_cost) -> weighted score -> auto if margin >= %.2f else fixed tie-break; the owner is not asked" % MARGIN}


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) < 2 or a[0] != "score":
        print(__doc__); return 2
    try:
        with open(a[1], encoding="utf-8") as f: out = run(json.load(f))
    except (OSError, ValueError, KeyError) as x:
        print(json.dumps({"ok": False, "error": f"{type(x).__name__}: {x}"})); return 2
    if "--out" in a:
        with open(a[a.index("--out") + 1], "w", encoding="utf-8") as f: json.dump(out, f, indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False)); return 0


if __name__ == "__main__":
    sys.exit(main())
