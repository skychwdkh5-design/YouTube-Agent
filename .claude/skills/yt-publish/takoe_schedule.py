#!/usr/bin/env python3
"""takoe_schedule.py - scheduled publishing queue for the second channel "Такое бывает" (UCOakEPBhSGwx-2RV0dKGdNA).

    python3 takoe_schedule.py plan         --queue Q --media-dir D --journal J            # dry run: checks + slot plan, sends nothing
    python3 takoe_schedule.py private-test --queue Q --media-dir D --journal J --id X --confirm
    python3 takoe_schedule.py schedule     --queue Q --media-dir D --journal J --confirm [--ids a,b]

Built on publish.py (same OAuth refresh, resumable upload, status read-back). Rules:
- Before any write: channels.list(mine=true) must return exactly UCOakEPBhSGwx-2RV0dKGdNA, otherwise nothing is sent.
- Slots are on the Asia/Ho_Chi_Minh 2-hour grid (00:00, 02:00 ... 22:00 local). The first free slot is at least
  `min_lead_minutes` (30) ahead; every next episode is exactly +2 h. Already scheduled videos on the channel are respected:
  a block that does not fit before them continues after the last one. Once one of our episodes is scheduled, the rest
  always continue after the last scheduled video, so the order inside each series never changes.
- The persistent journal (JSONL, branch takoe-data) keys every episode by queue id + file SHA-256 and records videoId and
  publishAt. A re-run never uploads a file the journal already has a videoId for; an interrupted upload ("started" without
  "uploaded") is adopted only if exactly one channel video carries the episode's exact title, otherwise the episode is skipped.
- A private test upload uses the final metadata; the scheduling run later sets publishAt on THAT videoId (no second upload).
- Uploads are private + publishAt. An episode counts as scheduled only if the read-back from the API shows
  privacyStatus=private, the same publishAt, uploadStatus uploaded/processed and no rejection/failure.
- An API error or an unconfirmed schedule stops the batch (the cause is shared by all episodes); a per-file problem
  (missing media, SHA mismatch, ambiguous match) only skips that episode.
Secrets are never printed (publish.redact).
"""
import argparse, json, os, sys, time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import publish as P  # noqa: E402

EXPECTED_CHANNEL_ID = "UCOakEPBhSGwx-2RV0dKGdNA"
ICT = timezone(timedelta(hours=7))           # Asia/Ho_Chi_Minh, no DST
SLOT = timedelta(hours=2)
READBACK_TRIES, READBACK_WAIT = 9, 10
FIELDS = ("id", "media", "title", "description", "made_for_kids", "contains_synthetic_media", "default_language")


# --- journal ---------------------------------------------------------------------------------------

def jread(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def jadd(path, rec):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    rec = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **rec}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return rec


def jstate(path, eid, sha):
    """Fold the journal for one episode file: state none|started|uploaded|scheduled, video_id, publish_at."""
    st = {"state": "none", "video_id": None, "publish_at": None, "private_test": False}
    for r in jread(path):
        if r.get("id") != eid or r.get("sha256") != sha:
            continue
        ev = r.get("event")
        if ev == "started":
            st.update(state="started")
        elif ev == "uploaded":
            st.update(state="uploaded", video_id=r["video_id"], private_test=bool(r.get("private_test")))
        elif ev == "abandoned":
            st.update(state="none", video_id=None)
        elif ev == "error" and st["state"] == "started" and str(r.get("message", "")).startswith("upload session refused"):
            st.update(state="none")            # YouTube refused before any byte was sent: nothing exists on the channel
        elif ev == "scheduled" and r.get("confirmed"):
            st.update(state="scheduled", video_id=r["video_id"], publish_at=r["publish_at"])
    return st


def jprevious(path, eid, sha):
    """videoIds of earlier file versions of this episode that are still live candidates for replacement."""
    vids, done = {}, set()
    for r in jread(path):
        if r.get("id") != eid or r.get("sha256") == sha:
            continue
        if r.get("event") == "uploaded":
            vids[r["video_id"]] = r["sha256"]
        elif r.get("event") == "replaced" and r.get("confirmed"):
            done.add(r["video_id"])
    return {v: h for v, h in vids.items() if v not in done}


def jall_videos(path, eid):
    return {r["video_id"] for r in jread(path) if r.get("id") == eid and r.get("video_id")}


