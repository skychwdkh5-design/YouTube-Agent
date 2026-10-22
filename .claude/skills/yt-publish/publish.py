#!/usr/bin/env python3
"""publish.py - official YouTube Data API v3 + OAuth 2.0 publishing, stdlib only.

    python3 publish.py auth                      # device-flow login (iPad friendly), stores the refresh token
    python3 publish.py channel                   # read-only: who the token belongs to
    python3 publish.py plan   --spec ep.json     # validate + duplicate check, sends nothing
    python3 publish.py upload --spec ep.json --confirm [--approve-visibility]
    python3 publish.py status --video-id ID      # real status as YouTube reports it
    python3 publish.py inventory                 # read-only list of every video on the channel
    python3 publish.py queue-run --mode autopilot --ids all --media-dir media   # dry run
    python3 publish.py queue-run ... --confirm   # real: upload private + publishAt, thumbnail, captions, verify
    python3 publish.py reconcile [--abandon]     # fix interrupted ('started') uploads
    python3 publish.py ledger

Credentials come from the environment only (YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN) and
are never printed, logged or written to the repo. There is deliberately NO command that edits,
deletes or re-publishes an existing video: this tool can only create new uploads, and a new upload is
PRIVATE unless --approve-visibility is passed together with a non-private spec.

Spec (JSON): file, kind (short|long), title, description, tags[], category_id, made_for_kids (bool),
contains_synthetic_media (bool), privacy (private|unlisted|public, default private),
publish_at (RFC 3339, future - schedules a private video to go public), default_language,
related_long_url (shorts only - appended to the description; the API has no Related-video field).
"""
import contextlib, difflib, fcntl, hashlib, json, os, re, shutil, subprocess, sys, time, urllib.error, urllib.parse, urllib.request, uuid
from datetime import datetime, timezone

SCOPE = "https://www.googleapis.com/auth/youtube"   # device flow does not offer youtube.upload
TOKEN_URL = "https://oauth2.googleapis.com/token"
DEVICE_URL = "https://oauth2.googleapis.com/device/code"
API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LEDGER = os.environ.get("YT_LEDGER", os.path.join(ROOT, "publish", "ledger.jsonl"))
QUEUE = os.path.join(ROOT, "publish", "queue.json")
UP = "https://www.googleapis.com/upload/youtube/v3"
CHUNK = 8 * 1024 * 1024                              # multiple of 256 KiB, as the resumable protocol requires
UA = "YouTube-Agent-yt-publish/1.0"
SECRETS = ("YT_CLIENT_SECRET", "YT_REFRESH_TOKEN", "GH_SECRETS_TOKEN", "GITHUB_TOKEN")


class PublishError(Exception):
    pass


def redact(text):
    text = str(text)
    for k in SECRETS:
        v = os.environ.get(k)
        if v and len(v) > 3:
            text = text.replace(v, "[REDACTED]")
    return text


