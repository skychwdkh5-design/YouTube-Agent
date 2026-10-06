#!/usr/bin/env python3
"""topicscore.py - rank the idea backlog by viral potential, with verification as a hard gate.

    python3 topicscore.py channel/ideas.md
    python3 topicscore.py channel/ideas.md --top 10 --json

THE BACKLOG is a markdown table, one row per idea, every criterion scored 1-5:

    | ID | Topic | Pillar | Region | Click | Gap | Interest | Outlier | Visual | Story | Verify | US | Evidence | Status |

  Click     would a U.S. viewer click the title + thumbnail on a home feed?
  Gap       is there a question they cannot answer themselves?
  Interest  proven demand - search volume, comment questions, recurring Reddit/forum interest
  Outlier   did a similar video beat its own channel's median? (yt-viral multiple)
  Visual    can the core idea be SHOWN on a map in one frame?
  Story     is there a cause, a conflict and a payoff, not just a fact?
  Verify    can the key claims be confirmed from primary sources?
  US        will a U.S. viewer understand why it matters without a lecture?

Weights follow the channel's selection order. The U.S. is the AUDIENCE, not a topic filter: Region is
recorded but never scored, so a global topic wins whenever it is the stronger idea.

Two rules the arithmetic cannot be talked out of:
  - Verify below 3 is REJECTED whatever else it scores. A viral topic we cannot check is a liability.
  - Interest or Outlier of 4-5 with an empty Evidence cell is counted as 3. Proven means shown.

Status DONE, DROPPED or PUBLISHED rows are skipped.
"""
import json, re, sys

WEIGHTS = {"click": .20, "gap": .20, "interest": .15, "outlier": .15, "visual": .10, "story": .10, "us": .10}
SKIP = {"DONE", "DROPPED", "PUBLISHED"}

def cells(line): return [c.strip() for c in line.strip().strip("|").split("|")]

def parse(path):
    rows, header = [], None
    for line in open(path, encoding="utf-8"):
        if not line.strip().startswith("|"):
            if header is not None: break      # only the first table is the data; later tables are notes
            continue
        c = cells(line)
        if all(re.fullmatch(r":?-{2,}:?", x) for x in c if x): continue
        if header is None: header = [h.lower() for h in c]; continue
        r = dict(zip(header, c + [""] * (len(header) - len(c))))
        if r.get("id") and r.get("topic"): rows.append(r)
    return rows

def num(v):
    m = re.search(r"[1-5]", v or "")
    return int(m.group(0)) if m else None

def score(r):
    notes, vals = [], {}
    for k in list(WEIGHTS) + ["verify"]:
        v = num(r.get(k))
        if v is None: notes.append(f"{k} not scored"); v = 1
        vals[k] = v
    if not r.get("evidence", "").strip():
        for k in ("interest", "outlier"):
            if vals[k] > 3: notes.append(f"{k} {vals[k]} without evidence - counted as 3"); vals[k] = 3
    total = round(sum(WEIGHTS[k] * vals[k] for k in WEIGHTS) / 5 * 100)
    if vals["verify"] < 3: verdict = "REJECTED"
    elif vals["verify"] == 3: verdict = "CAUTION"
    else: verdict = "GO" if total >= 70 else "MAYBE" if total >= 55 else "WEAK"
    return total, verdict, vals, notes

def main():
    a = sys.argv[1:]
    as_json = "--json" in a
    top = int(a[a.index("--top") + 1]) if "--top" in a else 10
    files = [x for x in a if not x.startswith("--") and not x.isdigit()]
    if not files: print(__doc__); sys.exit(2)
    out = []
    for r in parse(files[0]):
        if (r.get("status") or "").upper() in SKIP: continue
        total, verdict, vals, notes = score(r)
        out.append({"id": r["id"], "topic": r["topic"], "pillar": r.get("pillar", ""), "region": r.get("region", ""),
                    "score": total, "verdict": verdict, "criteria": vals, "notes": notes})
    order = {"GO": 0, "MAYBE": 1, "CAUTION": 2, "WEAK": 3, "REJECTED": 4}
    out.sort(key=lambda x: (order[x["verdict"]] == 4, -x["score"]))
    live = [x for x in out if x["verdict"] != "REJECTED"][:top]
    pillars = {}
    for x in live[:5]: pillars[x["pillar"]] = pillars.get(x["pillar"], 0) + 1
    crowd = [p for p, n in pillars.items() if n > 3]
    if as_json:
        print(json.dumps({"ranked": out, "top_pillar_mix": pillars, "pillar_warning": crowd}, indent=1)); return
    print(f"\n  {files[0]}: {len(out)} open ideas\n")
    for x in out[:top] + [x for x in out[top:] if x["verdict"] == "REJECTED"]:
        print(f"    {x['score']:3d}  {x['verdict']:<8} {x['id']:<5} {x['topic'][:58]:<58} [{x['pillar']}] {x['region']}")
        for n in x["notes"]: print(f"                    note: {n}")
    if crowd: print(f"\n  heads-up: the top five lean on one pillar ({', '.join(crowd)}) - fine for a week, not for a month")
    print()

if __name__ == "__main__":
    main()
