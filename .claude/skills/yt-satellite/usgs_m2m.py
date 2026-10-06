#!/usr/bin/env python3
"""usgs_m2m.py - Landsat evidence from the official USGS EROS M2M API, without inventing any.

    python3 usgs_m2m.py auth
    python3 usgs_m2m.py datasets [--name landsat_ot_c2_l1] [--keyword landsat]
    python3 usgs_m2m.py search --point LAT LON [--radius-km 5] --start 2025-06-01 --end 2025-08-31
    python3 usgs_m2m.py search --bbox MINLON MINLAT MAXLON MAXLAT --start ... --end ... [--cloud 20]
    python3 usgs_m2m.py metadata --entity LC80150332025240LGN00
    python3 usgs_m2m.py options  --entity LC80150332025240LGN00
    python3 usgs_m2m.py download --entity ID --product "Full-Resolution Browse (Natural Color) JPEG" \\
                                 --out ./usgs --confirm [--max-mb 50]

Every command prints JSON. Default dataset: landsat_ot_c2_l1 (Landsat 8-9 OLI/TIRS C2 L1).

Credentials come ONLY from the environment - USGS_M2M_USERNAME and USGS_M2M_TOKEN (an M2M
application token, not the account password). They are never printed, logged or written to disk,
and the session API key is logged out when each command finishes.

A search that finds nothing says so ("status": "no_scenes"). It never falls back to a nearby date,
a different place or a made-up scene. Downloads happen only with --confirm and refuse anything
over --max-mb (default 50 MB) - a full Level-1 bundle is over 1 GB. After a download the order is
removed from the USGS queue (download-order-remove); that cleanup is reported separately under
"cleanup" and never turns a good download into a failure.

Boxes that cross the 180th meridian or reach past a pole are refused with an explanation, never
clipped or wrapped: search each side of 180/-180 as its own --bbox.
"""
import json, math, os, sys, time, urllib.error, urllib.request

API = "https://m2m.cr.usgs.gov/api/api/json/stable/"
DEFAULT_DATASET = "landsat_ot_c2_l1"
UA = "YouTube-Agent-yt-satellite/1.0"


class M2MError(Exception):
    """A clean, reportable failure. `status` goes into the JSON output as-is."""

    def __init__(self, message, status="error", **extra):
        super().__init__(message)
        self.status = status
        self.extra = extra


def _redact(text, secrets):
    text = str(text)
    for s in secrets:
        if s and len(s) > 3:
            text = text.replace(s, "[REDACTED]")
    return text