# --- slots -----------------------------------------------------------------------------------------

def fmt(t):
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def local(t):
    return t.astimezone(ICT).strftime("%Y-%m-%d %H:%M")


def next_grid(t):
    """First slot of the 2-hour Nha Trang grid at or after t."""
    lt = t.astimezone(ICT)
    base = lt.replace(minute=0, second=0, microsecond=0)
    base = base.replace(hour=base.hour - base.hour % 2)
    while base < lt:
        base += SLOT
    return base.astimezone(timezone.utc)


def plan_slots(n, now, taken, after=None, lead_min=30):
    """n consecutive slots, +2 h each. taken: datetimes of videos already scheduled on the channel.
    after: if given, start strictly after it (keeps series order behind our own scheduled episodes)."""
    if n <= 0:
        return []
    start = next_grid(now + timedelta(minutes=lead_min))
    if after is not None:
        start = max(start, next_grid(after + SLOT))
    taken = sorted(taken)
    clash = lambda s: any(abs((s - t).total_seconds()) < SLOT.total_seconds() for t in taken)
    s = start
    while taken and s <= taken[-1]:
        block = [s + SLOT * k for k in range(n)]
        if not any(clash(x) for x in block):
            return block
        s += SLOT
    if taken:
        s = max(s, next_grid(taken[-1] + SLOT))
    return [s + SLOT * k for k in range(n)]


# --- YouTube -------------------------------------------------------------------------------------------

def verify_channel(token):
    j = P.api("GET", "channels", {"part": "id,snippet", "mine": "true"}, token=token)
    ids = [c["id"] for c in j.get("items", [])]
    if ids != [EXPECTED_CHANNEL_ID]:
        raise P.PublishError(f"channel mismatch: token belongs to {ids or 'no channel'}, expected {EXPECTED_CHANNEL_ID}. Nothing was sent.")
    return {"id": ids[0], "title": j["items"][0]["snippet"]["title"].strip()}


def full_status(vid, token):
    j = P.api("GET", "videos", {"part": "snippet,status,processingDetails,contentDetails", "id": vid}, token=token)
    if not j.get("items"):
        return {"video_id": vid, "found": False}
    v = j["items"][0]
    st, sn, pd = v["status"], v["snippet"], v.get("processingDetails", {})
    return {"video_id": vid, "found": True, "title": sn.get("title"), "description_len": len(sn.get("description", "")),
            "defaultLanguage": sn.get("defaultLanguage"), "defaultAudioLanguage": sn.get("defaultAudioLanguage"),
            "categoryId": sn.get("categoryId"), "privacyStatus": st.get("privacyStatus"), "publishAt": st.get("publishAt"),
            "uploadStatus": st.get("uploadStatus"), "madeForKids": st.get("madeForKids"),
            "selfDeclaredMadeForKids": st.get("selfDeclaredMadeForKids"), "containsSyntheticMedia": st.get("containsSyntheticMedia"),
            "rejectionReason": st.get("rejectionReason"), "failureReason": st.get("failureReason"),
            "processingStatus": pd.get("processingStatus"), "duration": v.get("contentDetails", {}).get("duration")}


def same_time(a, b):
    try:
        return a is not None and b is not None and P.parse_time(a) == P.parse_time(b)
    except P.PublishError:
        return False


def scheduled_ok(real, want):
    return (real.get("found") and real.get("privacyStatus") == "private" and same_time(real.get("publishAt"), want)
            and real.get("uploadStatus") in ("uploaded", "processed") and not real.get("rejectionReason") and not real.get("failureReason"))


def spec_for(e, path, publish_at=None):
    s = {"file": path, "kind": e.get("kind", "short"), "title": e["title"], "description": e["description"], "tags": e.get("tags", []),
         "category_id": e.get("category_id", "24"), "made_for_kids": e["made_for_kids"], "contains_synthetic_media": e["contains_synthetic_media"],
         "privacy": "private", "default_language": e["default_language"]}
    if publish_at:
        s["publish_at"] = publish_at
    return s