def http(method, url, headers=None, data=None, timeout=120):
    req = urllib.request.Request(url, data=data, method=method, headers={"User-Agent": UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def jhttp(method, url, headers=None, body=None, form=None):
    h = dict(headers or {})
    data = None
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        h["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json; charset=UTF-8"
    status, hdrs, raw = http(method, url, h, data)
    try:
        parsed = json.loads(raw) if raw else {}
    except ValueError:
        parsed = {"raw": raw[:300].decode("utf-8", "replace")}
    return status, hdrs, parsed


def need(name):
    v = os.environ.get(name)
    if not v:
        raise PublishError(f"{name} is not set (add it as a GitHub Actions secret / environment secret)")
    return v


# --- OAuth ------------------------------------------------------------------------------------------

def access_token():
    s, _, j = jhttp("POST", TOKEN_URL, form={
        "client_id": need("YT_CLIENT_ID"), "client_secret": need("YT_CLIENT_SECRET"),
        "refresh_token": need("YT_REFRESH_TOKEN"), "grant_type": "refresh_token"})
    if s != 200:
        hint = " - the refresh token is dead: re-run the auth step (an app left in 'Testing' expires tokens after 7 days)" if j.get("error") == "invalid_grant" else ""
        raise PublishError(f"token refresh failed: {j.get('error')}{hint}")
    return j["access_token"]


def api(method, path, params=None, body=None, token=None):
    url = f"{API}/{path}" + ("?" + urllib.parse.urlencode(params) if params else "")
    s, _, j = jhttp(method, url, {"Authorization": f"Bearer {token or access_token()}"}, body=body)
    if s >= 400:
        err = (j.get("error") or {})
        raise PublishError(f"YouTube API {s}: {err.get('message', j)} {[e.get('reason') for e in err.get('errors', [])]}")
    return j


def store_secret(name, value):
    """Write a GitHub Actions secret (libsodium sealed box). Needs GH_SECRETS_TOKEN + GITHUB_REPOSITORY."""
    from base64 import b64decode, b64encode
    from nacl import encoding, public  # pip install pynacl (in the workflow)
    repo, h = need("GITHUB_REPOSITORY"), {"Authorization": f"Bearer {need('GH_SECRETS_TOKEN')}", "Accept": "application/vnd.github+json"}
    s, _, k = jhttp("GET", f"https://api.github.com/repos/{repo}/actions/secrets/public-key", h)
    if s != 200:
        raise PublishError(f"cannot read repo public key ({s}); the PAT needs 'Secrets: read and write' on this repo")
    box = public.SealedBox(public.PublicKey(k["key"].encode(), encoding.Base64Encoder()))
    enc = b64encode(box.encrypt(value.encode())).decode()
    s, _, _ = jhttp("PUT", f"https://api.github.com/repos/{repo}/actions/secrets/{name}", h, body={"encrypted_value": enc, "key_id": k["key_id"]})
    if s not in (201, 204):
        raise PublishError(f"storing secret failed ({s})")


def cmd_auth(_):
    cid, csec = need("YT_CLIENT_ID"), need("YT_CLIENT_SECRET")
    s, _, d = jhttp("POST", DEVICE_URL, form={"client_id": cid, "scope": SCOPE})
    if s != 200:
        raise PublishError(f"device code request failed: {d.get('error')} {d.get('error_description', '')}")
    print(f"\n>>> Open {d['verification_url']} and enter the code: {d['user_code']}\n"
          f">>> Choose the Google account that owns the OrbitalAtlas channel (and the channel itself if asked).\n", flush=True)
    deadline, interval = time.time() + d["expires_in"], d.get("interval", 5)
    while time.time() < deadline:
        time.sleep(interval)
        s, _, t = jhttp("POST", TOKEN_URL, form={"client_id": cid, "client_secret": csec, "device_code": d["device_code"],
                                                 "grant_type": "urn:ietf:params:oauth:grant-type:device_code"})
        if s == 200:
            break
        err = t.get("error")
        if err == "slow_down":
            interval += 5
        elif err != "authorization_pending":
            raise PublishError(f"authorization failed: {err}")
    else:
        raise PublishError("code expired before it was entered - run auth again")
    if not t.get("refresh_token"):
        raise PublishError("Google returned no refresh token - remove the app at myaccount.google.com/permissions and retry")
    store_secret("YT_REFRESH_TOKEN", t["refresh_token"])
    return {"status": "ok", "stored_secret": "YT_REFRESH_TOKEN", "scope": t.get("scope")}


# --- channel / status -------------------------------------------------------------------------------

def cmd_channel(_):
    j = api("GET", "channels", {"part": "snippet,statistics,contentDetails", "mine": "true"})
    items = j.get("items", [])
    if not items:
        raise PublishError("token is valid but this Google account has no YouTube channel (pick the brand channel during auth)")
    return {"channels": [{"id": c["id"], "title": c["snippet"]["title"], "customUrl": c["snippet"].get("customUrl"),
                          "videos": c["statistics"].get("videoCount"), "subscribers": c["statistics"].get("subscriberCount"),
                          "hiddenSubs": c["statistics"].get("hiddenSubscriberCount")} for c in items]}


def video_status(vid, token=None):
    j = api("GET", "videos", {"part": "status,processingDetails,snippet", "id": vid}, token=token)
    if not j.get("items"):
        return {"video_id": vid, "found": False}
    v = j["items"][0]
    st, pd = v["status"], v.get("processingDetails", {})
    return {"video_id": vid, "found": True, "title": v["snippet"]["title"], "uploadStatus": st.get("uploadStatus"),
            "privacyStatus": st.get("privacyStatus"), "publishAt": st.get("publishAt"), "madeForKids": st.get("madeForKids"),
            "rejectionReason": st.get("rejectionReason"), "failureReason": st.get("failureReason"),
            "processing": pd.get("processingStatus")}


def cmd_status(a):
    return video_status(a.video_id)


# --- spec ------------------------------------------------------------------------------------------

def parse_time(s):
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        raise PublishError("publish_at must be RFC 3339, e.g. 2026-11-03T15:00:00Z")
    if t.tzinfo is None:
        raise PublishError("publish_at needs a timezone (use Z for UTC)")
    return t.astimezone(timezone.utc)


def validate(spec, now=None):
    now, errs, w = now or datetime.now(timezone.utc), [], []
    for k in ("file", "kind", "title", "description", "made_for_kids", "contains_synthetic_media"):
        if k not in spec:
            errs.append(f"missing '{k}'")
    if errs:
        raise PublishError("; ".join(errs))
    if spec["kind"] not in ("short", "long"):
        errs.append("kind must be short or long")
    if not isinstance(spec["made_for_kids"], bool) or not isinstance(spec["contains_synthetic_media"], bool):
        errs.append("made_for_kids and contains_synthetic_media must be true/false (your decision, never defaulted)")
    t = spec["title"].strip()
    if not 1 <= len(t) <= 100 or re.search(r"[<>]", t):
        errs.append("title must be 1-100 chars without < >")
    if len(spec["description"].encode()) > 5000 or re.search(r"[<>]", spec["description"]):
        errs.append("description over 5000 bytes or contains < >")
    tags = spec.get("tags", [])
    if sum(len(x) + (2 if " " in x else 0) for x in tags) + max(len(tags) - 1, 0) > 500:
        errs.append("tags exceed 500 characters in total")
    if spec.get("privacy", "private") not in ("private", "unlisted", "public"):
        errs.append("privacy must be private, unlisted or public")
    if spec.get("related_long_url") and spec["kind"] != "short":
        errs.append("related_long_url is for shorts only")
    if spec.get("publish_at") and parse_time(spec["publish_at"]) <= now:
        errs.append("publish_at is in the past")
    if not os.path.isfile(spec["file"]):
        errs.append(f"file not found: {spec['file']}")
    elif shutil.which("ffprobe"):
        p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                            "-of", "json", spec["file"]], capture_output=True, text=True)
        try:
            j = json.loads(p.stdout)
            wd, ht, dur = j["streams"][0]["width"], j["streams"][0]["height"], float(j["format"]["duration"])
            if spec["kind"] == "short" and (dur > 180 or ht < wd):
                errs.append(f"not a valid Short: {wd}x{ht}, {dur:.0f}s (needs vertical/square and at most 180s)")
            if spec["kind"] == "long" and dur <= 60:
                w.append(f"{dur:.0f}s long video - is this really a long-form episode?")
        except (ValueError, KeyError, IndexError):
            w.append("ffprobe could not read the file")
    if errs:
        raise PublishError("; ".join(errs))
    return w


def build_body(spec):
    desc = spec["description"].rstrip()
    if spec["kind"] == "short":
        if spec.get("related_long_url") and spec["related_long_url"] not in desc:
            desc += f"\n\nFull video: {spec.get('related_long_title') or 'on this channel'}\n{spec['related_long_url']}"
        if "#shorts" not in desc.lower():
            desc += "\n\n#Shorts"
    snip = {"title": spec["title"].strip(), "description": desc, "tags": spec.get("tags", []),
            "categoryId": str(spec.get("category_id", "27"))}
    if spec.get("default_language"):
        snip["defaultLanguage"] = snip["defaultAudioLanguage"] = spec["default_language"]
    status = {"privacyStatus": spec.get("privacy", "private"), "selfDeclaredMadeForKids": spec["made_for_kids"],
              "containsSyntheticMedia": spec["contains_synthetic_media"], "embeddable": spec.get("embeddable", True)}
    if spec.get("publish_at"):
        status["privacyStatus"] = "private"          # the API requires private + publishAt
        status["publishAt"] = parse_time(spec["publish_at"]).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"snippet": snip, "status": status}