class M2M:
    """Minimal M2M client. Use as a context manager so the API key is always logged out."""

    def __init__(self, username=None, token=None, timeout=120):
        self.username = (username or os.environ.get("USGS_M2M_USERNAME", "")).strip()
        self.token = (token or os.environ.get("USGS_M2M_TOKEN", "")).strip()
        self.timeout = timeout
        self.key = None

    def _secrets(self):
        return [self.username, self.token, self.key]

    def call(self, endpoint, payload=None, auth=True):
        headers = {"Content-Type": "application/json", "User-Agent": UA}
        if auth:
            if not self.key:
                raise M2MError("not authenticated")
            headers["X-Auth-Token"] = self.key
        req = urllib.request.Request(API + endpoint, data=json.dumps(payload).encode(),
                                     headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                body = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raw = e.read().decode(errors="replace")
            try:
                body = json.loads(raw)
            except ValueError:
                raise M2MError(_redact(f"{endpoint}: HTTP {e.code}: {raw[:300]}", self._secrets()))
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            raise M2MError(_redact(f"{endpoint}: {type(e).__name__}: {e}", self._secrets()))
        if body.get("errorCode"):
            raise M2MError(_redact(f"{endpoint}: {body['errorCode']}: {body.get('errorMessage')}",
                                   self._secrets()))
        return body.get("data")

    def login(self):
        if not self.username or not self.token:
            missing = [n for n, v in (("USGS_M2M_USERNAME", self.username),
                                      ("USGS_M2M_TOKEN", self.token)) if not v]
            raise M2MError("missing environment variable(s): " + ", ".join(missing))
        self.key = self.call("login-token", {"username": self.username, "token": self.token}, auth=False)
        if not self.key:
            raise M2MError("login-token returned no API key")
        return True

    def logout(self):
        if self.key:
            try:
                self.call("logout")
            except M2MError:
                pass
            self.key = None

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, *exc):
        self.logout()

    # --- queries -------------------------------------------------------------------------------

    def datasets(self, name=None, keyword=None):
        # dataset-search matches datasetName as a substring, so a keyword like "landsat" works too
        payload = {"datasetName": name or keyword or "landsat"}
        rows = self.call("dataset-search", payload) or []
        return [{"datasetName": d.get("datasetAlias"), "collectionName": d.get("collectionName"),
                 "abstract": (d.get("abstractText") or "")[:300],
                 "temporal": d.get("temporalCoverage")} for d in rows]

    def search(self, bbox, start, end, dataset=DEFAULT_DATASET, max_results=10, cloud_max=None):
        minlon, minlat, maxlon, maxlat = bbox
        scene_filter = {
            "spatialFilter": {"filterType": "mbr",
                              "lowerLeft": {"latitude": minlat, "longitude": minlon},
                              "upperRight": {"latitude": maxlat, "longitude": maxlon}},
            "acquisitionFilter": {"start": start, "end": end},
        }
        if cloud_max is not None:
            scene_filter["cloudCoverFilter"] = {"min": 0, "max": int(cloud_max), "includeUnknown": False}
        data = self.call("scene-search", {"datasetName": dataset, "maxResults": int(max_results),
                                          "sceneFilter": scene_filter}) or {}
        scenes = [_scene(r) for r in data.get("results") or []]
        return {"dataset": dataset, "query": {"bbox": list(bbox), "start": start, "end": end,
                                              "cloud_max": cloud_max},
                "totalHits": data.get("totalHits", 0), "returned": len(scenes),
                "status": "ok" if scenes else "no_scenes", "scenes": scenes}

    def metadata(self, entity_id, dataset=DEFAULT_DATASET):
        d = self.call("scene-metadata", {"datasetName": dataset, "entityId": entity_id,
                                         "metadataType": "full"})
        if not d:
            raise M2MError(f"no metadata for entity {entity_id} in {dataset}")
        out = _scene(d)
        out["fields"] = {m.get("fieldName"): m.get("value") for m in d.get("metadata") or []
                         if m.get("fieldName")}
        return out

    def options(self, entity_id, dataset=DEFAULT_DATASET):
        rows = self.call("download-options", {"datasetName": dataset, "entityIds": [entity_id]}) or []
        out = []
        for r in rows:
            out.append({"productId": r.get("id"), "productName": r.get("productName"),
                        "available": bool(r.get("available")), "filesize": r.get("filesize"),
                        "entityId": r.get("entityId"),
                        "secondary": [{"productId": s.get("id"), "displayId": s.get("displayId"),
                                       "available": bool(s.get("available")),
                                       "filesize": s.get("filesize")}
                                      for s in r.get("secondaryDownloads") or []]})
        return out

    def download(self, entity_id, product_name, out_dir, dataset=DEFAULT_DATASET,
                 max_mb=50, wait_s=300):
        all_opts = self.options(entity_id, dataset)
        if not all_opts:
            raise M2MError(f"no download options for {entity_id} in {dataset}", status="no_options")
        opts = [o for o in all_opts if o["productName"] == product_name and o["available"]]
        if not opts:
            raise M2MError(f"product '{product_name}' is not available for {entity_id}")
        opt = opts[0]
        size = opt.get("filesize") or 0
        if size > max_mb * 1024 * 1024:
            raise M2MError(f"product is {size / 1048576:.0f} MB, over --max-mb {max_mb}; "
                           "raise --max-mb only if the full file is really needed")
        label = f"yt-satellite-{int(time.time())}"
        try:
            req = self.call("download-request", {"label": label, "downloads": [
                {"entityId": entity_id, "productId": opt["productId"]}]}) or {}
            urls = [d["url"] for d in req.get("availableDownloads") or [] if d.get("url")]
            deadline = time.time() + wait_s
            while not urls and time.time() < deadline:
                time.sleep(10)
                ret = self.call("download-retrieve", {"label": label}) or {}
                urls = [d["url"] for d in ret.get("available") or [] if d.get("url")]
            if not urls:
                raise M2MError(f"download not ready after {wait_s}s (label {label})")
            try:
                os.makedirs(out_dir, exist_ok=True)
            except OSError as e:
                raise M2MError(f"cannot create output directory: {type(e).__name__}: {e}")
            saved = [self._fetch(url, out_dir, entity_id, max_mb) for url in urls]
        except M2MError as e:
            e.extra["cleanup"] = self.cleanup_order(label)
            raise
        return {"status": "ok", "entityId": entity_id, "product": product_name, "files": saved,
                "cleanup": self.cleanup_order(label)}

    def _fetch(self, url, out_dir, entity_id, max_mb):
        """Stream one file to disk, enforcing max_mb while reading; never leaves a partial file."""
        path, n, limit = None, 0, max_mb * 1024 * 1024
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}),
                                        timeout=self.timeout) as r:
                path = os.path.join(out_dir, _filename(r, url, entity_id))
                with open(path, "wb") as f:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk: break
                        n += len(chunk)
                        if n > limit:
                            raise M2MError(f"download exceeded --max-mb {max_mb}; removed partial file")
                        f.write(chunk)
        except (M2MError, urllib.error.URLError, OSError, ValueError) as e:
            if path and os.path.exists(path):
                os.remove(path)
            if isinstance(e, M2MError): raise
            # the URL itself is a signed link - keep it out of the message
            raise M2MError(_redact(f"file download failed: {type(e).__name__}: {e}; "
                                   "removed partial file", self._secrets() + [url]))
        return {"path": path, "bytes": n}

    def cleanup_order(self, label):
        """Remove our download order from the USGS queue (M2M `download-order-remove`).
        Best effort: a failure is reported, never raised, so it cannot undo a good download."""
        try:
            self.call("download-order-remove", {"label": label})
            return {"status": "removed", "label": label}
        except M2MError as e:
            return {"status": "failed", "label": label, "error": str(e)}