def unschedule(old, e, r, token, journal):
    """The replaced version stays on the channel as private without a publish time (never deleted)."""
    body = {"id": old, "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": e["made_for_kids"],
                                  "containsSyntheticMedia": e["contains_synthetic_media"], "embeddable": True,
                                  "license": "youtube", "publicStatsViewable": True}}
    P.api("PUT", "videos", {"part": "status"}, body=body, token=token)
    real = full_status(old, token)
    for _ in range(READBACK_TRIES):
        if real.get("privacyStatus") == "private" and not real.get("publishAt"):
            break
        time.sleep(READBACK_WAIT)
        real = full_status(old, token)
    ok = real.get("privacyStatus") == "private" and not real.get("publishAt")
    jadd(journal, {"event": "replaced", "id": e["id"], "sha256": None, "video_id": old, "replaced_by": r.get("video_id") or "new",
                   "confirmed": ok, "privacyStatus": real.get("privacyStatus"), "reported_publishAt": real.get("publishAt")})
    return {"video_id": old, "unscheduled": ok, "privacyStatus": real.get("privacyStatus"), "publishAt": real.get("publishAt")}


def set_schedule(vid, e, publish_at, token):
    body = {"id": vid, "status": {"privacyStatus": "private", "publishAt": publish_at, "selfDeclaredMadeForKids": e["made_for_kids"],
                                  "containsSyntheticMedia": e["contains_synthetic_media"], "embeddable": True,
                                  "license": "youtube", "publicStatsViewable": True}}
    return P.api("PUT", "videos", {"part": "status"}, body=body, token=token)


# --- checks ----------------------------------------------------------------------------------------------

def load(queue_path):
    doc = json.load(open(queue_path, encoding="utf-8"))
    if doc.get("expected_channel_id") != EXPECTED_CHANNEL_ID:
        raise P.PublishError("queue does not target Такое бывает")
    ids = [e["id"] for e in doc["items"]]
    if len(ids) != len(set(ids)):
        raise P.PublishError("duplicate ids in queue")
    return doc


def check_item(e, media_dir):
    pr = [f"missing field {k}" for k in FIELDS if k not in e]
    if pr:
        return pr, None
    path = os.path.join(media_dir, e["media"]["asset"])
    if os.path.basename(e["media"]["asset"]) != e["media"]["asset"] or not e["media"]["asset"].endswith(".mp4"):
        return ["media asset must be a plain .mp4 name"], None
    if not os.path.isfile(path):
        return [f"media not available: {e['media']['asset']}"], None
    if P.sha256(path) != e["media"]["sha256"]:
        return ["media SHA-256 differs from the queue"], None
    if e["made_for_kids"] is not False or not isinstance(e["contains_synthetic_media"], bool):
        return ["audience settings must be explicit (made_for_kids false, contains_synthetic_media bool)"], None
    try:
        warnings = P.validate(spec_for(e, path))
    except P.PublishError as ex:
        return [str(ex)], None
    return [], {"path": path, "warnings": warnings}


def title_hits(e, inv):
    return [v for v in inv if v["title"].strip() == e["title"].strip()]


def state_of(e, journal, inv):
    """Journal state, cross-checked with the channel. Returns (state dict, problem or None)."""
    st = jstate(journal, e["id"], e["media"]["sha256"])
    ours = jall_videos(journal, e["id"])            # earlier versions of this episode are replaced, not duplicates
    hits = [h for h in title_hits(e, inv) if h["video_id"] not in ours]
    if st["video_id"]:
        v = next((x for x in inv if x["video_id"] == st["video_id"]), None)
        if not v:
            return st, f"journal videoId {st['video_id']} is not on the channel any more"
        st["inv"] = v
        return st, None
    if st["state"] == "started":
        if len(hits) == 1:
            return {**st, "state": "adopt", "video_id": hits[0]["video_id"], "inv": hits[0]}, None
        return st, f"an earlier upload has an undetermined result and {len(hits)} channel videos match the title - skipped, check Studio"
    if hits:
        if len(hits) == 1 and hits[0]["privacy"] == "private" and not hits[0].get("publishAt"):
            return st, f"a private video {hits[0]['video_id']} with this exact title exists but is not in the journal - not matched automatically"
        return st, f"already on the channel: {', '.join(h['video_id'] + ' (' + h['privacy'] + (', scheduled' if h.get('publishAt') else '') + ')' for h in hits)}"
    return st, None


def future_taken(inv, now, exclude=()):
    out = []
    for v in inv:
        if v["video_id"] in exclude:
            continue
        if v.get("publishAt") and v["privacy"] == "private":
            t = P.parse_time(v["publishAt"])
            if t > now:
                out.append(t)
    return out


