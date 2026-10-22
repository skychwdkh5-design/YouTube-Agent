#!/usr/bin/env python3
"""release_check.py - independent, READ-ONLY check that scheduled videos really became public.

    python3 release_check.py run [--dry-run]       # what the scheduled workflow runs (every 15 min)
    python3 release_check.py status                # which videos are waiting for their release (ledger only, no network)

Works from the ledger alone (publish-ledger branch), so it needs no Claude session. A video is *awaiting release* when the ledger holds a `verified` event
(ok, with a publishAt) and no `release_confirmed` yet. Rules (publishAt = the time YouTube was asked to publish):

  - before publishAt + 3 min: nothing, no YouTube call;
  - then videos.list status (1 quota unit): public -> ledger `release_confirmed` (and the failure issue, if one was opened, gets a comment and is closed);
  - still private -> ledger `release_check` (attempt n); at attempt 3 a GitHub Issue is opened ONCE (it notifies the owner) with the diagnostics;
    checks continue every run, so a late release is still confirmed; after publishAt + 48 h the video is dropped (`release_check_abandoned`);
  - video missing on the channel -> issue at once;  publishAt moved into the future by someone -> `release_rescheduled`, no alarm.

It never uploads, never edits a video, never changes visibility or time: only videos.list (plus the OAuth token refresh) and GitHub issues.
"""
import json, os, re, subprocess, sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import publish as P  # noqa: E402

GRACE = timedelta(minutes=3)
ISSUE_AT_ATTEMPT = 3
STOP_AFTER = timedelta(hours=48)


def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def awaiting(records):
    """video_id -> state, built only from the ledger."""
    vids = {}
    for r in records:
        vid = r.get("video_id")
        if not vid:
            continue
        e = r.get("event")
        if e == "verified" and r.get("ok") is True and r.get("publishAt") and r.get("kind") != "private_test":
            old = vids.get(vid, {})
            same = old.get("publishAt") == r["publishAt"]
            vids[vid] = {"video_id": vid, "id": r.get("id"), "publishAt": r["publishAt"], "done": False, "attempts": old.get("attempts", 0) if same else 0,
                         "issue": old.get("issue") if same else None, "abandoned": False}
        elif vid in vids:
            v = vids[vid]
            if e == "release_confirmed" and r.get("publishAt") == v["publishAt"]:
                v["done"] = True
            elif e == "release_check" and r.get("publishAt") == v["publishAt"] and r.get("counts", True):
                v["attempts"] += 1
            elif e == "release_issue":
                v["issue"] = r.get("issue")
            elif e == "release_check_abandoned" and r.get("publishAt") == v["publishAt"]:
                v["abandoned"] = True
    return [v for v in vids.values() if not v["done"] and not v["abandoned"]]


def gh(*args):
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError("gh " + args[0] + " failed: " + P.redact(p.stderr)[:200])
    return p.stdout.strip()


def open_issue(title, body):
    out = gh("issue", "create", "--title", title, "--body", body)
    m = re.search(r"/issues/(\d+)", out)
    return int(m.group(1)) if m else None


def diagnostics(v, st):
    keys = ("privacyStatus", "publishAt", "uploadStatus", "processing", "rejectionReason", "failureReason", "madeForKids")
    rep = {k: st.get(k) for k in keys} if st.get("found") else {"found": False}
    return json.dumps(rep, indent=1)


def issue_body(v, st, attempts, now):
    return "\n".join([
        f"Release check: `{v['id']}` (video `{v['video_id']}`) was scheduled for **{v['publishAt']}** but YouTube still reports it as not public.",
        f"Attempts: {attempts}; last check {now:%Y-%m-%d %H:%M} UTC. This is an independent, read-only check; nothing was changed.", "",
        "YouTube status:", "```json", diagnostics(v, st), "```", "",
        "Likely causes: the API project is not audited and the video is locked as private; processing or a copyright/policy check; the schedule was changed in Studio.",
        f"What to do: open https://studio.youtube.com/video/{v['video_id']}/edit and look at Visibility; do NOT re-upload (the ledger blocks duplicates).",
        "Audit form for unaudited API projects: https://support.google.com/youtube/contact/yt_api_form",
        "The check keeps running every 15 minutes and will confirm and close this issue if the video becomes public."])