def _scene(r):
    tc = r.get("temporalCoverage") or {}
    browse = r.get("browse") or []
    return {"entityId": r.get("entityId"), "displayId": r.get("displayId"),
            "acquired": (tc.get("startDate") or "")[:10] or None,
            "cloudCover": r.get("cloudCover"), "publishDate": r.get("publishDate"),
            "spatialBounds": r.get("spatialBounds"),
            "browse": [b.get("browsePath") for b in browse if b.get("browsePath")][:3]}


def _filename(resp, url, entity_id):
    cd = resp.headers.get("Content-Disposition") or ""
    if "filename=" in cd:
        name = cd.split("filename=")[-1].strip().strip('"; ')
    else:
        name = url.split("?")[0].rstrip("/").split("/")[-1] or entity_id
    return os.path.basename(name) or entity_id


def point_bbox(lat, lon, radius_km):
    import math
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.01))
    return (lon - dlon, lat - dlat, lon + dlon, lat + dlat)


def check_bbox(bbox, from_point=False):
    """Refuse boxes the API cannot take as one rectangle. Coordinates are never clipped, wrapped
    or moved - an edge case is an error that says what to search instead."""
    minlon, minlat, maxlon, maxlat = bbox
    hint = " (from --point/--radius-km)" if from_point else ""
    if not all(math.isfinite(v) for v in bbox):
        raise M2MError(f"bbox{hint} has a non-finite value: {list(bbox)}")
    if minlat < -90 or maxlat > 90:
        raise M2MError(f"bbox{hint} {list(bbox)} reaches past a pole (latitude must stay within "
                       "-90..90); use a smaller --radius-km or an explicit --bbox")
    if minlon < -180 or maxlon > 180:
        raise M2MError(f"bbox{hint} {list(bbox)} crosses the 180th meridian; run two searches "
                       "with --bbox, one on each side of 180/-180")
    if minlon > maxlon:
        raise M2MError(f"bbox {list(bbox)} has MINLON > MAXLON; if it is meant to cross the 180th "
                       "meridian, run two searches, one on each side of 180/-180")
    if not (minlon < maxlon and minlat < maxlat):
        raise M2MError(f"invalid bbox {list(bbox)}: need MINLON < MAXLON and MINLAT < MAXLAT")


# --- CLI ---------------------------------------------------------------------------------------

def _arg(a, flag, n=1, default=None):
    if flag not in a: return default
    i = a.index(flag)
    vals = a[i + 1:i + 1 + n]
    if len(vals) < n: raise M2MError(f"{flag} needs {n} value(s)")
    return vals if n > 1 else vals[0]