def build_plan(doc, media_dir, journal, inv, now, ids=None):
    order = [e for e in doc["items"] if ids is None or e["id"] in ids]
    rows, todo, ours = [], [], []
    for e in order:
        pr, ok = check_item(e, media_dir)
        st, why = state_of(e, journal, inv) if not pr else ({"state": "none", "video_id": None}, None)
        row = {"id": e["id"], "series": e.get("series"), "episode": e.get("episode"), "version": e.get("version"),
               "sha256": e["media"]["sha256"], "state": st["state"], "video_id": st.get("video_id")}
        fixed = e.get("publish_at")
        if fixed:
            fixed = fmt(P.parse_time(fixed))
        live = st.get("inv") or {}
        prev = {v: h for v, h in jprevious(journal, e["id"], e["media"]["sha256"]).items()
                if any(x["video_id"] == v for x in inv)}
        if any(x["video_id"] in prev and x["privacy"] == "public" for x in inv):
            pr = pr or [f"an earlier version is already public ({', '.join(prev)}) - not replaced"]
        if prev and not pr:
            row["replaces"] = sorted(prev)
            if not fixed:
                old = [x.get("publishAt") for x in inv if x["video_id"] in prev and x.get("publishAt")]
                fixed = fmt(P.parse_time(old[0])) if old else None
        if pr or why:
            row.update(action="skip", reason="; ".join(pr) if pr else why)
        elif live.get("privacy") == "public":
            row.update(action="keep", publish_at=st.get("publish_at"), reason="already public")
        elif fixed and st["state"] == "scheduled" and same_time(st["publish_at"], fixed):
            row.update(action="keep", publish_at=fixed)
        elif fixed:
            # owner-set time: moved on the existing videoId, or uploaded once with it
            if P.parse_time(fixed) < now + timedelta(minutes=int(doc.get("min_lead_minutes", 30))):
                row.update(action="skip", reason=f"fixed time {fixed} is less than the lead time ahead")
            else:
                row.update(action="set_schedule" if st.get("video_id") else "upload_scheduled", path=ok["path"],
                           warnings=ok["warnings"], publish_at=fixed, fixed=True)
        elif st["state"] == "scheduled":
            row.update(action="keep", publish_at=st["publish_at"])
            ours.append(P.parse_time(st["publish_at"]))
        else:
            row.update(action="set_schedule" if st.get("video_id") else "upload_scheduled", path=ok["path"], warnings=ok["warnings"])
            todo.append(row)
        rows.append(row)
    lead = int(doc.get("min_lead_minutes", 30))
    fixed_rows = [r for r in rows if r.get("fixed")]
    ours += [P.parse_time(r["publish_at"]) for r in fixed_rows]
    moving = {r["video_id"] for r in todo + fixed_rows if r.get("video_id")} | {v for r in rows for v in r.get("replaces", [])}
    slots = plan_slots(len(todo), now, future_taken(inv, now, moving), after=max(ours) if ours else None, lead_min=lead)
    for row, s in zip(todo, slots):
        row["publish_at"] = fmt(s)
    for row in rows:
        if row.get("publish_at"):
            row["publish_at_ict"] = local(P.parse_time(row["publish_at"]))
    return rows


# --- commands --------------------------------------------------------------------------------------------

def connect(offline=False):
    if offline:
        return None, None, []
    token = P.access_token()
    ch = verify_channel(token)
    return token, ch, P.inventory(token)


def cmd_plan(a):
    doc = load(a.queue)
    token, ch, inv = connect(a.offline)
    now = datetime.now(timezone.utc)
    rows = build_plan(doc, a.media_dir, a.journal, inv, now, a.ids and set(a.ids.split(",")))
    seen = {r["video_id"] for r in jread(a.journal) if r.get("video_id")}
    known = [full_status(v, token) for v in sorted(seen)] if token else []
    return {"dry_run": True, "channel": ch, "now_ict": local(now), "channel_videos": len(inv), "journal_videos": known,
            "items": [{k: v for k, v in r.items() if k != "path"} for r in rows]}


