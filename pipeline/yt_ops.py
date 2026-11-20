#!/usr/bin/env python3
"""yt_ops.py - the YouTube side of the daily pipeline (Orbital Atlas). Runs in GitHub Actions, where the OAuth secrets live.

    python3 pipeline/yt_ops.py status   --out result.json                         # token + channel + scheduled videos (read-only)
    python3 pipeline/yt_ops.py preview  --request req.json --media-dir D --out result.json [--confirm]
    python3 pipeline/yt_ops.py schedule --request req.json --out result.json [--confirm]
    python3 pipeline/yt_ops.py thumbnail --request req.json --media-dir D --out result.json [--confirm]

preview  : uploads the approved-for-review version PRIVATE (no publishAt), sets cover + English captions, reads it back.
schedule : after the owner's "ок" on that version's card, sets privacy private + publishAt (YouTube makes it public at the
           slot), reads it back. It only ever touches the video this pipeline uploaded for that exact file.
thumbnail: replaces ONLY the cover of videos already on this channel (owner-requested restyle). Nothing else on the video
           changes (no title, description, privacy or time). Each (video, file sha256) pair is set at most once.

Duplicate protection (re-runs, repeated "ок", network timeouts):
  * every step writes ledger events keyed by the file sha256 (preview) or the approval id (schedule) BEFORE and AFTER the call;
  * an interrupted preview upload is never repeated blindly: the channel is searched for the marker tag first and the video
    is adopted if it is there; only a record older than 2 h with no such video on the channel is abandoned and retried;
  * a schedule that already happened is only re-verified; the same approval can never move a video to another time;
  * an unclear result is resolved by reading the video from YouTube before anything is sent again.
Without --confirm nothing is sent to YouTube (checks only).
"""
import argparse, json, os, sys, time
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".claude", "skills", "yt-publish"))
sys.path.insert(0, HERE)
import publish as P  # noqa: E402
import engine as E   # noqa: E402

ABANDON_AFTER = timedelta(hours=2)


class OpsError(Exception):
    def __init__(self, msg, kind="error"):
        super().__init__(msg)
        self.kind = kind


def classify(ex):
    s = str(ex)
    if "invalid_grant" in s or "token refresh failed" in s or "is not set" in s:
        return "auth"                                      # owner must log in again; the pipeline waits at this stage
    if "quotaExceeded" in s or "uploadLimitExceeded" in s:
        return "quota"
    return "error"


def fold(key, ledger=None):
    """State of one pipeline key from the ledger: none | started | done (+ video id, timestamps)."""
    st = {"state": "none", "video_id": None, "started_at": None, "steps": []}
    for r in (ledger if ledger is not None else P.ledger_read()):
        if r.get("key") != key:
            continue
        e = r.get("event")
        if e == "pipeline_started":
            st.update(state="started", started_at=r["at"])
        elif e == "pipeline_uploaded":
            st.update(state="done", video_id=r["video_id"])
        elif e == "pipeline_abandoned":
            st.update(state="none", video_id=None, started_at=None, steps=[])
        elif e in ("pipeline_thumbnail_set", "pipeline_captions_set", "pipeline_captions_unavailable"):
            st["steps"].append(e)
        elif e == "pipeline_scheduled":
            st.update(state="done", video_id=r["video_id"], publish_at=r.get("publish_at"))
    return st


def find_marker(token, tag, title):
    """Our own uploads carry the marker tag; used to adopt a video whose upload response was lost."""
    for v in P.inventory(token):
        if v["title"].strip() == title.strip():
            j = P.api("GET", "videos", {"part": "snippet", "id": v["video_id"]}, token=token)
            tags = (j.get("items") or [{}])[0].get("snippet", {}).get("tags", [])
            if tag in tags:
                return v["video_id"]
    return None


def check_channel(token, want):
    j = P.api("GET", "channels", {"part": "id", "mine": "true"}, token=token)
    got = [c["id"] for c in j.get("items", [])]
    if want not in got:
        raise OpsError(f"token belongs to {got}, not to {want}", "wrong_channel")


def op_status(a):
    token = P.access_token()
    ch = P.api("GET", "channels", {"part": "snippet", "mine": "true"}, token=token)
    inv = P.inventory(token)
    # titles of non-public videos stay out of public logs; slot picking needs only times and lengths
    vids = [{"video_id": v["video_id"], "privacy": v["privacy"], "publishAt": v["publishAt"], "publishedAt": v["publishedAt"],
             "seconds": v["seconds"], "title": v["title"] if v["privacy"] == "public" else None} for v in inv]
    return {"ok": True, "channel_id": ch["items"][0]["id"] if ch.get("items") else None, "videos": vids,
            "scheduled": [v for v in vids if v["publishAt"]]}


