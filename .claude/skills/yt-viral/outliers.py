#!/usr/bin/env python3
"""outliers.py - Outlier Detector: how far did a video beat its OWN channel's comparable videos?

    python3 outliers.py collected.json                      # table
    python3 outliers.py collected.json --json               # machine-readable
    python3 outliers.py collected.json --markdown           # for research/runs/<run>/OUTLIERS.md
    python3 outliers.py --rss feed1.xml feed2.xml --json    # YouTube channel RSS (free, no quota)
    python3 outliers.py collected.json --as-of 2026-10-30   # reproducible ages

Input (any collector: vidIQ, YouTube Data API, channel RSS, manual) - a list or {"videos": [...]}:

    {"channel": "...", "channel_id": "UC...", "video_id": "...", "title": "...", "views": 412000,
     "published": "2026-09-14T15:00:00Z", "duration": 613, "thumbnail": "https://...", "url": "..."}

Common aliases are accepted (viewCount, publishedAt, durationSeconds, ISO-8601 "PT10M13S",
channelTitle, channelId, videoId, thumbnails{...}). Unknown fields are kept as "extra".

How the baseline is built - this is the whole point:
  * only the SAME channel, the SAME format (long >= 3 min vs Shorts < 3 min), the video itself excluded;
  * only comparables at least 14 days old (younger view counts have not settled);
  * only comparables published within 365 days of the video (channels change size).
  baseline = median views of those comparables. ratio = views / baseline.

Honesty rules built in:
  * fewer than 5 comparables -> data "insufficient", no ratio tier at all; 5-7 -> "limited";
  * a video under 14 days old is "provisional" - its ratio will move;
  * very uneven channels (p75/p25 > 5) lower confidence;
  * a third-party score (vidIQ "breakout", "outlierScore") is used only when the channel's own comparables
    were not collected: data "external", confidence always low, never a focus video;
  * the tool never says "viral". Tiers: typical < 1.5x <= above < 3x <= strong (3-4x, study) < 4x <= exceptional;
  * "facts" are numbers that were collected; "hypotheses" (why it worked) are an empty list for a person
    or Claude to fill, labelled as unverified. Title/thumbnail observations are not causes.
Exit 0 always on a readable input (finding no outlier is a result), 2 on unusable input.
"""
import datetime as dt, json, os, re, statistics, sys
import xml.etree.ElementTree as ET

SHORT_MAX_S = 180
MIN_AGE_DAYS = 14
WINDOW_DAYS = 365
MIN_SUFFICIENT, MIN_LIMITED = 8, 5
SPREAD_WARN = 5.0
TIERS = ((4.0, "exceptional"), (3.0, "strong"), (1.5, "above"), (0.0, "typical"))
FOCUS_RATIO = 3.0


class InputError(Exception):
    pass


def _num(v):
    try:
        x = float(str(v).replace(",", ""))
        return x if x == x and x not in (float("inf"), float("-inf")) else None
    except (TypeError, ValueError):
        return None


