#!/usr/bin/env python3
"""yt-media-research: find real photos / video / imagery for a video in permitted libraries and keep a rights ledger. Free, read-only against the sources.

    media.py probe                                   # which libraries are reachable from THIS machine (honest: BLOCKED when the network policy denies)
    media.py search --root productions/S --scene shows --query "salton sea shoreline" [--sources commons,nasa,pexels,pixabay,unsplash]
    media.py add    --root productions/S --scene shows --page-url URL --title T --author A --license "Public Domain" --kind photo [...]   # register a candidate by hand / from a web search
    media.py verify --root productions/S             # re-evaluate every entry against the rules; writes media/ledger.json
    media.py fetch  --root productions/S [--id ID] --confirm   # download ONLY entries whose rights are VERIFIED; writes sha256
    media.py gaps   --root productions/S             # scenes that still have no VERIFIED media
    media.py report --root productions/S

A material enters a render only with status VERIFIED. Everything else (DISCOVERED, UNVERIFIED, NEEDS_OWNER, REJECTED) is excluded by the planner and listed in the
storyboard report. Google (or any web search) is a way to FIND a source page, never a permission: such entries start as DISCOVERED.
"""
import argparse, datetime, hashlib, json, os, re, sys, urllib.error, urllib.parse, urllib.request

UA = "OrbitalAtlas-media-research/1.0 (documentary channel; contact via channel owner)"
KINDS = ("photo", "video", "satellite", "map", "diagram", "rendering", "concept_art", "illustration")
NOT_REALITY = ("rendering", "concept_art", "illustration")          # never shown as a photograph of something that exists
STATUSES = ("DISCOVERED", "UNVERIFIED", "NEEDS_OWNER", "VERIFIED", "REJECTED")

# --- rights rules -------------------------------------------------------------------------------------------------------------------------------------------------
RULES = [   # (regex on the licence text, class, commercial_ok, attribution_required, share_alike, auto_verifiable, note)
    (r"\b(cc0|public domain mark|pdm)\b|^public domain$|\bpd[- ](old|us|usgov|self|author)", "PUBLIC_DOMAIN", True, False, False, True, "credit anyway"),
    (r"\bnasa\b.*(public domain|not copyrighted|media usage)|\b(usgs|us government work|u\.s\. government work|united states government work)\b", "US_GOVERNMENT", True, False, False, True,
     "US government work: usually free to use, credit the agency, never imply endorsement; third-party material inside it (photographer credits, logos) is NOT covered"),
    (r"\bcc[- ]by[- ]sa\b", "CC_BY_SA", True, True, True, False, "share-alike: derivative licensing needs the owner's decision"),
    (r"\bcc[- ]by[- ](nc|nd)", "CC_RESTRICTED", False, True, False, False, "non-commercial or no-derivatives: not usable"),
    (r"\bcc[- ]by\b(?![- ](sa|nc|nd))", "CC_BY", True, True, False, True, "attribution required on screen and in the description"),
    (r"\bpexels license\b", "FREE_LICENSE_PEXELS", True, False, False, True, "no resale of the unaltered file; no implied endorsement by shown persons; trademarks need care"),
    (r"\bpixabay (content )?license\b", "FREE_LICENSE_PIXABAY", True, False, False, True, "no resale of the unaltered file; identifiable people / brands restricted"),
    (r"\bunsplash license\b", "FREE_LICENSE_UNSPLASH", True, False, False, True, "no resale of the unaltered file; people / brands restricted"),
    (r"all rights reserved|\(c\)|©|copyright(ed)?\b|editorial use|getty|istock|shutterstock|alamy", "COPYRIGHTED", False, True, False, False, "copyrighted: needs a licence we do not have"),
]