def op_preview(a):
    req = json.load(open(a.request))
    if req.get("op") != "preview":
        raise OpsError("not a preview request")
    files = req["files"]
    vpath = os.path.join(a.media_dir, os.path.basename(files["video"]))
    if not os.path.isfile(vpath) or P.sha256(vpath) != req["video_sha256"]:
        raise OpsError("video file missing or its sha256 differs from the request")
    for k, hk in (("thumbnail", "thumbnail_sha256"), ("captions", "captions_sha256")):
        p = os.path.join(a.media_dir, os.path.basename(files[k]))
        if not os.path.isfile(p) or P.sha256(p) != req[hk]:
            raise OpsError(f"{k} missing or its sha256 differs from the request")
    key = "preview:" + req["video_sha256"]
    spec = {"file": vpath, "kind": "long", "title": req["title"], "description": req["description"],
            "tags": list(req["tags"]) + [req["marker_tag"]], "category_id": req.get("category_id", "28"),
            "made_for_kids": req["made_for_kids"], "contains_synthetic_media": req["contains_synthetic_media"],
            "default_language": req.get("default_language", "en"), "privacy": "private"}
    P.validate(spec)
    body = P.build_body(spec)
    assert body["status"]["privacyStatus"] == "private" and "publishAt" not in body["status"]
    if not a.confirm:
        return {"ok": True, "dry_run": True, "release": req["release"], "would_upload": fold(key)["state"] == "none"}
    token = P.access_token()
    check_channel(token, req["channel_id"])
    st = fold(key)
    if st["state"] == "started":
        vid = find_marker(token, req["marker_tag"], req["title"])
        if vid:
            P.ledger_add({"event": "pipeline_uploaded", "key": key, "release": req["release"], "video_id": vid, "adopted": True})
        elif datetime.now(timezone.utc) - datetime.fromisoformat(st["started_at"]) > ABANDON_AFTER:
            P.ledger_add({"event": "pipeline_abandoned", "key": key, "release": req["release"], "reason": "not on the channel 2 h after start"})
        else:
            raise OpsError("an earlier upload of this file is still undetermined (under 2 h) - not uploading again", "undetermined")
        st = fold(key)
    if st["state"] == "none":
        with P.ledger_lock():
            if fold(key)["state"] != "none":
                raise OpsError("a parallel run started this upload", "undetermined")
            P.ledger_add({"event": "pipeline_started", "key": key, "release": req["release"], "version": req["version"]})
        res = P.resumable_upload(vpath, body, token)
        P.ledger_add({"event": "pipeline_uploaded", "key": key, "release": req["release"], "video_id": res["id"]})
        st = fold(key)
    vid, warnings = st["video_id"], []
    if "pipeline_thumbnail_set" not in st["steps"]:
        P.set_thumbnail(vid, os.path.join(a.media_dir, os.path.basename(files["thumbnail"])), token)
        P.ledger_add({"event": "pipeline_thumbnail_set", "key": key, "video_id": vid})
    if "pipeline_captions_set" not in st["steps"] and "pipeline_captions_unavailable" not in st["steps"]:
        try:
            P.insert_caption(vid, os.path.join(a.media_dir, os.path.basename(files["captions"])), "en", "English", token)
            P.ledger_add({"event": "pipeline_captions_set", "key": key, "video_id": vid})
        except P.PublishError as ex:
            P.ledger_add({"event": "pipeline_captions_unavailable", "key": key, "video_id": vid, "message": P.redact(ex)[:200]})
            warnings.append("captions not uploaded: " + P.redact(ex)[:120])
    real = P.video_status(vid, token)
    ok = real.get("found") and real.get("privacyStatus") == "private" and not real.get("publishAt")
    P.ledger_add({"event": "pipeline_preview_verified", "key": key, "release": req["release"], "video_id": vid, "ok": bool(ok),
                  "privacyStatus": real.get("privacyStatus"), "uploadStatus": real.get("uploadStatus")})
    return {"ok": bool(ok), "release": req["release"], "version": req["version"], "video_sha256": req["video_sha256"], "video_id": vid,
            "privacyStatus": real.get("privacyStatus"), "uploadStatus": real.get("uploadStatus"), "processing": real.get("processing"),
            "warnings": warnings}


