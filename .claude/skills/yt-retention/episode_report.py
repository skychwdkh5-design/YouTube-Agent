#!/usr/bin/env python3
"""episode_report.py - post-publication report for one long episode, compared fairly with earlier ones.

    python3 episode_report.py metrics.json --history history.jsonl [--retention retention.csv] [--markdown]
    python3 episode_report.py metrics.json --history history.jsonl --append      # add this snapshot to history

metrics.json (one episode, one snapshot - fill from YouTube Studio exports or any analytics source):
    {"episode": "EP007", "published": "2026-11-02", "as_of": "2026-11-09", "duration_s": 452,
     "impressions": 18400, "views": 1210, "ctr_pct": 5.1,
     "traffic": {"browse": {"impressions": 12000, "ctr_pct": 4.2}, "search": {"impressions": 3100, "ctr_pct": 8.0},
                 "suggested": {"impressions": 3300, "ctr_pct": 5.3}},
     "retention_30s_pct": 71.0, "avg_view_duration_s": 151, "avg_pct_viewed": 33.4,
     "ab_test": {"variants": {"A": 0.52, "B": 0.31, "C": 0.17}, "metric": "watch time share", "winner": "A"},
     "hypotheses": [{"id": "H1", "statement": "Subject in first 3 s raises 30 s retention",
                     "metric": "retention_30s_pct", "direction": "higher"}]}

Fair comparison: only earlier snapshots at a similar AGE (days since publish, within +-30 %) are compared;
differences in duration (> 20 %) and traffic mix (browse share differs > 15 points) are named as
confounders. Small samples are "inconclusive": < 1,000 impressions for CTR, < 100 views for retention.
A hypothesis is "supported" / "not supported" / "inconclusive" against the median of comparable episodes,
with a noise margin. This is correlation; the report says so and never claims a cause.
"""
import csv, datetime as dt, json, os, statistics, sys

AGE_TOL = 0.30
DUR_TOL = 0.20
MIX_TOL = 15.0
MIN_IMPR, MIN_VIEWS = 1000, 100
MARGIN = {"ctr_pct": 0.5, "retention_30s_pct": 3.0, "avg_view_duration_s": 10.0, "avg_pct_viewed": 2.0}
METRICS = ("ctr_pct", "retention_30s_pct", "avg_view_duration_s", "avg_pct_viewed")


def _d(s):
    return dt.date.fromisoformat(str(s)[:10])


def age(m):
    return (_d(m["as_of"]) - _d(m["published"])).days


def browse_share(m):
    t = m.get("traffic") or {}
    tot = sum((v or {}).get("impressions") or 0 for v in t.values())
    return round(100.0 * ((t.get("browse") or {}).get("impressions") or 0) / tot, 1) if tot else None


def comparable(cur, hist):
    a = max(age(cur), 1)
    out, notes = [], []
    for h in hist:
        if h.get("episode") == cur.get("episode"):
            continue
        if abs(age(h) - a) > AGE_TOL * a:
            continue
        conf = []
        if cur.get("duration_s") and h.get("duration_s") and abs(h["duration_s"] - cur["duration_s"]) > DUR_TOL * cur["duration_s"]:
            conf.append("duration")
        bc, bh = browse_share(cur), browse_share(h)
        if bc is not None and bh is not None and abs(bc - bh) > MIX_TOL:
            conf.append("traffic mix")
        out.append(h)
        if conf:
            notes.append(f"{h['episode']}: differs in {', '.join(conf)}")
    return out, notes


def enough(m, metric):
    if metric == "ctr_pct":
        return (m.get("impressions") or 0) >= MIN_IMPR
    return (m.get("views") or 0) >= MIN_VIEWS


def retention_curve(path, duration):
    pts = []
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        for row in csv.reader(fh):
            try:
                x, y = float(row[0].strip().rstrip("%")), float(row[1].strip().rstrip("%"))
            except (ValueError, IndexError):
                continue
            pts.append((x, y))
    if len(pts) < 8:
        return None
    pct_axis = max(x for x, _ in pts) <= 100.5 and duration
    pts = [((x / 100.0 * duration) if pct_axis else x, y) for x, y in pts]
    dips, peaks = [], []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 < 30:
            continue                                  # the hook leak is reported separately
        if y0 - y1 >= 3.0:
            dips.append({"t": round(x1, 1), "drop_pts": round(y0 - y1, 1)})
        if y1 - y0 >= 1.5:
            peaks.append({"t": round(x1, 1), "rise_pts": round(y1 - y0, 1)})
    at30 = next((y for x, y in pts if x >= 30), None)
    return {"at_30s_pct": at30, "dips": sorted(dips, key=lambda d: -d["drop_pts"])[:5],
            "peaks": sorted(peaks, key=lambda p: -p["rise_pts"])[:3]}


