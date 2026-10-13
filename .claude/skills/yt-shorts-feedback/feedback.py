#!/usr/bin/env python3
"""feedback.py - Shorts Performance Feedback: record what happened to published Shorts and test hypotheses honestly.

    python3 feedback.py validate                         # check every record in analytics/shorts
    python3 feedback.py report [--video-id ID]           # derived metrics with intervals and caveats
    python3 feedback.py add --video-id ID --duration-seconds 51 --views 374 ...   # append one measurement (never overwrites)
    python3 feedback.py import-csv FILE [--map "Column=field"] [--write]          # YouTube Studio CSV export (dry run unless --write)
    python3 feedback.py import-api-json FILE --video-id ID [--write]              # saved YouTube Analytics API reports.query response
    python3 feedback.py evaluate [--hypothesis H-001]    # apply the pre-registered decision rule to the data we have
    python3 feedback.py power --baseline 45 --delta 5    # views needed per arm (percent metrics), or --n 1000 for the detectable difference
    python3 feedback.py plan-experiment --id EXP-001 --factor first_3s --variants A,B,C --videos s3,s4,s5,s6 --seed 7 [--write]
    python3 feedback.py schema [--write]                 # JSON Schema generated from the field table below

WHAT THIS IS NOT. Nothing here collects statistics from YouTube: there is no connected API, no scheduled job and no credentials. Numbers enter by
`add`, `import-csv` or `import-api-json` from a file a person exported. A measurement whose provenance is unknown keeps `null` fields instead of
guesses. `views` and `engaged_views` are different YouTube metrics and are never merged or substituted for each other. Statistical output is
descriptive: with one Short per variant and different topics, a difference is a lead for the next test, never a result.
"""
import argparse, csv, datetime, hashlib, io, itertools, json, math, os, random, re, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

def _repo_root():
    d = HERE
    for _ in range(6):
        if os.path.isdir(os.path.join(d, ".git")) or os.path.exists(os.path.join(d, "CLAUDE.md")): return d
        d = os.path.dirname(d)
    return os.path.abspath(os.path.join(HERE, "..", "..", ".."))

STORE = os.environ.get("SHORTS_STORE") or os.path.join(_repo_root(), "analytics", "shorts")

class FbError(Exception):
    def __init__(self, msg, status="error", **extra): super().__init__(msg); self.status, self.extra = status, extra

# ---------------------------------------------------------------- field table (single source of truth; schema/*.json is generated from it)
SOURCES = ("manual_entry", "studio_export_csv", "analytics_api_json")
# name, kind, required, nullable, lo, hi, description
MEASUREMENT_FIELDS = [
    ("video_id", "str", True, False, None, None, "internal production id (the production file stem); stable across re-exports"),
    ("youtube_video_id", "str", False, True, None, None, "the 11-character YouTube id once known"),
    ("publication_date", "date", True, True, None, None, "YYYY-MM-DD (channel timezone as shown in Studio); null when not supplied"),
    ("duration_seconds", "num", True, False, 1, 180, "length of the published file in seconds"),
    ("views", "int", True, False, 0, None, "YouTube `views`. NOT the same metric as engaged_views"),
    ("engaged_views", "int", True, True, 0, None, "YouTube `engagedViews`: views past the first frame, or tap-to-play (https://developers.google.com/youtube/analytics/metrics). Never equal to views by definition"),
    ("stayed_to_watch_percent", "num", True, True, 0, 100, "Studio 'viewed vs swiped away': share that stayed (percent)"),
    ("swiped_away_percent", "num", True, True, 0, 100, "Studio 'viewed vs swiped away': share that swiped away (percent)"),
    ("average_view_duration", "num", True, True, 0, None, "seconds. Can exceed duration_seconds when playbacks repeat"),
    ("average_percentage_viewed", "num", True, True, 0, None, "percent; above 100 means repeated playback is included in this figure"),
    ("subscribers_gained", "int", True, True, 0, None, "subscribers gained attributed to this video"),
    ("measurement_timestamp", "datetime", True, True, None, None, "ISO 8601 time the numbers were read; null when unknown"),
    ("experiment_variant", "str", True, True, None, None, "`<experiment id>:<variant>` or `baseline_unplanned`; null only if never assigned"),
    ("source", "enum", True, False, None, None, "provenance: " + ", ".join(SOURCES)),
    ("metric_source", "str", False, True, None, None, "which product produced the numbers: `studio` or `analytics_api`. The API excludes looping-clips traffic from averageViewDuration/averageViewPercentage since 2021-12-13, so the two must not be mixed in one comparison"),
    ("recorded_on", "date", True, False, None, None, "date the record was added to this store"),
    ("notes", "str", False, True, None, None, "free text, e.g. what is unknown"),
]
FIELD_INDEX = {f[0]: f for f in MEASUREMENT_FIELDS}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$"); DT = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$")