def _iso_duration(s):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", str(s or "").strip())
    if not m or not any(m.groups()):
        return None
    d, h, mi, se = (float(x) if x else 0.0 for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + se


def _date(s):
    if not s:
        return None
    s = str(s).strip().replace("Z", "+00:00")
    for fn in (dt.datetime.fromisoformat, lambda x: dt.datetime.strptime(x[:10], "%Y-%m-%d")):
        try:
            d = fn(s)
            return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
    return None


def _first(r, *keys):
    for k in keys:
        if k in r and r[k] not in (None, ""):
            return r[k]
    return None


def normalize(r):
    """One collected record -> the fields this tool uses. Raises nothing; missing stays None."""
    dur = _first(r, "duration", "durationSeconds", "duration_s", "lengthSeconds")
    dur = _iso_duration(dur) if isinstance(dur, str) and dur.startswith("P") else _num(dur)
    th = _first(r, "thumbnail", "thumbnailUrl", "thumbnail_url")
    if th is None and isinstance(r.get("thumbnails"), dict):
        best = max(r["thumbnails"].values(), key=lambda t: (t or {}).get("width") or 0, default=None)
        th = (best or {}).get("url")
    vid = _first(r, "video_id", "videoId", "id")
    known = {"duration", "durationSeconds", "duration_s", "lengthSeconds", "thumbnail", "thumbnailUrl", "thumbnail_url",
             "thumbnails", "video_id", "videoId", "id", "channel", "channelTitle", "channel_title", "channel_id",
             "channelId", "title", "views", "viewCount", "view_count", "published", "publishedAt", "published_at", "url",
             "breakout", "breakoutScore", "outlierScore", "outlier_score"}
    return {"channel": _first(r, "channel", "channelTitle", "channel_title") or "?",
            "channel_id": _first(r, "channel_id", "channelId"),
            "video_id": vid, "title": r.get("title") or "",
            "views": _num(_first(r, "views", "viewCount", "view_count")),
            "published": _first(r, "published", "publishedAt", "published_at"),
            "duration": dur, "thumbnail": th,
            "url": r.get("url") or (f"https://www.youtube.com/watch?v={vid}" if vid else None),
            "external_breakout": _num(_first(r, "breakout", "breakoutScore", "outlierScore", "outlier_score")),
            "extra": {k: v for k, v in r.items() if k not in known}}


def load(paths, rss=False):
    rows = []
    for p in paths:
        try:
            if rss:
                with open(p, encoding="utf-8") as fh:
                    rows += parse_rss(fh.read())
                continue
            with open(p, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError, ET.ParseError) as e:
            raise InputError(f"{p}: {type(e).__name__}: {e}")
        if isinstance(data, dict):
            data = data.get("videos") or data.get("results") or data.get("items") or []
        if not isinstance(data, list):
            raise InputError(f"{p}: expected a list of videos")
        rows += [x for x in data if isinstance(x, dict)]
    return [normalize(r) for r in rows]


def parse_rss(text):
    """YouTube channel RSS (youtube.com/feeds/videos.xml?channel_id=...): last ~15 uploads with views.
    RSS has no duration, so format is unknown and the report says so."""
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
          "m": "http://search.yahoo.com/mrss/"}
    root = ET.fromstring(text)
    ch = root.findtext("a:title", default="?", namespaces=ns)
    out = []
    for e in root.findall("a:entry", ns):
        stats = e.find("m:group/m:community/m:statistics", ns)
        th = e.find("m:group/m:thumbnail", ns)
        out.append({"channel": ch, "channel_id": e.findtext("yt:channelId", namespaces=ns),
                    "video_id": e.findtext("yt:videoId", namespaces=ns), "title": e.findtext("a:title", namespaces=ns),
                    "views": stats.get("views") if stats is not None else None,
                    "published": e.findtext("a:published", namespaces=ns),
                    "thumbnail": th.get("url") if th is not None else None,
                    "url": (e.find("a:link", ns).get("href") if e.find("a:link", ns) is not None else None)})
    return out


def fmt_of(v):
    if v["duration"] is None:
        return "unknown"
    return "short" if v["duration"] < SHORT_MAX_S else "long"


def _q(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * q
    f = int(k)
    return xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f)


def assess(v, channel_videos, as_of):
    pub = _date(v["published"])
    age = (as_of - pub).days if pub else None
    fmt = fmt_of(v)
    comps = []
    for c in channel_videos:
        if c is v or c["views"] is None:
            continue
        if fmt != "unknown" and fmt_of(c) not in (fmt, "unknown"):
            continue
        cp = _date(c["published"])
        if cp is None or (as_of - cp).days < MIN_AGE_DAYS:
            continue
        if pub is not None and abs((cp - pub).days) > WINDOW_DAYS:
            continue
        comps.append(c["views"])
    n = len(comps)
    base = statistics.median(comps) if comps else None
    ratio = round(v["views"] / base, 2) if base and v["views"] is not None else None
    p25, p75 = _q(comps, 0.25), _q(comps, 0.75)
    spread = round(p75 / p25, 2) if p25 else None
    data = "sufficient" if n >= MIN_SUFFICIENT else "limited" if n >= MIN_LIMITED else "insufficient"
    reasons = []
    if data != "sufficient":
        reasons.append(f"{n} comparable videos (need {MIN_SUFFICIENT} for a solid baseline)")
    if age is not None and age < MIN_AGE_DAYS:
        reasons.append(f"video is {age} days old - views have not settled")
    if age is None:
        reasons.append("no publish date")
    if spread and spread > SPREAD_WARN:
        reasons.append(f"channel is very uneven (p75/p25 = {spread})")
    if fmt == "unknown":
        reasons.append("duration unknown - long and Shorts may be mixed in the baseline")
    ext = v.get("external_breakout")
    if data == "insufficient" and ext is not None:
        # a third-party score (e.g. vidIQ breakout) whose baseline method and sample are not disclosed:
        # reported, tiered, but always low confidence and never "focus"
        data, ratio = "external", round(ext, 2)
        reasons.append("ratio is a third-party breakout score - baseline method and comparables not disclosed")
    tier = None
    if data != "insufficient" and ratio is not None:
        tier = next(name for lo, name in TIERS if ratio >= lo)
        if age is not None and age < MIN_AGE_DAYS:
            tier = "provisional-" + tier
    conf = "low" if data in ("insufficient", "external") else (
        "high" if data == "sufficient" and not reasons else "medium" if len(reasons) <= 1 else "low")
    return {"facts": {"channel": v["channel"], "channel_id": v["channel_id"], "video_id": v["video_id"], "title": v["title"],
                      "views": int(v["views"]) if v["views"] is not None else None, "published": v["published"],
                      "age_days": age, "duration_s": v["duration"], "format": fmt, "thumbnail": v["thumbnail"], "url": v["url"],
                      "baseline_median": int(base) if base is not None else None, "comparables": n,
                      "ratio": ratio, "channel_spread_p75_p25": spread},
            "assessment": {"data": data, "tier": tier, "focus": bool(tier and data != "external" and tier.split("-")[-1] in ("strong", "exceptional")),
                           "confidence": conf, "caveats": reasons},
            "hypotheses": [], "_hypotheses_note": "why it worked: unverified hypotheses only, never facts"}


