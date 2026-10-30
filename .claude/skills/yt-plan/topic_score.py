#!/usr/bin/env python3
"""topic_score.py - choose a long-form topic BEFORE the script, on the growth rubric. Zero dependencies.

    python3 topic_score.py topics.json              # JSON ranking
    python3 topic_score.py topics.json --markdown   # table for the run report

topics.json: {"topics": [{"id", "title", "scores": {...}, "evidence": {...}, ...}]}

Each criterion is scored 1-5 by a person or Claude, and each score needs a line of EVIDENCE (a source,
an outlier-scan row, a footage licence) - a score without evidence is reported, because a number
nobody can check is a guess.

    us_interest  broad US audience would care (search demand, news reach, everyday relevance)
    novelty      the verified facts are genuinely surprising, not the usual explainer
    hook         an honest emotional or visual hook exists for the first 3-15 s
    thumbnail    one clear subject that raises one concrete question on a phone screen
    rights       legal, good-quality footage/stills available             (GATE: < 3 blocks)
    facts        primary sources confirm the claims we would make         (GATE: < 3 blocks)
    proof        comparable videos already beat their channel baseline (outliers.py: >= 3x with
                 enough data = 5, 1.5-3x = 3-4, none found = 2, not checked = 1)
    length_fit   the story fills 6-8 minutes without padding               (GATE: < 3 blocks)

Gate evidence must be VERIFIABLE: rights, facts and length_fit each need a URL or a path to a file
(media.json, a run report, an outline). Without it the topic is "HOLD (unverified gates)", never
GO-CANDIDATE, whatever the scores say.

Rule: a topic is never chosen on competitor views alone. If "proof" is its only score >= 4 the topic is
HOLD (competitor-only), whatever the total.
"""
import json, re, sys

CRITERIA = {"us_interest": 1.0, "novelty": 1.0, "hook": 1.0, "thumbnail": 1.0, "rights": 1.5,
            "facts": 1.5, "proof": 0.75, "length_fit": 1.0}
GATES = ("rights", "facts", "length_fit")
GO = 3.5


def verifiable(text):
    """Evidence a person can check: a URL, or a path to a file in the repo / run folder
    (e.g. research/runs/<run>/media.json). A bare claim ("NASA imagery is public domain") is not."""
    t = str(text or "")
    return bool(re.search(r"https?://\S+", t) or re.search(r"(?:^|\s)[\w.-]+(?:/[\w.-]+)+\.(?:json|md|txt|csv|pdf)\b", t))


def score(topic, criteria=CRITERIA, gates=GATES):
    s = topic.get("scores") or {}
    missing = [k for k in criteria if k not in s]
    if missing:
        raise ValueError(f"{topic.get('id')}: missing scores {missing}")
    for k in criteria:
        if not isinstance(s[k], (int, float)) or not 1 <= s[k] <= 5:
            raise ValueError(f"{topic.get('id')}: {k}={s[k]} outside 1..5")
    total = round(sum(s[k] * w for k, w in criteria.items()) / sum(criteria.values()), 2)
    blocked = [g for g in gates if s[g] < 3]
    ev = topic.get("evidence") or {}
    no_evidence = [k for k in criteria if not ev.get(k)]
    strong = [k for k in criteria if s[k] >= 4]
    competitor_only = "proof" in criteria and strong == ["proof"]
    unverified = [g for g in gates if not verifiable(ev.get(g))]
    return total, blocked, no_evidence, competitor_only, unverified


def rank(topics, criteria=CRITERIA, gates=GATES):
    rows = []
    for t in topics:
        total, blocked, no_ev, comp, unver = score(t, criteria, gates)
        status = ("BLOCKED" if blocked else "HOLD (unverified gates)" if unver else "HOLD (competitor-only)" if comp
                  else "GO-CANDIDATE" if total >= GO else "HOLD")
        rows.append({**t, "total": total, "blocked_by": blocked, "unverified_gates": unver, "missing_evidence": no_ev,
                     "status": status})
    order = {"GO-CANDIDATE": 4, "HOLD": 3, "HOLD (unverified gates)": 2, "HOLD (competitor-only)": 1, "BLOCKED": 0}
    return sorted(rows, key=lambda r: (order[r["status"]], r["total"]), reverse=True)


def markdown(rows, criteria=CRITERIA):
    L = ["| # | Topic | " + " | ".join(criteria) + " | Total | Status |",
         "|---|---|" + "---|" * len(criteria) + "---|---|"]
    for i, r in enumerate(rows, 1):
        st = r["status"] + (f" ({', '.join(r['blocked_by'])})" if r["blocked_by"] else "")
        if r["unverified_gates"] and not r["blocked_by"]:
            st += f" ({', '.join(r['unverified_gates'])})"
        if r["missing_evidence"]:
            st += f"; no evidence: {', '.join(r['missing_evidence'])}"
        L.append(f"| {i} | {r['title']} | " + " | ".join(str(r["scores"][k]) for k in criteria) + f" | {r['total']} | {st} |")
    return "\n".join(L) + "\n"


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    files = [x for x in a if not x.startswith("--")]
    if not files or "-h" in a or "--help" in a:
        print(__doc__); return 0 if not files and ("-h" in a or "--help" in a) else 2
    try:
        with open(files[0], encoding="utf-8") as f:
            rows = rank(json.load(f)["topics"])
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(json.dumps({"result": "ERROR", "error": f"{type(e).__name__}: {e}"})); return 2
    print(markdown(rows) if "--markdown" in a else json.dumps(rows, ensure_ascii=False, indent=2), end="" if "--markdown" in a else "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
