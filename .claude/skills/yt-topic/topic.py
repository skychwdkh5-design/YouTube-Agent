#!/usr/bin/env python3
"""yt-topic: pick the next topic with a transparent score; no invented data.

collect : public YouTube search/browse JSON (no login) -> videos with views, age, channel subs, channel median
imagery : free Sentinel-2 availability for a topic's AOI/years (via yt-sentinel)
score   : candidates.json -> ranked topic.json + topic.md (weights, per-component points, missing data, caveats)

Measured components come from collected data. Judgement components (US potential, visual strength ...) must be
rated 1-5 with a written rationale by the agent; a candidate without them is reported "needs_ratings", never
guessed. YouTube's algorithm is not modelled: demand is what similar videos achieved, not a forecast.
"""
import argparse, json, os, re, statistics, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120 Safari/537.36", "Accept-Language": "en-US,en;q=0.9", "Cookie": "CONSENT=YES+1"}
KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"   # public web client key, read-only browse
RATED = ["us", "se", "no", "dk", "intl", "visual", "curiosity", "evidence", "monetization"]
# CLAUDE.md: US is dominant; Scandinavia only breaks near-ties; evidence is a gate.
WEIGHTS = {"us": 3.0, "demand": 2.0, "imagery": 1.5, "visual": 1.5, "curiosity": 1.5, "evidence": 1.5, "intl": 1.0, "monetization": 1.0}
TIE_WEIGHT = {"se": 0.4, "no": 0.4, "dk": 0.4}
TIE_MARGIN = 0.03


def age_days(s):
    m = re.search(r"(\d+)\s*(h|d|w|mo|y)", s or "")
    if not m:
        return None
    n, u = int(m.group(1)), m.group(2)
    return n * {"h": 1 / 24, "d": 1, "w": 7, "mo": 30, "y": 365}[u]


def parse_n(s):
    m = re.search(r"([\d.,]+)\s*([KMB]?)", (s or "").replace(",", ""))
    return int(float(m.group(1)) * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}[m.group(2)]) if m else None


# ---- collect (live) -------------------------------------------------------------------------------------------------
def _get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode("utf8", "replace")


def search(q):
    h = _get("https://www.youtube.com/results?search_query=" + urllib.parse.quote(q) + "&hl=en&gl=US")
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", h, re.S)
    if not m:
        raise RuntimeError("search page not parseable (consent/format change)")
    out = []
    def walk(o):
        if isinstance(o, dict):
            if "videoRenderer" in o:
                v = o["videoRenderer"]
                r0 = v.get("ownerText", {}).get("runs", [{}])[0]
                out.append({"id": v["videoId"], "title": v["title"]["runs"][0]["text"], "views": parse_n(v.get("viewCountText", {}).get("simpleText")),
                            "age": v.get("publishedTimeText", {}).get("simpleText"), "dur": v.get("lengthText", {}).get("simpleText"),
                            "channel": r0.get("text"), "channel_id": r0.get("navigationEndpoint", {}).get("browseEndpoint", {}).get("browseId")})
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(json.loads(m.group(1)))
    return out


def channel_stats(cid):
    """(subs, median views of the first page of uploads) or (None, None)."""
    subs = med = None
    try:
        h = _get(f"https://www.youtube.com/channel/{cid}/videos?hl=en&gl=US")
        m = re.search(r'([\d.,]+[KMB]?) subscribers', h)
        subs = parse_n(m.group(1)) if m else None
        body = json.dumps({"context": {"client": {"clientName": "WEB", "clientVersion": "2.20260101.00.00", "hl": "en", "gl": "US"}},
                           "browseId": cid, "params": "EgZ2aWRlb3PyBgQKAjoA"}).encode()
        r = urllib.request.Request(f"https://www.youtube.com/youtubei/v1/browse?key={KEY}", data=body, headers={"Content-Type": "application/json", **UA})
        s = urllib.request.urlopen(r, timeout=30).read().decode()
        vs = [parse_n(x) for x in re.findall(r'"viewCountText":\{"simpleText":"([^"]+) views"', s)] or \
             [parse_n(x) for x in re.findall(r'([\d.,]+[KMB]?) views', s)]
        vs = [v for v in vs if v]
        med = int(statistics.median(vs)) if len(vs) >= 4 else None
    except Exception:
        pass
    return subs, med


