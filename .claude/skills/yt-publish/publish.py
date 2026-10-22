#!/usr/bin/env python3
"""publish.py - official YouTube Data API v3 + OAuth 2.0 publishing, stdlib only.

    python3 publish.py auth                      # device-flow login (iPad friendly), stores the refresh token
    python3 publish.py channel                   # read-only: who the token belongs to
    python3 publish.py plan   --spec ep.json     # validate + duplicate check, sends nothing
    python3 publish.py upload --spec ep.json --confirm [--approve-visibility]
    python3 publish.py status --video-id ID      # real status as YouTube reports it
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
import hashlib, json, os, re, shutil, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

SCOPE = "https://www.googleapis.com/auth/youtube"   # device flow does not offer youtube.upload
TOKEN_URL = "https://oauth2.googleapis.com/token"
DEVICE_URL = "https://oauth2.googleapis.com/device/code"
API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos"
LEDGER = os.environ.get("YT_LEDGER", os.path.join(os.path.dirname(__file__), "..", "..", "..", "publish", "ledger.jsonl"))
CHUNK = 8 * 1024 * 1024                              # multiple of 256 KiB, as the resumable protocol requires
UA = "YouTube-Agent-yt-publish/1.0"
SECRETS = ("YT_CLIENT_SECRET", "YT_REFRESH_TOKEN", "GH_SECRETS_TOKEN")


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
        if spec.get("related_long_url"):
            desc += f"\n\nFull video: {spec['related_long_url']}"
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


def duplicate_of(digest, path=None):
    """Any earlier record for this file, including an interrupted 'started' one, blocks a re-upload."""
    for r in ledger_read(path):
        if r.get("sha256") == digest and r.get("event") in ("started", "uploaded"):
            return r
    return None


# --- upload ----------------------------------------------------------------------------------------

def resumable_upload(path, body, token):
    size = os.path.getsize(path)
    s, h, j = jhttp("POST", f"{UPLOAD}?uploadType=resumable&part=snippet,status",
                    {"Authorization": f"Bearer {token}", "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/*"}, body=body)
    h = {k.lower(): v for k, v in h.items()}
    if s != 200 or "location" not in h:
        raise PublishError(f"upload session refused ({s}): {j.get('error', j)}")
    loc, sent = h["location"], 0
    with open(path, "rb") as f:
        while sent < size:
            chunk = f.read(CHUNK)
            end = sent + len(chunk) - 1
            for attempt in range(5):
                s, rh, raw = http("PUT", loc, {"Content-Length": str(len(chunk)), "Content-Range": f"bytes {sent}-{end}/{size}"}, chunk, timeout=300)
                if s in (200, 201, 308):
                    break
                if s < 500:
                    raise PublishError(f"upload failed ({s}): {raw[:200]!r}")
                time.sleep(2 ** attempt)
            else:
                raise PublishError("upload kept failing with 5xx; nothing is lost - see ledger for the 'started' record")
            sent = end + 1
            print(f"  uploaded {sent * 100 // size}%", file=sys.stderr, flush=True)
    return json.loads(raw)


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
    a = p.parse_args(argv)
    try:
        out = {"auth": cmd_auth, "channel": cmd_channel, "plan": cmd_plan, "upload": cmd_upload, "status": cmd_status, "ledger": cmd_ledger}[a.cmd](a)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    except PublishError as e:
        print(json.dumps({"status": "error", "error": redact(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