def validate_record(rec):
    """returns (errors, warnings); errors make the record unusable, warnings are things a reader must know."""
    errs, warns = [], []
    if not isinstance(rec, dict): return ["record is not an object"], []
    for k in rec:
        if k not in FIELD_INDEX: errs.append(f"unknown field '{k}'")
    for name, kind, req, nullable, lo, hi, _ in MEASUREMENT_FIELDS:
        if name not in rec:
            if req: errs.append(f"missing required field '{name}' (use null if unknown, never a guess)" if nullable else f"missing required field '{name}'")
            continue
        v = rec[name]
        if v is None:
            if not nullable: errs.append(f"'{name}' may not be null")
            continue
        if kind == "str" and not (isinstance(v, str) and v.strip()): errs.append(f"'{name}' must be a non-empty string")
        elif kind == "int" and (isinstance(v, bool) or not isinstance(v, int)): errs.append(f"'{name}' must be an integer")
        elif kind == "num" and (isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)): errs.append(f"'{name}' must be a finite number")
        elif kind == "date" and not (isinstance(v, str) and DATE.match(v)): errs.append(f"'{name}' must be YYYY-MM-DD")
        elif kind == "datetime" and not (isinstance(v, str) and DT.match(v)): errs.append(f"'{name}' must be an ISO 8601 date-time")
        elif kind == "enum" and v not in SOURCES: errs.append(f"'{name}' must be one of {SOURCES}")
        if kind in ("int", "num") and isinstance(v, (int, float)) and not isinstance(v, bool):
            if lo is not None and v < lo: errs.append(f"'{name}' = {v} is below {lo}")
            if hi is not None and v > hi: errs.append(f"'{name}' = {v} is above {hi}")
    if errs: return errs, warns
    v, e = rec["views"], rec["engaged_views"]
    if e is not None and e > v: errs.append("engaged_views is larger than views")
    s, w = rec["stayed_to_watch_percent"], rec["swiped_away_percent"]
    if s is not None and w is not None and abs(s + w - 100) > 0.6: warns.append(f"stayed_to_watch_percent + swiped_away_percent = {s + w:.1f}, expected 100")
    d, a, p = rec["duration_seconds"], rec["average_view_duration"], rec["average_percentage_viewed"]
    if a is not None and p is not None:
        implied = 100.0 * a / d; tol = max(1.5, 100.0 * 0.5 / d + 0.5)       # durations are shown rounded to whole seconds
        if abs(implied - p) > tol: warns.append(f"average_percentage_viewed {p} disagrees with average_view_duration / duration_seconds = {implied:.1f}")
    if rec["measurement_timestamp"] and rec["publication_date"] and rec["measurement_timestamp"][:10] < rec["publication_date"]: errs.append("measurement_timestamp is before publication_date")
    if errs: return errs, warns
    if rec["measurement_timestamp"] is None: warns.append("measurement_timestamp unknown: the measurement window is unknown, so this record is not comparable with a fixed-window test")
    if rec["publication_date"] is None: warns.append("publication_date unknown")
    if rec["source"] == "analytics_api_json" and rec.get("metric_source") not in ("analytics_api", None): warns.append("source is analytics_api_json but metric_source says otherwise")
    return errs, warns

# ---------------------------------------------------------------- store
def _path(name): return os.path.join(STORE, name)
def _read_json(name, default):
    p = _path(name)
    if not os.path.exists(p): return default
    try:
        with open(p, encoding="utf-8") as f: return json.load(f)
    except json.JSONDecodeError as e: raise FbError(f"{name} is not valid JSON: {e}")
def _atomic_write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f: f.write(text)
    os.replace(tmp, path)
def load_measurements():
    p = _path("measurements.jsonl"); out = []
    if not os.path.exists(p): return out
    with open(p, encoding="utf-8") as f: lines = f.read().splitlines()
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line: continue
        try: out.append(json.loads(line))
        except json.JSONDecodeError as e: raise FbError(f"measurements.jsonl line {i}: {e}")
    return out
def record_key(r): return (r.get("video_id"), r.get("measurement_timestamp"), r.get("source"), r.get("metric_source"))
def append_measurement(rec):
    errs, warns = validate_record(rec)
    if errs: raise FbError("invalid record: " + "; ".join(errs), errors=errs)
    existing = load_measurements()
    if any(record_key(x) == record_key(rec) and x.get("views") == rec["views"] for x in existing):
        raise FbError("an identical measurement (same video, timestamp, source and views) is already stored", status="duplicate")
    text = "".join(json.dumps(x, ensure_ascii=False, sort_keys=False) + "\n" for x in existing) + json.dumps(rec, ensure_ascii=False) + "\n"
    _atomic_write(_path("measurements.jsonl"), text)
    return warns

# ---------------------------------------------------------------- statistics (stdlib only; descriptive, assumptions stated where used)
def _phi(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))
def _zinv(p):                                                                   # Acklam's rational approximation of the normal quantile
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    if p < 0.02425:
        q = math.sqrt(-2 * math.log(p)); return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > 1 - 0.02425: return -_zinv(1 - p)
    q = p - 0.5; r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
def wilson(k, n, z=1.959964):
    if n <= 0: return None
    p = k / n; den = 1 + z * z / n; ctr = (p + z * z / (2 * n)) / den; half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, ctr - half), min(1.0, ctr + half))
def two_proportion(k1, n1, k2, n2):
    """two-sided pooled z test; returns (difference p1-p2, z, p). Assumes independent viewers - Shorts views are not randomised, so read p as a rough guide."""
    p1, p2, p = k1 / n1, k2 / n2, (k1 + k2) / (n1 + n2); se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0: return p1 - p2, 0.0, 1.0
    z = (p1 - p2) / se; return p1 - p2, z, 2 * (1 - _phi(abs(z)))
def zero_event_upper(n, conf=0.95): return -math.log(1 - conf) / n              # exact one-sided Poisson bound when 0 events were seen in n trials (rule of three at 95 %)
def binom_two_sided(k, n, p):
    if n == 0: return 1.0
    pk = math.comb(n, k) * p ** k * (1 - p) ** (n - k); tot = 0.0
    for i in range(n + 1):
        pi = math.comb(n, i) * p ** i * (1 - p) ** (n - i)
        if pi <= pk * (1 + 1e-9): tot += pi
    return min(1.0, tot)