def run(dry=False, now=None, token_fn=None, status_fn=None):
    now = now or datetime.now(timezone.utc)
    token_fn, status_fn = token_fn or P.access_token, status_fn or P.video_status
    out, token = [], None
    for v in awaiting(P.ledger_read()):
        pa = parse(v["publishAt"])
        if now < pa + GRACE:
            out.append({"video_id": v["video_id"], "id": v["id"], "action": "not due yet", "due_at": (pa + GRACE).isoformat()})
            continue
        if now > pa + STOP_AFTER:
            out.append({"video_id": v["video_id"], "id": v["id"], "action": "abandoned (48 h after publishAt)"})
            if not dry:
                P.ledger_add({"event": "release_check_abandoned", "video_id": v["video_id"], "id": v["id"], "publishAt": v["publishAt"]})
            continue
        token = token or token_fn()
        st = status_fn(v["video_id"], token)
        rec = {"video_id": v["video_id"], "id": v["id"], "publishAt": v["publishAt"]}
        if st.get("found") and st.get("privacyStatus") == "public":
            out.append({**rec, "action": "release_confirmed", "delay_s": int((now - pa).total_seconds())})
            if not dry:
                P.ledger_add({"event": "release_confirmed", **rec, "privacyStatus": "public", "delay_s": int((now - pa).total_seconds())})
                if v["issue"]:
                    gh("issue", "comment", str(v["issue"]), "--body", f"Resolved: `{v['id']}` is public now (check {now:%Y-%m-%d %H:%M} UTC).")
                    gh("issue", "close", str(v["issue"]))
            continue
        new_pa = st.get("publishAt")
        if st.get("found") and new_pa and parse(new_pa) > now:
            out.append({**rec, "action": "release_rescheduled", "new_publishAt": new_pa})
            if not dry:
                P.ledger_add({"event": "release_rescheduled", **rec, "new_publishAt": new_pa})
                P.ledger_add({"event": "release_check", **rec, "counts": False, "note": "rescheduled"})
            continue
        attempts = v["attempts"] + 1
        missing = not st.get("found")
        out.append({**rec, "action": "still not public", "attempt": attempts, "privacyStatus": st.get("privacyStatus"), "found": not missing})
        if dry:
            continue
        P.ledger_add({"event": "release_check", **rec, "attempt": attempts, "privacyStatus": st.get("privacyStatus"), "uploadStatus": st.get("uploadStatus"),
                      "rejectionReason": st.get("rejectionReason"), "failureReason": st.get("failureReason"), "found": not missing})
        if (attempts >= ISSUE_AT_ATTEMPT or missing) and not v["issue"]:
            num = open_issue(f"Release check FAILED: {v['id']} is not public after {v['publishAt']}", issue_body(v, st, attempts, now))
            P.ledger_add({"event": "release_issue", **rec, "issue": num})
            out[-1]["issue"] = num
    return {"dry_run": dry, "checked_at": now.isoformat(timespec="seconds"), "items": out}


def main(argv=None):
    a = argv if argv is not None else sys.argv[1:]
    if not a or a[0] not in ("run", "status"):
        print(__doc__); return 2
    try:
        if a[0] == "status":
            print(json.dumps([{k: v[k] for k in ("id", "video_id", "publishAt", "attempts", "issue")} for v in awaiting(P.ledger_read())], indent=1)); return 0
        print(json.dumps(run(dry="--dry-run" in a), indent=1, ensure_ascii=False)); return 0
    except (P.PublishError, RuntimeError) as e:
        print(json.dumps({"status": "error", "error": P.redact(e)})); return 1


if __name__ == "__main__":
    sys.exit(main())