def _num(a, flag, n=1, default=None, kind=float, lo=None, hi=None):
    """Numeric flag value(s), validated - a bad value is a clean error, not a traceback."""
    raw = _arg(a, flag, n, default)
    if raw is None: return None
    vals = raw if isinstance(raw, list) else [raw]
    out = []
    for v in vals:
        try:
            x = kind(v)
        except (TypeError, ValueError):
            raise M2MError(f"{flag} expects {'an integer' if kind is int else 'a number'}, got {v!r}")
        if kind is float and not math.isfinite(x):
            raise M2MError(f"{flag} expects a finite number, got {v!r}")
        if (lo is not None and x < lo) or (hi is not None and x > hi):
            raise M2MError(f"{flag} must be between {lo} and {hi}, got {v!r}")
        out.append(x)
    return out if n > 1 else out[0]


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("-h", "--help"): print(__doc__); return 0
    cmd = a[0]
    try:
        dataset = _arg(a, "--dataset", default=DEFAULT_DATASET)
        if cmd not in ("auth", "datasets", "search", "metadata", "options", "download"):
            raise M2MError(f"unknown command {cmd}")
        if cmd == "search":
            start, end = _arg(a, "--start"), _arg(a, "--end")
            if not start or not end: raise M2MError("search needs --start and --end (YYYY-MM-DD)")
            if "--bbox" in a:
                bbox = tuple(_num(a, "--bbox", 4))
                check_bbox(bbox)
            elif "--point" in a:
                lat, lon = _num(a, "--point", 2)
                if not -90 <= lat <= 90: raise M2MError(f"--point latitude must be -90..90, got {lat}")
                if not -180 <= lon <= 180: raise M2MError(f"--point longitude must be -180..180, got {lon}")
                bbox = point_bbox(lat, lon, _num(a, "--radius-km", default=5, lo=0.001, hi=1000))
                check_bbox(bbox, from_point=True)
            else:
                raise M2MError("search needs --point LAT LON or --bbox MINLON MINLAT MAXLON MAXLAT")
            max_results = _num(a, "--max", default=10, kind=int, lo=1, hi=1000)
            cloud = _num(a, "--cloud", lo=0, hi=100)
        if cmd == "download":
            if "--confirm" not in a:
                raise M2MError("download needs --confirm; check `options` first and only download "
                               "imagery that the video actually needs")
            if not _arg(a, "--product"): raise M2MError("download needs --product \"<productName>\"")
            max_mb = _num(a, "--max-mb", default=50, lo=0.001)
        if cmd in ("metadata", "options", "download") and not _arg(a, "--entity"):
            raise M2MError(f"{cmd} needs --entity ENTITY_ID")

        with M2M() as m:
            if cmd == "auth":
                out = {"authenticated": True}
            elif cmd == "datasets":
                rows = m.datasets(_arg(a, "--name"), _arg(a, "--keyword"))
                out = {"status": "ok" if rows else "no_datasets", "datasets": rows}
            elif cmd == "search":
                out = m.search(bbox, start, end, dataset, max_results, cloud)
            elif cmd == "metadata":
                out = m.metadata(_arg(a, "--entity"), dataset)
            elif cmd == "options":
                rows = m.options(_arg(a, "--entity"), dataset)
                out = {"status": "ok" if rows else "no_options", "entityId": _arg(a, "--entity"),
                       "dataset": dataset, "options": rows}
            else:
                out = m.download(_arg(a, "--entity"), _arg(a, "--product"),
                                 _arg(a, "--out", default="./usgs"), dataset, max_mb)
        out["source"] = "USGS EROS M2M API (" + API + ")"
        print(json.dumps(out, indent=1, default=str))
        return 0
    except M2MError as e:
        print(json.dumps({"status": e.status, "error": str(e), **e.extra}, indent=1, default=str))
        return 2
    except Exception as e:  # last resort: still JSON, still redacted, never a traceback
        secrets = [os.environ.get("USGS_M2M_USERNAME", "").strip(),
                   os.environ.get("USGS_M2M_TOKEN", "").strip()]
        print(json.dumps({"status": "error",
                          "error": _redact(f"unexpected {type(e).__name__}: {e}", secrets)}, indent=1))
        return 2


if __name__ == "__main__":
    sys.exit(main())