def collect(queries, min_views=20000, pause=0.8):
    seen, chans, rows, errors = {}, {}, [], []
    for q in queries:
        try:
            for v in search(q):
                seen.setdefault(v["id"], v)
        except Exception as e:
            errors.append(f"{q}: {e}")
        time.sleep(pause)
    for v in seen.values():
        if (v["views"] or 0) < min_views or not v["channel_id"]:
            continue
        if v["channel_id"] not in chans:
            chans[v["channel_id"]] = channel_stats(v["channel_id"])
            time.sleep(pause / 2)
        subs, med = chans[v["channel_id"]]
        rows.append({**v, "subs": subs, "channel_median": med, "multiple": round(v["views"] / med, 1) if med else None,
                     "age_days": age_days(v["age"])})
    return {"queries": queries, "videos": sorted(rows, key=lambda r: -r["views"]), "errors": errors,
            "note": "views/ages are as shown publicly; median uses the channel's first ~30 uploads (rounded by YouTube)"}


# ---- measured components --------------------------------------------------------------------------------------------
def demand(videos, small_subs=350_000):
    """0-5 from what similar videos achieved recently. Returns (points, facts). No videos -> (None, reason)."""
    vs = [v for v in videos if v.get("views")]
    if len(vs) < 5:
        return None, {"reason": f"only {len(vs)} videos collected (< 5)"}
    recent = [v for v in vs if v.get("age_days") is not None and v["age_days"] <= 120]
    small_hits = [v for v in vs if v.get("subs") and v["subs"] <= small_subs and v["views"] >= 200_000]
    recent_small = [v for v in small_hits if v.get("age_days") is not None and v["age_days"] <= 365]
    recent_big = [v for v in recent if v["views"] >= 500_000]
    pts = 0.0
    pts += min(2.0, len(recent_small) * 0.5)          # small channels recently beat 200K: topic is reachable
    pts += min(1.5, len(recent_big) * 0.5)            # fresh attention exists
    pts += 1.5 if len(recent) >= 5 else (0.75 if len(recent) >= 2 else 0)   # steady supply of new videos
    saturation = len([v for v in recent if v["views"] < 20_000 or (v.get("subs") or 1e9) < 1_000])
    pts -= min(1.0, saturation * 0.1)                  # many tiny clones: crowding
    return round(max(0.0, min(5.0, pts)), 2), {"videos": len(vs), "recent_120d": len(recent), "small_channel_hits_200k": len(small_hits),
                                               "recent_small_hits": len(recent_small), "recent_500k": len(recent_big), "crowding_penalty": min(1.0, saturation * 0.1)}


def imagery_points(img):
    """0-5 from the number of requested years with a usable scene. None when unchecked; never assumed."""
    if not img:
        return None, {"reason": "imagery not checked"}
    want, have = len(img.get("years_wanted") or []), len(img.get("years_found") or [])
    if want == 0:
        return None, {"reason": "no years requested"}
    return round(5.0 * have / want, 2), {"years_found": img.get("years_found"), "years_missing": img.get("years_missing")}


def check_imagery(aoi, years, window=("09-20", "11-10"), cloud=3.0):
    sys.path.insert(0, os.path.join(HERE, "..", "yt-sentinel"))
    import sentinel as s
    items = []
    for y in years:
        items += s.stac_search(aoi, f"{y}-{window[0]}", f"{y}-{window[1]}", max(cloud, 5))
    pk = s.pick_per_year(items, years, window, cloud)
    return {"years_wanted": years, "years_found": sorted(pk["picks"]), "years_missing": pk["missing"], "orbit": pk["orbit"], "notes": pk["notes"]}