# --- ledger ----------------------------------------------------------------------------------------

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ledger_read(path=None):
    path = path or LEDGER
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(x) for x in f if x.strip()]


def ledger_add(rec, path=None):
    path = path or LEDGER
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **rec}, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


@contextlib.contextmanager
def ledger_lock(path=None):
    path = path or LEDGER
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path + ".lock", "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def ledger_state(digest, path=None):
    """Fold the ledger for one file: none | started | uploaded, plus which post-upload steps are done."""
    st = {"state": "none", "video_id": None, "done": [], "started_at": None, "title": None}
    for r in ledger_read(path):
        if r.get("sha256") != digest:
            continue
        e = r.get("event")
        if e == "started":
            st.update(state="started", video_id=None, done=[], started_at=r["at"], title=r.get("title"))
        elif e == "uploaded":
            st.update(state="uploaded", video_id=r["video_id"])
        elif e == "abandoned":
            st.update(state="none", video_id=None, done=[], started_at=None)
        elif e in ("thumbnail_set", "captions_set", "verified"):
            st["done"].append(e)
    return st


def duplicate_of(digest, path=None):
    """Any earlier record for this file, including an interrupted 'started' one, blocks a re-upload."""
    st = ledger_state(digest, path)
    return st if st["state"] != "none" else None