def n_per_arm(baseline, delta, alpha=0.05, power=0.8):
    p1, p2 = baseline, baseline + delta; za, zb = _zinv(1 - alpha / 2), _zinv(power); pb = (p1 + p2) / 2
    return math.ceil(((za * math.sqrt(2 * pb * (1 - pb)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / (delta ** 2))
def detectable_delta(baseline, n, alpha=0.05, power=0.8):
    lo, hi = 1e-4, min(0.999 - baseline, 0.6)
    if n_per_arm(baseline, hi, alpha, power) > n: return None
    for _ in range(60):
        mid = (lo + hi) / 2
        if n_per_arm(baseline, mid, alpha, power) > n: lo = mid
        else: hi = mid
    return hi

# ---------------------------------------------------------------- derived metrics
def latest_per_video(ms):
    best = {}
    for m in ms:
        k = m["video_id"]; ts = m.get("measurement_timestamp") or ""
        if k not in best or ts >= (best[k].get("measurement_timestamp") or ""): best[k] = m
    return best
def derived(m):
    d = {"video_id": m["video_id"], "experiment_variant": m.get("experiment_variant"), "views": m["views"], "engaged_views": m.get("engaged_views")}
    caveats = ["engaged_views and views are different YouTube metrics; the ratio describes this video only"] if m.get("engaged_views") is not None else []
    if m.get("engaged_views") is not None and m["views"]: d["engaged_views_per_view"] = round(m["engaged_views"] / m["views"], 4)
    s = m.get("stayed_to_watch_percent")
    if s is not None and m["views"]:
        k = round(m["views"] * s / 100.0); ci = wilson(k, m["views"])
        d["stayed_to_watch_percent"] = s; d["stayed_to_watch_naive_ci95_percent"] = [round(ci[0] * 100, 1), round(ci[1] * 100, 1)]
        caveats.append("the naive interval treats every view as an independent observation over `views` (ASSUMPTION: YouTube does not document the exported denominator; repeat viewers, autoplay loops and shared audiences make views dependent), so it understates the real uncertainty and must not be used to compare Shorts")
    a = m.get("average_view_duration")
    if a is not None:
        d["average_view_duration"] = a; d["replay_ratio"] = round(a / m["duration_seconds"], 3)
        if d["replay_ratio"] > 1: caveats.append(f"average view duration is {d['replay_ratio']:.2f}x the video length: playbacks repeat (loops or rewatching) in this figure; it does not say how many viewers rewatched")
    if m.get("average_percentage_viewed") is not None: d["average_percentage_viewed"] = m["average_percentage_viewed"]
    sg = m.get("subscribers_gained")
    if sg is not None and m["views"]:
        d["subscribers_gained"] = sg; d["subscribers_per_1000_views"] = round(1000.0 * sg / m["views"], 3)
        if sg == 0: d["subscribers_per_1000_views_upper95"] = round(1000.0 * zero_event_upper(m["views"]), 2); caveats.append("0 subscribers: the data are compatible with any true rate below the upper bound shown, not with 'zero conversion'")
    if m.get("measurement_timestamp") is None: caveats.append("measurement window unknown")
    d["metric_source"] = m.get("metric_source"); d["caveats"] = caveats
    return d

# ---------------------------------------------------------------- importers
ALIASES = {  # normalised header -> field. ASSUMPTION: Studio export headers vary by language and release; use --map to override. Unmapped columns are reported, never guessed.
    "views": "views", "engagedviews": "engaged_views", "stayedtowatch": "stayed_to_watch_percent", "swipedaway": "swiped_away_percent",
    "averageviewduration": "average_view_duration", "averagepercentageviewed": "average_percentage_viewed", "subscribers": "subscribers_gained",
    "subscribersgained": "subscribers_gained", "duration": "duration_seconds", "videopublishtime": "publication_date", "publishdate": "publication_date",
    "videoid": "youtube_video_id", "content": "title", "videotitle": "title", "videotitle ": "title", "video": "title"}
def _norm(h): return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\(.*?\)", "", h.lower())).replace(" ", "")
def parse_seconds(s):
    s = str(s).strip()
    if re.fullmatch(r"\d+(\.\d+)?", s): return float(s)
    m = re.fullmatch(r"(?:(\d+):)?(\d{1,2}):(\d{2})(?:\.\d+)?", s)
    if not m: raise FbError(f"cannot read '{s}' as a duration (use seconds or [H:]MM:SS)")
    return int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
def _num(s, integer=False):
    s = str(s).strip().replace(",", "").replace("%", "")
    if s in ("", "-", "N/A", "n/a"): return None
    v = float(s)
    return int(round(v)) if integer else v
def import_csv(text, mapping=None, registry=None, source="studio_export_csv", measured_at=None, variant=None):
    """returns (records, skipped, unmapped_columns). Rows are matched to a registered video by youtube id or title; unmatched rows are skipped with the reason."""
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows: raise FbError("the CSV has no data rows")
    cmap, unmapped = {}, []
    for h in rows[0].keys():
        f = (mapping or {}).get(h) or ALIASES.get(_norm(h))
        if f: cmap[h] = f
        else: unmapped.append(h)
    registry = registry or {}; recs, skipped = [], []
    by_yt = {v.get("youtube_video_id"): k for k, v in registry.items() if v.get("youtube_video_id")}; by_title = {v.get("title"): k for k, v in registry.items() if v.get("title")}
    today = datetime.date.today().isoformat()
    for i, row in enumerate(rows, 2):
        vals = {cmap[h]: row[h] for h in cmap}
        vid = by_yt.get(vals.get("youtube_video_id")) or by_title.get(vals.get("title"))
        if "video_id" in row and row["video_id"].strip(): vid = row["video_id"].strip()
        if not vid: skipped.append({"row": i, "reason": "no registered video matches the id/title in this row"}); continue
        try:
            reg = registry.get(vid, {})
            rec = {"video_id": vid, "youtube_video_id": vals.get("youtube_video_id") or reg.get("youtube_video_id"), "publication_date": (vals.get("publication_date") or reg.get("publication_date") or None),
                   "duration_seconds": parse_seconds(vals["duration_seconds"]) if vals.get("duration_seconds") else reg.get("duration_seconds"),
                   "views": _num(vals.get("views"), True), "engaged_views": _num(vals.get("engaged_views"), True) if "engaged_views" in vals else None,
                   "stayed_to_watch_percent": _num(vals.get("stayed_to_watch_percent")) if "stayed_to_watch_percent" in vals else None,
                   "swiped_away_percent": _num(vals.get("swiped_away_percent")) if "swiped_away_percent" in vals else None,
                   "average_view_duration": parse_seconds(vals["average_view_duration"]) if vals.get("average_view_duration") not in (None, "") else None,
                   "average_percentage_viewed": _num(vals.get("average_percentage_viewed")) if "average_percentage_viewed" in vals else None,
                   "subscribers_gained": _num(vals.get("subscribers_gained"), True) if "subscribers_gained" in vals else None,
                   "measurement_timestamp": measured_at, "experiment_variant": variant or reg.get("experiment_variant") or "baseline_unplanned",
                   "source": source, "metric_source": "studio", "recorded_on": today, "notes": None}
            if rec["publication_date"] and not DATE.match(rec["publication_date"]): rec["publication_date"] = rec["publication_date"][:10] if DATE.match(rec["publication_date"][:10]) else None
        except (FbError, ValueError, KeyError) as e: skipped.append({"row": i, "reason": f"{type(e).__name__}: {e}"}); continue
        errs, warns = validate_record(rec)
        if errs: skipped.append({"row": i, "reason": "; ".join(errs)}); continue
        recs.append((rec, warns))
    return recs, skipped, unmapped
API_MAP = {"views": "views", "engagedViews": "engaged_views", "averageViewDuration": "average_view_duration", "averageViewPercentage": "average_percentage_viewed", "subscribersGained": "subscribers_gained"}
# stayed_to_watch / swiped_away are not listed on https://developers.google.com/youtube/analytics/metrics (read 2026-10-12): they stay manual (null) for API imports.
def import_api_json(doc, video, measured_at, variant=None):
    if not isinstance(doc, dict) or "columnHeaders" not in doc or "rows" not in doc: raise FbError("expected a YouTube Analytics API reports.query response with columnHeaders and rows")
    names = [h.get("name") for h in doc["columnHeaders"]]
    if not doc["rows"]: raise FbError("the response has no rows")
    if len(doc["rows"]) > 1: raise FbError("the response has several rows; query one video per call (filters=video==ID) so the numbers cannot be mixed up")
    row = dict(zip(names, doc["rows"][0])); today = datetime.date.today().isoformat()
    rec = {"video_id": video["video_id"], "youtube_video_id": video.get("youtube_video_id"), "publication_date": video.get("publication_date"), "duration_seconds": video["duration_seconds"],
           "views": None, "engaged_views": None, "stayed_to_watch_percent": None, "swiped_away_percent": None, "average_view_duration": None, "average_percentage_viewed": None,
           "subscribers_gained": None, "measurement_timestamp": measured_at, "experiment_variant": variant or video.get("experiment_variant") or "baseline_unplanned",
           "source": "analytics_api_json", "metric_source": "analytics_api", "recorded_on": today,
           "notes": "stayed_to_watch/swiped_away are not available through this mapping; averageViewDuration/averageViewPercentage exclude looping-clips traffic (API, since 2021-12-13)"}
    for api, f in API_MAP.items():
        if api in row and row[api] is not None: rec[f] = int(row[api]) if f in ("views", "engaged_views", "subscribers_gained") else float(row[api])
    if rec["views"] is None: raise FbError("the response has no `views` column")
    unknown = [n for n in names if n not in API_MAP and n not in ("video", "day", "month")]
    return rec, unknown

# ---------------------------------------------------------------- hypotheses
# Unit of analysis: the VIDEO. Views inside one Short are not independent observations (repeat viewers, autoplay loops, shared audiences) and topic effects belong to the
# Short, so every comparison uses one value per Short and an exact permutation test. A design whose smallest attainable p-value exceeds alpha can never confirm anything
# and is classified exploratory automatically (2 Shorts vs 2 Shorts: smallest two-sided p = 2/6 = 0.33).
def design_min_p(na, nb):
    """smallest two-sided p an exact permutation test can ever return for arms of na and nb videos (data independent)"""
    return (2 if na == nb else 1) / math.comb(na + nb, na)
def permutation_test(a, b):
    """exact two-sided permutation test on the difference of arm means (one value per video); returns (mean_a - mean_b, p)"""
    pooled = list(a) + list(b); n, na = len(pooled), len(a)
    if n > 22: raise FbError("too many videos for exact enumeration (more than 22)")
    tot = sum(pooled); obs = abs(sum(a) / len(a) - sum(b) / len(b)); ge = total = 0
    for idx in itertools.combinations(range(n), na):
        sa = sum(pooled[i] for i in idx); d = abs(sa / na - (tot - sa) / (n - na)); total += 1; ge += d >= obs - 1e-9
    return sum(a) / len(a) - sum(b) / len(b), ge / total
def metric_value(m, metric):
    if metric == "subscribers_per_1000_views":
        return None if m.get("subscribers_gained") is None or not m.get("views") else 1000.0 * m["subscribers_gained"] / m["views"]
    return m.get(metric)
def _days(ts, pub): return (datetime.date.fromisoformat(ts[:10]) - datetime.date.fromisoformat(pub[:10])).days
def evaluate_hypothesis(h, ms, experiments=()):
    t = h.get("test")
    if not t: return {"id": h["id"], "verdict": "not_testable_yet", "reason": "no pre-registered test block"}
    exp = next((e for e in experiments if e["id"] == t.get("experiment")), None)
    cls = t.get("class") or (exp or {}).get("class") or "exploratory"; window = (exp or {}).get("measurement_window_days")
    latest = latest_per_video(ms); arms = {}
    for name, sel in t["arms"].items():
        arms[name] = [m for m in latest.values() if m.get("experiment_variant") in sel.get("variants", []) or m["video_id"] in sel.get("videos", [])]
    metric = t["primary_metric"]; out = {"id": h["id"], "class": cls, "primary_metric": metric, "unit_of_analysis": "video", "arms": {}}
    need = t.get("min_views_per_arm", 1000); min_videos = t.get("min_videos_per_arm", 2)
    for name, vids in arms.items(): out["arms"][name] = {"videos": [v["video_id"] for v in vids], "views": sum(v["views"] for v in vids)}
    def stop(reason): out.update(verdict="insufficient_data", reason=reason); return out
    if any(len(a["videos"]) < min_videos or a["views"] < need for a in out["arms"].values()):
        return stop(f"each arm needs >= {min_videos} video(s) and >= {need} views; have " + ", ".join(f"{k}: {len(a['videos'])} video(s), {a['views']} views" for k, a in out["arms"].items()))
    names = list(arms)
    if len(names) != 2: out.update(verdict="not_testable_yet", reason="exactly two arms are required"); return out
    allv = arms[names[0]] + arms[names[1]]
    if any(v.get("measurement_timestamp") is None for v in allv): return stop("a measurement has no measurement_timestamp, so the fixed measurement window cannot be verified")
    if any(v.get("metric_source") is None for v in allv): return stop("a measurement has no metric_source (studio or analytics_api)")
    if len({v.get("metric_source") for v in allv}) > 1: return stop("arms mix metric sources (studio vs analytics_api)")
    if window:
        for v in allv:
            if not v.get("publication_date"): return stop(f"{v['video_id']}: publication_date unknown, so the age at measurement cannot be checked against the {window}-day window")
            age = _days(v["measurement_timestamp"], v["publication_date"])
            if not window <= age <= window + 1: return stop(f"{v['video_id']} was measured at age {age} days; the plan requires {window}-{window + 1} days")
    vals = {n: [metric_value(v, metric) for v in arms[n]] for n in names}
    if any(x is None for n in names for x in vals[n]): return stop(f"{metric} is missing for some video")
    a, b = vals[names[0]], vals[names[1]]; alpha = t.get("alpha", 0.05); direction = t.get("direction", "A>B")
    diff, p = permutation_test(a, b); pmin = design_min_p(len(a), len(b))
    out.update(per_video={n: {v["video_id"]: round(x, 2) for v, x in zip(arms[n], vals[n])} for n in names}, mean={names[0]: round(sum(a) / len(a), 2), names[1]: round(sum(b) / len(b), 2)}, difference=round(diff, 2),
               permutation_p=round(p, 4), design_min_p=round(pmin, 4), alpha=alpha)
    pred_first = direction.replace(" ", "") == f"{names[0]}>{names[1]}"; matches = None if direction == "different" else ((diff > 0) == pred_first)
    if cls == "exploratory" or pmin > alpha:
        thr = t.get("lead_threshold"); out["why_exploratory"] = ("declared exploratory" if cls == "exploratory" else f"design cannot reach alpha: smallest attainable p = {pmin:.3f} > {alpha}")
        if thr is None: out["verdict"] = "exploratory_descriptive"
        elif abs(diff) < thr: out["verdict"] = "exploratory_no_lead"
        else: out["verdict"] = f"exploratory_lead_{names[0] if diff > 0 else names[1]}"
        out["matches_prediction"] = matches; out["lead_threshold"] = thr
        out["note"] = "exploratory: this can only suggest the next test. No winner is declared, no significance is claimed, and the permutation p-value above is not a decision criterion for this design."
        return out
    sig = p < alpha
    out["verdict"] = "inconclusive" if not sig else ("supported" if direction == "different" or matches else "contradicted")
    out["note"] = "video-level exact permutation test. Shorts are scheduled, not randomised by YouTube; one channel, one period: read this as evidence about this channel's Shorts, not a general law."
    return out

# ---------------------------------------------------------------- experiment planning (reproducible, committed before publishing)
def plan_experiment(exp_id, factor, variants, videos, seed, window_days=7, primary="stayed_to_watch_percent", hypotheses=(), definitions=None, exp_class=None, lead_threshold=None):
    if len(variants) < 2: raise FbError("at least two variants are needed")
    if len(set(variants)) != len(variants) or len(set(videos)) != len(videos): raise FbError("variants and videos must be unique")
    if len(videos) < 2 * len(variants): raise FbError(f"{len(videos)} video(s) is too few for {len(variants)} variants: need at least 2 per variant, otherwise the variant cannot be separated from the topic")
    if len(videos) % len(variants): raise FbError(f"{len(videos)} videos cannot be split evenly over {len(variants)} variants (blocked randomisation needs complete blocks)")
    missing = [v for v in (definitions or {}) if v not in variants]
    if missing: raise FbError(f"definitions for unknown variants: {missing}")
    per_arm = len(videos) // len(variants); pmin = design_min_p(per_arm, per_arm) if len(variants) == 2 else None
    cls = exp_class or ("confirmatory" if (pmin is not None and pmin <= 0.05) else "exploratory")
    if cls == "confirmatory" and (pmin is None or pmin > 0.05): raise FbError(f"a confirmatory experiment needs a design that can reach p <= 0.05; {per_arm} video(s) per arm gives a smallest p of {pmin if pmin is None else round(pmin, 3)}")
    rng = random.Random(seed); order = []
    for i in range(0, len(videos), len(variants)):
        vs = list(variants); rng.shuffle(vs); order += list(zip(videos[i:i + len(variants)], vs))                  # blocked randomisation: each block holds every variant once
    return {"id": exp_id, "status": "planned", "class": cls, "design_min_p": None if pmin is None else round(pmin, 4), "lead_threshold": lead_threshold, "factor": factor, "variants": variants,
            "variant_definitions": definitions or {}, "hypotheses": list(hypotheses), "randomisation": {"method": "blocked, seeded", "seed": seed, "block_size": len(variants)},
            "assignment": [{"video_id": v, "experiment_variant": f"{exp_id}:{x}"} for v, x in order], "measurement_window_days": window_days, "primary_metric": primary,
            "rules": ["change only the declared factor between variants", "measure each Short at the same age (measurement_window_days after publication, +1 day) and record measurement_timestamp",
                      "publish in the assignment order; do not reassign after seeing numbers", "do not stop early on a good-looking difference",
                      "an exploratory experiment never declares a winner"]}

# ---------------------------------------------------------------- schema generation
def build_schema():
    props, req = {}, []
    for name, kind, r, nullable, lo, hi, desc in MEASUREMENT_FIELDS:
        t = {"str": "string", "date": "string", "datetime": "string", "enum": "string", "int": "integer", "num": "number"}[kind]; p = {"type": [t, "null"] if nullable else t, "description": desc}
        if kind == "date": p["pattern"] = DATE.pattern
        if kind == "datetime": p["pattern"] = DT.pattern
        if kind == "enum": p["enum"] = list(SOURCES)
        if lo is not None: p["minimum"] = lo
        if hi is not None: p["maximum"] = hi
        props[name] = p
        if r: req.append(name)
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "yt-shorts-feedback/measurement/1", "title": "Shorts measurement", "type": "object", "additionalProperties": False, "required": req, "properties": props}

# ---------------------------------------------------------------- CLI
def _out(obj): print(json.dumps(obj, indent=1, ensure_ascii=False)); return 0

def _videos_doc(): return _read_json("videos.json", {"schema": "yt-shorts-feedback/videos/1", "videos": []})
def register_video(doc, v, slot=None, experiments=()):
    """append one Short to the registry; refuses duplicates; `slot` binds it to a pre-registered experiment assignment"""
    if not isinstance(v.get("video_id"), str) or not v["video_id"].strip(): raise FbError("video_id is required")
    if any(x["video_id"] == v["video_id"] for x in doc["videos"]): raise FbError(f"{v['video_id']} is already registered", status="duplicate")
    if not isinstance(v.get("duration_seconds"), (int, float)) or v["duration_seconds"] <= 0: raise FbError("duration_seconds must be a positive number")
    if v.get("publication_date") and not DATE.match(v["publication_date"]): raise FbError("publication_date must be YYYY-MM-DD")
    rec = dict(v); rec.setdefault("youtube_video_id", None); rec.setdefault("publication_date", None); rec.setdefault("experiment_variant", "baseline_unplanned")
    if slot:
        hit = [(e, x) for e in experiments for x in e.get("assignment", []) if x["video_id"] == slot]
        if not hit: raise FbError(f"no pre-registered assignment slot '{slot}'")
        e, x = hit[0]
        if any(y.get("slot") == slot for y in doc["videos"]): raise FbError(f"slot {slot} is already used", status="duplicate")
        rec["slot"] = slot; rec["experiment_variant"] = x["experiment_variant"]
    doc["videos"].append(rec); return rec
def brief(today=None):
    """everything an agent needs before writing or after publishing a Short, in one JSON object"""
    today = today or datetime.date.today().isoformat(); doc = _videos_doc(); ms = load_measurements(); latest = latest_per_video(ms)
    exps = _read_json("experiments.json", {"experiments": []})["experiments"]; hy = _read_json("hypotheses.json", {"hypotheses": []})["hypotheses"]
    used = {v.get("slot") for v in doc["videos"] if v.get("slot")}; nxt = None
    for e in exps:
        if e.get("status") not in ("planned", "running"): continue
        for x in e["assignment"]:
            if x["video_id"] not in used:
                var = x["experiment_variant"].split(":", 1)[1]
                nxt = {"experiment_id": e["id"], "class": e.get("class", "exploratory"), "factor": e["factor"], "slot": x["video_id"], "experiment_variant": x["experiment_variant"],
                       "variant_definition": e.get("variant_definitions", {}).get(var), "rules": e.get("rules", []),
                       "how": "build with variants.py (single variable), register with `feedback.py register-video ... --slot " + x["video_id"] + "`"}
                break
        if nxt: break
    window = {e["id"]: e.get("measurement_window_days", 7) for e in exps}; due = []
    for v in doc["videos"]:
        w = window.get((v.get("experiment_variant") or "").split(":")[0], 7); m = latest.get(v["video_id"])
        if not v.get("publication_date"): due.append({"video_id": v["video_id"], "action": "publication_date unknown: fill it from Studio before a windowed measurement is possible"}); continue
        age = _days(today, v["publication_date"])
        if m is None or (m.get("measurement_timestamp") and not (w <= _days(m["measurement_timestamp"], v["publication_date"]) <= w + 1)):
            if age < w: due.append({"video_id": v["video_id"], "action": f"measure on {(datetime.date.fromisoformat(v['publication_date']) + datetime.timedelta(days=w)).isoformat()} (age {w} days)"})
            elif age <= w + 1: due.append({"video_id": v["video_id"], "action": f"measure now (age {age} days, window {w}-{w + 1})"})
            else: due.append({"video_id": v["video_id"], "action": f"window missed (age {age} days): record the reading anyway with its true timestamp; it will be excluded from windowed tests"})
    res = [{"id": h["id"], "title": h.get("title"), "status": h.get("status"), "verdict": evaluate_hypothesis(h, ms, exps)["verdict"]} for h in hy]
    return {"status": "ok", "today": today, "registered_videos": len(doc["videos"]), "next_slot": nxt, "due_measurements": due, "hypotheses": res,
            "constraints": ["a Short in a running experiment changes only the declared variable", "a different spoken line is a new TTS take: paid, needs the user's explicit approval",
                            "unknown stays null; never estimate a publication date or timestamp", "Studio and Analytics API numbers are never mixed in one comparison",
                            "exploratory experiments declare no winner"]}
def cmd_register(a):
    doc = _videos_doc(); exps = _read_json("experiments.json", {"experiments": []})["experiments"]
    v = {"video_id": a.video_id, "title": a.title, "youtube_video_id": a.youtube_video_id, "publication_date": a.publication_date, "duration_seconds": a.duration_seconds}
    if a.production_sha256: v["production"] = {"file": a.production_file, "sha256": a.production_sha256}
    rec = register_video(doc, {k: x for k, x in v.items() if x is not None}, a.slot, exps)
    _atomic_write(_path("videos.json"), json.dumps(doc, indent=1, ensure_ascii=False) + "\n"); return _out({"status": "registered", "video": rec})
def cmd_brief(a): return _out(brief(a.today))

def cmd_validate(a):
    ms = load_measurements(); problems, warnings = [], []
    for i, m in enumerate(ms, 1):
        e, w = validate_record(m); problems += [f"record {i} ({m.get('video_id')}): {x}" for x in e]; warnings += [f"record {i} ({m.get('video_id')}): {x}" for x in w]
    videos = _read_json("videos.json", {"videos": []}).get("videos", []); ids = {v["video_id"] for v in videos}
    for m in ms:
        if videos and m.get("video_id") not in ids: problems.append(f"measurement for unregistered video_id '{m.get('video_id')}'")
    keys = [record_key(m) + (m.get("views"),) for m in ms]
    if len(keys) != len(set(keys)): problems.append("duplicate measurement records")
    return _out({"status": "ok" if not problems else "invalid", "records": len(ms), "videos": len(ids), "problems": problems, "warnings": warnings}) or (0 if not problems else 2)
def cmd_report(a):
    ms = load_measurements(); latest = latest_per_video(ms)
    if a.video_id and a.video_id not in latest: raise FbError(f"no measurement for '{a.video_id}'")
    sel = [latest[a.video_id]] if a.video_id else list(latest.values())
    rep = {"status": "ok", "videos": [derived(m) for m in sel], "pooled": {}}
    tv = sum(m["views"] for m in sel); ts = sum(m.get("subscribers_gained") or 0 for m in sel)
    if tv: rep["pooled"] = {"views": tv, "subscribers_gained": ts, "note": "pooled across the selected videos; subscribers per 1000 views upper 95% bound shown only when 0 were gained", **({"subscribers_per_1000_views_upper95": round(1000 * zero_event_upper(tv), 2)} if ts == 0 else {"subscribers_per_1000_views": round(1000.0 * ts / tv, 3)})}
    rep["comparability"] = "records from different metric_source or different measurement windows are not comparable"
    return _out(rep)
def cmd_add(a):
    reg = _registry().get(a.video_id, {}); a.publication_date = a.publication_date or reg.get("publication_date"); a.youtube_video_id = a.youtube_video_id or reg.get("youtube_video_id")
    rec = {"video_id": a.video_id, "youtube_video_id": a.youtube_video_id, "publication_date": a.publication_date, "duration_seconds": a.duration_seconds, "views": a.views, "engaged_views": a.engaged_views,
           "stayed_to_watch_percent": a.stayed_to_watch_percent, "swiped_away_percent": a.swiped_away_percent, "average_view_duration": a.average_view_duration,
           "average_percentage_viewed": a.average_percentage_viewed, "subscribers_gained": a.subscribers_gained, "measurement_timestamp": a.measurement_timestamp,
           "experiment_variant": a.experiment_variant or (_registry().get(a.video_id, {}).get("experiment_variant")) or "baseline_unplanned", "source": "manual_entry", "metric_source": a.metric_source, "recorded_on": datetime.date.today().isoformat(), "notes": a.notes}
    warns = append_measurement(rec); return _out({"status": "added", "warnings": warns})
def _registry(): return {v["video_id"]: v for v in _read_json("videos.json", {"videos": []}).get("videos", [])}
def cmd_import_csv(a):
    mapping = dict(x.split("=", 1) for x in (a.map or []))
    with open(a.file, encoding="utf-8-sig") as f: text = f.read()
    recs, skipped, unmapped = import_csv(text, mapping, _registry(), measured_at=a.measured_at, variant=a.variant)
    if a.write:
        for r, _ in recs: append_measurement(r)
    return _out({"status": "written" if a.write else "dry_run", "records": len(recs), "skipped": skipped, "unmapped_columns": unmapped, "warnings": [w for _, ws in recs for w in ws]})
def cmd_import_api(a):
    reg = _registry()
    if a.video_id not in reg: raise FbError(f"'{a.video_id}' is not in videos.json: register the video first")
    with open(a.file, encoding="utf-8") as f: doc = json.load(f)
    rec, unknown = import_api_json(doc, reg[a.video_id], a.measured_at, a.variant)
    errs, warns = validate_record(rec)
    if errs: raise FbError("invalid record: " + "; ".join(errs))
    if a.write: append_measurement(rec)
    return _out({"status": "written" if a.write else "dry_run", "record": rec, "ignored_columns": unknown, "warnings": warns})
def cmd_evaluate(a):
    hy = _read_json("hypotheses.json", {"hypotheses": []})["hypotheses"]; ms = load_measurements()
    sel = [h for h in hy if not a.hypothesis or h["id"] == a.hypothesis]
    if a.hypothesis and not sel: raise FbError(f"unknown hypothesis '{a.hypothesis}'")
    exps = _read_json("experiments.json", {"experiments": []})["experiments"]
    return _out({"status": "ok", "results": [evaluate_hypothesis(h, ms, exps) for h in sel]})
def videos_per_arm(d, alpha=0.05, power=0.8):
    """Shorts per arm for a standardised difference d (difference / between-Short standard deviation); normal approximation plus 1 for the exact permutation test"""
    return math.ceil(2 * ((_zinv(1 - alpha / 2) + _zinv(power)) / d) ** 2) + 1
def cmd_power(a):
    if a.effect_size:
        return _out({"status": "ok", "effect_size_d": a.effect_size, "videos_per_arm": videos_per_arm(a.effect_size, a.alpha, a.power), "alpha": a.alpha, "power": a.power,
                     "note": "unit = one Short. d = expected difference / between-Short standard deviation, which is unknown until several Shorts exist; two Shorts per arm can never reach p <= 0.05 (design_min_p)",
                     "design_min_p_by_videos_per_arm": {str(k): round(design_min_p(k, k), 4) for k in range(2, 9)}})
    if a.n:
        d = detectable_delta(a.baseline / 100.0, a.n, a.alpha, a.power)
        return _out({"status": "ok", "views_per_arm": a.n, "baseline_percent": a.baseline, "detectable_difference_pp": None if d is None else round(100 * d, 2), "alpha": a.alpha, "power": a.power,
                     "note": "NAIVE: two-sided pooled z test on a proportion that assumes independent views. Views of one Short are not independent and topic effects belong to the Short, so use `--effect-size` (Shorts per arm) for planning"})
    return _out({"status": "ok", "baseline_percent": a.baseline, "difference_pp": a.delta, "views_per_arm": n_per_arm(a.baseline / 100.0, a.delta / 100.0, a.alpha, a.power), "alpha": a.alpha, "power": a.power,
                 "note": "NAIVE: assumes independent views; see --effect-size for the Short-level planning figure"})
def cmd_plan(a):
    exp = plan_experiment(a.id, a.factor, a.variants.split(","), a.videos.split(","), a.seed, a.window_days, a.primary, a.hypotheses.split(",") if a.hypotheses else [], dict(x.split("=", 1) for x in (a.define or [])), a.exp_class, a.lead_threshold)
    if a.write:
        doc = _read_json("experiments.json", {"experiments": []})
        if any(e["id"] == a.id for e in doc["experiments"]): raise FbError(f"experiment {a.id} already exists; pre-registered plans are never rewritten", status="duplicate")
        doc["experiments"].append(exp); _atomic_write(_path("experiments.json"), json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    return _out({"status": "written" if a.write else "dry_run", "experiment": exp})
def cmd_schema(a):
    s = build_schema()
    if a.write: _atomic_write(os.path.join(HERE, "schema", "measurement.schema.json"), json.dumps(s, indent=1, ensure_ascii=False) + "\n")
    return _out(s)

def main(argv=None):
    ap = argparse.ArgumentParser(prog="feedback.py", description=__doc__.split("WHAT THIS IS NOT")[0].strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd"); S = lambda n, **k: sub.add_parser(n, **k)
    S("validate").set_defaults(f=cmd_validate)
    p = S("report"); p.add_argument("--video-id"); p.set_defaults(f=cmd_report)
    p = S("add"); p.add_argument("--video-id", required=True); p.add_argument("--youtube-video-id"); p.add_argument("--publication-date"); p.add_argument("--duration-seconds", type=float, required=True)
    p.add_argument("--views", type=int, required=True); p.add_argument("--engaged-views", type=int); p.add_argument("--stayed-to-watch-percent", type=float); p.add_argument("--swiped-away-percent", type=float)
    p.add_argument("--average-view-duration", type=float); p.add_argument("--average-percentage-viewed", type=float); p.add_argument("--subscribers-gained", type=int)
    p.add_argument("--measurement-timestamp"); p.add_argument("--experiment-variant"); p.add_argument("--metric-source", choices=("studio", "analytics_api")); p.add_argument("--notes"); p.set_defaults(f=cmd_add)
    p = S("import-csv"); p.add_argument("file"); p.add_argument("--map", action="append"); p.add_argument("--measured-at"); p.add_argument("--variant"); p.add_argument("--write", action="store_true"); p.set_defaults(f=cmd_import_csv)
    p = S("import-api-json"); p.add_argument("file"); p.add_argument("--video-id", required=True); p.add_argument("--measured-at"); p.add_argument("--variant"); p.add_argument("--write", action="store_true"); p.set_defaults(f=cmd_import_api)
    p = S("register-video"); p.add_argument("--video-id", required=True); p.add_argument("--title"); p.add_argument("--duration-seconds", type=float, required=True); p.add_argument("--publication-date"); p.add_argument("--youtube-video-id")
    p.add_argument("--slot", help="pre-registered experiment slot, e.g. SHORT3"); p.add_argument("--production-file"); p.add_argument("--production-sha256"); p.set_defaults(f=cmd_register)
    p = S("brief"); p.add_argument("--today", help="YYYY-MM-DD (tests)"); p.set_defaults(f=cmd_brief)
    p = S("evaluate"); p.add_argument("--hypothesis"); p.set_defaults(f=cmd_evaluate)
    p = S("power"); p.add_argument("--baseline", type=float); p.add_argument("--effect-size", type=float); p.add_argument("--delta", type=float); p.add_argument("--n", type=int); p.add_argument("--alpha", type=float, default=0.05); p.add_argument("--power", type=float, default=0.8); p.set_defaults(f=cmd_power)
    p = S("plan-experiment"); p.add_argument("--id", required=True); p.add_argument("--factor", required=True); p.add_argument("--variants", required=True); p.add_argument("--videos", required=True); p.add_argument("--seed", type=int, required=True)
    p.add_argument("--window-days", type=int, default=7); p.add_argument("--primary", default="stayed_to_watch_percent"); p.add_argument("--hypotheses"); p.add_argument("--define", action="append", help="VARIANT=description (repeatable)"); p.add_argument("--class", dest="exp_class", choices=("exploratory", "confirmatory")); p.add_argument("--lead-threshold", type=float, help="smallest difference in the metric's own unit worth following up (exploratory)"); p.add_argument("--write", action="store_true"); p.set_defaults(f=cmd_plan)
    p = S("schema"); p.add_argument("--write", action="store_true"); p.set_defaults(f=cmd_schema)
    try:
        a = ap.parse_args(argv)
        if not getattr(a, "f", None): print(__doc__); return 0
        if a.cmd == "power" and not a.effect_size and not (a.baseline and (a.delta or a.n)): raise FbError("power needs --effect-size (Shorts per arm) or --baseline with --delta (percentage points) or --n (views per arm; naive, independent-views assumption)")
        return a.f(a) or 0
    except FbError as e:
        print(json.dumps({"status": e.status, "error": str(e), **e.extra}, indent=1)); return 2
    except SystemExit: raise
    except (OSError, ValueError) as e:
        print(json.dumps({"status": "error", "error": f"{type(e).__name__}: {e}"}, indent=1)); return 2

if __name__ == "__main__":
    sys.exit(main())