def cmd_private_test(a):
    doc = load(a.queue)
    e = next((x for x in doc["items"] if x["id"] == a.id), None)
    if not e or e.get("private_test_allowed") is not True:
        raise P.PublishError("unknown id or not cleared for a private test")
    token, ch, inv = connect()
    pr, ok = check_item(e, a.media_dir)
    if pr:
        raise P.PublishError("; ".join(pr))
    st, why = state_of(e, a.journal, inv)
    if why:
        raise P.PublishError(why)
    sha = e["media"]["sha256"]
    if st["state"] == "adopt":
        jadd(a.journal, {"event": "uploaded", "id": e["id"], "sha256": sha, "video_id": st["video_id"], "private_test": True, "adopted": True})
        vid = st["video_id"]
    elif st.get("video_id"):
        vid = st["video_id"]
    else:
        if not a.confirm:
            return {"dry_run": True, "channel": ch, "id": e["id"], "would_upload": {"title": e["title"], "privacy": "private", "publishAt": None}}
        jadd(a.journal, {"event": "started", "id": e["id"], "sha256": sha, "file": e["media"]["asset"], "private_test": True})
        body = P.build_body(spec_for(e, ok["path"]))
        assert body["status"]["privacyStatus"] == "private" and "publishAt" not in body["status"]
        res = P.resumable_upload(ok["path"], body, token)
        vid = res["id"]
        jadd(a.journal, {"event": "uploaded", "id": e["id"], "sha256": sha, "video_id": vid, "private_test": True})
    real = full_status(vid, token)
    checks = {"channel": ch["id"] == EXPECTED_CHANNEL_ID, "found": bool(real.get("found")),
              "private": real.get("privacyStatus") == "private", "no_publishAt_yet": not real.get("publishAt"),
              "title": real.get("title") == e["title"], "language_ru": real.get("defaultLanguage") == e["default_language"],
              "made_for_kids": real.get("selfDeclaredMadeForKids") in (None, e["made_for_kids"]) and real.get("madeForKids") in (None, e["made_for_kids"]),
              "synthetic": real.get("containsSyntheticMedia") in (None, e["contains_synthetic_media"]),
              "upload_ok": real.get("uploadStatus") in ("uploaded", "processed"),
              "not_rejected": not real.get("rejectionReason") and not real.get("failureReason")}
    ok_all = all(checks.values())
    jadd(a.journal, {"event": "private_test_verified", "id": e["id"], "sha256": sha, "video_id": vid, "ok": ok_all,
                     "checks": checks, "processingStatus": real.get("processingStatus"), "uploadStatus": real.get("uploadStatus")})
    return {"id": e["id"], "video_id": vid, "studio_url": f"https://studio.youtube.com/video/{vid}/edit", "sha256": sha,
            "verified_private": ok_all, "checks": checks, "reported": real}


GENERAL = ("quotaExceeded", "uploadLimitExceeded", "rateLimitExceeded", "forbidden", "insufficientPermissions",
           "authError", "invalid_grant", "token refresh failed", "upload session refused", "channel mismatch")