# --- upload ----------------------------------------------------------------------------------------

def _query_offset(loc, size):
    """Ask the resumable session how many bytes it has: ('done', json) | ('offset', n) | (None, None)."""
    try:
        s, rh, raw = http("PUT", loc, {"Content-Length": "0", "Content-Range": f"bytes */{size}"}, b"", timeout=60)
    except OSError:
        return None, None
    if s in (200, 201):
        return "done", json.loads(raw)
    if s == 308:
        rng = {k.lower(): v for k, v in rh.items()}.get("range")
        return "offset", int(rng.split("-")[1]) + 1 if rng else 0
    return None, None


def resumable_upload(path, body, token):
    size = os.path.getsize(path)
    s, h, j = jhttp("POST", f"{UPLOAD}?uploadType=resumable&part=snippet,status",
                    {"Authorization": f"Bearer {token}", "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/*"}, body=body)
    h = {k.lower(): v for k, v in h.items()}
    if s != 200 or "location" not in h:
        raise PublishError(f"upload session refused ({s}): {j.get('error', j)}")
    loc, sent, fails = h["location"], 0, 0       # the session URL is a bearer capability: never logged or stored
    with open(path, "rb") as f:
        while True:
            f.seek(sent)
            chunk = f.read(CHUNK)
            try:
                s, rh, raw = http("PUT", loc, {"Content-Length": str(len(chunk)), "Content-Range": f"bytes {sent}-{sent + len(chunk) - 1}/{size}"}, chunk, timeout=300)
            except OSError:
                s, rh, raw = 0, {}, b""
            if s in (200, 201):
                return json.loads(raw)
            if s == 308:
                rng = {k.lower(): v for k, v in rh.items()}.get("range")
                sent, fails = (int(rng.split("-")[1]) + 1 if rng else 0), 0
                print(f"  uploaded {sent * 100 // size}%", file=sys.stderr, flush=True)
                continue
            if s == 0 or s >= 500:
                fails += 1
                if fails > 6:
                    raise PublishError("upload kept failing; the ledger keeps a 'started' record - run reconcile")
                time.sleep(min(2 ** fails, 60))
                kind, val = _query_offset(loc, size)
                if kind == "done":
                    return val
                if kind == "offset":
                    sent = val
                continue
            raise PublishError(f"upload failed ({s}): {raw[:200]!r}")


def multipart(meta, data, ctype):
    b = "yt" + uuid.uuid4().hex
    head = f"--{b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{json.dumps(meta)}\r\n--{b}\r\nContent-Type: {ctype}\r\n\r\n".encode()
    return head + data + f"\r\n--{b}--\r\n".encode(), f"multipart/related; boundary={b}"


def _post_raw(url, token, data, ctype):
    s, _, raw = http("POST", url, {"Authorization": f"Bearer {token}", "Content-Type": ctype, "Content-Length": str(len(data))}, data, timeout=120)
    j = json.loads(raw) if raw else {}
    if s >= 400:
        err = j.get("error", {})
        raise PublishError(f"YouTube API {s}: {err.get('message', j)} {[e.get('reason') for e in err.get('errors', [])]}")
    return j


