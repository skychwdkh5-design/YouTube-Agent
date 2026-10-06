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
over --max-mb (default 50 MB) - a full Level-1 bundle is over 1 GB.
"""
import json, os, sys, time, urllib.error, urllib.request

API = "https://m2m.cr.usgs.gov/api/api/json/stable/"
DEFAULT_DATASET = "landsat_ot_c2_l1"
UA = "YouTube-Agent-yt-satellite/1.0"


class M2MError(Exception):
    pass


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
        opts = [o for o in self.options(entity_id, dataset)
                if o["productName"] == product_name and o["available"]]
        if not opts:
            raise M2MError(f"product '{product_name}' is not available for {entity_id}")
        opt = opts[0]
        size = opt.get("filesize") or 0
        if size > max_mb * 1024 * 1024:
            raise M2MError(f"product is {size / 1048576:.0f} MB, over --max-mb {max_mb}; "
                           "raise --max-mb only if the full file is really needed")
        label = f"yt-satellite-{int(time.time())}"
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
        os.makedirs(out_dir, exist_ok=True)
        saved = []
        for url in urls:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}),
                                        timeout=self.timeout) as r:
                name = _filename(r, url, entity_id)
                path = os.path.join(out_dir, name)
                limit, n = max_mb * 1024 * 1024, 0
                with open(path, "wb") as f:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk: break
                        n += len(chunk)
                        if n > limit:
                            f.close(); os.remove(path)
                            raise M2MError(f"download exceeded --max-mb {max_mb}; removed partial file")
                        f.write(chunk)
            saved.append({"path": path, "bytes": n})
        return {"entityId": entity_id, "product": product_name, "files": saved}


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


# --- CLI ---------------------------------------------------------------------------------------

def _arg(a, flag, n=1, default=None):
    if flag not in a: return default
    i = a.index(flag)
    vals = a[i + 1:i + 1 + n]
    if len(vals) < n: raise SystemExit(f"{flag} needs {n} value(s)")
    return vals if n > 1 else vals[0]


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("-h", "--help"): print(__doc__); return 0
    cmd, dataset = a[0], _arg(a, "--dataset", default=DEFAULT_DATASET)
    try:
        if cmd == "search":
            start, end = _arg(a, "--start"), _arg(a, "--end")
            if not start or not end: raise M2MError("search needs --start and --end (YYYY-MM-DD)")
            if "--bbox" in a:
                bbox = tuple(float(x) for x in _arg(a, "--bbox", 4))
            elif "--point" in a:
                lat, lon = (float(x) for x in _arg(a, "--point", 2))
                bbox = point_bbox(lat, lon, float(_arg(a, "--radius-km", default=5)))
            else:
                raise M2MError("search needs --point LAT LON or --bbox MINLON MINLAT MAXLON MAXLAT")
            if not (-180 <= bbox[0] < bbox[2] <= 180 and -90 <= bbox[1] < bbox[3] <= 90):
                raise M2MError(f"invalid bbox {bbox}")
        if cmd == "download" and "--confirm" not in a:
            raise M2MError("download needs --confirm; check `options` first and only download "
                           "imagery that the video actually needs")
        if cmd not in ("auth", "datasets", "search", "metadata", "options", "download"):
            raise M2MError(f"unknown command {cmd}")
        if cmd in ("metadata", "options", "download") and not _arg(a, "--entity"):
            raise M2MError(f"{cmd} needs --entity ENTITY_ID")

        with M2M() as m:
            if cmd == "auth":
                out = {"authenticated": True}
            elif cmd == "datasets":
                rows = m.datasets(_arg(a, "--name"), _arg(a, "--keyword"))
                out = {"status": "ok" if rows else "no_datasets", "datasets": rows}
            elif cmd == "search":
                cloud = _arg(a, "--cloud")
                out = m.search(bbox, start, end, dataset, int(_arg(a, "--max", default=10)),
                               float(cloud) if cloud is not None else None)
            elif cmd == "metadata":
                out = m.metadata(_arg(a, "--entity"), dataset)
            elif cmd == "options":
                rows = m.options(_arg(a, "--entity"), dataset)
                out = {"entityId": _arg(a, "--entity"), "dataset": dataset, "options": rows}
            else:
                product = _arg(a, "--product")
                if not product: raise M2MError("download needs --product \"<productName>\"")
                out = m.download(_arg(a, "--entity"), product, _arg(a, "--out", default="./usgs"),
                                 dataset, float(_arg(a, "--max-mb", default=50)))
        out["source"] = "USGS EROS M2M API (" + API + ")"
        print(json.dumps(out, indent=1, default=str))
        return 0
    except M2MError as e:
        print(json.dumps({"status": "error", "error": str(e)}, indent=1))
        return 2


if __name__ == "__main__":
    sys.exit(main())