def op_thumbnail(a):
    """Cover-only update of existing videos. Request: {"op": "thumbnail", "channel_id", "reason", "owner_request",
    "items": [{"video_id", "file", "sha256"}]}. Every file is checked (sha256, JPEG/PNG, <= 2 MB) before anything is sent."""
    req = json.load(open(a.request))
    if req.get("op") != "thumbnail":
        raise OpsError("not a thumbnail request")
    if not req.get("owner_request") or not req.get("items"):
        raise OpsError("thumbnail request needs owner_request and items")
    items = []
    for it in req["items"]:
        path = os.path.join(a.media_dir, it["file"])
        if os.path.isabs(it["file"]) or ".." in it["file"].split("/"):
            raise OpsError(f"bad path {it['file']}")
        if not os.path.isfile(path) or P.sha256(path) != it["sha256"]:
            raise OpsError(f"{it['file']} missing or its sha256 differs from the request")
        if os.path.getsize(path) > 2 * 1024 * 1024:
            raise OpsError(f"{it['file']} is over 2 MB")
        items.append((it["video_id"], path, it["sha256"]))
    ledger = P.ledger_read()
    done = {(r.get("video_id"), r.get("sha256")) for r in ledger if r.get("event") == "pipeline_thumbnail_replaced"}
    if not a.confirm:
        return {"ok": True, "dry_run": True, "would_set": [v for v, _, h in items if (v, h) not in done]}
    token = P.access_token()
    check_channel(token, req["channel_id"])
    ours = {v["video_id"] for v in P.inventory(token)}
    res, ok = [], True
    for vid, path, h in items:
        if vid not in ours:
            res.append({"video_id": vid, "result": "refused: not on this channel"}); ok = False; continue
        if (vid, h) in done:
            res.append({"video_id": vid, "result": "already set"}); continue
        try:
            P.set_thumbnail(vid, path, token)
            P.ledger_add({"event": "pipeline_thumbnail_replaced", "key": "thumb:" + vid, "video_id": vid, "sha256": h,
                          "reason": req.get("reason", "")[:120]})
            res.append({"video_id": vid, "result": "set"})
        except (P.PublishError, OSError) as ex:
            res.append({"video_id": vid, "result": "error: " + P.redact(ex)[:160]}); ok = False
    return {"ok": ok, "items": res}


def verify_approval(req, now, ledger):
    a = req["approval"]
    cfg = E.load_config()
    if a.get("actor") not in cfg["owner"]["approval_actors"]:
        raise OpsError("approval is not from the owner's account", "refused")
    for k in ("video_id", "publish_at", "version_hash", "video_sha256"):
        if a.get(k) != req.get(k):
            raise OpsError(f"request {k} differs from the approval", "refused")
    if a.get("status") not in ("valid", "used"):
        raise OpsError(f"approval status {a.get('status')}", "refused")
    pv = fold("preview:" + a["video_sha256"], ledger)
    if pv.get("video_id") != a["video_id"]:
        raise OpsError("the approved video id is not this pipeline's upload of the approved file", "refused")
    t = E.parse(a["publish_at"])
    sched = fold("schedule:" + a["approval_id"], ledger)
    if sched["state"] != "done" and t - now < timedelta(minutes=30):
        raise OpsError("slot is less than 30 minutes away - a new card is needed", "expired")
    if t - now > timedelta(days=30):
        raise OpsError("slot more than 30 days ahead", "refused")
    for r in ledger:                                       # one approval moves one video once; one video gets one approval
        if r.get("event") == "pipeline_scheduled" and r.get("video_id") == a["video_id"] and r.get("key") != "schedule:" + a["approval_id"]:
            raise OpsError("this video was already scheduled by another approval", "refused")
    return a, t, sched


