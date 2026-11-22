#!/usr/bin/env python3
"""nexora_ops.py - NEXORA releases of the daily pipeline through NEXORA's own, existing YouTube machinery.

NEXORA keeps its own repository, channel token (NEXORA_YT_* secrets) and workflow (`nexora-youtube.yml` on branch
`youtube-ops`). This adapter only writes the files that workflow already understands, so no NEXORA code changes:

    python3 pipeline/nexora_ops.py request  --release R --ops-dir ../nexora-ops     # publish/requests/<id>.json + media/ (private upload)
    python3 pipeline/nexora_ops.py preview  --release R --ops-dir ../nexora-ops     # read publish/ledger.json -> preview-result JSON
    python3 pipeline/nexora_ops.py status   --ops-dir ../nexora-ops                 # channel_videos from publish/last-run.json (for slots)
    python3 pipeline/nexora_ops.py approval --release R --ops-dir ../nexora-ops     # publish/approvals/<id>.json (privacy scheduled)
    python3 pipeline/nexora_ops.py schedule --release R --ops-dir ../nexora-ops     # read the ledger -> schedule-result JSON

The NEXORA tool uploads PRIVATE, adopts an interrupted upload by its marker tag, applies an approval only when id, version,
sha256 and video id all match, and refuses a slot another video holds - the same guarantees as the OA side.
--ops-dir is a checkout of NEXORA's youtube-ops branch; the caller commits and pushes it (media via Git LFS, as NEXORA does).
"""
import argparse, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine as E  # noqa: E402
from run import DEFAULT_STATE  # noqa: E402


def nx_id(rel):
    return rel["id"]                                     # e.g. nx-20261120-01, unique per release


def cmd_request(a, cfg):
    r = E.load(a.state, a.release)
    v = E.current_version(r)
    if r["channel"] != "nx":
        raise E.PipelineError("not a NEXORA release")
    m = os.path.join(a.ops_dir, "media")
    os.makedirs(m, exist_ok=True)
    names = {}
    for k in ("video", "thumbnail", "captions"):
        src = v["files"][k]
        dst = f"{nx_id(r)}-v{v['n']}{os.path.splitext(src)[1]}"
        shutil.copy(src, os.path.join(m, dst))
        names[k] = "media/" + dst
    meta = r.get("meta") or {}
    req = {"id": nx_id(r), "version": v["n"], "kind": "long", "file": names["video"], "sha256": v["video_sha256"], "title": v["title"],
           "description": v["description"], "tags": v["tags"], "category_id": int(meta.get("category_id", 28)), "language": "en",
           "made_for_kids": bool(meta.get("made_for_kids", False)), "contains_synthetic_media": bool(meta.get("contains_synthetic_media", True)),
           "thumbnail": names["thumbnail"], "captions": names["captions"], "captions_name": "English", "expect_source": "1920x1080",
           "pipeline": {"release": r["id"], "version_hash": v["version_hash"]}}
    p = os.path.join(a.ops_dir, "publish", "requests", nx_id(r) + ".json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(req, open(p, "w"), ensure_ascii=False, indent=1)
    r["stage"] = "preview_requested"
    E.log(r, "preview_requested", target="NEXORA youtube-ops", request=p)
    E.save(a.state, r)
    return {"request": p, "lfs_files": list(names.values()), "next": "git lfs track media/*; commit; push youtube-ops"}


def ledger(a):
    p = os.path.join(a.ops_dir, "publish", "ledger.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def cmd_preview(a, cfg):
    r = E.load(a.state, a.release)
    v = E.current_version(r)
    e = ledger(a).get(f"{nx_id(r)}@v{v['n']}") or {}
    yt = e.get("youtube") or {}
    ok = e.get("sha256") == v["video_sha256"] and bool(e.get("video_id")) and yt.get("privacyStatus") == "private"
    res = {"ok": ok, "video_sha256": v["video_sha256"], "video_id": e.get("video_id"), "privacyStatus": yt.get("privacyStatus"),
           "error": None if ok else f"NEXORA ledger: {e.get('steps') or 'no entry yet'}"}
    if a.apply:
        E.apply_preview_result(r, res); E.save(a.state, r)
    return res


def cmd_status(a, cfg):
    p = os.path.join(a.ops_dir, "publish", "last-run.json")
    lr = json.load(open(p)) if os.path.exists(p) else {}
    vids = [{"video_id": v["id"], "privacy": v["privacy"], "publishAt": v.get("publishAt"), "publishedAt": v.get("publishedAt"),
             "seconds": None, "title": v.get("title")} for v in lr.get("channel_videos", [])]
    return {"ok": bool(lr), "source": "NEXORA publish/last-run.json", "videos": vids, "note": "durations unknown: every video counts as long"}


def cmd_approval(a, cfg):
    r = E.load(a.state, a.release)
    req = E.schedule_request(r, cfg)
    ap = req["approval"]
    doc = {"id": nx_id(r), "version": ap["version"], "sha256": ap["video_sha256"], "video_id": ap["video_id"], "privacy": "scheduled",
           "publish_at": ap["publish_at"], "made_for_kids": False, "contains_synthetic_media": True, "approved_by": "Егор (owner)",
           "approved_at": ap["approved_at"],
           "evidence": f"Pipeline card {ap['card_code']} ({ap['card_id']}) answered ОК by {ap['actor']} at {ap['approved_at']} "
                       f"(source: {ap.get('source') or 'decision card'}; message {ap.get('message_id')})",
           "scope": f"{nx_id(r)} v{ap['version']} only (pipeline approval {ap['approval_id']})"}
    if r.get("test"):
        raise E.PipelineError("a test release is never scheduled for real")
    p = os.path.join(a.ops_dir, "publish", "approvals", nx_id(r) + ".json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(doc, open(p, "w"), ensure_ascii=False, indent=1)
    r["stage"] = "schedule_requested"
    E.log(r, "schedule_requested", target="NEXORA youtube-ops", approval_id=ap["approval_id"])
    E.save(a.state, r)
    return {"approval_file": p}


def cmd_schedule(a, cfg):
    r = E.load(a.state, a.release)
    ap = r["approval"]
    e = ledger(a).get(f"{nx_id(r)}@v{ap['version']}") or {}
    yt = e.get("youtube") or {}
    ok = yt.get("privacyStatus") == "private" and yt.get("publishAt") == ap["publish_at"]
    res = {"ok": ok, "approval_id": ap["approval_id"], "video_id": ap["video_id"], "publishAt": yt.get("publishAt"),
           "privacyStatus": yt.get("privacyStatus"), "error": None if ok else f"NEXORA ledger: {e.get('steps')}"}
    if a.apply:
        E.apply_schedule_result(r, res); E.save(a.state, r)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["request", "preview", "status", "approval", "schedule"])
    ap.add_argument("--state", default=DEFAULT_STATE); ap.add_argument("--release"); ap.add_argument("--ops-dir", required=True)
    ap.add_argument("--apply", action="store_true", help="write the result into the release state")
    a = ap.parse_args(argv)
    try:
        out = globals()["cmd_" + a.cmd](a, E.load_config())
    except (E.PipelineError, KeyError, FileNotFoundError) as ex:
        out = {"ok": False, "error": str(ex)}
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