def set_thumbnail(vid, path, token):
    data = open(path, "rb").read()
    if len(data) > 2 * 1024 * 1024:
        raise PublishError("thumbnail over 2 MB")
    if data[:3] == b"\xff\xd8\xff":
        ctype = "image/jpeg"
    elif data[:8] == b"\x89PNG\r\n\x1a\n":
        ctype = "image/png"
    else:
        raise PublishError("thumbnail must be JPEG or PNG")
    return _post_raw(f"{UP}/thumbnails/set?videoId={vid}&uploadType=media", token, data, ctype)


def insert_caption(vid, path, language, name, token):
    meta = {"snippet": {"videoId": vid, "language": language, "name": name, "isDraft": False}}
    body, ctype = multipart(meta, open(path, "rb").read(), "application/octet-stream")
    return _post_raw(f"{UP}/captions?uploadType=multipart&part=snippet", token, body, ctype)


def parse_duration(iso):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    d, h, mi, sec = (int(x or 0) for x in m.groups()) if m else (0, 0, 0, 0)
    return d * 86400 + h * 3600 + mi * 60 + sec


def inventory(token=None):
    """Every video on the channel (uploads playlist), with real status. Read-only; ~3-6 quota units."""
    token = token or access_token()
    ch = api("GET", "channels", {"part": "contentDetails", "mine": "true"}, token=token)
    if not ch.get("items"):
        raise PublishError("no channel for this token")
    pl, ids, page = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"], [], None
    while True:
        p = {"part": "contentDetails", "playlistId": pl, "maxResults": 50, **({"pageToken": page} if page else {})}
        j = api("GET", "playlistItems", p, token=token)
        ids += [i["contentDetails"]["videoId"] for i in j.get("items", [])]
        page = j.get("nextPageToken")
        if not page:
            break
    out = []
    for i in range(0, len(ids), 50):
        j = api("GET", "videos", {"part": "snippet,status,contentDetails", "id": ",".join(ids[i:i + 50])}, token=token)
        for v in j.get("items", []):
            out.append({"video_id": v["id"], "title": v["snippet"]["title"], "privacy": v["status"]["privacyStatus"],
                        "publishAt": v["status"].get("publishAt"), "uploadStatus": v["status"].get("uploadStatus"),
                        "seconds": parse_duration(v["contentDetails"].get("duration")), "publishedAt": v["snippet"].get("publishedAt")})
    return out


def cmd_inventory(_):
    inv = inventory()
    # the repo and its logs are public: show titles only for already-public videos
    return {"count": len(inv), "videos": [{**v, "title": v["title"] if v["privacy"] == "public" else "[non-public]"} for v in inv]}


def cmd_plan(a):
    spec = json.load(open(a.spec))
    warnings = validate(spec)
    dup = duplicate_of(sha256(spec["file"]))
    return {"status": "blocked_duplicate" if dup else "ready", "duplicate_of": dup, "warnings": warnings,
            "request_body": build_body(spec), "needs_approve_visibility": build_body(spec)["status"]["privacyStatus"] != "private" or bool(spec.get("publish_at")),
            "sends_nothing": True}


def cmd_upload(a):
    spec = json.load(open(a.spec))
    plan = cmd_plan(a)
    if plan["status"] != "ready" and not a.force_duplicate:
        raise PublishError("this exact file is already in the ledger (uploaded or interrupted) - check the channel before retrying; --force-duplicate overrides")
    if not a.confirm:
        return plan
    if plan["needs_approve_visibility"] and not a.approve_visibility:
        raise PublishError("spec would make the video visible (unlisted/public/scheduled) - upload it as private, or pass --approve-visibility after the owner agrees")
    digest, body = sha256(spec["file"]), plan["request_body"]
    token = access_token()
    with ledger_lock():
        if duplicate_of(digest) and not a.force_duplicate:
            raise PublishError("a parallel run already started this file")
        ledger_add({"event": "started", "sha256": digest, "file": os.path.basename(spec["file"]), "kind": spec["kind"], "title": body["snippet"]["title"]})
    res = resumable_upload(spec["file"], body, token)
    vid = res["id"]
    ledger_add({"event": "uploaded", "sha256": digest, "video_id": vid, "kind": spec["kind"], "title": body["snippet"]["title"],
                "privacy_requested": body["status"]["privacyStatus"], "publish_at": body["status"].get("publishAt")})
    st = video_status(vid, token)
    ledger_add({"event": "verified", "video_id": vid, "sha256": digest, "uploadStatus": st["uploadStatus"], "privacyStatus": st["privacyStatus"]})
    note = None
    if st["privacyStatus"] != body["status"]["privacyStatus"]:
        note = "YouTube forced a different visibility than requested (unverified API projects are locked to private until the API audit is passed)"
    return {"status": "uploaded", "video_id": vid, "studio_url": f"https://studio.youtube.com/video/{vid}/edit", "reported": st, "note": note}