# ---- score ----------------------------------------------------------------------------------------------------------
def score_candidate(c, weights=WEIGHTS):
    miss, comp = [], {}
    ratings, why = c.get("ratings") or {}, c.get("rationale") or {}
    for k in RATED:
        v = ratings.get(k)
        if not isinstance(v, (int, float)) or not 1 <= v <= 5:
            miss.append(f"rating:{k}")
        elif len(str(why.get(k, ""))) < 10:
            miss.append(f"rationale:{k}")
    d_pts, d_facts = demand(c.get("videos") or [])
    i_pts, i_facts = imagery_points(c.get("imagery")) if c.get("needs_satellite", True) else (5.0, {"reason": "satellite not required"})
    if d_pts is None:
        miss.append("data:demand")
    if i_pts is None:
        miss.append("data:imagery")
    if miss:
        return {"id": c["id"], "status": "needs_data", "missing": miss}
    pts = {"us": ratings["us"], "demand": d_pts, "imagery": i_pts, **{k: ratings[k] for k in ("visual", "curiosity", "evidence", "intl", "monetization")}}
    total = sum(weights[k] * pts[k] for k in weights)
    tie = sum(TIE_WEIGHT[k] * ratings[k] for k in TIE_WEIGHT)
    gate = []
    if ratings["evidence"] <= 2:
        gate.append("evidence rating <= 2: a topic without reliable evidence loses")
    if c.get("needs_satellite", True) and i_pts == 0:
        gate.append("no usable satellite scene for the requested years")
    return {"id": c["id"], "title": c.get("title"), "status": "disqualified" if gate else "ok", "gates": gate,
            "total": round(total, 2), "max": round(5 * sum(weights.values()), 2), "tie_break": round(tie, 2),
            "points": pts, "demand_facts": d_facts, "imagery_facts": i_facts}


def rank(cands, weights=WEIGHTS):
    res = [score_candidate(c, weights) for c in cands]
    ok = [r for r in res if r["status"] == "ok"]
    ok.sort(key=lambda r: -r["total"])
    # Scandinavian appeal only reorders near-ties
    for i in range(len(ok) - 1):
        a, b = ok[i], ok[i + 1]
        if abs(a["total"] - b["total"]) <= TIE_MARGIN * a["max"] and b["tie_break"] > a["tie_break"]:
            ok[i], ok[i + 1] = b, a
    rest = [r for r in res if r["status"] != "ok"]
    out = {"schema": "yt-topic/1", "ranking": ok, "excluded": rest,
           "chosen": ok[0]["id"] if ok else None,
           "caveats": ["demand = what similar videos achieved, not a CTR/retention forecast", "ratings 1-5 are the agent's judgement with written rationale",
                       "no OrbitalAtlas analytics are used; add them when available"]}
    if not ok:
        out["status"] = "needs_data"
    else:
        out["status"] = "ok"
    return out


def memo(r, cands):
    t = {c["id"]: c for c in cands}
    L = ["# Topic decision", "", f"Chosen: **{r['chosen']}**" if r["chosen"] else "Chosen: none (blocked)", ""]
    for x in r["ranking"]:
        L.append(f"- {x['id']}: {x['total']}/{x['max']} (tie-break {x['tie_break']}) points {x['points']}")
        L.append(f"  - demand {x['demand_facts']}; imagery {x['imagery_facts']}")
    for x in r["excluded"]:
        L.append(f"- {x['id']}: {x['status']} {x.get('missing') or x.get('gates')}")
    L += ["", "Caveats:"] + [f"- {c}" for c in r["caveats"]]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("collect"); p.add_argument("--queries", required=True, help="semicolon separated"); p.add_argument("--out", required=True)
    p = sub.add_parser("imagery"); p.add_argument("--aoi", required=True); p.add_argument("--years", required=True)
    p = sub.add_parser("score"); p.add_argument("--candidates", required=True); p.add_argument("--out", required=True); p.add_argument("--memo")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "collect":
            r = collect([q.strip() for q in a.queries.split(";") if q.strip()])
            json.dump(r, open(a.out, "w"), indent=1)
            print(json.dumps({"status": "ok" if r["videos"] else "no_data", "videos": len(r["videos"]), "errors": r["errors"], "out": a.out}))
            return 0 if r["videos"] else 1
        if a.cmd == "imagery":
            print(json.dumps(check_imagery([float(x) for x in a.aoi.split(",")], [int(y) for y in a.years.split(",")]), indent=1))
            return 0
        d = json.load(open(a.candidates))
        r = rank(d["candidates"])
        json.dump(r, open(a.out, "w"), indent=1)
        if a.memo:
            open(a.memo, "w").write(memo(r, d["candidates"]))
        print(json.dumps({"status": r["status"], "chosen": r["chosen"], "ranking": [(x["id"], x["total"]) for x in r["ranking"]],
                          "excluded": [(x["id"], x["status"]) for x in r["excluded"]]}))
        return 0 if r["status"] == "ok" else 1
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