def classify(license_text):
    t = (license_text or "").strip().lower()
    if not t:
        return {"class": "UNKNOWN", "commercial_ok": None, "attribution_required": None, "share_alike": None, "auto_verifiable": False, "note": "no licence stated"}
    for rx, cls, com, att, sa, auto, note in RULES:
        if re.search(rx, t):
            return {"class": cls, "commercial_ok": com, "attribution_required": att, "share_alike": sa, "auto_verifiable": auto, "note": note}
    return {"class": "UNKNOWN", "commercial_ok": None, "attribution_required": None, "share_alike": None, "auto_verifiable": False, "note": "licence text not recognised"}


def evaluate(e):
    """The status an entry deserves from its own fields. Returns (status, reasons). VERIFIED needs evidence, a recognised free licence, attribution text when required,
    a source URL, and (for anything shown on screen) a local file with sha256."""
    why = []
    rights = classify(e.get("license"))
    e["rights_class"] = rights["class"]
    if rights["class"] in ("CC_RESTRICTED", "COPYRIGHTED"):
        return "REJECTED", [f"licence {e.get('license')!r}: {rights['note']}"]
    if e.get("kind") not in KINDS:
        why.append(f"kind must be one of {KINDS}")
    if not str(e.get("page_url", "")).startswith("https://"):
        why.append("page_url (the source page) must be an https URL")
    if not e.get("author"):
        why.append("author / rights holder missing")
    if not e.get("rights_evidence"):
        why.append("no rights evidence recorded (the licence statement read on the source page, with the date); a search-result snippet is not evidence")
    if rights["class"] == "UNKNOWN":
        why.append("licence unknown")
    if rights["attribution_required"] and not e.get("attribution_text"):
        why.append("attribution required but attribution_text missing")
    if e.get("kind") in NOT_REALITY and not e.get("on_screen_label"):
        why.append("a rendering / concept art / illustration needs an on-screen label (e.g. ARTIST'S RENDERING) and may never stand in for a photograph of a built object")
    if rights["class"] == "CC_BY_SA" or rights["auto_verifiable"] is False and rights["class"] != "UNKNOWN":
        return "NEEDS_OWNER", why + [f"{rights['class']}: {rights['note']}"]
    if why:
        return ("UNVERIFIED" if e.get("rights_evidence") else "DISCOVERED"), why        # DISCOVERED: found, licence never read from the source page
    if e.get("status") != "REJECTED" and (not e.get("local_path") or not e.get("sha256")):
        return "UNVERIFIED", ["rights look fine but the file is not fetched yet (run fetch --confirm); VERIFIED needs the local file and its sha256"]
    return "VERIFIED", [rights["note"]]


# --- ledger -------------------------------------------------------------------------------------------------------------------------------------------------------
def ledger_path(root):
    return os.path.join(root, "media", "ledger.json")


def load(root):
    p = ledger_path(root)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"schema": "yt-media-ledger/1", "entries": []}