# --- queue: the only path used by automation --------------------------------------------------------

REQUIRED = ("id", "mode", "kind", "media", "title", "title_status", "description", "made_for_kids",
            "contains_synthetic_media", "publish_at", "owner_approval")


def load_queue(path=None):
    with open(path or QUEUE) as f:
        return json.load(f)["items"]


def load_queue_doc(path=None):
    with open(path or QUEUE) as f:
        return json.load(f)


def _tokens(t):
    return {w for w in re.findall(r"[a-z0-9]+", t.lower()) if len(w) > 2}


def find_conflicts(entry, inv, state):
    """Beyond an exact title: near-identical title, or same kind + (almost) same duration + overlapping title words.
    A video we already uploaded ourselves (ledger state 'uploaded') is not a conflict."""
    if state == "uploaded" or not inv:
        return []
    out, t = [], entry["title"].strip().lower()
    sec, short = entry["media"].get("seconds"), entry["kind"] == "short"
    for v in inv:
        vt = re.sub(r"\s*#shorts\s*$", "", v["title"].strip().lower())
        ratio = difflib.SequenceMatcher(None, t, vt).ratio()
        both = _tokens(t) & _tokens(vt)
        close = sec is not None and abs(v["seconds"] - sec) <= 1.5 and len(both) / max(1, len(_tokens(t) | _tokens(vt))) >= 0.4
        if ratio >= 0.8 or close:
            out.append(f"possible duplicate of {v['video_id']} (title similarity {ratio:.2f}{', same duration' if close else ''})")
    return out


def resolve_related(entry, inv):
    """Short -> its long video. An explicit video_id must exist on the channel, be public, longer than 3 min and carry the
    exact title recorded in the queue; otherwise the long video must be found by title words exactly once."""
    r = entry.get("related")
    if not r:
        return None, None, None
    if r.get("video_id"):
        v = next((x for x in inv if x["video_id"] == r["video_id"]), None)
        if not v or v["seconds"] <= 180 or v["privacy"] != "public":
            return None, None, f"related video {r['video_id']} is not a public long video on the channel"
        if r.get("title") and v["title"] != r["title"]:
            return None, None, f"related video {r['video_id']} is titled '{v['title']}' on YouTube, queue says '{r['title']}'"
        return f"https://youtu.be/{v['video_id']}", v["title"], None
    hits = [v for v in inv if v["seconds"] > 180 and r["title_contains"].lower() in v["title"].lower() and v["privacy"] in ("public", "unlisted")]
    if len(hits) != 1:
        return None, None, f"related long video '{r['title_contains']}': {len(hits)} matches on the channel (need exactly 1, or set related.video_id)"
    return f"https://youtu.be/{hits[0]['video_id']}", hits[0]["title"], None


def find_related(entry, inv):
    url, _, why = resolve_related(entry, inv)
    return url, why