def build(cur, hist, retention=None):
    comps, notes = comparable(cur, hist)
    med = {k: statistics.median([h[k] for h in comps if h.get(k) is not None])
           for k in METRICS if any(h.get(k) is not None for h in comps)}
    rows = []
    for k in METRICS:
        v = cur.get(k)
        rows.append({"metric": k, "value": v, "comparable_median": med.get(k),
                     "delta": round(v - med[k], 2) if v is not None and k in med else None,
                     "sample_ok": enough(cur, k)})
    hyps = []
    for h in cur.get("hypotheses") or []:
        k, want = h.get("metric"), h.get("direction", "higher")
        v, base = cur.get(k), med.get(k)
        if v is None or base is None or not enough(cur, k) or len(comps) < 2:
            res = "inconclusive"
            why = "no comparable episodes" if len(comps) < 2 else "sample too small" if v is not None and base is not None else "metric missing"
        else:
            diff = v - base
            m = MARGIN.get(k, 0)
            if abs(diff) <= m:
                res, why = "inconclusive", f"within the noise margin ({m})"
            elif (diff > 0) == (want == "higher"):
                res, why = "supported", f"{v} vs median {base} of {len(comps)} comparable episodes"
            else:
                res, why = "not supported", f"{v} vs median {base} of {len(comps)} comparable episodes"
        hyps.append({**h, "result": res, "why": why})
    return {"episode": cur.get("episode"), "age_days": age(cur), "comparable_episodes": [h["episode"] for h in comps],
            "confounders": notes, "metrics": rows, "traffic": cur.get("traffic"), "browse_share_pct": browse_share(cur),
            "impressions": cur.get("impressions"), "ab_test": cur.get("ab_test"), "retention": retention,
            "hypotheses": hyps,
            "next_to_test": [], "_note": "correlation only - none of this shows what caused the result"}


def markdown(r):
    L = [f"# Episode report - {r['episode']} (day {r['age_days']})", "",
         "_Correlation, not causation. Compared only with episodes at a similar age._", "",
         f"Comparable episodes: {', '.join(r['comparable_episodes']) or 'none yet'}",
         *( [f"Confounders: {'; '.join(r['confounders'])}"] if r["confounders"] else []), "",
         "| metric | this episode | comparable median | delta | sample ok |", "|---|---|---|---|---|"]
    for m in r["metrics"]:
        L.append(f"| {m['metric']} | {m['value']} | {m['comparable_median']} | {m['delta']} | {'yes' if m['sample_ok'] else 'no'} |")
    if r["traffic"]:
        L += ["", "CTR by traffic source: " + ", ".join(f"{k} {v.get('ctr_pct')}% of {v.get('impressions'):,}"
                                                         for k, v in r["traffic"].items())]
    if r["ab_test"]:
        L += ["", f"A/B: {json.dumps(r['ab_test'], ensure_ascii=False)}"]
    ok = [h for h in r["hypotheses"] if h["result"] == "supported"]
    no = [h for h in r["hypotheses"] if h["result"] == "not supported"]
    inc = [h for h in r["hypotheses"] if h["result"] == "inconclusive"]
    L += ["", "## Which assumptions held?"] + [f"- {h['id']}: {h['statement']} - {h['why']}" for h in ok] + (["- none"] if not ok else [])
    L += ["", "## Which did not?"] + [f"- {h['id']}: {h['statement']} - {h['why']}" for h in no] + (["- none"] if not no else [])
    if inc:
        L += ["", "Inconclusive (do not record as learned):"] + [f"- {h['id']}: {h['statement']} - {h['why']}" for h in inc]
    L += ["", "## Where did viewers leave?"]
    ret = r["retention"]
    if ret:
        L.append(f"- at 30 s: {ret['at_30s_pct']}% still watching")
        L += [f"- dip at {d['t']} s (-{d['drop_pts']} points)" for d in ret["dips"]] or ["- no dip over 3 points after 30 s"]
        L += [f"- peak at {p['t']} s (+{p['rise_pts']} points: rewatched)" for p in ret["peaks"]]
    else:
        L.append("- no retention export given (Studio -> Engagement -> audience retention -> download)")
    L += ["", "## What to test next", "- _one change, one metric, written to docs/growth/EXPERIMENT_LOG.md_", ""]
    return "\n".join(L)


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or "-h" in a or "--help" in a:
        print(__doc__); return 0

    def val(name):
        if name not in a: return None
        i = a.index(name)
        if i + 1 >= len(a): raise ValueError(f"{name} needs a value")
        return a[i + 1]
    try:
        hist_p, ret_p = val("--history"), val("--retention")
        used = {hist_p, ret_p}
        files = [x for x in a if not x.startswith("--") and x not in used]
        if len(files) != 1: raise ValueError("give exactly one metrics.json")
        with open(files[0], encoding="utf-8") as f: cur = json.load(f)
        for k in ("episode", "published", "as_of"):
            if not cur.get(k): raise ValueError(f"metrics.json needs '{k}'")
        hist = []
        if hist_p and os.path.exists(hist_p):
            with open(hist_p, encoding="utf-8") as f: hist = [json.loads(x) for x in f if x.strip()]
        ret = retention_curve(ret_p, cur.get("duration_s")) if ret_p else None
        rep = build(cur, hist, ret)
        if "--append" in a:
            if not hist_p: raise ValueError("--append needs --history")
            with open(hist_p, "a", encoding="utf-8") as f:
                f.write(json.dumps({k: v for k, v in cur.items() if k != "hypotheses"}, ensure_ascii=False) + "\n")
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(json.dumps({"result": "ERROR", "error": f"{type(e).__name__}: {e}"})); return 2
    print(markdown(rep) if "--markdown" in a else json.dumps(rep, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