def save(root, led):
    p = ledger_path(root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".part"
    json.dump(led, open(tmp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    os.replace(tmp, p)


def refresh(led, root=None):
    """Re-evaluate every entry. With root, a file that is missing or whose sha256 no longer equals the recorded one drops the entry out of VERIFIED."""
    for e in led["entries"]:
        if e.get("status") == "REJECTED" and e.get("rejected_by_owner"):
            continue
        e["status"], e["status_reasons"] = evaluate(e)
        if root and e["status"] == "VERIFIED":
            fp = os.path.join(root, e["local_path"])
            if not os.path.exists(fp) or hashlib.sha256(open(fp, "rb").read()).hexdigest() != e.get("sha256"):
                e["status"], e["status_reasons"] = "UNVERIFIED", ["the file is missing or changed after its rights were verified (sha256 differs)"]
    return led


def new_id(led, title):
    base = re.sub(r"[^a-z0-9]+", "_", (title or "media").lower()).strip("_")[:28] or "media"
    ids = {e["id"] for e in led["entries"]}
    n, i = base, 2
    while n in ids:
        n = f"{base}_{i}"; i += 1
    return n


# --- providers (official APIs only; each returns candidate dicts, never a verified entry) -------------------------------------------------------------------------
def http_json(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers=dict({"User-Agent": UA, "Accept": "application/json"}, **(headers or {})))
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def parse_commons(payload):
    out = []
    for p in (payload.get("query", {}).get("pages") or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        em = ii.get("extmetadata") or {}
        g = lambda k: strip_html((em.get(k) or {}).get("value"))
        lic = g("LicenseShortName") or g("UsageTerms")
        out.append({"source": "commons", "title": p.get("title", "").replace("File:", ""), "page_url": ii.get("descriptionurl"), "file_url": ii.get("url"), "thumb_url": ii.get("thumburl"),
                    "author": g("Artist"), "license": lic, "license_url": g("LicenseUrl"), "attribution_required": g("AttributionRequired").lower() == "true",
                    "copyrighted_flag": g("Copyrighted"), "restrictions": g("Restrictions"), "date": g("DateTimeOriginal"), "description": g("ImageDescription")[:300],
                    "width": ii.get("width"), "height": ii.get("height"), "kind": "video" if str(ii.get("mime", "")).startswith("video") else "photo",
                    "rights_evidence": f"Wikimedia Commons file page extmetadata: LicenseShortName={lic!r}, Copyrighted={g('Copyrighted')!r}, UsageTerms={g('UsageTerms')!r}" if lic else ""})
    return out


def parse_nasa(payload):
    out = []
    for it in (payload.get("collection", {}).get("items") or []):
        d = (it.get("data") or [{}])[0]
        href = next((l.get("href") for l in it.get("links", []) if l.get("render") == "image"), None)
        nid = d.get("nasa_id")
        third = d.get("secondary_creator") or d.get("photographer")
        out.append({"source": "nasa", "title": d.get("title"), "page_url": f"https://images.nasa.gov/details/{nid}" if nid else None, "file_url": href, "author": d.get("secondary_creator") or d.get("center") or "NASA",
                    "license": "NASA media usage guidelines (not copyrighted unless noted; third-party credit: %s)" % third if third else "NASA media usage guidelines (not copyrighted)",
                    "date": d.get("date_created"), "description": strip_html(d.get("description"))[:300], "kind": "video" if d.get("media_type") == "video" else "photo", "nasa_id": nid,
                    "rights_evidence": "NASA Image and Video Library record; usage per https://www.nasa.gov/nasa-brand-center/images-and-media/" if nid else ""})
    return out


def parse_pexels(payload):
    return [{"source": "pexels", "title": p.get("alt") or f"pexels {p.get('id')}", "page_url": p.get("url"), "file_url": (p.get("src") or {}).get("original"), "author": p.get("photographer"),
             "license": "Pexels License", "kind": "photo", "width": p.get("width"), "height": p.get("height"),
             "rights_evidence": "Pexels API result (all content under the Pexels License, https://www.pexels.com/license/)"} for p in payload.get("photos", [])]


def parse_pixabay(payload):
    return [{"source": "pixabay", "title": h.get("tags"), "page_url": h.get("pageURL"), "file_url": h.get("largeImageURL"), "author": h.get("user"), "license": "Pixabay Content License",
             "kind": "video" if h.get("type") == "video" else "photo", "rights_evidence": "Pixabay API result (Pixabay Content License, https://pixabay.com/service/license-summary/)"} for h in payload.get("hits", [])]


def parse_unsplash(payload):
    return [{"source": "unsplash", "title": r.get("description") or r.get("alt_description") or r.get("id"), "page_url": (r.get("links") or {}).get("html"), "file_url": (r.get("urls") or {}).get("full"),
             "author": (r.get("user") or {}).get("name"), "license": "Unsplash License", "kind": "photo", "download_location": (r.get("links") or {}).get("download_location"),
             "rights_evidence": "Unsplash API result (Unsplash License, https://unsplash.com/license)"} for r in payload.get("results", [])]


PROVIDERS = {
    "commons": {"host": "commons.wikimedia.org", "needs_key": None, "parse": parse_commons,
                "url": lambda q, k: "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "generator": "search", "gsrsearch": q + " filetype:bitmap|drawing|video", "gsrnamespace": 6, "gsrlimit": 12,
                       "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 1920, "format": "json"}), "headers": lambda k: {}},
    "nasa": {"host": "images-api.nasa.gov", "needs_key": None, "parse": parse_nasa,
             "url": lambda q, k: "https://images-api.nasa.gov/search?" + urllib.parse.urlencode({"q": q, "media_type": "image,video", "page_size": 12}), "headers": lambda k: {}},
    "pexels": {"host": "api.pexels.com", "needs_key": "PEXELS_API_KEY", "parse": parse_pexels,
               "url": lambda q, k: "https://api.pexels.com/v1/search?" + urllib.parse.urlencode({"query": q, "per_page": 12}), "headers": lambda k: {"Authorization": k}},
    "pixabay": {"host": "pixabay.com", "needs_key": "PIXABAY_API_KEY", "parse": parse_pixabay,
                "url": lambda q, k: "https://pixabay.com/api/?" + urllib.parse.urlencode({"key": k, "q": q, "per_page": 12, "safesearch": "true"}), "headers": lambda k: {}},
    "unsplash": {"host": "api.unsplash.com", "needs_key": "UNSPLASH_ACCESS_KEY", "parse": parse_unsplash,
                 "url": lambda q, k: "https://api.unsplash.com/search/photos?" + urllib.parse.urlencode({"query": q, "per_page": 12}), "headers": lambda k: {"Authorization": "Client-ID " + k}},
}
MANUAL = {"usgs": "USGS has no stable media API: register pages by hand (add); public domain unless the page credits a third party",
          "press": "official press kits / media libraries: register by hand and quote the terms-of-use sentence that permits our use as rights_evidence",
          "web": "web search (Google or other) only DISCOVERS a source page; it is never a licence"}


def probe_host(host):
    try:
        urllib.request.urlopen(urllib.request.Request(f"https://{host}/", headers={"User-Agent": UA}, method="HEAD"), timeout=12)
        return {"host": host, "reachable": True}
    except urllib.error.HTTPError as e:
        return {"host": host, "reachable": e.code < 500 and e.code != 403, "http": e.code, "detail": "HTTP %d" % e.code}
    except Exception as e:                                               # network policy denial surfaces as a failed CONNECT
        return {"host": host, "reachable": False, "detail": f"{type(e).__name__}: {e}"[:120]}


PUBLIC_HOSTS = [   # free public pages and their direct asset hosts: no API key needed; role says what the host is for
    ("svs.gsfc.nasa.gov", "NASA Scientific Visualization Studio", "page+assets"),
    ("science.nasa.gov", "NASA Earth Observatory pages (earthobservatory.nasa.gov redirects here)", "page"),
    ("earthobservatory.nasa.gov", "NASA Earth Observatory (redirect)", "page"),
    ("assets.science.nasa.gov", "NASA Earth Observatory / science image files", "assets"),
    ("www.nasa.gov", "NASA media usage guidelines (the rights text)", "rights"),
    ("images.nasa.gov", "NASA Image and Video Library pages", "page"),
    ("images-api.nasa.gov", "NASA Image and Video Library API (free, no key)", "api"),
    ("images-assets.nasa.gov", "NASA Image and Video Library files", "assets"),
    ("commons.wikimedia.org", "Wikimedia Commons pages and API", "page+api"),
    ("upload.wikimedia.org", "Wikimedia Commons files", "assets"),
    ("www.usgs.gov", "USGS pages (public-domain policy in each image credit)", "page"),
    ("d9-wret.s3.us-west-2.amazonaws.com", "USGS-hosted image files", "assets"),
    ("pubs.usgs.gov", "USGS publications and figures", "page+assets"),
]


def probe_public():
    """Network reachability of the free public sources, one row per host. Reachability says nothing about the right to use a file: that is decided by `rights_evidence`."""
    rows = []
    for host, what, role in PUBLIC_HOSTS:
        try:
            r = urllib.request.urlopen(urllib.request.Request(f"https://{host}/", headers={"User-Agent": UA}), timeout=15)
            rows.append({"host": host, "role": role, "what": what, "network": "OK", "http": r.status})
        except urllib.error.HTTPError as e:
            rows.append({"host": host, "role": role, "what": what, "network": "OK" if e.code < 500 and e.code != 403 else "DENIED", "http": e.code})
        except Exception as e:
            rows.append({"host": host, "role": role, "what": what, "network": "BLOCKED_BY_NETWORK_POLICY" if "403" in str(e) else "UNREACHABLE", "detail": f"{type(e).__name__}: {e}"[:100]})
    return rows


def probe():
    rows = []
    for name, p in PROVIDERS.items():
        r = probe_host(p["host"])
        key = p["needs_key"]
        r.update(source=name, key_env=key, key_present=bool(key and os.environ.get(key)) if key else None)
        r["usable"] = r["reachable"] and (key is None or r["key_present"])
        r["status"] = "OK" if r["usable"] else ("BLOCKED_BY_NETWORK_POLICY" if not r["reachable"] else "NEEDS_API_KEY")
        rows.append(r)
    for name, note in MANUAL.items():
        rows.append({"source": name, "usable": True, "status": "MANUAL", "detail": note})
    return rows


def search(source, query):
    p = PROVIDERS[source]
    key = os.environ.get(p["needs_key"], "") if p["needs_key"] else ""
    if p["needs_key"] and not key:
        return {"source": source, "status": "NEEDS_API_KEY", "env": p["needs_key"], "results": []}
    try:
        return {"source": source, "status": "OK", "results": p["parse"](http_json(p["url"](query, key), p["headers"](key)))}
    except Exception as e:
        return {"source": source, "status": "BLOCKED", "error": f"{type(e).__name__}: {e}"[:200], "results": []}


# --- NASA Scientific Visualization Studio: free public pages, no key ---------------------------------------------------------------------------------------------
SVS_RIGHTS_SENTENCE = "All of our content is in the public domain (unless otherwise noted)"


def parse_svs(html_text):
    """Title, credit, visualizer, release date and movie files of an SVS visualization page, read from the page text itself."""
    import html as H
    t = H.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", html_text, flags=re.S))))
    title = (re.search(r"<title>(?:NASA SVS \| )?(.*?)</title>", html_text, flags=re.S) or [None, ""])[1].strip()
    credit = (re.search(r"Please give credit for this item to:\s*(.*?)\s+Visualizer\b", t) or [None, ""])[1].strip()
    viz = (re.search(r"Visualizer\s+(.*?)\s+(?:Missions|Datasets|Scientist|Producer|Writer|Data provider|Release date)", t) or [None, ""])[1].strip()
    rel = (re.search(r"Released\s+(\w+day, \w+ \d+, \d{4})", t) or [None, ""])[1]
    movies = []
    for m in re.finditer(r"([A-Za-z0-9_\-]+\.(?:mp4|webm))\s*\((\d+)x(\d+)\)\s*\[([\d.]+) (MB|GB|KB)\]", t):
        path = re.search(r'href="([^"]*' + re.escape(m.group(1)) + r')"', html_text)
        movies.append({"file": m.group(1), "w": int(m.group(2)), "h": int(m.group(3)), "size": m.group(4) + " " + m.group(5), "url": ("https://svs.gsfc.nasa.gov" + path.group(1)) if path and path.group(1).startswith("/") else (path.group(1) if path else None)})
    caveats = [w for w in ("music", "copyright", "licensed", "third party", "courtesy") if re.search(w, t, flags=re.I)]
    return {"title": title, "credit": credit, "visualizer": viz, "released": rel, "movies": movies, "caveat_words_on_page": caveats}


def svs_entry(page_url, page, help_text, today):
    """A ledger entry for an SVS visualization. The rights evidence is the sentence actually found on the SVS help page plus what the item page says (or does not say)."""
    movie = next((m for m in page["movies"] if "Web" in m["file"] and m["url"]), None) or next((m for m in page["movies"] if m["url"] and m["w"] <= 1920), None)
    found = SVS_RIGHTS_SENTENCE.lower() in re.sub(r"\s+", " ", help_text).lower()
    ev = (f"{today}: read https://svs.gsfc.nasa.gov/help/ FAQ: \"{SVS_RIGHTS_SENTENCE}\"" if found else "") + \
         (f"; item page {page_url} credits '{page['credit']}', visualizer {page['visualizer']}; caveat words on the item page: {page['caveat_words_on_page'] or 'none'}" if found else "")
    return {"title": page["title"], "page_url": page_url, "file_url": movie["url"] if movie else None, "kind": "video", "author": f"{page['credit']}; visualizer {page['visualizer']}".strip("; "),
            "license": "NASA SVS public domain (unless otherwise noted)", "license_url": "https://svs.gsfc.nasa.gov/help/", "date": page["released"],
            "attribution_text": f"{page['title']} / {page['credit']}, Scientific Visualization Studio", "rights_evidence": ev, "discovered_by": "svs-page",
            "svs_note": "if the item page names music or a third party, the audio/third-party part is NOT public domain: decide before use" if page["caveat_words_on_page"] else ""}


# --- CLI ----------------------------------------------------------------------------------------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    s = sub.add_parser("svs"); s.add_argument("--root", required=True); s.add_argument("--scene", required=True); s.add_argument("--url", required=True); s.add_argument("--fetch", action="store_true")
    for n in ("verify", "gaps", "report"):
        s = sub.add_parser(n); s.add_argument("--root", required=True)
    s = sub.add_parser("search"); s.add_argument("--root", required=True); s.add_argument("--scene", required=True); s.add_argument("--query", required=True); s.add_argument("--sources", default="commons,nasa,pexels,pixabay,unsplash")
    s = sub.add_parser("add"); s.add_argument("--root", required=True); s.add_argument("--scene", required=True)
    for k in ("page-url", "title", "author", "license", "kind", "file-url", "license-url", "attribution-text", "rights-evidence", "on-screen-label", "date", "discovered-by", "claims"):
        s.add_argument("--" + k)
    s.add_argument("--depicts-reality", choices=("true", "false"), default="true")
    s = sub.add_parser("fetch"); s.add_argument("--root", required=True); s.add_argument("--id"); s.add_argument("--confirm", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "probe":
        print(json.dumps({"api_providers": probe(), "free_public_hosts": probe_public()}, indent=1)); return 0
    if a.cmd == "svs":
        def get(u):
            return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=40).read().decode("utf-8", "replace")
        try:
            pg_html, helpt = get(a.url), get("https://svs.gsfc.nasa.gov/help/")
        except Exception as e:
            print(json.dumps({"status": "BLOCKED", "error": f"{type(e).__name__}: {e}"[:200]})); return 1
        page = parse_svs(pg_html)
        led = load(a.root)
        e = dict(svs_entry(a.url, page, helpt, datetime.date.today().isoformat()), scene=a.scene, depicts_reality=True, found_at=datetime.date.today().isoformat())
        e["id"] = new_id(led, page["title"])
        e["status"], e["status_reasons"] = evaluate(e)
        led["entries"].append(e); save(a.root, led)
        print(json.dumps({"id": e["id"], "status": e["status"], "reasons": e["status_reasons"], "file_url": e["file_url"], "movies": page["movies"]}, indent=1)); return 0
    if a.cmd == "search":
        led = load(a.root); out = []
        for src in a.sources.split(","):
            if src not in PROVIDERS:
                out.append({"source": src, "status": "UNKNOWN_SOURCE"}); continue
            r = search(src, a.query)
            n = 0
            for c in r["results"]:
                if not c.get("page_url"):
                    continue
                led["entries"].append(dict(c, id=new_id(led, c.get("title")), scene=a.scene, status="UNVERIFIED", query=a.query, found_at=datetime.date.today().isoformat(), depicts_reality=True,
                                           file_url=c.get("file_url"), attribution_text=(f"{c.get('title')} / {c.get('author')} / {c.get('license')}" if c.get("author") else None)))
                n += 1
            out.append({"source": src, "status": r["status"], "added": n, **({"error": r["error"]} if r.get("error") else {}), **({"env": r["env"]} if r.get("env") else {})})
        save(a.root, refresh(led)); print(json.dumps(out, indent=1)); return 0
    led = load(a.root)
    if a.cmd == "add":
        if not a.page_url or not a.title:
            print(json.dumps({"status": "error", "error": "--page-url and --title are required"})); return 1
        e = {"id": new_id(led, a.title), "scene": a.scene, "title": a.title, "page_url": a.page_url, "author": a.author, "license": a.license, "kind": a.kind or "photo", "file_url": a.file_url,
             "license_url": a.license_url, "attribution_text": a.attribution_text, "rights_evidence": a.rights_evidence, "on_screen_label": a.on_screen_label, "date": a.date,
             "discovered_by": a.discovered_by, "depicts_reality": a.depicts_reality == "true", "claims": (a.claims or "").split(",") if a.claims else [], "found_at": datetime.date.today().isoformat()}
        e["status"], e["status_reasons"] = evaluate(e)
        led["entries"].append(e); save(a.root, led); print(json.dumps({"status": e["status"], "id": e["id"], "reasons": e["status_reasons"]}, indent=1)); return 0
    if a.cmd == "verify":
        save(a.root, refresh(led, a.root)); print(json.dumps({e["id"]: e["status"] for e in led["entries"]}, indent=1)); return 0
    if a.cmd == "gaps":
        scenes = sorted({e["scene"] for e in led["entries"]})
        print(json.dumps({s: {"verified": [e["id"] for e in led["entries"] if e["scene"] == s and e["status"] == "VERIFIED"], "candidates": [(e["id"], e["status"]) for e in led["entries"] if e["scene"] == s and e["status"] != "VERIFIED"]} for s in scenes}, indent=1)); return 0
    if a.cmd == "fetch":
        res = []
        for e in led["entries"]:
            if a.id and e["id"] != a.id:
                continue
            if e.get("status") != "VERIFIED" and not (e.get("status") == "UNVERIFIED" and "file is not fetched yet" in " ".join(e.get("status_reasons") or [])):
                res.append({"id": e["id"], "skipped": f"status {e['status']}: only rights-cleared entries are downloaded"}); continue
            if not a.confirm:
                res.append({"id": e["id"], "would_fetch": e.get("file_url")}); continue
            try:
                req = urllib.request.Request(e["file_url"], headers={"User-Agent": UA})
                data = urllib.request.urlopen(req, timeout=120).read()
            except Exception as ex:
                res.append({"id": e["id"], "error": f"{type(ex).__name__}: {ex}"[:160]}); continue
            ext = os.path.splitext(urllib.parse.urlparse(e["file_url"]).path)[1].lower() or ".jpg"
            rel = os.path.join("media", "assets", e["id"] + ext)
            os.makedirs(os.path.join(a.root, "media", "assets"), exist_ok=True)
            open(os.path.join(a.root, rel), "wb").write(data)
            e.update(local_path=rel, sha256=hashlib.sha256(data).hexdigest(), retrieved=datetime.date.today().isoformat())
            res.append({"id": e["id"], "saved": rel, "bytes": len(data)})
        save(a.root, refresh(led)); print(json.dumps(res, indent=1)); return 0
    if a.cmd == "report":
        c = {}
        for e in led["entries"]:
            c[e["status"]] = c.get(e["status"], 0) + 1
        print(json.dumps({"entries": len(led["entries"]), "by_status": c, "verified_ids": [e["id"] for e in led["entries"] if e["status"] == "VERIFIED"]}, indent=1)); return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