def cmd_schedule(a):
    doc = load(a.queue)
    token, ch, inv = connect()
    now = datetime.now(timezone.utc)
    rows = build_plan(doc, a.media_dir, a.journal, inv, now, a.ids and set(a.ids.split(",")))
    if not a.confirm:
        return {"dry_run": True, "channel": ch, "items": [{k: v for k, v in r.items() if k != "path"} for r in rows]}
    by_id = {e["id"]: e for e in doc["items"]}
    out, stopped, fails, upload_stop = [], None, 0, None
    for r in rows:
        if r["action"] == "upload_scheduled" and upload_stop and not stopped:
            out.append({**{k: v for k, v in r.items() if k != "path"}, "action": "not_run", "reason": f"uploads stopped: {upload_stop}"})
            continue
        if r["action"] in ("skip", "keep") or stopped:
            res = {k: v for k, v in r.items() if k != "path"}
            if stopped and r["action"] not in ("skip", "keep"):
                res.update(action="not_run", reason=f"batch stopped: {stopped}")
            elif r["action"] == "keep":
                real = full_status(r["video_id"], token)
                res.update(confirmed=scheduled_ok(real, r["publish_at"]), reported={k: real.get(k) for k in ("privacyStatus", "publishAt", "uploadStatus", "processingStatus")})
            out.append(res)
            continue
        e, sha, want = by_id[r["id"]], r["sha256"], r["publish_at"]
        if P.parse_time(want) < datetime.now(timezone.utc) + timedelta(minutes=int(doc.get("min_lead_minutes", 30))):
            stopped = f"slot {want} is now less than the lead time ahead - re-run to plan fresh slots"
            out.append({**{k: v for k, v in r.items() if k != "path"}, "action": "not_run", "reason": stopped})
            continue
        try:
            vid = r.get("video_id")
            if r["state"] == "adopt":
                jadd(a.journal, {"event": "uploaded", "id": e["id"], "sha256": sha, "video_id": vid, "adopted": True})
            if vid:
                resp = set_schedule(vid, e, want, token)
                jadd(a.journal, {"event": "update_response", "id": e["id"], "sha256": sha, "video_id": vid, "status": resp.get("status") if isinstance(resp, dict) else None})
                step = "set_publishAt_on_existing_video"
            else:
                jadd(a.journal, {"event": "started", "id": e["id"], "sha256": sha, "file": e["media"]["asset"], "publish_at": want})
                body = P.build_body(spec_for(e, r["path"], want))
                assert body["status"]["privacyStatus"] == "private" and body["status"]["publishAt"] == want
                vid = P.resumable_upload(r["path"], body, token)["id"]
                jadd(a.journal, {"event": "uploaded", "id": e["id"], "sha256": sha, "video_id": vid, "publish_at": want})
                step = "uploaded_private_with_publishAt"
            real = full_status(vid, token)
            ok = scheduled_ok(real, want)
            for _ in range(READBACK_TRIES):          # the API read-back lags a write by up to ~a minute
                if ok:
                    break
                time.sleep(READBACK_WAIT)
                real = full_status(vid, token)
                ok = scheduled_ok(real, want)
            jadd(a.journal, {"event": "scheduled", "id": e["id"], "sha256": sha, "video_id": vid, "publish_at": want, "confirmed": ok,
                             "privacyStatus": real.get("privacyStatus"), "reported_publishAt": real.get("publishAt"),
                             "uploadStatus": real.get("uploadStatus"), "processingStatus": real.get("processingStatus")})
            out.append({"id": e["id"], "series": r["series"], "episode": r["episode"], "version": r["version"], "action": step,
                        "video_id": vid, "publish_at": want, "publish_at_ict": local(P.parse_time(want)), "confirmed": ok,
                        "reported": {k: real.get(k) for k in ("privacyStatus", "publishAt", "uploadStatus", "processingStatus", "rejectionReason", "failureReason")}})
            if not ok:
                fails += 1
                if fails >= 2 or len([o for o in out if o.get("confirmed")]) == 0:
                    stopped = f"YouTube did not confirm the schedule for {e['id']} (read-back {real.get('privacyStatus')}/{real.get('publishAt')}/{real.get('uploadStatus')})"
            else:
                fails = 0
                for old in r.get("replaces", []):
                    out[-1].setdefault("replaced", []).append(unschedule(old, e, {**r, "video_id": vid}, token, a.journal))
        except (P.PublishError, OSError, KeyError, ValueError) as ex:
            msg = P.redact(ex)[:400]
            jadd(a.journal, {"event": "error", "id": e["id"], "sha256": sha, "message": msg})
            out.append({"id": e["id"], "action": "error", "error": msg})
            if "uploadLimitExceeded" in msg:
                upload_stop = msg      # channel upload limit: moving existing videos still works
                continue
            stopped = msg  # an API/upload error is shared by every remaining episode: stop the batch
    return {"dry_run": False, "channel": ch, "stopped": stopped, "items": out}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "private-test", "schedule"):
        q = sub.add_parser(name)
        q.add_argument("--queue", required=True); q.add_argument("--media-dir", required=True); q.add_argument("--journal", required=True)
        q.add_argument("--confirm", action="store_true"); q.add_argument("--ids")
        q.add_argument("--offline", action="store_true")
        if name == "private-test":
            q.add_argument("--id", required=True)
    a = p.parse_args(argv)
    try:
        out = {"plan": cmd_plan, "private-test": cmd_private_test, "schedule": cmd_schedule}[a.cmd](a)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        if a.cmd == "private-test":
            return 0 if out.get("verified_private", out.get("dry_run")) else 1
        if a.cmd == "schedule" and not out.get("dry_run"):
            return 1 if out.get("stopped") or any(i.get("action") == "error" for i in out["items"]) else 0
        return 0
    except P.PublishError as e:
        print(json.dumps({"status": "error", "error": P.redact(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