def detect(videos, as_of=None):
    as_of = as_of or dt.datetime.now(dt.timezone.utc)
    by = {}
    for v in videos:
        by.setdefault(v["channel_id"] or v["channel"], []).append(v)
    out = [assess(v, by[v["channel_id"] or v["channel"]], as_of) for v in videos if v["views"] is not None]
    rank = {"exceptional": 4, "strong": 3, "above": 2, "typical": 1}
    out.sort(key=lambda r: (-(rank.get((r["assessment"]["tier"] or "").split("-")[-1], 0)),
                            -(r["facts"]["ratio"] or 0)))
    return {"as_of": as_of.date().isoformat(), "videos": len(videos), "channels": len(by),
            "focus_rule": f"study videos at >= {FOCUS_RATIO}x their channel baseline with enough data",
            "results": out,
            "focus": [r["facts"]["video_id"] or r["facts"]["title"] for r in out if r["assessment"]["focus"]
                      and r["assessment"]["confidence"] != "low"]}


def markdown(rep):
    L = [f"# Outlier scan - {rep['as_of']}", "",
         f"{rep['videos']} videos, {rep['channels']} channels. Baseline = median of the same channel's same-format videos, "
         f">= {MIN_AGE_DAYS} days old, within {WINDOW_DAYS} days. Nothing here is called viral.", "",
         "## Facts (collected numbers)", "",
         "| ratio | tier | data | conf. | views | baseline (n) | age d | channel | title |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rep["results"]:
        f, a = r["facts"], r["assessment"]
        L.append(f"| {f['ratio'] if f['ratio'] is not None else '-'}x | {a['tier'] or '-'} | {a['data']} | {a['confidence']} | "
                 f"{f['views']:,} | {f['baseline_median'] if f['baseline_median'] is not None else '-'} ({f['comparables']}) | "
                 f"{f['age_days'] if f['age_days'] is not None else '-'} | {f['channel']} | "
                 f"[{f['title'][:70]}]({f['url']}) |")
    L += ["", "## Hypotheses (unverified - why these might have worked)", "",
          "_Fill per focus video. Observations about title/thumbnail are not causes._", ""]
    for r in rep["results"]:
        if r["assessment"]["focus"]:
            L.append(f"- **{r['facts']['title'][:80]}** ({r['facts']['ratio']}x, {r['assessment']['confidence']} confidence): "
                     + ("; ".join(r["hypotheses"]) if r["hypotheses"] else "_no hypothesis yet_"))
    return "\n".join(L) + "\n"


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or "-h" in a or "--help" in a:
        print(__doc__); return 0
    try:
        as_of = None
        if "--as-of" in a:
            i = a.index("--as-of")
            as_of = _date(a[i + 1] if i + 1 < len(a) else "")
            if as_of is None:
                raise InputError("--as-of needs YYYY-MM-DD")
            del a[i:i + 2]
        flags = {x for x in a if x.startswith("--")}
        bad = flags - {"--json", "--markdown", "--rss"}
        if bad:
            raise InputError(f"unknown option(s): {sorted(bad)}")
        files = [x for x in a if not x.startswith("--")]
        if not files:
            raise InputError("give at least one input file")
        rep = detect(load(files, rss="--rss" in flags), as_of)
    except InputError as e:
        print(json.dumps({"result": "ERROR", "error": str(e)})); return 2
    if "--json" in flags:
        print(json.dumps(rep, indent=1, ensure_ascii=False))
    elif "--markdown" in flags:
        print(markdown(rep), end="")
    else:
        print(f"\n  {rep['videos']} videos, {rep['channels']} channels, as of {rep['as_of']}\n")
        for r in rep["results"][:30]:
            f, x = r["facts"], r["assessment"]
            print(f"  {str(f['ratio'] or '-'):>6}x  {x['tier'] or '-':<22} {x['confidence']:<6} {f['views']:>10,}  "
                  f"{f['channel'][:20]:<20} {f['title'][:50]}")
        print(f"\n  focus (>= {FOCUS_RATIO}x, not low confidence): {len(rep['focus'])}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