def check_entry(e, mode, media_dir, inv, now=None, hash_media=True):
    """Everything that must be true before this entry may touch YouTube. Returns (problems, spec)."""
    now, pr = now or datetime.now(timezone.utc), []
    miss = [k for k in REQUIRED if k not in e]
    if miss:
        return [f"missing fields: {miss}"], None
    if e.get("open_issues"):
        pr += [f"open issue: {x}" for x in e["open_issues"]]
    if e["mode"] != mode:
        pr.append(f"entry is mode '{e['mode']}', this run is '{mode}'")
    if e["title_status"] != "final":
        pr.append("title is not final (owner has not chosen it)")
    ap, med = e["owner_approval"], e["media"]
    if not (ap.get("approved") is True and ap.get("sha256") == med["sha256"] and ap.get("publish_at") == e["publish_at"]):
        pr.append("no matching owner approval (approved=true with this file's sha256 and this publish_at)")
    path = os.path.join(media_dir, med["asset"])
    if not os.path.isfile(path):
        pr.append(f"media not staged: {med['asset']}")
    elif hash_media and sha256(path) != med["sha256"]:
        pr.append("media sha256 differs from the approved one")
    if e["kind"] == "long" and e.get("thumbnail"):
        tf, rv = os.path.join(ROOT, e["thumbnail"]), e.get("thumbnail_review") or {}
        if not (rv.get("result") == "PASS" and os.path.isfile(tf) and rv.get("sha256") == sha256(tf)):
            pr.append("thumbnail has no PASS review for this exact file (docs/THUMBNAIL_STYLE_GUIDE.md section 5)")
        elif rv.get("owner_approved") is not True:
            pr.append("owner has not visually approved the thumbnail yet")
    for k in ("thumbnail", "captions"):
        f = (e.get(k) or {}).get("file") if k == "captions" else e.get(k)
        if f and not os.path.isfile(os.path.join(ROOT, f)):
            pr.append(f"{k} file missing: {f}")
    if inv is not None:
        st = ledger_state(med["sha256"])
        pr += find_conflicts(e, inv, st["state"])
    url, rtitle, why = resolve_related(e, inv) if (e.get("related") and inv is not None) else (None, None, None)
    if why:
        pr.append(why)
    if e.get("related") and inv is None:
        pr.append("related video cannot be resolved offline")
    if pr:
        return pr, None
    spec = {"file": path, "kind": e["kind"], "title": e["title"], "description": e["description"], "tags": e.get("tags", []),
            "category_id": e.get("category_id", "27"), "made_for_kids": e["made_for_kids"],
            "contains_synthetic_media": e["contains_synthetic_media"], "privacy": "public", "publish_at": e["publish_at"],
            "default_language": e.get("default_language", "en"), "related_long_url": url, "related_long_title": rtitle}
    try:
        validate(spec, now)
    except PublishError as ex:
        return [str(ex)], None
    return [], spec


def run_entry(e, spec, inv, token):
    sha, steps = e["media"]["sha256"], []
    st = ledger_state(sha)
    if st["state"] == "none":
        with ledger_lock():
            if ledger_state(sha)["state"] != "none":
                raise PublishError("a parallel run already started this file")
            ledger_add({"event": "started", "sha256": sha, "id": e["id"], "file": e["media"]["asset"], "kind": e["kind"]})
        body = build_body(spec)
        res = resumable_upload(spec["file"], body, token)
        ledger_add({"event": "uploaded", "sha256": sha, "id": e["id"], "video_id": res["id"], "publish_at": body["status"].get("publishAt")})
        st = ledger_state(sha)
        steps.append("uploaded")
    if st["state"] == "started":
        raise PublishError("an earlier upload of this file was interrupted - reconcile first")
    vid = st["video_id"]
    if e.get("thumbnail") and "thumbnail_set" not in st["done"]:
        set_thumbnail(vid, os.path.join(ROOT, e["thumbnail"]), token)
        ledger_add({"event": "thumbnail_set", "sha256": sha, "id": e["id"], "video_id": vid})
        steps.append("thumbnail")
    cap = e.get("captions")
    if cap and "captions_set" not in st["done"]:
        insert_caption(vid, os.path.join(ROOT, cap["file"]), cap.get("language", "en"), cap.get("name", "English"), token)
        ledger_add({"event": "captions_set", "sha256": sha, "id": e["id"], "video_id": vid})
        steps.append("captions")
    real = video_status(vid, token)
    want = e["publish_at"]
    ok = real.get("privacyStatus") == "private" and real.get("publishAt") == want and real.get("uploadStatus") in ("uploaded", "processed")
    ledger_add({"event": "verified", "sha256": sha, "id": e["id"], "video_id": vid, "ok": ok, "privacyStatus": real.get("privacyStatus"),
                "publishAt": real.get("publishAt"), "uploadStatus": real.get("uploadStatus")})
    return {"video_id": vid, "steps": steps, "verified_scheduled": ok, "reported": {k: real.get(k) for k in ("privacyStatus", "publishAt", "uploadStatus", "rejectionReason", "failureReason")}}