def op_schedule(a):
    req = json.load(open(a.request))
    if req.get("op") != "schedule":
        raise OpsError("not a schedule request")
    now = datetime.now(timezone.utc)
    appr, t, sched = verify_approval(req, now, P.ledger_read())
    key, want = "schedule:" + appr["approval_id"], t.strftime("%Y-%m-%dT%H:%M:%SZ")
    if not a.confirm:
        return {"ok": True, "dry_run": True, "release": req["release"], "approval_id": appr["approval_id"], "already_done": sched["state"] == "done",
                "checked": ["owner actor", "approval = request (video, time, version, file)", "video = this pipeline's private upload of that file",
                            "slot 30 min - 30 days ahead", "video not scheduled by another approval"]}
    if req.get("test") or appr.get("test"):
        raise OpsError("test releases are verified in dry runs only", "refused")
    token = P.access_token()
    check_channel(token, req["channel_id"])
    real = P.video_status(appr["video_id"], token)
    if not real.get("found"):
        raise OpsError("the preview video is not on the channel", "missing")
    if real.get("privacyStatus") == "public":
        raise OpsError("video is already public - nothing changed", "refused")
    if sched["state"] != "done" and real.get("publishAt") != want:
        for v in P.inventory(token):                     # the slot must still be free on the real channel
            if v["video_id"] != appr["video_id"] and v.get("publishAt") and v["seconds"] > 180 and \
                    E.parse(v["publishAt"]).astimezone(E.tzinfo()).date() == t.astimezone(E.tzinfo()).date():
                raise OpsError("another long video is already scheduled that day", "slot_taken")
        P.ledger_add({"event": "pipeline_started", "key": key, "release": req["release"], "video_id": appr["video_id"], "publish_at": want})
        status = {"privacyStatus": "private", "publishAt": want, "selfDeclaredMadeForKids": bool(req.get("made_for_kids", False)),
                  "containsSyntheticMedia": bool(req.get("contains_synthetic_media", False)), "embeddable": True,
                  "license": "youtube", "publicStatsViewable": True}
        try:
            P.api("PUT", "videos", {"part": "status"}, body={"id": appr["video_id"], "status": status}, token=token)
        except (OSError, P.PublishError) as ex:
            time.sleep(5)                                 # unclear result: read the truth before deciding anything
            real = P.video_status(appr["video_id"], token)
            if real.get("publishAt") != want:
                raise OpsError("schedule call failed: " + P.redact(ex)[:200], classify(ex))
        for wait in (0, 5, 10, 20):                       # YouTube's read-back can lag the update by seconds
            time.sleep(wait)
            real = P.video_status(appr["video_id"], token)
            if real.get("publishAt") == want:
                break
    ok = real.get("privacyStatus") == "private" and real.get("publishAt") == want
    if ok and sched["state"] != "done":
        P.ledger_add({"event": "pipeline_scheduled", "key": key, "release": req["release"], "video_id": appr["video_id"], "publish_at": want,
                      "approval_id": appr["approval_id"], "card_id": appr["card_id"]})
        # the existing verify-release workflow confirms the real release after publishAt from these 'uploaded'-style events
        P.ledger_add({"event": "uploaded", "sha256": appr["video_sha256"], "id": req["release"], "video_id": appr["video_id"], "publish_at": want,
                      "via": "pipeline"})
    P.ledger_add({"event": "pipeline_schedule_verified", "key": key, "release": req["release"], "video_id": appr["video_id"], "ok": ok,
                  "privacyStatus": real.get("privacyStatus"), "publishAt": real.get("publishAt")})
    return {"ok": ok, "release": req["release"], "approval_id": appr["approval_id"], "video_id": appr["video_id"],
            "privacyStatus": real.get("privacyStatus"), "publishAt": real.get("publishAt"), "uploadStatus": real.get("uploadStatus")}


def op_scout(a):
    import scout
    req = json.load(open(a.request))
    return {"ok": True, **scout.run(req["queries"][:8])}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("op", choices=["status", "preview", "schedule", "scout", "thumbnail"])
    p.add_argument("--request"); p.add_argument("--media-dir", default="media"); p.add_argument("--out")
    p.add_argument("--confirm", action="store_true")
    a = p.parse_args(argv)
    try:
        res = {"status": op_status, "preview": op_preview, "schedule": op_schedule, "scout": op_scout, "thumbnail": op_thumbnail}[a.op](a)
    except OpsError as ex:
        res = {"ok": False, "error": P.redact(ex)[:300], "error_kind": ex.kind}
    except (P.PublishError, OSError, KeyError, ValueError) as ex:
        res = {"ok": False, "error": P.redact(ex)[:300], "error_kind": classify(ex)}
    if a.request and os.path.isfile(a.request):
        r = json.load(open(a.request))
        res.setdefault("release", r.get("release")); res.setdefault("op", a.op)
        if a.op == "preview":
            res.setdefault("video_sha256", r.get("video_sha256"))
        if a.op == "schedule":
            res.setdefault("approval_id", r["approval"]["approval_id"])
    res["finished_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = json.dumps(res, indent=1, ensure_ascii=False)
    if a.out:
        open(a.out, "w").write(out + "\n")
    print(out)
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