def auto_reconcile(inv, abandon_after_s=7200):
    """Interrupted uploads: adopt the video if YouTube has it, abandon the record if it is old and absent."""
    acts, seen = [], {}
    for r in ledger_read():
        if r.get("event") == "started":
            seen[r["sha256"]] = r
    for sha, r in seen.items():
        st = ledger_state(sha)
        if st["state"] != "started":
            continue
        e = next((x for x in load_queue() if x["media"]["sha256"] == sha), None)
        hit = next((v for v in inv if e and v["title"].strip().lower() == e["title"].strip().lower()), None)
        if hit:
            ledger_add({"event": "uploaded", "sha256": sha, "id": r.get("id"), "video_id": hit["video_id"], "adopted": True})
            acts.append({"id": r.get("id"), "action": "adopted existing video"})
        elif (datetime.now(timezone.utc) - datetime.fromisoformat(st["started_at"])).total_seconds() > abandon_after_s:
            ledger_add({"event": "abandoned", "sha256": sha, "id": r.get("id"), "reason": "not on channel after 2h"})
            acts.append({"id": r.get("id"), "action": "abandoned stale record"})
    return acts


def cmd_queue_run(a):
    items = load_queue(a.queue)
    want = None if a.ids == "all" else set(a.ids.split(","))
    items = [e for e in items if want is None or e["id"] in want]
    if want and len(items) != len(want):
        raise PublishError(f"unknown ids: {want - {e['id'] for e in items}}")
    doc = load_queue_doc(a.queue)
    if not a.offline:
        ch = api("GET", "channels", {"part": "id,snippet", "mine": "true"})["items"][0]
        if ch["id"] != doc.get("expected_channel_id"):
            raise PublishError(f"token belongs to channel {ch['id']} ({ch['snippet'].get('customUrl')}), queue expects {doc.get('expected_channel_id')} - nothing was sent")
    inv = None if a.offline else inventory()
    actions = auto_reconcile(inv) if (inv is not None and a.confirm) else []
    token = access_token() if a.confirm else None
    out = []
    for e in sorted(items, key=lambda x: x.get("publish_at", "")):
        if e.get("mode") != a.mode:
            out.append({"id": e["id"], "status": "skipped", "why": f"mode {e.get('mode')} != {a.mode}"})
            continue
        problems, spec = check_entry(e, a.mode, a.media_dir, inv, hash_media=True)
        if problems:
            out.append({"id": e["id"], "status": "blocked", "problems": problems})
        elif not a.confirm:
            out.append({"id": e["id"], "status": "ready (dry run)", "publish_at": e["publish_at"]})
        else:
            try:
                out.append({"id": e["id"], "status": "done", **run_entry(e, spec, inv, token)})
            except PublishError as ex:
                ledger_add({"event": "error", "sha256": e["media"]["sha256"], "id": e["id"], "message": redact(ex)[:300]})
                out.append({"id": e["id"], "status": "error", "error": redact(ex)})
    return {"dry_run": not a.confirm, "reconcile": actions, "items": out}


def cmd_reconcile(a):
    acts = auto_reconcile(inventory(), abandon_after_s=0 if a.abandon else 7200)
    return {"actions": acts}


def cmd_ledger(_):
    return {"records": ledger_read()}


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth"); sub.add_parser("channel"); sub.add_parser("ledger")
    for n in ("plan", "upload"):
        s = sub.add_parser(n); s.add_argument("--spec", required=True)
        if n == "upload":
            s.add_argument("--confirm", action="store_true"); s.add_argument("--approve-visibility", action="store_true"); s.add_argument("--force-duplicate", action="store_true")
    sub.add_parser("status").add_argument("--video-id", required=True)
    sub.add_parser("inventory")
    sub.add_parser("reconcile").add_argument("--abandon", action="store_true", help="abandon stale 'started' records at once")
    q = sub.add_parser("queue-run")
    q.add_argument("--queue", default=QUEUE); q.add_argument("--mode", required=True, choices=["approval", "autopilot"])
    q.add_argument("--ids", required=True); q.add_argument("--media-dir", required=True)
    q.add_argument("--confirm", action="store_true"); q.add_argument("--offline", action="store_true")
    a = p.parse_args(argv)
    try:
        out = {"auth": cmd_auth, "channel": cmd_channel, "plan": cmd_plan, "upload": cmd_upload, "status": cmd_status, "ledger": cmd_ledger,
               "inventory": cmd_inventory, "queue-run": cmd_queue_run, "reconcile": cmd_reconcile}[a.cmd](a)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    except PublishError as e:
        print(json.dumps({"status": "error", "error": redact(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
